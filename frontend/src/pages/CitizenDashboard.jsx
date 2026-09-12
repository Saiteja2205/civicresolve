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
          to="/dashboard/complaints"
          className="dashboard-primary-action"
        >
          View my complaints
        </Link>
      </div>

      <div className="dashboard-stat-grid">
        <div className="dashboard-stat-card">
          <span>My complaints</span>
          <strong>Live</strong>
          <small>
            Open the complaints workspace
          </small>
        </div>

        <div className="dashboard-stat-card">
          <span>Tracking</span>
          <strong>Live</strong>
          <small>
            View complaint status history
          </small>
        </div>

        <div className="dashboard-stat-card">
          <span>Resolution</span>
          <strong>Live</strong>
          <small>
            Follow your grievance journey
          </small>
        </div>
      </div>

      <div className="dashboard-info-card">
        <p className="dashboard-eyebrow">
          COMPLAINT TRACKING
        </p>

        <h2>
          Your grievance journey is now visible.
        </h2>

        <p>
          Open My complaints to see your submitted
          grievances, current status, priority,
          department routing, and complete status history.
        </p>
      </div>
    </section>
  );
}

export default CitizenDashboard;