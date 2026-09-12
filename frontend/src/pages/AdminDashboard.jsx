import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import {
  getComplaints,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/admin-dashboard.css";


function getComplaintList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


function AdminDashboard() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const data = await getComplaints();

      setComplaints(
        getComplaintList(data),
      );
    } catch (requestError) {
      console.error(
        "Failed to load admin dashboard:",
        requestError,
      );

      setError(
        "Unable to load dashboard data. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const statistics = useMemo(() => {
    const total = complaints.length;

    const active = complaints.filter(
      (complaint) =>
        ![
          "RESOLVED",
          "CLOSED",
          "REJECTED",
        ].includes(complaint.status),
    ).length;

    const resolved = complaints.filter(
      (complaint) =>
        complaint.status === "RESOLVED" ||
        complaint.status === "CLOSED",
    ).length;

    const escalated = complaints.filter(
      (complaint) =>
        complaint.status === "ESCALATED",
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
      escalated,
      highPriority,
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
    <section className="admin-dashboard">
      <header className="admin-dashboard-header">
        <div>
          <p className="admin-dashboard-eyebrow">
            ADMINISTRATOR WORKSPACE
          </p>

          <h1>System overview</h1>

          <p>
            Monitor complaints, resolution progress,
            priorities, and escalations from one place.
          </p>
        </div>

        <div className="admin-dashboard-header-actions">
          <button
            type="button"
            className="admin-refresh-button"
            onClick={loadDashboard}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>

          <Link
            to="/dashboard/complaints"
            className="admin-primary-button"
          >
            View all complaints
          </Link>
          <Link
            to="/dashboard/analytics"
            className="admin-primary-button"
          >
            Analytics
          </Link>
          <Link
            to="/dashboard/sla"
            className="admin-primary-button"
          >
            SLA monitoring
          </Link>
        </div>
      </header>

      <div className="admin-welcome-strip">
        <div>
          <span>Signed in as</span>

          <strong>
            {user?.email || "Administrator"}
          </strong>
        </div>

        <span className="admin-role-pill">
          ADMIN
        </span>
      </div>

      {error && (
        <div
          className="admin-dashboard-error"
          role="alert"
        >
          <span>{error}</span>

          <button
            type="button"
            onClick={loadDashboard}
          >
            Try again
          </button>
        </div>
      )}

      <div className="admin-stat-grid">
        <article className="admin-stat-card">
          <div className="admin-stat-top">
            <span>Total complaints</span>

            <span className="admin-stat-icon">
              ALL
            </span>
          </div>

          <strong>
            {loading ? "—" : statistics.total}
          </strong>

          <p>
            All complaints visible to administrators
          </p>
        </article>

        <article className="admin-stat-card">
          <div className="admin-stat-top">
            <span>Active</span>

            <span className="admin-stat-icon">
              ACT
            </span>
          </div>

          <strong>
            {loading ? "—" : statistics.active}
          </strong>

          <p>
            Complaints still requiring action
          </p>
        </article>

        <article className="admin-stat-card">
          <div className="admin-stat-top">
            <span>Resolved</span>

            <span className="admin-stat-icon">
              DONE
            </span>
          </div>

          <strong>
            {loading ? "—" : statistics.resolved}
          </strong>

          <p>
            Resolved or closed complaints
          </p>
        </article>

        <article className="admin-stat-card">
          <div className="admin-stat-top">
            <span>Escalated</span>

            <span className="admin-stat-icon">
              SLA
            </span>
          </div>

          <strong>
            {loading ? "—" : statistics.escalated}
          </strong>

          <p>
            Complaints requiring escalation attention
          </p>
        </article>

        <article className="admin-stat-card admin-stat-card-alert">
          <div className="admin-stat-top">
            <span>High priority</span>

            <span className="admin-stat-icon">
              HIGH
            </span>
          </div>

          <strong>
            {loading ? "—" : statistics.highPriority}
          </strong>

          <p>
            High and critical priority complaints
          </p>
        </article>
      </div>

      <section className="admin-dashboard-card">
        <div className="admin-section-header">
          <div>
            <p className="admin-section-eyebrow">
              RECENT ACTIVITY
            </p>

            <h2>Recent complaints</h2>

            <p>
              The latest complaints received by
              CivicResolve.
            </p>
          </div>

          <Link
            to="/dashboard/complaints"
            className="admin-section-link"
          >
            See all
          </Link>
        </div>

        {loading ? (
          <div className="admin-table-loading">
            <div />
            <div />
            <div />
            <div />
            <div />
          </div>
        ) : recentComplaints.length === 0 ? (
          <div className="admin-empty-state">
            <h3>No complaints yet</h3>

            <p>
              Complaints submitted through the citizen
              portal will appear here.
            </p>
          </div>
        ) : (
          <div className="admin-table-wrapper">
            <table className="admin-complaint-table">
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
                {recentComplaints.map(
                  (complaint) => (
                    <tr key={complaint.id}>
                      <td>
                        <span className="admin-ticket-number">
                          {complaint.ticket_number}
                        </span>
                      </td>

                      <td>
                        <div className="admin-complaint-title">
                          {complaint.title}
                        </div>

                        <div className="admin-complaint-category">
                          {complaint.category_name ||
                            "Uncategorized"}
                        </div>
                      </td>

                      <td>
                        {complaint.department_name ||
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
                        <span className="admin-date">
                          {formatDate(
                            complaint.created_at,
                          )}
                        </span>
                      </td>

                      <td>
                        <Link
                          to={`/dashboard/complaints/${complaint.id}`}
                          className="admin-view-link"
                        >
                          View
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

      <section className="admin-dashboard-card admin-system-card">
        <div>
          <p className="admin-section-eyebrow">
            CIVICRESOLVE PIPELINE
          </p>

          <h2>Current workflow</h2>

          <p>
            New complaints move through AI analysis,
            intelligent routing, officer assignment,
            and SLA tracking automatically.
          </p>
        </div>

        <div className="admin-workflow">
          <div className="admin-workflow-step">
            <span>01</span>
            <strong>Submitted</strong>
          </div>

          <div className="admin-workflow-arrow">
            →
          </div>

          <div className="admin-workflow-step">
            <span>02</span>
            <strong>AI analyzed</strong>
          </div>

          <div className="admin-workflow-arrow">
            →
          </div>

          <div className="admin-workflow-step">
            <span>03</span>
            <strong>Assigned</strong>
          </div>

          <div className="admin-workflow-arrow">
            →
          </div>

          <div className="admin-workflow-step">
            <span>04</span>
            <strong>Resolved</strong>
          </div>
        </div>
      </section>
    </section>
  );
}

export default AdminDashboard;