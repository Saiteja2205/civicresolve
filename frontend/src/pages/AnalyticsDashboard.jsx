import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { Link } from "react-router-dom";

import {
  getComplaints,
  getSLARecords,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/analytics-dashboard.css";


function getList(data) {
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
  });
}


function getSLAState(sla) {
  if (
    sla.response_breached ||
    sla.resolution_breached
  ) {
    return "BREACHED";
  }

  const resolutionDeadline =
    sla.resolution_deadline
      ? new Date(
          sla.resolution_deadline,
        )
      : null;

  const responseDeadline =
    sla.response_deadline
      ? new Date(
          sla.response_deadline,
        )
      : null;

  const now = new Date();

  if (
    resolutionDeadline &&
    resolutionDeadline <= now &&
    !sla.resolution_completed_at
  ) {
    return "BREACHED";
  }

  if (
    responseDeadline &&
    responseDeadline <= now &&
    !sla.response_completed_at
  ) {
    return "BREACHED";
  }

  const deadline =
    resolutionDeadline ||
    responseDeadline;

  if (!deadline) {
    return "NO DEADLINE";
  }

  const hoursRemaining =
    (deadline.getTime() - now.getTime()) /
    (1000 * 60 * 60);

  if (hoursRemaining <= 24) {
    return "AT RISK";
  }

  return "ON TRACK";
}


function AnalyticsDashboard() {
  const [complaints, setComplaints] =
    useState([]);

  const [slaRecords, setSlaRecords] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  async function loadAnalytics() {
    try {
      setLoading(true);
      setError("");

      const [
        complaintsData,
        slaData,
      ] = await Promise.all([
        getComplaints(),
        getSLARecords(),
      ]);

      setComplaints(
        getList(complaintsData),
      );

      setSlaRecords(
        getList(slaData),
      );
    } catch (requestError) {
      console.error(
        "Failed to load analytics:",
        requestError,
      );

      setError(
        "Unable to load analytics data. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadAnalytics();
  }, []);


  const statistics = useMemo(() => {
    const total =
      complaints.length;

    const active =
      complaints.filter(
        (complaint) =>
          ![
            "RESOLVED",
            "CLOSED",
            "REJECTED",
          ].includes(
            complaint.status,
          ),
      ).length;

    const resolved =
      complaints.filter(
        (complaint) =>
          complaint.status ===
            "RESOLVED" ||
          complaint.status ===
            "CLOSED",
      ).length;

    const escalated =
      complaints.filter(
        (complaint) =>
          complaint.status ===
          "ESCALATED",
      ).length;

    const highPriority =
      complaints.filter(
        (complaint) =>
          complaint.priority ===
            "HIGH" ||
          complaint.priority ===
            "CRITICAL",
      ).length;

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

    return {
      total,
      active,
      resolved,
      escalated,
      highPriority,
      breached,
      atRisk,
    };
  }, [
    complaints,
    slaRecords,
  ]);


  const statusData = useMemo(() => {
    const statuses = [
      "SUBMITTED",
      "AI_ANALYZING",
      "ASSIGNED",
      "ACKNOWLEDGED",
      "IN_PROGRESS",
      "NEEDS_INFORMATION",
      "ESCALATED",
      "RESOLVED",
      "CLOSED",
      "REOPENED",
      "REJECTED",
    ];

    return statuses
      .map((status) => ({
        status,
        count: complaints.filter(
          (complaint) =>
            complaint.status ===
            status,
        ).length,
      }))
      .filter(
        (item) =>
          item.count > 0,
      );
  }, [complaints]);


  const priorityData = useMemo(() => {
    const priorities = [
      "LOW",
      "MEDIUM",
      "HIGH",
      "CRITICAL",
    ];

    return priorities.map(
      (priority) => ({
        priority,
        count: complaints.filter(
          (complaint) =>
            complaint.priority ===
            priority,
        ).length,
      }),
    );
  }, [complaints]);


  const departmentData = useMemo(() => {
    const departmentMap =
      new Map();

    complaints.forEach(
      (complaint) => {
        const department =
          complaint.department_name ||
          "Unassigned";

        const existing =
          departmentMap.get(
            department,
          ) || {
            department,
            total: 0,
            active: 0,
            resolved: 0,
          };

        existing.total += 1;

        if (
          ![
            "RESOLVED",
            "CLOSED",
            "REJECTED",
          ].includes(
            complaint.status,
          )
        ) {
          existing.active += 1;
        }

        if (
          complaint.status ===
            "RESOLVED" ||
          complaint.status ===
            "CLOSED"
        ) {
          existing.resolved += 1;
        }

        departmentMap.set(
          department,
          existing,
        );
      },
    );

    return Array.from(
      departmentMap.values(),
    ).sort(
      (a, b) =>
        b.total - a.total,
    );
  }, [complaints]);


  const recentComplaints =
    useMemo(() => {
      return [...complaints]
        .sort(
          (a, b) =>
            new Date(
              b.created_at,
            ) -
            new Date(
              a.created_at,
            ),
        )
        .slice(0, 6);
    }, [complaints]);


  const maxStatusCount =
    Math.max(
      ...statusData.map(
        (item) =>
          item.count,
      ),
      1,
    );


  const maxPriorityCount =
    Math.max(
      ...priorityData.map(
        (item) =>
          item.count,
      ),
      1,
    );


  const maxDepartmentCount =
    Math.max(
      ...departmentData.map(
        (item) =>
          item.total,
      ),
      1,
    );


  return (
    <section className="analytics-dashboard">
      <header className="analytics-header">
        <div>
          <p className="analytics-eyebrow">
            ADMINISTRATIVE INTELLIGENCE
          </p>

          <h1>
            Analytics & reporting
          </h1>

          <p>
            Understand complaint volume,
            workload, priorities, resolution
            progress, and SLA performance
            across CivicResolve.
          </p>
        </div>

        <div className="analytics-header-actions">
          <button
            type="button"
            className="analytics-refresh-button"
            onClick={loadAnalytics}
            disabled={loading}
          >
            {loading
              ? "Refreshing..."
              : "Refresh"}
          </button>

          <Link
            to="/dashboard/admin"
            className="analytics-secondary-button"
          >
            Admin dashboard
          </Link>
        </div>
      </header>


      {error && (
        <div
          className="analytics-error"
          role="alert"
        >
          <span>
            {error}
          </span>

          <button
            type="button"
            onClick={loadAnalytics}
          >
            Try again
          </button>
        </div>
      )}


      <div className="analytics-stat-grid">
        <article className="analytics-stat-card">
          <span>
            Total complaints
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.total}
          </strong>

          <p>
            All complaints currently visible
            to the administrator.
          </p>
        </article>


        <article className="analytics-stat-card">
          <span>
            Active
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.active}
          </strong>

          <p>
            Complaints still requiring
            action.
          </p>
        </article>


        <article className="analytics-stat-card">
          <span>
            Resolved / closed
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.resolved}
          </strong>

          <p>
            Complaints that reached
            resolution or closure.
          </p>
        </article>


        <article className="analytics-stat-card">
          <span>
            Escalated
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.escalated}
          </strong>

          <p>
            Complaints currently requiring
            escalation attention.
          </p>
        </article>


        <article className="analytics-stat-card analytics-stat-alert">
          <span>
            High / critical
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.highPriority}
          </strong>

          <p>
            Complaints requiring higher
            priority handling.
          </p>
        </article>


        <article className="analytics-stat-card analytics-stat-danger">
          <span>
            SLA breached
          </span>

          <strong>
            {loading
              ? "—"
              : statistics.breached}
          </strong>

          <p>
            SLA records that exceeded
            their deadline.
          </p>
        </article>
      </div>


      <div className="analytics-grid-two">
        <section className="analytics-card">
          <div className="analytics-card-header">
            <div>
              <p className="analytics-card-eyebrow">
                WORKFLOW
              </p>

              <h2>
                Status distribution
              </h2>
            </div>

            <span>
              {statistics.total} total
            </span>
          </div>


          {statusData.length === 0 ? (
            <div className="analytics-empty">
              No complaint data available.
            </div>
          ) : (
            <div className="analytics-bars">
              {statusData.map(
                (item) => (
                  <div
                    className="analytics-bar-row"
                    key={item.status}
                  >
                    <div className="analytics-bar-label">
                      <span>
                        {item.status.replace(
                          /_/g,
                          " ",
                        )}
                      </span>

                      <strong>
                        {item.count}
                      </strong>
                    </div>

                    <div className="analytics-bar-track">
                      <div
                        className="analytics-bar-fill"
                        style={{
                          width: `${
                            (item.count /
                              maxStatusCount) *
                            100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </section>


        <section className="analytics-card">
          <div className="analytics-card-header">
            <div>
              <p className="analytics-card-eyebrow">
                PRIORITY
              </p>

              <h2>
                Priority distribution
              </h2>
            </div>

            <span>
              {statistics.highPriority} high
            </span>
          </div>


          <div className="analytics-bars">
            {priorityData.map(
              (item) => (
                <div
                  className="analytics-bar-row"
                  key={item.priority}
                >
                  <div className="analytics-bar-label">
                    <span>
                      {item.priority}
                    </span>

                    <strong>
                      {item.count}
                    </strong>
                  </div>

                  <div className="analytics-bar-track">
                    <div
                      className="analytics-bar-fill"
                      style={{
                        width: `${
                          (item.count /
                            maxPriorityCount) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              ),
            )}
          </div>
        </section>
      </div>


      <section className="analytics-card">
        <div className="analytics-card-header">
          <div>
            <p className="analytics-card-eyebrow">
              DEPARTMENT LOAD
            </p>

            <h2>
              Department performance
            </h2>

            <p>
              Complaint volume and current
              workload by department.
            </p>
          </div>

          <Link
            to="/dashboard/complaints"
            className="analytics-card-link"
          >
            View complaints
          </Link>
        </div>


        {departmentData.length === 0 ? (
          <div className="analytics-empty">
            No department data available.
          </div>
        ) : (
          <div className="department-table-wrapper">
            <table className="department-table">
              <thead>
                <tr>
                  <th>
                    Department
                  </th>

                  <th>
                    Total
                  </th>

                  <th>
                    Active
                  </th>

                  <th>
                    Resolved
                  </th>

                  <th>
                    Workload
                  </th>
                </tr>
              </thead>

              <tbody>
                {departmentData.map(
                  (department) => (
                    <tr
                      key={
                        department.department
                      }
                    >
                      <td>
                        <strong>
                          {
                            department.department
                          }
                        </strong>
                      </td>

                      <td>
                        {department.total}
                      </td>

                      <td>
                        {department.active}
                      </td>

                      <td>
                        {department.resolved}
                      </td>

                      <td>
                        <div className="department-workload">
                          <div className="department-workload-track">
                            <div
                              className="department-workload-fill"
                              style={{
                                width: `${
                                  (department.total /
                                    maxDepartmentCount) *
                                  100
                                }%`,
                              }}
                            />
                          </div>

                          <span>
                            {department.total}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>


      <div className="analytics-grid-two">
        <section className="analytics-card">
          <div className="analytics-card-header">
            <div>
              <p className="analytics-card-eyebrow">
                SLA HEALTH
              </p>

              <h2>
                SLA overview
              </h2>
            </div>

            <Link
              to="/dashboard/sla"
              className="analytics-card-link"
            >
              Open SLA monitor
            </Link>
          </div>


          <div className="analytics-sla-grid">
            <div className="analytics-sla-item">
              <span>
                On track
              </span>

              <strong>
                {Math.max(
                  slaRecords.length -
                    statistics.breached -
                    statistics.atRisk,
                  0,
                )}
              </strong>
            </div>

            <div className="analytics-sla-item">
              <span>
                At risk
              </span>

              <strong>
                {statistics.atRisk}
              </strong>
            </div>

            <div className="analytics-sla-item analytics-sla-danger">
              <span>
                Breached
              </span>

              <strong>
                {statistics.breached}
              </strong>
            </div>
          </div>
        </section>


        <section className="analytics-card">
          <div className="analytics-card-header">
            <div>
              <p className="analytics-card-eyebrow">
                QUICK ACTIONS
              </p>

              <h2>
                Administration
              </h2>
            </div>
          </div>


          <div className="analytics-actions">
            <Link
              to="/dashboard/complaints"
              className="analytics-action"
            >
              <strong>
                All complaints
              </strong>

              <span>
                Search, filter, sort and manage
                complaints.
              </span>
            </Link>

            <Link
              to="/dashboard/sla"
              className="analytics-action"
            >
              <strong>
                SLA monitoring
              </strong>

              <span>
                Review breaches and approaching
                deadlines.
              </span>
            </Link>

            <Link
              to="/dashboard/admin"
              className="analytics-action"
            >
              <strong>
                System overview
              </strong>

              <span>
                Return to the main administrator
                dashboard.
              </span>
            </Link>
          </div>
        </section>
      </div>


      <section className="analytics-card">
        <div className="analytics-card-header">
          <div>
            <p className="analytics-card-eyebrow">
              RECENT INTAKE
            </p>

            <h2>
              Latest complaints
            </h2>
          </div>

          <Link
            to="/dashboard/complaints"
            className="analytics-card-link"
          >
            See all
          </Link>
        </div>


        {recentComplaints.length === 0 ? (
          <div className="analytics-empty">
            No recent complaints.
          </div>
        ) : (
          <div className="analytics-recent-list">
            {recentComplaints.map(
              (complaint) => (
                <Link
                  key={complaint.id}
                  to={`/dashboard/complaints/${complaint.id}`}
                  className="analytics-recent-item"
                >
                  <div>
                    <strong>
                      {
                        complaint.ticket_number
                      }
                    </strong>

                    <span>
                      {complaint.title}
                    </span>

                    <small>
                      {
                        complaint.department_name ||
                        "Unassigned"
                      }{" "}
                      •{" "}
                      {formatDate(
                        complaint.created_at,
                      )}
                    </small>
                  </div>

                  <div className="analytics-recent-badges">
                    <ComplaintPriorityBadge
                      priority={
                        complaint.priority
                      }
                    />

                    <ComplaintStatusBadge
                      status={
                        complaint.status
                      }
                    />
                  </div>
                </Link>
              ),
            )}
          </div>
        )}
      </section>
    </section>
  );
}


export default AnalyticsDashboard;