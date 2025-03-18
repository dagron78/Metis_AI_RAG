from typing import Generic, TypeVar, Type, List, Optional, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from sqlalchemy.sql import select, delete, update

from app.db.session import Base

# Define a generic type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base repository class with common CRUD operations
    """
    
    def __init__(self, session: Session, model_class: Type[ModelType]):
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
        """
        Get a record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Record if found, None otherwise
        """
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, 
                skip: int = 0, 
                limit: int = 100, 
                order_by: str = None, 
                order_direction: str = "asc") -> List[ModelType]:
        """
        Get all records with pagination and ordering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column to order by
            order_direction: Order direction (asc or desc)
            
        Returns:
            List of records
        """
        query = self.session.query(self.model_class)
        
        if order_by:
            column = getattr(self.model_class, order_by, None)
            if column:
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Create a new record
        
        Args:
            obj_in: Dictionary with record data
            
        Returns:
            Created record
        """
        db_obj = self.model_class(**obj_in)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj
    
    def update(self, id: Union[int, str, UUID], obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update a record
        
        Args:
            id: Record ID
            obj_in: Dictionary with record data
            
        Returns:
            Updated record if found, None otherwise
        """
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            
            self.session.commit()
            self.session.refresh(db_obj)
            return db_obj
        return None
    
    def delete(self, id: Union[int, str, UUID]) -> bool:
        """
        Delete a record
        
        Args:
            id: Record ID
            
        Returns:
            True if record was deleted, False otherwise
        """
        db_obj = self.get_by_id(id)
        if db_obj:
            self.session.delete(db_obj)
            self.session.commit()
            return True
        return False
    
    def count(self) -> int:
        """
        Count all records
        
        Returns:
            Number of records
        """
        return self.session.query(self.model_class).count()
    
    def exists(self, id: Union[int, str, UUID]) -> bool:
        """
        Check if a record exists
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        return self.session.query(
            self.session.query(self.model_class).filter(self.model_class.id == id).exists()
        ).scalar()