# Linux systemd Service Files for FOCOSA Hub
# Place these files in /etc/systemd/system/
# Then run: sudo systemctl enable focosa-user focosa-admin
#           sudo systemctl start focosa-user focosa-admin

---FILE 1: focosa-user.service---

[Unit]
Description=FOCOSA Hub User/Student API
Documentation=https://focosa.edu.ng
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/focosa
Environment="PATH=/var/www/focosa/venv/bin"
Environment="SECRET_KEY=your-secret-key-here"
Environment="USER_PORT=8000"
ExecStart=/var/www/focosa/venv/bin/python /var/www/focosa/main_user.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target


---FILE 2: focosa-admin.service---

[Unit]
Description=FOCOSA Hub Admin API
Documentation=https://focosa.edu.ng
After=network.target focosa-user.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/focosa
Environment="PATH=/var/www/focosa/venv/bin"
Environment="SECRET_KEY=your-secret-key-here"
Environment="ADMIN_PORT=8001"
ExecStart=/var/www/focosa/venv/bin/python /var/www/focosa/main_admin.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target


---INSTALLATION INSTRUCTIONS---

1. Create application directory:
   sudo mkdir -p /var/www/focosa
   sudo chown www-data:www-data /var/www/focosa

2. Copy application files:
   sudo cp main_user.py main_admin.py focosa.db* /var/www/focosa/
   sudo cp focosa-admin.html focosa-connected.html /var/www/focosa/
   sudo cp requirements.txt /var/www/focosa/

3. Create virtual environment:
   cd /var/www/focosa
   sudo python3 -m venv venv
   sudo venv/bin/pip install -r requirements.txt

4. Create service files:
   sudo cp focosa-user.service /etc/systemd/system/
   sudo cp focosa-admin.service /etc/systemd/system/

5. Update secret key:
   sudo nano /etc/systemd/system/focosa-user.service
   # Edit SECRET_KEY value
   sudo nano /etc/systemd/system/focosa-admin.service
   # Edit SECRET_KEY value

6. Reload systemd:
   sudo systemctl daemon-reload

7. Enable services (auto-start on boot):
   sudo systemctl enable focosa-user
   sudo systemctl enable focosa-admin

8. Start services:
   sudo systemctl start focosa-user
   sudo systemctl start focosa-admin

9. Check status:
   sudo systemctl status focosa-user
   sudo systemctl status focosa-admin

10. View logs:
    sudo journalctl -u focosa-user -f
    sudo journalctl -u focosa-admin -f


---COMMON COMMANDS---

# Check if services are running
systemctl is-active focosa-user
systemctl is-active focosa-admin

# Restart services
sudo systemctl restart focosa-user
sudo systemctl restart focosa-admin

# Stop services
sudo systemctl stop focosa-user
sudo systemctl stop focosa-admin

# View recent logs (last 50 lines)
sudo journalctl -u focosa-user -n 50
sudo journalctl -u focosa-admin -n 50

# Follow logs in real-time
sudo journalctl -u focosa-user -f
sudo journalctl -u focosa-admin -f

# Check disk usage
du -sh /var/www/focosa

# Backup database
sudo cp /var/www/focosa/focosa.db /var/backups/focosa.db.backup


---NGINX REVERSE PROXY SETUP---

# Create /etc/nginx/sites-available/focosa

upstream focosa_user {
    server localhost:8000;
}

upstream focosa_admin {
    server localhost:8001;
}

# User API
server {
    listen 80;
    server_name focosa.example.com;

    location / {
        proxy_pass http://focosa_user;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Admin API
server {
    listen 80;
    server_name admin.focosa.example.com;

    location / {
        proxy_pass http://focosa_admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable sites
sudo ln -s /etc/nginx/sites-available/focosa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
