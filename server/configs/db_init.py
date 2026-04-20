"""
Database initialization module - Creates tables at startup if they don't exist
"""

import logging

logger = logging.getLogger(__name__)

# SQL Schema Definition
DB_SCHEMA = """
-- Publishers table
CREATE TABLE IF NOT EXISTS publishers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authors table
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    publisher INTEGER NOT NULL,
    publication_year INTEGER,
    edition VARCHAR(50),
    language VARCHAR(50),
    pages INTEGER,
    isbn VARCHAR(20),
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (publisher) REFERENCES publishers(id)
);

-- Book Authors junction table (normalized M-to-M relationship)
CREATE TABLE IF NOT EXISTS book_authors (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id),
    UNIQUE(book_id, author_id)
);

-- Book Categories junction table (normalized M-to-M relationship)
CREATE TABLE IF NOT EXISTS book_categories (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE(book_id, category_id)
);

-- Outbox table for eventual consistency pattern
CREATE TABLE IF NOT EXISTS outbox (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_book_authors_book_id ON book_authors(book_id);
CREATE INDEX IF NOT EXISTS idx_book_authors_author_id ON book_authors(author_id);
CREATE INDEX IF NOT EXISTS idx_book_categories_book_id ON book_categories(book_id);
CREATE INDEX IF NOT EXISTS idx_book_categories_category_id ON book_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_books_publisher ON books(publisher);
CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox(status);
CREATE INDEX IF NOT EXISTS idx_outbox_book_id ON outbox(book_id);
CREATE INDEX IF NOT EXISTS idx_outbox_status_created ON outbox(status, created_at);
"""


async def initialize_database(db):
    """
    Initialize database schema at startup.
    Creates all tables if they don't exist.
    
    Args:
        db: PostgresDB instance
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        if not db or not db.pool:
            logger.error("Database pool not initialized")
            return False
        
        async with db.pool.acquire() as conn:
            # Execute the schema initialization
            await conn.execute(DB_SCHEMA)
            logger.info("Database schema initialized successfully")
        
        return True
    
    except Exception as e:
        logger.error(f"Error initializing database schema: {e}")
        return False


async def verify_tables(db):
    """
    Verify that all required tables exist.
    
    Args:
        db: PostgresDB instance
    
    Returns:
        dict: Status of each table
    """
    try:
        required_tables = [
            'publishers',
            'authors', 
            'categories',
            'books',
            'book_authors',
            'book_categories',
            'outbox'
        ]
        
        if not db or not db.pool:
            logger.error("Database pool not initialized")
            return {}
        
        async with db.pool.acquire() as conn:
            results = {}
            for table_name in required_tables:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                    """,
                    table_name
                )
                results[table_name] = "Exists" if result else "Missing"
            
            logger.info("Database Table Status:")
            for table, status in results.items():
                logger.info(f"  {status}: {table}")
            
            return results
    
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return {}


async def get_table_stats(db):
    """
    Get statistics about database tables (row counts, sizes).
    
    Args:
        db: PostgresDB instance
    
    Returns:
        dict: Statistics for each table
    """
    try:
        if not db or not db.pool:
            return {}
        
        async with db.pool.acquire() as conn:
            stats = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            if stats:
                logger.info("Database Table Statistics:")
                for stat in stats:
                    logger.info(f"  {stat['tablename']}: {stat['row_count']} rows, {stat['size']}")
            
            return [dict(s) for s in stats]
    
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return []
