import { useState } from "react";

import { runAIEvaluation } from "../services/complaintService.js";

import "../styles/ai-evaluation.css";


function formatPercentage(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return `${Number(value).toFixed(2)}%`;
}


function formatNumber(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return Number(value).toFixed(2);
}


function getResultClass(passed) {
  return passed
    ? "ai-evaluation-result-pass"
    : "ai-evaluation-result-fail";
}


function AIEvaluationPanel() {
  const [report, setReport] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleRunEvaluation() {
    setLoading(true);
    setError("");

    try {
      const data =
        await runAIEvaluation();

      setReport(data);
    } catch (requestError) {
      console.error(
        "AI evaluation failed:",
        requestError,
      );

      const responseData =
        requestError?.response?.data;

      setError(
        responseData?.detail ||
          "Unable to run the AI benchmark. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <section className="ai-evaluation-card">

      <header className="ai-evaluation-header">
        <div>
          <p className="ai-evaluation-eyebrow">
            AI QUALITY ASSURANCE
          </p>

          <h2>
            AI evaluation & benchmarking
          </h2>

          <p>
            Run the CivicResolve benchmark against
            representative grievance cases to measure
            classification, priority and urgency performance.
          </p>
        </div>

        <div className="ai-evaluation-badge">
          AI
        </div>
      </header>


      <div className="ai-evaluation-controls">
        <div>
          <strong>
            Benchmark suite
          </strong>

          <span>
            6 representative complaint cases
          </span>
        </div>

        <button
          type="button"
          className="ai-evaluation-run-button"
          onClick={
            handleRunEvaluation
          }
          disabled={loading}
        >
          {loading
            ? "Running benchmark..."
            : "Run AI benchmark"}
        </button>
      </div>


      {loading && (
        <div
          className="ai-evaluation-loading"
          aria-live="polite"
        >
          <div className="ai-evaluation-spinner" />

          <div>
            <strong>
              Evaluating AI predictions...
            </strong>

            <p>
              Each benchmark case is being processed
              through the configured AI analysis pipeline.
            </p>
          </div>
        </div>
      )}


      {error && (
        <div
          className="ai-evaluation-error"
          role="alert"
        >
          <div>
            <strong>
              Benchmark failed
            </strong>

            <p>
              {error}
            </p>
          </div>

          <button
            type="button"
            onClick={
              handleRunEvaluation
            }
            disabled={loading}
          >
            Retry
          </button>
        </div>
      )}


      {report && !loading && (
        <div className="ai-evaluation-results">

          <div className="ai-evaluation-metric-grid">

            <article className="ai-evaluation-metric">
              <span>
                Category accuracy
              </span>

              <strong>
                {formatPercentage(
                  report.category_accuracy_percent,
                )}
              </strong>

              <small>
                Correct predicted categories
              </small>
            </article>


            <article className="ai-evaluation-metric">
              <span>
                Priority accuracy
              </span>

              <strong>
                {formatPercentage(
                  report.priority_accuracy_percent,
                )}
              </strong>

              <small>
                Correct predicted priorities
              </small>
            </article>


            <article className="ai-evaluation-metric">
              <span>
                Urgency MAE
              </span>

              <strong>
                {formatNumber(
                  report.urgency_mae,
                )}
              </strong>

              <small>
                Lower is better
              </small>
            </article>


            <article className="ai-evaluation-metric">
              <span>
                Overall pass rate
              </span>

              <strong>
                {formatPercentage(
                  report.overall_pass_rate_percent,
                )}
              </strong>

              <small>
                Cases meeting benchmark criteria
              </small>
            </article>

          </div>


          <div className="ai-evaluation-summary">

            <div>
              <span>
                Total cases
              </span>

              <strong>
                {report.total_cases}
              </strong>
            </div>


            <div>
              <span>
                Passed
              </span>

              <strong>
                {report.passed_cases}
              </strong>
            </div>


            <div>
              <span>
                Failed
              </span>

              <strong>
                {report.failed_cases}
              </strong>
            </div>

          </div>


          <div className="ai-evaluation-case-section">

            <div className="ai-evaluation-section-heading">
              <div>
                <p>
                  BENCHMARK CASES
                </p>

                <h3>
                  Per-case evaluation
                </h3>
              </div>

              <span>
                {report.total_cases} cases
              </span>
            </div>


            {!Array.isArray(
              report.results,
            ) ||
            report.results.length === 0 ? (
              <div className="ai-evaluation-empty">
                No per-case results were returned.
              </div>
            ) : (
              <div className="ai-evaluation-table-wrapper">
                <table className="ai-evaluation-table">
                  <thead>
                    <tr>
                      <th>
                        Case
                      </th>

                      <th>
                        Category
                      </th>

                      <th>
                        Priority
                      </th>

                      <th>
                        Urgency
                      </th>

                      <th>
                        Result
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {report.results.map(
                      (result) => (
                        <tr
                          key={
                            result.name
                          }
                        >
                          <td>
                            <strong>
                              {result.name
                                .replace(
                                  /_/g,
                                  " ",
                                )}
                            </strong>
                          </td>

                          <td>
                            <div className="ai-evaluation-comparison">
                              <span>
                                {result.expected_category}
                              </span>

                              <small>
                                →
                              </small>

                              <span>
                                {result.predicted_category ||
                                  "—"}
                              </span>
                            </div>

                            <em
                              className={
                                result.category_correct
                                  ? "ai-evaluation-correct"
                                  : "ai-evaluation-incorrect"
                              }
                            >
                              {result.category_correct
                                ? "Correct"
                                : "Incorrect"}
                            </em>
                          </td>

                          <td>
                            <div className="ai-evaluation-comparison">
                              <span>
                                {result.expected_priority}
                              </span>

                              <small>
                                →
                              </small>

                              <span>
                                {result.predicted_priority ||
                                  "—"}
                              </span>
                            </div>

                            <em
                              className={
                                result.priority_correct
                                  ? "ai-evaluation-correct"
                                  : "ai-evaluation-incorrect"
                              }
                            >
                              {result.priority_correct
                                ? "Correct"
                                : "Incorrect"}
                            </em>
                          </td>

                          <td>
                            <div className="ai-evaluation-urgency">
                              <span>
                                {result.expected_urgency}
                              </span>

                              <small>
                                →
                              </small>

                              <span>
                                {result.predicted_urgency ??
                                  "—"}
                              </span>
                            </div>

                            {result.urgency_absolute_error !==
                              null &&
                              result.urgency_absolute_error !==
                                undefined && (
                                <em>
                                  Error:{" "}
                                  {
                                    result.urgency_absolute_error
                                  }
                                </em>
                              )}
                          </td>

                          <td>
                            <span
                              className={`ai-evaluation-result-pill ${getResultClass(
                                result.passed,
                              )}`}
                            >
                              {result.passed
                                ? "PASS"
                                : "FAIL"}
                            </span>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}

          </div>


          <div className="ai-evaluation-note">
            <strong>
              Evaluation note
            </strong>

            <p>
              Benchmark complaints are created inside
              isolated database transactions and rolled
              back after evaluation, so benchmark data
              does not become part of the live complaint
              dataset.
            </p>
          </div>

        </div>
      )}

    </section>
  );
}


export default AIEvaluationPanel;