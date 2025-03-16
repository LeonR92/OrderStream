from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from typing import Optional, List, Dict

# Initialize database
db = SQLAlchemy()

class Item(db.Model):
    """Item model representing products in the database."""
    
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Converts model instance to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_all() -> List["Item"]:
        """Fetch all items."""
        return Item.query.all()

    @staticmethod
    def get_by_id(item_id: int) -> Optional["Item"]:
        """Fetch an item by its ID."""
        return Item.query.get(item_id)

    @staticmethod
    def create(data: Dict) -> Optional["Item"]:
        """Create a new item and return it."""
        try:
            item = Item(
                name=data['name'],
                description=data.get('description', ''),
                price=data['price'],
                quantity=data['quantity']
            )
            db.session.add(item)
            db.session.commit()
            return item
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def update(item_id: int, data: Dict) -> Optional["Item"]:
        """Update an existing item and return it."""
        item = Item.query.get(item_id)
        if not item:
            return None

        try:
            if 'name' in data:
                item.name = data['name']
            if 'description' in data:
                item.description = data['description']
            if 'price' in data:
                item.price = data['price']
            if 'quantity' in data:
                item.quantity = data['quantity']

            db.session.commit()
            return item
        except Exception:
            db.session.rollback()
            return None

    @staticmethod
    def delete(item_id: int) -> bool:
        """Delete an item by ID."""
        item = Item.query.get(item_id)
        if not item:
            return False

        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
