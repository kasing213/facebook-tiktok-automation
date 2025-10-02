# app/repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.core.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T], ABC):
    """Base repository pattern for database operations"""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a single record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all records with optional pagination"""
        query = self.db.query(self.model)
        if limit:
            query = query.offset(offset).limit(limit)
        return query.all()

    def create(self, **kwargs) -> T:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.db.flush()
            self.db.refresh(instance)
        return instance

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID"""
        instance = self.get_by_id(id)
        if instance:
            self.db.delete(instance)
            self.db.flush()
            return True
        return False

    def exists(self, **filters) -> bool:
        """Check if a record exists with given filters"""
        return self.db.query(self.model).filter_by(**filters).first() is not None

    def count(self, **filters) -> int:
        """Count records with optional filters"""
        query = self.db.query(self.model)
        if filters:
            query = query.filter_by(**filters)
        return query.count()

    def find_by(self, **filters) -> List[T]:
        """Find records by filters"""
        return self.db.query(self.model).filter_by(**filters).all()

    def find_one_by(self, **filters) -> Optional[T]:
        """Find a single record by filters"""
        return self.db.query(self.model).filter_by(**filters).first()