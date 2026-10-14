"""
Parser: Mosorski partizanski odred (brigade code 148): every fighter of the odred, 1942-1944.

Source: Miroslav Velić, Ante V. Petrić, *Mosorski partizanski odred* (znaci.org 00003/794, the whole book's PDF
pp. 357-564: "I dio. Popis boraca Mosorskog partizanskog odreda 1942-1944.") → website/public/pdfs/mosorski-odred.pdf.
3,486 fighters by the book's own count (its tables after the list), of the I mosorski PO of February-April 1942,
the Mosorski bataljon, the Leteća mosorska četa and the odred of October 1943 - November 1944, alphabetical, one
column, a short bio each:
    ABRAM Mate STJEPAN, borac Mosorskog PO. Rođen 1. 7. 1915. Nova Sela, Omiš, zemljoradnik, Hrvat. U Mosorski PO
    došao 16. rujna 1944. godine. Poginuo 3. listopada 1944. kod Dobranja, Imotski, ...
The surname in capitals, the father in the genitive, the given name in capitals (two at times, "JURE-STANISLAV"),
a nickname in quotes ("»Trobo«"); the name may break over two lines ("ALBAHARI Morica / ALBERT, borac ..."). The
book's part II, the komande mjesta's men and the field workers and activists of the Mosor area (PDF p. 575 on), is
not read: it is not the odred's list. The scan loses some carons ("ZANIĆ"), which the corpus gives back
(parse_8_kordunaska_divizija.post).
Usage: python data-extraction/parse_mosorski_odred.py
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
_state = {'open': False}


def surname(w: str) -> bool:
    """A surname in capitals as the OCR reads it: mostly capitals, at times a small letter ("JERCiC", "BLASKOVIć",
    "KR2ELJ")"""
    letters = [c for c in w if c.isalpha()]
    up = sum(c.isupper() or c in 'li' for c in letters)              # l and i: the OCR's I
    return len(w) >= 2 and w[0].isupper() and up >= 2 and up >= 0.7 * len(letters)


def keep(ln: dict) -> bool:
    t = ln['text'].replace('\xad', '-').strip()
    if re.fullmatch(r'[\d\W]{1,5}|[A-Za-z]', t) or re.match(r'^(?:I DIO|POPIS BORACA MOSORSKOG|1942\s*[—-]\s*1944)', t):
        return False                                     # page numbers, the list's title
    t = re.sub(r'^I\s+(?=ZANKI\b)', 'Ž', t)              # "I ZANKI Andrije PAVAO" = ŽANKI
    # an entry: the surname in capitals, then the father or the given name; not a line that carries on a name
    # broken after the father ("ALBAHARI Morica" / "ALBERT, borac Mosorskog PO")
    t = re.sub(r'^[‘’\'"]+', '', t)                       # "‘dUKIC Petra LOVRE"
    first = t.split()[0] if t.split() else ''
    start = (surname(first.split('-')[0])
             and re.match(rf'^\S+(?:\s*-\s*\S+)?\s+(?:[{U}][{L}]+|[{U}]{{2}}|[{U}]\.|di\s|\(|[{L}]+\s+[{U}]{{2}})', t)
             and not re.match(r'^(?:NOB|NOV|NOVJ|KPJ|KPH|SKOJ|PO|MPO|CPO|ZAVNOH|AFŽ|NOO|NOF|SAD|RVI|KNOJ|OZN\w*|'
                              r'[KMO]{1,3}(?:KPH|KPJ)?|SKOJ\w*)\b', t)
             and not _state['open'])
    if start:
        t = '§x§ ' + t
    head = re.split(r'[,.]', re.sub(r'^§x§\s*', '', t), 1)[0]
    # a name line that ends before its comma: the given name is on the next line
    _state['open'] = bool(start) and ',' not in t and bool(re.fullmatch(rf'{CAPS}(?:-{CAPS})?\s+[{U}][{L}]+', head.strip()))
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    t = re.sub(r'^§x§\s*', '', text)
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)        # "ze- mljoradnik"
    # the name ends with the given name in capitals, before a comma, a full stop the OCR made of it ("ALJINOVIĆ Marina
    # MATE. borac") or none ("ALJINOVIĆ Paške MIJO borac"); a nickname in quotes may follow it first
    name = re.match(rf'^(\S+(?:\s+\([^)]*\))?\s+(?:[{U}][{L}]+\s+)?{CAPS}(?:\s*-\s*{CAPS})*)(?:\s*[.,]\s*|\s+)(?=[{L}])', t)
    if name:
        t = f'{name.group(1)}, {t[name.end():]}'
    t = re.sub(rf'^(\S+)\s+di\s+([{U}][{L}]+)\s+', r'\1 \2 ', t)                  # "CALICI di Vicenzo SEBASTI"
    # a line the text layer spaced out letter by letter ("M A T E b o r a c M o s o r s k o g P O R o đ e n"): its
    # letters run together, then the words are found again by their capitals
    t = re.sub(r'(?:(?<=\s)|^)((?:\S ){4,}\S)(?=\s|$)', lambda m: m.group(1).replace(' ', ''), t)
    # a line whose spaces the text layer lost: "ALJINOVIĆ Marina MATEboracMosorskogPORođen 1924. u Zrnovnici"
    glued = re.match(rf'^(\S+\s+[{U}][{L}]+\s+[{U}][{U}\-]+?)([{L}]\S{{8,}})', t)
    if glued:
        run = re.sub(rf'(?<=[{L}])(?=[{U}])|(?<=[{U}])(?=[{U}][{L}])|(?<=[{L}.])(?=\d)', ' ', glued.group(2))
        t = f'{glued.group(1)}, {run}{t[glued.end():]}'
    # a nickname between any quotes the OCR made of » and «: "«-Miško«", "“-Cinđrić«", "»Ico\""
    t = re.sub(r'\s[«»“"]-?\s*([^«»“"”,]+?)\s*-?[«»“"”]+', r' »\1«', t, 1)
    rec = k8.parse_entry(t)
    rec.pop('unit_detail', None)                          # the 8. division's brigades: not this list's
    y = re.search(r'\bRođen[a]?\s+(?:[^.]*?\b)?(1[89]\d\d)\b', rec['additional_info'])
    rec['birth_year'] = y.group(1) if y else rec.get('birth_year', '')
    return rec


FIX_GIVEN = {          # given names the OCR garbled or ran into the bio: (given name, words for the bio's start)
    'IVAN-IVANKOboracImosorskogPORođen': ('Ivan-Ivanko', 'borac I mosorskog PO'),
    'STIPE »Stipić-': ('Stipe', 'zvani Stipić'), 'MIHOVIL-Miće': ('Mihovil', 'zvani Miće'), 'SiDA': ('Sida', ''),
    'č/TANKO': ('Stanko', ''), 'VICivO': ('Vicko', ''), "Miće -Zingin'«": ('Miće', 'zvani Zingin'),
    'VLADIMIR »Cvijo*': ('Vladimir', 'zvani Cvijo'), 'JOSIP-Jozica': ('Josip', 'zvani Jozica'), 'Zoran-“': ('Zoran', ''),
    'MARiO': ('Mario', ''), 'ANTE»FunđaksboracLetećegmosorskogvodaRođenI77': ('Ante', 'zvani Funđaks; borac Letećeg mosorskog voda'),
    'KAZIMIRdesetar5vodaImosorskogPORođen3OII': ('Kazimir', 'desetar 5. voda I mosorskog PO'),
    'ANTEboracLetećemosorskečeteRođen95': ('Ante', 'borac Leteće mosorske čete'), 'MARIN »Titin<-': ('Marin', 'zvani Titin'),
    'ANTICA -MaIena-«': ('Antica', 'zvani Malena'),
}


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s['first_name'] in FIX_GIVEN:
            given, note = FIX_GIVEN[s['first_name']]
            s['first_name'] = given
            if note:
                s['additional_info'] = f"{note}; {s['additional_info']}".strip('; ')
        if s['last_name'] == 'Mno' and s['first_name'].startswith('JAVORČIĆ'):   # "Mno Jugoslavije JAVORČIĆ Mate ANTE"
            s['last_name'], s['middle_name'], s['first_name'] = 'JAVORČIĆ', 'Mate', 'Ante'
    return k8.post(soldiers)


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/mosorski-odred.pdf',
        brigade_code=148,
        output_path='website/public/mosorski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
