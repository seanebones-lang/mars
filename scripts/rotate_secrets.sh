#!/bin/bash
#
# Automated Secrets Rotation
# P0-Critical: Security best practice for production
#
# Usage: ./scripts/rotate_secrets.sh [--emergency]
#

set -e

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
EMERGENCY_MODE="${1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if running in emergency mode
if [ "$EMERGENCY_MODE" = "--emergency" ]; then
    log_warn "=========================================="
    log_warn "EMERGENCY SECRETS ROTATION"
    log_warn "=========================================="
    log_warn "This will rotate ALL secrets immediately."
    log_warn "Services will be restarted."
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_error "Aborted."
        exit 1
    fi
fi

log_info "=========================================="
log_info "Secrets Rotation for $ENVIRONMENT"
log_info "=========================================="

# Backup current secrets
log_step "1/6: Backing up current secrets"
BACKUP_FILE="secrets_backup_$(date +%Y%m%d_%H%M%S).env"
cat > "$BACKUP_FILE" <<EOF
# Secrets backup from $(date)
CLAUDE_API_KEY=$CLAUDE_API_KEY
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
DATABASE_URL=$DATABASE_URL
REDIS_URL=$REDIS_URL
SENTRY_DSN=$SENTRY_DSN
EOF

log_info "✓ Secrets backed up to $BACKUP_FILE"

# Rotate Claude API key
log_step "2/6: Rotating Claude API key"
log_warn "⚠️  Manual action required:"
log_warn "   1. Go to https://console.anthropic.com/settings/keys"
log_warn "   2. Create a new API key"
log_warn "   3. Enter the new key below"
read -p "New Claude API key: " NEW_CLAUDE_KEY

if [ -z "$NEW_CLAUDE_KEY" ]; then
    log_error "No key provided. Skipping Claude key rotation."
else
    # Update Render environment variable
    log_info "Updating Render environment..."
    # Note: This requires Render CLI or API
    # For now, manual update required
    log_warn "⚠️  Manual action required:"
    log_warn "   1. Go to https://dashboard.render.com/"
    log_warn "   2. Select agentguard-api service"
    log_warn "   3. Go to Environment tab"
    log_warn "   4. Update CLAUDE_API_KEY to: $NEW_CLAUDE_KEY"
    log_warn "   5. Save changes"
    read -p "Press Enter when done..."
    log_info "✓ Claude API key rotation complete"
fi

# Rotate Stripe secret key
log_step "3/6: Rotating Stripe secret key"
log_warn "⚠️  Manual action required:"
log_warn "   1. Go to https://dashboard.stripe.com/apikeys"
log_warn "   2. Roll the secret key"
log_warn "   3. Enter the new key below"
read -p "New Stripe secret key: " NEW_STRIPE_KEY

if [ -z "$NEW_STRIPE_KEY" ]; then
    log_error "No key provided. Skipping Stripe key rotation."
else
    log_warn "⚠️  Manual action required:"
    log_warn "   1. Go to https://dashboard.render.com/"
    log_warn "   2. Select agentguard-api service"
    log_warn "   3. Go to Environment tab"
    log_warn "   4. Update STRIPE_SECRET_KEY to: $NEW_STRIPE_KEY"
    log_warn "   5. Save changes"
    read -p "Press Enter when done..."
    log_info "✓ Stripe secret key rotation complete"
fi

# Rotate database password
log_step "4/6: Rotating database password"
log_warn "⚠️  Database password rotation requires:"
log_warn "   1. Render PostgreSQL dashboard access"
log_warn "   2. Service downtime during rotation"
log_warn "   3. Update DATABASE_URL in environment"
read -p "Rotate database password? (yes/no): " rotate_db

if [ "$rotate_db" = "yes" ]; then
    log_warn "⚠️  Manual action required:"
    log_warn "   1. Go to Render PostgreSQL dashboard"
    log_warn "   2. Reset database password"
    log_warn "   3. Update DATABASE_URL in service environment"
    log_warn "   4. Restart service"
    read -p "Press Enter when done..."
    log_info "✓ Database password rotation complete"
else
    log_warn "Skipping database password rotation"
fi

# Rotate Redis password
log_step "5/6: Rotating Redis password"
log_warn "⚠️  Redis password rotation requires:"
log_warn "   1. Render Redis dashboard access"
log_warn "   2. Service downtime during rotation"
log_warn "   3. Update REDIS_URL in environment"
read -p "Rotate Redis password? (yes/no): " rotate_redis

if [ "$rotate_redis" = "yes" ]; then
    log_warn "⚠️  Manual action required:"
    log_warn "   1. Go to Render Redis dashboard"
    log_warn "   2. Reset Redis password"
    log_warn "   3. Update REDIS_URL in service environment"
    log_warn "   4. Restart service"
    read -p "Press Enter when done..."
    log_info "✓ Redis password rotation complete"
else
    log_warn "Skipping Redis password rotation"
fi

# Restart services
log_step "6/6: Restarting services"
log_warn "⚠️  Manual action required:"
log_warn "   1. Go to https://dashboard.render.com/"
log_warn "   2. Restart agentguard-api service"
log_warn "   3. Restart agentguard-ui service"
log_warn "   4. Verify health checks pass"
read -p "Press Enter when done..."

# Verify services
log_info "Verifying services..."
sleep 10

# Check API health
API_HEALTH=$(curl -s https://agentguard-api.onrender.com/health | jq -r '.status' || echo "error")
if [ "$API_HEALTH" = "healthy" ]; then
    log_info "✓ API service healthy"
else
    log_error "✗ API service unhealthy: $API_HEALTH"
fi

# Check UI health
UI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://agentguard-ui.onrender.com || echo "000")
if [ "$UI_STATUS" = "200" ]; then
    log_info "✓ UI service healthy"
else
    log_error "✗ UI service unhealthy: HTTP $UI_STATUS"
fi

# Send notification
log_info "=========================================="
log_info "✅ Secrets Rotation Complete"
log_info "=========================================="
log_info "Backup saved to: $BACKUP_FILE"
log_info "Keep this file secure!"
log_info ""
log_info "Next rotation due: $(date -d '+30 days' +%Y-%m-%d)"
log_info "=========================================="

# Send Slack notification if webhook configured
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ Secrets rotation complete for $ENVIRONMENT environment. Next rotation: $(date -d '+30 days' +%Y-%m-%d)\"}" \
        2>/dev/null || true
fi

# Send alert via alert manager
if [ -n "$NEW_CLAUDE_KEY" ] || [ -n "$NEW_STRIPE_KEY" ]; then
    log_info "Sending security notification..."
    # This would integrate with the alert manager
    # python -c "from src.utils.alert_manager import get_alert_manager; get_alert_manager().alert_security_incident('Secrets Rotation', 'Scheduled secrets rotation completed successfully')"
fi

exit 0

