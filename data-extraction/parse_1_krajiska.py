"""
Parser: 1. krajiška proleterska brigada (brigade code 123).

Source: Milorad Gončin, Stevo Rauš, "Prva krajiška udarna proleterska brigada" (znaci.org 00001/226), the chapter
        "Dali su svoje živote za slobodu boreći se u redovima Prve krajiške narodnooslobodilačke proleterske udarne
        brigade" (226_7.pdf → website/public/pdfs/1-krajiska.pdf, book pp. 331-442), researched by Slobodan Spegar
        Spego: the brigade's fallen, died and missing, 2,127 by the editor's count. Its pages 112-114 are the book's
        contents.
One column, Latin, every line flush left; the surname and the given name in capitals, the father's name (genitive)
between them, a nickname after the given name; each entry ends with a semicolon:
    ADAMOVIĆ Jove BOŽO, rođen 1908. u Vranovini, Bosanski Petrovac, Srbin, zemljoradnik, u brigadi od decembra
    1942, 2. četa, 2. bataljon, borac, teže ranjen aprila 1943. kod sela Orašca (Travnik) i podlegao ranama ...;
    VUJASINOVIĆ Pere NIKOLA Nidže, rođen 1910. u Ivoševcima, Knin, ...
The text layer puts accents on capitals ("SLÀVKO", "MILÓS" = Miloš), reads J as ".I" ("STANO.IE"), splits names
("SPASO JE", "CA VIĆ") and loses carons ("BOZO", "roden"); a few entries lack their semicolon. Carons come back from
the corpus.
"""
import re
import unicodedata

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
FATHER = rf'\(?[{U}][{L}.]*\)?'
# SURNAME [SURNAME] Father GIVEN: the father in small letters (or an initial) between two words in capitals
HEAD = re.compile(rf'^{CAPS}(?:\s+{CAPS})*\s+(?:{FATHER}\s+)?{CAPS}\b')
_prev = {'end': ';', 'page': 0}


def plain_caps(t: str) -> str:
    """Accented capitals the OCR made of plain ones (À, Ì, Ó), and ".I" for J inside a word in capitals"""
    t = ''.join(c if c in 'čćžšđČĆŽŠĐ' else unicodedata.normalize('NFD', c)[0] for c in t)
    t = re.sub(rf'(?<=[{U}])\.I(?=[{U}])', 'J', t)
    return re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', t)


def keep(ln: dict) -> bool:
    t = plain_caps(ln['text'].strip())
    if re.fullmatch(r'[\d\W]{1,5}', t):                                      # the page number
        return False
    if ln['page'] == 1 or ln['page'] > 111:                                  # the editor's note; the book's contents
        return False
    new = bool(HEAD.match(t)) and (_prev['end'] in ';.:' or ln['page'] != _prev['page']
                                   or re.search(r'\br[oa][dđ]en', t[:100]))
    _prev['end'], _prev['page'] = t[-1:], ln['page']
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
    head, _, info = text.partition(',')
    words = head.split()
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = ''
    if words and re.fullmatch(FATHER, words[0]) and len(words) > 1:
        father = words.pop(0).strip('()')
        father = re.sub(r'ia$', 'la', father) if not father.endswith('ija') else father  # "Pavia" = Pavla
        father = father.replace('v.', 'r')                                   # "Pev.a" = Pera
    given = []
    while words and re.fullmatch(CAPS, words[0]):
        given.append(words.pop(0))
    if not given and len(last) > 1:                                          # "SURNAME GIVEN" without a father
        given = [last.pop()]
    last, given = join_split(last), join_split(given)
    nick = ' '.join(words).strip()
    info = re.sub(r'^[\W_]+', '', info.strip())
    lead = re.match(rf'^([{U}][{L}]+),\s*(?=r[oa][dđ]en)', info)             # "ŽIVADIN, Žika, rođen ..."
    if lead and not nick:
        nick, info = lead.group(1), info[lead.end():]
    info = re.sub(r'^r[oa][dđ]en(a?)\b', r'rođen\1', info)
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
        post_fn=post,
    )
