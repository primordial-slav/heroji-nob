"""
Parser: Šercerjeva brigada, II. SNOUB "Ljubo Šercer" (brigade code 141).

Source: Lado Ambrožič-Novljan, "Šercerjeva brigada" I (Knjižnica NOV in POS 6/1; znaci.org 00003/813.pdf)
        →  website/public/pdfs/sercerjeva.pdf (book pp. 509-523):
    pp. 1-9     "Seznam partizanov-prostovoljcev Šercerjeve brigade od ustanovitve brigade 6. oktobra 1942 do konca
                februarja 1943": "Delač Ivan-Mirko, Jakšiči pri Fari"
    pp. 10-15   "Padli v Šercerjevi brigadi od ustanovitve brigade 6. oktobra 1942 do konca leta 1943", under the
                place and the day they fell:
                    MALI KORINJ V SUHI
                        KRAJINI 17.—18. marca 1943
                    Groznik Ivan-Janez Jelševar,
                        Zagorje ob Savi
Two columns, each entry hanging. A man the book could not name ("Neznan borec", "dva neznana borca") gets no
record; one it knew only by his partisan name ("»Bolte«, nekje z Barja") goes under that name.
"""
import re
from statistics import median

from _parser_scaffold import _record, extract_lines_two_column, repair_lj_ocr, run_parser
from _slovene_lists import OWN, fix_ocr, name_part

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
PADLI_FROM = 10
COLUMN_SPLIT = 150
TITLE_END = {1: 172, PADLI_FROM: 172}                                      # the lists' titles run across both columns
MONTHS = 'januar|februar|marec|marca|april|maj|junij|julij|avgust|september|septembra|oktober|oktobra|novembra?|decembra?'
DATE = re.compile(rf'((?:\d{{1,2}}[.,]\s*(?:[-—–,]+\s*\d{{1,2}}\.\s*)?)?(?:{MONTHS})\w*\s+19\d\d|\d{{1,2}}\.\s*(?:{MONTHS})\w*\s*$|19\d\d$)')
UNNAMED = re.compile(r'^(?:\w+\s+)?neznan[ia]?\s+bor(?:ec|ca)\b', re.I)
SMALL = {'NAD', 'PRI', 'V', 'NA', 'OB', 'IN', 'POD', 'IZ', 'OKOLICA'}
# the capitals lost their carons: "PUDOB PRI LOZU", "JELENOV ZLEB"
CARONS = {'LOZU': 'LOŽU', 'ARTVIZE': 'ARTVIŽE', 'ZLEB': 'ŽLEB', 'SUMBERKU': 'ŠUMBERKU', 'POKOJIŠCE': 'POKOJIŠČE',
          'JURIŠCE': 'JURIŠČE', 'CRNI': 'ČRNI'}


def heading_line(t: str) -> bool:
    """'MALI KORINJ V SUHI', 'KLEČ pri starem logu', 'VRBlCJE PRI PODTABORU': the first word in capitals."""
    w = t.split()[0] if t.split() else ''
    return len(w) >= 3 and bool(re.fullmatch(rf'[{U}][{U}l12]+[.,]?', w)) and sum(c.isupper() for c in w) >= 2


def place_name(caps: str) -> str:
    """'PADE2 NAD BOROVNICO' -> 'Padež nad Borovnico'."""
    caps = re.sub(r'(?<=[A-Z])2\b', 'Ž', caps)
    caps = re.sub(rf'\b[{U}l1]{{3,}}\b', lambda m: m.group().replace('l', 'I').replace('1', 'I'), caps)   # "VRBlCJE"
    caps = re.sub(r'\s+', ' ', caps.replace(' JEK', 'JEK')).strip(' ,')
    out = []
    for w in caps.split(' '):
        w = CARONS.get(w, w)
        if w in SMALL and out:
            out.append(w.lower())
        elif re.fullmatch(rf'[{U}]+\.?', w):
            out.append(w[:1] + w[1:].lower())
        elif re.fullmatch(rf'\([{U}]+\)', w):
            out.append('(' + w[1] + w[2:].lower())
        else:
            out.append(w)
    return ' '.join(out)


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    """The lines in reading order, each entry's first line marked '§s§' or '§p§'; on the pages of the fallen each
    entry's line also carries its heading, '§p§<place>|<date>§'."""
    lines = extract_lines_two_column(pdf_path, start, end, 'auto')
    lines = [ln for ln in lines if ln['text'].strip() and ln['y'] > TITLE_END.get(ln['page'], 0)
             and not (re.fullmatch(r'[\d\W]{1,5}', ln['text'].strip()) and not re.fullmatch(r'19\d\d', ln['text'].strip()))]
    lines.sort(key=lambda l: (l['page'], l['x'] > COLUMN_SPLIT, l['y']))
    out, heading, in_heading = [], [], False
    for ln in lines:
        col = [o['x'] for o in lines if o['page'] == ln['page'] and (o['x'] > COLUMN_SPLIT) == (ln['x'] > COLUMN_SPLIT)
               and abs(o['y'] - ln['y']) <= 60]
        low = min(col)
        margin = median([x for x in col if x < low + 3])
        t = ln['text'].strip()
        fallen = ln['page'] >= PADLI_FROM
        dated = re.match(rf'^(?:\d|{MONTHS})', t)                             # "14. novembra 1943" under the place
        if fallen and (heading_line(t) or (in_heading and (ln['x'] - margin > 4 or dated))):
            heading = (heading if in_heading else []) + [t]
            in_heading = True
            continue
        in_heading = False
        if ln['x'] - margin <= 4 and re.match(rf'^(?:[{U}»]|[šžčć2][{L}]|\w+\s+neznan)', t):
            if fallen:
                text = re.sub(r'\bI(?=\d)', '1', ' '.join(heading))         # "I8,—21. oktobra"
                m = DATE.search(text)
                place, date = (text[:m.start()], m.group(1)) if m else (text, '')
                t = f'§p§{place_name(place)}|{date.strip()}§ ' + t
            else:
                t = '§s§ ' + t
        out.append(dict(ln, text=t))
    return out


def split_name(text: str) -> tuple[str, str]:
    """The name and the rest: 'Zdešar Janez-Zan, Horjul — ujet', 'Krčmar Radojka iz Hercegovine', 'Karletič Ivan'."""
    m = re.search(r',|\s+—\s+(?=[a-z»])|\s+(?=iz\s)', text)
    return (text[:m.start()], text[m.end():].strip(' ,')) if m else (text, '')


def parse_entry(text: str) -> dict:
    m = re.match(r'^§([sp])§(?:([^|§]*)\|([^§]*)§)?\s*', text)
    kind, place, date = m.group(1), (m.group(2) or '').strip(), (m.group(3) or '').strip()
    text = fix_ocr(re.sub(r'(?<=\w)-\s+(?=[a-zčšž])', '', text[m.end():]))      # "Mramoro- vo"
    text = re.sub(r'\s+', ' ', text).replace(' j e ', 'je ').replace('Aloj z', 'Alojz').replace('Gaber j e', 'Gaberje')
    if UNNAMED.match(text):
        return {}                                                             # the scaffold drops a record without a name
    head, rest = split_name(text)
    head = head.replace(' -', '-')                                            # "Jerman Hilarij -Vasilij"
    alias = re.fullmatch(r'»([^«]+)«', head.strip())
    words = head.split()
    named = re.fullmatch(r'»([^«]+)«\s+(\S+)', head.strip())
    if named:                                                                 # "»Srbo« Nikola, Bosna" (the fallen: "Nikola — »Srbo«")
        last, given, notes = named.group(2), '', ['zvani ' + named.group(1)]
    elif alias:                                                                 # "»Bolte«": known only by his partisan name
        last, given, notes = alias.group(1), '', []
    elif len(words) == 1:                                                     # "Giovanni, Italija", "Sever, drugi podatki"
        last, given, notes = words[0], '', []
    else:
        last, given, notes = name_part(head)
    info = '; '.join(notes + ([rest] if rest else []))
    if kind == 'p':
        info = (info + '; ' if info else '') + 'padel ' + ', '.join(x for x in (date, place) if x)
    rec = _record(last, given, '', info)
    home = re.split(r',|\s—\s', rest)[0].strip() if rest else ''
    if home and not re.search(r'\d|podatki|neznan|verjetno|nekje|okolic|trgovski|ranjen|ujet|^iz\s|»', home):
        rec['birth_place'] = home
    if kind == 'p':
        rec['death_type'] = 'poginuo'
        day = re.match(r'^(\d{1,2})[.,]\s*[-—–,]+\s*\d{1,2}\.\s*(.*)$', date)
        rec['death_date'] = re.sub(r'\bjanuar\b', 'januarja', day.group(2) if day else date)   # "23.—24. decembra 1942": the month
        if place and not re.search(r'umrl|ustreljen|padel (?:na|pri|po)|ubit od', rest):
            rec['death_place'] = place
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    return repair_lj_ocr(soldiers)                                         # no restore_diacritics: it reads Slovene -ic as -ić


if __name__ == '__main__':
    OWN['file'] = 'sercerjeva-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/sercerjeva.pdf',
        brigade_code=141,
        output_path='website/public/sercerjeva-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
