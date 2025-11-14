# Quick Start: Automation Scheduler

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- FastAPI server running
- PostgreSQL database configured
- At least one tenant with OAuth tokens connected

### Step 1: Create a Destination

Destinations are where automation results are sent (Telegram, webhooks, email).

```python
# Using Python
from app.core.db import get_db_session
from app.repositories import DestinationRepository
from app.core.models import DestinationType

with get_db_session() as db:
    dest_repo = DestinationRepository(db)

    destination = dest_repo.create_destination(
        tenant_id="your-tenant-uuid",
        name="My Telegram Channel",
        destination_type=DestinationType.telegram_chat,
        config={
            "chat_id": "-1001234567890",  # Your Telegram chat ID
            "parse_mode": "Markdown"
        }
    )
    db.commit()
    print(f"Destination created: {destination.id}")
```

### Step 2: Create an Automation

```python
from app.services.automation_service import AutomationService
from app.core.models import AutomationType

with get_db_session() as db:
    automation_service = AutomationService(db)

    # Create a daily Facebook report
    automation = automation_service.create_automation(
        tenant_id="your-tenant-uuid",
        destination_id="destination-uuid-from-step-1",
        name="Daily Facebook Metrics Report",
        automation_type=AutomationType.scheduled_report,
        schedule_config={
            "type": "daily",
            "hour": 9  # 9:00 AM UTC
        },
        automation_config={
            "period": "daily",
            "days": 7,
            "metric_types": ["ad_account", "pages"],
            "format": "text"
        },
        platforms=["facebook"]
    )

    print(f"Automation created: {automation.id}")
    print(f"Next run: {automation.next_run}")
```

### Step 3: Start the Server

The scheduler starts automatically with the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
🚀 FB/TikTok Automation API started (env=dev)
✅ Background token refresh and cleanup tasks started
✅ Automation scheduler started (check interval: 60s)
```

### Step 4: Monitor Execution

Watch the logs for execution messages:

```
Found 1 automation(s) due for execution
▶️  Executing automation: Daily Facebook Metrics Report (ID: abc-123, Type: scheduled_report)
✅ Automation Daily Facebook Metrics Report completed successfully (Run ID: def-456)
```

Check the database for execution history:

```sql
SELECT
    a.name,
    ar.status,
    ar.started_at,
    ar.completed_at,
    ar.result->>'formatted_output' as output
FROM automation_run ar
JOIN automation a ON ar.automation_id = a.id
ORDER BY ar.started_at DESC
LIMIT 5;
```

## 📋 Automation Types & Examples

### 1. Scheduled Report

**Use case**: Daily/weekly performance reports

```python
automation_service.create_automation(
    tenant_id=tenant_id,
    destination_id=destination_id,
    name="Weekly Performance Report",
    automation_type=AutomationType.scheduled_report,
    schedule_config={
        "type": "weekly",
        "weekday": 0,  # Monday
        "hour": 9
    },
    automation_config={
        "period": "weekly",
        "days": 7,
        "metric_types": ["ad_account", "pages"],
        "format": "text"
    },
    platforms=["facebook", "tiktok"]
)
```

### 2. Alert

**Use case**: Get notified when spend exceeds budget

```python
automation_service.create_automation(
    tenant_id=tenant_id,
    destination_id=destination_id,
    name="Spend Alert",
    automation_type=AutomationType.alert,
    schedule_config={
        "type": "interval",
        "interval_minutes": 30  # Check every 30 minutes
    },
    automation_config={
        "thresholds": {
            "max_daily_spend": 500.00,
            "min_ctr": 1.5
        }
    },
    platforms=["facebook"]
)
```

### 3. Data Sync

**Use case**: Export data to external systems

```python
automation_service.create_automation(
    tenant_id=tenant_id,
    destination_id=destination_id,
    name="Daily Data Export",
    automation_type=AutomationType.data_sync,
    schedule_config={
        "type": "daily",
        "hour": 2  # 2:00 AM UTC
    },
    automation_config={
        "sync_type": "webhook",
        "webhook_url": "https://your-api.com/webhook"
    },
    platforms=["facebook", "tiktok"]
)
```

## ⚙️ Configuration

### Environment Variables

Add to your `.env` file:

```bash
# How often the scheduler checks for due automations
AUTOMATION_CHECK_INTERVAL=60

# How often to refresh OAuth tokens
TOKEN_REFRESH_INTERVAL=3600

# How often to clean up expired tokens
CLEANUP_INTERVAL=86400
```

### Schedule Types

#### Interval
Run every N minutes:
```json
{
  "type": "interval",
  "interval_minutes": 60
}
```

#### Daily
Run once per day at specific hour (UTC):
```json
{
  "type": "daily",
  "hour": 9
}
```

#### Weekly
Run once per week on specific day:
```json
{
  "type": "weekly",
  "weekday": 0,  // 0=Monday, 6=Sunday
  "hour": 9
}
```

## 🧪 Testing

### Test with Demo Script

```bash
# Create and test an automation
python app/scripts/test_scheduler.py
```

This script will:
1. Create a test tenant and destination
2. Create a test automation
3. Run the scheduler manually
4. Show execution results

### Manual Testing

```python
# 1. Create a test automation that runs every 2 minutes
from datetime import datetime, timedelta

automation = automation_service.create_automation(
    tenant_id=tenant_id,
    destination_id=destination_id,
    name="Test Automation",
    automation_type=AutomationType.scheduled_report,
    schedule_config={
        "type": "interval",
        "interval_minutes": 2
    },
    automation_config={"period": "daily", "days": 1},
    platforms=["facebook"]
)

# 2. Manually set next_run to now
automation.next_run = datetime.utcnow()
db.commit()

# 3. Wait for the scheduler to pick it up (within 60 seconds)
# Watch the logs for execution
```

## 🔧 Management

### Pause an Automation

```python
automation_service.pause_automation(automation_id)
```

### Resume an Automation

```python
automation_service.resume_automation(automation_id)
```

### View Automation Status

```python
automation = automation_service.automation_repo.get_by_id(automation_id)
print(f"Status: {automation.status}")
print(f"Last run: {automation.last_run}")
print(f"Next run: {automation.next_run}")
print(f"Run count: {automation.run_count}")
print(f"Error count: {automation.error_count}")
```

### View Execution History

```python
runs = automation_service.get_automation_history(automation_id, limit=10)

for run in runs:
    print(f"Run {run.id}:")
    print(f"  Started: {run.started_at}")
    print(f"  Status: {run.status}")
    print(f"  Duration: {run.completed_at - run.started_at}")
    if run.error_message:
        print(f"  Error: {run.error_message}")
```

## 📊 Monitoring

### Check Scheduler Status

```bash
# Look for these log messages in the FastAPI server output:

# Scheduler started
✅ Automation scheduler started (check interval: 60s)

# Checking for due automations
Found 3 automation(s) due for execution

# Executing automations
▶️  Executing automation: Daily Report (ID: abc-123, Type: scheduled_report)
✅ Automation Daily Report completed successfully (Run ID: def-456)

# Errors
❌ Error executing automation Daily Report (ID: abc-123): [error details]
```

### Database Queries

```sql
-- Active automations
SELECT id, name, type, status, next_run
FROM automation
WHERE status = 'active'
ORDER BY next_run;

-- Recent executions
SELECT
    a.name,
    ar.status,
    ar.started_at,
    (ar.completed_at - ar.started_at) as duration
FROM automation_run ar
JOIN automation a ON ar.automation_id = a.id
ORDER BY ar.started_at DESC
LIMIT 20;

-- Error rate by automation
SELECT
    a.name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN ar.status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    ROUND(100.0 * SUM(CASE WHEN ar.status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
FROM automation_run ar
JOIN automation a ON ar.automation_id = a.id
GROUP BY a.id, a.name
HAVING COUNT(*) > 0
ORDER BY error_rate DESC;
```

## 🐛 Troubleshooting

### Automation Not Running

1. **Check automation status**:
   ```python
   automation = automation_service.automation_repo.get_by_id(automation_id)
   print(automation.status)  # Should be 'active'
   print(automation.next_run)  # Should be in the past
   ```

2. **Check scheduler is running**:
   Look for "✅ Automation scheduler started" in server logs

3. **Check for errors**:
   ```sql
   SELECT * FROM automation WHERE id = 'your-id';
   -- Look at error_count and last error
   ```

### OAuth Token Errors

If you see "No valid token found for platform":

```python
from app.repositories import AdTokenRepository

with get_db_session() as db:
    token_repo = AdTokenRepository(db)
    tokens = token_repo.get_tenant_tokens(tenant_id, platform=Platform.facebook)

    for token in tokens:
        print(f"Token {token.id}: is_valid={token.is_valid}, expires={token.expires_at}")
```

Re-authenticate if needed:
1. Go to `/oauth/facebook/authorize`
2. Complete OAuth flow
3. Verify token is stored and valid

### Destination Delivery Failures

Check destination configuration:

```python
from app.repositories import DestinationRepository

with get_db_session() as db:
    dest_repo = DestinationRepository(db)
    destination = dest_repo.get_by_id(destination_id)

    print(f"Type: {destination.type}")
    print(f"Config: {destination.config}")
    print(f"Is active: {destination.is_active}")
```

## 📚 Further Reading

- [SCHEDULER.md](SCHEDULER.md) - Comprehensive scheduler documentation
- [CLAUDE.md](CLAUDE.md) - Project overview and architecture
- [FastAPI Docs](https://fastapi.tiangolo.com/) - FastAPI framework
