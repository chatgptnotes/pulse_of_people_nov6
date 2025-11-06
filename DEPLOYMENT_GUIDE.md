# Django Backend Deployment Guide for Pulseofpeople.com

This guide covers deploying the Django backend separately from the React frontend.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Recommended Deployment Platforms](#recommended-deployment-platforms)
3. [Deployment Instructions](#deployment-instructions)
4. [Environment Configuration](#environment-configuration)
5. [Post-Deployment Steps](#post-deployment-steps)
6. [CI/CD Setup](#cicd-setup)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All code is committed to Git repository
- [ ] `requirements.txt` includes all dependencies (gunicorn, whitenoise, dj-database-url)
- [ ] Supabase PostgreSQL database is set up
- [ ] Environment variables are documented
- [ ] CORS settings include your frontend domain
- [ ] `DEBUG=False` for production
- [ ] Static files configuration is correct
- [ ] Database migrations are up to date

---

## Recommended Deployment Platforms

### 🥇 Option 1: Railway.app (RECOMMENDED)

**Best for**: Quick deployment, ease of use, automatic scaling

**Pricing**: Free tier with $5/month credit, then pay-as-you-go

**Features**:
- Automatic HTTPS
- GitHub integration
- Environment variable management
- Automatic deployments
- Built-in monitoring

**Pros**:
- Easiest to set up
- Great developer experience
- Excellent documentation
- Fast deployment times

**Cons**:
- Can be more expensive at scale

### 🥈 Option 2: Render.com

**Best for**: Simple deployment with free tier

**Pricing**: Free tier available, paid plans from $7/month

**Features**:
- Free SSL certificates
- Automatic deploys from Git
- Environment variables
- Cron jobs
- Background workers

**Pros**:
- Free tier for hobby projects
- Simple pricing
- Good performance

**Cons**:
- Free tier has spin-down after inactivity
- Limited resources on free tier

### 🥉 Option 3: DigitalOcean App Platform

**Best for**: Scalability and reliability

**Pricing**: Starts at $5/month

**Features**:
- Auto-scaling
- Load balancing
- Automatic HTTPS
- Database support
- CDN integration

**Pros**:
- Excellent performance
- Great documentation
- Predictable pricing

**Cons**:
- No free tier
- Slightly more complex setup

### Option 4: Heroku

**Best for**: Traditional PaaS with extensive add-on marketplace

**Pricing**: No free tier anymore, starts at $7/month

**Features**:
- Extensive add-on ecosystem
- Easy database management
- Automatic deployments

**Pros**:
- Most mature platform
- Extensive documentation
- Large community

**Cons**:
- No free tier
- Can be expensive

---

## Deployment Instructions

### Deploying to Railway.app

#### Step 1: Prepare Your Repository

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Django backend for pulseofpeople.com"

# Create GitHub repository (via GitHub CLI or web interface)
gh repo create pulseofpeople-backend --public --source=. --remote=origin

# Push to GitHub
git push -u origin main
```

#### Step 2: Deploy to Railway

1. **Sign up at [Railway.app](https://railway.app)**
   - Use GitHub OAuth for easy integration

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `pulseofpeople-backend` repository
   - Select the `backend` folder as the root directory

3. **Configure Build Settings**
   Railway will auto-detect Django. If not:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
   - Root Directory: `backend`

4. **Add Environment Variables** (See Environment Configuration section)

5. **Deploy**
   - Railway will automatically deploy
   - You'll get a URL like: `https://your-app.railway.app`

6. **Run Migrations**
   ```bash
   # In Railway dashboard, open the service terminal
   railway run python manage.py migrate
   railway run python manage.py createsuperuser
   ```

#### Step 3: Configure Custom Domain (Optional)

1. In Railway dashboard, go to Settings → Domains
2. Add your custom domain: `api.pulseofpeople.com`
3. Configure DNS:
   ```
   Type: CNAME
   Name: api
   Value: your-app.railway.app
   ```

---

### Deploying to Render.com

#### Step 1: Push to GitHub (same as Railway)

#### Step 2: Deploy to Render

1. **Sign up at [Render.com](https://render.com)**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - Name: `pulseofpeople-backend`
     - Region: Choose closest to your users
     - Branch: `main`
     - Root Directory: `backend`
     - Runtime: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

3. **Add Environment Variables** (See Environment Configuration section)

4. **Deploy**
   - Render will automatically deploy
   - You'll get a URL like: `https://pulseofpeople-backend.onrender.com`

5. **Run Initial Migrations**
   - In Render dashboard, open Shell
   - Run: `python manage.py migrate`
   - Run: `python manage.py createsuperuser`

---

### Deploying to DigitalOcean App Platform

#### Step 1: Push to GitHub (same as above)

#### Step 2: Deploy to DigitalOcean

1. **Sign up at [DigitalOcean](https://www.digitalocean.com)**

2. **Create App**
   - Go to App Platform
   - Click "Create App"
   - Connect your GitHub repository
   - Select your repository and branch

3. **Configure App**
   - Type: Web Service
   - Source Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3`

4. **Add Environment Variables** (See Environment Configuration section)

5. **Review and Deploy**
   - Choose your plan ($5/month minimum)
   - Review settings and deploy

6. **Run Migrations**
   - In App Console, run:
     ```bash
     python manage.py migrate
     python manage.py createsuperuser
     ```

---

## Environment Configuration

### Required Environment Variables

Add these to your deployment platform's environment variables:

```bash
# Django Core
SECRET_KEY=your-production-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=api.pulseofpeople.com,your-app.railway.app
USE_SQLITE=False

# Database (Supabase PostgreSQL)
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your_supabase_password
DB_HOST=db.your-project-ref.supabase.co
DB_PORT=5432
DB_SSLMODE=require

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# CORS (Add your frontend domains)
CORS_ALLOWED_ORIGINS=https://pulseofpeople.com,https://www.pulseofpeople.com,http://localhost:5173
CSRF_TRUSTED_ORIGINS=https://pulseofpeople.com,https://www.pulseofpeople.com

# Security
SECURE_SSL_REDIRECT=True

# Optional: Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pulseofpeople.com

# Optional: Sentiment Analysis
SENTIMENT_API_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key

# Feature Flags
ENABLE_NOTIFICATIONS=True
ENABLE_FILE_UPLOAD=True
ENABLE_SENTIMENT_ANALYSIS=True
ENABLE_AUDIT_LOGGING=True
ENABLE_REALTIME=True
```

### Generating Secure SECRET_KEY

```python
# In Python shell
import secrets
print(secrets.token_urlsafe(50))
```

Or use Django:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Post-Deployment Steps

### 1. Run Database Migrations

```bash
# Railway
railway run python manage.py migrate

# Render (in Shell)
python manage.py migrate

# DigitalOcean (in Console)
python manage.py migrate
```

### 2. Create Superuser

```bash
python manage.py createsuperuser
```

### 3. Collect Static Files (if needed)

```bash
python manage.py collectstatic --noinput
```

### 4. Test API Endpoints

```bash
# Health check
curl https://your-api-domain.com/api/health/

# Login
curl -X POST https://your-api-domain.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

### 5. Update Frontend Environment Variables

Update your React frontend's environment variables:

```bash
# frontend/.env.production
VITE_API_URL=https://api.pulseofpeople.com/api
```

### 6. Configure CORS

Ensure your backend's `CORS_ALLOWED_ORIGINS` includes your frontend domain:

```python
# In settings.py or via environment variable
CORS_ALLOWED_ORIGINS = [
    'https://pulseofpeople.com',
    'https://www.pulseofpeople.com',
]
```

---

## CI/CD Setup

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Django Backend

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd backend
        python manage.py test

    - name: Check migrations
      run: |
        cd backend
        python manage.py makemigrations --check --dry-run

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Railway
      run: |
        npm install -g @railway/cli
        railway up
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Setting Up CI/CD

1. **Add Railway Token to GitHub Secrets**
   ```bash
   # Get token
   railway login
   railway whoami --show-token

   # Add to GitHub: Settings → Secrets → New repository secret
   # Name: RAILWAY_TOKEN
   # Value: <your-token>
   ```

2. **Enable Auto-Deploy**
   - In Railway dashboard: Settings → Auto-deploy
   - Select branch: `main`

---

## Monitoring & Logging

### Railway Monitoring

1. **View Logs**
   - Railway dashboard → Select service → Logs tab
   - Or via CLI: `railway logs`

2. **Metrics**
   - CPU usage
   - Memory usage
   - Request count
   - Response times

### Error Tracking (Optional)

Consider adding Sentry for error tracking:

```bash
pip install sentry-sdk
```

Add to `settings.py`:
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    environment='production',
)
```

---

## Database Backups

### Supabase Backups

Supabase automatically backs up your database daily. To create manual backup:

1. Go to Supabase dashboard
2. Database → Backups
3. Click "Create backup"

### Local Database Dump

```bash
# Export from Supabase
pg_dump -h db.your-project.supabase.co \
  -U postgres.your-ref \
  -d postgres \
  -F c \
  -f backup_$(date +%Y%m%d).dump
```

---

## Security Best Practices

1. **Never commit secrets**
   - Use environment variables
   - Keep `.env` in `.gitignore`

2. **Use HTTPS only**
   - Set `SECURE_SSL_REDIRECT=True`
   - Configure HSTS headers

3. **Regular updates**
   ```bash
   pip list --outdated
   pip install --upgrade django djangorestframework
   ```

4. **Database security**
   - Use strong passwords
   - Enable SSL connections
   - Implement connection pooling

5. **Rate limiting**
   - Consider using `django-ratelimit`
   - Configure DDoS protection at platform level

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause**: Application failed to start

**Solution**:
1. Check logs: `railway logs` or platform dashboard
2. Verify environment variables
3. Check database connection
4. Ensure gunicorn is installed

### Issue: Database Connection Failed

**Cause**: Incorrect database credentials or SSL mode

**Solution**:
```bash
# Verify credentials in Supabase dashboard
# Ensure DB_SSLMODE=require
# Check DB_HOST format: db.xxxxx.supabase.co
```

### Issue: Static Files Not Loading

**Cause**: Static files not collected or served

**Solution**:
```python
# In settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Then run: `python manage.py collectstatic`

### Issue: CORS Errors

**Cause**: Frontend domain not in CORS_ALLOWED_ORIGINS

**Solution**:
```bash
# Update environment variable
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:5173
```

### Issue: Migrations Not Applied

**Solution**:
```bash
# Railway
railway run python manage.py migrate

# Or add to Procfile
release: python manage.py migrate --noinput
```

---

## Cost Estimates

### Railway
- Free: $5 credit/month
- Hobby: ~$5-10/month for small app
- Team: ~$20+/month with scaling

### Render
- Free: $0 (with limitations)
- Starter: $7/month
- Standard: $25/month

### DigitalOcean
- Basic: $5/month
- Professional: $12/month
- Professional Plus: $24/month

### Heroku
- Basic: $7/month
- Standard: $25-50/month

---

## Support & Resources

### Documentation
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Supabase Docs](https://supabase.com/docs)

### Community
- Django Discord
- Railway Discord
- Stack Overflow

---

## Next Steps

1. ✅ Initialize Git repository
2. ✅ Create GitHub repository
3. ✅ Choose deployment platform (Railway recommended)
4. ✅ Set up environment variables
5. ✅ Deploy backend
6. ✅ Run migrations
7. ✅ Test API endpoints
8. ✅ Update frontend to use production API
9. ✅ Set up CI/CD
10. ✅ Configure monitoring

---

**Last Updated**: 2025-11-06
**Version**: 1.0
**Author**: Pulseofpeople.com Team
