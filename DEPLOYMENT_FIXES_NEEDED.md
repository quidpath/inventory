# Critical Production Issues - Action Required

## Summary
Multiple services are failing in production/staging. Here are the issues and fixes needed:

---

## 1. ✅ FIXED: Inventory - TransactionLog UUID Issue
**Status:** Code fixed, needs redeployment

**Problem:** TransactionLog model had `user_id` and `corporate_id` as `PositiveIntegerField` but system passes UUIDs.

**Error:**
```
Field 'user_id' expected a number but got '561d2775-883f-462f-b62e-22aea3267f04'
```

**Fix Applied:**
- Changed `user_id` and `corporate_id` to `UUIDField` in audit models
- Created migration `0002_change_ids_to_uuid.py`
- Committed and pushed to Development

**Action Required:**
```bash
# On server, redeploy inventory service
cd /path/to/inventory
docker-compose down
docker-compose up -d
docker-compose exec inventory-backend python manage.py migrate
```

---

## 2. ❌ CRITICAL: Inventory Production - Database Password Failed
**Status:** Needs immediate attention

**Problem:** Inventory production container cannot connect to database.

**Error:**
```
connection to server at "postgres_inventory_prod" failed: 
FATAL: password authentication failed for user "inventory_user"
```

**Container Status:** Restarting continuously

**Action Required:**
1. Check environment variables in production:
   ```bash
   docker-compose exec postgres_inventory_prod env | grep POSTGRES
   ```

2. Verify `.env.production` file has correct credentials:
   ```
   DB_NAME=inventory_db
   DB_USER=inventory_user
   DB_PASSWORD=<correct_password>
   DB_HOST=postgres_inventory_prod
   DB_PORT=5432
   ```

3. If password is wrong, update it:
   ```bash
   # Stop containers
   docker-compose -f docker-compose.yml down
   
   # Update .env.production with correct password
   # Restart
   docker-compose -f docker-compose.yml up -d
   ```

---

## 3. ❌ POS Stage - Missing Database Tables
**Status:** Needs migration run

**Problem:** POS models exist but database tables not created.

**Error:**
```
relation "pos_order" does not exist
```

**Action Required:**
```bash
# On server
docker-compose exec pos-backend-stage python manage.py migrate
docker-compose restart pos-backend-stage
```

---

## 4. ❌ Service Integration - 404 Errors
**Status:** URL routing issue

**Problem:** Integrated endpoints returning 404.

**Errors:**
```
Not Found: /api/inventory/products/integrated/health/
Not Found: /api/inventory/products/integrated/list/
Not Found: /api/inventory/stock/moves/integrated/list/
```

**Possible Causes:**
1. URLs not registered in main `urls.py`
2. Middleware blocking requests
3. Service not fully started

**Action Required:**
1. Check if integrated URLs are registered:
   ```bash
   docker-compose exec inventory-backend-stage python manage.py show_urls | grep integrated
   ```

2. Verify URL configuration in `inventory_service/urls.py`

3. Check if health endpoint works:
   ```bash
   curl http://localhost:8015/api/inventory/products/integrated/health/
   ```

---

## 5. ⚠️ Multiple Services - Superuser Creation Warning
**Status:** Non-critical, but should be fixed

**Services Affected:** HRM, CRM, Projects

**Error:**
```
CommandError: You must use --username with --noinput.
```

**Action Required:**
Update `start.sh` in each service to either:
- Remove superuser creation command, OR
- Add proper environment variables:
  ```bash
  export DJANGO_SUPERUSER_USERNAME=admin
  export DJANGO_SUPERUSER_EMAIL=admin@example.com
  export DJANGO_SUPERUSER_PASSWORD=secure_password
  ```

---

## Deployment Priority

### Immediate (Production Down):
1. **Fix Inventory Production database password** - Service is down
2. **Run POS migrations** - Service returning errors

### High Priority (Staging Issues):
3. **Redeploy Inventory with UUID fix** - Prevents audit logging errors
4. **Fix integrated endpoint 404s** - Services can't communicate

### Low Priority (Warnings):
5. **Fix superuser creation warnings** - Non-blocking

---

## Quick Commands for Server

```bash
# Check all container statuses
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View logs for specific service
docker logs --tail 50 inventory-backend
docker logs --tail 50 pos-backend-stage

# Restart a service
docker-compose restart inventory-backend

# Run migrations
docker-compose exec inventory-backend python manage.py migrate
docker-compose exec pos-backend-stage python manage.py migrate

# Check database connection
docker-compose exec inventory-backend python manage.py dbshell
```

---

## Next Steps

1. SSH to production server
2. Fix database password for inventory production
3. Run migrations for POS
4. Redeploy inventory with UUID fixes
5. Investigate integrated endpoint 404s
6. Test service-to-service communication

