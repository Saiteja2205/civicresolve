import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { getComplaints } from "../services/complaintService.js";

import "../styles/dashboard-pages.css";


const CLOSED_STATUSES = [
  "RESOLVED",
  "CLOSED",
];

const INACTIVE_STATUSES = [
  "RESOLVED",
  "CLOSED",
  "REJECTED",
];

function getGreeting() {
  const hour = new Date().getHours();

  if (hour < 12) {
    return "Good morning";
  }

  if (hour < 17) {
    return "Good afternoon";
  }

  return "Good evening";
}

function getDisplayName(user) {
  if (user?.first_name) {
    return user.first_name;
  }

  if (user?.email) {
    return user.email.split("@")[0];
  }

  return "Citizen";
}

function getStatusLabel(status) {
  if (!status) {
    return "Unknown";
  }

  return status
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getStatusClass(status) {
  switch (status) {
    case "RESOLVED":
    case "CLOSED":
      return "citizen-status-success";

    case "ESCALATED":
    case "REJECTED":
      return "citizen-status-danger";

    case "NEEDS_INFORMATION":
      return "citizen-status-warning";

    case "IN_PROGRESS":
    case "ASSIGNED":
    case "ACKNOWLEDGED":
      return "citizen-status-active";

    case "REOPENED":
      return "citizen-status-reopened";

    case "AI_ANALYZING":
      return "citizen-status-ai";

    default:
      return "citizen-status-neutral";
  }
}

function getPriorityClass(priority) {
  if (priority === "HIGH" || priority === "CRITICAL") {
    return "citizen-priority-high";
  }

  if (priority === "MEDIUM") {
    return "citizen-priority-medium";
  }

  return "citizen-priority-low";
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

function normalizeComplaints(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}

function CitizenDashboard() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const loadComplaints = async () => {
      try {
        setIsLoading(true);
        setError("");

        const data = await getComplaints();

        if (isMounted) {
          setComplaints(normalizeComplaints(data));
        }
      } catch (requestError) {
        if (isMounted) {
          setError(
            requestError?.userMessage ||
              "Unable to load your complaints.",
          );
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadComplaints();

    return () => {
      isMounted = false;
    };
  }, []);

  const stats = useMemo(() => {
    const total = complaints.length;

    const resolved = complaints.filter((complaint) =>
      CLOSED_STATUSES.includes(complaint.status),
    ).length;

    const active = complaints.filter(
      (complaint) =>
        !INACTIVE_STATUSES.includes(complaint.status),
    ).length;

    const highPriority = complaints.filter(
      (complaint) =>
        complaint.priority === "HIGH" ||
        complaint.priority === "CRITICAL",
    ).length;

    return {
      total,
      active,
      resolved,
      highPriority,
    };
  }, [complaints]);

  const recentComplaints = useMemo(
    () =>
      [...complaints]
        .sort(
          (first, second) =>
            new Date(second.updated_at || second.created_at) -
            new Date(first.updated_at || first.created_at),
        )
        .slice(0, 5),
    [complaints],
  );

  const displayName = getDisplayName(user);

  return (
    <section className="dashboard-page citizen-dashboard">
      <div className="citizen-dashboard-header">
        <div className="citizen-dashboard-heading">
          <p className="dashboard-eyebrow">
            CITIZEN WORKSPACE
          </p>

          <h1>
            {getGreeting()}, {displayName}.
          </h1>

          <p>
            Track your complaints, follow updates, and stay
            informed about every resolution.
          </p>
        </div>

        <Link
          to="/dashboard/complaints/new"
          className="citizen-submit-button"
        >
          <span className="citizen-button-icon">+</span>
          Submit a complaint
          <span className="citizen-button-arrow">→</span>
        </Link>
      </div>

      <div className="citizen-stat-grid">
        <article className="citizen-stat-card">
          <div className="citizen-stat-top">
            <span className="citizen-stat-label">
              Total complaints
            </span>

            <span className="citizen-stat-icon citizen-stat-icon-neutral">
              #
            </span>
          </div>

          <strong>
            {isLoading ? "—" : stats.total}
          </strong>

          <span className="citizen-stat-note">
            All complaints submitted by you
          </span>

          <span className="citizen-stat-decoration" />
        </article>

        <article className="citizen-stat-card">
          <div className="citizen-stat-top">
            <span className="citizen-stat-label">
              Active
            </span>

            <span className="citizen-stat-icon citizen-stat-icon-blue">
              ↗
            </span>
          </div>

          <strong>
            {isLoading ? "—" : stats.active}
          </strong>

          <span className="citizen-stat-note">
            Currently moving through resolution
          </span>

          <span className="citizen-stat-decoration" />
        </article>

        <article className="citizen-stat-card">
          <div className="citizen-stat-top">
            <span className="citizen-stat-label">
              Resolved
            </span>

            <span className="citizen-stat-icon citizen-stat-icon-green">
              ✓
            </span>
          </div>

          <strong className="citizen-stat-value-green">
            {isLoading ? "—" : stats.resolved}
          </strong>

          <span className="citizen-stat-note">
            Complaints successfully resolved
          </span>

          <span className="citizen-stat-decoration" />
        </article>

        <article className="citizen-stat-card">
          <div className="citizen-stat-top">
            <span className="citizen-stat-label">
              High priority
            </span>

            <span className="citizen-stat-icon citizen-stat-icon-orange">
              !
            </span>
          </div>

          <strong className="citizen-stat-value-orange">
            {isLoading ? "—" : stats.highPriority}
          </strong>

          <span className="citizen-stat-note">
            High or critical priority complaints
          </span>

          <span className="citizen-stat-decoration" />
        </article>
      </div>

      <div className="citizen-dashboard-grid">
        <section className="citizen-complaints-card">
          <div className="citizen-card-header">
            <div>
              <p className="citizen-card-eyebrow">
                RECENT ACTIVITY
              </p>

              <h2>Your complaints</h2>

              <p>
                Follow the latest complaints and their current
                resolution status.
              </p>
            </div>

            {complaints.length > 0 && (
              <Link
                to="/dashboard/complaints"
                className="citizen-view-all"
              >
                View all
                <span>→</span>
              </Link>
            )}
          </div>

          {isLoading && (
            <div className="citizen-complaints-loading">
              <span className="citizen-loading-spinner" />

              <span>
                Loading your complaints...
              </span>
            </div>
          )}

          {!isLoading && error && (
            <div className="citizen-dashboard-error">
              <div className="citizen-error-icon">
                !
              </div>

              <h3>
                We couldn't load your complaints
              </h3>

              <p>{error}</p>

              <button
                type="button"
                onClick={() => window.location.reload()}
              >
                Try again
              </button>
            </div>
          )}

          {!isLoading &&
            !error &&
            recentComplaints.length === 0 && (
              <div className="citizen-empty-state">
                <div className="citizen-empty-icon">
                  +
                </div>

                <h3>
                  No complaints yet
                </h3>

                <p>
                  Your submitted complaints will appear here
                  so you can track them easily.
                </p>

                <Link
                  to="/dashboard/complaints/new"
                  className="citizen-empty-button"
                >
                  Report your first issue
                  <span>→</span>
                </Link>
              </div>
            )}

          {!isLoading &&
            !error &&
            recentComplaints.length > 0 && (
              <div className="citizen-complaint-list">
                {recentComplaints.map((complaint) => (
                  <Link
                    key={complaint.id}
                    to={`/dashboard/complaints/${complaint.id}`}
                    className="citizen-complaint-row"
                  >
                    <div className="citizen-complaint-main">
                      <div className="citizen-complaint-ticket">
                        {complaint.ticket_number ||
                          `CR-${String(complaint.id).padStart(5, "0")}`}
                      </div>

                      <h3>
                        {complaint.title ||
                          "Untitled complaint"}
                      </h3>

                      <div className="citizen-complaint-meta">
                        <span>
                          {complaint.department_name ||
                            complaint.category_name ||
                            "Department pending"}
                        </span>

                        <span className="citizen-meta-dot">
                          •
                        </span>

                        <span>
                          Updated{" "}
                          {formatDate(
                            complaint.updated_at ||
                              complaint.created_at,
                          )}
                        </span>
                      </div>
                    </div>

                    <div className="citizen-complaint-status">
                      <span
                        className={`citizen-status-badge ${getStatusClass(
                          complaint.status,
                        )}`}
                      >
                        {getStatusLabel(
                          complaint.status,
                        )}
                      </span>

                      {complaint.priority && (
                        <span
                          className={`citizen-priority-badge ${getPriorityClass(
                            complaint.priority,
                          )}`}
                        >
                          {complaint.priority}
                        </span>
                      )}
                    </div>

                    <span className="citizen-row-arrow">
                      →
                    </span>
                  </Link>
                ))}
              </div>
            )}
        </section>

        <aside className="citizen-side-column">
          <section className="citizen-quick-card">
            <div className="citizen-quick-icon">
              +
            </div>

            <p className="citizen-card-eyebrow">
              QUICK ACTION
            </p>

            <h2>
              Have a new issue?
            </h2>

            <p>
              Report a civic issue with text, voice, location,
              and supporting evidence.
            </p>

            <Link
              to="/dashboard/complaints/new"
              className="citizen-quick-button"
            >
              Report an issue
              <span>→</span>
            </Link>
          </section>

          <section className="citizen-how-card">
            <p className="citizen-card-eyebrow">
              HOW CIVICRESOLVE WORKS
            </p>

            <div className="citizen-how-list">
              <div className="citizen-how-item">
                <span>01</span>

                <div>
                  <strong>
                    Submit your issue
                  </strong>

                  <p>
                    Describe the problem with text, voice,
                    location, or evidence.
                  </p>
                </div>
              </div>

              <div className="citizen-how-item">
                <span>02</span>

                <div>
                  <strong>
                    AI-assisted analysis
                  </strong>

                  <p>
                    Your complaint is structured and routed
                    to the relevant workflow.
                  </p>
                </div>
              </div>

              <div className="citizen-how-item">
                <span>03</span>

                <div>
                  <strong>
                    Track resolution
                  </strong>

                  <p>
                    Follow status updates until the issue is
                    resolved.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </section>
  );
}

export default CitizenDashboard;