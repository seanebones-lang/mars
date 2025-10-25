#!/bin/bash
# AgentGuard DigitalOcean Deployment Script
# Run this on your Ubuntu 22.04 droplet as root

set -e

echo "=========================================="
echo "AgentGuard Deployment - DigitalOcean"
echo "=========================================="

# Update system
echo "Updating system..."
apt update && apt upgrade -y

# Install Python 3.13
echo "Installing Python 3.13..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install python3.13 python3.13-venv python3.13-dev python3.13-distutils -y

# Install build tools
echo "Installing build tools..."
apt install build-essential gcc g++ make libffi-dev libssl-dev curl git wget -y

# Install PostgreSQL
echo "Installing PostgreSQL..."
apt install postgresql postgresql-contrib -y
systemctl start postgresql
systemctl enable postgresql

# Install Redis
echo "Installing Redis..."
apt install redis-server -y
systemctl start redis-server
systemctl enable redis-server

# Install Nginx
echo "Installing Nginx..."
apt install nginx -y
systemctl start nginx
systemctl enable nginx

# Clone repository
echo "Cloning AgentGuard repository..."
cd /opt
git clone https://github.com/seanebones-lang/mars.git agentguard
cd agentguard

# Create virtual environment
echo "Creating Python virtual environment..."
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements-render.txt

# Setup PostgreSQL database
echo "Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE agentguard;"
sudo -u postgres psql -c "CREATE USER agentguard WITH PASSWORD 'agentguard_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE agentguard TO agentguard;"

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/agentguard.service <<EOF
[Unit]
Description=AgentGuard API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/agentguard
Environment="PATH=/opt/agentguard/venv/bin"
ExecStart=/opt/agentguard/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/agentguard <<EOF
server {
    listen 80;
    server_name 165.22.156.210;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/agentguard /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Start service
echo "Starting AgentGuard service..."
systemctl daemon-reload
systemctl start agentguard
systemctl enable agentguard

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "API URL: http://165.22.156.210"
echo "API Docs: http://165.22.156.210/docs"
echo "Health: http://165.22.156.210/health"
echo ""
echo "Check status: systemctl status agentguard"
echo "View logs: journalctl -u agentguard -f"
echo "=========================================="

