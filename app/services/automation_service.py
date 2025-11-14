# app/services/automation_service.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.models import Automation, AutomationType, AutomationStatus, AutomationRun
from app.repositories import AutomationRepository, AutomationRunRepository


class AutomationService:
    """Service layer for automation management"""

    def __init__(self, db: Session):
        self.db = db
        self.automation_repo = AutomationRepository(db)
        self.run_repo = AutomationRunRepository(db)

    def create_automation(
        self,
        tenant_id: UUID,
        destination_id: UUID,
        name: str,
        automation_type: AutomationType,
        schedule_config: dict = None,
        automation_config: dict = None,
        platforms: List[str] = None
    ) -> Automation:
        """Create a new automation with proper validation"""
        # Calculate initial next_run if schedule is provided
        next_run = None
        if schedule_config:
            next_run = self._calculate_next_run(schedule_config)

        automation = self.automation_repo.create_automation(
            tenant_id=tenant_id,
            destination_id=destination_id,
            name=name,
            automation_type=automation_type,
            schedule_config=schedule_config,
            automation_config=automation_config,
            platforms=platforms
        )

        if next_run:
            self.automation_repo.update(automation.id, next_run=next_run)

        self.db.commit()
        return automation

    def get_due_automations(self, current_time: datetime = None) -> List[Automation]:
        """Get all automations that are due to run"""
        return self.automation_repo.get_due_automations(current_time)

    async def execute_automation(self, automation_id: UUID) -> AutomationRun:
        """Execute an automation and create a run record"""
        automation = self.automation_repo.get_by_id(automation_id)
        if not automation:
            raise ValueError(f"Automation {automation_id} not found")

        if automation.status != AutomationStatus.active:
            raise ValueError(f"Automation {automation_id} is not active")

        # Create run record
        run = self.run_repo.create_run(automation_id)

        try:
            # Update automation run info
            now = datetime.utcnow()
            next_run = self._calculate_next_run(automation.schedule_config) if automation.schedule_config else None

            self.automation_repo.update_run_info(
                automation_id=automation_id,
                last_run=now,
                next_run=next_run
            )

            # Execute automation using the appropriate handler
            from app.services.automation_handlers import get_automation_handler
            handler = get_automation_handler(self.db, automation)
            result = await handler.execute()

            # Send results to destination if configured
            if automation.destination_id:
                from app.services.destination_sender import DestinationSenderService
                sender = DestinationSenderService(self.db)

                formatted_output = result.get("formatted_output", "")
                send_result = await sender.send_to_destination(
                    automation.destination_id,
                    formatted_output,
                    metadata={
                        "automation_id": str(automation_id),
                        "automation_name": automation.name,
                        "timestamp": now.isoformat()
                    }
                )

                result["delivery"] = send_result

            # Mark run as completed
            self.run_repo.complete_run(
                run.id,
                status="completed",
                result=result
            )

            self.db.commit()

        except Exception as e:
            # Record error in automation and run
            error_message = str(e)
            self.automation_repo.record_error(automation_id, error_message)
            self.run_repo.complete_run(
                run.id,
                status="failed",
                error_message=error_message
            )
            self.db.commit()
            raise

        return run

    def pause_automation(self, automation_id: UUID) -> Optional[Automation]:
        """Pause an automation"""
        automation = self.automation_repo.pause_automation(automation_id)
        if automation:
            self.db.commit()
        return automation

    def resume_automation(self, automation_id: UUID) -> Optional[Automation]:
        """Resume a paused automation"""
        automation = self.automation_repo.resume_automation(automation_id)
        if automation:
            # Recalculate next run time
            if automation.schedule_config:
                next_run = self._calculate_next_run(automation.schedule_config)
                self.automation_repo.update(automation_id, next_run=next_run)
            self.db.commit()
        return automation

    def get_tenant_automations(
        self,
        tenant_id: UUID,
        status: AutomationStatus = None,
        automation_type: AutomationType = None
    ) -> List[Automation]:
        """Get automations for a tenant"""
        return self.automation_repo.get_tenant_automations(tenant_id, status, automation_type)

    def get_automation_history(self, automation_id: UUID, limit: int = 50) -> List[AutomationRun]:
        """Get execution history for an automation"""
        return self.run_repo.get_automation_runs(automation_id, limit)

    def _calculate_next_run(self, schedule_config: dict) -> datetime:
        """Calculate next run time based on schedule configuration"""
        # Simple implementation - extend as needed for complex scheduling
        now = datetime.utcnow()

        schedule_type = schedule_config.get("type", "interval")

        if schedule_type == "interval":
            interval_minutes = schedule_config.get("interval_minutes", 60)
            return now + timedelta(minutes=interval_minutes)

        elif schedule_type == "daily":
            # Run daily at specified hour (default 9 AM)
            target_hour = schedule_config.get("hour", 9)
            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)

            # If time has passed today, schedule for tomorrow
            if next_run <= now:
                next_run += timedelta(days=1)

            return next_run

        elif schedule_type == "weekly":
            # Run weekly on specified day (0=Monday, 6=Sunday)
            target_weekday = schedule_config.get("weekday", 0)  # Monday
            target_hour = schedule_config.get("hour", 9)

            next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            days_ahead = target_weekday - now.weekday()

            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_run += timedelta(days=days_ahead)
            return next_run

        # Default to 1 hour interval
        return now + timedelta(hours=1)