# FOCOSA Hub - Vercel Frontend + Render Backend Deployment

## 🏗️ Complete Setup Guide

This guide covers deploying:
- **Frontend (HTML/React)** → Vercel
- **Backend (Python/FastAPI)** → Render (with automatic keep-alive)

---

## 📋 Prerequisites

1. GitHub account (https://github.com)
2. Vercel account (https://vercel.com) - Free
3. Render account (https://render.com) - Free
4. Your FOCOSA Hub project files

---

## PART 1: DEPLOY BACKEND TO RENDER ⭐ (Start Here)

### Step 1: Prepare Your Backend Files

1. Rename your backend files:
   - `main_user_render.py` → `main_user.py`
   - `main_admin_render.py` → `main_admin.py`

2. Ensure you have these files in your GitHub repo:
   ```
   focosa-hub/
   ├── main_user.py          (✅ has keep-alive)
   ├── main_admin.py         (✅ has keep-alive)
   ├── focosa.db             (database)
   ├── focosa.db-shm
   ├── focosa.db-wal
   └── requirements.txt
   ```

### Step 2: Update requirements.txt

Make sure it includes requests library (for keep-alive):

```txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
pydantic[email]==2.7.0
requests==2.31.0
```

### Step 3: Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment with keep-alive"
git push origin main
```

### Step 4: Deploy User API to Render

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. **Connect your GitHub repo**
   - Search for your `focosa-hub` repo
   - Click "Connect"

4. **Configure the service:**
   ```
   Name: focosa-user
   Environment: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: python main_user.py
   Plan: Free (this is fine!)
   ```

5. **Add Environment Variables** (Click "Add Environment Variable"):
   ```
   SECRET_KEY = your-super-secret-key-change-this
   PORT = 8000
   ENVIRONMENT = production
   DB_PATH = focosa.db
   ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app,http://localhost:3000
   ```

6. Click **"Create Web Service"**

7. **Wait for deployment** (2-3 minutes)

8. **Note the URL** you get:
   - Something like: `https://focosa-user.onrender.com`

✅ **Your User API is now live!**

### Step 5: Deploy Admin API to Render

1. Click **"New +"** → **"Web Service"** again
2. Same GitHub repo, but:
   ```
   Name: focosa-admin
   Environment: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: python main_admin.py
   ```

3. **Environment Variables:**
   ```
   SECRET_KEY = (same as above)
   PORT = 8001
   ENVIRONMENT = production
   DB_PATH = focosa.db
   ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app,http://localhost:3000
   ```

4. Click **"Create Web Service"**

✅ **Your Admin API is now live!**

### Step 6: Test Your Backend APIs

1. **Test User API:** Visit
   ```
   https://focosa-user.onrender.com/docs
   ```
   You should see Swagger documentation

2. **Test Admin API:** Visit
   ```
   https://focosa-admin.onrender.com/docs
   ```

3. **Test Health Check:**
   ```
   https://focosa-user.onrender.com/health
   https://focosa-admin.onrender.com/health
   ```

✅ **Both should return `{"status": "healthy", ...}`**

### Keep-Alive is AUTOMATIC! 🎉

Your code includes a keep-alive function that:
- ✅ Pings itself every 30 minutes
- ✅ Prevents Render from shutting down the app
- ✅ Works on free tier
- ✅ No manual configuration needed!

---

## PART 2: DEPLOY FRONTEND TO VERCEL

### Option A: Simple HTML Files (Quick)

#### Step 1: Update HTML Files

Update your HTML files to use Render URLs:

**focosa-connected.html (User Frontend):**
```html
<!-- At the top of your script section, add: -->
<script>
  // Production API URLs
  const API_URL = 'https://focosa-user.onrender.com';
  const ADMIN_API_URL = 'https://focosa-admin.onrender.com';
  
  // Use these in your fetch calls
  // fetch(`${API_URL}/departments`)
</script>
```

**focosa-admin.html (Admin Frontend):**
```html
<script>
  const ADMIN_API_URL = 'https://focosa-admin.onrender.com';
  const API_URL = 'https://focosa-user.onrender.com';
</script>
```

#### Step 2: Create Vercel Configuration

Create `vercel.json` in your repo root:

```json
{
  "buildCommand": "echo 'Static HTML deployment'",
  "outputDirectory": ".",
  "env": {
    "NEXT_PUBLIC_USER_API": "https://focosa-user.onrender.com",
    "NEXT_PUBLIC_ADMIN_API": "https://focosa-admin.onrender.com"
  }
}
```

#### Step 3: Deploy to Vercel

1. Go to https://vercel.com
2. Click **"Add New..."** → **"Project"**
3. **Import your GitHub repo**
4. **Configure Project:**
   - Framework Preset: "Other"
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: (leave empty)

5. **Add Environment Variables:**
   ```
   NEXT_PUBLIC_USER_API = https://focosa-user.onrender.com
   NEXT_PUBLIC_ADMIN_API = https://focosa-admin.onrender.com
   ```

6. Click **"Deploy"**

✅ You get a URL like: `https://focosa-hub.vercel.app`

---

### Option B: Next.js/React (Professional)

If you want a proper frontend framework:

#### Step 1: Create Next.js App

```bash
npx create-next-app@latest focosa-frontend --typescript --tailwind
cd focosa-frontend
npm install axios
```

#### Step 2: Create .env.local

```
NEXT_PUBLIC_USER_API_URL=https://focosa-user.onrender.com
NEXT_PUBLIC_ADMIN_API_URL=https://focosa-admin.onrender.com
```

#### Step 3: Create API Call Helper

Create `lib/api.ts`:

```typescript
import axios from 'axios';

const userAPI = axios.create({
  baseURL: process.env.NEXT_PUBLIC_USER_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const adminAPI = axios.create({
  baseURL: process.env.NEXT_PUBLIC_ADMIN_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export { userAPI, adminAPI };
```

#### Step 4: Build Components

Example component:

```typescript
// pages/departments.tsx
import { userAPI } from '@/lib/api';
import { useEffect, useState } from 'react';

export default function Departments() {
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    userAPI.get('/departments')
      .then(res => setDepartments(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h1>Departments</h1>
      {departments.map((dept: any) => (
        <div key={dept.id}>{dept.name}</div>
      ))}
    </div>
  );
}
```

#### Step 5: Deploy to Vercel

```bash
npm install -g vercel
vercel --prod
```

Or push to GitHub and Vercel auto-deploys!

---

## 📊 Your Final URLs

After deployment, you'll have:

```
User Frontend:     https://focosa-hub.vercel.app
User Backend API:  https://focosa-user.onrender.com
Admin Frontend:    https://focosa-hub.vercel.app/admin
Admin Backend API: https://focosa-admin.onrender.com
```

---

## 🔄 How Keep-Alive Works on Render

Your code includes automatic keep-alive:

```python
# This runs in the background:
def keep_alive():
    while True:
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            requests.get(f"{render_url}/health", timeout=5)
            # Pings itself every 30 minutes ✅
            print(f"✅ Keep-alive ping sent")
        time.sleep(1800)  # 30 minutes
```

**Benefits:**
- ✅ App never goes to sleep on free tier
- ✅ Always responds immediately to requests
- ✅ No manual configuration needed
- ✅ Completely automatic
- ✅ Works for both APIs

---

## 🔐 Environment Variables Setup

### For Render Services

**User API Environment:**
```
SECRET_KEY = focosa-change-me-in-production
PORT = 8000
ENVIRONMENT = production
DB_PATH = focosa.db
ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app
```

**Admin API Environment:**
```
SECRET_KEY = focosa-change-me-in-production
PORT = 8001
ENVIRONMENT = production
DB_PATH = focosa.db
ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app
```

### For Vercel

```
NEXT_PUBLIC_USER_API_URL = https://focosa-user.onrender.com
NEXT_PUBLIC_ADMIN_API_URL = https://focosa-admin.onrender.com
```

---

## 🧪 Testing Your Deployment

### 1. Test Backend APIs

```bash
# Test User API
curl https://focosa-user.onrender.com/health

# Test Admin API
curl https://focosa-admin.onrender.com/health

# Get departments
curl https://focosa-user.onrender.com/departments
```

### 2. Test Frontend

1. Visit your Vercel URL
2. Register a student account
3. Login with credentials
4. Go to admin section with admin credentials

### 3. Test Keep-Alive

Check Render logs:
```
✅ Keep-alive ping sent at 2024-03-15 14:30:45
✅ Keep-alive ping sent at 2024-03-15 15:00:45
✅ Keep-alive ping sent at 2024-03-15 15:30:45
```

If you see these every 30 minutes → **Keep-alive is working!** ✅

---

## 📱 Database Persistence

### Important: Database Survives Deployment!

Even though Render free tier restarts weekly:
- ✅ Your `focosa.db` file persists
- ✅ All data is saved between restarts
- ✅ Users, departments, events all stay
- ✅ No data loss

---

## 🚀 Making Changes

### Push Updates to Render

1. Make changes to your code
2. Commit to GitHub:
   ```bash
   git add .
   git commit -m "Update API endpoints"
   git push origin main
   ```
3. Render automatically redeploys! ✅

### Update Frontend on Vercel

1. Edit HTML/React files
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Update UI"
   git push origin main
   ```
3. Vercel automatically redeploys! ✅

---

## ⚠️ Common Issues & Solutions

### Issue: CORS Errors in Frontend

**Error:** "Access to XMLHttpRequest blocked by CORS policy"

**Solution:** Update `ALLOWED_ORIGINS` on Render:
```
ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app,http://localhost:3000
```

### Issue: 404 on `/health` endpoint

**Solution:** Make sure you're using `main_user_render.py` or `main_admin_render.py`
(they have the `/health` endpoint)

### Issue: App goes offline after 15 minutes

**Solution:** This means keep-alive isn't running. Check:
1. `ENVIRONMENT = production` is set in Render
2. `requests` library is in requirements.txt
3. No errors in logs

### Issue: "Database is locked"

**Solution:** This shouldn't happen with WAL mode, but if it does:
1. Redeploy the service
2. Database lock files will be cleared

### Issue: Vercel can't reach Render API

**Solution:** 
1. Check CORS origins are correct
2. Verify Render service is running (check health endpoint)
3. Clear browser cache and cookies

---

## 📈 Scaling Your App

### If You Need More Power:

**Render Paid Plans:**
- Starter: $7/month → More RAM, no restarts
- Standard: $25/month → 2GB RAM, 1GB storage
- Professional: $100+/month → Enterprise features

**Vercel:**
- Free forever for frontends
- Can upgrade to Pro ($20/month) if needed

---

## 📞 Support Resources

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Your APIs:** 
  - `https://focosa-user.onrender.com/docs`
  - `https://focosa-admin.onrender.com/docs`

---

## ✅ Deployment Checklist

- [ ] Backend code renamed to `main_user.py` and `main_admin.py`
- [ ] requirements.txt includes `requests` library
- [ ] Code pushed to GitHub
- [ ] User API deployed to Render
- [ ] Admin API deployed to Render
- [ ] Environment variables set on both Render services
- [ ] Both APIs accessible at `/docs` endpoints
- [ ] Both APIs returning healthy from `/health` endpoint
- [ ] Frontend updated with Render API URLs
- [ ] Frontend deployed to Vercel
- [ ] Tested user registration and login
- [ ] Tested admin functions
- [ ] Verified keep-alive is working in logs

---

## 🎉 You're Live!

Your FOCOSA Hub is now running on:
- 🎨 **Frontend:** Vercel (free, super fast)
- 🔧 **Backend:** Render (free, with auto keep-alive)
- 📦 **Database:** SQLite on Render (data persists)

**Everything automatically stays online!** No need to worry about apps going offline.

---

**Questions? Check the logs on Render dashboard!**
