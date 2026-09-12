import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { Link } from "react-router-dom";

import {
  getSLARecords,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/sla-dashboard.css";


function getSLAList(data) {
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


function getSLAState(sla) {
  if (
    sla.response_breached ||
    sla.resolution_breached
  ) {
    return "BREACHED";
  }

  if (
    sla.resolution_deadline &&
    new Date(sla.resolution_deadline) <=
      new Date()
  ) {
    return "BREACHED";
  }

  if (
    sla.response_deadline &&
    new Date(sla.response_deadline) <=
      new Date()
  ) {
    return "BREACHED";
  }

  const deadline =
    sla.resolution_deadline ||
    sla.response_deadline;

  if (!deadline) {
    return "NO DEADLINE";
  }

  const remaining =
    new Date(deadline).getTime() -
    Date.now();

  const hoursRemaining =
    remaining / (1000 * 60 * 60);

  if (hoursRemaining <= 24) {
    return "AT RISK";
  }

  return "ON TRACK";
}


function SLADashboard() {
  const [slaRecords, setSlaRecords] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [filter, setFilter] =
    useState("ALL");


  async function loadSLARecords() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getSLARecords();

      setSlaRecords(
        getSLAList(data),
      );
    } catch (requestError) {
      console.error(
        "Failed to load SLA records:",
        requestError,
      );

      setError(
        "Unable to load SLA data. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadSLARecords();
  }, []);


  const statistics = useMemo(() => {
    const total =
      slaRecords.length;

    const breached =
      slaRecords.filter(
        (sla) =>
          getSLAState(sla) ===
          "BREACHED",
      ).length;

    const atRisk =
      slaRecords.filter(
        (sla) =>
          getSLAState(sla) ===
          "AT RISK",
      ).length;

    const onTrack =
      slaRecords.filter(
        (sla) =>
          getSLAState(sla) ===
          "ON TRACK",
      ).length;

    const completed =
      slaRecords.filter(
        (sla) =>
          sla.response_completed_at ||
          sla.resolution_completed_at,
      ).length;

    return {
      total,
      breached,
      atRisk,
      onTrack,
      completed,
    };
  }, [slaRecords]);


  const filteredRecords =
    useMemo(() => {
      if (filter === "ALL") {
        return slaRecords;
      }

      return slaRecords.filter(
        (sla) =>
          getSLAState(sla) ===
          filter,
      );
    }, [
      slaRecords,
      filter,
    ]);


  return (
    <section className="sla-dashboard">
      <header className="sla-dashboard-header">
        <div>
          <p className="sla-dashboard-eyebrow">
            SLA & ESCALATION CONTROL
          </p>

          <h1>
            SLA monitoring
          </h1>

          <p>
            Monitor response and resolution
            deadlines, identify breaches,
            and prioritize complaints
            requiring administrative attention.
          </p>
        </div>

        <div className="sla-dashboard-actions">
          <button
            type="button"
            className="sla-refresh-button"
            onClick={loadSLARecords}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "Refresh"}
          </button>

          <Link
            to="/dashboard/complaints"
            className="sla-secondary-button"
          >
            View complaints
          </Link>
        </div>
      </header>


      {error && (
        <div
          className="sla-error"
          role="alert"
        >
          <span>{error}</span>

          <button
            type="button"
            onClick={loadSLARecords}
          >
            Try again
          </button>
        </div>
      )}


      <div className="sla-stat-grid">
        <article className="sla-stat-card">
          <div className="sla-stat-top">
            <span>
              Total SLA records
            </span>

            <span className="sla-stat-icon">
              ALL
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.total}
          </strong>

          <p>
            Complaints currently tracked
            by the SLA system.
          </p>
        </article>


        <article className="sla-stat-card sla-stat-card-danger">
          <div className="sla-stat-top">
            <span>
              Breached
            </span>

            <span className="sla-stat-icon">
              BREACH
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.breached}
          </strong>

          <p>
            Complaints that have exceeded
            an SLA deadline.
          </p>
        </article>


        <article className="sla-stat-card sla-stat-card-warning">
          <div className="sla-stat-top">
            <span>
              At risk
            </span>

            <span className="sla-stat-icon">
              RISK
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.atRisk}
          </strong>

          <p>
            Complaints approaching their
            SLA deadline.
          </p>
        </article>


        <article className="sla-stat-card">
          <div className="sla-stat-top">
            <span>
              On track
            </span>

            <span className="sla-stat-icon">
              OK
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.onTrack}
          </strong>

          <p>
            Complaints currently within
            their SLA window.
          </p>
        </article>


        <article className="sla-stat-card">
          <div className="sla-stat-top">
            <span>
              Completed
            </span>

            <span className="sla-stat-icon">
              DONE
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.completed}
          </strong>

          <p>
            SLA records with completed
            response or resolution.
          </p>
        </article>
      </div>


      <section className="sla-dashboard-card">
        <div className="sla-section-header">
          <div>
            <p className="sla-section-eyebrow">
              DEADLINE MONITOR
            </p>

            <h2>
              Complaint SLA status
            </h2>

            <p>
              Review individual SLA deadlines
              and open the related complaint.
            </p>
          </div>


          <div className="sla-filter-group">
            <button
              type="button"
              className={
                filter === "ALL"
                  ? "sla-filter-button active"
                  : "sla-filter-button"
              }
              onClick={() =>
                setFilter("ALL")
              }
            >
              All
            </button>

            <button
              type="button"
              className={
                filter === "BREACHED"
                  ? "sla-filter-button active"
                  : "sla-filter-button"
              }
              onClick={() =>
                setFilter("BREACHED")
              }
            >
              Breached
            </button>

            <button
              type="button"
              className={
                filter === "AT RISK"
                  ? "sla-filter-button active"
                  : "sla-filter-button"
              }
              onClick={() =>
                setFilter("AT RISK")
              }
            >
              At risk
            </button>

            <button
              type="button"
              className={
                filter === "ON TRACK"
                  ? "sla-filter-button active"
                  : "sla-filter-button"
              }
              onClick={() =>
                setFilter("ON TRACK")
              }
            >
              On track
            </button>
          </div>
        </div>


        {loading ? (
          <div className="sla-table-loading">
            <div />
            <div />
            <div />
            <div />
            <div />
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="sla-empty-state">
            <h3>
              No SLA records found
            </h3>

            <p>
              There are no SLA records matching
              the selected filter.
            </p>
          </div>
        ) : (
          <div className="sla-table-wrapper">
            <table className="sla-table">
              <thead>
                <tr>
                  <th>
                    Ticket
                  </th>

                  <th>
                    Complaint
                  </th>

                  <th>
                    Priority
                  </th>

                  <th>
                    Status
                  </th>

                  <th>
                    Response deadline
                  </th>

                  <th>
                    Resolution deadline
                  </th>

                  <th>
                    SLA state
                  </th>

                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredRecords.map(
                  (sla) => {
                    const complaint =
                      sla.complaint_detail ||
                      sla.complaint;

                    const state =
                      getSLAState(sla);

                    const complaintId =
                      typeof complaint ===
                      "object"
                        ? complaint.id
                        : complaint;

                    const ticketNumber =
                      typeof complaint ===
                      "object"
                        ? complaint.ticket_number
                        : sla.ticket_number;

                    const title =
                      typeof complaint ===
                      "object"
                        ? complaint.title
                        : sla.complaint_title;

                    const priority =
                      typeof complaint ===
                      "object"
                        ? complaint.priority
                        : sla.priority;

                    const status =
                      typeof complaint ===
                      "object"
                        ? complaint.status
                        : sla.status;

                    return (
                      <tr
                        key={sla.id}
                      >
                        <td>
                          <span className="sla-ticket-number">
                            {ticketNumber ||
                              "—"}
                          </span>
                        </td>

                        <td>
                          <div className="sla-complaint-title">
                            {title ||
                              "Complaint"}
                          </div>
                        </td>

                        <td>
                          <ComplaintPriorityBadge
                            priority={
                              priority
                            }
                          />
                        </td>

                        <td>
                          <ComplaintStatusBadge
                            status={
                              status
                            }
                          />
                        </td>

                        <td>
                          <span className="sla-date">
                            {formatDate(
                              sla.response_deadline,
                            )}
                          </span>
                        </td>

                        <td>
                          <span className="sla-date">
                            {formatDate(
                              sla.resolution_deadline,
                            )}
                          </span>
                        </td>

                        <td>
                          <span
                            className={
                              state ===
                              "BREACHED"
                                ? "sla-state sla-state-danger"
                                : state ===
                                    "AT RISK"
                                  ? "sla-state sla-state-warning"
                                  : "sla-state sla-state-ok"
                            }
                          >
                            {state}
                          </span>
                        </td>

                        <td>
                          {complaintId ? (
                            <Link
                              to={`/dashboard/complaints/${complaintId}`}
                              className="sla-view-link"
                            >
                              View
                            </Link>
                          ) : (
                            <span>
                              —
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}


export default SLADashboard;