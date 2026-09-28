"""
Generate corrections for mechanical text cleanup across all brigades.

Fixes OCR/layout artifacts in additional_info and the structured text fields:
  - line-break hyphens:        "Ita- lija" -> "Italija", "puškomitra- Ijezac" -> "puškomitraljezac"
  - compounds split at a line: "Barajevo- Beograd" -> "Barajevo-Beograd"
  - repeated spaces, doubled commas, "6.. 1943" -> "6. 1943", "Resnik ," -> "Resnik,"
Placeholders the books use for unknown data (e.g. 4. Splitska ".. .,") are left alone.

Each changed record becomes one `edit` correction that pins the current birth_year,
so apply_corrections.py doesn't re-derive it as a side effect.

Usage:
    python scripts/cleanup_text_fields.py            # dry run: stats + samples
    python scripts/cleanup_text_fields.py --write    # append corrections to corrections.json
    python scripts/apply_corrections.py --apply      # then apply them
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from name_utils import BRIGADE_CONFIGS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
L, U = 'a-zčćžšđ', 'A-ZČĆŽŠĐ'
TEXT_FIELDS = ('additional_info', 'birth_place', 'death_place', 'unit_detail', 'rank', 'occupation')

RULES = [
    ('line-break hyphen (OCR Ij)', re.compile(rf'(?<=[{L}])- Ij(?=[{L}])'), 'lj'),
    ('split compound', re.compile(rf'(?<=[{L}])- (?=[{U}])'), '-'),
    ('repeated spaces', re.compile(r'[ \t]{2,}'), ' '),
    ('doubled comma', re.compile(r',{2,}'), ','),
    ('space before comma', re.compile(r'(?<=\w) +(?=[,;](?:\s|$))'), ''),
    ('doubled period', re.compile(r'(?<=\w)\.\.(?!\.)(?=\s|$)'), '.'),
    ('doubled period', re.compile(rf'(?<=\w)\.\.(?=[{L}{U}])'), '. '),
    ('stray leading period', re.compile(rf'^\.\s+(?=[{L}\d])'), ''),
]
LINE_BREAK = re.compile(rf'([{U}{L}]*[{L}])- ([{L}]+)')
CLAUSE_WORDS = {'član', 'borac'}
WORD = re.compile(rf'[{U}{L}]+')


def build_vocabulary(texts) -> Counter:
    # Only words from unbroken text count, so fragments like "nuo" in "pogi- nuo" aren't "words"
    return Counter(w.lower() for t in texts for w in WORD.findall(LINE_BREAK.sub(' ', t)))


def clean(text: str, vocab: Counter) -> tuple[str, Counter]:
    applied = Counter()

    def join(m):
        left, right = m.group(1), m.group(2)
        if vocab[(left + right).lower()] < 2 and vocab[left.lower()] >= 2 and vocab[right.lower()] >= 2:
            if len(right) == 1:                      # "stupio- u": OCR noise between two words
                applied['stray hyphen'] += 1
                return f'{left} {right}'
            if right in CLAUSE_WORDS:                # "zemljoradnik- član": OCR'd comma
                applied['stray hyphen'] += 1
                return f'{left}, {right}'
            if len(left) >= 4 and len(right) >= 4:   # "radnik- bačvar", "april- novembar"
                applied['compound kept'] += 1
                return f'{left}-{right}'
        applied['line-break hyphen'] += 1
        return left + right

    text = LINE_BREAK.sub(join, text)
    for label, rx, repl in RULES:
        text, n = rx.subn(repl, text)
        if n:
            applied[label] += n
    stripped = text.strip()
    if stripped != text:
        applied['surrounding whitespace'] += 1
    return stripped, applied


def live_json_files() -> set[str]:
    units = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    return {m.group(1) for m in re.finditer(r"dataFile:\s*'/([^']+)'", units)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', action='store_true', help='append corrections to corrections.json')
    args = ap.parse_args()

    corrections_path = ROOT / 'corrections.json'
    corrections = json.loads(corrections_path.read_text(encoding='utf-8'))
    next_id = max(c['id'] for c in corrections) + 1

    live = live_json_files()
    brigades = {code: json.loads((ROOT / 'website' / 'public' / c['json_file']).read_text(encoding='utf-8'))
                for code, c in sorted(BRIGADE_CONFIGS.items()) if c['json_file'] in live}
    vocab = build_vocabulary(s.get(f) or '' for d in brigades.values() for s in d for f in TEXT_FIELDS)

    new, totals, samples = [], Counter(), []
    for code, soldiers in brigades.items():
        config = BRIGADE_CONFIGS[code]
        brigade_changes = 0
        for s in soldiers:
            fields, applied = {}, Counter()
            for f in TEXT_FIELDS:
                value = s.get(f)
                if isinstance(value, str) and value:
                    cleaned, a = clean(value, vocab)
                    if cleaned != value:
                        fields[f] = cleaned
                        applied += a
            if not fields:
                continue
            fields['birth_year'] = s.get('birth_year', '')
            new.append({
                'id': next_id + len(new), 'action': 'edit', 'soldier_id': s['soldier_id'], 'fields': fields,
                'reason': 'Text cleanup: ' + ', '.join(f'{k} x{v}' if v > 1 else k for k, v in applied.items()),
            })
            totals += applied
            brigade_changes += 1
            if brigade_changes <= 2:
                samples.append((config['name'], s.get('additional_info', ''), fields.get('additional_info')))
        if brigade_changes:
            print(f"  {config['name'][:30]:30s} {brigade_changes:5d} records")

    print(f"\n{len(new)} records to clean | fixes: {dict(totals)}")
    for name, before, after in samples:
        if after:
            print(f"\n  [{name[:20]}]\n    before: {before[:150]}\n    after:  {after[:150]}")

    if args.write and new:
        corrections_path.write_text(json.dumps(corrections + new, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\nAppended corrections {new[0]['id']}-{new[-1]['id']} to {corrections_path.name}")
    elif new:
        print('\nDry run. Use --write to append these corrections.')


if __name__ == '__main__':
    main()
