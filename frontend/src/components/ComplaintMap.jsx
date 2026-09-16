import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "../styles/complaint-map.css";
import { getComplaints } from "../services/complaintService.js";

const DEFAULT_CENTER = [16.5062, 80.648];
const DEFAULT_ZOOM = 11;

const PRIORITY_COLORS = {
  LOW: "#16a34a",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#dc2626",
};

const PRIORITY_LABELS = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  CRITICAL: "Critical",
};

const STATUS_LABELS = {
  SUBMITTED: "Submitted",
  AI_ANALYZING: "AI Analyzing",
  ASSIGNED: "Assigned",
  ACKNOWLEDGED: "Acknowledged",
  IN_PROGRESS: "In Progress",
  NEEDS_INFORMATION: "Needs Information",
  ESCALATED: "Escalated",
  RESOLVED: "Resolved",
  CLOSED: "Closed",
  REOPENED: "Reopened",
  REJECTED: "Rejected",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getComplaintArray(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  if (Array.isArray(data?.data)) {
    return data.data;
  }

  return [];
}

function parseCoordinate(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number.parseFloat(value);

  return Number.isFinite(number) ? number : null;
}

function createMarkerIcon(priority) {
  const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.MEDIUM;

  return L.divIcon({
    className: "complaint-map-marker-wrapper",
    html: `
      <div
        class="complaint-map-marker"
        style="--marker-color: ${color};"
      >
        <span></span>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -16],
  });
}

function createPopupContent(complaint) {
  const priority = complaint.priority || "MEDIUM";
  const status = complaint.status || "SUBMITTED";
  const complaintId = Number(complaint.id);

  return `
    <div class="complaint-map-popup">
      <div class="complaint-map-popup-ticket">
        ${escapeHtml(
          complaint.ticket_number || `Complaint #${complaint.id}`,
        )}
      </div>

      <div class="complaint-map-popup-title">
        ${escapeHtml(complaint.title || "Untitled complaint")}
      </div>

      <div class="complaint-map-popup-grid">
        <div>
          <span>Category</span>
          <strong>${escapeHtml(complaint.category_name || "—")}</strong>
        </div>

        <div>
          <span>Status</span>
          <strong>
            ${escapeHtml(STATUS_LABELS[status] || status)}
          </strong>
        </div>

        <div>
          <span>Priority</span>
          <strong>
            ${escapeHtml(PRIORITY_LABELS[priority] || priority)}
          </strong>
        </div>

        <div>
          <span>Location</span>
          <strong>${escapeHtml(complaint.location || "—")}</strong>
        </div>
      </div>

      <button
        type="button"
        class="complaint-map-popup-link"
        data-complaint-id="${Number.isFinite(complaintId) ? complaintId : ""}"
      >
        View complaint →
      </button>
    </div>
  `;
}

export default function ComplaintMap() {
  const navigate = useNavigate();

  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerLayerRef = useRef(null);

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadComplaints() {
      try {
        setLoading(true);
        setError("");

        const response = await getComplaints();

        if (cancelled) {
          return;
        }

        setComplaints(getComplaintArray(response));
      } catch (requestError) {
        if (cancelled) {
          return;
        }

        console.error(
          "Failed to load complaints for map:",
          requestError,
        );

        setError(
          requestError?.response?.data?.detail ||
            requestError?.message ||
            "Unable to load complaint locations.",
        );

        setComplaints([]);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadComplaints();

    return () => {
      cancelled = true;
    };
  }, []);

  const mappedComplaints = useMemo(() => {
    return complaints
      .map((complaint) => {
        const latitude = parseCoordinate(complaint.latitude);
        const longitude = parseCoordinate(complaint.longitude);

        return {
          ...complaint,
          latitude,
          longitude,
        };
      })
      .filter((complaint) => {
        return (
          complaint.latitude !== null &&
          complaint.longitude !== null &&
          complaint.latitude >= -90 &&
          complaint.latitude <= 90 &&
          complaint.longitude >= -180 &&
          complaint.longitude <= 180
        );
      });
  }, [complaints]);

  const filteredComplaints = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return mappedComplaints.filter((complaint) => {
      const matchesSearch =
        !query ||
        [
          complaint.ticket_number,
          complaint.title,
          complaint.location,
          complaint.category_name,
          complaint.status,
          complaint.priority,
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
    searchTerm,
    priorityFilter,
    statusFilter,
  ]);

  const stats = useMemo(() => {
    const activeStatuses = new Set([
      "SUBMITTED",
      "AI_ANALYZING",
      "ASSIGNED",
      "ACKNOWLEDGED",
      "IN_PROGRESS",
      "NEEDS_INFORMATION",
      "ESCALATED",
      "REOPENED",
    ]);

    return {
      totalMapped: filteredComplaints.length,

      active: filteredComplaints.filter((complaint) =>
        activeStatuses.has(complaint.status),
      ).length,

      high: filteredComplaints.filter(
        (complaint) => complaint.priority === "HIGH",
      ).length,

      critical: filteredComplaints.filter(
        (complaint) => complaint.priority === "CRITICAL",
      ).length,

      withoutCoordinates: complaints.filter((complaint) => {
        return (
          parseCoordinate(complaint.latitude) === null ||
          parseCoordinate(complaint.longitude) === null
        );
      }).length,
    };
  }, [complaints, filteredComplaints]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return undefined;
    }

    const map = L.map(mapContainerRef.current, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>',
      },
    ).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);

    mapRef.current = map;
    markerLayerRef.current = markerLayer;

    const resizeTimer = window.setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => {
      window.clearTimeout(resizeTimer);

      markerLayer.clearLayers();
      markerLayerRef.current = null;

      map.remove();
      mapRef.current = null;
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
      map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
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
          "CivicResolve complaint",
      });

      marker.bindPopup(
        createPopupContent(complaint),
        {
          maxWidth: 320,
          minWidth: 240,
        },
      );

      marker.on("popupopen", (event) => {
        const popupElement = event.popup.getElement();

        if (!popupElement) {
          return;
        }

        const button = popupElement.querySelector(
          "[data-complaint-id]",
        );

        if (!button) {
          return;
        }

        const complaintId = Number(
          button.getAttribute("data-complaint-id"),
        );

        const handleClick = () => {
          if (Number.isFinite(complaintId)) {
            navigate(`/dashboard/complaints/${complaintId}`);
          }
        };

        button.addEventListener("click", handleClick, {
          once: true,
        });
      });

      marker.addTo(markerLayer);
    });

    if (bounds.length === 1) {
      map.setView(bounds[0], 15);
    } else {
      map.fitBounds(bounds, {
        padding: [40, 40],
        maxZoom: 15,
      });
    }
  }, [filteredComplaints, navigate]);

  function clearFilters() {
    setSearchTerm("");
    setPriorityFilter("");
    setStatusFilter("");
  }

  return (
    <section className="complaint-map-card">
      <div className="complaint-map-header">
        <div>
          <span className="complaint-map-eyebrow">
            Geospatial intelligence
          </span>

          <h2>Complaint location map</h2>

          <p>
            View geographically tagged grievances and identify
            active complaint clusters.
          </p>
        </div>

        <div className="complaint-map-live-badge">
          <span className="complaint-map-live-dot" />
          Live complaint data
        </div>
      </div>

      <div className="complaint-map-stats">
        <div className="complaint-map-stat">
          <span>Mapped complaints</span>
          <strong>{stats.totalMapped}</strong>
        </div>

        <div className="complaint-map-stat">
          <span>Active</span>
          <strong>{stats.active}</strong>
        </div>

        <div className="complaint-map-stat">
          <span>High priority</span>
          <strong>{stats.high}</strong>
        </div>

        <div className="complaint-map-stat">
          <span>Critical</span>
          <strong>{stats.critical}</strong>
        </div>
      </div>

      <div className="complaint-map-toolbar">
        <div className="complaint-map-search">
          <span>⌕</span>

          <input
            type="search"
            placeholder="Search ticket, title, location..."
            value={searchTerm}
            onChange={(event) =>
              setSearchTerm(event.target.value)
            }
          />
        </div>

        <select
          value={priorityFilter}
          onChange={(event) =>
            setPriorityFilter(event.target.value)
          }
          aria-label="Filter by priority"
        >
          <option value="">All priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>

        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(event.target.value)
          }
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>

          {Object.entries(STATUS_LABELS).map(
            ([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ),
          )}
        </select>
      </div>

      <div className="complaint-map-container">
        <div
          ref={mapContainerRef}
          className="complaint-map"
          aria-label="Geographical complaint map"
        />

        {loading && (
          <div className="complaint-map-overlay">
            <div className="complaint-map-loading">
              <span className="complaint-map-spinner" />
              Loading complaint locations...
            </div>
          </div>
        )}

        {!loading && error && (
          <div className="complaint-map-overlay">
            <div className="complaint-map-message complaint-map-error">
              <strong>Unable to load map data</strong>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>

      <div className="complaint-map-footer">
        <div className="complaint-map-legend">
          {Object.entries(PRIORITY_COLORS).map(
            ([priority, color]) => (
              <span key={priority}>
                <i
                  className="complaint-map-legend-dot"
                  style={{
                    backgroundColor: color,
                  }}
                />
                {PRIORITY_LABELS[priority]}
              </span>
            ),
          )}
        </div>

        <div className="complaint-map-result-summary">
          {stats.withoutCoordinates > 0 && (
            <span>
              {stats.withoutCoordinates} complaints without
              coordinates
            </span>
          )}

          <span>
            Showing {filteredComplaints.length} of{" "}
            {mappedComplaints.length} mapped complaints
          </span>
        </div>
      </div>

      {filteredComplaints.length === 0 &&
        !loading &&
        !error && (
          <div className="complaint-map-empty">
            <strong>No mapped complaints found</strong>

            {mappedComplaints.length > 0 ? (
              <span>
                Try changing your search or filters.
              </span>
            ) : (
              <span>
                No complaints with valid latitude and
                longitude coordinates are currently
                available.
              </span>
            )}

            {(searchTerm ||
              priorityFilter ||
              statusFilter) && (
              <button
                type="button"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            )}
          </div>
        )}

      <div className="complaint-map-note">
        Map data · Only complaints containing valid latitude
        and longitude coordinates are displayed.
      </div>
    </section>
  );
}