from fastapi import APIRouter, Depends, Body
from src.controllers.search_controller import search_controller
from src.controllers.filter_controller import filter_controller
from pydantic import BaseModel


class SearchFilters(BaseModel):
    publisher: str | None = None
    category: str | None = None
    tag: str | None = None
    language: str | None = None
    year_gte: int | None = None
    year_lte: int | None = None
    author: str | None = None

class SearchRequest(BaseModel):
    query: str
    filters: SearchFilters | None = None

router = APIRouter()

@router.post("/")
async def search(search_request: SearchRequest = Body(...)):

        filters = {
            "publisher": search_request.filters.publisher if search_request.filters else None,
            "category": search_request.filters.category if search_request.filters else None,
            "tag": search_request.filters.tag if search_request.filters else None,
            "language": search_request.filters.language if search_request.filters else None,
            "year_gte": search_request.filters.year_gte if search_request.filters else None,
            "year_lte": search_request.filters.year_lte if search_request.filters else None,
            "author": search_request.filters.author if search_request.filters else None
        }
        return await search_controller.search(search_request.query.strip(), filters)

@router.post("/auto-complete")
async def auto_complete(search_request: SearchRequest = Body(...)):
        
        print("Received auto-complete request with query:", search_request.query, "and filters:", search_request.filters)
        filters = {
            "publisher": search_request.filters.publisher if search_request.filters else None,
            "category": search_request.filters.category if search_request.filters else None,
            "tag": search_request.filters.tag if search_request.filters else None,
            "language": search_request.filters.language if search_request.filters else None,
            "year_gte": search_request.filters.year_gte if search_request.filters else None,
            "year_lte": search_request.filters.year_lte if search_request.filters else None,
            "author": search_request.filters.author if search_request.filters else None
        }
        return await search_controller.auto_complete(search_request.query.strip(), filters)

@router.get("/filters/options")
async def get_filter_options():
    """Get all available filter options (authors, publishers, categories, languages)"""
    return await filter_controller.get_filter_options()
