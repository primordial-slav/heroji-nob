"""
Parser: 1. kosovsko-metohijska NOU brigada (brigade code 77).

Source: Milutin Milković, "Prva kosovsko-metohijska brigada" (znaci.org 00001/185_15.pdf, its pages 1-33, book
        pp. 351-383)  →  website/public/pdfs/1-kosovsko-metohijska.pdf. Two columns throughout, five lists:
    a  pp. 1-15     the fighters of the Kosovo-Metohija battalions "Boro Vukmirović" and "Ramiz Sadiku" (from whose
                    survivors the brigade was formed on 24 June 1944), then those who joined in June-August 1944
                        Ajtić Predrag, rođen 1921. u Prizrenu. Srbin, student. U NOB-i od 1941., nos. „PS 1941".
                    (entries are paragraphs: flush lines, a gap between entries)
    b  pp. 16-18    those who joined from Poreče and around Tetovo in September 1944, with their village
                        Georgijevski Marko, Grešnevo
                    and, at the foot of p. 18, those whose names or villages were not fully known
                        Abdulah iz sela Debrište
    c  pp. 19-24    those who joined from Junik, Dečani, Peć and Drenica from late October 1944: names only
    d  pp. 24-30    the fallen (from half-way down p. 24), a hanging indent
                        Avramovski Đorđe, poginuo 22. 10. 1944., Junik.
    e  pp. 31-33    the wounded, names only (written "ranjen" in the bio)
A list's letter headings ("A)", "dž)") and the prose between lists are left out.
"""
import re

from _parser_scaffold import _record, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
W = rf'[{U}][{L}]+(?:-[{U}][{L}]+)?'                                         # a capitalized word


def kind(page: int, y: float) -> str:
    """Which list a line on this page and height belongs to."""
    if page <= 15:
        return 'a'
    if page <= 18:
        return 'b2' if page == 18 and y > 410 else 'b'
    if page < 24 or (page == 24 and y < 380):
        return 'c'
    if page <= 30:
        return 'd'
    return 'e'


_state = {'prev': None, 'single': False}
_margin: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        if kind(ln['page'], ln['y']) == 'd' and re.match(rf'^{W}', ln['text'].strip()):
            key = (ln['page'], ln['x'] >= 150)
            _margin[key] = min(_margin.get(key, 1e9), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    k = kind(ln['page'], ln['y'])
    prev = _state['prev']
    _state['prev'] = ln
    if ln['page'] == 1 and ln['y'] < 195:
        return False                                                         # the heading and the note under it
    if re.fullmatch(r'[\d\W]{1,5}|\W*\w{1,2}\s*\)\s*', t) or re.fullmatch(r'(?:[A-ZČĆŽŠĐ]|Lj|Nj|Dž|dž|č|ć|š|ž|y)\s*\)?', t):
        return False                                                         # page numbers, "A)", "dž)", "y)" (У)
    new_col = prev is None or prev['page'] != ln['page'] or ln['y'] < prev['y'] - 5
    if k == 'a':
        if not re.search(r'\d|rođen|NOB|Srbin|Crnogor|Albanac|Slovenac|Hrvat|Makedon|Italijan|Jevrej|Musliman|[a-zčćžšđ]{4}', t):
            return False                                                     # a lone "V" heading
        if ((new_col or ln['y'] - prev['y'] > 15) and re.match(rf'^{W}\s+(?:[{U}]\.\s*)?{W}(?:\s+{W})?\s*(?:,|rođen)', t)) \
                or re.match(rf'^{W}\s+(?:[{U}]\.\s*)?{W}(?:\s+{W})?\s*,\s*rođen', t):          # "Đukić Ilija, rođen" after a short gap
            t = '§a§ ' + t
        elif re.match(r'^(?:Spisak boraca|kosovsko metohijskih|„Boro|u sastavu Prve|narodnooslobodila|Od preživelih|ljona 24|rodno oslobod|U periodu|\(Albanija|4, na Karaormanu|ši i sledeći)', t):
            return False
    elif k in ('b', 'b2', 'c', 'e'):
        if k == 'b2' and re.match(rf'^(?:{W}(?:\s+{W})?)\s+(?:iz\s+sela\s+{W}|selo\s+nepoznato)', t):
            t = '§b§ ' + t
        elif k == 'b' and re.fullmatch(rf'{W}(?:\s+{W})?(?:\s+{W})?,\s*{W}(?:\s+\w+)*', t):
            t = '§b§ ' + t
        elif k in ('c', 'e') and re.fullmatch(rf'{W}(?:\s+\(\w\))?(?:\s+{W}){{0,2}}', t):
            single = ' ' not in t
            if single and _state['single'] and not new_col:                 # "Jockić / Aleksandar": one name
                _state['single'] = False
                ln['text'] = t
                return True
            _state['single'] = single
            t = f'§{k}§ ' + t
        else:
            return False                                                     # the prose between the lists
    elif k == 'd':
        if re.match(r'^(?:U borbama koje|na, odnosno Prve|SU:|ci kosovsko|ijske NOU brigade)', t):
            return False
        if re.match(rf'^{W}\s+{W}', t) and ln['x'] <= _margin.get((ln['page'], ln['x'] >= 150), ln['x']) + 5:
            t = '§d§ ' + t                                                   # the fallen: a hanging indent
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    k = text[1:text.index('§', 1)]
    text = re.sub(r'^§\w+§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Pri- zrenu"
    text = text.replace('Pye.', 'Rus.')                                     # "Рус" read as Latin look-alikes
    if k == 'a':
        m = re.match(rf'^((?:{W}|[{U}]\.)(?:\s+(?:{W}|[{U}]\.)){{1,3}})\s*(?:,\s*|\s+(?=rođen))(.*)$', text)   # "Cergolj Albin rođen"
        head, rest = (m.group(1), m.group(2)) if m else text.partition(',')[::2]
        toks = head.split()
        notes = []
        initial = [t for t in toks[1:2] if re.fullmatch(rf'[{U}]\.', t)]       # "Mitrović I. Milan"
        toks = [t for t in toks if t not in initial]
        alias = re.match(rf'^\s*({W}\s+{W})\s*,\s*', rest)                    # "Radović Pavle, Radić Pavle, rođen"
        if alias and not re.match(r'rođen', alias.group(1)):
            notes.append('ili ' + alias.group(1))
            rest = rest[alias.end():]
        if len(toks) > 2:
            notes.append('zvani ' + ' '.join(toks[2:]))                       # "Bulatović Velimir Veljo"
        rec = _record(toks[0], toks[1] if len(toks) > 1 else '', initial[0] if initial else '', '; '.join(notes + [rest.strip()]))
        y = re.search(r'rođen[a]?\s+(1[89]\d\d)', rest)
        if y:
            rec['birth_year'] = y.group(1)
        return rec
    if k == 'b':
        m = re.match(rf'^({W})(?:\s+({W}))?\s*,?\s*(.*)$', text)
        last, given, rest = m.group(1), m.group(2) or '', m.group(3).strip()
        if re.match(r'^iz\s+sela', rest) and not given:                       # "Abdulah iz sela Debrište": a given name
            last, given = '', last
        return _record(last, given, '', rest)
    toks = text.split()
    toks = [t for t in toks if not re.fullmatch(r'\(\w\)', t)]               # "Azi (z) Sulja"
    rec = _record(toks[0] if toks else '', ' '.join(toks[1:]), '', '')            # "Uka Đon Lazar"
    if k == 'd':
        m = re.search(r',|\s(?=poginu|umr)', text)                            # "Petrovski Jovan poginuo 23. 9. 1944."
        head, rest = (text[:m.start()], text[m.end():]) if m else (text, '')
        h = head.split()
        rec = _record(h[0], ' '.join(h[1:2]), '', '; '.join((['zvani ' + ' '.join(h[2:])] if len(h) > 2 else [])
                                                             + ([rest.strip().rstrip('.')] if rest.strip() else [])))
        rec['death_type'] = 'poginuo'
    elif k == 'e':
        rec['additional_info'] = '; '.join(p for p in (rec['additional_info'], 'ranjen') if p)
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-kosovsko-metohijska.pdf',
        brigade_code=77,
        output_path='website/public/1-kosovsko-metohijska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='cyrillic',
        entry_start_re=re.compile(r'^§\w+§'),
        parse_entry_fn=parse,
        line_filter=keep,
    )
