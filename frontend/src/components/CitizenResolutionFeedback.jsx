import { useState } from "react";

import { reopenComplaint } from "../services/complaintService.js";


function CitizenResolutionFeedback({
  complaint,
  onReopened,
}) {
  const [showReopenBox, setShowReopenBox] =
    useState(false);

  const [comment, setComment] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  if (
    !complaint ||
    complaint.status !== "RESOLVED"
  ) {
    return null;
  }


  async function handleReopen() {
    const trimmedComment =
      comment.trim();

    if (trimmedComment.length < 10) {
      setError(
        "Please explain why the complaint is not resolved using at least 10 characters.",
      );
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");

      await reopenComplaint(
        complaint.id,
        trimmedComment,
      );

      setSuccess(
        "Your complaint has been reopened successfully. The administration team will review it and assign it again.",
      );

      setComment("");
      setShowReopenBox(false);

      if (onReopened) {
        await onReopened();
      }
    } catch (requestError) {
      console.error(
        "Failed to reopen complaint:",
        requestError,
      );

      const responseData =
        requestError?.response?.data;

      const message =
        responseData?.detail ||
        "Unable to reopen the complaint. Please try again.";

      setError(message);
    } finally {
      setLoading(false);
    }
  }


  return (
    <section className="citizen-resolution-card">
      <div className="citizen-resolution-content">
        <p className="citizen-resolution-eyebrow">
          RESOLUTION REVIEW
        </p>

        <h2>
          Is your complaint actually resolved?
        </h2>

        <p>
          The officer has marked this complaint
          as resolved. If the issue is still
          present or the resolution was
          incomplete, you can reopen the
          complaint.
        </p>
      </div>


      {success && (
        <div
          className="citizen-resolution-success"
          role="status"
        >
          {success}
        </div>
      )}


      {!showReopenBox && !success && (
        <button
          type="button"
          className="citizen-reopen-primary"
          onClick={() => {
            setShowReopenBox(true);
            setError("");
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
            value={comment}
            onChange={(event) =>
              setComment(event.target.value)
            }
            placeholder="Example: The Wi-Fi is still not working in my room even after the reported resolution."
            rows={5}
            disabled={loading}
          />

          <p className="citizen-reopen-helper">
            Please provide enough detail for the
            officer to understand what remains
            unresolved.
          </p>


          {error && (
            <p
              className="citizen-reopen-error"
              role="alert"
            >
              {error}
            </p>
          )}


          <div className="citizen-reopen-buttons">
            <button
              type="button"
              className="citizen-reopen-cancel"
              onClick={() => {
                setShowReopenBox(false);
                setComment("");
                setError("");
              }}
              disabled={loading}
            >
              Cancel
            </button>

            <button
              type="button"
              className="citizen-reopen-primary"
              onClick={handleReopen}
              disabled={loading}
            >
              {loading
                ? "Reopening..."
                : "Confirm reopen"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}


export default CitizenResolutionFeedback;