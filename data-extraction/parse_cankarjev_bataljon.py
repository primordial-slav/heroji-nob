"""
Parser: Cankarjev bataljon (brigade code 170), the Gorenjska battalion of 1941-42 that fought at Dražgoše.

Source: Ivan Jan, "Cankarjev bataljon in dražgoška bitka" (Partizanska knjiga, Ljubljana 1974; znaci.org 00003/1080.pdf)
        →  website/public/pdfs/cankarjev-bataljon.pdf (book pp. 338-346, "Dodatek s seznami"), one column, given name
        after the surname, where he was from after the comma:
    p. 1    "Formacija bataljona" at Dražgoše ("Komandant: Stane Žagar"), the staff and the companies' officers
    p. 2    "Španski borci" and "Narodni heroji" (the fallen, the living)
    pp. 3-7 "Padli cankarjevci v avgustu, v decembrskih, dražgoških in naslednjih bojih", under each battle and its day
            ("V Dražgošah od 9. do 11. januarja 1942:"), then "Padli na raznih krajih (a največ že v letu 1942)", where
            the book also names men who deserted, betrayed or later fell on the other side; their notes are kept as
            printed and they are not marked fallen. "Murnik mož in žena" and "Martin, nemški graničar" give no name a
            record can hold and stay out.
    p. 8    "Preživeli cankarjevci nosilci spomenice 1941" ("(umrl)": died since the war)
    p. 9    "Ostali preživeli udeleženci dražgoške bitke"
The book's next list, the villagers of Dražgoše the Germans killed (pp. 347-348), is civilians and is not read.
The staff's duties, the Spanish fighters and the narodni heroji go into the entry of the man in the lists below; a
name found in none of them is a record of its own.
"""
import re
import unicodedata
from difflib import SequenceMatcher

from _parser_scaffold import _record, extract_lines_single_column, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'

# each battle's heading → the place in the nominative and the day
BATTLES = {
    'Na Rženovem robu-Partizanskem vrhu': ('Rženov rob (Partizanski vrh)', '8. 8. 1941'),
    'Na Pasji ravni in Polhovcu': ('Pasja ravan in Polhovec', '1941'),
    'V Dražgošah': ('Dražgoše', '1942'),
    'Na Mošenjski planini': ('Mošenjska planina', '13. 1. 1942'),
    'V Vinharjih': ('Vinharje', '22. 1. 1942'),
    'Nad Crngrobom': ('Crngrob pri Škofji Loki', '27. 3. 1942'),
    'V jami pri Okroglem': ('Okroglo', '1942'),
    'Na Lipniški planini': ('Lipniška planina', '9. 9. 1942'),
    'V Udin borštu': ('Udin boršt', '14. 9. 1942'),
}
NOT_FALLEN = re.compile(r'izdajal|sovražnik|domobran|skrivač|nemški vojak|odpadnik|pobegnil|ušel|po vojni')
SKIP = re.compile(r'^(?:Murnik mož in žena|Martin, nemški graničar)')
EXTRA: dict = {}                                                   # fold(name) → notes from pp. 1-2
EXTRA_NAMES: list = []                                             # (given, surname, note, line) in their order


def fold(text: str) -> str:
    t = (text or '').lower().replace('đ', 'dj')
    return ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c))


def fix(t: str) -> str:
    t = re.sub(r'(?<![\w.])2(?=[a-zčšž])', 'Ž', t)                  # "Stane 2agar", "2elezniki"
    t = re.sub(r'\bKar1\s*,', 'Karl,', t)
    t = re.sub(r'^Zagar Stanko\b', 'Žagar Stanko', t)                 # the caron lost: Stane Žagar, fell at Crngrob
    t = re.sub(r'^Zakelj Janez, Ziri', 'Žakelj Janez, Žiri', t)
    t = t.replace('Papirnica - umrl po vojni', 'Papirnica, umrl po vojni')
    t = re.sub(r'^(\S+ \S+, )([a-zčšž])', lambda m: m.group(1) + m.group(2).upper(), t)   # "števerjan"
    return t.replace('.:Žiri', 'Žiri').replace('l. četa', '1. četa').replace('Padli: l.', 'Padli: 1.')


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out, heading, kind, pending, section, last_duty = [], '', '', '', 'štaba', ''
    for ln in extract_lines_single_column(pdf_path, start, end):
        t = fix(ln['text'].strip())
        if re.fullmatch(r'[~·\s]*\d{3}', t):
            continue
        if ln['page'] == 1:                                         # the formation: duties for the men below
            if re.match(r'^(?:DODATEK|FORMACIJA|Gorenjski štab|cijo bataljon)', t):
                continue
            if t in ('1. četa', '2. četa', 'Samostojni vod'):
                section = {'1. četa': '1. čete', '2. četa': '2. čete', 'Samostojni vod': 'samostojnega voda'}[t]
                continue
            m = re.match(r'^(?:dotlej\s+)?(?:(.+?):\s*)?([A-ZČŠŽ][a-zčšž]+ [A-ZČŠŽ][a-zčšž]+)$', t)
            if not m:
                pending = t                                         # "Politični komisar bataljona" / "dotlej ..."
                continue
            if t.startswith('dotlej'):
                duty = pending + ' do tedaj'                        # "Politični komisar bataljona / dotlej ..."
            else:
                duty = (m.group(1) or last_duty).strip()            # the couriers under "Kurirji:"
            pending, last_duty = '', duty
            duty = re.sub(r'^Kurirji$', 'Kurir', duty)
            note = f'v Dražgošah {duty[0].lower() + duty[1:]}' + ('' if section == 'štaba' else f' {section}')
            given, last = m.group(2).split()
            rank = re.sub(r'^polit komisar$', 'politkomisar', re.sub(r' bataljona do tedaj$|, medicinec$', '', duty.lower()))
            unit = {'1. čete': '1. četa', '2. čete': '2. četa', 'samostojnega voda': 'samostojni vod'}.get(section, 'štab bataljona')
            EXTRA_NAMES.append((given, last, note, ln, {'rank': rank, 'unit_detail': unit}))
            continue
        if ln['page'] == 2:                                         # Spanish fighters, narodni heroji
            if t.startswith('Španski'):
                kind = 'španski borec'
            elif t.startswith('Narodni heroji'):
                kind = 'narodni heroj'
            elif t.startswith('Živa'):
                kind = 'narodni heroj (živ)'
            m = re.search(r'\d\.\s+([A-ZČŠŽ][a-zčšž]+) ([A-ZČŠŽ][a-zčšž]+)$', t)
            if m:
                EXTRA_NAMES.append((m.group(1), m.group(2), kind, ln, {}))
            continue
        if re.match(r'^(?:PADLI CANKARJEVCI|DRAŽGOŠKIH IN)', t):
            continue
        if t.startswith('PREŽIVELI CANKARJEVCI'):
            heading = 'preživeli cankarjevci, nosilci spomenice 1941'
            continue
        if t.startswith('OSTALI PREŽIVELI'):
            heading = 'ostali preživeli udeleženci dražgoške bitke'
            continue
        if t.startswith('Do 1973. leta'):
            continue
        if re.match(r'^(?:Na|V|Nad|Padli)\s', t) and not re.match(rf'^[{U}][{L}]+ [{U}][{L}]+,', t):
            heading = t.rstrip(':')                                 # a battle; its heading may run on
            continue
        if heading and not heading.endswith(':') and re.match(r'^dolino od', t):
            heading = heading + ' ' + t.rstrip(':')
            continue
        if SKIP.match(t):
            continue
        starts = bool(re.match(rf'^[{U}][{L}]+(?:\s+[{U}][{L}]+(?:-[{U}][{L}]+)?)?(?:\s+(?:mlajši|starejši))?(?:\s+\([^)]*\))?\s*,', t))
        out.append(dict(ln, text=(f'§x§{heading}§ ' if starts else '') + t))
    return out


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([^§]*)§\s*(.*)$', text, re.S)
    heading, t = m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip()
    t = re.sub(r'\s+-\s+', ' - ', t)
    name, _, rest = t.partition(',')
    rest = rest.strip()
    nick = re.search(r'\(([^)]*)\)', name)
    name = re.sub(r'\s*\([^)]*\)', '', name)
    words = name.split()
    last, given = words[0], ' '.join(words[1:])
    notes = []
    age = re.search(r'\s+(mlajši|starejši)$', given)
    if age:
        given = given[:age.start()]
        notes.append(age.group(1))
    if '-' in given:                                                # "Udvanc Matija-Vajs", "Zupanc Ivan-Brico"
        given, alias = given.split('-', 1)
        notes.append(f'zvani {alias}')
    if nick:
        notes.append(f'zvani {nick.group(1)}')
    place, _, note = rest.partition(', ')
    if re.search(r'\d|ujet|ustreljen|padel|likvid|dezert|pobegnil|ubit|ušel|kot ', re.sub(r'\s*\(.*\)', '', place)):
        place, note = '', rest
    if heading.startswith('preživeli') or heading.startswith('ostali'):
        info = '; '.join(notes + [rest, heading])
    else:
        info = '; '.join(notes + [rest, 'padli cankarjevci: ' + heading[0].lower() + heading[1:]])
    rec = _record(last, given, '', info)
    home = re.sub(r'\s*\(.*$', '', place).strip()
    if home and not re.search(r'\d', home):
        rec['birth_place'] = home
    if heading.startswith('preživeli') or heading.startswith('ostali'):
        if re.search(r'\(umrl', rest):
            rec['death_type'] = 'umro'
    elif not NOT_FALLEN.search(rest):
        rec['death_type'] = 'streljan' if re.search(r'ustreljen', rest) else 'poginuo'
        battle = next((v for k, v in BATTLES.items() if heading.startswith(k)), None)
        if battle:
            rec['death_place'], rec['death_date'] = battle
        if re.search(r'padel pri Jamniku 11\. III\. 1942', rest):        # "Sever Marjan, Ljubljana (padel pri ...)"
            rec['death_place'], rec['death_date'] = 'Jamnik', '11. 3. 1942'
        if re.search(r'padel na Visokem', rest):                       # "Maček Ivan, Škofja Loka, padel na Visokem"
            rec['death_place'] = 'Visoko'
    elif re.search(r'po vojni', rest):
        rec['death_type'] = 'umro'
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """The staff's duties, the Spanish fighters and the narodni heroji go into the entry of the man in the lists."""
    out = list(soldiers)
    for given, last, note, ln, fields in EXTRA_NAMES:
        alive = 'živ' in note
        cands = [s for s in soldiers if fold(s['last_name']) == fold(last) and fold(s['first_name']) == fold(given)
                 and (not alive or s.get('death_type') != 'poginuo')]
        if not cands:                                               # "Matija Blejec" / "Bleje Matija", "Stane"/"Stanko"
            cands = [s for s in soldiers if fold(s['first_name']) in (fold(given), {'stane': 'stanko'}.get(fold(given)))
                     and SequenceMatcher(None, fold(s['last_name']), fold(last)).ratio() >= 0.8
                     and (not alive or s.get('death_type') != 'poginuo')]
        if alive and not cands and given == 'Anton':                # "Anton Dežman" / "Dežman Tone" (spomenica)
            cands = [s for s in soldiers if fold(s['last_name']) == fold(last) and s['first_name'] == 'Tone']
        text = note.replace(' (živ)', '')
        if len(cands) == 1:
            s = cands[0]
            s['additional_info'] = '; '.join(x for x in (s['additional_info'], text) if x)
            s.update(fields)                                        # the duty and company at Dražgoše
            continue
        if len(cands) > 1:                                          # "Gregor Rupnik": the elder or the younger
            continue
        rec = _record(last, given, '', text)                        # named only here
        rec.update(pdf_page=ln['page'], pdf_y=ln['y'], pdf_x=round(ln['x'], 1), pdf_file='cankarjev-bataljon.pdf')
        out.append(rec)
    return out


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/cankarjev-bataljon.pdf',
        brigade_code=170,
        output_path='website/public/cankarjev-bataljon-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
