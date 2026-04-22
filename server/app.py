from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.routes.search_routes import router as search_router
from src.routes.book_routes import router as book_router
from src.configs.db_config import search_db
import logging
from src.controllers.search_controller import search_controller 
from src.utility.cron_job import start_cronjob, stop_cronjob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await postgres_db.connect()
    await search_db.connect()
    await search_controller.init_index()
    start_cronjob(app, search_controller)
    
    yield
    
    stop_cronjob(app)
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