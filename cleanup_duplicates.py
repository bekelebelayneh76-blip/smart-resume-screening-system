#!/usr/bin/env python3
"""
Database Cleanup Script for Resume Screening System
This script removes duplicate entries from the all_submissions table,
keeping only the most recent entry for each unique email address.
"""

import sqlite3
from sqlite3 import Error

def get_sqlite_connection():
    """Establish a connection to the SQLite database."""
    try:
        connection = sqlite3.connect('resume_system.db')
        return connection
    except Error as e:
        print(f"Error connecting to SQLite: {e}")
        return None

def cleanup_duplicates():
    """Remove duplicate entries, keeping only the most recent for each email."""
    connection = get_sqlite_connection()
    if not connection:
        return False

    cursor = connection.cursor()
    try:
        # First, let's see how many duplicates we have
        cursor.execute("""
            SELECT email, COUNT(*) as count
            FROM all_submissions
            GROUP BY email
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)

        duplicates = cursor.fetchall()
        print(f"Found {len(duplicates)} emails with duplicates:")

        total_duplicates = 0
        for email, count in duplicates:
            print(f"  {email}: {count} entries")
            total_duplicates += count - 1  # -1 because we keep one

        print(f"\nTotal duplicate entries to remove: {total_duplicates}")

        if total_duplicates == 0:
            print("No duplicates found. Database is clean.")
            return True

        # Ask for confirmation
        confirm = input(f"\nThis will delete {total_duplicates} duplicate entries. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Cleanup cancelled.")
            return False

        # Create a temporary table with unique emails (keeping most recent)
        print("Creating temporary table with unique entries...")
        cursor.execute("""
            CREATE TABLE temp_submissions AS
            SELECT *
            FROM all_submissions
            WHERE id IN (
                SELECT MAX(id)
                FROM all_submissions
                GROUP BY email
            )
        """)

        # Get counts before cleanup
        cursor.execute("SELECT COUNT(*) FROM all_submissions")
        original_count = cursor.fetchone()[0]

        # Drop original table and rename temp table
        cursor.execute("DROP TABLE all_submissions")
        cursor.execute("ALTER TABLE temp_submissions RENAME TO all_submissions")

        # Recreate indexes and constraints
        cursor.execute("CREATE UNIQUE INDEX idx_email ON all_submissions(email)")

        # Get counts after cleanup
        cursor.execute("SELECT COUNT(*) FROM all_submissions")
        final_count = cursor.fetchone()[0]

        connection.commit()

        print("\nCleanup completed successfully!")
        print(f"Original entries: {original_count}")
        print(f"Final entries: {final_count}")
        print(f"Duplicates removed: {original_count - final_count}")

        return True

    except Error as e:
        print(f"Error during cleanup: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def show_statistics():
    """Show database statistics."""
    connection = get_sqlite_connection()
    if not connection:
        return

    cursor = connection.cursor()
    try:
        # Total submissions
        cursor.execute("SELECT COUNT(*) FROM all_submissions")
        total = cursor.fetchone()[0]
        print(f"Total submissions: {total}")

        # Unique emails
        cursor.execute("SELECT COUNT(DISTINCT email) FROM all_submissions")
        unique = cursor.fetchone()[0]
        print(f"Unique emails: {unique}")

        # Check for remaining duplicates
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT email, COUNT(*) as count
                FROM all_submissions
                GROUP BY email
                HAVING COUNT(*) > 1
            )
        """)
        remaining_duplicates = cursor.fetchone()[0]
        print(f"Emails with duplicates: {remaining_duplicates}")

        if remaining_duplicates > 0:
            print("\nWarning: Some duplicates still exist!")
        else:
            print("\n✅ No duplicates found - database is clean.")

    except Error as e:
        print(f"Error getting statistics: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("Resume Screening System - Database Cleanup Tool")
    print("=" * 50)

    show_statistics()

    print("\nStarting cleanup process...")
    success = cleanup_duplicates()

    if success:
        print("\n" + "=" * 50)
        show_statistics()
    else:
        print("Cleanup failed or was cancelled.")