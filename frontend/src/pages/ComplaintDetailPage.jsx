import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import {
  getComplaint,
  getComplaintHistory,
} from "../services/complaintService";
import "../styles/complaints.css";

function ComplaintDetailPage() {
  const { complaintId } = useParams();
  const { user } = useAuth();

  const [complaint, setComplaint] = useState(null);
  const [history, setHistory] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const backPath =
    user?.role === "OFFICER"
      ? "/dashboard/assigned"
      : "/dashboard/complaints";

  useEffect(() => {
    const loadComplaint = async () => {
      setIsLoading(true);
      setError("");

      try {
        const [complaintData, historyData] =
          await Promise.all([
            getComplaint(complaintId),
            getComplaintHistory(complaintId),
          ]);

        setComplaint(complaintData);

        setHistory(
          Array.isArray(historyData)
            ? historyData
            : [],
        );
      } catch (requestError) {
        console.error(
          "Failed to load complaint:",
          requestError,
        );

        setError(
          requestError.response?.data?.detail ||
            "Unable to load this complaint.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadComplaint();
  }, [complaintId]);

  if (isLoading) {
    return (
      <section className="complaint-detail-page">
        <div className="complaints-loading">
          <div className="complaints-spinner" />
          <p>Loading complaint...</p>
        </div>
      </section>
    );
  }

  if (error || !complaint) {
    return (
      <section className="complaint-detail-page">
        <Link
          to={backPath}
          className="complaint-back-link"
        >
          ← Back to complaints
        </Link>

        <div className="complaints-error">
          <strong>Complaint unavailable</strong>

          <p>
            {error || "Complaint not found."}
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="complaint-detail-page">
      <Link
        to={backPath}
        className="complaint-back-link"
      >
        ← Back to complaints
      </Link>

      <div className="complaint-detail-header">
        <div>
          <p className="dashboard-eyebrow">
            COMPLAINT DETAILS
          </p>

          <div className="complaint-ticket-large">
            {complaint.ticket_number}
          </div>

          <h1>{complaint.title}</h1>

          <p>
            Submitted on{" "}
            {formatDateTime(complaint.created_at)}
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

      <div className="complaint-detail-grid">
        <div className="complaint-detail-main">
          <div className="complaint-detail-card">
            <div className="complaint-card-heading">
              <p className="dashboard-eyebrow">
                DESCRIPTION
              </p>

              <h2>Issue reported</h2>
            </div>

            <p className="complaint-description">
              {complaint.description}
            </p>
          </div>

          <div className="complaint-detail-card">
            <div className="complaint-card-heading">
              <p className="dashboard-eyebrow">
                STATUS HISTORY
              </p>

              <h2>Complaint journey</h2>
            </div>

            {history.length === 0 ? (
              <p className="complaint-no-history">
                No history is available yet.
              </p>
            ) : (
              <div className="complaint-timeline">
                {history.map((entry) => (
                  <div
                    className="complaint-timeline-item"
                    key={entry.id}
                  >
                    <div className="complaint-timeline-marker" />

                    <div className="complaint-timeline-content">
                      <div className="complaint-timeline-top">
                        <strong>
                          {formatStatus(
                            entry.new_status,
                          )}
                        </strong>

                        <span>
                          {formatDateTime(
                            entry.created_at,
                          )}
                        </span>
                      </div>

                      {entry.comment && (
                        <p>{entry.comment}</p>
                      )}

                      {entry.changed_by_email && (
                        <small>
                          Updated by{" "}
                          {entry.changed_by_email}
                        </small>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <aside className="complaint-detail-sidebar">
          <div className="complaint-detail-card">
            <div className="complaint-card-heading">
              <p className="dashboard-eyebrow">
                ROUTING
              </p>

              <h2>Assignment information</h2>
            </div>

            <DetailRow
              label="Department"
              value={
                complaint.department_name ||
                "Not assigned"
              }
            />

            <DetailRow
              label="Category"
              value={
                complaint.category_name ||
                "Not classified"
              }
            />

            <DetailRow
              label="Location"
              value={
                complaint.location ||
                "Not provided"
              }
            />
          </div>

          <div className="complaint-detail-card">
            <div className="complaint-card-heading">
              <p className="dashboard-eyebrow">
                TIMELINE
              </p>

              <h2>Important dates</h2>
            </div>

            <DetailRow
              label="Submitted"
              value={formatDateTime(
                complaint.created_at,
              )}
            />

            <DetailRow
              label="Last updated"
              value={formatDateTime(
                complaint.updated_at,
              )}
            />

            <DetailRow
              label="Resolved"
              value={
                complaint.resolved_at
                  ? formatDateTime(
                      complaint.resolved_at,
                    )
                  : "Not resolved"
              }
            />

            <DetailRow
              label="Closed"
              value={
                complaint.closed_at
                  ? formatDateTime(
                      complaint.closed_at,
                    )
                  : "Not closed"
              }
            />
          </div>
        </aside>
      </div>
    </section>
  );
}

function DetailRow({ label, value }) {
  return (
    <div className="complaint-detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatStatus(status) {
  const labels = {
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

  return labels[status] ?? status;
}

function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default ComplaintDetailPage;