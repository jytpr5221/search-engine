from fastapi import APIRouter, HTTPException
from src.controllers.book_controller import book_controller
from src.controllers.book_controller import Book
router = APIRouter()

@router.get("/{book_id}")
async def get_book(book_id: int):
    return await book_controller.get_book(book_id)

@router.post("/create")
async def create_book(book: Book):
    return await book_controller.create_book(book)