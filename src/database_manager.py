import sqlite3
from pathlib import Path

DATABASE_PATH = Path("database") / "promotions.db"


def create_database():

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

            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

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
            source
        )
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            promotion["id"],
            promotion["title"],
            promotion["city"],
            promotion["bedrooms"],
            promotion["penthouse"],
            promotion["price"],
            "Idealista"
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
