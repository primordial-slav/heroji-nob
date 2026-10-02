"""
Parser: Posavsko-trebavski partizanski odred (brigade code 59).

Source: Esad Tihić, "Posavsko-trebavski odred" (znaci.org 00001/302.pdf), "Spisak boraca Posavsko-trebavskog odreda"
        (book p. 313 on)  →  website/public/pdfs/posavsko-trebavski-odred.pdf (PDF pages 307-395 of the book).
The SUBNOR committees of nine municipalities gathered the names; the list goes municipality by municipality
("Borci odreda sa područja opštine Brčko"), alphabetically within each. One column, Latin, every line flush left:
    ANTIĆ Save CVIJAN, 1927, Brvnik, Srbin, zemljoradnik, u odredu od 20. 9. 1943, član SKOJ-a, borac, umro 1962.
The surname and the given name in capitals, the father's name (genitive) between them. The text layer spaces some
surnames apart ("STO JANO VIĆ"), puts Greek capitals in others ("ΤΟΜΟ") and a comma after a few ("MALESAK, Avde
EJUB"); a few entries have no father ("GAČIĆ VLADO") or print the given name in small letters ("BEĆIĆ Velije Hazim").
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
GREEK = str.maketrans('ΑΒΕΗΙΚΜΝΟΡΤΥΧΖ', 'ABEHIKMNOPTYXZ')
# Words that begin a wrapped line in capitals, not an entry
NOT_NAME = re.compile(r'^(?:NOB|KPJ|SKOJ|SKJ|RVI|SUBNOR|AFŽ|USAOJ|NOV|POJ|JNA|[IVX]+)\b')
ENTRY = re.compile(rf'^[{U}£][{U}0-9\-]{{1,}}(?:\s|,|»|$)')
_heading = {'on': False}
_last: Counter = Counter()
_first: Counter = Counter()
TEXT_FIXES = [('OSMA Ni,', 'OSMAN,')]


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('posavsko-trebavski-odred-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _last[s['last_name'].upper()] += 1
                _first[s['first_name'].upper()] += 1


def clean(t: str) -> str:
    t = t.translate(GREEK).replace('£>', 'Đ')
    t = re.sub(rf'(?<=[{U}])»(?=[\s,])', '', t)                               # "PANTELIĆ» Marka"
    return re.sub(rf'(?<=[{U}])[01]|[01](?=[{U}]{{2}})', lambda m: 'I' if m.group(0) == '1' else 'O', t)   # JOS1POVIĆ, B0GOLJUB


def keep(ln: dict) -> bool:
    t = clean(ln['text'].strip())
    if re.fullmatch(r'[\d\W]{1,5}', t) or (len(t) < 15 and re.search(r'[·™]', t)):
        return False
    if t.startswith(('Borci odreda sa ', 'Dodatni spisak')):                 # a municipality's heading (and its next line)
        _heading['on'] = True
        return False
    if ENTRY.match(t) and not NOT_NAME.match(t) and len(re.match(rf'^[{U}]*', t).group(0)) + len(t) > 3:
        _heading['on'] = False
        t = '§x§ ' + t
    elif _heading['on']:
        return False
    ln['text'] = t
    return True


def is_caps(w: str) -> bool:
    return bool(re.fullmatch(rf'[{U}][{U}\-]*', w)) and len(w.replace('-', '')) >= 2


def join_surname(run: list[str]) -> str:
    """The capitals before the father's name: one surname, spaced apart in the text ("STO JANO VIĆ", "MILANO VIC")."""
    if len(run) == 1:
        return run[0]
    whole = ''.join(run)
    if _last[whole] or re.search(r'(?:VI[ĆC]|I[ĆC]|AC|AK)$', run[-1]) or any(len(w) <= 3 for w in run):
        return whole
    return '-'.join(run)


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    text = re.sub(r'^([^\d,]*?)\s*»([^«,\d]+)«', r'\1 - \2', text)       # "REŠAD »RESKO«": the name he went by
    text = re.sub(r'(?<=[{U}])\s*\((?=[{U}][{L}])'.replace('{U}', U).replace('{L}', L), ' ', text)   # "DOBORAC (Huseina"
    text = re.sub(rf'\s+-\s+(?=[{U}]{{2}})', ' - ', text)
    segs = text.split(',')
    words: list[str] = []
    info = ''
    for i, seg in enumerate(segs):
        d = re.search(r'\d', seg)
        if d:                                                                # a year ends the name: "VLAJKO 1911, Obudovac"
            words += seg[:d.start()].split()
            info = ','.join([seg[d.start():]] + segs[i + 1:])
            break
        words += seg.split()
        caps = [w for w in words[1:] if is_caps(w)]
        names = [w for w in words[1:] if re.fullmatch(rf'[{U}{L}][{L}.]+', w) and w not in ('rođ.', 'rod.', 'ud.')]
        if caps or len(names) >= 2 or i >= 2:
            info = ','.join(segs[i + 1:])
            break
    info = info.strip().lstrip(',').strip()
    # the surname: the capitals at the start
    run = []
    while words and is_caps(words[0]):
        run.append(words.pop(0))
    prefix = []
    if words and words[0] in ('rođ.', 'rod.', 'ud.'):                       # "HAMZIĆ rođ. NOVALIJA", "KOSIK ud. Nikolić"
        kind = 'ud.' if words.pop(0) == 'ud.' else 'rođ.'
        if words:
            prefix.append(f'{kind} {words.pop(0).title()}')
    nick = ''
    if '-' in words:                                                         # "B0GOLJUB - BOBAN": the name he went by
        k = words.index('-')
        nick = ' '.join(words[k + 1:])
        words = words[:k]
    if words or len(run) < 2:
        last = join_surname(run)
        lower = [w for w in words if not is_caps(w)]
        upper = [w for w in words if is_caps(w)]
        if upper:
            father, given = ' '.join(lower), upper[0]
            if len(upper) > 1:                                               # "DŽEM AL", "ČEDO MIR": one name spaced apart
                whole = ''.join(upper)
                if _first[whole] or any(len(w) <= 2 for w in upper):
                    given = whole
                else:
                    nick = (' '.join(upper[1:]) + (' ' + nick if nick else '')).strip()
        elif len(lower) >= 2:
            father, given = ' '.join(lower[:-1]), lower[-1]                  # "BEĆIĆ Velije Hazim"
        else:
            father, given = '', ' '.join(lower)
    else:                                                                    # no father: "GAČIĆ VLADO", "BRISTRIĆ ALMAZ"
        last, father, given = join_surname(run[:-1]), '', run[-1]
    father = father.replace('.', '')
    given = given.rstrip('.;:')
    father = {'lime': 'Ilije'}.get(father, father[:1].upper() + father[1:])
    if nick:
        prefix.append('zvani ' + nick.title())
    rec = _record(last, given, father, '; '.join(prefix + ([info] if info else [])))
    by = re.match(r'^(1[89]\d\d)\b', info)
    if by:
        rec['birth_year'] = by.group(1)
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(restore_diacritics(soldiers))


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/posavsko-trebavski-odred.pdf',
        brigade_code=59,
        output_path='website/public/posavsko-trebavski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        post_fn=post,
    )
