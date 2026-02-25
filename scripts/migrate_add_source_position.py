"""
Migration: Add source_position column to soldiers table.

This migration adds:
    - source_position INTEGER column
    - Index on (brigade_code, source_position)

Safe to run multiple times - checks if column exists first.

Usage:
    python scripts/migrate_add_source_position.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path("01-data/soldiers.db")


def column_exists(conn, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def index_exists(conn, index_name: str) -> bool:
    """Check if an index exists."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    return cursor.fetchone() is not None


def migrate():
    """Run the migration."""
    print("=" * 60)
    print("MIGRATION: Add source_position column")
    print("=" * 60)

    if not DATABASE_PATH.exists():
        print(f"ERROR: Database not found: {DATABASE_PATH}")
        print("Run scripts/setup_database.py first.")
        return False

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    changes_made = False

    # Add source_position column if not exists
    if not column_exists(conn, 'soldiers', 'source_position'):
        print("Adding source_position column...")
        cursor.execute("""
            ALTER TABLE soldiers ADD COLUMN source_position INTEGER
        """)
        changes_made = True
        print("  Column added successfully")
    else:
        print("source_position column already exists - skipping")

    # Add raw_data column if not exists
    if not column_exists(conn, 'soldiers', 'raw_data'):
        print("Adding raw_data column...")
        cursor.execute("""
            ALTER TABLE soldiers ADD COLUMN raw_data TEXT
        """)
        changes_made = True
        print("  Column added successfully")
    else:
        print("raw_data column already exists - skipping")

    # Add ai_process_count column if not exists
    if not column_exists(conn, 'soldiers', 'ai_process_count'):
        print("Adding ai_process_count column...")
        cursor.execute("""
            ALTER TABLE soldiers ADD COLUMN ai_process_count INTEGER DEFAULT 0
        """)
        # Set existing processed records to count=1
        cursor.execute("""
            UPDATE soldiers SET ai_process_count = 1 WHERE ai_processed = 1
        """)
        changes_made = True
        print("  Column added successfully")
    else:
        print("ai_process_count column already exists - skipping")

    # Add ai_nickname column if not exists
    if not column_exists(conn, 'soldiers', 'ai_nickname'):
        print("Adding ai_nickname column...")
        cursor.execute("""
            ALTER TABLE soldiers ADD COLUMN ai_nickname TEXT
        """)
        changes_made = True
        print("  Column added successfully")
    else:
        print("ai_nickname column already exists - skipping")

    # Add index on source_position
    index_name = 'idx_soldiers_source_position'
    if not index_exists(conn, index_name):
        print(f"Creating index {index_name}...")
        cursor.execute(f"""
            CREATE INDEX {index_name} ON soldiers(brigade_code, source_position)
        """)
        changes_made = True
        print("  Index created successfully")
    else:
        print(f"Index {index_name} already exists - skipping")

    if changes_made:
        conn.commit()
        print("\nMigration committed successfully")
    else:
        print("\nNo changes needed - database already up to date")

    # Verify
    print("\nVerifying schema...")
    cursor.execute("PRAGMA table_info(soldiers)")
    columns = cursor.fetchall()
    print(f"  soldiers table has {len(columns)} columns")

    target_cols = ['source_position', 'raw_data', 'ai_process_count', 'ai_nickname']
    for col in target_cols:
        exists = any(c[1] == col for c in columns)
        status = "OK" if exists else "MISSING"
        print(f"  - {col}: {status}")

    conn.close()

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    migrate()
