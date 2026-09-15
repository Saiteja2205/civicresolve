import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../services/notificationService.js";

import "./DashboardLayout.css";


function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
          "Unable to load notifications."
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
      handleOutsideClick
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick
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
              : item
          )
        );

        setUnreadCount((current) =>
          Math.max(0, current - 1)
        );
      }
    } catch (error) {
      console.error(
        "Failed to mark notification as read:",
        error
      );
    }

    setNotificationOpen(false);

    if (notification.complaint) {
      navigate(
        `/dashboard/complaints/${notification.complaint}`
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
        }))
      );

      setUnreadCount(0);
    } catch (error) {
      console.error(
        "Failed to mark all notifications as read:",
        error
      );

      setNotificationError(
        error?.response?.data?.detail ||
          "Unable to mark notifications as read."
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

    const seconds = Math.floor(
      difference / 1000
    );

    if (seconds < 60) {
      return "Just now";
    }

    const minutes = Math.floor(
      seconds / 60
    );

    if (minutes < 60) {
      return `${minutes}m ago`;
    }

    const hours = Math.floor(
      minutes / 60
    );

    if (hours < 24) {
      return `${hours}h ago`;
    }

    const days = Math.floor(
      hours / 24
    );

    if (days < 7) {
      return `${days}d ago`;
    }

    return date.toLocaleDateString(
      undefined,
      {
        day: "numeric",
        month: "short",
      }
    );
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

          {/* NOTIFICATION CENTER */}
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
                  (current) => !current
                )
              }
              aria-label={
                unreadCount > 0
                  ? `${unreadCount} unread notifications`
                  : "Notifications"
              }
              aria-expanded={notificationOpen}
            >

              <svg
                className="notification-bell-icon"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M18 8.5C18 5.46243 15.3137 3 12 3C8.68629 3 6 5.46243 6 8.5C6 15 3.5 16 3.5 17.5H20.5C20.5 16 18 15 18 8.5Z"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                <path
                  d="M9.5 20C10.0833 20.6667 10.9167 21 12 21C13.0833 21 13.9167 20.6667 14.5 20"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
              </svg>


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
                        New complaint activity will appear here.
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
                              notification
                            )
                          }
                        >

                          <div className="notification-item-icon">
                            {getNotificationIcon(
                              notification.type
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
                                  {notification.complaint_ticket}
                                </span>
                              )}

                              <time>
                                {formatNotificationTime(
                                  notification.created_at
                                )}
                              </time>

                            </div>

                          </div>

                        </button>
                      )
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


          <nav
            className="dashboard-nav"
            aria-label="Dashboard navigation"
          >

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