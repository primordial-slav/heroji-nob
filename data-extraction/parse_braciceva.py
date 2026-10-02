"""
Parser: Bračičeva brigada (brigade code 69).

Source: Mirko Fajdiga, "Bračičeva brigada na Štajerskem, Koroškem in Gorenjskem", II. del (Knjižnica NOV in POS, 1994;
        znaci.org 00003/775.pdf)  →  website/public/pdfs/braciceva.pdf (PDF pages 304-374 of the book):
    pp. 1-24    Padli borci (od ustanovitve brigade do osvoboditve), 503 names, one wide column
    pp. 25-71   Borci, ki so vojno preživeli, 1,720 names, two columns
The name in capitals, a hanging indent; "*" before the birth, "†" (read as t, f or +) before the death:
    ACMAN JURIJ, * 1913, Brezje, Mozirje, kmet; † 15. 9. 1944, ...
    BRDNIK JOŽE, * 1916, Smrečno, Slovenska Bistrica; Planica, Fram, kmet; † 1986      (died after the war)
An entry starts at the column's margin (measured near the line, as in _slovene_lists); the capitals the scan
garbled ("pgVEC", "ZI KER", "IVlARČIČ") are read back where the corpus knows the result.
"""
import re

from _parser_scaffold import _record, repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, columns_reader, given_names, surnames_and_places

U, L = 'A-ZČĆŽŠĐÖÜ', 'a-zčćžšđöü'
FALLEN_TO = 24
INDENT = Indent(padli_from=None, headings=re.compile(r'^(?:PADLI BORCI|BORCI, KI SO|\(Od ustanovitve)'))


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """The fallen in one column, the survivors in two."""
    lines = columns_reader(1)(pdf_path, start_page, min(end_page or 10 ** 6, FALLEN_TO))
    if not end_page or end_page > FALLEN_TO:
        lines += columns_reader(2)(pdf_path, max(start_page, FALLEN_TO + 1), end_page)
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t) or INDENT.headings.match(t) or t.startswith(('* * *', 'Poudarjamo')):
        return False
    if ln['page'] == 71 and ln['y'] > 230:                                   # the editors' afterword under the last names
        return False
    head = re.sub(r'^[^\w]+', '', t)
    caps = re.match(rf'^[{U}{L}/§]?[{U}][{U}lI1.\'’\- ]{{1,}}', head)
    named = re.match(rf'^[{U}]{{2,}}[{U}\-]*\s+[{U}]{{2,}}[{U}\-]*(?:-[{U}][{L}]+)?\s*[,*(;]', head)   # "DERNAČ IVAN, * 1915"
    if (ln['x'] < INDENT.margin(ln) + 4 and caps and sum(c.isupper() for c in head[:6]) >= 3) or named:
        t = ('§p§ ' if ln['page'] <= FALLEN_TO else '§s§ ') + head
    ln['text'] = t
    return True


def caps_word(w: str) -> str:
    """A capitalized word the scan garbled: a lowercase or stray first letter, l or 1 for I, a dot inside."""
    w = re.sub(r'^[§/]', '', w)
    w = re.sub(rf'^[{L}](?=[{U}]{{2}})', lambda m: m.group(0).upper(), w)    # "pgVEC"
    return w.replace('l', 'I').replace('1', 'I').replace('.', '').replace("'", '')


def split_name(head: str) -> tuple[str, str, list[str]]:
    notes = []
    head = re.sub(r'[‐‑–]', '-', head.replace('­', ''))
    head, _, other = head.partition(';')                                     # "VERA-Nuša; por. Vošnjak"
    if other.strip():
        notes.append(other.strip())
    m = re.search(r'\(([^)]*)\)', head)                                       # "MUNDA JELICA (Angelca Brumec)"
    if m:
        notes.append('ili ' + m.group(1).strip())
        head = head[:m.start()] + head[m.end():]
    if re.search(r'\bdr\.', head):
        notes.append('dr.')
        head = re.sub(r'\s*\bdr\.\s*', ' ', head)
    alias = ''
    m = re.search(rf'-([{U}][{L}I]*[{L}][{L}I]*(?:\s[{U}][{L}]+)?)\s*$', head)   # "BATIC TONE-Gojko", "SLAVKO-MaIi"
    if m:
        alias, head = re.sub(rf'(?<=[{L}])I', 'l', m.group(1)), head[:m.start()]
    toks = [caps_word(w) for w in head.split()]
    toks = [w for w in toks if w]
    sur, _ = surnames_and_places()
    for k in (3, 2):                                                         # "TO VORN IK JOŽE", "ZI KER AVGUST"
        if len(toks) > k and (sur[''.join(toks[:k]).title()] or (k == 2 and len(toks[1]) <= 3)):
            toks[:k] = [''.join(toks[:k])]
            break
    if len(toks) > 2 and given_names()[''.join(toks[1:]).title()] >= 3:
        toks[1:] = [''.join(toks[1:])]                                        # "STA NIS LAV" = Stanislav
    last = toks[0].title() if toks else ''
    given = ' '.join(w.title() for w in toks[1:])
    if '-' in given and not alias:                                          # "IVAN-VANJA", "SLAVKO-MaIi"
        given, alias = given.split('-', 1)
        alias = alias.replace('-', ' ').strip()
    alias = re.sub(r'(?<=[a-zčšž])I', 'l', alias).title() if alias else alias
    if alias:
        notes.append('zvani ' + alias)
    return last, given, notes


def parse(text: str) -> dict:
    fell = text.startswith('§p§')
    text = re.sub(r'^§[ps]§\s*', '', text)
    text = re.sub(r'(?<=[;,.\s])[tf+]\s(?=(?:\d|[a-zčšž]+ \d|okoli|de|po|1))', '† ', text)   # the dagger the scan misread
    head, _, rest = text.partition(',')
    if '*' in head:                                                           # "PREZL dr. * ..." without a comma
        head, _, more = head.partition('*')
        rest = '*' + more + (',' + rest if rest else '')
    last, given, notes = split_name(head)
    rest = re.sub(r'\s+', ' ', re.sub(r'­\s*', '', rest)).strip().lstrip(',').strip()   # soft hyphens at line ends
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    born = re.match(r'^\*\s*(?:(1[89]\d\d)\b,?\s*)?([^;]*)', rest)
    if born:
        if born.group(1):
            rec['birth_year'] = born.group(1)
        place = []
        for seg in born.group(2).split(','):                                 # "Brezje, Mozirje, kmet": the place, then the trade
            seg = re.sub(r'\s+\d+[a-z]?$', '', seg.strip())                   # "Hrvatini 44": no house number
            if not re.match(rf'^[{U}]', seg) or re.search(r'\d', seg):
                if re.fullmatch(rf'[{L}][{L} ]{{2,30}}', seg) and place:     # "kmet", "kmečki sin", "dijak"
                    rec['occupation'] = seg
                break
            place.append(seg)
        if place:
            rec['birth_place'] = ', '.join(place[:2])
    if fell:
        rec['death_type'] = 'poginuo'
        m = re.search(r'†\s*((?:\d{1,2}\.\s*\d{1,2}\.\s*)?1?9\d\d|[a-zčšž]+\s+19\d\d|19\d\d)\s*,?\s*(.*)', rest)
        if m:
            rec['death_date'] = re.sub(r'\s+', ' ', m.group(1))
            place = re.sub(r'^(?:v|pri|na|nad|pod)\s+', '', m.group(2).strip(' ,.'))
            if place and len(place) < 60:
                rec['death_place'] = place
    return rec


if __name__ == '__main__':
    OWN['file'] = 'braciceva-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/braciceva.pdf',
        brigade_code=69,
        output_path='website/public/braciceva-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=keep,
        post_fn=repair_lj_ocr,
    )
