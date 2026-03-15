"""Migration script to add round_config column to debate_topics table."""
import sqlite3
import os

# Use the same path as app/database.py
DB_PATH = os.path.join(os.path.dirname(__file__), "debates.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        print("Creating database with all tables...")
        # Create database with all tables
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("Database created successfully.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if debate_topics table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debate_topics'")
    if not cursor.fetchone():
        print("Table 'debate_topics' not found. Creating tables...")
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
        conn.close()
        # Re-open to check column
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(debate_topics)")
    columns = [row[1] for row in cursor.fetchall()]

    if "round_config" in columns:
        print("Column 'round_config' already exists. Migration not needed.")
    else:
        cursor.execute("ALTER TABLE debate_topics ADD COLUMN round_config TEXT")
        conn.commit()
        print("Successfully added 'round_config' column to debate_topics table.")

    conn.close()

if __name__ == "__main__":
    migrate()
