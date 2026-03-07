"""
Apply manual corrections to soldier JSON data files.

Reads corrections.json from the project root and applies edits, deletes,
and splits to the brigade JSON files in website/public/. Automatically
updates soldierCount in website/app/data/units.ts.

Designed to run as the LAST step before build, after normalize and
extract_pdf_positions, so corrections always win.

Usage:
    python scripts/apply_corrections.py              # dry run
    python scripts/apply_corrections.py --apply      # apply changes

Correction actions:
    edit   - Update fields on an existing soldier
    delete - Remove a soldier record
    split  - Replace one merged record with multiple new records
"""
import sys
import os
import json
import re
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add scripts dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from name_utils import BRIGADE_CONFIGS, extract_birth_info
from soldier_id_utils import generate_soldier_id, parse_soldier_id


def load_corrections(corrections_path):
    """Load and validate corrections from JSON file."""
    if not corrections_path.exists():
        print(f"  No corrections file found at {corrections_path}")
        return []

    with open(corrections_path, 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    if not corrections:
        print("  No corrections to apply.")
        return []

    # Validate each correction
    valid = []
    for i, c in enumerate(corrections):
        if 'action' not in c:
            print(f"  WARNING: Correction #{i} missing 'action', skipping")
            continue
        if c['action'] not in ('edit', 'delete', 'split'):
            print(f"  WARNING: Correction #{i} unknown action '{c['action']}', skipping")
            continue
        if 'soldier_id' not in c:
            print(f"  WARNING: Correction #{i} missing 'soldier_id', skipping")
            continue
        if c['action'] == 'split' and 'into' not in c:
            print(f"  WARNING: Correction #{i} split missing 'into', skipping")
            continue
        if c['action'] == 'edit' and 'fields' not in c:
            print(f"  WARNING: Correction #{i} edit missing 'fields', skipping")
            continue
        valid.append(c)

    return valid


def get_brigade_code_from_id(soldier_id):
    """Extract brigade code (int) from a 10-digit soldier ID."""
    return int(soldier_id[:4])


def get_json_path_for_brigade(brigade_code, public_dir):
    """Get the JSON file path for a brigade code."""
    config = BRIGADE_CONFIGS.get(brigade_code)
    if not config:
        return None
    return public_dir / config['json_file']


def get_next_sequence(soldiers, brigade_code):
    """Find the next available sequence number for a brigade."""
    prefix = f"{brigade_code:04d}"
    max_seq = 0
    for s in soldiers:
        sid = s.get('soldier_id', '')
        if sid.startswith(prefix) and len(sid) == 10:
            seq = int(sid[4:])
            if seq > max_seq:
                max_seq = seq
    return max_seq + 1


def rebuild_computed_fields(soldier):
    """Recalculate full_name and birth_year from other fields."""
    # Rebuild full_name
    parts = [soldier.get('last_name', '')]
    if soldier.get('middle_name'):
        parts.append(soldier['middle_name'])
    if soldier.get('first_name'):
        parts.append(soldier['first_name'])
    soldier['full_name'] = ' '.join(p for p in parts if p)

    # Rebuild birth_year from additional_info
    info = soldier.get('additional_info', '')
    if info:
        _, birth_year = extract_birth_info(info)
        if birth_year:
            soldier['birth_year'] = birth_year

    return soldier


def apply_edit(soldiers, correction):
    """Apply an edit correction. Returns (soldiers, applied)."""
    sid = correction['soldier_id']
    fields = correction['fields']

    for i, s in enumerate(soldiers):
        if s.get('soldier_id') == sid:
            reason = correction.get('reason', '')
            name_before = s.get('full_name', f"{s.get('last_name', '')} {s.get('first_name', '')}")

            for key, value in fields.items():
                s[key] = value

            s = rebuild_computed_fields(s)
            soldiers[i] = s

            name_after = s.get('full_name', '')
            print(f"    EDIT {sid}: {name_before} -> {name_after}")
            if reason:
                print(f"         Reason: {reason}")
            return soldiers, True

    print(f"    WARNING: Soldier {sid} not found for edit")
    return soldiers, False


def apply_delete(soldiers, correction):
    """Apply a delete correction. Returns (soldiers, applied)."""
    sid = correction['soldier_id']
    reason = correction.get('reason', '')

    for i, s in enumerate(soldiers):
        if s.get('soldier_id') == sid:
            name = s.get('full_name', f"{s.get('last_name', '')} {s.get('first_name', '')}")
            soldiers.pop(i)
            print(f"    DELETE {sid}: {name}")
            if reason:
                print(f"         Reason: {reason}")
            return soldiers, True

    print(f"    WARNING: Soldier {sid} not found for delete")
    return soldiers, False


def apply_split(soldiers, correction):
    """Apply a split correction. Returns (soldiers, applied, new_count)."""
    sid = correction['soldier_id']
    into = correction['into']
    reason = correction.get('reason', '')
    brigade_code = get_brigade_code_from_id(sid)

    # Find the soldier to split
    target_idx = None
    for i, s in enumerate(soldiers):
        if s.get('soldier_id') == sid:
            target_idx = i
            break

    if target_idx is None:
        print(f"    WARNING: Soldier {sid} not found for split")
        return soldiers, False, 0

    original = soldiers[target_idx]
    original_name = original.get('full_name', f"{original.get('last_name', '')} {original.get('first_name', '')}")

    # Copy PDF position from original to all new records
    pdf_fields = {}
    for key in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_file'):
        if key in original:
            pdf_fields[key] = original[key]

    # Generate new records
    next_seq = get_next_sequence(soldiers, brigade_code)
    new_records = []

    for j, entry in enumerate(into):
        new_soldier = {
            'soldier_id': generate_soldier_id(brigade_code, next_seq + j),
            'last_name': entry.get('last_name', ''),
            'middle_name': entry.get('middle_name', ''),
            'first_name': entry.get('first_name', ''),
            'fathers_name': entry.get('fathers_name', ''),
            'full_name': '',
            'additional_info': entry.get('additional_info', ''),
            'birth_year': '',
        }
        # Copy PDF position from original
        new_soldier.update(pdf_fields)
        # Override PDF fields if specified in the correction
        for key in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_file'):
            if key in entry:
                new_soldier[key] = entry[key]

        new_soldier = rebuild_computed_fields(new_soldier)
        new_records.append(new_soldier)

    # Replace original with new records
    soldiers[target_idx:target_idx + 1] = new_records

    new_names = [r.get('full_name', '') for r in new_records]
    print(f"    SPLIT {sid}: {original_name} -> {', '.join(new_names)}")
    if reason:
        print(f"         Reason: {reason}")

    # Net change in soldier count (new records minus the one removed)
    return soldiers, True, len(new_records) - 1


def update_units_ts(units_ts_path, count_updates):
    """Update soldierCount values in units.ts.

    units.ts format per brigade block:
        soldierCount: 3172,
        dataFile: '/ljubljanska-soldiers.json',
    """
    if not count_updates:
        return

    with open(units_ts_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for brigade_code, new_count in count_updates.items():
        config = BRIGADE_CONFIGS.get(brigade_code)
        if not config:
            continue
        json_file = config['json_file']

        # Pattern: soldierCount number on line before dataFile reference
        pattern = rf"(soldierCount:\s*)\d+(,\s*\n\s*dataFile:\s*'/{re.escape(json_file)}')"
        content = re.sub(pattern, rf"\g<1>{new_count}\g<2>", content)

    with open(units_ts_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description='Apply corrections to soldier JSON data')
    parser.add_argument('--apply', action='store_true',
                        help='Actually write changes (default: dry run)')
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    corrections_path = project_root / 'corrections.json'
    public_dir = project_root / 'website' / 'public'
    units_ts_path = project_root / 'website' / 'app' / 'data' / 'units.ts'

    if not args.apply:
        print("\n  *** DRY RUN - no files will be modified ***")
        print("  Use --apply to write changes\n")

    print("Loading corrections...")
    corrections = load_corrections(corrections_path)
    if not corrections:
        return

    print(f"Found {len(corrections)} correction(s)\n")

    # Group corrections by brigade
    by_brigade = {}
    for c in corrections:
        brigade_code = get_brigade_code_from_id(c['soldier_id'])
        by_brigade.setdefault(brigade_code, []).append(c)

    # Track count changes for units.ts
    count_updates = {}  # brigade_code -> new_count
    total_applied = 0
    total_skipped = 0

    # Process each brigade
    for brigade_code, brigade_corrections in sorted(by_brigade.items()):
        config = BRIGADE_CONFIGS.get(brigade_code)
        brigade_name = config['name'] if config else f"Brigade {brigade_code}"
        json_path = get_json_path_for_brigade(brigade_code, public_dir)

        if not json_path or not json_path.exists():
            print(f"\n  WARNING: JSON file not found for brigade {brigade_code}")
            total_skipped += len(brigade_corrections)
            continue

        print(f"\n  {brigade_name} ({json_path.name}):")

        with open(json_path, 'r', encoding='utf-8') as f:
            soldiers = json.load(f)
        original_count = len(soldiers)

        applied_count = 0
        for c in brigade_corrections:
            action = c['action']

            if action == 'edit':
                soldiers, applied = apply_edit(soldiers, c)
            elif action == 'delete':
                soldiers, applied = apply_delete(soldiers, c)
            elif action == 'split':
                soldiers, applied, _ = apply_split(soldiers, c)
            else:
                applied = False

            if applied:
                applied_count += 1
            else:
                total_skipped += 1

        total_applied += applied_count
        new_count = len(soldiers)

        if new_count != original_count:
            count_updates[brigade_code] = new_count
            print(f"    Count: {original_count} -> {new_count} ({new_count - original_count:+d})")

        if args.apply and applied_count > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(soldiers, f, ensure_ascii=False, indent=2)
            print(f"    Written: {json_path}")

    # Update units.ts counts
    if args.apply and count_updates:
        print(f"\n  Updating units.ts soldier counts...")
        update_units_ts(units_ts_path, count_updates)
        for bc, nc in count_updates.items():
            name = BRIGADE_CONFIGS.get(bc, {}).get('name', f'Brigade {bc}')
            print(f"    {name}: soldierCount -> {nc}")

    # Summary
    print(f"\n{'='*50}")
    print(f"  Applied: {total_applied}")
    print(f"  Skipped: {total_skipped}")
    if count_updates:
        print(f"  Counts updated: {len(count_updates)} brigade(s)")
    print(f"{'='*50}")

    if not args.apply and total_applied > 0:
        print(f"\n  *** DRY RUN complete. Use --apply to write changes ***")


if __name__ == '__main__':
    main()
