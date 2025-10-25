#!/bin/bash
# AgentGuard Production Deployment Script
# Deploys latest code to DigitalOcean server at 165.22.156.210
# Author: Sean McDonnell
# Date: October 25, 2025

set -euo pipefail

# Configuration
SERVER_IP="165.22.156.210"
SERVER_USER="root"
SERVER_FINGERPRINT="4e:ba:85:de:ee:f3:f3:ef:a2:ae:81:49:a3:5e:8a:7f"
PROJECT_DIR="/opt/agentguard"
REPO_URL="https://github.com/seanebones-lang/mars.git"
SERVICE_NAME="agentguard"
BRANCH="main"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

info() {
    echo -e "${PURPLE}[INFO]${NC} $1"
}

# Check if SSH key exists
check_ssh_key() {
    if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
        error "No SSH key found. Please set up SSH key authentication."
        echo "Run: ssh-keygen -t ed25519 -C 'your_email@example.com'"
        exit 1
    fi
    success "SSH key found"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection to ${SERVER_IP}..."
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "echo 'Connection successful'" > /dev/null 2>&1; then
        success "SSH connection successful"
        return 0
    else
        error "Cannot connect to server. Please check:"
        echo "  1. Server is running"
        echo "  2. SSH key is added to server"
        echo "  3. Firewall allows SSH (port 22)"
        echo ""
        echo "To add your SSH key to the server, run:"
        echo "  ssh-copy-id ${SERVER_USER}@${SERVER_IP}"
        exit 1
    fi
}

# Push local changes to git
push_to_git() {
    log "Checking for local changes..."
    
    if [ -n "$(git status --porcelain)" ]; then
        warn "Local changes detected. Committing and pushing..."
        git add .
        git commit -m "Deploy: $(date +'%Y-%m-%d %H:%M:%S')" || true
        git push origin ${BRANCH}
        success "Changes pushed to git"
    else
        info "No local changes to commit"
    fi
}

# Deploy to server
deploy_to_server() {
    log "Deploying to server ${SERVER_IP}..."
    
    ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} bash -s <<'ENDSSH'
set -e

# Colors for remote output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}AgentGuard Deployment - DigitalOcean${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if project directory exists
if [ ! -d "/opt/agentguard" ]; then
    echo -e "${YELLOW}Project directory not found. Running initial setup...${NC}"
    
    # Update system
    echo -e "${BLUE}Updating system...${NC}"
    apt update && apt upgrade -y
    
    # Install Python 3.13
    echo -e "${BLUE}Installing Python 3.13...${NC}"
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install python3.13 python3.13-venv python3.13-dev python3.13-distutils -y
    
    # Install build tools
    echo -e "${BLUE}Installing build tools...${NC}"
    apt install build-essential gcc g++ make libffi-dev libssl-dev curl git wget -y
    
    # Install PostgreSQL
    echo -e "${BLUE}Installing PostgreSQL...${NC}"
    apt install postgresql postgresql-contrib -y
    systemctl start postgresql
    systemctl enable postgresql
    
    # Install Redis
    echo -e "${BLUE}Installing Redis...${NC}"
    apt install redis-server -y
    systemctl start redis-server
    systemctl enable redis-server
    
    # Install Nginx
    echo -e "${BLUE}Installing Nginx...${NC}"
    apt install nginx -y
    systemctl start nginx
    systemctl enable nginx
    
    # Clone repository
    echo -e "${BLUE}Cloning AgentGuard repository...${NC}"
    cd /opt
    git clone https://github.com/seanebones-lang/mars.git agentguard
    cd agentguard
    
    # Create virtual environment
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3.13 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements-render.txt
    
    # Setup PostgreSQL database
    echo -e "${BLUE}Setting up PostgreSQL database...${NC}"
    sudo -u postgres psql -c "CREATE DATABASE agentguard;" || echo "Database already exists"
    sudo -u postgres psql -c "CREATE USER agentguard WITH PASSWORD 'agentguard_secure_password';" || echo "User already exists"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE agentguard TO agentguard;" || true
    
    # Create systemd service
    echo -e "${BLUE}Creating systemd service...${NC}"
    cat > /etc/systemd/system/agentguard.service <<'EOF'
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
    echo -e "${BLUE}Configuring Nginx...${NC}"
    cat > /etc/nginx/sites-available/agentguard <<'NGINXEOF'
server {
    listen 80;
    server_name 165.22.156.210;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXEOF
    
    ln -sf /etc/nginx/sites-available/agentguard /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl reload nginx
    
    # Start service
    echo -e "${BLUE}Starting AgentGuard service...${NC}"
    systemctl daemon-reload
    systemctl start agentguard
    systemctl enable agentguard
    
    echo -e "${GREEN}Initial setup complete!${NC}"
else
    echo -e "${BLUE}Updating existing deployment...${NC}"
    
    # Navigate to project directory
    cd /opt/agentguard
    
    # Stop service
    echo -e "${BLUE}Stopping AgentGuard service...${NC}"
    systemctl stop agentguard || true
    
    # Backup current version
    echo -e "${BLUE}Creating backup...${NC}"
    BACKUP_DIR="/opt/agentguard_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r /opt/agentguard "$BACKUP_DIR"
    echo -e "${GREEN}Backup created at: $BACKUP_DIR${NC}"
    
    # Pull latest changes
    echo -e "${BLUE}Pulling latest changes from git...${NC}"
    git fetch origin
    git reset --hard origin/main
    git pull origin main
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Update dependencies
    echo -e "${BLUE}Updating dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements-render.txt
    
    # Run database migrations if any
    echo -e "${BLUE}Running database migrations...${NC}"
    # Add migration commands here if needed
    
    # Start service
    echo -e "${BLUE}Starting AgentGuard service...${NC}"
    systemctl daemon-reload
    systemctl start agentguard
    
    echo -e "${GREEN}Deployment updated!${NC}"
fi

# Wait for service to start
echo -e "${BLUE}Waiting for service to start...${NC}"
sleep 5

# Check service status
echo -e "${BLUE}Checking service status...${NC}"
systemctl status agentguard --no-pager || true

# Test health endpoint
echo -e "${BLUE}Testing health endpoint...${NC}"
sleep 3
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}Health check passed!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    journalctl -u agentguard -n 50 --no-pager
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "API URL: http://165.22.156.210"
echo -e "API Docs: http://165.22.156.210/docs"
echo -e "Health: http://165.22.156.210/health"
echo -e ""
echo -e "Useful commands:"
echo -e "  Check status: systemctl status agentguard"
echo -e "  View logs: journalctl -u agentguard -f"
echo -e "  Restart: systemctl restart agentguard"
echo -e "${BLUE}========================================${NC}"

ENDSSH
    
    success "Deployment completed successfully!"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    sleep 3
    
    if curl -f http://${SERVER_IP}/health > /dev/null 2>&1; then
        success "Health check passed!"
        info "API is running at: http://${SERVER_IP}"
        info "API Docs: http://${SERVER_IP}/docs"
    else
        warn "Health check failed. Checking logs..."
        ssh ${SERVER_USER}@${SERVER_IP} "journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}AgentGuard Production Deployment${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Server: ${SERVER_IP}"
    echo -e "Branch: ${BRANCH}"
    echo -e "Time: $(date)"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_ssh_key
    test_ssh_connection
    push_to_git
    deploy_to_server
    verify_deployment
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Your AgentGuard API is now running at:"
    echo -e "  ${GREEN}http://${SERVER_IP}${NC}"
    echo -e ""
    echo -e "Next steps:"
    echo -e "  1. Visit http://${SERVER_IP}/docs for API documentation"
    echo -e "  2. Test the health endpoint: curl http://${SERVER_IP}/health"
    echo -e "  3. Monitor logs: ssh ${SERVER_USER}@${SERVER_IP} 'journalctl -u ${SERVICE_NAME} -f'"
    echo -e "${BLUE}========================================${NC}"
}

# Execute main function
main "$@"

