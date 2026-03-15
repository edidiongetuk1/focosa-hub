# FOCOSA Hub - Quick Start Guide

## 🚀 Start Here

This guide shows you the fastest ways to get both admin and user APIs running.

---

## Option 1: Quick Local Development (2 Terminals)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start User API (Terminal 1)
```bash
python main_user.py
```
✅ User API running at: http://localhost:8000

### Step 3: Start Admin API (Terminal 2)
```bash
python main_admin.py
```
✅ Admin API running at: http://localhost:8001

### Access
- **User Frontend:** http://localhost:8000
- **User API Docs:** http://localhost:8000/docs
- **Admin Frontend:** http://localhost:8001
- **Admin API Docs:** http://localhost:8001/docs

---

## Option 2: Docker (1 Command)

### Prerequisites
- Docker installed
- Docker Compose installed

### Step 1: Configure Environment
```bash
cp .env.template .env
# Edit .env and update SECRET_KEY
```

### Step 2: Run Everything
```bash
docker-compose up -d
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f focosa-user
docker-compose logs -f focosa-admin
```

### Stop Services
```bash
docker-compose down
```

### Access
- **User API:** http://localhost:8000
- **Admin API:** http://localhost:8001

---

## Option 3: Background Services (Linux/Mac)

### Create Start Script
Create `start_focosa.sh`:
```bash
#!/bin/bash

# Kill any existing processes
pkill -f "python main_user.py" 2>/dev/null
pkill -f "python main_admin.py" 2>/dev/null

# Start both in background
python main_user.py > logs/user.log 2>&1 &
python main_admin.py > logs/admin.log 2>&1 &

# Create logs directory
mkdir -p logs

echo "✅ Both services started!"
echo "User API: http://localhost:8000"
echo "Admin API: http://localhost:8001"
echo ""
echo "View logs:"
echo "  tail -f logs/user.log"
echo "  tail -f logs/admin.log"
```

### Run
```bash
chmod +x start_focosa.sh
./start_focosa.sh
```

---

## 🔐 Default Credentials

### Admin Login
- **Email:** admin@focosa.edu.ng
- **Password:** admin123

### First Time Setup
1. Go to http://localhost:8000
2. Register a student account
3. Go to http://localhost:8001
4. Login with admin credentials
5. Manage content and approve listings

---

## 📊 What's Running?

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| User API | 8000 | Student portal & frontend | http://localhost:8000 |
| Admin API | 8001 | Admin dashboard & management | http://localhost:8001 |
| Database | Local | SQLite (focosa.db) | Shared between both |

---

## ✅ Verify Everything Works

### Test User API
```bash
curl http://localhost:8000/departments
```

### Test Admin API (requires login)
```bash
curl -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@focosa.edu.ng&password=admin123"
```

---

## 📝 Key Differences

### User API Features
- ✅ Student registration
- ✅ View announcements, events, resources
- ✅ Browse marketplace listings
- ✅ Create marketplace listings (pending approval)
- ❌ No admin controls

### Admin API Features
- ✅ Manage users
- ✅ Create/edit/delete departments
- ✅ Manage lecturers
- ✅ Create announcements & events
- ✅ Upload resources
- ✅ Approve/reject marketplace listings
- ✅ Dashboard statistics

---

## 🔒 Security Notes

1. Change `admin123` password after first login
2. Update `SECRET_KEY` in `.env` for production
3. Use environment variables for sensitive data
4. Enable HTTPS in production
5. Restrict CORS origins to your domain

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process using port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Kill process using port 8001
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
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

### Can't Connect to API
- Check if ports 8000 and 8001 are in use
- Verify Python version: `python --version` (should be 3.8+)
- Check firewall settings
- Ensure dependencies are installed

---

## 📚 Next Steps

1. **Customize:** Edit HTML files (focosa-admin.html, focosa-connected.html)
2. **Add Features:** Modify main_admin.py or main_user.py
3. **Deploy:** See DEPLOYMENT_GUIDE.md for cloud options
4. **Scale:** Use load balancers for multiple instances

---

## 📞 Support

For detailed deployment info: See `DEPLOYMENT_GUIDE.md`
For API documentation: Visit `/docs` on either port
