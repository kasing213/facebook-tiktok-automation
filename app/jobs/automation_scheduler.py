# app/jobs/automation_scheduler.py
"""
Background job scheduler for executing automations based on their schedules.

This scheduler:
1. Periodically checks for automations that are due to run
2. Executes them using the AutomationService
3. Handles errors and retries
4. Logs execution results
"""
import asyncio
import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.core.models import Automation, AutomationStatus
from app.services.automation_service import AutomationService

logger = logging.getLogger(__name__)


class AutomationScheduler:
    """Background scheduler for executing automations"""

    def __init__(self, check_interval: int = 60):
        """
        Initialize the automation scheduler

        Args:
            check_interval: How often to check for due automations (in seconds)
        """
        self.check_interval = check_interval
        self.logger = logger
        self.is_running = False

    async def run_scheduler(self):
        """Main scheduler loop - checks and executes due automations"""
        self.is_running = True
        self.logger.info(f"🚀 Automation scheduler started (check interval: {self.check_interval}s)")

        while self.is_running:
            try:
                await self.check_and_execute_automations()

                # Wait for next check
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Automation scheduler error: {e}", exc_info=True)
                # Wait a bit before retrying on error
                await asyncio.sleep(min(self.check_interval, 300))

    async def check_and_execute_automations(self):
        """Check for due automations and execute them"""
        try:
            with get_db_session() as db:
                automation_service = AutomationService(db)

                # Get all automations that are due to run
                due_automations = automation_service.get_due_automations()

                if not due_automations:
                    self.logger.debug("No automations due for execution")
                    return

                self.logger.info(f"Found {len(due_automations)} automation(s) due for execution")

                # Execute each automation
                for automation in due_automations:
                    await self.execute_automation_safe(automation, db)

        except Exception as e:
            self.logger.error(f"Error checking due automations: {e}", exc_info=True)

    async def execute_automation_safe(self, automation: Automation, db: Session):
        """
        Execute a single automation with error handling

        Args:
            automation: The automation to execute
            db: Database session
        """
        try:
            self.logger.info(
                f"▶️  Executing automation: {automation.name} "
                f"(ID: {automation.id}, Type: {automation.type.value})"
            )

            automation_service = AutomationService(db)
            run = await automation_service.execute_automation(automation.id)

            self.logger.info(
                f"✅ Automation {automation.name} completed successfully "
                f"(Run ID: {run.id})"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Error executing automation {automation.name} "
                f"(ID: {automation.id}): {e}",
                exc_info=True
            )

    def stop(self):
        """Stop the scheduler gracefully"""
        self.logger.info("Stopping automation scheduler...")
        self.is_running = False


# Global scheduler instance
automation_scheduler = AutomationScheduler(check_interval=60)


async def run_automation_scheduler(check_interval: int = 60):
    """
    Run the automation scheduler - call this from your main application

    Args:
        check_interval: How often to check for due automations (in seconds)
    """
    scheduler = AutomationScheduler(check_interval=check_interval)
    await scheduler.run_scheduler()
