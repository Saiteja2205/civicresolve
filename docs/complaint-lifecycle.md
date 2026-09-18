# CivicResolve — Complaint Lifecycle

## 1. State Model

The backend defines these complaint statuses:

```text
SUBMITTED
AI_ANALYZING
ASSIGNED
ACKNOWLEDGED
IN_PROGRESS
NEEDS_INFORMATION
ESCALATED
RESOLVED
CLOSED
REOPENED
REJECTED
```

## 2. Valid Transitions

```text
SUBMITTED
├── AI_ANALYZING
├── ASSIGNED
└── REJECTED

AI_ANALYZING
├── ASSIGNED
└── SUBMITTED

ASSIGNED
└── ACKNOWLEDGED

ACKNOWLEDGED
└── IN_PROGRESS

IN_PROGRESS
├── RESOLVED
├── NEEDS_INFORMATION
└── ESCALATED

NEEDS_INFORMATION
└── IN_PROGRESS

ESCALATED
├── IN_PROGRESS
└── RESOLVED

RESOLVED
├── CLOSED
└── REOPENED

REOPENED
└── ASSIGNED

CLOSED
└── no transition

REJECTED
└── no transition
```

## 3. Submission

A citizen submits a complaint with a title, description, category, and optional location data.

The complaint is created with `SUBMITTED` status. The complaint-creation service starts the downstream AI/routing workflow according to the configured application flow.

## 4. AI Analysis

The complaint enters `AI_ANALYZING` while AI analysis is generated.

The analysis can determine:

- Language
- English normalized content
- Summary
- Explanation
- Category
- Department
- Priority
- Urgency
- Confidence

If AI analysis fails, the orchestration service can return the complaint to `SUBMITTED` rather than leaving the complaint permanently in the analysis state.

## 5. Assignment

After routing, an administrator can assign the complaint to an officer and department.

The assignment model records who created the assignment and whether the assignment remains active.

## 6. Officer Processing

The officer workflow is:

```text
ASSIGNED
   |
   v
ACKNOWLEDGED
   |
   v
IN_PROGRESS
```

From `IN_PROGRESS`, the complaint can be resolved, moved to `NEEDS_INFORMATION`, or escalated.

## 7. Resolution

When a complaint reaches `RESOLVED`, `resolved_at` is recorded.

The citizen can then provide resolution feedback.

An administrator can close a resolved complaint, setting `closed_at`.

## 8. Resolution Feedback

Feedback is stored with a `resolution_cycle`.

This allows a complaint to have a separate feedback record for each completed resolution cycle.

```text
Cycle 1
RESOLVED
  |
  +--> Feedback
  |
  +--> REOPENED
          |
          v
       ASSIGNED
          |
          v
       ACKNOWLEDGED
          |
          v
       IN_PROGRESS
          |
          v
       RESOLVED
          |
          +--> Cycle 2 Feedback
```

A feedback record is unique per complaint per resolution cycle and ratings are limited to 1–5.

## 9. Reopening

Only a citizen who owns the complaint can request reopening, and the complaint must be `RESOLVED`.

The citizen must provide a reopening explanation of at least 10 characters.

If an active assignment exists, the complaint is moved through `REOPENED` back to `ASSIGNED` for the existing officer. If there is no active assignment, the complaint remains `REOPENED` until reassignment.

## 10. Audit Trail

Every status transition is recorded in `ComplaintHistory` with:

- Old status
- New status
- User or system actor
- Comment
- Timestamp

Notifications are generated for complaint status changes and other operational events through the notification service.
