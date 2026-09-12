function ErrorMessage({ message, onRetry }) {
  if (!message) {
    return null;
  }

  return (
    <div
      className="error-message"
      role="alert"
      aria-live="assertive"
    >
      <div className="error-message-content">
        <strong>Something went wrong</strong>

        <span>{message}</span>
      </div>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          aria-label="Try loading the information again"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export default ErrorMessage;