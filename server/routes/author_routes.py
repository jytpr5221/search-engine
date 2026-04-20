from fastapi import APIRouter, HTTPException, Query, Header
from controllers.author_controller import AuthorController
from utility.security import get_token_from_header, verify_jwt_token
from pydantic import BaseModel

router = APIRouter()

# Initialize author controller (will be set in app.py)
author_controller = None

class AuthorRequest(BaseModel):
    name: str

def set_author_controller(controller):
    """Set the author controller instance"""
    global author_controller
    author_controller = controller

@router.post("/")
async def create_author(author_request: AuthorRequest, authorization: str = Header(None)):
    """Create a new author"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    if not author_controller:
        raise HTTPException(status_code=500, detail="Author controller not initialized")
    return await author_controller.create_author(author_request)

@router.get("/{author_id}")
async def get_author(author_id: int):
    """Get a single author by ID"""
    if not author_controller:
        raise HTTPException(status_code=500, detail="Author controller not initialized")
    return await author_controller.get_author(author_id)

@router.get("/")
async def get_all_authors(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all authors with pagination"""
    if not author_controller:
        raise HTTPException(status_code=500, detail="Author controller not initialized")
    return await author_controller.get_all_authors(limit=limit, offset=offset)

@router.post("/batch/ids")
async def get_authors_by_ids(author_ids: list[int]):
    """Get multiple authors by their IDs"""
    if not author_controller:
        raise HTTPException(status_code=500, detail="Author controller not initialized")
    return await author_controller.get_authors_by_ids(author_ids)
