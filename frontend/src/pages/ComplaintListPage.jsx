import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getComplaints } from "../services/complaintService";
import "../styles/complaints.css";

function ComplaintListPage() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const isOfficer = user?.role === "OFFICER";
  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    const loadComplaints = async () => {
      setIsLoading(true);
      setError("");

      try {
        const data = await getComplaints();

        const complaintList = Array.isArray(data)
          ? data
          : Array.isArray(data?.results)
            ? data.results
            : [];

        setComplaints(complaintList);
      } catch (requestError) {
        console.error(
          "Failed to load complaints:",
          requestError,
        );

        setError(
          requestError.response?.data?.detail ||
            "Unable to load complaints. Please try again.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadComplaints();
  }, []);

  const stats = useMemo(() => {
    const total = complaints.length;

    const active = complaints.filter(
      (complaint) =>
        !["RESOLVED", "CLOSED", "REJECTED"].includes(
          complaint.status,
        ),
    ).length;

    const resolved = complaints.filter(
      (complaint) =>
        ["RESOLVED", "CLOSED"].includes(
          complaint.status,
        ),
    ).length;

    const urgent = complaints.filter(
      (complaint) =>
        ["HIGH", "CRITICAL"].includes(
          complaint.priority,
        ),
    ).length;

    return {
      total,
      active,
      resolved,
      urgent,
    };
  }, [complaints]);

  const pageTitle = isAdmin
    ? "All complaints"
    : isOfficer
      ? "Assigned complaints"
      : "My complaints";

  const pageDescription = isAdmin
    ? "Monitor grievances across the entire CivicResolve system."
    : isOfficer
      ? "Review complaints currently assigned to you."
      : "Track every grievance you have submitted.";

  const detailBasePath = isOfficer
    ? "/dashboard/assigned"
    : "/dashboard/complaints";

  if (isLoading) {
    return (
      <section className="complaints-page">
        <div className="complaints-page-header">
          <div>
            <p className="dashboard-eyebrow">
              COMPLAINT TRACKING
            </p>

            <h1>{pageTitle}</h1>

            <p>{pageDescription}</p>
          </div>
        </div>

        <div className="complaints-loading">
          <div className="complaints-spinner" />
          <p>Loading complaints...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="complaints-page">
        <div className="complaints-page-header">
          <div>
            <p className="dashboard-eyebrow">
              COMPLAINT TRACKING
            </p>

            <h1>{pageTitle}</h1>

            <p>{pageDescription}</p>
          </div>
        </div>

        <div className="complaints-error">
          <strong>Unable to load complaints</strong>

          <p>{error}</p>

          <button
            type="button"
            onClick={() => window.location.reload()}
          >
            Try again
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="complaints-page">
      <div className="complaints-page-header">
        <div>
          <p className="dashboard-eyebrow">
            COMPLAINT TRACKING
          </p>

          <h1>{pageTitle}</h1>

          <p>{pageDescription}</p>
        </div>
      </div>

      <div className="complaint-stats-grid">
        <div className="complaint-stat-card">
          <span>Total</span>
          <strong>{stats.total}</strong>
          <small>Complaints visible to you</small>
        </div>

        <div className="complaint-stat-card">
          <span>Active</span>
          <strong>{stats.active}</strong>
          <small>Still being processed</small>
        </div>

        <div className="complaint-stat-card">
          <span>Resolved</span>
          <strong>{stats.resolved}</strong>
          <small>Resolved or closed</small>
        </div>

        <div className="complaint-stat-card">
          <span>High priority</span>
          <strong>{stats.urgent}</strong>
          <small>High or critical priority</small>
        </div>
      </div>

      {complaints.length === 0 ? (
        <div className="complaints-empty">
          <div className="complaints-empty-icon">C</div>

          <h2>No complaints yet</h2>

          <p>
            {isOfficer
              ? "There are currently no complaints assigned to you."
              : isAdmin
                ? "There are currently no complaints in the system."
                : "You have not submitted any complaints yet."}
          </p>
        </div>
      ) : (
        <div className="complaints-table-card">
          <div className="complaints-table-header">
            <div>
              <h2>Complaint records</h2>

              <span>
                {complaints.length}{" "}
                {complaints.length === 1
                  ? "complaint"
                  : "complaints"}
              </span>
            </div>
          </div>

          <div className="complaints-table-wrapper">
            <table className="complaints-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Complaint</th>
                  <th>Department</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {complaints.map((complaint) => (
                  <tr key={complaint.id}>
                    <td>
                      <strong className="complaint-ticket">
                        {complaint.ticket_number}
                      </strong>
                    </td>

                    <td>
                      <div className="complaint-title-cell">
                        <strong>{complaint.title}</strong>

                        <span>
                          {truncateText(
                            complaint.description,
                            80,
                          )}
                        </span>
                      </div>
                    </td>

                    <td>
                      <span className="complaint-department">
                        {complaint.department_name || "—"}
                      </span>

                      <small>
                        {complaint.category_name || "—"}
                      </small>
                    </td>

                    <td>
                      <ComplaintPriorityBadge
                        priority={complaint.priority}
                      />
                    </td>

                    <td>
                      <ComplaintStatusBadge
                        status={complaint.status}
                      />
                    </td>

                    <td>
                      <span className="complaint-date">
                        {formatDate(complaint.created_at)}
                      </span>
                    </td>

                    <td>
                      <Link
                        to={`${detailBasePath}/${complaint.id}`}
                        className="complaint-view-link"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

function truncateText(text, maxLength) {
  if (!text) {
    return "";
  }

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength)}...`;
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default ComplaintListPage;