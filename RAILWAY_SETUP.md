# Railway Deployment Fix Guide

Your deployment failed because Railway needs to know the `backend/` folder is where the Django app lives.

## Quick Fix Steps

### Step 1: Open Railway Dashboard

```bash
railway open
```

This will open your project: https://railway.com/project/d4271494-7e7c-43bf-bc4c-e3687783627e

### Step 2: Configure Root Directory

1. **Click on your service** (in the project dashboard)
2. Go to **Settings** tab (top menu)
3. Scroll down to **Source** section
4. Find **Root Directory** field
5. Enter: `backend`
6. Click **Save** or it will auto-save

### Step 3: Verify Build Configuration

In Settings, check:
- ✅ **Root Directory**: `backend`
- ✅ **Build Command**: (leave empty, will auto-detect)
- ✅ **Start Command**: (leave empty, Railway will use Procfile or railway.json)

### Step 4: Add Environment Variables

1. Go to **Variables** tab
2. Click **+ New Variable**
3. Add each variable (see list below)

#### Required Variables:

```bash
# Generate SECRET_KEY first (see below)
SECRET_KEY=your-generated-secret-key

# Django Settings
DEBUG=False
USE_SQLITE=False

# Railway provides these automatically:
# ALLOWED_HOSTS will use ${{RAILWAY_PUBLIC_DOMAIN}}

# For ALLOWED_HOSTS, use:
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},${{RAILWAY_PRIVATE_DOMAIN}},localhost

# Supabase Database (REQUIRED - Get from Supabase Dashboard)
DB_NAME=postgres
DB_USER=postgres.iwtgbseaoztjbnvworyq
DB_PASSWORD=<YOUR_SUPABASE_PASSWORD>
DB_HOST=db.iwtgbseaoztjbnvworyq.supabase.co
DB_PORT=5432
DB_SSLMODE=require

# Supabase API (REQUIRED)
SUPABASE_URL=https://iwtgbseaoztjbnvworyq.supabase.co
SUPABASE_ANON_KEY=<YOUR_ANON_KEY>
SUPABASE_SERVICE_ROLE_KEY=<YOUR_SERVICE_KEY>
SUPABASE_JWT_SECRET=<YOUR_JWT_SECRET>

# CORS (Add your frontend domain)
CORS_ALLOWED_ORIGINS=https://pulseofpeople.com,https://www.pulseofpeople.com,https://${{RAILWAY_PUBLIC_DOMAIN}}
CSRF_TRUSTED_ORIGINS=https://pulseofpeople.com,https://www.pulseofpeople.com,https://${{RAILWAY_PUBLIC_DOMAIN}}

# Security
SECURE_SSL_REDIRECT=True
```

#### Generate SECRET_KEY:

Run this locally:
```bash
cd backend
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as the `SECRET_KEY` value in Railway.

### Step 5: Get Supabase Credentials

1. Go to your Supabase project: https://supabase.com/dashboard
2. Click on your project
3. Go to **Project Settings** → **Database**
4. Copy the connection string details:
   - Host (DB_HOST)
   - Database (DB_NAME)
   - User (DB_USER)
   - Password (DB_PASSWORD)

5. Go to **Project Settings** → **API**
6. Copy:
   - Project URL (SUPABASE_URL)
   - anon/public key (SUPABASE_ANON_KEY)
   - service_role key (SUPABASE_SERVICE_ROLE_KEY)
   - JWT Secret (SUPABASE_JWT_SECRET)

### Step 6: Redeploy

Railway will automatically redeploy after you:
- Set the root directory
- Add environment variables

Or manually trigger a redeploy:
```bash
railway up
```

Or in the dashboard:
- Go to **Deployments** tab
- Click **Deploy** button

### Step 7: Monitor Deployment

Watch the build logs:
```bash
railway logs
```

Or in the dashboard:
- Click on the latest deployment
- View **Build Logs** and **Deploy Logs**

### Step 8: Run Migrations

Once the deployment succeeds, run migrations:

```bash
# Connect to Railway shell
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

### Step 9: Test Your API

Get your Railway URL:
```bash
railway domain
```

Or check in dashboard under **Settings** → **Domains**

Test the health endpoint:
```bash
curl https://your-app.up.railway.app/api/health/
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Troubleshooting

### Issue: Build still failing

**Check:**
1. Root directory is set to `backend`
2. All environment variables are added
3. Supabase credentials are correct

**View logs:**
```bash
railway logs --follow
```

### Issue: Database connection failed

**Fix:**
1. Verify DB_HOST format: `db.xxxxx.supabase.co`
2. Ensure DB_SSLMODE=require
3. Check password is correct (no quotes)
4. Verify database user has correct permissions

### Issue: Module not found errors

**Fix:**
- Railway should auto-install from requirements.txt
- If not, check that requirements.txt is in backend/ folder

### Issue: Static files not loading

**Fix:**
Already handled by WhiteNoise in settings.py. Run:
```bash
railway run python manage.py collectstatic --noinput
```

---

## Alternative: Deploy via Web UI Only

If CLI isn't working well:

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **New Project** → **Deploy from GitHub**
3. **Connect your repo**: chatgptnotes/pulseofpeople_Django
4. **Configure**:
   - Root Directory: `backend`
   - Add all environment variables
5. **Deploy**

---

## Quick Command Reference

```bash
# View logs
railway logs

# Run commands
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py collectstatic

# Open dashboard
railway open

# Check status
railway status

# Get domain
railway domain

# Redeploy
railway up

# Link different service
railway link
```

---

## Success Checklist

- [ ] Root directory set to `backend`
- [ ] All environment variables added
- [ ] Supabase credentials configured
- [ ] Build succeeded
- [ ] Deployment succeeded
- [ ] Health endpoint responds
- [ ] Migrations ran successfully
- [ ] Superuser created
- [ ] Can access admin panel
- [ ] API endpoints working

---

## Your Project URLs

- **Railway Project**: https://railway.com/project/d4271494-7e7c-43bf-bc4c-e3687783627e
- **Your Domain**: (will be shown after successful deployment)
- **Admin Panel**: https://your-domain.up.railway.app/admin/
- **API Health**: https://your-domain.up.railway.app/api/health/

---

**Need Help?**

Check the detailed deployment guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

Or create an issue: https://github.com/chatgptnotes/pulseofpeople_Django/issues
