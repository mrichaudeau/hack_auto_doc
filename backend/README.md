# AI-Powered Technology Watch Platform - Backend API

Backend API for the AI-powered Technology Watch Platform, built with Django and Django REST Framework.

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Poetry (Python package manager)
- SQLite (development) or PostgreSQL (production)

### Installation

1. **Clone the repository and navigate to backend**
   ```bash
   cd backend
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and configure your settings (see Environment Variables section below).

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Run migrations**
   ```bash
   poetry run python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   poetry run python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   poetry run python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/`

## 📚 API Documentation

### Authentication Endpoints

#### 1. Register New User

**Endpoint:** `POST /api/auth/register/`

**Description:** Creates a new user account with email/password. Sends a verification email.

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**Success Response (201 Created):**
```json
{
  "message": "Inscription réussie ! Un email de vérification a été envoyé à votre adresse.",
  "email": "user@example.com"
}
```

**Error Responses:**
- `400 Bad Request`: Validation errors (weak password, passwords don't match, invalid email)
- `409 Conflict`: Email already exists

#### 2. Verify Email

**Endpoint:** `GET/POST /api/auth/verify-email/<key>/`

**Description:** Verifies the user's email address using the token sent via email.

**Success Response (200 OK):**
```json
{
  "message": "Votre adresse email a été vérifiée avec succès ! Vous pouvez maintenant vous connecter.",
  "email": "user@example.com",
  "verified": true
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Token de vérification invalide ou expiré.",
  "code": "invalid_token"
}
```

#### 3. Resend Verification Email

**Endpoint:** `POST /api/auth/resend-verification/`

**Description:** Resends the verification email to an unverified account.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Un nouvel email de vérification a été envoyé.",
  "email": "user@example.com"
}
```

## 🔐 Security Features

### Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- Cannot be too similar to user information
- Cannot be a commonly used password

### Password Hashing

- **Algorithm:** Argon2 (most secure)
- **Fallback:** PBKDF2 (Django default)

### Email Verification

- Email verification is **mandatory** for all standard accounts
- Verification tokens expire after **3 days**
- Accounts remain inactive (`is_active=False`) until email verification

### CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to allow requests from:
- `http://localhost:3000` (React frontend in development)
- `http://127.0.0.1:3000`

## 🛠️ Environment Variables

### Required Variables

#### Django Core

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | `django-insecure-xxx` | Yes |
| `DEBUG` | Enable debug mode (only for development) | `True` | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` | Yes |

#### Email Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.console.EmailBackend` | Yes |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` | Production |
| `EMAIL_PORT` | SMTP server port | `587` | Production |
| `EMAIL_USE_TLS` | Use TLS encryption | `True` | Production |
| `EMAIL_HOST_USER` | SMTP username | `your-email@example.com` | Production |
| `EMAIL_HOST_PASSWORD` | SMTP password | `your-password` | Production |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@techwatch.com` | Yes |

#### CORS Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000` | Yes |

### Development vs Production

**Development:**
- Use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` to print emails to console
- Use SQLite database (default)
- Set `DEBUG=True`

**Production:**
- Configure SMTP settings for real email delivery
- Use PostgreSQL database
- Set `DEBUG=False`
- Use a strong, randomly generated `SECRET_KEY`
- Configure proper `ALLOWED_HOSTS`

## 🏗️ Project Structure

```
backend/
├── accounts/               # User authentication app
│   ├── managers.py         # CustomUserManager
│   ├── models.py           # CustomUser model
│   ├── serializers.py      # DRF serializers
│   ├── validators.py       # Password validators
│   ├── views.py            # API views
│   ├── urls.py             # URL routing
│   └── tests.py            # Tests
├── config/                 # Django project settings
│   ├── settings.py         # Main settings
│   ├── urls.py             # Root URL configuration
│   ├── wsgi.py             # WSGI config
│   └── asgi.py             # ASGI config
├── templates/              # Email templates
│   └── account/
│       └── email/
│           ├── email_confirmation_subject.txt
│           ├── email_confirmation_message.txt
│           └── email_confirmation_message.html
├── manage.py               # Django management script
├── pyproject.toml          # Poetry dependencies
└── README.md               # This file
```

## 🧪 Testing

### Run All Tests

```bash
poetry run python manage.py test
```

### Run Specific Test Module

```bash
poetry run python manage.py test accounts.tests.test_models
```

### Check Code Coverage

```bash
poetry run coverage run --source='.' manage.py test
poetry run coverage report
```

## 📦 Dependencies

### Core Dependencies

- **Django 5.2.7**: Web framework
- **djangorestframework 3.16.1**: REST API framework
- **django-allauth 65.12.1**: Authentication system
- **argon2-cffi 25.1.0**: Secure password hashing
- **django-cors-headers 4.9.0**: CORS handling
- **psycopg2-binary 2.9.11**: PostgreSQL adapter
- **python-decouple 3.8**: Environment variable management

See `pyproject.toml` for complete dependency list.

## 🚧 Roadmap

### Completed (Bloc 1 - US-1)

- ✅ Custom User model with email authentication
- ✅ User registration API
- ✅ Email verification system
- ✅ Password complexity validation (Argon2)
- ✅ CORS configuration

### In Progress (Bloc 1)

- ⏳ JWT authentication (US-2)
- ⏳ Login/logout endpoints (US-2)
- ⏳ Password reset functionality (US-4)
- ⏳ Profile management (US-5)

### Upcoming

- 📅 Microsoft Entra ID (SSO) integration (US-3)
- 📅 Subject & subscription management (Bloc 2)
- 📅 AI content pipeline with Langgraph (Bloc 3)
- 📅 Report consultation system (Bloc 4)
- 📅 Recommendation engine with pgvector (Bloc 5)
- 📅 FinOps cost tracking (Bloc 6)

## 🤝 Contributing

This project follows the specifications in `docs/action_plan/bloc_1/`.

### Development Workflow

1. Create a feature branch: `feature/task-x.y-description`
2. Implement the task according to specifications
3. Write tests (unit, integration, E2E)
4. Commit with descriptive message
5. Create a pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all public methods
- Keep functions small and focused

## 📄 License

[To be defined]

## 👥 Authors

AI-Powered Technology Watch Platform Team

---

**Status:** 🚧 Active Development

**Last Updated:** 2025-10-25
