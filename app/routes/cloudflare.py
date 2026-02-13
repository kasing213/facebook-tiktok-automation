"""Cloudflare integration API routes."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.authorization import get_current_owner
from app.core.models import User, UserRole
from app.core.config import get_settings
from app.cloudflare import (
    CloudflareService,
    DNSManagementService,
    CloudflareConfig,
)
from app.cloudflare.models import (
    DNSRecordCreate,
    DNSRecordUpdate,
    DNSRecordResponse,
    BulkDNSOperation,
    CloudflareHealthStatus,
)
from app.cloudflare.exceptions import CloudflareError, CloudflareConfigError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloudflare", tags=["cloudflare"])

settings = get_settings()


def get_cloudflare_config() -> CloudflareConfig:
    """Get Cloudflare configuration from environment."""
    try:
        # Extract secret values — settings fields are SecretStr
        api_token = settings.CLOUDFLARE_API_TOKEN.get_secret_value() or None
        api_key = settings.CLOUDFLARE_API_KEY.get_secret_value() or None

        return CloudflareConfig(
            domain=settings.CLOUDFLARE_DOMAIN,
            api_token=api_token,
            email=settings.CLOUDFLARE_EMAIL or None,
            api_key=api_key,
            zone_id=settings.CLOUDFLARE_ZONE_ID,
            test_mode=settings.CLOUDFLARE_TEST_MODE,
            request_timeout=settings.CLOUDFLARE_REQUEST_TIMEOUT,
            max_requests_per_minute=settings.CLOUDFLARE_MAX_REQUESTS_PER_MINUTE,
            log_level=settings.CLOUDFLARE_LOG_LEVEL,
            audit_logging=settings.CLOUDFLARE_AUDIT_LOGGING,
            sync_to_db=settings.CLOUDFLARE_SYNC_TO_DB,
            cache_ttl=settings.CLOUDFLARE_CACHE_TTL,
            auto_update_enabled=settings.CLOUDFLARE_AUTO_UPDATE_ENABLED,
            require_superuser=settings.CLOUDFLARE_REQUIRE_SUPERUSER,
        )
    except Exception as e:
        raise CloudflareConfigError(f"Failed to load Cloudflare configuration: {str(e)}")


async def get_cloudflare_service(
    config: CloudflareConfig = Depends(get_cloudflare_config),
) -> CloudflareService:
    """Get Cloudflare service instance."""
    if not settings.CLOUDFLARE_INTEGRATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudflare integration is disabled"
        )

    service = CloudflareService(config)
    try:
        await service._initialize_client()
        return service
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize Cloudflare service: {str(e)}"
        )


async def get_dns_service(
    cf_service: CloudflareService = Depends(get_cloudflare_service),
    current_user: User = Depends(get_current_user),
) -> DNSManagementService:
    """Get DNS management service with user context."""
    config = cf_service.config
    if config.require_superuser and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for Cloudflare operations"
        )

    return DNSManagementService(cf_service, tenant_id=str(current_user.tenant_id))


@router.get("/health", response_model=CloudflareHealthStatus)
async def health_check(
    cf_service: CloudflareService = Depends(get_cloudflare_service),
) -> CloudflareHealthStatus:
    """Check Cloudflare service health status."""
    try:
        return await cf_service.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )
    finally:
        await cf_service.close()


@router.get("/zone/info")
async def get_zone_info(
    cf_service: CloudflareService = Depends(get_cloudflare_service),
    current_user: User = Depends(get_current_owner),
):
    """Get Cloudflare zone information."""
    try:
        zone_info = await cf_service.get_zone_info()
        return {"zone": zone_info}
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get zone info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get zone information"
        )
    finally:
        await cf_service.close()


@router.post("/dns/sync")
async def sync_dns_records(
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_owner),
):
    """Sync DNS records from Cloudflare to local database."""
    try:
        stats = await dns_service.sync_dns_records(db)
        return {"message": "DNS records synced successfully", "stats": stats}
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync DNS records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync DNS records"
        )
    finally:
        await dns_service.cf_service.close()


@router.get("/dns/records", response_model=List[DNSRecordResponse])
async def get_dns_records(
    record_type: Optional[str] = None,
    name: Optional[str] = None,
    sync_first: bool = False,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
) -> List[DNSRecordResponse]:
    """Get DNS records with optional filtering and sync."""
    try:
        records = await dns_service.get_dns_records(
            session=db,
            record_type=record_type,
            name=name,
            sync_first=sync_first,
        )
        return records
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get DNS records: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get DNS records"
        )
    finally:
        await dns_service.cf_service.close()


@router.post("/dns/records", response_model=DNSRecordResponse)
async def create_dns_record(
    record_data: DNSRecordCreate,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_user),
) -> DNSRecordResponse:
    """Create a new DNS record."""
    try:
        record = await dns_service.create_dns_record(
            session=db,
            record_data=record_data,
            user_id=str(current_user.id),
        )
        return record
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create DNS record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create DNS record"
        )
    finally:
        await dns_service.cf_service.close()


@router.get("/dns/records/{record_id}", response_model=DNSRecordResponse)
async def get_dns_record(
    record_id: str,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
) -> DNSRecordResponse:
    """Get a specific DNS record."""
    try:
        records = await dns_service.get_dns_records(session=db)
        record = next((r for r in records if r.id == record_id), None)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DNS record not found"
            )

        return record
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get DNS record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get DNS record"
        )
    finally:
        await dns_service.cf_service.close()


@router.put("/dns/records/{record_id}", response_model=DNSRecordResponse)
async def update_dns_record(
    record_id: str,
    record_data: DNSRecordUpdate,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_user),
) -> DNSRecordResponse:
    """Update an existing DNS record."""
    try:
        record = await dns_service.update_dns_record(
            session=db,
            record_id=record_id,
            record_data=record_data,
            user_id=str(current_user.id),
        )
        return record
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update DNS record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update DNS record"
        )
    finally:
        await dns_service.cf_service.close()


@router.delete("/dns/records/{record_id}")
async def delete_dns_record(
    record_id: str,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_user),
):
    """Delete a DNS record."""
    try:
        success = await dns_service.delete_dns_record(
            session=db,
            record_id=record_id,
            user_id=str(current_user.id),
        )

        if success:
            return {"message": "DNS record deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete DNS record"
            )
    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete DNS record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete DNS record"
        )
    finally:
        await dns_service.cf_service.close()


@router.post("/dns/bulk")
async def bulk_dns_operation(
    operation: BulkDNSOperation,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_owner),
):
    """Perform bulk DNS operations."""
    try:
        results = []
        errors = []

        for i, record_data in enumerate(operation.records):
            try:
                if operation.operation_type == "create":
                    record_create = DNSRecordCreate(**record_data)
                    result = await dns_service.create_dns_record(
                        session=db,
                        record_data=record_create,
                        user_id=str(current_user.id),
                    )
                    results.append({"index": i, "status": "success", "record": result})

                elif operation.operation_type == "update":
                    record_id = record_data.pop("id")
                    record_update = DNSRecordUpdate(**record_data)
                    result = await dns_service.update_dns_record(
                        session=db,
                        record_id=record_id,
                        record_data=record_update,
                        user_id=str(current_user.id),
                    )
                    results.append({"index": i, "status": "success", "record": result})

                elif operation.operation_type == "delete":
                    record_id = record_data["id"]
                    await dns_service.delete_dns_record(
                        session=db,
                        record_id=record_id,
                        user_id=str(current_user.id),
                    )
                    results.append({"index": i, "status": "success", "record_id": record_id})

                else:
                    errors.append({"index": i, "error": f"Invalid operation type: {operation.operation_type}"})

            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return {
            "message": "Bulk operation completed",
            "total": len(operation.records),
            "success": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors,
        }

    except Exception as e:
        logger.error(f"Bulk DNS operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk operation failed"
        )
    finally:
        await dns_service.cf_service.close()


@router.post("/facebook/domain-verification")
async def create_facebook_verification_record(
    verification_code: str,
    db: Session = Depends(get_db),
    dns_service: DNSManagementService = Depends(get_dns_service),
    current_user: User = Depends(get_current_user),
) -> DNSRecordResponse:
    """Create Facebook domain verification TXT record."""
    try:
        # Create TXT record for Facebook domain verification
        record_data = DNSRecordCreate(
            name=dns_service.cf_service.config.domain,
            type="TXT",
            content=f"facebook-domain-verification={verification_code}",
            ttl=300,
            comment="Facebook domain verification record",
        )

        record = await dns_service.create_dns_record(
            session=db,
            record_data=record_data,
            user_id=str(current_user.id),
        )

        return record

    except CloudflareError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create Facebook verification record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Facebook verification record"
        )
    finally:
        await dns_service.cf_service.close()
