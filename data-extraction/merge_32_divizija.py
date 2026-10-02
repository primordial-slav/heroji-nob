"""Merge corrections for unit 35: the division's roster (names only) and "Borci 32. divizije NOVJ" (one entry per
unit a man fought in). Dry run prints counts and samples; --write appends the corrections.

1. In the book, a man is listed under each unit he fought in, with all his details under the first: entries of
   one name in different units, with no father, birth year or village that disagree, are one man when the roster
   has that name once, or when they agree on father and birth year.
2. A name the roster prints once and the book (after 1.) has once is the same man; so is a pair the duplicate
   finder grades "sure" (father agrees).
The book's richest entry is kept (its bio shows in the list); a roster record with a portrait is kept instead.
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
F = ROOT / 'website/public/32-divizija-soldiers.json'
d = json.loads(F.read_text(encoding='utf-8'))
portraits = set(json.loads((ROOT / 'website/app/data/portrait-index.json').read_text(encoding='utf-8')))


def fold(s: str) -> str:
    s = s.lower().replace('đ', 'dj')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def key(s):
    return fold(s['last_name']) + '|' + fold(s['first_name'])


def village(s):
    m = re.search(r'\bs\.\s*([A-ZČĆŽŠĐ][\w]+)', s['additional_info'])
    return fold(m.group(1))[:5] if m else ''


def father(s):
    return fold(s.get('fathers_name') or s.get('middle_name') or '').rstrip('.')


def agree_father(a, b):
    fa, fb = father(a), father(b)
    if not fa or not fb:
        return None
    if len(fa) == 1 or len(fb) == 1:
        return fa[0] == fb[0]
    return fa[:4] == fb[:4]


def conflict(a, b) -> bool:
    if agree_father(a, b) is False:
        return True
    ya, yb = a.get('birth_year'), b.get('birth_year')
    if ya and yb and abs(int(ya) - int(yb)) > 1:
        return True
    va, vb = village(a), village(b)
    return bool(va and vb and va != vb)


roster = [s for s in d if s['pdf_file'] == '32-divizija.pdf']
book = [s for s in d if s['pdf_file'] == '32-divizija-borci.pdf']
rcount = Counter(key(s) for s in roster)
rby = defaultdict(list)
for s in roster:
    rby[key(s)].append(s)
groups = defaultdict(list)
for s in book:
    groups[key(s)].append(s)

merges = []          # (keep, merge, reason)
book_keeper = {}     # key -> the book record a group consolidates into
stats = Counter()
for k, g in groups.items():
    if not k.split('|')[1] or not k.split('|')[0]:
        continue
    if len(g) == 1:
        book_keeper[k] = g[0]
        continue
    pair_ok = all(not conflict(a, b) for i, a in enumerate(g) for b in g[i + 1:])
    units = [s.get('unit_detail', '') for s in g]
    strong = all(agree_father(a, b) and a.get('birth_year') and a.get('birth_year') == b.get('birth_year')
                 for i, a in enumerate(g) for b in g[i + 1:])
    if pair_ok and len(set(units)) == len(units) and (rcount[k] == 1 or strong):
        keep = max(g, key=lambda s: (len(s['additional_info']), s['soldier_id'] < '0'))
        for s in g:
            if s is not keep:
                merges.append((keep, s, 'listed under another unit he fought in'))
        book_keeper[k] = keep
        stats['book groups merged'] += 1
        stats['book entries merged'] += len(g) - 1
    else:
        stats['book groups left'] += 1

# 2. the roster
used = {id(m) for _, m, _ in merges}
for k, rs in rby.items():
    if len(rs) != 1 or k not in book_keeper:
        continue
    if sum(1 for s in groups[k] if id(s) not in used) != 1:
        continue
    r, b = rs[0], book_keeper[k]
    if agree_father(r, b) is False:
        stats['roster father disagrees'] += 1
        continue
    if r['soldier_id'] in portraits:
        merges.append((r, b, 'the same name, once in each list'))
        # the book's other entries of this man follow b (apply_merge carries other_sources along)
    else:
        merges.append((b, r, 'the same name, once in each list'))
    stats['roster merged (unique name)'] += 1

print(dict(stats), len(merges))
for kp, m, why in merges[:12]:
    print(f"  {kp['soldier_id']} {kp['full_name']} | {kp['additional_info'][:50]}  <-  {m['soldier_id']} {m['full_name']} | {m['additional_info'][:40]}  ({why})")

if '--write' in sys.argv:
    cf = ROOT / 'corrections.json'
    corr = json.loads(cf.read_text(encoding='utf-8'))
    nid = max(c['id'] for c in corr) + 1
    # a book entry merged into a roster record (portrait) must be merged after its own group's merges
    for i, (kp, m, why) in enumerate(merges):
        corr.append({'id': nid + i, 'action': 'merge', 'soldier_id': kp['soldier_id'], 'merge_id': m['soldier_id'],
                     'merge_name': m['full_name'],
                     'reason': f"Same soldier in 32-divizija.pdf and 32-divizija-borci.pdf: {why}"
                     if m['pdf_file'] != kp['pdf_file'] else f"Same soldier twice in 32-divizija-borci.pdf: {why}"})
    cf.write_text(json.dumps(corr, ensure_ascii=False, indent=2), encoding='utf-8')
    print('appended', len(merges), 'from', nid)
