"""DNS management service for Cloudflare integration."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from .client import CloudflareService
from .models import (
    DNSRecord,
    DNSRecordCreate,
    DNSRecordUpdate,
    DNSRecordResponse,
    CloudflareOperation,
    BulkDNSOperation,
)
from .exceptions import CloudflareError, CloudflareValidationError

logger = logging.getLogger(__name__)


class DNSManagementService:
    """High-level DNS management service with database synchronization."""

    def __init__(self, cloudflare_service: CloudflareService, tenant_id: Optional[str] = None):
        """Initialize DNS management service."""
        self.cf_service = cloudflare_service
        self.tenant_id = tenant_id

    async def sync_dns_records(self, session: Session) -> Dict[str, int]:
        """Sync DNS records from Cloudflare to local database."""
        try:
            # Fetch all DNS records from Cloudflare
            cf_records = await self.cf_service.list_dns_records(per_page=1000)

            stats = {"created": 0, "updated": 0, "deleted": 0, "errors": 0}

            # Get existing records from database
            existing_records = session.execute(
                select(DNSRecord).where(DNSRecord.tenant_id == self.tenant_id)
            ).scalars().all()
            existing_ids = {record.id for record in existing_records}
            cf_record_ids = set()

            for cf_record in cf_records:
                try:
                    cf_record_ids.add(cf_record["id"])

                    # Check if record exists in database
                    existing_record = session.get(DNSRecord, cf_record["id"])

                    if existing_record:
                        # Update existing record
                        existing_record.name = cf_record["name"]
                        existing_record.type = cf_record["type"]
                        existing_record.content = cf_record["content"]
                        existing_record.ttl = cf_record["ttl"]
                        existing_record.proxied = cf_record.get("proxied", False)
                        existing_record.priority = cf_record.get("priority")
                        existing_record.comment = cf_record.get("comment")
                        existing_record.modified_on = datetime.fromisoformat(
                            cf_record["modified_on"].replace("Z", "+00:00")
                        )
                        existing_record.last_synced = datetime.utcnow()
                        existing_record.sync_status = "synced"
                        existing_record.updated_at = datetime.utcnow()

                        session.add(existing_record)
                        stats["updated"] += 1
                    else:
                        # Create new record
                        new_record = DNSRecord(
                            id=cf_record["id"],
                            zone_id=cf_record["zone_id"],
                            name=cf_record["name"],
                            type=cf_record["type"],
                            content=cf_record["content"],
                            ttl=cf_record["ttl"],
                            proxied=cf_record.get("proxied", False),
                            priority=cf_record.get("priority"),
                            comment=cf_record.get("comment"),
                            created_on=datetime.fromisoformat(
                                cf_record["created_on"].replace("Z", "+00:00")
                            ),
                            modified_on=datetime.fromisoformat(
                                cf_record["modified_on"].replace("Z", "+00:00")
                            ),
                            tenant_id=self.tenant_id,
                            last_synced=datetime.utcnow(),
                            sync_status="synced",
                        )
                        session.add(new_record)
                        stats["created"] += 1

                except Exception as e:
                    logger.error(f"Error syncing record {cf_record.get('id')}: {str(e)}")
                    stats["errors"] += 1

            # Mark records that no longer exist in Cloudflare
            deleted_ids = existing_ids - cf_record_ids
            for record_id in deleted_ids:
                record = session.get(DNSRecord, record_id)
                if record:
                    session.delete(record)
                    stats["deleted"] += 1

            session.commit()

            # Log sync operation
            await self._log_operation(
                session=session,
                operation_type="sync",
                resource_type="dns_records",
                status="success",
                result_data=stats,
            )

            return stats

        except Exception as e:
            logger.error(f"Error syncing DNS records: {str(e)}")
            await self._log_operation(
                session=session,
                operation_type="sync",
                resource_type="dns_records",
                status="error",
                error_message=str(e),
            )
            raise CloudflareError(f"Failed to sync DNS records: {str(e)}")

    async def get_dns_records(
        self,
        session: Session,
        record_type: Optional[str] = None,
        name: Optional[str] = None,
        sync_first: bool = False,
    ) -> List[DNSRecordResponse]:
        """Get DNS records from local database with optional Cloudflare sync."""
        try:
            if sync_first:
                await self.sync_dns_records(session)

            query = select(DNSRecord).where(DNSRecord.tenant_id == self.tenant_id)

            if record_type:
                query = query.where(DNSRecord.type == record_type)
            if name:
                query = query.where(DNSRecord.name.contains(name))

            records = session.execute(query).scalars().all()

            return [
                DNSRecordResponse(
                    id=record.id,
                    zone_id=record.zone_id,
                    zone_name=self.cf_service.config.domain,
                    name=record.name,
                    type=record.type,
                    content=record.content,
                    ttl=record.ttl,
                    proxied=record.proxied,
                    priority=record.priority,
                    comment=record.comment,
                    created_on=record.created_on,
                    modified_on=record.modified_on,
                    tenant_id=str(record.tenant_id) if record.tenant_id else None,
                    last_synced=record.last_synced,
                    sync_status=record.sync_status,
                )
                for record in records
            ]

        except Exception as e:
            logger.error(f"Error getting DNS records: {str(e)}")
            raise CloudflareError(f"Failed to get DNS records: {str(e)}")

    async def create_dns_record(
        self, session: Session, record_data: DNSRecordCreate, user_id: Optional[str] = None
    ) -> DNSRecordResponse:
        """Create a new DNS record in Cloudflare and local database."""
        try:
            # Validate record data
            self._validate_dns_record(record_data.model_dump())

            # Create record in Cloudflare
            cf_data = record_data.model_dump(exclude_none=True)
            cf_record = await self.cf_service.create_dns_record(cf_data)

            # Create record in local database
            db_record = DNSRecord(
                id=cf_record["id"],
                zone_id=cf_record["zone_id"],
                name=cf_record["name"],
                type=cf_record["type"],
                content=cf_record["content"],
                ttl=cf_record["ttl"],
                proxied=cf_record.get("proxied", False),
                priority=cf_record.get("priority"),
                comment=cf_record.get("comment"),
                created_on=datetime.fromisoformat(cf_record["created_on"].replace("Z", "+00:00")),
                modified_on=datetime.fromisoformat(cf_record["modified_on"].replace("Z", "+00:00")),
                tenant_id=self.tenant_id,
                last_synced=datetime.utcnow(),
                sync_status="synced",
            )

            session.add(db_record)
            session.commit()

            # Log operation
            await self._log_operation(
                session=session,
                operation_type="create",
                resource_type="dns_record",
                resource_id=cf_record["id"],
                user_id=user_id,
                operation_data=cf_data,
                result_data=cf_record,
                status="success",
            )

            return DNSRecordResponse(
                id=cf_record["id"],
                zone_id=cf_record["zone_id"],
                zone_name=self.cf_service.config.domain,
                name=cf_record["name"],
                type=cf_record["type"],
                content=cf_record["content"],
                ttl=cf_record["ttl"],
                proxied=cf_record.get("proxied", False),
                priority=cf_record.get("priority"),
                comment=cf_record.get("comment"),
                created_on=datetime.fromisoformat(cf_record["created_on"].replace("Z", "+00:00")),
                modified_on=datetime.fromisoformat(cf_record["modified_on"].replace("Z", "+00:00")),
                tenant_id=str(self.tenant_id) if self.tenant_id else None,
                last_synced=datetime.utcnow(),
                sync_status="synced",
            )

        except Exception as e:
            logger.error(f"Error creating DNS record: {str(e)}")
            await self._log_operation(
                session=session,
                operation_type="create",
                resource_type="dns_record",
                user_id=user_id,
                operation_data=record_data.model_dump(),
                status="error",
                error_message=str(e),
            )
            raise CloudflareError(f"Failed to create DNS record: {str(e)}")

    async def update_dns_record(
        self,
        session: Session,
        record_id: str,
        record_data: DNSRecordUpdate,
        user_id: Optional[str] = None,
    ) -> DNSRecordResponse:
        """Update an existing DNS record."""
        try:
            # Get existing record
            existing_record = session.get(DNSRecord, record_id)
            if not existing_record or str(existing_record.tenant_id) != str(self.tenant_id):
                raise CloudflareError(f"DNS record {record_id} not found")

            # Validate update data
            update_data = record_data.model_dump(exclude_none=True)
            if update_data:
                self._validate_dns_record(update_data, partial=True)

            # Update record in Cloudflare
            cf_record = await self.cf_service.update_dns_record(record_id, update_data)

            # Update record in local database
            for field, value in update_data.items():
                if hasattr(existing_record, field):
                    setattr(existing_record, field, value)

            existing_record.modified_on = datetime.fromisoformat(
                cf_record["modified_on"].replace("Z", "+00:00")
            )
            existing_record.last_synced = datetime.utcnow()
            existing_record.sync_status = "synced"
            existing_record.updated_at = datetime.utcnow()

            session.add(existing_record)
            session.commit()

            # Log operation
            await self._log_operation(
                session=session,
                operation_type="update",
                resource_type="dns_record",
                resource_id=record_id,
                user_id=user_id,
                operation_data=update_data,
                result_data=cf_record,
                status="success",
            )

            return DNSRecordResponse(
                id=cf_record["id"],
                zone_id=cf_record["zone_id"],
                zone_name=self.cf_service.config.domain,
                name=cf_record["name"],
                type=cf_record["type"],
                content=cf_record["content"],
                ttl=cf_record["ttl"],
                proxied=cf_record.get("proxied", False),
                priority=cf_record.get("priority"),
                comment=cf_record.get("comment"),
                created_on=datetime.fromisoformat(cf_record["created_on"].replace("Z", "+00:00")),
                modified_on=datetime.fromisoformat(cf_record["modified_on"].replace("Z", "+00:00")),
                tenant_id=str(self.tenant_id) if self.tenant_id else None,
                last_synced=datetime.utcnow(),
                sync_status="synced",
            )

        except Exception as e:
            logger.error(f"Error updating DNS record {record_id}: {str(e)}")
            await self._log_operation(
                session=session,
                operation_type="update",
                resource_type="dns_record",
                resource_id=record_id,
                user_id=user_id,
                operation_data=record_data.model_dump(),
                status="error",
                error_message=str(e),
            )
            raise CloudflareError(f"Failed to update DNS record: {str(e)}")

    async def delete_dns_record(
        self, session: Session, record_id: str, user_id: Optional[str] = None
    ) -> bool:
        """Delete a DNS record."""
        try:
            # Get existing record
            existing_record = session.get(DNSRecord, record_id)
            if not existing_record or str(existing_record.tenant_id) != str(self.tenant_id):
                raise CloudflareError(f"DNS record {record_id} not found")

            # Delete record from Cloudflare
            await self.cf_service.delete_dns_record(record_id)

            # Delete record from local database
            session.delete(existing_record)
            session.commit()

            # Log operation
            await self._log_operation(
                session=session,
                operation_type="delete",
                resource_type="dns_record",
                resource_id=record_id,
                user_id=user_id,
                status="success",
            )

            return True

        except Exception as e:
            logger.error(f"Error deleting DNS record {record_id}: {str(e)}")
            await self._log_operation(
                session=session,
                operation_type="delete",
                resource_type="dns_record",
                resource_id=record_id,
                user_id=user_id,
                status="error",
                error_message=str(e),
            )
            raise CloudflareError(f"Failed to delete DNS record: {str(e)}")

    def _validate_dns_record(self, record_data: Dict[str, Any], partial: bool = False) -> None:
        """Validate DNS record data."""
        if not partial:
            required_fields = ["name", "type", "content"]
            for field in required_fields:
                if field not in record_data:
                    raise CloudflareValidationError(f"Missing required field: {field}")

        # Validate record type
        valid_types = ["A", "AAAA", "CNAME", "MX", "TXT", "SRV", "NS", "PTR"]
        if "type" in record_data and record_data["type"] not in valid_types:
            raise CloudflareValidationError(f"Invalid record type: {record_data['type']}")

        # Validate TTL
        if "ttl" in record_data:
            ttl = record_data["ttl"]
            if not isinstance(ttl, int) or ttl < 1 or ttl > 2147483647:
                raise CloudflareValidationError("TTL must be between 1 and 2147483647")

        # Validate MX priority
        if record_data.get("type") == "MX" and "priority" not in record_data:
            raise CloudflareValidationError("MX records require a priority field")

    async def _log_operation(
        self,
        session: Session,
        operation_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        operation_data: Optional[Dict[str, Any]] = None,
        result_data: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        error_message: Optional[str] = None,
    ) -> CloudflareOperation:
        """Log Cloudflare operation for audit trail."""
        operation = CloudflareOperation(
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            operation_data=operation_data,
            result_data=result_data,
            status=status,
            error_message=error_message,
            user_id=user_id,
            tenant_id=self.tenant_id,
            completed_at=datetime.utcnow() if status in ["success", "error"] else None,
        )

        session.add(operation)
        session.commit()
        return operation
