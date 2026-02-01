"""
Add unique soldier IDs to all JSON files.
This ensures consistency between the Excel and website data.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
from pathlib import Path

# Brigade configuration
BRIGADES = [
    {
        'code': 1,
        'name': 'Prva Proleterska',
        'json_file': 'website/public/prva-proleterska-soldiers.json'
    },
    {
        'code': 2,
        'name': 'Prva Lička Proleterska',
        'json_file': 'website/public/soldiers.json'
    },
    {
        'code': 3,
        'name': 'Druga Lička Proleterska',
        'json_file': 'website/public/druga-licka-soldiers.json'
    },
    {
        'code': 4,
        'name': 'Ljubljanska (10. SNOUB)',
        'json_file': 'website/public/ljubljanska-soldiers.json'
    },
]


def generate_soldier_id(brigade_code: int, sequence: int) -> str:
    """Generate unique 10-digit soldier ID."""
    return f"{brigade_code:04d}{sequence:06d}"


def main():
    print("=" * 70)
    print("Adding Soldier IDs to JSON Files")
    print("=" * 70)

    for brigade in BRIGADES:
        print(f"\nProcessing {brigade['name']}...")
        json_path = Path(brigade['json_file'])

        if not json_path.exists():
            print(f"  WARNING: File not found: {json_path}")
            continue

        # Load soldiers
        with open(json_path, 'r', encoding='utf-8') as f:
            soldiers = json.load(f)

        # Add IDs
        for i, soldier in enumerate(soldiers, 1):
            soldier['soldier_id'] = generate_soldier_id(brigade['code'], i)

        # Save back
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(soldiers, f, ensure_ascii=False, indent=2)

        print(f"  Updated {len(soldiers)} soldiers")
        print(f"  ID range: {generate_soldier_id(brigade['code'], 1)} - {generate_soldier_id(brigade['code'], len(soldiers))}")

    print("\n" + "=" * 70)
    print("Done! All JSON files updated with soldier IDs")
    print("=" * 70)


if __name__ == "__main__":
    main()
