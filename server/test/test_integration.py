import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app import app
from src.controllers.book_controller import Book
import json
from pathlib import Path
import tempfile


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def temp_books_json():
    """Create temporary books.json for integration tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        initial_books = [
            {
                "id": 1,
                "title": "Integration Test Book",
                "description": "For testing",
                "publisher": "Test Pub",
                "publication_year": 2023,
                "edition": "1st",
                "language": "English",
                "authors": ["Test Author"],
                "categories": ["Test"],
                "tags": ["integration"],
                "pages": 100,
                "isbn": "1234567890",
                "state": "completed"
            }
        ]
        json.dump(initial_books, f)
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()


class TestAPIIntegration:
    """Integration tests for API endpoints"""

    @pytest.mark.asyncio
    async def test_create_book_endpoint(self, client):
        """Test POST /api/book/create endpoint"""
        book_data = {
            "title": "Integration Test Book",
            "description": "Test Description",
            "publisher": "Integration Publisher",
            "publication_year": 2024,
            "edition": 1,
            "language": "English",
            "book_authors": ["Author 1"],
            "book_tags": ["tag1"],
            "book_categories": ["Category"]
        }
        
        with patch('src.routes.book_routes.book_controller.create_book') as mock_create:
            mock_create.return_value = {"id": 2, "message": "Book created successfully", "state": "pending"}
            
            response = client.post("/api/book/create", json=book_data)
            
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_get_book_endpoint(self, client):
        """Test GET /api/book/{book_id} endpoint"""
        with patch('src.routes.book_routes.book_controller.get_book') as mock_get:
            mock_get.return_value = {
                "id": 1,
                "title": "Test Book",
                "state": "completed"
            }
            
            response = client.get("/api/book/1")
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_endpoint(self, client):
        """Test POST /api/search endpoint"""
        search_data = {
            "query": "python",
            "filters": {
                "publisher": None,
                "category": None,
                "language": "English"
            }
        }
        
        with patch('src.routes.search_routes.search_controller.search') as mock_search:
            mock_search.return_value = [
                {"_id": "1", "_source": {"id": 1, "title": "Python Book", "authors": [], "publisher": "Test", "edition": 1, "publication_year": 2020}}
            ]
            
            response = client.post("/api/search/", json=search_data)
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auto_complete_endpoint(self, client):
        """Test POST /api/search/auto-complete endpoint"""
        search_data = {
            "query": "python",
            "filters": None
        }
        
        with patch('src.routes.search_routes.search_controller.auto_complete') as mock_ac:
            mock_ac.return_value = [
                {"_id": "1", "_source": {"id": 1, "title": "Python Book", "authors": [], "publisher": "Test", "edition": 1, "publication_year": 2020}}
            ]
            
            response = client.post("/api/search/auto-complete", json=search_data)
            
            assert response.status_code == 200

    def test_root_endpoint(self, client):
        """Test GET / endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "message" in response.json()
