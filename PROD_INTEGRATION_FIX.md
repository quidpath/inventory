# Production Multi-Service Integration Fix

## Issues Identified

1. **Missing Cross-Service Authentication Secrets** - Production .env was missing service secrets for POS, CRM, HRM, PROJECTS, and BILLING
2. **Missing Microservice URLs** - Production environment didn't have URLs for all microservices
3. **Container Naming Inconsistency** - Container was named `inventory-backend` instead of `inventory-backend-prod`
4. **Database Credentials Issue** - PostgreSQL container doesn't have the `inventory_user` role created
5. **Missing Environment Variables** - ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS were not being passed from GitHub secrets

## Changes Made

### 1. GitHub Workflow Updates

#### `deploy-prod.yml`
- Added `CSRF_TRUSTED_ORIGINS` to secrets payload
- Added `inventory-backend-prod` to `ALLOWED_HOSTS`
- Fixed `PROJECTS_SERVICE_URL` port from 8007 to 8000 (internal container port)

#### `deploy-stage.yml`
- Added `CSRF_TRUSTED_ORIGINS` to secrets payload
- Added `inventory-backend-stage` to `ALLOWED_HOSTS`
- Fixed `PROJECTS_SERVICE_URL` port from 8007 to 8000 (internal container port)

### 2. Docker Compose Updates

#### `docker-compose.yml` (Production)
- Changed container name from `inventory-backend` to `inventory-backend-prod`
- Changed celery container name from `inventory-celery` to `inventory-celery-prod`
- Added all service URLs to backend environment variables:
  - `ERP_BACKEND_URL`
  - `POS_SERVICE_URL`
  - `CRM_SERVICE_URL`
  - `HRM_SERVICE_URL`
  - `PROJECTS_SERVICE_URL`
- Added `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` environment variables
- Added all service URLs to celery environment variables

#### `docker-compose.stage.yml` (Stage)
- Added `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` environment variables
- Added all service URLs to backend and celery environment variables

## Database Fix Required

The production PostgreSQL container needs to be recreated with the correct credentials. Two options:

### Option 1: Recreate Database (Clean Start)
```bash
# SSH into server
ssh ubuntu@vps-3902112c.vps.ovh.net

# Stop and remove containers
docker-compose -f /path/to/inventory/docker-compose.yml down

# Remove the database volume (CAUTION: This deletes all data!)
sudo rm -rf /mnt/ebs/inventory_prod/postgres_prod_data_v2

# Redeploy from GitHub (will create fresh database)
```

### Option 2: Fix Existing Database (Preserve Data)
```bash
# SSH into server
ssh ubuntu@vps-3902112c.vps.ovh.net

# Access postgres as superuser
docker exec -it postgres_inventory_prod psql -U postgres

# Create the user and grant permissions
CREATE USER inventory_user WITH PASSWORD 'Inv8DovvXsROv62UfvFEr4D97EPullwFsj';
CREATE DATABASE inventory_db OWNER inventory_user;
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
\q

# Restart the inventory backend
docker restart inventory-backend-prod
```

## Deployment Steps

1. **Commit and push changes** to trigger GitHub Actions workflow
2. **Fix database credentials** on server (choose Option 1 or 2 above)
3. **Verify deployment** by checking logs and testing endpoints

## Verification Commands

```bash
# Check container status
docker ps | grep inventory

# Check backend logs
docker logs --tail 100 inventory-backend-prod

# Check celery logs
docker logs --tail 50 inventory-celery-prod

# Test health endpoint
curl http://localhost:8014/api/inventory/health/

# Check network connectivity
docker exec inventory-backend-prod ping -c 2 quidpath-backend-prod
docker exec inventory-backend-prod ping -c 2 pos-backend
docker exec inventory-backend-prod ping -c 2 crm-backend
```

## Expected Result

After deployment:
- ✅ Inventory service connects to all microservices (ERP, POS, CRM, HRM, PROJECTS)
- ✅ Cross-service authentication works with proper secrets
- ✅ Database migrations run successfully
- ✅ Container names are consistent with naming convention
- ✅ All environment variables are properly configured

## Service URLs Configuration

### Production
- ERP Backend: `http://quidpath-backend-prod:8004`
- POS Service: `http://pos-backend:8000`
- CRM Service: `http://crm-backend:8000`
- HRM Service: `http://hrm-backend:8000`
- Projects Service: `http://projects-backend:8000`

### Stage
- ERP Backend: `http://quidpath-backend-stage:8004`
- POS Service: `http://pos-backend-stage:8000`
- CRM Service: `http://crm-backend-stage:8000`
- HRM Service: `http://hrm-backend-stage:8000`
- Projects Service: `http://projects-backend-stage:8000`

## Notes

- All changes are now in the codebase and will persist through deployments
- GitHub secrets are used to populate the .env file during deployment
- The infra repository handles the actual deployment and .env creation
- Stage environment is already working correctly with these configurations
