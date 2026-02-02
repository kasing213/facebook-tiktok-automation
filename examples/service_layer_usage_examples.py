# examples/service_layer_usage_examples.py
"""
Comprehensive examples showing how to use the enhanced service layer.
Demonstrates all patterns: base service, validation, caching, circuit breaker,
health monitoring, task queue, and dependency injection.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.services.base_service import BaseService, service_method
from app.services.validation_schemas import (
    CreateProductRequest, ProductInfo, CreateProductResponse,
    UpdateStockRequest, UpdateStockResponse
)
from app.services.cache_service import cached_method, ServiceCache
from app.services.circuit_breaker import circuit_breaker, get_service_circuit_breaker
from app.services.task_queue import background_task, TaskPriority
from app.core.dependency_injection import scoped_service, inject, DIContainer
from app.core.exceptions import ServiceError, ValidationError


# Example: Complete Inventory Service Implementation
@scoped_service()
class ExampleInventoryService(BaseService):
    """
    Complete example inventory service demonstrating all patterns.

    Features demonstrated:
    - Request/response validation
    - Caching with Redis fallback
    - Circuit breaker for external calls
    - Background task processing
    - Comprehensive metrics and health checks
    - Proper error handling and logging
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self.circuit_breaker = get_service_circuit_breaker('inventory_service')
        self.cache = ServiceCache('InventoryService')

    def _service_specific_health_checks(self) -> Dict[str, Any]:
        """Service-specific health checks"""
        return {
            "cache_stats": self.cache.get_cache_stats(),
            "circuit_breaker": self.circuit_breaker.get_state_info(),
            "database_connected": self.db is not None
        }

    @service_method(retry_count=3, track_metrics=True)
    def create_product(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new product with full validation and caching.

        Example usage:
        >>> service = ExampleInventoryService(db)
        >>> result = service.create_product({
        ...     "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "name": "Premium Coffee Beans",
        ...     "sku": "COFFEE-001",
        ...     "price": 25.99,
        ...     "stock_quantity": 100,
        ...     "description": "High-quality arabica coffee beans",
        ...     "category": "Beverages",
        ...     "low_stock_threshold": 10
        ... })
        """
        # 1. Validate request using standardized patterns
        validation_result = self.validate_request(request_data, CreateProductRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            with self.transaction():
                # 2. Business logic validation
                existing_product = self._check_sku_exists(request.tenant_id, request.sku)
                if existing_product:
                    return self.format_error_response(
                        "Product with this SKU already exists",
                        "DUPLICATE_SKU",
                        {"existing_product_id": str(existing_product["id"])}
                    )

                # 3. Create product record
                product_data = self._create_product_record(request)

                # 4. Queue background tasks
                self._queue_product_tasks(product_data)

                # 5. Clear relevant caches
                await self.cache.clear_service_cache()

                # 6. Format successful response
                response_data = CreateProductResponse(
                    product=ProductInfo(**product_data)
                )

                self.log_service_action("product_created", {
                    "product_id": str(product_data["id"]),
                    "tenant_id": str(request.tenant_id),
                    "sku": request.sku
                })

                return self.format_success_response(
                    response_data.dict(),
                    "Product created successfully"
                )

        except Exception as e:
            self.logger.error(f"Failed to create product: {e}")
            return self.format_error_response(
                "Failed to create product",
                "PRODUCT_CREATION_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    @cached_method(ttl=300, skip_args=['force_refresh'])  # Cache for 5 minutes
    async def get_product_by_id(
        self,
        tenant_id: UUID,
        product_id: UUID,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get product by ID with caching.

        Example usage:
        >>> result = await service.get_product_by_id(tenant_id, product_id)
        """
        try:
            # Simulate database query
            product_data = self._fetch_product_from_db(tenant_id, product_id)

            if not product_data:
                return self.format_error_response(
                    "Product not found",
                    "PRODUCT_NOT_FOUND"
                )

            # External API call with circuit breaker
            enriched_data = await self._enrich_product_data_with_circuit_breaker(product_data)

            response = ProductInfo(**enriched_data)

            return self.format_success_response(
                response.dict(),
                "Product retrieved successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to get product {product_id}: {e}")
            return self.format_error_response(
                "Failed to retrieve product",
                "PRODUCT_RETRIEVAL_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    def update_stock(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update product stock with audit trail.

        Example usage:
        >>> result = service.update_stock({
        ...     "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "product_id": "456e7890-e89b-12d3-a456-426614174000",
        ...     "quantity_change": -5,
        ...     "reason": "Sale to customer",
        ...     "reference_type": "invoice",
        ...     "reference_id": "789e0123-e89b-12d3-a456-426614174000"
        ... })
        """
        # Validate request
        validation_result = self.validate_request(request_data, UpdateStockRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            with self.transaction():
                # Get current product
                product = self._fetch_product_from_db(request.tenant_id, request.product_id)
                if not product:
                    return self.format_error_response(
                        "Product not found",
                        "PRODUCT_NOT_FOUND"
                    )

                # Validate tenant access
                access_result = self.validate_tenant_resource_access(
                    request.tenant_id,
                    UUID(product["tenant_id"])
                )
                if not access_result.is_valid:
                    return self.format_validation_error_response(access_result)

                # Check if stock would go negative
                current_stock = product["stock_quantity"]
                new_stock = current_stock + request.quantity_change

                if new_stock < 0:
                    return self.format_error_response(
                        "Insufficient stock",
                        "INSUFFICIENT_STOCK",
                        {
                            "current_stock": current_stock,
                            "requested_change": request.quantity_change,
                            "would_result_in": new_stock
                        }
                    )

                # Create stock movement record
                movement_data = self._create_stock_movement(
                    product_id=request.product_id,
                    quantity_change=request.quantity_change,
                    quantity_before=current_stock,
                    quantity_after=new_stock,
                    reason=request.reason,
                    reference_type=request.reference_type,
                    reference_id=request.reference_id
                )

                # Update product stock
                self._update_product_stock(request.product_id, new_stock)

                # Queue background tasks for low stock alerts
                if self._is_low_stock(product, new_stock):
                    self._queue_low_stock_alert(product, new_stock)

                # Invalidate caches
                await self.cache.delete(f"product:{request.product_id}")

                # Format response
                response_data = UpdateStockResponse(
                    movement=movement_data,
                    current_stock=new_stock,
                    is_low_stock=self._is_low_stock(product, new_stock)
                )

                self.log_service_action("stock_updated", {
                    "product_id": str(request.product_id),
                    "quantity_change": request.quantity_change,
                    "new_stock": new_stock
                })

                return self.format_success_response(
                    response_data.dict(),
                    "Stock updated successfully"
                )

        except Exception as e:
            self.logger.error(f"Failed to update stock: {e}")
            return self.format_error_response(
                "Failed to update stock",
                "STOCK_UPDATE_ERROR",
                {"error": str(e)}
            )

    @circuit_breaker(
        name="product_enrichment",
        failure_threshold=3,
        success_threshold=2,
        timeout_duration=30
    )
    async def _enrich_product_data_with_circuit_breaker(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich product data with external API call protected by circuit breaker.

        This demonstrates how to use circuit breaker for external service calls.
        """
        # Simulate external API call
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            # This would be a real external API call
            # response = await client.get(f"https://api.example.com/products/{product_data['sku']}")
            # enrichment_data = response.json()

            # Simulated enrichment
            enrichment_data = {
                "market_price": product_data.get("price", 0) * 1.1,
                "competitor_count": 5,
                "category_rank": 3
            }

        # Merge enrichment data
        enriched_data = {**product_data, **enrichment_data}
        return enriched_data

    @background_task(priority=TaskPriority.LOW, max_retries=3)
    async def _queue_product_tasks(self, product_data: Dict[str, Any]) -> None:
        """
        Queue background tasks for product creation.

        This demonstrates background task processing.
        """
        # Tasks that can be processed asynchronously
        tasks = [
            self._send_product_created_notification(product_data),
            self._update_product_search_index(product_data),
            self._generate_product_analytics(product_data)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    @background_task(priority=TaskPriority.HIGH, max_retries=2)
    async def _queue_low_stock_alert(self, product: Dict[str, Any], current_stock: int) -> None:
        """
        Queue high-priority low stock alert.
        """
        alert_data = {
            "product_id": product["id"],
            "product_name": product["name"],
            "sku": product["sku"],
            "current_stock": current_stock,
            "threshold": product["low_stock_threshold"],
            "tenant_id": product["tenant_id"]
        }

        # Send alert via multiple channels
        await asyncio.gather(
            self._send_email_alert(alert_data),
            self._send_telegram_alert(alert_data),
            return_exceptions=True
        )

    # Helper methods (implementation details)
    def _check_sku_exists(self, tenant_id: UUID, sku: str) -> Optional[Dict[str, Any]]:
        """Check if SKU already exists for tenant"""
        # Database query implementation
        return None

    def _create_product_record(self, request: CreateProductRequest) -> Dict[str, Any]:
        """Create product record in database"""
        product_id = uuid4()
        return {
            "id": product_id,
            "tenant_id": request.tenant_id,
            "name": request.name,
            "sku": request.sku,
            "price": request.price,
            "stock_quantity": request.stock_quantity,
            "description": request.description,
            "category": request.category,
            "unit": request.unit or "piece",
            "low_stock_threshold": request.low_stock_threshold,
            "is_active": request.is_active,
            "is_low_stock": request.stock_quantity <= request.low_stock_threshold,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    def _fetch_product_from_db(self, tenant_id: UUID, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch product from database"""
        # Database query implementation
        return {
            "id": product_id,
            "tenant_id": str(tenant_id),
            "name": "Sample Product",
            "sku": "SAMPLE-001",
            "price": 25.99,
            "stock_quantity": 100,
            "description": "Sample product description",
            "category": "Sample Category",
            "unit": "piece",
            "low_stock_threshold": 10,
            "is_active": True,
            "is_low_stock": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    def _create_stock_movement(self, **kwargs) -> Dict[str, Any]:
        """Create stock movement record"""
        return {
            "id": uuid4(),
            "created_at": datetime.utcnow(),
            **kwargs
        }

    def _update_product_stock(self, product_id: UUID, new_stock: int) -> None:
        """Update product stock in database"""
        pass

    def _is_low_stock(self, product: Dict[str, Any], current_stock: int) -> bool:
        """Check if product is low on stock"""
        return current_stock <= product["low_stock_threshold"]

    async def _send_product_created_notification(self, product_data: Dict[str, Any]) -> None:
        """Send product created notification"""
        self.logger.info(f"Sending notification for product {product_data['id']}")

    async def _update_product_search_index(self, product_data: Dict[str, Any]) -> None:
        """Update search index with new product"""
        self.logger.info(f"Updating search index for product {product_data['id']}")

    async def _generate_product_analytics(self, product_data: Dict[str, Any]) -> None:
        """Generate analytics for new product"""
        self.logger.info(f"Generating analytics for product {product_data['id']}")

    async def _send_email_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send low stock email alert"""
        self.logger.info(f"Sending email alert for product {alert_data['product_id']}")

    async def _send_telegram_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send low stock Telegram alert"""
        self.logger.info(f"Sending Telegram alert for product {alert_data['product_id']}")


# Example: Using dependency injection in FastAPI routes
def example_fastapi_integration():
    """
    Example of how to integrate with FastAPI using dependency injection.
    """
    from fastapi import FastAPI, Depends, HTTPException
    from app.core.service_configuration import get_inventory_service

    app = FastAPI()

    @app.post("/api/products")
    async def create_product(
        product_data: Dict[str, Any],
        inventory_service: ExampleInventoryService = Depends(get_inventory_service)
    ):
        """Create new product endpoint"""
        result = inventory_service.create_product(product_data)

        if not result.get("success", False):
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Failed to create product")
            )

        return result

    @app.get("/api/products/{product_id}")
    async def get_product(
        product_id: str,
        tenant_id: str,
        inventory_service: ExampleInventoryService = Depends(get_inventory_service)
    ):
        """Get product by ID endpoint"""
        result = await inventory_service.get_product_by_id(
            UUID(tenant_id),
            UUID(product_id)
        )

        if not result.get("success", False):
            raise HTTPException(
                status_code=404,
                detail=result.get("message", "Product not found")
            )

        return result


# Example: Manual service usage without DI
async def example_manual_service_usage():
    """
    Example of manual service usage for testing or standalone operations.
    """
    from app.core.db import get_db_session_with_retry

    # Create service instance
    with get_db_session_with_retry() as db:
        service = ExampleInventoryService(db)

        # Create product
        product_request = {
            "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Premium Coffee Beans",
            "sku": "COFFEE-001",
            "price": 25.99,
            "stock_quantity": 100,
            "description": "High-quality arabica coffee beans",
            "category": "Beverages",
            "low_stock_threshold": 10
        }

        result = service.create_product(product_request)
        print(f"Create product result: {result}")

        # Get product (cached)
        if result.get("success") and result.get("data"):
            product_id = result["data"]["product"]["id"]
            tenant_id = UUID(product_request["tenant_id"])

            get_result = await service.get_product_by_id(tenant_id, UUID(product_id))
            print(f"Get product result: {get_result}")

        # Check service health
        health = service.get_health_status()
        print(f"Service health: {health}")

        # Check metrics
        metrics = service.get_metrics()
        print(f"Service metrics: {metrics}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_manual_service_usage())