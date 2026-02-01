"""
Run AI extraction on ALL soldiers in the database.
Processes in batches of 40 for efficiency.
Updates database with results as it goes.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from openai import OpenAI

DATABASE_PATH = Path("01-data/soldiers.db")
BATCH_SIZE = 40
LOG_FILE = Path("logs/ai_extraction_full.log")

# Extraction prompt
EXTRACTION_PROMPT = """You are extracting soldier information from Yugoslav WWII Partisan brigade records.

You will receive multiple raw text entries about soldiers. For EACH soldier, extract structured information.

## Context

These are historical records from WWII Yugoslav Partisan brigades. The text may have:
- OCR errors (broken words, strange characters)
- Line breaks in the middle of words (like "pogi-nuo" instead of "poginuo")
- Mixed formats (some entries more detailed than others)
- Serbian/Croatian language with special characters (č, ć, š, ž, đ)

## Fields to Extract (per soldier)

Extract these fields (leave empty string "" if not found):

1. **last_name**: Family name/surname
2. **first_name**: Given name
3. **fathers_name**: Father's name (convert to nominative form - see below)
4. **birth_year**: Year of birth (just the 4-digit year)
5. **birth_date**: Full birth date if available (format: DD.MM.YYYY or as written)
6. **birthplace**: Place of birth (village, town, region)
7. **military_unit**: Battalion, company, role (e.g., "3. bataljon", "1. četa", "borac", "komandir voda")
8. **rank_or_role**: Military rank or role (e.g., "borac", "vodnik", "komandir", "bolničar", "kurir")
9. **death_date**: Date of death if mentioned
10. **death_place**: Place of death if mentioned
11. **death_cause**: How they died (e.g., "poginuo" = killed in action, "umro" = died, "nestao" = missing)
12. **other_info**: Any other relevant info (ethnicity, occupation before war, when joined NOB, etc.)
13. **confidence**: "high", "medium", or "low" - your confidence in the extraction accuracy
14. **parsing_issues**: List any problems encountered (e.g., "OCR error", "unclear format", "merged text", "incomplete data")

## Important Notes

- "rođen/rođena" = born
- "poginuo/poginula" = killed in action
- "umro/umrla" = died (often from illness/wounds)
- "nestao/nestala" = missing
- "u NOB od" = in the People's Liberation War since (date they joined)
- "s." or "selo" = village

## CRITICAL: Name Order Pattern

There are TWO common formats:

### Format 1: LASTNAME Father's_genitive FIRSTNAME
When you see ALL CAPS at the END, that's the soldier's FIRST NAME:
- "BUBALO Rade MARKO" → last=BUBALO, father=Rade, first=MARKO
- "ADAMOVIĆ Dmitra DANILO" → last=ADAMOVIĆ, father=Dmitar, first=DANILO

### Format 2: LASTNAME Father's_genitive First_name (mixed case)
When the last part is lowercase/mixed, it's still the first name:
- "ĐEKIĆ Živanov Sreten" → last=ĐEKIĆ, father=Živan, first=Sreten
- "KALINIĆ Marka Dragan" → last=KALINIĆ, father=Marko, first=Dragan

### KEY RULE: Father's name comes BEFORE first name
The middle position is ALWAYS the father's name. The LAST name part (before any comma) is the soldier's FIRST NAME.

### CONVERT FATHER'S NAME TO NOMINATIVE FORM
The source text has father's names in genitive. Convert them back to nominative:
- Lazara → Lazar
- Milorada → Milorad
- Petra → Petar
- Dmitra → Dmitar
- Đure → Đuro
- Marka → Marko
- Jovana → Jovan
- Milana → Milan
- Živanov → Živan
- Petrov → Petar
- Radovanov → Radovan

## Response Format

Return a JSON object with an array of soldier extractions:
{
  "soldiers": [
    {
      "input_index": 0,
      "last_name": "...",
      "first_name": "...",
      "fathers_name": "...",
      "birth_year": "...",
      "birth_date": "",
      "birthplace": "...",
      "military_unit": "...",
      "rank_or_role": "...",
      "death_date": "",
      "death_place": "",
      "death_cause": "",
      "other_info": "...",
      "confidence": "high|medium|low",
      "parsing_issues": []
    },
    ...
  ]
}
"""


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log(message):
    """Log to console and file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)

    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def build_raw_text(soldier):
    """Build raw text from soldier record."""
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

    return raw_text


def extract_batch(client, soldiers_batch):
    """Process a batch of soldiers with OpenAI."""

    # Build batch text
    batch_text = ""
    for i, soldier in enumerate(soldiers_batch):
        raw_text = build_raw_text(soldier)
        batch_text += f"\n--- Soldier {i} (ID: {soldier['soldier_id']}) ---\n{raw_text}\n"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract information for these {len(soldiers_batch)} soldiers:\n{batch_text}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return {
        'soldiers': result.get('soldiers', []),
        'tokens': {
            'prompt': response.usage.prompt_tokens,
            'completion': response.usage.completion_tokens,
            'total': response.usage.total_tokens
        }
    }


def update_soldier_ai(conn, soldier_id, ai_result):
    """Update soldier with AI extraction results."""
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE soldiers SET
            ai_processed = 1,
            ai_process_count = COALESCE(ai_process_count, 0) + 1,
            ai_confidence = ?,
            ai_parsing_issues = ?,
            ai_last_name = ?,
            ai_first_name = ?,
            ai_fathers_name = ?,
            ai_birth_year = ?,
            ai_birthplace = ?,
            ai_military_unit = ?,
            ai_rank_or_role = ?,
            ai_death_date = ?,
            ai_death_place = ?,
            ai_death_cause = ?,
            ai_other_info = ?,
            updated_at = ?
        WHERE soldier_id = ?
    """, (
        ai_result.get('confidence', ''),
        ', '.join(ai_result.get('parsing_issues', [])),
        ai_result.get('last_name', ''),
        ai_result.get('first_name', ''),
        ai_result.get('fathers_name', ''),
        ai_result.get('birth_year', ''),
        ai_result.get('birthplace', ''),
        ai_result.get('military_unit', ''),
        ai_result.get('rank_or_role', ''),
        ai_result.get('death_date', ''),
        ai_result.get('death_place', ''),
        ai_result.get('death_cause', ''),
        ai_result.get('other_info', ''),
        datetime.now().isoformat(),
        soldier_id
    ))


def main():
    log("=" * 70)
    log("AI EXTRACTION - FULL DATABASE")
    log("=" * 70)

    # Load API key
    api_key = None
    key_file = Path("01-data/openai-api.txt")
    if key_file.exists():
        content = key_file.read_text().strip()
        if content.startswith('OPENAI_API_KEY='):
            api_key = content.split('=', 1)[1]
        else:
            api_key = content

    if not api_key:
        log("ERROR: OPENAI_API_KEY not found in 01-data/openai-api.txt")
        return

    client = OpenAI(api_key=api_key)

    # Get soldiers that haven't been processed
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT soldier_id, last_name, middle_name, first_name, additional_info, brigade_code
        FROM soldiers
        WHERE ai_processed = 0
        ORDER BY brigade_code, sequence_num
    """)

    soldiers = [dict(row) for row in cursor.fetchall()]
    total_soldiers = len(soldiers)

    log(f"Soldiers to process: {total_soldiers:,}")
    log(f"Batch size: {BATCH_SIZE}")
    log(f"Total batches: {(total_soldiers + BATCH_SIZE - 1) // BATCH_SIZE}")
    log("")

    # Stats tracking
    total_tokens = 0
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    issues_count = 0
    start_time = time.time()

    # Process in batches
    batch_num = 0
    for i in range(0, total_soldiers, BATCH_SIZE):
        batch_num += 1
        batch = soldiers[i:i + BATCH_SIZE]

        try:
            result = extract_batch(client, batch)
            total_tokens += result['tokens']['total']

            # Update database
            for j, ai_soldier in enumerate(result['soldiers']):
                if j < len(batch):
                    soldier_id = batch[j]['soldier_id']
                    update_soldier_ai(conn, soldier_id, ai_soldier)

                    # Track stats
                    conf = ai_soldier.get('confidence', 'medium')
                    confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
                    if ai_soldier.get('parsing_issues'):
                        issues_count += 1

            conn.commit()

            # Progress update
            processed = min(i + BATCH_SIZE, total_soldiers)
            pct = processed / total_soldiers * 100
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total_soldiers - processed) / rate if rate > 0 else 0

            log(f"Batch {batch_num}: {processed:,}/{total_soldiers:,} ({pct:.1f}%) | "
                f"Tokens: {total_tokens:,} | ETA: {eta/60:.1f}min")

        except Exception as e:
            log(f"ERROR in batch {batch_num}: {e}")
            # Continue with next batch
            time.sleep(2)

    # Final stats
    elapsed = time.time() - start_time

    # Cost calculation
    input_tokens = total_tokens * 0.7
    output_tokens = total_tokens * 0.3
    cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)

    log("")
    log("=" * 70)
    log("EXTRACTION COMPLETE")
    log("=" * 70)
    log(f"Total processed: {total_soldiers:,}")
    log(f"Time elapsed: {elapsed/60:.1f} minutes")
    log(f"Total tokens: {total_tokens:,}")
    log(f"Estimated cost: ${cost:.2f}")
    log("")
    log("Confidence breakdown:")
    log(f"  High:   {confidence_counts.get('high', 0):,}")
    log(f"  Medium: {confidence_counts.get('medium', 0):,}")
    log(f"  Low:    {confidence_counts.get('low', 0):,}")
    log(f"  With issues: {issues_count:,}")

    conn.close()

    log("")
    log("Run 'python scripts/db_export.py' to update JSON/Excel files")


if __name__ == "__main__":
    main()
