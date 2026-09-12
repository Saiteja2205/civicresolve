const PRIORITY_LABELS = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  CRITICAL: "Critical",
};

function ComplaintPriorityBadge({ priority }) {
  const label = PRIORITY_LABELS[priority] ?? priority;

  const priorityClass = priority?.toLowerCase();

  return (
    <span
      className={`complaint-priority complaint-priority-${priorityClass}`}
    >
      {label}
    </span>
  );
}

export default ComplaintPriorityBadge;