# CivicResolve

## AI-Powered Grievance Intelligence & Resolution Platform

CivicResolve is a full-stack grievance management platform that uses AI to understand, classify, prioritize and route citizen complaints while providing structured workflows for officers and administrators.

The platform is designed around the complete complaint lifecycle:

**Submission → AI Analysis → Routing → Assignment → SLA Monitoring → Resolution → Feedback → Closure**

---

## Project Status

### Version 1 — Core Platform Complete

The current V1 implementation includes:

* Role-based authentication
* Citizen dashboard
* Officer workspace
* Administrator dashboard
* Complaint submission
* AI-based complaint analysis
* Category and department routing
* Officer assignment and reassignment
* Complaint lifecycle management
* Complaint history and audit trail
* SLA calculation
* SLA monitoring
* Escalation workflow
* Resolution and reopening
* Citizen feedback
* Search, filtering and sorting
* Analytics dashboard
* Profile management
* Activity center
* Responsive UI
* Loading, error and empty states
* Accessibility and UI consistency improvements

---

## User Roles

### Citizen

Citizens can:

* Submit complaints
* Track submitted complaints
* View complaint details
* View complaint history
* Provide resolution feedback
* Reopen eligible complaints
* Manage profile information
* View activity

### Officer

Officers can:

* View assigned complaints
* Acknowledge complaints
* Start complaint processing
* Resolve complaints
* Track complaint information

### Administrator

Administrators can:

* View all complaints
* Assign and reassign officers
* Monitor SLA status
* Close resolved complaints
* View analytics
* Manage operational workflows

---

## AI Capabilities

The current AI pipeline uses Google's Gemini API to assist with complaint analysis.

The system can derive:

* Complaint summary
* Predicted category
* Predicted department
* Priority
* Urgency
* Confidence

AI responses are validated by the backend before being used by the application.

External AI failures are handled so that complaint processing does not depend entirely on successful AI availability.

---

## Technology Stack

### Frontend

* React
* Vite
* React Router
* Axios
* CSS

### Backend

* Python
* Django
* Django REST Framework
* JWT authentication

### Database

* SQLite for development
* PostgreSQL planned for production

### AI

* Google Gemini
* `google-genai`

### Development

* Git
* GitHub
* REST APIs
* Environment variables

---

## Architecture

```text
Citizen / Officer / Admin
          ↓
    React Frontend
          ↓
    Django REST API
          ↓
 ┌────────┼───────────┐
 │        │           │
 ▼        ▼           ▼
Auth     AI       Workflow/SLA
 │        │           │
 └────────┼───────────┘
          ↓
       Database
```

See the detailed architecture documentation in:

* `docs/architecture.md`
* `docs/complaint-lifecycle.md`
* `docs/ai-pipeline.md`
* `docs/database-design.md`

---

## Complaint Lifecycle

```text
SUBMITTED
    ↓
AI_ANALYZING
    ↓
ASSIGNED
    ↓
ACKNOWLEDGED
    ↓
IN_PROGRESS
    ↓
RESOLVED
    ↓
CLOSED
```

Additional paths support information requests, escalation and reopening.

---

## SLA Management

CivicResolve supports priority-based SLA policies.

The system tracks:

* Response deadlines
* Resolution deadlines
* Completion timestamps
* Response breaches
* Resolution breaches
* Escalation

---

## V2 Roadmap

The next development phase will introduce:

1. Duplicate complaint detection
2. AI SLA-breach prediction
3. Knowledge base + AI resolution recommendations
4. Multimodal complaint submission
5. Smart officer workload balancing
6. Notifications

These features will be implemented and evaluated incrementally.

---

## Development

### Backend

```bash
cd backend
```

Activate the virtual environment and run the Django development server according to the project's local environment configuration.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The production frontend can be verified with:

```bash
npm run build
```

---

## Environment Variables

Secrets and API credentials must be stored in environment variables.

Do not commit:

```text
.env
.env.local
API keys
Passwords
JWT secrets
Production credentials
```

---

## Engineering Goals

CivicResolve is being developed with emphasis on:

* Backend-enforced authorization
* Explicit workflow transitions
* AI output validation
* Auditability
* SLA-driven operations
* Testability
* Security
* Performance
* Production deployment
* Measurable AI evaluation

---

## Future Evaluation

V2 AI components will be evaluated using labeled test data.

Planned metrics include:

* Accuracy
* Precision
* Recall
* F1-score
* ROC-AUC where appropriate

Actual evaluation results will be added after testing.

---

## License

This project is currently developed as a personal academic and portfolio project.
