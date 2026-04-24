-- SQL Cleanup Script for Resume Screening System
-- Run these queries in sequence to remove duplicate entries
-- WARNING: Backup your database before running these commands!

-- Step 1: Check current duplicates
SELECT email, COUNT(*) as duplicate_count
FROM all_submissions
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Step 2: Create backup table (optional but recommended)
CREATE TABLE all_submissions_backup AS SELECT * FROM all_submissions;

-- Step 3: Delete duplicates, keeping only the most recent entry for each email
DELETE FROM all_submissions
WHERE id NOT IN (
    SELECT MAX(id)
    FROM all_submissions
    GROUP BY email
);

-- Step 4: Verify cleanup
SELECT email, COUNT(*) as count
FROM all_submissions
GROUP BY email
HAVING COUNT(*) > 1;

-- Step 5: Get final statistics
SELECT
    (SELECT COUNT(*) FROM all_submissions) as final_count,
    (SELECT COUNT(*) FROM all_submissions_backup) as original_count,
    ((SELECT COUNT(*) FROM all_submissions_backup) - (SELECT COUNT(*) FROM all_submissions)) as duplicates_removed;

-- Optional: Drop backup table after verification
-- DROP TABLE all_submissions_backup;