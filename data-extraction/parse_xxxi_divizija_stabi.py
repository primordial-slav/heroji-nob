"""
Stanko Petelin-Vojko, *Med Triglavom in Trstom - Zgodovina XXXI. divizije* (2), (znaci.org 00003/1083, the whole
book's PDF pp. 268-273 → website/public/pdfs/xxxi-divizija-stabi.pdf, book pp. 557-562): "Štabi XXXI. divizije ter
Gradnikove, Prešernove in Vojkove brigade", the commanders, commissars, their deputies and the chiefs of staff of the
XXXI. divizija and its three brigades, numbered under each unit and duty, each with the days he held the post and the
rank he had when the book was written:
    l. DUŠAN ŠVARA-DULE, generalmajor JLA (od 6. okt. 1943 do 13. jan. 1944).
A book across units: its entries are added to the records of the officers it names (Gradnikova is unit 64), the rest
go to Ostali borci. A man in several posts is one entry with each of them, in the book's order.

The text layer spaces letters apart ("IVA N", "SV ARA"), loses carons ("POTOCAR", "JOZE"), garbles a few names
("MARJANOVI(:;>", "I{UK-BRANK0") and reads the footnote marks as figures, quotes or letters ("ČAPAJEV:i"); each name is
the one of PEOPLE (read from the page images: the Slovenes' -ič and the Serbs' and Montenegrins' -ić as the book prints them) whose letters it is closest to.
The footnotes (in smaller type) tell who fell and who died after the war; DEATHS holds them, read from the page images,
since their marks are garbled too. "Robin", deputy commissar of the Prešernova, is a man whose surname the author could
not learn (`unnamed`).

Output: data-extraction/znaci/xxxi-divizija-stabi-entries.json (IDs 9072xxxxxx, by each man's first post).
Usage: python data-extraction/parse_xxxi_divizija_stabi.py
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path
from statistics import median

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'xxxi-divizija-stabi.pdf'
OUT = HERE / 'znaci' / 'xxxi-divizija-stabi-entries.json'
PREFIX = '9072'
BOOK_PAGE = {p: 556 + p for p in range(1, 7)}
UNITS = {'XXXI. DIVIZIJA': ('XXXI. divizija NOV in POJ', None), 'III. SNOUB': ('III. SNOUB »Ivana Gradnika«', 64),
         'VII. SNOUB': ('VII. SNOUB »Franceta Prešerna«', None), 'XVI. SNOUB': ('XVI. SNOUB »Janka Premrla-Vojka«', None)}
DUTIES = {'Komandanti': 'komandant', 'Komisarji': 'komisar', 'Namestniki komandantov': 'namestnik komandanta',
          'Namestniki komisarjev': 'namestnik komisarja', 'Načelniki štaba': 'načelnik štaba'}
PEOPLE = [
    'Dušan Švara-Dule', 'Stane Potočar-Lazar', 'Jože Klanjšek-Vasja', 'Franc Rojšek-Jaka', 'Evgen Matejka-Pemc',
    'Ciril Keršič-Metod', 'Rudi Kodrič-Branko', 'Jože Kuk-Branko', 'Ivan Franko-Iztok', 'Rudolf Hribernik-Svarun',
    'Branko Karapandža-Matjažek', 'Anton Peternelj-Igor', 'Franc Kranjc-Franjo', 'Ivan Turšič-Iztok', 'Milan Tominec',
    'Stanko Petelin-Vojko', 'Samuel Horvat-Samo', 'Danilo Šorović', 'Martin Greif-Rudi', 'Stanko Jež',
    'Ratko Marjanović', 'Ivan Sulič-Iztok', 'Rado Klanjšček', 'Cveto Močnik-Florijan', 'Anton Bavec-Cene',
    'Jože Čerin-Peter', 'Franc Tavčar-Rok', 'Vinko Šumrada-Radoš', 'Drago Flis-Strela', 'Viljem Klemenc-Vili',
    'Alojz Tomšič', 'Anton Kvaternik', 'Slavko Bombač-Boris', 'Jože Avsec-Čapajev', 'Jože Mihevc-Rudar',
    'Franc Nemgar', 'Svetolik Jovanović-Mito', 'Drago Braniselj-Svarun', 'Miro Pavlin', 'Franc Vehar',
    'Franc Primožič', 'Franc Rustja-Čanči', 'Oto Vrhunec-Blaž Ostrovrhar', 'Ivan Leban', 'Rado Jakin',
    'Dušan Vukadinović', 'Ivan Javor-Igor', 'Silvo Klavčič-Silvan', 'Franc Jereb-Slavko', 'Janko Prezelj-Stane',
    'Karl Leskovec', 'Ferdo Tolar-Mirko', 'Ludvik Petelinšek-Črt', 'Davorin Ferligoj', 'Viktor Kirn',
    'Anton Selišnik', 'Milan Našič', 'Albin Drolc-Krtina', 'Franc Jernejc-Milče', 'Robin', 'Franc Čopi-Borutin',
    'Petar Alfirević-Pero', 'Stanko Primožič-Gorazd', 'Jan Koncilija', 'Karol Nardin-Jakec', 'Rudolf Griželj-Vardar',
    'Henrik Zdešar', 'Jože Lenart', 'Jože Berce-Rudi', 'Mirko Dukić', 'Avgust Jereb-Rok', 'Anton Milič-Marko',
    'Miran Bertok', 'Ivan Puntar-Gubec', 'Radovan Dolenc-Perun', 'Jože Sagadin', 'Ljubo Nenezić', 'Pavle Kogej',
]
# the footnotes: (fate, ISO day or year, place)
DEATHS = {
    'Evgen Matejka-Pemc': ('Padel je 3. maja 1945 ob Soči.', 'poginuo', '1945-05-03', 'Soča'),
    'Ciril Keršič-Metod': ('Ko je bil na partijskem tečaju na Dolenjskem, se je iz nepojasnjenih razlogov sam ustrelil.',
                           'umro', '1944', ''),
    'Jože Kuk-Branko': ('Leta 1946 se je smrtno ponesrečil.', '', '', ''),
    'Ivan Turšič-Iztok': ('Padel je 27. julija 1944 pri Lokvah v Trnovskem gozdu.', 'poginuo', '1944-07-27', 'Lokve'),
    'Ratko Marjanović': ('Umrl je po končani vojni v Sarajevu.', '', '', ''),
    'Cveto Močnik-Florijan': ('Padel je na dan ustanovitve brigade na Golobarju.', 'poginuo', '1943-04-26', 'Golobar'),
    'Jože Avsec-Čapajev': ('Smrtno se je ponesrečil 8. februarja 1944 na Cerkljanskem vrhu.', 'umro', '1944-02-08',
                           'Cerkljanski vrh'),
    'Jože Mihevc-Rudar': ('Padel je 20. junija 1944 na Jelovici.', 'poginuo', '1944-06-20', 'Jelovica'),
    'Franc Nemgar': ('Padel je 2. maja 1945 na Bazovici pri Trstu.', 'poginuo', '1945-05-02', 'Bazovica'),
    'Svetolik Jovanović-Mito': ('Padel je 20. decembra 1944 v Dobravi pri Gorenji vasi.', 'poginuo', '1944-12-20',
                                'Dobrava pri Gorenji vasi'),
    'Drago Braniselj-Svarun': ('Padel je 17. januarja 1944 na Vojskem.', 'poginuo', '1944-01-17', 'Vojsko'),
    'Oto Vrhunec-Blaž Ostrovrhar': ('Padel je 5. aprila 1945 pod Blegošem.', 'poginuo', '1945-04-05', 'Blegoš'),
    'Silvo Klavčič-Silvan': ('Padel je 4. avgusta 1943 pri Hotavljah.', 'poginuo', '1943-08-04', 'Hotavlje'),
    'Ludvik Petelinšek-Črt': ('Padel je 15. marca 1944 pri Leskovici.', 'poginuo', '1944-03-15', 'Leskovica'),
    'Milan Našič': ('Padel je 15. avgusta 1943 na Krimu.', 'poginuo', '1943-08-15', 'Krim'),
    'Albin Drolc-Krtina': ('Po vojni se je smrtno ponesrečil v Kranju.', '', '', ''),
    'Robin': ('Njegovega priimka ni bilo moč ugotoviti. Padel je 4. avgusta 1943 na Žirovskem vrhu.', 'poginuo',
              '1943-08-04', 'Žirovski vrh'),
    'Radovan Dolenc-Perun': ('Padel je 8. oktobra 1944 pred Trnovim na Primorskem.', 'poginuo', '1944-10-08', 'Trnovo'),
}
# the text layer's slips in the days
WHEN = {'cd ': 'od ', 'ja:n.': 'jan.', 'ma,rca': 'marca', 's,ept.': 'sept.', 'W. marca': '10. marca',
        'sepctembra': 'septembra'}
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def key(s: str) -> str:
    return re.sub(r'[^A-Z]', '', s.upper().translate(FOLD))


KEYS = {key(p): p for p in PEOPLE}


def person(printed: str) -> str:
    k = key(re.sub(r'[\d\'"’:;]+i?$', '', printed.strip()))
    best = max(KEYS, key=lambda c: difflib.SequenceMatcher(None, k, c).ratio())
    assert difflib.SequenceMatcher(None, k, best).ratio() > .8, (printed, best)
    return KEYS[best]


def lines_of(page) -> list[dict]:
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    h = median(w['bottom'] - w['top'] for w in words)
    out = []
    for ws in entry_boxes._cluster(words, 0.45 * h):
        size = max(w['bottom'] - w['top'] for w in ws)
        out.append({'x0': min(w['x0'] for w in ws), 'x1': max(w['x1'] for w in ws), 'top': min(w['top'] for w in ws),
                    'bottom': max(w['bottom'] for w in ws), 'text': ' '.join(w['text'] for w in ws), 'small': size < 7.5})
    return out


def read() -> list[dict]:
    """[{unit, duty, printed, text, page, x0, x1, top, bottom}] in the book's order"""
    posts, unit, duty, cur = [], None, None, None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for ln in lines_of(page):
                t = ln['text'].strip().lstrip('. ')
                if ln['small'] or re.fullmatch(r'\d{3}', t) or t.startswith('ŠTABI') or t.startswith('PREŠERNOVE'):
                    continue                                       # footnotes, the page number, the title
                u = next((v for k, v in UNITS.items() if t.startswith(k)), None)
                if u:
                    unit, cur = u, None
                    continue
                d = next((v for k, v in DUTIES.items() if t.rstrip(':').replace(' ', '') == k.replace(' ', '')
                          or t.startswith(k + ':')), None)
                if d:
                    duty, cur = d, None
                    continue
                m = re.match(r'^(?:[l1]|\d{1,2})\.\s+(.+)$', t)
                if m and re.match(r'[A-ZČĆŽŠĐ]{2}|[A-ZČĆŽŠĐ] [A-Z]', m.group(1)):
                    cur = {'unit': unit, 'duty': duty, 'text': m.group(1), 'page': pno, 'x0': ln['x0'],
                           'x1': ln['x1'], 'top': ln['top'], 'bottom': ln['bottom']}
                    posts.append(cur)
                elif cur:
                    cur['text'] += ' ' + t
                    if pno == cur['page']:
                        cur['x1'], cur['bottom'] = max(cur['x1'], ln['x1']), ln['bottom']
    return posts


def main():
    posts = read()
    people: dict[str, dict] = {}
    for p in posts:
        text = re.sub(r'\s+', ' ', p['text']).strip()
        name = re.split(r',|\s\(', text, 1)[0]
        who = person(name)
        rank = re.search(r',\s*([^()]+?)\s*\(', text)
        when = re.search(r'\(([^()]*)\)', text)
        when = re.sub(r'\b[lI]\.', '1.', when.group(1)) if when else ''
        for a, b in WHEN.items():
            when = when.replace(a, b)
        e = people.setdefault(who, {'posts': [], 'rank': '', 'first': p, 'units': set()})
        e['posts'].append(f"{p['unit'][0]}, {p['duty']}" + (f" ({when})" if when else ''))
        e['rank'] = e['rank'] or (rank.group(1).strip() if rank else '')
        if p['unit'][1]:
            e['units'].add(p['unit'][1])
    assert set(people) == set(PEOPLE), set(PEOPLE) ^ set(people)
    recs = []
    for no, (who, e) in enumerate(sorted(people.items(), key=lambda x: posts.index(x[1]['first'])), 1):
        name, _, nick = who.partition('-')
        given, _, last = name.partition(' ')
        death = DEATHS.get(who, ('', '', '', ''))
        text = '; '.join(e['posts']) + '.' + (f" Čin: {e['rank']}." if e['rank'] else '') + (f' {death[0]}' if death[0] else '')
        p = e['first']
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {given}' + (f' — {nick}' if nick else ''),
                     'last_name': last, 'first_name': given, 'also': [], 'nick': nick, 'fathers_name': '',
                     'birth_year': '', 'born_in': '', 'death_year': death[2][:4], 'death_date': death[2],
                     'death_type': death[1], 'death_place': death[3], 'survived': not death[1],
                     'unnamed': who == 'Robin', 'units': sorted(e['units']), 'no': no,
                     'list': 'Štabi XXXI. divizije ter Gradnikove, Prešernove in Vojkove brigade',
                     'additional_info': f'Štabi XXXI. divizije: {text}', 'source_page': BOOK_PAGE[p['page']],
                     'pdf_file': PDF, 'pdf_page': p['page'], 'pdf_x': round(p['x0'], 1), 'pdf_y': round(p['top'], 1),
                     # his first post's lines (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(posts)} posts, {len(recs)} men -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][20:200]}")


if __name__ == '__main__':
    main()
