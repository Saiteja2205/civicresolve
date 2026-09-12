import { useAuth } from "../context/AuthContext.jsx";
import "../styles/dashboard-pages.css";

function AdminDashboard() {
  const { user } = useAuth();

  return (
    <section className="dashboard-page">
      <div className="dashboard-page-header">
        <div>
          <p className="dashboard-eyebrow">
            ADMINISTRATION
          </p>

          <h1>System overview</h1>

          <p>
            Signed in as {user?.email}.
          </p>
        </div>
      </div>

      <div className="dashboard-stat-grid">
        <div className="dashboard-stat-card">
          <span>Total complaints</span>
          <strong>—</strong>
          <small>System-wide analytics coming next</small>
        </div>

        <div className="dashboard-stat-card">
          <span>Departments</span>
          <strong>5</strong>
          <small>Configured in CivicResolve</small>
        </div>

        <div className="dashboard-stat-card">
          <span>Officers</span>
          <strong>—</strong>
          <small>Live workload coming next</small>
        </div>
      </div>

      <div className="dashboard-info-card">
        <p className="dashboard-eyebrow">
          ADMIN CONTROL CENTER
        </p>

        <h2>Monitor the entire grievance workflow.</h2>

        <p>
          The administrator workspace will provide complaint
          oversight, officer assignments, department management,
          SLA monitoring, and system-level analytics.
        </p>
      </div>
    </section>
  );
}

export default AdminDashboard;