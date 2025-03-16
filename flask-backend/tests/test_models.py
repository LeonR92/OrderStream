import pytest
from flask import Flask
from models import db, Item

@pytest.fixture(scope="function")
def test_app():
    """Creates a Flask test app with an in-memory SQLite database."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app  
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope="function")
def sample_item(test_app):
    """Creates and commits a sample item in the database."""
    with test_app.app_context():
        item = Item.create({
            "name": "Test Item",
            "description": "A sample item for testing",
            "price": 19.99,
            "quantity": 5
        })
        db.session.refresh(item)  
        return item.id  

def test_create_item(test_app):
    """Test creating an item."""
    with test_app.app_context():
        data = {
            "name": "New Item",
            "description": "This is a new item",
            "price": 9.99,
            "quantity": 3
        }
        item = Item.create(data)
        assert item is not None
        assert item.name == "New Item"
        assert item.description == "This is a new item"
        assert float(item.price) == 9.99  
        assert item.quantity == 3

def test_get_all_items(test_app, sample_item):
    """Test fetching all items."""
    with test_app.app_context():
        items = Item.get_all()
        assert len(items) == 1
        assert items[0].name == "Test Item"

def test_get_by_id(test_app, sample_item):
    """Test fetching an item by ID (avoiding detached instance)."""
    with test_app.app_context():
        item = Item.get_by_id(sample_item)  
        assert item is not None
        assert item.name == "Test Item"

def test_update_item(test_app, sample_item):
    """Test updating an existing item."""
    with test_app.app_context():
        updated_data = {"name": "Updated Item", "price": 25.99}
        updated_item = Item.update(sample_item, updated_data)

        assert updated_item is not None
        assert updated_item.name == "Updated Item"
        assert float(updated_item.price) == 25.99  

def test_delete_item(test_app, sample_item):
    """Test deleting an item."""
    with test_app.app_context():
        success = Item.delete(sample_item)
        assert success is True

        item = Item.get_by_id(sample_item)
        assert item is None  
