#!/bin/bash
# AgentGuard Automated Database Backup Setup
# Configures daily and hourly backups with retention policies

set -e

echo "=========================================="
echo "AgentGuard Database Backup Setup"
echo "=========================================="

# Configuration
BACKUP_DIR="/var/backups/agentguard"
S3_BUCKET="${AWS_S3_BUCKET:-agentguard-backups}"
RETENTION_DAYS=30
HOURLY_RETENTION=7  # Keep hourly backups for 7 days
DATABASE_URL="${DATABASE_URL}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create backup directories
echo -e "${YELLOW}Creating backup directories...${NC}"
sudo mkdir -p ${BACKUP_DIR}/{daily,hourly,logs}
sudo chown -R $(whoami):$(whoami) ${BACKUP_DIR}

# Install required tools
echo -e "${YELLOW}Installing required tools...${NC}"
if ! command -v pg_dump &> /dev/null; then
    echo "Installing PostgreSQL client..."
    sudo apt-get update
    sudo apt-get install -y postgresql-client
fi

if ! command -v aws &> /dev/null; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Create backup script
echo -e "${YELLOW}Creating backup script...${NC}"
cat > ${BACKUP_DIR}/backup.sh << 'EOF'
#!/bin/bash
# AgentGuard Database Backup Script

set -e

# Configuration
BACKUP_TYPE=$1  # daily or hourly
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/agentguard"
LOG_FILE="${BACKUP_DIR}/logs/backup_${TIMESTAMP}.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a ${LOG_FILE}
}

log "Starting ${BACKUP_TYPE} backup..."

# Extract database connection details
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\(.*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/.*:\(.*\)@.*/\1/p')

# Backup filename
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_TYPE}/agentguard_${BACKUP_TYPE}_${TIMESTAMP}.sql.gz"

# Perform backup
log "Creating backup: ${BACKUP_FILE}"
PGPASSWORD="${DB_PASS}" pg_dump \
    -h ${DB_HOST} \
    -p ${DB_PORT} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    --format=custom \
    --compress=9 \
    --verbose \
    2>> ${LOG_FILE} | gzip > ${BACKUP_FILE}

# Verify backup
if [ -f "${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    log "Backup created successfully: ${BACKUP_SIZE}"
else
    log "ERROR: Backup failed!"
    exit 1
fi

# Upload to S3 (if configured)
if [ ! -z "${AWS_S3_BUCKET}" ]; then
    log "Uploading to S3: s3://${AWS_S3_BUCKET}/${BACKUP_TYPE}/"
    aws s3 cp ${BACKUP_FILE} s3://${AWS_S3_BUCKET}/${BACKUP_TYPE}/ \
        --storage-class STANDARD_IA \
        2>> ${LOG_FILE}
    
    if [ $? -eq 0 ]; then
        log "S3 upload successful"
    else
        log "WARNING: S3 upload failed"
    fi
fi

# Cleanup old backups
if [ "${BACKUP_TYPE}" == "daily" ]; then
    RETENTION_DAYS=30
elif [ "${BACKUP_TYPE}" == "hourly" ]; then
    RETENTION_DAYS=7
fi

log "Cleaning up backups older than ${RETENTION_DAYS} days..."
find ${BACKUP_DIR}/${BACKUP_TYPE}/ -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# Cleanup old logs (keep 30 days)
find ${BACKUP_DIR}/logs/ -name "*.log" -mtime +30 -delete

log "Backup completed successfully!"

# Send notification (optional)
if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST ${SLACK_WEBHOOK_URL} \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ AgentGuard ${BACKUP_TYPE} backup completed: ${BACKUP_SIZE}\"}" \
        2>> ${LOG_FILE}
fi

exit 0
EOF

chmod +x ${BACKUP_DIR}/backup.sh

# Create restore script
echo -e "${YELLOW}Creating restore script...${NC}"
cat > ${BACKUP_DIR}/restore.sh << 'EOF'
#!/bin/bash
# AgentGuard Database Restore Script

set -e

BACKUP_FILE=$1

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /var/backups/agentguard/daily/agentguard_daily_20251105_020000.sql.gz"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "=========================================="
echo "AgentGuard Database Restore"
echo "=========================================="
echo "Backup file: ${BACKUP_FILE}"
echo ""
echo "WARNING: This will overwrite the current database!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Extract database connection details
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\(.*\):.*/\1/p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's/.*:\/\/.*:\(.*\)@.*/\1/p')

echo "Restoring database..."
gunzip -c ${BACKUP_FILE} | PGPASSWORD="${DB_PASS}" pg_restore \
    -h ${DB_HOST} \
    -p ${DB_PORT} \
    -U ${DB_USER} \
    -d ${DB_NAME} \
    --clean \
    --if-exists \
    --verbose

echo "Restore completed successfully!"
exit 0
EOF

chmod +x ${BACKUP_DIR}/restore.sh

# Setup cron jobs
echo -e "${YELLOW}Setting up cron jobs...${NC}"

# Remove existing AgentGuard backup cron jobs
crontab -l 2>/dev/null | grep -v "agentguard backup" | crontab - || true

# Add new cron jobs
(crontab -l 2>/dev/null; echo "# AgentGuard automated backups") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * ${BACKUP_DIR}/backup.sh daily # agentguard backup daily") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * ${BACKUP_DIR}/backup.sh hourly # agentguard backup hourly") | crontab -

echo -e "${GREEN}✓ Cron jobs configured:${NC}"
echo "  - Daily backup: 2:00 AM"
echo "  - Hourly backup: Every hour"

# Test backup
echo -e "${YELLOW}Running test backup...${NC}"
${BACKUP_DIR}/backup.sh daily

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test backup successful!${NC}"
else
    echo -e "${RED}✗ Test backup failed!${NC}"
    exit 1
fi

# Create backup monitoring script
cat > ${BACKUP_DIR}/check_backups.sh << 'EOF'
#!/bin/bash
# Check backup health and send alerts if needed

BACKUP_DIR="/var/backups/agentguard"
ALERT_THRESHOLD_HOURS=26  # Alert if no backup in 26 hours

# Check latest daily backup
LATEST_DAILY=$(find ${BACKUP_DIR}/daily -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
if [ -z "${LATEST_DAILY}" ]; then
    echo "ERROR: No daily backups found!"
    exit 1
fi

LATEST_DAILY_AGE=$(( ($(date +%s) - $(stat -c %Y "${LATEST_DAILY}")) / 3600 ))

if [ ${LATEST_DAILY_AGE} -gt ${ALERT_THRESHOLD_HOURS} ]; then
    echo "WARNING: Latest backup is ${LATEST_DAILY_AGE} hours old!"
    
    # Send alert
    if [ ! -z "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST ${SLACK_WEBHOOK_URL} \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"⚠️ AgentGuard backup is ${LATEST_DAILY_AGE} hours old!\"}"
    fi
    exit 1
fi

echo "✓ Backups are healthy (latest: ${LATEST_DAILY_AGE} hours ago)"
exit 0
EOF

chmod +x ${BACKUP_DIR}/check_backups.sh

# Add backup monitoring to cron (check every 6 hours)
(crontab -l 2>/dev/null; echo "0 */6 * * * ${BACKUP_DIR}/check_backups.sh # agentguard backup monitoring") | crontab -

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Backup setup complete!${NC}"
echo "=========================================="
echo ""
echo "Backup Configuration:"
echo "  - Backup directory: ${BACKUP_DIR}"
echo "  - Daily backups: 2:00 AM (kept for 30 days)"
echo "  - Hourly backups: Every hour (kept for 7 days)"
echo "  - S3 bucket: ${S3_BUCKET}"
echo "  - Monitoring: Every 6 hours"
echo ""
echo "Scripts created:"
echo "  - Backup: ${BACKUP_DIR}/backup.sh"
echo "  - Restore: ${BACKUP_DIR}/restore.sh"
echo "  - Monitor: ${BACKUP_DIR}/check_backups.sh"
echo ""
echo "To restore a backup:"
echo "  ${BACKUP_DIR}/restore.sh <backup_file>"
echo ""
echo "To list backups:"
echo "  ls -lh ${BACKUP_DIR}/daily/"
echo "  ls -lh ${BACKUP_DIR}/hourly/"
echo ""
echo "To check backup status:"
echo "  ${BACKUP_DIR}/check_backups.sh"
echo ""

