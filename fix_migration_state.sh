#!/bin/bash
# Fix migration state for inventory services
# This script fixes the migration state after removing the problematic 0002 migration

echo "=== Fixing Inventory Migration State ==="

# Function to fix migration for a container
fix_migration() {
    local container=$1
    echo ""
    echo "Fixing migration state for $container..."
    
    # Check if container exists and is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "⚠️  Container $container not found or not running"
        return 1
    fi
    
    # Delete the problematic migration record
    echo "Removing migration record for 0002_change_ids_to_uuid..."
    docker exec $container python manage.py shell << 'EOF'
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        DELETE FROM django_migrations 
        WHERE app = 'audit' 
        AND name = '0002_change_ids_to_uuid';
    """)
    cursor.execute("""
        DELETE FROM django_migrations 
        WHERE app = 'audit' 
        AND name = '0003_fix_uuid_columns';
    """)
    print("✓ Removed old migration records")
EOF
    
    # Run migrations
    echo "Running migrations..."
    docker exec $container python manage.py migrate audit
    
    echo "✓ Migration state fixed for $container"
}

# Fix staging
echo ""
echo "=== STAGING ENVIRONMENT ==="
fix_migration "inventory-backend-stage"

# Fix production
echo ""
echo "=== PRODUCTION ENVIRONMENT ==="
fix_migration "inventory-backend"

echo ""
echo "=== RESTARTING CONTAINERS ==="
docker restart inventory-backend-stage
docker restart inventory-backend

echo ""
echo "✅ Migration fix complete!"
echo ""
echo "Monitor logs with:"
echo "  docker logs -f inventory-backend-stage"
echo "  docker logs -f inventory-backend"
