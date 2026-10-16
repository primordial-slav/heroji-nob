"""
Parser: 6. Krajiška NOU brigada (brigade code 13) — its war cadre, a third book.

Source: "Šesta krajiška NOU brigada — ratna sjećanja", part IV (znaci.org 00001/147_4.pdf), "Spisak ratnog kadra
        Šeste krajiške NOU brigade 1942—1943." (book pp. 739-745)  →  website/public/pdfs/6-krajiska-kadar.pdf
        (PDF pp. 28-34 of the part; the page with the title lost it when znaci re-typeset the book).
Cyrillic, two columns, a name a line under a bold heading for each duty, from the brigade's commanders down to the
company medics and "Ostali kadar"; a heading's list runs on into the next column and page:
    Команданти Бригаде:            Интенданти:
    Богуновић Урош „Роца"          Вулин Коста
No fathers, no years: a man is his name and nickname, and one name under several duties is one man (who rose from
company to battalion), the same name twice under one duty two men. znaci re-typeset the book from its OCR in a font
without ђ, as the survivors' list after it (the unit's second book): Ђ is Б and ђ is ћ (Буро = Đuro, Борћо = Đorđo,
Анћелка = Anđelka), Ћ is Н or И (Носић = Ćosić, Иургуз = Ćurguz); each duty's names are in alphabetical order,
which tells the letter, and the corpus tells the rest. Other slips are read from the page (`WORDS`).
The book's list of the fallen is the unit's first book (IDs from 1), the survivors the second (10001); these get
IDs from 20001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, cyrillic_to_latin, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/6-krajiska-kadar.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_147_4.pdf'   # znaci.org 00001/147_4.pdf
FIRST_PAGE, LAST_PAGE = 28, 34
TITLE = 'Spisak ratnog kadra Šeste krajiške NOU brigade 1942—1943'
SPLIT = 250                                                                  # the gutter, in viewer x
LINES: dict = {}                                                             # (page, y, x) -> the line's box


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def read_lines(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """Each column's lines top to bottom, left column first; a line is bold where all its words are."""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages[start_page - 1:end_page], start_page):
            for left in (True, False):
                rows: list = []
                for w in sorted(viewer_words(page, extra_attrs=['fontname']), key=lambda w: (w['top'], w['x0'])):
                    if (w['x0'] < SPLIT) != left:
                        continue
                    row = next((r for r in rows if abs(r[0]['top'] - w['top']) <= 3), None)
                    if row is None:
                        rows.append([w])
                    else:
                        row.append(w)
                for r in sorted(rows, key=lambda r: r[0]['top']):
                    r.sort(key=lambda w: w['x0'])
                    ln = {'text': ' '.join(w['text'] for w in r), 'x': round(r[0]['x0'], 1),
                          'y': round(min(w['top'] for w in r), 1), 'page': n,
                          'bold': all('Bold' in w['fontname'] for w in r)}
                    LINES[(n, ln['y'], ln['x'])] = (ln['x'], ln['y'], round(max(w['x1'] for w in r), 1),
                                           round(max(w['bottom'] for w in r), 1))
                    out.append(ln)
    return out


DUTY = {'d': ''}
# the duties' headings in the list's order; the text layer garbles some ("Zal1jenici", "Iiteidanti", "Četie
# boliičarke") and sets two in the body's font ("Komesari četa", "Politički delegati"), so a line is a heading
# by its words, not its font
HEADINGS = ['Komandanti Brigade', 'Komesari Brigade', 'Zamjenici komandanta Brigade', 'Zamjenici komesara Brigade',
            'Načelnici štaba Brigade', 'Obavještajni oficiri', 'Oficiri OZN-e', 'Omladinski rukovodioci', 'Intendanti',
            'Referenti saniteta', 'Članovi Politodjela', 'Sekretari Štaba', 'Komandanti bataljona',
            'Zamjenici komandanta bataljona', 'Komesari bataljona', 'Zamjenici komesara bataljona',
            'Omladinski rukovodioci bataljona', 'Obavještajni oficiri bataljona', 'Intendanti bataljona',
            'Referenti saniteta bataljona', 'Sekretari štabova bataljona', 'Komandiri četa', 'Zamjenici komandira četa',
            'Komesari četa', 'Zamjenici komesara četa', 'Komandiri vodova', 'Politički delegati', 'Četne bolničarke',
            'Ostali kadar']


def heading(t: str) -> str:
    from difflib import SequenceMatcher
    t = t.rstrip(': ')
    best = max(HEADINGS, key=lambda h: SequenceMatcher(None, t.lower(), h.lower()).ratio())
    return best if SequenceMatcher(None, t.lower(), best.lower()).ratio() >= 0.8 else ''


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        t = ln['text'].strip()
        h = heading(t)
        if h:
            DUTY['d'] = h
        if h or re.fullmatch(r'\d+\s*\.?', t):                               # a heading, a page number ("742.", "744 .")
            ln['drop'] = True
        else:
            ln['text'] = f"§§{DUTY['d']}|{t}"


def keep(ln: dict) -> bool:
    return not ln.get('drop')


# the text layer's slips, read from the list's order and the unit's other books (in Latin, before the name is split)
WORDS = [("ŠolC'", 'Šolc'), ('Šušnics1(', 'Šušnica'), ('Bandi ćBogdan', 'Bandić Bogdan'), ('1pubin', 'Tubin'),
         ('Adiamović', 'Adamović'), ('Agbama', 'Agbaba'), ("Stevo'", 'Stevo'), ('Pegar', 'Petar'), ('Dušai', 'Dušan'),
         ('Sgevo', 'Stevo'), ('Sgevan', 'Stevan'), ('Kavačević', 'Kovačević'), ('Spaeo', 'Spaso'),
         ('Koluncija', 'Kolundžija'), ('Koluddžić', 'Kolundžija'), ('Kornca', 'Korica'), ('Marjanov Rade', 'Marjanović Rade'),
         ('Ilića Milan', 'Ilić Milan'), ('Kurića Mićo', 'Kuridža Mićo'), ('Vranjeig', 'Vranješ'), ('Milovap', 'Milovan'),
         ('Milap', 'Milan'), ('Šniro', 'Špiro'), ('Sovijb', 'Sovilj'), ('Vuslidžić', 'Busulhodžić'),
         ('Badenković', 'Radenković'), ('Nurnuz', 'Ćurguz'), ('Joe-O', 'Jovo'), ('Milinković- Persa', 'Milinković Persa'),
         ('NeMilinović—Kotur', 'Milinović-Kotur'), ('Bukanov', 'Đukanov'), ('Aićelka', 'Anđelka'), ('Anćelka', 'Anđelka')]
# the font has no ђ: ћ inside a name is ђ where the corpus knows only that (Borćo = Đorđo, Kalućerović = Kaluđerović)
ALPHABET = ['A', 'B', 'V', 'G', 'D', 'Đ', 'E', 'Ž', 'Z', 'I', 'J', 'K', 'L', 'Lj', 'M', 'N', 'Nj', 'O', 'P', 'R', 'S',
            'T', 'Ć', 'U', 'F', 'H', 'C', 'Č', 'Š']                       # Džakula stands among the D names
WOMEN = {'Referenti saniteta', 'Referenti saniteta bataljona', 'Četne bolničarke'}


def parse(text: str) -> dict:
    duty, name = text[2:].split('|', 1)
    for a, b in WORDS:
        name = name.replace(a, b)
    nick = ''
    m = re.search(r'\s*[„"]\s*([^"“”]+?)\s*["“”\']\s*$', name)
    if m:
        nick, name = m.group(1), name[:m.start()]
    last, _, given = name.strip().partition(' ')
    married = ''
    if last == 'Bajić' and given.endswith(' Maran'):                        # "Bajić Jovanka Maran"
        given, married = given[:-6], 'Maran'
    rec = _record(last, given.strip(), '', '')
    rec['_duty'], rec['_nick'], rec['_married'] = duty, nick, married
    return rec


def letter(name: str) -> int:
    for i in sorted(range(len(ALPHABET)), key=lambda i: -len(ALPHABET[i])):
        if name.startswith(ALPHABET[i]):
            return i
    return -1


def corpus() -> tuple:
    import glob
    import json
    from collections import Counter
    unit, given, last = Counter(), Counter(), Counter()
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            if s['soldier_id'].startswith('001302'):
                continue
            given[s['first_name']] += 1
            if f.endswith('6-krajiska-soldiers.json'):
                unit[(s['last_name'], s['first_name'])] += 1
                last[s['last_name']] += 1
    return unit, given, last


def read_back(soldiers: list[dict]) -> None:
    """Đ for Б and Ć for Н, И or К where the list's order puts them; ђ for ћ where the corpus knows only that."""
    unit, given, last = corpus()
    by_duty: dict = {}
    for s in soldiers:
        by_duty.setdefault(s['_duty'], []).append(s)
    for posts in by_duty.values():
        for i, s in enumerate(posts):
            ln, gv = s['last_name'], s['first_name']
            # how far the duty's alphabetical list has come, by the names before that can't be misread letters
            reached = max([letter(p['last_name']) for p in posts[:i] if p['last_name'][:1] not in 'BNIK'] or [-1])
            if (ln, gv) not in unit:
                if ln[:1] == 'B' and reached >= ALPHABET.index('D'):
                    ln = 'Đ' + ln[1:]
                elif ln[:1] in 'NIK' and reached >= ALPHABET.index('T'):
                    ln = 'Ć' + ln[1:]
                inner = re.sub('ć(?!$)', 'đ', ln[:-2]) + ln[-2:]           # not the -ić at the end
                if inner != ln and not last[ln] and last[inner]:
                    ln = inner
            if (ln, gv) not in unit:
                for g in (('Đ' + gv[1:]) if gv[:1] == 'B' else gv, gv):
                    for h in {g, re.sub('ć(?!$)', 'đ', g)}:
                        if (ln, h) in unit or (given[h] > 3 * given[gv] and given[h] >= 5):
                            gv = h
                            break
                    else:
                        continue
                    break
            s['last_name'], s['first_name'] = ln, gv


def fold(s: dict) -> tuple:
    g = s['first_name']
    if s['_duty'] not in WOMEN:
        g = re.sub(r'a$', 'o', g)                                            # Sveta = Sveto, Laza = Lazo
    return s['last_name'], g, s['_nick']


def men(soldiers: list[dict]) -> list[dict]:
    """One record a man: his posts in the list's order; the same name twice under one duty is two men."""
    read_back(soldiers)
    out, seen = [], {}
    for s in soldiers:
        key, n = fold(s), 0
        while (key, n) in seen and s['_duty'] in seen[(key, n)]['_duties']:
            n += 1
        man = seen.get((key, n))
        if man is None:
            man = seen[(key, n)] = s
            s['_duties'], s['_rects'] = [], []
            out.append(s)
        man['_duties'].append(s['_duty'])
        box = LINES[(s['pdf_page'], s['pdf_y'], s['pdf_x'])]
        if s['pdf_page'] == man['pdf_page']:
            man['_rects'].append(list(box))
    for s in out:
        notes = [f"zvani {s['_nick']}"] if s['_nick'] else []
        notes += [f"({s['_married']})"] if s['_married'] else []
        s['additional_info'] = '; '.join(notes + [f"{TITLE}: {'; '.join(s['_duties'])}"])
        x0, y0, x1, y1 = s['_rects'][0]
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = x0, y0, x1, y1
        if len(s['_rects']) > 1:
            s['pdf_rects'] = s['_rects']
        s['full_name'] = f"{s['last_name']} {s['first_name']}".strip()
        for k in ('_duty', '_nick', '_married', '_duties', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=13, output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/6-krajiska-soldiers.json',
               extract_fn=read_lines, script='cyrillic', entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse,
               prepare_fn=prepare, line_filter=keep, post_fn=men, id_start=20001, keep_other_sources=True)
