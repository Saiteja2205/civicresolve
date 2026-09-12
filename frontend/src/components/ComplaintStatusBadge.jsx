const STATUS_LABELS = {
  SUBMITTED: "Submitted",
  AI_ANALYZING: "AI Analyzing",
  ASSIGNED: "Assigned",
  ACKNOWLEDGED: "Acknowledged",
  IN_PROGRESS: "In Progress",
  NEEDS_INFORMATION: "Needs Information",
  ESCALATED: "Escalated",
  RESOLVED: "Resolved",
  CLOSED: "Closed",
  REOPENED: "Reopened",
  REJECTED: "Rejected",
};

function ComplaintStatusBadge({ status }) {
  const label = STATUS_LABELS[status] ?? status;

  const statusClass = status
    ?.toLowerCase()
    .replaceAll("_", "-");

  return (
    <span
      className={`complaint-status complaint-status-${statusClass}`}
    >
      <span className="complaint-status-dot" />
      {label}
    </span>
  );
}

export default ComplaintStatusBadge;