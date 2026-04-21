#!/bin/bash

# Script to fix the UUID migration issue in inventory service
# Run this inside the inventory-backend-stage container

echo "🔧 Fixing UUID migration issue for inventory service..."

# Step 1: Reset the audit app migrations
echo "📝 Resetting audit migrations..."
python manage.py migrate audit zero --fake

# Step 2: Drop the audit tables manually
echo "🗑️  Dropping audit tables..."
python manage.py shell << 'EOF'
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS audit_transactionlog CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS audit_notification CASCADE;")
    print("Tables dropped successfully")
EOF

# Step 3: Remove migration record from database
echo "🧹 Cleaning migration records..."
python manage.py shell << 'EOF'
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'audit' AND name = '0002_change_ids_to_uuid';")
    print("Migration records cleaned")
EOF

# Step 4: Run migrations fresh
echo "▶️  Running fresh migrations..."
python manage.py migrate audit

echo "✅ Migration issue fixed successfully!"