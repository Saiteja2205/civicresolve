import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

import {
  acknowledgeComplaint,
  getComplaint,
  getComplaintHistory,
  resolveComplaint,
  startComplaint,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/complaints.css";
import "../styles/complaint-actions.css";


function getBackPath(role) {
  if (role === "OFFICER") {
    return "/dashboard/assigned";
  }

  return "/dashboard/complaints";
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString([], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function getActionLabel(status) {
  if (status === "ASSIGNED") {
    return "Acknowledge complaint";
  }

  if (status === "ACKNOWLEDGED") {
    return "Start work";
  }

  if (status === "IN_PROGRESS") {
    return "Resolve complaint";
  }

  return "";
}


function getActionDescription(status) {
  if (status === "ASSIGNED") {
    return "Confirm that you have received this complaint.";
  }

  if (status === "ACKNOWLEDGED") {
    return "Start working on this complaint.";
  }

  if (status === "IN_PROGRESS") {
    return "Mark this complaint as resolved.";
  }

  return "";
}


function getApiErrorMessage(requestError) {
  const responseData =
    requestError?.response?.data;

  if (typeof responseData === "string") {
    return responseData;
  }

  if (responseData?.detail) {
    return responseData.detail;
  }

  if (
    responseData &&
    typeof responseData === "object"
  ) {
    return Object.values(responseData)
      .flat()
      .join(" ");
  }

  return "Unable to update the complaint.";
}


function ComplaintDetailPage() {
  const { complaintId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const [comment, setComment] = useState("");
  const [showActionBox, setShowActionBox] =
    useState(false);


  async function loadComplaint() {
    try {
      setLoading(true);
      setError("");

      const [complaintData, historyData] =
        await Promise.all([
          getComplaint(complaintId),
          getComplaintHistory(complaintId),
        ]);

      setComplaint(complaintData);

      setHistory(
        Array.isArray(historyData)
          ? historyData
          : historyData?.results || [],
      );
    } catch (requestError) {
      console.error(
        "Failed to load complaint:",
        requestError,
      );

      setError(
        "Unable to load this complaint.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadComplaint();
  }, [complaintId]);


  async function handleAction() {
    if (!complaint?.id) {
      setActionError(
        "Complaint ID is missing. Please reload the page.",
      );
      return;
    }

    setActionLoading(true);
    setActionError("");

    try {
      if (complaint.status === "ASSIGNED") {
        await acknowledgeComplaint(
          complaint.id,
          comment,
        );
      } else if (
        complaint.status === "ACKNOWLEDGED"
      ) {
        await startComplaint(
          complaint.id,
          comment,
        );
      } else if (
        complaint.status === "IN_PROGRESS"
      ) {
        await resolveComplaint(
          complaint.id,
          comment,
        );
      } else {
        return;
      }

      /*
       * IMPORTANT:
       *
       * The action endpoints return a small status
       * response, not the complete complaint object.
       *
       * Therefore we must reload the complete complaint
       * instead of doing:
       *
       * setComplaint(response)
       */

      const [updatedComplaint, updatedHistory] =
        await Promise.all([
          getComplaint(complaint.id),
          getComplaintHistory(complaint.id),
        ]);

      setComplaint(updatedComplaint);

      setHistory(
        Array.isArray(updatedHistory)
          ? updatedHistory
          : updatedHistory?.results || [],
      );

      setComment("");
      setShowActionBox(false);
    } catch (requestError) {
      console.error(
        "Complaint action failed:",
        requestError,
      );

      setActionError(
        getApiErrorMessage(requestError),
      );
    } finally {
      setActionLoading(false);
    }
  }


  if (loading) {
    return (
      <section className="complaint-detail-page">
        <div className="complaint-detail-loading">
          Loading complaint...
        </div>
      </section>
    );
  }


  if (error || !complaint) {
    return (
      <section className="complaint-detail-page">
        <div className="complaint-detail-error">
          <h2>Complaint unavailable</h2>

          <p>
            {error ||
              "The requested complaint could not be found."}
          </p>

          <Link
            to={getBackPath(user?.role)}
            className="complaint-back-link"
          >
            Back to complaints
          </Link>
        </div>
      </section>
    );
  }


  const isOfficer =
    user?.role === "OFFICER";

  const actionLabel =
    getActionLabel(complaint.status);

  const actionDescription =
    getActionDescription(
      complaint.status,
    );

  const canTakeAction =
    isOfficer &&
    [
      "ASSIGNED",
      "ACKNOWLEDGED",
      "IN_PROGRESS",
    ].includes(complaint.status);


  return (
    <section className="complaint-detail-page">
      <div className="complaint-detail-topbar">
        <Link
          to={getBackPath(user?.role)}
          className="complaint-back-link"
        >
          ← Back
        </Link>
      </div>


      <div className="complaint-detail-header">
        <div>
          <p className="complaint-detail-eyebrow">
            COMPLAINT
          </p>

          <div className="complaint-ticket-large">
            {complaint.ticket_number}
          </div>

          <h1>{complaint.title}</h1>

          <p className="complaint-detail-submitted">
            Submitted{" "}
            {formatDate(
              complaint.created_at,
            )}
          </p>
        </div>

        <div className="complaint-detail-badges">
          <ComplaintStatusBadge
            status={complaint.status}
          />

          <ComplaintPriorityBadge
            priority={complaint.priority}
          />
        </div>
      </div>


      {canTakeAction && (
        <section className="complaint-action-card">
          <div className="complaint-action-content">
            <p className="complaint-action-eyebrow">
              OFFICER ACTION
            </p>

            <h2>{actionLabel}</h2>

            <p>{actionDescription}</p>
          </div>


          {!showActionBox ? (
            <button
              type="button"
              className="complaint-action-primary"
              onClick={() =>
                setShowActionBox(true)
              }
            >
              {actionLabel}
            </button>
          ) : (
            <div className="complaint-action-box">
              <label htmlFor="action-comment">
                Comment
                <span>Optional</span>
              </label>

              <textarea
                id="action-comment"
                value={comment}
                onChange={(event) =>
                  setComment(event.target.value)
                }
                placeholder={
                  complaint.status ===
                  "IN_PROGRESS"
                    ? "Example: The network issue has been fixed and connectivity has been restored."
                    : "Add an optional note about this action."
                }
                rows={4}
                disabled={actionLoading}
              />


              {actionError && (
                <p
                  className="complaint-action-error"
                  role="alert"
                >
                  {actionError}
                </p>
              )}


              <div className="complaint-action-buttons">
                <button
                  type="button"
                  className="complaint-action-cancel"
                  onClick={() => {
                    setShowActionBox(false);
                    setComment("");
                    setActionError("");
                  }}
                  disabled={actionLoading}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="complaint-action-primary"
                  onClick={handleAction}
                  disabled={actionLoading}
                >
                  {actionLoading
                    ? "Updating..."
                    : `Confirm: ${actionLabel}`}
                </button>
              </div>
            </div>
          )}
        </section>
      )}


      <div className="complaint-detail-grid">
        <div className="complaint-detail-main">

          <article className="complaint-detail-card">
            <div className="complaint-detail-card-header">
              <h2>Description</h2>
            </div>

            <div className="complaint-description">
              {complaint.description}
            </div>
          </article>


          <article className="complaint-detail-card">
            <div className="complaint-detail-card-header">
              <h2>Status history</h2>

              <span>
                {history.length} events
              </span>
            </div>


            {history.length === 0 ? (
              <div className="complaint-history-empty">
                No history available.
              </div>
            ) : (
              <div className="complaint-timeline">
                {history.map(
                  (item, index) => (
                    <div
                      className="complaint-timeline-item"
                      key={
                        item.id ||
                        `${item.created_at}-${index}`
                      }
                    >
                      <div className="complaint-timeline-marker" />

                      <div className="complaint-timeline-content">
                        <div className="complaint-timeline-header">
                          <strong>
                            {item.new_status}
                          </strong>

                          <span>
                            {formatDate(
                              item.created_at,
                            )}
                          </span>
                        </div>

                        <p>
                          {item.comment ||
                            "Status updated."}
                        </p>

                        {item.changed_by && (
                          <small>
                            Updated by{" "}
                            {item.changed_by}
                          </small>
                        )}
                      </div>
                    </div>
                  ),
                )}
              </div>
            )}
          </article>

        </div>


        <aside className="complaint-detail-sidebar">

          <article className="complaint-detail-card">
            <div className="complaint-detail-card-header">
              <h2>Complaint information</h2>
            </div>

            <dl className="complaint-info-list">

              <div>
                <dt>Category</dt>
                <dd>
                  {complaint.category_name ||
                    "—"}
                </dd>
              </div>

              <div>
                <dt>Department</dt>
                <dd>
                  {complaint.department_name ||
                    "—"}
                </dd>
              </div>

              <div>
                <dt>Priority</dt>
                <dd>
                  <ComplaintPriorityBadge
                    priority={
                      complaint.priority
                    }
                  />
                </dd>
              </div>

              <div>
                <dt>Location</dt>
                <dd>
                  {complaint.location ||
                    "Not provided"}
                </dd>
              </div>

              <div>
                <dt>Latitude</dt>
                <dd>
                  {complaint.latitude ??
                    "—"}
                </dd>
              </div>

              <div>
                <dt>Longitude</dt>
                <dd>
                  {complaint.longitude ??
                    "—"}
                </dd>
              </div>

              <div>
                <dt>Last updated</dt>
                <dd>
                  {formatDate(
                    complaint.updated_at,
                  )}
                </dd>
              </div>

            </dl>
          </article>

        </aside>
      </div>


      {complaint.status === "RESOLVED" && (
        <div className="complaint-resolution-notice">
          <strong>Complaint resolved</strong>

          <span>
            This complaint has been marked as resolved.
          </span>
        </div>
      )}


      {complaint.status === "CLOSED" && (
        <div className="complaint-resolution-notice">
          <strong>Complaint closed</strong>

          <span>
            This complaint has been closed by an
            administrator.
          </span>
        </div>
      )}


      {complaint.status === "ESCALATED" && (
        <div className="complaint-escalation-notice">
          <strong>SLA escalation</strong>

          <span>
            This complaint has exceeded its resolution
            SLA and requires attention.
          </span>
        </div>
      )}
    </section>
  );
}

export default ComplaintDetailPage;