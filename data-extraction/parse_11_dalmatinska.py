"""
Parser: 11. dalmatinska (biokovska) udarna brigada (brigade code 53).

Source: Milan Rako, Slavko Družijanić, "Jedanaesta dalmatinska udarna brigada" (znaci.org 00003/547.pdf), "Popis
        boraca Jedanaeste dalmatinske udarne brigade" (book pp. 479-600)  →  website/public/pdfs/11-dalmatinska.pdf
        (PDF pages 467-587 of the book): pp. 1-26 "Poginuli borci", 27 "Nestali borci", 28-121 "Preživjeli borci
        brigade (na dan 15. maja 1945)".
Two columns, Latin, a hanging indent; znaci.org re-typeset the book from its OCR:
    BANDELJ (Alojza) FRANC, desetar u 1. č. 5. bat., r. 12. 6. 1913, Zavino, Ajdovščina, zemljoradnik, u NOB od
    14. 9. 1943, NOP-u pristupio jula 1943. Poginuo u borbi s Nijemcima za Ston, 17. 10. 1944.
The father's name (genitive) in brackets; a woman's other surname after a hyphen (BAČIĆ-SURJAN); a nickname after
the given name and a hyphen (DANE-Velega).
"""
import re

from _parser_scaffold import extract_lines_two_column, parse_standard_entry, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEADINGS = re.compile(r'^(?:POPIS BORACA JEDANAESTE DALMATINSKE|UDARNE BRIGADE|POGINULI BORCI|NESTALI BORCI|'
                      r'PREŽIVJELI BORCI BRIGADE|\(na dan 15\. maja 1945\)|NESTALI|BORCI|POGINULI|PREŽIVJELI|BORCI BRIGADE)$')
_margin: dict = {}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    by_col: dict = {}
    for ln in lines:
        if re.match(rf'^[{U}]{{2}}', ln['text']):
            by_col.setdefault((ln['page'], ln['x'] > 250), []).append(ln['x'])
    for col, xs in by_col.items():
        _margin[col] = min(xs)
    return lines


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 26:
        return False                                                         # a table of the fallen by battle and battalion
    if HEADINGS.match(t) or re.fullmatch(r'[\d\W]{1,5}', t):
        return False
    margin = _margin.get((ln['page'], ln['x'] > 250), ln['x'])
    if ln['x'] <= margin + 4 and re.match(rf'^[{U}]', t):
        t = '§x§ ' + t                                                       # an entry starts at the column's edge
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    head, comma, tail = text.partition(',')
    if comma and re.match(r'\s*\(', tail):
        head, comma, tail = text.partition(', (')[0] + ' (', '', text.partition(', (')[2]   # "Papalin, (Marka)"
        text = head + tail
    text = re.sub(r'\(l([a-zčćžšđ])', r'(I\1', text)                          # "(lbre)" = Ibre
    text = re.sub(r'\(([šžčćđ])', lambda m: '(' + m.group(1).upper(), text)   # "(štipana)"
    text = re.sub(r'\s+,', ',', text)                                         # "Stjepana , KARMELA"
    text = re.sub(r'\)\s*,\s*(?=[A-ZČĆŽŠĐ]{2})', ') ', text)                     # "(Stjepana), KARMELA"
    text = text.replace('(Ornerà)', '(Omera)').replace('(Pavia)', '(Pavla)')
    first = text.split(' ', 1)[0]
    letters = [c for c in first if c.isalpha()]
    if len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) >= 0.6 and not re.fullmatch(
            r'[A-ZČĆŽŠĐ\-]+-[A-ZČĆŽŠĐ][a-zčćžšđ]+', first):
        text = first.upper().replace('1', 'I') + text[len(first):]          # "BACiĆ-OLIĆ", "VOLAREV1C"
    name, comma, rest = text.partition(',')
    name = re.sub(rf'(?<=[{U}])l(?=[{U}])', 'I', name)                       # "ZlVOTA"
    prefix = []
    # a Korčula house name after the surname: "BOROVINA Lušica (Nikole) BERNARDO", "ANDRIJIĆ-Ćućera (Antuna) IVAN"
    hm = re.match(rf'^([{U}][{U}\-]*[{U}])(?:-|\s)([{U}][{L}]+)\s+(?=\(|[{U}][{L}]+\s+[{U}]{{2,}}|[{U}]{{2,}})', name)
    if hm and not (name[hm.end(1)] == ' ' and re.match(rf'[{U}][{L}]+\s+[{U}]{{2,}}\s*$', name[hm.end(1):].strip())):
        prefix.append('zvani ' + hm.group(2))
        name = hm.group(1) + ' ' + name[hm.end():]
    dr = re.search(r'\sdr\.?\s', name)
    if dr:
        name = name[:dr.start()] + ' ' + name[dr.end():]
        prefix.append('dr.')
    # "BANDELJ (Alojza) FRANC" → "BANDELJ Alojza FRANC"; "ALKALAJ (M.) BEBA"
    name = re.sub(rf'^([{U}][{U}\-]+(?:\s[{U}]{{2,}})?)\s*\(([{U}][{L}]+(?:\s+i\s+[{U}][{L}]+)?|[{U}]\.)\)\s*', r'\1 \2 ', name)
    sm = re.match(rf'^([{U}]+) ([{U}]+) (?=[{U}][{L}]+\.? [{U}]{{2,}})', name)   # "ALA VANJA Sime MARKO"
    if sm:
        a, b = sm.groups()
        name = (a + b if min(len(a), len(b)) <= 3 else f'{a}-{b}') + ' ' + name[sm.end():]
    nm = re.search(rf'(\s[{U}]{{2,}})\s*(-+)\s*([{U}][{U}{L}]+)\s*$', name)    # "DANE-Velega", "LUCIJA--CETI", "LUCI-JA"
    if nm:
        if nm.group(2) == '-' and nm.group(3).isupper() and len(nm.group(3)) <= 3:
            name = name[:nm.start()] + nm.group(1) + nm.group(3)                # a name split at the line's end
        else:
            name = name[:nm.start()] + nm.group(1)
            prefix.append('zvani ' + (nm.group(3).title() if nm.group(3).isupper() else nm.group(3)))
    rec = parse_standard_entry(name.strip() + comma + rest)
    if prefix:
        rec['additional_info'] = '; '.join(prefix) + '; ' + rec['additional_info']
    return rec


BIRTH = re.compile(r'\br\.\s*(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)\b')


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        m = BIRTH.search(s['additional_info'])
        if m and not s['birth_year']:
            s['birth_year'] = m.group(1)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/11-dalmatinska.pdf',
        brigade_code=53,
        output_path='website/public/11-dalmatinska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
