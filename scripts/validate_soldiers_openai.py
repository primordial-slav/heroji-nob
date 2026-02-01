"""
Validate soldier data extraction using OpenAI GPT-4o-mini.
Tests on a random sample of soldiers to check if data was parsed correctly.
"""

import sys
import json
import random
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'openai'])
    from openai import OpenAI

# The validation prompt - based on our knowledge of the data format
VALIDATION_PROMPT = """You are validating soldier records extracted from Yugoslav WWII Partisan brigade documents.

## Expected Data Format

These records were extracted from historical PDFs listing soldiers from various brigades. The original format typically was:
LASTNAME Father's_name FIRSTNAME, additional information

### Field Expectations:

1. **last_name**: Should be a surname (family name). In original docs it was often ALL CAPS.
   - Examples: "ADAMOVIĆ", "BABIĆ", "ALEKSIĆ"
   - Issues to flag: Contains first name mixed in, has numbers, looks like a sentence

2. **middle_name**: This is the FATHER'S NAME (not a middle name in Western sense).
   - May be empty (that's OK)
   - May be a single initial with period like "M." (OK)
   - May be full name in genitive case like "Dmitra", "Stevana", "Milana" (OK)
   - Issues to flag: Contains full sentences, looks like additional_info leaked in

3. **first_name**: The soldier's given name.
   - Examples: "DANILO", "Nikola", "Stevo", "Mara"
   - May be ALL CAPS (that's OK, it's from original formatting)
   - Issues to flag: Contains last name mixed in, has birth info, has unit info

4. **additional_info**: Everything else - birth, military unit, death info, etc.
   - May contain: "rođen 1924" (born 1924), "rođena" for females
   - May contain: birthplace like "u s. Mekinjar" (in village Mekinjar), "u Beogradu"
   - May contain: military unit like "Borac 3. bataljona", "1. četa", "komandir voda"
   - May contain: death info like "Poginuo na Udbini" (killed at Udbina), "Umro od tifusa" (died of typhus)
   - May contain: dates like "21. 08. 1942. godine"
   - This field can be empty (some records had minimal info)

## Your Task

Analyze the provided soldier record and check if the parsing looks correct.

Return a JSON object with:
{
  "valid": true/false,
  "confidence": "high"/"medium"/"low",
  "issues": ["list of specific issues found, empty if valid"],
  "suggested_fixes": {"field_name": "suggested value"} or {} if no fixes needed
}

Common parsing errors to catch:
- Names concatenated together (e.g., last_name="ANĐELKOVIĆ STRAHINJA" should be split)
- First name contains additional_info (e.g., first_name="VELIMIR. rođen u s. Trlić...")
- Father's name and first name swapped
- OCR artifacts like random characters or broken words
"""


def validate_soldier(client, soldier, soldier_id):
    """Validate a single soldier record using GPT-4o-mini."""

    soldier_data = json.dumps(soldier, ensure_ascii=False, indent=2)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": VALIDATION_PROMPT},
            {"role": "user", "content": f"Validate this soldier record (ID: {soldier_id}):\n\n{soldier_data}"}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    result['soldier_id'] = soldier_id
    result['original_data'] = soldier

    # Track token usage
    result['tokens_used'] = {
        'prompt': response.usage.prompt_tokens,
        'completion': response.usage.completion_tokens,
        'total': response.usage.total_tokens
    }

    return result


def load_all_soldiers():
    """Load soldiers from all brigade JSON files."""
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
                soldier['_brigade'] = brigade_name
                soldier['_source_index'] = i
                all_soldiers.append(soldier)

    return all_soldiers


def main():
    # Check for API key - try file first, then env var
    api_key = None
    key_file = Path("01-data/openai-api.txt")
    if key_file.exists():
        content = key_file.read_text().strip()
        if content.startswith('OPENAI_API_KEY='):
            api_key = content.split('=', 1)[1]
        else:
            api_key = content

    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')

    if not api_key:
        print("ERROR: OPENAI_API_KEY not found")
        print("Either set environment variable or create 01-data/openai-api.txt")
        return

    client = OpenAI(api_key=api_key)

    # Load all soldiers
    print("Loading soldiers...")
    all_soldiers = load_all_soldiers()
    print(f"Total soldiers: {len(all_soldiers):,}")

    # Random sample of 100
    sample_size = 100
    print(f"\nSelecting random sample of {sample_size} soldiers...")
    sample = random.sample(all_soldiers, sample_size)

    # Validate each soldier
    results = []
    total_tokens = 0
    invalid_count = 0

    print("\nValidating soldiers...")
    print("-" * 60)

    for i, soldier in enumerate(sample):
        soldier_display = {k: v for k, v in soldier.items() if not k.startswith('_')}
        result = validate_soldier(client, soldier_display, i + 1)
        results.append(result)

        total_tokens += result['tokens_used']['total']

        if not result['valid']:
            invalid_count += 1
            print(f"\n[{i+1}/{sample_size}] INVALID - {soldier['_brigade']}")
            print(f"  Data: {soldier_display}")
            print(f"  Issues: {result['issues']}")
            if result.get('suggested_fixes'):
                print(f"  Suggested fixes: {result['suggested_fixes']}")
        else:
            # Show progress for valid ones
            confidence = result['confidence']
            print(f"[{i+1}/{sample_size}] Valid ({confidence}) - {soldier.get('last_name', '?')} {soldier.get('first_name', '?')}")

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total validated: {sample_size}")
    print(f"Valid records: {sample_size - invalid_count}")
    print(f"Invalid records: {invalid_count}")
    print(f"Error rate: {invalid_count / sample_size * 100:.1f}%")
    print(f"\nTotal tokens used: {total_tokens:,}")

    # Cost calculation (GPT-4o-mini pricing)
    input_tokens = sum(r['tokens_used']['prompt'] for r in results)
    output_tokens = sum(r['tokens_used']['completion'] for r in results)
    cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
    print(f"Estimated cost: ${cost:.4f}")
    print(f"Projected cost for all {len(all_soldiers):,} soldiers: ${cost / sample_size * len(all_soldiers):.2f}")

    # Save detailed results
    output_file = Path("validation_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_validated': sample_size,
                'valid': sample_size - invalid_count,
                'invalid': invalid_count,
                'error_rate': invalid_count / sample_size,
                'total_tokens': total_tokens,
                'estimated_cost': cost
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
