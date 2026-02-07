# Package Compatibility Guide

## Overview

This document tracks all package version updates, compatibility changes, and the rationale behind version pinning decisions for the Facebook/TikTok Automation Platform.

---

## Recent Updates (February 2026)

### SQLAlchemy 2.0.30 → 2.0.36 (February 7, 2026)

**Reason:** Python 3.13 compatibility fix

**Issue Encountered:**
```
TypeError: Can't replace canonical symbol for '__firstlineno__' with new int value 615
File: sqlalchemy/sql/compiler.py, line 615
```

**Resolution:**
- Updated to SQLAlchemy 2.0.36 which includes Python 3.13 support
- Version type: **Patch update** (2.0.x series)
- Backward compatibility: ✅ **100% compatible**

**Impact:**
- **Code changes required:** None
- **Breaking changes:** None
- **Migration required:** No
- **Services affected:** Both facebook-automation and api-gateway

**Testing:**
```bash
# Verified successful import
python -c "from app.main import app; print('✅ Backend OK')"
python -c "from src.main import app; print('✅ API Gateway OK')"
```

---

### psycopg[binary] 3.1.18 → 3.2.13 (February 7, 2026)

**Reason:** Version 3.1.18 no longer available in PyPI

**Issue Encountered:**
```
ERROR: Could not find a version that satisfies the requirement psycopg-binary==3.1.18
Available versions: 3.2.2, 3.2.3, ..., 3.2.13
```

**Resolution:**
- Updated to latest stable version 3.2.13
- Version type: **Minor update** (3.1 → 3.2)
- Backward compatibility: ✅ **Maintained**

**Impact:**
- **Code changes required:** None
- **Breaking changes:** None (error handling classes unchanged)
- **Migration required:** No
- **Services affected:** Both facebook-automation and api-gateway

**Usage in codebase:**
```python
# Only used for exception handling
import psycopg.errors

# Connection handled via SQLAlchemy dialect
engine = create_engine("postgresql+psycopg://...")
```

---

## Compatibility Matrix

### Current Versions (As of February 7, 2026)

| Package | Main Backend | API Gateway | Status | Notes |
|---------|-------------|-------------|--------|-------|
| **fastapi** | 0.111.0 | 0.111.0 | ✅ Aligned | Web framework |
| **uvicorn[standard]** | 0.30.6 | 0.30.6 | ✅ Aligned | ASGI server |
| **SQLAlchemy** | 2.0.36 | 2.0.36 | ✅ Aligned | Database ORM |
| **psycopg[binary]** | 3.2.13 | 3.2.13 | ✅ Aligned | PostgreSQL driver |
| **pydantic** | 2.8.2 | 2.8.2 | ✅ Aligned | Data validation |
| **pydantic-settings** | 2.4.0 | 2.4.0 | ✅ Aligned | Settings management |
| **aiogram** | 3.10.0 | 3.10.0 | ✅ Aligned | Telegram bot framework |
| **motor** | 3.3.2 | 3.3.2 | ✅ Aligned | MongoDB async driver |
| **httpx** | 0.27.0 | 0.27.0 | ✅ Aligned | HTTP client |
| **python-dotenv** | 1.0.1 | 1.0.1 | ✅ Aligned | Environment variables |
| **python-jose[cryptography]** | 3.3.0 | 3.3.0 | ✅ Aligned | JWT authentication |

### Backend-Only Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| alembic | 1.13.2 | Database migrations |
| apscheduler | 3.10.4 | Background job scheduling |
| stripe | 10.12.0 | Payment processing |
| fpdf2 | 2.7.6 | PDF generation |
| openpyxl | 3.1.2 | Excel export |
| boto3 | 1.34.84 | R2/S3 storage |
| pymongo | 4.6.1 | MongoDB sync driver |

---

## Version Pinning Policy

### Philosophy

**Production services MUST use pinned versions (`==`) for:**
- ✅ **Reproducibility** - Same build every time
- ✅ **Stability** - No surprise breaking changes
- ✅ **Debuggability** - Consistent environment across deploys
- ✅ **Security** - Controlled updates with testing

### Rules

#### ✅ DO: Pin exact versions in production

```python
# requirements.txt (CORRECT)
fastapi==0.111.0
sqlalchemy==2.0.36
pydantic==2.8.2
```

#### ❌ DON'T: Use loose version constraints in production

```python
# requirements.txt (WRONG)
fastapi>=0.104.0    # Could install 0.112.0 with breaking changes
sqlalchemy>=2.0.0   # Could install 2.1.0 with API changes
pydantic>=2.5.0     # Version drift between services
```

### When to Use Loose Versions

**Development/experimentation only:**
```python
# requirements-dev.txt (acceptable)
pytest>=7.4.0
black>=23.0.0
mypy>=1.0.0
```

**Never in production:**
- `requirements.txt` ❌
- `api-gateway/requirements.txt` ❌
- `Dockerfile` build dependencies ❌

---

## Update Process

### Standard Update Workflow

When updating a package version, follow these steps:

#### 1. Test in Main Backend First

```bash
cd /path/to/facebook-automation

# Update requirements.txt
vim requirements.txt
# Change: package==1.0.0 → package==1.1.0

# Install new version
pip install -r requirements.txt

# Run tests
python -m pytest

# Verify imports
python -c "from app.main import app; print('✅ OK')"

# Start server and test manually
uvicorn app.main:app --reload
```

#### 2. Check for Breaking Changes

```bash
# Review package changelog
# Check migration guide
# Test critical endpoints:
#   - Authentication
#   - Database queries
#   - Invoice creation
#   - Payment verification
```

#### 3. Update API Gateway to Match

```bash
cd api-gateway

# Update requirements.txt to match backend version
vim requirements.txt
# Change: package>=1.0.0 → package==1.1.0

# Install and test
pip install -r requirements.txt
python -c "from src.main import app; print('✅ OK')"

# Test Telegram bot
python src/run.py  # Verify /start, /status commands
```

#### 4. Document the Change

Add entry to this file (`docs/PACKAGE_COMPATIBILITY.md`):

```markdown
### package-name X.Y.Z → A.B.C (Date)

**Reason:** [Why the update was needed]

**Issue Encountered:**
```
[Error message or problem that prompted update]
```

**Resolution:**
- [What was changed]
- Version type: [Patch/Minor/Major update]
- Backward compatibility: [Yes/No]

**Impact:**
- Code changes required: [Yes/No - describe]
- Breaking changes: [List any]
- Migration required: [Yes/No]
```

#### 5. Deploy Both Services Together

```bash
# Commit changes
git add requirements.txt api-gateway/requirements.txt docs/PACKAGE_COMPATIBILITY.md
git commit -m "chore: update package to version X.Y.Z"

# Push to trigger Railway deployment
git push origin main

# Monitor Railway logs for both services
railway logs --service facebook-automation
railway logs --service api-gateway
```

---

## Troubleshooting

### Version Conflict Errors

**Error:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Solution:**
```bash
# Create fresh virtual environment
python -m venv .venv-fresh
source .venv-fresh/bin/activate  # Windows: .venv-fresh\Scripts\activate

# Install from scratch
pip install --upgrade pip
pip install -r requirements.txt
```

### Import Errors After Update

**Error:**
```
ImportError: cannot import name 'X' from 'package'
```

**Solution:**
1. Check package changelog for renamed/moved imports
2. Search codebase for all imports: `grep -r "from package import" .`
3. Update import statements
4. Document breaking change in this file

### Database Connection Issues

**Error:**
```
OperationalError: could not connect to database
psycopg.errors...
```

**Solution:**
1. Verify `psycopg[binary]` version matches SQLAlchemy compatibility
2. Check `connect_args` in `app/core/db.py`
3. Test connection with minimal script:
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg://...")
with engine.connect() as conn:
    print(conn.execute(text("SELECT 1")).scalar())
```

---

## Automated Version Drift Detection

### Check Version Alignment

Use the provided script to detect version mismatches:

```bash
python scripts/check_version_drift.py
```

**Expected output when aligned:**
```
🔍 Version Drift Analysis

✅ All versions aligned!
```

**Output when drift detected:**
```
🔍 Version Drift Analysis

⚠️  fastapi                Backend: ==0.111.0       Gateway: >=0.104.0
⚠️  sqlalchemy             Backend: ==2.0.36        Gateway: >=2.0.0
⚠️  pydantic               Backend: ==2.8.2         Gateway: >=2.5.0

⚠️  Version drift detected - consider aligning api-gateway with backend
```

### CI/CD Integration (Future)

Add to `.github/workflows/version-check.yml`:

```yaml
name: Version Drift Check

on: [pull_request]

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check version alignment
        run: python scripts/check_version_drift.py
```

---

## Critical Dependencies

These packages require special care when updating:

### Database Layer

| Package | Current | Why Critical |
|---------|---------|--------------|
| **SQLAlchemy** | 2.0.36 | Core ORM - affects all DB queries |
| **psycopg[binary]** | 3.2.13 | PostgreSQL driver - connection handling |
| **alembic** | 1.13.2 | Schema migrations - data integrity |

**Update considerations:**
- Test all migrations
- Verify connection pooling (NullPool + pgbouncer)
- Check prepared statement handling

### Web Framework

| Package | Current | Why Critical |
|---------|---------|--------------|
| **fastapi** | 0.111.0 | API contracts - breaking changes affect clients |
| **uvicorn** | 0.30.6 | ASGI server - affects performance & stability |
| **pydantic** | 2.8.2 | Request/response validation - schema changes |

**Update considerations:**
- Test all API endpoints
- Verify OpenAPI docs generation
- Check request validation behavior

### Authentication & Security

| Package | Current | Why Critical |
|---------|---------|--------------|
| **python-jose[cryptography]** | 3.3.0 | JWT tokens - security critical |
| **cryptography** | 42.0.8 | Encryption - password hashing, tokens |

**Update considerations:**
- Never update mid-deployment (invalidates tokens)
- Test token generation/validation
- Verify password hashing compatibility

---

## Version History

### February 2026

- **2026-02-07**: SQLAlchemy 2.0.30 → 2.0.36 (Python 3.13 compat)
- **2026-02-07**: psycopg[binary] 3.1.18 → 3.2.13 (PyPI availability)
- **2026-02-07**: Aligned all api-gateway versions with main backend

### January 2026

- **2026-01-12**: fpdf2, openpyxl updates for PDF/Excel export
- Initial production deployment with pinned versions

---

## Related Documentation

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Docker deployment guide
- [CLAUDE.md](../CLAUDE.md) - Project architecture and best practices
- Main [requirements.txt](../requirements.txt)
- API Gateway [requirements.txt](../api-gateway/requirements.txt)

---

**Last Updated:** February 7, 2026
**Maintained By:** Development Team
**Review Cycle:** Update after each package version change
