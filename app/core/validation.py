# app/core/validation.py
"""
Standardized request/response validation system for all services.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, get_origin, get_args
from pydantic import BaseModel, Field, validator, ValidationError
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class ValidationResult:
    """Result of validation operation"""

    def __init__(self, is_valid: bool, errors: List[str] = None, data: Any = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data

    def add_error(self, error: str):
        """Add validation error"""
        self.is_valid = False
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "valid": self.is_valid,
            "errors": self.errors,
            "data": self.data
        }


class BaseRequestModel(BaseModel):
    """Base class for all request models"""

    class Config:
        validate_assignment = True
        extra = "forbid"  # Reject unknown fields
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class BaseResponseModel(BaseModel):
    """Base class for all response models"""

    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }


class PaginatedResponse(BaseResponseModel, Generic[T]):
    """Generic paginated response"""

    data: List[T] = []
    total: int = 0
    page: int = 1
    size: int = 10
    pages: int = 0

    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        """Calculate total pages"""
        total = values.get('total', 0)
        size = values.get('size', 10)
        return (total + size - 1) // size if size > 0 else 0


class ErrorResponse(BaseResponseModel):
    """Standard error response"""

    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None, **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            **kwargs
        )


class ValidationRequestModel(BaseRequestModel):
    """Request model for validation operations"""

    tenant_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    correlation_id: Optional[str] = None


class RequestValidator:
    """Request validation utilities"""

    @staticmethod
    def validate_model(data: Dict[str, Any], model_class: Type[T]) -> ValidationResult:
        """Validate data against Pydantic model"""
        try:
            model_instance = model_class(**data)
            return ValidationResult(
                is_valid=True,
                data=model_instance
            )
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                message = error["msg"]
                errors.append(f"{field}: {message}")

            return ValidationResult(
                is_valid=False,
                errors=errors
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"]
            )

    @staticmethod
    def validate_tenant_access(tenant_id: UUID, resource_tenant_id: UUID) -> ValidationResult:
        """Validate tenant has access to resource"""
        if tenant_id != resource_tenant_id:
            return ValidationResult(
                is_valid=False,
                errors=["Access denied: Resource belongs to different tenant"]
            )
        return ValidationResult(is_valid=True)

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """Validate required fields are present"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            return ValidationResult(
                is_valid=False,
                errors=[f"Missing required fields: {', '.join(missing_fields)}"]
            )

        return ValidationResult(is_valid=True)

    @staticmethod
    def validate_uuid_format(value: str, field_name: str = "id") -> ValidationResult:
        """Validate UUID format"""
        try:
            UUID(value)
            return ValidationResult(is_valid=True)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                errors=[f"{field_name} must be a valid UUID format"]
            )


class ResponseFormatter:
    """Response formatting utilities"""

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Operation completed successfully",
        **kwargs
    ) -> Dict[str, Any]:
        """Format success response"""
        response = BaseResponseModel(message=message, **kwargs)
        result = response.dict()
        if data is not None:
            result["data"] = data
        return result

    @staticmethod
    def error_response(
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Format error response"""
        response = ErrorResponse(
            message=message,
            error_code=error_code,
            details=details,
            **kwargs
        )
        return response.dict()

    @staticmethod
    def validation_error_response(validation_result: ValidationResult) -> Dict[str, Any]:
        """Format validation error response"""
        return ResponseFormatter.error_response(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_errors": validation_result.errors}
        )

    @staticmethod
    def paginated_response(
        items: List[Any],
        total: int,
        page: int = 1,
        size: int = 10,
        message: str = "Data retrieved successfully"
    ) -> Dict[str, Any]:
        """Format paginated response"""
        response = PaginatedResponse(
            data=items,
            total=total,
            page=page,
            size=size,
            message=message
        )
        return response.dict()


class ServiceValidator:
    """Service-level validation decorator and utilities"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.validation")

    def validate_request(
        self,
        request_model: Type[BaseRequestModel],
        tenant_validation: bool = True,
        required_role: str = None
    ):
        """Decorator for request validation"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Extract request data (assume first arg after self is request data)
                if len(args) < 2:
                    raise ValueError("Request validation requires request data as first argument")

                request_data = args[1]
                if not isinstance(request_data, dict):
                    raise ValueError("Request data must be a dictionary")

                # Validate against model
                validation_result = RequestValidator.validate_model(request_data, request_model)
                if not validation_result.is_valid:
                    return ResponseFormatter.validation_error_response(validation_result)

                # Add validated data to kwargs
                kwargs['validated_data'] = validation_result.data

                # Tenant validation
                if tenant_validation and hasattr(validation_result.data, 'tenant_id'):
                    # This would integrate with actual tenant validation logic
                    pass

                try:
                    return func(*args, **kwargs)
                except ValidationError as e:
                    self.logger.error(f"Validation error in {func.__name__}: {e}")
                    return ResponseFormatter.error_response(
                        message="Request validation failed",
                        error_code="VALIDATION_ERROR"
                    )
                except Exception as e:
                    self.logger.error(f"Unexpected error in {func.__name__}: {e}")
                    return ResponseFormatter.error_response(
                        message="Internal server error",
                        error_code="INTERNAL_ERROR"
                    )

            return wrapper
        return decorator

    def format_response(self, response_model: Type[BaseResponseModel] = None):
        """Decorator for response formatting"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)

                    # If result is already formatted, return as-is
                    if isinstance(result, dict) and 'success' in result:
                        return result

                    # Format successful response
                    if response_model and result is not None:
                        # Validate response against model
                        if isinstance(result, dict):
                            validated_response = response_model(**result)
                            return validated_response.dict()

                    return ResponseFormatter.success_response(data=result)

                except Exception as e:
                    self.logger.error(f"Error in {func.__name__}: {e}")
                    return ResponseFormatter.error_response(
                        message=str(e),
                        error_code="SERVICE_ERROR"
                    )

            return wrapper
        return decorator


# Common validation models for reuse across services

class PaginationRequest(BaseRequestModel):
    """Standard pagination request"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=10, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$", description="Sort order")


class TenantRequest(ValidationRequestModel):
    """Request requiring tenant validation"""
    tenant_id: UUID = Field(..., description="Tenant ID")


class IdRequest(BaseRequestModel):
    """Request with ID parameter"""
    id: UUID = Field(..., description="Resource ID")


class BulkRequest(BaseRequestModel):
    """Bulk operation request"""
    ids: List[UUID] = Field(..., min_items=1, max_items=100, description="List of IDs")


class DateRangeRequest(BaseRequestModel):
    """Date range filtering request"""
    start_date: Optional[datetime] = Field(default=None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(default=None, description="End date (inclusive)")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class SearchRequest(PaginationRequest):
    """Search request with pagination"""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")