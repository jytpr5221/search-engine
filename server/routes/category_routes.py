from fastapi import APIRouter, HTTPException, Query, Header
from controllers.category_controller import CategoryController
from utility.security import get_token_from_header, verify_jwt_token
from pydantic import BaseModel

router = APIRouter()

# Initialize category controller (will be set in app.py)
category_controller = None

class CategoryRequest(BaseModel):
    name: str

def set_category_controller(controller):
    """Set the category controller instance"""
    global category_controller
    category_controller = controller

@router.post("/")
async def create_category(category_request: CategoryRequest, authorization: str = Header(None)):
    """Create a new category"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    if not category_controller:
        raise HTTPException(status_code=500, detail="Category controller not initialized")
    return await category_controller.create_category(category_request)

@router.get("/{category_id}")
async def get_category(category_id: int):
    """Get a single category by ID"""
    if not category_controller:
        raise HTTPException(status_code=500, detail="Category controller not initialized")
    return await category_controller.get_category(category_id)

@router.get("/")
async def get_all_categories(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all categories with pagination"""
    if not category_controller:
        raise HTTPException(status_code=500, detail="Category controller not initialized")
    return await category_controller.get_all_categories(limit=limit, offset=offset)

@router.post("/batch/ids")
async def get_categories_by_ids(category_ids: list[int]):
    """Get multiple categories by their IDs"""
    if not category_controller:
        raise HTTPException(status_code=500, detail="Category controller not initialized")
    return await category_controller.get_categories_by_ids(category_ids)
