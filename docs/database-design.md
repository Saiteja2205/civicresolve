# CivicResolve - Database Design

## 1. Overview

CivicResolve uses a relational database model to represent users,
organizational structure, complaints, AI analysis, assignments,
complaint history, SLA information and operational workflows.

The database is designed around the complaint as the central business
entity.

---

## 2. User

The application uses a custom Django user model.

### Important fields

- `id`
- `email`
- `phone`
- `role`
- `department`
- Django authentication fields

### Roles

- `USER`
- `OFFICER`
- `ADMIN`

The user's email is used as the authentication identifier.

---

## 3. Department

A Department represents an operational department responsible for
handling complaints.

### Important fields

- `id`
- `name`
- `description`
- `is_active`
- `created_at`
- `updated_at`

Examples:

- IT Support
- Maintenance
- Hostel
- Transport
- Security

---

## 4. Category

A Category represents a complaint classification and belongs to a
Department.

### Important fields

- `id`
- `name`
- `description`
- `department`
- `is_active`
- `created_at`
- `updated_at`

Examples:

- Wi-Fi → IT Support
- Network → IT Support
- Electrical → Maintenance
- Plumbing → Maintenance
- Food → Hostel
- Bus → Transport
- CCTV → Security

A database constraint prevents duplicate category names within the
same department.

---

## 5. Complaint

Complaint is the central business entity in CivicResolve.

### Important fields

- `id`
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

### Status values

- `SUBMITTED`
- `AI_ANALYZING`
- `ASSIGNED`
- `ACKNOWLEDGED`
- `IN_PROGRESS`
- `NEEDS_INFORMATION`
- `ESCALATED`
- `RESOLVED`
- `CLOSED`
- `REOPENED`
- `REJECTED`

### Priority values

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

### Ticket number

Each complaint receives a unique ticket number.

Example:

`CR-000020`

---

## 6. Complaint Assignment

ComplaintAssignment records the assignment of a complaint to an
officer and department.

### Important fields

- `id`
- `complaint`
- `department`
- `officer`
- `assigned_by`
- `assigned_at`
- `unassigned_at`
- `reason`

The assignment model also supports reassignment by retaining assignment
history.

---

## 7. Complaint History

ComplaintHistory stores the audit trail of complaint status changes.

### Important fields

- `id`
- `complaint`
- `changed_by`
- `old_status`
- `new_status`
- `comment`
- `created_at`

This allows the system to track how a complaint progressed through its
lifecycle.

---

## 8. Complaint Analysis

ComplaintAnalysis stores the result of AI-based complaint analysis.

### Important fields

- `id`
- `complaint`
- `summary`
- `predicted_category`
- `predicted_department`
- `predicted_priority`
- `urgency`
- `confidence`
- `model_name`

The AI analysis is stored separately from the core Complaint entity.

This keeps AI-specific information isolated from the main complaint
record.

---

## 9. SLA Policy

SLAPolicy defines the response and resolution time limits for each
priority level.

### Important fields

- `id`
- `priority`
- `response_time_hours`
- `resolution_time_hours`
- `active`

---

## 10. Complaint SLA

ComplaintSLA stores the SLA information associated with a complaint.

### Important fields

- `id`
- `complaint`
- `policy`
- `response_deadline`
- `resolution_deadline`
- `response_completed_at`
- `resolution_completed_at`
- `response_breached`
- `resolution_breached`

This allows CivicResolve to monitor both response and resolution SLA
compliance.

---

## 11. Notification

Notifications are part of the planned CivicResolve V2 functionality.

The planned Notification entity will support:

- Recipient
- Complaint
- Notification type
- Message
- Read/unread state
- Creation timestamp

Notifications will be used for events such as:

- New complaint assignment
- SLA warnings
- SLA breaches
- Escalations
- Complaint resolution
- Complaint reopening

This entity will be implemented during the V2 Notifications phase.

---

## 12. Feedback

Citizen resolution feedback is part of the complaint resolution
workflow.

Feedback functionality is associated with the resolution/reopen
process.

The exact V2 database representation will be documented after the
feedback implementation is finalized.

---

## 13. V2 Planned Database Extensions

The following entities are planned for CivicResolve V2.

### Duplicate Detection

Potential entities:

- `ComplaintSimilarity`
- `ComplaintCluster`

These will support semantic similarity and grouping of related
complaints.

### SLA Prediction

Potential entity:

- `SLARiskPrediction`

Possible information:

- Complaint
- Risk score
- Risk level
- Model version
- Prediction timestamp

### Knowledge Base

Potential entities:

- `KnowledgeArticle`
- `KnowledgeCategory`

These will store approved operational knowledge used by the AI
resolution recommendation system.

### Multimodal Complaints

The complaint model/storage layer will be extended to support uploaded
media such as images and audio.

The exact storage design will be finalized during implementation.

---

## 14. Relationships

The core relationships are:

```text
User
 │
 ├── Department
 │
 └── Complaint
       │
       ├── Category
       │      └── Department
       │
       ├── ComplaintAnalysis
       │
       ├── ComplaintAssignment
       │      ├── Officer
       │      └── Department
       │
       ├── ComplaintHistory
       │      └── User
       │
       └── ComplaintSLA
              └── SLAPolicy
