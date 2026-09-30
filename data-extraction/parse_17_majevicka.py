"""
Parser: 17. majevička NOU brigada (brigade code 29) — the fallen and died, with the 3rd Majevica NOP detachment.

Source: "Sedamnaesta majevička NOU brigada" (grupa autora), chapter "Spisak boraca Trećeg majevičkog NOP odreda
        i 17. majevičke NOU brigade poginulih i umrlih u NOR"
        znaci.org/00003/567_2.pdf  →  website/public/pdfs/17-majevicka.pdf
Single column, Latin. pp. 2-60 the list, a letter heading per letter group.
    ADŽIĆ (RADENKO) NEDELJKO, rođen 1927. godine u selu Drežnik, opština Titovo Užice. U brigadu ...
    ZIVANOVIC (SAVO) DANICA zv. SEKA, rođena 1923. godine u Sremskoj Mitrovici. ...
    ABRUĆ IBRAHIM. U brigadu došao marta 1945. godine. ...
The father (in brackets) is printed in the nominative. An entry's first line is indented ~19pt; the rest
start at the page's margin.
"""
import json
import re
from collections import Counter, defaultdict

from _margin_entries import fix_caps_head, lone_names_to_given
from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser, title_case

MARK = '⁣'
U = 'A-ZČĆŽŠĐ'
_margin: dict = defaultdict(lambda: 1e9)


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        if len(ln['text'].strip()) > 20:                      # body lines, not letter headings or page numbers
            key = (ln.get('file'), ln['page'])
            _margin[key] = min(_margin[key], ln['x'])


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or re.fullmatch(r'[A-Za-zČĆŽŠĐčćžšđ]', t):     # page numbers, letter headings
        return False
    if ln['page'] == 2 and ln['y'] < 420:                      # the chapter title
        return False
    t = fix_caps_head(t)                                       # "AKARATOVlC" -> AKARATOVIC
    t = re.sub(rf'\b(?=[{U}l]*[{U}][{U}l]*l)(?=(?:[{U}]*l){{0,2}}[{U}]*\b)[{U}l]{{3,}}\b',   # "ZlVAN" -> ZIVAN
               lambda m: m.group(0).replace('l', 'I'), t)
    t = re.sub(rf'^([{U}]{{2,}}) [—–-] ([{U}]{{2,}})(?=\s*\()', r'\1-\2', t)   # "LUKIĆ — VEJNOVIĆ (VOJO) DRAGOMIR"
    # a surname the OCR spaced out: "MI JATO VIĆ (BOŠKO)", "GOSPA VIĆ", "II AL ANO VIĆ"
    t = re.sub(rf'^((?:[{U}]{{1,6}} ){{1,3}})(VIĆ|VIC|IĆ|IC)\b', lambda m: m.group(1).replace(' ', '') + m.group(2), t)
    indented = ln['x'] > _margin[(ln.get('file'), ln['page'])] + 10
    # a surname and a bracketed father start an entry wherever the line sits ("VEJNOVIĆ (VOJO) DRAGOMIR")
    if indented and re.match(rf'^[{U}]{{2,}}', t) or re.match(rf'^[{U}]{{3,}}(?:-[{U}]+)?\s*\([{U}]{{2,}}\)', t):
        t = re.sub(r'^(\S+)', r'\1' + MARK, t, count=1)
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    """SURNAME [(FATHER)] [dr] GIVEN [NICK | zv. NICK][ — Rus], bio. The name ends at a comma, a full stop, a dash
    or "iz"/"rođen"; "(prezime nepoznato)" marks an unknown surname ("JOVANKA (prezime nepoznato), Sremica")."""
    text = text.replace(MARK, '').translate(str.maketrans('ÀÈÌÒÙàèìòù', 'AEIOUaeiou'))
    # not at "zv." or after an initial ("KOPRIVA F. HAMZA")
    end = re.search(r',|(?<!\s[A-ZČĆŽŠĐ])(?<!zv)\.\s|\s[—–]\s|\s(?=iz\s|rođen)|\.$', text)
    head, bio = (text[:end.start()], text[end.end():].strip()) if end else (text, '')
    prefix = []
    father = ''
    unknown_surname = re.search(r'\((?:prezime nepoznato|nepoznato prezime)\)', head, re.I)
    head = re.sub(r'\((?:prezime nepoznato|nepoznato prezime)\)', '', head, flags=re.I)
    m = re.search(r'\(([^)]*)\)', head)
    if m:
        inside = m.group(1).strip().replace('0', 'O')
        if re.fullmatch(rf'[{U}][{U}a-zčćžšđ\-]*', inside):
            father = inside
        else:                                                           # "(supruga dr Vladimira)": a note
            prefix.append(inside)
        head = head[:m.start()] + ' ' + head[m.end():]
    if re.search(r'\bdr\b\.?', head, re.I):
        prefix.append('dr')
        head = re.sub(r'\bdr\b\.?', ' ', head, flags=re.I)
    nick = re.search(rf'\bzv\.\s*([{U}][^\s]*)', head)
    if nick:
        prefix.append('zvani ' + title_case(nick.group(1)))
        head = head[:nick.start()] + head[nick.end():]
    toks = [re.sub(r'^2', 'Ž', t) for t in head.split()]                  # "2IVAN": Ž read as 2
    if unknown_surname:
        last, given = '', toks
        prefix.append('prezime nepoznato')
    else:
        last, given = (toks[0] if toks else ''), toks[1:]
    if not father and len(given) > 1 and re.fullmatch(rf'[{U}]\.?', given[0]):   # "KOPRIVA F. HAMZA"
        father = given.pop(0).rstrip('.')
    if len(given) > 1:                                                    # "CVIJETIN CETO": a nickname
        prefix.append('zvani ' + ' '.join(title_case(g) for g in given[1:]))
    info = '; '.join(prefix + ([bio] if bio else []))
    return _record(last, given[0] if given else '', title_case(father), info)


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', 'tuzlanski-odred-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    # one-name entries ("OBRAD. Rodom iz Livna", "DINO — ITALIJAN") are given names
    return lone_names_to_given(repair_lj_ocr(restore_diacritics(soldiers)), *name_counts())


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/17-majevicka.pdf',
        brigade_code=29,
        output_path='website/public/17-majevicka-soldiers.json',
        start_page=2,
        end_page=60,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        prepare_fn=prepare,
        post_fn=post,
    )
