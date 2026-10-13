"""
Parser: 1. krajiška proleterska brigada (brigade code 123).

Source: Milorad Gončin, Stevo Rauš, "Prva krajiška udarna proleterska brigada" (znaci.org 00001/226), the chapter
        "Dali su svoje živote za slobodu boreći se u redovima Prve krajiške narodnooslobodilačke proleterske udarne
        brigade" (226_7.pdf → website/public/pdfs/1-krajiska.pdf, book pp. 331-442), researched by Slobodan Spegar
        Spego: the brigade's fallen, died and missing, 2,127 by the editor's count (all read). Its pages 112-114 are
        the book's contents.
One column, Latin, each entry hanging: its first line starts some 23pt left of the lines under it, on every page,
and that alone tells where an entry starts (some lack the semicolon that ends the others, some start with a name the
scan garbled). The surname and the given name in capitals, the father's name (genitive) between them, a nickname
after the given name:
    ADAMOVIĆ Jove BOŽO, rođen 1908. u Vranovini, Bosanski Petrovac, Srbin, zemljoradnik, u brigadi od decembra
    1942, 2. četa, 2. bataljon, borac, teže ranjen aprila 1943. kod sela Orašca (Travnik) i podlegao ranama ...;
    VUJASINOVIĆ Pere NIKOLA Nidže, rođen 1910. u Ivoševcima, Knin, ...
The text layer puts accents on capitals ("SLÀVKO", "MILÓS" = Miloš), reads J as ".I" ("STANO.IE"), I as l or 1
("VlSEKRUNA", "S1MATOVIĆ"), splits names ("SPASO JE", "CA VIĆ"), ends a name with a semicolon or a full stop
("SIMIĆ Koste DEJAN; rođen") and loses carons ("BOZO", "roden"). Carons come back from the corpus.
"""
import re
import unicodedata

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
FATHER = rf'\(?[{U}][{L}.]*\)?'
_left: dict = {}                     # page -> where its entries' first lines start
TEXT_FIXES = [('SUHA! ', 'SUHAJ ')]  # the J of a Temerin Hungarian's surname read as "!"


def plain_caps(t: str) -> str:
    """Accented capitals the OCR made of plain ones (À, Ì, Ó), ".I" for J and l or 1 for I in a word in capitals"""
    t = ''.join(c if c in 'čćžšđČĆŽŠĐ' else unicodedata.normalize('NFD', c)[0] for c in t)
    t = re.sub(rf'(?<=[{U}])\.I(?=[{U}])', 'J', t)
    t = re.sub(rf'(?<=[{U}])[1l](?=[{U}])', 'I', t)
    return re.sub(rf'(?<![\w{L}])l(?=[{U}]{{2}})', 'I', t)                    # "lVANIĆ"


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t))


def measure(lines: list[dict]) -> None:
    for ln in lines:
        if not page_number(ln['text'].strip()):
            _left[ln['page']] = min(_left.get(ln['page'], 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = plain_caps(re.sub(r'^[•·\s]+', '', ln['text'].strip()))
    if page_number(t):
        return False
    new = ln['x'] < _left[ln['page']] + 12                                   # the entry's first line hangs
    ln['text'] = ('§x§ ' if new else '') + t
    return True


def join_split(words: list[str]) -> list[str]:
    """A name the text spaced apart: "SPASO JE" = Spasoje, "CA VIĆ" = Cavić, "MOMČILO VIĆ" = Momčilović"""
    out = []
    for w in words:
        if out and (len(w) <= 2 or re.fullmatch(r'(?:V?IĆ|OVIĆ)', w) or len(out[-1]) <= 2):
            out[-1] += w
        else:
            out.append(w)
    return out


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).rstrip(' ;:')
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    # the name ends at its comma, or a semicolon or full stop the scan put there ("SIMIĆ Koste DEJAN; rođen")
    end = re.search(r'[,;]|\.+(?=\s*r[oa][dđ]en)|\s+(?=r[oa][dđ]en)', text)
    head, info = (text[:end.start()], text[end.end():]) if end else (text, '')
    head = re.sub(rf"(?<=[{L}])-(?=[{U}]{{2}})|'", ' ', head)                 # "Damjana-VASO", "RISTIĆ'Dmitra"
    words = [w.upper() if sum(c.isupper() for c in w) >= 0.7 * len(w) else w  # "MARKo"
             for w in head.split()]
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = ''
    if words and re.fullmatch(FATHER, words[0]) and len(words) > 1:
        father = words.pop(0).strip('()')
        father = re.sub(r'ia$', 'la', father) if not father.endswith('ija') else father  # "Pavia" = Pavla
        father = father.replace('v.', 'r')                                   # "Pev.a" = Pera
    if not father and len(words) > 1 and re.fullmatch(rf'[{L}]+', words[0]):
        father = words.pop(0).title()                                        # "KERKEZ vida MILAN"
    given = []
    while words and re.fullmatch(CAPS, words[0]):
        given.append(words.pop(0))
    if not given and words and re.fullmatch(rf'[{U}][{L}]+', words[0]):
        given = [words.pop(0)]                                               # "LIČINA Petra Božo"
    if not given and len(last) > 1:                                          # "SURNAME GIVEN" without a father
        given = [last.pop()]
    last, given = join_split(last), join_split(given)
    nick = ' '.join(words).strip()
    info = re.sub(r'^[\W_]+', '', info.strip())
    lead = re.match(rf'^([{U}][{L}]+),\s*(?=r[oa][dđ]en)', info)             # "ŽIVADIN, Žika, rođen ..."
    if lead and not nick:
        nick, info = lead.group(1), info[lead.end():]
    info = re.sub(r'^r[oa][dđ]en(a?)\b', r'rođen\1', info)
    info = re.sub(r"^rođen(a?)[.'’]\s*", r'rođen\1 ', info)                   # "rođen'1920", "rođen. 1927"
    info = re.sub(r'(?<=\d)O|O(?=\d)', '0', info)                           # "192O"
    info = re.sub(r'\b[Il]\s?(?=9\d\d\b)|(?<=\b19)[Il](?=\d\b)', '1', info)   # "I912", "I 923", "19I9"
    if nick:
        info = f'zvani {nick}; {info}'
    return _record(' '.join(last), ' '.join(given), father, info)


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-krajiska.pdf',
        brigade_code=123,
        output_path='website/public/1-krajiska-soldiers.json',
        start_page=2,
        end_page=111,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
