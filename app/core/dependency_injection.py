# app/core/dependency_injection.py
"""
Service dependency injection system for clean service layer architecture.
"""
import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, TypeVar, Callable, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceScope(Enum):
    """Service lifecycle scopes"""
    SINGLETON = "singleton"  # Single instance for entire application
    SCOPED = "scoped"       # Single instance per request/transaction
    TRANSIENT = "transient" # New instance every time


@dataclass
class ServiceDescriptor:
    """Service registration descriptor"""
    service_type: Type
    implementation_type: Type
    scope: ServiceScope
    factory: Optional[Callable] = None
    dependencies: List[Type] = field(default_factory=list)
    singleton_instance: Optional[Any] = None


class ServiceRegistrationError(Exception):
    """Raised when service registration fails"""
    pass


class ServiceResolutionError(Exception):
    """Raised when service resolution fails"""
    pass


class CircularDependencyError(ServiceResolutionError):
    """Raised when circular dependency is detected"""
    pass


class DIContainer:
    """
    Dependency Injection Container for managing service lifecycles and dependencies.

    Features:
    - Multiple service scopes (singleton, scoped, transient)
    - Automatic dependency resolution
    - Circular dependency detection
    - Factory method support
    - Service decoration
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._resolution_stack: List[Type] = []

    def register(
        self,
        service_type: Type[T],
        implementation_type: Type[T] = None,
        scope: ServiceScope = ServiceScope.TRANSIENT,
        factory: Callable = None
    ) -> 'DIContainer':
        """
        Register a service with the container.

        Args:
            service_type: Service interface or class
            implementation_type: Concrete implementation (defaults to service_type)
            scope: Service lifecycle scope
            factory: Optional factory function

        Returns:
            Self for method chaining

        Raises:
            ServiceRegistrationError: If registration fails
        """
        impl_type = implementation_type or service_type

        if not inspect.isclass(service_type):
            raise ServiceRegistrationError(f"Service type must be a class: {service_type}")

        if factory and not callable(factory):
            raise ServiceRegistrationError(f"Factory must be callable: {factory}")

        # Extract dependencies from constructor
        dependencies = self._extract_dependencies(impl_type if not factory else factory)

        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            scope=scope,
            factory=factory,
            dependencies=dependencies
        )

        self._services[service_type] = descriptor
        logger.debug(f"Registered service: {service_type.__name__} -> {impl_type.__name__} ({scope.value})")

        return self

    def register_singleton(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DIContainer':
        """Register service as singleton"""
        return self.register(service_type, implementation_type, ServiceScope.SINGLETON)

    def register_scoped(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DIContainer':
        """Register service as scoped"""
        return self.register(service_type, implementation_type, ServiceScope.SCOPED)

    def register_transient(self, service_type: Type[T], implementation_type: Type[T] = None) -> 'DIContainer':
        """Register service as transient"""
        return self.register(service_type, implementation_type, ServiceScope.TRANSIENT)

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        scope: ServiceScope = ServiceScope.TRANSIENT
    ) -> 'DIContainer':
        """Register service with factory function"""
        return self.register(service_type, factory=factory, scope=scope)

    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """Register service instance as singleton"""
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=type(instance),
            scope=ServiceScope.SINGLETON,
            singleton_instance=instance
        )

        self._services[service_type] = descriptor
        logger.debug(f"Registered instance: {service_type.__name__}")

        return self

    def resolve(self, service_type: Type[T], scope_id: str = None) -> T:
        """
        Resolve service instance.

        Args:
            service_type: Service type to resolve
            scope_id: Scope identifier for scoped services

        Returns:
            Service instance

        Raises:
            ServiceResolutionError: If service cannot be resolved
            CircularDependencyError: If circular dependency detected
        """
        if service_type in self._resolution_stack:
            cycle = " -> ".join(t.__name__ for t in self._resolution_stack) + f" -> {service_type.__name__}"
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")

        if service_type not in self._services:
            raise ServiceResolutionError(f"Service not registered: {service_type.__name__}")

        descriptor = self._services[service_type]

        try:
            self._resolution_stack.append(service_type)
            return self._create_instance(descriptor, scope_id)
        finally:
            self._resolution_stack.pop()

    def create_scope(self, scope_id: str = None) -> 'ServiceScope':
        """Create new service scope"""
        if scope_id is None:
            import uuid
            scope_id = str(uuid.uuid4())

        return ServiceScope(self, scope_id)

    def _create_instance(self, descriptor: ServiceDescriptor, scope_id: str) -> Any:
        """Create service instance based on scope"""

        # Singleton scope
        if descriptor.scope == ServiceScope.SINGLETON:
            if descriptor.singleton_instance is not None:
                return descriptor.singleton_instance

            instance = self._build_instance(descriptor, scope_id)
            descriptor.singleton_instance = instance
            return instance

        # Scoped instance
        elif descriptor.scope == ServiceScope.SCOPED:
            if not scope_id:
                raise ServiceResolutionError(
                    f"Scoped service {descriptor.service_type.__name__} requires scope_id"
                )

            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}

            scope_services = self._scoped_instances[scope_id]

            if descriptor.service_type not in scope_services:
                instance = self._build_instance(descriptor, scope_id)
                scope_services[descriptor.service_type] = instance

            return scope_services[descriptor.service_type]

        # Transient scope
        else:
            return self._build_instance(descriptor, scope_id)

    def _build_instance(self, descriptor: ServiceDescriptor, scope_id: str) -> Any:
        """Build service instance with dependencies"""

        # Use factory if available
        if descriptor.factory:
            # Resolve factory dependencies
            factory_args = self._resolve_dependencies(descriptor.dependencies, scope_id)

            if asyncio.iscoroutinefunction(descriptor.factory):
                # Handle async factory (would need async context)
                raise ServiceResolutionError("Async factories not supported in sync resolution")

            return descriptor.factory(*factory_args)

        # Use constructor
        else:
            constructor_args = self._resolve_dependencies(descriptor.dependencies, scope_id)
            return descriptor.implementation_type(*constructor_args)

    def _resolve_dependencies(self, dependencies: List[Type], scope_id: str) -> List[Any]:
        """Resolve list of dependencies"""
        resolved_deps = []

        for dep_type in dependencies:
            try:
                resolved_dep = self.resolve(dep_type, scope_id)
                resolved_deps.append(resolved_dep)
            except ServiceResolutionError:
                # Try to resolve as optional dependency
                logger.warning(f"Could not resolve dependency: {dep_type.__name__}")
                resolved_deps.append(None)

        return resolved_deps

    def _extract_dependencies(self, target_type: Union[Type, Callable]) -> List[Type]:
        """Extract dependencies from constructor or factory signature"""
        dependencies = []

        try:
            if inspect.isclass(target_type):
                # Get constructor signature
                sig = inspect.signature(target_type.__init__)
                parameters = list(sig.parameters.values())[1:]  # Skip 'self'
            else:
                # Get function signature
                sig = inspect.signature(target_type)
                parameters = list(sig.parameters.values())

            for param in parameters:
                if param.annotation and param.annotation != inspect.Parameter.empty:
                    # Skip basic types and focus on class dependencies
                    if inspect.isclass(param.annotation):
                        dependencies.append(param.annotation)
                    # Handle Optional types
                    elif hasattr(param.annotation, '__origin__') and param.annotation.__origin__ is Union:
                        args = param.annotation.__args__
                        if len(args) == 2 and type(None) in args:
                            # This is Optional[Type]
                            non_none_type = next(arg for arg in args if arg != type(None))
                            if inspect.isclass(non_none_type):
                                dependencies.append(non_none_type)

        except Exception as e:
            logger.warning(f"Could not extract dependencies from {target_type}: {e}")

        return dependencies

    def dispose_scope(self, scope_id: str) -> None:
        """Dispose scoped services"""
        if scope_id in self._scoped_instances:
            scoped_services = self._scoped_instances[scope_id]

            # Call dispose methods if available
            for service_instance in scoped_services.values():
                if hasattr(service_instance, 'dispose'):
                    try:
                        service_instance.dispose()
                    except Exception as e:
                        logger.error(f"Error disposing service {type(service_instance).__name__}: {e}")

            del self._scoped_instances[scope_id]
            logger.debug(f"Disposed scope: {scope_id}")

    def get_service_info(self) -> Dict[str, Any]:
        """Get container information"""
        return {
            "registered_services": len(self._services),
            "services": {
                service.__name__: {
                    "implementation": desc.implementation_type.__name__,
                    "scope": desc.scope.value,
                    "has_factory": desc.factory is not None,
                    "dependencies": [dep.__name__ for dep in desc.dependencies],
                    "is_singleton_created": desc.singleton_instance is not None
                }
                for service, desc in self._services.items()
            },
            "active_scopes": list(self._scoped_instances.keys())
        }


class ServiceScope:
    """Service scope context manager"""

    def __init__(self, container: DIContainer, scope_id: str):
        self.container = container
        self.scope_id = scope_id

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve service in this scope"""
        return self.container.resolve(service_type, self.scope_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.dispose_scope(self.scope_id)


# Global container instance
_global_container = DIContainer()


def inject(service_type: Type[T]) -> T:
    """
    Decorator for injecting services into functions/methods.

    Args:
        service_type: Service type to inject

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject service as first argument
            service_instance = _global_container.resolve(service_type)
            return func(service_instance, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            service_instance = _global_container.resolve(service_type)
            return await func(service_instance, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator


def get_container() -> DIContainer:
    """Get global DI container"""
    return _global_container


def configure_services(configurator: Callable[[DIContainer], None]) -> None:
    """Configure services using a configuration function"""
    configurator(_global_container)


def resolve_service(service_type: Type[T]) -> T:
    """Resolve service from global container"""
    return _global_container.resolve(service_type)


# Service registration decorators
def singleton_service(service_type: Type = None):
    """Decorator to register class as singleton service"""
    def decorator(cls):
        _global_container.register_singleton(service_type or cls, cls)
        return cls
    return decorator


def scoped_service(service_type: Type = None):
    """Decorator to register class as scoped service"""
    def decorator(cls):
        _global_container.register_scoped(service_type or cls, cls)
        return cls
    return decorator


def transient_service(service_type: Type = None):
    """Decorator to register class as transient service"""
    def decorator(cls):
        _global_container.register_transient(service_type or cls, cls)
        return cls
    return decorator