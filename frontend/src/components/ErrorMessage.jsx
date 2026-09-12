function ErrorMessage({ message, onRetry }) {
  if (!message) {
    return null;
  }

  return (
    <div className="error-message" role="alert">
      <div className="error-message-content">
        <strong>Something went wrong</strong>
        <span>{message}</span>
      </div>

      {onRetry && (
        <button type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;