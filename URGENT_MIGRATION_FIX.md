# URGENT: Fix Inventory Migration Issue

## Problem
Inventory services (stage and prod) are crashing due to UUID migration error:
```
django.db.utils.ProgrammingError: cannot cast type integer to uuid
```

## Root Cause
Migration `0002_change_ids_to_uuid` was trying to use Django's AlterField which generates SQL that can't convert integer to UUID. This migration has been removed and replaced with `0002_fix_uuid_columns` which uses raw SQL.

## Solution
Run these commands on the production server to fix the migration state:

### Step 1: Fix Staging Environment

```bash
# Remove old migration records from database
docker exec inventory-backend-stage python manage.py shell << 'EOF'
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'audit' AND name = '0002_change_ids_to_uuid';")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'audit' AND name = '0003_fix_uuid_columns';")
    print("✓ Removed old migration records")
EOF

# Restart the container to pull new code
docker restart inventory-backend-stage

# Wait 10 seconds for container to start
sleep 10

# Check logs
docker logs --tail 50 inventory-backend-stage
```

### Step 2: Fix Production Environment

```bash
# Remove old migration records from database
docker exec inventory-backend python manage.py shell << 'EOF'
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'audit' AND name = '0002_change_ids_to_uuid';")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'audit' AND name = '0003_fix_uuid_columns';")
    print("✓ Removed old migration records")
EOF

# Restart the container to pull new code
docker restart inventory-backend

# Wait 10 seconds for container to start
sleep 10

# Check logs
docker logs --tail 50 inventory-backend
```

### Step 3: Verify Services Are Running

```bash
# Check container status
docker ps | grep inventory-backend

# Both should show "Up" status, not "Restarting"

# Test staging API
curl -I https://stage-inventory.quidpath.com/api/inventory/health/

# Test production API
curl -I https://api.quidpath.com/api/inventory/health/
```

## What Changed

### Before (Broken):
- `0002_change_ids_to_uuid.py` - Used Django AlterField (fails on integer→UUID)
- `0003_fix_uuid_columns.py` - Raw SQL fix

### After (Fixed):
- `0002_fix_uuid_columns.py` - Raw SQL fix (renamed from 0003)
- Removed the broken 0002 migration

## Expected Result

After running the fix:
- ✅ Containers start successfully
- ✅ Migrations run without errors
- ✅ Services respond to health checks
- ✅ Inventory API is accessible

## If Issues Persist

1. **Check if containers are still restarting**:
   ```bash
   docker ps | grep inventory-backend
   ```

2. **View full logs**:
   ```bash
   docker logs inventory-backend-stage
   docker logs inventory-backend
   ```

3. **Manually run migrations**:
   ```bash
   docker exec inventory-backend-stage python manage.py migrate --fake audit 0001
   docker exec inventory-backend-stage python manage.py migrate audit
   ```

## Rollback Plan

If the fix doesn't work, rollback to previous image:
```bash
# Find previous working image
docker images | grep quidpath_inventory

# Update docker-compose to use previous image tag
# Then restart containers
```

## Timeline

- **Issue Detected**: 2026-04-22 10:00 UTC
- **Fix Committed**: 2026-04-22 10:15 UTC (commit fdd74fa)
- **Fix Deployed**: Automatic via GitHub Actions
- **Manual Fix Required**: Yes - migration state cleanup

## Contact

If you need assistance, check:
- GitHub Actions: https://github.com/quidpath/inventory/actions
- This documentation: `inventory/URGENT_MIGRATION_FIX.md`
