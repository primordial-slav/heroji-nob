import csv
import random
import sys
from pathlib import Path
from collections import Counter

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

def sample_soldiers():
    """Sample 500 random soldiers and analyze date formats"""

    csv_files = [
        '01-data/processed/prva_licka_proleterska_soldiers.csv',
        '01-data/processed/prva_proleterska_soldiers.csv',
        '01-data/processed/ljubljanska_soldiers.csv'
    ]

    all_soldiers = []

    for csv_file in csv_files:
        file_path = Path(csv_file)
        if not file_path.exists():
            continue

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('additional_info'):
                    all_soldiers.append({
                        'name': f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                        'info': row.get('additional_info', '')
                    })

    # Sample 500 random soldiers
    sample_size = min(500, len(all_soldiers))
    sampled = random.sample(all_soldiers, sample_size)

    print(f"Sampled {sample_size} soldiers from {len(all_soldiers)} total\n")
    print("="*100)

    # Show the samples
    for i, soldier in enumerate(sampled, 1):
        print(f"{i}. {soldier['name']}")
        print(f"   Info: {soldier['info'][:150]}{'...' if len(soldier['info']) > 150 else ''}")
        print()

        if i >= 50:  # Show first 50 in detail
            break

    print("\n" + "="*100)
    print("ANALYSIS OF DATE PATTERNS:")
    print("="*100 + "\n")

    # Analyze patterns
    patterns = {
        'starts_with_4digit_year': 0,  # 1920, Somewhere
        'starts_with_ddmmyyyy': 0,     # 29. 12. 1924, Somewhere
        'starts_with_dd_mm_yyyy': 0,   # 15. 4. 1925
        'starts_with_yyyy_dot': 0,     # 1912. Somewhere
        'contains_poginuo': 0,         # Contains death info
        'contains_padel': 0,           # Contains death info (Slovenian)
        'no_clear_date': 0
    }

    examples = {
        'starts_with_4digit_year': [],
        'starts_with_ddmmyyyy': [],
        'starts_with_dd_mm_yyyy': [],
        'starts_with_yyyy_dot': [],
        'contains_poginuo': [],
        'contains_padel': [],
        'no_clear_date': []
    }

    import re

    for soldier in sampled:
        info = soldier['info'].strip()

        # Check for death mentions
        if 'poginuo' in info.lower() or 'nestao' in info.lower():
            patterns['contains_poginuo'] += 1
            if len(examples['contains_poginuo']) < 5:
                examples['contains_poginuo'].append(info[:100])

        if 'padel' in info.lower():
            patterns['contains_padel'] += 1
            if len(examples['contains_padel']) < 5:
                examples['contains_padel'].append(info[:100])

        # Check date patterns at start
        if re.match(r'^\d{1,2}\.\s*\d{1,2}\.\s*\d{4}', info):
            patterns['starts_with_ddmmyyyy'] += 1
            if len(examples['starts_with_ddmmyyyy']) < 5:
                examples['starts_with_ddmmyyyy'].append(info[:100])
        elif re.match(r'^\d{4}\.\s+\w', info):
            patterns['starts_with_yyyy_dot'] += 1
            if len(examples['starts_with_yyyy_dot']) < 5:
                examples['starts_with_yyyy_dot'].append(info[:100])
        elif re.match(r'^\d{4},\s+\w', info):
            patterns['starts_with_4digit_year'] += 1
            if len(examples['starts_with_4digit_year']) < 5:
                examples['starts_with_4digit_year'].append(info[:100])
        elif re.match(r'^\d{4}\s+\w', info):
            patterns['starts_with_4digit_year'] += 1
            if len(examples['starts_with_4digit_year']) < 5:
                examples['starts_with_4digit_year'].append(info[:100])
        else:
            patterns['no_clear_date'] += 1
            if len(examples['no_clear_date']) < 5:
                examples['no_clear_date'].append(info[:100])

    # Print analysis
    for pattern, count in patterns.items():
        percentage = (count / sample_size) * 100
        print(f"{pattern}: {count} ({percentage:.1f}%)")
        if examples[pattern]:
            print("  Examples:")
            for ex in examples[pattern]:
                print(f"    - {ex}")
        print()

if __name__ == '__main__':
    sample_soldiers()
