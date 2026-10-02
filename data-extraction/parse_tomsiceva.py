"""
Parser: Tomšičeva brigada, 1. SNOUB "Tone Tomšič" (brigade code 70).

Source: Franci Strle, "Tomšičeva brigada" (Knjižnica NOV in POS), the rosters at the end of three of its four books:
    knj. 2 (znaci.org 00003/787.pdf, PDF pp. 840-871)  →  tomsiceva-2.pdf: 16 July 1942 - 13 July 1943
    knj. 3 (00003/792.pdf, pp. 646-649)                →  tomsiceva-3.pdf: names left out of knj. 2's list
    knj. 4 (00003/788.pdf, pp. 573-678)                →  tomsiceva-4.pdf: 13 July 1943 - 1 April 1944 (pp. 1-48),
                                                                           1 April 1944 - 15 May 1945 (pp. 49-106)
One wide column, a soldier a line, no commas; "*" before the birth, "†" (read as 1, t, f or +, or glued to the year,
"11943") before the death:
    Abina Jože * 1925 Log † 1944 Pohorje Resnik
    Bizjak Marija-Micka, por. Zakotnik * 1922 ...
A soldier in several periods is printed in each list: find_source_duplicates merges them.
"""
import re

from _parser_scaffold import _record, repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, fix_ocr, name_part

U, L = 'A-ZČĆŽŠĐÖÜ', 'a-zčćžšđöü'
INDENT = Indent(padli_from=None, headings=re.compile(r'^(?:SEZNAM BORCEV|ZA [CČ]AS OD|za čas od|seznama 2\. knjige|\d+\.? (?:JULIJA|APRILA))'))
DAGGER = re.compile(r'\s(?:[1tf+†]\s?|1(?=19\d\d))(?=(?:19[1-9]\d|po osvoboditvi|po vojni)\b)')


FOOTNOTE: dict = {}                                                          # page -> y of the note under the list


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.match(r'^\*\s*Seznam', t):                                         # "* Seznam je delo komisije ...": the note
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


BOOKS = [
    ('website/public/pdfs/tomsiceva-2.pdf', 1),
    ('website/public/pdfs/tomsiceva-3.pdf', 10001),
    ('website/public/pdfs/tomsiceva-4.pdf', 100001),
]

if __name__ == '__main__':
    OWN['file'] = 'tomsiceva-soldiers.json'
    for pdf, id_start in BOOKS:
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
            post_fn=repair_lj_ocr,
            id_start=id_start,
            keep_other_sources=id_start > 1,
        )
