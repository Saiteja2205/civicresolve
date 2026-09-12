import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

import "../styles/dashboard-pages.css";


function CitizenDashboard() {
  const { user } = useAuth();

  return (
    <section className="dashboard-page">
      <div className="dashboard-page-header">
        <div>
          <p className="dashboard-eyebrow">
            CITIZEN WORKSPACE
          </p>

          <h1>Good morning.</h1>

          <p>
            Welcome back, {user?.email}.
          </p>
        </div>

        <Link
          to="/dashboard/complaints/new"
          className="dashboard-primary-action"
        >
          Submit a complaint
        </Link>
      </div>

      <div className="dashboard-card-grid">
        <article className="dashboard-stat-card">
          <span className="dashboard-stat-label">
            My complaints
          </span>

          <strong className="dashboard-stat-value">
            —
          </strong>

          <span className="dashboard-stat-note">
            View your complaint history
          </span>
        </article>

        <article className="dashboard-stat-card">
          <span className="dashboard-stat-label">
            Active complaints
          </span>

          <strong className="dashboard-stat-value">
            —
          </strong>

          <span className="dashboard-stat-note">
            Complaints currently being handled
          </span>
        </article>

        <article className="dashboard-stat-card">
          <span className="dashboard-stat-label">
            Resolved
          </span>

          <strong className="dashboard-stat-value">
            —
          </strong>

          <span className="dashboard-stat-note">
            Successfully resolved complaints
          </span>
        </article>
      </div>

      <div className="dashboard-content-card">
        <div>
          <p className="dashboard-card-eyebrow">
            COMPLAINT TRACKING
          </p>

          <h2>
            Need to report an issue?
          </h2>

          <p>
            Submit a complaint and CivicResolve will
            analyze the issue, identify the appropriate
            department, assign an officer, and track
            the resolution process.
          </p>
        </div>

        <div className="dashboard-action-row">
          <Link
            to="/dashboard/complaints/new"
            className="dashboard-primary-action"
          >
            Submit a complaint
          </Link>

          <Link
            to="/dashboard/complaints"
            className="dashboard-secondary-action"
          >
            View my complaints
          </Link>
        </div>
      </div>
    </section>
  );
}

export default CitizenDashboard;