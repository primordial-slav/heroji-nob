"""
Parser: Kosovelova brigada, 19. SNOUB "Srečko Kosovel" (brigade code 142).

Source: Stanko Petelin, "Kosovelova brigada" (Knjižnica NOV in POS 22; znaci.org 00003/773.pdf)
        →  website/public/pdfs/kosovelova.pdf (book pp. 803-824):
    pp. 2-17    "Seznam padlih, pogrešanih in za posledicami ran umrlih borcev" (504 names, the book says), two
                columns, each entry hanging:
                    Abram Marjan, rojen 5. febru-
                        arja 1923, Kosovelje, umrl 29.
                        aprila 1945, Kosovelje
    pp. 18-22   "Poveljniški kader": the brigade's and its battalions' commanders, deputies, commissars, their
                assistants and the chiefs of staff, one a line under the duty, "Turšič Ivan-Iztok od 23. 9. 1943 do
                4. 3. 1944". A man who held several duties is one record with each of them.
The text layer reads j as i ("roien", "iunija", "Colia" = Colja) and l as i ("umri" = umrl).
"""
import re

from _parser_scaffold import _record, extract_lines_single_column, extract_lines_two_column, run_parser
from _slovene_lists import OWN, fix_ocr, given_names, name_part, surnames_and_places

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
COMMAND_FROM = 18
INTRO_END = 260                                                              # p. 2: the list starts under the foreword
# "Abram Marjan, rojen", "Benčič Jože rojen", "Božeglav Edvard-Brdavs, rojen", "Bune Oskar, roien"
START = re.compile(rf"^(?:[{U}]|[šžč][{L}])[^,\d]{{2,40}}?[,.]?\s+r[o0]i?[ij1l]\s*e\s*[nm]a?\b")
DUTY = re.compile(r'^(?:Komandant|Namestni|Namesinik|Politi|Pomo[čć]ni|Na[čć]elni|Nov \d|\d\. bataljon)')
MONTHS = {'januaria': 'januarja', 'februaria': 'februarja', 'iunija': 'junija', 'iulija': 'julija', 'iuliia': 'julija',
          'maia': 'maja', 'ianuaria': 'januarja', 'oikltobra': 'oktobra', 'iunija': 'junija'}
FATES = [(r'pogrešan[a]?', 'nestao'), (r'ustreljen[a]?|ustreljan|obešen[a]?', 'streljan'), (r'umrl[a]?|utonil[a]?', 'umro'),
         (r'pad[e]?l[a]?', 'poginuo'), (r'ubit[a]?|sežgan[a]?', 'ubijen')]
# the duty headings, in the singular
DUTIES = [(r'^komandant\w*', 'komandant'), (r'^namest?[ns]i[nk]\w* komandanta', 'namestnik komandanta'),
          (r'^politi\w+ komisar\w*', 'politični komisar'), (r'^pomo[čć]ni\w* politi\w+ komisarja', 'pomočnik političnega komisarja'),
          (r'^na[čć]elni\w* štaba', 'načelnik štaba')]
# first letters the scan cut off at the page's edge ("ieražin Robert"), and other names it garbled
NAME_FIXES = {'ieražin': 'Seražin', 'romšič': 'Tomšič', 'lorvat': 'Horvat', 'Boìeglav': 'Božeglav', 'Emi]': 'Emil',
              'Jemej': 'Jernej', 'Karei': 'Karel', 'Drej ček': 'Drejček', 'Kođrič': 'Kodrič', 'Fepi': 'Pepi',
              'Sibelja': 'Šibelja', 'Skrk': 'Škrk', 'Zom': 'Zorn', 'Zigon': 'Žigon', 'Zerjal': 'Žerjal', 'Svigelj': 'Švigelj',
              'Spacapan': 'Špacapan', 'Sebenik': 'Šebenik', 'Skabar': 'Škabar', 'Baie': 'Bajc'}


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    fallen = extract_lines_two_column(pdf_path, start, COMMAND_FROM - 1, 'auto')
    fallen = [ln for ln in fallen if not (ln['page'] == 2 and ln['y'] < INTRO_END)]
    fallen.sort(key=lambda l: (l['page'], l['x'] > 230, l['y']))
    command = extract_lines_single_column(pdf_path, COMMAND_FROM, end)
    out, duty, unit = [], '', 'brigade'
    for ln in fallen:
        t = ln['text'].strip()
        if re.fullmatch(r"[\d\W]{1,6}", t):
            continue
        out.append(dict(ln, text=('§p§ ' if START.match(t) else '') + t))
    for ln in command:
        t = ln['text'].strip()
        if re.fullmatch(r"[\d\W]{1,6}|POVELJNIŠKI KADER|brigade|\*.*|preimenovan.*|taljon postai.*|decembra preimen.*|sk'i partizan.*", t):
            continue
        if re.match(r'^(?:Nov )?\d\. bataljon', t):
            unit = re.sub(r'[*:]|\s+f$', '', t).strip().replace(' (prej 2.)', ', prej 2.')
            continue
        if DUTY.match(t):
            duty = re.sub(r'\s+brigade$', '', t).strip()
            if re.search(r'brigad', t) or duty.endswith('brigado'):
                unit = 'brigade'
            continue
        if re.match(r'^\(zastopal', t):                                     # "(zastopal komandanta) od ..." under the name
            out.append(dict(ln, text=t))
            continue
        out.append(dict(ln, text=f'§k§{duty}|{unit}§ ' + t))
    return out


def clean(text: str) -> str:
    text = re.sub(r'(?<=[a-zčšž])[­-]\s+(?=[a-zčšž])', '', text)        # "Voj- ščica", "pa­ del"
    text = text.replace("'", '').replace('’', '')                              # "2'4. marca"
    text = re.sub(r'\br[o0]i?[ij1l]\s*e\s*[nm](a?)\b', r'rojen\1', text)        # "roien", "roijen", "rojem"
    text = re.sub(r'\b(\d{1,2})[.,]\s*(?=[a-z])', r'\1. ', text)                 # "11aprila", "10, septembra"
    text = re.sub(r'\b1Ž\.', '12.', text)
    text = re.sub(r'\b(\d{1,2})(?=(?:januar|februar|marc|april|maj|junij|julij|avgust|septemb|oktob|novemb|decemb))', r'\1. ', text)   # "1marca"
    text = text.replace('februari a', 'februarja').replace('jamuar', 'januar')
    text = text.replace('Poreaen', 'Porezen').replace('Čmomelj', 'Črnomelj')
    text = re.sub(r'\b(ap|mar|februar)\s+(rila|ca|i a)\b', lambda m: m.group(1) + m.group(2).replace(' ', '').replace('ia', 'ja'), text)
    text = text.replace('ustreljen.', 'ustreljen').replace('pogrešan oa ', 'pogrešan od ')
    text = re.sub(r'\bu[ij]?mi?r[il]\b', 'umrl', text)                       # "umri", "ujmrl", "umiri"
    text = re.sub(r'\bpade[\]i]|\bpadtei\b', 'padel', text)
    text = re.sub(r'\bpogreša\b', 'pogrešan', text)
    text = re.sub(r'\bustr[eé]l[ij]en\b|\bustreljan\b', 'ustreljen', text)
    text = re.sub(r'^(\S+?)-\s+(?=[A-ZČŠŽ])', r'\1 ', text)                  # "Zbogai- Angel"
    text = re.sub(r'\bTmov', 'Trnov', text).replace('CerKno', 'Cerkno')
    text = re.sub(r'\bRižar?ma\b', 'Rižarna', text)
    for a, b in MONTHS.items():
        text = re.sub(rf'\b{a}\b', b, text)
    text = re.sub(r'\b(januar|februar|septem|okto|novem|decem)\s+(ja|bra|ba)\b', r'\1\2', text)
    text = text.replace('j ulij a', 'julija').replace('februar ja', 'februarja')
    return re.sub(r'\s+', ' ', text).strip()


def known_j(word: str) -> str:
    """'Colia' = Colja, 'Cigoi' = Cigoj: an i the corpus knows as j."""
    sur, plc = surnames_and_places()
    if sur[word] or given_names()[word]:
        return word
    for i in [m.start() for m in re.finditer('i', word)]:
        cand = word[:i] + 'j' + word[i + 1:]
        if sur[cand] >= 2 or given_names()[cand] >= 5:
            return cand
    return word


def parse_fallen(text: str) -> dict:
    text = clean(fix_ocr(text))
    m = re.search(r',?\s+rojen(a?)\b\s*', text)
    if not m:
        raise ValueError(text)
    head, rest = text[:m.start()], text[m.end():]
    for a, b in NAME_FIXES.items():
        head = re.sub(rf'\b{re.escape(a)}(?=\W|$)', b, head)
    last, given, notes = name_part(head)
    last, given = known_j(last), known_j(given)
    info = '; '.join(notes + ['rojen' + m.group(1) + ' ' + rest])
    rec = _record(last, given, '', info)
    born = re.match(r'^((?:\d{1,2}\.\s*)?(?:[a-z]+\s+)?(?:[a-z]\s+)?(1[89]\d\d)|\(\?\))[,.]?\s*', rest)
    tail = rest[born.end():] if born else rest
    if born and born.group(2):
        rec['birth_year'] = born.group(2)
    fate = None
    for pat, kind in FATES:
        fm = re.search(rf'\b(?:{pat})\b', tail)
        if fm and (fate is None or fm.start() < fate[0].start()):
            fate = (fm, kind)
    if fate:
        fm, kind = fate
        place = tail[:fm.start()].strip(' ,.')
        if place and not re.search(r'\d|\?', place):
            rec['birth_place'] = place
        rec['death_type'] = kind
        after = tail[fm.end():].strip(' ,')
        dm = re.match(r'^((?:\d{1,2}\.\s*)?(?:[a-z]+\s+)?(?:19\d\d)|\(\?\)\s*(?:19\d\d)?)[,.]?\s*', after)
        if dm and re.search(r'19\d\d', dm.group(1)):
            rec['death_date'] = re.sub(r'^\(\?\)\s*', '', dm.group(1)).strip()
        where = after[dm.end():] if dm else after
        where = re.sub(r'^(?:pri|v|na|blizu)\s+', '', where.strip(' ,.')) if kind != 'streljan' else where.strip(' ,.')
        if where and not re.search(r'neznano|\d|\?|bolnišnic|^v\s|^(?:od|konec|spomladi)\b|^[a-z]+a$', where) and kind != 'umro':
            rec['death_place'] = re.sub(r'^(?:v|pri|blizu)\s+', '', where)
    return rec


def parse_command(text: str) -> dict:
    m = re.match(r'^§k§([^|]*)\|([^§]*)§\s*', text)
    duty, unit = m.group(1), m.group(2)
    text = fix_ocr(text[m.end():]).replace(' cd ', ' od ').replace('°d ', 'od ')
    for a, b in NAME_FIXES.items():
        text = re.sub(rf'(?<!\w){re.escape(a)}(?=\W|$)', b, text)
    nm = re.search(r'\s+(?:od\s|\(zastopal|\d)', text)
    head, rest = (text[:nm.start()], text[nm.start():].strip()) if nm else (text, '')
    last, given, notes = name_part(head)
    rest = re.sub(r'(\d)\.1 (9\d\d)', r'\1. 1\2', rest.replace("'", ''))     # "4. 3.1 944", "2'3. 1."
    rest = re.sub(r'\s+', ' ', rest)
    duty = duty.lower()
    for pat, one in DUTIES:
        duty = re.sub(pat, one, duty)
    duty = re.sub(r'\s+brigad\w*$', '', duty)
    nov = re.match(r'^(Nov )?(\d\. bataljon)(.*)$', unit)
    where = ' brigade' if unit == 'brigade' else f" {'novega ' if nov.group(1) else ''}{nov.group(2)}a{nov.group(3)}"
    rec = _record(last, given, '', '; '.join(notes + [f'{duty}{where} {rest}'.strip()]))
    rec['_duty'] = True
    return rec


def parse_entry(text: str) -> dict:
    return parse_command(text) if text.startswith('§k§') else parse_fallen(re.sub(r'^§p§\s*', '', text))


def post(soldiers: list[dict]) -> list[dict]:
    """A commander who held several duties is one record, at the first line the list names him."""
    out, seen = [], {}
    for s in soldiers:
        if not s.pop('_duty', False):
            out.append(s)
            continue
        key = (s['last_name'], s['first_name'])
        if key in seen:
            first = seen[key]
            alias = re.match(r'^zvani [^;]+; ', s['additional_info'])
            add = s['additional_info'][alias.end():] if alias and first['additional_info'].startswith(alias.group()) else s['additional_info']
            first['additional_info'] += '; ' + add
            continue
        seen[key] = s
        out.append(s)
    return out


if __name__ == '__main__':
    OWN['file'] = 'kosovelova-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/kosovelova.pdf',
        brigade_code=142,
        output_path='website/public/kosovelova-soldiers.json',
        start_page=2,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[pk]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
