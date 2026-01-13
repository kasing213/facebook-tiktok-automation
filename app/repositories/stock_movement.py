from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text
from app.core.models import StockMovement, Product, MovementType
from app.repositories.base import BaseRepository
import datetime as dt


class StockMovementRepository(BaseRepository[StockMovement]):
    def __init__(self, db: Session):
        super().__init__(db, StockMovement)

    def get_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        product_id: Optional[UUID] = None
    ) -> List[StockMovement]:
        """Get stock movements for a tenant with optional product filter"""
        query = self.db.query(StockMovement).filter(StockMovement.tenant_id == tenant_id)

        if product_id:
            query = query.filter(StockMovement.product_id == product_id)

        return query.order_by(desc(StockMovement.created_at)).limit(limit).all()

    def get_by_product(self, product_id: UUID, tenant_id: UUID, limit: int = 50) -> List[StockMovement]:
        """Get stock movements for a specific product"""
        return self.db.query(StockMovement).filter(
            and_(
                StockMovement.product_id == product_id,
                StockMovement.tenant_id == tenant_id
            )
        ).order_by(desc(StockMovement.created_at)).limit(limit).all()

    def create_movement(
        self,
        tenant_id: UUID,
        product_id: UUID,
        movement_type: MovementType,
        quantity: int,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> StockMovement:
        """Create a stock movement and update product stock"""
        # Create movement record
        movement = StockMovement(
            tenant_id=tenant_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by
        )

        self.db.add(movement)
        self.db.flush()  # Get the movement ID without committing

        # Update product stock
        self._update_product_stock(product_id, tenant_id, movement_type, quantity)

        return movement

    def create_adjustment(
        self,
        tenant_id: UUID,
        product_id: UUID,
        new_stock_level: int,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> StockMovement:
        """Create a stock adjustment to set stock to exact level"""
        # Get current stock
        current_stock = self.db.query(Product.current_stock).filter(
            and_(
                Product.id == product_id,
                Product.tenant_id == tenant_id
            )
        ).scalar()

        if current_stock is None:
            raise ValueError("Product not found")

        adjustment_quantity = new_stock_level - current_stock

        return self.create_movement(
            tenant_id=tenant_id,
            product_id=product_id,
            movement_type=MovementType.adjustment,
            quantity=adjustment_quantity,
            reference_type="manual",
            notes=notes,
            created_by=created_by
        )

    def get_movement_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[dt.datetime] = None,
        end_date: Optional[dt.datetime] = None
    ) -> List[dict]:
        """Get movement summary by product for a date range"""
        query = self.db.query(
            StockMovement.product_id,
            Product.name.label('product_name'),
            Product.sku.label('product_sku'),
            func.sum(
                func.case(
                    (StockMovement.movement_type == MovementType.in_stock, StockMovement.quantity),
                    else_=0
                )
            ).label('total_in'),
            func.sum(
                func.case(
                    (StockMovement.movement_type == MovementType.out_stock, StockMovement.quantity),
                    else_=0
                )
            ).label('total_out'),
            func.sum(
                func.case(
                    (StockMovement.movement_type == MovementType.adjustment, StockMovement.quantity),
                    else_=0
                )
            ).label('total_adjustments'),
            func.count(StockMovement.id).label('movement_count')
        ).join(Product, StockMovement.product_id == Product.id).filter(
            StockMovement.tenant_id == tenant_id
        )

        if start_date:
            query = query.filter(StockMovement.created_at >= start_date)
        if end_date:
            query = query.filter(StockMovement.created_at <= end_date)

        return query.group_by(
            StockMovement.product_id,
            Product.name,
            Product.sku
        ).order_by(Product.name).all()

    def _update_product_stock(
        self,
        product_id: UUID,
        tenant_id: UUID,
        movement_type: MovementType,
        quantity: int
    ) -> None:
        """Update product stock level based on movement"""
        if movement_type == MovementType.in_stock:
            stock_change = quantity
        elif movement_type == MovementType.out_stock:
            stock_change = -quantity
        else:  # adjustment
            stock_change = quantity

        # Use raw SQL for atomic update
        self.db.execute(
            text("""
                UPDATE inventory.products
                SET current_stock = current_stock + :stock_change,
                    updated_at = NOW()
                WHERE id = :product_id AND tenant_id = :tenant_id
            """),
            {
                "stock_change": stock_change,
                "product_id": str(product_id),
                "tenant_id": str(tenant_id)
            }
        )

    def get_recent_movements_by_reference(
        self,
        tenant_id: UUID,
        reference_type: str,
        reference_id: str
    ) -> List[StockMovement]:
        """Get movements by reference (e.g., invoice movements)"""
        return self.db.query(StockMovement).filter(
            and_(
                StockMovement.tenant_id == tenant_id,
                StockMovement.reference_type == reference_type,
                StockMovement.reference_id == reference_id
            )
        ).order_by(desc(StockMovement.created_at)).all()