# FOCOSA Hub - Vercel Frontend + PythonAnywhere Backend Deployment

## 🏗️ Setup Guide

Deploy your:
- **Frontend** → Vercel (free)
- **Backend** → PythonAnywhere (free with generous limits)

---

## Part 1: Deploy Backend to PythonAnywhere

### Step 1: Create PythonAnywhere Account

1. Go to https://www.pythonanywhere.com
2. Click **"Sign Up"**
3. Choose **"Beginner"** account (free!)
4. Verify email

### Step 2: Upload Your Code

1. Go to **"Files"** tab
2. Create a new folder: `/mysite`
3. Upload these files:
   ```
   main_user.py
   main_admin.py
   focosa.db (optional - will be created)
   requirements.txt
   ```

### Step 3: Set Up Virtual Environment

Go to **"Consoles"** tab and create a new **Bash console**:

```bash
# Go to your directory
cd /home/yourusername/mysite

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.8 focosa
pip install -r requirements.txt
```

### Step 4: Create WSGI Files

Go to **"Files"** and create `/mysite/user_wsgi.py`:

```python
import sys
import os

# Add project directory to path
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.append(path)

# Set environment
os.environ['ENVIRONMENT'] = 'production'
os.environ['SECRET_KEY'] = 'your-secret-key-change-this'
os.environ['DB_PATH'] = '/home/yourusername/mysite/focosa.db'
os.environ['ALLOWED_ORIGINS'] = 'https://focosa.vercel.app,https://admin.vercel.app'

# Import and run
from main_user import app

# This is what PythonAnywhere looks for
application = app
```

Create `/mysite/admin_wsgi.py`:

```python
import sys
import os

path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.append(path)

os.environ['ENVIRONMENT'] = 'production'
os.environ['SECRET_KEY'] = 'your-secret-key-change-this'
os.environ['DB_PATH'] = '/home/yourusername/mysite/focosa.db'
os.environ['ALLOWED_ORIGINS'] = 'https://focosa.vercel.app,https://admin.vercel.app'

from main_admin import app

application = app
```

### Step 5: Add Web Apps

Go to **"Web"** tab:

#### Add User API:

1. Click **"Add a new web app"**
2. Choose **"Manual configuration"** → **Python 3.8**
3. Configure:
   - **WSGI Configuration File:** `/home/yourusername/mysite/user_wsgi.py`
   - **Virtualenv:** `/home/yourusername/.virtualenvs/focosa`
   - **Working Directory:** `/home/yourusername/mysite`

4. Reload the web app
5. Note the URL: `yourusername.pythonanywhere.com`

#### Add Admin API:

1. Click **"Add another web app"**
2. **Important:** Choose **different domain** if available
   - Or use subfolder: `/mysite/admin`
3. Same WSGI setup but use `admin_wsgi.py`
4. If same domain, add path: `/admin`

### Step 6: Update Virtualenv and Packages

In **Bash console**:

```bash
workon focosa
cd /home/yourusername/mysite
pip install fastapi uvicorn passlib python-jose pydantic requests
```

### Step 7: Keep-Alive Task (Important!)

Go to **"Tasks"** tab and create a **Scheduled Task**:

**Run daily at 3:00 AM:**
```bash
curl https://yourusername.pythonanywhere.com/health
curl https://yourusername.pythonanywhere.com/admin/health
```

Or run in Python:

```python
import requests

try:
    requests.get("https://yourusername.pythonanywhere.com/health")
    requests.get("https://yourusername.pythonanywhere.com/admin/health")
    print("Keep-alive pings sent")
except:
    pass
```

### Step 8: Test Your APIs

Visit in browser:
```
https://yourusername.pythonanywhere.com/docs
https://yourusername.pythonanywhere.com/health
```

✅ Should see Swagger documentation and health status

---

## Part 2: Deploy Frontend to Vercel

Same as before! (See VERCEL_RENDER_DEPLOYMENT.md)

---

## 📋 Your Final URLs

```
Frontend:        https://focosa-hub.vercel.app
User API:        https://yourusername.pythonanywhere.com
Admin API:       https://yourusername.pythonanywhere.com/admin (or separate domain)
API Docs:        https://yourusername.pythonanywhere.com/docs
Health Check:    https://yourusername.pythonanywhere.com/health
```

---

## 🔄 Keep-Alive on PythonAnywhere

PythonAnywhere keeps free tier apps online, BUT:
- ✅ Apps pause after 3 months of inactivity
- ✅ First request takes 5-10 seconds (warm-up)
- ⚠️ Not ideal for high-traffic apps

**Solution: Use Scheduled Tasks**

Go to **"Tasks"** and schedule:
```bash
# Run every 6 hours
curl https://yourusername.pythonanywhere.com/health
```

This keeps your app active!

---

## ⚠️ PythonAnywhere Limitations

| Feature | Free | Paid |
|---------|------|------|
| Web Apps | 1 | Unlimited |
| Storage | 512MB | 10GB+ |
| Bandwidth | 100MB/day | Unlimited |
| Always-on | No | Yes |
| Custom Domain | No | Yes |
| Database | SQLite only | MySQL/PostgreSQL |
| SSL | ✅ Free | ✅ Free |

---

## 🚀 If You Need More Power

**Upgrade to Paid:**
- **$5/month** - Extra resources
- **$20/month** - Always-on, unlimited bandwidth
- **$50/month** - Enterprise features

Or stick with **Render** (better for heavy traffic)!

---

## 🔧 Troubleshooting PythonAnywhere

### Issue: 502 Bad Gateway

**Solution:**
1. Go to "Web" tab
2. Check if web app is listed
3. Click to reload it
4. Check error log in "Files" → "var/log"

### Issue: Module not found (e.g., fastapi)

**Solution:**
1. Make sure virtualenv is created
2. Activate it: `workon focosa`
3. Install: `pip install fastapi uvicorn`
4. Reload web app

### Issue: Cannot connect to database

**Solution:**
1. Check database file path is correct
2. File should be in `/home/yourusername/mysite/`
3. Check permissions: should be readable/writable

### Issue: CORS errors

**Solution:**
1. Update WSGI file with correct ALLOWED_ORIGINS
2. Reload web app
3. Clear browser cache

---

## 📱 Static Files / Static Website

If you want to serve HTML from PythonAnywhere:

1. Create `/mysite/static/` folder
2. Put HTML files there
3. Configure in WSGI:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="/home/yourusername/mysite/static", html=True), name="static")
```

---

## Comparison: Render vs PythonAnywhere

| Feature | Render | PythonAnywhere |
|---------|--------|---|
| **Keep-Alive Required** | ✅ Included in code | ⚠️ Need scheduled task |
| **Free Plan** | ✅ Good | ✅ Very limited |
| **Paid Plan Cost** | $7/month | $5/month |
| **Ease of Deployment** | ✅ One-click (GitHub) | ⚠️ Manual upload |
| **Database Persistence** | ✅ Yes | ✅ Yes |
| **Auto-Redeploy on Push** | ✅ Yes | ❌ No |
| **Uptime SLA** | 99.9% | Best effort |
| **Recommended For** | Modern apps | Legacy apps |

---

## 📝 Summary

**To deploy on PythonAnywhere:**

1. ✅ Create account (free)
2. ✅ Upload code via Files
3. ✅ Create virtual environment
4. ✅ Create WSGI files
5. ✅ Add web apps (1-2)
6. ✅ Schedule keep-alive task
7. ✅ Reload web apps
8. ✅ Test at `/docs`

**Takes ~30 minutes once you understand the steps!**

---

## Next: Deploy Frontend to Vercel

See **VERCEL_RENDER_DEPLOYMENT.md** Part 2

Your FOCOSA Hub will be online 24/7! 🎉
