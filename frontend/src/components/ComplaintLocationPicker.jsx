import { useEffect, useRef, useState } from "react";
import L from "leaflet";

import "leaflet/dist/leaflet.css";
import "../styles/complaint-location-picker.css";

const DEFAULT_CENTER = [16.521, 80.667];
const DEFAULT_ZOOM = 13;
const LOCATION_ZOOM = 18;

function isValidLatitude(value) {
  if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
  ) {
    return false;
  }

  const number = Number(value);

  return Number.isFinite(number) && number >= -90 && number <= 90;
}

function isValidLongitude(value) {
  if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
  ) {
    return false;
  }

  const number = Number(value);

  return Number.isFinite(number) && number >= -180 && number <= 180;
}

function formatAccuracy(accuracy) {
  if (!Number.isFinite(accuracy)) {
    return null;
  }

  if (accuracy < 10) {
    return `±${Math.round(accuracy)} m`;
  }

  if (accuracy < 1000) {
    return `±${Math.round(accuracy)} m`;
  }

  return `±${(accuracy / 1000).toFixed(1)} km`;
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
  const accuracyCircleRef = useRef(null);

  const [isOpen, setIsOpen] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState("");
  const [locationAccuracy, setLocationAccuracy] = useState(null);
  const [locationSource, setLocationSource] = useState("");

  const hasCoordinates =
    isValidLatitude(latitude) &&
    isValidLongitude(longitude);

  useEffect(() => {
    if (!isOpen || !mapContainerRef.current || mapRef.current) {
      return undefined;
    }

    const initialCenter = hasCoordinates
      ? [Number(latitude), Number(longitude)]
      : DEFAULT_CENTER;

    const map = L.map(mapContainerRef.current, {
      center: initialCenter,
      zoom: hasCoordinates ? LOCATION_ZOOM : DEFAULT_ZOOM,
      scrollWheelZoom: true,
    });

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors',
        maxZoom: 19,
      },
    ).addTo(map);

    map.on("click", (event) => {
      const selectedLatitude =
        event.latlng.lat.toFixed(6);

      const selectedLongitude =
        event.latlng.lng.toFixed(6);

      setLocationError("");
      setLocationAccuracy(null);
      setLocationSource("Map selection");

      onLocationSelect(
        selectedLatitude,
        selectedLongitude,
      );
    });

    mapRef.current = map;

    window.setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
      accuracyCircleRef.current = null;
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

      if (accuracyCircleRef.current) {
        accuracyCircleRef.current.remove();
        accuracyCircleRef.current = null;
      }

      return;
    }

    const position = [
      Number(latitude),
      Number(longitude),
    ];

    if (!markerRef.current) {
      markerRef.current = L.circleMarker(position, {
        radius: 9,
        weight: 3,
        color: "#ffffff",
        fillColor: "#7f56d9",
        fillOpacity: 1,
      }).addTo(map);

      markerRef.current.bindTooltip(
        locationSource === "Current location"
          ? "Your current location"
          : "Selected complaint location",
        {
          direction: "top",
          offset: [0, -8],
        },
      );
    } else {
      markerRef.current.setLatLng(position);

      markerRef.current.setTooltipContent(
        locationSource === "Current location"
          ? "Your current location"
          : "Selected complaint location",
      );
    }

    if (
      locationSource === "Current location" &&
      Number.isFinite(locationAccuracy)
    ) {
      if (!accuracyCircleRef.current) {
        accuracyCircleRef.current = L.circle(position, {
          radius: locationAccuracy,
          weight: 1.5,
          color: "#7f56d9",
          fillColor: "#7f56d9",
          fillOpacity: 0.12,
        }).addTo(map);
      } else {
        accuracyCircleRef.current.setLatLng(position);
        accuracyCircleRef.current.setRadius(locationAccuracy);
      }
    } else if (accuracyCircleRef.current) {
      accuracyCircleRef.current.remove();
      accuracyCircleRef.current = null;
    }

    map.setView(position, Math.max(map.getZoom(), LOCATION_ZOOM), {
      animate: true,
    });
  }, [
    latitude,
    longitude,
    hasCoordinates,
    locationAccuracy,
    locationSource,
  ]);

  function handleToggle() {
    setIsOpen((current) => !current);
  }

  function handleClear() {
    setLocationError("");
    setLocationAccuracy(null);
    setLocationSource("");
    onLocationSelect("", "");
  }

  function handleUseCurrentLocation() {
    if (!navigator.geolocation) {
      setLocationError(
        "Your browser does not support location services.",
      );
      return;
    }

    if (disabled || locationLoading) {
      return;
    }

    setLocationLoading(true);
    setLocationError("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const selectedLatitude =
          position.coords.latitude.toFixed(6);

        const selectedLongitude =
          position.coords.longitude.toFixed(6);

        const accuracy = Number(position.coords.accuracy);

        onLocationSelect(
          selectedLatitude,
          selectedLongitude,
        );

        setLocationAccuracy(
          Number.isFinite(accuracy) ? accuracy : null,
        );

        setLocationSource("Current location");
        setLocationLoading(false);
        setLocationError("");
        setIsOpen(true);
      },
      (error) => {
        console.error(
          "Unable to get current location:",
          error,
        );

        setLocationLoading(false);

        if (error.code === 1) {
          setLocationError(
            "Location permission was denied. Allow location access for localhost and try again.",
          );
        } else if (error.code === 2) {
          setLocationError(
            "Your current location could not be determined. Try again or select a point on the map.",
          );
        } else if (error.code === 3) {
          setLocationError(
            "Location request timed out. Please try again.",
          );
        } else {
          setLocationError(
            "Unable to get your current location. Please try again.",
          );
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 60000,
      },
    );
  }

  return (
    <div className="complaint-location-picker">
      <div className="complaint-location-picker-header">
        <div>
          <h3>Pin complaint location</h3>

          <p>
            Select the exact location manually or use your
            current location.
          </p>
        </div>

        <div className="complaint-location-picker-actions">
          <button
            type="button"
            className="complaint-location-current-button"
            onClick={handleUseCurrentLocation}
            disabled={disabled || locationLoading}
          >
            <span aria-hidden="true">📍</span>

            {locationLoading
              ? "Locating..."
              : "Use my current location"}
          </button>

          <button
            type="button"
            className="complaint-location-map-toggle"
            onClick={handleToggle}
            disabled={disabled}
          >
            {isOpen ? "Hide map" : "Pick on map"}
          </button>
        </div>
      </div>

      {locationError && (
        <div
          className="complaint-location-error"
          role="alert"
        >
          {locationError}
        </div>
      )}

      {hasCoordinates && (
        <div className="complaint-location-selected">
          <div
            className="complaint-location-selected-icon"
            aria-hidden="true"
          >
            ✓
          </div>

          <div className="complaint-location-selected-content">
            <strong>
              {locationSource === "Current location"
                ? "Current location selected"
                : "Location selected"}
            </strong>

            <span>
              Latitude {Number(latitude).toFixed(6)}, Longitude{" "}
              {Number(longitude).toFixed(6)}
            </span>

            {locationSource === "Current location" &&
              locationAccuracy !== null && (
                <span className="complaint-location-accuracy">
                  GPS accuracy: {formatAccuracy(locationAccuracy)}
                </span>
              )}
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
            <span
              className="complaint-location-map-pin"
              aria-hidden="true"
            >
              +
            </span>

            <span>
              Click anywhere on the map to place or correct
              the complaint location.
            </span>
          </div>

          <div
            ref={mapContainerRef}
            className="complaint-location-map"
            aria-label="Complaint location map"
          />

          <div className="complaint-location-map-footer">
            <div>
              <span>
                {locationSource === "Current location"
                  ? "GPS position detected. The circle shows the estimated accuracy."
                  : hasCoordinates
                    ? "Click again to move the complaint location."
                    : "Click the map to select a complaint location."}
              </span>

              {locationSource === "Current location" &&
                locationAccuracy !== null && (
                  <strong>
                    Accuracy: {formatAccuracy(locationAccuracy)}
                  </strong>
                )}
            </div>

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

      {!hasCoordinates && !isOpen && !locationError && (
        <p className="complaint-location-picker-hint">
          You can select a point on the map or use your
          current location. Coordinates are optional.
        </p>
      )}
    </div>
  );
}

export default ComplaintLocationPicker;