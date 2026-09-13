# CivicResolve Testing Strategy

## 1. Purpose

The CivicResolve testing strategy is designed to verify:

- API correctness
- Authentication
- Role-based authorization
- Complaint validation
- Complaint workflow correctness
- AI integration
- AI failure and fallback handling
- Department routing
- Officer assignment
- SLA calculation and monitoring
- Complaint history and auditability
- Frontend/backend integration
- Responsive behavior
- Accessibility
- Production build stability

Testing will expand as additional V2 features are implemented.

---

# 2. Current Automated Test Status

The current Django backend test suite contains:

```text
9 tests

Latest verified result:

Ran 9 tests in 14.313s

OK

Django system checks also completed successfully:

System check identified no issues (0 silenced).

Current status:

Metric	Result
Tests discovered	9
Tests passed	9
Tests failed	0
Django system check	Pass
3. Testing Levels

CivicResolve uses several testing levels.

3.1 Unit Testing

Unit tests verify individual pieces of application logic.

Examples include:

Serializer validation
Complaint validation
SLA calculations
Status transition logic
Assignment validation
AI response validation
Utility/service functions
3.2 API Testing

API tests verify REST API behavior.

Important checks include:

HTTP status codes
Authentication requirements
Role permissions
Request validation
Response structure
Resource visibility
Invalid resource handling
3.3 Integration Testing

Integration tests verify interactions between multiple backend components.

The complaint creation flow is conceptually:

Complaint API
      |
      v
Complaint Creation Service
      |
      v
AI Analysis
      |
      v
Category / Department Routing
      |
      v
Officer Selection
      |
      v
Officer Assignment
      |
      v
SLA Creation
      |
      v
Complaint History

Tests should verify that these components work correctly together.

3.4 Frontend Integration Testing

Frontend integration testing verifies communication between the React application and Django REST API.

Important scenarios include:

Login
JWT token handling
Current-user loading
Protected routes
Dashboard loading
Complaint submission
Complaint tracking
Complaint history
Officer actions
Admin assignment
SLA monitoring
Profile updates
Activity display
Error handling
3.5 End-to-End Testing

End-to-end testing verifies complete user journeys.

A primary citizen journey is:

Login
  |
  v
Submit complaint
  |
  v
AI analysis
  |
  v
Department routing
  |
  v
Officer assignment
  |
  v
Officer acknowledgement
  |
  v
Officer starts work
  |
  v
Officer resolves complaint
  |
  v
Citizen provides feedback
  |
  v
Admin closes or complaint is reopened
4. Authentication Testing

Authentication tests should verify:

Valid credentials produce tokens
Invalid credentials are rejected
Missing credentials are rejected
Missing access token is rejected on protected endpoints
Invalid access tokens are rejected
Expired access tokens are rejected
Valid refresh tokens produce new access tokens
Protected endpoints cannot be accessed anonymously
Current-user endpoint returns the authenticated user
5. Authorization Testing

Role-based authorization is critical to CivicResolve.

5.1 Citizen

Verify that citizens:

Can create complaints
Can view their own complaints
Cannot view another citizen's complaints
Cannot assign complaints
Cannot perform officer-only actions
Cannot perform admin-only actions
Can view their own activity
Can update their own profile
5.2 Officer

Verify that officers:

Can view complaints assigned to them
Cannot access complaints assigned only to another officer
Can acknowledge assigned complaints
Can start assigned complaints
Can resolve assigned complaints
Cannot perform admin-only assignment operations
Cannot access admin-only SLA data
Cannot close complaints when closure is admin-only
Can view relevant activity
5.3 Admin

Verify that admins:

Can view all complaints
Can assign complaints
Can reassign complaints
Can access all assignments
Can access SLA records
Can close complaints
Can access active officer data
Can view global activity
Can access analytics functionality
6. Complaint Validation Testing

Invalid complaint input should be tested.

Title

Test:

Less than 5 characters
Exactly 5 characters
Valid normal title
Exactly 200 characters
More than 200 characters
Description

Test:

Less than 10 characters
Exactly 10 characters
Valid description
Location

When provided, test:

Less than 3 characters
Exactly 3 characters
Valid location
Latitude

Test:

Below -90
Exactly -90
Valid value
Exactly 90
Above 90
Longitude

Test:

Below -180
Exactly -180
Valid value
Exactly 180
Above 180
Other validation

Also test:

Missing required fields
Invalid category
Invalid data types
Malformed request bodies
7. Complaint Workflow Testing

Complaint status changes should be treated as a workflow/state machine.

Important states include:

SUBMITTED
AI_ANALYZING
ASSIGNED
ACKNOWLEDGED
IN_PROGRESS
RESOLVED
CLOSED
REOPENED

Testing should verify:

Valid transitions succeed
Invalid transitions are rejected
Correct role can perform each transition
Unauthorized roles are rejected
Status history is created
Old status is recorded
New status is recorded
Correct user is recorded
Timestamps are recorded
Resolution timestamps are updated correctly
Closure timestamps are updated correctly
Reopened complaints follow the intended workflow
8. Complaint Assignment Testing

Assignment tests should cover:

Admin assignment
Admin reassignment
Officer existence validation
Officer role validation
Officer active-status validation
Department existence
Department active-status validation
Officer/department relationship validation
Invalid complaint status
Closing previous active assignment
Creating new active assignment
Assignment reason
Assignment history
Correct assignment visibility by role
9. AI Testing

AI output should never be treated as automatically trustworthy.

The system should validate AI responses before using them.

9.1 Valid AI Output

Test:

Valid summary
Valid predicted category
Valid predicted department
Valid priority
Valid urgency score
Valid confidence score
Valid model name
9.2 Invalid AI Output

Test:

Missing fields
Invalid category
Invalid department
Invalid priority
Urgency score below 0
Urgency score above 100
Confidence score below 0
Confidence score above 100
Malformed model response
Unexpected response structure
9.3 AI Provider Failure

Test:

Provider/API failure
Timeout
Invalid API response
Temporary service failure
Unexpected exception

The complaint creation process should remain usable when AI analysis fails.

The fallback path must be tested so that an AI outage does not unnecessarily prevent complaint submission.

10. AI Evaluation

AI functionality should eventually be evaluated using real test datasets.

Potential classification metrics include:

Accuracy
Precision
Recall
F1 score

Routing evaluation should measure:

Department routing accuracy
Correct category prediction
Correct priority prediction

Additional AI quality measures may include:

Confidence calibration
AI failure rate
Fallback rate
Invalid-output rate

No AI performance metric should be reported without actual evaluation data.

11. SLA Testing

SLA functionality should be tested for:

SLA creation
Priority-based policy selection
Response deadline calculation
Resolution deadline calculation
Response completion
Resolution completion
Response breach detection
Resolution breach detection
Breached-only filtering
SLA monitoring
Escalation behavior
11.1 SLA Boundary Testing

Important boundary conditions include:

Before deadline
     |
     v
Exactly at deadline
     |
     v
After deadline

These cases are important because small timing errors can cause incorrect breach classification.

12. History and Audit Testing

Complaint history provides traceability for important workflow changes.

Verify that each important status change records:

Complaint
User responsible for the change
Previous status
New status
Comment where applicable
Timestamp

Also verify that:

History belongs to the correct complaint
History is returned in chronological order
Reassignment does not silently remove previous assignment information
Important workflow actions remain auditable
13. Organization API Testing

Test the organization APIs.

Categories
GET /api/organizations/categories/

Verify:

Authentication is required
Only active categories are returned
Categories from inactive departments are excluded
Results are ordered correctly
Departments
GET /api/organizations/departments/

Verify:

Authentication is required
Only active departments are returned
Results are ordered by department name
Officers
GET /api/organizations/officers/

Verify:

Authentication is required
Admin permission is required
Only active officers are returned
Officers belong to active departments
Officer filtering
GET /api/organizations/officers/?department={id}

Verify:

Department filtering works
Invalid department values are handled safely
Only matching active officers are returned
14. Profile API Testing

Test:

Retrieve profile
Update first name
Update last name
Update phone
Invalid phone
Phone below minimum length
Phone above maximum length
Attempt to change email
Attempt to change role
Attempt to change department
Unauthenticated profile access

Read-only fields should not be modifiable through the profile serializer.

15. Assignment API Testing

Test:

Admin can list assignments
Officer can see own assignments
Citizen cannot access assignment listing
Admin can create assignment
Admin can update assignment
Admin can delete assignment
Complaint filtering works
Unauthorized assignment access is rejected
16. SLA API Testing

Test:

Admin can list SLA records
Non-admin users cannot access SLA records
Status filtering works
Priority filtering works
breached=true filtering works
Response breach values are correct
Resolution breach values are correct
Deadline fields are correct
17. Activity API Testing

Test:

Citizen
Can view own complaint activity
Cannot view unrelated complaint activity
Officer
Can view activity related to assigned complaints
Cannot view unrelated complaints
Admin
Can view global activity

Also verify:

Correct ordering
Correct complaint association
Correct user information
18. Frontend Testing

The frontend should be tested for all major role-based workflows.

Authentication

Test:

Login success
Invalid login
Token handling
Protected routes
Logout
Current-user loading
Citizen

Test:

Dashboard
Complaint submission
Complaint list
Complaint details
Complaint history
Resolution feedback
Reopen workflow
Profile
Activity
Officer

Test:

Dashboard
Assigned complaint list
Complaint details
Acknowledge
Start
Resolve
Profile
Activity
Admin

Test:

Dashboard
Complaint overview
Search/filter/sort
Assignment
Reassignment
SLA monitoring
Analytics
Complaint closure
Profile
Activity
19. Frontend State Testing

Data-driven screens should support the following states:

Loading
   |
   +----> Success
   |
   +----> Error
   |
   +----> Empty
   |
   +----> Filtered Empty

Verify that users receive useful feedback in each state.

Important UI states include:

Loading indicators
Error messages
Retry actions
Empty-state messages
Disabled actions while processing
20. Responsive Testing

The frontend should be tested at:

Desktop
Tablet
Mobile

Important areas include:

Top navigation
Sidebar/navigation
Dashboard cards
Complaint tables
Complaint forms
Complaint detail pages
Filters
Action buttons
Profile forms
Activity pages

Wide tables may use intentional horizontal scrolling.

Other pages should avoid unnecessary horizontal overflow.

21. Accessibility Testing

Accessibility checks should include:

Keyboard navigation
Visible focus indicators
Meaningful button labels
Form labels
Semantic headings
Accessible error messages
Accessible loading messages
Appropriate interactive target sizes
Meaningful link text
Reduced-motion support

Interactive elements should remain usable without relying only on mouse interaction.

22. Regression Testing

Whenever a feature changes, previously working workflows should be retested.

Minimum regression workflow:

Login
  |
  v
Citizen complaint creation
  |
  v
AI processing
  |
  v
Department routing
  |
  v
Officer assignment
  |
  v
Officer acknowledgement
  |
  v
Officer starts work
  |
  v
Officer resolution
  |
  v
Citizen feedback
  |
  v
Reopen if applicable
  |
  v
Admin closure

Also retest:

Profile
Activity
SLA monitoring
Analytics
Role-based navigation
Complaint search/filtering
23. Manual API Testing

During development, APIs may be tested using tools such as:

Postman
Insomnia
REST Client
Browser for suitable GET requests
Frontend integration

For each important API, test:

Valid request
Missing authentication
Wrong role
Invalid input
Non-existent resource
Successful request
24. Test Data Strategy

Development and testing should use representative test accounts.

Minimum roles:

Admin
Officer
Citizen

Organizations should contain:

Multiple departments
Multiple categories
Multiple officers
Officers belonging to different departments

Complaint test data should include:

Different priorities
Different categories
Different departments
Different statuses
Assigned complaints
Unassigned complaints
Resolved complaints
Closed complaints
Reopened complaints
SLA-breached complaints
25. Security Testing

Security testing should verify:

Authentication is required for protected endpoints
Role permissions cannot be bypassed
Users cannot access another user's private complaints
Officers cannot access unrelated complaints
Admin-only endpoints reject other roles
JWT handling is secure
Secrets are not committed to Git
API keys are stored in environment variables
Debug mode is disabled in production
Error messages do not expose sensitive information
CORS is restricted appropriately for production

Security testing will be expanded during the dedicated security milestone.

26. Performance Testing

Performance testing should eventually measure:

API response time
Database query performance
Complaint list performance
Complaint detail performance
AI analysis latency
SLA monitoring performance
Large complaint dataset behavior
Concurrent request behavior

Performance numbers should be recorded from actual tests.

27. Production Build Testing

Before deployment, verify:

Backend
python manage.py test

The command must complete with:

OK

Also run:

python manage.py check

The Django system check should report no issues.

Frontend

Run:

npm run build

The production build must complete successfully without errors.

28. Continuous Regression Checklist

Before major commits or releases:

[ ] Backend tests pass
[ ] Django system check passes
[ ] Frontend build passes
[ ] Authentication works
[ ] Citizen workflow works
[ ] Officer workflow works
[ ] Admin workflow works
[ ] Assignment works
[ ] SLA monitoring works
[ ] Profile works
[ ] Activity works
[ ] Analytics works
[ ] No secrets committed
[ ] No unexpected console errors
29. Future V2 Testing

Testing will expand as new features are implemented.

Duplicate Complaint Detection

Measure:

Similarity accuracy
Duplicate detection precision
Duplicate detection recall
F1 score
False-positive rate
False-negative rate
Clustering quality
AI SLA-Breach Prediction

Measure:

MAE
RMSE
Prediction accuracy
Precision
Recall
F1 score
Performance by priority level
Knowledge Base

Measure:

Retrieval relevance
Retrieval precision
Answer grounding
Source correctness
Hallucination rate
Resolution recommendation usefulness
Multimodal Complaints

Measure:

Voice transcription quality
Image processing accuracy
Extraction accuracy
Failure rate
Processing latency
Smart Assignment

Measure:

Assignment accuracy
Workload distribution
SLA impact
Reassignment rate
Officer utilization
30. Testing Principles

CivicResolve follows these principles:

Test real behavior, not assumptions.
Do not report fabricated metrics.
Test both successful and failure paths.
Treat authorization as a security requirement.
Validate AI output before using it.
Keep the system usable when external AI services fail.
Maintain auditability of important workflow changes.
Run regression tests after significant changes.
Test the frontend and backend together for critical user journeys.
Record actual measurements for performance and AI evaluation.
31. Current Status

Current verified backend status:

Automated tests: 9
Passing: 9
Failing: 0
Django system check: PASS

The frontend production build has also previously been verified successfully with Vite.

The testing strategy will be updated as the system moves from V1 into V2 and production deployment.