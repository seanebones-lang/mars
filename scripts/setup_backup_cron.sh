#!/bin/bash
#
# Setup Automated Backup Cron Jobs
# P0-Critical: Configure automatic daily backups
#
# Usage: ./scripts/setup_backup_cron.sh
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up automated database backups...${NC}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create cron job for daily backups at 2 AM
CRON_JOB="0 2 * * * cd ${PROJECT_DIR} && /bin/bash ${SCRIPT_DIR}/backup_database.sh >> /var/log/agentguard/backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup_database.sh"; then
    echo -e "${YELLOW}Backup cron job already exists${NC}"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Daily backup cron job added (runs at 2 AM)${NC}"
fi

# Create log directory
sudo mkdir -p /var/log/agentguard
sudo chown $USER:$USER /var/log/agentguard

# Create backup directory
sudo mkdir -p /var/backups/agentguard
sudo chown $USER:$USER /var/backups/agentguard

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Automated backups configured!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Schedule: Daily at 2:00 AM"
echo "Backup location: /var/backups/agentguard"
echo "Log location: /var/log/agentguard/backup.log"
echo ""
echo "To view cron jobs: crontab -l"
echo "To view backup logs: tail -f /var/log/agentguard/backup.log"
echo "To run backup manually: ${SCRIPT_DIR}/backup_database.sh"

exit 0

