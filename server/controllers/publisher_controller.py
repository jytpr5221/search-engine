from pydantic import BaseModel
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class Publisher(BaseModel):
    id: int | None = None
    name: str

class PublisherController:
    
    def __init__(self, db):
        self.db = db
    

    async def create_publisher(self, publisher: Publisher):
        try:
            query = "INSERT INTO publishers (name) VALUES ($1) RETURNING id, name"
            result = await self.db.fetchrow(query, publisher.name)
            return {"id": result["id"], "name": result["name"]} if result else None
        except Exception as e:
            logger.error(f"Error creating publisher: {e}")
            raise HTTPException(status_code=500, detail="Error creating publisher")

    async def get_publisher(self, publisher_id: int):
        try:
            query = "SELECT * FROM publishers WHERE id = $1"
            result = await self.db.fetchrow(query, publisher_id)
            if not result:
                raise HTTPException(status_code=404, detail="Publisher not found")
            return dict(result)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching publisher: {e}")
            raise HTTPException(status_code=500, detail="Error fetching publisher")
    
    async def get_all_publishers(self, limit: int = 100, offset: int = 0):
        """Get all publishers with pagination"""
        try:
            query = "SELECT * FROM publishers ORDER BY id DESC LIMIT $1 OFFSET $2"
            results = await self.db.fetch(query, limit, offset)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching publishers: {e}")
            raise HTTPException(status_code=500, detail="Error fetching publishers")
    
    async def get_publishers_by_ids(self, publisher_ids: list[int]):
        """Get multiple publishers by their IDs"""
        try:
            if not publisher_ids:
                return []
            placeholders = ",".join([f"${i}" for i in range(1, len(publisher_ids) + 1)])
            query = f"SELECT * FROM publishers WHERE id IN ({placeholders})"
            results = await self.db.fetch(query, *publisher_ids)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching publishers by ids: {e}")
            raise HTTPException(status_code=500, detail="Error fetching publishers")
        

