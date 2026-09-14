function getRiskClass(riskLevel) {
  switch (riskLevel) {
    case "CRITICAL":
      return "critical";

    case "HIGH":
      return "high";

    case "MEDIUM":
      return "medium";

    case "LOW":
    default:
      return "low";
  }
}


function getProgressClass(percent) {
  if (percent >= 100) {
    return "breached";
  }

  if (percent >= 75) {
    return "warning";
  }

  return "normal";
}


function formatHours(hours) {
  if (hours === null || hours === undefined) {
    return "—";
  }

  if (hours < 0) {
    return `${Math.abs(hours).toFixed(1)}h overdue`;
  }

  if (hours < 1) {
    return `${Math.round(hours * 60)}m remaining`;
  }

  if (hours < 24) {
    return `${hours.toFixed(1)}h remaining`;
  }

  return `${(hours / 24).toFixed(1)}d remaining`;
}


function formatPercent(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  return `${Number(value).toFixed(1)}%`;
}


function clampPercent(value) {
  if (value === null || value === undefined) {
    return 0;
  }

  return Math.min(100, Math.max(0, Number(value)));
}


function ComplaintSLARiskPanel({
  risk,
  loading = false,
  error = "",
  onRetry,
}) {
  if (loading) {
    return (
      <section className="complaint-sla-risk-card">
        <div className="complaint-sla-risk-header">
          <div>
            <p className="complaint-sla-risk-eyebrow">
              PREDICTIVE SLA MONITORING
            </p>

            <h2>
              SLA breach risk
            </h2>
          </div>
        </div>

        <div className="complaint-sla-risk-loading">
          <div className="complaint-sla-risk-spinner" />

          <div>
            <strong>
              Calculating SLA risk...
            </strong>

            <p>
              Analysing SLA progress, urgency,
              activity and workload.
            </p>
          </div>
        </div>
      </section>
    );
  }


  if (error) {
    return (
      <section className="complaint-sla-risk-card">
        <div className="complaint-sla-risk-header">
          <div>
            <p className="complaint-sla-risk-eyebrow">
              PREDICTIVE SLA MONITORING
            </p>

            <h2>
              SLA breach risk
            </h2>
          </div>
        </div>

        <div
          className="complaint-sla-risk-error"
          role="alert"
        >
          <div>
            <strong>
              SLA risk unavailable
            </strong>

            <p>
              {error}
            </p>
          </div>

          {onRetry && (
            <button
              type="button"
              className="complaint-sla-risk-retry"
              onClick={onRetry}
            >
              Retry
            </button>
          )}
        </div>
      </section>
    );
  }


  if (!risk) {
    return null;
  }


  const riskClass =
    getRiskClass(risk.risk_level);

  const resolutionProgress =
    clampPercent(
      risk.resolution_progress_percent,
    );

  const responseProgress =
    clampPercent(
      risk.response_progress_percent,
    );

  const resolutionProgressClass =
    getProgressClass(
      risk.resolution_progress_percent,
    );

  const responseProgressClass =
    getProgressClass(
      risk.response_progress_percent,
    );


  return (
    <section
      className={`complaint-sla-risk-card risk-${riskClass}`}
    >
      <div className="complaint-sla-risk-header">
        <div>
          <p className="complaint-sla-risk-eyebrow">
            PREDICTIVE SLA MONITORING
          </p>

          <h2>
            SLA breach risk
          </h2>

          <p className="complaint-sla-risk-description">
            Explainable prediction based on the
            complaint's current progress and
            operational signals.
          </p>
        </div>

        <div
          className={`complaint-sla-risk-badge risk-${riskClass}`}
        >
          <span>
            {risk.risk_level || "LOW"}
          </span>

          <strong>
            {risk.risk_score ?? 0}
          </strong>
        </div>
      </div>


      <div className="complaint-sla-risk-summary">
        <div className="complaint-sla-risk-score">
          <div
            className="complaint-sla-risk-score-track"
            aria-hidden="true"
          >
            <div
              className="complaint-sla-risk-score-fill"
              style={{
                width: `${clampPercent(
                  risk.risk_score,
                )}%`,
              }}
            />
          </div>

          <div className="complaint-sla-risk-score-label">
            <strong>
              {risk.risk_score ?? 0}/100
            </strong>

            <span>
              {risk.risk_label ||
                "Current breach risk"}
            </span>
          </div>
        </div>

        <div className="complaint-sla-risk-action">
          <span>
            Recommended action
          </span>

          <strong>
            {risk.recommended_action ||
              "Continue normal monitoring."}
          </strong>
        </div>
      </div>


      <div className="complaint-sla-progress-grid">
        <article className="complaint-sla-progress-card">
          <div className="complaint-sla-progress-heading">
            <div>
              <span>
                Resolution SLA
              </span>

              <strong>
                {formatPercent(
                  risk.resolution_progress_percent,
                )}
              </strong>
            </div>

            <small
              className={
                risk.resolution_breached
                  ? "sla-breached"
                  : ""
              }
            >
              {risk.resolution_breached
                ? "Breached"
                : formatHours(
                    risk.resolution_hours_remaining,
                  )}
            </small>
          </div>

          <div className="complaint-sla-progress-track">
            <div
              className={`complaint-sla-progress-fill ${resolutionProgressClass}`}
              style={{
                width: `${resolutionProgress}%`,
              }}
            />
          </div>

          <p>
            Time consumed toward the
            resolution deadline.
          </p>
        </article>


        <article className="complaint-sla-progress-card">
          <div className="complaint-sla-progress-heading">
            <div>
              <span>
                Response SLA
              </span>

              <strong>
                {formatPercent(
                  risk.response_progress_percent,
                )}
              </strong>
            </div>

            <small
              className={
                risk.response_breached
                  ? "sla-breached"
                  : ""
              }
            >
              {risk.response_breached
                ? "Breached"
                : formatHours(
                    risk.response_hours_remaining,
                  )}
            </small>
          </div>

          <div className="complaint-sla-progress-track">
            <div
              className={`complaint-sla-progress-fill ${responseProgressClass}`}
              style={{
                width: `${responseProgress}%`,
              }}
            />
          </div>

          <p>
            Time consumed toward the
            response deadline.
          </p>
        </article>
      </div>


      <div className="complaint-sla-risk-metrics">
        <div>
          <span>
            Officer workload
          </span>

          <strong>
            {risk.officer_workload ?? "—"}
          </strong>

          <small>
            active complaints
          </small>
        </div>

        <div>
          <span>
            Department breach rate
          </span>

          <strong>
            {formatPercent(
              risk.department_breach_rate_percent,
            )}
          </strong>

          <small>
            historical performance
          </small>
        </div>

        <div>
          <span>
            AI urgency
          </span>

          <strong>
            {formatPercent(
              risk.urgency_score,
            )}
          </strong>

          <small>
            complaint urgency
          </small>
        </div>
      </div>


      <div className="complaint-sla-risk-factors">
        <div className="complaint-sla-risk-section-heading">
          <div>
            <span>
              Explainability
            </span>

            <h3>
              Risk factors
            </h3>
          </div>
        </div>

        {Array.isArray(risk.factors) &&
        risk.factors.length > 0 ? (
          <ul>
            {risk.factors.map(
              (factor, index) => (
                <li
                  key={`${factor}-${index}`}
                >
                  <span className="complaint-sla-risk-factor-dot" />

                  <span>
                    {factor}
                  </span>
                </li>
              ),
            )}
          </ul>
        ) : (
          <p className="complaint-sla-risk-no-factors">
            No elevated risk factors detected.
          </p>
        )}
      </div>


      <div className="complaint-sla-risk-footer">
        <span>
          Prediction basis
        </span>

        <p>
          {risk.prediction_basis ||
            "Explainable SLA risk scoring."}
        </p>

        {risk.as_of && (
          <small>
            Calculated{" "}
            {new Date(
              risk.as_of,
            ).toLocaleString([], {
              day: "2-digit",
              month: "short",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </small>
        )}
      </div>
    </section>
  );
}


export default ComplaintSLARiskPanel;