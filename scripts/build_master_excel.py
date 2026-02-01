"""
Build master Excel file with all soldiers from all brigades.
Includes:
- Unique 10-digit soldier IDs
- All parsed fields
- AI extraction metadata columns (confidence, parsing_issues)
- Data quality tracking
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Brigade configuration
BRIGADES = [
    {
        'code': 1,
        'name': 'Prva Proleterska',
        'short_name': 'prva_proleterska',
        'json_file': 'website/public/prva-proleterska-soldiers.json'
    },
    {
        'code': 2,
        'name': 'Prva Lička Proleterska',
        'short_name': 'prva_licka',
        'json_file': 'website/public/soldiers.json'
    },
    {
        'code': 3,
        'name': 'Druga Lička Proleterska',
        'short_name': 'druga_licka',
        'json_file': 'website/public/druga-licka-soldiers.json'
    },
    {
        'code': 4,
        'name': 'Ljubljanska (10. SNOUB)',
        'short_name': 'ljubljanska',
        'json_file': 'website/public/ljubljanska-soldiers.json'
    },
]


def generate_soldier_id(brigade_code: int, sequence: int) -> str:
    """Generate unique 10-digit soldier ID."""
    return f"{brigade_code:04d}{sequence:06d}"


def load_ai_extraction_results():
    """Load existing AI extraction results for merging."""
    ai_file = Path("01-data/processed/ai_extraction_batched_100.json")
    if not ai_file.exists():
        return {}

    with open(ai_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create lookup by raw_input text
    results = {}
    for soldier in data.get('results', []):
        raw = soldier.get('_raw_input', '')
        if raw:
            results[raw] = {
                'ai_confidence': soldier.get('confidence', ''),
                'ai_parsing_issues': ', '.join(soldier.get('parsing_issues', [])),
                'ai_last_name': soldier.get('last_name', ''),
                'ai_first_name': soldier.get('first_name', ''),
                'ai_fathers_name': soldier.get('fathers_name', ''),
                'ai_birth_year': soldier.get('birth_year', ''),
                'ai_birthplace': soldier.get('birthplace', ''),
                'ai_military_unit': soldier.get('military_unit', ''),
                'ai_rank_or_role': soldier.get('rank_or_role', ''),
                'ai_death_date': soldier.get('death_date', ''),
                'ai_death_place': soldier.get('death_place', ''),
                'ai_death_cause': soldier.get('death_cause', ''),
                'ai_other_info': soldier.get('other_info', ''),
            }
    return results


def build_raw_text(soldier):
    """Reconstruct raw text from parsed fields for AI matching."""
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


def main():
    print("=" * 70)
    print("Building Master Soldier Database Excel")
    print("=" * 70)

    # Load AI extraction results
    print("\nLoading AI extraction results...")
    ai_results = load_ai_extraction_results()
    print(f"  Found {len(ai_results)} AI-processed records")

    # Process all brigades
    all_soldiers = []

    for brigade in BRIGADES:
        print(f"\nProcessing {brigade['name']}...")
        json_path = Path(brigade['json_file'])

        if not json_path.exists():
            print(f"  WARNING: File not found: {json_path}")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            soldiers = json.load(f)

        print(f"  Loaded {len(soldiers)} soldiers")

        for i, soldier in enumerate(soldiers, 1):
            # Generate unique ID
            soldier_id = generate_soldier_id(brigade['code'], i)

            # Build raw text for AI matching
            raw_text = build_raw_text(soldier)

            # Check for AI results
            ai_data = ai_results.get(raw_text, {})

            # Build record
            record = {
                # Identification
                'soldier_id': soldier_id,
                'brigade_code': brigade['code'],
                'brigade_name': brigade['name'],
                'sequence_num': i,

                # Original parsed data
                'last_name': soldier.get('last_name', ''),
                'middle_name': soldier.get('middle_name', ''),
                'first_name': soldier.get('first_name', ''),
                'additional_info': soldier.get('additional_info', ''),

                # Full name for easy reference
                'full_name': ' '.join(filter(None, [
                    soldier.get('last_name', ''),
                    soldier.get('middle_name', ''),
                    soldier.get('first_name', '')
                ])),

                # AI extraction status
                'ai_processed': 'yes' if ai_data else 'no',
                'ai_confidence': ai_data.get('ai_confidence', ''),
                'ai_parsing_issues': ai_data.get('ai_parsing_issues', ''),

                # AI extracted fields (if available)
                'ai_fathers_name': ai_data.get('ai_fathers_name', ''),
                'ai_birth_year': ai_data.get('ai_birth_year', ''),
                'ai_birthplace': ai_data.get('ai_birthplace', ''),
                'ai_military_unit': ai_data.get('ai_military_unit', ''),
                'ai_rank_or_role': ai_data.get('ai_rank_or_role', ''),
                'ai_death_date': ai_data.get('ai_death_date', ''),
                'ai_death_place': ai_data.get('ai_death_place', ''),
                'ai_death_cause': ai_data.get('ai_death_cause', ''),
                'ai_other_info': ai_data.get('ai_other_info', ''),

                # Quality tracking
                'manually_reviewed': '',
                'review_notes': '',
                'data_source': brigade['short_name'],
            }

            all_soldiers.append(record)

        print(f"  Assigned IDs: {generate_soldier_id(brigade['code'], 1)} - {generate_soldier_id(brigade['code'], len(soldiers))}")

    # Create DataFrame
    print(f"\nTotal soldiers: {len(all_soldiers)}")
    df = pd.DataFrame(all_soldiers)

    # Reorder columns for logical grouping
    column_order = [
        # ID columns
        'soldier_id', 'brigade_code', 'brigade_name', 'sequence_num',

        # Original data
        'last_name', 'middle_name', 'first_name', 'full_name', 'additional_info',

        # AI status
        'ai_processed', 'ai_confidence', 'ai_parsing_issues',

        # AI extracted fields
        'ai_fathers_name', 'ai_birth_year', 'ai_birthplace',
        'ai_military_unit', 'ai_rank_or_role',
        'ai_death_date', 'ai_death_place', 'ai_death_cause',
        'ai_other_info',

        # Quality tracking
        'manually_reviewed', 'review_notes', 'data_source',
    ]

    df = df[column_order]

    # Save to Excel
    output_path = Path("01-data/processed/master_soldiers_database.xlsx")
    print(f"\nSaving to: {output_path}")

    # Use ExcelWriter for better formatting
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Soldiers', index=False)

        # Add summary sheet
        summary_data = []
        for brigade in BRIGADES:
            brigade_df = df[df['brigade_code'] == brigade['code']]
            ai_processed = len(brigade_df[brigade_df['ai_processed'] == 'yes'])
            summary_data.append({
                'Brigade Code': brigade['code'],
                'Brigade Name': brigade['name'],
                'Total Soldiers': len(brigade_df),
                'AI Processed': ai_processed,
                'AI Pending': len(brigade_df) - ai_processed,
                'First ID': generate_soldier_id(brigade['code'], 1),
                'Last ID': generate_soldier_id(brigade['code'], len(brigade_df)),
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Add metadata sheet
        meta_data = {
            'Field': [
                'Generated Date',
                'Total Soldiers',
                'Total Brigades',
                'AI Processed Count',
                'ID Format',
            ],
            'Value': [
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                len(df),
                len(BRIGADES),
                len(df[df['ai_processed'] == 'yes']),
                'BBBBNNNNNN (4-digit brigade + 6-digit sequence)',
            ]
        }
        meta_df = pd.DataFrame(meta_data)
        meta_df.to_excel(writer, sheet_name='Metadata', index=False)

    print(f"\nDone! Created Excel with {len(df)} soldiers")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Brigade':<30} {'Count':>8} {'AI Done':>10} {'ID Range':<25}")
    print("-" * 70)
    for brigade in BRIGADES:
        brigade_df = df[df['brigade_code'] == brigade['code']]
        ai_done = len(brigade_df[brigade_df['ai_processed'] == 'yes'])
        id_range = f"{generate_soldier_id(brigade['code'], 1)}-{generate_soldier_id(brigade['code'], len(brigade_df))}"
        print(f"{brigade['name']:<30} {len(brigade_df):>8} {ai_done:>10} {id_range:<25}")
    print("-" * 70)
    print(f"{'TOTAL':<30} {len(df):>8} {len(df[df['ai_processed'] == 'yes']):>10}")


if __name__ == "__main__":
    main()
