"""
FOCOSA Hub — Admin API (FastAPI + SQLite Backend)
====================================================
Run:  python main_admin.py
Port: 8001 (Admin only)

API docs: http://localhost:8001/docs
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
import os

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
SECRET_KEY  = os.getenv("SECRET_KEY", "focosa-super-secret-key-change-in-prod")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
DB_PATH     = "focosa.db"
ADMIN_PORT  = int(os.getenv("ADMIN_PORT", 8001))

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(
    title="FOCOSA Hub Admin API",
    version="1.0.0",
    description="Admin-only endpoints for FOCOSA Hub"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# DATABASE SETUP (Same as main.py)
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
# AUTH UTILITIES (Same as main.py)
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
# ROUTES — AUTH
# ─────────────────────────────────────────────────────────
@app.post("/auth/token", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
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

@app.get("/auth/me", tags=["Auth"])
async def get_me(current_user = Depends(get_current_admin)):
    return current_user

# ─────────────────────────────────────────────────────────
# ROUTES — DEPARTMENTS (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@app.get("/departments", tags=["Departments - Admin"])
async def list_departments(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM departments ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.post("/departments", tags=["Departments - Admin"], status_code=201)
async def create_department(body: DepartmentCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.execute("""
            INSERT INTO departments (name, code, hod, description)
            VALUES (?,?,?,?)
        """, (body.name, body.code.upper(), body.hod, body.description))
        db.commit()
        return {"id": cur.lastrowid, "message": "Department created"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Department name or code already exists")

@app.delete("/departments/{dept_id}", tags=["Departments - Admin"])
async def delete_department(dept_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM departments WHERE id=?", (dept_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — LECTURERS (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@app.get("/lecturers", tags=["Lecturers - Admin"])
async def list_lecturers(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM lecturers ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.post("/lecturers", tags=["Lecturers - Admin"], status_code=201)
async def create_lecturer(body: LecturerCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("""
        INSERT INTO lecturers (name, email, department, position, office)
        VALUES (?,?,?,?,?)
    """, (body.name, body.email, body.department, body.position, body.office))
    db.commit()
    return {"id": cur.lastrowid, "message": "Lecturer added"}

@app.delete("/lecturers/{lec_id}", tags=["Lecturers - Admin"])
async def delete_lecturer(lec_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM lecturers WHERE id=?", (lec_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — EVENTS (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@app.get("/events", tags=["Events - Admin"])
async def list_events(limit: int = 100, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM events ORDER BY date ASC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.post("/events", tags=["Events - Admin"], status_code=201)
async def create_event(body: EventCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("""
        INSERT INTO events (title, description, date, location, status)
        VALUES (?,?,?,?,?)
    """, (body.title, body.description, body.date, body.location, body.status or "upcoming"))
    db.commit()
    return {"id": cur.lastrowid, "message": "Event created"}

@app.delete("/events/{event_id}", tags=["Events - Admin"])
async def delete_event(event_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM events WHERE id=?", (event_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — ANNOUNCEMENTS (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@app.get("/announcements", tags=["Announcements - Admin"])
async def list_announcements(limit: int = 100, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]

@app.post("/announcements", tags=["Announcements - Admin"], status_code=201)
async def create_announcement(body: AnnouncementCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("""
        INSERT INTO announcements (title, content, type, is_active)
        VALUES (?,?,?,?)
    """, (body.title, body.content, body.type, 1 if body.is_active else 0))
    db.commit()
    return {"id": cur.lastrowid, "message": "Announcement published"}

@app.delete("/announcements/{ann_id}", tags=["Announcements - Admin"])
async def delete_announcement(ann_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM announcements WHERE id=?", (ann_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — RESOURCES (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@app.get("/resources", tags=["Resources - Admin"])
async def list_resources(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM resources ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/resources", tags=["Resources - Admin"], status_code=201)
async def create_resource(body: ResourceCreate, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("""
        INSERT INTO resources (title, department, level, url)
        VALUES (?,?,?,?)
    """, (body.title, body.department, body.level, body.url))
    db.commit()
    return {"id": cur.lastrowid, "message": "Resource uploaded"}

@app.delete("/resources/{res_id}", tags=["Resources - Admin"])
async def delete_resource(res_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM resources WHERE id=?", (res_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — MARKETPLACE LISTINGS (ADMIN MODERATION)
# ─────────────────────────────────────────────────────────
@app.get("/listings", tags=["Marketplace - Admin"])
async def list_listings(status: Optional[str] = None, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    if status:
        rows = db.execute("SELECT * FROM listings WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM listings ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.patch("/listings/{listing_id}/approve", tags=["Marketplace - Admin"])
async def approve_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE listings SET status='approved' WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Listing approved"}

@app.patch("/listings/{listing_id}/reject", tags=["Marketplace - Admin"])
async def reject_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE listings SET status='rejected' WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Listing rejected"}

@app.delete("/listings/{listing_id}", tags=["Marketplace - Admin"])
async def delete_listing(listing_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM listings WHERE id=?", (listing_id,))
    db.commit()
    return {"message": "Deleted"}

# ─────────────────────────────────────────────────────────
# ROUTES — ADMIN STATS & USERS
# ─────────────────────────────────────────────────────────
@app.get("/admin/stats", tags=["Admin"])
async def admin_stats(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
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

@app.get("/users", tags=["Users - Admin"])
async def list_users(current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT id, full_name, email, role, is_verified, is_active, created_at FROM users ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@app.delete("/users/{user_id}", tags=["Users - Admin"])
async def delete_user(user_id: int, current_user = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    return {"message": "User deleted"}

# ─────────────────────────────────────────────────────────
# SERVE ADMIN FRONTEND
# ─────────────────────────────────────────────────────────
try:
    app.mount("/", StaticFiles(directory=".", files={"focosa-admin.html": "focosa-admin.html"}), name="admin")
except Exception as e:
    print(f"⚠️  Admin HTML not found: {e}")

# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 FOCOSA Hub ADMIN API starting on http://localhost:{ADMIN_PORT}")
    print(f"📚 Swagger docs:  http://localhost:{ADMIN_PORT}/docs")
    print(f"🔑 Default admin: admin@focosa.edu.ng / admin123")
    uvicorn.run("main_admin:app", host="0.0.0.0", port=ADMIN_PORT, reload=True)
