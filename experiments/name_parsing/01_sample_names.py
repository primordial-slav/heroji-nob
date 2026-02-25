"""
Sample names from database for analysis.

Extracts 800 random names from Prva Proleterska (Code 1)
and 200 from Ljubljanska (Code 4) for Slovenian patterns.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path("01-data/soldiers.db")
OUTPUT_PATH = Path("experiments/name_parsing/data/sampled_names.json")


def sample_names():
    """Sample names from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    samples = []

    # Sample 800 from Prva Proleterska (Code 1)
    cursor.execute("""
        SELECT
            soldier_id, brigade_code, raw_data,
            last_name, middle_name, first_name,
            ai_fathers_name, ai_first_name, ai_last_name,
            ai_confidence
        FROM soldiers
        WHERE brigade_code = 1
          AND raw_data IS NOT NULL
          AND raw_data != ''
        ORDER BY RANDOM()
        LIMIT 800
    """)

    for row in cursor.fetchall():
        samples.append(dict(row))

    print(f"Sampled {len(samples)} from Prva Proleterska")

    # Sample 200 from Ljubljanska (Code 4)
    cursor.execute("""
        SELECT
            soldier_id, brigade_code, raw_data,
            last_name, middle_name, first_name,
            ai_fathers_name, ai_first_name, ai_last_name,
            ai_confidence
        FROM soldiers
        WHERE brigade_code = 4
          AND raw_data IS NOT NULL
          AND raw_data != ''
        ORDER BY RANDOM()
        LIMIT 200
    """)

    ljubljanska_count = 0
    for row in cursor.fetchall():
        samples.append(dict(row))
        ljubljanska_count += 1

    print(f"Sampled {ljubljanska_count} from Ljubljanska")

    conn.close()

    # Save to JSON
    output = {
        'sampled_at': datetime.now().isoformat(),
        'total_count': len(samples),
        'breakdown': {
            'prva_proleterska': 800,
            'ljubljanska': ljubljanska_count
        },
        'samples': samples
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(samples)} samples to {OUTPUT_PATH}")

    # Show a few examples
    print("\nExample samples:")
    for sample in samples[:5]:
        print(f"  {sample['raw_data'][:70]}...")


if __name__ == "__main__":
    sample_names()
