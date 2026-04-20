from fastapi import APIRouter, HTTPException, Query, Header
from controllers.publisher_controller import PublisherController
from utility.security import get_token_from_header, verify_jwt_token
from pydantic import BaseModel

router = APIRouter()

# Initialize publisher controller (will be set in app.py)
publisher_controller = None

class PublisherRequest(BaseModel):
    name: str

def set_publisher_controller(controller):
    """Set the publisher controller instance"""
    global publisher_controller
    publisher_controller = controller

@router.post("/")
async def create_publisher(publisher_request: PublisherRequest, authorization: str = Header(None)):
    """Create a new publisher"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    if not publisher_controller:
        raise HTTPException(status_code=500, detail="Publisher controller not initialized")
    return await publisher_controller.create_publisher(publisher_request)

@router.get("/{publisher_id}")
async def get_publisher(publisher_id: int):
    """Get a single publisher by ID"""
    if not publisher_controller:
        raise HTTPException(status_code=500, detail="Publisher controller not initialized")
    return await publisher_controller.get_publisher(publisher_id)

@router.get("/")
async def get_all_publishers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all publishers with pagination"""
    if not publisher_controller:
        raise HTTPException(status_code=500, detail="Publisher controller not initialized")
    return await publisher_controller.get_all_publishers(limit=limit, offset=offset)

@router.post("/batch/ids")
async def get_publishers_by_ids(publisher_ids: list[int]):
    """Get multiple publishers by their IDs"""
    if not publisher_controller:
        raise HTTPException(status_code=500, detail="Publisher controller not initialized")
    return await publisher_controller.get_publishers_by_ids(publisher_ids)
