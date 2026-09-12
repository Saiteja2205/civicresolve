import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import "./DashboardLayout.css";


function DashboardLayout() {
  const { user, logout } = useAuth();

  const roleLabel = {
    USER: "Citizen",
    OFFICER: "Officer",
    ADMIN: "Administrator",
  };


  function getNavClass({
    isActive,
  }) {
    return `dashboard-nav-link ${
      isActive ? "active" : ""
    }`;
  }


  return (
    <div className="dashboard-shell">
      <header className="dashboard-topbar">
        <div className="dashboard-brand">
          <div className="dashboard-brand-mark">
            C
          </div>

          <div>
            <div className="dashboard-brand-name">
              CivicResolve
            </div>

            <div className="dashboard-brand-tagline">
              Intelligent grievance resolution
            </div>
          </div>
        </div>


        <div className="dashboard-user-area">
          <div className="dashboard-user-info">
            <strong>
              {user?.email}
            </strong>

            <span>
              {roleLabel[user?.role] ??
                user?.role}
            </span>
          </div>

          <button
            type="button"
            className="dashboard-logout"
            onClick={logout}
          >
            Sign out
          </button>
        </div>
      </header>


      <div className="dashboard-body">
        <aside className="dashboard-sidebar">
          <div className="sidebar-section-label">
            Workspace
          </div>


          <nav className="dashboard-nav">
            <NavLink
              to="/dashboard"
              end
              className={getNavClass}
            >
              <span>
                Overview
              </span>
            </NavLink>
            <NavLink
              to="/dashboard/activity"
              className={getNavClass}
            >
              <span>
                Activity
              </span>
            </NavLink>

            <NavLink
              to="/dashboard/profile"
              className={getNavClass}
            >
              <span>
                Profile
              </span>
            </NavLink>

            {user?.role === "USER" && (
              <>
                <NavLink
                  to="/dashboard/complaints"
                  className={getNavClass}
                >
                  <span>
                    My complaints
                  </span>
                </NavLink>

                <NavLink
                  to="/dashboard/complaints/new"
                  className={getNavClass}
                >
                  <span>
                    New complaint
                  </span>
                </NavLink>
              </>
            )}


            {user?.role === "OFFICER" && (
              <NavLink
                to="/dashboard/assigned"
                className={getNavClass}
              >
                <span>
                  Assigned complaints
                </span>
              </NavLink>
            )}


            {user?.role === "ADMIN" && (
              <>
                <NavLink
                  to="/dashboard/complaints"
                  className={getNavClass}
                >
                  <span>
                    All complaints
                  </span>
                </NavLink>

                <NavLink
                  to="/dashboard/sla"
                  className={getNavClass}
                >
                  <span>
                    SLA monitoring
                  </span>
                </NavLink>

                <NavLink
                  to="/dashboard/analytics"
                  className={getNavClass}
                >
                  <span>
                    Analytics
                  </span>
                </NavLink>
              </>
            )}
          </nav>


          <div className="sidebar-footer">
            <div className="sidebar-security-dot" />

            <div>
              <strong>
                Secure session
              </strong>

              <span>
                JWT authenticated
              </span>
            </div>
          </div>
        </aside>


        <main className="dashboard-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}


export default DashboardLayout;