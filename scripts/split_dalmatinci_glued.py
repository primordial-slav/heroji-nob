"""The Dalmatinci u Prvoj proleterskoj list's glued entries. A heading the parser missed (it stood mid-line in the text
layer: "... u oslobođenom Beogradu. ATLAGIĆ Jovana MIĆO MILAN, rođen 1918, ...") left the next man's entry inside the
one before. Each host keeps its own text and box (an edit; for an entry merged into a roster record it lands in that
record's other_sources), each glued man becomes a record of the list (an add, ids from 0001403001) read by the
parser's own parse(), with his box drawn as the parser draws them: from his heading's line to the next entry, one
rectangle a column. Done on 2026-10-17 (corrections 250001-250572; see CLAUDE.md, Known OCR Issues, after the Beogradski
bataljon). Usage, from the project root: python scripts/split_dalmatinci_glued.py [unit file] --range=LO-HI [--write]
[--dump=proposals.json]; a re-run on the split list finds nothing more."""
import json
import re
import sys
from collections import Counter

sys.path.insert(0, 'data-extraction')
sys.stdout.reconfigure(encoding='utf-8')
import parse_8_kordunaska_divizija as k8  # noqa: E402
import parse_dalmatinci_prva_proleterska as P  # noqa: E402

PDF = 'website/public/pdfs/dalmatinci-prva-proleterska.pdf'
R = '"Dalmatinci u Prvoj proleterskoj": the entry was glued into the one before (its heading stood mid-line), read from the page, 2026-10-17'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
START = re.compile(rf'(?<=[.;:)] )({CAPS}(?:\s*-\s*{CAPS})?(?:\s+\([^)]*\))?\s+(?:[{U}][{L}]+\s+|\.\s?\.\s?\.?\s*)?{CAPS}(?:\s+{CAPS})*)(?=\s*[,.]|\s+[{U}][{L}]|\s+U\s)')
NOT = re.compile(r'^(?:NOB|NOV|NOVJ|KPJ|KPH|KP|KK|OK|MK|SKOJ|JNA|BJV|VŠ|PPK|SAD|SSSR|SUBNOR|AFŽ|NOO|ZAVNOH|URS|II|III|IV|VI|VII|VIII|IX|XI|XII|XX)\b')


# headings the rule can't see: after a speck ("V , jf"), a closing quote, or glued to a word the line broke
EXTRA_HEADS = ['JURČEVIĆ Filipa SLAV-KA', 'KUMBAT JURE', 'KUVAČIĆ Jure MARKO', 'ŽARNIĆ Mate MATE KRANKIN', 'STIPETIĆ (ili SIPETIĆ)']
# an entry's end as the text layer left it: a speck, a word whose last line the text layer lost (a gap on the page)
ENDS = {'V , jf': '', 'u borbi s Nijem-': 'u borbi s Nijemcima.', 'u borbi s Talijanima i četnici-': 'u borbi s Talijanima i četnicima.'}


def on_line(key: str, text: str) -> bool:
    """The heading's surname in capitals on the line, not a name inside the text ("bataljona »Josip Jurčević«")"""
    parts = [key] + ([key.split('-')[0] + '-'] if '-' in key else [])
    toks = re.findall(r'[A-ZČĆŽŠĐa-zčćžšđlI1\-]+', text)
    return any(t == p or (t.isupper() and fold(t) == fold(p)) for t in toks for p in parts)


def mend(t: str) -> str:
    t = t.strip()
    for a, b in ENDS.items():
        if t.endswith(a):
            t = t[:-len(a)] + b
    return t.strip()


def fold(s: str) -> str:
    return re.sub(r'[^A-Z]', '', s.upper().translate(str.maketrans('ČĆŽŠĐ', 'CCZSD')))


def joined(name: str) -> str:
    """A name the line break left a hyphen in ("Dam-Jan", "To-Dor", "And-Rija"): one word where the corpus knows it so"""
    def fix(m):
        a, b = m.group(1), m.group(2)
        whole = a + b.lower()
        return whole if k8.known(whole, 'first_name') or k8.known(whole, 'last_name') else m.group(0)
    return re.sub(rf'([{U}][{L}]+)-([{U}][{L}]+)', fix, name)


def box(lines):
    rects = {}
    for ln in lines:
        r = rects.setdefault((ln['page'], ln['col']), [ln['x'], ln['y'] - 1, ln['x1'], ln['bottom']])
        r[0], r[2], r[3] = min(r[0], ln['x']), max(r[2], ln['x1']), max(r[3], ln['bottom'])
    first = rects[(lines[0]['page'], lines[0]['col'])]
    out = {'pdf_x_end': round(first[2], 1), 'pdf_y_end': round(first[3], 1)}
    same_page = [[round(v, 1) for v in r] for (pg, _), r in rects.items() if pg == lines[0]['page']]
    if len(same_page) > 1:
        out['pdf_rects'] = same_page
    return out


def main():
    k8.corpus()
    lines = P.extract(PDF, 1, None)
    starts = [i for i, ln in enumerate(lines) if ln['text'].startswith('§x§')]
    at = {(ln['page'], ln['x'], ln['y']): i for i, ln in enumerate(lines) if ln['text'].startswith('§x§')}
    src = next((a for a in sys.argv[1:] if a.endswith('.json')), 'website/public/prva-proleterska-soldiers.json')
    d = json.load(open(src, encoding='utf-8'))
    # the father's nominative the unit's records give for each genitive
    nom = Counter()
    for s in d:
        if s.get('middle_name') and s.get('fathers_name'):
            nom[(s['middle_name'], s['fathers_name'])] += 1
    surnames = {}
    for s in d:
        surnames.setdefault(k8.fold(s['last_name']), Counter())[s['last_name']] += 1
    corr = json.load(open('corrections.json', encoding='utf-8'))
    lo, hi = [int(v) for v in next(a for a in sys.argv if a.startswith('--range=')).split('=')[1].split('-')]
    nid = max([c['id'] for c in corr if lo <= c['id'] <= hi] + [lo - 1]) + 1
    done = {c.get('new_id') for c in corr if c['action'] == 'add'}
    new, n, problems = [], 3001, []
    for s in d:
        ents = [(s['soldier_id'], s)] + [(o['soldier_id'], o) for o in s.get('other_sources', ()) if not o.get('unit_file')
                                         and not o.get('ref_book')]
        for sid, e in ents:
            if not (sid or '').startswith('00014'):
                continue
            info = e.get('additional_info') or ''
            heads = [(m.start(), m.group(1)) for m in START.finditer(info) if not NOT.match(m.group(1))]
            heads = sorted(heads + [(info.index(h), h) for h in EXTRA_HEADS if h in info])
            if not heads:
                continue
            i = at.get((e['pdf_page'], e['pdf_x'], e['pdf_y']))
            if i is None:
                problems.append((sid, 'start line not found'))
                continue
            j = next((k for k in starts if k > i), len(lines))
            # each heading's line, in order
            ks, k = [], i
            for _, head in heads:
                key = head.split()[0]
                # after the host's first line and after the heading before (a line holds one heading)
                hit = next((q for q in range(k + 1, j) if on_line(key, lines[q]['text'])), None)
                if hit is None:
                    break
                ks.append(hit)
                k = hit
            if len(ks) != len(heads):
                problems.append((sid, 'heading line not found: ' + ' | '.join(h for _, h in heads)))
                continue
            host_text = mend(info[:heads[0][0]])
            fields = {'additional_info': host_text, **box(lines[i:ks[0] + 1])}
            new.append({'action': 'edit', 'soldier_id': sid, 'fields': fields,
                        'reason': f"{e.get('full_name') or e.get('name')}: the next entries were glued into its text; {R}"})
            for h, (pos, _) in enumerate(heads):
                seg = mend(info[pos:(heads[h + 1][0] if h + 1 < len(heads) else len(info))])
                # "BEVANDA (ili IVANDA) . . . JURE": the other spelling of the surname goes into the text
                alt = re.match(r'^(\S+)\s+(\(ili [^)]*\))\s*(.*)$', seg, re.S)
                if alt:
                    seg = f'{alt.group(1)} {alt.group(3)}'
                bare = re.match(r'^(\S+)\s*\.\s+(.*)$', seg, re.S) if alt else None   # "STIPETIĆ (ili SIPETIĆ). U NOB-u"
                rec = ({'last_name': bare.group(1).title(), 'first_name': '', 'middle_name': '', 'additional_info': bare.group(2)}
                       if bare else P.parse(seg))
                if alt:
                    rec['additional_info'] = f"{alt.group(2).replace('DU-NAN', 'DUNAN')} {rec.get('additional_info') or ''}".strip()
                for f in ('last_name', 'first_name'):
                    rec[f] = joined(rec.get(f) or '')
                # the parser's post step for one record: the corpus's spelling, a final -ič is -ić, and where the
                # unit holds the surname with its carons, those win (the scan loses them)
                last = k8.respell(rec['last_name'], 'last_name')
                if last.endswith('ič') and not k8.known(last, 'last_name'):
                    last = last[:-2] + 'ić'
                forms = surnames.get(k8.fold(last))
                if forms:
                    last = max(list(forms) + [last], key=lambda v: (k8.marks(v), forms.get(v, 0)))
                rec['last_name'] = last
                rec['first_name'] = ' '.join(k8.respell(w, 'first_name') for w in rec['first_name'].split(' '))
                rec['middle_name'] = k8.respell(rec.get('middle_name') or '', 'middle_name')
                rec.pop('fathers_name', None)            # the normalizer puts the genitive in the nominative
                first = ks[h]
                last = ks[h + 1] if h + 1 < len(ks) else j - 1
                ln = lines[first]
                rec.update({'pdf_file': 'dalmatinci-prva-proleterska.pdf', 'pdf_page': ln['page'], 'pdf_x': ln['x'],
                            'pdf_y': ln['y'], **box(lines[first:last + 1])})
                rec = {k: v for k, v in rec.items() if v not in (None, '') or k in ('middle_name', 'first_name')}
                rec.pop('full_name', None)
                new_id = f'0001{400000 + n:06d}'
                assert new_id not in done
                new.append({'action': 'add', 'soldier_id': s['soldier_id'], 'new_id': new_id, 'record': rec,
                            'reason': f"{rec.get('last_name')} {rec.get('middle_name') or ''} {rec.get('first_name')}: glued into the entry of "
                                      f"{e.get('full_name') or e.get('name')}; {R}".replace('  ', ' ')})
                print(new_id, rec.get('last_name'), rec.get('middle_name'), rec.get('first_name'), '|', rec.get('fathers_name'),
                      f"p{rec['pdf_page']}", '|', rec.get('additional_info', '')[:70])
                n += 1
    for i, c in enumerate(new):
        c['id'] = nid + i
    assert nid + len(new) - 1 <= hi, 'past the range'
    assert not {c['id'] for c in new} & {c['id'] for c in corr}, 'ids taken'
    print(len(new), 'corrections', sum(c['action'] == 'add' for c in new), 'men;', len(problems), 'problems')
    for p in problems:
        print('  PROBLEM', p)
    dump = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--dump=')), None)
    if dump:
        json.dump(new, open(dump, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if '--write' in sys.argv:
        corr += new
        open('corrections.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(corr, ensure_ascii=False, indent=2) + '\n')
        print('written', new[0]['id'], '-', new[-1]['id'])


if __name__ == '__main__':
    main()
