"""
Parser: 1. i 2. prekomorska brigada (brigade code 144).

Source: Srečko Vilhar, Albert Klun, "Prva in druga prekomorska brigada" (Knjižnica NOV in POS 25-1, 1967; znaci.org
        00003/769.pdf) →  website/public/pdfs/1-2-prekomorska.pdf (book pp. 357-372):
    pp. 1-9     "Seznam padlih borcev in bork prve in druge prekomorske brigade" (Albert Klun), a paragraph each:
                    ADAM Anton, r. 26. 5. 1918 (Dol. Košana—Pivka), p. 26. 5. 1944 (Drvar).
                r. = rojen, p. = padel, u. = umrl; "(I.)", "(II.)" tell two men of one name apart.
    pp. 11-14   "Seznam vodilnega kadra": the staffs of the brigades in the camps at Carbonara and Gravina, on Korčula,
                Hvar and Vis, and of the joined brigades leaving Vis, run on under each unit, given name first
                ("Komandant: Savo Celebič, Milan Kmet; politkomisar: ..."); then the companies' officers in
                alphabetical runs, surname first ("Abinum Samuel, Bereta Joko, ..."). A man under several duties is
                one record with each of them.
"""
import re
import unicodedata

from _parser_scaffold import _record, extract_lines_single_column, run_parser, title_case
from _slovene_lists import OWN, fix_ocr, read_given

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_TO, CADRE_FROM = 9, 11
FATE = [(r'\bu\.', 'umro'), (r'\bp\.', 'poginuo'), (r'\bpogrešan[a]?\b', 'nestao')]
# the camp or island each staff list is for
PHASES = [(r'V CARBONARI', 'prva brigada v Carbonari'), (r'V GRAVINI', 'prva brigada v Gravini'),
          (r'NA OTOKU KORČULI', 'prva brigada na Korčuli'), (r'NA OTOKIH HVAR IN VIS', 'druga brigada na Hvaru in Visu'),
          (r'ŠTAB ZDRUŽENE', 'združena prva in druga brigada ob odhodu z Visa')]
COMPANY_LISTS = {'Komandirji čet': 'komandir čete', 'Politkomisarji čet': 'politkomisar čete',
                 'Pomočniki politkomisarjev čet': 'pomočnik politkomisarja čete',
                 'Namestniki komandirjev čet': 'namestnik komandirja čete'}
NAME_FIXES = {'Ferdinad': 'Ferdinand', 'Andrò': 'Andro', 'Zivic': 'Živic', 'Duro': 'Djuro', 'Celebic': 'Čelebič',
              'Celebič': 'Čelebič', 'Sukljan': 'Šukljan', 'Sav': 'Šav', 'Cukič': 'Čukič'}


def fold(text: str) -> str:
    t = (text or '').lower().replace('đ', 'dj')
    t = ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', t).replace('dj', 'd')


def entry_start(t: str) -> bool:
    """'ABRAM Marcelo,', 'JOKIČ, r.', 'FATUR Janez (II.),', 'URŠlC Anton,', 'STII3ELJ Ferdinand': the surname in
    capitals (the scan reads some letters small, B as 3, I as l)."""
    m = re.match(r'^(\S+)(?=[\s,(])', t)
    if not m or not re.match(rf'^[{U}2]', t):
        return False
    w = m.group(1).rstrip(',')
    caps = sum(c.isupper() or c in '023' for c in w)
    return len(w) >= 2 and caps >= max(2, len(w) - 2) and bool(
        re.match(rf'^\S+(?:\s+[{U}]{{2,}})*\s*(?:\([IV]+\.\)\s*)?(?:[{U}][{L}]|,)', t))   # "DEL MEDICO Franc", "MIRC RUDOLF,"


def phase_of(t: str) -> str | None:
    for pat, label in PHASES:
        if re.search(pat, t):
            return label
    return None


def unit_of(t: str) -> str | None:
    """'1. SLOVENSKI BATALJON' -> '1. slovenskega bataljona', 'ŠTAB BRIGADE' -> 'brigade', 'ŽENSKA ČETA'."""
    if re.match(r'^ŠTAB (?:BRIGADE|ZDRUŽENE)', t):
        return 'brigade'
    m = re.match(rf'^(\d)\.\s+(?:([{U}]+I)\s+)?BATALJON$', t)
    if m:
        adj = (m.group(2).lower()[:-1] + 'ega ') if m.group(2) else ''
        return f'{m.group(1)}. {adj}bataljona'
    if re.match(r'^ŽENSKA [CČ]ETA$', t):
        return 'ženske čete'
    return None


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_single_column(pdf_path, start, end)
    out = []
    for ln in lines:
        t = ln['text'].strip()
        if ln['page'] > FALLEN_TO or re.fullmatch(r'[\d\W]{1,5}', t):
            continue
        out.append(dict(ln, text=('§p§ ' if entry_start(t) else '') + t))
    cadre = [ln for ln in lines if ln['page'] >= CADRE_FROM and ln['text'].strip()
             and not re.fullmatch(r'[\d\W]{1,6}|\d+ 1\. in 2\. prekomorska brigada.*', ln['text'].strip())]
    sections, cur, phase, note = [], None, '', False
    for ln in cadre:
        t = ln['text'].strip()
        if t.startswith('Opomba:') or t.startswith('Zaradi večkratnih'):
            note = True
            continue
        if note and not (unit_of(t) or phase_of(t) or t in COMPANY_LISTS):
            continue                                                         # the editor's notes under the lists
        note = False
        ph = phase_of(t)
        if ph:
            phase = ph
            if not t.startswith('ŠTAB ZDRUŽENE'):
                continue
        if re.match(r'^(?:VODILNI KADER BRIGAD|OB ODHODU Z VISA)', t):
            continue
        u = unit_of(t)
        if u or t in COMPANY_LISTS:
            cur = {'unit': u or '', 'phase': '' if t in COMPANY_LISTS else phase, 'company': COMPANY_LISTS.get(t),
                   'text': '', 'at': []}
            sections.append(cur)
            continue
        if cur is None or re.fullmatch(r'\((?:prej|reorganizirani)[^)]*\)', t):
            if cur is not None and t.startswith('(prej'):
                cur['unit'] += ' ' + t                                        # "1. BATALJON (prej 4. bataljon)"
            continue
        if not cur['text']:
            joined = ''
        elif re.search(rf'[{L}][-­]$', cur['text']):                       # "Mar-" / "dešič": one word
            joined = cur['text'][:-1]
        else:
            joined = cur['text'] + ' '
        cur['at'].append((len(joined), ln))
        cur['text'] = joined + t.replace('Curk, pomočnik', 'Curk; pomočnik')   # the book's comma for a semicolon
    for sec in sections:
        text = sec['text']

        def line_at(i: int) -> dict:
            at = [ln for pos, ln in sec['at'] if pos <= i]
            return at[-1] if at else sec['at'][0][1]

        if not sec['at']:
            continue
        if sec['company']:
            for m in re.finditer(r'[^,.]+', text):
                name = m.group().strip()
                if name:
                    out.append(dict(line_at(m.start()), text=f"§c§{sec['company']}|{sec['phase']}§ {name}"))
            continue
        for part in re.finditer(r'([^:;]+):\s*([^;]+)', text):
            duty = part.group(1).strip().replace('-', '').replace('\u00ad', '')
            duty = re.sub(r'\b(po|na)\s+(močnik|mestnik)', r'\1\2', duty)       # "po- / močnik" over two lines
            duty = re.sub(r'^.*?\b(?=komandant|komandir|politkomisar|pomočnik|namestnik)', '', duty.lower(), count=1)
            for m in re.finditer(r'\s*([^,]+)', part.group(2)):
                name = m.group(1).strip(' .')
                if name:
                    where = 'brigade' if sec['unit'] == 'brigade' else sec['unit']
                    out.append(dict(line_at(part.start(2) + m.start(1)),
                                    text=f"§k§{duty} {where}|{sec['phase']}§ {name}"))
    return out


def surname(w: str) -> str:
    w = re.sub(r'[IJ]3', 'B', w).replace('3', 'B').replace('0', 'O').replace('2', 'Ž')
    w = re.sub(r'(?<=[A-ZČŠŽ])l(?=[A-ZČŠŽ]|$)', 'I', w)                       # "URŠlC"
    return title_case(w.upper())


def place(text: str) -> str:
    return re.sub(r'\s*[—–]+\s*', ', ', text.strip(' ,.'))


def parse_fallen(text: str) -> dict:
    text = fix_ocr(re.sub(rf'(?<=[{L}])[-­]\s+(?=[{L}])', '', text))
    head, _, rest = text.partition(',')
    notes = re.findall(r'\(([IV]+\.)\)', head)
    head = re.sub(r'\([^)]*\)', ' ', head).split()
    caps = [w for w in head if sum(c.isupper() or c in '023' for c in w) >= max(2, len(w) - 2)]
    if len(caps) == len(head) or len(caps) == 0:                             # "MIRC RUDOLF": the given name in capitals too
        caps = head[:1]
    last = ' '.join(surname(w) for w in caps)                                 # "DEL MEDICO Franc"
    given = ' '.join(title_case(w) if w.isupper() else w for w in head[len(caps):])
    rest = rest.strip()
    rec = _record(last, read_given(given), '', '; '.join(notes + [rest.rstrip('.')]))
    born = re.match(r'^r\.\s*([^,(]*?)\s*(?:,\s*)?(?:\(([^)]*)\))?\s*,', rest)
    if born:
        y = re.search(r'\b(1[89]\d\d)\b', born.group(1))
        if y:
            rec['birth_year'] = y.group(1)
        if born.group(2):
            rec['birth_place'] = place(born.group(2))
    fates = [(m, kind) for pat, kind in FATE for m in [re.search(pat, rest)] if m]
    if fates:
        fm, kind = min(fates, key=lambda x: x[0].start())
        rec['death_type'] = kind
        after = rest[fm.end():].strip()
        dm = re.match(r'^((?:\d{1,2}\.\s*\d{1,2}\.\s*|[a-z]+\s+)?19\d\d)\b', after)
        if dm:
            rec['death_date'] = dm.group(1)
            after = after[dm.end():]
        pm = re.match(r'^,?\s*\(([^)]*)\)', after)
        if pm and not re.search(r'\d', pm.group(1)):
            rec['death_place'] = place(pm.group(1))
    return rec


def parse_officer(text: str) -> dict:
    m = re.match(r'^§([kc])§([^|]*)\|([^§]*)§\s*', text)
    kind, duty, phase = m.group(1), m.group(2).strip(), m.group(3)
    name = fix_ocr(text[m.end():]).strip(' .')
    notes = []
    alt = re.search(r'\(([^)]*)\)', name)                                    # "Egon (Alfred) Nojman"
    if alt:
        notes.append('ili ' + alt.group(1))
        name = (name[:alt.start()] + name[alt.end():]).strip()
    words = name.split()
    if len(words) > 2 and words[1][:1].islower():                             # "Tom šič" broken over two lines
        words[:2] = [words[0] + words[1]]
    words = [w[:1].upper() + w[1:] for w in words]
    words = re.sub(r'(?<=[a-zčšž])\s+(?=[a-zčšž])', '', ' '.join(words)).split()
    words = [NAME_FIXES.get(w, w) for w in words]
    if kind == 'c':                                                           # the companies' lists: surname first
        last, given = words[0], ' '.join(words[1:])
    else:
        last, given = words[-1], ' '.join(words[:-1])
    rec = _record(last, read_given(given), '', '; '.join(notes + [f'{duty} ({phase})' if phase else duty]))
    rec['_duty'] = True
    return rec


def parse_entry(text: str) -> dict:
    if text.startswith(('§k§', '§c§')):
        return parse_officer(text)
    return parse_fallen(re.sub(r'^§p§\s*', '', text))


def post(soldiers: list[dict]) -> list[dict]:
    """A man named under several duties is one record (names compared without carons: "Čelebič", "Celebic")."""
    out, seen = [], {}
    for s in soldiers:
        if not s.pop('_duty', False):
            out.append(s)
            continue
        key = (fold(s['last_name']), fold(s['first_name']))
        if key in seen:
            first = seen[key]
            add = re.sub(r'^(?:ili [^;]+; )?', '', s['additional_info'])
            if add not in first['additional_info']:
                first['additional_info'] += '; ' + add
            continue
        seen[key] = s
        out.append(s)
    return out


if __name__ == '__main__':
    OWN['file'] = '1-2-prekomorska-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/1-2-prekomorska.pdf',
        brigade_code=144,
        output_path='website/public/1-2-prekomorska-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[pkc]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
