# FOCOSA Hub - Separate Admin & User Deployment Guide

## Overview
You now have TWO completely separate FastAPI applications:
- **main_admin.py** → Admin dashboard (Port 8001)
- **main_user.py** → Student/User frontend (Port 8000)

Both share the SAME database (`focosa.db`) but run independently.

---

## ⚙️ Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Run Both Simultaneously (Option A: Two Terminal Windows)

**Terminal 1 - Start User/Student API:**
```bash
python main_user.py
```
- Access at: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:8000

**Terminal 2 - Start Admin API:**
```bash
python main_admin.py
```
- Access at: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Frontend: http://localhost:8001

### 3. Run Both Simultaneously (Option B: Concurrently)

**Install concurrently:**
```bash
pip install concurrently --break-system-packages
```

**Create start_both.sh:**
```bash
#!/bin/bash
concurrently "python main_user.py" "python main_admin.py"
```

**Run:**
```bash
chmod +x start_both.sh
./start_both.sh
```

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  # User/Student API
  focosa-user:
    build:
      context: .
      dockerfile: Dockerfile.user
    container_name: focosa-user-api
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your-secret-key-here
      - USER_PORT=8000
    volumes:
      - ./focosa.db:/app/focosa.db
    restart: unless-stopped

  # Admin API
  focosa-admin:
    build:
      context: .
      dockerfile: Dockerfile.admin
    container_name: focosa-admin-api
    ports:
      - "8001:8001"
    environment:
      - SECRET_KEY=your-secret-key-here
      - ADMIN_PORT=8001
    volumes:
      - ./focosa.db:/app/focosa.db
    restart: unless-stopped
```

**Create `Dockerfile.user`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY focosa.db* ./
COPY main_user.py ./
COPY focosa-connected.html ./

EXPOSE 8000

CMD ["python", "main_user.py"]
```

**Create `Dockerfile.admin`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY focosa.db* ./
COPY main_admin.py ./
COPY focosa-admin.html ./

EXPOSE 8001

CMD ["python", "main_admin.py"]
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

**Check logs:**
```bash
docker-compose logs -f focosa-user
docker-compose logs -f focosa-admin
```

**Stop services:**
```bash
docker-compose down
```

---

## ☁️ Cloud Deployment Options

### Option 1: Render.com (Easiest)

**For User API:**
1. Create new Web Service
2. Connect your GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main_user.py`
5. Environment variables: `SECRET_KEY=your-key`, `USER_PORT=10000`

**For Admin API:**
1. Repeat above but use `python main_admin.py`
2. Environment variables: `SECRET_KEY=your-key`, `ADMIN_PORT=10000`

### Option 2: Railway.app

1. Create two services:
   - focosa-user: runs `python main_user.py`
   - focosa-admin: runs `python main_admin.py`
2. Share the same database volume
3. Set environment variables per service

### Option 3: Heroku

**For User API:**
```bash
heroku create focosa-user
heroku config:set SECRET_KEY=your-key USER_PORT=5000
git push heroku main
```

**For Admin API:**
```bash
heroku create focosa-admin
heroku config:set SECRET_KEY=your-key ADMIN_PORT=5000
git push heroku main
```

### Option 4: AWS EC2

1. Launch 2 EC2 instances (or use 1 with both services)
2. Install Python and dependencies
3. Start both apps as systemd services

**Create `/etc/systemd/system/focosa-user.service`:**
```ini
[Unit]
Description=FOCOSA User API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/focosa
ExecStart=/usr/bin/python3 /home/ubuntu/focosa/main_user.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create `/etc/systemd/system/focosa-admin.service`:**
```ini
[Unit]
Description=FOCOSA Admin API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/focosa
ExecStart=/usr/bin/python3 /home/ubuntu/focosa/main_admin.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable focosa-user
sudo systemctl enable focosa-admin
sudo systemctl start focosa-user
sudo systemctl start focosa-admin
```

---

## 🔒 Production Security Checklist

- [ ] Change `SECRET_KEY` in environment variables
- [ ] Update CORS `allow_origins` to specific domains (not `["*"]`)
- [ ] Use HTTPS with SSL certificates
- [ ] Implement rate limiting
- [ ] Set strong database passwords
- [ ] Use environment files (`.env`) with secrets
- [ ] Enable API key authentication for critical endpoints
- [ ] Set up monitoring and logging

---

## 📊 Database Sharing

Both applications use the same `focosa.db` file. WAL mode ensures proper concurrency.

**Key Features:**
- ✅ Both apps can read simultaneously
- ✅ Admin app writes data
- ✅ User app reads data
- ✅ WAL (Write-Ahead Logging) prevents conflicts
- ✅ Shared database volume in Docker

---

## 🔐 API Endpoints Summary

### User API (Port 8000)
```
POST   /auth/register              - Register new account
POST   /auth/token                 - Login
GET    /auth/me                    - Get profile
PATCH  /auth/profile               - Update profile
GET    /departments                - View departments
GET    /lecturers                  - View lecturers
GET    /events                     - View events
GET    /announcements              - View announcements
GET    /resources                  - View study materials
POST   /listings                   - Create marketplace item
GET    /listings                   - Browse marketplace
GET    /my-listings                - View your listings
```

### Admin API (Port 8001)
```
POST   /auth/token                 - Admin login only
GET    /auth/me                    - Get admin profile
GET    /admin/stats                - Dashboard statistics
GET    /users                      - List all users
DELETE /users/{user_id}            - Delete user
POST   /departments                - Create department
GET    /departments                - View departments
DELETE /departments/{dept_id}      - Delete department
POST   /lecturers                  - Add lecturer
DELETE /lecturers/{lec_id}         - Remove lecturer
POST   /events                     - Create event
DELETE /events/{event_id}          - Delete event
POST   /announcements              - Create announcement
DELETE /announcements/{ann_id}     - Delete announcement
POST   /resources                  - Upload resource
DELETE /resources/{res_id}         - Delete resource
PATCH  /listings/{listing_id}/approve   - Approve listing
PATCH  /listings/{listing_id}/reject    - Reject listing
DELETE /listings/{listing_id}      - Delete listing
```

---

## 🚀 Scaling Considerations

### Load Balancing
If you need multiple instances:
```yaml
# Use Nginx or HAProxy to route traffic
focosa-user.example.com → 8000 (or multiple instances)
focosa-admin.example.com → 8001 (or single instance)
```

### Database Backup
```bash
# Backup database
cp focosa.db focosa.db.backup

# Restore from backup
cp focosa.db.backup focosa.db
```

---

## ❓ Troubleshooting

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Database locked error:**
- Ensure only one write operation at a time
- WAL mode should handle this automatically
- Check file permissions on `focosa.db*` files

**CORS errors:**
- Update `allow_origins` in FastAPI middleware
- Ensure frontend and API URLs match

**Import errors:**
```bash
pip install -r requirements.txt --break-system-packages
```

---

## 📞 Support

For issues or questions:
1. Check API docs at `/docs` endpoints
2. Review logs in terminal or systemd journals
3. Verify database connectivity
4. Test endpoints with curl or Postman
