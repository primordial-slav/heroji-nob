"""
Parser: Prva slovenska artilerijska brigada (brigade code 71).

Source: Borivoj Lah-Boris, "Prva slovenska artilerijska brigada" (Knjižnica NOV in POS 23/1, Ljubljana 1975;
        znaci.org 00003/826.pdf)  →  website/public/pdfs/1-slovenska-artilerijska.pdf (PDF pages 389-405 of the book):
    pp. 1-4     Seznam starešin: the staffs, each post with its holders and dates (not read: they are in the roster)
    pp. 5-15    Seznam topničarjev, two columns
    pp. 16-17   Seznam padlih, two columns
A soldier a line, the birthplace run on to a line set in; "roj." is "rojen", born, not a maiden name:
    Ambrožič Jože, roj. 1915
        Podgrad
    Gimpelj Franc, padel avgusta
        1944, V. Lipovec
The scan drops the caron of a surname's capital ("Cerne" = Černe, "Saruga" = Šaruga). The lists run in the
Slovene alphabet (C, Č, ... S, Š, ... Z, Ž), so a C, S or Z name printed among the Č, Š or Ž names takes it back.
"""
import re

from _parser_scaffold import _record, run_parser
from _slovene_lists import OWN, Indent, columns_reader, fix_ocr, given_names, name_part

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
PADLI_FROM = 16
HEADINGS = re.compile(r'^(?:SEZNAM|PNIČARJEV|PADLIH)')
INDENT = Indent(padli_from=PADLI_FROM, headings=HEADINGS)
MONTHS = r'(?:januarja|februarja|marca|aprila|maja|junija|julija|avgusta|septembra|oktobra|novembra|decembra)'
SMALL_WORDS = ('v', 'na', 'ob', 'pri', 'pod', 'nad', 'in')


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'\d{1,3}\*?|\W+', t) or HEADINGS.match(t):              # page numbers, "26*", the headings ("1944," stays)
        return False
    if ln['x'] < INDENT.margin(ln) + 5 and re.match(rf'^(?:[{U}]|[šžčć][{L}])', t):
        t = ('§p§ ' if ln['page'] >= PADLI_FROM else '§s§ ') + t
    ln['text'] = t
    return True


def place(s: str) -> str:
    """'Ret j e' = Retje: letters the scan spaced apart go back on the word."""
    toks: list[str] = []
    for w in s.split():
        if toks and re.fullmatch(rf'[{L}]{{1,2}}', w) and w not in SMALL_WORDS:
            toks[-1] += w
        else:
            toks.append(w)
    return ' '.join(toks).strip(' ,.')


def parse(text: str) -> dict:
    fell = text.startswith('§p§')
    text = fix_ocr(re.sub(r'^§[sp]§\s*', '', text))
    text = re.sub(r'\broj[,.]\s*', 'roj. ', text)                              # "roj, 1923"
    text = re.sub(r'\b19(\d)[.,](\d)\b', r'19\1\2', text).replace('194A', '1944')   # "194.4", "194A"
    text = re.sub(r'\s+', ' ', text).strip()
    head, comma, rest = text.partition(',')
    if not comma:                                                            # "Cik dr. Rudi Celje": no comma
        m = re.match(rf'^(\S+\s+(?:dr\.\s+)?\S+)\s+((?:roj\.|pad(?:el|la)\b|[{U}]).*)$', head)
        if m:
            head, rest = m.group(1), m.group(2)
    last, given, notes = name_part(head.strip())
    given = given.rstrip('.')                                                # "Kozina Jože. Novo mesto"
    rest = rest.strip()
    rec = _record(last, given, '', '; '.join(notes + ([rest] if rest else [])))
    born = re.match(r'^roj\.\s*(?:(1[89]\d\d)\b[.,]?\s*)?([^,]*?)\s*(?:,|$)', rest)      # "roj. 1921, D. Briga"
    if born:
        if born.group(1):
            rec['birth_year'] = born.group(1)
        bp = place(re.split(r'\s(?=pad(?:el|la)\b)', born.group(2))[0])
        if bp and re.match(rf'^[{U}]', bp) and not re.search(r'\d', bp):
            rec['birth_place'] = bp
    if fell:
        rec['death_type'] = 'poginuo'
        m = re.search(rf'(?:\bpad(?:el|la)\s+|^|,\s*)({MONTHS}\s+)?(19[34]\d)\b[.,]?\s*(.*)$', rest)
        if m:
            rec['death_date'] = (m.group(1) or '') + m.group(2)
            dp = place(m.group(3))
            if dp and re.match(rf'^[{U}]', dp) and not re.search(r'\d', dp):
                rec['death_place'] = dp
    return rec


def _inversions(keys: list[str]) -> int:
    return sum(1 for i, a in enumerate(keys) for b in keys[i + 1:] if b < a)


def caron_block(run: list[dict]) -> int:
    """Where the Č (Š, Ž) names start among a list's C and Č names, in printed order: the split that leaves
    both parts closest to alphabetical order (the book slips here and there: "Sršen", "Sprajcer"). len(run)
    when the names read as one alphabetical run."""
    keys = [s['last_name'][1:].lower() + ' ' + s['first_name'].lower() for s in run]
    whole = _inversions(keys)
    best, at = whole, len(run)
    for k in range(1, len(run)):
        cost = _inversions(keys[:k]) + _inversions(keys[k:])
        if cost < best:
            best, at = cost, k
    return at if best * 3 < whole else len(run)                              # a clear second run, not noise


def carons(soldiers: list[dict]) -> list[dict]:
    """In each list (roster, fallen), the C, S and Z names printed after the list has moved on to Č, Š or Ž take
    the caron back ("Cvetko", then "Cakarevič" = Čakarevič). A given name the corpus doesn't know as printed,
    but well with a caron, too."""
    n = 0
    for fallen in (False, True):
        listed = [s for s in soldiers if (s['pdf_page'] >= PADLI_FROM) == fallen]
        for plain, caron in (('C', 'Č'), ('S', 'Š'), ('Z', 'Ž')):
            run = [s for s in listed if s['last_name'][:1] in (plain, caron)]
            for s in run[caron_block(run):]:
                if s['last_name'][:1] == plain:
                    s['last_name'] = caron + s['last_name'][1:]
                    n += 1
    for s in soldiers:
        g = s['first_name']
        caron = {'C': 'Č', 'S': 'Š', 'Z': 'Ž'}.get(g[:1])
        if caron and not given_names()[g] and given_names()[caron + g[1:]] >= 10:
            s['first_name'] = caron + g[1:]
            n += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['first_name']) if p)
    print(f'  carons restored in {n} names')
    return soldiers


if __name__ == '__main__':
    OWN['file'] = '1-slovenska-artilerijska-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/1-slovenska-artilerijska.pdf',
        brigade_code=71,
        output_path='website/public/1-slovenska-artilerijska-soldiers.json',
        start_page=5,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=keep,
        post_fn=carons,
    )
