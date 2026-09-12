function EmptyState({
  title = "Nothing here yet",
  message = "There is no data to display.",
  actionLabel,
  onAction,
}) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">—</div>

      <h3>{title}</h3>

      <p>{message}</p>

      {actionLabel && onAction && (
        <button type="button" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export default EmptyState;