#!/bin/bash
# SECURE RENDER DEPLOYMENT SCRIPT - 2025 ENTERPRISE
# AgentGuard AI Hallucination Detection Platform
# NO API KEYS - Uses environment variables only

set -euo pipefail

# Configuration
PROJECT_NAME="AgentGuard Enterprise"
RENDER_SERVICE_NAME="agentguard-enterprise-api"
GIT_BRANCH="main"

# Colors for output
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

# Display secure deployment instructions
show_secure_deployment_instructions() {
    log "=== SECURE RENDER DEPLOYMENT INSTRUCTIONS ==="
    echo
    info "Your AgentGuard Enterprise system is ready for secure deployment!"
    echo
    echo -e "${YELLOW}STEP 1: Push Code to Repository${NC}"
    echo "  git add ."
    echo "  git commit -m \"Deploy AgentGuard Enterprise - Secure 2025\""
    echo "  git push origin ${GIT_BRANCH}"
    echo
    echo -e "${YELLOW}STEP 2: Configure Render Service${NC}"
    echo "  Your existing Render service will auto-deploy from Git push"
    echo "  Service Name: ${RENDER_SERVICE_NAME}"
    echo "  Build Command: pip install -r requirements.txt"
    echo "  Start Command: python -m uvicorn src.api.main_realtime:app --host 0.0.0.0 --port \$PORT --workers 4"
    echo
    echo -e "${YELLOW}STEP 3: Set Environment Variables in Render Dashboard${NC}"
    echo "  🔒 CRITICAL: Set these in Render dashboard (NOT in code):"
    echo "  - CLAUDE_API_KEY: [Your Claude API key - NEVER commit this]"
    echo "  - APP_ENV: production"
    echo "  - LOG_LEVEL: info"
    echo "  - WORKERS: 4"
    echo "  - ENABLE_ADVANCED_RAG: true"
    echo "  - ENABLE_WIKIPEDIA_GROUNDING: true"
    echo "  - TOKENIZERS_PARALLELISM: false"
    echo
    echo -e "${YELLOW}STEP 4: Verify Deployment${NC}"
    echo "  Health Check: https://${RENDER_SERVICE_NAME}.onrender.com/health"
    echo "  API Docs: https://${RENDER_SERVICE_NAME}.onrender.com/docs"
    echo
    echo -e "${GREEN}EXPECTED DEPLOYMENT TIME: 5-10 minutes${NC}"
    echo
    success "Secure deployment instructions provided!"
    warn "🔒 SECURITY REMINDER: NEVER commit API keys to Git!"
}

# Main execution
main() {
    log "=== AgentGuard Enterprise Secure Deployment - 2025 ==="
    log "Preparing ${PROJECT_NAME} for secure cloud deployment"
    
    show_secure_deployment_instructions
    
    echo
    success "=== SECURE DEPLOYMENT PREPARATION COMPLETE ==="
    info "Your AgentGuard Enterprise system follows 2025 security best practices!"
    echo
    warn "🔒 Remember to set CLAUDE_API_KEY in Render dashboard environment variables"
}

# Execute main function
main "$@"
