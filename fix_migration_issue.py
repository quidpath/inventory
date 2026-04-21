#!/usr/bin/env python
"""
Script to fix the UUID migration issue in the inventory service.
This script should be run on the server to reset the migration state.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings.stage')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection


def fix_migration_issue():
    """
    Fix the UUID migration issue by resetting the problematic migration.
    """
    print("🔧 Fixing UUID migration issue...")
    
    try:
        # Step 1: Mark the problematic migration as not applied
        print("📝 Marking migration 0002_change_ids_to_uuid as unapplied...")
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM django_migrations 
                WHERE app = 'audit' AND name = '0002_change_ids_to_uuid';
            """)
        
        # Step 2: Drop and recreate the audit tables to ensure clean state
        print("🗑️  Dropping existing audit tables...")
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS audit_transactionlog CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS audit_notification CASCADE;")
        
        # Step 3: Reset migrations for audit app
        print("🔄 Resetting audit app migrations...")
        execute_from_command_line(['manage.py', 'migrate', 'audit', 'zero', '--fake'])
        
        # Step 4: Run migrations again
        print("▶️  Running migrations...")
        execute_from_command_line(['manage.py', 'migrate', 'audit'])
        
        print("✅ Migration issue fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing migration: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = fix_migration_issue()
    sys.exit(0 if success else 1)