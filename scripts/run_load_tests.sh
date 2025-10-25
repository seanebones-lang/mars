#!/bin/bash
#
# Run Complete Load Testing Suite
# P0-Critical: Validate all performance targets
#
# Usage: ./scripts/run_load_tests.sh [staging|production]
#

set -e

# Configuration
ENVIRONMENT="${1:-staging}"
RESULTS_DIR="./load_test_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

# Set environment-specific URLs
if [ "$ENVIRONMENT" = "staging" ]; then
    API_URL="https://agentguard-api-staging.onrender.com"
    WS_URL="wss://agentguard-api-staging.onrender.com/ws/monitor"
else
    API_URL="https://agentguard-api.onrender.com"
    WS_URL="wss://agentguard-api.onrender.com/ws/monitor"
fi

log_info "=========================================="
log_info "AgentGuard Load Testing Suite"
log_info "=========================================="
log_info "Environment: $ENVIRONMENT"
log_info "API URL: $API_URL"
log_info "WebSocket URL: $WS_URL"
log_info "Results Directory: $RESULTS_DIR"
log_info "=========================================="

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    log_error "Locust not installed. Installing..."
    pip install locust
fi

# Check if websockets is installed
if ! python -c "import websockets" 2>/dev/null; then
    log_error "websockets not installed. Installing..."
    pip install websockets
fi

# Test 1: Baseline Performance Test
log_step "Test 1/5: Baseline Performance (100 users, 2 minutes)"
log_info "Target: Establish baseline metrics"

locust -f tests/load/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 2m \
    --host="$API_URL" \
    --html="$RESULTS_DIR/baseline_${TIMESTAMP}.html" \
    --csv="$RESULTS_DIR/baseline_${TIMESTAMP}" \
    2>&1 | tee "$RESULTS_DIR/baseline_${TIMESTAMP}.log"

log_info "✓ Baseline test complete"
sleep 10

# Test 2: Target Load Test
log_step "Test 2/5: Target Load (1,000 users, 5 minutes)"
log_info "Target: 1,000+ req/sec, P95 < 200ms"

locust -f tests/load/locustfile.py \
    --headless \
    --users 1000 \
    --spawn-rate 100 \
    --run-time 5m \
    --host="$API_URL" \
    --html="$RESULTS_DIR/target_load_${TIMESTAMP}.html" \
    --csv="$RESULTS_DIR/target_load_${TIMESTAMP}" \
    2>&1 | tee "$RESULTS_DIR/target_load_${TIMESTAMP}.log"

log_info "✓ Target load test complete"
sleep 10

# Test 3: Stress Test
log_step "Test 3/5: Stress Test (5,000 users, 3 minutes)"
log_info "Target: Find breaking point"

locust -f tests/load/locustfile.py \
    --headless \
    --users 5000 \
    --spawn-rate 500 \
    --run-time 3m \
    --host="$API_URL" \
    --user-classes StressTestUser \
    --html="$RESULTS_DIR/stress_${TIMESTAMP}.html" \
    --csv="$RESULTS_DIR/stress_${TIMESTAMP}" \
    2>&1 | tee "$RESULTS_DIR/stress_${TIMESTAMP}.log"

log_info "✓ Stress test complete"
sleep 10

# Test 4: Spike Test
log_step "Test 4/5: Spike Test (0 → 2,000 → 0 users)"
log_info "Target: Handle sudden traffic spikes"

locust -f tests/load/locustfile.py \
    --headless \
    --users 2000 \
    --spawn-rate 1000 \
    --run-time 2m \
    --host="$API_URL" \
    --user-classes SpikeTestUser \
    --html="$RESULTS_DIR/spike_${TIMESTAMP}.html" \
    --csv="$RESULTS_DIR/spike_${TIMESTAMP}" \
    2>&1 | tee "$RESULTS_DIR/spike_${TIMESTAMP}.log"

log_info "✓ Spike test complete"
sleep 10

# Test 5: WebSocket Load Test
log_step "Test 5/5: WebSocket Load Test (1,000 concurrent connections)"
log_info "Target: 10,000+ concurrent WebSocket connections"

python tests/load/websocket_load_test.py \
    --url "$WS_URL" \
    --connections 1000 \
    --duration 120 \
    2>&1 | tee "$RESULTS_DIR/websocket_${TIMESTAMP}.log"

log_info "✓ WebSocket test complete"

# Generate Summary Report
log_info "=========================================="
log_info "Generating Summary Report"
log_info "=========================================="

SUMMARY_FILE="$RESULTS_DIR/summary_${TIMESTAMP}.md"

cat > "$SUMMARY_FILE" <<EOF
# Load Test Summary Report

**Environment**: $ENVIRONMENT  
**Date**: $(date)  
**API URL**: $API_URL  
**WebSocket URL**: $WS_URL

---

## Test Results

### Test 1: Baseline Performance
- **Users**: 100
- **Duration**: 2 minutes
- **Results**: See \`baseline_${TIMESTAMP}.html\`

### Test 2: Target Load
- **Users**: 1,000
- **Duration**: 5 minutes
- **Target**: 1,000+ req/sec, P95 < 200ms
- **Results**: See \`target_load_${TIMESTAMP}.html\`

### Test 3: Stress Test
- **Users**: 5,000
- **Duration**: 3 minutes
- **Target**: Find breaking point
- **Results**: See \`stress_${TIMESTAMP}.html\`

### Test 4: Spike Test
- **Users**: 0 → 2,000 → 0
- **Duration**: 2 minutes
- **Target**: Handle sudden spikes
- **Results**: See \`spike_${TIMESTAMP}.html\`

### Test 5: WebSocket Load
- **Connections**: 1,000 concurrent
- **Duration**: 2 minutes
- **Target**: 10,000+ concurrent connections
- **Results**: See \`websocket_${TIMESTAMP}.log\`

---

## Performance Targets

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| Requests/sec | > 1,000 | TBD | ⏳ |
| P95 Response Time | < 200ms | TBD | ⏳ |
| Failure Rate | < 1% | TBD | ⏳ |
| Concurrent Users | 10,000+ | TBD | ⏳ |
| WebSocket Connections | 10,000+ | TBD | ⏳ |

---

## Files Generated

EOF

# List all generated files
ls -lh "$RESULTS_DIR"/*${TIMESTAMP}* >> "$SUMMARY_FILE"

log_info "=========================================="
log_info "✅ All Load Tests Complete!"
log_info "=========================================="
log_info "Results saved to: $RESULTS_DIR"
log_info "Summary report: $SUMMARY_FILE"
log_info ""
log_info "View HTML reports:"
log_info "  - Baseline: $RESULTS_DIR/baseline_${TIMESTAMP}.html"
log_info "  - Target Load: $RESULTS_DIR/target_load_${TIMESTAMP}.html"
log_info "  - Stress: $RESULTS_DIR/stress_${TIMESTAMP}.html"
log_info "  - Spike: $RESULTS_DIR/spike_${TIMESTAMP}.html"
log_info "=========================================="

# Send notification if Slack webhook configured
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✅ Load testing complete for $ENVIRONMENT environment. Results: $RESULTS_DIR\"}" \
        2>/dev/null || true
fi

exit 0

