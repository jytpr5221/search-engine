from fastapi import HTTPException
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OutboxController:
    """Handles processing of outbox entries for eventual consistency"""
    
    def __init__(self, db, search_db):
        self.db = db
        self.search_db = search_db
    
    async def process_pending_outbox(self):
        """Process all pending outbox entries and sync to Elasticsearch"""
        try:
            async with self.db.pool.acquire() as conn:
                async with conn.transaction():
                    # Fetch all pending outbox entries
                    pending_query = """
                        SELECT id, book_id FROM outbox 
                        WHERE status = 'pending'
                        LIMIT 100
                    """
                    pending_entries = await conn.fetch(pending_query)
                    
                    if not pending_entries:
                        logger.info("No pending outbox entries to process")
                        return {"processed": 0}
                    
                    # Get book IDs from pending entries
                    book_ids = [entry['book_id'] for entry in pending_entries]
                    
                    # Fetch full book data with relationships
                    books_data = await self._get_books_for_indexing(conn, book_ids)
                    
                    if books_data:
                        # Prepare documents for bulk indexing
                        documents = self._prepare_documents_for_indexing(books_data)
                        
                        # Bulk index to Elasticsearch
                        result = await self.search_db.index_bulk(index="books", documents=documents)
                        
                        # Update outbox status to completed for successfully indexed books
                        successful_ids = [str(doc.id) for doc in documents]
                        if successful_ids:
                            placeholders = ",".join([f"${i}" for i in range(1, len(successful_ids) + 1)])
                            update_query = f"""
                                UPDATE outbox 
                                SET status = 'completed' 
                                WHERE book_id IN ({placeholders})
                            """
                            await conn.execute(update_query, *[int(bid) for bid in successful_ids])
                            logger.info(f"Processed {len(successful_ids)} outbox entries")
                            return {"processed": len(successful_ids)}
                    
                    return {"processed": 0}
        
        except Exception as e:
            logger.error(f"Error processing outbox entries: {e}")
            return {"processed": 0, "error": str(e)}
    
    async def _get_books_for_indexing(self, conn, book_ids):
        """Fetch books with all their relationships for indexing"""
        try:
            if not book_ids:
                return []
            
            placeholders = ",".join([f"${i}" for i in range(1, len(book_ids) + 1)])
            query = f"""
                SELECT 
                    b.id,
                    b.title,
                    b.description,
                    b.publisher,
                    p.name as publisher_name,
                    b.publication_year,
                    b.edition,
                    b.language,
                    b.pages,
                    b.isbn,
                    b.tags,
                    array_agg(DISTINCT a.id) FILTER (WHERE a.id IS NOT NULL) as author_ids,
                    array_agg(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL) as author_names,
                    array_agg(DISTINCT c.id) FILTER (WHERE c.id IS NOT NULL) as category_ids,
                    array_agg(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL) as category_names
                FROM books b
                LEFT JOIN publishers p ON b.publisher = p.id
                LEFT JOIN book_authors ba ON b.id = ba.book_id
                LEFT JOIN authors a ON ba.author_id = a.id
                LEFT JOIN book_categories bc ON b.id = bc.book_id
                LEFT JOIN categories c ON bc.category_id = c.id
                WHERE b.id IN ({placeholders})
                GROUP BY b.id, b.title, b.description, b.publisher, p.name, b.publication_year, 
                         b.edition, b.language, b.pages, b.isbn, b.tags
                ORDER BY b.id
            """
            results = await conn.fetch(query, *book_ids)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching books for indexing: {e}")
            raise
    
    def _prepare_documents_for_indexing(self, books_data):
        """Convert database records to Elasticsearch document format"""
        from pydantic import BaseModel
        
        class ESBook(BaseModel):
            id: int
            title: str
            description: str
            publisher: int
            publisher_name: str
            publication_year: int
            edition: str
            language: str
            pages: int
            isbn: str
            tags: list
            author_ids: list
            author_names: list
            category_ids: list
            category_names: list
        
        documents = []
        for book in books_data:
            doc = ESBook(
                id=book['id'],
                title=book['title'],
                description=book['description'],
                publisher=book['publisher'],
                publisher_name=book['publisher_name'] or '',
                publication_year=book['publication_year'],
                edition=book['edition'],
                language=book['language'],
                pages=book['pages'],
                isbn=book['isbn'],
                tags=book['tags'] or [],
                author_ids=book['author_ids'] or [],
                author_names=book['author_names'] or [],
                category_ids=book['category_ids'] or [],
                category_names=book['category_names'] or []
            )
            documents.append(doc)
        
        return documents
    
    async def get_outbox_status(self, book_id: int = None):
        """Get status of outbox entries"""
        try:
            if book_id:
                query = "SELECT id, book_id, status, created_at FROM outbox WHERE book_id = $1"
                result = await self.db.fetchrow(query, book_id)
                return dict(result) if result else None
            else:
                query = "SELECT id, book_id, status, created_at FROM outbox ORDER BY created_at DESC LIMIT 100"
                results = await self.db.fetch(query)
                return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching outbox status: {e}")
            raise HTTPException(status_code=500, detail="Error fetching outbox status")


outbox_controller = OutboxController(db=None, search_db=None)
