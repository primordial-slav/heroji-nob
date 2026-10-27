"""The Dalmatinci u Prvoj proleterskoj list's broken headings (2026-10-27). The book prints "SURNAME Father GIVEN
NICKNAME, rođen ...", the father's place ". . ." where it isn't known; the parser, and the split of the glued entries
(scripts/split_dalmatinci_glued.py), read some headings wrong:
- the nickname run into the given name ("NIKO PRPIĆ" as Nikoprpić, "IVO ŽUTI" Ivožuti), or kept with the hyphen of
  its line break ("BAJ- / LO" as Baj-Lo); it goes into the text as "zvani X;", as the list's other records have it;
- a given name broken over two lines ("GOJ- / KO" Goj-Ko), joined again;
- a double surname printed without its hyphen read as surname and given name ("MARTINOVIĆ STANIĆ Petra MANDE");
- a heading glued after another man's line ("POPOVIĆ Milivoja MAR- / KO MARKIĆ" as "Ko Markić", "JELASKA
  Maksimilijana MILENA ZIJA" as "Milena Zija", "BOZANIC Ante KATA TINA KNEZ" as "Tina Knez");
- the words after ". . ." read as a name ("BUBALO . . . JOZO. U NOB-u" as "Bubalojozou NOB-u");
- the given name of an "(ili X) . . . NAME" heading lost;
- four men on p. 182 whose records sit one heading back (each has his own text at the man before's line), one of
  them (Petković Ivana Jakov "Ćore") with no record at all; Grlić Marko at Grlić J. Anka's line on p. 285, she with
  none; Suša Gojko and Svoboda Pero in one record (p. 287).
Each fix was read from the page. Usage, from the project root: python scripts/fix_dalmatinci_names.py --start=N [--write]
"""
import json
import re
import sys

sys.path.insert(0, 'data-extraction')
sys.path.insert(0, 'scripts')
sys.stdout.reconfigure(encoding='utf-8')
import parse_dalmatinci_prva_proleterska as P  # noqa: E402
from split_dalmatinci_glued import box  # noqa: E402

PDF = 'website/public/pdfs/dalmatinci-prva-proleterska.pdf'
UNIT = 'website/public/prva-proleterska-soldiers.json'
R = '"Dalmatinci u Prvoj proleterskoj": the heading read from the page (scripts/fix_dalmatinci_names.py), 2026-10-27'

# soldier -> (surname, father as printed, the father's nominative, given name, nickname); None keeps the field
NAMES = {
    '0001403038': (None, None, None, 'Ante', 'Adamov'),            # DIVIĆ Ike ANTE ADA-MOV
    '0001403048': ('Finzi-Malzalta', 'Josipa-Bepa', 'Josip-Bepo', 'Matilda', None),   # FINZI MALZALTA Josipa-Bepa MATILDA
    '0001403053': (None, None, None, 'Joso', 'Krstun'),            # GRUBIŠIĆ Krste JOSO KRSTUN
    '0001403106': (None, None, None, 'Stevo', 'Pliva'),            # ODOVIĆ Jove STE-VO-PLIVA
    '0001403107': (None, None, None, 'Ivan', 'Ivo'),               # OMEROVIĆ Ivana IVAN IVO
    '0001403117': (None, None, None, 'Branko', 'Popivačev'),       # PUTNIKOVIĆ Konstantina BRANKO-POPIVAČEV
    '0001403133': ('Šupe-Rak', None, None, 'Ikica', 'Ika'),        # ŠUPE-RAK Ivana IKICA / IKA
    '0001400053': (None, None, None, 'Ivo', 'Žuti'),
    '0001400071': (None, None, None, 'Ivo', 'Ive'),
    '0001400081': (None, None, None, 'Ivo', 'Cigo'),
    '0001400100': (None, None, None, 'Petar', 'Mađar'),
    '0001403166': ('Bubalo', '', '', 'Jozo', None),                # BUBALO . . . JOZO. U NOB-u 1943.
    '0001403167': (None, None, None, 'Ante', 'Marinčić'),
    '0001400156': (None, None, None, 'Milovan', None),             # MILO- / VAN
    '0001400224': (None, None, None, 'Lazo', None),                # LAZÖ (ili GO- / LIĆ)
    '0001400255': (None, None, None, 'Krsto', 'Musa'),
    '0001400261': (None, None, None, 'Dane', 'Barela'),            # DANE BARE- / LA
    '0001400264': (None, None, None, 'Frane', 'Mojić'),            # FRANE MO- / JIĆ
    '0001400280': (None, None, None, 'Kajo', 'Vuko'),
    '0001400306': (None, None, None, 'Mijo', 'Mijutina'),
    '0001400309': (None, None, None, 'Živko', None),               # JOGIĆ (ili JOKIĆ) . . . ŽIV- / KO
    '0001403189': ('Jurković-Vajler', None, None, 'Dobrila', None),   # JURKOVIĆ-VAJLER DO- / BRILA
    '0001400333': (None, None, None, 'Gojko', None),
    '0001400354': (None, None, None, 'Nike', 'Šubašić'),
    '0001400355': (None, None, None, 'Niko', 'Prpić'),
    '0001400364': (None, None, None, 'Arsenije', None),
    '0001403198': ('Komandžija', '', '', 'Petar', None),           # KOMANDŽIJA . . . PE- / TAR. U NOB-u 1943.
    '0001400378': ('Popović', 'Milivoja', 'Milivoje', 'Marko', 'Markić'),   # POPOVIĆ Milivoja MAR- / KO MARKIĆ
    '0001400381': ('Kočić-Rak', None, None, 'Dragica', None),     # KOČIĆ-RAK Ivana DRAGI- / CA ž. MIRKA
    '0001400401': (None, None, None, 'Andrija', None),
    '0001400407': (None, '', '', 'Marija', 'Janja'),               # KOŠTAN . . . MARIJA JA- / NJA
    '0001400417': (None, None, None, 'Ivan', 'Iko'),
    '0001400453': (None, None, None, 'Vuco', None),                # KUZMAN Ante VUCO ro- / đen 1929
    '0001403214': ('Mandić', 'K', '', 'Paško', 'Raško'),           # MANDIĆ K. PAŠKO RAŠ- / KO
    '0001400495': (None, None, None, 'Božo', 'Jastreb'),
    '0001400508': (None, None, None, 'Stanko', 'Prpić'),
    '0001403231': ('Martinović-Stanić', 'Petra', 'Petar', 'Mande', None),   # MARTINOVIĆ STANIĆ / Petra MANDE
    '0001403235': (None, None, None, 'Kažimir', 'Miro'),           # KAŽI- / MIR-MIRO
    '0001400526': (None, None, None, 'Jovan', None),
    '0001400552': ('Jelaska', 'Maksimilijana', 'Maksimilijan', 'Milena', 'Zija'),   # JELASKA Maksimilijana MILENA ZIJA
    '0001400561': (None, None, None, 'Mileva', None),              # MILIŠIĆ Ante MILEVA ž. Petra
    '0001400563': (None, None, None, 'Branko', None),
    '0001400588': (None, None, None, 'Mate', 'Matacin'),
    '0001400592': (None, None, None, 'Mijo', 'Crnogaća'),
    '0001403251': (None, None, None, 'Miljenko', 'Brico'),
    '0001400637': (None, None, None, 'Josip', 'Pikulo'),
    '0001403257': ('Petković-Komadina', 'Ante', 'Ante', 'Kata', None),   # PETKOVIĆ KOMADINA Ante KATA
    '0001403256': ('Petković-Barić', 'Lovre', 'Lovre', 'Josip', None),   # PETKOVIĆ BARIĆ Lovre JOSIP
    '0001400669': (None, None, None, 'Stanko', 'Kedžo'),
    '0001400683': (None, None, None, 'Matilda', None),
    '0001400695': (None, None, None, 'Mile', 'Picunov'),
    '0001400721': (None, None, None, 'Božo', 'Barikada'),
    '0001400743': (None, None, None, 'Tugomir', None),
    '0001400746': (None, None, None, 'Nikola', 'Niko'),            # NIKO-NI- / KOLA; the roster's Radoš Nikola
    '0001400748': (None, None, None, 'Benjamin', 'Bajlo'),         # BENJANIN BAJ- / LO; the roster's Rak Benjamin
    '0001400749': (None, None, None, 'Frane', 'Nane'),
    '0001400750': (None, None, None, 'Joso', 'Jole'),
    '0001400776': (None, None, None, 'Ivan', 'Ivo'),
    '0001400782': (None, None, None, 'Duje', 'Ukić'),
    '0001400814': (None, None, None, 'Savo', None),                # SLAVICA (ili SAVICA) . . . SAVO
    '0001400843': ('Suša', '', '', 'Gojko', None),                 # SUŠA . . . GOJKO, then SVOBODA . . . PERO
    '0001400850': ('Božanić', 'Ante', 'Ante', 'Kata', 'Tina'),     # BOZANIC Ante KATA TINA KNEZ
    '0001400925': (None, None, None, 'Vaso', 'Joso'),
    '0001400928': (None, None, None, 'Pavle', 'Kalić'),            # PAVLE KA- / LIĆ
    '0001400944': (None, None, None, 'Antica', 'Malena'),
    '0001401076': (None, '', '', 'Slavko', 'Slavka'),              # ŠUPE . . . SLAVKO SLAV- / KA
    '0001401096': (None, None, None, 'Ivo', 'Ivan'),
    '0001400966': ('Ćogelja', None, None, 'Šime', None),           # ĆOGELJA (ili ĆOGA) . . . ŠIME
    '0001403162': (None, None, None, 'Jure', None),                # BEVANDA (ili IVANDA) . . JURE
}
# the text as it should read where the heading's words were left in it, or the scan lost a part
TEXT = {
    '0001403048': ('Josipa-Bepa MATILDA, ', ''),
    '0001403107': ('rođen Supetar', 'rođen 1912, Supetar'),
    '0001403166': ('1943. Bio u 6. bataljonu.', 'U NOB-u 1943. Bio u 6. bataljonu.'),
    '0001400224': ('(ili GO-LIĆ)f', '(ili GOLIĆ)'),
    '0001400309': ('(ili JOKIĆ) . . . ŽIV-KO', '(ili JOKIĆ)'),
    '0001403198': ('1943. Bugojno.', 'U NOB-u 1943. Bugojno.'),
    '0001400381': ('rođena 1920.', 'ž. Mirka, rođena 1920.'),
    '0001400453': ('1929, Vojnić', 'rođen 1929, Vojnić'),
    '0001403231': ('Petra MANDE, ', ''),
    '0001400561': ('rođena 1896', 'ž. Petra, rođena 1896'),
    '0001403257': ('Ante KATA, ', ''),
    '0001403256': ('Lovre JOSIP, ', ''),
    '0001400724': ('rođen Biljane Gornje', 'rođen 1917, Biljane Gornje'),
    '0001400748': ('rođen Rakovo Selo', 'rođen 1924. Rakovo Selo'),
    '0001400814': ('(ili SAVICA) . . . SAVO. ', '(ili SAVICA) '),
    '0001400843': (None, ''),                                        # Suša's heading stands alone; the text is Svoboda's
    '0001400850': ('rođena 1922.', 'Knez, rođena 1922.'),
    '0001400966': ('(ili ĆOGA) . .. ŠIME, ', '(ili ĆOGA) '),
    '0001403162': ('(ili IVANDA) . . JURE. ', '(ili IVANDA) '),
}
YEARS = {'0001403107': '1912', '0001400724': '1917'}
# records whose heading is elsewhere on the page: page, the heading's left and top (the parser's line)
MOVE = {
    '0001403256': (182, 140.8, 655.2),     # Petković-Barić Lovre Josip
    '0001403257': (182, 263.4, 514.8),     # Petković-Komadina Ante Kata
    '0001403258': (182, 385.3, 469.5),     # Petković-Barić Martina Marko
    '0001403173': (285, 348.2, 601.1),     # Grlić Marko
    '0001400843': (287, 211.5, 340.9),     # Suša Gojko: his own line, Svoboda's after it
}
# the roster's records the same scan's caron loss reached ("Radoš Marka Duro", zvani Juko: Đuro)
ROSTER = {'0001010194': {'first_name': 'Đuro'}}
# men with no record: (new id, after which record, page, heading's left and top, record fields)
ADD = [
    ('0001403328', '0001403256', (182, 139.8, 333.6),
     {'last_name': 'Petković', 'middle_name': 'Ivana', 'first_name': 'Jakov', 'nick': 'Ćore'}),
    ('0001403329', '0001403173', (285, 348.2, 577.1),
     {'last_name': 'Grlić', 'middle_name': 'J', 'first_name': 'Anka', 'text': 'Dubrovnik, rođena 1924. Borac 4. bataljona.'}),
    ('0001403330', '0001400843', (287, 211.5, 349.0),
     {'last_name': 'Svoboda', 'middle_name': '', 'first_name': 'Pero', 'text': 'rođen 1922. U NOB-u 1942. Borac 2. bataljona.'}),
]


# entries glued into another's text behind a surname the scan spaced out ("JE LAVI Ć Ivana FRANE, rođen 1919"), which
# the split of 2026-10-17 couldn't see: the host keeps its text up to the heading, each man a record of the list
GLUED = re.compile(r'(?<=[.!?»] )([A-ZČĆŽŠĐ](?: ?[A-ZČĆŽŠĐ]){2,})\s+([A-ZČĆŽŠĐ][a-zčćžšđ]+)\s+([A-ZČĆŽŠĐ]{2,})\s*,\s*rođen')


def glued(start, first_new):
    lines = P.extract(PDF, 1, None)
    starts = [i for i, ln in enumerate(lines) if ln['text'].startswith('§x§')]

    def line_at(page, x, y):
        return min((i for i, ln in enumerate(lines) if ln['page'] == page and abs(ln['x'] - x) < 3),
                   key=lambda i: abs(lines[i]['y'] - y))

    d = json.load(open(UNIT, encoding='utf-8'))
    hosts = []
    for s in d:
        for e in [s] + list(s.get('other_sources') or ()):
            if e.get('pdf_file') == 'dalmatinci-prva-proleterska.pdf' and GLUED.search(e.get('additional_info') or ''):
                hosts.append((s, e))
    heads_at = {}
    for s, e in hosts:
        i = line_at(e['pdf_page'], e['pdf_x'], e['pdf_y'])
        j = min([k for k in starts if k > i] + [len(lines)])
        found = []
        for m in GLUED.finditer(e['additional_info']):
            surname = m.group(1).replace(' ', '')
            k = next(q for q in range((found[-1][1] + 1) if found else i + 1, j)
                     if lines[q]['text'].replace(' ', '').replace('§x§', '').startswith(surname))
            found.append((m, k))
        heads_at[(s['soldier_id'], e.get('soldier_id') or s['soldier_id'])] = (i, j, found)
    corr, n = [], first_new
    for (keeper, host), (i, j, found) in heads_at.items():
        text = next(e for s, e in hosts if (e.get('soldier_id') or s['soldier_id']) == host)['additional_info']
        corr.append({'action': 'edit', 'soldier_id': host,
                     'fields': {'additional_info': text[:found[0][0].start()].strip(), **box(lines[i:found[0][1]])},
                     'reason': f"the next entries were glued into its text (a surname the scan spaced out); {R}"})
        for h, (m, k) in enumerate(found):
            end = found[h + 1][0].start() if h + 1 < len(found) else len(text)
            seg = text[m.start():end].strip().replace(m.group(1), m.group(1).replace(' ', ''), 1)
            rec = P.parse(seg)
            rec.pop('full_name', None)
            rec.pop('fathers_name', None)            # the normalizer puts the genitive in the nominative
            last_line = (found[h + 1][1] if h + 1 < len(found) else j)
            ln = lines[k]
            rec.update({'pdf_file': 'dalmatinci-prva-proleterska.pdf', 'pdf_page': ln['page'], 'pdf_x': ln['x'],
                        'pdf_y': ln['y'], **box(lines[k:last_line])})
            new_id = f'0001{400000 + n:06d}'
            corr.append({'action': 'add', 'soldier_id': keeper, 'new_id': new_id, 'record': rec,
                         'reason': f"{rec['last_name']} {rec['middle_name']} {rec['first_name']}: glued into another's entry behind "
                                   f"a surname the scan spaced out (\"{m.group(1)}\"); {R}"})
            n += 1
    for k, c in enumerate(corr):
        c['id'] = start + k
    return corr


def main():
    start = int(next(a for a in sys.argv if a.startswith('--start=')).split('=')[1])
    if '--glued' in sys.argv:
        corr = glued(start, 3331)
        for c in corr:
            f = c.get('fields') or c.get('record')
            print(c['id'], c['action'], c.get('new_id') or c['soldier_id'], '|', f.get('last_name', ''), f.get('middle_name', ''),
                  f.get('first_name', ''), '|', (f.get('additional_info') or '')[-70:], '|', f.get('pdf_page'), f.get('pdf_y'), f.get('pdf_y_end'))
        if '--write' in sys.argv:
            allc = json.load(open('corrections.json', encoding='utf-8'))
            assert not {c['id'] for c in corr} & {c['id'] for c in allc}, 'ids taken'
            allc += corr
            open('corrections.json', 'w', encoding='utf-8', newline='\r\n').write(json.dumps(allc, ensure_ascii=False, indent=2))
            print('written', corr[0]['id'], '-', corr[-1]['id'])
        return
    lines = P.extract(PDF, 1, None)
    starts = [i for i, ln in enumerate(lines) if ln['text'].startswith('§x§')]

    def line_at(page, x, y):
        return min((i for i, ln in enumerate(lines) if ln['page'] == page and abs(ln['x'] - x) < 3),
                   key=lambda i: abs(lines[i]['y'] - y))

    # every heading's line: the parser's starts, and the ones fixed here
    heads = set(starts) | {line_at(*p) for p in MOVE.values()} | {line_at(*a[2]) for a in ADD}

    def entry(page, x, y):
        i = line_at(page, x, y)
        j = min([k for k in heads if k > i] + [len(lines)])
        ln = lines[i]
        return i, j, {'pdf_page': ln['page'], 'pdf_x': ln['x'], 'pdf_y': ln['y'], **box(lines[i:j])}

    d = {s['soldier_id']: s for s in json.load(open(UNIT, encoding='utf-8'))}
    corr = []
    for sid, (last, mid, fat, first, nick) in NAMES.items():
        s = d[sid]
        f = {}
        if last is not None:
            f['last_name'] = last
        if mid is not None:
            f['middle_name'] = mid
            f['fathers_name'] = fat
        f['first_name'] = first
        text = s.get('additional_info') or ''
        if sid in TEXT:
            old, new = TEXT[sid]
            if old is None:
                text = new
            else:
                assert old in text, (sid, old, text[:80])
                text = text.replace(old, new, 1)
        if nick and not text.startswith(('zvani ', 'zvana ')):
            text = f'zvani {nick}; {text}'.strip()
        if text != (s.get('additional_info') or ''):
            f['additional_info'] = text
        if sid in YEARS:
            f['birth_year'] = YEARS[sid]
        if sid in MOVE:
            f.update(entry(*MOVE[sid])[2])
        corr.append({'action': 'edit', 'soldier_id': sid, 'fields': f,
                     'reason': f"{s['full_name']}: {R}"})
    for sid, page_pos in MOVE.items():
        if sid not in NAMES:
            corr.append({'action': 'edit', 'soldier_id': sid, 'fields': entry(*page_pos)[2],
                         'reason': f"{d[sid]['full_name']}: the record stood at the heading before its own; {R}"})
    for new_id, after, pos, rec in ADD:
        i, j, place = entry(*pos)
        text = rec.pop('text', None)
        if text is None:     # the entry's own text, from its heading's line to the next heading
            body = ' '.join(lines[k]['text'].replace('§x§', '') for k in range(i, j))
            body = re.sub(r'(\w)- (\w)', r'\1\2', body)          # a word the line broke ("Vr- polje")
            text = body.split(', ', 1)[1] if ', ' in body else body
        nick = rec.pop('nick', None)
        if nick:
            text = f'zvani {nick}; {text}'
        rec.update({'additional_info': text, 'pdf_file': 'dalmatinci-prva-proleterska.pdf', **place})
        corr.append({'action': 'add', 'soldier_id': after, 'new_id': new_id, 'record': rec,
                     'reason': f"{rec['last_name']} {rec['middle_name']} {rec['first_name']}: no record held the heading; {R}".replace('  ', ' ')})
    for sid, f in ROSTER.items():
        corr.append({'action': 'edit', 'soldier_id': sid, 'fields': f,
                     'reason': f"{d[sid]['full_name']}: the caron the scan lost; zvani Juko, the Dalmatinci list's \"JUKO ĐURO\""})
    for k, c in enumerate(corr):
        c['id'] = start + k
    for c in corr:
        f = c.get('fields') or c.get('record')
        print(c['id'], c['action'], c.get('new_id') or c['soldier_id'], '|', f.get('last_name', ''), f.get('middle_name', ''),
              f.get('first_name', ''), '|', (f.get('additional_info') or '')[:60], '|', f.get('pdf_y', ''))
    if '--write' in sys.argv:
        allc = json.load(open('corrections.json', encoding='utf-8'))
        assert not {c['id'] for c in corr} & {c['id'] for c in allc}, 'ids taken'
        allc += corr
        open('corrections.json', 'w', encoding='utf-8', newline='\r\n').write(json.dumps(allc, ensure_ascii=False, indent=2) + '\n')
        print('written', corr[0]['id'], '-', corr[-1]['id'])


if __name__ == '__main__':
    main()
