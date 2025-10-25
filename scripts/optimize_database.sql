-- Database Optimization Script
-- P1-2: Performance optimization through indexes and query optimization
--
-- Usage: psql $DATABASE_URL -f scripts/optimize_database.sql

\echo 'AgentGuard Database Optimization'
\echo '================================='
\echo ''

-- Create indexes for common queries
\echo 'Creating indexes...'

-- Index on detection_results for agent_id lookups
CREATE INDEX IF NOT EXISTS idx_detection_results_agent_id 
ON detection_results(agent_id);

-- Index on detection_results for created_at (time-based queries)
CREATE INDEX IF NOT EXISTS idx_detection_results_created_at 
ON detection_results(created_at DESC);

-- Composite index for agent_id + created_at (common query pattern)
CREATE INDEX IF NOT EXISTS idx_detection_results_agent_created 
ON detection_results(agent_id, created_at DESC);

-- Index on detection_results for hallucination_risk (filtering)
CREATE INDEX IF NOT EXISTS idx_detection_results_risk 
ON detection_results(hallucination_risk);

-- Index on audit_log for timestamp
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
ON audit_log(timestamp DESC) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log');

-- Index on audit_log for user_id
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id 
ON audit_log(user_id) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log');

-- Index on sessions for user_id
CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
ON sessions(user_id) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sessions');

-- Index on sessions for expires_at (cleanup queries)
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
ON sessions(expires_at) WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sessions');

\echo 'Indexes created successfully.'
\echo ''

-- Analyze tables for query planner
\echo 'Analyzing tables...'
ANALYZE detection_results;
ANALYZE audit_log;
ANALYZE sessions;

\echo 'Table analysis complete.'
\echo ''

-- Vacuum tables to reclaim space
\echo 'Vacuuming tables...'
VACUUM ANALYZE detection_results;
VACUUM ANALYZE audit_log;
VACUUM ANALYZE sessions;

\echo 'Vacuum complete.'
\echo ''

-- Show table sizes
\echo 'Table sizes:'
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''

-- Show index usage statistics
\echo 'Index usage statistics:'
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY idx_scan DESC;

\echo ''

-- Show slow queries (if pg_stat_statements is enabled)
\echo 'Top 10 slowest queries (if pg_stat_statements enabled):'
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_time DESC
LIMIT 10;

\echo ''
\echo 'Database optimization complete!'
\echo ''
\echo 'Recommendations:'
\echo '1. Monitor index usage with: SELECT * FROM pg_stat_user_indexes;'
\echo '2. Check for unused indexes periodically'
\echo '3. Run VACUUM ANALYZE weekly'
\echo '4. Monitor table bloat'
\echo '5. Consider partitioning large tables (>10M rows)'

