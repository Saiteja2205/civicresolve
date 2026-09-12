import { useAuth } from "../context/AuthContext.jsx";
import "../styles/dashboard-pages.css";

function OfficerDashboard() {
  const { user } = useAuth();

  return (
    <section className="dashboard-page">
      <div className="dashboard-page-header">
        <div>
          <p className="dashboard-eyebrow">
            OFFICER WORKSPACE
          </p>

          <h1>Officer overview</h1>

          <p>
            Department: {user?.department_name ?? "Not assigned"}
          </p>
        </div>
      </div>

      <div className="dashboard-stat-grid">
        <div className="dashboard-stat-card">
          <span>Assigned complaints</span>
          <strong>—</strong>
          <small>Live assignments coming next</small>
        </div>

        <div className="dashboard-stat-card">
          <span>In progress</span>
          <strong>—</strong>
          <small>Work currently underway</small>
        </div>

        <div className="dashboard-stat-card">
          <span>SLA attention</span>
          <strong>—</strong>
          <small>SLA monitoring coming next</small>
        </div>
      </div>

      <div className="dashboard-info-card">
        <p className="dashboard-eyebrow">OFFICER TOOLS</p>

        <h2>Resolve assigned grievances efficiently.</h2>

        <p>
          Your officer workspace will show assigned complaints,
          priority, SLA deadlines, complaint history, and status
          actions.
        </p>
      </div>
    </section>
  );
}

export default OfficerDashboard;