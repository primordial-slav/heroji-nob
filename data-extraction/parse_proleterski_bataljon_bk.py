"""
Parser: Proleterski bataljon Bosanske krajine (brigade code 163).

Source: Savo Trikić, Dušan Repajić, "Proleterski bataljon Bosanske krajine" (Beograd 1982; znaci.org 00003/490.pdf),
        "Spisak boraca Proleterskog bataljona Bosanske krajine" →  website/public/pdfs/proleterski-bataljon-bk.pdf
        (book pp. 256-362): a bio beside each fighter's portrait, surname first in capitals, the father in brackets:
            ANIC (Nikole) ĐURO, rođen 1914. Otiš-Lušci Palanka, Sanski Most. Srbin, šumarski radnik, u NOB-u od
            1941. U Grmečku proletersku četu stupio je 27. 2. 1942. g. Desetar, komandir voda i komandant
            bataljona. Član KPJ. Poginuo oktobra 1942. na Skupiduši ...
The blocks stand in two columns that sit elsewhere on every page, with a third now and then; PyMuPDF's text blocks
are the book's blocks, so each is read whole and its box is the entry's (`entry_boxes.INLINE_ENTRIES`).
A third name in capitals after the given name is what he was called ("JANJUS (Steve) RADOSLAV RADE").
The pages before the list (pp. 1-3) are the editors' account of the battalion's men.
"""
import glob
import json
import re
from collections import Counter

import fitz

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser, title_case

U = 'A-ZČĆŽŠĐ'
LIST_FROM = 4                                                                # p. 259 of the book: the first bio
NOT_NAME = r'(?!(?:KPJ|SKOJ|NOB|NOV|OZN)\b)'
# "ANIC (Nikole) ĐURO", "KOVAČEVI Č (Riste) ĐURO", "NIKOLIĆ BOŠKO, rođen", "TIŠMA JOVO, U Drvarsku ..."
START = re.compile(rf'^{NOT_NAME}[{U}][{U}12 ]*[{U}1]\s*\(|^{NOT_NAME}[{U}]{{3,}}(?:\s+[{U}]{{2,}})+\s*[,.]?\s')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """One line per bio, its box in the marker: '§x§x1|y1§ ANIC (Nikole) ĐURO, ...'. A block that doesn't start
    with a name goes on the bio before it."""
    doc = fitz.open(pdf_path)
    out = []
    for pno in range(max(start, LIST_FROM), (end or len(doc)) + 1):
        blocks = [b for b in doc[pno - 1].get_text('blocks') if b[4].strip() and b[1] < 790]
        blocks.sort(key=lambda b: (round(b[0] / 60), b[1]))                    # down each column
        for x0, y0, x1, y1, text, *_ in blocks:
            text = re.sub(r'\s*\n\s*', ' ', text).strip()
            if re.fullmatch(r'[\d\W]{1,4}', text):
                continue
            if START.match(text) or not out:
                out.append({'page': pno, 'x': round(x0, 1), 'y': round(y0, 1), 'text': text, 'box': [x1, y1]})
            else:
                prev = out[-1]
                prev['text'] += ' ' + text
                if prev['page'] == pno and abs(prev['x'] - x0) < 20:
                    prev['box'] = [max(prev['box'][0], x1), max(prev['box'][1], y1)]
    return [{'page': e['page'], 'x': e['x'], 'y': e['y'],
             'text': f"§x§{e['box'][0]:.1f}|{e['box'][1]:.1f}§ {e['text']}"} for e in out]


def parse_entry(text: str) -> dict:
    box = re.match(r'^§x§([\d.]+)\|([\d.]+)§\s*', text)
    text = text[box.end():]
    text = re.sub(r'(?<=[a-zčćšžđ])-\s+(?=[a-zčćšžđ])', '', text)               # "ro- đen"
    text = re.sub(rf'(?<=[{U}])-\s+(?=[{U}])', '', text)                        # "MIHAJ- LO"
    text = re.sub(rf'(?<=[{U}])l(?=[{U}]|\b)', 'I', text[:60].replace('Ö', 'O')) + text[60:]   # "MlCO", "ClC", "RAJKÖ"
    nick = r'\s*(?:\(([^)]*)\)|([A-ZČĆŽŠĐ][a-zčćžšđ]+))?'                   # "IRFAN (Babo)", "MIRKO Caruga"
    tail = r"\s*[,.'^]*\s+(?=[a-zčćšžđ]|U\s|[A-ZČĆŽŠĐ][a-zčćžšđ]|\d|\.)(.*)$"
    m = re.match(rf'^([{U}12][{U}12 ]*?)\s*\(([^)]*?)(?:\)|j\s|\s)\s*([{U}1][{U}1\- ]*?)?{nick}{tail}', text)
    if m:                                                                     # "GOLIC (Joeej MOJSIJE, ro-": a lost bracket
        last, father, names, info = m.group(1), m.group(2), (m.group(3) or '').split(), m.group(6)
        names += [m.group(4) or m.group(5)] if (m.group(4) or m.group(5)) else []
    else:                                                                     # "NIKOLIĆ BOŠKO, rođen", "KLJAJIC RADE, Srbin"
        m = re.match(rf'^([{U}1][{U}1]+)\s+([{U}1][{U}1\- ]*?){nick}{tail}', text)
        if not m:
            return {}
        last, father, names, info = m.group(1), '', m.group(2).split(), m.group(5)
        names += [m.group(3) or m.group(4)] if (m.group(3) or m.group(4)) else []
    last = title_case(last.replace(' ', '').replace('1', 'I').replace('2', 'Ž'))   # "J AN JUS" = Janjus, "HAD2I..."
    father = re.sub(r'[^A-Za-zČĆŽŠĐčćžšđ]', '', father)
    father = re.sub(r'e[ej]$', 'e', father)                                     # "Mustafej", "Joeej": the bracket read as j
    names = [n.replace('1', 'I') for n in names]
    given = title_case(names[0]) if names else ''
    alias = ' '.join(title_case(w) for w in names[1:])
    given, _, dash = given.partition('-')                                       # "PERO-MUKONJA"
    alias = alias or dash.title()
    info = info.strip()
    info = re.sub(r'^\.?zv\.\s*„([^"“”]+)["“”]\s*', lambda k: f'zvani {k.group(1)}; ', info)
    if alias:
        info = f'zvani {alias}; ' + info
    rec = _record(last, given, father, info)
    rec['middle_name'] = father
    rec['_box'] = (float(box.group(1)), float(box.group(2)))
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """"Kljajič" = Kljajić: the scan's č for ć at a name's end, where the other units know the name only with ć."""
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    seen = Counter()
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('/proleterski-bataljon-bk-soldiers.json'):
            for r in json.load(open(f, encoding='utf-8')):
                seen[r.get('last_name') or ''] += 1
    for s in soldiers:
        s['pdf_x_end'], s['pdf_y_end'] = s.pop('_box')
        name = s['last_name']
        if name.endswith('ič') and seen[name[:-1] + 'ć'] >= 5 and seen[name[:-1] + 'ć'] >= 5 * seen[name]:
            s['last_name'] = name[:-1] + 'ć'
            s['full_name'] = s['full_name'].replace(name, s['last_name'], 1)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/proleterski-bataljon-bk.pdf',
        brigade_code=163,
        output_path='website/public/proleterski-bataljon-bk-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
