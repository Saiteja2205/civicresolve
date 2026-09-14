import { useEffect, useRef, useState } from "react";

import {
  uploadComplaintEvidence,
} from "../services/complaintService.js";

import "../styles/complaint-evidence.css";


const MAX_FILE_SIZE = 5 * 1024 * 1024;

const ALLOWED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];


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

  return "Unable to upload the evidence image.";
}


function formatFileSize(bytes) {
  if (!bytes) {
    return "0 KB";
  }

  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}


function getConsistencyLabel(value) {
  if (value === true) {
    return "Consistent with complaint";
  }

  if (value === false) {
    return "Potential mismatch";
  }

  return "Not determined";
}


function ComplaintEvidencePanel({
  complaint,
  isCitizen,
}) {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] =
    useState(null);

  const [previewUrl, setPreviewUrl] =
    useState("");

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [evidence, setEvidence] =
    useState(
      Array.isArray(complaint?.evidence)
        ? complaint.evidence
        : [],
    );


  useEffect(() => {
    setEvidence(
      Array.isArray(complaint?.evidence)
        ? complaint.evidence
        : [],
    );
  }, [complaint?.evidence]);


  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);


  function clearSelectedFile() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(null);
    setPreviewUrl("");
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }


  function handleFileChange(event) {
    const file =
      event.target.files?.[0];

    setError("");
    setSuccess("");

    if (!file) {
      clearSelectedFile();
      return;
    }

    if (
      !ALLOWED_TYPES.includes(
        file.type,
      )
    ) {
      setError(
        "Unsupported image type. Please select a JPEG, PNG, or WEBP image.",
      );
      clearSelectedFile();
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError(
        "Evidence image must be 5 MB or smaller.",
      );
      clearSelectedFile();
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    setPreviewUrl(
      URL.createObjectURL(file),
    );
  }


  async function handleUpload() {
    if (!complaint?.id) {
      setError(
        "Complaint ID is missing. Please reload the page.",
      );
      return;
    }

    if (!selectedFile) {
      setError(
        "Please select an image first.",
      );
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const uploadedEvidence =
        await uploadComplaintEvidence(
          complaint.id,
          selectedFile,
        );

      setEvidence((current) => [
        uploadedEvidence,
        ...current,
      ]);

      setSuccess(
        uploadedEvidence.analysis_status ===
          "completed"
          ? "Evidence uploaded and analyzed successfully."
          : "Evidence uploaded. AI analysis is currently unavailable.",
      );

      clearSelectedFile();
    } catch (requestError) {
      console.error(
        "Evidence upload failed:",
        requestError,
      );

      setError(
        getApiErrorMessage(
          requestError,
        ),
      );
    } finally {
      setUploading(false);
    }
  }


  return (
    <article className="complaint-evidence-card">
      <div className="complaint-evidence-header">
        <div>
          <p className="complaint-evidence-eyebrow">
            AI EVIDENCE INTELLIGENCE
          </p>

          <h2>
            Complaint evidence
          </h2>

          <p>
            Upload a photo to support this
            complaint. CivicResolve analyzes
            the image for evidence type,
            severity, confidence, and
            consistency with the complaint.
          </p>
        </div>

        <span className="complaint-evidence-count">
          {evidence.length}{" "}
          {evidence.length === 1
            ? "image"
            : "images"}
        </span>
      </div>


      {isCitizen && (
        <div className="complaint-evidence-upload">
          <label
            htmlFor="complaint-evidence-image"
            className="complaint-evidence-file-label"
          >
            <span>
              Choose evidence image
            </span>

            <small>
              JPEG, PNG, or WEBP · Maximum 5 MB
            </small>
          </label>

          <input
            ref={fileInputRef}
            id="complaint-evidence-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleFileChange}
            disabled={uploading}
          />


          {selectedFile && (
            <div className="complaint-evidence-selected">
              <div className="complaint-evidence-preview">
                <img
                  src={previewUrl}
                  alt="Selected complaint evidence preview"
                />
              </div>

              <div className="complaint-evidence-selected-info">
                <strong>
                  {selectedFile.name}
                </strong>

                <span>
                  {formatFileSize(
                    selectedFile.size,
                  )}
                </span>

                <div className="complaint-evidence-upload-actions">
                  <button
                    type="button"
                    className="complaint-evidence-upload-button"
                    onClick={handleUpload}
                    disabled={uploading}
                  >
                    {uploading
                      ? "Uploading & analyzing..."
                      : "Upload evidence"}
                  </button>

                  <button
                    type="button"
                    className="complaint-evidence-cancel-button"
                    onClick={
                      clearSelectedFile
                    }
                    disabled={uploading}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}


          {uploading && (
            <div
              className="complaint-evidence-processing"
              role="status"
              aria-live="polite"
            >
              <span className="complaint-evidence-spinner" />

              <div>
                <strong>
                  AI analysis in progress
                </strong>

                <p>
                  Gemini is examining the
                  uploaded evidence against
                  the complaint.
                </p>
              </div>
            </div>
          )}


          {error && (
            <p
              className="complaint-evidence-error"
              role="alert"
            >
              {error}
            </p>
          )}


          {success && (
            <p
              className="complaint-evidence-success"
              role="status"
            >
              {success}
            </p>
          )}
        </div>
      )}


      {evidence.length === 0 ? (
        <div className="complaint-evidence-empty">
          <strong>
            No evidence uploaded yet
          </strong>

          <span>
            Adding a clear photo can help
            officers understand the reported
            issue.
          </span>
        </div>
      ) : (
        <div className="complaint-evidence-list">
          {evidence.map(
            (item, index) => (
              <article
                className="complaint-evidence-item"
                key={
                  item.id ||
                  `${item.uploaded_at}-${index}`
                }
              >
                <div className="complaint-evidence-image">
                  {item.image_url ||
                  item.image ? (
                    <img
                      src={
                        item.image_url ||
                        item.image
                      }
                      alt={
                        item.original_filename ||
                        "Complaint evidence"
                      }
                    />
                  ) : (
                    <span>
                      No preview
                    </span>
                  )}
                </div>


                <div className="complaint-evidence-details">
                  <div className="complaint-evidence-item-top">
                    <div>
                      <strong>
                        {item.original_filename ||
                          "Evidence image"}
                      </strong>

                      <small>
                        {item.content_type ||
                          "Image"}{" "}
                        ·{" "}
                        {formatFileSize(
                          item.file_size,
                        )}
                      </small>
                    </div>

                    <span
                      className={
                        item.analysis_completed
                          ? "complaint-evidence-status completed"
                          : "complaint-evidence-status pending"
                      }
                    >
                      {item.analysis_completed
                        ? "Analyzed"
                        : "Analysis unavailable"}
                    </span>
                  </div>


                  {item.analysis_completed && (
                    <>
                      <div className="complaint-evidence-metrics">
                        <div>
                          <span>
                            Evidence type
                          </span>

                          <strong>
                            {item.evidence_type_display ||
                              item.evidence_type ||
                              "Other"}
                          </strong>
                        </div>

                        <div>
                          <span>
                            Severity
                          </span>

                          <strong>
                            {item.severity_score ??
                              "—"}
                            /100
                          </strong>
                        </div>

                        <div>
                          <span>
                            AI confidence
                          </span>

                          <strong>
                            {item.confidence_score ??
                              "—"}
                            /100
                          </strong>
                        </div>
                      </div>


                      <div
                        className={
                          item.complaint_consistency ===
                          true
                            ? "complaint-evidence-consistency match"
                            : item.complaint_consistency ===
                                false
                              ? "complaint-evidence-consistency mismatch"
                              : "complaint-evidence-consistency"
                        }
                      >
                        <strong>
                          {getConsistencyLabel(
                            item.complaint_consistency,
                          )}
                        </strong>

                        {item.analysis_explanation && (
                          <p>
                            {
                              item.analysis_explanation
                            }
                          </p>
                        )}
                      </div>


                      {item.observations && (
                        <div className="complaint-evidence-observations">
                          <span>
                            AI observations
                          </span>

                          <p>
                            {item.observations}
                          </p>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </article>
            ),
          )}
        </div>
      )}
    </article>
  );
}


export default ComplaintEvidencePanel;