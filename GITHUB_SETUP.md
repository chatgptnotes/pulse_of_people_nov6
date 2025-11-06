# GitHub Repository Setup Guide

This guide will help you push your Django backend to GitHub and deploy it.

## Quick Setup (Recommended)

### Option 1: Using GitHub CLI (gh)

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
# Windows: https://github.com/cli/cli/releases

# Login to GitHub
gh auth login

# Create repository and push
gh repo create pulseofpeople-backend --public --source=. --remote=origin --push

# View your repository
gh repo view --web
```

### Option 2: Using GitHub Web Interface

1. **Go to GitHub** and sign in: https://github.com

2. **Create New Repository**
   - Click the "+" icon → "New repository"
   - Repository name: `pulseofpeople-backend`
   - Description: "Django REST API backend for Pulseofpeople.com voter sentiment analysis platform"
   - Choose: Public or Private
   - **DO NOT** initialize with README (we already have one)
   - Click "Create repository"

3. **Push your local repository**
   ```bash
   # Add GitHub remote
   git remote add origin https://github.com/YOUR_USERNAME/pulseofpeople-backend.git

   # Verify remote
   git remote -v

   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

---

## Repository Structure

Your repository is now organized as:

```
pulseofpeople-backend/
├── backend/                    # Django application
│   ├── api/                    # API app with models, views, serializers
│   ├── config/                 # Django settings and configuration
│   ├── manage.py               # Django management script
│   ├── requirements.txt        # Python dependencies
│   ├── Procfile               # For Heroku/Railway deployment
│   ├── runtime.txt            # Python version specification
│   ├── railway.json           # Railway.app configuration
│   ├── render.yaml            # Render.com configuration
│   └── README.md              # Backend-specific documentation
├── frontend/                   # React frontend (for reference)
├── frontend_ARCHIVED/          # Archived frontend version
├── DEPLOYMENT_GUIDE.md         # Comprehensive deployment guide
├── GITHUB_SETUP.md            # This file
├── README.md                  # Main project documentation
├── .gitignore                 # Git ignore rules
└── [other documentation files]
```

---

## Post-Push Steps

### 1. Verify Repository

```bash
# View repository in browser
gh repo view --web

# Or manually visit:
# https://github.com/YOUR_USERNAME/pulseofpeople-backend
```

### 2. Configure Repository Settings (Optional)

#### Add Topics (for discoverability)
- Go to your repository on GitHub
- Click "About" gear icon
- Add topics: `django`, `django-rest-framework`, `postgresql`, `supabase`, `jwt-authentication`, `python`, `voter-analysis`

#### Set Repository Description
"Django REST API backend for Pulseofpeople.com - Multi-tenant voter sentiment analysis platform with RBAC, real-time notifications, and Supabase integration"

#### Update Homepage URL
- Settings → Homepage URL: `https://api.pulseofpeople.com` (after deployment)

### 3. Protect Main Branch (Recommended)

```bash
# Via GitHub CLI
gh api -X PUT repos/:owner/:repo/branches/main/protection \
  -f required_status_checks='{"strict":true,"contexts":[]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}'
```

Or via GitHub web:
- Settings → Branches → Add branch protection rule
- Branch name pattern: `main`
- Enable:
  - ✅ Require pull request reviews before merging
  - ✅ Require status checks to pass before merging
  - ✅ Include administrators (optional)

---

## Next Steps: Deployment

Now that your code is on GitHub, choose a deployment platform:

### 🥇 Railway.app (Recommended)

**1. Sign up at Railway.app**
   - https://railway.app
   - Sign in with GitHub

**2. Create New Project**
   - Dashboard → "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `pulseofpeople-backend`
   - Select `backend` folder as root directory

**3. Configure Environment Variables**
   - Add all variables from `backend/.env.example`
   - See DEPLOYMENT_GUIDE.md for details

**4. Deploy**
   - Railway will automatically build and deploy
   - You'll get a URL: `https://your-app.railway.app`

**5. Run Migrations**
   ```bash
   railway run python manage.py migrate
   railway run python manage.py createsuperuser
   ```

**6. Set Custom Domain (Optional)**
   - Settings → Domains → Add domain
   - Point `api.pulseofpeople.com` to Railway

### 🥈 Alternative: Render.com

**1. Sign up at Render.com**
   - https://render.com
   - Connect GitHub account

**2. Create Web Service**
   - New → Web Service
   - Connect repository: `pulseofpeople-backend`
   - Root directory: `backend`
   - Runtime: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

**3. Add Environment Variables**
   - Copy from `backend/.env.example`

**4. Deploy**
   - Render will auto-deploy on push to main

---

## CI/CD Setup (Optional but Recommended)

### GitHub Actions Workflow

Create `.github/workflows/django-ci.yml`:

```yaml
name: Django CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

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
      env:
        SECRET_KEY: test-secret-key
        DEBUG: True
        USE_SQLITE: True
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

### Setup CI/CD:

1. **Get Railway Token**
   ```bash
   railway login
   railway whoami --show-token
   ```

2. **Add to GitHub Secrets**
   - Repository → Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `RAILWAY_TOKEN`
   - Value: `<your-token>`

3. **Push Workflow**
   ```bash
   git add .github/workflows/django-ci.yml
   git commit -m "Add CI/CD workflow"
   git push
   ```

---

## Useful Git Commands

### Daily Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Your commit message"

# Push to GitHub
git push

# Pull latest changes
git pull

# Create new branch
git checkout -b feature/new-feature

# Switch branch
git checkout main

# Merge branch
git merge feature/new-feature
```

### Branch Management

```bash
# List branches
git branch -a

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Rename current branch
git branch -m new-branch-name
```

### Undo Changes

```bash
# Discard changes in working directory
git checkout -- filename

# Unstage file
git reset HEAD filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1
```

### View History

```bash
# View commit history
git log --oneline --graph --all

# View specific file history
git log --follow filename

# View changes
git diff

# View changes for specific file
git diff filename
```

---

## Collaborative Development

### Fork Workflow (for contributors)

1. Fork repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pulseofpeople-backend.git
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/pulseofpeople-backend.git
   ```
4. Create feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
5. Make changes and commit
6. Push to your fork:
   ```bash
   git push origin feature/amazing-feature
   ```
7. Create Pull Request on GitHub

### Syncing Fork

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream main into your main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

---

## Environment-Specific Branches

Consider this branching strategy:

- `main` - Production-ready code (protected)
- `develop` - Integration branch for features
- `staging` - Pre-production testing
- `feature/*` - Feature development branches
- `hotfix/*` - Production hotfixes

### Setup

```bash
# Create develop branch
git checkout -b develop
git push -u origin develop

# Create staging branch
git checkout -b staging
git push -u origin staging
```

---

## Troubleshooting

### Issue: Permission Denied (publickey)

**Solution**: Set up SSH keys
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
```

### Issue: Remote Already Exists

**Solution**: Update remote URL
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/pulseofpeople-backend.git
```

### Issue: Merge Conflicts

**Solution**: Resolve manually
```bash
# Pull latest changes
git pull

# Fix conflicts in files (marked with <<<<<<<, =======, >>>>>>>)
# Then:
git add .
git commit -m "Resolve merge conflicts"
git push
```

### Issue: Large Files

**Solution**: Use Git LFS or .gitignore
```bash
# Install Git LFS
brew install git-lfs
git lfs install

# Track large files
git lfs track "*.psd"
git add .gitattributes
```

---

## Security Best Practices

1. **Never commit secrets**
   - `.env` is in `.gitignore`
   - Use environment variables
   - Use GitHub Secrets for CI/CD

2. **Review commits before pushing**
   ```bash
   git diff --staged
   ```

3. **Enable two-factor authentication**
   - GitHub Settings → Security

4. **Use SSH keys instead of passwords**
   - More secure
   - No password prompts

5. **Sign commits (optional)**
   ```bash
   git config --global user.signingkey <your-key-id>
   git config --global commit.gpgsign true
   ```

---

## Repository Badges (Optional)

Add to your README.md:

```markdown
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Build Status](https://github.com/YOUR_USERNAME/pulseofpeople-backend/workflows/Django%20CI/badge.svg)](https://github.com/YOUR_USERNAME/pulseofpeople-backend/actions)
```

---

## Resources

### Documentation
- [GitHub Docs](https://docs.github.com/)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI](https://cli.github.com/)

### Tutorials
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

### Tools
- [GitHub Desktop](https://desktop.github.com/) - GUI for Git
- [GitKraken](https://www.gitkraken.com/) - Advanced Git GUI
- [VS Code Git Extension](https://code.visualstudio.com/docs/editor/versioncontrol)

---

## Summary

Your repository is now:
- ✅ Initialized with Git
- ✅ First commit created
- ✅ Ready to push to GitHub
- ✅ Configured for deployment (Railway, Render, DO)
- ✅ Production-ready with proper .gitignore
- ✅ Documented with comprehensive guides

**Next Step**: Push to GitHub and deploy!

```bash
# If not already done:
gh repo create pulseofpeople-backend --public --source=. --remote=origin --push

# Or manually:
git remote add origin https://github.com/YOUR_USERNAME/pulseofpeople-backend.git
git push -u origin main
```

---

**Last Updated**: 2025-11-06
