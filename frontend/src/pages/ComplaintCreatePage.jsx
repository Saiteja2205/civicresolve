import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  createComplaint,
  getCategories,
} from "../services/complaintService.js";

import ComplaintLocationPicker from "../components/ComplaintLocationPicker.jsx";

import "../styles/complaint-form.css";
import "../styles/voice-input.css";

function ComplaintCreatePage() {
  const navigate = useNavigate();

  const recognitionRef = useRef(null);

  const [categories, setCategories] = useState([]);

  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "",
    location: "",
    latitude: "",
    longitude: "",
  });

  const [loadingCategories, setLoadingCategories] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const [speechSupported, setSpeechSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const [voiceInterimText, setVoiceInterimText] = useState("");

  useEffect(() => {
    async function loadCategories() {
      try {
        setLoadingCategories(true);
        setError("");

        const data = await getCategories();

        const categoryList = Array.isArray(data)
          ? data
          : data.results || [];

        setCategories(categoryList);
      } catch (requestError) {
        console.error("Failed to load categories:", requestError);

        setError(
          "Unable to load complaint categories. Please try again.",
        );
      } finally {
        setLoadingCategories(false);
      }
    }

    loadCategories();
  }, []);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return undefined;
    }

    setSpeechSupported(true);

    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setSpeechError("");
      setVoiceInterimText("");
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (
        let index = event.resultIndex;
        index < event.results.length;
        index += 1
      ) {
        const transcript =
          event.results[index][0].transcript;

        if (event.results[index].isFinal) {
          finalText += transcript;
        } else {
          interimText += transcript;
        }
      }

      if (finalText.trim()) {
        setForm((current) => {
          const existingDescription =
            current.description.trim();

          const separator =
            existingDescription ? " " : "";

          return {
            ...current,
            description:
              existingDescription +
              separator +
              finalText.trim(),
          };
        });

        setFieldErrors((current) => ({
          ...current,
          description: "",
        }));

        setError("");
      }

      setVoiceInterimText(interimText.trim());
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event.error,
      );

      setIsListening(false);

      if (event.error === "not-allowed") {
        setSpeechError(
          "Microphone access was denied. Allow microphone permission and try again.",
        );
      } else if (event.error === "no-speech") {
        setSpeechError(
          "No speech was detected. Please try speaking again.",
        );
      } else if (event.error === "audio-capture") {
        setSpeechError(
          "No microphone was detected. Check your microphone and try again.",
        );
      } else if (event.error === "network") {
        setSpeechError(
          "Speech recognition could not connect. Check your internet connection and try again.",
        );
      } else {
        setSpeechError(
          "Voice input encountered an error. Please try again.",
        );
      }

      setVoiceInterimText("");
    };

    recognition.onend = () => {
      setIsListening(false);
      setVoiceInterimText("");
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setFieldErrors((current) => ({
      ...current,
      [name]: "",
    }));

    setError("");

    if (name === "description") {
      setSpeechError("");
    }
  }

  function handleMapLocationSelect(latitude, longitude) {
    setForm((current) => ({
      ...current,
      latitude,
      longitude,
    }));

    setFieldErrors((current) => ({
      ...current,
      latitude: "",
      longitude: "",
    }));

    setError("");
  }

  function startVoiceInput() {
    if (!speechSupported) {
      setSpeechError(
        "Voice input is not supported in this browser. Please use Chrome or Edge.",
      );
      return;
    }

    if (!recognitionRef.current) {
      setSpeechError(
        "Voice input is not ready. Please refresh the page and try again.",
      );
      return;
    }

    if (isListening) {
      return;
    }

    setSpeechError("");
    setVoiceInterimText("");

    try {
      recognitionRef.current.start();
    } catch (recognitionError) {
      console.error(
        "Unable to start speech recognition:",
        recognitionError,
      );

      setSpeechError(
        "Unable to start voice input. Please try again.",
      );
    }
  }

  function stopVoiceInput() {
    if (!recognitionRef.current) {
      return;
    }

    try {
      recognitionRef.current.stop();
    } catch (recognitionError) {
      console.error(
        "Unable to stop speech recognition:",
        recognitionError,
      );
    }

    setIsListening(false);
    setVoiceInterimText("");
  }

  function clearVoiceTranscript() {
    setForm((current) => ({
      ...current,
      description: "",
    }));

    setVoiceInterimText("");
    setSpeechError("");

    setFieldErrors((current) => ({
      ...current,
      description: "",
    }));
  }

  function validateForm() {
    const errors = {};

    if (!form.title.trim()) {
      errors.title = "Title is required.";
    } else if (form.title.trim().length < 5) {
      errors.title = "Title must be at least 5 characters.";
    }

    if (!form.description.trim()) {
      errors.description = "Description is required.";
    } else if (form.description.trim().length < 10) {
      errors.description =
        "Description must be at least 10 characters.";
    }

    if (!form.category) {
      errors.category = "Please select a category.";
    }

    if (
      form.latitude.trim() &&
      Number.isNaN(Number(form.latitude))
    ) {
      errors.latitude = "Latitude must be a valid number.";
    }

    if (
      form.longitude.trim() &&
      Number.isNaN(Number(form.longitude))
    ) {
      errors.longitude = "Longitude must be a valid number.";
    }

    if (
      form.latitude.trim() &&
      (
        Number(form.latitude) < -90 ||
        Number(form.latitude) > 90
      )
    ) {
      errors.latitude =
        "Latitude must be between -90 and 90.";
    }

    if (
      form.longitude.trim() &&
      (
        Number(form.longitude) < -180 ||
        Number(form.longitude) > 180
      )
    ) {
      errors.longitude =
        "Longitude must be between -180 and 180.";
    }

    if (
      form.latitude.trim() &&
      !form.longitude.trim()
    ) {
      errors.longitude =
        "Longitude is required when latitude is provided.";
    }

    if (
      form.longitude.trim() &&
      !form.latitude.trim()
    ) {
      errors.latitude =
        "Latitude is required when longitude is provided.";
    }

    return errors;
  }

  function extractApiErrors(requestError) {
    const data = requestError?.response?.data;

    if (!data) {
      return {
        general:
          "Something went wrong while submitting the complaint.",
      };
    }

    if (typeof data === "string") {
      return {
        general: data,
      };
    }

    const errors = {};

    Object.entries(data).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        errors[key] = value.join(" ");
      } else if (typeof value === "string") {
        errors[key] = value;
      } else {
        errors[key] = JSON.stringify(value);
      }
    });

    return errors;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (isListening) {
      stopVoiceInput();
    }

    const validationErrors = validateForm();

    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    setError("");
    setFieldErrors({});

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: Number(form.category),
    };

    if (form.location.trim()) {
      payload.location = form.location.trim();
    }

    if (form.latitude.trim()) {
      payload.latitude = Number(form.latitude);
    }

    if (form.longitude.trim()) {
      payload.longitude = Number(form.longitude);
    }

    try {
      const complaint = await createComplaint(payload);

      navigate(
        `/dashboard/complaints/${complaint.id}`,
        {
          replace: true,
        },
      );
    } catch (requestError) {
      console.error(
        "Complaint submission failed:",
        requestError,
      );

      const apiErrors =
        extractApiErrors(requestError);

      const generalError =
        apiErrors.general ||
        apiErrors.detail ||
        "Complaint submission failed.";

      setError(generalError);

      const mappedFieldErrors = {
        ...apiErrors,
      };

      delete mappedFieldErrors.general;
      delete mappedFieldErrors.detail;

      setFieldErrors(mappedFieldErrors);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="complaint-form-page">
      <div className="complaint-form-header">
        <div>
          <p className="dashboard-eyebrow">
            CITIZEN WORKSPACE
          </p>

          <h1>Submit a complaint</h1>

          <p>
            Tell us what happened. CivicResolve will analyze
            and route your complaint automatically.
          </p>
        </div>

        <Link
          to="/dashboard/complaints"
          className="complaint-secondary-action"
        >
          Back to complaints
        </Link>
      </div>

      <div className="complaint-form-card">
        <div className="complaint-form-intro">
          <h2>Complaint details</h2>

          <p>
            Provide clear information so the system can
            classify and route the issue accurately.
          </p>
        </div>

        {error && (
          <div
            className="complaint-form-error"
            role="alert"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="complaint-form-grid">
            <div className="complaint-field complaint-field-full">
              <label htmlFor="title">
                Complaint title
              </label>

              <input
                id="title"
                name="title"
                type="text"
                value={form.title}
                onChange={handleChange}
                placeholder="Example: Wi-Fi not working in Block A"
                maxLength={200}
                disabled={submitting}
              />

              {fieldErrors.title && (
                <p className="complaint-field-error">
                  {fieldErrors.title}
                </p>
              )}
            </div>

            <div className="complaint-field complaint-field-full">
              <div className="voice-description-header">
                <label htmlFor="description">
                  Description
                </label>

                {speechSupported && (
                  <span className="voice-supported-label">
                    Voice input available
                  </span>
                )}
              </div>

              <div
                className={`voice-input-panel ${
                  isListening
                    ? "voice-input-panel-active"
                    : ""
                }`}
              >
                <div className="voice-input-top">
                  <div>
                    <h3>
                      Speak your complaint
                    </h3>

                    <p>
                      You can describe the issue naturally.
                      The transcript will appear below for
                      you to review and edit.
                    </p>
                  </div>

                  <div className="voice-input-actions">
                    {!isListening ? (
                      <button
                        type="button"
                        className="voice-start-button"
                        onClick={startVoiceInput}
                        disabled={
                          submitting ||
                          !speechSupported
                        }
                      >
                        <span aria-hidden="true">
                          🎙️
                        </span>
                        Start voice
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="voice-stop-button"
                        onClick={stopVoiceInput}
                        disabled={submitting}
                      >
                        <span
                          className="voice-recording-dot"
                          aria-hidden="true"
                        />
                        Stop listening
                      </button>
                    )}
                  </div>
                </div>

                {!speechSupported && (
                  <p
                    className="voice-browser-warning"
                    role="status"
                  >
                    Voice input is not supported in this
                    browser. Use Chrome or Edge for voice
                    complaint submission.
                  </p>
                )}

                {isListening && (
                  <div
                    className="voice-listening-status"
                    role="status"
                    aria-live="polite"
                  >
                    <span
                      className="voice-pulse"
                      aria-hidden="true"
                    />

                    Listening... Speak clearly about the
                    problem.
                  </div>
                )}

                {voiceInterimText && (
                  <div className="voice-interim-text">
                    <span>Live transcript:</span>{" "}
                    {voiceInterimText}
                  </div>
                )}

                {form.description.trim() && (
                  <button
                    type="button"
                    className="voice-clear-button"
                    onClick={clearVoiceTranscript}
                    disabled={submitting}
                  >
                    Clear description
                  </button>
                )}
              </div>

              <textarea
                id="description"
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe the problem, when it started, and any useful details — or use voice input above."
                rows={7}
                disabled={submitting}
              />

              <div className="complaint-field-meta">
                <span>
                  Minimum 10 characters
                </span>

                <span>
                  {form.description.length} characters
                </span>
              </div>

              {speechError && (
                <p
                  className="voice-error"
                  role="alert"
                >
                  {speechError}
                </p>
              )}

              {fieldErrors.description && (
                <p className="complaint-field-error">
                  {fieldErrors.description}
                </p>
              )}
            </div>

            <div className="complaint-field">
              <label htmlFor="category">
                Category
              </label>

              <select
                id="category"
                name="category"
                value={form.category}
                onChange={handleChange}
                disabled={
                  loadingCategories || submitting
                }
              >
                <option value="">
                  {loadingCategories
                    ? "Loading categories..."
                    : "Select a category"}
                </option>

                {categories.map((category) => (
                  <option
                    key={category.id}
                    value={category.id}
                  >
                    {category.name}
                    {" — "}
                    {category.department_name}
                  </option>
                ))}
              </select>

              {fieldErrors.category && (
                <p className="complaint-field-error">
                  {fieldErrors.category}
                </p>
              )}

              {!loadingCategories &&
                categories.length === 0 && (
                  <p className="complaint-field-error">
                    No active categories are available.
                  </p>
                )}
            </div>

            <div className="complaint-field">
              <label htmlFor="location">
                Location
              </label>

              <input
                id="location"
                name="location"
                type="text"
                value={form.location}
                onChange={handleChange}
                placeholder="Example: Block A, Room 204"
                disabled={submitting}
              />

              {fieldErrors.location && (
                <p className="complaint-field-error">
                  {fieldErrors.location}
                </p>
              )}
            </div>

            <div className="complaint-form-section">
              <div>
                <h3>Complaint location</h3>

                <p>
                  You can enter coordinates manually or
                  select the exact point on the map.
                </p>
              </div>

              <ComplaintLocationPicker
                latitude={form.latitude}
                longitude={form.longitude}
                onLocationSelect={
                  handleMapLocationSelect
                }
                disabled={submitting}
              />

              <div className="complaint-coordinate-grid">
                <div className="complaint-field">
                  <label htmlFor="latitude">
                    Latitude
                  </label>

                  <input
                    id="latitude"
                    name="latitude"
                    type="number"
                    step="any"
                    value={form.latitude}
                    onChange={handleChange}
                    placeholder="16.521000"
                    disabled={submitting}
                  />

                  {fieldErrors.latitude && (
                    <p className="complaint-field-error">
                      {fieldErrors.latitude}
                    </p>
                  )}
                </div>

                <div className="complaint-field">
                  <label htmlFor="longitude">
                    Longitude
                  </label>

                  <input
                    id="longitude"
                    name="longitude"
                    type="number"
                    step="any"
                    value={form.longitude}
                    onChange={handleChange}
                    placeholder="80.667000"
                    disabled={submitting}
                  />

                  {fieldErrors.longitude && (
                    <p className="complaint-field-error">
                      {fieldErrors.longitude}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="complaint-form-footer">
            <Link
              to="/dashboard/complaints"
              className="complaint-cancel-action"
            >
              Cancel
            </Link>

            <button
              type="submit"
              className="complaint-submit-action"
              disabled={
                submitting ||
                loadingCategories ||
                categories.length === 0
              }
            >
              {submitting
                ? "Submitting & analyzing..."
                : "Submit complaint"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

export default ComplaintCreatePage;