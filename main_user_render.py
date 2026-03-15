# FOCOSA Hub - Vercel Frontend + Render/PythonAnywhere Backend

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│  VERCEL (Frontend - Static Files)    │
│  URL: focosa.vercel.app              │
│  - focosa-connected.html (User)      │
│  - focosa-admin.html (Admin)         │
└───────────────┬──────────────────────┘
                │ API Calls
                ▼
        ┌───────────────────────┐
        │   Render (Backend)    │
        │   URL: focosa.onrender.com
        │   - main_user.py      │
        │   - main_admin.py     │
        │   - focosa.db         │
        └───────────────────────┘
```

---

## Option 1: RENDER (Recommended) ⭐

Render automatically keeps your free tier app alive!

### Step 1: Prepare Backend for Render

#### Update main_user.py
Add this at the TOP of the file (after imports):

```python
# ✅ ADD THIS - KEEP RENDER ALWAYS ACTIVE
import threading
import requests
import time

# Keep-Alive Function
def keep_alive():
    """Keep the app alive by pinging it every 30 minutes"""
    while True:
        try:
            # Get the URL from environment or use localhost
            app_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
            requests.get(f"{app_url}/health", timeout=5)
            print(f"✅ Keep-alive ping sent at {datetime.now()}")
        except Exception as e:
            print(f"⚠️  Keep-alive ping failed: {e}")
        time.sleep(1800)  # Ping every 30 minutes

# Start keep-alive thread
def start_keep_alive():
    if os.getenv("ENVIRONMENT") == "production":
        thread = threading.Thread(target=keep_alive, daemon=True)
        thread.start()
```

#### Add Health Check Endpoint (after other endpoints)

```python
# ─────────────────────────────────────────────────────────
# ROUTES — HEALTH CHECK (For Keep-Alive)
# ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring and keep-alive"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "FOCOSA User API"
    }
```

#### Update Main Entry Point

```python
if __name__ == "__main__":
    import uvicorn
    init_db()
    
    # Start keep-alive in production
    start_keep_alive()
    
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 FOCOSA Hub USER API starting on port {port}")
    print(f"📚 Swagger docs:  http://localhost:{port}/docs")
    print(f"🔑 Default admin: admin@focosa.edu.ng / admin123")
    uvicorn.run("main_user:app", host="0.0.0.0", port=port, reload=False)
```

#### Do Same for main_admin.py

Add the same keep-alive code and health check endpoint.

---

### Step 2: Update CORS for Vercel

In **both** main_user.py and main_admin.py, update the CORS middleware:

```python
# OLD (Allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NEW (Specific to Vercel)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://localhost:8001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Step 3: Deploy to Render

#### Create Render Services

**Service 1: User API**

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   ```
   Name: focosa-user
   Environment: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: python main_user.py
   Plan: Free
   ```
5. Environment Variables:
   ```
   SECRET_KEY = your-secret-key-here
   PORT = 8000
   ENVIRONMENT = production
   ALLOWED_ORIGINS = https://focosa.vercel.app,https://admin.vercel.app,http://localhost:3000
   ```
6. Click "Create Web Service"

**Service 2: Admin API**

1. Click "New +" → "Web Service"
2. Same as above but:
   ```
   Name: focosa-admin
   Start Command: python main_admin.py
   PORT = 8001
   ```

#### Render URLs You'll Get:
- User API: `https://focosa-user.onrender.com`
- Admin API: `https://focosa-admin.onrender.com`

---

## Option 2: PythonAnywhere

### Step 1: Deploy to PythonAnywhere

1. Go to https://www.pythonanywhere.com
2. Sign up (free account available)
3. Go to Web tab
4. Add new web app → Select Flask/Django/etc
5. Upload your files via Files tab

### Step 2: Configure WSGI File

Create `mysite/wsgi.py`:

```python
# PythonAnywhere WSGI configuration
import sys
import os

path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.append(path)

# For User API
from main_user import app as user_app
application = user_app

# Or for Admin API
from main_admin import app as admin_app
application = admin_app
```

### Step 3: Add Keep-Alive Task

PythonAnywhere free tier automatically keeps apps alive, but add this scheduled task:

1. Go to Tasks
2. Create new scheduled task
3. Run daily:
   ```
   curl https://yourusername.pythonanywhere.com/health
   ```

---

## ⭐ Option 3: Deploy to BOTH Render (Best Practice)

### Create render.yaml (Infrastructure as Code)

```yaml
services:
  - type: web
    name: focosa-user
    env: python
    pythonVersion: 3.11
    buildCommand: pip install -r requirements.txt
    startCommand: python main_user.py
    envVars:
      - key: SECRET_KEY
        value: your-secret-key-change-this
      - key: PORT
        value: 8000
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_ORIGINS
        value: https://focosa.vercel.app,https://admin.vercel.app

  - type: web
    name: focosa-admin
    env: python
    pythonVersion: 3.11
    buildCommand: pip install -r requirements.txt
    startCommand: python main_admin.py
    envVars:
      - key: SECRET_KEY
        value: your-secret-key-change-this
      - key: PORT
        value: 8001
      - key: ENVIRONMENT
        value: production
      - key: ALLOWED_ORIGINS
        value: https://focosa.vercel.app,https://admin.vercel.app
```

---

## 🎨 Step 4: Deploy Frontend to Vercel

### Option A: Static HTML Files (Simple)

1. Create a GitHub repo
2. Push HTML files:
   ```
   focosa-connected.html → index.html (rename)
   focosa-admin.html → admin.html (rename)
   ```
3. Go to https://vercel.com
4. Import your GitHub repo
5. Deploy → Automatic!

### Option B: React/Next.js Frontend (Advanced)

Create a proper React app:

```bash
npx create-next-app@latest focosa-frontend
cd focosa-frontend
npm install axios
```

#### Create .env.local

```
NEXT_PUBLIC_USER_API=https://focosa-user.onrender.com
NEXT_PUBLIC_ADMIN_API=https://focosa-admin.onrender.com
```

#### Update API calls

```javascript
// pages/index.js
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_USER_API;

export default function Home() {
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL}/departments`)
      .then(res => setDepartments(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      {departments.map(dept => (
        <div key={dept.id}>{dept.name}</div>
      ))}
    </div>
  );
}
```

#### Deploy to Vercel

```bash
npm install -g vercel
vercel
# Follow prompts
```

---

## 🔑 Complete Updated main_user.py with Keep-Alive

```python
"""
FOCOSA Hub — User API (Render Compatible)
==========================================
Run:  python main_user.py
Port: 8000

This version includes keep-alive functionality for Render
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
import os
import threading
import requests
import time

# ─────────────────────────────────────────────────────────
# KEEP-ALIVE CONFIGURATION (Render)
# ─────────────────────────────────────────────────────────
def keep_alive():
    """Keep the app alive by pinging itself every 30 minutes"""
    while True:
        try:
            render_url = os.getenv("RENDER_EXTERNAL_URL")
            if render_url:
                requests.get(f"{render_url}/health", timeout=5)
                print(f"✅ Keep-alive ping sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"⚠️  Keep-alive error: {e}")
        time.sleep(1800)  # 30 minutes

def start_keep_alive():
    """Start keep-alive thread if in production"""
    if os.getenv("ENVIRONMENT") == "production":
        thread = threading.Thread(target=keep_alive, daemon=True)
        thread.start()

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
SECRET_KEY  = os.getenv("SECRET_KEY", "focosa-super-secret-key-change-in-prod")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
DB_PATH     = os.getenv("DB_PATH", "focosa.db")
PORT        = int(os.getenv("PORT", 8000))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS Origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(
    title="FOCOSA Hub User API",
    version="1.0.0",
    description="Public-facing endpoints for students/users"
)

# ─────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name    TEXT    NOT NULL,
        email        TEXT    UNIQUE NOT NULL,
        password     TEXT    NOT NULL,
        matric_number TEXT,
        department   TEXT,
        level        TEXT,
        role         TEXT    NOT NULL DEFAULT 'student',
        is_verified  INTEGER NOT NULL DEFAULT 0,
        is_active    INTEGER NOT NULL DEFAULT 1,
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS departments (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    UNIQUE NOT NULL,
        code         TEXT    UNIQUE NOT NULL,
        hod          TEXT,
        description  TEXT,
        student_count INTEGER DEFAULT 0,
        course_count  INTEGER DEFAULT 0,
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS lecturers (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        email        TEXT,
        department   TEXT,
        position     TEXT,
        office       TEXT,
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        description  TEXT,
        date         TEXT,
        location     TEXT,
        status       TEXT    NOT NULL DEFAULT 'upcoming',
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS announcements (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        content      TEXT    NOT NULL,
        type         TEXT    NOT NULL DEFAULT 'General',
        is_active    INTEGER NOT NULL DEFAULT 1,
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS resources (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        department   TEXT,
        level        TEXT,
        url          TEXT,
        downloads    INTEGER DEFAULT 0,
        uploaded_by  INTEGER REFERENCES users(id),
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS listings (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT    NOT NULL,
        description  TEXT,
        price        REAL    NOT NULL,
        category     TEXT,
        contact      TEXT,
        seller_id    INTEGER REFERENCES users(id),
        seller_name  TEXT,
        status       TEXT    NOT NULL DEFAULT 'pending',
        created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    """)

    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    if row["cnt"] == 0:
        hashed = pwd_ctx.hash("admin123")
        conn.execute("""
            INSERT INTO users (full_name, email, password, role, is_verified)
            VALUES (?, ?, ?, ?, ?)
        """, ("FOCOSA Admin", "admin@focosa.edu.ng", hashed, "admin", 1))

        depts = [
            ("Computer Science",       "CSC", "Prof. Adeyemi",  420, 38),
            ("Software Engineering",   "SEN", "Dr. Okafor",     280, 32),
            ("Cybersecurity",          "CYB", "Dr. Ibrahim",    195, 28),
            ("Information Technology", "IFT", "Prof. Uche",     352, 35),
        ]
        conn.executemany("""
            INSERT OR IGNORE INTO departments (name, code, hod, student_count, course_count)
            VALUES (?, ?, ?, ?, ?)
        """, depts)

        conn.commit()

# ─────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    matric_number: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None

class ListingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    contact: Optional[str] = None

# ─────────────────────────────────────────────────────────
# AUTH UTILITIES
# ─────────────────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2), db: sqlite3.Connection = Depends(get_db)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credential_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credential_exception
    
    user = db.execute("SELECT * FROM users WHERE email=?", (token_data.email,)).fetchone()
    if user is None:
        raise credential_exception
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# ─────────────────────────────────────────────────────────
# HEALTH CHECK (For Keep-Alive)
# ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint - used for keep-alive pings"""
    return {
        "status": "healthy",
        "service": "FOCOSA User API",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT
    }

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "FOCOSA Hub User API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ─────────────────────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────────────────────
@app.post("/auth/register", tags=["Authentication"], status_code=201)
async def register(body: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    """Register a new student/user account"""
    existing = db.execute("SELECT id FROM users WHERE email=?", (body.email,)).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(body.password)
    try:
        cur = db.execute("""
            INSERT INTO users (full_name, email, password, matric_number, department, level, role, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (body.full_name, body.email, hashed_password, body.matric_number, 
              body.department, body.level, "student", 1))
        db.commit()
        return {"id": cur.lastrowid, "message": "Account created successfully", "email": body.email}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Failed to create account")

@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    """Login with email and password"""
    user = db.execute("SELECT * FROM users WHERE email=?", (form_data.username,)).fetchone()
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", tags=["Authentication"])
async def get_me(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user["id"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "matric_number": current_user["matric_number"],
        "department": current_user["department"],
        "level": current_user["level"],
        "role": current_user["role"],
    }

# ─────────────────────────────────────────────────────────
# ROUTES — DEPARTMENTS (Public)
# ─────────────────────────────────────────────────────────
@app.get("/departments", tags=["Academic"])
async def list_departments(db: sqlite3.Connection = Depends(get_db)):
    """Get all departments"""
    rows = db.execute("SELECT id, name, code, hod, student_count, course_count FROM departments ORDER BY name").fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — LECTURERS (Public)
# ─────────────────────────────────────────────────────────
@app.get("/lecturers", tags=["Academic"])
async def list_lecturers(db: sqlite3.Connection = Depends(get_db)):
    """Get all lecturers"""
    rows = db.execute("SELECT id, name, email, department, position, office FROM lecturers ORDER BY name").fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — EVENTS (Public)
# ─────────────────────────────────────────────────────────
@app.get("/events", tags=["Events"])
async def list_events(limit: int = 50, db: sqlite3.Connection = Depends(get_db)):
    """Get upcoming events"""
    rows = db.execute("""
        SELECT id, title, description, date, location, status 
        FROM events 
        WHERE status IN ('upcoming', 'ongoing')
        ORDER BY date ASC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — ANNOUNCEMENTS (Public)
# ─────────────────────────────────────────────────────────
@app.get("/announcements", tags=["Announcements"])
async def list_announcements(limit: int = 50, db: sqlite3.Connection = Depends(get_db)):
    """Get all active announcements"""
    rows = db.execute("""
        SELECT id, title, content, type, created_at 
        FROM announcements 
        WHERE is_active=1 
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — RESOURCES (Public)
# ─────────────────────────────────────────────────────────
@app.get("/resources", tags=["Resources"])
async def list_resources(department: Optional[str] = None, level: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    """Get study resources"""
    query = "SELECT id, title, department, level, downloads, created_at FROM resources WHERE 1=1"
    params = []
    
    if department:
        query += " AND department=?"
        params.append(department)
    if level:
        query += " AND level=?"
        params.append(level)
    
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — MARKETPLACE (Public Browse)
# ─────────────────────────────────────────────────────────
@app.get("/listings", tags=["Marketplace"])
async def list_listings(category: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    """Get approved marketplace listings"""
    if category:
        rows = db.execute("""
            SELECT id, title, description, price, category, seller_name, created_at 
            FROM listings 
            WHERE status='approved' AND category=?
            ORDER BY created_at DESC
        """, (category,)).fetchall()
    else:
        rows = db.execute("""
            SELECT id, title, description, price, category, seller_name, created_at 
            FROM listings 
            WHERE status='approved'
            ORDER BY created_at DESC
        """).fetchall()
    return [dict(r) for r in rows]

@app.post("/listings", tags=["Marketplace"], status_code=201)
async def create_listing(body: ListingCreate, current_user = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Create a new marketplace listing (requires login)"""
    cur = db.execute("""
        INSERT INTO listings (title, description, price, category, contact, seller_id, seller_name, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (body.title, body.description, body.price, body.category, body.contact, 
          current_user["id"], current_user["full_name"], "pending"))
    db.commit()
    return {
        "id": cur.lastrowid,
        "message": "Listing submitted for review",
        "status": "pending"
    }

# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    init_db()
    
    # Start keep-alive in production
    start_keep_alive()
    
    print(f"\n{'='*50}")
    print(f"🚀 FOCOSA Hub USER API")
    print(f"{'='*50}")
    print(f"Port: {PORT}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Database: {DB_PATH}")
    print(f"CORS Origins: {ALLOWED_ORIGINS}")
    print(f"\n📚 Swagger Docs: http://localhost:{PORT}/docs")
    print(f"❤️  Health Check: http://localhost:{PORT}/health")
    print(f"\n🔑 Default Admin Credentials:")
    print(f"   Email: admin@focosa.edu.ng")
    print(f"   Password: admin123")
    print(f"{'='*50}\n")
    
    uvicorn.run("main_user:app", host="0.0.0.0", port=PORT, reload=(ENVIRONMENT != "production"))
