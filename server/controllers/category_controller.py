from pydantic import BaseModel
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class Category(BaseModel):
    id: int | None = None
    name: str

class CategoryController:

    def __init__(self, db):
        self.db = db
    

    async def create_category(self, category: Category):
        try:
            query = "INSERT INTO categories (name) VALUES ($1) RETURNING id, name"
            result = await self.db.fetchrow(query, category.name)
            return {"id": result["id"], "name": result["name"]} if result else None
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            raise HTTPException(status_code=500, detail="Error creating category")

    async def get_category(self, category_id: int):
        try:
            query = "SELECT * FROM categories WHERE id = $1"
            result = await self.db.fetchrow(query, category_id)
            if not result:
                raise HTTPException(status_code=404, detail="Category not found")
            return dict(result)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching category: {e}")
            raise HTTPException(status_code=500, detail="Error fetching category")
    
    async def get_all_categories(self, limit: int = 100, offset: int = 0):
        """Get all categories with pagination"""
        try:
            query = "SELECT * FROM categories ORDER BY id DESC LIMIT $1 OFFSET $2"
            results = await self.db.fetch(query, limit, offset)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            raise HTTPException(status_code=500, detail="Error fetching categories")
    
    async def get_categories_by_ids(self, category_ids: list[int]):
        """Get multiple categories by their IDs"""
        try:
            if not category_ids:
                return []
            placeholders = ",".join([f"${i}" for i in range(1, len(category_ids) + 1)])
            query = f"SELECT * FROM categories WHERE id IN ({placeholders})"
            results = await self.db.fetch(query, *category_ids)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error(f"Error fetching categories by ids: {e}")
            raise HTTPException(status_code=500, detail="Error fetching categories")
