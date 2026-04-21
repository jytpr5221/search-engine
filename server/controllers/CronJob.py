import asyncio
import json
import os
from elasticsearch import AsyncElasticsearch

es = AsyncElasticsearch("http://localhost:9200")

FILE_PATH = "books.json"
LAST_HASH = None


def get_file_hash():
    if not os.path.exists(FILE_PATH):
        return None
    with open(FILE_PATH, "rb") as f:
        return hash(f.read())


async def sync_books():
    global LAST_HASH

    while True:
        try:
            current_hash = get_file_hash()

            if current_hash != LAST_HASH:
                print("Change detected in books.json")

                with open(FILE_PATH, "r") as f:
                    books = json.load(f)

                for book in books:
                    await es.index(
                        index="books",
                        id=book["id"],
                        document=book
                    )

                print("Synced to Elasticsearch")
                LAST_HASH = current_hash

        except Exception as e:
            print("Sync error:", e)

        await asyncio.sleep(5)  # poll every 5 sec


async def start_sync():
    await sync_books()