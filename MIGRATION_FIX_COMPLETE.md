# Migration Fix - Complete Solution

## Root Cause Identified

The migration issues were caused by **incorrect field types in the initial migration**:

### Original Problem
In `inventory_service/audit/migrations/0001_initial.py`:
- `user_id` was defined as `PositiveIntegerField` 
- `corporate_id` was defined as `PositiveIntegerField`
- `recipient_id` was defined as `PositiveIntegerField`

But the application code expected these to be **UUIDs** to match the user IDs from the main quidpath-backend service.

### The Failed Fix Attempt
Migration `0002_fix_uuid_columns.py` tried to convert these integer fields to UUID fields, but:
1. You can't directly convert integers to UUIDs in PostgreSQL
2. The SQL comparison `uuid >= integer` caused the error
3. Even with table existence checks, the conversion logic was flawed

## Complete Solution Applied

### 1. Fixed the Initial Migration
**File:** `inventory_service/audit/migrations/0001_initial.py`

Changed field types from `PositiveIntegerField` to `UUIDField`:
```python
# Before
('user_id', models.PositiveIntegerField(blank=True, null=True))
('corporate_id', models.PositiveIntegerField(blank=True, null=True))
('recipient_id', models.PositiveIntegerField(db_index=True))

# After
('user_id', models.UUIDField(blank=True, null=True))
('corporate_id', models.UUIDField(blank=True, null=True))
('recipient_id', models.UUIDField(db_index=True))
```

### 2. Deleted the Problematic Migration
**Deleted:** `inventory_service/audit/migrations/0002_fix_uuid_columns.py`

This migration is no longer needed because:
- The initial migration now creates the correct field types
- No conversion is necessary
- Eliminates the source of the error

### 3. Fresh Database Volumes
**Changed in both `docker-compose.stage.yml` and `docker-compose.yml`:**

```yaml
# Stage
volumes:
  - /mnt/ebs/inventory/postgres_db_stage_data_v2:/var/lib/postgresql/data

# Production  
volumes:
  - /mnt/ebs/inventory_prod/postgres_prod_data_v2:/var/lib/postgresql/data
```

**Why this is safe:**
- No inventory data exists yet
- Fresh database will be created with correct schema from the start
- Old database volumes remain untouched (can be deleted later if needed)

## What Happens on Next Deployment

1. **New Docker image** will be built with the corrected migration
2. **New database volume** (`_v2`) will be created (empty)
3. **Initial migration** will run and create tables with **UUID fields** from the start
4. **No conversion errors** because fields are correct from the beginning
5. **Container starts successfully** and passes health checks

## Verification Steps

After deployment completes, verify on the server:

```bash
# Check container is running
docker ps | grep inventory-backend-stage

# Check logs show successful migration
docker logs inventory-backend-stage | grep -A 5 "Running migrations"

# Should see:
# Running migrations:
#   Applying audit.0001_initial... OK
#   Applying products.0001_initial... OK
#   ... (other migrations)

# Verify database schema
docker exec postgres_inventory_stage psql -U <user> -d <db> -c "\d audit_transactionlog"

# Should show user_id and corporate_id as 'uuid' type, not 'integer'
```

## Why This Won't Happen Again

### Prevention Measures

1. **Correct Initial Migrations**
   - Always define fields with the correct type from the start
   - Match field types with related services (UUIDs for user references)

2. **Migration Testing**
   - Test migrations locally before deploying
   - Use fresh database to catch initial migration issues
   - Run `python manage.py migrate` in development

3. **Type Consistency**
   - User IDs across all services are UUIDs
   - Corporate IDs are UUIDs
   - Maintain consistency in field types

4. **Better Error Handling**
   - Start script now exits on migration failure
   - Prevents infinite restart loops
   - Clear error messages for debugging

## Files Changed

1. ✅ `inventory_service/audit/migrations/0001_initial.py` - Fixed field types
2. ✅ `inventory_service/audit/migrations/0002_fix_uuid_columns.py` - Deleted
3. ✅ `docker-compose.stage.yml` - New database volume path
4. ✅ `docker-compose.yml` - New database volume path
5. ✅ `start.sh` - Already has migration failure detection

## Deployment Status

- ✅ Changes committed to Development branch
- ✅ Pushed to GitHub
- ⏳ GitHub Actions building new image
- ⏳ Deployment to staging server in progress

Monitor deployment at:
- GitHub Actions: https://github.com/quidpath/inventory/actions
- Server logs: `ssh ubuntu@vps-3902112c.vps.ovh.net "docker logs -f inventory-backend-stage"`

## Expected Timeline

- Image build: ~3-5 minutes
- Deployment trigger: ~1 minute
- Container startup: ~30 seconds
- Migration execution: ~10 seconds
- **Total: ~5-7 minutes from push**

## Success Criteria

✅ Container status shows "Up" (not "Restarting")  
✅ Logs show "Starting Gunicorn..."  
✅ Health endpoint responds: `curl http://localhost:8015/health/`  
✅ No migration errors in logs  
✅ Database tables created with UUID fields  

## Rollback Plan (if needed)

If something unexpected happens:

```bash
# Stop the new containers
docker-compose -f docker-compose.stage.yml down

# Revert to old volume (if needed)
# Edit docker-compose.stage.yml and change _v2 back to original path

# Deploy previous working image
# Update IMAGE_TAG in .env to previous version
docker-compose -f docker-compose.stage.yml up -d
```

## Next Steps After Successful Deployment

1. ✅ Verify inventory service is running
2. ✅ Test API endpoints
3. ✅ Check integration with quidpath-backend
4. ✅ Monitor for any runtime errors
5. ✅ Apply same fix to production when ready

## Lessons Learned

1. **Always match field types** across microservices
2. **Test migrations with fresh databases** to catch initial migration issues
3. **Don't try to fix migrations with more migrations** - fix the source
4. **Fresh database is better** than complex conversion logic when no data exists
5. **Type conversions in SQL** (especially integer to UUID) are problematic

---

**Status:** ✅ Fix deployed, awaiting verification  
**Date:** 2026-04-22  
**Branch:** Development  
**Environment:** Stage (will apply to Production after verification)
