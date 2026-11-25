"""The census records that left their part before build_ostali_borci.py wrote redirects for them (2026-11-22): every
census record ID any commit's census parts held and today's don't, redirected to the record that holds the man's entry
now, in website/data/moved-ids.json. The builder keeps them from then on (census_redirects).

    python scripts/backfill_census_redirects.py            # dry run: counts and samples
    python scripts/backfill_census_redirects.py --write
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from name_utils import BRIGADE_CONFIGS, CENSUS_VOLUMES, OSTALI_CODES  # noqa: E402
from safe_write import write_text  # noqa: E402

ID = re.compile(rb'"soldier_id": "(\d{10})"')
PARTS = [f"website/public/{BRIGADE_CONFIGS[c]['json_file']}" for c in CENSUS_VOLUMES.values()]
MOVED = ROOT / 'website' / 'data' / 'moved-ids.json'


def git(*args: str) -> str:
    return subprocess.run(['git', *args], capture_output=True, cwd=ROOT).stdout.decode('utf-8')


def ever_committed() -> set[str]:
    """Every census record ID in any committed version of the census parts"""
    blobs = set()
    for line in git('log', '--format=%H', '--', *PARTS).split():
        for name in git('show', '--name-only', '--format=', line, '--', *PARTS).split():
            blob = git('rev-parse', f'{line}:{name}').strip()
            if blob and not blob.startswith(line):
                blobs.add(blob)
    out = set()
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=ROOT)
    for blob in sorted(blobs):
        proc.stdin.write(blob.encode() + b'\n')
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        if len(header) < 3:
            continue
        data = proc.stdout.read(int(header[2]) + 1)
        out |= {m.decode() for m in ID.findall(data)}
    proc.stdin.close()
    proc.wait()
    print(f'{len(blobs)} committed versions of the census parts, {len(out)} census record IDs in them')
    return out


def main():
    write = '--write' in sys.argv
    now = set()
    for p in PARTS:
        now |= {m.decode() for m in ID.findall((ROOT / p).read_bytes())}
    left = ever_committed() - now
    census_entry = {}
    for vol, code in CENSUS_VOLUMES.items():
        f = ROOT / 'data-extraction' / 'zrtve-rata' / f'zrtve-rata-1964-{vol}-entries.json'
        for e in json.loads(f.read_text(encoding='utf-8')):
            census_entry[f"{code:04d}{e['soldier_id'][4:]}"] = e['soldier_id']
    ostali = {f'{c:04d}' for c in OSTALI_CODES}
    holders = defaultdict(set)
    for c in json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8')):
        if c['action'] == 'reference' and c['soldier_id'][:4] not in ostali:
            holders[c['ref_id']].add(c['soldier_id'])
    present = set()                                       # every record on the site now
    for f in glob.glob(str(ROOT / 'website' / 'public' / '*.json')):
        if Path(f).name.split('-')[0] != 'ostali' or Path(f).name == 'ostali-borci.json':
            present |= {m.decode() for m in ID.findall(Path(f).read_bytes())}
    ids = json.loads((ROOT / 'data-extraction' / 'ostali_borci_ids.json').read_text(encoding='utf-8'))
    unit_ids = json.loads((ROOT / 'data-extraction' / 'unit_record_ids.json').read_text(encoding='utf-8'))
    on_site = ROOT / 'data-extraction' / '.cache' / 'ostali_on_site.json'
    with_of = {e['entry']: e['with'] for e in json.loads(on_site.read_text(encoding='utf-8'))} if on_site.exists() else {}

    def holder_of(e: str) -> str | None:              # as build_ostali_borci.py's
        held = sorted(r for r in holders.get(e, ()) if r in present)
        if held:
            return held[0]
        for rid in (unit_ids.get(e), ids.get(e)):
            if rid in present:
                return rid
        held = sorted(r for w in with_of.get(e, ()) for r in holders.get(w, ()) if r in present)
        return held[0] if held else None
    found, none = {}, []
    for rid in sorted(left):
        e = census_entry.get(rid)
        to = holder_of(e) if e else None
        if to:
            found[rid] = to
        else:
            none.append(rid)
    moved = json.loads(MOVED.read_text(encoding='utf-8'))
    new = {k: v for k, v in found.items() if moved.get(k) != v}
    print(f'{len(left)} census records have left their part; {len(found)} redirect ({len(new)} new), {len(none)} '
          f'have no record holding the entry: {none[:10]}')
    for k in list(new)[:8]:
        print('  ', k, '->', new[k])
    if write and new:
        write_text(MOVED, json.dumps({**moved, **new}, ensure_ascii=False, indent=0, sort_keys=True) + '\n')
        print('Written', MOVED)


if __name__ == '__main__':
    main()
