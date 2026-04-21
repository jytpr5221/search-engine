from fastapi import APIRouter, HTTPException, Request
from controllers.book_controller import book_controller
import json
import os

router = APIRouter()
BOOKS_FILE = "books.json"

@router.get("/{book_id}")
async def get_book(book_id: int):
    return await book_controller.get_book(book_id)

@router.post("/create-book")
async def create_book_route(request: Request):
    try:
        data = await request.json()

        # Load existing books
        if not os.path.exists(BOOKS_FILE):
            books = []
        else:
            with open(BOOKS_FILE, "r", encoding="utf-8") as f:
                books = json.load(f)

        # 🔥 DELETE CASE
        if data.get("type") == "delete":
            book_id = data.get("id")

            books = [b for b in books if b.get("id") != book_id]

            # Save back
            with open(BOOKS_FILE, "w", encoding="utf-8") as f:
                json.dump(books, f, indent=2)

            return {
                "status": "success",
                "message": f"Book {book_id} deleted"
            }

        # 🔥 ADD CASE
        else:
            # Get next ID
            if books:
                last_id = max(b.get("id", 0) for b in books)
            else:
                last_id = 0

            new_id = last_id + 1

            # Build new book object
            new_book = {
                "id": new_id,
                "title": data.get("title"),
                "description": data.get("description"),
                "publisher": data.get("publisher"),
                "publication_year": data.get("publication_year"),
                "edition": data.get("edition"),
                "language": data.get("language"),
                "authors": data.get("authors", []),
                "categories": data.get("categories", []),
                "tags": data.get("tags", []),
                "pages": data.get("pages"),
                "isbn": data.get("isbn")
            }

            books.append(new_book)

            # Save back
            with open(BOOKS_FILE, "w", encoding="utf-8") as f:
                json.dump(books, f, indent=2)

            return {
                "status": "success",
                "data": new_book
            }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }