from pydantic import BaseModel
from fastapi import HTTPException
import json
from pathlib import Path

class Book(BaseModel):
    title: str
    description: str
    id: int | None = None
    publisher: str 
    publication_year: int
    edition: int
    language: str
    book_authors: list
    book_tags: list
    book_categories: list
    isbn:str | None = None
    pages: int | None = None


class BookController:

    def __init__(self, db):
        self.db = db
        self.books_json_path = Path(__file__).parent.parent.parent / "books.json"
    
    def _get_next_id(self) -> int:
        """Get the next ID by fetching the last ID from books.json"""
        try:
            with open(self.books_json_path, 'r') as f:
                books = json.load(f)
            return books[-1]["id"] + 1 if books else 1
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading books.json: {e}")

    async def create_book(self, book: Book):
        try:
            # Get next ID
            book_id = self._get_next_id()
            
            # Create book dict with new ID and state='pending'
            book_dict = book.model_dump(exclude={"id"})
            book_dict["id"] = book_id
            book_dict["state"] = "pending"
            book_dict["authors"] = book_dict.pop("book_authors", [])
            book_dict["tags"] = book_dict.pop("book_tags", [])
            book_dict["categories"] = book_dict.pop("book_categories", [])
            
            # Read current books
            with open(self.books_json_path, 'r') as f:
                books = json.load(f)
            
            # Append new book
            books.append(book_dict)
            
            # Write back to file
            with open(self.books_json_path, 'w') as f:
                json.dump(books, f, indent=2)
            
            return {"id": book_id, "message": "Book created successfully", "state": "pending"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating book: {e}")

    async def get_book(self, book_id: int):
        try:
            with open('books.json', 'r') as f:
                books = json.load(f)
                for book in books:
                    if book['id'] == book_id:
                        return book
            raise HTTPException(status_code=404, detail="Book not found")
        except Exception as e:
            print(f"Error fetching book from JSON: {e}")
            raise HTTPException(status_code=500, detail="Error fetching book from JSON")
    

book_controller = BookController(db=None)