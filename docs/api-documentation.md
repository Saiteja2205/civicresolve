All application APIs are prefixed with:

/api/
2. Authentication

CivicResolve uses JWT authentication.

Protected API requests require the following HTTP header:

Authorization: Bearer <access_token>
2.1 Obtain JWT Token
POST /api/auth/token/

Authenticates a user and returns an access token and refresh token.

Request
{
  "email": "user@example.com",
  "password": "password"
}
Response
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
2.2 Refresh JWT Token
POST /api/auth/token/refresh/

Generates a new access token using a valid refresh token.

Request
{
  "refresh": "<refresh_token>"
}
Response
{
  "access": "<new_access_token>"
}
3. Current User API
3.1 Get Current User
GET /api/auth/me/

Authentication required.

Returns information about the currently authenticated user.

Response fields
id
email
phone
role
role_display
department
department_name
first_name
last_name
Example
{
  "id": 1,
  "email": "citizen@example.com",
  "phone": "9876543210",
  "role": "CITIZEN",
  "role_display": "Citizen",
  "department": null,
  "department_name": null,
  "first_name": "Example",
  "last_name": "User"
}
4. User Profile API
4.1 Get Profile
GET /api/auth/profile/

Authentication required.

Returns the authenticated user's profile.

4.2 Update Profile
PUT /api/auth/profile/

Authentication required.

Updates the authenticated user's profile.

4.3 Partially Update Profile
PATCH /api/auth/profile/

Authentication required.

Updates selected profile fields.

Editable fields
phone
first_name
last_name
Read-only fields
id
email
role
role_display
department
department_name
Phone validation

The phone field:

Must contain digits
Minimum length: 10
Maximum length: 15
5. Complaint APIs
5.1 List Complaints
GET /api/complaints/

Authentication required.

Complaint visibility depends on the authenticated user's role.

Citizen

Citizens can view their own complaints.

Officer

Officers can view complaints that are actively assigned to them.

Admin

Admins can view all complaints.

5.2 Create Complaint
POST /api/complaints/

Authentication required.

Citizen access.

Complaint creation is handled through the complaint creation service.

The service performs the initial complaint workflow and AI processing.

Request
{
  "category": 1,
  "title": "Street light not working",
  "description": "The street light near the main road has not been working for three days.",
  "location": "Main Road",
  "latitude": 17.3850,
  "longitude": 78.4867
}
Validation
Title
Minimum length: 5 characters
Maximum length: 200 characters
Description
Minimum length: 10 characters
Location

If provided:

Minimum length: 3 characters
Latitude

Must be between:

-90 and 90
Longitude

Must be between:

-180 and 180
5.3 Retrieve Complaint
GET /api/complaints/{id}/

Authentication required.

Returns a single complaint if the authenticated user has permission to access it.

5.4 Update Complaint
PUT /api/complaints/{id}/

Authentication required.

Admin/officer access.

5.5 Partially Update Complaint
PATCH /api/complaints/{id}/

Authentication required.

Admin/officer access.

5.6 Delete Complaint
DELETE /api/complaints/{id}/

Authentication required.

Admin-only access.

6. Complaint Workflow Actions

CivicResolve uses dedicated endpoints for important complaint workflow actions.

6.1 Assign Complaint
POST /api/complaints/{id}/assign/

Admin-only access.

Request
{
  "officer_id": 12,
  "department_id": 3
}

The assignment operation validates:

Officer exists
Officer is active
Officer has the officer role
Department exists
Department is active
Officer belongs to the selected department
Complaint is in an assignable status

Supported assignable complaint statuses include:

SUBMITTED
AI_ANALYZING
REOPENED
ASSIGNED

If an active assignment already exists, the previous active assignment is closed before creating the new assignment.

6.2 Acknowledge Complaint
POST /api/complaints/{id}/acknowledge/

Officer-only access.

Moves the complaint through the acknowledgement workflow.

6.3 Start Complaint
POST /api/complaints/{id}/start/

Officer-only access.

Moves the complaint into active processing.

6.4 Resolve Complaint
POST /api/complaints/{id}/resolve/

Officer-only access.

Marks the complaint as resolved through the centralized complaint status workflow.

6.5 Close Complaint
POST /api/complaints/{id}/close/

Admin-only access.

Closes a resolved complaint.

7. Reopen Complaint
POST /api/complaints/{id}/reopen/

Authentication required.

Reopens a complaint through the supported resolution workflow.

The endpoint is implemented using the complaint reopen view.

8. Complaint History
8.1 Get Complaint History
GET /api/complaints/{id}/history/

Authentication required.

Returns the status/history records associated with a complaint.

Response fields
id
complaint
changed_by
changed_by_email
old_status
new_status
comment
created_at

History records are returned in chronological order.

Example
{
  "id": 10,
  "complaint": 25,
  "changed_by": 7,
  "changed_by_email": "officer@example.com",
  "old_status": "ASSIGNED",
  "new_status": "ACKNOWLEDGED",
  "comment": "Complaint acknowledged.",
  "created_at": "2026-09-13T10:30:00Z"
}
9. Complaint Assignments
9.1 List Assignments
GET /api/assignments/

Authentication required.

Assignment visibility depends on role.

Role	Access
Citizen	No assignment list access
Officer	Own assignments
Admin	All assignments
9.2 Filter Assignments by Complaint
GET /api/assignments/?complaint={id}

Returns assignments associated with the specified complaint, subject to role permissions.

9.3 Retrieve Assignment
GET /api/assignments/{id}/

Authentication required.

9.4 Create Assignment
POST /api/assignments/

Admin-only access.

9.5 Update Assignment
PUT /api/assignments/{id}/

Admin-only access.

9.6 Partially Update Assignment
PATCH /api/assignments/{id}/

Admin-only access.

9.7 Delete Assignment
DELETE /api/assignments/{id}/

Admin-only access.

10. SLA APIs
10.1 List SLA Records
GET /api/sla/

Authentication required.

Admin-only access.

SLA records are read-only through this API.

10.2 Filter SLA Records by Status
GET /api/sla/?status={status}
10.3 Filter SLA Records by Priority
GET /api/sla/?priority={priority}
10.4 Get Breached SLA Records
GET /api/sla/?breached=true

Returns SLA records where response or resolution breach conditions are present.

10.5 SLA Response Fields

SLA records expose:

id
complaint
complaint_ticket_number
title
priority
status
policy
policy_priority
response_time_hours
resolution_time_hours
response_deadline
resolution_deadline
response_completed_at
resolution_completed_at
response_breached
resolution_breached
11. User Activity API
11.1 Get User Activity
GET /api/activity/

Authentication required.

Returns complaint history/activity records visible to the authenticated user.

Admin

Admins can view activity across complaints.

Officer

Officers can view activity related to complaints assigned to them.

Citizen

Citizens can view activity related to their own complaints.

12. Organization APIs

Organization APIs expose active categories, departments, and officers.

12.1 List Active Categories
GET /api/organizations/categories/

Authentication required.

Returns active complaint categories belonging to active departments.

Categories are ordered by:

Department name
Category name
12.2 List Active Departments
GET /api/organizations/departments/

Authentication required.

Returns active departments ordered by name.

12.3 List Active Officers
GET /api/organizations/officers/

Authentication required.

Admin-only access.

Returns active officers belonging to active departments.

Response fields
id
email
phone
department_id
department_name
is_active
Example
{
  "id": 12,
  "email": "officer@example.com",
  "phone": "9876543210",
  "department_id": 3,
  "department_name": "Municipal Services",
  "is_active": true
}
12.4 Filter Officers by Department
GET /api/organizations/officers/?department={department_id}

Authentication required.

Admin-only access.

Returns active officers belonging to the specified department.

13. Complaint Serializer Fields

The complaint API exposes the following fields:

id
ticket_number
user
user_email
category
category_name
department_name
title
description
status
priority
location
latitude
longitude
created_at
updated_at
resolved_at
closed_at
Read-only complaint fields

The following fields are controlled by the backend:

id
ticket_number
user
user_email
category_name
department_name
status
priority
created_at
updated_at
resolved_at
closed_at
14. Complaint AI Analysis Data

Complaint AI analysis records contain:

id
complaint
complaint_ticket_number
summary
predicted_category
predicted_category_name
predicted_department
predicted_department_name
predicted_priority
urgency_score
confidence_score
model_name
created_at
updated_at
AI score ranges

The following values are constrained to:

0 - 100
urgency_score
confidence_score

AI analysis is integrated into complaint creation, with fallback handling when AI analysis fails.

15. Complaint Assignment Serializer Fields

Assignment records contain:

id
complaint
department
department_name
officer
officer_email
assigned_by
assigned_by_email
assigned_at
unassigned_at
reason

Backend-controlled fields include:

id
assigned_by
assigned_by_email
assigned_at
officer_email
department_name
16. Permission Summary
Operation	Citizen	Officer	Admin
Login/token	Yes	Yes	Yes
Current user	Yes	Yes	Yes
Profile	Yes	Yes	Yes
Create complaint	Yes	No	No
View own complaints	Yes	No	Yes
View assigned complaints	No	Yes	Yes
Update complaint	No	Yes	Yes
Delete complaint	No	No	Yes
Assign complaint	No	No	Yes
Acknowledge complaint	No	Yes	No
Start complaint	No	Yes	No
Resolve complaint	No	Yes	No
Close complaint	No	No	Yes
Reopen complaint	Authenticated	Authenticated	Authenticated
Complaint history	Own	Assigned	All
Assignments	No	Own	All
SLA records	No	No	Yes
Activity	Own	Assigned	All
Categories	Authenticated	Authenticated	Authenticated
Departments	Authenticated	Authenticated	Authenticated
Officers	No	No	Yes
17. Common HTTP Status Codes
200 OK

Request completed successfully.

201 Created

A new resource was successfully created.

204 No Content

Request completed successfully without a response body.

400 Bad Request

Request validation failed or request data is invalid.

401 Unauthorized

Authentication is missing, invalid, or expired.

403 Forbidden

The user is authenticated but does not have permission to perform the requested operation.

404 Not Found

The requested resource does not exist or is not accessible.

18. Development API Configuration

The current development backend uses:

http://127.0.0.1:8000

The frontend communicates with the backend using HTTP requests and JWT authentication.

Production deployment should use:

HTTPS
Secure environment variables
Production database configuration
Correct CORS configuration
Production server configuration
Secure secret management
Debug mode disabled
19. Planned V2 APIs

The following are planned features and are not current API endpoints.

They should only be added to the implemented API documentation after development and testing.

Planned areas include:

Duplicate complaint detection
Complaint similarity search
Duplicate/related complaint clustering
AI SLA-breach prediction
Knowledge-base search
AI-assisted resolution recommendations
Voice complaint submission
Image/evidence upload
Smart workload balancing
In-app notifications
Email notifications
20. API Documentation Status

The current API documentation covers the implemented:

JWT authentication
Current-user API
Profile API
Complaint API
Complaint workflow actions
Complaint reopen workflow
Complaint history
Assignment API
SLA API
Activity API
Category API
Department API
Officer API
Role-based access control