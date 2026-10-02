"""
Parser: 14. hercegovačka (omladinska) NOU brigada (brigade code 81).

Source: "Četrnaesta hercegovačka omladinska brigada" (znaci.org 00001/268_5.pdf, its pages 38-82, book pp. 243-287)
        →  website/public/pdfs/14-hercegovacka.pdf. One column, Latin:
    pp. 1-32    "Spisak boraca koji su prošli kroz 14. hercegovačku (omladinsku) brigadu", a soldier a line:
                    AVDALOVIĆ V. Ljubo, rođen 1925. Drežanj (Nevesinje)
                    BABIĆ Mićo, rođen u selu Trnovica (Bileća)
                    ALEKSIĆ Danilo, Bileća
    pp. 33-45   "Spisak poginulih boraca 14. hercegovačke omladinske NOU brigade" (189 names), a hanging indent:
                    ANDRIĆ R. Mara, rođena 1924. u selu Pijescima (Mostar), politički delegat voda u 1. bataljonu.
                        Poginula u borbi za oslobođenje Konjica, marta 1945.
The surname in capitals, the father's initial and the given name not. The roster lists everyone who served, the fallen
too, so a fallen soldier is in both lists. The text layer splits some surnames ("STANKO VIĆ", "HUB ANA") and given
names ("Tod or", "Fad il"), and reads I as l or 1 inside capitals ("PERlSlĆ", "ĆUK1LO").
The "Komandni sastav" before the roster (book pp. 234-242, names under each duty) is not read.
"""
import re
from collections import Counter
from itertools import product

from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_FROM = 33
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))
        if ln['page'] == 29 and ln['text'].strip() == 'rođen Stolac':       # printed above the line it belongs to
            ln['text'] = ''
        if ln['page'] == 29 and ln['text'].strip() == 'HODZIĆ A. HUSO, 1910.':
            ln['text'] = 'HODZIĆ A. HUSO, rođen 1910. Stolac'


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 80)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 3:
            return x
    return xs[0] if xs else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if not t or re.fullmatch(r'[\d\W]{1,5}|\w{1,2}|\.S 2 25', t):
        return False                                                         # page numbers, the letter headings ("A", "DŽ")
    page = ln['page']
    t = t.replace('Ü', 'U')                                                  # "RÜPER"
    if (page == 1 and (ln['y'] < 150 or ln['y'] > 490)) or (page == FALLEN_FROM and (ln['y'] < 140 or ln['y'] > 510)):
        return False                                                         # the headings and the notes under the lists
    t = re.sub(rf'(?<=[{U}])[l1](?=[{U}])|(?<=[{U}][{U}])[l1]\b', 'I', t)    # "PERlSlĆ", "ĆUK1LO"
    if ln['x'] <= margin(ln) + 4 and re.match(rf'^[{U}]{{2,}}', t):
        t = ('§p§ ' if page >= FALLEN_FROM else '§r§ ') + t
    ln['text'] = t
    return True


SPECIAL = {
    'BAKŠIĆ Šuvalija - Hida': ('BAKŠIĆ', 'Hida', '', ['ili Šuvalija']),
}


def name(head: str) -> tuple[str, str, str, list[str]]:
    """'STANKO VIĆ R. Gojko' -> ('STANKOVIĆ', 'Gojko', 'R.', []); nicknames and other names go to the notes."""
    if head in SPECIAL:
        return SPECIAL[head]
    notes = []
    head = re.sub(r'»([^«]+)«', lambda m: notes.append('zvani ' + m.group(1).strip()) or '', head)
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})?', toks[0]):
        caps.append(toks.pop(0))
    last = ''.join(caps)                                                     # "STANKO VIĆ", "HUB ANA"
    if toks and re.fullmatch(r'\(([^)]+)\)', toks[0]):                       # "MILIĆEVIĆ (Šukić) M. Dušan"
        notes.append('ili ' + toks.pop(0)[1:-1])
    initial = ''
    if toks and re.fullmatch(rf'(?:[{U}]|DŽ|LJ|NJ|Dž|Lj|Nj)\.?', toks[0]):
        initial = toks.pop(0).rstrip('.').title() + '.'
    if toks and re.fullmatch(r'\(([^)]+)\)', toks[0]):                       # "GUZINA S. (Beba) Alka"
        notes.append('zvani ' + toks.pop(0)[1:-1])
    given = toks.pop(0) if toks else ''
    rest = ' '.join(toks)
    alt = re.fullmatch(rf'-\s*([{U}][{L}]+)', rest)                          # "Vlado - Vladimir"
    if alt:
        notes.append('ili ' + alt.group(1))
    elif rest:
        notes.append('zvani ' + rest)                                       # "Boro Borislav", "Jovo Mali"
    return last, given, initial, notes


GENITIVE = {'Stoca': 'Stolac', 'Trebinja': 'Trebinje', 'Trebinju': 'Trebinje', 'Mostara': 'Mostar', 'Bileće': 'Bileća',
            'Nevesinja': 'Nevesinje', 'Konjica': 'Konjic', 'Ljubinja': 'Ljubinje', 'Gacka': 'Gacko', 'Čapljine': 'Čapljina',
            'Sarajeva': 'Sarajevo', 'Metkovića': 'Metković', 'Dubrovnika': 'Dubrovnik'}
NOT_PLACES = {'Italijan'}


def known(phrase: str, ex, own: Counter) -> str:
    '''The nominative of a place printed after "u": this book's own roster spelling first ("u Zasadu" = Zasad), else
    the one the other units know.'''
    best = max((c for c in (' '.join(w) for w in product(*(ex._variants(x) for x in phrase.split()))) if c != phrase and own[c]),
               key=lambda c: own[c], default=None)
    return best or ex._known(phrase, locative=True) or ''


def birthplace(rest: str, ex, own: Counter) -> str:
    """'rođen 1925. Drežanj (Nevesinje)' -> 'Drežanj, Nevesinje'; 'rođen u selu Rapti, Bobani (Trebinje)' -> 'Rapti,
    Trebinje'; a place after "u" or "na" ("u Trebinju", "u Lastvi (Trebinje)") only where the other units know its
    nominative."""
    m = re.match(r'^(?:rođen[a]?|rodom)?\s*(?:(?:1[89]\d\d)[.,]?\s*)?(.*)$', rest)
    place = re.split(r'(?<!\bs)\.\s+(?=[A-ZČĆŽŠĐ])|\.$', m.group(1).strip())[0]
    place = re.sub(r'[\s•\'.,]+$', '', place)
    if ')' in place and '(' not in place:
        place = re.sub(r'\s+(\S+\))$', r' (\1', place)                       # "Rotimlja Stolac)"
    muni = re.search(r'\(([^)]+)\)', place)
    muni = muni.group(1).strip() if muni and re.fullmatch(rf'[{U}][{L}]+(?:\s+[{U}][{L}]+)?', muni.group(1).strip()) else ''
    kod = re.search(rf'\)\s*kod\s+([{U}][{L}]+)$', place)                    # "Rapti, (Bobani) kod Trebinja"
    if kod and kod.group(1) in GENITIVE:
        muni = GENITIVE[kod.group(1)]
    muni = GENITIVE.get(muni, muni)                                          # "(Trebinju)"
    place = re.split(r'\s*\(', place)[0]
    village = re.sub(r'^godine\s+', '', re.split(r',\s*', place)[0].strip())
    kod = re.search(rf'\s+kod\s+([{U}][{L}]+)$', village)                     # "u selu Zasad kod Trebinja"
    if kod:
        muni = muni or GENITIVE.get(kod.group(1), '')
        village = village[:kod.start()]
    prep = re.match(r'^(u\s+(?:selu|zaseoku)|selo|s\.|u|na|iz|od)\s+', village)
    village = village[prep.end():] if prep else village
    if prep and prep.group(1) == 's.' and not muni and len(re.split(r',\s*', place)) == 2:
        muni = re.split(r',\s*', place)[1]                                   # "s. Nanuvići, Trebinje\"
    if not re.fullmatch(rf'[{U}][{L}]+(?:\s+[{U}{L}][{L}]+){{0,2}}', village) or village in NOT_PLACES:
        return ''
    if prep and prep.group(1) in ('u', 'na'):
        village = known(village, ex, own)
    elif prep and prep.group(1).startswith('u ') and not own[village]:
        village = known(village, ex, own) or village                        # "u selu Orahovcu\"
    elif prep and prep.group(1) in ('iz', 'od'):
        return ''                                                            # "rodom iz Bileće", "rodom od Livna"
    if not village:
        return ''
    return village + (', ' + muni if muni and muni != village else '')


def parse(text: str) -> dict:
    kind = text[1]
    text = re.sub(r'^§\w§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "ba- taljona"
    text = text.replace('Ü', 'U').replace('ü', 'u')
    text = re.sub(rf'\b([{U}][{L}]{{1,4}}) ([{L}]{{1,3}})(?=,|\s*$|\s+»)', r'\1\2', text)   # "Tod or", "Fad il", "Ram iz,"
    text = re.sub(rf'(?<=[{U}][{L}])ii\b', 'il', text)                     # "Adii"
    text = re.sub(r'(?<=\s)0\.(?=\s)', 'O.', text)                           # "ŠUNJE 0. Omer"
    m = re.search(r',|\s+(?=rođen|iz\s|rodom|-\s+[A-ZČĆŽŠĐ][a-z]+$)', text)
    head, rest = (text[:m.start()], text[m.end():].strip()) if m else (text, '')
    rest = re.sub(r'^[-–]\s*', '', rest)                                      # "NATALI - Italijan"
    last, given, initial, notes = name(head.strip())
    rec = _record(last, given, initial, '; '.join(notes + ([rest] if rest else [])))
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    rec['_place'] = rest
    if kind == 'p':
        rec['death_type'] = 'umro' if re.search(r'\b(?:[Uu]mr(?:o|la)|[Pp]odlega(?:o|la))\b', rest) and not re.search(r'\b[Pp]oginu', rest) else 'poginuo'
    return rec


def places(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    import extract_structured_fields as esf
    ex = esf.build_extractor(esf.load_live())
    own = Counter()                                                          # the villages the roster prints in the nominative
    for s in soldiers:
        m = re.match(rf'^rođen[a]?\s*(?:1[89]\d\d[.,]?\s*)?(u selu\s+)?([{U}][{L}]+(?:\s+[{U}{L}][{L}]+){{0,2}})\s*(?:,|\(|$)', s['_place'])
        if m and s['pdf_page'] < FALLEN_FROM:
            own[m.group(2)] += 1
    for s in soldiers:
        place = birthplace(s.pop('_place', ''), ex, own)
        if place:
            s['birth_place'] = place
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/14-hercegovacka.pdf',
        brigade_code=81,
        output_path='website/public/14-hercegovacka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§\w§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=places,
    )
