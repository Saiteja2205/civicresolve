# CivicResolve — Project Overview

## 1. Problem Statement

Civic grievance handling can require manual complaint classification, routing, assignment, monitoring, and follow-up. A digital platform can centralize these operations and provide citizens and public-service staff with a common view of complaint progress.

## 2. Proposed Solution

CivicResolve is an AI-powered grievance intelligence and resolution platform. Citizens submit complaints through a web interface. The backend analyzes the complaint, preserves the original citizen text, generates structured AI information, routes the complaint, supports officer assignment, tracks service-level deadlines, and maintains an auditable status history.

## 3. Target Users

- Citizens
- Officers
- Administrators

## 4. Core Functional Areas

- Authentication and role-based authorization
- Complaint submission and tracking
- AI complaint analysis
- Multilingual complaint processing
- Voice-assisted complaint creation
- Category and department routing
- Officer assignment and reassignment
- Complaint status workflow
- Complaint history and audit trail
- SLA management and risk calculation
- Duplicate candidate detection
- Evidence upload and AI evidence analysis
- Resolution assistance
- Citizen resolution feedback
- Reopening and subsequent resolution cycles
- Notifications
- Analytics and activity views

## 5. AI Features

The current AI implementation uses Google Gemini through a provider abstraction.

### Text complaint analysis

The system produces structured analysis including language, English normalized content, summary, explanation, category, department, priority, urgency, and confidence.

### Multilingual processing

Original complaint text remains in `Complaint.title` and `Complaint.description`. AI-generated English content is stored separately in `ComplaintAnalysis.english_title` and `ComplaintAnalysis.english_description`, with the detected language stored in `ComplaintAnalysis.detected_language`.

### Voice processing

The frontend captures a browser speech transcript and sends it to the backend voice translation service. Gemini detects the transcript language and returns an English title and description suitable for editing before complaint submission.

### Image evidence analysis

Complaint evidence images can be analyzed using Gemini multimodal generation. Structured metadata is stored separately from the original image.

### Semantic duplicate detection

Complaint text is embedded into 768-dimensional vectors. pgvector cosine distance is used to identify semantically similar complaint candidates. Duplicate detection is advisory and requires administrative review.

### Resolution assistant

Administrators and currently assigned officers can request an AI-generated resolution draft and citizen-response draft based on complaint context, history, evidence, and SLA information.

## 6. Technology Stack

- Frontend: React, Vite, React Router, Axios, Leaflet, CSS
- Backend: Python, Django, Django REST Framework
- Authentication: Simple JWT
- Database: SQLite for local fallback; PostgreSQL supported through `DATABASE_URL`
- Vector search: pgvector
- AI: Google GenAI SDK and Gemini
- Production server: Gunicorn
- Static-file middleware: WhiteNoise

## 7. Project Scope

The current implementation is intended as an academic and portfolio project. The application contains working citizen, officer, and administrator workflows and has been manually and automatically tested. Production deployment still requires environment-specific infrastructure configuration.
