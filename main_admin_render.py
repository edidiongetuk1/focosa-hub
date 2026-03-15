"""
FOCOSA Hub — Admin API (Render Compatible)
============================================
Run:  python main_admin.py
Port: 8001

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
PORT        = int(os.getenv("PORT", 8001))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS Origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8001"
).split(",")

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(
    title="FOCOSA Hub Admin API",
    version="1.0.0",
    description="Admin-only endpoints for FOCOSA Hub"
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

class DepartmentCreate(BaseModel):
    name: str
    code: str
    hod: Optional[str] = None
    description: Optional[str] = None

class LecturerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    office: Optional[str] = None

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    type: Optional[str] = "General"
    is_active: bool = True

class ResourceCreate(BaseModel):
    title: str
    department: Optional[str] = None
    level: Optional[str] = None
    url: Optional[str] = None

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
    return user

async def get_current_admin(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

# ─────────────────────────────────────────────────────────
# HEALTH CHECK (For Keep-Alive)
# ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint - used for keep-alive pings"""
    return {
        "status": "healthy",
        "service": "FOCOSA Admin API",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT
    }

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "FOCOSA Hub Admin API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ─────────────────────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────────────────────
@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    """Admin login - requires admin role"""
    user = db.execute("SELECT * FROM users WHERE email=?", (form_data.username,)).fetchone()
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", tags=["Authentication"])
async def get_me(current_user = Depends(get_current_admin)):
    """Get current admin profile"""
    return current_user

# ─────────────────────────────────────────────────────────
# ROUTES — ADMIN STATS
# ─────────────────────────────────────────────────────────
@app.get("/admin/stats", tags=["Admin Dashboard"])
async def admin_stats(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get admin dashboard statistics"""
    def count(table, where=""):
        sql = f"SELECT COUNT(*) as cnt FROM {table}"
        if where: sql += f" WHERE {where}"
        return db.execute(sql).fetchone()["cnt"]
    return {
        "users":         count("users"),
        "departments":   count("departments"),
        "lecturers":     count("lecturers"),
        "events":        count("events"),
        "announcements": count("announcements"),
        "resources":     count("resources"),
        "listings":      count("listings"),
        "pending_listings": count("listings", "status='pending'"),
    }

@app.get("/users", tags=["Users Management"])
async def list_users(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all users"""
    rows = db.execute("SELECT id, full_name, email, role, is_verified, is_active, created_at FROM users ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# ROUTES — DEPARTMENTS
# ─────────────────────────────────────────────────────────
@app.get("/departments", tags=["Departments"])
async def list_departments(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all departments"""
    rows = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.post("/departments", tags=["Departments"], status_code=201)
async def create_department(body: DepartmentCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Create a new department"""
    try:
        cur = db.execute("""
            INSERT INTO departments (name, code, hod, description)
            VALUES (?,?,?,?)
        """, (body.name, body.code.upper(), body.hod, body.description))
        db.commit()
        return {"id": cur.lastrowid, "message": "Department created"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Department name or code already exists")

@app.delete("/departments/{dept_id}", tags=["Departments"])
async def delete_department(dept_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete a department"""
    db.execute("DELETE FROM departments WHERE id=?", (dept_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — LECTURERS
# ─────────────────────────────────────────────────────────
@app.get("/lecturers", tags=["Lecturers"])
async def list_lecturers(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all lecturers"""
    rows = db.execute("SELECT * FROM lecturers ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.post("/lecturers", tags=["Lecturers"], status_code=201)
async def create_lecturer(body: LecturerCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Add a new lecturer"""
    cur = db.execute("""
        INSERT INTO lecturers (name, email, department, position, office)
        VALUES (?,?,?,?,?)
    """, (body.name, body.email, body.department, body.position, body.office))
    db.commit()
    return {"id": cur.lastrowid, "message": "Lecturer added"}

@app.delete("/lecturers/{lec_id}", tags=["Lecturers"])
async def delete_lecturer(lec_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete a lecturer"""
    db.execute("DELETE FROM lecturers WHERE id=?", (lec_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — EVENTS
# ─────────────────────────────────────────────────────────
@app.get("/events", tags=["Events"])
async def list_events(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all events"""
    rows = db.execute("SELECT * FROM events ORDER BY date ASC").fetchall()
    return [dict(r) for r in rows]

@app.post("/events", tags=["Events"], status_code=201)
async def create_event(body: EventCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Create a new event"""
    cur = db.execute("""
        INSERT INTO events (title, description, date, location, status)
        VALUES (?,?,?,?,?)
    """, (body.title, body.description, body.date, body.location, body.status or "upcoming"))
    db.commit()
    return {"id": cur.lastrowid, "message": "Event created"}

@app.delete("/events/{event_id}", tags=["Events"])
async def delete_event(event_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete an event"""
    db.execute("DELETE FROM events WHERE id=?", (event_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — ANNOUNCEMENTS
# ─────────────────────────────────────────────────────────
@app.get("/announcements", tags=["Announcements"])
async def list_announcements(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all announcements"""
    rows = db.execute("SELECT * FROM announcements ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/announcements", tags=["Announcements"], status_code=201)
async def create_announcement(body: AnnouncementCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Create a new announcement"""
    cur = db.execute("""
        INSERT INTO announcements (title, content, type, is_active)
        VALUES (?,?,?,?)
    """, (body.title, body.content, body.type, 1 if body.is_active else 0))
    db.commit()
    return {"id": cur.lastrowid, "message": "Announcement published"}

@app.delete("/announcements/{ann_id}", tags=["Announcements"])
async def delete_announcement(ann_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete an announcement"""
    db.execute("DELETE FROM announcements WHERE id=?", (ann_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — RESOURCES
# ─────────────────────────────────────────────────────────
@app.get("/resources", tags=["Resources"])
async def list_resources(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all resources"""
    rows = db.execute("SELECT * FROM resources ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/resources", tags=["Resources"], status_code=201)
async def create_resource(body: ResourceCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Upload a new resource"""
    cur = db.execute("""
        INSERT INTO resources (title, department, level, url)
        VALUES (?,?,?,?)
    """, (body.title, body.department, body.level, body.url))
    db.commit()
    return {"id": cur.lastrowid, "message": "Resource uploaded"}

@app.delete("/resources/{res_id}", tags=["Resources"])
async def delete_resource(res_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete a resource"""
    db.execute("DELETE FROM resources WHERE id=?", (res_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — MARKETPLACE MODERATION
# ─────────────────────────────────────────────────────────
@app.get("/listings", tags=["Marketplace"])
async def list_listings(status: Optional[str] = None, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Get all marketplace listings"""
    if status:
        rows = db.execute("SELECT * FROM listings WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM listings ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.patch("/listings/{listing_id}/approve", tags=["Marketplace"])
async def approve_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Approve a marketplace listing"""
    db.execute("UPDATE listings SET status='approved' WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Listing approved"}

@app.patch("/listings/{listing_id}/reject", tags=["Marketplace"])
async def reject_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Reject a marketplace listing"""
    db.execute("UPDATE listings SET status='rejected' WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Listing rejected"}

@app.delete("/listings/{listing_id}", tags=["Marketplace"])
async def delete_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    """Delete a marketplace listing"""
    db.execute("DELETE FROM listings WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    init_db()
    
    # Start keep-alive in production
    start_keep_alive()
    
    print(f"\n{'='*50}")
    print(f"🚀 FOCOSA Hub ADMIN API")
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
    
    uvicorn.run("main_admin:app", host="0.0.0.0", port=PORT, reload=(ENVIRONMENT != "production"))
