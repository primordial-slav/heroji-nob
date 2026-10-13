"""
Parser: 5. srpska brigada (3. južnomoravska until spring 1944; brigade code 127).

Source: Stanimir Jovanović, Dragoljub Mirčetić, "Peta srpska NOU brigada" (znaci.org 00001/86), the appendices
        (86_13.pdf → website/public/pdfs/5-srpska.pdf): "Prilog br. 2", the list of the brigade's fallen and dead
        fighters and officers (PDF pp. 18-78). "Prilog br. 1" before it (the staffs and commands, in prose) and the
        literature, abbreviations and contents after it are not read.
Cyrillic, one column, each entry hanging (its first line some 24pt left of the lines under it), under letter headings:
    АКСЕНТИЈЕВИЋ Јована МИЛОЉУБ, 1914, Бољковци, Горњи Милановац, земљорадник. У НОВЈ од октобра 1944. године,
    борац 3. батаљона. Рањен у борбама против Немаца, код Шаренграда, на Сремском фронту, и подлегао ранама.
    АДАМОВИЋ ДРАГОСЛАВ, погинуо на Сремском фронту.
A father's name (genitive) or initial stands between the surname and the given name; a nickname follows a dash. The
scan spells some names in Latin look-alikes of the Cyrillic letters ("ABPAMOBHR" = Аврамовић, "MHXHR" = Михић: read
back as in parse_uzicki_odred.decode) and reads Ћ as К, Н or Б at a name's end ("АВРАМОВИН").
"""
import re

from _parser_scaffold import _record, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser
from parse_uzicki_odred import FIRST, LAST, decode

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\->4]+'
_left: dict = {}


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t)) or len(t) <= 2


def entry_like(t: str) -> bool:
    return bool(re.match(rf'^[{U}A-Z]{{3,}}', t))


def measure(lines: list[dict]) -> None:
    for ln in lines:
        t = ln['text'].strip()
        if entry_like(t) and not page_number(t):
            _left[ln['page']] = min(_left.get(ln['page'], 10 ** 6), ln['x'])


def letters(t: str) -> str:
    """Љ and Њ read as "Л>", "Н>" (after transliteration "L>", "H>"), У as Y or ¥"""
    t = re.sub(r'L>(?=[A-ZČĆŽŠĐ¥])', 'LJ', t).replace('L>', 'Lj')
    t = re.sub(r'H>(?=[A-ZČĆŽŠĐ¥])', 'NJ', t).replace('H>', 'Nj')
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])¥|¥(?=[A-ZČĆŽŠĐ])', 'U', t)
    t = re.sub(r'(?:(?<=[A-ZČĆŽŠĐ])|(?<![\w)]))L[za)](?=U)', 'LJ', t)          # "DRAGOLzUB", "DRAGOL)UB", "LzUBISAV"
    return re.sub(r'(?<![\w])[Y¥](?=\s|$)', 'U', t)


def keep(ln: dict) -> bool:
    t = letters(ln['text'].strip())
    if page_number(t):
        return False                                         # the page number, a letter heading ("A", "Б")
    if ln['page'] == 18 and not re.search(r'[a-zčćžšđ]', t):
        return False                                         # "Прилог бр. 2.", the list's title
    new = ln['x'] < _left.get(ln['page'], 0) + 12 and entry_like(t)
    ln['text'] = ('§x§ ' if new else '') + t
    return True


def read_word(w: str, known) -> str:
    return decode(w, known) or w


TEXT_FIXES = [('KOH,HR ', 'KONJIĆ '),          # Коњић read as "KOH,HR": the comma would end the name
              ('APArOAiYE', 'DRAGOLJUB'), ('11AYH', 'PAUN'),   # given names the scan garbled past rules
              ('STEFANOVIK, Svetozara', 'STEFANOVIK Svetozara')]  # a comma inside the name


def join_split(words: list[str]) -> list[str]:
    """A name the scan spaced apart: "SLABOLJ UB", "BOGOLJ UB" (Bogoljub)"""
    out = []
    for w in words:
        if out and len(w) <= 2 and re.fullmatch(CAPS, w):
            out[-1] += w
        else:
            out.append(w)
    return out


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).strip()
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    head, _, info = text.partition(',')
    head = re.sub(r'\s+[-–—]\s*|\s*[-–—]\s+', ' — ', head)
    parts = head.split(' — ')
    other = []
    # "МИХАИЛОВИЋ - СТАНКОВИЋ Горче МИХАИЛО": two surnames, a father and the given name after the dash
    if len(parts) > 1 and re.fullmatch(rf'{CAPS}(?:\s+{CAPS})*', parts[0].strip()) and             re.match(rf'^{CAPS}\s+[{U}][{L}]+\s+{CAPS}', parts[1].strip()):
        other, parts = parts[0].split(), parts[1:]
    words = join_split([w.strip('.') if not re.fullmatch(rf'[{U}]\.', w) else w for w in parts[0].split()])
    nick = parts[1:]
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = ''
    if words and (re.fullmatch(rf'[{U}][{L}]+', words[0]) or re.fullmatch(rf'[{U}]\.', words[0])):
        father = words.pop(0)
    given = [w for w in words if re.fullmatch(CAPS, w) or re.fullmatch(rf'[{U}][{L}]+', w)]
    if not given and len(last) > 2 and not father:                           # "ЂОРЂЕВИЋ ЖИВОЈИН СОКО": a nickname
        given, nick, last = [last[1]], last[2:] + nick, last[:1]
    elif not given and len(last) > 1:                                        # "АДАМОВИЋ ДРАГОСЛАВ": no father
        given = [last.pop()]
    if len(given) > 1:                                                       # "СТОЈАДИН ДИНЕ": a nickname
        given, nick = given[:1], given[1:] + nick
    last = other + last
    last = ['-'.join(read_word(p, LAST) for p in w.split('-')) for w in last]
    given = [read_word(w, FIRST) for w in given]
    info = info.strip()
    if nick:
        info = 'zvani ' + ' '.join(nick).strip().title() + '; ' + info
    return _record('-'.join(last) if other else ' '.join(last), ' '.join(given), father, info)


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True)))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/5-srpska.pdf',
        brigade_code=127,
        output_path='website/public/5-srpska-soldiers.json',
        start_page=18,
        end_page=78,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
