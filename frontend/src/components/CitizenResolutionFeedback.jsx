import { useEffect, useState } from "react";

import {
  getResolutionFeedback,
  submitResolutionFeedback,
  updateResolutionFeedback,
  reopenComplaint,
} from "../services/complaintService.js";

function CitizenResolutionFeedback({
  complaint,
  onReopened,
}) {
  const [feedback, setFeedback] = useState(null);
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");

  const [feedbackLoading, setFeedbackLoading] =
    useState(true);

  const [feedbackSubmitting, setFeedbackSubmitting] =
    useState(false);

  const [editing, setEditing] =
    useState(false);

  const [feedbackError, setFeedbackError] =
    useState("");

  const [feedbackSuccess, setFeedbackSuccess] =
    useState("");

  const [showReopenBox, setShowReopenBox] =
    useState(false);

  const [reopenComment, setReopenComment] =
    useState("");

  const [reopenLoading, setReopenLoading] =
    useState(false);

  const [reopenError, setReopenError] =
    useState("");

  const [reopenSuccess, setReopenSuccess] =
    useState("");

  const isResolved =
    complaint?.status === "RESOLVED";

  useEffect(() => {
    let active = true;

    async function loadFeedback() {
      if (!complaint) {
        return;
      }

      try {
        setFeedbackLoading(true);
        setFeedbackError("");
        setFeedbackSuccess("");

        const response =
          await getResolutionFeedback(
            complaint.id,
          );

        const items = Array.isArray(
          response?.feedback,
        )
          ? response.feedback
          : [];

        const currentCycle = Number(
          response?.current_resolution_cycle,
        ) || 1;

        const currentCycleFeedback =
          items.find(
            (item) =>
              Number(
                item.resolution_cycle,
              ) === currentCycle,
          ) || null;

        if (!active) {
          return;
        }

        setFeedback(
          currentCycleFeedback,
        );

        if (currentCycleFeedback) {
          setRating(
            Number(
              currentCycleFeedback.rating,
            ) || 0,
          );

          setComment(
            currentCycleFeedback.comment ||
              "",
          );
        } else {
          setRating(0);
          setComment("");
        }

        setEditing(false);
      } catch (requestError) {
        if (!active) {
          return;
        }

        const responseData =
          requestError?.response?.data;

        setFeedbackError(
          responseData?.detail ||
            "Unable to load your resolution feedback.",
        );
      } finally {
        if (active) {
          setFeedbackLoading(false);
        }
      }
    }

    loadFeedback();

    return () => {
      active = false;
    };
  }, [complaint]);

  if (!complaint) {
    return null;
  }

  function getErrorMessage(requestError) {
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

    return "Something went wrong. Please try again.";
  }

  async function handleFeedbackSubmit() {
    if (rating < 1 || rating > 5) {
      setFeedbackError(
        "Please select a rating between 1 and 5.",
      );
      return;
    }

    const trimmedComment =
      comment.trim();

    if (trimmedComment.length > 2000) {
      setFeedbackError(
        "Feedback comment cannot exceed 2000 characters.",
      );
      return;
    }

    try {
      setFeedbackSubmitting(true);
      setFeedbackError("");
      setFeedbackSuccess("");

      if (editing && feedback?.id) {
        const response =
          await updateResolutionFeedback(
            feedback.id,
            {
              rating,
              comment: trimmedComment,
            },
          );

        const updatedFeedback =
          response?.feedback || response;

        setFeedback(
          updatedFeedback,
        );

        setRating(
          Number(
            updatedFeedback?.rating,
          ) || rating,
        );

        setComment(
          updatedFeedback?.comment ||
            "",
        );

        setEditing(false);

        setFeedbackSuccess(
          "Your resolution feedback has been updated.",
        );

        return;
      }

      const response =
        await submitResolutionFeedback(
          complaint.id,
          rating,
          trimmedComment,
        );

      const submittedFeedback =
        response?.feedback || null;

      setFeedback(
        submittedFeedback,
      );

      setRating(
        Number(
          submittedFeedback?.rating,
        ) || rating,
      );

      setComment(
        submittedFeedback?.comment ||
          trimmedComment,
      );

      setEditing(false);

      setFeedbackSuccess(
        "Thank you. Your resolution feedback has been submitted.",
      );
    } catch (requestError) {
      setFeedbackError(
        getErrorMessage(requestError),
      );
    } finally {
      setFeedbackSubmitting(false);
    }
  }

  function handleEdit() {
    if (!feedback || !isResolved) {
      return;
    }

    setRating(
      Number(feedback.rating) || 0,
    );

    setComment(
      feedback.comment || "",
    );

    setEditing(true);
    setFeedbackError("");
    setFeedbackSuccess("");
  }

  function handleCancelEdit() {
    if (feedback) {
      setRating(
        Number(feedback.rating) || 0,
      );

      setComment(
        feedback.comment || "",
      );
    }

    setEditing(false);
    setFeedbackError("");
    setFeedbackSuccess("");
  }

  async function handleReopen() {
    const trimmedComment =
      reopenComment.trim();

    if (trimmedComment.length < 10) {
      setReopenError(
        "Please explain why the complaint is not resolved using at least 10 characters.",
      );
      return;
    }

    try {
      setReopenLoading(true);
      setReopenError("");
      setReopenSuccess("");

      await reopenComplaint(
        complaint.id,
        trimmedComment,
      );

      setReopenSuccess(
        "Your complaint has been reopened and returned to the assigned officer.",
      );

      setReopenComment("");
      setShowReopenBox(false);

      if (onReopened) {
        await onReopened();
      }
    } catch (requestError) {
      setReopenError(
        getErrorMessage(requestError),
      );
    } finally {
      setReopenLoading(false);
    }
  }

  if (
    !isResolved &&
    !feedback &&
    !feedbackLoading &&
    !reopenSuccess
  ) {
    return null;
  }

  return (
    <section className="citizen-resolution-card">
      <div className="citizen-resolution-content">
        <p className="citizen-resolution-eyebrow">
          RESOLUTION REVIEW
        </p>

        <h2>
          {isResolved
            ? feedback
              ? "Your resolution feedback"
              : "How was your resolution?"
            : "Previous resolution feedback"}
        </h2>

        <p>
          {isResolved
            ? feedback
              ? "You have already submitted feedback for this resolution. You can edit your rating or comment."
              : "Your complaint has been marked as resolved. Please rate the resolution and optionally share your experience."
            : "Your previous resolution feedback is preserved while the complaint is being worked on again."}
        </p>
      </div>

      {feedbackLoading && (
        <div className="citizen-feedback-loading">
          Loading your feedback...
        </div>
      )}

      {!feedbackLoading &&
        feedback &&
        !editing && (
          <div className="citizen-feedback-submitted">
            {feedbackSuccess && (
              <div className="citizen-feedback-success">
                {feedbackSuccess}
              </div>
            )}

            <div className="citizen-feedback-header">
              <span className="citizen-feedback-label">
                YOUR FEEDBACK
              </span>

              {isResolved && (
                <button
                  type="button"
                  className="citizen-feedback-edit"
                  onClick={handleEdit}
                >
                  Edit
                </button>
              )}
            </div>

            <div className="citizen-feedback-display">
              <div className="citizen-feedback-display-rating">
                <span className="citizen-feedback-comment-label">
                  Your rating
                </span>

                <div className="citizen-rating citizen-rating-readonly">
                  {[1, 2, 3, 4, 5].map(
                    (value) => (
                      <span
                        key={value}
                        className={
                          value <=
                          Number(
                            feedback.rating,
                          )
                            ? "citizen-rating-star active"
                            : "citizen-rating-star"
                        }
                      >
                        ★
                      </span>
                    ),
                  )}
                </div>

                <span className="citizen-rating-value">
                  {feedback.rating} out of 5
                </span>
              </div>

              {feedback.comment && (
                <div className="citizen-feedback-comment">
                  <span className="citizen-feedback-comment-label">
                    Comment
                  </span>

                  <p>
                    {feedback.comment}
                  </p>
                </div>
              )}

              <div className="citizen-feedback-cycle">
                Resolution cycle{" "}
                {feedback.resolution_cycle}
              </div>
            </div>
          </div>
        )}

      {!feedbackLoading &&
        feedback &&
        editing && (
          <div className="citizen-feedback-form">
            <div className="citizen-feedback-field">
              <label>
                Your rating
              </label>

              <div
                className="citizen-rating"
                role="radiogroup"
                aria-label="Resolution rating"
              >
                {[1, 2, 3, 4, 5].map(
                  (value) => (
                    <button
                      key={value}
                      type="button"
                      className={
                        value <= rating
                          ? "citizen-rating-star active"
                          : "citizen-rating-star"
                      }
                      onClick={() =>
                        setRating(value)
                      }
                      aria-label={`${value} out of 5 stars`}
                      aria-pressed={
                        value <= rating
                      }
                    >
                      ★
                    </button>
                  ),
                )}
              </div>

              <span className="citizen-rating-value">
                {rating} out of 5
              </span>
            </div>

            <div className="citizen-feedback-field">
              <label htmlFor="resolution-feedback-comment">
                Comment
              </label>

              <textarea
                id="resolution-feedback-comment"
                value={comment}
                onChange={(event) =>
                  setComment(
                    event.target.value,
                  )
                }
                rows={5}
                maxLength={2000}
                disabled={
                  feedbackSubmitting
                }
              />

              <span className="citizen-feedback-helper">
                Optional. Maximum 2000 characters.
              </span>
            </div>

            {feedbackError && (
              <div
                className="citizen-feedback-error"
                role="alert"
              >
                {feedbackError}
              </div>
            )}

            <div className="citizen-feedback-actions">
              <button
                type="button"
                className="citizen-feedback-cancel"
                onClick={
                  handleCancelEdit
                }
                disabled={
                  feedbackSubmitting
                }
              >
                Cancel
              </button>

              <button
                type="button"
                className="citizen-feedback-submit"
                onClick={
                  handleFeedbackSubmit
                }
                disabled={
                  feedbackSubmitting
                }
              >
                {feedbackSubmitting
                  ? "Updating..."
                  : "Update feedback"}
              </button>
            </div>
          </div>
        )}

      {!feedbackLoading &&
        !feedback &&
        isResolved && (
          <div className="citizen-feedback-form">
            <div className="citizen-feedback-field">
              <label>
                Your rating
              </label>

              <div
                className="citizen-rating"
                role="radiogroup"
                aria-label="Resolution rating"
              >
                {[1, 2, 3, 4, 5].map(
                  (value) => (
                    <button
                      key={value}
                      type="button"
                      className={
                        value <= rating
                          ? "citizen-rating-star active"
                          : "citizen-rating-star"
                      }
                      onClick={() =>
                        setRating(value)
                      }
                      aria-label={`${value} out of 5 stars`}
                      aria-pressed={
                        value <= rating
                      }
                    >
                      ★
                    </button>
                  ),
                )}
              </div>

              <span className="citizen-rating-value">
                {rating > 0
                  ? `${rating} out of 5`
                  : "Select a rating"}
              </span>
            </div>

            <div className="citizen-feedback-field">
              <label htmlFor="resolution-feedback-comment">
                Comment
              </label>

              <textarea
                id="resolution-feedback-comment"
                value={comment}
                onChange={(event) =>
                  setComment(
                    event.target.value,
                  )
                }
                placeholder="Tell us about your experience with the resolution."
                rows={5}
                maxLength={2000}
                disabled={
                  feedbackSubmitting
                }
              />

              <span className="citizen-feedback-helper">
                Optional. Maximum 2000 characters.
              </span>
            </div>

            {feedbackError && (
              <div
                className="citizen-feedback-error"
                role="alert"
              >
                {feedbackError}
              </div>
            )}

            <button
              type="button"
              className="citizen-feedback-submit"
              onClick={
                handleFeedbackSubmit
              }
              disabled={feedbackSubmitting}
            >
              {feedbackSubmitting
                ? "Submitting..."
                : "Submit feedback"}
            </button>
          </div>
        )}

      {reopenSuccess && (
        <div
          className="citizen-reopen-success"
          role="status"
        >
          {reopenSuccess}
        </div>
      )}

      {isResolved && (
        <div className="citizen-reopen-section">
          <div className="citizen-reopen-content">
            <h3>
              Is the issue still unresolved?
            </h3>

            <p>
              If the problem still exists or
              the resolution was incomplete,
              you can reopen the complaint.
            </p>
          </div>

          {!showReopenBox && (
            <button
              type="button"
              className="citizen-reopen-primary"
              onClick={() => {
                setShowReopenBox(true);
                setReopenError("");
              }}
            >
              The issue is not resolved
            </button>
          )}

          {showReopenBox && (
            <div className="citizen-reopen-box">
              <label htmlFor="reopen-comment">
                Why are you reopening this complaint?
              </label>

              <textarea
                id="reopen-comment"
                value={reopenComment}
                onChange={(event) =>
                  setReopenComment(
                    event.target.value,
                  )
                }
                placeholder="Example: The issue is still present even after the reported resolution."
                rows={5}
                disabled={reopenLoading}
              />

              <p className="citizen-reopen-helper">
                Please provide enough detail
                for the officer to understand
                what remains unresolved.
              </p>

              {reopenError && (
                <p
                  className="citizen-reopen-error"
                  role="alert"
                >
                  {reopenError}
                </p>
              )}

              <div className="citizen-reopen-buttons">
                <button
                  type="button"
                  className="citizen-reopen-cancel"
                  onClick={() => {
                    setShowReopenBox(false);
                    setReopenComment("");
                    setReopenError("");
                  }}
                  disabled={reopenLoading}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  className="citizen-reopen-primary"
                  onClick={handleReopen}
                  disabled={reopenLoading}
                >
                  {reopenLoading
                    ? "Reopening..."
                    : "Confirm reopen"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default CitizenResolutionFeedback;