"""
The war's events each soldier was part of, for the line under the facts in his record dialog and memorial card
(lib/warEvents.ts; the user's decisions of 2026-10-30): one file per unit, website/data/events/<unit data file>,
soldier_id -> [WarEvent, ...] in the order they happened, which scripts/prepare-data.ts merges into the records.

  - igman: the Prva proleterska's column on Igman, 27-28 January 1942 (scripts/make_igman_list.py, build()).
  - sutjeska: the battle of the Sutjeska, May and June 1943: every man an entry of Viktor Kučan's Borci Sutjeske holds
    (borci-sutjeske-<unit>.pdf), his own, merged into his record, or his record's in another unit he is linked to.
    The book is the roll of everyone in the battle, so it is sure.

    python scripts/make_war_events.py           # after the units' records change (a merge, a link, a new unit);
                                                # it also writes those units' life events again (each event a step)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS           # noqa: E402
from cleanup_text_fields import live_json_files   # noqa: E402
import make_igman_list                            # noqa: E402
import extract_life_events                        # noqa: E402

OUT = ROOT / 'website' / 'data' / 'events'
SUTJESKA_BOOK = 'borci-sutjeske-'


def at_sutjeska(s: dict) -> bool:
    entries = [s] + list(s.get('other_sources') or [])
    return any((e.get('pdf_file') or '').startswith(SUTJESKA_BOOK) for e in entries)


def main():
    live = live_json_files()
    counts = Counter()
    written = set()
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        name = cfg['json_file']
        if name not in live:
            continue
        soldiers = json.loads((ROOT / 'website' / 'public' / name).read_text(encoding='utf-8'))
        events: dict[str, list[dict]] = {}
        if code == 1:
            for sid, e in make_igman_list.build(soldiers)[3].items():
                events.setdefault(sid, []).append(e)
                counts['igman'] += 1
        for s in soldiers:
            if at_sutjeska(s):
                events.setdefault(s['soldier_id'], []).append({'e': 'sutjeska', 'sure': True})
                counts['sutjeska'] += 1
        path = OUT / name
        had = path.exists()
        if events:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(events, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
            written.add(path.name)
        elif had:
            path.unlink()
        # each event is a step of the record's "Životni put": the unit's life events read again with them
        if events or had:
            extract_life_events._war_cache.pop(code, None)
            lines = extract_life_events.write_events({code: (name, soldiers)})
            counts['lines'] += lines.get(name, 0)
    print(f"igman {counts['igman']}, sutjeska {counts['sutjeska']}, in {len(written)} unit files ({OUT.relative_to(ROOT)}); "
          f"life lines rewritten for those units: {counts['lines']} soldiers")


if __name__ == '__main__':
    main()
