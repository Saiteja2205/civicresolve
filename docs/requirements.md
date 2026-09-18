# CivicResolve — Requirements

## Functional Requirements

### Authentication

- Users must authenticate before accessing protected application features.
- Authentication uses email and password.
- JWT access and refresh tokens are used by the API.

### Role Management

The system supports:

- Citizen (`USER`)
- Officer (`OFFICER`)
- Administrator (`ADMIN`)

Backend permission checks enforce role-specific operations.

### Complaint Management

Citizens must be able to:

- Create complaints
- Track complaints
- View complaint history
- Provide resolution feedback
- Reopen eligible resolved complaints
- Upload complaint evidence

### AI Complaint Intelligence

The system should support:

- Complaint summarization
- Category prediction
- Department prediction
- Priority prediction
- Urgency scoring
- Confidence scoring
- Language detection
- English translation/normalization

### Workflow

The system must enforce valid complaint status transitions and maintain a history of changes.

### Assignment

Administrators must be able to assign and reassign complaints to officers associated with the selected department.

### SLA

The system must maintain priority-based response and resolution targets and expose SLA status and risk information.

### Duplicate Detection

The system should generate semantic duplicate candidates without automatically changing the complaint state.

### Evidence

Citizens should be able to upload validated evidence images to their own complaints. Evidence can be analyzed using AI.

### Feedback

Citizens should be able to rate a resolved complaint from 1 to 5 and provide an optional comment. Feedback is tracked by resolution cycle.

### Notifications

The system should provide in-app notifications for relevant complaint and operational events.

## Technical Requirements

- React/Vite frontend
- Django REST Framework backend
- JWT authentication
- Environment-based configuration
- REST API communication
- SQLite local database fallback
- PostgreSQL support
- pgvector support for semantic embeddings
- Google Gemini integration
- Production static-file handling through WhiteNoise
- Gunicorn-compatible deployment
- Backend automated testing
- Production frontend build support
