"""
Parser: 19. sjevernodalmatinska divizija (brigade code 79).

Source: Dragutin Grgurević, "Devetnaesta sjevernodalmatinska divizija" (znaci.org 00003/575.pdf, PDF pages 257-303,
        book pp. 253-299)  →  website/public/pdfs/19-sjevernodalmatinska.pdf:
    "Popis poginulih i umrlih boraca Devetnaeste sjevernodalmatinske divizije od formiranja do kraja rata", two columns,
    a hanging indent; surname and given name in capitals, the father (genitive) or an initial between them:
        ALAVANJA Ante SAVA, iz Donjeg Karina, u borbi kod Plitvičkog Leskovca, 30. III 1945.
        BABIĆ MILKA, iz Benkovca, u borbi za Gračac, 16. IV 1944.
The bio has no "poginuo": the parser sets the death (type, date, and the place of the battle in the nominative, where
the place is known to the other units).
"""
import re

from _parser_scaffold import _record, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROMAN = re.compile(r'^[IVX]+$')
_starts: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault((ln['page'], ln['x'] > 250), []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    xs = sorted(x for y, x in _starts.get((ln['page'], ln['x'] > 250), []) if abs(y - ln['y']) <= 80)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 3:
            return x
    return xs[0] if xs else ln['x']


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] <= 2 or re.fullmatch(r'[\d\W]{1,5}|\w{1,2}', t):
        return False                                                         # the heading and the author's note; "A", "ž"
    first = t.split()[0] if t.split() else ''
    if ln['x'] <= margin(ln) + 4 and re.match(rf'^[{U}]{{2,}}', first) and not ROMAN.match(first.rstrip('.,')):
        t = '§p§ ' + t
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}]{{2,}}(?:[- ][{U}]{{2,}})*?)\s+(?:([{U}][{L}]+(?:-[{U}][{L}]+)?|[{U}]\.)\s+)?([{U}]{{2,}}(?:-[{U}]{{2,}})?)((?:\s+[{U}]{{2,}})*)\s*,?\s*(.*)$')
DATE = re.compile(r'(\d{1,2}\.\s*[IVX]+\.?\s*1?9\d\d|[a-zčćžšđ]+\s+19\d\d|19\d\d)\.?\s*$')


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Su- šaka"
    text = re.sub(r'\bboibi\b|\bboribi\b', 'borbi', text)
    text = text.replace('&', '').replace("'", '').replace('’', '').replace('ü', 'u').replace('ä', 'a')
    text = re.sub(rf'(?<=[{U}])2|2(?=[{U}])', 'Ž', text)                        # "RU2IČIĆ"
    text = re.sub(rf'(?<=[{U}])1|1(?=[{U}])', 'I', text)                        # "ŠVERD1JA"
    text = re.sub(rf'^([{U}]{{2,}}) ([{U}]{{1,3}})(?=\s)', r'\1\2', text)        # "ŠVERDI JA"
    text = re.sub(rf'\b([{U}][{L}]{{0,4}}) ([{L}]{{1,4}})\b(?=\s+[{U}]{{2}})', r'\1\2', text)   # "Tri vuna", "Has ana" (the father)
    m = NAME.match(text)
    if not m:
        head, _, rest = text.partition(',')
        toks = head.split()
        rec = _record(toks[0].title() if toks else '', ' '.join(t.title() for t in toks[1:]), '', rest.strip())
    else:
        last, father, given, nick, rest = m.groups()
        notes = ['zvani ' + nick.strip().title()] if nick.strip() else []
        rec = _record(last.title(), given.title(), father or '', '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
        text = rest
    rec['death_type'] = 'umro' if re.search(r'\bumr(?:o|la)\b', text) else 'poginuo'
    d = DATE.search(text.rstrip(' .:'))
    if d:
        rec['death_date'] = re.sub(r'\s+', ' ', d.group(1))
    b = re.search(rf'\bu\s+borbi\s+((?:za|kod|na|u)\s+[{U}][^,(]*?)\s*(?:\(|,|\s+\d|$)', text)
    if b:
        rec['_battle'] = b.group(1).strip()
    return rec


def places(soldiers: list[dict]) -> list[dict]:
    """The place of the battle, "u borbi kod Plitvičkog Leskovca" = Plitvički Leskovac, where the nominative is a
    place the other units know (extract_structured_fields.Extractor.nominative)."""
    import sys
    sys.path.insert(0, 'scripts')
    import extract_structured_fields as esf
    ex = esf.build_extractor(esf.load_live())
    for s in soldiers:
        phrase = s.pop('_battle', '')
        if phrase:
            known = ex._known(re.sub(r'^(?:za|kod|na|u)\s+', '', phrase), locative=True)   # a place the other units know
            if known:
                s['death_place'] = known
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/19-sjevernodalmatinska.pdf',
        brigade_code=79,
        output_path='website/public/19-sjevernodalmatinska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='latin',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=places,
    )
