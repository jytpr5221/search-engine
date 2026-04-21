from pydantic import BaseModel
from fastapi import HTTPException
import json

class Book(BaseModel):
    title: str
    description: str
    id: int | None = None
    publisher: int 
    publication_year: int
    edition: int
    language: str
    book_authors: list
    book_tags: list
    book_categories: list


class BookController:

    def __init__(self, db):
        self.db = db
    

    async def create_book(self, book: Book):
        query = """
            INSERT INTO books 
            (title, description, publisher, publication_year, edition, language)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, title
        """

        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    result = await conn.fetchrow(
                        query,
                        book.title,
                        book.description,
                        book.publisher,
                        book.publication_year,
                        book.edition,
                        book.language
                    )

                    book_id = result["id"]

                    if book.book_authors:
                        await conn.executemany(
                            "INSERT INTO book_authors (book_id, author_id) VALUES ($1, $2)",
                            [(book_id, author_id) for author_id in book.book_authors]
                        )

                    if book.book_tags:
                        await conn.executemany(
                            "INSERT INTO book_tags (book_id, tag_id) VALUES ($1, $2)",
                            [(book_id, tag_id) for tag_id in book.book_tags]
                        )

                    if book.book_categories:
                        await conn.executemany(
                            "INSERT INTO book_categories (book_id, category_id) VALUES ($1, $2)",
                            [(book_id, cat_id) for cat_id in book.book_categories]
                        )

                    return {"id": book_id, "title": result["title"]}

                except Exception as e:
                    print(f"Error creating book: {e}")
                    raise HTTPException(status_code=500, detail="Error creating book")
                

    async def get_book(self, book_id: int):

        print(book_id)
        try:
            query = "SELECT * FROM books WHERE id = $1"
            result = await self.db.query(query, book_id)
            return result[0] if result else {}
        except Exception as e:
            print(f"Error fetching book: {e}")
            raise HTTPException(status_code=500, detail="Error fetching book")

    async def get_book_temp(self, book_id: int):
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