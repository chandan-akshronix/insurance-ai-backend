-- Migration script to add 'role' column to users table
-- Run this SQL script on your PostgreSQL database

-- Step 1: Add the role column with default value 'user'
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user';

-- Step 2: Update existing users to have 'user' role (if any are NULL)
UPDATE users 
SET role = 'user' 
WHERE role IS NULL;

-- Step 3: Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'role';

