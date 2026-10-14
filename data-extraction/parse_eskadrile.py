"""
Parser: 1. i 2. eskadrila NOVJ (the RAF's 352 and 351 (Yugoslav) Squadrons; brigade code 139).

Source: Predrag Pejčić, "Prva i druga eskadrila NOVJ" (Beograd 1991; znaci.org 00001/115), the appendix "Spisak
        ljudstva 1. i 2. eskadrile NOVJ" (115_14.pdf → website/public/pdfs/eskadrile-novj.pdf, book pp. 331-354): the
        squadrons' people, the first squadron, then the second, then "Neutvrđena identifikacija", names whose
        squadron the author could not establish. Its last pages are the book's contents.
Two columns, Latin, every line flush left; an entry starts with the surname and the given name in capitals and,
for most, the service number, then rank, duty, birth and how the man came to the squadrons (from the Middle East,
from Italian captivity, from the country):
    BARUCA JOSIP 791326, desetar, avio-mehaničar, rođen 1922. u Koštabani kod Kopra, došao sa Bliskog istoka 1944.
The last list gives names only, one a line. The squadron goes to unit_detail. The scan reads "rođen" as "roden" and I
as 1 in names ("CIGL1Č").
"""
import re

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}1\-]*'
COLUMN_SPLIT = 110
SECTIONS = {'PRVA ESKADRILA NOVJ': '1. eskadrila NOVJ (352. skvadron)', 'DRUGA ESKADRILA NOVJ': '2. eskadrila NOVJ (351. skvadron)',
            'NEUTVRĐENA IDENTIFIKACIJA': 'eskadrila neutvrđena'}
# the name in capitals, then the service number (after a full stop, or on the next line), a comma or the rank
START = re.compile(rf'^{CAPS}(?:\s+{CAPS})+(?:\.?\s+\d{{4,6}}|\s*,|\s+[{L}(]|$)')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    lines = sorted(lines, key=lambda l: (l['page'], l['x'] > COLUMN_SPLIT, l['y']))
    out, section = [], ''
    for ln in lines:
        t = ln['text'].strip()
        if re.match(r'^Spisak ljudstva|^1\. i 2\. eskadrile', t):
            continue
        head = next((k for k in SECTIONS if t.startswith(k)), None)
        if head:
            section = SECTIONS[head]
            t = t[len(head):].strip()                       # a heading and the first entry on one line
            if not t:
                continue
            ln = dict(ln, text=t)
        ln['section'] = section
        out.append(ln)
    return out


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t):
        return False
    names_only = ln['section'] == 'eskadrila neutvrđena' and re.fullmatch(rf'{CAPS}(?:\s+{CAPS})+', t)
    new = bool(START.match(t)) or bool(names_only)
    ln['text'] = (f"§x§{ln['section']}§ " if new else '') + t
    return True


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([^§]*)§\s*', text)
    section = m.group(1) if m else ''
    text = text[m.end():] if m else text
    text = re.sub(rf'(?<=[{U}])1(?=[{U}]|\b)', 'I', text)                   # "CIGL1Č"
    nm = re.match(rf'^((?:{CAPS}\s+)*{CAPS})\s*(\d{{4,6}})?[.,]?\s*', text)
    words = nm.group(1).split() if nm else []
    info = text[nm.end():] if nm else text
    if nm and nm.group(2):
        info = f'{nm.group(2)}, {info}'                                     # the service number
    info = re.sub(r'\broden(a?)\b', r'rođen\1', info).strip().rstrip('.')
    last, given = (words[:1], words[1:2]) if len(words) > 1 else (words, [])
    nick = words[2:]
    if nick:
        info = 'zvani ' + ' '.join(nick).title() + '; ' + info
    rec = _record(' '.join(last), ' '.join(given), '', info)
    rec['unit_detail'] = section
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/eskadrile-novj.pdf',
        brigade_code=139,
        output_path='website/public/eskadrile-novj-soldiers.json',
        start_page=1,
        end_page=24,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
