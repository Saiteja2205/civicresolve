import { useEffect, useRef, useState } from "react";
import L from "leaflet";

import "leaflet/dist/leaflet.css";
import "../styles/complaint-location-picker.css";

const DEFAULT_CENTER = [16.521, 80.667];
const DEFAULT_ZOOM = 13;

function isValidLatitude(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= -90 && number <= 90;
}

function isValidLongitude(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= -180 && number <= 180;
}

function ComplaintLocationPicker({
  latitude,
  longitude,
  onLocationSelect,
  disabled = false,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  const [isOpen, setIsOpen] = useState(false);

  const hasCoordinates =
    isValidLatitude(latitude) && isValidLongitude(longitude);

  useEffect(() => {
    if (!isOpen || !mapContainerRef.current || mapRef.current) {
      return undefined;
    }

    const initialCenter = hasCoordinates
      ? [Number(latitude), Number(longitude)]
      : DEFAULT_CENTER;

    const map = L.map(mapContainerRef.current, {
      center: initialCenter,
      zoom: hasCoordinates ? 16 : DEFAULT_ZOOM,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    map.on("click", (event) => {
      const selectedLatitude = event.latlng.lat.toFixed(6);
      const selectedLongitude = event.latlng.lng.toFixed(6);

      onLocationSelect(selectedLatitude, selectedLongitude);
    });

    mapRef.current = map;

    window.setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }

    const map = mapRef.current;

    if (!hasCoordinates) {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }

      return;
    }

    const position = [Number(latitude), Number(longitude)];

    if (!markerRef.current) {
      markerRef.current = L.circleMarker(position, {
        radius: 9,
        weight: 3,
        color: "#ffffff",
        fillColor: "#7f56d9",
        fillOpacity: 1,
      }).addTo(map);

      markerRef.current.bindTooltip("Selected complaint location", {
        direction: "top",
        offset: [0, -8],
      });
    } else {
      markerRef.current.setLatLng(position);
    }

    map.setView(position, Math.max(map.getZoom(), 16), {
      animate: true,
    });
  }, [latitude, longitude, hasCoordinates]);

  function handleToggle() {
    setIsOpen((current) => !current);
  }

  function handleClear() {
    onLocationSelect("", "");
  }

  return (
    <div className="complaint-location-picker">
      <div className="complaint-location-picker-header">
        <div>
          <h3>Pin complaint location</h3>
          <p>
            Select the exact location on the map. This helps administrators
            visualize complaints geographically.
          </p>
        </div>

        <button
          type="button"
          className="complaint-location-map-toggle"
          onClick={handleToggle}
          disabled={disabled}
        >
          {isOpen ? "Hide map" : "Pick on map"}
        </button>
      </div>

      {hasCoordinates && (
        <div className="complaint-location-selected">
          <div className="complaint-location-selected-icon" aria-hidden="true">
            ✓
          </div>

          <div className="complaint-location-selected-content">
            <strong>Location selected</strong>
            <span>
              Latitude {Number(latitude).toFixed(6)}, Longitude{" "}
              {Number(longitude).toFixed(6)}
            </span>
          </div>

          <button
            type="button"
            className="complaint-location-clear"
            onClick={handleClear}
            disabled={disabled}
          >
            Clear
          </button>
        </div>
      )}

      {isOpen && (
        <div className="complaint-location-map-wrapper">
          <div className="complaint-location-map-instruction">
            <span className="complaint-location-map-pin" aria-hidden="true">
              +
            </span>

            <span>
              Click anywhere on the map to place the complaint location.
            </span>
          </div>

          <div
            ref={mapContainerRef}
            className="complaint-location-map"
            aria-label="Complaint location map"
          />

          <div className="complaint-location-map-footer">
            <span>
              {hasCoordinates
                ? "You can click again to move the location pin."
                : "No map location selected yet."}
            </span>

            {hasCoordinates && (
              <button
                type="button"
                className="complaint-location-clear-map"
                onClick={handleClear}
                disabled={disabled}
              >
                Remove pin
              </button>
            )}
          </div>
        </div>
      )}

      {!hasCoordinates && !isOpen && (
        <p className="complaint-location-picker-hint">
          Location coordinates are optional. You can enter them manually below
          or use the map to select a point.
        </p>
      )}
    </div>
  );
}

export default ComplaintLocationPicker;