from fastapi import FastAPI
import asyncio
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes.search_routes import router as search_router
from routes.book_routes import router as book_router
from configs.db_config import postgres_db, search_db
import logging
from controllers.search_controller import search_controller 
from controllers.CronJob import start_sync

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await postgres_db.connect()
    await search_db.connect()
    await search_controller.init_index()

    task = asyncio.create_task(start_sync())
    
    yield
    
    task.cancel()
    # await postgres_db.close()
    await search_db.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

version_prefix =f"/api"


@app.get("/")
async def root():
    return {"message": "server is running"}

app.include_router(search_router, prefix=f"{version_prefix}/search", tags=["search"])
app.include_router(book_router, prefix=f"{version_prefix}/book", tags=["book"])

if __name__ == "__main__":
    uvicorn.run("app:app", host = "0.0.0.0", port = 8000, reload = True, timeout_keep_alive=30)