"""
Use OpenAI GPT-4o-mini to intelligently extract soldier information.
The AI reads the raw text about a soldier and extracts structured fields.
"""

import sys
import json
import random
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from openai import OpenAI

# Extraction prompt - AI pulls out the information intelligently
EXTRACTION_PROMPT = """You are extracting soldier information from Yugoslav WWII Partisan brigade records.

You will receive a raw text entry about a soldier. Your job is to intelligently parse it and extract structured information.

## Context

These are historical records from WWII Yugoslav Partisan brigades. The text may have:
- OCR errors (broken words, strange characters)
- Line breaks in the middle of words (like "pogi-nuo" instead of "poginuo")
- Mixed formats (some entries more detailed than others)
- Serbian/Croatian language with special characters (č, ć, š, ž, đ)

## Fields to Extract

Extract these fields (leave empty string "" if not found):

1. **last_name**: Family name/surname
2. **first_name**: Given name
3. **fathers_name**: Father's name (often in genitive case like "Milana" meaning "of Milan")
4. **birth_year**: Year of birth (just the 4-digit year)
5. **birth_date**: Full birth date if available (format: DD.MM.YYYY or as written)
6. **birthplace**: Place of birth (village, town, region)
7. **military_unit**: Battalion, company, role (e.g., "3. bataljon", "1. četa", "borac", "komandir voda")
8. **rank_or_role**: Military rank or role (e.g., "borac", "vodnik", "komandir", "bolničar", "kurir")
9. **death_date**: Date of death if mentioned
10. **death_place**: Place of death if mentioned
11. **death_cause**: How they died (e.g., "poginuo" = killed in action, "umro" = died, "nestao" = missing, "streljan" = executed)
12. **other_info**: Any other relevant info (ethnicity, occupation before war, when joined NOB, etc.)

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
- "ADAMOVIĆ Dmitra DANILO" → last=ADAMOVIĆ, father=Dmitra (of Dmitar), first=DANILO
- "GRBIĆ Đure ISO" → last=GRBIĆ, father=Đure (of Đuro), first=ISO

### Format 2: LASTNAME Father's_genitive First_name (mixed case)
When the last part is lowercase/mixed, it's still the first name:
- "ĐEKIĆ Živanov Sreten" → last=ĐEKIĆ, father=Živanov (of Živan), first=Sreten
- "KALINIĆ Marka Dragan" → last=KALINIĆ, father=Marka (of Marko), first=Dragan

### KEY RULE: Father's name comes BEFORE first name
The middle position is ALWAYS the father's name. The LAST name part (before any comma or additional info) is the soldier's FIRST NAME.

IMPORTANT: When the last word before the comma is in ALL CAPS, that is definitely the FIRST NAME:
- "TISAJ Andrija LENARD" → last=TISAJ, father=Andrija, first=LENARD (LENARD is caps = first name!)

### CONVERT FATHER'S NAME TO NOMINATIVE FORM
The source text has father's names in genitive. Convert them back to nominative (the actual name):
- Lazara → **Lazar**
- Milorada → **Milorad**
- Petra → **Petar**
- Dmitra → **Dmitar**
- Đure → **Đuro**
- Marka → **Marko**
- Jovana → **Jovan**
- Milana → **Milan**
- Bogoljuba → **Bogoljub**
- Vojislava → **Vojislav**

For -ov/-ev/-in endings, extract the root name:
- Živanov → **Živan**
- Petrov → **Petar** (or **Petro**)
- Radovanov → **Radovan**

Some names stay the same: Rade, Mile, Jovo, Sava

## Response Format

Return ONLY a JSON object with the extracted fields. Fix any obvious OCR errors (like "pogi-nuo" → "poginuo").

Example output:
{
  "last_name": "ADAMOVIĆ",
  "first_name": "Danilo",
  "fathers_name": "Dmitar",
  "birth_year": "1924",
  "birth_date": "",
  "birthplace": "Mekinjar",
  "military_unit": "3. bataljon",
  "rank_or_role": "borac",
  "death_date": "21.08.1942",
  "death_place": "Udbina",
  "death_cause": "poginuo",
  "other_info": ""
}
"""


def extract_soldier_info(client, raw_text, soldier_id):
    """Use AI to extract structured info from raw soldier text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": f"Extract soldier information from this text:\n\n{raw_text}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['_raw_input'] = raw_text
    result['_soldier_id'] = soldier_id
    result['_tokens'] = {
        'prompt': response.usage.prompt_tokens,
        'completion': response.usage.completion_tokens,
        'total': response.usage.total_tokens
    }

    return result


def load_soldiers_with_raw_text():
    """
    Load soldiers and reconstruct the raw text from our parsed fields.
    This simulates what the original text looked like.
    """
    files = [
        ('Prva Lička', 'website/public/soldiers.json'),
        ('Prva Proleterska', 'website/public/prva-proleterska-soldiers.json'),
        ('Ljubljanska', 'website/public/ljubljanska-soldiers.json'),
        ('Druga Lička', 'website/public/druga-licka-soldiers.json')
    ]

    all_soldiers = []
    for brigade_name, filepath in files:
        p = Path(filepath)
        if p.exists():
            data = json.load(open(p, encoding='utf-8'))
            for i, soldier in enumerate(data):
                # Reconstruct raw text from parsed fields
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

                all_soldiers.append({
                    'raw_text': raw_text,
                    'original_parsed': soldier,
                    'brigade': brigade_name,
                    'source_index': i
                })

    return all_soldiers


def main():
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
        print("ERROR: OPENAI_API_KEY not found in 01-data/openai-api.txt")
        return

    client = OpenAI(api_key=api_key)

    # Load all soldiers
    print("Loading soldiers...")
    all_soldiers = load_soldiers_with_raw_text()
    print(f"Total soldiers: {len(all_soldiers):,}")

    # Random sample
    sample_size = 100
    print(f"\nSelecting random sample of {sample_size} soldiers...")
    sample = random.sample(all_soldiers, sample_size)

    # Extract info for each soldier
    results = []
    total_tokens = 0

    print("\nExtracting soldier information with AI...")
    print("=" * 70)

    for i, soldier in enumerate(sample):
        extracted = extract_soldier_info(client, soldier['raw_text'], i + 1)
        extracted['_brigade'] = soldier['brigade']
        extracted['_original_parsed'] = soldier['original_parsed']
        results.append(extracted)

        total_tokens += extracted['_tokens']['total']

        # Display result
        print(f"\n[{i+1}/{sample_size}] {soldier['brigade']}")
        print(f"  RAW: {soldier['raw_text'][:100]}{'...' if len(soldier['raw_text']) > 100 else ''}")
        print(f"  → Name: {extracted.get('first_name', '')} {extracted.get('fathers_name', '')} {extracted.get('last_name', '')}")
        print(f"  → Born: {extracted.get('birth_year', '')} in {extracted.get('birthplace', '')}")
        print(f"  → Unit: {extracted.get('military_unit', '')} ({extracted.get('rank_or_role', '')})")
        if extracted.get('death_cause'):
            print(f"  → Death: {extracted.get('death_cause', '')} {extracted.get('death_date', '')} at {extracted.get('death_place', '')}")

    # Summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total processed: {sample_size}")
    print(f"Total tokens used: {total_tokens:,}")

    # Cost calculation
    input_tokens = sum(r['_tokens']['prompt'] for r in results)
    output_tokens = sum(r['_tokens']['completion'] for r in results)
    cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
    print(f"Estimated cost: ${cost:.4f}")
    print(f"Projected cost for all {len(all_soldiers):,} soldiers: ${cost / sample_size * len(all_soldiers):.2f}")

    # Save results
    output_file = Path("01-data/processed/ai_extraction_example_100.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_processed': sample_size,
                'total_tokens': total_tokens,
                'estimated_cost': cost,
                'projected_full_cost': cost / sample_size * len(all_soldiers)
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
