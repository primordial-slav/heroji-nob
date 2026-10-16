"""
Parser: 1. dalmatinska proleterska brigada (brigade code 36) — its officers on the day it was formed, a sixth list.

Source: Mirko Novović, Stevan Petković, the brigade's monograph (znaci.org 00001/108, the chapter 108_3.pdf, its PDF
        pp. 4-7, book pp. 55-58)  →  website/public/pdfs/1-dalmatinska-formiranje.pdf: "Starješinski sastav 1.
        dalmatinske NOU brigade na dan formiranja 6. IX 1942.", the officers of the brigade staff, the Politički
        odjel, the music, the command platoon and the four battalions' staffs and companies, run on, the duty, the
        name, the year of birth, nationality and trade:
    Komandant Petar Cetković Pero, rođen 1907. godine, Crnogorac, oficir bivše jugoslovenske vojske. Politički ...
    1. četa: Komandir Petar Bjelobrk, rođen 1915. godine, Srbin, radnik. Politički komesar Paško Pilić, ...
A third word of the name is what he was called ("zvani Pero;"). The photographs' captions (smaller type) are left
out. znaci re-typeset the book from its OCR, so the page shows its slips ("Cetković", "Bilie", "Zunković"); the names
take back the carons the brigade's other lists print (`parse_1_dalmatinska_komandni_sastav.spelled`). The other
lists are the unit's first (IDs from 1), the monograph's lists (10001), the women (20001), the staff changes (30001)
and Borci Sutjeske (100001); these get IDs from 40001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

import parse_1_dalmatinska_komandni_sastav as ks
import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/1-dalmatinska-formiranje.pdf'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_108_3.pdf'   # znaci.org 00001/108_3.pdf
FIRST_PAGE, LAST_PAGE = 4, 7
TITLE = 'Starješinski sastav 1. dalmatinske brigade na dan formiranja 6. IX 1942.'
SECTIONS = [(r'^STAB BRIGADE|^ŠTAB BRIGADE', 'Štab brigade', 'brigade'),
            (r'^Politi\S+ odjel brigade', 'Štab brigade', 'političkog odjela brigade'),
            (r'^Muzika brigade', 'Štab brigade', 'muzike brigade'),
            (r'^Komandni vod', 'Štab brigade', 'komandnog voda'),
            (r'^1\. BATALJON', '1. bataljon', '1. bataljona »Ante Jonić«'),
            (r'^2\. BATALJON', '2. bataljon', '2. bataljona »Bude Borjan«'),
            (r'^3\. BATALJON', '3. bataljon', '3. bataljona »Josip Jurčević«'),
            (r'^4\. BATALJON', '4. bataljon', '4. bataljona »Tadija Anušić«')]
DUTIES = ['Zamjenik političkog komesara', 'Zamjenik komandanta', 'Pomoćnik obavještajnog oficira', 'Obavještajni oficir',
          'Omladinski rukovodilac brigade', 'Omladinski rukovodilac', 'Brigadni barjaktar', 'Barjaktar',
          'Oficir pri štabu brigade', 'Oficir pri štabu', 'Rukovodilac političkog odjela', 'Clan političkog odjela',
          'Politički komesar', 'Komandant', 'Komandir voda', 'Komandir', 'Načelnik štaba', 'Intendant',
          'Referent saniteta']
DUTY = re.compile(r'(?:^|(?<=\s))(' + '|'.join(DUTIES) + r')\s')       # "... Hrvat, radnik Politički komesar ..."
# a name whose duty the print left out: "Ante Kitarović Bute, rođen 1917. godine" (the 2. bataljon's youth leader)
BARE = re.compile(r'(?<=\.\s)(?=[A-ZČĆŽŠĐ][a-zčćžšđ]+ [A-ZČĆŽŠĐ][a-zčćžšđ]+(?: [A-ZČĆŽŠĐ][a-zčćžšđ]+)?, rođen)')
NAME_FIXES = {'Peko Bogdan': 'Bogdan Peko', 'Bilie': 'Bilić', 'Sćekić': 'Šćekić', 'Cetković': 'Ćetković',
              'Kažimir': 'Kazimir', 'Tonči Paunović': 'Tonči Paunović'}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def stream_of(pdf) -> list[dict]:
    """The list's words in reading order, without the captions (in smaller type) and page numbers; each line's
    words tagged with the section heading it stands under."""
    out, on, section = [], False, None
    for n, page in enumerate(pdf.pages, 1):
        rows: list = []
        for w in sorted(viewer_words(page, extra_attrs=['size']), key=lambda w: (w['top'], w['x0'])):
            if rows and abs(w['top'] - rows[-1][0]['top']) <= 3:
                rows[-1].append(w)
            else:
                rows.append([w])
        for r in rows:
            r.sort(key=lambda w: w['x0'])
            text = ' '.join(w['text'] for w in r)
            if r[0]['size'] < 9.5 and re.search(r'[a-zčćžšđ]{2}', text):
                continue                                                     # a caption, in smaller type
            if text.startswith('NA DAN FORMIRANJA'):
                on = True
                continue
            if not on or re.fullmatch(r'\d\d|5«', text):
                continue
            sec = next((s for s in SECTIONS if re.match(s[0], text)), None)
            if sec:
                section = sec
                continue
            for w in r:
                out.append({**w, 'page': n, 'section': section})
    return out


def read_posts(pdf_path: str) -> None:
    with pdfplumber.open(pdf_path) as pdf:
        ws = stream_of(pdf)
    # the text of each section, and where each character came from
    by_section: list = []
    for w in ws:
        if not by_section or by_section[-1][0] is not w['section']:
            by_section.append([w['section'], '', []])
        sec = by_section[-1]
        if sec[1].endswith('-') and w['text'][:1].islower():                 # "ofi-" / "cir"
            sec[1] = sec[1][:-1]
            sec[2].pop()
        elif sec[1]:
            sec[1] += ' '
            sec[2].append(None)
        sec[1] += w['text']
        sec[2] += [w] * len(w['text'])
    for section, text, owner in by_section:
        company = ''
        cuts = sorted({m.start(1) for m in DUTY.finditer(text)} | {m.start() for m in BARE.finditer(text)}
                      | {m.start() for m in re.finditer(r'[/\d]\. četa:', text)})
        for a, b in zip(cuts, cuts[1:] + [len(text)]):
            chunk = text[a:b].strip()
            m = re.match(r'([/\d])\. četa:\s*', chunk)
            if m:
                company = f"{'1' if m.group(1) == '/' else m.group(1)}. četa"
                continue
            duty = next((d for d in DUTIES if chunk.startswith(d + ' ')), '')
            rest = chunk[len(duty):].strip()
            words = [w for w in owner[a:a + len(chunk)] if w]
            POSTS.append({'section': section, 'company': company, 'duty': duty, 'rest': rest,
                          'page': words[0]['page'], 'words': list({id(w): w for w in words}.values())})


def finish(p: dict) -> None:
    """'Petar Cetković Pero, rođen 1907. godine, Crnogorac, ...' -> Ćetković Petar, zvani Pero, and the bio."""
    rest = p['rest']
    for a, b in NAME_FIXES.items():
        rest = rest.replace(a, b)
    title = ''
    if rest.startswith('dr '):
        title, rest = 'dr', rest[3:]
    m = re.match(r'([A-ZČĆŽŠĐ][a-zčćžšđ]+(?: [A-ZČĆŽŠĐ][a-zčćžšđ]+)*)[.,]?\s*(.*)$', rest)
    names, bio = m.group(1).split(), m.group(2)
    if names[-1] == 'Hrvat':                                                 # "dr Orest Zunković, Hrvat, lekar"
        names, bio = names[:-1], 'Hrvat, ' + bio
    given, last, nick = names[0], names[1] if len(names) > 1 else '', ' '.join(names[2:])
    bio = re.sub(r'^rođen\b', 'rođen', bio.replace('roden', 'rođen')).rstrip('. ')
    sec = p['section']
    duty = p['duty'].replace('Clan', 'Član')
    duty = duty[:1].lower() + duty[1:]
    where = f"{p['company'][:-1]}e {sec[2]}" if p['company'] else sec[2]  # "3. čete 4. bataljona"
    if duty.endswith(('političkog odjela', 'voda')):                       # "rukovodilac političkog odjela", "komandir voda"
        duty = f"{duty} brigade" if 'odjela' in duty else 'komandir komandnog voda'
    elif duty and not duty.endswith(('brigade', 'barjaktar')) or duty == 'barjaktar':
        duty = f'{duty} {where}'
    elif not duty:                                                          # Kitarović, whose duty the print left out
        duty = where.replace('bataljona', 'bataljon')
    p.update(given=ks.spelled(given, 'first_name'), last=ks.spelled(last, 'last_name'), nick=nick, title=title,
             unit=f"{p['company']}, {sec[1]}" if p['company'] else sec[1], post=f'{duty}, {bio}' if bio else duty)
    y = re.search(r'rođen[a]? (1[89]\d\d)', bio)
    p['birth_year'] = y.group(1) if y else ''


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    k8.corpus()
    ks.load_unit()
    read_posts(pdf_path)
    for p in POSTS:
        finish(p)
    return [{'text': '§§post' + str(i), 'x': round(p['words'][0]['x0'], 1), 'y': round(p['words'][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    info = '; '.join(([p['title']] if p['title'] else []) + ([f"zvani {p['nick']}"] if p['nick'] else [])
                     + [f"{TITLE}: {p['post']}."])
    rec = _record(p['last'], p['given'], '', info)
    rec['birth_year'] = p['birth_year']
    rec['unit_detail'] = p['unit']
    rec['_post'] = int(text[6:])
    return rec


def boxes(soldiers: list[dict]) -> list[dict]:
    """A box around the post's words on each line, on its first page."""
    for s in soldiers:
        p = POSTS[s.pop('_post')]
        lines: list = []
        for w in p['words']:
            if w['page'] != p['page']:
                continue
            if lines and abs(lines[-1][0]['top'] - w['top']) <= 3:
                lines[-1].append(w)
            else:
                lines.append([w])
        r = [[round(min(w['x0'] for w in ln), 1), round(min(w['top'] for w in ln), 1),
              round(max(w['x1'] for w in ln), 1), round(max(w['bottom'] for w in ln), 1)] for ln in lines]
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
    return soldiers


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=36, output_path=sys.argv[1] if len(sys.argv) > 1 else ks.UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=boxes,
               id_start=40001, keep_other_sources=True)
