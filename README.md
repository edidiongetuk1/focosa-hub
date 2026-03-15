# FOCOSA Hub - Separate Admin & User Hosting

## 🎯 What You Get

You now have **two completely separate applications** that can be hosted independently:

| Component | Details |
|-----------|---------|
| **main_user.py** | Student/User API (Port 8000) |
| **main_admin.py** | Admin Dashboard API (Port 8001) |
| **focosa.db** | Shared SQLite database |
| **No Routing** | No internal request routing ✅ |
| **Independent** | Can deploy on different servers |

---

## 📁 Files Generated

```
├── main_user.py                    # User/Student API application
├── main_admin.py                   # Admin API application
├── docker-compose.yml              # Docker Compose configuration
├── Dockerfile.user                 # Docker image for user API
├── Dockerfile.admin                # Docker image for admin API
├── .env.template                   # Environment variables template
│
├── QUICKSTART.md                   # 5-minute quick start guide ⭐ START HERE
├── DEPLOYMENT_GUIDE.md             # Complete deployment instructions
├── ARCHITECTURE.md                 # Technical architecture overview
├── SYSTEMD_SETUP.md               # Linux systemd service setup
│
└── requirements.txt               # Python dependencies (unchanged)
```

---

## 🚀 Quick Start (Choose One)

### 1️⃣ Local Development (Easiest)
```bash
# Terminal 1
python main_user.py

# Terminal 2
python main_admin.py
```
**Access:**
- User: http://localhost:8000
- Admin: http://localhost:8001

⏱️ **Time:** 2 minutes

---

### 2️⃣ Docker (Most Professional)
```bash
docker-compose up -d
```

⏱️ **Time:** 3 minutes (after Docker install)

---

### 3️⃣ Linux Server (Production)
Follow `SYSTEMD_SETUP.md` for systemd service configuration

⏱️ **Time:** 15 minutes

---

## 🔐 Default Admin Credentials

```
Email:    admin@focosa.edu.ng
Password: admin123
```

⚠️ **Change this immediately in production!**

---

## 📊 Key Differences From Original

### Original (Single App)
```
main.py
  ├─ /admin/* routes  → Admin endpoints
  └─ /* routes       → User endpoints
  
Port: 8000 (everything)
Limitation: Cannot separate deployments
```

### New (Two Apps) ✨
```
main_admin.py        main_user.py
  │                    │
  ├─ Admin endpoints   ├─ User endpoints
  ├─ All admin routes  ├─ All user routes
  └─ Requires admin    └─ No admin needed
  
Ports: 8001 (admin)   8000 (user)
Benefit: Complete separation
```

---

## 🎯 Why Separate Apps?

**Advantages:**
1. ✅ **Scale Independently** - Add 10 user instances, keep 1 admin
2. ✅ **Deploy Separately** - Update user code without touching admin
3. ✅ **Better Security** - Isolate admin interface
4. ✅ **Different Hosts** - Admin in internal network, users on cloud
5. ✅ **No Routing Overhead** - Direct endpoints, no filtering
6. ✅ **Easier Testing** - Each app has its own test suite
7. ✅ **Future-Proof** - Easy to add microservices later

---

## 📈 Next Steps

### Step 1: Read Documentation
1. Start with **QUICKSTART.md** (5 minutes)
2. Review **ARCHITECTURE.md** if you want details
3. Check **DEPLOYMENT_GUIDE.md** for your hosting option

### Step 2: Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run both apps
python main_user.py  # Terminal 1
python main_admin.py # Terminal 2
```

### Step 3: Deploy
Choose your hosting platform:
- **Render.com** - Easiest
- **Railway** - Fast
- **Docker** - Most flexible
- **Linux Server** - Most control
- **AWS/GCP/Azure** - Enterprise

See DEPLOYMENT_GUIDE.md for step-by-step instructions.

---

## 🏗️ Architecture at a Glance

```
┌──────────────────────────────────────────┐
│         SHARED DATABASE (focosa.db)      │
│  Departments, Users, Events, Resources   │
└─────────┬────────────────────────┬───────┘
          │                        │
   ┌──────▼─────────┐    ┌─────────▼──────┐
   │   USER API     │    │  ADMIN API     │
   │   Port 8000    │    │  Port 8001     │
   ├────────────────┤    ├────────────────┤
   │ • Register     │    │ • Dashboard    │
   │ • Login        │    │ • Manage all   │
   │ • Browse       │    │ • Create/Edit  │
   │ • Marketplace  │    │ • Approve      │
   └────────────────┘    └────────────────┘
         │                       │
    Student                   Admin
    Portal                   Portal
```

---

## ⚙️ Configuration

### Environment Variables
Create `.env` file:
```bash
cp .env.template .env
# Edit .env with your values
```

**Key Variables:**
- `SECRET_KEY` - JWT secret (change for production!)
- `USER_PORT` - Port for user API (default 8000)
- `ADMIN_PORT` - Port for admin API (default 8001)
- `DB_PATH` - Path to database (default ./focosa.db)

---

## 📝 API Endpoints

### User API (8000)
```
POST   /auth/register              Register new account
POST   /auth/token                 Login
GET    /departments                View departments
GET    /lecturers                  View lecturers
GET    /events                     View events
GET    /announcements              View announcements
GET    /resources                  View resources
GET    /listings                   Browse marketplace
POST   /listings                   Create listing
```

### Admin API (8001)
```
POST   /auth/token                 Admin login
GET    /admin/stats                Dashboard statistics
GET    /users                      List all users
POST   /departments                Create department
POST   /events                     Create event
POST   /announcements              Create announcement
POST   /resources                  Upload resource
PATCH  /listings/{id}/approve      Approve marketplace item
PATCH  /listings/{id}/reject       Reject marketplace item
```

Full documentation at:
- http://localhost:8000/docs (User API)
- http://localhost:8001/docs (Admin API)

---

## 🐛 Common Issues

### Port Already in Use
```bash
# Find and kill process
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Database Lock Error
```bash
# Remove lock files
rm -f focosa.db-shm focosa.db-wal
```

### Import Errors
```bash
pip install -r requirements.txt --break-system-packages
```

### CORS Issues
Update `allow_origins` in the FastAPI middleware of both apps

---

## 💡 Pro Tips

1. **Use environment files** - Don't hardcode secrets
2. **Monitor both services** - Use systemd or Docker logging
3. **Backup database** - Regular backups of focosa.db
4. **Use HTTPS** - Always in production
5. **Rate limiting** - Add to protect APIs
6. **Logging** - Enable detailed logging for debugging

---

## 🎓 Learning Path

### Beginner
1. Read QUICKSTART.md
2. Run locally with two terminals
3. Test both apps in browser

### Intermediate
1. Read ARCHITECTURE.md
2. Set up with Docker Compose
3. Deploy to Render.com or Railway

### Advanced
1. Read DEPLOYMENT_GUIDE.md (full section)
2. Set up on Linux server with systemd
3. Configure nginx reverse proxy
4. Set up monitoring and backups

---

## 🔗 Important Links

- **FastAPI:** https://fastapi.tiangolo.com
- **Uvicorn:** https://www.uvicorn.org
- **SQLite:** https://www.sqlite.org
- **Docker:** https://www.docker.com
- **JWT:** https://jwt.io

---

## ✅ Checklist for Production

- [ ] Change default admin password
- [ ] Update SECRET_KEY in environment
- [ ] Set specific CORS origins (not `["*"]`)
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Set up logging (Sentry, DataDog, etc.)
- [ ] Load test both services
- [ ] Document any customizations
- [ ] Create runbooks for common tasks

---

## 📞 Support & Help

### For Setup Issues
1. Check QUICKSTART.md troubleshooting section
2. Review API docs at `/docs` endpoints
3. Check application logs in terminal or systemd journals

### For Deployment Issues
1. Consult DEPLOYMENT_GUIDE.md for your platform
2. Check docker-compose logs
3. Verify firewall and port settings

### For Feature Development
1. Modify main_user.py or main_admin.py
2. Test changes locally first
3. Deploy to staging before production

---

## 🎉 You're All Set!

Your FOCOSA Hub project is now ready for:
- ✅ Local development
- ✅ Docker containerization
- ✅ Cloud deployment
- ✅ Independent scaling
- ✅ Production use

**Start with:** QUICKSTART.md → 5 minutes to get running!

---

**Happy Coding! 🚀**
