from abc import ABC, abstractmethod
import asyncpg
from elasticsearch import AsyncElasticsearch
import logging
from dotenv import load_dotenv
import os

load_dotenv()
class DB(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass

class PostgresDB(DB):

    def __init__(self, uri: str):
        self.uri = uri
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
            dsn=self.uri,
            min_size=1,
            max_size=10
            )

            logging.info(f"Connected to PostgreSQL at {self.uri}")
        except Exception as e:
            logging.error(f"Error connecting to PostgreSQL at {self.uri}: {e}")
            if self.pool:
                await self.pool.close()
            raise Exception(f"PostgreSQL connection failed: {e}") from e

    async def close(self):
        await self.pool.close()

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
        

class SearchDB(DB):

    def __init__(self, uri: str):
        self.uri = uri
        self.client = None

    async def connect(self):
        self.client = AsyncElasticsearch(hosts=[self.uri])
        try:
            ok = await self.client.ping()
            logging.info(f"Connected to Elasticsearch at {self.uri}, ping response: {ok}")
        except Exception as e:
            logging.error(f"Error connecting to Elasticsearch at {self.uri}: {e}")
            try:
                await self.client.close()
            except Exception:
                pass
            raise Exception(f"Elasticsearch connection failed: {e}") from e
        if not ok:
            try:
                await self.client.close()
            except Exception:
                pass
            raise Exception(f"Elasticsearch ping returned False for {self.uri}")

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def index(self, index: str, document: dict, doc_id=None):
        return await self.client.index(
            index=index,
            id=doc_id,
            document=document
        )
    
    async def index_bulk(self, index: str, documents: list):
        actions = []

        for doc in documents:
            # Handle both dicts and Pydantic models
            doc_id = doc.get("id") if isinstance(doc, dict) else doc.id
            doc_data = doc if isinstance(doc, dict) else doc.model_dump(exclude_none=True)
            
            pair = (
                {"index": {"_index": index, "_id": doc_id}},
                doc_data
            )

            for item in pair:
                actions.append(item)
        return await self.client.bulk(operations=actions)
    
    async def create_index(self, index: str, settings: dict = None):
        body = settings if settings else {}
        return await self.client.indices.create(index=index, body=body)

    async def get(self, index: str, doc_id: str):
        return await self.client.get(index=index, id=doc_id)

    async def delete(self, index: str, doc_id: str):
        return await self.client.delete(index=index, id=doc_id)

    async def search(self, index: str, query: dict):
        return await self.client.search(
            index=index,
            query=query,
        )
    

# postgres_db = PostgresDB(os.getenv("POSTGRESS_DB_URI"))
search_db = SearchDB(os.getenv("ELASTICSEARCH_URI"))