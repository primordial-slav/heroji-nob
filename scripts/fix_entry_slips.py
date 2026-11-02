"""
Slips of the units' entries that a rule reads safely (2026-11-02). Each writes `edit` corrections; run without --write to read them.

  surnames  A surname cut at the front or misread at its first letter, told by its neighbours on the page of an alphabetical
            list: "Ević" among Ivanišević and Radošević, "Topović" among four Popović, "Cudić" among the Č.
  given     A given name left in the text, in capitals before the first comma, the father taken for it: "Čanić Bogoljuba |
            PETAR, 1925, Vrelo" is Čanić Bogoljuba Petar; where the record has a given name, those capitals are what he was
            called ("zvani Hamdo; borac, ...").
  marks     The scan's marks in the text: a soft hyphen before a space (a word broken at the line's end), ">" for the j of Љ
            and Њ, "_", "^", "•", "■", "©" and "°" for o inside a word, and specks that close an entry.

A name changed here must also change in the guards that hold it (link_name, merge_name, and identity_decisions.json).
"""
import collections, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS

CAP = 'A-ZČĆŽŠĐ'
LOW = 'a-zčćžšđ'
CARONS = {'Č': 'C', 'Ć': 'C', 'Š': 'S', 'Ž': 'Z', 'Đ': 'D'}


def base(ch):
    return CARONS.get(ch, ch)


# read on the page: the neighbours' rule can't tell these (a common surname misread, one of two garbled forms)
SURNAMES = {'0006004734': 'Nešić', '0044000149': 'Rogulja', '0003000447': 'Ivanišević', '0013000344': 'Radošević'}
NOT_THESE = {'0007100815', '0007100477'}


def load():
    units = {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists() and code != 122 and not 131 <= code <= 138:
            units[code] = json.loads(p.read_text(encoding='utf-8'))
    return units


def surnames(units):
    bearers = collections.Counter(s.get('last_name') for data in units.values() for s in data)
    out = []
    for code, data in units.items():
        pages = collections.defaultdict(list)
        for s in data:
            if s.get('pdf_file') and s.get('pdf_page') and s.get('pdf_y') is not None and s.get('last_name'):
                pages[(s['pdf_file'], int(s['pdf_page']))].append(s)
        for (pdf, pg), rows in pages.items():
            rows.sort(key=lambda s: (round((s.get('pdf_x') or 0) / 120), s['pdf_y']))
            for i, s in enumerate(rows):
                last = s['last_name']
                near = [rows[j]['last_name'] for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < len(rows)]
                if len(near) < 3 or len(last) < 2:
                    continue
                firsts = collections.Counter(n[0] for n in near)
                sect, n = firsts.most_common(1)[0]
                if n < len(near) - 1 or last[0] == sect:
                    continue                                    # no one letter the list is at, or he is at it
                # cut at the front: a neighbour at the list's letter ends with this surname
                cut = [m for m in near if m[0] == sect and len(m) > len(last) and m.endswith(last.lower()) and last[0].lower() == m[len(m) - len(last)]]
                # misread at the first letter: the same otherwise
                first = [m for m in near if m[0] == sect and len(m) == len(last) and m[1:] == last[1:]]
                if cut and bearers[last] <= 4 and bearers[cut[0]] >= 3 * bearers[last]:
                    out.append((code, s, cut[0], 'cut'))
                elif first and bearers[first[0]] >= 3 * bearers[last] and bearers[first[0]] >= 2 and s['soldier_id'] not in NOT_THESE:
                    out.append((code, s, first[0], 'first'))                # only towards the spelling the site knows far better
    by_id = {s['soldier_id']: (code, s) for code, data in units.items() for s in data}
    for sid, new in SURNAMES.items():
        if sid in by_id:
            out.append((by_id[sid][0], by_id[sid][1], new, 'read'))
    return out


# the words that open a text in capitals and name no man: units, states, peoples
NOT_NAMES = {'SSSR', 'ZSSR', 'ZDA', 'FOS', 'UKB', 'KB', 'ITALIJAN', 'UKRAJINAC', 'GGG', 'ČSR', 'CSSR', 'SAD', 'USA', 'III', 'VII', 'VIII', 'XII', 'XIV', 'XVI', 'ROĐEN',
        'SKOJ', 'KPJ', 'KPH', 'NOV', 'NOB', 'NOR', 'POJ', 'VPV', 'KNOJ', 'PPK', 'SFRJ', 'FNRJ', 'AFŽ', 'KPO', 'NOO', 'NOP', 'NOU', 'RAF', 'VKS', 'UDB', 'OZN', 'OZNA'}
# read one by one: the record's name goes as given here
BY_HAND = {
    '0001008979': {'middle_name': 'Consolato', 'fathers_name': 'Consolato', 'first_name': 'Stefano', 'text': 1},
    '0119001176': {'middle_name': 'Mile', 'fathers_name': 'Mile', 'first_name': 'Miodrag', 'text': 1},
    '0035109682': {'last_name': 'Rončević', 'first_name': 'Ante', 'text': 1},
    '0035100613': {'last_name': 'Belković-Jovićin', 'first_name': 'Jelka', 'text': 1},
    '0056001522': {'middle_name': 'Š.', 'fathers_name': 'Š.', 'first_name': 'Redžo', 'text': 1},
    '0010204570': {'last_name': 'Šeparović-Bastel', 'middle_name': 'Ivana', 'fathers_name': 'Ivan', 'first_name': 'Anđelka', 'cut': r'^BASTEL Ivana ANĐELKA,\s*'},
    '0035105557': {'last_name': 'Krajačić', 'first_name': 'Josip', 'cut': r'^JOSIP PRIKA,\s*', 'lead': 'zvani Prika; '},
    '0058002890': {'last_name': 'Vujasinović-Mirković', 'first_name': 'Branko', 'cut': r'^MIRKOVIĆ; BRANKO,\s*'},
    '0097000036': {'first_name': 'Ibrahim', 'cut': r'^', 'lead': 'borac, '},
    '0007003263': {'last_name': 'Matić-Periša', 'middle_name': 'Grgura', 'fathers_name': 'Grgur', 'first_name': 'Marija', 'cut': r'^MARIJA, Grgura\.\s*'},
    '0007003161': {'cut': r'^DRAGI, Vida\.\s*', 'lead': 'zvani Dragi; '},
    '0021002467': {'cut': r'^ŽIVKOVIĆ Đ\. NENAD\.\s*', 'lead': 'zvani Živković Đ. Nenad; '},
    '0016001947': None, '0013001084': None,
}


def given(units, current):
    names = collections.Counter(s.get('first_name') for data in units.values() for s in data)

    def is_genitive(g):
        cands = [g[:-1], g[:-1] + 'o', g[:-1] + 'e', g[:-2] + 'a' + g[-2:-1]] if g.endswith('a') else [g[:-1] + 'o', g[:-1] + 'a'] if g.endswith('e') else []
        best = max(cands, key=lambda c: names.get(c, 0), default=None)
        return bool(best) and names.get(g, 0) < 0.2 * names.get(best, 0), best

    out = []
    for code, data in units.items():
        for s in data:
            t = current(s)
            hand = BY_HAND.get(s['soldier_id'], 0)
            if hand is None:
                continue
            if hand:
                f = {k: v for k, v in hand.items() if k not in ('text', 'cut', 'lead')}
                new = re.sub(hand['cut'], '', t) if 'cut' in hand else re.sub(rf'^[{CAP}]{{3,}}\s*,?\s*', '', t)
                f['additional_info'] = hand.get('lead', '') + new
                out.append((code, s, 'read', f))
                continue
            m = re.match(rf'^([{CAP}]{{3,}}(?:[ -][{CAP}]{{3,}})*)(\s*[,.;:]|\s)\s*', t)
            if not m or m.group(1) in NOT_NAMES:
                continue
            caps = m.group(1)
            rest = t[m.end():]
            title = '-'.join(w.capitalize() for w in caps.replace(' ', '-').split('-'))
            first, mid = s.get('first_name') or '', s.get('middle_name') or ''
            if code == 35:                                       # "PIŠTA, Stjepana, r. 1921": the father stands after the name
                fm = re.match(rf'^([{CAP}][{LOW}]+),\s*(?=r\.|s\.|[{CAP}][{LOW}]+,)', rest)
                if fm and not mid and is_genitive(fm.group(1))[0]:
                    out.append((code, s, 'nick', {'middle_name': fm.group(1), 'fathers_name': is_genitive(fm.group(1))[1], 'additional_info': f'zvani {title}; {rest[fm.end():]}'}))
                    continue
            if not first:                                        # "Janković | SIMA, 1927"
                out.append((code, s, 'given', {'first_name': title, 'additional_info': rest}))
            elif len(first) <= 2 and not mid:                    # "Ćupović S | PETAK, rođen 1908": the father's initial
                out.append((code, s, 'father', {'middle_name': first + '.', 'fathers_name': first + '.', 'first_name': title, 'additional_info': rest}))
            elif not mid and is_genitive(first)[0] and (names.get(title.split('-')[0], 0) >= 3):
                out.append((code, s, 'father', {'middle_name': first, 'fathers_name': is_genitive(first)[1], 'first_name': title, 'additional_info': rest}))
            elif names.get(title.split('-')[0], 0) >= 0 and len(caps.split()) == 1:
                out.append((code, s, 'nick', {'additional_info': f'zvani {title}; {rest}'}))
    return out


MARKS = re.compile('[­~^•■_©°®>]')
# a word holding ">": л> and н> are Љ and Њ
def clean(t):
    o = t
    t = re.sub('(?<=[^\\W\\d_])­\\s*(?=[^\\W\\d_])', '', t)
    t = t.replace('­', '-')
    t = re.sub(r'(?<=[lLnN])>(?=[^\W\d_])', 'j', t)
    t = re.sub(r'(?<=[a-zčćžšđ])_(?=[a-zčćžšđ])', '', t)
    t = re.sub(r'_+', ' ', t)
    t = re.sub(r'\s*[■•]+\s*(?=[,.;:)])', '', t)
    t = re.sub(r'(?<=—)[■•]+', '', t)
    t = re.sub(r'(?<=-)\s*[■•]+\s*(?=[^\W\d_])', '', t)
    t = re.sub(r'\s+[■•]+\s+', ' ', t)
    t = re.sub(r'(?<=\s)[■•]+(?=[^\W\d_\d])|(?<=[^\W\d_])[■•]+(?=\s)', '', t)
    t = re.sub(r'(?<=\d)-\^(?=[^\W\d_])', ' ', t)
    t = re.sub(r'\s+\^\s+', ' ', t)
    t = re.sub(r'(?<=[^\W\d_])\^\s', ', ', t)
    t = re.sub(r'(?<=\biz)\^(?=[^\W\d_])', ' ', t)
    t = re.sub(r'(?<=[^\W\d_])\^(?=[^\W\d_])', '', t)
    t = re.sub(r'\bN[©°]B\b|\bN[O°]®', 'NOB', t)
    t = re.sub(r'(?<![\w])©(?=[a-zA-Z])|(?<=[^\W\d_])©(?=[^\W\d_])', 'o', t)
    t = re.sub(r'(?<=[^\W\d_])°(?=[a-zčćžšđ])', 'o', t)
    t = re.sub(r'(?<=[^\W\d_])~(?=[^\W\d_])', '-', t)
    t = re.sub(r',~(?=[^\W\d_])', ', ', t)
    # specks that close an entry: past its last full stop, no word of three letters
    m = re.search(r'^(.*[.)»«])\s*([^\w]*(?:\b\w{1,2}\b[^\w]*)*)$', t)
    if m and len(m.group(2)) >= 3 and re.search(r'[•■~^\'"\\/<>{}|]', m.group(2)):
        t = m.group(1)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    return t if t != o else o


def main():
    units = load()
    corr = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    pending = {}
    for c in corr:
        if c['action'] == 'edit' and 'additional_info' in (c.get('fields') or {}):
            pending[c['soldier_id']] = c['fields']['additional_info']
        if c['action'] == 'add' and c.get('new_id'):
            pending[c['new_id']] = c['record'].get('additional_info', '')

    def current(s):
        return pending.get(s['soldier_id'], s.get('additional_info') or '').strip()

    edits = {}
    renames = {}
    names = surnames(units)
    print('surnames', len(names), collections.Counter(n[3] for n in names))
    for code, s, new, how in names:
        print('  ', code, s['soldier_id'], s.get('full_name'), '->', new, how, '|', (s.get('additional_info') or '')[:50])
        edits.setdefault(s['soldier_id'], ({}, []))[0]['last_name'] = new
        edits[s['soldier_id']][1].append(f'Its surname on the page of an alphabetical list ({s.get("pdf_file")}, p. {s.get("pdf_page")}): "{s["last_name"]}" among {new}')
        renames[s['soldier_id']] = (s.get('full_name'), new)
    giv = given(units, current)
    print('given', len(giv), collections.Counter(g[2] for g in giv))
    for code, s, how, f in giv:
        print('  ', code, s['soldier_id'], s.get('full_name'), how, '|', f.get('middle_name', ''), '/', f.get('first_name', ''), '|', f['additional_info'][:70])
        edits.setdefault(s['soldier_id'], ({}, []))[0].update(f)
        edits[s['soldier_id']][1].append("The capitals opening the text are its given name or what he was called, on the page")
    marks = 0
    for code, data in units.items():
        for s in data:
            t = current(s)
            if not t or not MARKS.search(t):
                continue
            n = edits.get(s['soldier_id'], ({}, []))[0].get('additional_info', t)
            new = clean(n)
            if new != n:
                marks += 1
                if marks % 40 == 0:
                    print('   marks:', s['soldier_id'], '|', n[-70:], '=>', new[-70:])
                edits.setdefault(s['soldier_id'], ({}, []))[0]['additional_info'] = new
                edits[s['soldier_id']][1].append("The scan's marks in the text")
    print('marks', marks, 'edits', len(edits))
    if '--write' in sys.argv:
        start = int(sys.argv[sys.argv.index('--write') + 1])
        assert not [c for c in corr if c['id'] >= start]
        add = [{'id': start + i, 'action': 'edit', 'soldier_id': k, 'fields': v[0], 'reason': '; '.join(dict.fromkeys(v[1]))} for i, (k, v) in enumerate(edits.items())]
        # the guards follow the names (full_name is rebuilt from the fields)
        n = 0
        new_full = {}
        for code, data in units.items():
            for s in data:
                f = edits.get(s['soldier_id'], ({},))[0]
                if any(k in f for k in ('last_name', 'first_name', 'middle_name')):
                    new_full[s['soldier_id']] = (s.get('full_name'), ' '.join(x for x in (f.get('last_name', s.get('last_name')), f.get('middle_name', s.get('middle_name')), f.get('first_name', s.get('first_name'))) if x))
        for c in corr:
            for idk, namek in (('link_id', 'link_name'), ('merge_id', 'merge_name')):
                if c.get(idk) in new_full and c.get(namek) == new_full[c[idk]][0]:
                    c[namek] = new_full[c[idk]][1]
                    n += 1
        (ROOT / 'corrections.json').write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        dec_path = ROOT / 'identity_decisions.json'
        dec = json.loads(dec_path.read_text(encoding='utf-8'))
        m = 0
        for d in dec:
            for idk, namek in (('a', 'a_name'), ('b', 'b_name')):
                if d.get(idk) in new_full and d.get(namek) == new_full[d[idk]][0]:
                    d[namek] = new_full[d[idk]][1]
                    m += 1
        dec_path.write_text(json.dumps(dec, ensure_ascii=False, indent=1), encoding='utf-8')
        print('written', len(add), start, start + len(add) - 1, 'guards', n, m)


if __name__ == '__main__':
    main()
