from fastapi import APIRouter, HTTPException, Request
from controllers.book_controller import book_controller
from controllers.insert_Producer import create_book

router = APIRouter()

@router.get("/{book_id}")
async def get_book(book_id: int):
    return await book_controller.get_book_temp(book_id)

@router.post("/create-book")
async def create_book_route(request: Request):
    try:
        data = await request.json()   # 🔥 raw JSON from frontend

        result = await create_book(data)  # your existing function

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }