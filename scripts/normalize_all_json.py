"""
Normalize all brigade JSON files in website/public/.

Applies unified name cleaning, casing normalization, name splitting,
and genitive→nominative conversion. Produces:

1. Corrected JSON files (overwritten in-place)
2. A detailed quality report (printed + saved to 01-data/processed/)
3. An issues file listing all records with problems

Usage:
    python scripts/normalize_all_json.py              # dry run (report only)
    python scripts/normalize_all_json.py --apply       # apply changes
    python scripts/normalize_all_json.py --apply --backup  # apply + keep .bak files

Designed for extensibility: to add a new brigade, just:
1. Add it to BRIGADE_CONFIGS in name_utils.py
2. Place its JSON in website/public/
3. Re-run this script
"""

import sys
import os
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add scripts dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from name_utils import (
    BRIGADE_CONFIGS,
    normalize_soldier,
    validate_soldier,
    extract_birth_info,
    to_title_case,
)


def get_brigade_code_from_id(soldier_id):
    """Extract brigade code from a 10-digit soldier ID."""
    if soldier_id and len(soldier_id) == 10 and soldier_id.isdigit():
        return int(soldier_id[:4])
    return None


def process_brigade(json_path, brigade_code, config):
    """
    Process all soldiers in a brigade JSON file.

    Returns:
        (normalized_soldiers, stats_dict, issues_list)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    stats = {
        'total': len(soldiers),
        'names_changed': 0,
        'first_name_split': 0,
        'casing_fixed': 0,
        'fields_cleaned': 0,
        'fathers_name_converted': 0,
        'birth_year_extracted': 0,
        'issues_by_type': {},
        'issue_records': 0,
    }

    all_issues = []
    normalized = []

    for i, soldier in enumerate(soldiers):
        original = dict(soldier)

        # Normalize
        result = normalize_soldier(soldier, brigade_code)

        # Extract birth info if not already present
        additional_info = result.get('additional_info', '')
        if additional_info and not result.get('birth_year'):
            dob, birth_year = extract_birth_info(additional_info)
            if birth_year:
                result['birth_year'] = birth_year
                stats['birth_year_extracted'] += 1

        # Track what changed
        if original.get('last_name', '') != result.get('last_name', ''):
            stats['names_changed'] += 1
            # Determine type of change
            orig_ln = original.get('last_name', '')
            if orig_ln and orig_ln.isupper() and not result['last_name'].isupper():
                stats['casing_fixed'] += 1
        if original.get('first_name', '') != result.get('first_name', ''):
            stats['names_changed'] += 1
            if len(original.get('first_name', '').split()) > len(result.get('first_name', '').split()):
                stats['first_name_split'] += 1
        if result.get('fathers_name') and result.get('fathers_name') != result.get('middle_name'):
            stats['fathers_name_converted'] += 1

        # Validate
        issues = validate_soldier(result)
        if issues:
            stats['issue_records'] += 1
            for issue in issues:
                stats['issues_by_type'][issue] = stats['issues_by_type'].get(issue, 0) + 1
            all_issues.append({
                'soldier_id': result.get('soldier_id', f'row_{i}'),
                'original': {
                    'last_name': original.get('last_name', ''),
                    'first_name': original.get('first_name', ''),
                    'middle_name': original.get('middle_name', ''),
                },
                'normalized': {
                    'last_name': result.get('last_name', ''),
                    'first_name': result.get('first_name', ''),
                    'middle_name': result.get('middle_name', ''),
                    'fathers_name': result.get('fathers_name', ''),
                },
                'issues': issues,
            })

        normalized.append(result)

    return normalized, stats, all_issues


def print_report(brigade_name, stats):
    """Print a formatted report for one brigade."""
    total = stats['total']
    print(f"\n{'='*60}")
    print(f"  {brigade_name}")
    print(f"  {total:,} soldiers")
    print(f"{'='*60}")

    print(f"\n  Changes applied:")
    print(f"    Names changed (casing/cleaning):  {stats['names_changed']:,}")
    print(f"    Casing fixes (CAPS → Title):      {stats['casing_fixed']:,}")
    print(f"    First names split (merged→split):  {stats['first_name_split']:,}")
    print(f"    Father's names converted (gen→nom): {stats['fathers_name_converted']:,}")
    print(f"    Birth years extracted:              {stats['birth_year_extracted']:,}")

    if stats['issues_by_type']:
        print(f"\n  Remaining issues ({stats['issue_records']:,} records):")
        for issue, count in sorted(stats['issues_by_type'].items(), key=lambda x: -x[1]):
            pct = count / total * 100
            print(f"    {issue:40s} {count:5,} ({pct:.1f}%)")
    else:
        print(f"\n  No issues detected!")


def main():
    parser = argparse.ArgumentParser(description='Normalize all brigade JSON files')
    parser.add_argument('--apply', action='store_true',
                        help='Actually write changes (default: dry run)')
    parser.add_argument('--backup', action='store_true',
                        help='Create .bak files before overwriting')
    parser.add_argument('--brigade', type=int, default=None,
                        help='Only process a specific brigade code')
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    public_dir = project_root / 'website' / 'public'
    output_dir = project_root / '01-data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.apply:
        print("\n  *** DRY RUN - no files will be modified ***")
        print("  Use --apply to write changes\n")

    all_stats = {}
    all_issues = []
    total_soldiers = 0
    total_changes = 0

    # Process each brigade
    for code, config in sorted(BRIGADE_CONFIGS.items()):
        if args.brigade and code != args.brigade:
            continue

        json_file = public_dir / config['json_file']
        if not json_file.exists():
            print(f"\n  WARNING: {json_file} not found, skipping {config['name']}")
            continue

        print(f"\n  Processing {config['name']}...")

        normalized, stats, issues = process_brigade(json_file, code, config)

        # Print report
        print_report(config['name'], stats)
        all_stats[config['name']] = stats
        all_issues.extend(issues)
        total_soldiers += stats['total']
        total_changes += stats['names_changed']

        # Write if --apply
        if args.apply:
            if args.backup:
                backup_path = json_file.with_suffix('.json.bak')
                shutil.copy2(json_file, backup_path)
                print(f"\n  Backup: {backup_path}")

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(normalized, f, ensure_ascii=False, indent=2)
            print(f"  Written: {json_file}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total soldiers:     {total_soldiers:,}")
    print(f"  Total name changes: {total_changes:,}")
    print(f"  Total with issues:  {len(all_issues):,}")

    # Aggregate issues across brigades
    global_issues = {}
    for issue_rec in all_issues:
        for issue in issue_rec['issues']:
            global_issues[issue] = global_issues.get(issue, 0) + 1

    if global_issues:
        print(f"\n  Global issue breakdown:")
        for issue, count in sorted(global_issues.items(), key=lambda x: -x[1]):
            print(f"    {issue:40s} {count:5,}")

    # Save issues report
    issues_file = output_dir / f'normalization_issues_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    report = {
        'generated_at': datetime.now().isoformat(),
        'dry_run': not args.apply,
        'stats_by_brigade': all_stats,
        'global_issue_counts': global_issues,
        'issue_records': all_issues,
    }
    with open(issues_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Issues report: {issues_file}")

    if not args.apply:
        print(f"\n  *** DRY RUN complete. Use --apply to write changes ***")


if __name__ == '__main__':
    main()
