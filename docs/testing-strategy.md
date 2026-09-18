# CivicResolve — Testing Strategy

## 1. Testing Goals

Testing focuses on:

- Backend correctness
- Permission enforcement
- Complaint state transitions
- AI validation and failure handling
- Data preservation
- Assignment behavior
- SLA behavior
- Evidence validation
- Duplicate detection behavior
- Resolution feedback cycles
- Multilingual processing
- Voice input integration
- Frontend build integrity
- End-to-end role workflows

## 2. Automated Backend Tests

The Django project contains tests across the complaints, accounts, organizations, and notifications domains, including dedicated post-feature regression suites.

The latest verified complaint test run was:

```text
Found 206 test(s).
Ran 206 tests
OK
```

This confirms 206 tests passed with zero failures in the verified run.

Run:

```bash
cd backend
python manage.py check
python manage.py test complaints
```

## 3. System Check

Run:

```bash
python manage.py check
```

The verified run returned no Django system-check issues.

## 4. Frontend Build

The production bundle is verified using:

```bash
cd frontend
npm run build
```

A successful Vite build confirms that the application compiles into a production bundle.

## 5. Manual End-to-End Tests

### Citizen

Verify:

1. Login
2. Dashboard loading
3. Live complaint statistics
4. Complaint creation
5. Complaint list
6. Complaint details
7. Complaint history
8. Evidence upload
9. Notifications
10. Resolution feedback
11. Feedback editing
12. Reopening
13. Second resolution cycle
14. Second feedback submission
15. Profile and activity

### Officer

Verify:

1. Login
2. Assigned complaint list
3. Complaint detail
4. Acknowledge
5. Start work
6. Resolution
7. Evidence visibility
8. Resolution assistant for assigned complaints
9. Notifications

### Administrator

Verify:

1. Login
2. All complaint visibility
3. Assignment and reassignment
4. SLA dashboard
5. SLA risk
6. Duplicate review
7. Analytics
8. Complaint closure
9. Resolution assistant
10. AI evaluation endpoint

## 6. Multilingual Testing

Test typed complaints in:

- English
- Telugu
- Hindi

For non-English complaints verify:

- Original title is unchanged
- Original description is unchanged
- `detected_language` is populated
- `english_title` is populated
- `english_description` is populated
- AI classification continues to work

## 7. Voice Testing

Verify:

1. Browser supports Speech Recognition
2. Microphone permission is granted
3. Voice transcript is captured
4. `/api/voice-translation/` returns HTTP 200
5. Detected language appears in the form
6. English title is populated
7. English description is populated
8. Generated content remains editable
9. Complaint submission works after voice processing

The browser speech recognition layer and AI translation layer should be tested separately when diagnosing language issues.

## 8. Feedback and Reopen Regression

Test the complete sequence:

```text
RESOLVED
  |
  v
Feedback cycle 1
  |
  v
Edit feedback cycle 1
  |
  v
REOPENED
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
  v
RESOLVED
  |
  v
Feedback cycle 2
```

Verify that feedback from cycle 1 is not overwritten by cycle 2.

## 9. Authorization Testing

Test that:

- Citizens cannot manage other citizens' complaints
- Citizens cannot perform officer/admin workflow actions
- Officers cannot operate on unrelated complaints
- Officers cannot perform administrator-only assignment management
- Only administrators can review duplicate candidates
- Only citizens can upload evidence to their own complaints
- Only administrators can run the AI benchmark endpoint

## 10. Regression Procedure

After a code change:

```bash
cd backend
python manage.py check
python manage.py test complaints
```

Then:

```bash
cd ../frontend
npm run build
```

Finally verify Git status:

```bash
cd ..
git status
```

A clean working tree is expected after committing intended changes.
