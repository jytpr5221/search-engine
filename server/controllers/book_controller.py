from pydantic import BaseModel
from fastapi import HTTPException
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BookCreateRequest(BaseModel):
    title: str
    description: str
    publisher: int
    publication_year: int
    edition: str
    language: str
    authors: list[int]
    categories: list[int]
    tags: list[str]
    pages: int
    isbn: str


class BookController:

    def __init__(self, db, search_db):
        self.db = db
        self.search_db = search_db
    
    async def _validate_references(self, conn, publisher_id: int, author_ids: list[int], category_ids: list[int]):
        """Validate that all references exist in their respective tables"""
        try:
            # Check publisher
            publisher = await conn.fetchrow("SELECT id FROM publishers WHERE id = $1", publisher_id)
            if not publisher:
                raise HTTPException(status_code=400, detail=f"Publisher with id {publisher_id} not found")
            
            # Check authors
            if author_ids:
                placeholders = ",".join([f"${i}" for i in range(1, len(author_ids) + 1)])
                authors = await conn.fetch(f"SELECT id FROM authors WHERE id IN ({placeholders})", *author_ids)
                if len(authors) != len(author_ids):
                    found_ids = {a['id'] for a in authors}
                    missing_ids = set(author_ids) - found_ids
                    raise HTTPException(status_code=400, detail=f"Authors with ids {missing_ids} not found")
            
            # Check categories
            if category_ids:
                placeholders = ",".join([f"${i}" for i in range(1, len(category_ids) + 1)])
                categories = await conn.fetch(f"SELECT id FROM categories WHERE id IN ({placeholders})", *category_ids)
                if len(categories) != len(category_ids):
                    found_ids = {c['id'] for c in categories}
                    missing_ids = set(category_ids) - found_ids
                    raise HTTPException(status_code=400, detail=f"Categories with ids {missing_ids} not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating references: {e}")
            raise HTTPException(status_code=500, detail="Error validating references")

    async def create_book(self, book: BookCreateRequest):
        """Create a book with outbox pattern for eventual consistency"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    # Validate all references first
                    await self._validate_references(conn, book.publisher, book.authors, book.categories)
                    
                    # Insert book
                    book_query = """
                        INSERT INTO books 
                        (title, description, publisher, publication_year, edition, language, pages, isbn)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                    """
                    result = await conn.fetchrow(
                        book_query,
                        book.title,
                        book.description,
                        book.publisher,
                        book.publication_year,
                        book.edition,
                        book.language,
                        book.pages,
                        book.isbn
                    )
                    
                    book_id = result["id"]
                    
                    # Insert book_authors
                    if book.authors:
                        await conn.executemany(
                            "INSERT INTO book_authors (book_id, author_id) VALUES ($1, $2)",
                            [(book_id, author_id) for author_id in book.authors]
                        )
                    
                    # Insert book_categories
                    if book.categories:
                        await conn.executemany(
                            "INSERT INTO book_categories (book_id, category_id) VALUES ($1, $2)",
                            [(book_id, cat_id) for cat_id in book.categories]
                        )
                    
                    # Insert tags as array in books table (or separate table if preferred)
                    # For now, storing as JSON array in a separate column
                    if book.tags:
                        await conn.execute(
                            "UPDATE books SET tags = $1 WHERE id = $2",
                            book.tags,
                            book_id
                        )
                    
                    # Create outbox entry with pending status
                    outbox_query = """
                        INSERT INTO outbox (book_id, status, created_at)
                        VALUES ($1, $2, $3)
                        RETURNING id
                    """
                    await conn.fetchrow(
                        outbox_query,
                        book_id,
                        'pending',
                        datetime.utcnow()
                    )
                    
                    return {"id": book_id, "title": book.title, "status": "pending"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating book: {e}")
            raise HTTPException(status_code=500, detail="Error creating book")

    async def get_book(self, book_id: int):
        """Get a single book with all its relationships"""
        try:
            query = """
                SELECT b.*, 
                       array_agg(DISTINCT a.id) as author_ids,
                       array_agg(DISTINCT c.id) as category_ids
                FROM books b
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.id
                WHERE b.id = $1
                GROUP BY b.id
            """
            result = await self.db.fetchrow(query, book_id)
            if not result:
                raise HTTPException(status_code=404, detail="Book not found")
            return dict(result)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching book: {e}")
            raise HTTPException(status_code=500, detail="Error fetching book")

    async def get_all_books(self, limit: int = 100, offset: int = 0):
        """Get all books with pagination"""
        try:
            query = """
                SELECT b.*, 
                       array_agg(DISTINCT a.id) as author_ids,
                       array_agg(DISTINCT c.id) as category_ids
                FROM books b
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.id
                GROUP BY b.id
                ORDER BY b.id DESC
                LIMIT $1 OFFSET $2
            """
            results = await self.db.fetch(query, limit, offset)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            raise HTTPException(status_code=500, detail="Error fetching books")

    async def get_books_by_ids(self, book_ids: list[int]):
        """Get multiple books by their IDs"""
        try:
            if not book_ids:
                return []
            placeholders = ",".join([f"${i}" for i in range(1, len(book_ids) + 1)])
            query = f"""
                SELECT b.*, 
                       array_agg(DISTINCT a.id) as author_ids,
                       array_agg(DISTINCT c.id) as category_ids
                FROM books b
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.id
                WHERE b.id IN ({placeholders})
                GROUP BY b.id
            """
            results = await self.db.fetch(query, *book_ids)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching books by ids: {e}")
            raise HTTPException(status_code=500, detail="Error fetching books")

    async def update_book(self, book_id: int, update_data: dict):
        """Update a book (partial update) with outbox pattern for eventual consistency"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if book exists
                    existing = await conn.fetchrow("SELECT id FROM books WHERE id = $1", book_id)
                    if not existing:
                        raise HTTPException(status_code=404, detail="Book not found")
                    
                    # Build update query dynamically
                    allowed_fields = ['title', 'description', 'publisher', 'publication_year', 'edition', 'language', 'pages', 'isbn', 'tags']
                    updates = []
                    values = []
                    param_count = 1
                    
                    for field, value in update_data.items():
                        if field in allowed_fields and value is not None:
                            updates.append(f"{field} = ${param_count}")
                            values.append(value)
                            param_count += 1
                    
                    has_field_updates = bool(updates)
                    
                    # Update book fields if any were provided
                    if has_field_updates:
                        values.append(book_id)
                        update_query = f"UPDATE books SET {', '.join(updates)} WHERE id = ${param_count} RETURNING id"
                        await conn.fetchrow(update_query, *values)
                    
                    # Handle authors if provided
                    has_author_updates = False
                    if 'authors' in update_data:
                        has_author_updates = True
                        await conn.execute("DELETE FROM book_authors WHERE book_id = $1", book_id)
                        if update_data['authors']:
                            await conn.executemany(
                                "INSERT INTO book_authors (book_id, author_id) VALUES ($1, $2)",
                                [(book_id, author_id) for author_id in update_data['authors']]
                            )
                    
                    # Handle categories if provided
                    has_category_updates = False
                    if 'categories' in update_data:
                        has_category_updates = True
                        await conn.execute("DELETE FROM book_categories WHERE book_id = $1", book_id)
                        if update_data['categories']:
                            await conn.executemany(
                                "INSERT INTO book_categories (book_id, category_id) VALUES ($1, $2)",
                                [(book_id, cat_id) for cat_id in update_data['categories']]
                            )
                    
                    # Create outbox entry if any updates were made
                    if has_field_updates or has_author_updates or has_category_updates:
                        outbox_query = """
                            INSERT INTO outbox (book_id, status, created_at)
                            VALUES ($1, $2, $3)
                            RETURNING id
                        """
                        await conn.fetchrow(
                            outbox_query,
                            book_id,
                            'pending',
                            datetime.utcnow()
                        )
                        logger.info(f"Created outbox entry for updated book {book_id}")
                    
                    return await self.get_book(book_id)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating book: {e}")
            raise HTTPException(status_code=500, detail="Error updating book")

    async def delete_book(self, book_id: int):
        """Delete a book and all its relationships, also remove from Elasticsearch"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    # Check if book exists
                    existing = await conn.fetchrow("SELECT id FROM books WHERE id = $1", book_id)
                    if not existing:
                        raise HTTPException(status_code=404, detail="Book not found")
                    
                    # Delete related records
                    await conn.execute("DELETE FROM book_authors WHERE book_id = $1", book_id)
                    await conn.execute("DELETE FROM book_categories WHERE book_id = $1", book_id)
                    await conn.execute("DELETE FROM outbox WHERE book_id = $1", book_id)
                    
                    # Delete the book
                    await conn.execute("DELETE FROM books WHERE id = $1", book_id)
            
            # Remove from Elasticsearch
            try:
                await self.search_db.delete(index="books", doc_id=str(book_id))
            except Exception as e:
                logger.warning(f"Book {book_id} might not exist in Elasticsearch: {e}")
            
            return {"message": f"Book {book_id} deleted successfully"}
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting book: {e}")
            raise HTTPException(status_code=500, detail="Error deleting book")

    async def get_book_temp(self, book_id: int):
        try:
            with open('books.json', 'r') as f:
                books = json.load(f)
                for book in books:
                    if book['id'] == book_id:
                        return book
            raise HTTPException(status_code=404, detail="Book not found")
        except Exception as e:
            logger.error(f"Error fetching book from JSON: {e}")
            raise HTTPException(status_code=500, detail="Error fetching book from JSON")
    

book_controller = BookController(db=None, search_db=None)