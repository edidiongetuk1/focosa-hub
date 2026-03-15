# FOCOSA Hub - Architecture & Comparison Guide

## 📊 Your Setup: Separate Applications (No Routing)

You now have a **dual-service architecture** where:
- Admin and User interfaces run as **completely independent applications**
- They communicate with the same database
- No internal routing between them
- Can be deployed on different servers/containers
- Can be scaled independently

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED DATABASE                           │
│                  (focosa.db with WAL)                        │
└──────────┬──────────────────────────────┬────────────────────┘
           │                              │
           ↓                              ↓
    ┌─────────────────┐          ┌──────────────────┐
    │   USER API      │          │   ADMIN API      │
    │   Port 8000     │          │   Port 8001      │
    ├─────────────────┤          ├──────────────────┤
    │ FastAPI Server  │          │ FastAPI Server   │
    │                 │          │                  │
    │ • Register      │          │ • Dashboard      │
    │ • Login         │          │ • Manage Users   │
    │ • View Content  │          │ • Create Events  │
    │ • Marketplace   │          │ • Upload Content │
    │ • Resources     │          │ • Moderate Items │
    └────────┬────────┘          └────────┬─────────┘
             │                            │
             ↓                            ↓
    ┌──────────────────┐      ┌──────────────────┐
    │  focosa-         │      │  focosa-         │
    │  connected.html  │      │  admin.html      │
    │  (Frontend)      │      │  (Frontend)      │
    └──────────────────┘      └──────────────────┘
             │                            │
             ↓                            ↓
    http://localhost:8000    http://localhost:8001
```

---

## 📈 Comparison: Different Approaches

### Option 1: Separate Apps (YOUR CHOICE) ✅

```
main_user.py     main_admin.py
     ↓                ↓
  Port 8000      Port 8001
     ↓                ↓
  [User Endpoints]  [Admin Endpoints]
     ↓                ↓
  Same Database   Same Database
```

**Advantages:**
- ✅ Complete separation of concerns
- ✅ Can deploy independently
- ✅ No routing overhead
- ✅ Easy to scale differently
- ✅ Can use different tech stacks later
- ✅ Better security (separate instances)
- ✅ Easy to maintain

**Disadvantages:**
- ⚠️ Slight code duplication (shared auth logic)
- ⚠️ Must manage 2 services
- ⚠️ Need to sync code updates

**Best For:**
- Large teams
- Microservices architecture
- Different deployment needs
- High-traffic applications

---

### Option 2: Single App with Routing (Alternative)

```
main.py
   ↓
[Router A: /user/*]  ←→  [User Endpoints]
[Router B: /admin/*] ←→  [Admin Endpoints]
   ↓
Port 8000
```

**Advantages:**
- ✅ One codebase to maintain
- ✅ Single deployment
- ✅ Easier initial setup

**Disadvantages:**
- ⚠️ Cannot scale independently
- ⚠️ Admin features run on same instance as user
- ⚠️ More complex code
- ⚠️ More routing overhead
- ⚠️ Single point of failure

**Best For:**
- Small applications
- Initial MVP
- Limited resources

---

### Option 3: Microservices with Message Queue (Advanced)

```
[Message Queue: RabbitMQ/Redis]
         ↓
    ┌────┴────┐
    ↓         ↓
User Service  Admin Service
  Port 8000    Port 8001
    ↓         ↓
[Shared DB]  [Shared DB]
```

**Advantages:**
- ✅ Perfect decoupling
- ✅ Can scale infinitely
- ✅ Handle high load

**Disadvantages:**
- ⚠️ Complex infrastructure
- ⚠️ Requires DevOps experience
- ⚠️ Overkill for most projects

**Best For:**
- Enterprise applications
- High-traffic systems
- Complex workflows

---

## 🔄 Data Flow Examples

### User Registers (Port 8000)
```
1. POST /auth/register (User API)
2. Hash password
3. Insert into users table
4. Return success
5. Both User & Admin can see the user
```

### Admin Creates Event (Port 8001)
```
1. POST /events (Admin API - requires admin login)
2. Validate admin credentials
3. Insert into events table
4. Return event ID
5. User API immediately sees event via /events GET
```

### User Creates Marketplace Listing (Port 8000)
```
1. POST /listings (User API - requires user login)
2. Insert with status='pending'
3. Return listing ID
4. Admin API can see pending listings
5. Admin approves: PATCH /listings/{id}/approve (Port 8001)
6. User API shows approved listings
```

---

## 🔐 Security Architecture

### Authentication Flow

```
User API (Port 8000)
└─ Student/User Login
   └─ JWT Token Created
   └─ Token stored in browser
   └─ Used for /listings, /profile, etc.

Admin API (Port 8001)
└─ Admin Login (Requires role='admin' in users table)
   └─ JWT Token Created (different from user tokens)
   └─ Token stored in browser
   └─ Used for management endpoints
   └─ All endpoints check for role='admin'
```

### Database Security
- WAL mode prevents concurrent write conflicts
- Each app can write independently
- Foreign key constraints enforced
- Role-based access control

---

## 🚀 Deployment Scenarios

### Scenario 1: Local Development
```
Terminal 1: python main_user.py
Terminal 2: python main_admin.py
Database: ./focosa.db (local)
```

### Scenario 2: Docker (Same Server)
```
docker-compose.yml
├─ Service: focosa-user (port 8000)
├─ Service: focosa-admin (port 8001)
└─ Volume: focosa.db (shared)
```

### Scenario 3: Different Servers
```
Server A (Production):
  └─ main_user.py → focosa-user.example.com
  
Server B (Production):
  └─ main_admin.py → admin.focosa.example.com
  
Database Server:
  └─ focosa.db (on NFS or cloud storage)
```

### Scenario 4: Kubernetes
```
Deployment: focosa-user
  └─ Replicas: 3-5 (auto-scale)
  └─ Port: 8000
  
Deployment: focosa-admin
  └─ Replicas: 1-2
  └─ Port: 8001
  
PersistentVolume: focosa.db
  └─ Shared across all pods
```

---

## 📊 Performance Considerations

### Single Server (Docker Compose)
```
Resources per service:
├─ CPU: ~100-200m each
├─ Memory: ~128-256MB each
├─ Disk: ~100MB (database)
└─ Total: ~500MB RAM, ~200m CPU
```

### Multiple Servers
```
Server 1 (User API):
├─ 2+ CPU cores
├─ 2GB+ RAM
└─ Network connection to database

Server 2 (Admin API):
├─ 1+ CPU core
├─ 1GB+ RAM
└─ Network connection to database

Database Server:
├─ 4+ CPU cores
├─ 4GB+ RAM
└─ SSD storage for better performance
```

### Scaling
```
User API: Can scale to 10+ instances
Admin API: Usually 1-2 instances enough

Load balancer routes:
├─ focosa.example.com → 10 user instances
└─ admin.focosa.example.com → 1-2 admin instances
```

---

## 📈 Database Design Notes

### Shared Database Benefits
- Single source of truth
- No data replication
- Consistency guaranteed
- Lower storage costs

### Potential Issues
- Concurrent write conflicts (solved by WAL mode)
- Network latency if database is remote
- Backup complexity (backup once, used by both)

### WAL Mode Explanation
```
Traditional Mode:
Write → Database
↓
Fast but risky

WAL Mode (Write-Ahead Logging):
Write → WAL File → Database
↓
Safe and concurrent
Multiple readers + 1 writer simultaneously
```

---

## 🔧 Maintenance Tasks

### Regular Backups
```bash
# Daily backup
cp focosa.db /backups/focosa-$(date +%Y%m%d).db

# Keep last 7 days
find /backups -name "focosa-*.db" -mtime +7 -delete
```

### Database Optimization
```bash
# Weekly: Vacuum database
sqlite3 focosa.db VACUUM;

# Monitor database size
du -sh focosa.db

# Check integrity
sqlite3 focosa.db PRAGMA integrity_check;
```

### Log Management
```bash
# View logs
journalctl -u focosa-user -f
journalctl -u focosa-admin -f

# Rotate logs
logrotate /etc/logrotate.d/focosa
```

---

## 🎯 Migration Path

### Phase 1: Development (Current)
- Two separate apps
- Local database
- Docker Compose for testing

### Phase 2: Production (Next)
- Deploy user API to production
- Deploy admin API to separate server
- Use cloud database or managed SQLite
- Set up load balancer

### Phase 3: Scale (Future)
- Multiple user API instances
- Auto-scaling based on load
- Redis cache for performance
- Separate analytics database

### Phase 4: Enterprise (Advanced)
- Kubernetes orchestration
- Microservices per domain
- Event-driven architecture
- CQRS pattern

---

## 📞 Making Your Choice

**Use Separate Apps If:**
- ✅ Planning to scale user and admin independently
- ✅ Want different security models
- ✅ Plan different tech stacks in future
- ✅ Have large team working on it
- ✅ Want complete separation

**Use Single App With Routing If:**
- ⚠️ Building MVP
- ⚠️ Very small team
- ⚠️ Limited resources
- ⚠️ Simple requirements

**YOU CHOSE:** Separate Apps → Best for growing applications! ✅

---

## 🎓 Next Steps

1. **Read:** QUICKSTART.md (5 minutes)
2. **Test:** Run both apps locally
3. **Deploy:** Follow DEPLOYMENT_GUIDE.md
4. **Monitor:** Set up logging and monitoring
5. **Scale:** Add more user instances as needed

---

## 📚 Additional Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- Docker Docs: https://docs.docker.com
- SQLite Documentation: https://sqlite.org/docs.html
- JWT Tokens: https://jwt.io
