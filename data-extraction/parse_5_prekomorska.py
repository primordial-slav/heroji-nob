"""
Parser: 5. prekomorska brigada (brigade code 143).

Source: Albert Klun, Rado Bordon et al., "Peta prekomorska brigada" (Knjižnica NOV in POS; znaci.org 00003/816.pdf)
        →  website/public/pdfs/5-prekomorska.pdf (book pp. 283-301):
    pp. 1-14    "Seznam padlih borcev in bork" (256, the book says), one column, a paragraph each:
                    BAŠA FRANC, r. 26. decembra 1923 Podgraje—Ilirska Bistrica,
                        p. 28. februarja 1945 Gospić.
                r. = rojen, p. = padel, pg. = pogrešan, u. = umrl; "Village—Municipality".
    pp. 17-19   "Seznam vodilnega kadra brigade" (Albert Klun), run on under each unit's heading, given name first:
                    Komandant: Tone Kodrič; politični komisar: 1. Drago Kunaver, 2. Ivan Debenc; ...
                and the company commanders and commissars in alphabetical runs. A man who held several duties is one
                record with each of them.
"""
import re

from _parser_scaffold import _record, extract_lines_single_column, run_parser, title_case
from _slovene_lists import OWN, fix_ocr, read_given

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_TO, CADRE_FROM = 14, 17
# photo pages among the fallen: the caption under the grave at Divoselo (p. 5), a poem and the caption of the
# memorial at Ilirska Bistrica (p. 13)
CAPTIONS = {5: lambda y: y > 300, 13: lambda y: y < 230 or y > 430}
# "ČUŠ IVAN,", "ČUŠ Ivan,", "BENCIN,"; "<r." and "ir." are the scan's specks
START = re.compile(rf'^[{U}2][{U}02šžčćđ]+(?:\s+[{U}2][\w02]+)*(?:\s*\([^)]*\))?\s*,')
HEADINGS = re.compile(rf'^(?:ŠTAB BRIGADE|\d\. BATALJON|[{U}() ]*ČETA\b[{U} ]*$|KOMANDIRJI ČET|POLITIČNI KOMISARJ\w* [CČ]ET)')
# the companies' headings in the genitive: "komandir spremljevalne čete"
COMPANIES = {'SPREMLJEVALNA ČETA': 'spremljevalne čete', 'IZVIDNIŠKA (JU RI SNA) ČETA': 'izvidniške (jurišne) čete',
             'ČETA ZA ZVEZO': 'čete za zvezo', 'INTENDANTSKA ČETA': 'intendantske čete'}
FATE = [(r'\bpg\.', 'nestao', 'pogrešan'), (r'\bu\.', 'umro', 'umrl'), (r'\bp\.', 'poginuo', 'padel')]
NAME_FIXES = {'Jancz': 'Janez', 'Jemej': 'Jernej', 'Stojam': 'Stojan', 'StojanTroha': 'Stojan Troha', 'Ivam Cetntrih': 'Ivan Centrih',
              'Karei Pimat': 'Karel Pirnat', 'Frane Planine': 'Franc Planinc', 'Frane Cerne': 'Franc Černe', 'Jože Duiar': 'Jože Dular',
              'Miatks Katrn': 'Matks Katrn', 'Marjan Kavoič': 'Marjan Kavčič', 'Stane Maline': 'Stane Malinc', 'Ninat': 'Ninat',
              'Jože 2agar': 'Jože Žagar', 'Ivan Meke': 'Ivan Mekc'}


def unit_of(head: str) -> str:
    head = head.rstrip('*').strip()
    if head == 'ŠTAB BRIGADE':
        return 'brigade'
    m = re.match(r'^(\d)\. BATALJON', head)
    if m:
        return f'{m.group(1)}. bataljona'
    return COMPANIES.get(head, head.lower())


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_single_column(pdf_path, start, end)
    out = []
    for ln in lines:
        t = ln['text'].strip()
        if ln['page'] > FALLEN_TO or re.fullmatch(r'[\d\W]{1,5}|S E Z N A M|\d+ Peta prekomorska brigada', t):
            continue
        if CAPTIONS.get(ln['page'], lambda y: False)(ln['y']):
            continue
        out.append(dict(ln, text=('§p§ ' if START.match(t) else '') + t))
    # the cadre: the text of each unit, with where each character's line is
    cadre = [ln for ln in lines if ln['page'] >= CADRE_FROM and ln['text'].strip()
             and not re.fullmatch(r'[\d\W]{1,5}', ln['text'].strip()) and not ln['text'].lstrip().startswith('*')]
    cadre = [ln for ln in cadre if not re.match(r'^(?:je to označeno|namu\. Ime|ni bilo mogoče|tične komisar)', ln['text'].strip())]
    sections, cur = [], None
    for ln in cadre:
        t = ln['text'].strip()
        if HEADINGS.match(t):
            cur = {'unit': unit_of(t), 'text': '', 'at': []}
            sections.append(cur)
            continue
        if cur is None:
            continue
        if not cur['text']:
            joined = ''
        elif re.search(r'[a-zčšž][-­]$', cur['text']):                  # "Kuna-" / "ver": one word
            joined = cur['text'][:-1]
        else:
            joined = cur['text'] + ' '
        cur['at'].append((len(joined), ln))
        cur['text'] = joined + t
    for sec in sections:
        text = sec['text']

        def line_at(i: int) -> dict:
            at = [ln for pos, ln in sec['at'] if pos <= i]
            return at[-1] if at else sec['at'][0][1]

        if sec['unit'].startswith(('komandirji', 'politični komisarj')):
            duty = 'komandir čete' if sec['unit'].startswith('komandirji') else 'politični komisar čete'
            for m in re.finditer(r'[^,.]+', text):
                name = m.group().strip()
                if name:
                    out.append(dict(line_at(m.start()), text=f'§k§{duty}|§ {name}'))
            continue
        for part in re.finditer(r'([^:;]+):\s*([^;]+)', text):
            duty = part.group(1).strip().replace('pomoćnik', 'pomočnik').replace('komisar ja', 'komisarja')
            duty = duty[:1].lower() + duty[1:]                                 # "sekretar SKOJ", "oficir OZN"
            for m in re.finditer(r'\s*(?:\d\.\s*)?([^,]+)', part.group(2)):
                name = m.group(1).strip(' .')
                if name and name != '?' and not name.startswith('(?)'):
                    out.append(dict(line_at(part.start(2) + m.start(1)), text=f'§k§{duty}|{sec["unit"]}§ {name}'))
                elif name.startswith('(?)') and len(name) > 4:                   # "(?) dr. Kraševec": the given name unknown
                    out.append(dict(line_at(part.start(2) + m.start(1)), text=f'§k§{duty}|{sec["unit"]}§ {name[3:].strip()}'))
    return out


def place(text: str) -> str:
    """'Podgraje—Ilirska Bistrica' -> 'Podgraje, Ilirska Bistrica'."""
    text = re.sub(r'\s*[—–]+\s*', ', ', text.strip(' ,.'))
    return re.sub(r'^(?:na|v|okolica)\s+', '', text)


def parse_fallen(text: str) -> dict:
    text = fix_ocr(re.sub(r'(?<=[a-zčšž])[-­]\s+(?=[a-zčšž])', '', text))
    text = re.sub(r'\bir\.', 'r.', text)
    head, _, rest = text.partition(',')
    notes = []
    for note in re.findall(r'\(([^)]*)\)', head):                           # "(I.)", "(mitraljezec iz ZSSR)", "(IVAN?)"
        notes.append(f'ili {note.title()}' if re.fullmatch(rf'[{U}]+\?', note) else note)
    head = re.sub(r'\([^)]*\)', ' ', head).upper()                          # "HRAšEVEC"
    words = [w.replace('0', 'O').replace('2', 'Ž') for w in head.split()]
    rest = rest.strip()
    last, given = title_case(words[0]), ' '.join(title_case(w) for w in words[1:])
    rec = _record(last, read_given(given), '', '; '.join(notes + [rest.rstrip('.')]))
    fate = min(((re.search(pat, rest), kind, word) for pat, kind, word in FATE if re.search(pat, rest)),
               key=lambda x: x[0].start(), default=None)
    born = re.match(r'^r\.\s*(.*?)(?:,\s*|\s+)(?=(?:p|pg|u)\.|$)', rest)
    if born:
        b = born.group(1).strip(' ,.')
        y = re.search(r'\b(1[89]\d\d)\b', b)
        if y:
            rec['birth_year'] = y.group(1)
        where = re.sub(r'^(?:\d{1,2}\.\s*)?(?:[a-z]+\s+)?(?:1[89]\d\d)?[,.]?\s*', '', b)
        if where and not re.search(r'\d', where):
            rec['birth_place'] = place(where)
    if fate:
        fm, kind, word = fate
        rec['death_type'] = kind
        after = rest[fm.end():].strip(' .')
        dm = re.match(r'^((?:\d{1,2}\.\s*)?(?:[a-z]+\s+)?19\d\d)\b\.?\s*', after)
        if dm:
            rec['death_date'] = dm.group(1)
            after = after[dm.end():]
        if after and not re.search(r'\d', after):
            rec['death_place'] = place(after)
    return rec


def parse_command(text: str) -> dict:
    m = re.match(r'^§k§([^|]*)\|([^§]*)§\s*', text)
    duty, unit = m.group(1), m.group(2)
    name = fix_ocr(text[m.end():]).strip(' .')
    for a, b in NAME_FIXES.items():
        name = re.sub(rf'(?<!\w){re.escape(a)}(?!\w)', b, name)
    name = re.sub(r'\s*\((\w+)\)$', r'\1', name)                             # "Završnik-Pastir (ček)" = Pastirček
    notes = []
    if name.startswith('dr. '):
        notes.append('dr.')
        name = name[4:]
    words = name.split()
    alias = ''
    if '-' in words[-1]:                                                       # "Franc Mazovec-Risto": the partisan name
        words[-1], alias = words[-1].split('-', 1)
    last, given = words[-1][:1].upper() + words[-1][1:], ' '.join(words[:-1])   # "Franc šuštar"
    given = read_given(given[:1].upper() + given[1:]) if given else ''
    if alias:
        notes.append('zvani ' + alias)
    where = '' if not unit else (' brigade' if unit == 'brigade' else ' ' + unit)
    rec = _record(last, given, '', '; '.join(notes + [f'{duty}{where}']))
    rec['_duty'] = True
    return rec


def parse_entry(text: str) -> dict:
    return parse_command(text) if text.startswith('§k§') else parse_fallen(re.sub(r'^§p§\s*', '', text))


def post(soldiers: list[dict]) -> list[dict]:
    """A man named under several duties is one record."""
    out, seen = [], {}
    for s in soldiers:
        if not s.pop('_duty', False):
            out.append(s)
            continue
        key = (s['last_name'], s['first_name'])
        if key in seen:
            first = seen[key]
            add = re.sub(r'^(?:dr\.; )?(?:zvani [^;]+; )?', '', s['additional_info'])
            if add not in first['additional_info']:
                first['additional_info'] += '; ' + add
            continue
        seen[key] = s
        out.append(s)
    return out


if __name__ == '__main__':
    OWN['file'] = '5-prekomorska-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/5-prekomorska.pdf',
        brigade_code=143,
        output_path='website/public/5-prekomorska-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[pk]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
