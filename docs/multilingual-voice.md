# CivicResolve — Multilingual and Voice Processing

## 1. Objective

The multilingual feature allows CivicResolve to accept complaint content written or transcribed in languages other than English while preserving the original citizen wording.

## 2. Typed Complaint Processing

For a typed complaint, AI analysis detects the primary language and produces an English representation.

```text
Citizen enters complaint
        |
        v
Complaint.title / Complaint.description
        |
        v
AI complaint analysis
        |
        +------------------------------+
        |                              |
        v                              v
Detected language             English representation
                                      |
                              +-------+-------+
                              |               |
                              v               v
                       english_title  english_description
```

The original complaint remains unchanged.

## 3. Stored Representation

The database separates original and normalized content:

```text
Complaint
├── title = original citizen title
└── description = original citizen description

ComplaintAnalysis
├── detected_language
├── english_title
└── english_description
```

This provides an auditable separation between citizen-submitted content and AI-generated English processing content.

## 4. Voice Workflow

The frontend uses the browser Speech Recognition API when available.

```text
Start voice
    |
    v
Browser Speech Recognition
    |
    v
Transcript
    |
    v
POST /api/voice-translation/
    |
    v
Gemini multilingual processing
    |
    +---------------------+
    |                     |
    v                     v
Language              English title
                         + description
    |                     |
    +----------+----------+
               |
               v
        Editable complaint form
               |
               v
          Normal submission
```

## 5. Backend Voice Endpoint

Endpoint:

```text
POST /api/voice-translation/
```

Request:

```json
{
  "text": "voice transcript"
}
```

Response:

```json
{
  "detected_language": "English",
  "english_title": "Water Supply Problem",
  "english_description": "There is a problem with the water supply."
}
```

## 6. Validation

The voice translation service validates:

- Input is a string
- Input is not empty
- Input has at least five characters
- Input does not exceed 10,000 characters
- Detected language is non-empty text
- English title is non-empty and at most 200 characters
- English description is non-empty and at most 5,000 characters

## 7. Browser Speech Recognition Limitation

The current frontend explicitly requests:

```text
en-IN
```

for browser speech recognition.

Therefore, the architecture contains two distinct language layers:

1. Browser speech-to-text language recognition
2. Backend Gemini multilingual interpretation/translation

The backend can process multilingual transcript text, but native speech recognition for a particular language depends on browser support and the configured recognition language.

## 8. User Experience

The complaint creation interface:

- Provides a Start Voice control
- Shows a listening state
- Shows interim transcript text when available
- Shows an AI conversion state
- Displays the detected language
- Populates English title and description
- Keeps the generated content editable
- Allows the user to submit the complaint through the normal workflow
