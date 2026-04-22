#!/usr/bin/env python
"""
Quick script to check and fix audit migration issues before running migrations.
This should be run before 'python manage.py migrate' in start.sh
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings')
django.setup()

from django.db import connection


def check_and_fix():
    """Check if audit tables exist, if not clear migration records."""
    try:
        with connection.cursor() as cursor:
            # Check if audit_transactionlog table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'audit_transactionlog'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            # Check if audit migrations are recorded
            cursor.execute("""
                SELECT COUNT(*) FROM django_migrations WHERE app = 'audit';
            """)
            migration_count = cursor.fetchone()[0]
            
            # If migrations are recorded but table doesn't exist, clear the records
            if migration_count > 0 and not table_exists:
                print("⚠️  Detected inconsistent migration state for audit app")
                print("   Migrations recorded but tables don't exist")
                print("   Clearing audit migration records...")
                
                cursor.execute("DELETE FROM django_migrations WHERE app = 'audit';")
                print("✓ Cleared audit migration records")
                print("   Migrations will be re-run from scratch")
            elif table_exists:
                print("✓ Audit tables exist, migration state OK")
            else:
                print("✓ No audit migrations applied yet, will run fresh")
                
    except Exception as e:
        print(f"⚠️  Could not check migration state: {e}")
        print("   Continuing anyway...")


if __name__ == '__main__':
    check_and_fix()
