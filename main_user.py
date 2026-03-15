"""
FOCOSA Hub — User/Student API (FastAPI + SQLite Backend)
==========================================================
Run:  python main_user.py
Port: 8000 (Students/Users only)

API docs: http://localhost:8000/docs
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
USER_PORT   = int(os.getenv("USER_PORT", 8000))

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2  = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(
    title="FOCOSA Hub User API",
    version="1.0.0",
    description="Public-facing endpoints for students/users"
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
    matric_number: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
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
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

# ─────────────────────────────────────────────────────────
# ROUTES — AUTH (Public)
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

@app.patch("/auth/profile", tags=["Authentication"])
async def update_profile(body: UserUpdate, current_user = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Update user profile"""
    updates = []
    params = []
    
    if body.full_name:
        updates.append("full_name=?")
        params.append(body.full_name)
    if body.matric_number:
        updates.append("matric_number=?")
        params.append(body.matric_number)
    if body.department:
        updates.append("department=?")
        params.append(body.department)
    if body.level:
        updates.append("level=?")
        params.append(body.level)
    
    if not updates:
        return {"message": "No updates provided"}
    
    params.append(current_user["id"])
    sql = f"UPDATE users SET {', '.join(updates)} WHERE id=?"
    db.execute(sql, params)
    db.commit()
    
    return {"message": "Profile updated successfully"}

# ─────────────────────────────────────────────────────────
# ROUTES — DEPARTMENTS (Public Read-Only)
# ─────────────────────────────────────────────────────────
@app.get("/departments", tags=["Academic"])
async def list_departments(db: sqlite3.Connection = Depends(get_db)):
    """Get all departments"""
    rows = db.execute("SELECT id, name, code, hod, student_count, course_count FROM departments ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.get("/departments/{dept_id}", tags=["Academic"])
async def get_department(dept_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get department details"""
    row = db.execute("SELECT id, name, code, hod, description, student_count, course_count FROM departments WHERE id=?", (dept_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Department not found")
    return dict(row)

# ─────────────────────────────────────────────────────────
# ROUTES — LECTURERS (Public Read-Only)
# ─────────────────────────────────────────────────────────
@app.get("/lecturers", tags=["Academic"])
async def list_lecturers(department: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    """Get all lecturers, optionally filtered by department"""
    if department:
        rows = db.execute("SELECT id, name, email, department, position, office FROM lecturers WHERE department=? ORDER BY name", 
                         (department,)).fetchall()
    else:
        rows = db.execute("SELECT id, name, email, department, position, office FROM lecturers ORDER BY name").fetchall()
    return [dict(r) for r in rows]

@app.get("/lecturers/{lecturer_id}", tags=["Academic"])
async def get_lecturer(lecturer_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get lecturer details"""
    row = db.execute("SELECT id, name, email, department, position, office FROM lecturers WHERE id=?", (lecturer_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    return dict(row)

# ─────────────────────────────────────────────────────────
# ROUTES — EVENTS (Public Read-Only)
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

@app.get("/events/{event_id}", tags=["Events"])
async def get_event(event_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get event details"""
    row = db.execute("""
        SELECT id, title, description, date, location, status, created_at 
        FROM events WHERE id=?
    """, (event_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return dict(row)

# ─────────────────────────────────────────────────────────
# ROUTES — ANNOUNCEMENTS (Public Read-Only)
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

@app.get("/announcements/{ann_id}", tags=["Announcements"])
async def get_announcement(ann_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get announcement details"""
    row = db.execute("""
        SELECT id, title, content, type, created_at 
        FROM announcements WHERE id=? AND is_active=1
    """, (ann_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return dict(row)

# ─────────────────────────────────────────────────────────
# ROUTES — RESOURCES (Public Read-Only)
# ─────────────────────────────────────────────────────────
@app.get("/resources", tags=["Resources"])
async def list_resources(department: Optional[str] = None, level: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    """Get study resources, optionally filtered by department and level"""
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

@app.get("/resources/{res_id}", tags=["Resources"])
async def get_resource(res_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get resource details and track download"""
    row = db.execute("""
        SELECT id, title, department, level, url, downloads, created_at 
        FROM resources WHERE id=?
    """, (res_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Increment download count
    db.execute("UPDATE resources SET downloads = downloads + 1 WHERE id=?", (res_id,))
    db.commit()
    
    return dict(row)

# ─────────────────────────────────────────────────────────
# ROUTES — MARKETPLACE LISTINGS (Students Only)
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

@app.get("/listings/{listing_id}", tags=["Marketplace"])
async def get_listing(listing_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get listing details"""
    row = db.execute("""
        SELECT id, title, description, price, category, contact, seller_name, created_at 
        FROM listings WHERE id=? AND status='approved'
    """, (listing_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    return dict(row)

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

@app.get("/my-listings", tags=["Marketplace"])
async def get_my_listings(current_user = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    """Get your own listings"""
    rows = db.execute("""
        SELECT id, title, description, price, category, status, created_at 
        FROM listings 
        WHERE seller_id=?
        ORDER BY created_at DESC
    """, (current_user["id"],)).fetchall()
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────────────────
# SERVE STUDENT FRONTEND
# ─────────────────────────────────────────────────────────
try:
    app.mount("/", StaticFiles(directory=".", files={"focosa-connected.html": "focosa-connected.html"}), name="frontend")
except Exception as e:
    print(f"⚠️  User HTML not found: {e}")

# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"🚀 FOCOSA Hub USER API starting on http://localhost:{USER_PORT}")
    print(f"📚 Swagger docs:  http://localhost:{USER_PORT}/docs")
    print(f"📝 Register endpoint: POST /auth/register")
    uvicorn.run("main_user:app", host="0.0.0.0", port=USER_PORT, reload=True)
