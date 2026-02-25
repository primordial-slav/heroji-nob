"""
Extract naming patterns from analysis results.

This script analyzes the AI-parsed results to build:
1. Genitive ending patterns (how to detect father's name)
2. Common first names by ethnicity/gender
3. Genitive -> Nominative transformation rules
4. Actual nickname examples

This helps us build rule-based parsing for the future.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import re
import pandas as pd
from pathlib import Path
from collections import defaultdict

OUTPUT_DIR = Path("experiments/name_parsing/output")


def extract_genitive_patterns(df):
    """
    Analyze genitive -> nominative transformations to find patterns.
    """
    patterns = defaultdict(list)

    for _, row in df.iterrows():
        gen = str(row.get('fathers_name_original', '')).strip()
        nom = str(row.get('parsed_fathers_name', '')).strip()

        if not gen or not nom or gen == 'nan' or nom == 'nan':
            continue
        if gen == nom:
            # No transformation - might already be nominative
            patterns['no_change'].append({'gen': gen, 'nom': nom})
            continue

        # Analyze the ending transformation
        # Find common suffix
        min_len = min(len(gen), len(nom))
        common_prefix_len = 0
        for i in range(min_len):
            if gen[i].lower() == nom[i].lower():
                common_prefix_len = i + 1
            else:
                break

        if common_prefix_len > 0:
            gen_suffix = gen[common_prefix_len-1:]
            nom_suffix = nom[common_prefix_len-1:]

            # Categorize by transformation type
            if gen.endswith('a') and not nom.endswith('a'):
                patterns['ends_in_a'].append({'gen': gen, 'nom': nom, 'gen_suffix': gen_suffix, 'nom_suffix': nom_suffix})
            elif gen.endswith('e') and not nom.endswith('e'):
                patterns['ends_in_e'].append({'gen': gen, 'nom': nom, 'gen_suffix': gen_suffix, 'nom_suffix': nom_suffix})
            elif 'ov' in gen.lower() or 'ev' in gen.lower():
                patterns['possessive_ov_ev'].append({'gen': gen, 'nom': nom})
            elif gen.endswith('in'):
                patterns['ends_in_in'].append({'gen': gen, 'nom': nom})
            else:
                patterns['other'].append({'gen': gen, 'nom': nom, 'gen_suffix': gen_suffix, 'nom_suffix': nom_suffix})

    return dict(patterns)


def extract_first_names(df):
    """
    Build list of first names by ethnicity and gender.
    """
    names_by_ethnicity = defaultdict(lambda: {'male': set(), 'female': set()})

    for _, row in df.iterrows():
        first_name = str(row.get('parsed_first_name', '')).strip().upper()
        ethnicity = str(row.get('ethnicity', 'Unknown')).strip()
        is_female = row.get('is_female', False)
        confidence = str(row.get('confidence', '')).strip()

        if not first_name or first_name == 'NAN':
            continue

        # Only use high/medium confidence
        if confidence not in ['high', 'medium']:
            continue

        gender = 'female' if is_female else 'male'
        names_by_ethnicity[ethnicity][gender].add(first_name)

    # Convert sets to sorted lists
    result = {}
    for eth, genders in names_by_ethnicity.items():
        result[eth] = {
            'male': sorted(list(genders['male'])),
            'female': sorted(list(genders['female']))
        }

    return result


def extract_nickname_examples(df):
    """
    Find actual nickname examples (where nickname field is populated).
    """
    examples = []

    for _, row in df.iterrows():
        nickname = str(row.get('parsed_nickname', '')).strip()
        if nickname and nickname != 'nan' and nickname != '':
            examples.append({
                'raw_data': str(row.get('raw_data', ''))[:80],
                'first_name': row.get('parsed_first_name', ''),
                'nickname': nickname,
                'ethnicity': row.get('ethnicity', ''),
                'confidence': row.get('confidence', '')
            })

    return examples


def analyze_genitive_endings(patterns):
    """
    Derive rules for genitive detection from patterns.
    """
    rules = []

    # Analyze 'ends_in_a' pattern
    if patterns.get('ends_in_a'):
        transformations = defaultdict(int)
        for item in patterns['ends_in_a']:
            gen_end = item['gen'][-2:] if len(item['gen']) >= 2 else item['gen'][-1:]
            nom_end = item['nom'][-2:] if len(item['nom']) >= 2 else item['nom'][-1:]
            transformations[f"{gen_end} -> {nom_end}"] += 1

        rules.append({
            'pattern': 'Genitive ending in -a',
            'description': 'Most common: names ending in consonant add -a in genitive',
            'examples': [f"{p['gen']} -> {p['nom']}" for p in patterns['ends_in_a'][:10]],
            'transformations': dict(transformations)
        })

    # Analyze 'ends_in_e' pattern
    if patterns.get('ends_in_e'):
        rules.append({
            'pattern': 'Genitive ending in -e',
            'description': 'Names ending in -a change to -e in genitive (Nikola -> Nikole)',
            'examples': [f"{p['gen']} -> {p['nom']}" for p in patterns['ends_in_e'][:10]]
        })

    # Possessive forms
    if patterns.get('possessive_ov_ev'):
        rules.append({
            'pattern': 'Possessive -ov/-ev',
            'description': 'Possessive adjective form (Miloš -> Milošev, Vojin -> Vojinov)',
            'examples': [f"{p['gen']} -> {p['nom']}" for p in patterns['possessive_ov_ev'][:10]]
        })

    # No change cases
    if patterns.get('no_change'):
        rules.append({
            'pattern': 'No change',
            'description': 'Some names appear in nominative form already',
            'examples': [p['gen'] for p in patterns['no_change'][:10]]
        })

    return rules


def main():
    print("=" * 60)
    print("PATTERN EXTRACTION")
    print("=" * 60)

    # Find the latest analysis file
    files = list(OUTPUT_DIR.glob('analysis_results_*.xlsx'))
    if not files:
        # Try the original filename
        files = list(OUTPUT_DIR.glob('analysis_results.xlsx'))

    if not files:
        print("ERROR: No analysis results found. Run 02_analyze_names.py first.")
        return

    latest = max(files, key=lambda p: p.stat().st_mtime)
    print(f"Reading: {latest.name}")

    df = pd.read_excel(latest)
    print(f"Loaded {len(df)} records")

    # Extract patterns
    print("\nExtracting genitive patterns...")
    genitive_patterns = extract_genitive_patterns(df)

    print("\nExtracting first names by ethnicity...")
    first_names = extract_first_names(df)

    print("\nExtracting nickname examples...")
    nicknames = extract_nickname_examples(df)

    print("\nAnalyzing genitive rules...")
    genitive_rules = analyze_genitive_endings(genitive_patterns)

    # Save results
    print("\nSaving pattern files...")

    # 1. Genitive patterns raw data
    with open(OUTPUT_DIR / 'patterns_genitive_raw.json', 'w', encoding='utf-8') as f:
        # Convert for JSON serialization
        serializable = {}
        for k, v in genitive_patterns.items():
            serializable[k] = v[:50] if len(v) > 50 else v  # Limit to 50 examples each
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    # 2. Genitive rules (derived)
    with open(OUTPUT_DIR / 'patterns_genitive_rules.json', 'w', encoding='utf-8') as f:
        json.dump(genitive_rules, f, ensure_ascii=False, indent=2)

    # 3. First names by ethnicity
    with open(OUTPUT_DIR / 'patterns_first_names.json', 'w', encoding='utf-8') as f:
        json.dump(first_names, f, ensure_ascii=False, indent=2)

    # 4. Nickname examples
    with open(OUTPUT_DIR / 'patterns_nicknames.json', 'w', encoding='utf-8') as f:
        json.dump(nicknames, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("PATTERN SUMMARY")
    print("=" * 60)

    print("\nGenitive Patterns Found:")
    for pattern_type, examples in genitive_patterns.items():
        print(f"  {pattern_type}: {len(examples)} examples")

    print("\nFirst Names by Ethnicity:")
    for eth, genders in sorted(first_names.items()):
        male_count = len(genders['male'])
        female_count = len(genders['female'])
        print(f"  {eth}: {male_count} male, {female_count} female")

    print(f"\nNickname Examples Found: {len(nicknames)}")
    if nicknames:
        print("  Examples:")
        for ex in nicknames[:5]:
            print(f"    {ex['first_name']} -> {ex['nickname']} ({ex['ethnicity']})")

    print("\nGenitive Detection Rules:")
    for rule in genitive_rules:
        print(f"\n  {rule['pattern']}:")
        print(f"    {rule['description']}")
        if rule.get('examples'):
            print(f"    Examples: {', '.join(rule['examples'][:5])}")

    print("\n" + "=" * 60)
    print("Output files:")
    print(f"  {OUTPUT_DIR / 'patterns_genitive_raw.json'}")
    print(f"  {OUTPUT_DIR / 'patterns_genitive_rules.json'}")
    print(f"  {OUTPUT_DIR / 'patterns_first_names.json'}")
    print(f"  {OUTPUT_DIR / 'patterns_nicknames.json'}")


if __name__ == "__main__":
    main()
