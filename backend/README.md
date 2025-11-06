# Pulseofpeople.com - Django Backend API

Django REST Framework backend for the Pulseofpeople.com voter sentiment analysis platform.

## Overview

This is the backend API server for Pulseofpeople.com, handling:
- User authentication (JWT-based)
- Multi-tenant data management
- Real-time notifications
- Voter database management
- Campaign analytics
- Sentiment analysis
- Integration with Supabase PostgreSQL

## Tech Stack

- **Framework**: Django 5.2
- **API**: Django REST Framework 3.16
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL (Supabase)
- **Storage**: Supabase Storage
- **Real-time**: Supabase Realtime
- **Server**: Gunicorn

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL (via Supabase)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/pulseofpeople-backend.git
   cd pulseofpeople-backend/backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at: http://localhost:8000

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

```bash
# Database
DB_HOST=db.xxxxx.supabase.co
DB_NAME=postgres
DB_USER=postgres.xxxxx
DB_PASSWORD=your-password

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://pulseofpeople.com
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/login/` - Login with credentials
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout user

### User Endpoints

- `GET /api/users/` - List users
- `GET /api/users/{id}/` - Get user details
- `PATCH /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user
- `GET /api/profile/me/` - Get current user profile
- `PATCH /api/profile/me/` - Update current user profile

### Notification Endpoints

- `GET /api/notifications/` - List notifications
- `POST /api/notifications/` - Create notification
- `PATCH /api/notifications/{id}/mark-read/` - Mark as read
- `POST /api/notifications/mark-all-read/` - Mark all as read
- `DELETE /api/notifications/{id}/` - Delete notification

### Health Check

- `GET /api/health/` - API health status

### Admin Panel

Access Django admin at: http://localhost:8000/admin

## Project Structure

```
backend/
├── api/                    # Main API app
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # API routes
│   ├── permissions.py     # Custom permissions
│   └── utils.py           # Utility functions
├── config/                # Django configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI config
│   └── asgi.py            # ASGI config
├── supabase/              # Supabase integration
│   └── client.py          # Supabase client setup
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── runtime.txt           # Python version
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Code Style

We follow PEP 8 style guidelines. Format code with:

```bash
black .
flake8 .
```

## Deployment

See the main [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

### Quick Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Quick Deploy to Render

1. Connect GitHub repository to Render
2. Configure environment variables
3. Deploy automatically on push to main

## Database

### Schema

The application uses Supabase PostgreSQL with the following main tables:

- `user_profiles` - Extended user information
- `tenants` - Multi-tenant organizations
- `constituencies` - Electoral constituencies
- `voters` - Voter database
- `campaigns` - Campaign management
- `surveys` - Survey definitions
- `survey_responses` - Survey responses
- `notifications` - User notifications
- `audit_logs` - Activity audit trail

### Migrations

All database migrations are in `api/migrations/`. Apply with:

```bash
python manage.py migrate
```

## Multi-Tenancy

The application supports multi-tenant architecture with:
- Organization-based tenant isolation
- Row-level security via Supabase RLS
- Subdomain-based routing (planned)
- Role-based access control (RBAC)

## Security

### Authentication

- JWT-based authentication
- Access token expiry: 1 hour
- Refresh token expiry: 7 days
- Password validation and hashing

### CORS

Configure allowed origins in environment variables:

```bash
CORS_ALLOWED_ORIGINS=https://pulseofpeople.com,http://localhost:5173
```

### Rate Limiting

Consider implementing rate limiting for production:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## Monitoring

### Logs

View logs in production:

```bash
# Railway
railway logs

# Render
# View in dashboard

# Heroku
heroku logs --tail
```

### Health Checks

Monitor API health at: `/api/health/`

## Troubleshooting

### Database Connection Issues

1. Verify Supabase credentials
2. Check `DB_SSLMODE=require`
3. Ensure IP is whitelisted in Supabase

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Migration Issues

```bash
# Reset migrations (development only)
python manage.py migrate --fake api zero
python manage.py migrate api
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is proprietary and confidential.

## Support

For issues and questions:
- Create an issue in GitHub
- Contact: support@pulseofpeople.com

## Related Repositories

- **Frontend**: [pulseofpeople-frontend](https://github.com/your-username/pulseofpeople-frontend)
- **Documentation**: [pulseofpeople-docs](https://github.com/your-username/pulseofpeople-docs)

---

**Version**: 1.7.0
**Last Updated**: 2025-11-06
**Python**: 3.13
**Django**: 5.2
