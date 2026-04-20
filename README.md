# Campus Library Search Engine

An end-to-end library discovery platform with:
- **Client**: a modern React + Vite interface for searching books
- **Server**: a FastAPI service powered by Elasticsearch for semantic and keyword-based discovery

---

## What This Project Does

This project helps users quickly find library books by title, author, topic, publisher, ISBN, and more.

### Client (`client-inverto`)
- Beautiful search-first UI with autocomplete
- Search results list and detailed book view
- Calls backend APIs for autocomplete, search, and book details
- Includes graceful fallback mock data in UI for unavailable API responses

### Server (`server`)
- FastAPI-based backend with async endpoints
- Elasticsearch-backed indexing and retrieval
- Filter-aware search (`publisher`, `category`, `tag`, `language`, year range)
- Startup lifecycle that connects to search DB and initializes index automatically

---

## Tech Stack

- **Frontend**: React, Vite, Axios
- **Backend**: FastAPI, Uvicorn, Pydantic
- **Search Engine**: Elasticsearch 8.x
- **Infra (local)**: Docker Compose (Elasticsearch + Kibana)
- **Data Access (present in codebase)**: asyncpg, psycopg, python-dotenv

---

## Project Structure

```text
campus-library-searchEngine-jp/
|- client-inverto/        # React app
|- server/                # FastAPI + search logic
|  |- app.py              # App entry point
|  |- routes/             # API routes
|  |- controllers/        # Search + book controllers
|  |- configs/db_config.py
|  |- utility/            # Query reformulation helpers
|  |- docker-compose.yaml # Elasticsearch + Kibana
|  |- books.json          # Sample book data for details endpoint
|- README.md
```

---

## Prerequisites

Install these before running:
- **Node.js** (18+ recommended) and npm
- **Python** (3.10+ recommended) and pip
- **Docker Desktop** (for Elasticsearch/Kibana)

---

## Quick Start

### 1) Start Search Infrastructure (Elasticsearch + Kibana)

From `server/`:

```bash
docker compose up -d
```

Services:
- Elasticsearch: `http://localhost:9200`
- Kibana: `http://localhost:5601`

---

### 2) Run the Server

From `server/`:

```bash
pip install fastapi uvicorn pydantic asyncpg elasticsearch python-dotenv psycopg
python app.py
```

Server runs at: `http://localhost:8000`

Health route:
- `GET /` -> `{"message": "server is running"}`

> Note: The repository currently does not include a `requirements.txt`, so dependencies are installed explicitly above.

---

### 3) Run the Client

From `client-inverto/`:

```bash
npm install
npm run dev
```

Client (Vite dev server) usually runs at: `http://localhost:5173`

---

## Environment Variables (Server)

Create a `.env` file inside `server/`:

```env
ELASTICSEARCH_URI=http://localhost:9200
POSTGRESS_DB_URI=postgresql://user:password@localhost:5432/dbname
```

Notes:
- `ELASTICSEARCH_URI` is required for current search features.
- PostgreSQL connection is present in architecture, but active startup currently focuses on Elasticsearch.

---

## API Overview

Base prefix: `/api`

- `POST /api/search/`  
  Full search with optional filters.

- `POST /api/search/auto-complete`  
  Lightweight suggestions for query typing.

- `POST /api/search/index`  
  Index one book document.

- `POST /api/search/bulk-index`  
  Index multiple book documents in one request.

- `GET /api/book/{book_id}`  
  Fetch book details (currently backed by `books.json` in server).

---

## How The Server Is Built

The server is designed as an async search service with clear separation of concerns:

1. **Application lifecycle (`app.py`)**
   - Starts FastAPI app
   - Enables CORS
   - Connects to Elasticsearch on startup
   - Initializes search index if missing

2. **Route layer (`routes/`)**
   - Defines request/response contracts with Pydantic models
   - Exposes search and book APIs

3. **Controller layer (`controllers/`)**
   - `search_controller.py` builds and executes Elasticsearch queries
   - Handles autocomplete, full search, single indexing, and bulk indexing
   - `book_controller.py` currently serves book detail from local JSON data

4. **DB abstraction (`configs/db_config.py`)**
   - Contains reusable DB interfaces for PostgreSQL and Elasticsearch
   - Uses `AsyncElasticsearch` for async search operations

5. **Query intelligence (`utility/reform_queries.py`)**
   - Reformulates incoming text query into structured keyword signals
   - Supports better targeting for author/publisher/category/tag signals

---

## Search Design Highlights

Search behavior combines multiple strategies:
- Cross-field matching over title, tags, categories, publisher
- Fuzzy matching for typo tolerance
- N-gram analyzers for partial token matching
- Exact term boosts (for example ISBN-like exact matches)
- Additional filter clauses for structured narrowing (language/year/category/etc.)

The Elasticsearch index mapping includes:
- Custom analyzers (`standard_lower`, `ngram_analyzer`, `name_analyzer`)
- Normalizers for lowercase/ascii folding
- Multi-field mappings for flexible retrieval and boosting.

---

## Book Document Schema

```json
{
  "id": "<number>",
  "title": "<string>",
  "description": "<string>",
  "publisher": "<string>",
  "publication_year": "<number>",
  "edition": "<string>",
  "language": "<string>",
  "authors": ["<string>"],
  "categories": ["<string>"],
  "tags": ["<string>"],
  "pages": "<number>",
  "isbn": "<string>"
}
```

---

## Useful Commands

### Client
```bash
npm run dev
npm run build
npm run preview
npm run lint
```

### Server
```bash
python app.py
docker compose up -d
docker compose down
```

---

## Current Notes

- `server/package-lock.json` exists but server is Python-based.
- A proper `requirements.txt` would improve reproducibility.
- PostgreSQL integration is scaffolded and can be fully enabled later.

---

## Future Improvements (Suggested)

- Add `requirements.txt` and optional `pyproject.toml`
- Add seed/index script for `books.json` -> Elasticsearch bulk import
- Add API docs section with sample request/response payloads
- Add unit/integration tests for search query builder
