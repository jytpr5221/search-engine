import json
import logging
import os
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

BOOKS_JSON_PATH = Path(__file__).parent.parent.parent / "books.json"
print(f"Using BOOKS_JSON_PATH: {BOOKS_JSON_PATH}")  # Debug statement to verify path

async def get_pending_books() -> list:
    """Fetch all books with state='pending' from books.json"""
    try:
        with open(BOOKS_JSON_PATH, 'r') as f:
            books = json.load(f)
        return [book for book in books if book.get("state") == "pending"]
    except Exception as e:
        logger.error(f"Error reading books.json: {e}")
        return []


async def update_books_state(book_ids: list, new_state: str) -> None:
    """Update state of specified books in books.json"""
    try:
        with open(BOOKS_JSON_PATH, 'r') as f:
            books = json.load(f)
        
        for book in books:
            if book.get("id") in book_ids:
                book["state"] = new_state
        
        with open(BOOKS_JSON_PATH, 'w') as f:
            json.dump(books, f, indent=2)
        
        logger.info(f"Updated {len(book_ids)} books to state: {new_state}")
    except Exception as e:
        logger.error(f"Error updating books.json: {e}")


async def index_pending_books(search_controller) -> None:
    """Cronjob: Fetch pending books and index them using search_controller.index_books_bulk"""
    pending_books = await get_pending_books()
    
    if not pending_books:
        logger.debug("No pending books to index")
        return
    
    try:
        # Index books in bulk using search_controller with state field included
        result = await search_controller.index_books_bulk(pending_books)
        
        # Mark as completed after successful indexing
        book_ids = [book["id"] for book in pending_books]
        await update_books_state(book_ids, "completed")
        
        logger.info(
            f"Indexed {result['success_count']} books successfully. "
            f"Errors: {result['error_count']}"
        )
    except Exception as e:
        logger.error(f"Error indexing pending books: {e}")


def start_cronjob(app, search_controller) -> None:
    """Initialize and start the cronjob scheduler"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    
    scheduler = AsyncIOScheduler()
    
    # Add the cronjob task - runs every 30 seconds
    scheduler.add_job(
        index_pending_books,
        trigger=IntervalTrigger(seconds=30),
        args=[search_controller],
        id="index_pending_books",
        name="Index Pending Books",
        replace_existing=True
    )
    
    app.state.scheduler = scheduler
    scheduler.start()
    logger.info("Cronjob scheduler started - indexing pending books every 30 seconds")


def stop_cronjob(app) -> None:
    """Stop the cronjob scheduler"""
    if hasattr(app.state, 'scheduler') and app.state.scheduler.running:
        app.state.scheduler.shutdown()
        logger.info("Cronjob scheduler stopped")
