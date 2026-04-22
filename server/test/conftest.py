import pytest
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path so src module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import SearchController - need to mock the db imports
with patch.dict('sys.modules', {
    'configs': MagicMock(),
    'configs.db_config': MagicMock(),
    'utility': MagicMock(),
    'utility.reform_queries': MagicMock()
}):
    from src.controllers.book_controller import BookController
    from src.controllers.search_controller import SearchController


@pytest.fixture
def temp_books_json():
    """Create a temporary books.json for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        initial_books = [
            {
                "id": 1,
                "title": "Test Book",
                "description": "Test Description",
                "publisher": "Test Publisher",
                "publication_year": 2023,
                "edition": "1st",
                "language": "English",
                "authors": ["Test Author"],
                "categories": ["Fiction"],
                "tags": ["test"],
                "pages": 100,
                "isbn": "1234567890",
                "state": "completed"
            }
        ]
        json.dump(initial_books, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def book_controller(temp_books_json, monkeypatch):
    """Create BookController with mocked file path"""
    controller = BookController(db=None)
    controller.books_json_path = Path(temp_books_json)
    return controller


@pytest.fixture
def search_controller():
    """Create SearchController with mocked database"""
    controller = SearchController()
    controller.search_db = MagicMock()
    return controller


@pytest.fixture
def mock_search_db():
    """Mock search database"""
    mock_db = AsyncMock()
    mock_db.client = AsyncMock()
    mock_db.index_bulk = AsyncMock(return_value={"items": [], "errors": 0})
    mock_db.search = AsyncMock(return_value={"hits": {"hits": []}})
    return mock_db
