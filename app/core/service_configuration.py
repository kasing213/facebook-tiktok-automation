# app/core/service_configuration.py
"""
Service layer configuration and dependency injection setup.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.core.dependency_injection import DIContainer, configure_services
from app.core.db import get_db_session_with_retry
from app.core.crypto import TokenEncryptor
from app.services.cache_service import CacheManager
from app.services.circuit_breaker import CircuitBreakerRegistry
from app.services.task_queue import TaskQueue
from app.services.health_monitor import ServiceHealthMonitor


# Abstract service interfaces
class IAuthService:
    """Auth service interface"""
    pass


class IInventoryService:
    """Inventory service interface"""
    pass


class IInvoiceService:
    """Invoice service interface"""
    pass


class IOCRService:
    """OCR service interface"""
    pass


class IEmailService:
    """Email service interface"""
    pass


# Service implementations would implement these interfaces
# from app.services.auth_service import AuthService
# from app.services.inventory_service import InventoryService
# etc.


def configure_core_services(container: DIContainer) -> None:
    """Configure core infrastructure services"""

    # Database session factory
    def db_factory() -> Session:
        return next(get_db_session_with_retry())

    container.register_factory(Session, db_factory, scope=DIContainer.ServiceScope.SCOPED)

    # Crypto services
    container.register_singleton(TokenEncryptor, TokenEncryptor)

    # Cache manager (singleton)
    container.register_singleton(CacheManager, CacheManager)

    # Circuit breaker registry (singleton)
    container.register_singleton(CircuitBreakerRegistry, CircuitBreakerRegistry)

    # Task queue (singleton)
    container.register_singleton(TaskQueue, TaskQueue)

    # Health monitor (singleton)
    container.register_singleton(ServiceHealthMonitor, ServiceHealthMonitor)


def configure_business_services(container: DIContainer) -> None:
    """Configure business logic services"""

    # Auth service (scoped to request/transaction)
    # container.register_scoped(IAuthService, AuthService)

    # Inventory service (scoped)
    # container.register_scoped(IInventoryService, InventoryService)

    # Invoice service (scoped)
    # container.register_scoped(IInvoiceService, InvoiceService)

    # OCR service (transient - each request gets new instance)
    # container.register_transient(IOCRService, OCRService)

    # Email service (transient)
    # container.register_transient(IEmailService, EmailService)

    pass  # Services would be registered here


def configure_external_services(container: DIContainer) -> None:
    """Configure external service clients"""

    # HTTP clients, API clients, etc.
    # These are typically transient or singleton depending on thread safety

    pass


def setup_dependency_injection() -> None:
    """
    Main function to set up all dependency injection configuration.
    Call this during application startup.
    """
    def configurator(container: DIContainer) -> None:
        configure_core_services(container)
        configure_business_services(container)
        configure_external_services(container)

    configure_services(configurator)


# Example service decorators (would be used on actual service classes)

# @singleton_service(IAuthService)
# class AuthService(BaseService):
#     def __init__(self, db: Session, encryptor: TokenEncryptor):
#         super().__init__(db)
#         self.encryptor = encryptor
#
#     def _service_specific_health_checks(self) -> Dict[str, Any]:
#         return {"encryptor": self.encryptor is not None}


# @scoped_service(IInventoryService)
# class InventoryService(BaseService):
#     def __init__(self, db: Session, cache_manager: CacheManager):
#         super().__init__(db)
#         self.cache = cache_manager.get_service_cache(self.__class__.__name__)
#
#     def _service_specific_health_checks(self) -> Dict[str, Any]:
#         return self.cache.get_cache_stats()


# FastAPI dependency injection integration
def get_auth_service() -> 'IAuthService':
    """FastAPI dependency for auth service"""
    from app.core.dependency_injection import resolve_service
    return resolve_service(IAuthService)


def get_inventory_service() -> 'IInventoryService':
    """FastAPI dependency for inventory service"""
    from app.core.dependency_injection import resolve_service
    return resolve_service(IInventoryService)


def get_invoice_service() -> 'IInvoiceService':
    """FastAPI dependency for invoice service"""
    from app.core.dependency_injection import resolve_service
    return resolve_service(IInvoiceService)