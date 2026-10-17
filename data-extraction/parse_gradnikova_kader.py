"""
Parser: Gradnikova brigada (brigade code 64) — its command and its narodni heroji, a second list.

Source: Stanko Petelin, "Gradnikova brigada" (Knjižnica NOV in POS, 2nd ed. 1983; znaci.org 00003/825.pdf, PDF and
        book pp. 791-799, before the roster on the site)  →  website/public/pdfs/gradnikova-kader.pdf:
        "Poveljstvo III. SNOUB Ivana Gradnika", the brigade's commanders, political commissars, their deputies and
        chiefs of staff, numbered under each duty with the days held, a footnote telling who fell:
    1. DANILO ŠOROVIČ (od 26. aprila 1943 do 3. novembra 1943)
        and "Narodni heroji Gradnikove brigade", a short biography of each beside his portrait:
    DRAGO FLIS-STRELA, je bil rojen leta 1921 v Blanci pri Krškem. ...
The part after the hyphen is what he was called ("zvani Strela;", as the roster writes it). A man in several posts, or
in a post and among the heroes, is one record with each; his box is around his name at his first post, a hero's around
his biography. The Serbs' -ić is set -ič, as in the book's roster (Šorovič, Marjanovič, Jovanovič); "MOCNIK" and
"VUKADINOVIC" lost their carons. The footnotes' deaths, and each
hero's birth and death, are set as fields (the biographies give the places in the locative). The roster is the unit's
first list (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/gradnikova-kader.pdf'
UNIT = 'website/public/gradnikova-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_825.pdf'   # znaci.org 00003/825.pdf
FIRST_PAGE, LAST_PAGE = 791, 799
COMMAND = 'Poveljstvo Gradnikove brigade'
HEROES = 'Narodni heroj Gradnikove brigade'   # the book's heading in the singular, which gives the medal
DUTIES = {'Komandanti': 'komandant', 'Politični komisarji': 'politični komisar',
          'Namestniki komandantov': 'namestnik komandanta', 'Namestniki političnih komisarjev': 'namestnik političnega komisarja',
          'Načelniki štaba': 'načelnik štaba'}
SURNAMES = {'Vukadinovic': 'Vukadinovič', 'Mocnik': 'Močnik'}
TEXT = {'Š ercer j evem': 'Šercerjevem', ' ie bil': ' je bil', 'ßa ': 'ga ', 'diverzantske^': 'diverzantske',
        'MOCNIK': 'MOČNIK', "marca'1945": 'marca 1945'}
# the footnotes (by the man's name) and the heroes' lives: (note, birth year, birthplace, death type, day, place)
FATES = {
    'Močnik Cveto': ('Padel je na dan ustanovitve brigade na Golobarju.', '1914', 'Ljubljana', 'poginuo', '26. 4. 1943', 'Golobar'),
    'Avsec Jože': ('Smrtno se je ponesrečil 8. februarja 1944 na Cerkljanskem vrhu.', '', '', 'umro', '8. 2. 1944',
                   'Cerkljanski vrh'),
    'Mihevc Jože': ('Padel je 20. junija 1944 na Jelovici.', '1922', 'Idrija', 'poginuo', '20. 6. 1944', 'Jelovica'),
    'Nemgar Franc': ('Padel je 2. maja 1945 na Opčinah pri Trstu.', '', '', 'poginuo', '2. 5. 1945', 'Opčine'),
    'Jovanovič Svetolik': ('Padel je 20. decembra 1944 v Dobravi pri Gorenji vasi.', '', '', 'poginuo', '20. 12. 1944',
                           'Dobrava pri Gorenji vasi'),
    'Braniselj Drago': ('Padel je 17. januarja 1944 na Vojskem.', '', '', 'poginuo', '17. 1. 1944', 'Vojsko'),
    'Vrhunec Oto': ('Padel je 5. aprila 1945 nad Selško dolino.', '', '', 'poginuo', '5. 4. 1945', 'Selška dolina'),
    'Flis Drago': ('', '1921', 'Blanca', '', '', ''),
    'Likar Ivan': ('', '1921', 'Log pod Mangartom', '', '', ''),
    'Maslo Drago': ('', '1912', 'Ostrožno Brdo', '', '', ''),
    'Munih Dušan': ('', '1924', 'Sela pri Volčah', 'poginuo', '10. 1. 1945', 'Boršt'),
    'Pokovec Franc': ('', '1921', 'Ljubljana', '', '', ''),
    'Škapin Mihaela': ('', '1922', 'Veliko Polje', 'poginuo', '15. 11. 1943', 'Žirovski vrh'),
    'Tavčar Franc': ('', '1920', 'Jarše', '', '', ''),
    'Učakar Janez': ('', '1918', 'Pristava pri Moravčah', '', '', ''),
}
POSTS: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for i in range(FIRST_PAGE - 1, LAST_PAGE):
        w.add_page(r.pages[i])
    with open(PDF, 'wb') as f:
        w.write(f)


def mended(text: str) -> str:
    text = re.sub(r'­\s+', '', text)                                # "od\xad šel": a word broken over lines
    text = re.sub(r'(?<=[a-zčšž])- (?=[a-zčšž])', '', text)
    for a, b in TEXT.items():
        text = text.replace(a, b)
    return re.sub(r'\s+', ' ', text).strip()


def person(caps: str) -> tuple[str, str, str]:
    """'DANILO ŠOROVIČ' -> (Šorović, Danilo, ''); 'OTO VRHUNEC-BLAŽ OSTROVRHAR' -> (Vrhunec, Oto, Blaž Ostrovrhar)"""
    name, _, nick = caps.title().partition('-')
    given, _, last = name.partition(' ')
    return SURNAMES.get(last, last), given, nick


def read_posts(pdf_path: str) -> None:
    duty, cur = '', None
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            for r in rows_of(viewer_words(page, extra_attrs=['size', 'fontname'])):
                text = ' '.join(w['text'] for w in r)
                size = max(w['size'] for w in r)
                if size < 7.4 or size > 11 or re.fullmatch(r'\d{3}', text):
                    continue                                             # footnotes, titles, page numbers
                if n <= 3:                                               # the command
                    if 'Italic' in r[0]['fontname']:
                        duty = DUTIES[text.rstrip(' :')]
                        continue
                    m = re.match(r'^(\d{1,2}) ?\. ([A-ZČĆŠŽĐ]{2}.+)$', text)     # not "10. februarja 1944)" run on
                    if m:
                        cur = {'kind': 'post', 'duty': duty, 'text': m.group(2), 'page': n, 'rows': [r]}
                        POSTS.append(cur)
                    else:
                        cur['text'] += ' ' + text
                    continue
                m = re.match(r'^((?:[A-ZČĆŠŽĐ]{2,}[- ]?)+?)(?:,? je\b|,|$)', text)    # a hero: "DRAGO FLIS-STRELA, je bil"
                if m and len(m.group(1).split()) >= 2 and m.group(1).isupper():
                    cur = {'kind': 'hero', 'caps': m.group(1).strip(' ,'), 'text': text, 'page': n, 'rows': [r]}
                    POSTS.append(cur)
                elif cur and cur['kind'] == 'hero':
                    cur['text'] += ' ' + text
                    if cur['page'] == n:
                        cur['rows'].append(r)


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    read_posts(pdf_path)
    for p in POSTS:
        p['text'] = mended(p['text'])
        if p['kind'] == 'post':
            caps, _, when = p['text'].partition('(')
            caps = re.sub(r"[\d' ]+$", '', caps.strip())                # the footnote mark: "MOČNIK-FLORJAN 2", "MITO ' 1"
            p['last'], p['given'], p['nick'] = person(mended(caps))
            p['line'] = f"{p['duty']} ({when.rstrip(') ')})"
            first = p['rows'][0]
            name = first[:next((i for i, w in enumerate(first) if w['text'].startswith('(')), len(first))]
            p['box'] = [first[0]['x0'], min(w['top'] for w in name), max(w['x1'] for w in name),
                        max(w['bottom'] for w in name)]
        else:
            p['last'], p['given'], p['nick'] = person(mended(p['caps']))
            p['line'] = p['text']
            ws = [w for r in p['rows'] for w in r]
            p['box'] = [min(w['x0'] for w in ws), min(w['top'] for w in ws), max(w['x1'] for w in ws),
                        max(w['bottom'] for w in ws)]
    return [{'text': '§§post' + str(i), 'x': round(p['box'][0], 1), 'y': round(p['box'][1], 1), 'page': p['page']}
            for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], '', '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        key = f"{p['last']} {p['given']}"
        man = seen.get(key)
        if man is None:
            man = seen[key] = s
            s['_posts'], s['_bio'], s['_nicks'] = [], '', []
            s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = [round(v, 1) for v in p['box']]
            s['unit_detail'] = 'Štab brigade'
            out.append(s)
        if p['kind'] == 'post':
            man['_posts'].append(p['line'])
        else:
            man['_bio'] = p['line']
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
    for s in out:
        key = f"{s['last_name']} {s['first_name']}"
        note, born, place, death, day, where = FATES.get(key, ('',) * 6)
        word = 'zvana' if key == 'Škapin Mihaela' else 'zvani'
        parts = [f'{word} {n}' for n in s['_nicks']]
        if s['_posts']:
            parts.append(f"{COMMAND}: {'; '.join(s['_posts'])}." + (f' {note}' if note else ''))
        if s['_bio']:                                                   # after a post's full stop, a sentence of its own
            parts.append(f"{HEROES}: {s['_bio']}")
            if s['_posts']:
                parts[-2:] = [f'{parts[-2]} {parts[-1]}']
        if not s['_posts']:
            s['unit_detail'] = None
        s['additional_info'] = '; '.join(parts)
        if born:
            s['birth_year'], s['birth_place'] = born, place
        if death:
            s['death_type'], s['death_date'], s['death_place'] = death, day, where
        s['full_name'] = key
        for k in ('_post', '_posts', '_bio', '_nicks'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=64, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
