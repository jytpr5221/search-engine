from fastapi import APIRouter, HTTPException, Query, Header
from controllers.book_controller import book_controller, BookCreateRequest
from utility.security import get_token_from_header, verify_jwt_token
from typing import Optional

router = APIRouter()

@router.post("/")
async def create_book(book_request: BookCreateRequest, authorization: str = Header(None)):
    """Create a new book with validation and outbox pattern"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    return await book_controller.create_book(book_request)

@router.get("/{book_id}")
async def get_book(book_id: int):
    """Get a single book by ID"""
    return await book_controller.get_book(book_id)

@router.get("/")
async def get_all_books(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all books with pagination"""
    return await book_controller.get_all_books(limit=limit, offset=offset)

@router.post("/batch/ids")
async def get_books_by_ids(book_ids: list[int]):
    """Get multiple books by their IDs"""
    return await book_controller.get_books_by_ids(book_ids)

@router.put("/{book_id}")
async def update_book(book_id: int, update_data: dict, authorization: str = Header(None)):
    """Update a book (partial update)"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    return await book_controller.update_book(book_id, update_data)

@router.delete("/{book_id}")
async def delete_book(book_id: int, authorization: str = Header(None)):
    """Delete a book and all its relationships"""
    # Verify token
    token = get_token_from_header(authorization)
    verify_jwt_token(token)
    return await book_controller.delete_book(book_id)

@router.get("/{book_id}/temp")
async def get_book_temp(book_id: int):
    """Get book from temporary JSON file (legacy endpoint)"""
    return await book_controller.get_book_temp(book_id)