import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import {
  getComplaintSLARisk,
  getComplaints,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";

import "../styles/officer-dashboard.css";


function getComplaintList(data) {
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


function formatRemainingHours(hours) {
  if (hours === null || hours === undefined) {
    return "SLA unavailable";
  }

  const numericHours = Number(hours);

  if (Number.isNaN(numericHours)) {
    return "SLA unavailable";
  }

  if (numericHours <= 0) {
    return "Overdue";
  }

  if (numericHours < 1) {
    const minutes = Math.max(
      1,
      Math.round(numericHours * 60),
    );

    return `${minutes} min remaining`;
  }

  if (numericHours < 24) {
    const roundedHours = Math.max(
      1,
      Math.round(numericHours),
    );

    return `${roundedHours}h remaining`;
  }

  const days = Math.floor(numericHours / 24);
  const remainingHours = Math.round(
    numericHours % 24,
  );

  if (remainingHours === 0) {
    return `${days}d remaining`;
  }

  return `${days}d ${remainingHours}h remaining`;
}


function getRiskLevel(risk) {
  if (!risk) {
    return "UNKNOWN";
  }

  return (
    risk.risk_level ||
    risk.risk ||
    "UNKNOWN"
  ).toUpperCase();
}


function getRiskLabel(risk) {
  const riskLevel = getRiskLevel(risk);

  if (riskLevel === "CRITICAL") {
    return "Critical risk";
  }

  if (riskLevel === "HIGH") {
    return "High risk";
  }

  if (riskLevel === "MEDIUM") {
    return "Medium risk";
  }

  if (riskLevel === "LOW") {
    return "Low risk";
  }

  return "Risk unavailable";
}


function getRiskClass(risk) {
  const riskLevel = getRiskLevel(risk);

  if (riskLevel === "CRITICAL") {
    return "critical";
  }

  if (riskLevel === "HIGH") {
    return "high";
  }

  if (riskLevel === "MEDIUM") {
    return "medium";
  }

  if (riskLevel === "LOW") {
    return "low";
  }

  return "unknown";
}


function getRiskIcon(risk) {
  const riskLevel = getRiskLevel(risk);

  if (riskLevel === "CRITICAL") {
    return "!";
  }

  if (riskLevel === "HIGH") {
    return "!";
  }

  if (riskLevel === "MEDIUM") {
    return "•";
  }

  if (riskLevel === "LOW") {
    return "✓";
  }

  return "?";
}


function getSlaHours(risk) {
  if (!risk) {
    return null;
  }

  if (
    risk.resolution_hours_remaining !==
    undefined
  ) {
    return Number(
      risk.resolution_hours_remaining,
    );
  }

  if (
    risk.hours_remaining !== undefined
  ) {
    return Number(risk.hours_remaining);
  }

  return null;
}


function getSlaState(risk) {
  if (!risk) {
    return "unknown";
  }

  if (
    risk.resolution_breached ||
    risk.response_breached
  ) {
    return "overdue";
  }

  const riskLevel = getRiskLevel(risk);

  if (
    riskLevel === "CRITICAL" ||
    riskLevel === "HIGH"
  ) {
    return "at-risk";
  }

  return "normal";
}


function OfficerDashboard() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [slaRisks, setSlaRisks] = useState({});
  const [loading, setLoading] = useState(true);
  const [riskLoading, setRiskLoading] = useState(false);
  const [error, setError] = useState("");
  const [riskError, setRiskError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] =
    useState("ALL");
  const [riskFilter, setRiskFilter] =
    useState("ALL");

  async function loadComplaints() {
    try {
      setLoading(true);
      setError("");
      setRiskError("");

      const data = await getComplaints();

      const complaintList =
        getComplaintList(data);

      setComplaints(complaintList);

      setRiskLoading(true);

      const riskResults =
        await Promise.allSettled(
          complaintList.map(
            async (complaint) => {
              const risk =
                await getComplaintSLARisk(
                  complaint.id,
                );

              return {
                complaintId: complaint.id,
                risk,
              };
            },
          ),
        );

      const riskMap = {};
      let failedRiskRequests = 0;

      riskResults.forEach((result) => {
        if (
          result.status === "fulfilled"
        ) {
          riskMap[
            result.value.complaintId
          ] = result.value.risk;
        } else {
          failedRiskRequests += 1;
        }
      });

      setSlaRisks(riskMap);

      if (failedRiskRequests > 0) {
        setRiskError(
          "Some SLA risk information could not be loaded.",
        );
      }
    } catch (requestError) {
      console.error(
        "Failed to load officer dashboard:",
        requestError,
      );

      setError(
        "Unable to load assigned complaints.",
      );
    } finally {
      setLoading(false);
      setRiskLoading(false);
    }
  }


  useEffect(() => {
    loadComplaints();
  }, []);


  const statistics = useMemo(() => {
    const assigned =
      complaints.length;

    const inProgress =
      complaints.filter(
        (complaint) =>
          complaint.status ===
          "IN_PROGRESS",
      ).length;

    const atRisk =
      complaints.filter((complaint) => {
        const risk =
          slaRisks[complaint.id];

        const riskLevel =
          getRiskLevel(risk);

        return (
          riskLevel === "HIGH" ||
          riskLevel === "CRITICAL"
        );
      }).length;

    const overdue =
      complaints.filter((complaint) => {
        const risk =
          slaRisks[complaint.id];

        return (
          risk?.response_breached ||
          risk?.resolution_breached
        );
      }).length;

    const urgent =
      complaints.filter(
        (complaint) =>
          complaint.priority ===
            "HIGH" ||
          complaint.priority ===
            "CRITICAL",
      ).length;

    const pending =
      complaints.filter(
        (complaint) =>
          complaint.status ===
            "ASSIGNED" ||
          complaint.status ===
            "ACKNOWLEDGED",
      ).length;

    const resolved =
      complaints.filter(
        (complaint) =>
          complaint.status ===
            "RESOLVED" ||
          complaint.status ===
            "CLOSED",
      ).length;

    return {
      assigned,
      pending,
      inProgress,
      atRisk,
      overdue,
      urgent,
      resolved,
    };
  }, [complaints, slaRisks]);


  const filteredComplaints = useMemo(() => {
    const normalizedSearch =
      searchTerm.trim().toLowerCase();

    return [...complaints]
      .filter((complaint) => {
        if (
          statusFilter !== "ALL" &&
          complaint.status !== statusFilter
        ) {
          return false;
        }

        if (riskFilter !== "ALL") {
          const riskLevel =
            getRiskLevel(
              slaRisks[complaint.id],
            );

          if (riskLevel !== riskFilter) {
            return false;
          }
        }

        if (!normalizedSearch) {
          return true;
        }

        const searchableText = [
          complaint.ticket_number,
          complaint.title,
          complaint.description,
          complaint.category_name,
          complaint.location,
          complaint.status,
          complaint.priority,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchableText.includes(
          normalizedSearch,
        );
      })
      .sort((a, b) => {
        const riskA =
          slaRisks[a.id];

        const riskB =
          slaRisks[b.id];

        const riskWeight = {
          CRITICAL: 4,
          HIGH: 3,
          MEDIUM: 2,
          LOW: 1,
          UNKNOWN: 0,
        };

        const riskDifference =
          riskWeight[
            getRiskLevel(riskB)
          ] -
          riskWeight[
            getRiskLevel(riskA)
          ];

        if (riskDifference !== 0) {
          return riskDifference;
        }

        const dateA =
          new Date(a.created_at).getTime();

        const dateB =
          new Date(b.created_at).getTime();

        return dateB - dateA;
      });
  }, [
    complaints,
    searchTerm,
    statusFilter,
    riskFilter,
    slaRisks,
  ]);


  function clearFilters() {
    setSearchTerm("");
    setStatusFilter("ALL");
    setRiskFilter("ALL");
  }


  return (
    <section className="officer-dashboard">
      <header className="officer-dashboard-header">
        <div>
          <p className="officer-dashboard-eyebrow">
            OFFICER WORKSPACE
          </p>

          <h1>Officer dashboard</h1>

          <p>
            Monitor your assigned complaints,
            prioritize SLA risks, and move each
            grievance through the resolution workflow.
          </p>
        </div>

        <button
          type="button"
          className="officer-refresh-button"
          onClick={loadComplaints}
          disabled={loading}
        >
          {loading
            ? "Refreshing..."
            : "Refresh dashboard"}
        </button>
      </header>


      <div className="officer-profile-strip">
        <div>
          <span>Officer</span>

          <strong>
            {user?.email || "Officer"}
          </strong>
        </div>

        <div>
          <span>Department</span>

          <strong>
            {user?.department_name || "—"}
          </strong>
        </div>

        <div>
          <span>Dashboard status</span>

          <strong>
            {riskLoading
              ? "Updating SLA risk..."
              : "Live data"}
          </strong>
        </div>

        <span className="officer-role-pill">
          OFFICER
        </span>
      </div>


      {error && (
        <div
          className="officer-dashboard-error"
          role="alert"
        >
          <span>{error}</span>

          <button
            type="button"
            onClick={loadComplaints}
          >
            Try again
          </button>
        </div>
      )}


      {riskError && !error && (
        <div
          className="officer-dashboard-warning"
          role="status"
        >
          <span>{riskError}</span>
        </div>
      )}


      <div className="officer-stat-grid">
        <article className="officer-stat-card">
          <div className="officer-stat-card-top">
            <span>Assigned</span>

            <span className="officer-stat-icon">
              A
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.assigned}
          </strong>

          <p>
            Complaints currently assigned to you
          </p>
        </article>


        <article className="officer-stat-card">
          <div className="officer-stat-card-top">
            <span>In progress</span>

            <span className="officer-stat-icon">
              →
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.inProgress}
          </strong>

          <p>
            Complaints currently being worked on
          </p>
        </article>


        <article className="officer-stat-card officer-stat-risk">
          <div className="officer-stat-card-top">
            <span>At risk</span>

            <span className="officer-stat-icon">
              !
            </span>
          </div>

          <strong>
            {loading || riskLoading
              ? "—"
              : statistics.atRisk}
          </strong>

          <p>
            High or critical SLA risk
          </p>
        </article>


        <article className="officer-stat-card officer-stat-overdue">
          <div className="officer-stat-card-top">
            <span>Overdue</span>

            <span className="officer-stat-icon">
              !
            </span>
          </div>

          <strong>
            {loading || riskLoading
              ? "—"
              : statistics.overdue}
          </strong>

          <p>
            Complaints with an SLA breach
          </p>
        </article>


        <article className="officer-stat-card">
          <div className="officer-stat-card-top">
            <span>High priority</span>

            <span className="officer-stat-icon">
              ↑
            </span>
          </div>

          <strong>
            {loading
              ? "—"
              : statistics.urgent}
          </strong>

          <p>
            High and critical complaints
          </p>
        </article>
      </div>


      <section className="officer-dashboard-card">
        <div className="officer-section-header">
          <div>
            <p className="officer-section-eyebrow">
              WORK QUEUE
            </p>

            <h2>My complaints</h2>

            <p>
              Complaints are prioritized using
              current SLA risk and submission time.
            </p>
          </div>

          <div className="officer-queue-summary">
            <strong>
              {filteredComplaints.length}
            </strong>

            <span>
              {filteredComplaints.length === 1
                ? "complaint shown"
                : "complaints shown"}
            </span>
          </div>
        </div>


        <div className="officer-filter-bar">
          <div className="officer-search-box">
            <label htmlFor="officer-search">
              Search
            </label>

            <input
              id="officer-search"
              type="search"
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(
                  event.target.value,
                )
              }
              placeholder="Search ticket, title, category, location..."
            />
          </div>


          <div className="officer-filter-control">
            <label htmlFor="officer-status-filter">
              Status
            </label>

            <select
              id="officer-status-filter"
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(
                  event.target.value,
                )
              }
            >
              <option value="ALL">
                All statuses
              </option>

              <option value="ASSIGNED">
                Assigned
              </option>

              <option value="ACKNOWLEDGED">
                Acknowledged
              </option>

              <option value="IN_PROGRESS">
                In progress
              </option>

              <option value="RESOLVED">
                Resolved
              </option>

              <option value="CLOSED">
                Closed
              </option>

              <option value="ESCALATED">
                Escalated
              </option>

              <option value="REOPENED">
                Reopened
              </option>
            </select>
          </div>


          <div className="officer-filter-control">
            <label htmlFor="officer-risk-filter">
              SLA risk
            </label>

            <select
              id="officer-risk-filter"
              value={riskFilter}
              onChange={(event) =>
                setRiskFilter(
                  event.target.value,
                )
              }
            >
              <option value="ALL">
                All risk levels
              </option>

              <option value="CRITICAL">
                Critical
              </option>

              <option value="HIGH">
                High
              </option>

              <option value="MEDIUM">
                Medium
              </option>

              <option value="LOW">
                Low
              </option>
            </select>
          </div>


          {(searchTerm ||
            statusFilter !== "ALL" ||
            riskFilter !== "ALL") && (
            <button
              type="button"
              className="officer-clear-filter"
              onClick={clearFilters}
            >
              Clear
            </button>
          )}
        </div>


        {loading ? (
          <div className="officer-loading">
            <div />
            <div />
            <div />
            <div />
            <div />
          </div>
        ) : filteredComplaints.length ===
          0 ? (
          <div className="officer-empty-state">
            <div className="officer-empty-icon">
              ✓
            </div>

            <h3>
              {complaints.length === 0
                ? "No assigned complaints"
                : "No complaints match your filters"}
            </h3>

            <p>
              {complaints.length === 0
                ? "New complaints assigned to you will appear here."
                : "Try changing your search or filter criteria."}
            </p>

            {complaints.length > 0 && (
              <button
                type="button"
                className="officer-empty-clear"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="officer-table-wrapper">
            <table className="officer-complaint-table">
              <thead>
                <tr>
                  <th>Ticket</th>
                  <th>Complaint</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>SLA</th>
                  <th>AI risk</th>
                  <th>Updated</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredComplaints.map(
                  (complaint) => {
                    const risk =
                      slaRisks[complaint.id];

                    const riskClass =
                      getRiskClass(risk);

                    const slaState =
                      getSlaState(risk);

                    const slaHours =
                      getSlaHours(risk);

                    return (
                      <tr
                        key={complaint.id}
                        className={
                          slaState === "overdue"
                            ? "officer-row-overdue"
                            : slaState === "at-risk"
                              ? "officer-row-at-risk"
                              : ""
                        }
                      >
                        <td>
                          <span className="officer-ticket">
                            {complaint.ticket_number}
                          </span>
                        </td>


                        <td>
                          <div className="officer-title">
                            {complaint.title}
                          </div>

                          <div className="officer-location">
                            {complaint.category_name ||
                              "No category"}

                            {" • "}

                            {complaint.location ||
                              "No location"}
                          </div>
                        </td>


                        <td>
                          <ComplaintPriorityBadge
                            priority={
                              complaint.priority
                            }
                          />
                        </td>


                        <td>
                          <ComplaintStatusBadge
                            status={
                              complaint.status
                            }
                          />
                        </td>


                        <td>
                          <div
                            className={`officer-sla-cell officer-sla-${slaState}`}
                          >
                            <strong>
                              {risk
                                ? formatRemainingHours(
                                    slaHours,
                                  )
                                : "Loading..."}
                            </strong>

                            {risk && (
                              <span>
                                {risk.resolution_breached
                                  ? "Resolution breached"
                                  : risk.response_breached
                                    ? "Response breached"
                                    : "Resolution SLA"}
                              </span>
                            )}
                          </div>
                        </td>


                        <td>
                          <div
                            className={`officer-risk-badge officer-risk-${riskClass}`}
                          >
                            <span>
                              {getRiskIcon(
                                risk,
                              )}
                            </span>

                            <div>
                              <strong>
                                {getRiskLabel(
                                  risk,
                                )}
                              </strong>

                              {risk?.risk_score !==
                                undefined && (
                                <small>
                                  Score{" "}
                                  {
                                    risk.risk_score
                                  }
                                </small>
                              )}
                            </div>
                          </div>
                        </td>


                        <td>
                          <span className="officer-updated">
                            {formatDate(
                              complaint.updated_at ||
                                complaint.created_at,
                            )}
                          </span>
                        </td>


                        <td>
                          <Link
                            to={`/dashboard/assigned/${complaint.id}`}
                            className="officer-view-link"
                          >
                            Open
                          </Link>
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


      <section className="officer-dashboard-footer-grid">
        <article className="officer-insight-card">
          <div className="officer-insight-icon">
            !
          </div>

          <div>
            <span>Priority workload</span>

            <strong>
              {loading
                ? "—"
                : statistics.urgent}{" "}
              high-priority cases
            </strong>

            <p>
              Review high and critical complaints
              before lower-priority work.
            </p>
          </div>
        </article>


        <article className="officer-insight-card">
          <div className="officer-insight-icon">
            ✓
          </div>

          <div>
            <span>Resolution progress</span>

            <strong>
              {loading
                ? "—"
                : statistics.resolved}{" "}
              resolved or closed
            </strong>

            <p>
              Keep complaint status updated so
              citizens receive accurate progress.
            </p>
          </div>
        </article>


        <article className="officer-insight-card">
          <div className="officer-insight-icon">
            AI
          </div>

          <div>
            <span>AI assistance</span>

            <strong>
              SLA risk + resolution assistant
            </strong>

            <p>
              Open a complaint to access the
              AI-assisted operational tools.
            </p>
          </div>
        </article>
      </section>
    </section>
  );
}


export default OfficerDashboard;