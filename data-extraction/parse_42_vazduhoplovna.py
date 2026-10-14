"""
Parser: 42. vazduhoplovna divizija (brigade code 140).

Source: Predrag Pejčić, "42. vazduhoplovna divizija" (znaci.org 00001/238), the appendix "Spisak ljudstva 42.
        vazduhoplovne divizije po pukovima i ostalih jedinica" (238_16.pdf → website/public/pdfs/42-vazduhoplovna.pdf,
        book pp. 291-321): the division's people by its staff and attached units, its regiments (421., 422. ...) and
        the mobile aircraft workshop. Its last two pages are the book's contents.
Two columns, Latin, each entry hanging (its first line some 13pt left of the lines under it), the surname and the
given name in capitals, a father's initial between them, then rank and duty:
    MARIČIĆ R. NIKOLA, mlađi vodnik, radio-telegrafist
    RADOVANOVIĆ Ing. MIODRAG, poručnik, načelnik meteorološke službe i Meteorološkog biroa
The unit an entry stands under goes to unit_detail. The scan spaces some surnames apart ("STE VANO VIĆ").
"""
import re

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]*'
COLUMN_SPLIT = 110                 # the left column's lines start at x 14-32, the right column's at 185-205
HEADING = re.compile(r'(?:PUK|JEDINIC|RADIONIC|ESKADRIL|DIVIZIJ|BATALJON|ČETA|ODELJENJ|BAZA|ŠTAB|PARM|POZADINSK|POKRETN|AEROPLANSK)')
_left: dict = {}


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t))


def heading(t: str) -> bool:
    """A unit's heading in capitals ("421. VAZDUHOPLOVNI PUK", "POKRETNA AEROPLANSKA" / "RADIONICA (PARM I)"); not a
    line of an entry that ends on "PARM" ("spec. PARM")"""
    return not re.search(rf'[{L},]', t) and bool(HEADING.search(t)) and len(t) >= 10


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    lines = sorted(lines, key=lambda l: (l['page'], l['x'] > COLUMN_SPLIT, l['y']))
    out, section = [], ''
    for ln in lines:
        t = ln['text'].strip()
        if re.match(r'^Spisak ljudstva|^divizije\d*$', t):
            continue                                                   # the appendix's title
        if heading(t):
            # a heading broken over two lines ("POKRETNA AEROPLANSKA" / "RADIONICA (PARM I)") runs on
            section = (section + ' ' + t) if out and out[-1].get('heading') and out[-1]['page'] == ln['page'] else t
            out.append({'heading': True, 'page': ln['page'], 'text': '', 'x': ln['x'], 'y': ln['y']})
            continue
        ln['section'] = section
        out.append(ln)
    return [ln for ln in out if not ln.get('heading')]


def measure(lines: list[dict]) -> None:
    for ln in lines:
        if re.match(rf'^{CAPS}', ln['text'].strip()) and not page_number(ln['text']):
            key = (ln['page'], ln['x'] > COLUMN_SPLIT)
            _left[key] = min(_left.get(key, 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if page_number(t):
        return False
    new = ln['x'] < _left.get((ln['page'], ln['x'] > COLUMN_SPLIT), 0) + 7 and bool(re.match(rf'^{CAPS}', t))
    ln['text'] = (f"§x§{ln['section']}§ " if new else '') + t
    return True


def join_split(words: list[str]) -> list[str]:
    """A surname the text spaced apart: "STE VANO VIĆ STEVAN" = Stevanović Stevan (only where more than two words
    stand in capitals, so "BABIĆ TOMA" stays two)"""
    words = list(words)
    while len(words) > 2:
        i = next((i for i in range(len(words) - 1)
                  if len(words[i]) <= 3 or len(words[i + 1]) <= 3 or re.fullmatch(r'O?V?IĆ', words[i + 1])), None)
        if i is None:
            break
        words[i:i + 2] = [words[i] + words[i + 1]]
    return words


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([^§]*)§\s*', text)
    section = m.group(1).strip() if m else ''
    text = text[m.end():] if m else text
    text = re.sub(rf'([{U}]{{2,}})-\s+([{U}]{{2,}})', r'\1\2', text)        # "ALEKSAN- DAR" broken over two lines
    head, _, info = text.partition(',')
    words = head.replace('.', '. ').split()
    title = [w for w in words if re.fullmatch(r'(?:Ing|ing|dr|Dr)\.?', w)]
    words = [w for w in words if w not in title]
    initial = [w for w in words if re.fullmatch(rf'[{U}][{L}]?\.', w)]
    caps = join_split([w for w in words if re.fullmatch(CAPS, w) and w not in initial])
    last, given = (caps[:1], caps[1:2]) if len(caps) > 1 else (caps, [])
    nick = caps[2:]
    info = info.strip().rstrip('.')
    if nick:
        info = 'zvani ' + ' '.join(nick).title() + '; ' + info
    if title:
        info = title[0].lower().rstrip('.') + '.; ' + info
    rec = _record(' '.join(last), ' '.join(given), initial[0] if initial else '', info)
    if section:
        detail = section[:1] + section[1:].lower()
        rec['unit_detail'] = re.sub(r'\bparm( i+)?\b', lambda m: m.group(0).upper(), detail)   # "(PARM III)"
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/42-vazduhoplovna.pdf',
        brigade_code=140,
        output_path='website/public/42-vazduhoplovna-soldiers.json',
        start_page=1,
        end_page=29,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
