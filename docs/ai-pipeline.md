# CivicResolve — AI Pipeline

## 1. Overview

CivicResolve isolates AI operations in backend services and uses a Gemini provider abstraction. The application requests structured JSON from the model and validates the result before persisting AI-derived fields.

```text
Complaint
   |
   v
AI orchestration
   |
   v
Prompt construction
   |
   v
Gemini provider
   |
   v
JSON response
   |
   v
Output validation
   |
   v
Category fallback / persistence
   |
   v
ComplaintAnalysis + complaint priority
```

## 2. Provider

The current provider is `GeminiProvider` in `complaints/services/ai_provider.py`.

The configured primary model is `gemini-3.8-flash`, with fallback model names configured in the provider for provider/service failures.

The provider uses:

- Request timeout protection
- Retry handling
- Model fallback handling
- Structured JSON response configuration
- Separate text and image generation paths

## 3. Complaint Analysis

`ai_orchestration_service.run_ai_analysis()` moves a complaint into `AI_ANALYZING`, calls the analysis service, and keeps the complaint in the analysis workflow so routing and assignment can continue.

If the AI provider fails, the orchestration layer returns the complaint to `SUBMITTED` and records the failure transition through complaint history.

## 4. Prompt Inputs

The complaint analysis prompt includes:

- Complaint title
- Complaint description
- Location
- Citizen-selected category when present
- Active departments
- Active categories

The model is instructed to produce structured fields for language, English normalization, summary, explanation, category, department, priority, urgency, and confidence.

## 5. Multilingual Analysis

The multilingual complaint analysis flow is designed around preservation of the original citizen text.

```text
Original complaint
       |
       +------------------------------+
       |                              |
       v                              v
Complaint.title              Complaint.description
       |                              |
       +--------------+---------------+
                      |
                      v
                 Gemini analysis
                      |
          +-----------+-----------+
          |                       |
          v                       v
 detected_language         English representation
                                  |
                         +--------+--------+
                         |                 |
                         v                 v
                  english_title   english_description
```

The English representation is stored on `ComplaintAnalysis` rather than replacing the citizen's original content.

## 6. Validation

The backend validates:

- Required analysis fields
- Summary and explanation type and length
- Priority against the supported priority choices
- Category and department IDs
- Category/department consistency
- Urgency range
- Confidence range
- Detected-language type and length
- English title and description type and length

If a predicted category is missing, the backend can use the complaint's selected category as a fallback when it is valid and active.

## 7. Voice Processing

Voice complaint processing has a separate service because the input is a speech transcript rather than a saved complaint.

```text
Browser Speech Recognition
          |
          v
Transcript
          |
          v
POST /api/voice-translation/
          |
          v
Voice translation service
          |
          v
Gemini
          |
          v
Language + English title + English description
          |
          v
Editable complaint form
```

The current browser configuration requests `en-IN`. The backend translation service can interpret multilingual or transliterated transcript text, but actual speech-to-text language support remains dependent on the browser recognition implementation.

## 8. Evidence AI

Evidence images are validated before analysis. The evidence AI service sends complaint context and image bytes to Gemini's multimodal generation path.

Structured output includes:

- Evidence type
- Observations
- Severity score
- Confidence score
- Complaint consistency
- Analysis explanation

The original evidence image remains stored independently of the AI result.

## 9. Embeddings and Duplicate Detection

Complaint text is converted to a 768-dimensional embedding using `gemini-embedding-001`.

The embedding is stored in `ComplaintEmbedding` and used with pgvector cosine distance.

The duplicate detector currently uses a default similarity threshold of `0.85`, a default maximum of five results, and a default lookback period of 180 days.

Duplicate detection is advisory. It does not automatically reject, delete, close, or otherwise change a complaint.

## 10. Resolution Assistant

The resolution assistant uses:

- Complaint information
- Category and department
- Existing AI analysis
- Complaint history
- Evidence analysis
- SLA information

The output contains:

- Resolution draft
- Recommended actions
- Citizen response draft
- Confidence score
- Basis

The prompt explicitly prevents the assistant from claiming that unverified actions have already been completed.

## 11. AI Evaluation

The `ai-evaluation/` endpoint runs the configured benchmark cases through the AI evaluation service. The endpoint is administrator-only.

The project also contains benchmark and evaluation service modules so AI behavior can be evaluated separately from normal complaint processing.
