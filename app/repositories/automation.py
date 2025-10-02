# app/repositories/automation.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.models import Automation, AutomationType, AutomationStatus, AutomationRun
from .base import BaseRepository


class AutomationRepository(BaseRepository[Automation]):
    """Repository for automation operations"""

    def __init__(self, db: Session):
        super().__init__(db, Automation)

    def get_tenant_automations(
        self,
        tenant_id: UUID,
        status: AutomationStatus = None,
        automation_type: AutomationType = None
    ) -> List[Automation]:
        """Get automations for a tenant with optional filters"""
        filters = {"tenant_id": tenant_id}
        if status:
            filters["status"] = status
        if automation_type:
            filters["type"] = automation_type
        return self.find_by(**filters)

    def get_active_automations(self, tenant_id: UUID = None) -> List[Automation]:
        """Get all active automations, optionally filtered by tenant"""
        filters = {"status": AutomationStatus.active}
        if tenant_id:
            filters["tenant_id"] = tenant_id
        return self.find_by(**filters)

    def get_due_automations(self, current_time: datetime = None) -> List[Automation]:
        """Get automations that are due to run"""
        if current_time is None:
            current_time = datetime.utcnow()

        return (
            self.db.query(Automation)
            .filter(
                and_(
                    Automation.status == AutomationStatus.active,
                    or_(
                        Automation.next_run.is_(None),
                        Automation.next_run <= current_time
                    )
                )
            )
            .all()
        )

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
        """Create a new automation"""
        return self.create(
            tenant_id=tenant_id,
            destination_id=destination_id,
            name=name,
            type=automation_type,
            status=AutomationStatus.active,
            schedule_config=schedule_config or {},
            automation_config=automation_config or {},
            platforms=platforms or []
        )

    def update_run_info(
        self,
        automation_id: UUID,
        next_run: datetime = None,
        last_run: datetime = None,
        increment_run_count: bool = True
    ) -> Optional[Automation]:
        """Update automation run information"""
        updates = {}
        if next_run:
            updates["next_run"] = next_run
        if last_run:
            updates["last_run"] = last_run

        automation = self.get_by_id(automation_id)
        if automation and increment_run_count:
            updates["run_count"] = automation.run_count + 1

        return self.update(automation_id, **updates) if updates else automation

    def record_error(self, automation_id: UUID, error_message: str) -> Optional[Automation]:
        """Record an error for an automation"""
        automation = self.get_by_id(automation_id)
        if automation:
            return self.update(
                automation_id,
                error_count=automation.error_count + 1,
                last_error=error_message,
                status=AutomationStatus.error
            )
        return None

    def pause_automation(self, automation_id: UUID) -> Optional[Automation]:
        """Pause an automation"""
        return self.update(automation_id, status=AutomationStatus.paused)

    def resume_automation(self, automation_id: UUID) -> Optional[Automation]:
        """Resume a paused automation"""
        return self.update(automation_id, status=AutomationStatus.active)


class AutomationRunRepository(BaseRepository[AutomationRun]):
    """Repository for automation run operations"""

    def __init__(self, db: Session):
        super().__init__(db, AutomationRun)

    def create_run(
        self,
        automation_id: UUID,
        status: str = "running",
        result: dict = None,
        logs: dict = None
    ) -> AutomationRun:
        """Create a new automation run"""
        return self.create(
            automation_id=automation_id,
            status=status,
            result=result or {},
            logs=logs or {}
        )

    def complete_run(
        self,
        run_id: UUID,
        status: str,
        result: dict = None,
        error_message: str = None,
        logs: dict = None
    ) -> Optional[AutomationRun]:
        """Complete an automation run"""
        return self.update(
            run_id,
            completed_at=datetime.utcnow(),
            status=status,
            result=result,
            error_message=error_message,
            logs=logs
        )

    def get_automation_runs(
        self,
        automation_id: UUID,
        limit: int = 100,
        status: str = None
    ) -> List[AutomationRun]:
        """Get runs for a specific automation"""
        query = self.db.query(AutomationRun).filter(AutomationRun.automation_id == automation_id)
        if status:
            query = query.filter(AutomationRun.status == status)
        return query.order_by(AutomationRun.started_at.desc()).limit(limit).all()