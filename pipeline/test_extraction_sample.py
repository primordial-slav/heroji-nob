"""
Test AI Extraction on Sample from Database
==========================================

Runs AI extraction on 100 random soldiers from the database
to verify the extraction pipeline is working correctly.

Usage:
    python pipeline/test_extraction_sample.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import sqlite3
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI

DATABASE_PATH = Path("01-data/soldiers.db")
API_KEY_FILE = Path("01-data/openai-api.txt")
PROMPT_FILE = Path("pipeline/prompts/extract_prompt.txt")
BATCH_SIZE = 30


def load_api_key():
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"Set OPENAI_API_KEY env var or create {API_KEY_FILE}")
    content = API_KEY_FILE.read_text().strip()
    if content.startswith('OPENAI_API_KEY='):
        return content.split('=', 1)[1]
    return content


def load_prompt():
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding='utf-8')


def build_raw_text(soldier):
    """Build raw text from soldier record for AI input."""
    parts = []
    if soldier['last_name']:
        parts.append(soldier['last_name'])
    if soldier['middle_name']:
        parts.append(soldier['middle_name'])
    if soldier['first_name']:
        parts.append(soldier['first_name'])

    raw_text = ' '.join(parts)
    if soldier['additional_info']:
        raw_text += ', ' + soldier['additional_info']

    # Also use raw_data if available
    if soldier.get('raw_data'):
        raw_text = soldier['raw_data']

    return raw_text


def extract_batch(client, prompt, soldiers_batch):
    """Extract structured data from a batch."""
    batch_text = ""
    for i, soldier in enumerate(soldiers_batch):
        raw_text = build_raw_text(soldier)
        batch_text += f"\n--- Soldier {i} (ID: {soldier['soldier_id']}) ---\n{raw_text}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Extract data for these {len(soldiers_batch)} soldiers:\n{batch_text}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return {
        'soldiers': result.get('soldiers', []),
        'tokens': response.usage.total_tokens
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test AI extraction on sample')
    parser.add_argument('--sample', type=int, default=100, help='Number of soldiers to sample')
    args = parser.parse_args()

    sample_size = args.sample
    output_file = Path(f"pipeline/workspaces/test_sample_{sample_size}.xlsx")

    print("=" * 60)
    print(f"TEST AI EXTRACTION - {sample_size} SOLDIER SAMPLE")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    # Get 100 random soldiers (mix from different brigades)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT soldier_id, brigade_code, last_name, middle_name, first_name,
               additional_info, raw_data,
               ai_last_name, ai_first_name, ai_fathers_name, ai_confidence
        FROM soldiers
        ORDER BY RANDOM()
        LIMIT ?
    """, (sample_size,))

    soldiers = [dict(row) for row in cursor.fetchall()]
    print(f"Selected {len(soldiers)} soldiers from database")

    # Show brigade distribution
    brigade_counts = {}
    for s in soldiers:
        bc = s['brigade_code']
        brigade_counts[bc] = brigade_counts.get(bc, 0) + 1
    print(f"Brigade distribution: {brigade_counts}")
    print()

    # Setup AI
    client = OpenAI(api_key=load_api_key())
    prompt = load_prompt()

    # Process in batches
    results = []
    total_tokens = 0
    start_time = time.time()

    batch_num = 0
    for i in range(0, len(soldiers), BATCH_SIZE):
        batch_num += 1
        batch = soldiers[i:i + BATCH_SIZE]

        try:
            result = extract_batch(client, prompt, batch)
            total_tokens += result['tokens']

            # Combine original + extracted data
            for j, ai_soldier in enumerate(result['soldiers']):
                if j < len(batch):
                    orig = batch[j]
                    results.append({
                        # IDs
                        'soldier_id': orig['soldier_id'],
                        'brigade_code': orig['brigade_code'],

                        # Original input
                        'input_text': build_raw_text(orig),

                        # Original parsed (from database)
                        'orig_last_name': orig['last_name'] or '',
                        'orig_first_name': orig['first_name'] or '',
                        'orig_middle_name': orig['middle_name'] or '',

                        # Previous AI extraction (if any)
                        'prev_ai_last_name': orig['ai_last_name'] or '',
                        'prev_ai_first_name': orig['ai_first_name'] or '',
                        'prev_ai_fathers_name': orig['ai_fathers_name'] or '',
                        'prev_ai_confidence': orig['ai_confidence'] or '',

                        # NEW AI extraction
                        'new_ai_last_name': ai_soldier.get('last_name', ''),
                        'new_ai_first_name': ai_soldier.get('first_name', ''),
                        'new_ai_fathers_name': ai_soldier.get('fathers_name', ''),
                        'new_ai_birth_year': ai_soldier.get('birth_year', ''),
                        'new_ai_birthplace': ai_soldier.get('birthplace', ''),
                        'new_ai_military_unit': ai_soldier.get('military_unit', ''),
                        'new_ai_rank_or_role': ai_soldier.get('rank_or_role', ''),
                        'new_ai_death_date': ai_soldier.get('death_date', ''),
                        'new_ai_death_place': ai_soldier.get('death_place', ''),
                        'new_ai_death_cause': ai_soldier.get('death_cause', ''),
                        'new_ai_other_info': ai_soldier.get('other_info', ''),
                        'new_ai_confidence': ai_soldier.get('confidence', ''),
                        'new_ai_parsing_issues': ', '.join(ai_soldier.get('parsing_issues', [])),
                    })

            print(f"Batch {batch_num}: {min(i + BATCH_SIZE, len(soldiers))}/{len(soldiers)} | Tokens: {total_tokens}")

        except Exception as e:
            print(f"ERROR in batch {batch_num}: {e}")
            time.sleep(2)

    conn.close()

    # Check if we got any results
    if not results:
        print()
        print("ERROR: No results - all API calls failed.")
        print("Check your OpenAI API quota at: https://platform.openai.com/account/limits")
        return

    # Save to Excel
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    # Create Excel with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Full data
        df.to_excel(writer, sheet_name='All Data', index=False)

        # Comparison view (side by side)
        compare_df = df[[
            'soldier_id', 'input_text',
            'orig_last_name', 'new_ai_last_name',
            'orig_first_name', 'new_ai_first_name',
            'orig_middle_name', 'new_ai_fathers_name',
            'new_ai_confidence', 'new_ai_parsing_issues'
        ]].copy()
        compare_df.to_excel(writer, sheet_name='Compare Names', index=False)

        # Issues only
        issues_df = df[df['new_ai_parsing_issues'] != '']
        if len(issues_df) > 0:
            issues_df.to_excel(writer, sheet_name='With Issues', index=False)

        # Low confidence
        low_conf_df = df[df['new_ai_confidence'] == 'low']
        if len(low_conf_df) > 0:
            low_conf_df.to_excel(writer, sheet_name='Low Confidence', index=False)

    # Stats
    elapsed = time.time() - start_time
    cost = (total_tokens * 0.7 * 0.15 / 1_000_000) + (total_tokens * 0.3 * 0.60 / 1_000_000)

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Processed: {len(results)} soldiers")
    print(f"Time: {elapsed:.1f}s")
    print(f"Tokens: {total_tokens:,}")
    print(f"Est. cost: ${cost:.4f}")
    print()

    # Confidence breakdown
    conf_counts = df['new_ai_confidence'].value_counts()
    print("Confidence breakdown:")
    for conf, count in conf_counts.items():
        print(f"  {conf}: {count}")

    issues_count = len(df[df['new_ai_parsing_issues'] != ''])
    print(f"  With issues: {issues_count}")

    print()
    print(f"Output: {output_file}")
    print()
    print("Sheets in Excel:")
    print("  - All Data: Complete extraction results")
    print("  - Compare Names: Side-by-side original vs AI")
    print("  - With Issues: Rows with parsing issues")
    print("  - Low Confidence: Rows with low confidence")


if __name__ == "__main__":
    main()
