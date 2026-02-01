"""
Create JSON data file for Druga Lička brigade for the website.
"""

import sys
import json
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    # Read the CSV
    csv_path = Path("01-data/processed/druga_licka_proleterska_soldiers.csv")
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # Convert to list of dicts matching website format
    soldiers = []
    for _, row in df.iterrows():
        soldier = {
            "last_name": str(row['last_name']) if pd.notna(row['last_name']) else "",
            "middle_name": str(row['middle_name']) if pd.notna(row['middle_name']) else "",
            "first_name": str(row['first_name']) if pd.notna(row['first_name']) else "",
            "additional_info": str(row['additional_info']) if pd.notna(row['additional_info']) else ""
        }
        soldiers.append(soldier)

    print(f"Total soldiers: {len(soldiers)}")

    # Save to JSON
    output_path = Path("website/public/druga-licka-soldiers.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")

    # Show sample
    print("\nFirst 3 entries:")
    for s in soldiers[:3]:
        print(f"  {s['last_name']} {s['middle_name']} {s['first_name']}")


if __name__ == "__main__":
    main()
