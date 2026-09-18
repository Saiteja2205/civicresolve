# CivicResolve — Project Structure

```text
civicresolve/
├── backend/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── complaints/
│   │   ├── migrations/
│   │   ├── management/
│   │   ├── services/
│   │   │   ├── ai_analysis_service.py
│   │   │   ├── ai_evaluation_service.py
│   │   │   ├── ai_orchestration_service.py
│   │   │   ├── ai_output_validator.py
│   │   │   ├── ai_prompt.py
│   │   │   ├── ai_provider.py
│   │   │   ├── assignment_service.py
│   │   │   ├── complaint_creation_service.py
│   │   │   ├── complaint_embedding_service.py
│   │   │   ├── complaint_service.py
│   │   │   ├── duplicate_detection_service.py
│   │   │   ├── embedding_provider.py
│   │   │   ├── evidence_ai_service.py
│   │   │   ├── evidence_service.py
│   │   │   ├── officer_assignment_service.py
│   │   │   ├── resolution_assistant_service.py
│   │   │   ├── routing_service.py
│   │   │   ├── sla_monitoring_service.py
│   │   │   ├── sla_risk_service.py
│   │   │   ├── sla_service.py
│   │   │   └── voice_translation_service.py
│   │   ├── ai_evaluation_views.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── resolution_assistant_views.py
│   │   ├── resolution_feedback_views.py
│   │   ├── resolution_views.py
│   │   ├── sla_risk_views.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── voice_translation_views.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── notifications/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── organizations/
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── index.html
│
├── docs/
├── .env.example
└── README.md
```

## Backend Service Responsibilities

| Service | Responsibility |
|---|---|
| `ai_analysis_service.py` | Validate and persist complaint AI analysis |
| `ai_orchestration_service.py` | Manage complaint AI analysis workflow |
| `ai_prompt.py` | Build complaint analysis prompt |
| `ai_provider.py` | Gemini text/image provider boundary |
| `voice_translation_service.py` | Multilingual voice transcript conversion |
| `routing_service.py` | Category/department routing |
| `assignment_service.py` | Complaint assignment operations |
| `officer_assignment_service.py` | Officer selection/assignment logic |
| `complaint_service.py` | Complaint state transitions |
| `sla_service.py` | SLA creation/handling |
| `sla_monitoring_service.py` | SLA monitoring operations |
| `sla_risk_service.py` | SLA risk calculation |
| `complaint_embedding_service.py` | Complaint embedding generation/persistence |
| `embedding_provider.py` | Gemini embedding provider |
| `duplicate_detection_service.py` | Semantic duplicate candidate detection |
| `evidence_service.py` | Evidence validation/storage |
| `evidence_ai_service.py` | Gemini evidence analysis |
| `resolution_assistant_service.py` | AI resolution assistance |
| `ai_evaluation_service.py` | AI benchmark evaluation |
