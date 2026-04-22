# Inventory Service - Production Deployment Guide

## Overview
This guide will help you deploy the inventory service to production with full multi-service integration.

## Prerequisites
- All changes committed to the `master` branch
- GitHub secrets configured properly
- SSH access to production server

## Step 1: Commit and Push Changes

```bash
cd /path/to/inventory
git add .
git commit -m "Fix prod multi-service integration - add service URLs and secrets"
git push origin master
```

This will trigger the GitHub Actions workflow which will:
1. Build the Docker image
2. Push to Docker Hub
3. Trigger deployment via infra repository
4. Create .env file from GitHub secrets
5. Deploy containers on the server

## Step 2: Monitor GitHub Actions

1. Go to GitHub repository → Actions tab
2. Watch the "Build Prod Image & Deploy (Inventory)" workflow
3. Ensure it completes successfully

## Step 3: Fix Database on Server

The production database needs the correct user created. SSH into the server and run:

```bash
# SSH into server
ssh ubuntu@vps-3902112c.vps.ovh.net

# Navigate to inventory directory (or wherever the fix script is)
cd /path/to/inventory

# Make script executable
chmod +x fix_prod_database.sh

# Run the fix script
./fix_prod_database.sh
```

### Alternative: Manual Database Fix

If you prefer to do it manually:

```bash
# SSH into server
ssh ubuntu@vps-3902112c.vps.ovh.net

# Access postgres as superuser
docker exec -it postgres_inventory_prod psql -U postgres

# Run these SQL commands:
CREATE USER inventory_user WITH PASSWORD 'Inv8DovvXsROv62UfvFEr4D97EPullwFsj';
CREATE DATABASE inventory_db OWNER inventory_user;
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
\c inventory_db
GRANT ALL ON SCHEMA public TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO inventory_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO inventory_user;
\q

# Restart containers
docker restart inventory-backend-prod
docker restart inventory-celery-prod
```

## Step 4: Verify Deployment

### Check Container Status
```bash
ssh ubuntu@vps-3902112c.vps.ovh.net "docker ps | grep inventory"
```

Expected output should show:
- `inventory-backend-prod` - Running (not restarting)
- `inventory-celery-prod` - Running
- `postgres_inventory_prod` - Running (healthy)
- `inventory_redis` - Running

### Check Backend Logs
```bash
ssh ubuntu@vps-3902112c.vps.ovh.net "docker logs --tail 50 inventory-backend-prod"
```

Look for:
- ✅ "Starting gunicorn"
- ✅ "Inventory integration client initialized"
- ✅ No database connection errors
- ✅ No authentication errors

### Check Celery Logs
```bash
ssh ubuntu@vps-3902112c.vps.ovh.net "docker logs --tail 30 inventory-celery-prod"
```

Look for:
- ✅ "celery@... ready"
- ✅ No connection errors

### Test Network Connectivity
```bash
# Test connection to other services
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec inventory-backend-prod ping -c 2 quidpath-backend-prod"
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec inventory-backend-prod ping -c 2 pos-backend"
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec inventory-backend-prod ping -c 2 crm-backend"
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec inventory-backend-prod ping -c 2 hrm-backend"
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec inventory-backend-prod ping -c 2 projects-backend"
```

All should respond successfully.

### Test API Endpoints
```bash
# Test health endpoint
ssh ubuntu@vps-3902112c.vps.ovh.net "curl -s http://localhost:8014/api/inventory/health/ | jq"

# Test from main backend (cross-service call)
ssh ubuntu@vps-3902112c.vps.ovh.net "docker exec quidpath-backend-prod curl -s http://inventory-backend-prod:8000/api/inventory/health/"
```

## Step 5: Verify Integration

### Test Cross-Service Communication

From the main quidpath backend, test calling inventory:

```bash
ssh ubuntu@vps-3902112c.vps.ovh.net

# Enter the main backend container
docker exec -it quidpath-backend-prod bash

# Test inventory service
curl http://inventory-backend-prod:8000/api/inventory/health/

# Exit container
exit
```

## Troubleshooting

### Container Keeps Restarting

Check logs for errors:
```bash
docker logs --tail 100 inventory-backend-prod
```

Common issues:
- Database connection failed → Check database credentials
- Migration errors → May need to reset database
- Network errors → Check if quidpath_network exists

### Database Connection Errors

```bash
# Check if database user exists
docker exec postgres_inventory_prod psql -U postgres -c "\du"

# Check if database exists
docker exec postgres_inventory_prod psql -U postgres -c "\l"

# Test connection
docker exec postgres_inventory_prod psql -U inventory_user -d inventory_db -c "SELECT 1;"
```

### Network Issues

```bash
# Check if container is on the right networks
docker inspect inventory-backend-prod | grep -A 10 Networks

# Should show both:
# - inventory_prod_network
# - tmp_quidpath_network
```

### Service Authentication Errors

Check if environment variables are set:
```bash
docker exec inventory-backend-prod env | grep SERVICE_SECRET
```

Should show:
- INVENTORY_SERVICE_SECRET
- ERP_SERVICE_SECRET
- POS_SERVICE_SECRET
- CRM_SERVICE_SECRET
- HRM_SERVICE_SECRET
- PROJECTS_SERVICE_SECRET
- BILLING_SERVICE_SECRET

## Rollback Procedure

If deployment fails and you need to rollback:

```bash
# SSH into server
ssh ubuntu@vps-3902112c.vps.ovh.net

# Stop current containers
docker-compose -f /path/to/inventory/docker-compose.yml down

# Use previous image tag
export IMAGE_TAG=quidpathbackend/quidpath_inventory:prod-YYYY-MM-DD_HH-MM-SS

# Start with old image
docker-compose -f /path/to/inventory/docker-compose.yml up -d
```

## Success Criteria

✅ All containers running without restarts
✅ No errors in backend logs
✅ Database migrations completed
✅ Health endpoint responds
✅ Can ping all other services
✅ Cross-service authentication works
✅ Stage and prod both working identically

## Post-Deployment

1. Monitor logs for 10-15 minutes
2. Test key inventory endpoints
3. Verify integration with other services
4. Check Celery tasks are processing
5. Update team on deployment status

## Support

If issues persist:
1. Check PROD_INTEGRATION_FIX.md for detailed changes
2. Compare with stage environment (which is working)
3. Review GitHub Actions logs
4. Check infra repository deployment logs
