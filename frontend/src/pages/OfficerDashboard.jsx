import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import { getComplaints } from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/officer-dashboard.css";


function getComplaintList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


function OfficerDashboard() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadComplaints() {
    try {
      setLoading(true);
      setError("");

      const data = await getComplaints();

      setComplaints(
        getComplaintList(data),
      );
    } catch (requestError) {
      console.error(
        "Failed to load officer complaints:",
        requestError,
      );

      setError(
        "Unable to load assigned complaints.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadComplaints();
  }, []);

  const statistics = useMemo(() => {
    const assigned = complaints.length;

    const pending = complaints.filter(
      (complaint) =>
        complaint.status === "ASSIGNED" ||
        complaint.status === "ACKNOWLEDGED",
    ).length;

    const inProgress = complaints.filter(
      (complaint) =>
        complaint.status === "IN_PROGRESS",
    ).length;

    const resolved = complaints.filter(
      (complaint) =>
        complaint.status === "RESOLVED" ||
        complaint.status === "CLOSED",
    ).length;

    const urgent = complaints.filter(
      (complaint) =>
        complaint.priority === "HIGH" ||
        complaint.priority === "CRITICAL",
    ).length;

    return {
      assigned,
      pending,
      inProgress,
      resolved,
      urgent,
    };
  }, [complaints]);

  const recentComplaints = useMemo(() => {
    return [...complaints]
      .sort(
        (a, b) =>
          new Date(b.created_at) -
          new Date(a.created_at),
      )
      .slice(0, 8);
  }, [complaints]);

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

  return (
    <section className="officer-dashboard">
      <header className="officer-dashboard-header">
        <div>
          <p className="officer-dashboard-eyebrow">
            OFFICER WORKSPACE
          </p>

          <h1>Assigned complaints</h1>

          <p>
            Manage the complaints assigned to you and
            move them through the resolution workflow.
          </p>
        </div>

        <button
          type="button"
          className="officer-refresh-button"
          onClick={loadComplaints}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      <div className="officer-profile-strip">
        <div>
          <span>Officer</span>

          <strong>
            {user?.email || "Officer"}
          </strong>
        </div>

        <div>
          <span>Department</span>

          <strong>
            {user?.department_name || "—"}
          </strong>
        </div>

        <span className="officer-role-pill">
          OFFICER
        </span>
      </div>

      {error && (
        <div
          className="officer-dashboard-error"
          role="alert"
        >
          <span>{error}</span>

          <button
            type="button"
            onClick={loadComplaints}
          >
            Try again
          </button>
        </div>
      )}

      <div className="officer-stat-grid">
        <article className="officer-stat-card">
          <span>Assigned</span>

          <strong>
            {loading ? "—" : statistics.assigned}
          </strong>

          <p>Total active assignments</p>
        </article>

        <article className="officer-stat-card">
          <span>Pending</span>

          <strong>
            {loading ? "—" : statistics.pending}
          </strong>

          <p>Awaiting acknowledgement or action</p>
        </article>

        <article className="officer-stat-card">
          <span>In progress</span>

          <strong>
            {loading ? "—" : statistics.inProgress}
          </strong>

          <p>Currently being worked on</p>
        </article>

        <article className="officer-stat-card">
          <span>Resolved</span>

          <strong>
            {loading ? "—" : statistics.resolved}
          </strong>

          <p>Successfully resolved or closed</p>
        </article>

        <article className="officer-stat-card officer-stat-alert">
          <span>High priority</span>

          <strong>
            {loading ? "—" : statistics.urgent}
          </strong>

          <p>High and critical complaints</p>
        </article>
      </div>

      <section className="officer-dashboard-card">
        <div className="officer-section-header">
          <div>
            <p className="officer-section-eyebrow">
              WORK QUEUE
            </p>

            <h2>Your complaints</h2>

            <p>
              Complaints currently assigned to your
              officer account.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="officer-loading">
            <div />
            <div />
            <div />
            <div />
          </div>
        ) : recentComplaints.length === 0 ? (
          <div className="officer-empty-state">
            <h3>No assigned complaints</h3>

            <p>
              New complaints assigned to your department
              will appear here.
            </p>
          </div>
        ) : (
          <div className="officer-table-wrapper">
            <table className="officer-complaint-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Complaint</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {recentComplaints.map(
                  (complaint) => (
                    <tr key={complaint.id}>
                      <td>
                        <span className="officer-ticket">
                          {complaint.ticket_number}
                        </span>
                      </td>

                      <td>
                        <div className="officer-title">
                          {complaint.title}
                        </div>

                        <div className="officer-location">
                          {complaint.location || "No location"}
                        </div>
                      </td>

                      <td>
                        {complaint.category_name ||
                          "—"}
                      </td>

                      <td>
                        <ComplaintPriorityBadge
                          priority={
                            complaint.priority
                          }
                        />
                      </td>

                      <td>
                        <ComplaintStatusBadge
                          status={
                            complaint.status
                          }
                        />
                      </td>

                      <td>
                        {formatDate(
                          complaint.created_at,
                        )}
                      </td>

                      <td>
                        <Link
                          to={`/dashboard/assigned/${complaint.id}`}
                          className="officer-view-link"
                        >
                          Open
                        </Link>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}

export default OfficerDashboard;