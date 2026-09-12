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

        <button type="button" className="dashboard-primary-action">
          Submit a complaint
        </button>
      </div>

      <div className="dashboard-stat-grid">
        <div className="dashboard-stat-card">
          <span>My complaints</span>
          <strong>—</strong>
          <small>Coming in the next phase</small>
        </div>

        <div className="dashboard-stat-card">
          <span>In progress</span>
          <strong>—</strong>
          <small>Live complaint tracking</small>
        </div>

        <div className="dashboard-stat-card">
          <span>Resolved</span>
          <strong>—</strong>
          <small>Resolution history</small>
        </div>
      </div>

      <div className="dashboard-info-card">
        <p className="dashboard-eyebrow">CIVICRESOLVE</p>

        <h2>Everything about your grievance, in one place.</h2>

        <p>
          Submit an issue, track its progress, and see how it
          moves through analysis, department routing, officer
          assignment, and resolution.
        </p>
      </div>
    </section>
  );
}

export default CitizenDashboard;