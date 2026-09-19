import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getComplaints } from "../services/complaintService";

import "../styles/complaints.css";
import "../styles/complaint-filters.css";
import "../styles/complaint-list.css";

const STATUS_OPTIONS = [
  {
    value: "",
    label: "All statuses",
  },
  {
    value: "SUBMITTED",
    label: "Submitted",
  },
  {
    value: "AI_ANALYZING",
    label: "AI analyzing",
  },
  {
    value: "ASSIGNED",
    label: "Assigned",
  },
  {
    value: "ACKNOWLEDGED",
    label: "Acknowledged",
  },
  {
    value: "IN_PROGRESS",
    label: "In progress",
  },
  {
    value: "NEEDS_INFORMATION",
    label: "Needs information",
  },
  {
    value: "ESCALATED",
    label: "Escalated",
  },
  {
    value: "RESOLVED",
    label: "Resolved",
  },
  {
    value: "CLOSED",
    label: "Closed",
  },
  {
    value: "REOPENED",
    label: "Reopened",
  },
  {
    value: "REJECTED",
    label: "Rejected",
  },
];

const PRIORITY_OPTIONS = [
  {
    value: "",
    label: "All priorities",
  },
  {
    value: "CRITICAL",
    label: "Critical",
  },
  {
    value: "HIGH",
    label: "High",
  },
  {
    value: "MEDIUM",
    label: "Medium",
  },
  {
    value: "LOW",
    label: "Low",
  },
];

const SORT_OPTIONS = [
  {
    value: "newest",
    label: "Newest first",
  },
  {
    value: "oldest",
    label: "Oldest first",
  },
  {
    value: "priority",
    label: "Highest priority first",
  },
];

const PRIORITY_RANK = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
};

function getComplaintList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}

function getErrorMessage(requestError) {
  return (
    requestError?.response?.data?.detail ||
    "Unable to load complaints. Please try again."
  );
}

function ComplaintListPage() {
  const { user } = useAuth();

  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [sortOrder, setSortOrder] = useState("newest");

  const isOfficer = user?.role === "OFFICER";
  const isAdmin = user?.role === "ADMIN";

  async function loadComplaints() {
    setIsLoading(true);
    setError("");

    try {
      const data = await getComplaints();

      setComplaints(getComplaintList(data));
    } catch (requestError) {
      console.error("Failed to load complaints:", requestError);

      setError(getErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadComplaints();
  }, []);

  const departments = useMemo(() => {
    const names = complaints
      .map((complaint) => complaint.department_name)
      .filter(Boolean);

    return [...new Set(names)].sort((a, b) => a.localeCompare(b));
  }, [complaints]);

  const stats = useMemo(() => {
    const total = complaints.length;

    const active = complaints.filter(
      (complaint) =>
        !["RESOLVED", "CLOSED", "REJECTED"].includes(
          complaint.status,
        ),
    ).length;

    const resolved = complaints.filter((complaint) =>
      ["RESOLVED", "CLOSED"].includes(complaint.status),
    ).length;

    const urgent = complaints.filter((complaint) =>
      ["HIGH", "CRITICAL"].includes(complaint.priority),
    ).length;

    return {
      total,
      active,
      resolved,
      urgent,
    };
  }, [complaints]);

  const filteredComplaints = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    const filtered = complaints.filter((complaint) => {
      const searchableText = [
        complaint.ticket_number,
        complaint.title,
        complaint.description,
        complaint.department_name,
        complaint.category_name,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !normalizedSearch ||
        searchableText.includes(normalizedSearch);

      const matchesStatus =
        !statusFilter ||
        complaint.status === statusFilter;

      const matchesPriority =
        !priorityFilter ||
        complaint.priority === priorityFilter;

      const matchesDepartment =
        !departmentFilter ||
        complaint.department_name === departmentFilter;

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPriority &&
        matchesDepartment
      );
    });

    return [...filtered].sort((a, b) => {
      if (sortOrder === "oldest") {
        return (
          new Date(a.created_at) -
          new Date(b.created_at)
        );
      }

      if (sortOrder === "priority") {
        const priorityDifference =
          (PRIORITY_RANK[b.priority] || 0) -
          (PRIORITY_RANK[a.priority] || 0);

        if (priorityDifference !== 0) {
          return priorityDifference;
        }

        return (
          new Date(b.created_at) -
          new Date(a.created_at)
        );
      }

      return (
        new Date(b.created_at) -
        new Date(a.created_at)
      );
    });
  }, [
    complaints,
    searchTerm,
    statusFilter,
    priorityFilter,
    departmentFilter,
    sortOrder,
  ]);

  const hasActiveFilters =
    searchTerm.trim() !== "" ||
    statusFilter !== "" ||
    priorityFilter !== "" ||
    departmentFilter !== "" ||
    sortOrder !== "newest";

  function clearFilters() {
    setSearchTerm("");
    setStatusFilter("");
    setPriorityFilter("");
    setDepartmentFilter("");
    setSortOrder("newest");
  }

  const pageTitle = isAdmin
    ? "All complaints"
    : isOfficer
      ? "Assigned complaints"
      : "My complaints";

  const pageDescription = isAdmin
    ? "Monitor grievances across the entire CivicResolve system."
    : isOfficer
      ? "Review complaints currently assigned to you."
      : "Track every grievance you have submitted.";

  const detailBasePath = isOfficer
    ? "/dashboard/assigned"
    : "/dashboard/complaints";

  if (isLoading) {
    return (
      <section className="complaints-page">
        <div className="complaints-page-header">
          <div>
            <p className="dashboard-eyebrow">
              COMPLAINT TRACKING
            </p>

            <h1>{pageTitle}</h1>

            <p>{pageDescription}</p>
          </div>
        </div>

        <div className="complaints-loading">
          <div className="complaints-spinner" />

          <p>Loading complaints...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="complaints-page">
        <div className="complaints-page-header">
          <div>
            <p className="dashboard-eyebrow">
              COMPLAINT TRACKING
            </p>

            <h1>{pageTitle}</h1>

            <p>{pageDescription}</p>
          </div>
        </div>

        <div className="complaints-error">
          <strong>Unable to load complaints</strong>

          <p>{error}</p>

          <button
            type="button"
            onClick={loadComplaints}
          >
            Try again
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="complaints-page">
      <div className="complaints-page-header">
        <div>
          <p className="dashboard-eyebrow">
            COMPLAINT TRACKING
          </p>

          <h1>{pageTitle}</h1>

          <p>{pageDescription}</p>
        </div>

        <button
          type="button"
          className="complaints-refresh-button"
          onClick={loadComplaints}
          disabled={isLoading}
        >
          <span className="complaints-refresh-icon">
            ↻
          </span>

          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="complaint-stats-grid">
        <div className="complaint-stat-card">
          <span>Total</span>

          <strong>{stats.total}</strong>

          <small>Complaints visible to you</small>
        </div>

        <div className="complaint-stat-card">
          <span>Active</span>

          <strong>{stats.active}</strong>

          <small>Still being processed</small>
        </div>

        <div className="complaint-stat-card">
          <span>Resolved</span>

          <strong>{stats.resolved}</strong>

          <small>Resolved or closed</small>
        </div>

        <div className="complaint-stat-card">
          <span>High priority</span>

          <strong>{stats.urgent}</strong>

          <small>High or critical priority</small>
        </div>
      </div>

      <section className="complaint-filter-card">
        <div className="complaint-filter-header">
          <div>
            <p className="complaint-filter-eyebrow">
              FIND A COMPLAINT
            </p>

            <h2>Search and filter</h2>

            <p>
              Narrow down the complaint records visible
              to you.
            </p>
          </div>

          {hasActiveFilters && (
            <button
              type="button"
              className="complaint-clear-filters"
              onClick={clearFilters}
            >
              Clear filters
            </button>
          )}
        </div>

        <div className="complaint-filter-grid">
          <div className="complaint-filter-field complaint-filter-search">
            <label htmlFor="complaint-search">
              Search
            </label>

            <input
              id="complaint-search"
              type="search"
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
              placeholder="Ticket, title, description, department..."
            />
          </div>

          <div className="complaint-filter-field">
            <label htmlFor="complaint-status">
              Status
            </label>

            <select
              id="complaint-status"
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value)
              }
            >
              {STATUS_OPTIONS.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="complaint-filter-field">
            <label htmlFor="complaint-priority">
              Priority
            </label>

            <select
              id="complaint-priority"
              value={priorityFilter}
              onChange={(event) =>
                setPriorityFilter(event.target.value)
              }
            >
              {PRIORITY_OPTIONS.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="complaint-filter-field">
            <label htmlFor="complaint-department">
              Department
            </label>

            <select
              id="complaint-department"
              value={departmentFilter}
              onChange={(event) =>
                setDepartmentFilter(event.target.value)
              }
            >
              <option value="">All departments</option>

              {departments.map((department) => (
                <option
                  key={department}
                  value={department}
                >
                  {department}
                </option>
              ))}
            </select>
          </div>

          <div className="complaint-filter-field">
            <label htmlFor="complaint-sort">
              Sort
            </label>

            <select
              id="complaint-sort"
              value={sortOrder}
              onChange={(event) =>
                setSortOrder(event.target.value)
              }
            >
              {SORT_OPTIONS.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {complaints.length === 0 ? (
        <div className="complaints-empty">
          <div className="complaints-empty-icon">
            +
          </div>

          <h2>No complaints yet</h2>

          <p>
            {isOfficer
              ? "There are currently no complaints assigned to you."
              : isAdmin
                ? "There are currently no complaints in the system."
                : "You have not submitted any complaints yet."}
          </p>

          {!isOfficer && !isAdmin && (
            <Link
              to="/dashboard/complaints/new"
              className="complaint-empty-action"
            >
              Report your first issue
              <span>→</span>
            </Link>
          )}
        </div>
      ) : (
        <section className="complaint-records-card">
          <div className="complaint-records-header">
            <div>
              <p className="complaint-records-eyebrow">
                YOUR CASES
              </p>

              <h2>Complaint records</h2>

              <p>
                Follow the latest updates across your
                grievances.
              </p>
            </div>

            <div className="complaint-record-count">
              <strong>
                {filteredComplaints.length}
              </strong>

              <span>
                of {complaints.length}{" "}
                {complaints.length === 1
                  ? "complaint"
                  : "complaints"}
              </span>
            </div>
          </div>

          {filteredComplaints.length === 0 ? (
            <div className="complaint-filter-empty">
              <div className="complaint-filter-empty-icon">
                ?
              </div>

              <h3>No matching complaints</h3>

              <p>
                Try changing your search or filter
                criteria.
              </p>

              <button
                type="button"
                onClick={clearFilters}
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="complaint-record-list">
              {filteredComplaints.map((complaint) => (
                <article
                  key={complaint.id}
                  className="complaint-record"
                >
                  <div className="complaint-record-main">
                    <div className="complaint-record-top">
                      <div className="complaint-record-ticket">
                        <span>CASE</span>

                        <strong>
                          {complaint.ticket_number}
                        </strong>
                      </div>

                      <ComplaintStatusBadge
                        status={complaint.status}
                      />
                    </div>

                    <Link
                      to={`${detailBasePath}/${complaint.id}`}
                      className="complaint-record-title"
                    >
                      {complaint.title}
                    </Link>

                    <p className="complaint-record-description">
                      {truncateText(
                        complaint.description,
                        150,
                      )}
                    </p>

                    <div className="complaint-record-meta">
                      <span>
                        <strong>Department</strong>
                        {complaint.department_name ||
                          "Not assigned"}
                      </span>

                      <span>
                        <strong>Category</strong>
                        {complaint.category_name ||
                          "General"}
                      </span>

                      <span>
                        <strong>Submitted</strong>
                        {formatDate(
                          complaint.created_at,
                        )}
                      </span>

                      {complaint.updated_at && (
                        <span>
                          <strong>Updated</strong>
                          {formatDate(
                            complaint.updated_at,
                          )}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="complaint-record-side">
                    <div className="complaint-record-priority">
                      <span>Priority</span>

                      <ComplaintPriorityBadge
                        priority={complaint.priority}
                      />
                    </div>

                    <Link
                      to={`${detailBasePath}/${complaint.id}`}
                      className="complaint-record-action"
                    >
                      <span>View complaint</span>
                      <span>→</span>
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </section>
  );
}

function truncateText(text, maxLength) {
  if (!text) {
    return "";
  }

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength)}...`;
}

function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default ComplaintListPage;