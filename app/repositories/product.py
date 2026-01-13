from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from app.core.models import Product, StockMovement, MovementType
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db, Product)

    def get_by_tenant(self, tenant_id: UUID, active_only: bool = True) -> List[Product]:
        """Get all products for a tenant"""
        query = self.db.query(Product).filter(Product.tenant_id == tenant_id)
        if active_only:
            query = query.filter(Product.is_active == True)
        return query.order_by(asc(Product.name)).all()

    def get_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Product]:
        """Get product by SKU within tenant"""
        return self.db.query(Product).filter(
            and_(
                Product.tenant_id == tenant_id,
                Product.sku == sku,
                Product.is_active == True
            )
        ).first()

    def get_low_stock_products(self, tenant_id: UUID) -> List[Product]:
        """Get products below their low stock threshold"""
        return self.db.query(Product).filter(
            and_(
                Product.tenant_id == tenant_id,
                Product.is_active == True,
                Product.track_stock == True,
                Product.current_stock <= Product.low_stock_threshold
            )
        ).order_by(asc(Product.current_stock)).all()

    def update_stock(self, product_id: UUID, tenant_id: UUID, new_stock: int) -> bool:
        """Update product stock level"""
        updated = self.db.query(Product).filter(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
            )
        ).update({"current_stock": new_stock})
        return updated > 0

    def search_products(self, tenant_id: UUID, search_term: str, limit: int = 50) -> List[Product]:
        """Search products by name or SKU"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Product).filter(
            and_(
                Product.tenant_id == tenant_id,
                Product.is_active == True,
                (Product.name.ilike(search_pattern) | Product.sku.ilike(search_pattern))
            )
        ).order_by(asc(Product.name)).limit(limit).all()

    def create_with_tenant(self, tenant_id: UUID, **kwargs) -> Product:
        """Create product ensuring tenant isolation"""
        kwargs['tenant_id'] = tenant_id
        return self.create(**kwargs)

    def get_by_id_and_tenant(self, product_id: UUID, tenant_id: UUID) -> Optional[Product]:
        """Get product by ID ensuring it belongs to the tenant"""
        return self.db.query(Product).filter(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
            )
        ).first()

    def update_by_tenant(self, product_id: UUID, tenant_id: UUID, **kwargs) -> Optional[Product]:
        """Update product ensuring tenant isolation"""
        product = self.get_by_id_and_tenant(product_id, tenant_id)
        if not product:
            return None

        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)

        self.db.commit()
        self.db.refresh(product)
        return product

    def soft_delete_by_tenant(self, product_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete product by setting is_active=False"""
        updated = self.db.query(Product).filter(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
            )
        ).update({"is_active": False})
        return updated > 0