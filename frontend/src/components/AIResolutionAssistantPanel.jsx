import { useState } from "react";


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

  return "Unable to generate AI resolution assistance.";
}


function formatConfidence(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return `${Number(value).toFixed(0)}%`;
}


function AIResolutionAssistantPanel({
  complaintId,
  canUseAssistant,
  onGenerated,
}) {
  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  async function generateAssistance() {
    if (!complaintId) {
      setError(
        "Complaint ID is missing. Please reload the page.",
      );

      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await onGenerated(
        complaintId,
      );

      setResult(response);
    } catch (requestError) {
      console.error(
        "AI resolution assistant failed:",
        requestError,
      );

      setResult(null);

      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setLoading(false);
    }
  }


  if (!canUseAssistant) {
    return null;
  }


  return (
    <section className="ai-resolution-assistant-card">

      <div className="ai-resolution-assistant-header">
        <div>
          <p className="ai-resolution-assistant-eyebrow">
            AI DECISION SUPPORT
          </p>

          <h2>
            Resolution assistant
          </h2>

          <p>
            Generate a draft resolution plan using
            the complaint details, history, evidence
            and SLA information.
          </p>
        </div>

        <div className="ai-resolution-assistant-icon">
          AI
        </div>
      </div>


      {!result && !loading && (
        <div className="ai-resolution-assistant-intro">
          <div className="ai-resolution-assistant-intro-grid">

            <div>
              <span>
                01
              </span>

              <strong>
                Understand
              </strong>

              <p>
                Reviews the complaint and available
                operational information.
              </p>
            </div>


            <div>
              <span>
                02
              </span>

              <strong>
                Recommend
              </strong>

              <p>
                Suggests practical actions for the
                assigned officer.
              </p>
            </div>


            <div>
              <span>
                03
              </span>

              <strong>
                Draft
              </strong>

              <p>
                Creates a response draft that can be
                reviewed before sending.
              </p>
            </div>

          </div>


          <div className="ai-resolution-assistant-actions">
            <button
              type="button"
              className="ai-resolution-assistant-primary"
              onClick={
                generateAssistance
              }
            >
              Generate AI assistance
            </button>
          </div>
        </div>
      )}


      {loading && (
        <div
          className="ai-resolution-assistant-loading"
          aria-live="polite"
        >
          <div className="ai-resolution-assistant-spinner" />

          <div>
            <strong>
              Generating resolution assistance...
            </strong>

            <p>
              AI is reviewing the complaint context.
              This may take a few seconds.
            </p>
          </div>
        </div>
      )}


      {error && (
        <div
          className="ai-resolution-assistant-error"
          role="alert"
        >
          <div>
            <strong>
              Unable to generate assistance
            </strong>

            <p>
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={
              generateAssistance
            }
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}


      {result && !loading && (
        <div className="ai-resolution-assistant-result">

          <div className="ai-resolution-assistant-result-header">
            <div>
              <span>
                GENERATED DRAFT
              </span>

              <h3>
                AI resolution guidance
              </h3>
            </div>

            <div className="ai-resolution-assistant-confidence">
              <span>
                Confidence
              </span>

              <strong>
                {formatConfidence(
                  result.confidence_score,
                )}
              </strong>
            </div>
          </div>


          <article className="ai-resolution-assistant-section">
            <div className="ai-resolution-assistant-section-heading">
              <span>
                01
              </span>

              <h4>
                Resolution draft
              </h4>
            </div>

            <p className="ai-resolution-assistant-draft">
              {result.resolution_draft ||
                "No resolution draft was generated."}
            </p>
          </article>


          <article className="ai-resolution-assistant-section">
            <div className="ai-resolution-assistant-section-heading">
              <span>
                02
              </span>

              <h4>
                Recommended actions
              </h4>
            </div>

            {Array.isArray(
              result.recommended_actions,
            ) &&
            result.recommended_actions.length > 0 ? (
              <ol className="ai-resolution-assistant-actions-list">
                {result.recommended_actions.map(
                  (action, index) => (
                    <li
                      key={`${action}-${index}`}
                    >
                      <span>
                        {index + 1}
                      </span>

                      <p>
                        {action}
                      </p>
                    </li>
                  ),
                )}
              </ol>
            ) : (
              <p className="ai-resolution-assistant-empty">
                No specific actions were generated.
              </p>
            )}
          </article>


          <article className="ai-resolution-assistant-section">
            <div className="ai-resolution-assistant-section-heading">
              <span>
                03
              </span>

              <h4>
                Citizen response draft
              </h4>
            </div>

            <div className="ai-resolution-assistant-response">
              {result.citizen_response_draft ||
                "No citizen response draft was generated."}
            </div>
          </article>


          <article className="ai-resolution-assistant-section">
            <div className="ai-resolution-assistant-section-heading">
              <span>
                04
              </span>

              <h4>
                Evidence basis
              </h4>
            </div>

            {Array.isArray(
              result.basis,
            ) &&
            result.basis.length > 0 ? (
              <div className="ai-resolution-assistant-basis">
                {result.basis.map(
                  (item, index) => (
                    <span
                      key={`${item}-${index}`}
                    >
                      {item}
                    </span>
                  ),
                )}
              </div>
            ) : (
              <p className="ai-resolution-assistant-empty">
                No basis information was returned.
              </p>
            )}
          </article>


          <div className="ai-resolution-assistant-disclaimer">
            <strong>
              Review before use
            </strong>

            <p>
              This is an AI-generated draft for
              officer/admin decision support. It does
              not claim that any action has been
              completed and does not resolve the
              complaint automatically.
            </p>
          </div>


          <div className="ai-resolution-assistant-footer">
            <div>
              <span>
                AI model
              </span>

              <strong>
                {result.model ||
                  "Configured AI provider"}
              </strong>
            </div>

            <button
              type="button"
              className="ai-resolution-assistant-secondary"
              onClick={
                generateAssistance
              }
              disabled={loading}
            >
              Regenerate
            </button>
          </div>

        </div>
      )}

    </section>
  );
}


export default AIResolutionAssistantPanel;