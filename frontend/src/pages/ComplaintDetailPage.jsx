import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

import {
  acknowledgeComplaint,
  assignComplaint,
  closeComplaint,
  getComplaint,
  getComplaintAssignments,
  getComplaintHistory,
  getDepartments,
  getOfficers,
  resolveComplaint,
  startComplaint,
} from "../services/complaintService.js";

import ComplaintPriorityBadge from "../components/ComplaintPriorityBadge.jsx";
import ComplaintStatusBadge from "../components/ComplaintStatusBadge.jsx";
import CitizenResolutionFeedback from "../components/CitizenResolutionFeedback.jsx";

import "../styles/complaints.css";
import "../styles/complaint-actions.css";
import "../styles/admin-actions.css";
import "../styles/admin-assignment.css";
import "../styles/citizen-resolution.css";


function getBackPath(role) {
  if (role === "OFFICER") {
    return "/dashboard/assigned";
  }

  return "/dashboard/complaints";
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


function getActionLabel(status) {
  if (status === "ASSIGNED") {
    return "Acknowledge complaint";
  }

  if (status === "ACKNOWLEDGED") {
    return "Start work";
  }

  if (status === "IN_PROGRESS") {
    return "Resolve complaint";
  }

  return "";
}


function getActionDescription(status) {
  if (status === "ASSIGNED") {
    return "Confirm that you have received this complaint.";
  }

  if (status === "ACKNOWLEDGED") {
    return "Start working on this complaint.";
  }

  if (status === "IN_PROGRESS") {
    return "Mark this complaint as resolved.";
  }

  return "";
}


function getApiErrorMessage(requestError) {
  const responseData =
    requestError?.response?.data;

  if (typeof responseData === "string") {
    return responseData;
  }

  if (responseData?.detail) {
    return responseData.detail;
  }

  if (
    responseData &&
    typeof responseData === "object"
  ) {
    return Object.values(responseData)
      .flat()
      .join(" ");
  }

  return "Unable to update the complaint.";
}


function getList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


function ComplaintDetailPage() {
  const { complaintId } = useParams();
  const { user } = useAuth();

  const [complaint, setComplaint] =
    useState(null);

  const [history, setHistory] =
    useState([]);

  const [assignments, setAssignments] =
    useState([]);

  const [departments, setDepartments] =
    useState([]);

  const [officers, setOfficers] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [assignmentLoading, setAssignmentLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [actionError, setActionError] =
    useState("");

  const [assignmentError, setAssignmentError] =
    useState("");

  const [comment, setComment] =
    useState("");

  const [showActionBox, setShowActionBox] =
    useState(false);

  const [showCloseBox, setShowCloseBox] =
    useState(false);

  const [showAssignmentBox, setShowAssignmentBox] =
    useState(false);

  const [selectedDepartment, setSelectedDepartment] =
    useState("");

  const [selectedOfficer, setSelectedOfficer] =
    useState("");


  const isOfficer =
    user?.role === "OFFICER";

  const isAdmin =
    user?.role === "ADMIN";

  const isCitizen =
    user?.role === "USER";


  async function loadComplaint() {
    try {
      setLoading(true);
      setError("");

      const [
        complaintData,
        historyData,
      ] = await Promise.all([
        getComplaint(complaintId),
        getComplaintHistory(complaintId),
      ]);

      setComplaint(complaintData);

      setHistory(
        getList(historyData),
      );

      if (user?.role === "ADMIN") {
        const [
          assignmentData,
          departmentData,
        ] = await Promise.all([
          getComplaintAssignments(
            complaintId,
          ),
          getDepartments(),
        ]);

        setAssignments(
          getList(assignmentData),
        );

        setDepartments(
          getList(departmentData),
        );
      }
    } catch (requestError) {
      console.error(
        "Failed to load complaint:",
        requestError,
      );

      setError(
        "Unable to load this complaint.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadComplaint();
  }, [
    complaintId,
    user?.role,
  ]);


  async function refreshComplaintData(id) {
    const [
      updatedComplaint,
      updatedHistory,
    ] = await Promise.all([
      getComplaint(id),
      getComplaintHistory(id),
    ]);

    setComplaint(updatedComplaint);

    setHistory(
      getList(updatedHistory),
    );

    if (user?.role === "ADMIN") {
      const assignmentData =
        await getComplaintAssignments(id);

      setAssignments(
        getList(assignmentData),
      );
    }
  }


  async function loadOfficers(
    departmentId,
  ) {
    if (!departmentId) {
      setOfficers([]);
      setSelectedOfficer("");
      return;
    }

    try {
      const data =
        await getOfficers(
          departmentId,
        );

      setOfficers(
        getList(data),
      );

      setSelectedOfficer("");
    } catch (requestError) {
      console.error(
        "Failed to load officers:",
        requestError,
      );

      setAssignmentError(
        "Unable to load officers for this department.",
      );

      setOfficers([]);
    }
  }


  function handleDepartmentChange(
    event,
  ) {
    const departmentId =
      event.target.value;

    setSelectedDepartment(
      departmentId,
    );

    setAssignmentError("");

    loadOfficers(
      departmentId,
    );
  }


  async function handleAssignment() {
    if (!complaint?.id) {
      setAssignmentError(
        "Complaint ID is missing. Please reload the page.",
      );
      return;
    }

    if (!selectedDepartment) {
      setAssignmentError(
        "Please select a department.",
      );
      return;
    }

    if (!selectedOfficer) {
      setAssignmentError(
        "Please select an officer.",
      );
      return;
    }

    setAssignmentLoading(true);
    setAssignmentError("");

    try {
      await assignComplaint(
        complaint.id,
        {
          officer_id:
            Number(selectedOfficer),

          department_id:
            Number(selectedDepartment),

          reason:
            "Officer selected by administrator.",
        },
      );

      await refreshComplaintData(
        complaint.id,
      );

      setShowAssignmentBox(false);
      setSelectedDepartment("");
      setSelectedOfficer("");
      setOfficers([]);
    } catch (requestError) {
      console.error(
        "Complaint assignment failed:",
        requestError,
      );

      setAssignmentError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setAssignmentLoading(false);
    }
  }


  async function handleOfficerAction() {
    if (!complaint?.id) {
      setActionError(
        "Complaint ID is missing. Please reload the page.",
      );
      return;
    }

    setActionLoading(true);
    setActionError("");

    try {
      if (complaint.status === "ASSIGNED") {
        await acknowledgeComplaint(
          complaint.id,
          comment,
        );
      } else if (
        complaint.status === "ACKNOWLEDGED"
      ) {
        await startComplaint(
          complaint.id,
          comment,
        );
      } else if (
        complaint.status === "IN_PROGRESS"
      ) {
        await resolveComplaint(
          complaint.id,
          comment,
        );
      } else {
        return;
      }

      await refreshComplaintData(
        complaint.id,
      );

      setComment("");
      setShowActionBox(false);
    } catch (requestError) {
      console.error(
        "Complaint action failed:",
        requestError,
      );

      setActionError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setActionLoading(false);
    }
  }


  async function handleCloseComplaint() {
    if (!complaint?.id) {
      setActionError(
        "Complaint ID is missing. Please reload the page.",
      );
      return;
    }

    if (complaint.status !== "RESOLVED") {
      setActionError(
        "Only resolved complaints can be closed.",
      );
      return;
    }

    setActionLoading(true);
    setActionError("");

    try {
      await closeComplaint(
        complaint.id,
        comment,
      );

      await refreshComplaintData(
        complaint.id,
      );

      setComment("");
      setShowCloseBox(false);
    } catch (requestError) {
      console.error(
        "Complaint close action failed:",
        requestError,
      );

      setActionError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setActionLoading(false);
    }
  }


  if (loading) {
    return (
      <section className="complaint-detail-page">
        <div className="complaint-detail-loading">
          Loading complaint...
        </div>
      </section>
    );
  }


  if (error || !complaint) {
    return (
      <section className="complaint-detail-page">
        <div className="complaint-detail-error">
          <h2>
            Complaint unavailable
          </h2>

          <p>
            {error ||
              "The requested complaint could not be found."}
          </p>

          <Link
            to={getBackPath(
              user?.role,
            )}
            className="complaint-back-link"
          >
            Back to complaints
          </Link>
        </div>
      </section>
    );
  }


  const actionLabel =
    getActionLabel(
      complaint.status,
    );

  const actionDescription =
    getActionDescription(
      complaint.status,
    );


  const canTakeOfficerAction =
    isOfficer &&
    [
      "ASSIGNED",
      "ACKNOWLEDGED",
      "IN_PROGRESS",
    ].includes(
      complaint.status,
    );


  const canCloseComplaint =
    isAdmin &&
    complaint.status ===
      "RESOLVED";


  const canManageAssignment =
    isAdmin &&
    [
      "SUBMITTED",
      "AI_ANALYZING",
      "REOPENED",
      "ASSIGNED",
    ].includes(
      complaint.status,
    );


  const activeAssignment =
    assignments.find(
      (assignment) =>
        !assignment.unassigned_at,
    );


  return (
    <section className="complaint-detail-page">

      <div className="complaint-detail-topbar">
        <Link
          to={getBackPath(
            user?.role,
          )}
          className="complaint-back-link"
        >
          ← Back
        </Link>
      </div>


      <div className="complaint-detail-header">
        <div>
          <p className="complaint-detail-eyebrow">
            COMPLAINT
          </p>

          <div className="complaint-ticket-large">
            {complaint.ticket_number}
          </div>

          <h1>
            {complaint.title}
          </h1>

          <p className="complaint-detail-submitted">
            Submitted{" "}
            {formatDate(
              complaint.created_at,
            )}
          </p>
        </div>


        <div className="complaint-detail-badges">
          <ComplaintStatusBadge
            status={
              complaint.status
            }
          />

          <ComplaintPriorityBadge
            priority={
              complaint.priority
            }
          />
        </div>
      </div>


      {canManageAssignment && (
        <section className="admin-assignment-card">

          <div className="admin-assignment-header">
            <div>
              <p className="admin-assignment-eyebrow">
                ADMINISTRATOR CONTROL
              </p>

              <h2>
                Officer assignment
              </h2>

              <p>
                Review the current officer and
                assign the complaint to another
                active officer when necessary.
              </p>
            </div>


            {!showAssignmentBox && (
              <button
                type="button"
                className="admin-assignment-primary"
                onClick={() => {
                  setShowAssignmentBox(
                    true,
                  );

                  setAssignmentError(
                    "",
                  );
                }}
              >
                {activeAssignment
                  ? "Reassign officer"
                  : "Assign officer"}
              </button>
            )}
          </div>


          {activeAssignment && (
            <div className="admin-current-assignment">

              <span>
                Currently assigned to
              </span>

              <strong>
                {activeAssignment.officer_email ||
                  `Officer #${activeAssignment.officer}`}
              </strong>

              <small>
                {activeAssignment.department_name ||
                  "Department unavailable"}
              </small>

            </div>
          )}


          {showAssignmentBox && (
            <div className="admin-assignment-form">

              <div className="admin-assignment-field">
                <label htmlFor="assignment-department">
                  Department
                </label>

                <select
                  id="assignment-department"
                  value={
                    selectedDepartment
                  }
                  onChange={
                    handleDepartmentChange
                  }
                  disabled={
                    assignmentLoading
                  }
                >
                  <option value="">
                    Select department
                  </option>

                  {departments.map(
                    (department) => (
                      <option
                        key={
                          department.id
                        }
                        value={
                          department.id
                        }
                      >
                        {department.name}
                      </option>
                    ),
                  )}
                </select>
              </div>


              <div className="admin-assignment-field">
                <label htmlFor="assignment-officer">
                  Officer
                </label>

                <select
                  id="assignment-officer"
                  value={
                    selectedOfficer
                  }
                  onChange={(event) =>
                    setSelectedOfficer(
                      event.target.value,
                    )
                  }
                  disabled={
                    assignmentLoading ||
                    !selectedDepartment
                  }
                >
                  <option value="">
                    {!selectedDepartment
                      ? "Select department first"
                      : officers.length ===
                          0
                        ? "No active officers"
                        : "Select officer"}
                  </option>

                  {officers.map(
                    (officer) => (
                      <option
                        key={
                          officer.id
                        }
                        value={
                          officer.id
                        }
                      >
                        {officer.email}
                      </option>
                    ),
                  )}
                </select>
              </div>


              {assignmentError && (
                <p
                  className="admin-assignment-error"
                  role="alert"
                >
                  {assignmentError}
                </p>
              )}


              <div className="admin-assignment-buttons">

                <button
                  type="button"
                  className="admin-assignment-cancel"
                  onClick={() => {
                    setShowAssignmentBox(
                      false,
                    );

                    setSelectedDepartment(
                      "",
                    );

                    setSelectedOfficer(
                      "",
                    );

                    setOfficers([]);

                    setAssignmentError(
                      "",
                    );
                  }}
                  disabled={
                    assignmentLoading
                  }
                >
                  Cancel
                </button>


                <button
                  type="button"
                  className="admin-assignment-primary"
                  onClick={
                    handleAssignment
                  }
                  disabled={
                    assignmentLoading
                  }
                >
                  {assignmentLoading
                    ? "Assigning..."
                    : activeAssignment
                      ? "Confirm reassignment"
                      : "Confirm assignment"}
                </button>

              </div>

            </div>
          )}

        </section>
      )}


      {canTakeOfficerAction && (
        <section className="complaint-action-card">

          <div className="complaint-action-content">

            <p className="complaint-action-eyebrow">
              OFFICER ACTION
            </p>

            <h2>
              {actionLabel}
            </h2>

            <p>
              {actionDescription}
            </p>

          </div>


          {!showActionBox ? (
            <button
              type="button"
              className="complaint-action-primary"
              onClick={() =>
                setShowActionBox(
                  true,
                )
              }
            >
              {actionLabel}
            </button>
          ) : (
            <div className="complaint-action-box">

              <label htmlFor="action-comment">
                Comment
                <span>
                  Optional
                </span>
              </label>

              <textarea
                id="action-comment"
                value={comment}
                onChange={(event) =>
                  setComment(
                    event.target.value,
                  )
                }
                placeholder={
                  complaint.status ===
                  "IN_PROGRESS"
                    ? "Example: The network issue has been fixed and connectivity has been restored."
                    : "Add an optional note about this action."
                }
                rows={4}
                disabled={
                  actionLoading
                }
              />


              {actionError && (
                <p
                  className="complaint-action-error"
                  role="alert"
                >
                  {actionError}
                </p>
              )}


              <div className="complaint-action-buttons">

                <button
                  type="button"
                  className="complaint-action-cancel"
                  onClick={() => {
                    setShowActionBox(
                      false,
                    );

                    setComment("");

                    setActionError(
                      "",
                    );
                  }}
                  disabled={
                    actionLoading
                  }
                >
                  Cancel
                </button>


                <button
                  type="button"
                  className="complaint-action-primary"
                  onClick={
                    handleOfficerAction
                  }
                  disabled={
                    actionLoading
                  }
                >
                  {actionLoading
                    ? "Updating..."
                    : `Confirm: ${actionLabel}`}
                </button>

              </div>

            </div>
          )}

        </section>
      )}


      {canCloseComplaint && (
        <section className="admin-close-card">

          <div className="admin-close-content">

            <p className="admin-close-eyebrow">
              ADMINISTRATOR ACTION
            </p>

            <h2>
              Close complaint
            </h2>

            <p>
              This complaint has been resolved
              by the officer. Closing it will
              complete the complaint lifecycle.
            </p>

          </div>


          {!showCloseBox ? (
            <button
              type="button"
              className="admin-close-primary"
              onClick={() => {
                setShowCloseBox(
                  true,
                );

                setActionError(
                  "",
                );
              }}
            >
              Close complaint
            </button>
          ) : (
            <div className="admin-close-box">

              <label htmlFor="close-comment">
                Closing comment
                <span>
                  Optional
                </span>
              </label>

              <textarea
                id="close-comment"
                value={comment}
                onChange={(event) =>
                  setComment(
                    event.target.value,
                  )
                }
                placeholder="Example: Resolution verified and complaint closed."
                rows={4}
                disabled={
                  actionLoading
                }
              />


              {actionError && (
                <p
                  className="admin-close-error"
                  role="alert"
                >
                  {actionError}
                </p>
              )}


              <div className="admin-close-buttons">

                <button
                  type="button"
                  className="admin-close-cancel"
                  onClick={() => {
                    setShowCloseBox(
                      false,
                    );

                    setComment("");

                    setActionError(
                      "",
                    );
                  }}
                  disabled={
                    actionLoading
                  }
                >
                  Cancel
                </button>


                <button
                  type="button"
                  className="admin-close-primary"
                  onClick={
                    handleCloseComplaint
                  }
                  disabled={
                    actionLoading
                  }
                >
                  {actionLoading
                    ? "Closing..."
                    : "Confirm: Close complaint"}
                </button>

              </div>

            </div>
          )}

        </section>
      )}


      {/* DAY 11 — CITIZEN RESOLUTION FEEDBACK */}

      {isCitizen &&
        complaint.status === "RESOLVED" && (
          <CitizenResolutionFeedback
            complaint={complaint}
            onReopened={async () => {
              await refreshComplaintData(
                complaint.id,
              );
            }}
          />
        )}


      <div className="complaint-detail-grid">

        <div className="complaint-detail-main">

          <article className="complaint-detail-card">

            <div className="complaint-detail-card-header">
              <h2>
                Description
              </h2>
            </div>

            <div className="complaint-description">
              {complaint.description}
            </div>

          </article>


          <article className="complaint-detail-card">

            <div className="complaint-detail-card-header">

              <h2>
                Status history
              </h2>

              <span>
                {history.length} events
              </span>

            </div>


            {history.length === 0 ? (
              <div className="complaint-history-empty">
                No history available.
              </div>
            ) : (
              <div className="complaint-timeline">

                {history.map(
                  (item, index) => (
                    <div
                      className="complaint-timeline-item"
                      key={
                        item.id ||
                        `${item.created_at}-${index}`
                      }
                    >

                      <div className="complaint-timeline-marker" />


                      <div className="complaint-timeline-content">

                        <div className="complaint-timeline-header">

                          <strong>
                            {item.new_status}
                          </strong>

                          <span>
                            {formatDate(
                              item.created_at,
                            )}
                          </span>

                        </div>


                        <p>
                          {item.comment ||
                            "Status updated."}
                        </p>


                        {item.changed_by_email && (
                          <small>
                            Updated by{" "}
                            {
                              item.changed_by_email
                            }
                          </small>
                        )}

                      </div>

                    </div>
                  ),
                )}

              </div>
            )}

          </article>

        </div>


        <aside className="complaint-detail-sidebar">

          <article className="complaint-detail-card">

            <div className="complaint-detail-card-header">
              <h2>
                Complaint information
              </h2>
            </div>


            <dl className="complaint-info-list">

              <div>
                <dt>
                  Category
                </dt>

                <dd>
                  {complaint.category_name ||
                    "—"}
                </dd>
              </div>


              <div>
                <dt>
                  Department
                </dt>

                <dd>
                  {complaint.department_name ||
                    "—"}
                </dd>
              </div>


              <div>
                <dt>
                  Priority
                </dt>

                <dd>
                  <ComplaintPriorityBadge
                    priority={
                      complaint.priority
                    }
                  />
                </dd>
              </div>


              <div>
                <dt>
                  Location
                </dt>

                <dd>
                  {complaint.location ||
                    "Not provided"}
                </dd>
              </div>


              <div>
                <dt>
                  Latitude
                </dt>

                <dd>
                  {complaint.latitude ??
                    "—"}
                </dd>
              </div>


              <div>
                <dt>
                  Longitude
                </dt>

                <dd>
                  {complaint.longitude ??
                    "—"}
                </dd>
              </div>


              <div>
                <dt>
                  Last updated
                </dt>

                <dd>
                  {formatDate(
                    complaint.updated_at,
                  )}
                </dd>
              </div>

            </dl>

          </article>

        </aside>

      </div>


      {complaint.status ===
        "RESOLVED" && (
        <div className="complaint-resolution-notice">

          <strong>
            Complaint resolved
          </strong>

          <span>
            This complaint has been marked
            as resolved and is waiting for
            administrator closure.
          </span>

        </div>
      )}


      {complaint.status ===
        "CLOSED" && (
        <div className="complaint-resolution-notice">

          <strong>
            Complaint closed
          </strong>

          <span>
            This complaint has completed its
            resolution lifecycle.
          </span>

        </div>
      )}


      {complaint.status ===
        "REOPENED" && (
        <div className="complaint-resolution-notice">

          <strong>
            Complaint reopened
          </strong>

          <span>
            The citizen has indicated that
            the previous resolution was not
            satisfactory. The complaint is
            waiting for reassignment.
          </span>

        </div>
      )}


      {complaint.status ===
        "ESCALATED" && (
        <div className="complaint-escalation-notice">

          <strong>
            SLA escalation
          </strong>

          <span>
            This complaint has exceeded its
            resolution SLA and requires
            attention.
          </span>

        </div>
      )}

    </section>
  );
}


export default ComplaintDetailPage;