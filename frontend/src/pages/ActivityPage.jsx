import {
  useEffect,
  useState,
} from "react";

import { Link } from "react-router-dom";

import {
  getActivity,
} from "../services/complaintService.js";

import "../styles/activity-page.css";


function getActivityList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


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


function ActivityPage() {
  const [activities, setActivities] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  async function loadActivity() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getActivity();

      setActivities(
        getActivityList(data),
      );
    } catch (requestError) {
      console.error(
        "Failed to load activity:",
        requestError,
      );

      setError(
        "Unable to load activity. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadActivity();
  }, []);


  return (
    <section className="activity-page">
      <header className="activity-header">
        <div>
          <p className="activity-eyebrow">
            ACTIVITY CENTER
          </p>

          <h1>
            Notifications & activity
          </h1>

          <p>
            Stay updated on complaint status
            changes, assignments, resolutions,
            and other important activity.
          </p>
        </div>

        <button
          type="button"
          className="activity-refresh-button"
          onClick={loadActivity}
          disabled={loading}
        >
          {loading
            ? "Refreshing..."
            : "Refresh"}
        </button>
      </header>


      {error && (
        <div
          className="activity-error"
          role="alert"
        >
          <span>
            {error}
          </span>

          <button
            type="button"
            onClick={loadActivity}
          >
            Try again
          </button>
        </div>
      )}


      <section className="activity-card">
        <div className="activity-card-header">
          <div>
            <p className="activity-card-eyebrow">
              RECENT UPDATES
            </p>

            <h2>
              Complaint activity
            </h2>
          </div>

          <span>
            {activities.length} updates
          </span>
        </div>


        {loading ? (
          <div className="activity-loading">
            <div />
            <div />
            <div />
            <div />
            <div />
          </div>
        ) : activities.length === 0 ? (
          <div className="activity-empty">
            <h3>
              No activity yet
            </h3>

            <p>
              Complaint updates will appear
              here as your cases progress.
            </p>
          </div>
        ) : (
          <div className="activity-list">
            {activities.map(
              (activity) => (
                <div
                  className="activity-item"
                  key={activity.id}
                >
                  <div className="activity-indicator">
                    <span />
                  </div>

                  <div className="activity-content">
                    <div className="activity-top">
                      <strong>
                        {activity.complaint_ticket_number ||
                          activity.complaint?.ticket_number ||
                          `Complaint #${activity.complaint}`}
                      </strong>

                      <span>
                        {formatDate(
                          activity.created_at,
                        )}
                      </span>
                    </div>

                    <p>
                      {activity.old_status &&
                        activity.new_status
                        ? `${activity.old_status.replace(
                            /_/g,
                            " ",
                          )} → ${activity.new_status.replace(
                            /_/g,
                            " ",
                          )}`
                        : activity.new_status ||
                          "Complaint updated"}
                    </p>

                    {activity.comment && (
                      <div className="activity-comment">
                        {activity.comment}
                      </div>
                    )}

                    {activity.changed_by_email && (
                      <small>
                        Updated by{" "}
                        {
                          activity.changed_by_email
                        }
                      </small>
                    )}

                    {activity.complaint && (
                      <Link
                        to={`/dashboard/complaints/${
                          typeof activity.complaint ===
                          "object"
                            ? activity.complaint.id
                            : activity.complaint
                        }`}
                        className="activity-view-link"
                      >
                        View complaint
                      </Link>
                    )}
                  </div>
                </div>
              ),
            )}
          </div>
        )}
      </section>
    </section>
  );
}


export default ActivityPage;