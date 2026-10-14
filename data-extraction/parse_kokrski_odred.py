"""
Parser: Kokrški odred (brigade code 171), the second Kokrški odred, 27 August 1944 - May 1945.

Source: Ivan Jan, "Kokrški odred - narodnoosvobodilni boj pod Karavankami" III (Knjižnica NOV in POS 26/4; znaci.org
        00003/1052.pdf) →  website/public/pdfs/kokrski-odred.pdf (book pp. 453-478): "Spisek borcev Drugega kokrškega
        odreda", the author's reconstruction from the odred's own rosters and orders, not in alphabetical order, one
        column, each entry hanging:
            štab odreda: / komandant: / Prezelj Janko-Stane - od 27. 8. 1944 do 12. 5. 1945
            Bernik Stane, 1923, komandir                 (from the štabna zaščita on, the year of birth)
            Cengle Ivan-Kroparček (padel)
        under headings for the staffs, the intelligence centre and points, the courier stations, the hospital and
        the ambulances, the workshops, the battalions' companies by period and the Jurišni bataljon; a few
        paragraphs run the names on ("Porenta Ivo-Vojko, Korinšek Dušan, Pirih Lojze-Tone"). The book warns that men
        transferred or promoted appear more than once; each entry is kept, as printed. The corrections the book
        prints at its end ("Popravki k 3. knjigi", pp. 573-574) are applied (`ERRATA`). The facsimile of the
        1. bataljon's cadre of 15 February 1945 after the list (pp. 479-484) has no readable text and is not read.
The pdfplumber text loses the soft hyphens at line ends; they come back from PyMuPDF's lines.
"""
import re

import fitz
import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_offset

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FIRST_BOOK_PAGE = 453
NAME = rf"(?:Dr\.\s+)?[{U}][{L}]+(?:-[{U}][{L}]+)?\s+[{U}][{L}]+(?:-[{U}{L}][{L}]+)?"
BOXES: dict = {}
# "Popravki k 3. knjigi" (book pp. 573-574), by book page: the printed text → the corrected
ERRATA = {
    465: [('Bagatelj Milan', 'Batagelj Milan')],
    466: [('Šilar Vinko', 'Šlibar Vinko'), ('Bertoncelj Pavel, 1926', 'Bertoncelj Pavel, 1916')],
    471: [('Kink Ivan', 'King Ivan')],
    473: [('Eberl Avgust', 'Eberle Avgust'), ('Gros Franc, 1916, obveščevalec', 'Gros Franc, 1916, obveščevalec (ubežnik)')],
    475: [('Černivec', 'Črnivec')],
    477: [('Avsenik Janez, polikomisar', 'Avsenik Janez, politkomisar'), ('Kink Ivan', 'King Ivan')],
    478: [('Klajndinst Pavle', 'Klajndinst Pavel'), ('Košiu Pavel', 'Košir Pavel')],
}
# the text layer's slips in names, read from the page: the printed text → the page's
SCAN = [('3učar', 'Bučar'), ('?ajk Miha', 'Pajk Miha'), ('l\\Iali', 'Mali'), ('J\\fakarov, Mirko', 'Makarov Mirko'),
        ('Markelj, Janko', 'Markelj Janko'), ('Korenčan ,Dušan', 'Korenčan Dušan'), ('Jurij-:Eluko', 'Jurij-Duko'),
        ('Bratkovič Peter-Zvcnko', 'Bratkovič Peter-Zvonko'), ('Mitja Valenčič-Sonc', 'Valenčič Mitja-Sonc'),
        ('Zirovnik', 'Žirovnik'), ('194,\'i', '1945'), ('Ziger Ljudevit', 'Žiger Ljudevit'), ('Stane žagar', 'Žagar Stane'),
        ('lVI', 'M'), ('Marinčl.č', 'Marinčič'), ('Konrad.JRobi', 'Konrad-Robi'), ('Jurišna ceta', 'Jurišna četa')]


def heading(t: str) -> bool:
    return bool(t.endswith(':') or re.search(r':\s*\(', t)
                or re.fullmatch(rf'[{U}\s().0-9\'-]+', t) and re.search(rf'[{U}]{{3}}', t)        # not "1944)"
                or re.fullmatch(r'(?:[»>]+[^«]*«|\(Seznam [^)]*\)|\d{1,2}\. \d{1,2}\. 19\d\d|[lI1-9]\. četa)', t)
                or re.fullmatch(rf'[{U}][{L}]+(?:-[{L}]+)? 19\d\d(?:-[{L}]+ 19\d\d)?', t)          # "Januar-marec 1945"
                or re.fullmatch(rf'(?:Poveljstvo|Jurišni bataljon|Ostalo moštvo|September|Desetina za zvezo)\b.*', t))


def _fitz_hyphens(pdf_path: str) -> dict:
    """(page, rounded y) of each line PyMuPDF reads with a hyphen at its end."""
    out = {}
    for i, page in enumerate(fitz.open(pdf_path), 1):
        for b in page.get_text('dict')['blocks']:
            for ln in b.get('lines', []):
                t = ''.join(s['text'] for s in ln['spans']).rstrip()
                if t.endswith(('-', '­')) and not t.endswith(' -'):
                    out.setdefault(i, []).append((ln['bbox'][1], t.rstrip('-­').strip()[-6:]))
    return out


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    hyph = _fitz_hyphens(pdf_path)
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn in range(start, min(end or len(pdf.pages), len(pdf.pages)) + 1):
            page = pdf.pages[pn - 1]
            dx, dy = viewer_offset(page)
            book = FIRST_BOOK_PAGE + pn - 1
            top = mid = role = ''
            entry_x, after_heading, prev, prose, last_caps = None, True, '', False, False
            if out:
                top, mid, role = out[-1]['ctx']
            for ln in page.extract_text_lines(strip=True, return_chars=False):
                t = ln['text'].strip().replace('­', '')
                if not t or re.fullmatch(r'\d{3}|30 Kokrški odred III\.', t):
                    continue
                if any(abs(y - ln['top']) < 3 and t.endswith(end) for y, end in hyph.get(pn, [])) and not t.endswith('-'):
                    t += '-'
                for a, b in SCAN + ERRATA.get(book, []):
                    t = t.replace(a, b)
                x = ln['x0'] - dx
                t = re.sub(r'^([šžčćđ])(?=[a-zšžčćđ]+ [A-ZČŠŽ])', lambda m: m.group(1).upper(), t)   # "šebat Ignac"
                t = re.sub(r'^([a-z])(?=[a-zšžčćđ]+ [A-ZČŠŽ][a-zčšž]+, 1[89]\d\d)', lambda m: m.group(1).upper(), t)   # "frnik Viktor, 1910"
                t = re.sub(rf'^({NAME})\.\s+(1[89]\d\d)\.?', r'\1, \2,', t).replace(',,', ',')   # "Jože-Tiger. 1926. desetar"
                t = re.sub(rf'^([{U}][{L}]+), (?=[{U}][{L}]+\b)', r'\1 ', t)              # "Batagelj, Milan, obveščevalec"
                t = re.sub(rf' ,(?=[{U}])', ' ', t)                                     # "Baloh ,Ignac"
                flush = entry_x is None or x < entry_x + 4
                if prose and (t[:1].islower() or not flush):
                    continue                                                # the author's sentences between the lists
                prose = False
                if t.startswith('* ') or (out and out[-1].get('note') and out[-1]['page'] == pn):   # the editor's note
                    if t.startswith('* '):
                        out.append({'note': True, 'ctx': (top, mid, role), 'text': '', 'x': x, 'y': 0, 'page': pn})
                    continue
                t = re.sub(rf'\bl\. (?=[{U}]{{3}}|bataljon|čet)', '1. ', t)        # "SPISEK MOŠTVA l. BATALJONA"
                t = re.sub(r'(?<=\d\. )l\.', '1.', t)                              # "4. l. 1945"
                if t == 'Delavnice' or heading(t) and not re.match(NAME + r'\s*[,(-]', t):
                    h = t.rstrip(':').strip()
                    caps = bool(re.fullmatch(rf'[{U}\s().0-9\'-]+', h))
                    if caps and last_caps:                                   # a title on two lines
                        top = top + ' ' + h.lower()
                    elif caps and len(h) > 12:
                        top, mid, role = h.rstrip("'").capitalize().replace('drugega kokrškega', 'Drugega kokrškega').replace('ceta', 'četa'), '', ''
                    elif re.match(r'^(?:komandant|politkomisar|poli tkomisar|namestnik|načelnik)', h):
                        role = h.replace('politkomisarj a', 'politkomisarja').replace('poli tkomisar', 'politkomisar')
                    else:
                        period = r'(?:\d{1,2}\. \d|\(Seznam|September|[A-Z][a-z]+-[a-z]+ 19)'
                        if mid and re.match(period, h) and not re.match(period, mid):   # a period replaces the one before
                            mid = re.sub(r', ' + period + r'.*$', '', mid) + ', ' + h
                        elif re.match(period, h):
                            mid = h
                        elif re.match(r'^[lI1-9]\. (?:četa|bataljon)|^[»>]', h) and mid \
                                and not re.match(r'^[lI1-9]\. (?:četa|bataljon)|^[»>]', mid):
                            mid = re.sub(r', (?:[lI1-9]\. (?:četa|bataljon)|[»>].*)$', '', mid) + ', ' + re.sub(r'^l\. ', '1. ', h).replace('>>', '»')
                        elif re.match(r'^[lI1-9]\. (?:četa|bataljon)|^[»>]', h):
                            mid = re.sub(r'^l\. ', '1. ', h).replace('>>', '»')
                        else:
                            mid = h
                        role = ''
                    after_heading, entry_x, last_caps = True, None, caps
                    out.append({'heading': True, 'ctx': (top, mid, role), 'text': '', 'x': x, 'y': 0, 'page': pn})
                    continue
                last_caps = False
                named = bool(re.match(NAME + r'(?:\s*$|\s*[,(]|\s+-|\s+in\s|\s+od\s|\s+\d)', t))
                starts = named and not (prev.endswith(',') or prev.endswith('-') and not prev.endswith(' -')) \
                    and (after_heading or entry_x is None or x < entry_x + 8)
                loose = bool(re.match(rf'^(?:Dr\.\s+)?[{U}][{L}.]+(?:\s+[{U}]|,|$)', t))   # "Erman Ljudmila-lVIilica", "Georg,"
                if not named and loose and flush and not prev.endswith(','):
                    named = starts = True
                if not named and flush and t[:1].isupper() and not re.match(r'^\d', t) and not after_heading:
                    if len(t) <= 55 and not t.endswith('.') and ',' not in t:   # "Radio ekipa »Stol 33«", "Osebje tehnike"
                        mid = t.replace('((', '«')
                        role = ''
                        after_heading, entry_x = True, None
                        out.append({'heading': True, 'ctx': (top, mid, role), 'text': '', 'x': x, 'y': 0, 'page': pn})
                    else:
                        prose = True
                    continue
                if starts:
                    entry_x, after_heading = x, False
                prev = t
                ctx = (top, mid, role)
                out.append({'text': ('§x§' + '|'.join(ctx) + '§ ' if starts else '') + t, 'x': round(x, 1),
                            'y': round(ln['top'] - dy, 1), 'page': pn, 'ctx': ctx,
                            'x1': round(ln['x1'] - dx, 1), 'y1': round(ln['bottom'] - dy, 1)})
    lines = [l for l in out if not l.get('heading') and not l.get('note')]
    cur = None
    for l in lines:                                                         # each entry's box: its lines
        if l['text'].startswith('§x§'):
            cur = (l['page'], l['y'], l['x'])
            BOXES[cur] = {'pdf_x_end': l['x1'], 'pdf_y_end': l['y1'] + 1.5}
        elif cur and cur[0] == l['page']:
            BOXES[cur]['pdf_x_end'] = max(BOXES[cur]['pdf_x_end'], l['x1'])
            BOXES[cur]['pdf_y_end'] = l['y1'] + 1.5
    return lines


def split_names(text: str) -> list[str]:
    """A paragraph that runs the names on: "Porenta Ivo-Vojko, Korinšek Dušan, Pirih Lojze-Tone"."""
    text = text.replace('. Nekaj časa administratorka tudi Regovc', ', Regovc')
    parts = re.split(rf',\s+(?={NAME}(?:\s*$|\s*[,(]))|\s+in\s+(?={NAME}(?:\s*$|\s*[,(]))', text)
    if len(parts) > 1 and re.fullmatch(r'\s*desetarji\s*', parts[-1].split(',')[-1]):
        parts = [p.replace(', desetarji', '') + ', desetar' for p in parts]
    return parts


def parse_one(text: str, ctx: str, role: str = '') -> dict:
    text = re.sub(r'\s+', ' ', text).strip(' ,')
    for a, b in (('koman dant', 'komandant'), ('sre dine', 'sredine'), ('bata ljon', 'bataljon'), ('Tri-· glav', 'Triglav'),
                 ('»Triglav"', '»Triglav«'), ('de• cembra', 'decembra'), ('de•-cembra', 'decembra')):
        text = text.replace(a, b)                                           # words the line end broke
    text = re.split(r'\s+(?:Obstajala je le|Se drugi trije|Iz bataljona so bili|z nekaj tovariši minerji\. Vsi ti|'
                    r'V 1\. bataljon je bilo)\b', text)[0]                  # the author's sentences between the lists
    m = re.match(rf'^(Dr\.\s+)?([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+([{U}][{L}]+)(?:-([{U}{L}][{L}]+))?\s*(.*)$', text)
    if not m:
        one = re.match(rf'^([{U}][{L}]+)(?:,\s*(.*))?$', text)          # "Georg, nemški dezerter, kuhar", "Šinkovec"
        if not one:
            return {}
        rec = _record(one.group(1), '', '', '; '.join(x for x in (one.group(2), ctx) if x))
        rec['birth_year'] = ''
        return rec
    last, given, alias, rest = m.group(2), m.group(3), m.group(4), m.group(5).strip(' ,')
    notes = ([f'zvani {alias[0].upper() + alias[1:]}'] if alias else []) + (['dr.'] if m.group(1) else [])
    rest = re.sub(r'^-\s*', '', rest)
    year = re.match(r'^(1[89]\d\d)\b[.,]?\s*', rest)
    info = '; '.join(notes + ([rest] if rest else []) + ([ctx] if ctx else []))
    rec = _record(last, given, '', info)
    rec['birth_year'] = year.group(1) if year else ''
    fell = re.search(r'\(padel(?:\s+(\d{1,2})\.\s*(\d{1,2})\.\s*(19\d\d))?\)|ko je padel', rest)
    if fell:
        rec['death_type'] = 'poginuo'
        if fell.group(1):
            rec['death_date'] = f'{int(fell.group(1))}. {int(fell.group(2))}. {fell.group(3)}'
        else:
            d = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(19\d\d), ko je padel', rest)
            if d:
                rec['death_date'] = f'{int(d.group(1))}. {int(d.group(2))}. {d.group(3)}'
    elif re.search(r'\(ujet\)', rest):
        rec['death_type'] = 'zarobljen'
    elif re.search(r'\(umrl', rest):                                        # "(umrl 1978)", "(umrl po vojni)"
        rec['death_type'] = 'umro'
    duty = re.search(r'\b(komandant|komandir|politkomisar|namestnik \w+|pomočnik \w+|vodnik|desetar|politdelegat|'
                     r'intendant|bolničar(?:ka)?|kurir|obveščeval(?:ec|ka)|ekonom|kuhar(?:ica)?|orožar|administrator(?:ka)?|'
                     r'šifrant|mesar|vodja)\b', rest)
    if duty:
        rec['rank'] = duty.group(1)
    elif role:
        rec['rank'] = re.sub(r'^(komandant|politkomisar|namestnik|načelnik štaba).*', r'\1', role)
    bat = re.search(r'([123])\. bataljon', ctx) or re.search(r'(Jurišn\w+ (?:bataljon|četa))', ctx)
    cet = re.search(r'\b([12])\. četa\b', ctx)
    if bat:
        b = f'{bat.group(1)}. bataljon' if bat.group(1).isdigit() else bat.group(1).replace('Jurišna četa', 'Jurišna četa 2. bataljona')
        rec['unit_detail'] = ', '.join(x for x in ((f'{cet.group(1)}. četa' if cet else ''), b) if x)
    elif re.match(r'(?i)štab odreda|širši štab', ctx):
        rec['unit_detail'] = 'štab odreda'
    return rec


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([^§]*)§\s*(.*)$', text, re.S)
    top, mid, role = (m.group(1).split('|') + ['', '', ''])[:3]
    ctx = ', '.join(x for x in (mid, role) if x)
    if top and not re.match(r'(?i)štab drugega|spisek borcev', top):
        ctx = ', '.join(x for x in (top, ctx) if x)
    parts = split_names(m.group(2))
    recs = [r for r in (parse_one(p, ctx, role) for p in parts) if r]
    if not recs:
        return {}
    first = recs[0]
    if len(recs) > 1:
        first['_more'] = recs[1:]
    return first


def post(soldiers: list[dict]) -> list[dict]:
    out = []
    for s in soldiers:
        more = s.pop('_more', [])
        box = BOXES.get((s.get('pdf_page'), s.get('pdf_y'), s.get('pdf_x')))
        if box:
            s.update(box)
        out.append(s)
        for r in more:                                                      # the names run on in the paragraph
            r.update({k: s[k] for k in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_file', 'pdf_x_end', 'pdf_y_end') if k in s})
            out.append(r)
    return out


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/kokrski-odred.pdf',
        brigade_code=171,
        output_path='website/public/kokrski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
