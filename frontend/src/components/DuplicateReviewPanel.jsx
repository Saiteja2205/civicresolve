import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getComplaint } from "../services/complaintService.js";

import {
  getDuplicateRecords,
  reviewDuplicate,
} from "../services/duplicateService.js";

import "../styles/duplicate-review.css";


const STATUS_LABELS = {
  PENDING: "Pending review",
  CONFIRMED: "Confirmed duplicate",
  REJECTED: "Not a duplicate",
};


function getList(data) {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString([], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function getStatusClass(status) {
  if (status === "CONFIRMED") {
    return "duplicate-status-confirmed";
  }

  if (status === "REJECTED") {
    return "duplicate-status-rejected";
  }

  return "duplicate-status-pending";
}


function DuplicateReviewPanel() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [statusFilter, setStatusFilter] = useState("ALL");

  const [search, setSearch] = useState("");

  const [selectedRecord, setSelectedRecord] = useState(null);

  const [comparison, setComparison] = useState(null);

  const [comparisonLoading, setComparisonLoading] = useState(false);

  const [comparisonError, setComparisonError] = useState("");

  const [reviewLoading, setReviewLoading] = useState(null);

  const [reviewError, setReviewError] = useState("");

  const [comment, setComment] = useState("");


  async function loadDuplicates(showInitialLoading = false) {
    try {
      if (showInitialLoading) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError("");

      const data = await getDuplicateRecords();

      setRecords(getList(data));
    } catch (requestError) {
      console.error(
        "Failed to load duplicate records:",
        requestError,
      );

      setError(
        requestError?.response?.data?.detail ||
          "Unable to load duplicate records.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }


  useEffect(() => {
    loadDuplicates(true);
  }, []);


  const statistics = useMemo(() => {
    return {
      all: records.length,

      pending: records.filter(
        (record) => record.status === "PENDING",
      ).length,

      confirmed: records.filter(
        (record) => record.status === "CONFIRMED",
      ).length,

      rejected: records.filter(
        (record) => record.status === "REJECTED",
      ).length,
    };
  }, [records]);


  const filteredRecords = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return records
      .filter((record) => {
        if (
          statusFilter !== "ALL" &&
          record.status !== statusFilter
        ) {
          return false;
        }

        if (!normalizedSearch) {
          return true;
        }

        const searchableText = [
          record.complaint_ticket_number,
          record.complaint_title,
          record.possible_duplicate_ticket_number,
          record.possible_duplicate_title,
          record.review_comment,
          record.reviewed_by_email,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return searchableText.includes(normalizedSearch);
      })
      .sort(
        (a, b) =>
          Number(b.similarity_score || 0) -
          Number(a.similarity_score || 0),
      );
  }, [records, search, statusFilter]);


  async function openComparison(record) {
    setSelectedRecord(record);
    setComparison(null);
    setComparisonError("");
    setComparisonLoading(true);
    setReviewError("");
    setComment(record.review_comment || "");

    try {
      const [
        complaint,
        possibleDuplicate,
      ] = await Promise.all([
        getComplaint(record.complaint),
        getComplaint(record.possible_duplicate),
      ]);

      setComparison({
        complaint,
        possibleDuplicate,
      });
    } catch (requestError) {
      console.error(
        "Failed to load complaint comparison:",
        requestError,
      );

      setComparisonError(
        requestError?.response?.data?.detail ||
          "Unable to load the complaint comparison.",
      );
    } finally {
      setComparisonLoading(false);
    }
  }


  function closeComparison() {
    if (reviewLoading) {
      return;
    }

    setSelectedRecord(null);
    setComparison(null);
    setComparisonError("");
    setReviewError("");
    setComment("");
  }


  async function handleReview(record, newStatus) {
    if (reviewLoading) {
      return;
    }

    const statusLabel = STATUS_LABELS[newStatus];

    let reviewComment = "";

    if (newStatus === "REJECTED") {
      reviewComment =
        comment.trim() ||
        "Reviewed by administrator and determined not to be a duplicate.";
    }

    if (newStatus === "CONFIRMED") {
      reviewComment =
        comment.trim() ||
        "Reviewed by administrator and confirmed as a duplicate.";
    }

    if (
      !window.confirm(
        `Mark ${record.complaint_ticket_number} and ${record.possible_duplicate_ticket_number} as "${statusLabel}"?`,
      )
    ) {
      return;
    }

    try {
      setReviewLoading(record.id);
      setReviewError("");

      const updated = await reviewDuplicate(
        record.id,
        newStatus,
        reviewComment,
      );

      setRecords((current) =>
        current.map((item) =>
          item.id === record.id ? updated : item,
        ),
      );

      if (selectedRecord?.id === record.id) {
        setSelectedRecord(updated);

        setComment(
          updated.review_comment || "",
        );
      }
    } catch (requestError) {
      console.error(
        "Failed to review duplicate:",
        requestError,
      );

      const message =
        requestError?.response?.data?.detail ||
        "Unable to update duplicate review.";

      setReviewError(message);
    } finally {
      setReviewLoading(null);
    }
  }


  function renderComplaintSummary(complaint) {
    if (!complaint) {
      return null;
    }

    return (
      <div className="duplicate-comparison-card">

        <div className="duplicate-comparison-card-header">

          <div>
            <span className="duplicate-comparison-ticket">
              {complaint.ticket_number}
            </span>

            <h3>
              {complaint.title}
            </h3>
          </div>

          <Link
            to={`/dashboard/complaints/${complaint.id}`}
            className="duplicate-detail-link"
            onClick={closeComparison}
          >
            Open complaint
          </Link>
        </div>


        <div className="duplicate-comparison-description">
          <span>Description</span>

          <p>
            {complaint.description ||
              "No description provided."}
          </p>
        </div>


        <dl className="duplicate-comparison-meta">

          <div>
            <dt>Category</dt>

            <dd>
              {complaint.category_name ||
                "Not available"}
            </dd>
          </div>


          <div>
            <dt>Department</dt>

            <dd>
              {complaint.department_name ||
                "Not assigned"}
            </dd>
          </div>


          <div>
            <dt>Priority</dt>

            <dd>
              {complaint.priority || "—"}
            </dd>
          </div>


          <div>
            <dt>Status</dt>

            <dd>
              {complaint.status || "—"}
            </dd>
          </div>


          <div>
            <dt>Location</dt>

            <dd>
              {complaint.location ||
                "Not provided"}
            </dd>
          </div>


          <div>
            <dt>Submitted</dt>

            <dd>
              {formatDate(complaint.created_at)}
            </dd>
          </div>

        </dl>

      </div>
    );
  }


  return (
    <section className="duplicate-review-section">

      <div className="duplicate-review-header">

        <div>
          <p className="duplicate-review-eyebrow">
            DUPLICATE INTELLIGENCE
          </p>

          <h2>
            Duplicate complaint review
          </h2>

          <p>
            Review complaints identified as
            semantically similar by the
            duplicate detection engine.
          </p>
        </div>


        <button
          type="button"
          className="duplicate-refresh-button"
          onClick={() => loadDuplicates(false)}
          disabled={refreshing}
        >
          {refreshing
            ? "Refreshing..."
            : "Refresh"}
        </button>

      </div>


      <div className="duplicate-stat-grid">

        <button
          type="button"
          className={`duplicate-stat ${
            statusFilter === "ALL"
              ? "duplicate-stat-active"
              : ""
          }`}
          onClick={() => setStatusFilter("ALL")}
        >
          <span>All candidates</span>

          <strong>
            {statistics.all}
          </strong>
        </button>


        <button
          type="button"
          className={`duplicate-stat ${
            statusFilter === "PENDING"
              ? "duplicate-stat-active"
              : ""
          }`}
          onClick={() =>
            setStatusFilter("PENDING")
          }
        >
          <span>Pending review</span>

          <strong>
            {statistics.pending}
          </strong>
        </button>


        <button
          type="button"
          className={`duplicate-stat ${
            statusFilter === "CONFIRMED"
              ? "duplicate-stat-active"
              : ""
          }`}
          onClick={() =>
            setStatusFilter("CONFIRMED")
          }
        >
          <span>Confirmed</span>

          <strong>
            {statistics.confirmed}
          </strong>
        </button>


        <button
          type="button"
          className={`duplicate-stat ${
            statusFilter === "REJECTED"
              ? "duplicate-stat-active"
              : ""
          }`}
          onClick={() =>
            setStatusFilter("REJECTED")
          }
        >
          <span>Rejected</span>

          <strong>
            {statistics.rejected}
          </strong>
        </button>

      </div>


      <div className="duplicate-toolbar">

        <div className="duplicate-search">

          <label htmlFor="duplicate-search">
            Search
          </label>

          <input
            id="duplicate-search"
            type="search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Ticket number or complaint title..."
          />

        </div>


        <div className="duplicate-filter">

          <label htmlFor="duplicate-status">
            Review status
          </label>

          <select
            id="duplicate-status"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value)
            }
          >
            <option value="ALL">
              All statuses
            </option>

            <option value="PENDING">
              Pending review
            </option>

            <option value="CONFIRMED">
              Confirmed duplicate
            </option>

            <option value="REJECTED">
              Not a duplicate
            </option>
          </select>

        </div>

      </div>


      {error && (
        <div
          className="duplicate-error"
          role="alert"
        >
          <span>{error}</span>

          <button
            type="button"
            onClick={() =>
              loadDuplicates(true)
            }
          >
            Try again
          </button>
        </div>
      )}


      {loading ? (
        <div className="duplicate-loading">

          <div className="duplicate-loading-row" />

          <div className="duplicate-loading-row" />

          <div className="duplicate-loading-row" />

        </div>
      ) : filteredRecords.length === 0 ? (
        <div className="duplicate-empty">

          <div className="duplicate-empty-icon">
            ✓
          </div>

          <h3>
            No duplicate candidates found
          </h3>

          <p>
            No records match the current
            search and review filters.
          </p>

        </div>
      ) : (
        <div className="duplicate-list">

          {filteredRecords.map((record) => (
            <article
              key={record.id}
              className="duplicate-card"
            >

              <div className="duplicate-card-main">

                <div className="duplicate-card-heading">

                  <div className="duplicate-ticket-pair">

                    <span>
                      {record.complaint_ticket_number}
                    </span>

                    <b>↔</b>

                    <span>
                      {
                        record.possible_duplicate_ticket_number
                      }
                    </span>

                  </div>


                  <span
                    className={`duplicate-status ${getStatusClass(
                      record.status,
                    )}`}
                  >
                    {
                      STATUS_LABELS[
                        record.status
                      ] || record.status
                    }
                  </span>

                </div>


                <div className="duplicate-title-pair">

                  <div>
                    <span>
                      Original complaint
                    </span>

                    <strong>
                      {record.complaint_title}
                    </strong>
                  </div>


                  <div>
                    <span>
                      Possible duplicate
                    </span>

                    <strong>
                      {record.possible_duplicate_title}
                    </strong>
                  </div>

                </div>


                <div className="duplicate-card-meta">

                  <span>
                    Detected{" "}
                    {formatDate(
                      record.detected_at,
                    )}
                  </span>

                  {record.reviewed_by_email && (
                    <span>
                      Reviewed by{" "}
                      {record.reviewed_by_email}
                    </span>
                  )}

                </div>

              </div>


              <div className="duplicate-card-score">

                <div
                  className="duplicate-score-ring"
                  style={{
                    "--duplicate-score":
                      `${Math.min(
                        Number(
                          record.similarity_percentage ||
                            0,
                        ),
                        100,
                      )}%`,
                  }}
                >
                  <strong>
                    {
                      record.similarity_percentage ??
                      (
                        Number(
                          record.similarity_score ||
                            0,
                        ) * 100
                      ).toFixed(2)
                    }
                    %
                  </strong>

                  <span>
                    similarity
                  </span>
                </div>

              </div>


              <div className="duplicate-card-actions">

                <button
                  type="button"
                  className="duplicate-secondary-button"
                  onClick={() =>
                    openComparison(record)
                  }
                >
                  Compare complaints
                </button>


                {/* Review actions are available ONLY
                    while the record is pending. */}
                {record.status === "PENDING" && (
                  <>
                    <button
                      type="button"
                      className="duplicate-confirm-button"
                      disabled={
                        reviewLoading === record.id
                      }
                      onClick={() =>
                        handleReview(
                          record,
                          "CONFIRMED",
                        )
                      }
                    >
                      {reviewLoading === record.id
                        ? "Updating..."
                        : "Confirm duplicate"}
                    </button>


                    <button
                      type="button"
                      className="duplicate-reject-button"
                      disabled={
                        reviewLoading === record.id
                      }
                      onClick={() =>
                        handleReview(
                          record,
                          "REJECTED",
                        )
                      }
                    >
                      Reject
                    </button>
                  </>
                )}

              </div>

            </article>
          ))}

        </div>
      )}


      <div className="duplicate-review-footer">

        Showing{" "}
        <strong>
          {filteredRecords.length}
        </strong>{" "}
        of{" "}
        <strong>
          {records.length}
        </strong>{" "}
        duplicate candidates

      </div>


      {selectedRecord && (
        <div
          className="duplicate-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeComparison();
            }
          }}
        >

          <div
            className="duplicate-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="duplicate-modal-title"
          >

            <div className="duplicate-modal-header">

              <div>

                <p className="duplicate-review-eyebrow">
                  SEMANTIC COMPARISON
                </p>

                <h2 id="duplicate-modal-title">
                  Complaint comparison
                </h2>

                <p>
                  {
                    selectedRecord.complaint_ticket_number
                  }{" "}
                  ↔{" "}
                  {
                    selectedRecord.possible_duplicate_ticket_number
                  }
                </p>

              </div>


              <button
                type="button"
                className="duplicate-modal-close"
                onClick={closeComparison}
                disabled={Boolean(reviewLoading)}
                aria-label="Close comparison"
              >
                ×
              </button>

            </div>


            <div className="duplicate-modal-score">

              <strong>
                {
                  selectedRecord.similarity_percentage ??
                  (
                    Number(
                      selectedRecord.similarity_score ||
                        0,
                    ) * 100
                  ).toFixed(2)
                }
                %
              </strong>

              <span>
                semantic similarity
              </span>

            </div>


            {comparisonLoading ? (
              <div className="duplicate-modal-loading">

                <div className="duplicate-spinner" />

                <span>
                  Loading complaint details...
                </span>

              </div>
            ) : comparisonError ? (
              <div
                className="duplicate-error"
                role="alert"
              >
                {comparisonError}
              </div>
            ) : comparison ? (
              <div className="duplicate-comparison-grid">

                {renderComplaintSummary(
                  comparison.complaint,
                )}

                {renderComplaintSummary(
                  comparison.possibleDuplicate,
                )}

              </div>
            ) : null}


            {/* Review controls are intentionally shown
                only for pending records. */}
            {selectedRecord.status === "PENDING" && (
              <div className="duplicate-review-controls">

                <div>

                  <label htmlFor="duplicate-review-comment">
                    Review comment
                  </label>

                  <textarea
                    id="duplicate-review-comment"
                    rows="3"
                    value={comment}
                    onChange={(event) =>
                      setComment(
                        event.target.value,
                      )
                    }
                    maxLength={2000}
                    placeholder="Optional reason for your decision..."
                    disabled={Boolean(reviewLoading)}
                  />

                  <small>
                    {comment.length}/2000
                  </small>

                </div>


                {reviewError && (
                  <div
                    className="duplicate-error"
                    role="alert"
                  >
                    {reviewError}
                  </div>
                )}


                <div className="duplicate-modal-actions">

                  <button
                    type="button"
                    className="duplicate-reject-button"
                    disabled={
                      reviewLoading ===
                      selectedRecord.id
                    }
                    onClick={() =>
                      handleReview(
                        selectedRecord,
                        "REJECTED",
                      )
                    }
                  >
                    Reject duplicate
                  </button>


                  <button
                    type="button"
                    className="duplicate-confirm-button"
                    disabled={
                      reviewLoading ===
                      selectedRecord.id
                    }
                    onClick={() =>
                      handleReview(
                        selectedRecord,
                        "CONFIRMED",
                      )
                    }
                  >
                    Confirm duplicate
                  </button>

                </div>

              </div>
            )}


            {/* Once reviewed, show the immutable review result
                instead of allowing another decision. */}
            {selectedRecord.status !== "PENDING" && (
              <div className="duplicate-reviewed-summary">

                <div>

                  <span>
                    Review decision
                  </span>

                  <strong>
                    {
                      STATUS_LABELS[
                        selectedRecord.status
                      ]
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Reviewed by
                  </span>

                  <strong>
                    {
                      selectedRecord.reviewed_by_email ||
                      "Administrator"
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Reviewed at
                  </span>

                  <strong>
                    {formatDate(
                      selectedRecord.reviewed_at,
                    )}
                  </strong>

                </div>


                {selectedRecord.review_comment && (
                  <div className="duplicate-review-comment-display">

                    <span>
                      Comment
                    </span>

                    <p>
                      {
                        selectedRecord.review_comment
                      }
                    </p>

                  </div>
                )}

              </div>
            )}

          </div>

        </div>
      )}

    </section>
  );
}


export default DuplicateReviewPanel;