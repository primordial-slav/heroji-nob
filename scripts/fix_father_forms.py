"""
Fathers left as the book prints them, in a case or as a possessive (2026-11-03): `fathers_name` holds the nominative, `middle_name` the printed form, and
where the converter knew no name the two stayed one: "Otac: Rostema", "Otac: Savin". Here a form is read through the names the 1964 census prints in the
nominative and the units' own given names: Rustema Rustem, Vićentija Vićentije, Grge Grga, Savin Savo, Aganov Agan.

A form is changed only where it is rare as a name itself (the reading counted at least 15 times for every time the form is, and 5 times at the least). Between
two readings ("Savin": Savo or Sava; "Toše": Toša or Tošo) the unit's own men decide, a reading twice the other's; else the site's, three times; else it stays.
A form in -e stays in the Dalmatian units, whose lists print it as the nominative (Bože, Grge, Mate). A unit whose fathers are mostly in the nominative already
keeps its forms in -a ("Rada", "Mata": the Prva vojvođanska, the 17. majevička). A woman's name goes through too; standardize_fields.parents moves her to the
mother's row.

python scripts/fix_father_forms.py [--write START]
"""
import collections, glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS

DALMATIAN = {1, 7, 8, 36, 46, 50, 53, 79, 103, 148, 168}
# Lika, Kordun, Banija and the Krajina: where nothing decides, the -o their men bear (the census's Simo 639 to Sima 31 in Croatia)
O_UNITS = {2, 3, 10, 13, 20, 44, 45, 47, 48, 60, 94, 118, 120, 123}
HAND = {'Durin': 'Đuro', 'Mitrov': 'Mitar', 'Petrov': 'Petar', 'Aleksandrov': 'Aleksandar'}
NOT = {'Božin', 'Radin', 'Savin', 'Stanka', 'Pera', 'Milana'} - {'Savin', 'Radin', 'Stanka', 'Milana'}    # the ones the list showed to be names of their own
NAME = re.compile(r'[A-ZČĆŽŠĐ][a-zčćžšđ]+')
VOWELS = 'aeiou'


def readings(f):
    out = []
    if f.endswith('a') and len(f) >= 4 and f[-2] not in VOWELS:
        out += [f[:-1], f[:-1] + 'o', f[:-1] + 'e']
    elif f.endswith('ja') and len(f) >= 5:
        out += [f[:-1] + 'e', f[:-1], f[:-1] + 'o']                # Vićentija Vićentije, Ristivoja Ristivoje
    if f.endswith('e') and len(f) >= 4:
        out += [f[:-1] + 'a', f[:-1] + 'o']
    if re.search(r'[oe]v$', f) and len(f) >= 5:
        s = f[:-2]
        out += [s, s + 'o', s + 'a', s + 'e']
    if f.endswith('in') and len(f) >= 5:
        s = f[:-2]
        out += [s + 'a', s + 'o', s + 'e']
    return out


def main():
    census = collections.Counter()
    for p in glob.glob(str(ROOT / 'data-extraction/zrtve-rata/*-entries.json')):
        for e in json.load(open(p, encoding='utf-8')):
            census[(e.get('fathers_name') or '').strip()] += 1
    units, given, unit_given = {}, collections.Counter(), {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        if code == 122 or 131 <= code <= 138:
            continue
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists():
            units[code] = json.loads(p.read_text(encoding='utf-8'))
            names = collections.Counter(s.get('first_name') for s in units[code] if s.get('first_name'))
            given.update(names)
            # the unit's men: a given name in -a may be a woman's (Lika's Sava), a father's nominative is a man's
            names = collections.Counter({k: v for k, v in names.items() if k[-1] != 'a'})
            for s in units[code]:
                f = s.get('fathers_name') or ''
                if f and f != (s.get('middle_name') or ''):
                    names[f] += 1
            unit_given[code] = names
    def n(w):
        return census[w] + given[w]
    edits, kinds, kept = [], collections.Counter(), collections.Counter()
    samples = collections.defaultdict(list)
    for code, data in units.items():
        printed = [s for s in data if (s.get('fathers_name') or '') and s.get('fathers_name') == s.get('middle_name')]
        whole = [s for s in printed if NAME.fullmatch(s['fathers_name']) and n(s['fathers_name']) >= 20]
        consonant = sum(s['fathers_name'][-1] not in VOWELS for s in whole)
        nominative_list = len(whole) >= 30 and consonant / len(whole) > .3
        for s in printed:
            f = s['fathers_name']
            if not NAME.fullmatch(f) or f in NOT:
                continue
            if f in HAND:
                to = HAND[f]
            else:
                if nominative_list and f[-1] in 'ae':
                    continue
                if f.endswith('e') and code in DALMATIAN:
                    continue
                cands = sorted(((n(c), c) for c in readings(f)), reverse=True)
                if not cands or cands[0][0] < 5 or cands[0][0] < 15 * (n(f) + 1):
                    continue
                strong = [(k, c) for k, c in cands if k >= cands[0][0] / 3]
                if len(strong) > 1:
                    own = sorted(((unit_given[code][c], c) for _, c in strong), reverse=True)
                    if own[0][0] and own[0][0] >= 2 * own[1][0]:
                        to = own[0][1]
                    elif strong[0][0] >= 3 * strong[1][0]:
                        to = strong[0][1]
                    elif code in O_UNITS and any(c.endswith('o') for _, c in strong):
                        to = next(c for _, c in strong if c.endswith('o'))
                    else:
                        kept[f] += 1
                        continue
                else:
                    to = cands[0][1]
            kinds[f'{f[-2:]}'] += 1
            samples[(f, to)].append(s['soldier_id'])
            edits.append({'action': 'edit', 'soldier_id': s['soldier_id'], 'fields': {'fathers_name': to},
                          'reason': f'The father in the nominative: the book prints "{f}"'})
    print(len(edits), 'records,', len(samples), 'forms')
    for (f, to), ids in sorted(samples.items(), key=lambda kv: -len(kv[1]))[:90]:
        print(f'  {len(ids):4d} {f} -> {to}  {ids[0]}')
    print('left between two readings:', kept.most_common(40))
    if '--write' in sys.argv:
        corr = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
        start = int(sys.argv[sys.argv.index('--write') + 1])
        assert not [c for c in corr if c['id'] >= start]
        for i, c in enumerate(edits):
            c['id'] = start + i
        open(ROOT / 'corrections.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(corr + edits, ensure_ascii=False, indent=2) + '\n')
        print('written', start, start + len(edits) - 1)


if __name__ == '__main__':
    main()
