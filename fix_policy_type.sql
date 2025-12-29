-- Fix Policy Type Enum - Update types to match backend enum values
-- Run this SQL script to fix the type enum mismatch

-- Update policy types to use enum values
UPDATE policy 
SET type = 'life_insurance' 
WHERE type = 'life';

UPDATE policy 
SET type = 'vehicle_insurance' 
WHERE type = 'vehicle';

UPDATE policy 
SET type = 'health_insurance' 
WHERE type = 'health';

-- Verify the update
SELECT 
    type, 
    COUNT(*) as count 
FROM policy 
GROUP BY type 
ORDER BY count DESC;

