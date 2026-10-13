"""
Parser: 51. vojvođanska udarna divizija (brigade code 111), second book: the fallen of the whole division.

Source: Sreta Savić, "51. vojvođanska divizija" (znaci.org 00001/152; the list is bound into 152_7.pdf after the last
chapter, its PDF pp. 74-144, book pp. 219-288) → website/public/pdfs/51-divizija-savic.pdf. "Spisak poginulih boraca i
rukovodilaca 51. vojvođanske udarne divizije od dana formiranja 1. novembra 1944. godine do kraja rata 15. maja 1945.
godine", Latin, one column, numbered afresh under each heading: SEDMA, OSMA, DVANAESTA, ČETRNAESTA (slovačka) and
ARTILJERIJSKA BRIGADA, PRIŠTAPSKE JEDINICE:
    16. ANDRIC BORIVOJ, 1927, Srbobran, St. Bečej, borac, poginuo 16. 11. 1944. u s. Batina.
    1. BESLIN Dušana ŽARKO, 1918, Uljma, Bela Crkva, borac — telef. bat. za vezu, poginuo u Somboru 19. 11. 1944.
The name in capitals, the father in the genitive (title case) or an initial between surname and given name; the scan
loses carons ("ANDRIC", "KOV AC"), which the corpus gives back (parse_8_kordunaska_divizija.post). Each record gets
its brigade (unit_detail) and birth year (the field extractor reads the rest); the author's note after the list is not
read.
The book's first list (Božić's Batina, parse_51_divizija.py) keeps its IDs; these get 0111010001 on, and the same man
in both is merged (scripts/find_source_duplicates.py), and linked to his record in the 7., 8. and 12. vojvođanska
(units 22, 78, 75) by the link pass.
"""
import re

import parse_51_divizija as b51
import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEADINGS = {'SEDMABRIGADA': '7. vojvođanska brigada', 'OSMABRIGADA': '8. vojvođanska brigada',
            'DVANAESTABRIGADA': '12. vojvođanska brigada', 'ČETRNAESTABRIGADA': '14. vojvođanska (slovačka) brigada',
            'ARTILJERIJSKABRIGADA': 'artiljerijska brigada', 'PRIŠTAPSKEJEDINICE': 'prištapske jedinice'}
_state = {'unit': '', 'note': False}
SPELLED = {'VELIMI!?': 'VELIMIR'}                                           # read from the page image
GIVEN = {'Dužan': 'Dušan'}                                                  # ž for š


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if _state['note'] or t.startswith('NAPOMENA'):
        _state['note'] = True                                                # the author's note ends the list
        return False
    squeezed = re.sub(r'\s+', '', t)
    if squeezed in HEADINGS:
        _state['unit'] = HEADINGS[squeezed]
        return False
    if re.fullmatch(r'\d{1,3}', t) or (ln['page'] == 1 and not _state['unit']):
        return False                                                         # page numbers; the list's title
    # "16. ANDRIC", and as the scan has some: "66 BOROJEV" (no dot), "16.-KONDAC", "B62. KOVACEVIĆ"
    m = re.match(r'^(\d{1,3})\.\s*(?=[A-ZČĆŽŠĐ])', t) or re.match(r'^[A-Z]?(\d{1,3})(?:\.[-\s]*|\s+)(?=[A-ZČĆŽŠĐ]{2})', t)
    if m:
        t = f"§d§{_state['unit']}§ " + t[m.end():]
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    m = re.match(r'^§d§([^§]*)§\s*', text)
    unit, text = (m.group(1), text[m.end():]) if m else ('', text)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "pogi- nuo", "Stari Be- čej"
    # the name ends at a comma, or at the birth year after a full stop or nothing ("KRAINOVIĆ DUŠAN. 1925",
    # "SABO Đure DURA 1924")
    m = re.match(r'^(.*?)(?:,|\.(?=\s+1[89]\d\d\b)|\s+(?=1[89]\d\d\b))', text)
    head, info = (m.group(1), text[m.end():]) if m else (text, '')
    info = info.strip(' ,').rstrip('.').strip() + '.' if info.strip(' ,') else ''
    for bad, good in SPELLED.items():
        head = head.replace(bad, good)
    # the scan's specks in a name: a stop inside or after a word ("VUČA.N", "ANDRE.JA", "CISLER. JOVAN"), "ie" for
    # IĆ ("STOJAKOVie"), "2" for Ž ("2IVA"), a dash between two surnames ("VOJNIĆ — HAJDUK"), an ending in brackets
    # ("ATANACKOV (IC)")
    head = re.sub(rf'(?<=[{U}])\.(?=[{U}])|(?<=[{U}]{{2}})\.(?=\s)', '', head).replace('À', 'A')
    head = re.sub(rf'(?<=[{U}]{{3}})ie\b', 'IĆ', head)
    head = re.sub(rf'\b2(?=[{U}]{{2}})', 'Ž', head)
    head = re.sub(r'\s*[—–]\s*', '-', head)
    head = re.sub(r'\s*\((I[CĆ])\)', r'\1', head)
    # another surname or a nickname in brackets: "PARTALOV (PARTALA) M. MILOŠ", "BURIK Adama PALJO (BENJA)"
    m = re.search(r'\s*\(([^)]+)\)', head)
    if m:
        after_surname = len(head[:m.start()].split()) == 1
        head = head[:m.start()] + head[m.end():]
        info = (f'prezime i {m.group(1).title()}; ' if after_surname else f'zvani {m.group(1).title()}; ') + info
    # "l" and "1" for I inside a word in capitals ("ZlVAN", "ARClC", "PAVL1K")
    words = [re.sub('[l1]', 'I', w) if re.fullmatch(rf'[{U}][{U}l1]*[{U}]', w) else w for w in head.split()]
    # the surname in capitals ("KOV AC", "ARN AUTO VIČ" spaced apart; once in title case, "Ljutica ZlVAN"), then the
    # father: an initial ("A.") or a genitive in title case ("Dušana"), then the given name in capitals
    father_at = next((i for i, w in enumerate(words) if i and re.fullmatch(rf'[{U}]\.|[{U}][{L}]+', w)), None)
    if father_at is not None:
        last = k8.join_parts(words[:father_at], 'last_name')
        father = words[father_at]
        given = ' '.join(words[father_at + 1:])
    elif len(words) >= 2:
        last = k8.join_parts(words[:-1], 'last_name') if len(words) > 2 else words[0]
        father, given = '', words[-1]
    else:
        last, father, given = (words[0] if words else ''), '', ''
    rec = _record(k8.caps_word(last) if last.isupper() else last, GIVEN.get(given.title(), given.title()), father, info)
    y = re.match(r'(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    if unit:
        rec['unit_detail'] = unit
    # birthplace, duty and death are read from the entry by scripts/extract_structured_fields.py (the place of death
    # in the nominative: "na Batini", "kod Koprivnice")
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """The corpus's spellings (parse_8_kordunaska_divizija.post), but never one with fewer carons than the book prints
    ("VUČA.N" stays Vučan though the corpus knows only "Vucan"); and a given name in D that the corpus spells with Đ
    at least twice as often is Đ ("DURA": Đura 200, Dura 69 in the other books' scans, which lose the Đ too)"""
    fields = ('last_name', 'first_name', 'middle_name')
    for s in soldiers:
        s['_printed'] = {f: s[f] for f in fields}
    soldiers = k8.post(soldiers)
    for s in soldiers:
        for f in fields:
            was = s['_printed'][f]
            if k8.fold(was) == k8.fold(s[f]) and k8.marks(was) > k8.marks(s[f]):
                s[f] = was
            if f != 'last_name' and s[f][:1] == 'D':
                cands = k8._spell['first_name'].get(k8.fold(s[f]), {})
                dj = 'Đ' + s[f][1:].upper()
                if cands.get(dj, 0) >= 2 * cands.get(s[f].upper(), 0) and cands.get(dj, 0) >= 5:
                    s[f] = 'Đ' + s[f][1:]
        del s['_printed']
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def corpus() -> None:
    """The other units' spellings (parse_51_divizija.corpus), and Božić's list of the same division, which prints many
    of these men with the carons this scan lost (Čik, Šisler, Čapko)"""
    import json
    b51.corpus()
    for s in json.load(open('website/public/51-divizija-soldiers.json', encoding='utf-8')):
        if s.get('pdf_file') == '51-divizija.pdf':
            for f in k8._spell:
                if s.get(f):
                    k8._spell[f][k8.fold(s[f])][s[f].upper()] += 3      # the same men: weigh them over other books


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/51-divizija-savic.pdf',
        brigade_code=111,
        output_path='website/public/51-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§d§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
