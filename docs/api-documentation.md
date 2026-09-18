# CivicResolve — API Documentation

Base URL in local development:

```text
http://127.0.0.1:8000/api
```

The API uses JWT authentication. Protected requests should include:

```text
Authorization: Bearer <access_token>
```

## Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/token/` | Obtain access and refresh tokens |
| POST | `/auth/token/refresh/` | Refresh an access token |
| GET | `/auth/me/` | Get the authenticated user |
| GET/PATCH | `/auth/profile/` | View/update the user profile |

## Complaints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/complaints/` | List complaints visible to the authenticated role |
| POST | `/complaints/` | Create a complaint; citizen only |
| GET | `/complaints/{id}/` | Retrieve a complaint |
| PUT/PATCH | `/complaints/{id}/` | Update a complaint under backend permission rules |
| DELETE | `/complaints/{id}/` | Delete a complaint; administrator permission |
| GET | `/complaints/{id}/duplicates/` | Get duplicate candidates for a complaint |
| POST | `/complaints/{id}/assign/` | Assign/reassign a complaint |
| POST | `/complaints/{id}/acknowledge/` | Acknowledge an assigned complaint |
| POST | `/complaints/{id}/start/` | Move complaint to in-progress |
| POST | `/complaints/{id}/resolve/` | Resolve a complaint |
| POST | `/complaints/{id}/close/` | Close a resolved complaint |
| GET | `/complaints/{id}/history/` | Get complaint status history |
| POST | `/complaints/{id}/reopen/` | Reopen a citizen-owned resolved complaint |
| GET | `/complaints/{id}/sla-risk/` | Calculate current SLA risk |
| POST | `/complaints/{id}/resolution-assistant/` | Generate AI resolution assistance |

### Complaint creation

Example request body:

```json
{
  "title": "Large pothole near Block A",
  "description": "A large pothole has been present near Block A for several days.",
  "category": 1,
  "location": "Block A entrance",
  "latitude": 17.385000,
  "longitude": 78.486700
}
```

`location`, `latitude`, and `longitude` are optional in the frontend flow.

## Assignments

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/assignments/` | List assignments visible to the role |
| POST | `/assignments/` | Create an assignment; administrator |
| GET | `/assignments/{id}/` | Retrieve an assignment |
| PUT/PATCH | `/assignments/{id}/` | Update an assignment; administrator |
| DELETE | `/assignments/{id}/` | Remove an assignment; administrator |

The assignment logic validates that the selected user is an officer and belongs to the selected department.

The `complaint` query parameter can be used to filter assignments by complaint ID.

## SLA

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/sla/` | List SLA records; administrator |
| GET | `/sla/{id}/` | Retrieve an SLA record; administrator |

Supported filters in the current view include:

- `status`
- `priority`
- `breached=true`

## Duplicate Complaints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/complaint-duplicates/` | List duplicate candidate records visible to the role |
| GET | `/complaint-duplicates/{id}/` | Retrieve a duplicate candidate |
| PUT/PATCH | `/complaint-duplicates/{id}/` | Review a candidate; administrator only |

Duplicate records are generated automatically. Direct creation and deletion through the API are disabled.

Administrative review can update:

```text
status
review_comment
```

Allowed review statuses:

```text
PENDING
CONFIRMED
REJECTED
```

## Evidence

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/complaint-evidence/` | List evidence visible to the role |
| POST | `/complaint-evidence/` | Upload evidence; citizen for their own complaint |
| GET | `/complaint-evidence/{id}/` | Retrieve evidence |
| DELETE | `/complaint-evidence/{id}/` | Delete evidence under endpoint permission rules |

Evidence upload expects multipart form data containing the complaint ID and image.

Current validation limits include:

- Maximum image size: 5 MB
- Supported image types: JPEG, PNG, WEBP
- File contents are verified as valid images

Evidence can be analyzed using Gemini Vision after upload.

## Resolution Feedback

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/complaints/{id}/resolution-feedback/` | Get feedback for the complaint's current resolution cycle |
| POST | `/complaints/{id}/resolution-feedback/` | Submit citizen feedback for the current cycle |
| GET | `/complaints/resolution-feedback/{id}/` | Retrieve a feedback record |
| PUT/PATCH | `/complaints/resolution-feedback/{id}/` | Update feedback under the current-cycle rules |

Feedback ratings are constrained to 1–5.

## Reopen

```text
POST /complaints/{id}/reopen/
```

Only the citizen who owns the complaint can request reopening, and the complaint must currently be `RESOLVED`.

The reopen comment must contain at least 10 characters.

If an active assignment exists, the reopened complaint is returned to `ASSIGNED`; otherwise it remains `REOPENED` and waits for reassignment.

## Voice Translation

```text
POST /voice-translation/
```

Request:

```json
{
  "text": "Voice transcript goes here"
}
```

Response shape:

```json
{
  "detected_language": "Telugu",
  "english_title": "Water Problem in Hostel",
  "english_description": "There is a water problem in the hostel."
}
```

The service does not modify the original complaint because the endpoint processes a transcript before complaint creation.

## AI Evaluation

```text
POST /ai-evaluation/
```

Administrator-only endpoint for running the configured benchmark cases.

## Activity

```text
GET /activity/
```

Returns complaint-history activity visible to the authenticated user.

## Organizations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/organizations/categories/` | List active categories |
| GET | `/organizations/departments/` | List active departments |
| GET | `/organizations/officers/` | List active officers |

The officer endpoint accepts an optional `department` query parameter.

## Notifications

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/notifications/` | List notifications and unread count |
| POST | `/notifications/{id}/read/` | Mark one notification as read |
| POST | `/notifications/read-all/` | Mark all notifications as read |

## Permission Model

The backend uses role-specific permissions and queryset filtering.

### Citizen

Can create complaints and access their own complaints and related records.

### Officer

Can access complaints currently assigned to them for officer workflow operations.

### Administrator

Can access system-wide complaint and operational management features permitted by the application.

Backend authorization should always be treated as the source of truth.
