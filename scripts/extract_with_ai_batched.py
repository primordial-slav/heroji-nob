"""
Use OpenAI GPT-4o-mini to intelligently extract soldier information.
BATCHED version - processes multiple soldiers per API call for cost efficiency.
Also tracks parsing confidence and errors.
"""

import sys
import json
import random
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from openai import OpenAI

# Extraction prompt - AI pulls out the information intelligently
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


def extract_soldiers_batch(client, soldiers_batch, batch_start_idx):
    """Use AI to extract structured info from a batch of soldiers."""

    # Format the batch for the prompt
    batch_text = ""
    for i, soldier in enumerate(soldiers_batch):
        batch_text += f"\n--- Soldier {i} ---\n{soldier['raw_text']}\n"

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

    # Add metadata
    result['_batch_start_idx'] = batch_start_idx
    result['_tokens'] = {
        'prompt': response.usage.prompt_tokens,
        'completion': response.usage.completion_tokens,
        'total': response.usage.total_tokens
    }

    # Match results back to original soldiers
    for i, extracted in enumerate(result.get('soldiers', [])):
        if i < len(soldiers_batch):
            extracted['_raw_input'] = soldiers_batch[i]['raw_text']
            extracted['_brigade'] = soldiers_batch[i]['brigade']
            extracted['_global_index'] = batch_start_idx + i

    return result


def load_soldiers_with_raw_text():
    """Load soldiers and reconstruct the raw text from our parsed fields."""
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
    batch_size = 20
    print(f"\nSelecting random sample of {sample_size} soldiers...")
    print(f"Processing in batches of {batch_size}...")
    sample = random.sample(all_soldiers, sample_size)

    # Process in batches
    all_results = []
    total_tokens = 0
    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    with_issues = 0

    num_batches = (sample_size + batch_size - 1) // batch_size

    print("\nExtracting soldier information with AI (batched)...")
    print("=" * 70)

    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, sample_size)
        batch = sample[start_idx:end_idx]

        print(f"\n[Batch {batch_idx + 1}/{num_batches}] Processing soldiers {start_idx + 1}-{end_idx}...")

        result = extract_soldiers_batch(client, batch, start_idx)
        total_tokens += result['_tokens']['total']

        for soldier in result.get('soldiers', []):
            all_results.append(soldier)

            # Track confidence
            conf = soldier.get('confidence', 'medium')
            if conf == 'high':
                high_confidence += 1
            elif conf == 'low':
                low_confidence += 1
            else:
                medium_confidence += 1

            # Track issues
            if soldier.get('parsing_issues'):
                with_issues += 1

            # Display
            name = f"{soldier.get('first_name', '')} {soldier.get('fathers_name', '')} {soldier.get('last_name', '')}"
            issues = soldier.get('parsing_issues', [])
            issue_str = f" ⚠️ {issues}" if issues else ""
            print(f"  [{conf}] {name.strip()}{issue_str}")

    # Summary
    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total processed: {sample_size}")
    print(f"Batches: {num_batches} (size {batch_size})")
    print(f"\nConfidence breakdown:")
    print(f"  High:   {high_confidence} ({high_confidence/sample_size*100:.1f}%)")
    print(f"  Medium: {medium_confidence} ({medium_confidence/sample_size*100:.1f}%)")
    print(f"  Low:    {low_confidence} ({low_confidence/sample_size*100:.1f}%)")
    print(f"\nWith parsing issues: {with_issues} ({with_issues/sample_size*100:.1f}%)")

    print(f"\nTotal tokens used: {total_tokens:,}")

    # Cost calculation
    input_tokens = total_tokens * 0.7  # rough estimate
    output_tokens = total_tokens * 0.3
    cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
    print(f"Estimated cost: ${cost:.4f}")
    print(f"Projected cost for all {len(all_soldiers):,} soldiers: ${cost / sample_size * len(all_soldiers):.2f}")

    # Separate results by confidence
    output_dir = Path("01-data/processed")

    # All results
    output_file = output_dir / "ai_extraction_batched_100.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_processed': sample_size,
                'batch_size': batch_size,
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence,
                'low_confidence': low_confidence,
                'with_issues': with_issues,
                'total_tokens': total_tokens,
                'estimated_cost': cost
            },
            'results': all_results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nAll results saved to: {output_file}")

    # Problematic results only
    problematic = [r for r in all_results if r.get('confidence') == 'low' or r.get('parsing_issues')]
    if problematic:
        problem_file = output_dir / "ai_extraction_issues.json"
        with open(problem_file, 'w', encoding='utf-8') as f:
            json.dump(problematic, f, ensure_ascii=False, indent=2)
        print(f"Problematic entries ({len(problematic)}) saved to: {problem_file}")


if __name__ == "__main__":
    main()
