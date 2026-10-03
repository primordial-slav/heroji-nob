"""
Parser: 8. banijska NOU brigada (brigade code 45) — the brigade's fallen and dead, a second book.

Source: Ljuban Đurić, "Osma banijska NOU brigada" (znaci.org 00003/383.pdf, its pages 244-309, book pp. 247-312)
        →  website/public/pdfs/8-banijska-poginuli.pdf. Latin, two columns, every line flush left, a blank line
        between entries, by letter:
    "Pregled palih i umrlih boraca brigade (7. septembar 1942 - 6. decembar 1944.)":
        ARBUTINA Sime DMITAR, 1925, Gornji Žirovac, kotar Dvor, zemljoradnik, Srbin. Borac od 14. 5. 1942. godine,
        poginuo 7. 3. 1943. tokom prijenosa ranjenika Centralne bolnice NOVJ preko Neretve.
An entry starts after the gap. The father in the genitive or as an initial, or none ("BABIĆ MILAN"); the given name
in capitals or not ("CREVAR Adama Pavao"), a nickname after it ("SIMO ŠIMA"). The text layer spaces surnames apart
("RAD AKO VIĆ", "ERKALO VIĆ") and keeps the hyphen of a name broken at a line end ("ALEKSAN-DAR"). The unit's first
book is its Borci Sutjeske chapter (IDs 1-); these get IDs from 10001; the same soldier in both is merged.
"""
import re
import sys

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FATHERS = {'Pavia': 'Pavla', 'Jocana': 'Jovana'}                          # the scan's slips


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(fn, encoding='utf-8')):
            if s.get('pdf_file') == '8-banijska-poginuli.pdf':
                continue
            for f in k8._spell:
                if s.get(f):
                    k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def prepare(lines: list[dict]) -> None:
    """The gap above each line in its column (None at a column's head)."""
    last: dict = {}
    for ln in lines:
        key = (ln['page'], ln['x'] > 200)
        ln['_gap'] = ln['y'] - last[key] if key in last else None
        last[key] = ln['y']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|[A-ZČĆŽŠĐ]{1,2}', t) or re.match(r'^(?:Pregled palih|ih boraca brigade|\(7\. septembar|6\. decembar 1944)', t):
        return False                                                         # page numbers, letters, the title
    if ln['page'] == 1 and ln['y'] > 480:
        return False                                                         # the author's footnote
    gap = ln.get('_gap')
    head = re.match(rf'^[{U}][{U}\-]+(?:\s+-)?\s+[{U}(]', t)                 # "ARBUTINA Sime", "HOLANĐANIN (podaci"
    if head and (gap is None or gap > 15):
        t = '§e§ ' + t
    ln['text'] = t
    return True


def merge_fragments(tokens: list[str]) -> list[str]:
    """'STE VAN' = STEVAN, 'RAD AKO VIĆ' = RADAKOVIĆ, 'MATU A' = MATUA; 'JOKA - SELANEC' = JOKA-SELANEC."""
    out: list[str] = []
    for t in tokens:
        if out and out[-1] != '-' and t != '-' and (re.fullmatch(r'(?:O|E)?VIĆ|IĆ|[A-ZČĆŽŠĐ]', t) or (len(t) <= 3 and (
                not k8.known(t, 'first_name') or k8.known(out[-1] + t, 'first_name') > k8.known(t, 'first_name')))):
            out[-1] += t
        else:
            out.append(t)
    res: list[str] = []
    i = 0
    while i < len(out):
        if out[i] == '-' and res and i + 1 < len(out):
            res[-1] += '-' + out[i + 1]
            i += 2
        else:
            res.append(out[i])
            i += 1
    return res


def parse(text: str) -> dict:
    text = re.sub(r'^§e§\s*', '', text)
    text = re.sub(rf'(?<=[{U}])-\s*(?=[{U}])', '', text)                    # "ALEKSAN-DAR": a line-break hyphen
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "zemljo- radnik"
    unknown = re.match(rf'^([{U}]+)\s*(\(podaci nepoznati?\w*\)|zv\.\s+\w+\s*\(podaci nepozna\w*\))[,.]?\s*(.*)$', text)
    if unknown:                                                              # "HOLANĐANIN (podaci nepoznati)", "IVAN zv. domobran"
        rec = _record(unknown.group(1).title(), '', '', (unknown.group(2) + ' ' + unknown.group(3)).strip())
        rec['_given_only'] = unknown.group(1) == 'IVAN'
        return rec
    m = re.match(r'^(.*?)(?:,\s*|\s+(?=1[89]\d\d\b))(.*)$', text)
    head, info = (m.group(1), m.group(2)) if m else (text, '')
    words = head.split()
    caps = []
    while words and (re.fullmatch(rf'[{U}][{U}\-]*', words[0]) or words[0] == '-'):
        caps.append(words.pop(0))
    nick = []
    if words:                                                                # "ARBUTINA Rade DMITAR", "CREVAR Adama Pavao"
        last = k8.join_parts([w for w in merge_fragments(caps)], 'last_name') if caps else ''
        father = words.pop(0) if len(words) > 1 else ''
        given = merge_fragments([w.upper() for w in words])
        given, nick = given[:1], given[1:]
    else:                                                                    # "BABIĆ MILAN", "ZMIJANAC MILAN MIĆO"
        tokens = merge_fragments(caps)
        last, father, given, nick = tokens[0], '', tokens[1:2], tokens[2:]
    notes = ['zvani ' + ' '.join(w.title() for w in nick)] if nick else []
    father = FATHERS.get(father, father)
    rec = _record(last, given[0].title().rstrip('.') if given else '', father, '; '.join(notes + [info] * bool(info)))
    y = re.match(r'(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.match(rf'(?:1[89]\d\d[,.]\s*)?([{U}][{L}]+(?:\s+[{U}]?[{L}]+)?)\s*,\s*kotar\s+([{U}][{L}]+(?:\s+[{U}][{L}]+)?)', info)
    if b:
        rec['birth_place'] = f'{b.group(1)}, {b.group(2)}'                  # "Gornji Žirovac, kotar Dvor"
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = k8.post(soldiers)                                             # carons the scan lost: "ADZIC" = Adžić
    for s in soldiers:
        if s.pop('_given_only', False):
            s['first_name'], s['last_name'] = s['last_name'], ''             # "IVAN zv. domobran": no surname
            s['full_name'] = s['first_name']
        if not s['middle_name']:
            s['fathers_name'] = ''
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/8-banijska-poginuli.pdf',
        brigade_code=45,
        output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/8-banijska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='latin',
        entry_start_re=re.compile(r'^§e§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=len(sys.argv) <= 1,
    )
