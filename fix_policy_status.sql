-- Fix Policy Status - Set all NULL statuses to 'Active'
-- Run this SQL script to fix the status field issue

-- Option 1: Set all NULL statuses to 'Active'
UPDATE policy 
SET status = 'Active' 
WHERE status IS NULL OR status = '';

-- Verify the update
SELECT 
    status, 
    COUNT(*) as count 
FROM policy 
GROUP BY status 
ORDER BY count DESC;

-- Check result
SELECT COUNT(*) as total_policies,
       COUNT(CASE WHEN status IS NOT NULL AND status != '' THEN 1 END) as policies_with_status,
       COUNT(CASE WHEN status IS NULL OR status = '' THEN 1 END) as policies_without_status
FROM policy;

