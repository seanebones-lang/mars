#!/bin/bash
#
# Database Backup Script for AgentGuard
# P0-Critical: Automated database backup and disaster recovery
#
# Usage: ./scripts/backup_database.sh [backup_name]
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/agentguard}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-agentguard-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-backup_${TIMESTAMP}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    log_error "DATABASE_URL environment variable not set"
    exit 1
fi

# Parse DATABASE_URL
# Format: postgresql://user:password@host:port/dbname
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

log_info "Starting database backup for ${DB_NAME}"
log_info "Backup name: ${BACKUP_NAME}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Backup filename
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
BACKUP_METADATA="${BACKUP_DIR}/${BACKUP_NAME}.meta.json"

# Perform backup
log_info "Creating database dump..."
export PGPASSWORD="${DB_PASS}"

if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --file="${BACKUP_FILE}.tmp" \
    --verbose; then
    
    mv "${BACKUP_FILE}.tmp" "${BACKUP_FILE}"
    log_info "Database dump created successfully: ${BACKUP_FILE}"
else
    log_error "Database dump failed"
    rm -f "${BACKUP_FILE}.tmp"
    exit 1
fi

unset PGPASSWORD

# Get backup size
BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)

# Create metadata file
cat > "${BACKUP_METADATA}" <<EOF
{
  "backup_name": "${BACKUP_NAME}",
  "timestamp": "${TIMESTAMP}",
  "database": "${DB_NAME}",
  "host": "${DB_HOST}",
  "size": "${BACKUP_SIZE}",
  "format": "custom",
  "compression": "gzip",
  "retention_days": ${RETENTION_DAYS}
}
EOF

log_info "Backup metadata created: ${BACKUP_METADATA}"

# Upload to S3 if AWS CLI is available and S3_BUCKET is set
if command -v aws &> /dev/null && [ -n "${S3_BUCKET}" ]; then
    log_info "Uploading backup to S3: s3://${S3_BUCKET}/"
    
    if aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/backups/${BACKUP_NAME}.sql.gz" \
        && aws s3 cp "${BACKUP_METADATA}" "s3://${S3_BUCKET}/backups/${BACKUP_NAME}.meta.json"; then
        log_info "Backup uploaded to S3 successfully"
    else
        log_warn "Failed to upload backup to S3 (local backup still available)"
    fi
else
    log_warn "AWS CLI not available or S3_BUCKET not set - skipping S3 upload"
fi

# Clean up old backups
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "backup_*.meta.json" -mtime +${RETENTION_DAYS} -delete

# Verify backup integrity
log_info "Verifying backup integrity..."
if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log_info "Backup integrity verified successfully"
else
    log_error "Backup integrity check failed!"
    exit 1
fi

# Summary
log_info "=========================================="
log_info "Backup completed successfully!"
log_info "Backup file: ${BACKUP_FILE}"
log_info "Backup size: ${BACKUP_SIZE}"
log_info "Timestamp: ${TIMESTAMP}"
log_info "=========================================="

# Send notification (optional)
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ AgentGuard database backup completed: ${BACKUP_NAME} (${BACKUP_SIZE})\"}" \
        2>/dev/null || true
fi

exit 0

