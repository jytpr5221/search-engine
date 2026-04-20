from fastapi import APIRouter, Depends, Body, Header
from controllers.search_controller import search_controller
from utility.security import get_token_from_header, verify_jwt_token
from pydantic import BaseModel


class BookDocument(BaseModel):
    id: int | None
    title: str
    authors: list
    publisher: str
    publication_year: int
    isbn: str
    description: str
    tags: list
    categories: list
    edition: str
    pages: int
    language: str

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

class IndexRequest(BaseModel):
    document: BookDocument

class BulkRequest(BaseModel):
    documents: list[BookDocument]

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

@router.post('/index')
async def index_book(document: IndexRequest = Body(...), authorization: str = Header(None)):
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    return await search_controller.index_book(document.document)

@router.post('/bulk-index')
async def bulk_index(bulk_request: BulkRequest = Body(...), authorization: str = Header(None)):
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    return await search_controller.index_books_bulk(bulk_request.documents)