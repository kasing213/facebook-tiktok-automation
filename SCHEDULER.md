# Automation Job Scheduler & Worker Documentation

## Overview

The Facebook/TikTok Automation platform includes a comprehensive background job system for executing automations on schedule. This system consists of:

1. **Automation Scheduler** - Checks for due automations and triggers execution
2. **Automation Handlers** - Execute different types of automations (reports, alerts, data sync)
3. **Token Refresh Worker** - Keeps OAuth tokens fresh and valid
4. **Cleanup Worker** - Removes expired/invalid tokens

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                      (app/main.py)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Lifespan Manager
                   │
        ┌──────────┴──────────┬──────────────┬────────────────┐
        │                     │              │                │
        ▼                     ▼              ▼                ▼
┌───────────────┐   ┌──────────────┐  ┌──────────┐  ┌──────────────┐
│   Automation  │   │    Token     │  │ Cleanup  │  │  Other Jobs  │
│   Scheduler   │   │   Refresh    │  │  Worker  │  │   (Future)   │
└───────┬───────┘   └──────────────┘  └──────────┘  └──────────────┘
        │
        │ Checks every N seconds
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│             AutomationService.get_due_automations()        │
└───────────────────┬───────────────────────────────────────┘
                    │
                    │ Execute each automation
                    │
        ┌───────────┴───────────┬────────────────┐
        │                       │                │
        ▼                       ▼                ▼
┌──────────────┐      ┌──────────────┐   ┌──────────────┐
│ Scheduled    │      │    Alert     │   │  Data Sync   │
│   Report     │      │   Handler    │   │   Handler    │
│  Handler     │      │              │   │              │
└──────┬───────┘      └──────┬───────┘   └──────┬───────┘
       │                     │                  │
       │                     │                  │
       └─────────────────────┴──────────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │  Destination Sender   │
                 │  (Telegram, Webhook)  │
                 └───────────────────────┘
```

## Components

### 1. Automation Scheduler

**File**: `app/jobs/automation_scheduler.py`

**Purpose**: Periodically checks for automations that are due to run and executes them.

**Key Features**:
- Configurable check interval (default: 60 seconds)
- Graceful error handling and retries
- Comprehensive logging
- Safe concurrent execution

**Configuration**:
```python
# In .env or environment variables
AUTOMATION_CHECK_INTERVAL=60  # Check every 60 seconds
```

**How it works**:
1. Every N seconds, query database for automations where `next_run <= current_time` and `status = 'active'`
2. For each due automation, call `AutomationService.execute_automation()`
3. Update `last_run`, `next_run`, and `run_count` in the database
4. Create an `AutomationRun` record with execution results
5. Send results to the configured destination

**Starting the scheduler**:
```python
# Automatically started in FastAPI lifespan
from app.jobs.automation_scheduler import run_automation_scheduler

automation_task = asyncio.create_task(
    run_automation_scheduler(check_interval=60)
)
```

### 2. Automation Handlers

**File**: `app/services/automation_handlers.py`

Handlers are responsible for executing specific automation types:

#### ScheduledReportHandler

Generates periodic reports with metrics from Facebook/TikTok.

**Configuration Example**:
```json
{
  "period": "daily",
  "days": 7,
  "metric_types": ["ad_account", "pages"],
  "format": "text"
}
```

**Platforms**: `["facebook", "tiktok"]`

**Output**: Formatted text or HTML report with metrics

#### AlertHandler

Monitors metrics and sends alerts when thresholds are breached.

**Configuration Example**:
```json
{
  "thresholds": {
    "max_daily_spend": 1000.00,
    "min_ctr": 2.0
  }
}
```

**Platforms**: `["facebook", "tiktok"]`

**Output**: Alert message if thresholds are breached

#### DataSyncHandler

Syncs platform data to external systems (webhooks, databases).

**Configuration Example**:
```json
{
  "sync_type": "webhook",
  "webhook_url": "https://example.com/webhook"
}
```

**Platforms**: `["facebook", "tiktok"]`

**Output**: Sync confirmation with result details

### 3. Automation Service

**File**: `app/services/automation_service.py`

**Key Methods**:

```python
class AutomationService:
    def create_automation(...) -> Automation:
        """Create a new automation with schedule"""

    def get_due_automations(current_time: datetime = None) -> List[Automation]:
        """Get automations that need to run now"""

    async def execute_automation(automation_id: UUID) -> AutomationRun:
        """Execute an automation and record results"""

    def pause_automation(automation_id: UUID) -> Automation:
        """Pause an automation"""

    def resume_automation(automation_id: UUID) -> Automation:
        """Resume a paused automation"""
```

### 4. Schedule Configuration

Automations support flexible scheduling:

#### Interval-based
```json
{
  "type": "interval",
  "interval_minutes": 60
}
```
Runs every N minutes.

#### Daily
```json
{
  "type": "daily",
  "hour": 9
}
```
Runs daily at 9:00 AM UTC.

#### Weekly
```json
{
  "type": "weekly",
  "weekday": 0,  # 0=Monday, 6=Sunday
  "hour": 9
}
```
Runs weekly on Monday at 9:00 AM UTC.

## Database Schema

### Automation Table
```sql
CREATE TABLE automation (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    destination_id UUID NOT NULL REFERENCES destination(id),
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- scheduled_report, alert, data_sync
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, paused, stopped, error
    schedule_config JSON,
    automation_config JSON,
    platforms JSON,  -- ["facebook", "tiktok"]
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### AutomationRun Table
```sql
CREATE TABLE automation_run (
    id UUID PRIMARY KEY,
    automation_id UUID NOT NULL REFERENCES automation(id),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    result JSON,
    error_message TEXT,
    logs JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Usage Examples

### Creating an Automation via API

```python
import httpx

# 1. Create a scheduled report automation
response = httpx.post(
    "http://localhost:8000/api/automations",
    json={
        "tenant_id": "tenant-uuid",
        "destination_id": "destination-uuid",
        "name": "Daily Facebook Report",
        "type": "scheduled_report",
        "schedule_config": {
            "type": "daily",
            "hour": 9
        },
        "automation_config": {
            "period": "daily",
            "days": 7,
            "metric_types": ["ad_account", "pages"],
            "format": "text"
        },
        "platforms": ["facebook"]
    }
)
```

### Creating an Alert Automation

```python
response = httpx.post(
    "http://localhost:8000/api/automations",
    json={
        "tenant_id": "tenant-uuid",
        "destination_id": "destination-uuid",
        "name": "Spend Alert",
        "type": "alert",
        "schedule_config": {
            "type": "interval",
            "interval_minutes": 30
        },
        "automation_config": {
            "thresholds": {
                "max_daily_spend": 1000.00,
                "min_ctr": 2.0
            }
        },
        "platforms": ["facebook"]
    }
)
```

### Pausing/Resuming an Automation

```python
# Pause
httpx.post(f"http://localhost:8000/api/automations/{automation_id}/pause")

# Resume
httpx.post(f"http://localhost:8000/api/automations/{automation_id}/resume")
```

## Testing

### Manual Testing

```bash
# 1. Create a test automation
python app/scripts/test_scheduler.py

# 2. Start the FastAPI server (scheduler starts automatically)
uvicorn app.main:app --reload

# 3. Check logs for scheduler activity
# Look for:
# - "🚀 Automation scheduler started"
# - "Found N automation(s) due for execution"
# - "▶️  Executing automation: ..."
# - "✅ Automation completed successfully"
```

### Checking Execution History

```sql
-- View all automation runs
SELECT
    ar.id,
    a.name,
    ar.status,
    ar.started_at,
    ar.completed_at,
    ar.error_message
FROM automation_run ar
JOIN automation a ON ar.automation_id = a.id
ORDER BY ar.started_at DESC
LIMIT 20;

-- View automation statistics
SELECT
    id,
    name,
    status,
    last_run,
    next_run,
    run_count,
    error_count
FROM automation
WHERE tenant_id = 'your-tenant-id';
```

## Configuration Reference

### Environment Variables

```bash
# Automation Scheduler
AUTOMATION_CHECK_INTERVAL=60  # Check interval in seconds (default: 60)

# Token Refresh Worker
TOKEN_REFRESH_INTERVAL=3600   # Check interval in seconds (default: 3600)

# Cleanup Worker
CLEANUP_INTERVAL=86400        # Check interval in seconds (default: 86400)
```

### Application Settings

In `app/core/config.py`:

```python
class Settings(BaseSettings):
    # Background Job Configuration
    TOKEN_REFRESH_INTERVAL: int = Field(
        default=3600,
        description="Token refresh check interval in seconds",
        ge=60
    )
    AUTOMATION_CHECK_INTERVAL: int = Field(
        default=60,
        description="Automation scheduler check interval in seconds",
        ge=10
    )
    CLEANUP_INTERVAL: int = Field(
        default=86400,
        description="Cleanup job interval in seconds",
        ge=3600
    )
```

## Monitoring & Logging

### Log Levels

- **INFO**: Normal operation, automation execution
- **WARNING**: Recoverable errors, retry attempts
- **ERROR**: Failed executions, critical issues

### Key Log Messages

```
🚀 Automation scheduler started (check interval: 60s)
Found 3 automation(s) due for execution
▶️  Executing automation: Daily Facebook Report (ID: abc-123, Type: scheduled_report)
✅ Automation Daily Facebook Report completed successfully (Run ID: def-456)
❌ Error executing automation: [error details]
```

### Metrics to Monitor

- Automation execution success rate
- Average execution time
- Error rate by automation type
- Destination delivery success rate

## Troubleshooting

### Automation Not Running

1. **Check automation status**:
   ```sql
   SELECT id, name, status, next_run FROM automation WHERE id = 'your-id';
   ```
   Ensure `status = 'active'` and `next_run` is in the past.

2. **Check scheduler logs**:
   Look for "Found N automation(s) due for execution" messages.

3. **Check scheduler interval**:
   Verify `AUTOMATION_CHECK_INTERVAL` is set appropriately.

### Execution Errors

1. **Check automation run logs**:
   ```sql
   SELECT * FROM automation_run
   WHERE automation_id = 'your-id'
   ORDER BY started_at DESC LIMIT 1;
   ```

2. **Common issues**:
   - Invalid/expired OAuth tokens → Check token validity
   - Platform API errors → Check API credentials
   - Destination errors → Verify destination configuration

### Performance Issues

1. **Reduce check interval** if too many automations
2. **Use interval-based scheduling** instead of frequent cron schedules
3. **Monitor database query performance**

## Future Enhancements

- [ ] Cron expression support for scheduling
- [ ] Retry policies for failed executions
- [ ] Rate limiting for platform API calls
- [ ] Execution priority queues
- [ ] Distributed worker support (Celery/Redis)
- [ ] Automation templates
- [ ] Web UI for automation management
- [ ] Real-time execution monitoring dashboard

## References

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Asyncio Task Management](https://docs.python.org/3/library/asyncio-task.html)
