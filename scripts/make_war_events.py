"""
The war's events each soldier was part of, for the line under the facts in his record dialog and memorial card
(lib/warEvents.ts; the user's decisions of 2026-10-30): one file per unit, website/data/events/<unit data file>,
soldier_id -> [WarEvent, ...] in the order they happened, which scripts/prepare-data.ts merges into the records.

  - igman: the Prva proleterska's column on Igman, 27-28 January 1942 (scripts/make_igman_list.py, build()).
  - neretva: the battle of the Neretva, February and March 1943: every man an entry of whose says he was in it (NERETVA).
  - kozara (June-July 1942), drvar (the raid of 25 May 1944), beograd (its liberation, October 1944), srem (the Srem
    front, October 1944 - April 1945), trst (the fighting for Trieste, April-May 1945): the same, by TEXT_EVENTS.
  - sutjeska: the battle of the Sutjeska, May and June 1943: every man an entry of Viktor Kučan's Borci Sutjeske holds
    (borci-sutjeske-<unit>.pdf), his own, merged into his record, or his record's in another unit he is linked to.
    The book is the roll of everyone in the battle, so it is sure.

    python scripts/make_war_events.py           # after the units' records change (a merge, a link, a new unit);
                                                # it also writes those units' life events again (each event a step)
"""
from __future__ import annotations
from safe_write import write_text

import json
import re
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


# a family's account that he fought at the Sutjeska (Porodična arhiva, the record's own entry or a reference): what a
# family tells of the war goes into the card's line (the user, 2026-11-23, Divljak Živko: "dodati ucesnik bitke na
# sutjesci u zivotni put, uvesti to pravilo od porodicnih feedbackova")
FAMILY_SUTJESKA = re.compile(r'\b(?:bitk|bic|bitc|borb)\w*\s+na\s+(?:\w+\s+i\s+)?Sutjesc', re.I)


# the battle of the Neretva, February and March 1943 (the user, 2026-11-24, Žujić-Torbica Zora: "add bitka na neretvi
# just like we have for sutjeska igmanski mars"): an entry of his that says he was in it, a family's account or a
# book's ("Učestvovala u bici na Neretvi", "učesnik bitke na Neretvi", "u bitkama na Neretvi i Sutjesci"); no roll of
# the battle exists, so a unit's being there is not enough
NERETVA = re.compile(r'\b(?:bitk|bic|bitc|bitak)\w*\s+(?:na|za)\s+Neretv|\bBitk\w*\s+za\s+ranjenike', re.I)

# More of the war's events, the same way: an entry of his that says he took part (the user adopted them 2026-11-24,
# docs/claude/feedback-rules.md, rule 5), in the order they happened. Belgrade and Trieste count only where he was in
# the fighting, not "po oslobođenju Beograda vraćen ..." (AFTER)
TEXT_EVENTS = {
    'kozara': re.compile(r'\b(?:bitk|bic|bitc|borb|ofanziv)\w*\s+na\s+Kozar|\bkozarsk\w+\s+(?:ofanziv|bitk|bic|epope|proboj)'
                         r'|\bproboj\w*\s+(?:iz\s+)?(?:neprijateljskog\s+)?(?:obruč\w*\s+)?(?:na|sa|s)\s+Kozar', re.I),
    'neretva': NERETVA,
    'drvar': re.compile(r'\bdesant\w*\s+na\s+Drvar|\bdrvarsk\w*\s+desant|\bodbran\w*\s+(?:Vrhovnog\s+štaba\s+)?(?:u|na|kod)\s+Drvar',
                        re.I),
    'beograd': re.compile(r'\b(?:oslobođenj|oslobodjenj|oslobađanj|oslobadjanj|borb|bitk|bic|bitc)\w*\s+(?:za\s+)?'
                          r'(?:oslobođenje\s+|oslobodjenje\s+)?Beograd|\bBeogradsk\w+\s+operacij', re.I),
    'srem': re.compile(r'\bSremsk\w*\s+front', re.I),
    'trst': re.compile(r'\b(?:oslobođenj|oslobodjenj|borb|bitk|bic|bitc)\w*\s+(?:za\s+)?(?:oslobođenje\s+|oslobodjenje\s+)?Trst'
                       r'|\bTr[šs][ćč]ansk\w+\s+operacij', re.I),
}
AFTER = re.compile(r'\b(?:po|posle|poslije|nakon|do|od|prije|pre|pred|iza)\s+$', re.I)
# every event, in the order they happened (a soldier's list is in this order)
EVENT_ORDER = ['igman', 'kozara', 'neretva', 'sutjeska', 'drvar', 'beograd', 'srem', 'trst']


def at_event(s: dict, rx: re.Pattern) -> bool:
    for e in [s] + list(s.get('other_sources') or []):
        text = e.get('additional_info') or ''
        for m in rx.finditer(text):
            if not AFTER.search(text[max(0, m.start() - 12):m.start()]):
                return True
    return False


def at_neretva(s: dict) -> bool:
    return at_event(s, NERETVA)


def at_sutjeska(s: dict) -> bool:
    entries = [s] + list(s.get('other_sources') or [])
    return any((e.get('pdf_file') or '').startswith(SUTJESKA_BOOK) or
               ((e.get('source_url') or '').startswith('porodica:') and FAMILY_SUTJESKA.search(e.get('additional_info') or ''))
               for e in entries)


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
            found = [k for k, rx in TEXT_EVENTS.items() if at_event(s, rx)]
            if at_sutjeska(s):
                found.append('sutjeska')
            for kind in sorted(found, key=EVENT_ORDER.index):
                events.setdefault(s['soldier_id'], []).append({'e': kind, 'sure': True})
                counts[kind] += 1
        path = OUT / name
        had = path.exists()
        if events:
            OUT.mkdir(parents=True, exist_ok=True)
            write_text(path, json.dumps(events, ensure_ascii=False, separators=(',', ':')) + '\n')
            written.add(path.name)
        elif had:
            path.unlink()
        # each event is a step of the record's "Životni put": the unit's life events read again with them
        if events or had:
            extract_life_events._war_cache.pop(code, None)
            lines = extract_life_events.write_events({code: (name, soldiers)})
            counts['lines'] += lines.get(name, 0)
    print(', '.join(f'{k} {counts[k]}' for k in EVENT_ORDER) + f", in {len(written)} unit files ({OUT.relative_to(ROOT)}); "
          f"life lines rewritten for those units: {counts['lines']} soldiers")


if __name__ == '__main__':
    main()
