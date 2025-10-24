#!/bin/bash

# Watcher AI - Production Setup Script
# This script prepares the environment for production deployment

set -e

echo "🚀 Watcher AI - Production Setup"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if required tools are installed
check_requirements() {
    print_info "Checking requirements..."
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js found: $NODE_VERSION"
    else
        print_error "Node.js not found. Please install Node.js 18+"
        exit 1
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_status "Python found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        print_status "Git found: $GIT_VERSION"
    else
        print_error "Git not found. Please install Git"
        exit 1
    fi
}

# Generate secure secrets
generate_secrets() {
    print_info "Generating secure secrets..."
    
    # Create secrets directory
    mkdir -p secrets
    
    # Generate JWT secret
    JWT_SECRET=$(openssl rand -hex 32)
    echo "JWT_SECRET_KEY=$JWT_SECRET" > secrets/jwt_secret.env
    print_status "JWT secret generated"
    
    # Generate encryption key
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" > secrets/encryption_key.env
    print_status "Encryption key generated"
    
    # Generate webhook secret
    WEBHOOK_SECRET=$(openssl rand -hex 32)
    echo "WEBHOOK_SECRET=$WEBHOOK_SECRET" > secrets/webhook_secret.env
    print_status "Webhook secret generated"
    
    print_warning "Secrets generated in ./secrets/ directory"
    print_warning "Keep these secrets secure and add them to your deployment platform"
}

# Validate environment configuration
validate_config() {
    print_info "Validating configuration files..."
    
    # Check Vercel configuration
    if [ -f "agentguard-ui/vercel.json" ]; then
        print_status "Vercel configuration found"
    else
        print_error "Vercel configuration missing"
        exit 1
    fi
    
    # Check Render configuration
    if [ -f "render.yaml" ]; then
        print_status "Render configuration found"
    else
        print_error "Render configuration missing"
        exit 1
    fi
    
    # Check Docker configuration
    if [ -f "Dockerfile" ]; then
        print_status "Docker configuration found"
    else
        print_warning "Docker configuration missing (optional)"
    fi
    
    # Check requirements.txt
    if [ -f "requirements.txt" ]; then
        print_status "Python requirements found"
    else
        print_error "Python requirements.txt missing"
        exit 1
    fi
    
    # Check package.json
    if [ -f "agentguard-ui/package.json" ]; then
        print_status "Frontend package.json found"
    else
        print_error "Frontend package.json missing"
        exit 1
    fi
}

# Test local build
test_build() {
    print_info "Testing local build..."
    
    # Test backend
    print_info "Testing backend..."
    if python3 -c "from src.api.main_realtime import app; print('Backend import successful')"; then
        print_status "Backend imports successfully"
    else
        print_error "Backend import failed"
        exit 1
    fi
    
    # Test frontend build
    print_info "Testing frontend build..."
    cd agentguard-ui
    
    if npm install --silent; then
        print_status "Frontend dependencies installed"
    else
        print_error "Frontend dependency installation failed"
        exit 1
    fi
    
    if npm run build > /dev/null 2>&1; then
        print_status "Frontend builds successfully"
    else
        print_error "Frontend build failed"
        exit 1
    fi
    
    cd ..
}

# Create deployment checklist
create_checklist() {
    print_info "Creating deployment checklist..."
    
    cat > DEPLOYMENT_CHECKLIST.md << 'EOF'
# 🚀 Watcher AI - Deployment Checklist

## Pre-Deployment
- [ ] All code committed and pushed to GitHub
- [ ] Environment secrets generated
- [ ] Configuration files validated
- [ ] Local build tests passed
- [ ] Claude API key obtained
- [ ] Domain DNS configured

## Vercel Frontend Deployment
- [ ] Vercel project created
- [ ] Repository connected
- [ ] Environment variables configured
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Build successful
- [ ] Health check passing

## Render Backend Deployment
- [ ] PostgreSQL database created
- [ ] Redis cache created
- [ ] Web service created
- [ ] Environment variables configured
- [ ] Health checks configured
- [ ] Auto-deploy enabled
- [ ] Build successful
- [ ] Health check passing

## Post-Deployment Testing
- [ ] Frontend loads correctly
- [ ] Backend API responds
- [ ] Authentication works
- [ ] Real-time features functional
- [ ] Database connections active
- [ ] Redis cache working
- [ ] WebSocket connections stable
- [ ] All endpoints tested

## Production Verification
- [ ] Admin user created
- [ ] Sample data loaded
- [ ] Performance metrics baseline
- [ ] Error tracking active
- [ ] Monitoring dashboards configured
- [ ] Backup systems verified
- [ ] Support documentation updated

## Go-Live
- [ ] DNS propagated
- [ ] SSL certificates verified
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Team notified
- [ ] Documentation updated
- [ ] Launch announcement ready

## Success Criteria
- [ ] 99.9% uptime
- [ ] <100ms response time
- [ ] <0.1% error rate
- [ ] All features functional
- [ ] Security best practices implemented
- [ ] Monitoring and alerting active
EOF

    print_status "Deployment checklist created: DEPLOYMENT_CHECKLIST.md"
}

# Create environment template
create_env_template() {
    print_info "Creating environment template..."
    
    cat > .env.production.template << 'EOF'
# Watcher AI - Production Environment Template
# Copy this file and fill in the actual values

# API Configuration
NEXT_PUBLIC_API_URL=https://watcher-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://watcher-api.onrender.com

# Application Configuration
NEXT_PUBLIC_APP_NAME=Watcher AI
NEXT_PUBLIC_APP_DESCRIPTION=Real-Time Hallucination Defense
NEXT_PUBLIC_DOMAIN=watcher.mothership-ai.com
NEXT_PUBLIC_COMPANY_NAME=Mothership AI
NEXT_PUBLIC_COMPANY_URL=https://mothership-ai.com

# Security Configuration (Generate with: openssl rand -hex 32)
CLAUDE_API_KEY=your_claude_api_key_here
JWT_SECRET_KEY=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here
WEBHOOK_SECRET=your_webhook_secret_here

# Database Configuration (Auto-filled by Render)
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port/0

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_MONITORING=true
NEXT_PUBLIC_ENABLE_WEBHOOKS=true
NEXT_PUBLIC_ENABLE_BATCH_PROCESSING=true
NEXT_PUBLIC_ENABLE_MULTI_TENANT=true

# Contact Information
NEXT_PUBLIC_SUPPORT_EMAIL=support@mothership-ai.com
NEXT_PUBLIC_SALES_EMAIL=sales@mothership-ai.com
NEXT_PUBLIC_LINKEDIN_URL=https://linkedin.com/in/seanmcdonnell
NEXT_PUBLIC_GITHUB_URL=https://github.com/seanebones-lang

# Version Information
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_BUILD_DATE=2025-10-24
NEXT_PUBLIC_COMMIT_SHA=812239f
EOF

    print_status "Environment template created: .env.production.template"
}

# Main execution
main() {
    echo ""
    print_info "Starting production setup..."
    echo ""
    
    check_requirements
    echo ""
    
    generate_secrets
    echo ""
    
    validate_config
    echo ""
    
    test_build
    echo ""
    
    create_checklist
    echo ""
    
    create_env_template
    echo ""
    
    print_status "Production setup complete!"
    echo ""
    print_info "Next steps:"
    echo "1. Review generated secrets in ./secrets/ directory"
    echo "2. Follow DEPLOYMENT_GUIDE.md for deployment instructions"
    echo "3. Use DEPLOYMENT_CHECKLIST.md to track progress"
    echo "4. Configure environment variables using .env.production.template"
    echo ""
    print_warning "Keep all secrets secure and never commit them to version control!"
    echo ""
    print_status "Ready for production deployment! 🚀"
}

# Run main function
main "$@"
