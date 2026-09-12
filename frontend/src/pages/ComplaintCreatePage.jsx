import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  createComplaint,
  getCategories,
} from "../services/complaintService.js";

import "../styles/complaint-form.css";

function ComplaintCreatePage() {
  const navigate = useNavigate();

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
        console.error(
          "Failed to load categories:",
          requestError,
        );

        setError(
          "Unable to load complaint categories. Please try again.",
        );
      } finally {
        setLoadingCategories(false);
      }
    }

    loadCategories();
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
              <label htmlFor="description">
                Description
              </label>

              <textarea
                id="description"
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe the problem, when it started, and any useful details."
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
                <h3>Optional location coordinates</h3>

                <p>
                  These can be used later for map-based
                  complaint visualization.
                </p>
              </div>

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
                    placeholder="17.3850"
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
                    placeholder="78.4867"
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