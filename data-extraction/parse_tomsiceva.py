"""
Parser: Tomšičeva brigada, 1. SNOUB "Tone Tomšič" (brigade code 70).

Source: Franci Strle, "Tomšičeva brigada" (Knjižnica NOV in POS), the rosters at the end of its four books:
    knj. 1 (znaci.org 00003/790.pdf, PDF pp. 535-543)  →  tomsiceva-1.pdf: the units the brigade grew from, the
                                                           udarna grupa of the 3. bataljon Ljuba Šercerja, Daki's
                                                           leteča udarna patrulja, the Proletarska udarna patrulja
                                                           and četa (pp. 1-3), and the 1. slovenski proletarski
                                                           udarni bataljon Toneta Tomšiča (pp. 5-9; p. 4 is blank)
    knj. 2 (znaci.org 00003/787.pdf, PDF pp. 840-871)  →  tomsiceva-2.pdf: 16 July 1942 - 13 July 1943
    knj. 3 (00003/792.pdf, pp. 646-649)                →  tomsiceva-3.pdf: names left out of knj. 2's list
    knj. 4 (00003/788.pdf, pp. 573-678)                →  tomsiceva-4.pdf: 13 July 1943 - 1 April 1944 (pp. 1-48),
                                                                           1 April 1944 - 15 May 1945 (pp. 49-106)
One wide column, a soldier a line, no commas; "*" before the birth, "†" (read as 1, t, f or +, or glued to the year,
"11943") before the death:
    Abina Jože * 1925 Log † 1944 Pohorje Resnik
    Bizjak Marija-Micka, por. Zakotnik * 1922 ...
A soldier in several periods is printed in each list: find_source_duplicates merges them.
Knj. 1 prints the dagger without a year too ("t Beograd") and leaves three men out of the site: Maček Alojz
("pobegnil-izdajalec"), Škrlj Domin ("pobegnil, padel pri begu") and Zalar Tone-Anton ("pobegnil"), who deserted.
Run with book numbers (`python parse_tomsiceva.py 1`) to read only those books: their records alone are replaced.
"""
import sys
import re

from _parser_scaffold import _record, repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, fix_ocr, name_part

U, L = 'A-ZČĆŽŠĐÖÜ', 'a-zčćžšđöü'
INDENT = Indent(padli_from=None, headings=re.compile(r'^(?:SEZNAM BORCEV|ZA [CČ]AS OD|za čas od|seznama 2\. knjige|\d+\.? (?:JULIJA|APRILA))'))
DAGGER = re.compile(r'\s(?:[1tf+†]\s?|1(?=19\d\d))(?=(?:19[1-9]\d|po osvoboditvi|po vojni)\b)')


FOOTNOTE: dict = {}                                                          # page -> y of the note under the list
BOOK1 = {'on': False}                                                        # reading knj. 1


# knj. 1's OCR: lost carons (the places as the other books and the list's own lines print them), a split word
BOOK1_WORDS = [('Lj ubijana-Gal j evica', 'Ljubljana-Galjevica'), ('194G', '1946'), ('Sentjošt', 'Šentjošt'),
               ('Crna vas', 'Črna vas'), ('Crni vasi', 'Črni vasi'), ('Zelimlje', 'Želimlje'), ('Skrilje', 'Škrilje'),
               ('-škofljica', '-Škofljica'), ('-Skofja', '-Škofja'), ('-Zumberk', '-Žumberk'), ('Sodrašica', 'Sodražica'),
               ('Lužajih', 'Lužarjih'), ('Jože-Crni', 'Jože-Črni'), ('Zagarjev', 'Žagarjev'), ('Zan-Boris', 'Žan-Boris'),
               ('Ivan-Zan ', 'Ivan-Žan '), ('Jožc-', 'Jože-')]
# surnames whose first caron the OCR lost, by the list's order (Cvar, Čampa; Šparovec, Štupica) and the other books
BOOK1_SURNAMES = {'Campa': 'Čampa', 'Sile': 'Šile', 'Smuc': 'Šmuc', 'Soba': 'Šoba', 'Stupica': 'Štupica',
                  'Zgonee': 'Zgonec', 'Zmuc': 'Žmuc', 'Zorž': 'Žorž', 'Zur': 'Žur', 'Konig': 'König',
                  'Bognadovič': 'Bogdanovič'}


def book1_line(t: str) -> str:
    """Knj. 1's slips: "® 1920" and "i: 1918" for the birth's star, "-f 1943" and a dagger before a place alone."""
    for a, b in BOOK1_WORDS:
        t = t.replace(a, b)
    t = re.sub(r'\s(?:®|i:)\s', ' * ', t)
    t = re.sub(r'\s-[tf]\s(?=19\d\d)', ' † ', t)
    return re.sub(rf'(?<=\s)[tf+](?=\s[{U}])', '†', t)                       # "ujet t Beograd", "f Dachau"


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if BOOK1['on']:
        if re.fullmatch(rf'[{U}\W\d ]+', t) and re.search(rf'[{U}]{{3}}', t):     # "PROLETARSKE UDARNE PATRULJE"
            return False
        t = ln['text'] = book1_line(t)
    if re.match(r'^\*\s*(?:Seznam|Borci)', t):                               # "* Seznam je delo komisije ...": the note
        FOOTNOTE[ln['page']] = ln['y']
    if ln['page'] in FOOTNOTE and ln['y'] >= FOOTNOTE[ln['page']] - 1:
        return False
    if re.fullmatch(r'[\d\W]{1,5}', t) or INDENT.headings.match(t) or t.startswith('* '):
        return False
    named = re.match(rf'^[{U}][{L}]+ [{U}][{L}]+(?:-\S+)?(?:,[^*]*)? \*', t)          # "Adamič Viktor-Zmago * 1903", skewed in
    if (ln['x'] < INDENT.margin(ln) + 4 and re.match(rf'^(?:[{U}]|[šžčć][{L}])', t)) or (named and ln['x'] < INDENT.margin(ln) + 30):
        t = '§s§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = fix_ocr(re.sub(r'^§s§\s*', '', text))
    text = DAGGER.sub(' † ', ' ' + text).strip()
    head, star, rest = text.partition('*')
    death = ''
    if not star:                                                             # no birth: "Andoljšek Franc Ribnica † 1943"
        head, _, death = text.partition('†')
        m = re.match(rf'^(\S+\s+\S+(?:-\S+)?)\s+(.*)$', head.strip())
        head, place_only = (m.group(1), m.group(2)) if m else (head, '')
        rest = place_only
    else:
        rest, _, death = rest.partition('†')
    last, given, notes = name_part(head.strip().rstrip(','))
    notes = [n.rstrip(' ,') for n in notes]                                  # "Valerija-Zmaga, por. ..."
    given = given.strip(' ,_.')
    given = given[:1].upper() + given[1:]                                    # "janez"
    rest, death = rest.strip(), death.strip()
    info = ' '.join(p for p in (('* ' + rest) if star and rest else rest, ('† ' + death) if death else '') if p)
    rec = _record(last, given, '', '; '.join(notes + ([info] if info else [])))
    m = re.match(r'^(1[89]\d\d)\b\s*(.*)$', rest)
    birth_place = m.group(2) if m else rest
    if m:
        rec['birth_year'] = m.group(1)
    birth_place = re.sub(r'\s+\d+[a-z]?$', '', birth_place).strip(' ,')     # "Dolenja vas 16": no house number
    if birth_place and re.match(rf'^[{U}]', birth_place) and not re.search(r'\d', birth_place):
        rec['birth_place'] = birth_place
    d = re.match(r'^(19[1-9]\d)(?:\s*[-—]\s*19\d\d)?\s*(.*)$', death)
    if d and int(d.group(1)) <= 1945:                                      # died in the war; "† po osvoboditvi" did not
        rec['death_type'] = 'poginuo'
        rec['death_date'] = d.group(1)
        if d.group(2) and re.match(rf'^[{U}]', d.group(2)):
            rec['death_place'] = d.group(2).strip(' ,')
    return rec


DESERTED = re.compile(r'(?<!ujet, )\bpobegnil\b|izdajalec')
# The lists print in bold the men of the units each grew from (the footnotes): in the first, the udarna grupa and
# the two patrols, the rest only in the Proletarska udarna četa; in the second, the četa and the units before it.
# znaci re-typeset the book from its OCR, which kept the bold on the first list's pages and lost most of it on the
# second's (p. 5 has none), so there it tells nothing
BOOK1_UNITS = [(4, 'Udarna grupa 3. bataljona Ljuba Šercerja, Dakijeva leteča in Proletarska udarna patrulja',
                'Proletarska udarna četa'),
               (99, '1. slovenski proletarski udarni bataljon Toneta Tomšiča',
                '1. slovenski proletarski udarni bataljon Toneta Tomšiča')]


def bold_starts(pdf_path: str) -> dict:
    """(page, y) of each line whose first two words are set in bold."""
    import pdfplumber
    from pdf_coords import viewer_words
    bold = {}
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            rows: dict = {}
            for w in viewer_words(page, extra_attrs=['fontname']):
                rows.setdefault(round(w['top']), []).append(w)
            for y, ws in rows.items():
                ws.sort(key=lambda w: w['x0'])
                bold[(n, y)] = all('Bold' in w['fontname'] for w in ws[:2])
    return bold


def book1_post(soldiers: list[dict]) -> list[dict]:
    out = []
    bold = bold_starts(BOOKS[1][0])
    for s in repair_lj_ocr(soldiers):
        info = s['additional_info'] = s.get('additional_info', '').replace(', Živel', ', živel')   # fix_ocr's capital
        if DESERTED.search(info):
            print('  deserted, left out:', s['last_name'], s['first_name'])
            continue
        last, given = BOOK1_SURNAMES.get(s['last_name'], s['last_name']), s['first_name']
        if given.startswith('('):                                            # "Jelen (drugi podatki neznani) † 1943"
            info, given = f'{given} {info}'.strip(), ''
        elif last == 'Adolf-Adi':                                            # "Adolf-Adi Morost": a given name alone
            last, given, info = '', 'Adolf', f'zvani Adi; {given}, {info}'
        elif '(' in given:                                                   # "Veršnik Rok (Rajko)-Gašper"
            given, alias = given.split('(', 1)
            given, info = given.strip(), f'({alias}; {info}'
        s['last_name'], s['first_name'], s['additional_info'] = last, given, info
        s['full_name'] = f'{last} {given}'.strip()
        # the birthplace before ", ujet", ", pogrešan", ", živel" and "(samo udarna grupa)"; the place of death too
        m = re.match(r'^\*?\s*(?:1[89]\d\d|192-|\(\?\))?\s*([^†(]*)', info.split('; ')[-1])
        place = re.split(r',\s*(?:ujet|pogrešan|živel)\b', m.group(1))[0].strip(' ,')
        if last and place and re.match(rf'^[{U}]', place) and not re.search(r'\d', place):     # not "Adolf: Morost"
            s['birth_place'] = place
        else:
            s.pop('birth_place', None)
        if s.get('death_place'):
            s['death_place'] = re.split(r'\s*\(', s['death_place'])[0]
        first = [b for (p, y), b in bold.items() if p == s['pdf_page'] and abs(y - s['pdf_y']) <= 3]
        early, rest = next((e, r) for p, e, r in BOOK1_UNITS if s['pdf_page'] < p)
        s['unit_detail'] = early if first and first[0] else rest
        out.append(s)
    return out


BOOKS = {
    1: ('website/public/pdfs/tomsiceva-1.pdf', 200001),
    2: ('website/public/pdfs/tomsiceva-2.pdf', 1),
    3: ('website/public/pdfs/tomsiceva-3.pdf', 10001),
    4: ('website/public/pdfs/tomsiceva-4.pdf', 100001),
}

if __name__ == '__main__':
    OWN['file'] = 'tomsiceva-soldiers.json'
    for book in [int(a) for a in sys.argv[1:]] or sorted(BOOKS):
        pdf, id_start = BOOKS[book]
        BOOK1['on'] = book == 1
        INDENT.cols.clear()
        INDENT.split.clear()
        FOOTNOTE.clear()
        run_parser(
            pdf_path=pdf,
            brigade_code=70,
            output_path='website/public/tomsiceva-soldiers.json',
            start_page=1,
            end_page=None,
            layout='single',
            extract_fn=columns_reader(1),
            script='latin',
            entry_start_re=re.compile(r'^§s§'),
            parse_entry_fn=parse,
            prepare_fn=INDENT.prepare,
            line_filter=keep,
            post_fn=book1_post if book == 1 else repair_lj_ocr,
            id_start=id_start,
            keep_other_sources=True,
        )
