# CivicResolve

## GenAI-Powered Intelligent Grievance & Tracking System

CivicResolve is a full-stack grievance management platform for submitting, analyzing, routing, assigning, monitoring, resolving, and tracking citizen complaints.

The system combines a React/Vite frontend with a Django REST Framework backend. Google Gemini is used for complaint analysis, multilingual processing, image evidence analysis, semantic embeddings, duplicate detection support, and officer-facing resolution assistance.

## Project Status

The current implementation is a functional academic and portfolio project with completed end-to-end workflows for citizens, officers, and administrators.

Verified project capabilities include:

- JWT-based authentication
- Role-based authorization for citizens, officers, and administrators
- Citizen complaint submission and tracking
- AI complaint analysis
- Language detection and English normalization/translation
- Multilingual voice complaint input
- Category and department prediction
- Priority and urgency scoring
- AI confidence scoring
- Automatic routing and officer assignment workflows
- Complaint status history and audit trail
- SLA policy and complaint SLA tracking
- SLA risk calculation
- Escalation workflow
- Semantic complaint embeddings
- Duplicate complaint candidate detection and administrative review
- Complaint evidence image upload
- Gemini-based evidence analysis
- AI resolution assistant for administrators and assigned officers
- Citizen resolution feedback
- Resolution-cycle-aware feedback and reopening workflow
- Notifications and read/unread management
- Activity center
- Analytics and administrative dashboards
- Complaint location coordinates and map-related UI
- Responsive frontend UI
- Backend validation and permission enforcement

## User Roles

### Citizen

Citizens can:

- Sign in using email and password
- Submit complaints
- Submit typed or voice-assisted complaints
- Provide complaint category and optional location information
- View their own complaints
- View complaint details and history
- Upload evidence to their own complaints
- View relevant AI analysis
- Provide resolution feedback after resolution
- Edit feedback for the current resolution cycle while the complaint is resolved
- Reopen a resolved complaint
- View notifications
- View activity
- Manage their profile

### Officer

Officers can:

- View complaints currently assigned to them
- View complaint details and history
- Acknowledge assigned complaints
- Start complaint processing
- Mark complaints as resolved
- View relevant evidence
- Use the AI resolution assistant for complaints currently assigned to them
- View notifications and activity

### Administrator

Administrators can:

- View all complaints
- Assign and reassign complaints
- Manage operational workflows
- Close resolved complaints
- Monitor SLA records and SLA risk
- Review duplicate complaint candidates
- Use the AI resolution assistant
- Run the AI evaluation benchmark endpoint
- View analytics
- Access administrative dashboards
- Manage users and organizational information through the application/API where permitted

## Complaint Lifecycle

The backend enforces explicit status transitions.

```text
SUBMITTED
    |
    v
AI_ANALYZING
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
    +----------------------+
    |                      |
    v                      v
NEEDS_INFORMATION      ESCALATED
    |                      |
    +----------+-----------+
               |
               v
          IN_PROGRESS
               |
               v
           RESOLVED
            /     \
           v       v
       CLOSED    REOPENED
                    |
                    v
                 ASSIGNED
```

`SUBMITTED` can also be rejected. Terminal `CLOSED` and `REJECTED` complaints have no further status transitions in the current workflow.

## AI Capabilities

The AI layer is implemented around a provider abstraction with Google Gemini as the current provider.

### Complaint analysis

For each complaint, the AI analysis can produce:

- Detected language
- English title
- English description
- Complaint summary
- Explanation
- Predicted category
- Predicted department
- Predicted priority
- Urgency score
- Confidence score

The original citizen title and description are stored on `Complaint` and are not overwritten by the multilingual processing fields. English normalized/translated content is stored separately on `ComplaintAnalysis`.

### Voice complaint processing

The frontend uses the browser Speech Recognition API when available. The resulting transcript is sent to the backend voice translation endpoint, where Gemini detects the language and generates an English complaint title and description.

The current browser implementation requests `en-IN` speech recognition. Therefore, the multilingual AI translation layer is multilingual, while the browser speech-to-text layer remains dependent on the browser's supported recognition behavior and configured recognition language.

### Evidence analysis

Uploaded complaint evidence is validated as an image and can be analyzed with Gemini Vision. The system stores structured metadata such as evidence type, observations, severity, confidence, and complaint consistency while retaining the original evidence file.

### Semantic duplicate detection

Complaint text can be converted into 768-dimensional Gemini embeddings and stored using pgvector. Duplicate candidates are generated from semantic similarity and are advisory; the duplicate detector does not automatically reject or delete complaints. Administrators can review candidate records.

### Resolution assistant

The AI resolution assistant uses complaint details, history, evidence analysis, and SLA information to produce a proposed resolution draft, recommended actions, citizen response draft, confidence score, and information basis. It is an assistive feature and does not make the final resolution decision.

## Technology Stack

### Frontend

- React 19
- Vite 8
- React Router 7
- Axios
- Leaflet
- CSS

### Backend

- Python
- Django 6.1
- Django REST Framework 3.18
- Django REST Framework Simple JWT
- django-cors-headers
- WhiteNoise
- Gunicorn
- python-dotenv

### Database

- SQLite for local development when `DATABASE_URL` is not configured
- PostgreSQL supported through `DATABASE_URL`
- pgvector used by the complaint embedding model

### AI

- Google GenAI SDK
- Google Gemini text and multimodal generation
- Gemini embeddings

### Development

- Git
- GitHub
- REST APIs
- Environment variables

## Architecture

```text
+-----------------------------+
| Citizen / Officer / Admin   |
+--------------+--------------+
               |
               v
+-----------------------------+
| React + Vite Frontend        |
| Pages / Components / Context |
+--------------+--------------+
               |
               | REST + JWT
               v
+-----------------------------+
| Django REST Framework API    |
+--------------+--------------+
               |
       +-------+-------+----------------+
       |               |                |
       v               v                v
 Authentication     Complaint       Notifications
 Authorization      Workflow
       |               |
       |       +-------+-------+----------------+
       |       |       |       |                |
       |       v       v       v                v
       |      AI      SLA   Assignment       Evidence
       |       |       |       |                |
       |       +-------+-------+----------------+
       |               |
       +---------------+----------------+
                       |
                       v
                 Database / Storage
                       |
                       +--> pgvector embeddings
                       +--> complaint evidence

AI provider:
Django services --> Google Gemini
```

## Repository Structure

```text
civicresolve/
├── backend/
│   ├── accounts/
│   ├── complaints/
│   ├── notifications/
│   ├── organizations/
│   ├── config/
│   ├── media/
│   ├── staticfiles/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── docs/
└── README.md
```

## Local Setup

### Prerequisites

Install:

- Python 3.13 or a compatible Python version supported by the project environment
- Node.js and npm
- A Google Gemini API key for AI features
- PostgreSQL with pgvector for a production deployment that uses semantic embeddings

### Backend

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the project-root `.env` file using `.env.example` as the template.

Run migrations:

```bash
python manage.py migrate
```

Check the project:

```bash
python manage.py check
```

Start Django:

```bash
python manage.py runserver
```

### Frontend

From the project root:

```bash
cd frontend
npm install
npm run dev
```

The frontend API base URL is configured through `VITE_API_BASE_URL`.

Example local frontend environment:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Environment Variables

The backend reads environment variables from the project-root `.env` file.

Use `.env.example` as the starting point.

```text
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=False
DJANGO_CSRF_COOKIE_SECURE=False
DJANGO_SECURE_HSTS_SECONDS=0
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=False
DJANGO_SECURE_HSTS_PRELOAD=False
DJANGO_USE_PROXY_SSL_HEADER=False
DATABASE_URL=
GEMINI_API_KEY=
```

For the frontend:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Never commit real API keys, Django secrets, passwords, or production credentials.

## Authentication

The API uses JWT authentication through Django REST Framework Simple JWT.

The configured token lifetimes are:

- Access token: 30 minutes
- Refresh token: 7 days
- Refresh token rotation: enabled

The frontend stores access and refresh tokens in browser local storage and uses the authenticated user context to protect routes and select role-specific dashboards.

## API Overview

The API is mounted under `/api/`.

Major endpoint groups include:

```text
/api/auth/me/
/api/auth/profile/
/api/auth/token/
/api/auth/token/refresh/

/api/complaints/
/api/complaints/{id}/
/api/complaints/{id}/assign/
/api/complaints/{id}/acknowledge/
/api/complaints/{id}/start/
/api/complaints/{id}/resolve/
/api/complaints/{id}/close/
/api/complaints/{id}/history/
/api/complaints/{id}/duplicates/
/api/complaints/{id}/reopen/
/api/complaints/{id}/resolution-feedback/
/api/complaints/resolution-feedback/{id}/
/api/complaints/{id}/sla-risk/
/api/complaints/{id}/resolution-assistant/

/api/assignments/
/api/sla/
/api/complaint-duplicates/
/api/complaint-evidence/
/api/voice-translation/
/api/ai-evaluation/
/api/activity/

/api/organizations/categories/
/api/organizations/departments/
/api/organizations/officers/

/api/notifications/
/api/notifications/{id}/read/
/api/notifications/read-all/
```

See `docs/api-documentation.md` for the detailed endpoint reference.

## Testing

The current verification cycle included:

- Django system check
- Complaint application automated tests
- Frontend production build
- Citizen, officer, and administrator workflow testing
- Complaint lifecycle testing
- Feedback and reopening testing
- Multilingual typed complaint testing
- Multilingual voice testing
- Permission testing
- Evidence, duplicate, notification, and SLA testing

The latest complaint test run completed with:

```text
206 tests
206 passed
0 failed
```

Run the backend tests with:

```bash
cd backend
python manage.py check
python manage.py test complaints
```

Build the frontend with:

```bash
cd frontend
npm run build
```

## Production Considerations

Before deployment:

1. Set `DJANGO_DEBUG=False`.
2. Configure a strong `DJANGO_SECRET_KEY`.
3. Configure production `DJANGO_ALLOWED_HOSTS`.
4. Configure production `CORS_ALLOWED_ORIGINS`.
5. Configure production `CSRF_TRUSTED_ORIGINS`.
6. Enable HTTPS-related settings appropriate for the hosting platform.
7. Configure `DATABASE_URL` for PostgreSQL.
8. Ensure PostgreSQL has the pgvector extension available.
9. Ensure the Python pgvector dependency is included in the deployment environment because the current Django models import `pgvector.django`.
10. Configure `GEMINI_API_KEY` securely.
11. Run migrations.
12. Run `python manage.py collectstatic` for the production static-file pipeline.
13. Configure persistent media storage if complaint evidence must survive application filesystem replacement.
14. Run the final backend and frontend verification after deployment.

## Documentation

Detailed project documentation is available under `docs/`:

- `project-overview.md` — problem, solution, scope, and users
- `architecture.md` — system and application architecture
- `database-design.md` — models and relationships
- `api-documentation.md` — REST API reference
- `ai-pipeline.md` — AI architecture and processing
- `complaint-lifecycle.md` — complaint state machine and workflows
- `testing-strategy.md` — automated and manual testing
- `requirements.md` — functional and technical requirements
- `deployment.md` — production deployment guide
- `multilingual-voice.md` — multilingual and voice processing details
- `project-structure.md` — repository organization

## Future Scope

Potential future work can include:

- Improved browser speech-language selection for native multilingual speech recognition
- Dedicated production media/object storage
- More extensive labeled datasets for AI evaluation
- Additional forecasting or predictive operational analytics
- Expanded multilingual user-interface support
- More advanced workload optimization
- Production observability and centralized logging

## License

CivicResolve is currently developed as a personal academic and portfolio project.
