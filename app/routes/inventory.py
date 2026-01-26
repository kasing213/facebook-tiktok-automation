from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.deps import get_db
from app.core.authorization import get_current_member_or_owner, require_role
from app.core.models import User, Product, StockMovement, MovementType, UserRole
from app.repositories.product import ProductRepository
from app.repositories.stock_movement import StockMovementRepository
from app.services.product_image_service import ProductImageService
import datetime as dt


router = APIRouter(prefix="/inventory", tags=["inventory"])


# Pydantic models
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: float = Field(..., ge=0)  # Supports decimal prices like 49.99
    cost_price: Optional[float] = Field(None, ge=0)
    currency: str = Field("KHR", max_length=3)
    low_stock_threshold: Optional[int] = Field(10, ge=0)
    track_stock: bool = True


class ProductCreate(ProductBase):
    current_stock: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    track_stock: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    tenant_id: UUID
    current_stock: int
    is_active: bool
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class StockAdjustmentRequest(BaseModel):
    product_id: UUID
    new_stock_level: int = Field(..., ge=0)
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    product_id: UUID
    movement_type: MovementType
    quantity: int
    reference_type: Optional[str]
    reference_id: Optional[str]
    notes: Optional[str]
    created_by: Optional[UUID]
    created_at: dt.datetime

    class Config:
        from_attributes = True


def _add_image_url(product: Product) -> dict:
    """Helper to convert product to dict with image_url computed"""
    image_service = ProductImageService()
    data = {
        "id": product.id,
        "tenant_id": product.tenant_id,
        "name": product.name,
        "sku": product.sku,
        "description": product.description,
        "unit_price": product.unit_price,
        "cost_price": product.cost_price,
        "currency": product.currency,
        "current_stock": product.current_stock,
        "low_stock_threshold": product.low_stock_threshold,
        "track_stock": product.track_stock,
        "is_active": product.is_active,
        "image_id": product.image_id,
        "image_url": image_service.get_image_url(product.image_id) if product.image_id else None,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
    return data


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    active_only: bool = Query(True, description="Filter active products only"),
    search: Optional[str] = Query(None, description="Search by name or SKU"),
    low_stock_only: bool = Query(False, description="Show only low stock products"),
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """List products for the current tenant"""
    product_repo = ProductRepository(db)

    if search:
        products = product_repo.search_products(current_user.tenant_id, search)
    elif low_stock_only:
        products = product_repo.get_low_stock_products(current_user.tenant_id)
    else:
        products = product_repo.get_by_tenant(current_user.tenant_id, active_only)

    # Add image_url to each product
    return [_add_image_url(p) for p in products]


@router.post("/products", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    product_repo = ProductRepository(db)

    # Check for duplicate SKU if provided
    if product_data.sku:
        existing = product_repo.get_by_sku(current_user.tenant_id, product_data.sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )

    try:
        product = product_repo.create_with_tenant(
            tenant_id=current_user.tenant_id,
            **product_data.model_dump()
        )
        db.commit()

        # Create initial stock movement if stock > 0
        if product_data.current_stock > 0:
            movement_repo = StockMovementRepository(db)
            movement_repo.create_movement(
                tenant_id=current_user.tenant_id,
                product_id=product.id,
                movement_type=MovementType.in_stock,
                quantity=product_data.current_stock,
                reference_type="initial",
                notes="Initial stock",
                created_by=current_user.id
            )
            db.commit()

        return _add_image_url(product)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    product_repo = ProductRepository(db)
    product = product_repo.get_by_id_and_tenant(product_id, current_user.tenant_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return _add_image_url(product)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Update product"""
    product_repo = ProductRepository(db)

    # Check for duplicate SKU if updating SKU
    if product_data.sku:
        existing = product_repo.get_by_sku(current_user.tenant_id, product_data.sku)
        if existing and existing.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )

    try:
        update_data = {k: v for k, v in product_data.model_dump().items() if v is not None}
        product = product_repo.update_by_tenant(product_id, current_user.tenant_id, **update_data)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        db.commit()
        return _add_image_url(product)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/products/{product_id}")
@require_role(UserRole.admin)  # Only owners can delete products
def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Soft delete product (Owner only)"""
    product_repo = ProductRepository(db)

    if not product_repo.soft_delete_by_tenant(product_id, current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    db.commit()
    return {"message": "Product deleted successfully"}


@router.post("/adjust-stock")
def adjust_stock(
    adjustment: StockAdjustmentRequest,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Manually adjust product stock level"""
    product_repo = ProductRepository(db)
    movement_repo = StockMovementRepository(db)

    # Verify product belongs to tenant
    product = product_repo.get_by_id_and_tenant(adjustment.product_id, current_user.tenant_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    try:
        movement = movement_repo.create_adjustment(
            tenant_id=current_user.tenant_id,
            product_id=adjustment.product_id,
            new_stock_level=adjustment.new_stock_level,
            notes=adjustment.notes,
            created_by=current_user.id
        )
        db.commit()

        return {
            "message": "Stock adjusted successfully",
            "movement_id": movement.id,
            "new_stock_level": adjustment.new_stock_level
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/movements", response_model=List[StockMovementResponse])
def list_movements(
    product_id: Optional[UUID] = Query(None, description="Filter by product"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """List stock movements for the tenant"""
    movement_repo = StockMovementRepository(db)
    movements = movement_repo.get_by_tenant(current_user.tenant_id, limit, product_id)
    return movements


@router.get("/low-stock", response_model=List[ProductResponse])
def get_low_stock_products(
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get products below their low stock threshold"""
    product_repo = ProductRepository(db)
    products = product_repo.get_low_stock_products(current_user.tenant_id)
    return [_add_image_url(p) for p in products]


@router.get("/movements/summary")
def get_movement_summary(
    start_date: Optional[dt.datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[dt.datetime] = Query(None, description="End date for summary"),
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Get movement summary by product"""
    movement_repo = StockMovementRepository(db)
    summary = movement_repo.get_movement_summary(
        current_user.tenant_id,
        start_date,
        end_date
    )

    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "total_in": row.total_in or 0,
                "total_out": row.total_out or 0,
                "total_adjustments": row.total_adjustments or 0,
                "movement_count": row.movement_count
            }
            for row in summary
        ]
    }


# ============================================================================
# Product Image Endpoints (MongoDB GridFS)
# ============================================================================

@router.post("/products/{product_id}/image")
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """
    Upload or replace product image.
    Max 10MB, supports JPEG, PNG, WebP, GIF.
    """
    product_repo = ProductRepository(db)

    # Verify product belongs to tenant
    product = product_repo.get_by_id_and_tenant(product_id, current_user.tenant_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Read and validate image
    content = await file.read()
    image_service = ProductImageService()

    validation_error = image_service.validate_image(content, file.content_type)
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )

    try:
        # Delete old image if exists
        if product.image_id:
            await image_service.delete_image(product.image_id)

        # Upload new image
        image_id, image_url = await image_service.upload_image(
            tenant_id=current_user.tenant_id,
            file_content=content,
            filename=file.filename or "product_image",
            content_type=file.content_type
        )

        # Update product with new image_id
        product_repo.update_by_tenant(product_id, current_user.tenant_id, image_id=image_id)
        db.commit()

        return {
            "product_id": str(product_id),
            "image_id": image_id,
            "image_url": image_url
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.delete("/products/{product_id}/image")
async def delete_product_image(
    product_id: UUID,
    current_user: User = Depends(get_current_member_or_owner),
    db: Session = Depends(get_db)
):
    """Delete product image"""
    product_repo = ProductRepository(db)

    # Verify product belongs to tenant
    product = product_repo.get_by_id_and_tenant(product_id, current_user.tenant_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    if not product.image_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product has no image"
        )

    try:
        # Delete from GridFS
        image_service = ProductImageService()
        await image_service.delete_image(product.image_id)

        # Clear image_id on product
        product_repo.update_by_tenant(product_id, current_user.tenant_id, image_id=None)
        db.commit()

        return {"message": "Image deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )


@router.get("/products/image/{image_id}")
async def get_product_image(image_id: str):
    """
    Serve product image from GridFS.

    This endpoint is PUBLIC (no auth required) because:
    1. <img> tags cannot send Authorization headers
    2. image_id (MongoDB ObjectId) is unguessable (24-char hex)
    3. Images are cached by browsers, so auth would break caching
    """
    image_service = ProductImageService()
    # No tenant validation - security via unguessable image_id
    result = await image_service.get_image(image_id, tenant_id=None)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    content, content_type, filename = result

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=86400"  # 1 day cache
        }
    )