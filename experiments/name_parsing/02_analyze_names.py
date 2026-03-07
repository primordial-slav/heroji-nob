"""
Analyze sampled names using OpenAI.

For each name:
1. Parse the raw data to extract correct first name, father's name, last name
2. Convert genitive/possessive forms to nominative
3. Identify ethnicity and naming patterns
4. Categorize any parsing errors
5. Flag women's names

Outputs:
- analysis_results.xlsx: Full analysis for human review
- reference_genitive.json/csv: High-confidence genitive→nominative mappings
- reference_ethnic_patterns.json: Ethnic naming patterns
- summary_stats.json: Statistics on errors found
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import time
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI

# Paths
DATA_PATH = Path("experiments/name_parsing/data/sampled_names.json")
OUTPUT_DIR = Path("experiments/name_parsing/output")
API_KEY_FILE = Path("01-data/openai-api.txt")

# Batch size for API calls
BATCH_SIZE = 20


SYSTEM_PROMPT = """You are an expert in Yugoslav (Serbian, Croatian, Slovenian, Macedonian, Montenegrin) naming conventions and linguistics.

## CRITICAL: Yugoslav Naming Pattern

In Yugoslav military records, the standard format is:
**LASTNAME + FathersName(in genitive case) + FIRSTNAME**

The MIDDLE word is the FATHER'S NAME in genitive case, NOT the person's first name!

### EXAMPLES - Read these carefully:

Example 1: "PETROVIĆ Milana MARKO"
- PETROVIĆ = Last name
- Milana = Father's name IN GENITIVE (father is Milan, "Milana" means "of Milan")
- MARKO = First name (this is the soldier's actual name)
- Result: Last=PETROVIĆ, First=MARKO, Father=Milan

Example 2: "MORAVČEVIĆ Dragutina BRANISLAV"
- MORAVČEVIĆ = Last name
- Dragutina = Father's name IN GENITIVE (father is Dragutin)
- BRANISLAV = First name (the soldier's actual name)
- Result: Last=MORAVČEVIĆ, First=BRANISLAV, Father=Dragutin

Example 3: "MITIĆ Božidara ILIJA"
- MITIĆ = Last name
- Božidara = Father's name IN GENITIVE (father is Božidar)
- ILIJA = First name
- Result: Last=MITIĆ, First=ILIJA, Father=Božidar

### How to identify the father's name (genitive):
The genitive form typically ends in:
- -a: Milan→Milana, Dragutin→Dragutina, Božidar→Božidara, Milivoje→Milivoja
- -e: Sava→Save, Nikola→Nikole
- -ov/-ev (possessive): Miloš→Milošev, Vojin→Vojinov

### When there is NO father's name:
"LEMOVIĆ STJEPAN" = Last: LEMOVIĆ, First: STJEPAN, Father: (none)
"KRIVOŠIJA BRANKO" = Last: KRIVOŠIJA, First: BRANKO, Father: (none)

### Slovenian Pattern (no patronymic):
"Kovač Franc" = Last: Kovač, First: Franc, Father: (none)
Slovenian names typically don't include father's name.

### Italian Pattern:
"ROSSI Giovanni LUIGI" = Last: Rossi, First: Giovanni, Middle/Second name: Luigi
Italian names may have two given names but no patronymic.

### Hungarian Pattern:
Family name first, given name second (like in records).

### Nicknames (RARE):
A nickname only appears when there are TWO names after the father's name:
- "SEKULIĆ Batrića BLAŽO SELJO" = First: BLAŽO, Nickname: SELJO (Seljo is diminutive of Blažo)
- "BOŽOVIĆ Pavia RADOMIR RACO" = First: RADOMIR, Nickname: RACO

DO NOT mark the first name as a nickname. Nicknames are additional short names.

## Women's Names:
Names like Marija, Milka, Stana, Ljubica, Dragica, Radmila indicate female.

## Common OCR Errors:
- Đ→D or Dj
- Ć→C
- Č→C
- Š→S
- Ž→Z
- Lj→L or Lj
- Nj→N or Nj

## Your Task:
For each soldier record, analyze the raw_data and determine:
1. The correctly parsed last_name, first_name, and fathers_name (in NOMINATIVE form)
2. The likely ethnicity based on the name
3. Whether this is a woman's name
4. Any errors in the current parsing
5. Your confidence level

IMPORTANT: Only mark confidence as "high" if you are very certain. Use "medium" for reasonable guesses and "low" for uncertain cases."""


USER_PROMPT_TEMPLATE = """Analyze these {count} soldier records. For each one, extract the correct name components.

REMEMBER: The pattern is LASTNAME + FathersName(genitive) + FIRSTNAME
- The LAST word is usually the FIRST NAME (the soldier's actual name)
- The MIDDLE word (if present) is the FATHER'S name in genitive case
- Convert father's name from genitive to nominative (e.g., Milana → Milan)

Return a JSON object with this structure:
{{
  "analyses": [
    {{
      "soldier_id": "the soldier_id from input",
      "raw_data": "first 100 chars of raw_data",

      "parsed_last_name": "the family name (usually first word, in caps)",
      "parsed_first_name": "the soldier's actual first name (usually LAST word before comma/year)",
      "parsed_nickname": "ONLY if there are TWO names at the end, the second shorter one is nickname. Usually empty.",
      "parsed_fathers_name": "father's name converted to NOMINATIVE form. Empty string if no father's name present.",
      "fathers_name_original_form": "father's name exactly as it appears in raw_data (genitive form). Empty if none.",

      "is_female": true/false,
      "ethnicity": "Serbian/Croatian/Slovenian/Italian/Hungarian/Albanian/Jewish/Montenegrin/Macedonian/Bosnian/Muslim/Unknown",

      "error_types": ["list of error types found in CURRENT parsing, not your parsing"],
      "notes": "any observations about OCR issues, unusual patterns, etc.",

      "confidence": "high/medium/low"
    }}
  ]
}}

Error types to use:
- "genitive_not_converted": Father's name left in genitive form
- "father_merged_with_first": Father's name wrongly merged with first name
- "ocr_error": Character recognition issues
- "not_a_name": Bad data (place names, notes parsed as names)
- "ethnic_pattern": Non-Slavic naming convention mishandled
- "abbreviated": Father's name is initial only
- "missing_fathers_name": No father's name when one was expected
- "correct": Current parsing is correct

Here are the records to analyze:

{records}"""


def load_api_key():
    """Load OpenAI API key from env var or file fallback."""
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    if not API_KEY_FILE.exists():
        raise FileNotFoundError(f"Set OPENAI_API_KEY env var or create {API_KEY_FILE}")
    content = API_KEY_FILE.read_text().strip()
    if content.startswith('OPENAI_API_KEY='):
        return content.split('=', 1)[1]
    return content


def load_samples():
    """Load sampled names from JSON."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['samples']


def format_record_for_prompt(sample):
    """Format a single record for the prompt."""
    return f"""---
soldier_id: {sample['soldier_id']}
raw_data: {sample['raw_data'][:150] if sample['raw_data'] else 'N/A'}
current_parse:
  last_name: {sample.get('last_name', '')}
  middle_name: {sample.get('middle_name', '')}
  first_name: {sample.get('first_name', '')}
  ai_fathers_name: {sample.get('ai_fathers_name', '')}
---"""


def analyze_batch(client, batch):
    """Analyze a batch of records with OpenAI."""
    records_text = "\n".join(format_record_for_prompt(s) for s in batch)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                count=len(batch),
                records=records_text
            )}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return result.get('analyses', []), response.usage.total_tokens


def build_reference_tables(analyses):
    """Build reference tables from high-confidence analyses."""
    genitive_mappings = {}  # genitive_form -> nominative_form
    ethnic_patterns = {}  # ethnicity -> list of example names

    for analysis in analyses:
        if analysis.get('confidence') != 'high':
            continue

        # Genitive mappings
        fathers_orig = analysis.get('fathers_name_original_form', '').strip()
        fathers_nom = analysis.get('parsed_fathers_name', '').strip()

        if fathers_orig and fathers_nom and fathers_orig != fathers_nom:
            if fathers_orig not in genitive_mappings:
                genitive_mappings[fathers_orig] = {
                    'nominative': fathers_nom,
                    'examples': []
                }
            # Add example if we don't have too many
            if len(genitive_mappings[fathers_orig]['examples']) < 3:
                genitive_mappings[fathers_orig]['examples'].append({
                    'raw': analysis.get('raw_data', '')[:80],
                    'soldier_id': analysis.get('soldier_id', '')
                })

        # Ethnic patterns
        ethnicity = analysis.get('ethnicity', 'Unknown')
        if ethnicity and ethnicity != 'Unknown':
            if ethnicity not in ethnic_patterns:
                ethnic_patterns[ethnicity] = {
                    'count': 0,
                    'example_names': [],
                    'naming_notes': set()
                }
            ethnic_patterns[ethnicity]['count'] += 1

            # Add example name
            if len(ethnic_patterns[ethnicity]['example_names']) < 10:
                ethnic_patterns[ethnicity]['example_names'].append({
                    'last_name': analysis.get('parsed_last_name', ''),
                    'first_name': analysis.get('parsed_first_name', ''),
                    'nickname': analysis.get('parsed_nickname', ''),
                    'fathers_name': analysis.get('parsed_fathers_name', ''),
                    'is_female': analysis.get('is_female', False)
                })

    # Convert sets to lists for JSON serialization
    for eth in ethnic_patterns.values():
        eth['naming_notes'] = list(eth['naming_notes'])

    return genitive_mappings, ethnic_patterns


def calculate_stats(analyses):
    """Calculate summary statistics."""
    stats = {
        'total_analyzed': len(analyses),
        'confidence_breakdown': {'high': 0, 'medium': 0, 'low': 0},
        'ethnicity_breakdown': {},
        'error_type_counts': {},
        'female_count': 0,
        'nickname_count': 0,
        'correct_count': 0
    }

    for analysis in analyses:
        # Confidence
        conf = analysis.get('confidence', 'low')
        stats['confidence_breakdown'][conf] = stats['confidence_breakdown'].get(conf, 0) + 1

        # Ethnicity
        eth = analysis.get('ethnicity', 'Unknown')
        stats['ethnicity_breakdown'][eth] = stats['ethnicity_breakdown'].get(eth, 0) + 1

        # Error types
        for error in analysis.get('error_types', []):
            stats['error_type_counts'][error] = stats['error_type_counts'].get(error, 0) + 1

        # Female
        if analysis.get('is_female'):
            stats['female_count'] += 1

        # Nickname
        if analysis.get('parsed_nickname'):
            stats['nickname_count'] += 1

        # Correct
        if 'correct' in analysis.get('error_types', []):
            stats['correct_count'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description='Analyze sampled names with OpenAI')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                        help=f'Records per API call (default: {BATCH_SIZE})')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of records to process (for testing)')
    parser.add_argument('--resume', type=int, default=0,
                        help='Resume from record index')
    args = parser.parse_args()

    print("=" * 60)
    print("NAME PARSING ANALYSIS")
    print("=" * 60)

    # Load samples
    samples = load_samples()
    if args.limit:
        samples = samples[:args.limit]
    if args.resume:
        samples = samples[args.resume:]

    print(f"Loaded {len(samples)} samples to analyze")

    # Setup OpenAI
    client = OpenAI(api_key=load_api_key())

    # Process in batches
    all_analyses = []
    total_tokens = 0
    start_time = time.time()

    for i in range(0, len(samples), args.batch_size):
        batch = samples[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(samples) + args.batch_size - 1) // args.batch_size

        try:
            analyses, tokens = analyze_batch(client, batch)
            all_analyses.extend(analyses)
            total_tokens += tokens

            elapsed = time.time() - start_time
            rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
            eta = (len(samples) - i - len(batch)) / rate if rate > 0 else 0

            print(f"Batch {batch_num}/{total_batches}: {len(analyses)} analyzed | "
                  f"Tokens: {total_tokens:,} | ETA: {eta:.0f}s")

        except Exception as e:
            print(f"ERROR in batch {batch_num}: {e}")
            time.sleep(2)

    # Build reference tables
    print("\nBuilding reference tables...")
    genitive_mappings, ethnic_patterns = build_reference_tables(all_analyses)

    # Calculate stats
    stats = calculate_stats(all_analyses)
    stats['total_tokens'] = total_tokens
    stats['processing_time_seconds'] = time.time() - start_time

    # Save outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Full analysis Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f'analysis_results_{timestamp}.xlsx'
    print(f"\nSaving {excel_filename}...")
    df_data = []
    for analysis in all_analyses:
        df_data.append({
            'soldier_id': analysis.get('soldier_id', ''),
            'raw_data': analysis.get('raw_data', ''),
            'parsed_last_name': analysis.get('parsed_last_name', ''),
            'parsed_first_name': analysis.get('parsed_first_name', ''),
            'parsed_nickname': analysis.get('parsed_nickname', ''),
            'parsed_fathers_name': analysis.get('parsed_fathers_name', ''),
            'fathers_name_original': analysis.get('fathers_name_original_form', ''),
            'is_female': analysis.get('is_female', False),
            'ethnicity': analysis.get('ethnicity', ''),
            'error_types': ', '.join(analysis.get('error_types', [])),
            'notes': analysis.get('notes', ''),
            'confidence': analysis.get('confidence', '')
        })
    df = pd.DataFrame(df_data)
    df.to_excel(OUTPUT_DIR / excel_filename, index=False)

    # 2. Genitive reference - JSON
    print("Saving reference_genitive.json...")
    with open(OUTPUT_DIR / 'reference_genitive.json', 'w', encoding='utf-8') as f:
        json.dump(genitive_mappings, f, ensure_ascii=False, indent=2)

    # 3. Genitive reference - CSV
    print("Saving reference_genitive.csv...")
    gen_df_data = []
    for genitive, data in genitive_mappings.items():
        gen_df_data.append({
            'genitive_form': genitive,
            'nominative_form': data['nominative'],
            'example_count': len(data['examples']),
            'example_raw': data['examples'][0]['raw'] if data['examples'] else ''
        })
    gen_df = pd.DataFrame(gen_df_data)
    gen_df.to_csv(OUTPUT_DIR / 'reference_genitive.csv', index=False, encoding='utf-8')

    # 4. Ethnic patterns - JSON
    print("Saving reference_ethnic_patterns.json...")
    with open(OUTPUT_DIR / 'reference_ethnic_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(ethnic_patterns, f, ensure_ascii=False, indent=2)

    # 5. Summary stats - JSON
    print("Saving summary_stats.json...")
    with open(OUTPUT_DIR / 'summary_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total analyzed: {stats['total_analyzed']}")
    print(f"Processing time: {stats['processing_time_seconds']:.1f}s")
    print(f"Total tokens: {stats['total_tokens']:,}")
    print()
    print("Confidence breakdown:")
    for conf, count in stats['confidence_breakdown'].items():
        pct = count / stats['total_analyzed'] * 100 if stats['total_analyzed'] > 0 else 0
        print(f"  {conf}: {count} ({pct:.1f}%)")
    print()
    print("Ethnicity breakdown:")
    for eth, count in sorted(stats['ethnicity_breakdown'].items(), key=lambda x: -x[1]):
        print(f"  {eth}: {count}")
    print()
    print("Error types found:")
    for error, count in sorted(stats['error_type_counts'].items(), key=lambda x: -x[1]):
        print(f"  {error}: {count}")
    print()
    print(f"Women identified: {stats['female_count']}")
    print(f"Nicknames found: {stats['nickname_count']}")
    print(f"Correctly parsed: {stats['correct_count']}")
    print()
    print(f"Genitive mappings collected: {len(genitive_mappings)}")
    print()
    print("Output files:")
    print(f"  {OUTPUT_DIR / excel_filename}")
    print(f"  {OUTPUT_DIR / 'reference_genitive.json'}")
    print(f"  {OUTPUT_DIR / 'reference_genitive.csv'}")
    print(f"  {OUTPUT_DIR / 'reference_ethnic_patterns.json'}")
    print(f"  {OUTPUT_DIR / 'summary_stats.json'}")


if __name__ == "__main__":
    main()
