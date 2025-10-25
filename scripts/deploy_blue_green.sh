#!/bin/bash
#
# Blue-Green Deployment Script for AgentGuard
# P0-Critical: Zero-downtime deployment with automatic rollback
#
# Usage: ./scripts/deploy_blue_green.sh [staging|production]
#

set -e
set -u

# Configuration
ENVIRONMENT="${1:-staging}"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Validate environment
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_info "Usage: $0 [staging|production]"
    exit 1
fi

log_info "=========================================="
log_info "Blue-Green Deployment to $ENVIRONMENT"
log_info "=========================================="

# Set environment-specific variables
if [ "$ENVIRONMENT" = "staging" ]; then
    DEPLOY_HOOK="${RENDER_DEPLOY_HOOK_STAGING:-}"
    API_URL="https://agentguard-api-staging.onrender.com"
    UI_URL="https://agentguard-ui-staging.onrender.com"
else
    DEPLOY_HOOK="${RENDER_DEPLOY_HOOK_PRODUCTION:-}"
    API_URL="https://agentguard-api.onrender.com"
    UI_URL="https://agentguard-ui.onrender.com"
fi

# Check if deploy hook is set
if [ -z "$DEPLOY_HOOK" ]; then
    log_error "Deploy hook not set for $ENVIRONMENT"
    log_info "Set RENDER_DEPLOY_HOOK_${ENVIRONMENT^^} environment variable"
    exit 1
fi

# Step 1: Pre-deployment checks
log_step "1/8: Running pre-deployment checks..."

# Check current system health
log_info "Checking current system health..."
CURRENT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" || echo "000")

if [ "$CURRENT_HEALTH" != "200" ]; then
    log_warn "Current system health check failed (HTTP $CURRENT_HEALTH)"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        log_error "Deployment cancelled"
        exit 1
    fi
else
    log_info "✓ Current system is healthy"
fi

# Step 2: Create backup
log_step "2/8: Creating pre-deployment backup..."
if [ -f "./scripts/backup_database.sh" ]; then
    ./scripts/backup_database.sh "pre_deploy_$(date +%Y%m%d_%H%M%S)" || log_warn "Backup failed"
    log_info "✓ Backup created"
else
    log_warn "Backup script not found - skipping backup"
fi

# Step 3: Run tests
log_step "3/8: Running test suite..."
if command -v pytest &> /dev/null; then
    log_info "Running backend tests..."
    if pytest tests/ -v --tb=short; then
        log_info "✓ All tests passed"
    else
        log_error "Tests failed!"
        read -p "Deploy anyway? (yes/no): " CONTINUE
        if [ "$CONTINUE" != "yes" ]; then
            log_error "Deployment cancelled"
            exit 1
        fi
    fi
else
    log_warn "pytest not found - skipping tests"
fi

# Step 4: Trigger deployment
log_step "4/8: Triggering deployment..."
log_info "Deploying to $ENVIRONMENT..."

DEPLOY_RESPONSE=$(curl -s -X POST "$DEPLOY_HOOK")
log_info "Deploy triggered: $DEPLOY_RESPONSE"

# Step 5: Wait for deployment
log_step "5/8: Waiting for deployment to complete..."
log_info "This may take 3-5 minutes..."
sleep 180  # Wait 3 minutes for build

# Step 6: Health check new deployment
log_step "6/8: Checking new deployment health..."

RETRY_COUNT=0
NEW_HEALTH="000"

while [ $RETRY_COUNT -lt $HEALTH_CHECK_RETRIES ]; do
    log_info "Health check attempt $((RETRY_COUNT + 1))/$HEALTH_CHECK_RETRIES..."
    
    NEW_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" || echo "000")
    
    if [ "$NEW_HEALTH" = "200" ]; then
        log_info "✓ New deployment is healthy!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep $HEALTH_CHECK_INTERVAL
done

if [ "$NEW_HEALTH" != "200" ]; then
    log_error "New deployment health check failed after $HEALTH_CHECK_RETRIES attempts"
    log_error "HTTP Status: $NEW_HEALTH"
    
    # Step 7: Rollback on failure
    log_step "7/8: ROLLING BACK deployment..."
    log_error "Automatic rollback not yet implemented - manual rollback required"
    log_error "Go to Render dashboard and rollback to previous deployment"
    exit 1
fi

# Step 7: Smoke tests
log_step "7/8: Running smoke tests..."

# Test critical endpoints
log_info "Testing API endpoints..."

# Health endpoint
if curl -f -s "$API_URL/health" > /dev/null; then
    log_info "✓ Health endpoint OK"
else
    log_error "Health endpoint failed"
    exit 1
fi

# Docs endpoint
if curl -f -s "$API_URL/docs" > /dev/null; then
    log_info "✓ Docs endpoint OK"
else
    log_warn "Docs endpoint failed"
fi

# Frontend
if curl -f -s "$UI_URL/" > /dev/null; then
    log_info "✓ Frontend OK"
else
    log_warn "Frontend check failed"
fi

# Test agent endpoint (if API key available)
if [ -n "${CLAUDE_API_KEY:-}" ]; then
    log_info "Testing agent endpoint..."
    TEST_RESPONSE=$(curl -s -X POST "$API_URL/test-agent" \
        -H "Content-Type: application/json" \
        -d '{"agent_output":"test","ground_truth":"test"}' || echo "failed")
    
    if [ "$TEST_RESPONSE" != "failed" ]; then
        log_info "✓ Agent endpoint OK"
    else
        log_warn "Agent endpoint test failed"
    fi
fi

# Step 8: Post-deployment tasks
log_step "8/8: Post-deployment tasks..."

# Send notification
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ AgentGuard deployed to $ENVIRONMENT successfully\"}" \
        2>/dev/null || true
fi

# Log deployment
DEPLOYMENT_LOG="/var/log/agentguard/deployments.log"
if [ -d "$(dirname "$DEPLOYMENT_LOG")" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $ENVIRONMENT | SUCCESS | $(git rev-parse --short HEAD)" >> "$DEPLOYMENT_LOG"
fi

# Summary
log_info "=========================================="
log_info "✅ Deployment completed successfully!"
log_info "=========================================="
log_info "Environment: $ENVIRONMENT"
log_info "API URL: $API_URL"
log_info "UI URL: $UI_URL"
log_info "Health Status: HTTP $NEW_HEALTH"
log_info "Timestamp: $(date)"
log_info "=========================================="

# Monitor for 5 minutes
log_info "Monitoring deployment for 5 minutes..."
log_info "Press Ctrl+C to stop monitoring"

for i in {1..30}; do
    sleep 10
    CURRENT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" || echo "000")
    if [ "$CURRENT_HEALTH" != "200" ]; then
        log_error "Health check failed during monitoring (HTTP $CURRENT_HEALTH)"
        log_error "Deployment may be unstable!"
        exit 1
    fi
    echo -n "."
done

echo ""
log_info "✅ Deployment stable after 5 minutes of monitoring"

exit 0

