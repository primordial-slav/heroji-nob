"""
Set up SQLite database for soldier records.
Creates schema, migrates existing data, and sets up indexes.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path("01-data/soldiers.db")

# Brigade configuration
BRIGADES = [
    (1, 'Prva Proleterska', 'prva_proleterska', 'website/public/prva-proleterska-soldiers.json'),
    (2, 'Prva Lička Proleterska', 'prva_licka', 'website/public/soldiers.json'),
    (3, 'Druga Lička Proleterska', 'druga_licka', 'website/public/druga-licka-soldiers.json'),
    (4, 'Ljubljanska (10. SNOUB)', 'ljubljanska', 'website/public/ljubljanska-soldiers.json'),
]

SCHEMA = """
-- Brigades reference table
CREATE TABLE IF NOT EXISTS brigades (
    code INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    json_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main soldiers table
CREATE TABLE IF NOT EXISTS soldiers (
    soldier_id TEXT PRIMARY KEY,  -- 10-digit ID: BBBBNNNNNN
    brigade_code INTEGER NOT NULL,
    sequence_num INTEGER NOT NULL,

    -- Original parsed data
    last_name TEXT,
    middle_name TEXT,
    first_name TEXT,
    additional_info TEXT,

    -- AI extraction status
    ai_processed INTEGER DEFAULT 0,  -- 0=no, 1=yes
    ai_confidence TEXT,  -- high, medium, low
    ai_parsing_issues TEXT,  -- comma-separated issues

    -- AI extracted fields
    ai_fathers_name TEXT,
    ai_birth_year TEXT,
    ai_birthplace TEXT,
    ai_military_unit TEXT,
    ai_rank_or_role TEXT,
    ai_death_date TEXT,
    ai_death_place TEXT,
    ai_death_cause TEXT,
    ai_other_info TEXT,

    -- Quality tracking
    manually_reviewed INTEGER DEFAULT 0,  -- 0=no, 1=yes
    review_notes TEXT,

    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key
    FOREIGN KEY (brigade_code) REFERENCES brigades(code)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_soldiers_brigade ON soldiers(brigade_code);
CREATE INDEX IF NOT EXISTS idx_soldiers_last_name ON soldiers(last_name);
CREATE INDEX IF NOT EXISTS idx_soldiers_first_name ON soldiers(first_name);
CREATE INDEX IF NOT EXISTS idx_soldiers_ai_processed ON soldiers(ai_processed);
CREATE INDEX IF NOT EXISTS idx_soldiers_ai_confidence ON soldiers(ai_confidence);
CREATE INDEX IF NOT EXISTS idx_soldiers_updated ON soldiers(updated_at);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS soldiers_fts USING fts5(
    soldier_id,
    last_name,
    first_name,
    middle_name,
    additional_info,
    content='soldiers',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS soldiers_ai AFTER INSERT ON soldiers BEGIN
    INSERT INTO soldiers_fts(rowid, soldier_id, last_name, first_name, middle_name, additional_info)
    VALUES (new.rowid, new.soldier_id, new.last_name, new.first_name, new.middle_name, new.additional_info);
END;

CREATE TRIGGER IF NOT EXISTS soldiers_ad AFTER DELETE ON soldiers BEGIN
    INSERT INTO soldiers_fts(soldiers_fts, rowid, soldier_id, last_name, first_name, middle_name, additional_info)
    VALUES('delete', old.rowid, old.soldier_id, old.last_name, old.first_name, old.middle_name, old.additional_info);
END;

CREATE TRIGGER IF NOT EXISTS soldiers_au AFTER UPDATE ON soldiers BEGIN
    INSERT INTO soldiers_fts(soldiers_fts, rowid, soldier_id, last_name, first_name, middle_name, additional_info)
    VALUES('delete', old.rowid, old.soldier_id, old.last_name, old.first_name, old.middle_name, old.additional_info);
    INSERT INTO soldiers_fts(rowid, soldier_id, last_name, first_name, middle_name, additional_info)
    VALUES (new.rowid, new.soldier_id, new.last_name, new.first_name, new.middle_name, new.additional_info);
END;

-- View for easy querying with brigade name
CREATE VIEW IF NOT EXISTS soldiers_view AS
SELECT
    s.*,
    b.name as brigade_name,
    s.last_name || ' ' || COALESCE(s.middle_name, '') || ' ' || s.first_name as full_name
FROM soldiers s
JOIN brigades b ON s.brigade_code = b.code;
"""


def create_database():
    """Create the database and schema."""
    print(f"Creating database: {DATABASE_PATH}")

    # Remove existing database if present
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print("  Removed existing database")

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Execute schema
    cursor.executescript(SCHEMA)
    conn.commit()

    print("  Schema created successfully")
    return conn


def insert_brigades(conn):
    """Insert brigade reference data."""
    print("\nInserting brigades...")
    cursor = conn.cursor()

    for code, name, short_name, json_file in BRIGADES:
        cursor.execute(
            "INSERT INTO brigades (code, name, short_name, json_file) VALUES (?, ?, ?, ?)",
            (code, name, short_name, json_file)
        )
        print(f"  [{code}] {name}")

    conn.commit()


def load_ai_results():
    """Load AI extraction results for matching."""
    ai_file = Path("01-data/processed/ai_extraction_batched_100.json")
    if not ai_file.exists():
        return {}

    with open(ai_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create lookup by soldier_id if available, otherwise by raw text
    results = {}
    for soldier in data.get('results', []):
        # Try to match by reconstructed raw text
        raw = soldier.get('_raw_input', '')
        if raw:
            results[raw] = soldier

    return results


def build_raw_text(soldier):
    """Reconstruct raw text for AI matching."""
    parts = []
    if soldier.get('last_name'):
        parts.append(soldier['last_name'])
    if soldier.get('middle_name'):
        parts.append(soldier['middle_name'])
    if soldier.get('first_name'):
        parts.append(soldier['first_name'])

    raw_text = ' '.join(parts)
    if soldier.get('additional_info'):
        raw_text += ', ' + soldier['additional_info']

    return raw_text


def migrate_soldiers(conn):
    """Migrate soldiers from JSON files to database."""
    print("\nMigrating soldiers...")
    cursor = conn.cursor()

    # Load AI results
    ai_results = load_ai_results()
    print(f"  Loaded {len(ai_results)} AI extraction results")

    total_inserted = 0
    total_ai_matched = 0

    for code, name, short_name, json_file in BRIGADES:
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"  WARNING: {json_file} not found")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            soldiers = json.load(f)

        print(f"\n  Processing {name}: {len(soldiers)} soldiers")

        batch = []
        for i, soldier in enumerate(soldiers, 1):
            soldier_id = soldier.get('soldier_id', f"{code:04d}{i:06d}")
            raw_text = build_raw_text(soldier)
            ai_data = ai_results.get(raw_text, {})

            if ai_data:
                total_ai_matched += 1

            record = (
                soldier_id,
                code,
                i,
                soldier.get('last_name', ''),
                soldier.get('middle_name', ''),
                soldier.get('first_name', ''),
                soldier.get('additional_info', ''),
                1 if ai_data else 0,
                ai_data.get('confidence', ''),
                ', '.join(ai_data.get('parsing_issues', [])) if ai_data else '',
                ai_data.get('fathers_name', ''),
                ai_data.get('birth_year', ''),
                ai_data.get('birthplace', ''),
                ai_data.get('military_unit', ''),
                ai_data.get('rank_or_role', ''),
                ai_data.get('death_date', ''),
                ai_data.get('death_place', ''),
                ai_data.get('death_cause', ''),
                ai_data.get('other_info', ''),
            )
            batch.append(record)

        # Bulk insert
        cursor.executemany("""
            INSERT INTO soldiers (
                soldier_id, brigade_code, sequence_num,
                last_name, middle_name, first_name, additional_info,
                ai_processed, ai_confidence, ai_parsing_issues,
                ai_fathers_name, ai_birth_year, ai_birthplace,
                ai_military_unit, ai_rank_or_role,
                ai_death_date, ai_death_place, ai_death_cause, ai_other_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)

        total_inserted += len(batch)
        print(f"    Inserted {len(batch)} soldiers (IDs: {batch[0][0]} - {batch[-1][0]})")

    conn.commit()
    print(f"\n  Total inserted: {total_inserted}")
    print(f"  AI matched: {total_ai_matched}")


def verify_database(conn):
    """Verify the database was created correctly."""
    print("\n" + "=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    cursor = conn.cursor()

    # Count by brigade
    cursor.execute("""
        SELECT b.name, COUNT(s.soldier_id) as count,
               SUM(s.ai_processed) as ai_done
        FROM brigades b
        LEFT JOIN soldiers s ON b.code = s.brigade_code
        GROUP BY b.code
        ORDER BY b.code
    """)

    print(f"\n{'Brigade':<35} {'Count':>8} {'AI Done':>8}")
    print("-" * 55)
    total = 0
    total_ai = 0
    for name, count, ai_done in cursor.fetchall():
        print(f"{name:<35} {count:>8} {ai_done:>8}")
        total += count
        total_ai += ai_done or 0
    print("-" * 55)
    print(f"{'TOTAL':<35} {total:>8} {int(total_ai):>8}")

    # Test FTS search
    print("\n\nTesting full-text search...")
    cursor.execute("""
        SELECT soldier_id, last_name, first_name
        FROM soldiers_fts
        WHERE soldiers_fts MATCH 'Adam*'
        LIMIT 5
    """)
    results = cursor.fetchall()
    print(f"  Search 'Adam*': {len(results)} results")
    for sid, ln, fn in results:
        print(f"    {sid}: {ln} {fn}")

    # File size
    size_mb = DATABASE_PATH.stat().st_size / (1024 * 1024)
    print(f"\n\nDatabase file size: {size_mb:.2f} MB")
    print(f"Location: {DATABASE_PATH.absolute()}")


def main():
    print("=" * 70)
    print("SOLDIER DATABASE SETUP")
    print("=" * 70)

    conn = create_database()
    insert_brigades(conn)
    migrate_soldiers(conn)
    verify_database(conn)

    conn.close()

    print("\n" + "=" * 70)
    print("Setup complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
