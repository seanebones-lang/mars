#!/bin/bash
#
# Database Restore Script for AgentGuard
# P0-Critical: Disaster recovery and database restoration
#
# Usage: ./scripts/restore_database.sh <backup_name>
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/agentguard}"
S3_BUCKET="${S3_BUCKET:-agentguard-backups}"

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

# Check arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <backup_name>"
    log_info "Available backups:"
    ls -lh "${BACKUP_DIR}"/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    log_error "DATABASE_URL environment variable not set"
    exit 1
fi

# Parse DATABASE_URL
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

log_warn "=========================================="
log_warn "DATABASE RESTORE OPERATION"
log_warn "=========================================="
log_warn "This will OVERWRITE the current database!"
log_warn "Database: ${DB_NAME}"
log_warn "Host: ${DB_HOST}"
log_warn "Backup: ${BACKUP_NAME}"
log_warn "=========================================="

# Check if backup file exists locally
if [ ! -f "${BACKUP_FILE}" ]; then
    log_warn "Backup file not found locally: ${BACKUP_FILE}"
    
    # Try to download from S3
    if command -v aws &> /dev/null && [ -n "${S3_BUCKET}" ]; then
        log_info "Attempting to download from S3..."
        if aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_NAME}.sql.gz" "${BACKUP_FILE}"; then
            log_info "Backup downloaded from S3 successfully"
        else
            log_error "Failed to download backup from S3"
            exit 1
        fi
    else
        log_error "Backup file not found and S3 download not available"
        exit 1
    fi
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
if ! gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log_error "Backup file is corrupted!"
    exit 1
fi
log_info "Backup integrity verified"

# Confirmation prompt
read -p "Are you sure you want to restore? This cannot be undone! (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    log_warn "Restore cancelled by user"
    exit 0
fi

# Create a safety backup before restore
SAFETY_BACKUP="${BACKUP_DIR}/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
log_info "Creating safety backup before restore: ${SAFETY_BACKUP}"
export PGPASSWORD="${DB_PASS}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom --compress=9 --file="${SAFETY_BACKUP}" || log_warn "Safety backup failed"

# Perform restore
log_info "Starting database restore..."
log_info "Dropping existing database connections..."

# Terminate existing connections
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${DB_NAME}'
  AND pid <> pg_backend_pid();
EOF

# Drop and recreate database
log_info "Dropping and recreating database..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME};
EOF

# Restore from backup
log_info "Restoring database from backup..."
if pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --verbose --clean --if-exists "${BACKUP_FILE}"; then
    log_info "Database restored successfully!"
else
    log_error "Database restore failed!"
    log_error "Safety backup available at: ${SAFETY_BACKUP}"
    exit 1
fi

unset PGPASSWORD

# Verify restore
log_info "Verifying restore..."
export PGPASSWORD="${DB_PASS}"
TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
unset PGPASSWORD

log_info "Restored ${TABLE_COUNT} tables"

# Summary
log_info "=========================================="
log_info "Restore completed successfully!"
log_info "Database: ${DB_NAME}"
log_info "Backup: ${BACKUP_NAME}"
log_info "Tables restored: ${TABLE_COUNT}"
log_info "Safety backup: ${SAFETY_BACKUP}"
log_info "=========================================="

# Send notification
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"⚠️ AgentGuard database restored from backup: ${BACKUP_NAME}\"}" \
        2>/dev/null || true
fi

exit 0

