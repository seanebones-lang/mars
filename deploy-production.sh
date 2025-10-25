#!/bin/bash
# AgentGuard Complete Production Deployment to DigitalOcean
# Handles Docker, Docker Compose, PostgreSQL, Redis, Nginx, SSL
# Author: Sean McDonnell
# Date: October 25, 2025

set -euo pipefail

# Configuration
SERVER_IP="165.22.156.210"
SERVER_USER="root"
PROJECT_DIR="/opt/agentguard"
REPO_URL="https://github.com/seanebones-lang/mars.git"
BRANCH="main"
DOMAIN="${DOMAIN:-165.22.156.210}"  # Use IP if no domain set

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
info() { echo -e "${PURPLE}[INFO]${NC} $1"; }

# Check SSH connection
check_ssh() {
    log "Testing SSH connection to ${SERVER_IP}..."
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "echo 'Connected'" > /dev/null 2>&1; then
        success "SSH connection successful"
    else
        error "Cannot connect to server"
        echo "Run: ssh-copy-id ${SERVER_USER}@${SERVER_IP}"
        exit 1
    fi
}

# Push local changes
push_changes() {
    log "Pushing local changes to git..."
    if [ -n "$(git status --porcelain)" ]; then
        git add .
        git commit -m "Deploy: $(date +'%Y-%m-%d %H:%M:%S')" || true
        git push origin ${BRANCH}
        success "Changes pushed"
    else
        info "No local changes"
    fi
}

# Main deployment
deploy() {
    log "Starting deployment to ${SERVER_IP}..."
    
    ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} bash -s <<'ENDSSH'
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}AgentGuard Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Update system
echo -e "${BLUE}[1/10] Updating system...${NC}"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

# Install Docker
echo -e "${BLUE}[2/10] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Install dependencies
    apt-get install -y -qq \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up stable repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker installed successfully${NC}"
else
    echo -e "${GREEN}Docker already installed${NC}"
fi

# Install Docker Compose standalone (for compatibility)
echo -e "${BLUE}[3/10] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed: ${DOCKER_COMPOSE_VERSION}${NC}"
else
    echo -e "${GREEN}Docker Compose already installed${NC}"
fi

# Install additional tools
echo -e "${BLUE}[4/10] Installing additional tools...${NC}"
apt-get install -y -qq git curl wget htop net-tools ufw

# Configure firewall
echo -e "${BLUE}[5/10] Configuring firewall...${NC}"
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # API (optional, for direct access)
ufw reload
echo -e "${GREEN}Firewall configured${NC}"

# Clone or update repository
echo -e "${BLUE}[6/10] Setting up project...${NC}"
if [ -d "/opt/agentguard" ]; then
    echo -e "${YELLOW}Project exists, updating...${NC}"
    cd /opt/agentguard
    
    # Stop existing containers
    docker-compose down || docker compose down || true
    
    # Backup
    BACKUP_DIR="/opt/agentguard_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r /opt/agentguard "$BACKUP_DIR"
    echo -e "${GREEN}Backup created: $BACKUP_DIR${NC}"
    
    # Pull latest
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    echo -e "${YELLOW}Cloning repository...${NC}"
    mkdir -p /opt
    cd /opt
    git clone https://github.com/seanebones-lang/mars.git agentguard
    cd agentguard
fi

# Create environment file
echo -e "${BLUE}[7/10] Creating environment configuration...${NC}"
cat > /opt/agentguard/.env.production <<'EOF'
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=AgentGuard
APP_VERSION=1.0.0

# Database
POSTGRES_DB=agentguard
POSTGRES_USER=agentguard
POSTGRES_PASSWORD=agentguard_secure_$(openssl rand -hex 16)
DATABASE_URL=postgresql://agentguard:agentguard_secure_$(openssl rand -hex 16)@postgres:5432/agentguard

# Redis
REDIS_PASSWORD=redis_secure_$(openssl rand -hex 16)
REDIS_URL=redis://:redis_secure_$(openssl rand -hex 16)@redis:6379/0

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 32)

# API Keys (SET THESE MANUALLY)
CLAUDE_API_KEY=your_claude_api_key_here

# CORS
CORS_ORIGINS=http://165.22.156.210,https://165.22.156.210

# Workers
WORKERS=4
EOF

echo -e "${GREEN}Environment file created${NC}"
echo -e "${YELLOW}IMPORTANT: Edit /opt/agentguard/.env.production and set CLAUDE_API_KEY${NC}"

# Create Docker Compose override for production
echo -e "${BLUE}[8/10] Creating Docker Compose configuration...${NC}"
cat > /opt/agentguard/docker-compose.override.yml <<'EOF'
version: '3.8'

services:
  watcher-api:
    restart: always
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    restart: always
    env_file:
      - .env.production
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    restart: always
    env_file:
      - .env.production
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
EOF

# Build and start containers
echo -e "${BLUE}[9/10] Building and starting Docker containers...${NC}"
cd /opt/agentguard

# Pull latest images
docker-compose pull || docker compose pull || true

# Build images
docker-compose build --no-cache || docker compose build --no-cache

# Start services
docker-compose up -d || docker compose up -d

echo -e "${GREEN}Docker containers started${NC}"

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 10

# Check container status
docker-compose ps || docker compose ps

# Configure Nginx
echo -e "${BLUE}[10/10] Configuring Nginx reverse proxy...${NC}"
apt-get install -y -qq nginx

# Create Nginx configuration
cat > /etc/nginx/sites-available/agentguard <<'NGINXEOF'
upstream agentguard_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name 165.22.156.210;
    
    client_max_body_size 100M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API proxy
    location / {
        proxy_pass http://agentguard_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Health check
    location /health {
        proxy_pass http://agentguard_api/health;
        access_log off;
    }
    
    # API docs
    location /docs {
        proxy_pass http://agentguard_api/docs;
    }
}
NGINXEOF

# Enable site
ln -sf /etc/nginx/sites-available/agentguard /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

echo -e "${GREEN}Nginx configured and started${NC}"

# Create management script
cat > /opt/agentguard/manage.sh <<'MGMTEOF'
#!/bin/bash
# AgentGuard Management Script

case "$1" in
    start)
        cd /opt/agentguard
        docker-compose up -d
        echo "AgentGuard started"
        ;;
    stop)
        cd /opt/agentguard
        docker-compose down
        echo "AgentGuard stopped"
        ;;
    restart)
        cd /opt/agentguard
        docker-compose restart
        echo "AgentGuard restarted"
        ;;
    logs)
        cd /opt/agentguard
        docker-compose logs -f
        ;;
    status)
        cd /opt/agentguard
        docker-compose ps
        ;;
    update)
        cd /opt/agentguard
        git pull origin main
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo "AgentGuard updated"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update}"
        exit 1
        ;;
esac
MGMTEOF

chmod +x /opt/agentguard/manage.sh

# Final health check
echo -e "${BLUE}Running health check...${NC}"
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed!${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    docker-compose logs --tail=50 watcher-api || docker compose logs --tail=50 watcher-api
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "API URL: http://165.22.156.210"
echo -e "API Docs: http://165.22.156.210/docs"
echo -e "Health: http://165.22.156.210/health"
echo -e ""
echo -e "${YELLOW}Important Next Steps:${NC}"
echo -e "1. Edit /opt/agentguard/.env.production and set CLAUDE_API_KEY"
echo -e "2. Restart: /opt/agentguard/manage.sh restart"
echo -e ""
echo -e "Management commands:"
echo -e "  /opt/agentguard/manage.sh start    - Start services"
echo -e "  /opt/agentguard/manage.sh stop     - Stop services"
echo -e "  /opt/agentguard/manage.sh restart  - Restart services"
echo -e "  /opt/agentguard/manage.sh logs     - View logs"
echo -e "  /opt/agentguard/manage.sh status   - Check status"
echo -e "  /opt/agentguard/manage.sh update   - Update from git"
echo -e "${BLUE}========================================${NC}"

ENDSSH
    
    success "Remote deployment completed!"
}

# Verify deployment
verify() {
    log "Verifying deployment..."
    sleep 5
    
    echo ""
    info "Testing endpoints..."
    
    if curl -f -s http://${SERVER_IP}/health > /dev/null 2>&1; then
        success "✓ Health check passed"
    else
        warn "✗ Health check failed"
    fi
    
    if curl -f -s http://${SERVER_IP}/docs > /dev/null 2>&1; then
        success "✓ API docs accessible"
    else
        warn "✗ API docs not accessible"
    fi
    
    echo ""
    info "Checking Docker containers..."
    ssh ${SERVER_USER}@${SERVER_IP} "cd /opt/agentguard && docker-compose ps"
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
    
    check_ssh
    push_changes
    deploy
    verify
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Your AgentGuard API is now running at:"
    echo -e "  ${GREEN}http://${SERVER_IP}${NC}"
    echo -e "  ${GREEN}http://${SERVER_IP}/docs${NC} (API Documentation)"
    echo -e ""
    echo -e "${YELLOW}Critical Next Steps:${NC}"
    echo -e "1. SSH into server: ssh ${SERVER_USER}@${SERVER_IP}"
    echo -e "2. Edit environment: nano /opt/agentguard/.env.production"
    echo -e "3. Set CLAUDE_API_KEY with your actual API key"
    echo -e "4. Restart services: /opt/agentguard/manage.sh restart"
    echo -e ""
    echo -e "Management commands:"
    echo -e "  ssh ${SERVER_USER}@${SERVER_IP} '/opt/agentguard/manage.sh status'"
    echo -e "  ssh ${SERVER_USER}@${SERVER_IP} '/opt/agentguard/manage.sh logs'"
    echo -e "  ssh ${SERVER_USER}@${SERVER_IP} '/opt/agentguard/manage.sh restart'"
    echo -e "${BLUE}========================================${NC}"
}

main "$@"

