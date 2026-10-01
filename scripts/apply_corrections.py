"""
Apply manual corrections to soldier JSON data files.

Reads corrections.json from the project root and applies edits, deletes,
and splits to the brigade JSON files in website/public/. Automatically
updates soldierCount in website/app/data/units.ts.

Designed to run as the LAST step before build, after normalize and
extract_pdf_positions, so corrections always win.

Afterwards, empty structured fields (birth_place, death_date, rank, ...) are read
from each record's additional_info (scripts/extract_structured_fields.py). When a
correction rewrites additional_info, values that had been read from the old text
are dropped and read again from the new one; values set by corrections stay.

Last, every unit on the site gets its entries' highlight boxes (pdf_x_end,
pdf_y_end, pdf_x_left) recomputed from the PDFs by data-extraction/entry_boxes.py,
so they follow the final positions. Those fields are always computed: a value a
correction sets for them is overwritten.

Usage:
    python scripts/apply_corrections.py              # dry run
    python scripts/apply_corrections.py --apply      # apply changes

Correction actions:
    edit   - Update fields on an existing soldier
    delete - Remove a soldier record
    split  - Replace one merged record with multiple new records
    add    - Insert a soldier the parser missed, after the record `soldier_id`,
             under the fixed id `new_id`. Once that id exists the record is not
             inserted again, but it gets back the fields the correction sets
             (except those a later edit sets), so normalize_all_json.py cannot
             undo them.
    merge  - `merge_id` is the same soldier as `soldier_id`, from another book
             of the unit (or another list in the same book): its entry moves
             into soldier_id's `other_sources` (printed name, text, place on
             the page), fields soldier_id lacks are taken from it, and the
             record merge_id is removed. `merge_name` (merge_id's full_name)
             guards against a re-parse that gave the id to someone else.
    link   - `link_id` is the same soldier as `soldier_id`, in another unit's
             book: both records stay in their units, each gets the other's
             entries in other_sources (marked with unit_file) and the fields
             it lacks (apply_links; `link_name` guards like merge_name).
"""
import sys
import os
import json
import re
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add scripts dir for imports (and data-extraction, for entry_boxes; at module
# level so entry_boxes' worker processes can import it too)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data-extraction'))

from name_utils import BRIGADE_CONFIGS, extract_birth_info
from soldier_id_utils import generate_soldier_id, parse_soldier_id
import extract_structured_fields as structured
import feminine_alias
import entry_boxes

POSITION_FIELDS = ('pdf_file', 'pdf_page', 'pdf_x', 'pdf_y')


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
        if c['action'] not in ('edit', 'delete', 'split', 'add', 'merge', 'link'):
            print(f"  WARNING: Correction #{i} unknown action '{c['action']}', skipping")
            continue
        if c['action'] == 'add' and ('record' not in c or 'new_id' not in c):
            print(f"  WARNING: Correction #{i} add missing 'record' or 'new_id', skipping")
            continue
        if 'soldier_id' not in c:
            print(f"  WARNING: Correction #{i} missing 'soldier_id', skipping")
            continue
        if c['action'] == 'split' and 'into' not in c:
            print(f"  WARNING: Correction #{i} split missing 'into', skipping")
            continue
        if c['action'] == 'link' and 'link_id' not in c:
            print(f"  WARNING: Correction #{i} link missing 'link_id', skipping")
            continue
        if c['action'] == 'merge' and 'merge_id' not in c:
            print(f"  WARNING: Correction #{i} merge missing 'merge_id', skipping")
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


def rebuild_computed_fields(soldier, skip_birth_year=False):
    """Recalculate full_name and birth_year from other fields."""
    # Rebuild full_name
    parts = [soldier.get('last_name', '')]
    if soldier.get('middle_name'):
        parts.append(soldier['middle_name'])
    if soldier.get('first_name'):
        parts.append(soldier['first_name'])
    soldier['full_name'] = ' '.join(p for p in parts if p)

    # Rebuild birth_year from additional_info (unless correction explicitly set it)
    if not skip_birth_year:
        info = soldier.get('additional_info', '')
        if info:
            _, birth_year = extract_birth_info(info)
            if birth_year:
                soldier['birth_year'] = birth_year

    return soldier


MANUAL_FIELDS = {}   # soldier_id -> structured fields some correction sets explicitly
EDITED_FIELDS = {}   # soldier_id -> fields some edit correction sets
DELETED = {}         # soldier_id -> the record a delete correction removed in this run
MERGED_IDS = set()   # ids a merge correction folds into another record: their earlier edits are done (after a re-parse
                     # they apply before the merge), so a later run finds nothing to edit and that is fine


def apply_edit(soldiers, correction):
    """Apply an edit correction. Returns (soldiers, applied)."""
    sid = correction['soldier_id']
    fields = correction['fields']

    for i, s in enumerate(soldiers):
        if s.get('soldier_id') == sid:
            reason = correction.get('reason', '')
            name_before = s.get('full_name', f"{s.get('last_name', '')} {s.get('first_name', '')}")
            old_info = s.get('additional_info', '')

            if any(k in fields for k in POSITION_FIELDS):
                # the old box belongs to the old position; entry_boxes draws the new one
                for k in entry_boxes.BOX_FIELDS:
                    s.pop(k, None)
            for key, value in fields.items():
                s[key] = value
            if 'additional_info' in fields and fields['additional_info'] != old_info:
                # re-read from the new text below; fields any correction sets for this soldier stay
                structured.forget_stale(s, old_info, keep=MANUAL_FIELDS.get(sid, set()) | set(fields))

            # Skip birth_year rebuild if correction explicitly sets it
            skip_birth_year = 'birth_year' in fields
            s = rebuild_computed_fields(s, skip_birth_year=skip_birth_year)
            soldiers[i] = s

            name_after = s.get('full_name', '')
            print(f"    EDIT {sid}: {name_before} -> {name_after}")
            if reason:
                print(f"         Reason: {reason}")
            return soldiers, True

    if sid in MERGED_IDS:
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
            DELETED[sid] = soldiers.pop(i)
            print(f"    DELETE {sid}: {name}")
            if reason:
                print(f"         Reason: {reason}")
            return soldiers, True

    print(f"    WARNING: Soldier {sid} not found for delete")
    return soldiers, False


SOURCE_FIELDS = ('pdf_file', 'pdf_page', 'pdf_x', 'pdf_y') + entry_boxes.BOX_FIELDS + ('source_url',)
# what the soldier's entry takes from another book's entry when its own is empty
MERGE_FILL = ('middle_name', 'fathers_name', 'birth_year') + tuple(structured.FIELDS)


def apply_merge(soldiers, correction):
    """Apply a merge correction: `merge_id` is the same soldier as `soldier_id`, read from another book (or another
    list in the same book). Its entry becomes one of soldier_id's other_sources (the printed name, the text and its
    place on the page), fields soldier_id lacks are taken from it, and the record merge_id is removed.
    Returns (soldiers, applied); once merged, re-applying finds the source already there."""
    sid, mid = correction['soldier_id'], correction['merge_id']
    keep = next((s for s in soldiers if s.get('soldier_id') == sid), None)
    gone = next((s for s in soldiers if s.get('soldier_id') == mid), None)
    if keep is None:
        print(f"    WARNING: Soldier {sid} not found for merge")
        return soldiers, False
    if gone is None:
        if any(o.get('soldier_id') == mid for o in keep.get('other_sources', ())):
            return soldiers, True
        print(f"    WARNING: Soldier {mid} not found for merge into {sid}")
        return soldiers, False
    expect = correction.get('merge_name')
    if expect and gone.get('full_name') != expect:
        # a re-parse gave the id to someone else: the correction must be checked, not applied blindly
        print(f"    WARNING: {mid} is {gone.get('full_name')!r}, not {expect!r}; merge into {sid} skipped")
        return soldiers, False

    source = {'soldier_id': mid, 'name': gone.get('full_name', ''), 'additional_info': gone.get('additional_info', '')}
    source.update({k: gone[k] for k in SOURCE_FIELDS if gone.get(k) not in (None, '')})
    others = [o for o in keep.get('other_sources', ()) if o.get('soldier_id') != mid]
    # a soldier merged into `gone` earlier comes along
    others += [o for o in gone.get('other_sources', ()) if o.get('soldier_id') != sid]
    keep['other_sources'] = others + [source]
    taken = [k for k in MERGE_FILL if not keep.get(k) and gone.get(k)]
    if 'middle_name' in taken and 'fathers_name' not in taken:
        taken.append('fathers_name')                   # the father comes as a pair: as printed, and nominative
    for k in taken:
        keep[k] = gone[k]
    rebuild_computed_fields(keep, skip_birth_year=True)
    soldiers = [s for s in soldiers if s is not gone]
    print(f"    MERGE {mid} into {sid}: {gone.get('full_name')} -> {keep.get('full_name')}"
          + (f" (took {', '.join(taken)})" if taken else ''))
    if correction.get('reason'):
        print(f"         Reason: {correction['reason']}")
    return soldiers, True


def apply_links(links, units):
    """The same soldier in two units' books: each record keeps its place in its own unit and gets the other units'
    entries in other_sources (with unit_file, the other unit's data file; that record's own merged entries come
    along), and fields it lacks are filled from them. Linked records form groups (a soldier in three units). The
    linked entries are rebuilt on every run. units: {code: soldiers}, changed in place.
    Returns how many links were applied."""
    by_id = {s['soldier_id']: (code, s) for code, soldiers in units.items() for s in soldiers}
    for soldiers in units.values():
        for s in soldiers:
            if any(o.get('unit_file') for o in s.get('other_sources', ())):
                s['other_sources'] = [o for o in s['other_sources'] if not o.get('unit_file')]
                if not s['other_sources']:
                    del s['other_sources']
    parent = {}

    def root(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x

    applied = 0
    for c in links:
        a, b = by_id.get(c['soldier_id']), by_id.get(c['link_id'])
        if a is None or b is None:
            print(f"    WARNING: link {c['soldier_id']} - {c['link_id']}: "
                  f"{c['soldier_id'] if a is None else c['link_id']} not found")
            continue
        name = c.get('link_name') or ''
        rec = b[1]
        # the father may have been filled in from the other record since: surname and given name decide
        if name and rec.get('full_name') != name and not (name.startswith(rec.get('last_name') or '\0')
                                                         and name.endswith(rec.get('first_name') or '\0')):
            print(f"    WARNING: {c['link_id']} is {b[1].get('full_name')!r}, not {c['link_name']!r}; link skipped")
            continue
        parent[root(c['soldier_id'])] = root(c['link_id'])
        applied += 1
    groups = {}
    for sid in list(parent):
        groups.setdefault(root(sid), set()).add(sid)
    for members in groups.values():
        members |= {root(next(iter(members)))}
        recs = sorted((by_id[m] for m in members), key=lambda cs: cs[1]['soldier_id'])
        for code, s in recs:
            linked = []
            for other_code, o in recs:
                if o is s:
                    continue
                unit_file = BRIGADE_CONFIGS[other_code]['json_file']
                entry = {'soldier_id': o['soldier_id'], 'name': o.get('full_name', ''), 'additional_info': o.get('additional_info', '')}
                entry.update({k: o[k] for k in SOURCE_FIELDS if o.get(k) not in (None, '')})
                linked.append({**entry, 'unit_file': unit_file})
                linked += [{**e, 'unit_file': unit_file} for e in o.get('other_sources', ()) if not e.get('unit_file')]
                for k in MERGE_FILL:
                    if not s.get(k) and o.get(k):
                        s[k] = o[k]
            s['other_sources'] = s.get('other_sources', []) + linked
            rebuild_computed_fields(s, skip_birth_year=True)
    return applied


def restore_added(soldier, correction):
    """An added soldier that exists already gets back the fields its correction sets, so that the correction wins
    over the pipeline for it as an edit does ("(...)kolić" is not cleaned, "Stevo" not reset). Returns True when a
    field changed."""
    sid = soldier['soldier_id']
    fields = {k: v for k, v in correction['record'].items()
              if k not in entry_boxes.BOX_FIELDS and k not in EDITED_FIELDS.get(sid, ())}   # a later edit wins
    changed = {k for k, v in fields.items() if soldier.get(k) != v}
    if not changed:
        return False
    old_info = soldier.get('additional_info', '')
    if changed & set(POSITION_FIELDS):
        for k in entry_boxes.BOX_FIELDS:
            soldier.pop(k, None)
    soldier.update(fields)
    if 'additional_info' in changed:
        structured.forget_stale(soldier, old_info, keep=MANUAL_FIELDS.get(sid, set()) | set(fields))
    rebuild_computed_fields(soldier, skip_birth_year='birth_year' in fields)
    print(f"    RESTORE {sid}: {soldier['full_name']} ({', '.join(sorted(changed))})")
    return True


def apply_add(soldiers, correction):
    """Apply an add correction. Returns (soldiers, applied). Once new_id exists the add is not applied again, but
    the record gets back the fields the correction sets (restore_added)."""
    new_id = correction['new_id']
    existing = next((s for s in soldiers if s.get('soldier_id') == new_id), None)
    if existing is not None:
        restore_added(existing, correction)
        return soldiers, False

    record = {'soldier_id': new_id, 'last_name': '', 'middle_name': '', 'first_name': '', 'fathers_name': '',
              'full_name': '', 'additional_info': '', 'birth_year': ''}
    record.update(correction['record'])
    record = rebuild_computed_fields(record, skip_birth_year='birth_year' in correction['record'])
    # an id deleted earlier in this run and added again (a parse error's id reused for a missing soldier): the
    # entries of other books merged into it stay with it
    before = DELETED.pop(new_id, None)
    if before and before.get('other_sources'):
        record['other_sources'] = before['other_sources']

    anchor = next((i for i, s in enumerate(soldiers) if s.get('soldier_id') == correction['soldier_id']), len(soldiers) - 1)
    soldiers.insert(anchor + 1, record)
    print(f"    ADD {new_id}: {record['full_name']}")
    if correction.get('reason'):
        print(f"         Reason: {correction['reason']}")
    return soldiers, True


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

    standard_keys = {'last_name', 'middle_name', 'first_name', 'fathers_name',
                      'full_name', 'additional_info', 'birth_year',
                      'pdf_page', 'pdf_y', 'pdf_x', 'pdf_file'}

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
        # Copy extra structured fields (birth_place, ethnicity, etc.)
        for key, val in entry.items():
            if key not in standard_keys and key not in new_soldier:
                new_soldier[key] = val

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

    Returns {brigade_code: (old, new)} for the counts that changed.
    """
    changed = {}
    if not count_updates:
        return changed

    with open(units_ts_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for brigade_code, new_count in count_updates.items():
        config = BRIGADE_CONFIGS.get(brigade_code)
        if not config:
            continue
        json_file = config['json_file']

        # Pattern: soldierCount number on line before dataFile reference
        pattern = rf"(soldierCount:\s*)(\d+)(,\s*\n\s*dataFile:\s*'/{re.escape(json_file)}')"
        m = re.search(pattern, content)
        if m and int(m.group(2)) != new_count:
            changed[brigade_code] = (int(m.group(2)), new_count)
            content = re.sub(pattern, rf"\g<1>{new_count}\g<3>", content)

    if changed:
        with open(units_ts_path, 'w', encoding='utf-8') as f:
            f.write(content)
    return changed


def main():
    parser = argparse.ArgumentParser(description='Apply corrections to soldier JSON data')
    parser.add_argument('--apply', action='store_true',
                        help='Actually write changes (default: dry run)')
    parser.add_argument('--brigade', type=int,
                        help='Only this unit (default: every unit with corrections and every unit on the site)')
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
    print(f"Found {len(corrections)} correction(s)\n")

    for c in corrections:
        set_fields = set(c.get('fields', {})) | set(c.get('record', {}))
        MANUAL_FIELDS.setdefault(c.get('new_id') or c['soldier_id'], set()).update(set_fields & set(structured.FIELDS))
        if c['action'] == 'edit':
            EDITED_FIELDS.setdefault(c['soldier_id'], set()).update(c['fields'])
        elif c['action'] == 'merge':
            MERGED_IDS.add(c['merge_id'])

    links = [c for c in corrections if c['action'] == 'link']
    corrections = [c for c in corrections if c['action'] != 'link']

    # Group corrections by brigade
    by_brigade = {}
    for c in corrections:
        brigade_code = get_brigade_code_from_id(c['soldier_id'])
        by_brigade.setdefault(brigade_code, []).append(c)

    live_files = structured.live_json_files()   # brigades on the site (preview-only brigades are left alone)
    # which given names are women's, read from every unit's bios (feminine_alias)
    names = feminine_alias.name_genders([s for _, d in structured.load_live().values() for s in d])

    live_codes = {code for code, cfg in BRIGADE_CONFIGS.items() if cfg['json_file'] in live_files}
    box_cache = entry_boxes.PageCache()

    # Track count changes for units.ts
    count_updates = {}  # brigade_code -> new_count
    total_applied = 0
    total_skipped = 0

    results = {}         # brigade_code -> (json_path, original_text, soldiers), written after the link pass

    # Process each brigade with corrections, and every brigade on the site (entry boxes)
    codes = [args.brigade] if args.brigade else sorted(set(by_brigade) | live_codes)
    for brigade_code in codes:
        brigade_corrections = by_brigade.get(brigade_code, [])
        config = BRIGADE_CONFIGS.get(brigade_code)
        brigade_name = config['name'] if config else f"Brigade {brigade_code}"
        json_path = get_json_path_for_brigade(brigade_code, public_dir)

        if not json_path or not json_path.exists():
            print(f"\n  WARNING: JSON file not found for brigade {brigade_code}")
            total_skipped += len(brigade_corrections)
            continue

        print(f"\n  {brigade_name} ({json_path.name}):")

        with open(json_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
        soldiers = json.loads(original_text)
        original_count = len(soldiers)
        original_boxes = entry_boxes.box_snapshot(soldiers)

        applied_count = 0
        for c in brigade_corrections:
            action = c['action']

            if action == 'edit':
                soldiers, applied = apply_edit(soldiers, c)
            elif action == 'delete':
                soldiers, applied = apply_delete(soldiers, c)
            elif action == 'split':
                soldiers, applied, _ = apply_split(soldiers, c)
            elif action == 'add':
                soldiers, applied = apply_add(soldiers, c)
            elif action == 'merge':
                soldiers, applied = apply_merge(soldiers, c)
            else:
                applied = False

            if applied:
                applied_count += 1
            else:
                total_skipped += 1

        total_applied += applied_count
        new_count = len(soldiers)

        if json_path.name in live_files:
            women = feminine_alias.apply(soldiers, names)
            if women:
                print(f"    Women's nicknames: 'zvana' in {women} record(s)")

        if applied_count > 0 and json_path.name in live_files:
            filled = structured.fill(soldiers)
            if filled:
                print(f"    Structured fields read from the bio for {filled} record(s)")

        # units.ts follows the file, also when a re-parse (not a correction) changed its size
        count_updates[brigade_code] = new_count
        if new_count != original_count:
            print(f"    Count: {original_count} -> {new_count} ({new_count - original_count:+d})")

        if json_path.name in live_files:
            box_stats = entry_boxes.fill_boxes(soldiers, box_cache)
            changed = sum(1 for sid, box in entry_boxes.box_snapshot(soldiers).items()
                          if original_boxes.get(sid) != box)
            print(f"    Entry boxes: {entry_boxes.describe(box_stats, changed)}")

        results[brigade_code] = (json_path, original_text, soldiers)

    box_cache.save()

    # The same soldier in two units (links): every unit file is read, the processed ones from this run
    if links:
        units = {code: res[2] for code, res in results.items()}
        for code, cfg in BRIGADE_CONFIGS.items():
            path = public_dir / cfg['json_file']
            if code not in units and cfg['json_file'] in live_files and path.exists():
                units[code] = json.loads(path.read_text(encoding='utf-8'))
        n = apply_links(links, units)
        print(f"\n  Links between units: {n} applied")
        total_applied += n
        total_skipped += len(links) - n

    for brigade_code, (json_path, original_text, soldiers) in results.items():
        new_text = json.dumps(soldiers, ensure_ascii=False, indent=2)
        if args.apply and new_text != original_text:
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(new_text)
            print(f"    Written: {json_path}")

    # Update units.ts counts
    changed = {}
    if args.apply and count_updates:
        changed = update_units_ts(units_ts_path, count_updates)
        if changed:
            print(f"\n  Updated units.ts soldier counts:")
        for bc, (oc, nc) in changed.items():
            name = BRIGADE_CONFIGS.get(bc, {}).get('name', f'Brigade {bc}')
            print(f"    {name}: soldierCount {oc} -> {nc}")

    # Summary
    print(f"\n{'='*50}")
    print(f"  Applied: {total_applied}")
    print(f"  Skipped: {total_skipped}")
    if changed:
        print(f"  Counts updated: {len(changed)} brigade(s)")
    print(f"{'='*50}")

    if not args.apply and total_applied > 0:
        print(f"\n  *** DRY RUN complete. Use --apply to write changes ***")


if __name__ == '__main__':
    main()
