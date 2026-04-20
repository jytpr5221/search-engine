from pydantic import BaseModel
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class Author(BaseModel):
    id: int | None = None
    name: str


class AuthorController:

    def __init__(self, db):
        self.db = db
    

    async def create_author(self, author: Author):
        try:
            query = "INSERT INTO authors (name) VALUES ($1) RETURNING id, name"
            result = await self.db.fetchrow(query, author.name)
            return {"id": result["id"], "name": result["name"]} if result else None
        except Exception as e:
            logger.error(f"Error creating author: {e}")
            raise HTTPException(status_code=500, detail="Error creating author")

    async def get_author(self, author_id: int):
        try:
            query = "SELECT * FROM authors WHERE id = $1"
            result = await self.db.fetchrow(query, author_id)
            if not result:
                raise HTTPException(status_code=404, detail="Author not found")
            return dict(result)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching author: {e}")
            raise HTTPException(status_code=500, detail="Error fetching author")
    
    async def get_all_authors(self, limit: int = 100, offset: int = 0):
        """Get all authors with pagination"""
        try:
            query = "SELECT * FROM authors ORDER BY id DESC LIMIT $1 OFFSET $2"
            results = await self.db.fetch(query, limit, offset)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching authors: {e}")
            raise HTTPException(status_code=500, detail="Error fetching authors")
    
    async def get_authors_by_ids(self, author_ids: list[int]):
        """Get multiple authors by their IDs"""
        try:
            if not author_ids:
                return []
            placeholders = ",".join([f"${i}" for i in range(1, len(author_ids) + 1)])
            query = f"SELECT * FROM authors WHERE id IN ({placeholders})"
            results = await self.db.fetch(query, *author_ids)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching authors by ids: {e}")
            raise HTTPException(status_code=500, detail="Error fetching authors")