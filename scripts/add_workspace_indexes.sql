-- AgentGuard Workspace Database Optimization
-- Add indexes for improved query performance
-- Run this script after workspace tables are created

-- ============================================
-- WORKSPACE INDEXES
-- ============================================

-- Projects table indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_updated 
ON projects(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_projects_status 
ON projects(user_id, status);

CREATE INDEX IF NOT EXISTS idx_projects_tags 
ON projects USING GIN(tags);

COMMENT ON INDEX idx_projects_user_updated IS 'Optimize project listing by user with recent first';
COMMENT ON INDEX idx_projects_status IS 'Filter projects by status';
COMMENT ON INDEX idx_projects_tags IS 'Search projects by tags';

-- Favorites table indexes
CREATE INDEX IF NOT EXISTS idx_favorites_user_type 
ON favorites(user_id, item_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_favorites_item 
ON favorites(item_type, item_id);

COMMENT ON INDEX idx_favorites_user_type IS 'List favorites by user and type';
COMMENT ON INDEX idx_favorites_item IS 'Check if item is favorited';

-- Workspace settings indexes
CREATE INDEX IF NOT EXISTS idx_workspace_settings_user_key 
ON workspace_settings(user_id, key);

CREATE INDEX IF NOT EXISTS idx_workspace_settings_category 
ON workspace_settings(user_id, category);

COMMENT ON INDEX idx_workspace_settings_user_key IS 'Fast lookup of specific settings';
COMMENT ON INDEX idx_workspace_settings_category IS 'List settings by category';

-- API keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_active 
ON api_keys(user_id, is_active);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash 
ON api_keys(key_hash);

CREATE INDEX IF NOT EXISTS idx_api_keys_expires 
ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

COMMENT ON INDEX idx_api_keys_user_active IS 'List active keys for user';
COMMENT ON INDEX idx_api_keys_hash IS 'Fast API key verification';
COMMENT ON INDEX idx_api_keys_expires IS 'Find expired keys for cleanup';

-- Activity logs indexes
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created 
ON activity_logs(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_logs_type 
ON activity_logs(user_id, activity_type, created_at DESC);

COMMENT ON INDEX idx_activity_logs_user_created IS 'Recent activity feed';
COMMENT ON INDEX idx_activity_logs_type IS 'Filter activity by type';

-- ============================================
-- EXISTING SYSTEM INDEXES
-- ============================================

-- Test results indexes (if not exists)
CREATE INDEX IF NOT EXISTS idx_test_results_timestamp 
ON test_results(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_test_results_user 
ON test_results(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_test_results_risk 
ON test_results(hallucination_risk) WHERE hallucination_risk > 0.7;

COMMENT ON INDEX idx_test_results_timestamp IS 'Recent tests first';
COMMENT ON INDEX idx_test_results_user IS 'User test history';
COMMENT ON INDEX idx_test_results_risk IS 'High-risk results';

-- Webhook deliveries indexes
CREATE INDEX IF NOT EXISTS idx_webhooks_status 
ON webhook_deliveries(status, created_at);

CREATE INDEX IF NOT EXISTS idx_webhooks_webhook_id 
ON webhook_deliveries(webhook_id, created_at DESC);

COMMENT ON INDEX idx_webhooks_status IS 'Failed webhook cleanup';
COMMENT ON INDEX idx_webhooks_webhook_id IS 'Webhook delivery history';

-- User sessions indexes (if applicable)
CREATE INDEX IF NOT EXISTS idx_user_sessions_user 
ON user_sessions(user_id, expires_at) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_sessions_token 
ON user_sessions(session_token) WHERE is_active = true;

-- ============================================
-- PERFORMANCE OPTIMIZATION
-- ============================================

-- Analyze tables for query planner
ANALYZE projects;
ANALYZE favorites;
ANALYZE workspace_settings;
ANALYZE api_keys;
ANALYZE activity_logs;
ANALYZE test_results;
ANALYZE webhook_deliveries;

-- Vacuum tables to reclaim space
VACUUM ANALYZE projects;
VACUUM ANALYZE favorites;
VACUUM ANALYZE workspace_settings;
VACUUM ANALYZE api_keys;
VACUUM ANALYZE activity_logs;

-- ============================================
-- QUERY OPTIMIZATION SETTINGS
-- ============================================

-- Set statistics target for better query planning
ALTER TABLE projects ALTER COLUMN user_id SET STATISTICS 1000;
ALTER TABLE favorites ALTER COLUMN user_id SET STATISTICS 1000;
ALTER TABLE api_keys ALTER COLUMN key_hash SET STATISTICS 1000;
ALTER TABLE activity_logs ALTER COLUMN user_id SET STATISTICS 1000;

-- ============================================
-- MAINTENANCE QUERIES
-- ============================================

-- View index usage statistics
-- Run this periodically to identify unused indexes
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
*/

-- View table sizes
/*
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
*/

-- View slow queries (requires pg_stat_statements extension)
/*
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
*/

-- ============================================
-- CLEANUP JOBS (Run periodically)
-- ============================================

-- Delete expired API keys (run daily)
/*
DELETE FROM api_keys 
WHERE expires_at < NOW() 
AND is_active = false;
*/

-- Archive old activity logs (run monthly)
/*
DELETE FROM activity_logs 
WHERE created_at < NOW() - INTERVAL '90 days';
*/

-- Clean up old webhook deliveries (run weekly)
/*
DELETE FROM webhook_deliveries 
WHERE created_at < NOW() - INTERVAL '30 days'
AND status = 'delivered';
*/

-- ============================================
-- VERIFICATION
-- ============================================

-- Verify all indexes were created
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN ('projects', 'favorites', 'workspace_settings', 'api_keys', 'activity_logs')
ORDER BY tablename, indexname;

-- Check index sizes
SELECT 
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;

COMMIT;

