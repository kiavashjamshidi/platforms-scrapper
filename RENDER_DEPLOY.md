# Deploy to Render.com (FREE Forever)

## Why Render.com?
- ✅ 750 hours/month FREE (no trial, no expiration)
- ✅ No credit card required
- ✅ Automatic HTTPS
- ✅ Free PostgreSQL database
- ✅ Docker support
- ✅ Custom domains (free)

## Deployment Steps:

### 1. Go to render.com and sign up with GitHub

### 2. Create services:

#### A. Database (PostgreSQL)
1. Click "New" → "PostgreSQL"
2. Name: `streaming-db`
3. Plan: Free
4. Create

#### B. API Service
1. Click "New" → "Web Service"
2. Connect GitHub repo: `platforms-scrapper`
3. Settings:
   - Name: `streaming-api`
   - Environment: Docker
   - Dockerfile path: `Dockerfile` (in root)
   - Plan: Free
4. Environment Variables:
   - DATABASE_URL: (copy from PostgreSQL service)
   - Add other env vars from your .env

#### C. Dashboard Service
1. Click "New" → "Web Service"
2. Connect same repo
3. Settings:
   - Name: `streaming-dashboard`
   - Environment: Docker
   - Dockerfile path: `dashboard/Dockerfile`
   - Plan: Free

### 3. Your URLs will be:
- Dashboard: https://streaming-dashboard.onrender.com
- API: https://streaming-api.onrender.com

## Advantages over Railway:
- No trial period confusion
- Clearly free forever
- More hours per month (750 vs 500)
- Excellent Docker support