import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "promotions.db"
)


def create_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            promotion_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            city TEXT,
            bedrooms INTEGER,
            penthouse INTEGER,
            price INTEGER,
            source TEXT,
            developer TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'NORMAL',
            status TEXT DEFAULT 'NEW'
        )
    """)

    cursor.execute("PRAGMA table_info(promotions)")
    existing_columns = {
        column[1]
        for column in cursor.fetchall()
    }

    required_columns = {
        "city": "TEXT",
        "bedrooms": "INTEGER",
        "penthouse": "INTEGER",
        "price": "INTEGER",
        "source": "TEXT",
        "developer": "TEXT",
        "score": "INTEGER DEFAULT 0",
        "priority": "TEXT DEFAULT 'NORMAL'",
        "status": "TEXT DEFAULT 'NEW'",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE promotions "
                f"ADD COLUMN {column_name} {column_type}"
            )

    connection.commit()
    connection.close()


def promotion_exists(promotion_id):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT 1 FROM promotions WHERE promotion_id=?",
        (promotion_id,)
    )

    exists = cursor.fetchone() is not None

    connection.close()

    return exists


def save_promotion(promotion):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO promotions
        (
            promotion_id,
            title,
            city,
            bedrooms,
            penthouse,
            price,
            source,
            developer,
            score,
            priority
        )
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            promotion["id"],
            promotion["title"],
            promotion.get("city"),
            promotion.get("bedrooms"),
            promotion.get("penthouse", False),
            promotion.get("price"),
            promotion.get("source", "Desconocida"),
            promotion.get("developer"),
            promotion.get("score", 0),
            promotion.get("priority", "PRIORIDAD NORMAL"),
        )
    )

    connection.commit()
    connection.close()


def total_promotions():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM promotions")

    total = cursor.fetchone()[0]

    connection.close()

    return total