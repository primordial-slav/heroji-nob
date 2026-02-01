"""
Export soldiers database to JSON (for website) and Excel (for review).
Run this after making changes to the database.

Output locations:
- Excel: 01-data/exports/excel/
- JSON:  website/public/ (for website)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path("01-data/soldiers.db")
EXPORT_EXCEL_DIR = Path("01-data/exports/excel")
EXPORT_JSON_DIR = Path("01-data/exports/json")


def get_connection():
    """Get database connection."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")
    return sqlite3.connect(DATABASE_PATH)


def export_json():
    """Export soldiers to JSON files for website."""
    print("Exporting to JSON (website/public/)...")

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get brigades
    cursor.execute("SELECT code, name, json_file FROM brigades ORDER BY code")
    brigades = cursor.fetchall()

    for brigade in brigades:
        code = brigade['code']
        name = brigade['name']
        json_file = brigade['json_file']

        # Get soldiers for this brigade
        cursor.execute("""
            SELECT soldier_id, last_name, middle_name, first_name, additional_info
            FROM soldiers
            WHERE brigade_code = ?
            ORDER BY sequence_num
        """, (code,))

        soldiers = []
        for row in cursor.fetchall():
            soldiers.append({
                'soldier_id': row['soldier_id'],
                'last_name': row['last_name'] or '',
                'middle_name': row['middle_name'] or '',
                'first_name': row['first_name'] or '',
                'additional_info': row['additional_info'] or '',
            })

        # Write JSON to website/public
        output_path = Path(json_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(soldiers, f, ensure_ascii=False, indent=2)

        print(f"  {name}: {len(soldiers)} soldiers")

    conn.close()
    print("  Done!")


def export_excel():
    """Export full database to Excel."""
    EXPORT_EXCEL_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()

    # === 1. All Soldiers ===
    all_soldiers_path = EXPORT_EXCEL_DIR / "all_soldiers.xlsx"
    print(f"Exporting: {all_soldiers_path}")

    df = pd.read_sql_query("""
        SELECT
            s.soldier_id,
            s.brigade_code,
            b.name as brigade_name,
            s.sequence_num,
            s.raw_data,
            s.last_name,
            s.middle_name,
            s.first_name,
            s.additional_info,
            CASE s.ai_processed WHEN 1 THEN 'yes' ELSE 'no' END as ai_processed,
            s.ai_process_count,
            s.ai_confidence,
            s.ai_parsing_issues,
            s.ai_last_name,
            s.ai_first_name,
            s.ai_fathers_name,
            s.ai_birth_year,
            s.ai_birthplace,
            s.ai_military_unit,
            s.ai_rank_or_role,
            s.ai_death_date,
            s.ai_death_place,
            s.ai_death_cause,
            s.ai_other_info,
            CASE s.manually_reviewed WHEN 1 THEN 'yes' ELSE 'no' END as manually_reviewed,
            s.review_notes,
            s.created_at,
            s.updated_at
        FROM soldiers s
        JOIN brigades b ON s.brigade_code = b.code
        ORDER BY s.brigade_code, s.sequence_num
    """, conn)

    # Summary sheet
    summary_df = pd.read_sql_query("""
        SELECT
            b.code as brigade_code,
            b.name as brigade_name,
            COUNT(s.soldier_id) as total_soldiers,
            SUM(s.ai_processed) as ai_processed,
            COUNT(s.soldier_id) - SUM(s.ai_processed) as ai_pending,
            MIN(s.soldier_id) as first_id,
            MAX(s.soldier_id) as last_id
        FROM brigades b
        LEFT JOIN soldiers s ON b.code = s.brigade_code
        GROUP BY b.code
        ORDER BY b.code
    """, conn)

    with pd.ExcelWriter(all_soldiers_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='All Soldiers', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        pd.DataFrame({
            'Field': ['Generated', 'Total Soldiers', 'Database'],
            'Value': [datetime.now().isoformat(), len(df), str(DATABASE_PATH.absolute())]
        }).to_excel(writer, sheet_name='Metadata', index=False)

    print(f"  {len(df)} soldiers")

    # === 2. AI Processed Only ===
    ai_processed_path = EXPORT_EXCEL_DIR / "ai_processed_soldiers.xlsx"
    print(f"Exporting: {ai_processed_path}")

    ai_df = pd.read_sql_query("""
        SELECT
            s.soldier_id,
            b.name as brigade_name,
            s.raw_data,
            s.last_name,
            s.middle_name,
            s.first_name,
            s.additional_info,
            s.ai_process_count,
            s.ai_confidence,
            s.ai_parsing_issues,
            s.ai_last_name,
            s.ai_first_name,
            s.ai_fathers_name,
            s.ai_birth_year,
            s.ai_birthplace,
            s.ai_military_unit,
            s.ai_rank_or_role,
            s.ai_death_date,
            s.ai_death_place,
            s.ai_death_cause,
            s.ai_other_info,
            s.updated_at
        FROM soldiers s
        JOIN brigades b ON s.brigade_code = b.code
        WHERE s.ai_processed = 1
        ORDER BY s.soldier_id
    """, conn)

    ai_df.to_excel(ai_processed_path, index=False)
    print(f"  {len(ai_df)} soldiers")

    # === 3. Issues Only (low confidence or parsing issues) ===
    issues_path = EXPORT_EXCEL_DIR / "needs_review.xlsx"
    print(f"Exporting: {issues_path}")

    issues_df = pd.read_sql_query("""
        SELECT
            s.soldier_id,
            b.name as brigade_name,
            s.last_name,
            s.first_name,
            s.additional_info,
            s.ai_confidence,
            s.ai_parsing_issues
        FROM soldiers s
        JOIN brigades b ON s.brigade_code = b.code
        WHERE s.ai_processed = 1
          AND (s.ai_confidence = 'low' OR s.ai_parsing_issues != '')
        ORDER BY s.ai_confidence, s.soldier_id
    """, conn)

    issues_df.to_excel(issues_path, index=False)
    print(f"  {len(issues_df)} soldiers need review")

    conn.close()
    print("  Done!")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Export soldiers database')
    parser.add_argument('--json', action='store_true', help='Export to JSON only')
    parser.add_argument('--excel', action='store_true', help='Export to Excel only')
    args = parser.parse_args()

    print("=" * 60)
    print("DATABASE EXPORT")
    print("=" * 60)

    if args.json:
        export_json()
    elif args.excel:
        export_excel()
    else:
        # Default: export both
        export_json()
        print()
        export_excel()

    print()
    print("=" * 60)
    print("Export complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
