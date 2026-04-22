# Service URLs Configuration

## Overview
Service URLs are now environment-specific and configured in the respective settings files. No hardcoded URLs in base.py.

## Configuration Structure

```
base.py          → Defines variables (no defaults)
├── dev.py       → Development URLs
├── stage.py     → Stage URLs  
└── prod.py      → Production URLs
```

## Environment-Specific URLs

### Development Environment
**File**: `inventory_service/settings/dev.py`

```python
ERP_BACKEND_URL = "http://quidpath-backend-dev:8004"
POS_SERVICE_URL = "http://pos-backend-dev:8000"
CRM_SERVICE_URL = "http://crm-backend-dev:8000"
HRM_SERVICE_URL = "http://hrm-backend-dev:8000"
PROJECTS_SERVICE_URL = "http://projects-backend-dev:8007"
```

**Container Names**:
- `quidpath-backend-dev` (port 8004)
- `pos-backend-dev` (port 8000)
- `crm-backend-dev` (port 8000)
- `hrm-backend-dev` (port 8000)
- `projects-backend-dev` (port 8007)
- `inventory-backend-dev` (port 8000)

---

### Stage Environment
**File**: `inventory_service/settings/stage.py`

```python
ERP_BACKEND_URL = "http://quidpath-backend-stage:8004"
POS_SERVICE_URL = "http://pos-backend-stage:8000"
CRM_SERVICE_URL = "http://crm-backend-stage:8000"
HRM_SERVICE_URL = "http://hrm-backend-stage:8000"
PROJECTS_SERVICE_URL = "http://projects-backend-stage:8007"
```

**Container Names**:
- `quidpath-backend-stage` (port 8004)
- `pos-backend-stage` (port 8000)
- `crm-backend-stage` (port 8000)
- `hrm-backend-stage` (port 8000)
- `projects-backend-stage` (port 8007)
- `inventory-backend-stage` (port 8000)

**Deployment Workflow**: `.github/workflows/deploy-stage.yml`
- Sets environment variables via GitHub Actions
- Overrides defaults if needed

---

### Production Environment
**File**: `inventory_service/settings/prod.py`

```python
ERP_BACKEND_URL = "http://quidpath-backend-prod:8004"
POS_SERVICE_URL = "http://pos-backend:8000"
CRM_SERVICE_URL = "http://crm-backend:8000"
HRM_SERVICE_URL = "http://hrm-backend:8000"
PROJECTS_SERVICE_URL = "http://projects-backend:8007"
```

**Container Names**:
- `quidpath-backend-prod` (port 8004)
- `pos-backend` (port 8000)
- `crm-backend` (port 8000)
- `hrm-backend` (port 8000)
- `projects-backend` (port 8007)
- `inventory-backend` (port 8000)

**Deployment Workflow**: `.github/workflows/deploy-prod.yml`
- Sets environment variables via GitHub Actions
- Overrides defaults if needed

---

## Service Secrets Configuration

All environments use the same secrets (configured via GitHub Secrets):

```python
# Own service secret
INVENTORY_SERVICE_SECRET = os.environ.get("INVENTORY_SERVICE_SECRET", "")

# Cross-service secrets (for calling other services)
ERP_SERVICE_SECRET = os.environ.get("ERP_SERVICE_SECRET", "")
POS_SERVICE_SECRET = os.environ.get("POS_SERVICE_SECRET", "")
CRM_SERVICE_SECRET = os.environ.get("CRM_SERVICE_SECRET", "")
HRM_SERVICE_SECRET = os.environ.get("HRM_SERVICE_SECRET", "")
PROJECTS_SERVICE_SECRET = os.environ.get("PROJECTS_SERVICE_SECRET", "")
BILLING_SERVICE_SECRET = os.environ.get("BILLING_SERVICE_SECRET", "")
```

These are defined in `base.py` and shared across all environments.

---

## How It Works

### 1. Base Settings (`base.py`)
```python
# Defines variables without defaults
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL")
POS_SERVICE_URL = os.environ.get("POS_SERVICE_URL")
# ... etc
```

### 2. Environment Settings (`stage.py`, `prod.py`, `dev.py`)
```python
# Overrides with environment-specific defaults
ERP_BACKEND_URL = os.environ.get("ERP_BACKEND_URL", "http://quidpath-backend-stage:8004")
# ... etc
```

### 3. Deployment Workflows
```yaml
# Sets environment variables that override defaults
add ERP_BACKEND_URL "http://quidpath-backend-stage:8004"
add POS_SERVICE_URL "http://pos-backend-stage:8000"
# ... etc
```

### Priority Order
1. **Environment Variable** (from deployment workflow) - Highest priority
2. **Settings File Default** (stage.py/prod.py/dev.py) - Fallback
3. **Base Settings** (base.py) - No default, will be None if not set

---

## Benefits

✅ **No Hardcoded URLs**: All URLs are environment-specific  
✅ **Easy to Update**: Change URLs in one place per environment  
✅ **Consistent Naming**: Clear container naming convention  
✅ **Deployment Safety**: Workflow validates URLs before deployment  
✅ **No Cross-Environment Issues**: Stage and prod are completely isolated  

---

## Verification

### Check Current Configuration
```python
# In Django shell
from django.conf import settings

print(f"ERP Backend: {settings.ERP_BACKEND_URL}")
print(f"POS Service: {settings.POS_SERVICE_URL}")
print(f"CRM Service: {settings.CRM_SERVICE_URL}")
print(f"HRM Service: {settings.HRM_SERVICE_URL}")
print(f"Projects Service: {settings.PROJECTS_SERVICE_URL}")
```

### Test Service Communication
```bash
# From inside inventory container
curl http://quidpath-backend-stage:8004/health/
curl http://pos-backend-stage:8000/health/
curl http://crm-backend-stage:8000/health/
curl http://hrm-backend-stage:8000/health/
curl http://projects-backend-stage:8007/health/
```

---

## Troubleshooting

### DNS Resolution Errors
**Error**: `Failed to resolve 'service-name'`

**Solution**:
1. Check container name matches settings
2. Verify containers are on same Docker network
3. Check deployment workflow sets correct URLs

### Wrong Environment URLs
**Error**: Stage trying to connect to prod URLs

**Solution**:
1. Verify `DJANGO_SETTINGS_MODULE` is set correctly
2. Check deployment workflow environment variables
3. Restart container after configuration changes

---

## Migration Checklist

When adding a new service:

- [ ] Add URL variable to `base.py` (no default)
- [ ] Add URL with default to `dev.py`
- [ ] Add URL with default to `stage.py`
- [ ] Add URL with default to `prod.py`
- [ ] Add URL to stage deployment workflow
- [ ] Add URL to prod deployment workflow
- [ ] Add service secret to `base.py`
- [ ] Add service secret to GitHub Secrets
- [ ] Test in dev environment
- [ ] Deploy to stage and verify
- [ ] Deploy to prod and verify

---

## Container Naming Convention

```
{service}-backend[-{environment}]:{port}

Examples:
- quidpath-backend-stage:8004
- pos-backend-stage:8000
- inventory-backend-stage:8000
- quidpath-backend-prod:8004
- pos-backend:8000 (prod, no suffix)
```

**Note**: Some production containers don't have `-prod` suffix (e.g., `pos-backend` instead of `pos-backend-prod`). Always check the actual container names in your Docker environment.
