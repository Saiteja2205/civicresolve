# CivicResolve — Database Design

## 1. Overview

The data model separates identity, organizational data, complaints, AI analysis, assignments, workflow history, SLA records, semantic data, evidence, feedback, and notifications.

## 2. Main Entities

### User

Stores application users using email as the login identifier.

Key fields:

- `email`
- `phone`
- `role`
- `department`
- Django authentication fields

Roles:

- `USER`
- `OFFICER`
- `ADMIN`

### Department

Stores operational departments.

Key fields:

- `name`
- `description`
- `is_active`
- timestamps

### Category

Stores complaint categories linked to departments.

Key fields:

- `name`
- `description`
- `department`
- `is_active`
- timestamps

A database constraint prevents duplicate category names within the same department.

### Complaint

The central business entity.

Key fields:

- `ticket_number`
- `user`
- `category`
- `title`
- `description`
- `status`
- `priority`
- `location`
- `latitude`
- `longitude`
- `created_at`
- `updated_at`
- `resolved_at`
- `closed_at`

Ticket numbers are generated in the `CR-000001` style.

## 3. Complaint Analysis

`ComplaintAnalysis` is a one-to-one extension of a complaint.

Key fields:

- `summary`
- `explanation`
- `detected_language`
- `english_title`
- `english_description`
- `predicted_category`
- `predicted_department`
- `predicted_priority`
- `urgency_score`
- `confidence_score`
- `model_name`
- timestamps

The multilingual fields are deliberately separate from the original complaint fields.

```text
Complaint
├── title
└── description

ComplaintAnalysis
├── detected_language
├── english_title
└── english_description
```

## 4. Complaint Assignment

`ComplaintAssignment` records which officer and department are associated with a complaint.

Fields include:

- `complaint`
- `department`
- `officer`
- `assigned_by`
- `assigned_at`
- `unassigned_at`
- `reason`

An active assignment is represented by a null `unassigned_at` value.

## 5. Complaint History

`ComplaintHistory` provides an audit trail for status changes.

Fields include:

- `complaint`
- `changed_by`
- `old_status`
- `new_status`
- `comment`
- `created_at`

The history is ordered chronologically.

## 6. SLA Data

### SLAPolicy

Stores priority-specific response and resolution targets.

Fields:

- `priority`
- `response_time_hours`
- `resolution_time_hours`
- `is_active`
- timestamps

### ComplaintSLA

Stores SLA deadlines and completion/breach state for a complaint.

Fields:

- `complaint`
- `policy`
- `response_deadline`
- `resolution_deadline`
- `response_completed_at`
- `resolution_completed_at`
- `response_breached`
- `resolution_breached`
- timestamps

## 7. Vector and Duplicate Data

### ComplaintEmbedding

Stores one semantic embedding per complaint.

Fields:

- `complaint`
- `embedding`
- `embedding_model`
- `source_text_hash`
- timestamps

The vector field is configured for 768 dimensions.

### ComplaintDuplicate

Stores a candidate relationship between complaints.

Fields include:

- `complaint`
- `possible_duplicate`
- `similarity_score`
- `detection_threshold`
- `embedding_model`
- `status`
- `detected_at`
- `updated_at`
- `reviewed_by`
- `reviewed_at`
- `review_comment`

Review states are `PENDING`, `CONFIRMED`, and `REJECTED`.

## 8. Evidence

`ComplaintEvidence` stores uploaded complaint images and structured AI analysis.

Stored metadata includes:

- Original filename
- Content type
- File size
- Uploaded user
- Upload time
- Evidence type
- Observations
- Severity score
- Confidence score
- Complaint consistency
- AI explanation
- AI model
- Analysis timestamp

The original image is retained independently of AI analysis.

## 9. Resolution Feedback

`ComplaintResolutionFeedback` stores citizen feedback after resolution.

Fields:

- `complaint`
- `citizen`
- `rating`
- `comment`
- `resolution_cycle`
- `created_at`
- `updated_at`

Constraints enforce a rating from 1 to 5 and one feedback record per complaint per resolution cycle.

This supports:

```text
Resolution cycle 1
    feedback 1
        |
        v
     reopen
        |
        v
Resolution cycle 2
    feedback 2
```

## 10. Notifications

`Notification` stores in-app notifications for users.

Key fields:

- `recipient`
- `notification_type`
- `title`
- `message`
- `complaint`
- `metadata`
- `is_read`
- `created_at`
- `read_at`

Indexes support recipient/read-state and recipient/time queries.

## 11. Relationship Summary

```text
User 1 ─── * Complaint
User 1 ─── * Notification
User 1 ─── * ComplaintAssignment
User 1 ─── * ComplaintHistory
User 1 ─── * ComplaintEvidence
User 1 ─── * ComplaintResolutionFeedback

Department 1 ─── * Category
Department 1 ─── * ComplaintAssignment

Category 1 ─── * Complaint
Category 1 ─── * ComplaintAnalysis

Complaint 1 ─── 1 ComplaintAnalysis
Complaint 1 ─── * ComplaintAssignment
Complaint 1 ─── * ComplaintHistory
Complaint 1 ─── 1 ComplaintSLA
Complaint 1 ─── 1 ComplaintEmbedding
Complaint 1 ─── * ComplaintDuplicate
Complaint 1 ─── * ComplaintEvidence
Complaint 1 ─── * ComplaintResolutionFeedback
Complaint 1 ─── * Notification
```
