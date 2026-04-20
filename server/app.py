from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.search_routes import router as search_router
from routes.book_routes import router as book_router
from routes.author_routes import router as author_router, set_author_controller
from routes.category_routes import router as category_router, set_category_controller
from routes.publisher_routes import router as publisher_router, set_publisher_controller
from routes.auth_routes import router as auth_router
from configs.db_config import postgres_db, search_db
from configs.db_init import initialize_database, verify_tables, get_table_stats
import logging
from controllers.search_controller import search_controller
from controllers.book_controller import book_controller
from controllers.author_controller import AuthorController
from controllers.category_controller import CategoryController
from controllers.publisher_controller import PublisherController
from controllers.outbox_controller import OutboxController
from utility.outbox_scheduler import OutboxScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize controllers with database connections
author_controller = None
category_controller = None
publisher_controller = None
outbox_controller = None
outbox_scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global author_controller, category_controller, publisher_controller, outbox_controller, outbox_scheduler
    
    # Connect to databases
    logger.info("Connecting to PostgreSQL database...")
    await postgres_db.connect()
    
    logger.info("Connecting to Elasticsearch...")
    await search_db.connect()
    
    # Initialize database schema - creates tables if they don't exist
    logger.info("Initializing database schema...")
    db_init_success = await initialize_database(postgres_db)
    if not db_init_success:
        logger.warning("Database schema initialization had issues, continuing anyway...")
    
    # Verify tables exist
    logger.info("Verifying database tables...")
    table_status = await verify_tables(postgres_db)
    
    # Initialize controllers with database
    logger.info("Initializing controllers...")
    book_controller.db = postgres_db
    book_controller.search_db = search_db
    
    author_controller = AuthorController(postgres_db)
    category_controller = CategoryController(postgres_db)
    publisher_controller = PublisherController(postgres_db)
    
    # Set controller references in routes
    set_author_controller(author_controller)
    set_category_controller(category_controller)
    set_publisher_controller(publisher_controller)
    
    outbox_controller = OutboxController(postgres_db, search_db)
    
    # Initialize and start outbox scheduler
    logger.info("Starting outbox scheduler (30-second interval)...")
    outbox_scheduler = OutboxScheduler(outbox_controller, interval=30)
    await outbox_scheduler.start()
    
    # Initialize search index
    logger.info("Initializing search index...")
    await search_controller.init_index()
    
    # Get and log database statistics
    logger.info("Database statistics:")
    await get_table_stats(postgres_db)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if outbox_scheduler:
        await outbox_scheduler.stop()
    
    await postgres_db.close()
    await search_db.close()
    
    logger.info("Application shutdown complete")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

version_prefix = f"/api"


@app.get("/")
async def root():
    return {"message": "server is running"}

app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["auth"])
app.include_router(search_router, prefix=f"{version_prefix}/search", tags=["search"])
app.include_router(book_router, prefix=f"{version_prefix}/book", tags=["book"])
app.include_router(author_router, prefix=f"{version_prefix}/author", tags=["author"])
app.include_router(category_router, prefix=f"{version_prefix}/category", tags=["category"])
app.include_router(publisher_router, prefix=f"{version_prefix}/publisher", tags=["publisher"])

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, timeout_keep_alive=30)