"""
Parser: 9. srpska udarna brigada (brigade code 165).

Source: "Deveta srpska udarna brigada u stroju i s narodom", spomen-knjiga (Beograd - Zaječar; znaci.org 00001/121)
        →  website/public/pdfs/9-srpska.pdf, the three lists znaci.org has (its chapters leave out the book's roll
        of the brigade with a bio of each, pp. 47-372):
    pp. 1-6     "Rođenje Devete / Stroj u Rečici": the 377 fighters at its founding on 11 March 1944, two columns,
                "ALEKSIĆ Vitomir Đura" (surname, given name, what he was called), and the political workers present
    pp. 7-22    "Komandni sastav brigade, bataljona i četa (11. 3. 1944 - 20. 5. 1945)": under each staff and company,
                the duty in a column on the left, "KECMAN Jovan Čeda 22.5.44.-15.5.45."; "Nije utvrđeno u kom su
                bataljonu i četi bili": "Komandiri: ANTONIJEVIĆ Branko, VELIČKOVIĆ Dušan, ..."
    pp. 23-26   "Bolničarke i borci / Stroj žena": "BABIĆ Jovičić (Sima) Jelena" (married name, father, given name)
Cyrillic; the OCR reads Л as Ј1 and spaces some surnames apart ("В АСИЋ"). A man in several lists is one record.
"""
import re
import unicodedata

import pdfplumber

from _parser_scaffold import _record, cyrillic_to_latin, run_parser, title_case
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LINEUP_TO, COMMAND_TO = 6, 22
SECTION = re.compile(r'^(?:ŠTAB|JEDINICE PRI|KOMANDA|Komanda|NIJE UTVRĐENO|KOMANDNI SASTAV|Sastav)')
# the duty labels, in the singular
DUTIES = [(r'^komandanti\b', 'komandant'), (r'^zamenici komandanta', 'zamenik komandanta'), (r'^zamenici komandira', 'zamenik komandira'),
          (r'^zamenici\b.*', 'zamenik komandanta'), (r'^politički komesari.*', 'politički komesar'),
          (r'^pomoćnici.*', 'pomoćnik političkog komesara'), (r'^načelnici.*', 'načelnik štaba'),
          (r'^intendanti.*', 'intendant'), (r'^referenti.*', 'referent saniteta'), (r'^obaveštajni.*', 'obaveštajni oficir'),
          (r'^omladinski.*', 'omladinski rukovodilac'), (r'^komandiri\b.*', 'komandir'), (r'^kulturno.*', 'kulturno-prosvetni referent'),
          (r'^politički\b.*', 'politički komesar'), (r'^koma[nv]d?iri\b.*', 'komandir'), (r'^obave\w*.*', 'obaveštajni oficir'),
          (r'^sanitetski.*', 'sanitetski referent'), (r'^ekonomi?\b.*', 'ekonom'), (r'^operativni.*', 'operativni oficir')]
BATTALION = {'battalion': ''}


def fold(t: str) -> str:
    t = (t or '').lower().replace('đ', 'dj')
    return re.sub(r'[^a-z]', '', ''.join(c for c in unicodedata.normalize('NFD', t) if not unicodedata.combining(c)))


def latin(t: str) -> str:
    t = cyrillic_to_latin(t).replace('J1', 'L').replace('Ј1', 'L')
    return re.sub(rf'\b([{U}])\s+(?=[{U}]{{2,}})', r'\1', t)                    # "V ASIĆ", "B OGOS AVLJEVIĆ"


def rows_of(page) -> list[list[dict]]:
    words = viewer_words(page)
    for w in words:
        w['text'] = latin(w['text'])
    rows: dict = {}
    for w in sorted(words, key=lambda w: w['top']):
        key = next((k for k in rows if abs(k - w['top']) < 4), w['top'])
        rows.setdefault(key, []).append(w)
    return [sorted(rows[k], key=lambda w: w['x0']) for k in sorted(rows)]


def names_in(text: str) -> list[str]:
    """'ALEKSIĆ Vitomir Đura BOŠKOVIĆ Veља Dragan' -> two names: each starts with a surname in capitals."""
    text = re.sub(rf'(?<=[{U}])\s+(?=[{U}]{{2,}}\b)', '', text)               # "BOGOS AVLJEVIĆ"
    starts = [m.start() for m in re.finditer(rf'(?<!\S)[{U}][{U}]+(?=\s|$|,)', text)]
    return [text[a:b].strip(' ,') for a, b in zip(starts, starts[1:] + [len(text)])]


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(1, len(pdf.pages) + 1):
            rows = rows_of(pdf.pages[pno - 1])
            if pno <= LINEUP_TO:
                body = False
                for row in rows:
                    text = ' '.join(w['text'] for w in row)
                    if re.search(r'Reč je o 377|A to su:', text):
                        body = True
                        continue
                    if not body or not re.match(rf'^[{U}]', text) or len(row) > 9:
                        continue
                    for name in names_in(text):
                        out.append({'page': pno, 'x': row[0]['x0'], 'y': row[0]['top'], 'text': f'§l§ {name}'})
            elif pno <= COMMAND_TO:
                out += command_page(pno, rows)
            else:
                for row in rows:
                    text = ' '.join(w['text'] for w in row)
                    if re.match(rf'^[{U}]{{2,}}', text) and not re.match(r'^(?:BOLNIČARKE|STROJ ŽENA)', text):
                        out.append({'page': pno, 'x': row[0]['x0'], 'y': row[0]['top'], 'text': f'§z§ {text}'})
    return out


def command_page(pno: int, rows: list[list[dict]]) -> list[dict]:
    """The officers of each staff and company: the duty labels stand in a column on the left, centred beside their
    names, so each name takes the label block whose middle is nearest within its section."""
    out, section, labels, names = [], '', [], []

    def flush():
        for n in names:
            duty = min(labels, key=lambda b: abs(b['y'] - n['y']))['text'] if labels else ''
            out.append(dict(n, text=f"§k§{duty}|{section}§ {n['text']}"))
        names.clear()
        labels.clear()

    for row in rows:
        text = ' '.join(w['text'] for w in row)
        if SECTION.match(text) and not re.search(r'\d{1,2}\.\s*\d', text):
            flush()
            section = text.strip()
            b = re.match(r'^ŠTAB (\w+) BATALJONA', section)
            if b:
                BATTALION['battalion'] = b.group(1).lower() + ' bataljona'
            elif re.match(r'^ŠTAB 9|^JEDINICE PRI', section):
                BATTALION['battalion'] = ''
            if section.lower().startswith('komanda') and BATTALION['battalion']:
                section = f"{section[:1].upper()}{section[1:].lower()} {BATTALION['battalion']}"
            continue
        if section.startswith('NIJE UTVRĐENO'):                              # "Komandiri: ANTONIJEVIĆ Branko, ..."
            names.append({'page': pno, 'x': row[0]['x0'], 'y': row[0]['top'], 'text': '§run§ ' + text})
            continue
        left = [w for w in row if w['x0'] < 110]
        rest = [w for w in row if w['x0'] >= 110]
        if left:
            t = ' '.join(w['text'] for w in left)
            if t[:1].isupper() or not labels:
                labels.append({'y': left[0]['top'], 'text': t, 'n': 1})
            else:
                b = labels[-1]
                b['y'] = (b['y'] * b['n'] + left[0]['top']) / (b['n'] + 1)
                b['n'] += 1
                b['text'] += ' ' + t
        rt = ' '.join(w['text'] for w in rest)
        if re.match(rf'^[{U}]{{2,}}', rt):
            names.append({'page': pno, 'x': rest[0]['x0'], 'y': rest[0]['top'], 'text': rt})
        elif names and re.match(r'^[\d.\s-]+$', rt):                         # dates on a line of their own
            near = min(names, key=lambda n: abs(n['y'] - row[0]['top']))
            near['text'] += ' ' + rt
    flush()
    return out


def split_name(text: str) -> tuple[str, str, list[str]]:
    """'KECMAN Jovan Čeda 22.5.44.-15.5.45.' -> ('Kecman', 'Jovan', ['zvani Čeda', '22.5.44.-15.5.45.'])"""
    dates = re.search(r'\s[-\d][\d.\s-]*$', text)
    tail = dates.group().strip() if dates else ''
    text = text[:dates.start()] if dates else text
    words = text.split()
    last = title_case(words[0]) if words else ''
    given = words[1] if len(words) > 1 else ''
    notes = ['zvani ' + ' '.join(words[2:])] if len(words) > 2 else []
    return last, given, notes + ([tail] if tail else [])


def parse_entry(text: str) -> dict:
    kind = text[1]
    if text.startswith('§l§'):
        last, given, notes = split_name(text[4:].strip())
        rec = _record(last, given, '', '; '.join(['u stroju brigade u Rečici 11. marta 1944'] + notes))
    elif text.startswith('§z§'):
        t = text[4:].strip()
        m = re.match(rf'^([{U}][{U}\-]+)\s+(?:(?:ud\.|udata)\s+)?([{U}][{L}]+(?:-[{U}][{L}]+)?\s+)?(?:\(([^)]*)\)\s*)?(.*)$', t)
        if not m:
            return {}
        words = m.group(4).split()
        notes = []
        if m.group(2):
            notes.append(f'udata {m.group(2).strip()}')
        if len(words) > 1:
            notes.append('zvana ' + ' '.join(words[1:]))
        rec = _record(title_case(m.group(1)), words[0] if words else '', (m.group(3) or '').strip(' .'),
                      '; '.join(['bolničarka ili borac u stroju žena brigade'] + notes))
        rec['fathers_name'] = (m.group(3) or '').strip(' .') if m.group(3) and len(m.group(3).strip(' .')) > 2 else ''
    else:
        m = re.match(r'^§k§([^|]*)\|([^§]*)§\s*(.*)$', text, re.S)
        duty, section, rest = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if rest.startswith('§run§'):
            return {'_run': rest[6:], '_section': section}
        last, given, notes = split_name(rest)
        where = section[:1] + section[1:].lower() if section.isupper() else section
        duty = duty.lower()
        for pat, one in DUTIES:
            duty = re.sub(pat, one, duty, count=1)
        rec = _record(last, given, '', '; '.join([f'{duty} ({where})' if where else duty] + notes))
    rec['_merge'] = True
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    """One record per man: the line-up first, then his duties and the women's list fold into it."""
    out, seen = [], {}
    for s in soldiers:
        s.pop('_merge', None)
        key = (fold(s['last_name']), fold(s['first_name']))
        if key in seen and s['first_name']:
            first = seen[key]
            have = first['additional_info'].split('; ')
            new = [x for x in s['additional_info'].split('; ') if x and x not in have]
            if new:
                first['additional_info'] = '; '.join(have + new)
            if s.get('fathers_name') and not first.get('fathers_name'):
                first['fathers_name'] = s['fathers_name']
            continue
        seen[key] = s
        out.append(s)
    return out


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/9-srpska.pdf',
        brigade_code=165,
        output_path='website/public/9-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[lkz]§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
