import { useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { getComplaints } from "../services/complaintService.js";
import "../styles/complaint-map.css";

const DEFAULT_CENTER = [16.521, 80.667];

const PRIORITY_META = {
  LOW: {
    label: "Low",
    color: "#2563eb",
  },
  MEDIUM: {
    label: "Medium",
    color: "#d97706",
  },
  HIGH: {
    label: "High",
    color: "#dc2626",
  },
  CRITICAL: {
    label: "Critical",
    color: "#991b1b",
  },
};

const TERMINAL_STATUSES = new Set([
  "RESOLVED",
  "CLOSED",
  "REJECTED",
]);

function getComplaintList(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.results)) {
    return response.results;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  return [];
}

function getCoordinate(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function hasValidCoordinates(complaint) {
  const latitude = getCoordinate(complaint.latitude);
  const longitude = getCoordinate(complaint.longitude);

  return (
    latitude !== null &&
    longitude !== null &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  );
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getPriorityColor(priority) {
  return PRIORITY_META[priority]?.color ?? "#64748b";
}

function createMarkerIcon(priority) {
  const color = getPriorityColor(priority);

  return L.divIcon({
    className: "complaint-map-marker-wrapper",
    html: `
      <div
        class="complaint-map-marker"
        style="background:${color};"
        aria-hidden="true"
      ></div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
  });
}

function buildPopup(complaint) {
  const ticket = escapeHtml(
    complaint.ticket_number || "Complaint",
  );

  const title = escapeHtml(
    complaint.title || "Untitled complaint",
  );

  const category = escapeHtml(
    complaint.category_name ||
      complaint.category?.name ||
      complaint.category ||
      "Uncategorized",
  );

  const status = escapeHtml(
    complaint.status || "UNKNOWN",
  );

  const priority = escapeHtml(
    complaint.priority || "MEDIUM",
  );

  const location = escapeHtml(
    complaint.location || "Location not provided",
  );

  return `
    <div class="complaint-map-popup">
      <div class="complaint-map-popup-ticket">
        ${ticket}
      </div>

      <div class="complaint-map-popup-title">
        ${title}
      </div>

      <div class="complaint-map-popup-row">
        <span>Category</span>
        <strong>${category}</strong>
      </div>

      <div class="complaint-map-popup-row">
        <span>Status</span>
        <strong>${status}</strong>
      </div>

      <div class="complaint-map-popup-row">
        <span>Priority</span>
        <strong>${priority}</strong>
      </div>

      <div class="complaint-map-popup-row">
        <span>Location</span>
        <strong>${location}</strong>
      </div>

      <a
        class="complaint-map-popup-link"
        href="/dashboard/complaints/${encodeURIComponent(complaint.id)}"
      >
        View complaint
      </a>
    </div>
  `;
}

export default function ComplaintMap() {
  const mapElementRef = useRef(null);
  const mapRef = useRef(null);
  const markerLayerRef = useRef(null);

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  async function loadComplaints(showRefreshState = false) {
    try {
      if (showRefreshState) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await getComplaints();
      const data = getComplaintList(response);

      setComplaints(data);
    } catch (requestError) {
      console.error(
        "Failed to load complaints for map:",
        requestError,
      );

      setError(
        requestError?.response?.data?.detail ||
          requestError?.message ||
          "Unable to load complaint locations.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadComplaints();

    // Initial data load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const mappedComplaints = useMemo(() => {
    return complaints
      .filter(hasValidCoordinates)
      .map((complaint) => ({
        ...complaint,
        latitude: getCoordinate(complaint.latitude),
        longitude: getCoordinate(complaint.longitude),
      }));
  }, [complaints]);

  const filteredComplaints = useMemo(() => {
    const query = search.trim().toLowerCase();

    return mappedComplaints.filter((complaint) => {
      const matchesSearch =
        !query ||
        [
          complaint.ticket_number,
          complaint.title,
          complaint.description,
          complaint.location,
          complaint.status,
          complaint.priority,
          complaint.category_name,
          complaint.category?.name,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value).toLowerCase().includes(query),
          );

      const matchesPriority =
        !priorityFilter ||
        complaint.priority === priorityFilter;

      const matchesStatus =
        !statusFilter ||
        complaint.status === statusFilter;

      return (
        matchesSearch &&
        matchesPriority &&
        matchesStatus
      );
    });
  }, [
    mappedComplaints,
    search,
    priorityFilter,
    statusFilter,
  ]);

  const stats = useMemo(() => {
    const active = mappedComplaints.filter(
      (complaint) =>
        !TERMINAL_STATUSES.has(complaint.status),
    ).length;

    const highOrCritical = mappedComplaints.filter(
      (complaint) =>
        complaint.priority === "HIGH" ||
        complaint.priority === "CRITICAL",
    ).length;

    const critical = mappedComplaints.filter(
      (complaint) => complaint.priority === "CRITICAL",
    ).length;

    return {
      total: mappedComplaints.length,
      active,
      highOrCritical,
      critical,
      withoutCoordinates:
        Math.max(
          complaints.length - mappedComplaints.length,
          0,
        ),
    };
  }, [complaints, mappedComplaints]);

  const statusOptions = useMemo(() => {
    return [
      ...new Set(
        mappedComplaints.map(
          (complaint) => complaint.status,
        ),
      ),
    ]
      .filter(Boolean)
      .sort();
  }, [mappedComplaints]);

  useEffect(() => {
    if (!mapElementRef.current || mapRef.current) {
      return undefined;
    }

    const map = L.map(mapElementRef.current, {
      center: DEFAULT_CENTER,
      zoom: 6,
      scrollWheelZoom: true,
    });

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      },
    ).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);

    mapRef.current = map;
    markerLayerRef.current = markerLayer;

    const resizeTimer = window.setTimeout(() => {
      map.invalidateSize();
    }, 150);

    return () => {
      window.clearTimeout(resizeTimer);
      map.remove();

      mapRef.current = null;
      markerLayerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const markerLayer = markerLayerRef.current;

    if (!map || !markerLayer) {
      return;
    }

    markerLayer.clearLayers();

    if (filteredComplaints.length === 0) {
      map.setView(DEFAULT_CENTER, 6);
      return;
    }

    const bounds = [];

    filteredComplaints.forEach((complaint) => {
      const position = [
        complaint.latitude,
        complaint.longitude,
      ];

      bounds.push(position);

      const marker = L.marker(position, {
        icon: createMarkerIcon(complaint.priority),
        title:
          complaint.ticket_number ||
          complaint.title ||
          "Complaint",
      });

      marker.bindPopup(
        buildPopup(complaint),
        {
          maxWidth: 320,
        },
      );

      marker.addTo(markerLayer);
    });

    if (bounds.length === 1) {
      map.setView(bounds[0], 14);
    } else {
      map.fitBounds(bounds, {
        padding: [40, 40],
        maxZoom: 15,
      });
    }
  }, [filteredComplaints]);

  function resetFilters() {
    setSearch("");
    setPriorityFilter("");
    setStatusFilter("");
  }

  return (
    <section className="complaint-map-card">
      <div className="complaint-map-header">
        <div>
          <div className="complaint-map-eyebrow">
            Geospatial intelligence
          </div>

          <h2>Complaint location map</h2>

          <p>
            Visualize reported complaints by location,
            priority, and workflow status.
          </p>
        </div>

        <button
          type="button"
          className="complaint-map-refresh"
          onClick={() => loadComplaints(true)}
          disabled={loading || refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="complaint-map-stats">
        <div className="complaint-map-stat">
          <span>Mapped complaints</span>
          <strong>{stats.total}</strong>
        </div>

        <div className="complaint-map-stat">
          <span>Active</span>
          <strong>{stats.active}</strong>
        </div>

        <div className="complaint-map-stat complaint-map-stat-warning">
          <span>High / critical</span>
          <strong>{stats.highOrCritical}</strong>
        </div>

        <div className="complaint-map-stat complaint-map-stat-critical">
          <span>Critical</span>
          <strong>{stats.critical}</strong>
        </div>

        <div className="complaint-map-stat">
          <span>Without coordinates</span>
          <strong>{stats.withoutCoordinates}</strong>
        </div>
      </div>

      <div className="complaint-map-toolbar">
        <div className="complaint-map-field complaint-map-search">
          <label htmlFor="complaint-map-search">
            Search
          </label>

          <input
            id="complaint-map-search"
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Ticket, title, location, category..."
          />
        </div>

        <div className="complaint-map-field">
          <label htmlFor="complaint-map-priority">
            Priority
          </label>

          <select
            id="complaint-map-priority"
            value={priorityFilter}
            onChange={(event) =>
              setPriorityFilter(event.target.value)
            }
          >
            <option value="">All priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>

        <div className="complaint-map-field">
          <label htmlFor="complaint-map-status">
            Status
          </label>

          <select
            id="complaint-map-status"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
          >
            <option value="">All statuses</option>

            {statusOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="complaint-map-reset"
          onClick={resetFilters}
          disabled={
            !search &&
            !priorityFilter &&
            !statusFilter
          }
        >
          Reset
        </button>
      </div>

      <div className="complaint-map-legend">
        <span>Priority:</span>

        {Object.entries(PRIORITY_META).map(
          ([key, meta]) => (
            <span
              key={key}
              className="complaint-map-legend-item"
            >
              <span
                className="complaint-map-legend-dot"
                style={{
                  background: meta.color,
                }}
              />
              {meta.label}
            </span>
          ),
        )}

        <strong>
          {filteredComplaints.length} shown
        </strong>
      </div>

      <div className="complaint-map-container">
        {loading && (
          <div className="complaint-map-overlay">
            <div className="complaint-map-loading">
              Loading complaint locations...
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="complaint-map-empty">
            <strong>
              Unable to load the map data
            </strong>

            <p>{error}</p>

            <button
              type="button"
              onClick={() => loadComplaints()}
            >
              Try again
            </button>
          </div>
        )}

        {!loading &&
          !error &&
          mappedComplaints.length === 0 && (
            <div className="complaint-map-empty">
              <strong>
                No complaints have coordinates yet
              </strong>

              <p>
                Add valid latitude and longitude values
                to a complaint to display it on the map.
              </p>
            </div>
          )}

        {!loading &&
          !error &&
          mappedComplaints.length > 0 &&
          filteredComplaints.length === 0 && (
            <div className="complaint-map-empty">
              <strong>
                No mapped complaints match these filters
              </strong>

              <p>
                Reset the filters to view all mapped
                complaints.
              </p>
            </div>
          )}

        <div
          ref={mapElementRef}
          className="complaint-map"
          aria-label="Complaint locations map"
        />
      </div>

      <div className="complaint-map-footer">
        <span>
          Only complaints with valid latitude and
          longitude coordinates are displayed on the map.
        </span>

        <a
          href="https://www.openstreetmap.org/"
          target="_blank"
          rel="noreferrer"
        >
          OpenStreetMap
        </a>
      </div>
    </section>
  );
}