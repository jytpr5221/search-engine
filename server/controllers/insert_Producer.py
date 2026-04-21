import asyncio
import asyncpg
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

async def create_book(data):
    conn = await asyncpg.connect(
        user='postgres',
        password='Pramodha@5',
        database='Demo',
        host='localhost'
    )

    # 1. Publisher
    pub = await conn.fetchrow(
        "SELECT id FROM publishers WHERE name=$1", data["publisher"]
    )
    if not pub:
        pub = await conn.fetchrow(
            "INSERT INTO publishers(name) VALUES($1) RETURNING id",
            data["publisher"]
        )
    publisher_id = pub["id"]

    # 2. Insert book
    book = await conn.fetchrow(
        """
        INSERT INTO books(id, 
            title, description, publisher_id,
            publication_year, edition, language,
            pages, isbn, tags
        )
        VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9, $10)
        RETURNING id
        """,
        data["id"],
        data["title"],
        data.get("description"),
        publisher_id,
        data.get("publication_year"),
        data.get("edition"),
        data.get("language"),
        data.get("pages"),
        data.get("isbn"),
        json.dumps(data.get("tags", []))
    )
    book_id = book["id"]

    # 3. Authors
    for name in data["authors"]:
        a = await conn.fetchrow("SELECT id FROM authors WHERE name=$1", name)
        if not a:
            a = await conn.fetchrow(
                "INSERT INTO authors(name) VALUES($1) RETURNING id", name
            )
        await conn.execute(
            "INSERT INTO book_authors(book_id, author_id) VALUES($1, $2)",
            book_id, a["id"]
        )

    # 4. Categories
    for name in data["categories"]:
        c = await conn.fetchrow("SELECT id FROM categories WHERE name=$1", name)
        if not c:
            c = await conn.fetchrow(
                "INSERT INTO categories(name) VALUES($1) RETURNING id", name
            )
        await conn.execute(
            "INSERT INTO book_categories(book_id, category_id) VALUES($1, $2)",
            book_id, c["id"]
        )

    # 🔥 5. BUILD FULL DOCUMENT (IMPORTANT)

    authors = await conn.fetch(
        """
        SELECT a.name FROM authors a
        JOIN book_authors ba ON a.id = ba.author_id
        WHERE ba.book_id=$1
        """,
        book_id
    )

    categories = await conn.fetch(
        """
        SELECT c.name FROM categories c
        JOIN book_categories bc ON c.id = bc.category_id
        WHERE bc.book_id=$1
        """,
        book_id
    )

    # 🔥 FINAL DOCUMENT (matches your ES format)
    document = {
        "id": book_id,
        "title": data["title"],
        "description": data.get("description"),
        "publisher": data["publisher"],
        "publication_year": data.get("publication_year"),
        "edition": data.get("edition"),
        "language": data.get("language"),
        "authors": [a["name"] for a in authors],
        "categories": [c["name"] for c in categories],
        "tags": data.get("tags", []),
        "pages": data.get("pages"),
        "isbn": data.get("isbn")
    }

    # 🔥 6. Send FULL doc to Kafka
    producer.send("sync_postgres_to_es", document)
    producer.flush()

    print("Sent full document to Kafka")

    await conn.close()


async def delete_book(book_id: int):
    conn = await asyncpg.connect(
        user='postgres',
        password='Pramodha@5',
        database='Demo',
        host='localhost'
    )

    # Delete from Postgres (cascade handles relations)
    await conn.execute(
        "DELETE FROM books WHERE id=$1",
        book_id
    )

    # 🔥 Send DELETE event to Kafka
    event = {
        "type": "delete",
        "id": book_id
    }

    producer.send("sync_postgres_to_es", event)
    producer.flush()

    print(f"Deleted book {book_id} and sent event")

    await conn.close()


# TEST
asyncio.run(delete_book(701))