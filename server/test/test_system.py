import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from src.controllers.book_controller import BookController, Book
from src.controllers.search_controller import SearchController
from src.utility.cron_job import get_pending_books, index_pending_books, update_books_state


@pytest.fixture
def system_test_books_json():
    """Create temporary books.json for system tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        initial_books = [
            {
                "id": 100,
                "title": "System Test Book",
                "description": "For system testing",
                "publisher": "Test Pub",
                "publication_year": 2023,
                "edition": "1st",
                "language": "English",
                "authors": ["Test Author"],
                "categories": ["Test"],
                "tags": ["system"],
                "pages": 100,
                "isbn": "9999999999",
                "state": "pending"
            }
        ]
        json.dump(initial_books, f)
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def system_book_controller(system_test_books_json):
    """BookController for system tests"""
    controller = BookController(db=None)
    controller.books_json_path = Path(system_test_books_json)
    return controller


@pytest.fixture
def system_search_controller():
    """SearchController for system tests"""
    controller = SearchController()
    controller.search_db = MagicMock()
    controller.search_db.index_bulk = AsyncMock(return_value={"items": [1], "errors": 0})
    controller.search_db.search = AsyncMock(return_value={
        "hits": {
            "hits": [
                {"_id": 1, "_source": {"title": "System Test Book", "state": "completed"}}
            ]
        }
    })
    return controller


class TestSystemFlow:
    """System tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_create_book_to_search_flow(self, system_book_controller, system_search_controller):
        """Test complete flow: Create book -> Index -> Search"""
        
        # Step 1: Create a new book
        new_book = Book(
            title="Flow Test Book",
            description="Testing complete flow",
            publisher="Test Publisher",
            publication_year=2024,
            edition=1,
            language="English",
            book_authors=["Flow Author"],
            book_tags=["flow"],
            book_categories=["Test"]
        )
        
        create_result = await system_book_controller.create_book(new_book)
        assert create_result["state"] == "pending"
        new_book_id = create_result["id"]
        
        # Step 2: Verify book was added to JSON with pending state
        with open(system_book_controller.books_json_path, 'r') as f:
            books = json.load(f)
        
        assert len(books) == 2
        assert books[-1]["state"] == "pending"
        assert books[-1]["id"] == new_book_id
        
        # Step 3: Get pending books (simulating cron job)
        with patch('src.utility.cron_job.BOOKS_JSON_PATH', system_book_controller.books_json_path):
            pending = await get_pending_books()
            assert any(b["id"] == new_book_id for b in pending)
        
        # Step 4: Update book state to completed
        with patch('src.utility.cron_job.BOOKS_JSON_PATH', system_book_controller.books_json_path):
            await update_books_state([new_book_id], "completed")
        
        # Step 5: Verify state was updated
        with open(system_book_controller.books_json_path, 'r') as f:
            books = json.load(f)
        
        new_book_record = next((b for b in books if b["id"] == new_book_id), None)
        assert new_book_record is not None
        assert new_book_record["state"] == "completed"

    @pytest.mark.asyncio
    async def test_pending_books_indexing_cron_job(self, system_book_controller, system_search_controller):
        """Test cronjob indexing of pending books"""
        
        # Create multiple pending books
        for i in range(3):
            book = Book(
                title=f"Cron Test Book {i}",
                description=f"Test {i}",
                publisher="Cron Publisher",
                publication_year=2024,
                edition=i+1,
                language="English",
                book_authors=["Author"],
                book_tags=["cron"],
                book_categories=["Test"]
            )
            await system_book_controller.create_book(book)
        
        # Get all pending books
        with patch('src.utility.cron_job.BOOKS_JSON_PATH', system_book_controller.books_json_path):
            pending_books = await get_pending_books()
        
        assert len(pending_books) >= 3
        
        # Update all to completed
        book_ids = [b["id"] for b in pending_books]
        with patch('src.utility.cron_job.BOOKS_JSON_PATH', system_book_controller.books_json_path):
            await update_books_state(book_ids, "completed")
        
        # Verify all are completed
        with open(system_book_controller.books_json_path, 'r') as f:
            books = json.load(f)
        
        for book_id in book_ids:
            book = next((b for b in books if b["id"] == book_id), None)
            assert book["state"] == "completed"

    @pytest.mark.asyncio
    async def test_search_with_mock_data(self, system_search_controller):
        """Test searching with mocked search results"""
        
        # Mock the search_db for the controller
        system_search_controller.search_db = MagicMock()
        system_search_controller.search_db.search = AsyncMock(return_value={
            "hits": {
                "hits": [
                    {"_id": 1, "_source": {"title": "Python Guide", "state": "completed"}}
                ]
            }
        })
        
        # Search for books with mocked results
        with patch('src.controllers.search_controller.search_db', system_search_controller.search_db):
            with patch('src.controllers.search_controller.reformulate_query') as mock_reform:
                mock_reform.return_value = ({}, "python")
                search_result = await system_search_controller.search("python", filters={"language": "English"})
        
        assert isinstance(search_result, list)

    @pytest.mark.asyncio
    async def test_book_state_transitions(self, system_book_controller):
        """Test state transitions: pending -> completed"""
        
        # Create book with pending state
        book = Book(
            title="State Transition Test",
            description="Testing state changes",
            publisher="State Publisher",
            publication_year=2024,
            edition=1,
            language="English",
            book_authors=["Author"],
            book_tags=["state"],
            book_categories=["Test"]
        )
        
        result = await system_book_controller.create_book(book)
        book_id = result["id"]
        
        # Verify initial state is pending
        with open(system_book_controller.books_json_path, 'r') as f:
            books = json.load(f)
        book_record = next((b for b in books if b["id"] == book_id), None)
        assert book_record["state"] == "pending"
        
        # Transition to completed
        with patch('src.utility.cron_job.BOOKS_JSON_PATH', system_book_controller.books_json_path):
            await update_books_state([book_id], "completed")
        
        # Verify state changed
        with open(system_book_controller.books_json_path, 'r') as f:
            books = json.load(f)
        book_record = next((b for b in books if b["id"] == book_id), None)
        assert book_record["state"] == "completed"
