# CivicResolve — Deployment Guide

## 1. Deployment Architecture

A production deployment can be organized as:

```text
Browser
   |
   v
React production build
   |
   v
HTTPS reverse proxy / hosting
   |
   v
Django + Gunicorn
   |
   +--> PostgreSQL + pgvector
   +--> Persistent media storage
   +--> Google Gemini API
```

The exact hosting provider is not fixed by the repository, so infrastructure-specific commands should be adapted to the selected platform.

## 2. Production Environment

Set:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<strong-random-secret>
DJANGO_ALLOWED_HOSTS=<production-hosts>
CORS_ALLOWED_ORIGINS=https://<frontend-domain>
CSRF_TRUSTED_ORIGINS=https://<frontend-domain>
DATABASE_URL=<postgresql-database-url>
GEMINI_API_KEY=<gemini-api-key>
```

Enable secure browser settings as appropriate:

```text
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_USE_PROXY_SSL_HEADER=True
```

HSTS settings should be enabled only when the production HTTPS setup is confirmed.

## 3. Database

The settings file supports `DATABASE_URL`. When it is supplied, Django uses `dj-database-url` to parse the connection configuration.

For the complete vector workflow, PostgreSQL must have the pgvector extension available.

The current `requirements.txt` uses `pgvector.django` in the Django settings and models but does not list the Python `pgvector` package. Before production deployment, make sure that package is explicitly included in the deployment dependency set.

## 4. Backend Build Steps

```bash
cd backend
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

Install any additional production dependency required by the pgvector integration if it is not yet present in the dependency file.

Run:

```bash
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
```

Start Gunicorn using the Django WSGI module:

```bash
gunicorn config.wsgi:application
```

The application is designed so that the WSGI module is `config.wsgi:application`.

## 5. Frontend Build

Set the production API URL:

```text
VITE_API_BASE_URL=https://<backend-domain>/api
```

Install and build:

```bash
cd frontend
npm install
npm run build
```

Deploy the generated Vite `dist/` directory using the selected static hosting platform or web server.

## 6. Static Files

Django uses WhiteNoise and `CompressedManifestStaticFilesStorage` for static files.

Run:

```bash
python manage.py collectstatic --noinput
```

## 7. Media Files

Complaint evidence is stored under Django's media storage configuration.

The local implementation uses filesystem storage. In production, use persistent storage suitable for the hosting platform so uploaded evidence is not lost when an application instance is replaced.

## 8. CORS and CSRF

The production frontend origin must be explicitly included in:

```text
CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS
```

Do not use broad wildcard configuration for authenticated production deployments unless the security design explicitly requires it.

## 9. HTTPS and Proxy Settings

The settings include production controls for:

- SSL redirect
- Secure session cookies
- Secure CSRF cookies
- HSTS
- Proxy SSL headers
- Content-type sniffing protection
- Frame protection
- Referrer policy
- Cross-origin policies

Configure these according to the hosting provider and reverse-proxy topology.

## 10. Production Verification

After deployment:

```bash
python manage.py check --deploy
```

Then verify:

1. Login
2. Token refresh
3. Citizen dashboard
4. Complaint creation
5. AI analysis
6. Multilingual processing
7. Voice processing where browser support is available
8. Assignment
9. Officer workflow
10. Resolution
11. Feedback
12. Reopen
13. Notifications
14. Evidence upload
15. Duplicate detection
16. SLA views
17. Admin analytics

Also run the frontend production build before release.
