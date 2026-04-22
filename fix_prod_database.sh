#!/bin/bash
# Script to fix production database credentials
# Run this on the server after deployment

echo "=== Fixing Production Inventory Database ==="

# Check if postgres container is running
if ! docker ps | grep -q postgres_inventory_prod; then
    echo "ERROR: postgres_inventory_prod container is not running!"
    exit 1
fi

echo "Creating database user and database..."

# Create user and database
docker exec -i postgres_inventory_prod psql -U postgres <<EOF
-- Check if user exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'inventory_user') THEN
        CREATE USER inventory_user WITH PASSWORD 'Inv8DovvXsROv62UfvFEr4D97EPullwFsj';
        RAISE NOTICE 'User inventory_user created';
    ELSE
        RAISE NOTICE 'User inventory_user already exists';
    END IF;
END
\$\$;

-- Check if database exists
SELECT 'CREATE DATABASE inventory_db OWNER inventory_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'inventory_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;

-- Connect to the database and grant schema privileges
\c inventory_db
GRANT ALL ON SCHEMA public TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO inventory_user;

\q
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database user and database created successfully!"
    echo ""
    echo "Now restarting inventory containers..."
    
    # Restart inventory containers
    docker restart inventory-backend-prod
    docker restart inventory-celery-prod
    
    echo ""
    echo "✅ Containers restarted!"
    echo ""
    echo "Waiting 10 seconds for containers to start..."
    sleep 10
    
    echo ""
    echo "=== Checking container status ==="
    docker ps | grep inventory
    
    echo ""
    echo "=== Checking backend logs (last 30 lines) ==="
    docker logs --tail 30 inventory-backend-prod
    
else
    echo "❌ Failed to create database user/database"
    exit 1
fi
