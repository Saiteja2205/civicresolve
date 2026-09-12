function LoadingState({ message = "Loading..." }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-spinner" />
      <span>{message}</span>
    </div>
  );
}

export default LoadingState;