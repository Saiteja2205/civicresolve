import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/notificationService.js";

import "./DashboardLayout.css";

function DashboardIcon({ name }) {
  const paths = {
    overview: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    activity: (
      <>
        <path d="M4 12h4l2-6 4 12 2-6h4" />
      </>
    ),
    profile: (
      <>
        <circle cx="12" cy="8" r="3.2" />
        <path d="M5 20c.8-3.2 3.1-5 7-5s6.2 1.8 7 5" />
      </>
    ),
    complaints: (
      <>
        <rect x="4" y="3" width="16" height="18" rx="2" />
        <path d="M8 8h8M8 12h8M8 16h5" />
      </>
    ),
    add: (
      <>
        <path d="M12 5v14M5 12h14" />
      </>
    ),
    assigned: (
      <>
        <path d="M5 5h14v14H5z" />
        <path d="m8 12 2.5 2.5L16 9" />
      </>
    ),
    sla: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    analytics: (
      <>
        <path d="M5 19V9M12 19V5M19 19v-7" />
        <path d="M3 19h18" />
      </>
    ),
    bell: (
      <>
        <path d="M18 8.5C18 5.46 15.31 3 12 3S6 5.46 6 8.5C6 15 3.5 16 3.5 17.5h17C20.5 16 18 15 18 8.5Z" />
        <path d="M9.5 20c.58.67 1.42 1 2.5 1s1.92-.33 2.5-1" />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 20 6v5c0 5-3.3 8.3-8 10-4.7-1.7-8-5-8-10V6l8-3Z" />
        <path d="m8.5 12 2.2 2.2 4.8-5" />
      </>
    ),
    logout: (
      <>
        <path d="M10 5H5v14h5" />
        <path d="m14 8 4 4-4 4M18 12H9" />
      </>
    ),
  };

  return (
    <svg
      className="dashboard-nav-icon"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <g
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {paths[name]}
      </g>
    </svg>
  );
}

function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationLoading, setNotificationLoading] = useState(true);
  const [notificationError, setNotificationError] = useState("");
  const [notificationOpen, setNotificationOpen] = useState(false);

  const notificationRef = useRef(null);

  const roleLabel = {
    USER: "Citizen",
    OFFICER: "Officer",
    ADMIN: "Administrator",
  };

  const role = roleLabel[user?.role] ?? user?.role ?? "User";

  const displayName =
    user?.first_name ||
    user?.email?.split("@")[0] ||
    "User";

  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  function getNavClass({ isActive }) {
    return `dashboard-nav-link ${isActive ? "active" : ""}`;
  }

  async function loadNotifications(showLoading = false) {
    if (showLoading) {
      setNotificationLoading(true);
    }

    try {
      setNotificationError("");

      const data = await getNotifications();

      setNotifications(data?.notifications ?? []);
      setUnreadCount(data?.unread_count ?? 0);
    } catch (error) {
      console.error("Failed to load notifications:", error);

      setNotificationError(
        error?.response?.data?.detail ||
          "Unable to load notifications.",
      );
    } finally {
      setNotificationLoading(false);
    }
  }

  useEffect(() => {
    loadNotifications(true);

    const interval = setInterval(() => {
      loadNotifications(false);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleOutsideClick(event) {
      if (
        notificationRef.current &&
        !notificationRef.current.contains(event.target)
      ) {
        setNotificationOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick,
      );
    };
  }, []);

  async function handleNotificationClick(notification) {
    try {
      if (!notification.is_read) {
        await markNotificationRead(notification.id);

        setNotifications((current) =>
          current.map((item) =>
            item.id === notification.id
              ? {
                  ...item,
                  is_read: true,
                }
              : item,
          ),
        );

        setUnreadCount((current) =>
          Math.max(0, current - 1),
        );
      }
    } catch (error) {
      console.error(
        "Failed to mark notification as read:",
        error,
      );
    }

    setNotificationOpen(false);

    if (notification.complaint) {
      navigate(
        `/dashboard/complaints/${notification.complaint}`,
      );
    }
  }

  async function handleMarkAllRead() {
    if (unreadCount === 0) {
      return;
    }

    try {
      await markAllNotificationsRead();

      setNotifications((current) =>
        current.map((item) => ({
          ...item,
          is_read: true,
        })),
      );

      setUnreadCount(0);
    } catch (error) {
      console.error(
        "Failed to mark all notifications as read:",
        error,
      );

      setNotificationError(
        error?.response?.data?.detail ||
          "Unable to mark notifications as read.",
      );
    }
  }

  function formatNotificationTime(timestamp) {
    if (!timestamp) {
      return "";
    }

    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
      return "";
    }

    const now = new Date();
    const difference = now.getTime() - date.getTime();
    const seconds = Math.floor(difference / 1000);

    if (seconds < 60) {
      return "Just now";
    }

    const minutes = Math.floor(seconds / 60);

    if (minutes < 60) {
      return `${minutes}m ago`;
    }

    const hours = Math.floor(minutes / 60);

    if (hours < 24) {
      return `${hours}h ago`;
    }

    const days = Math.floor(hours / 24);

    if (days < 7) {
      return `${days}d ago`;
    }

    return date.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
    });
  }

  function getNotificationIcon(type) {
    switch (type) {
      case "COMPLAINT_SUBMITTED":
        return "＋";
      case "COMPLAINT_ASSIGNED":
        return "↗";
      case "STATUS_CHANGED":
        return "↻";
      case "SLA_WARNING":
        return "⚠";
      case "SLA_BREACH":
        return "⏱";
      case "ESCALATED":
        return "↑";
      case "EVIDENCE_UPLOADED":
        return "▣";
      default:
        return "•";
    }
  }

  function getPageContext() {
    const path = location.pathname;

    if (path.includes("/complaints/new")) {
      return "New complaint";
    }

    if (path.includes("/complaints/")) {
      return "Complaint details";
    }

    if (path.includes("/complaints")) {
      return user?.role === "ADMIN"
        ? "All complaints"
        : "My complaints";
    }

    if (path.includes("/assigned")) {
      return "Assigned complaints";
    }

    if (path.includes("/analytics")) {
      return "Analytics";
    }

    if (path.includes("/sla")) {
      return "SLA monitoring";
    }

    if (path.includes("/activity")) {
      return "Activity";
    }

    if (path.includes("/profile")) {
      return "Profile";
    }

    return "Overview";
  }

  return (
    <div className="dashboard-shell">
      <header className="dashboard-topbar">
        <div className="dashboard-brand">
          <div className="dashboard-brand-mark">
            CR
          </div>

          <div className="dashboard-brand-copy">
            <div className="dashboard-brand-name">
              CivicResolve
            </div>

            <div className="dashboard-brand-tagline">
              Intelligent grievance resolution
            </div>
          </div>
        </div>

        <div className="dashboard-context">
          <span>
            {role} workspace
          </span>
          <strong>
            {getPageContext()}
          </strong>
        </div>

        <div className="dashboard-user-area">
          <div
            className="notification-center"
            ref={notificationRef}
          >
            <button
              type="button"
              className={`notification-bell ${
                notificationOpen
                  ? "notification-bell-open"
                  : ""
              }`}
              onClick={() =>
                setNotificationOpen(
                  (current) => !current,
                )
              }
              aria-label={
                unreadCount > 0
                  ? `${unreadCount} unread notifications`
                  : "Notifications"
              }
              aria-expanded={notificationOpen}
            >
              <DashboardIcon name="bell" />

              {unreadCount > 0 && (
                <span className="notification-badge">
                  {unreadCount > 99
                    ? "99+"
                    : unreadCount}
                </span>
              )}
            </button>

            {notificationOpen && (
              <div className="notification-dropdown">
                <div className="notification-dropdown-header">
                  <div>
                    <strong>
                      Notifications
                    </strong>

                    <span>
                      {unreadCount > 0
                        ? `${unreadCount} unread`
                        : "All caught up"}
                    </span>
                  </div>

                  {unreadCount > 0 && (
                    <button
                      type="button"
                      className="notification-mark-all"
                      onClick={handleMarkAllRead}
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                <div className="notification-list">
                  {notificationLoading ? (
                    <div className="notification-state">
                      <div className="notification-spinner" />

                      <span>
                        Loading notifications...
                      </span>
                    </div>
                  ) : notificationError ? (
                    <div className="notification-state notification-state-error">
                      <strong>
                        Couldn't load notifications
                      </strong>

                      <span>
                        {notificationError}
                      </span>

                      <button
                        type="button"
                        onClick={() =>
                          loadNotifications(true)
                        }
                      >
                        Try again
                      </button>
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="notification-state">
                      <div className="notification-empty-icon">
                        ✓
                      </div>

                      <strong>
                        No notifications
                      </strong>

                      <span>
                        New complaint activity will
                        appear here.
                      </span>
                    </div>
                  ) : (
                    notifications.map(
                      (notification) => (
                        <button
                          type="button"
                          key={notification.id}
                          className={`notification-item ${
                            notification.is_read
                              ? ""
                              : "notification-item-unread"
                          }`}
                          onClick={() =>
                            handleNotificationClick(
                              notification,
                            )
                          }
                        >
                          <div className="notification-item-icon">
                            {getNotificationIcon(
                              notification.type,
                            )}
                          </div>

                          <div className="notification-item-content">
                            <div className="notification-item-top">
                              <strong>
                                {notification.title}
                              </strong>

                              {!notification.is_read && (
                                <span className="notification-unread-dot" />
                              )}
                            </div>

                            <p>
                              {notification.message}
                            </p>

                            <div className="notification-item-meta">
                              {notification.complaint_ticket && (
                                <span>
                                  {
                                    notification.complaint_ticket
                                  }
                                </span>
                              )}

                              <time>
                                {formatNotificationTime(
                                  notification.created_at,
                                )}
                              </time>
                            </div>
                          </div>
                        </button>
                      ),
                    )
                  )}
                </div>

                <div className="notification-dropdown-footer">
                  <button
                    type="button"
                    onClick={() => {
                      setNotificationOpen(false);
                      navigate("/dashboard/activity");
                    }}
                  >
                    View all activity
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="dashboard-user-info">
            <strong>
              {displayName}
            </strong>

            <span>
              {role}
            </span>
          </div>

          <div className="dashboard-user-avatar">
            {initials || "U"}
          </div>

          <button
            type="button"
            className="dashboard-logout"
            onClick={logout}
            aria-label="Sign out"
            title="Sign out"
          >
            <DashboardIcon name="logout" />

            <span>
              Sign out
            </span>
          </button>
        </div>
      </header>

      <div className="dashboard-body">
        <aside className="dashboard-sidebar">
          <div className="sidebar-role-card">
            <div className="sidebar-role-icon">
              {initials || "U"}
            </div>

            <div>
              <strong>
                {displayName}
              </strong>

              <span>
                {role}
              </span>
            </div>
          </div>

          <div className="sidebar-scroll">
            <div className="sidebar-section-label">
              Workspace
            </div>

            <nav
              className="dashboard-nav"
              aria-label="Dashboard navigation"
            >
              <NavLink
                to="/dashboard"
                end
                className={getNavClass}
                title="Overview"
              >
                <DashboardIcon name="overview" />

                <span>
                  Overview
                </span>
              </NavLink>

              <NavLink
                to="/dashboard/activity"
                className={getNavClass}
                title="Activity"
              >
                <DashboardIcon name="activity" />

                <span>
                  Activity
                </span>
              </NavLink>

              <NavLink
                to="/dashboard/profile"
                className={getNavClass}
                title="Profile"
              >
                <DashboardIcon name="profile" />

                <span>
                  Profile
                </span>
              </NavLink>

              {user?.role === "USER" && (
                <>
                  <div className="sidebar-section-label sidebar-section-secondary">
                    Complaints
                  </div>

                  <NavLink
                    to="/dashboard/complaints"
                    className={getNavClass}
                    title="My complaints"
                  >
                    <DashboardIcon name="complaints" />

                    <span>
                      My complaints
                    </span>
                  </NavLink>

                  <NavLink
                    to="/dashboard/complaints/new"
                    className={`${getNavClass({
                      isActive:
                        location.pathname ===
                        "/dashboard/complaints/new",
                    })} dashboard-nav-primary`}
                    title="New complaint"
                  >
                    <DashboardIcon name="add" />

                    <span>
                      New complaint
                    </span>
                  </NavLink>
                </>
              )}

              {user?.role === "OFFICER" && (
                <>
                  <div className="sidebar-section-label sidebar-section-secondary">
                    Operations
                  </div>

                  <NavLink
                    to="/dashboard/assigned"
                    className={getNavClass}
                    title="Assigned complaints"
                  >
                    <DashboardIcon name="assigned" />

                    <span>
                      Assigned complaints
                    </span>
                  </NavLink>

                  <NavLink
                    to="/dashboard/sla"
                    className={getNavClass}
                    title="SLA monitoring"
                  >
                    <DashboardIcon name="sla" />

                    <span>
                      SLA monitoring
                    </span>
                  </NavLink>
                </>
              )}

              {user?.role === "ADMIN" && (
                <>
                  <div className="sidebar-section-label sidebar-section-secondary">
                    Management
                  </div>

                  <NavLink
                    to="/dashboard/complaints"
                    className={getNavClass}
                    title="All complaints"
                  >
                    <DashboardIcon name="complaints" />

                    <span>
                      All complaints
                    </span>
                  </NavLink>

                  <NavLink
                    to="/dashboard/sla"
                    className={getNavClass}
                    title="SLA monitoring"
                  >
                    <DashboardIcon name="sla" />

                    <span>
                      SLA monitoring
                    </span>
                  </NavLink>

                  <NavLink
                    to="/dashboard/analytics"
                    className={getNavClass}
                    title="Analytics"
                  >
                    <DashboardIcon name="analytics" />

                    <span>
                      Analytics
                    </span>
                  </NavLink>
                </>
              )}
            </nav>
          </div>

          <div className="sidebar-footer">
            <div className="sidebar-security-icon">
              <DashboardIcon name="shield" />
            </div>

            <div>
              <strong>
                Secure session
              </strong>

              <span>
                JWT authenticated
              </span>
            </div>

            <span className="sidebar-security-status" />
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