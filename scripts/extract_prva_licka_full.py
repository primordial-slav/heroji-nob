"""
Extract all Prva Lička Proleterska soldiers using AI and update Excel file.
Batched processing for cost efficiency.
"""

import sys
import json
import os
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
from openai import OpenAI

EXTRACTION_PROMPT = """You are extracting soldier information from Yugoslav WWII Partisan brigade records.

You will receive multiple raw text entries about soldiers. For EACH soldier, extract structured information.

## Context

These are historical records from WWII Yugoslav Partisan brigades. The text may have:
- OCR errors (broken words, strange characters)
- Line breaks in the middle of words (like "pogi-nuo" instead of "poginuo")
- Serbian/Croatian language with special characters (č, ć, š, ž, đ)

## Fields to Extract (per soldier)

1. **last_name**: Family name/surname
2. **first_name**: Given name
3. **fathers_name**: Father's name (CONVERT to nominative form)
4. **birth_year**: Year of birth (4-digit year only)
5. **birth_date**: Full birth date if available
6. **birthplace**: Place of birth
7. **military_unit**: Battalion, company (e.g., "3. bataljon", "1. četa")
8. **rank_or_role**: Role (e.g., "borac", "vodnik", "komandir", "bolničar")
9. **death_date**: Date of death if mentioned
10. **death_place**: Place of death if mentioned
11. **death_cause**: How died (poginuo/umro/nestao)
12. **other_info**: Other info (ethnicity, occupation, when joined NOB)
13. **confidence**: "high", "medium", or "low"
14. **parsing_issues**: List any problems

## CRITICAL: Name Order Pattern

Format: LASTNAME Father's_genitive FIRSTNAME
- Middle position = father's name
- Last position (before comma) = soldier's first name
- ALL CAPS at end = definitely first name

Examples:
- "BUBALO Rade MARKO" → last=BUBALO, father=Rade, first=MARKO
- "ĐEKIĆ Živanov Sreten" → last=ĐEKIĆ, father=Živan, first=Sreten

## CONVERT FATHER'S NAME TO NOMINATIVE
- Lazara → Lazar, Milorada → Milorad, Petra → Petar
- Dmitra → Dmitar, Đure → Đuro, Marka → Marko
- Jovana → Jovan, Milana → Milan
- Živanov → Živan, Petrov → Petar, Radovanov → Radovan

## Response Format
Return JSON: {"soldiers": [{...}, {...}]}
"""


def extract_soldiers_batch(client, soldiers_batch):
    """Extract info from a batch of soldiers."""
    batch_text = ""
    for i, raw_text in enumerate(soldiers_batch):
        batch_text += f"\n--- Soldier {i} ---\n{raw_text}\n"

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
    tokens = response.usage.total_tokens
    return result.get('soldiers', []), tokens


def main():
    # Load API key (env var first, file fallback)
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        key_file = Path("01-data/openai-api.txt")
        if key_file.exists():
            content = key_file.read_text().strip()
            api_key = content.split('=', 1)[1] if content.startswith('OPENAI_API_KEY=') else content
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY env var or create 01-data/openai-api.txt")
        return
    client = OpenAI(api_key=api_key)

    # Load Prva Lička soldiers
    print("Loading Prva Lička soldiers...")
    soldiers_json = json.load(open('website/public/soldiers.json', encoding='utf-8'))
    print(f"Total soldiers: {len(soldiers_json):,}")

    # Prepare raw text for each soldier
    soldiers_raw = []
    for soldier in soldiers_json:
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
        soldiers_raw.append(raw_text)

    # Process in batches
    batch_size = 20
    num_batches = (len(soldiers_raw) + batch_size - 1) // batch_size

    all_results = []
    total_tokens = 0
    high_conf = 0
    med_conf = 0
    low_conf = 0
    with_issues = 0

    print(f"\nProcessing {num_batches} batches...")
    print("=" * 70)

    start_time = time.time()

    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(soldiers_raw))
        batch = soldiers_raw[start_idx:end_idx]

        try:
            results, tokens = extract_soldiers_batch(client, batch)
            total_tokens += tokens

            for i, r in enumerate(results):
                r['_original_index'] = start_idx + i
                r['_raw_input'] = batch[i] if i < len(batch) else ""
                all_results.append(r)

                conf = r.get('confidence', 'medium')
                if conf == 'high':
                    high_conf += 1
                elif conf == 'low':
                    low_conf += 1
                else:
                    med_conf += 1
                if r.get('parsing_issues'):
                    with_issues += 1

            # Progress update every 10 batches
            if (batch_idx + 1) % 10 == 0 or batch_idx == num_batches - 1:
                elapsed = time.time() - start_time
                rate = (batch_idx + 1) / elapsed * 60
                remaining = (num_batches - batch_idx - 1) / rate if rate > 0 else 0
                print(f"[{batch_idx + 1}/{num_batches}] {end_idx:,} soldiers processed | "
                      f"{rate:.1f} batches/min | ~{remaining:.1f} min remaining")

        except Exception as e:
            print(f"[{batch_idx + 1}/{num_batches}] ERROR: {e}")
            # Add empty results for failed batch
            for i in range(len(batch)):
                all_results.append({
                    '_original_index': start_idx + i,
                    '_raw_input': batch[i],
                    'confidence': 'low',
                    'parsing_issues': [f'API error: {str(e)}']
                })

        # Small delay to avoid rate limits
        time.sleep(0.1)

    elapsed_total = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Total processed: {len(all_results):,}")
    print(f"Time: {elapsed_total/60:.1f} minutes")
    print(f"\nConfidence: High={high_conf} ({high_conf/len(all_results)*100:.1f}%), "
          f"Medium={med_conf} ({med_conf/len(all_results)*100:.1f}%), "
          f"Low={low_conf} ({low_conf/len(all_results)*100:.1f}%)")
    print(f"With issues: {with_issues} ({with_issues/len(all_results)*100:.1f}%)")
    print(f"\nTokens: {total_tokens:,}")
    cost = total_tokens * 0.15 / 1_000_000 * 0.7 + total_tokens * 0.60 / 1_000_000 * 0.3
    print(f"Estimated cost: ${cost:.2f}")

    # Create DataFrame with new structure
    print("\nCreating Excel file...")
    df = pd.DataFrame(all_results)

    # Rename/reorder columns for Excel
    columns_map = {
        'last_name': 'Last Name',
        'first_name': 'First Name',
        'fathers_name': 'Father\'s Name',
        'birth_year': 'Birth Year',
        'birth_date': 'Birth Date',
        'birthplace': 'Birthplace',
        'military_unit': 'Military Unit',
        'rank_or_role': 'Rank/Role',
        'death_date': 'Death Date',
        'death_place': 'Death Place',
        'death_cause': 'Death Cause',
        'other_info': 'Other Info',
        'confidence': 'AI Confidence',
        'parsing_issues': 'Parsing Issues',
        '_raw_input': 'Original Text'
    }

    # Select and rename columns
    output_cols = []
    for old, new in columns_map.items():
        if old in df.columns:
            df[new] = df[old]
            output_cols.append(new)

    df_output = df[output_cols].copy()

    # Convert parsing_issues list to string
    if 'Parsing Issues' in df_output.columns:
        df_output['Parsing Issues'] = df_output['Parsing Issues'].apply(
            lambda x: '; '.join(x) if isinstance(x, list) else str(x) if x else ''
        )

    # Save to Excel
    output_path = Path("01-data/processed/prva_licka_ai_extracted.xlsx")
    df_output.to_excel(output_path, index=False)
    print(f"Saved to: {output_path}")

    # Also save JSON for backup
    json_path = Path("01-data/processed/prva_licka_ai_extracted.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"JSON backup: {json_path}")

    # Save issues separately
    issues = [r for r in all_results if r.get('confidence') == 'low' or r.get('parsing_issues')]
    if issues:
        issues_path = Path("01-data/processed/prva_licka_issues.json")
        with open(issues_path, 'w', encoding='utf-8') as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)
        print(f"Issues ({len(issues)}): {issues_path}")


if __name__ == "__main__":
    main()
