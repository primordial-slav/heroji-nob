"""
Parser: Druga lička brigada (brigade code 3) — its officers, a fourth list.

Source: Đorđe J. Orlović, *Druga lička proleterska brigada* (Beograd 1983; znaci.org 00001/160, the chapter 160_20.pdf,
        its 12 pages, book pp. 349-360; the author is in it, the brigade's intelligence officer of 1944)  →  website/public/pdfs/druga-licka-staresine.pdf: "Starešinski sastav štaba Druge ličke brigade i
        štabova njenih bataljona od stvaranja brigade do kraja rata", the commanders, commissars, their deputies and
        the operations, intelligence and supply officers of the brigade staff and of the staffs of its four
        battalions and its 5. mitraljeski bataljon, under each duty in prose, a paragraph a man or two:
    KOMANDANTI
    Milan Ljubiše Šakić (Mićun), rođen 1915. godine u trgovačkoj porodici u Udbini. Po zanimanju učitelj, ...
The prose names a man as the sentence needs him ("dužnost je poverena Stevi Milana Žuniću, rođenom ..."), so the men
of each paragraph are given by hand (`MEN`, read from the paragraphs), with the father as printed and what he was
called. A man in several posts is one record with each paragraph; a paragraph that names two men is in both. The
battalions' headings all read "ŠTAB 1. BATALJONA" in znaci's re-typeset text; they are the 1., 2., 3. and 4. bataljon
in turn, as the paragraphs tell (Opsenica's bataljon, the 2., is not the one Bogdanović was moved to, the 1.). The
author's footnotes are left out. The fallen of the unit's first book are its first list (IDs from 1), the survivors
and the memoir book's fallen from 10001 and 20001; these get IDs from 30001.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/druga-licka-staresine.pdf'
UNIT = 'website/public/druga-licka-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00001_160_20.pdf'   # znaci.org 00001/160_20.pdf
TITLE = 'Starešinski sastav štaba Druge ličke brigade i štabova njenih bataljona'
UNITS = ['Štab brigade', '1. bataljon', '2. bataljon', '3. bataljon', '4. bataljon', '5. mitraljeski bataljon']
OF_UNIT = ['brigade', '1. bataljona', '2. bataljona', '3. bataljona', '4. bataljona', '5. mitraljeskog bataljona']
DUTIES = {'KOMANDANTI': 'komandant', 'POLITIČKI KOMESARI': 'politički komesar',
          'ZAMENICI KOMANDANTA': 'zamenik komandanta', 'ZAMENICI POLITIČKOG KOMESARA': 'zamenik političkog komesara',
          'OPERATIVNI OFICIRI': 'operativni oficir', 'OBAVEŠTAJNI OFICIRI': 'obaveštajni oficir',
          'INTENDANTI': 'intendant'}
# the men each paragraph names (its number among the chapter's paragraphs): surname, given name, father as printed,
# what he was called, and his duty where it isn't the heading's; 'key' parts two men of one name
MEN = {
    0: [('Šakić', 'Milan', 'Ljubiše', 'Mićun')], 1: [('Uzelac', 'Mile', '', 'Miloš')], 2: [('Dotlić', 'Dušan', 'Dane')],
    3: [('Rakić', 'Dragan', 'Mile')], 4: [('Babić', 'Petar', 'Petra', 'Pepa')], 5: [('Stanković', 'Đuro', 'Danila')],
    6: [('Damjanović', 'Branko', 'Ilije')], 7: [('Pavičić', 'Milan')], 8: [('Radaković', 'Lazo')],
    9: [('Dotlić', 'Dušan'), ('Pokrajac', 'Đurađ')], 10: [('Rakić', 'Dragan'), ('Damjanović', 'Danilo', '', 'Danić')],
    11: [('Medić', 'Ljubomir', '', 'Brzica')], 12: [('Ugarković', 'Dane', 'Dmitra')],
    13: [('Mandarić', 'Vladimir', '', '', 'načelnik štaba')], 14: [('Vujinović', 'Bogdan', 'Nikole')],
    15: [('Mrda', 'Simo')], 16: [('Pejnović', 'Nikola', 'Jovana', 'Nikica')], 17: [('Hinić', 'Jovo', 'Manojla')],
    18: [('Pokrajac', 'Đurađ', 'Rade', 'Đuđa')], 19: [('Sever', 'Milan', 'Jovana')],
    20: [('Damjanović', 'Danilo'), ('Medić', 'Ljubomir'), ('Palija', 'Ilija', 'Ilije')],
    22: [('Stjelja', 'Branko', 'Marka')], 23: [('Kovač', 'Jovan')], 24: [('Orlović', 'Đorđe', 'Jovana')],
    25: [('Mirković', 'Rade', 'Dane')], 26: [('Martinović', 'Luka')], 27: [('Ugarković', 'Milan')],
    28: [('Marelj', 'Dušan', '', 'Dujo')], 29: [('Delić', 'Vlajko')], 30: [('Adžić', 'Nikola', '', 'Adžija')],
    31: [('Radaković', 'Nikola')], 32: [('Delić', 'Rade', 'Miče')], 33: [('Dmitrašinović', 'Proko')],
    # 1. bataljon
    34: [('Popović', 'Tomica', 'Jovana')], 35: [('Rakić', 'Dragan'), ('Sever', 'Milan')],
    36: [('Palija', 'Ilija'), ('Divjak', 'Bude')], 37: [('Tankosić', 'Milan')],
    38: [('Tankosić', 'Milan'), ('Palija', 'Ilija')], 39: [('Rašeta', 'Petar', 'Koje', 'Pejo')],
    40: [('Rašeta', 'Ilija', 'Milana', 'Ico')], 41: [('Dozet', 'Radovan', 'Sime')],
    42: [('Mrda', 'Simo'), ('Bogdanović', 'Jovo')], 43: [('Milošević', 'Ilija', 'Stevana')], 44: [('Pavičić', 'Milan')],
    45: [('Knežević', 'Mile')], 46: [('Dotlić', 'Dušan'), ('Rašeta', 'Stevan', '', 'Steviša')],
    47: [('Orlović', 'Đorđe')], 48: [('Dragaš', 'Stojan')], 49: [('Medić', 'Mirko', 'Petra')],
    50: [('Rašeta', 'Petar', '', 'Pejo')], 51: [('Vlaisavljević', 'Dušan', 'Mile')], 52: [('Galin', 'Simo', 'Nikole')],
    53: [('Milošević', 'Ilija')], 54: [('Ćuić', 'Dane', 'Vladimira')], 55: [('Priča', 'Mile')],
    56: [('Orlić', 'Milan', 'Mojsija')], 57: [('Hinić', 'Petar', '', '', None, 'Hinić Petar 1922')],
    58: [('Rašeta', 'Stevan', '', 'Steviša'), ('Rašeta', 'Petar', 'Andrija', '', None, 'Rašeta Petar Andrije')],
    59: [('Ljuština', 'Marko')], 60: [('Nikolić', 'Boško')], 61: [('Vukmirović', 'Milan')],
    62: [('Stjelja', 'Branko'), ('Kljajić', 'Rade', 'Stojana')], 63: [('Martinović', 'Luka')], 64: [('Ratković', 'Ivo')],
    # 2. bataljon
    65: [('Opsenica', 'Staniša')], 66: [('Ćurčić', 'Jovan', 'Staniša')], 67: [('Ratković', 'Rade', 'Vuje')],
    68: [('Damjanović', 'Danilo')], 69: [('Ugarković', 'Dane')], 70: [('Opačić', 'Dušan', 'Jove', 'Čaruga')],
    71: [('Bogdanović', 'Jovo', 'Stojana')], 72: [('Žunić', 'Stevo', 'Milana')], 73: [('Pamuković', 'Kamilo')],
    74: [('Balać', 'Petar', 'Jove', 'Žika')], 75: [('Hinić', 'Stevo', 'Manojla')], 76: [('Ćuić', 'Bogdan', 'Ilije')],
    77: [('Narančić', 'Božo')], 78: [('Ratković', 'Rade', 'Vuje')], 79: [('Ugarković', 'Dane')],
    80: [('Božić', 'Vladimir')], 81: [('Orlović', 'Đorđe')], 82: [('Rašeta', 'Ilija', '', 'Ico')],
    84: [('Ratković', 'Dušan', 'Bože')], 85: [('Hinić', 'Petar', 'Pantelije', 'Pejica', None, 'Hinić Petar Pejica')],
    86: [('Milošević', 'Ilija')], 87: [('Hinić', 'Jovo', 'Manojla')], 88: [('Vukobratović', 'Nikola', 'Dane')],
    89: [('Barać', 'Dane', '', 'Dako')], 90: [('Rapajić', 'Milan', '', 'Mića')], 91: [('Čović', 'Dušan')],
    92: [('Krtinić', 'Petar')], 93: [('Tankosić', 'Milan')], 94: [('Smiljanić', 'Tanasije')], 96: [('Kovač', 'Jovan')],
    # 3. bataljon
    97: [('Rakić', 'Dragan')], 98: [('Ćosić', 'Dušan', 'Luke')], 99: [('Vukadinović', 'Milan', 'Stevana')],
    100: [('Sever', 'Milan')], 101: [('Grahovac', 'Ivan', 'Tome')], 102: [('Sadžak', 'Jovo', 'Nikole', 'Jocan')],
    103: [('Sladić', 'Duka', 'Bude')], 104: [('Bosnić', 'Jovan', 'Luke')], 105: [('Galin', 'Simo', 'Nikole')],
    106: [('Korać', 'Rade', 'Miloša', 'Raco')], 107: [('Dopuđa', 'Sava', 'Petra')],
    108: [('Grković', 'Jovo', 'Bože', 'Jovica')], 109: [('Priča', 'Mile'), ('Obradović', 'Božo')],
    110: [('Milić', 'Tomo')], 111: [('Ćosić', 'Dušan')], 112: [('Ćuić', 'Dušan'), ('Ivančević', 'Dmitar')],
    113: [('Drakulić', 'Milan')], 114: [('Bosnić', 'Jovan')], 115: [('Bajić', 'Branko', '', 'Baja')],
    116: [('Korać', 'Rade')], 117: [('Grković', 'Jovo', '', 'Jovica'), ('Ratković', 'Dušan')],
    118: [('Banić', 'Mile', 'Dane')], 119: [('Ćuić', 'Dane')], 120: [('Hinić', 'Milan')],
    121: [('Osmanbegović', 'Salih')], 122: [('Orlović', 'Đorđe')], 124: [('Barać', 'Milan')], 125: [('Blanuša', '')],
    126: [('Divjak', 'Blagoje')], 127: [('Barać', 'Milan')],
    # 4. bataljon
    128: [('Šijan', 'Milan')], 129: [('Dotlić', 'Dušan')], 130: [('Rašeta', 'Stevan', 'Mile', 'Steviša')],
    131: [('Mihovilović', 'Milanko')], 132: [('Obradović', 'Milan', 'Stevana', 'Miča')],
    133: [('Drakulić', 'Milan', 'Jove')], 134: [('Olbina', 'Dmitar')], 135: [('Basta', 'Petar', 'Ilije')],
    136: [('Ratković', 'Dušan', 'Bože')], 137: [('Lovrić', 'Iso')], 138: [('Milić', 'Tomo')],
    139: [('Vukadinović', 'Milan', 'Stevana')], 140: [('Ivančević', 'Dmitar')], 141: [('Orlović', 'Đorđe', 'Jovana')],
    142: [('Olbina', 'Dmitar')], 144: [('Hinić', 'Petar', 'Pantelije', 'Pejica', None, 'Hinić Petar Pejica')],
    145: [('Pejnović', 'Nikola')], 146: [('Korać', 'Rade', '', 'Raco')], 147: [('Vukobratović', 'Nikola', 'Dane')],
    148: [('Hinić', 'Jovo', 'Manojla')], 149: [('Budisavljević', 'Ilija')], 150: [('Antić', 'Emil')],
    151: [('Mihovilović', 'Milanko')], 152: [('Nikolić', 'Boško')], 153: [('Majstorović', 'Dušan', 'Miloša')],
    154: [('Vukobratović', 'Nikola')], 155: [('Končar', 'Geco')], 156: [('Majstorović', 'Dušan')],
    # 5. mitraljeski bataljon: one paragraph, its whole staff
    158: [('Divjak', 'Bude', '', '', 'komandant'), ('Balać', 'Petar', 'Jove', 'Žika', 'politički komesar'),
          ('Ćupurdija', 'Daćo', '', '', 'politički komesar'), ('Hinić', 'Jovo', '', '', 'zamenik političkog komesara')],
}
PARAS: list = []                     # [text, page, unit index, duty, lines]
POSTS: list = []
_unit: dict = {}


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    for page in r.pages:
        w.add_page(page)
    with open(PDF, 'wb') as f:
        w.write(f)


def fold(t: str) -> str:
    t = unicodedata.normalize('NFKD', t.lower().replace('đ', 'd'))
    return ''.join(c for c in t if not unicodedata.combining(c))


ADDS = {('c', 'č'), ('c', 'ć'), ('s', 'š'), ('z', 'ž'), ('d', 'đ')}


def spelled(name: str, field: str) -> str:
    """The unit's spelling of a name where the page lost a caron ("Dorđe" = Đorđe); a mark the page prints stays
    (the unit's lists have their own slips: "Šever", "Damjanovič")."""
    cands = _unit.get(field, {}).get(fold(name), Counter())
    if name in cands:
        return name
    for cand, _ in cands.most_common():
        if len(cand) == len(name) and all(a == b or (a.lower(), b.lower()) in ADDS for a, b in zip(name, cand)):
            return cand
    return name


def read_paragraphs(pdf_path: str) -> None:
    """The chapter's paragraphs (a line set in from the text's left edge starts one), each under its staff and duty;
    the headings and the footnotes (in smaller type) are not paragraphs."""
    unit, duty = -1, ''
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            rows: list = []
            for w in sorted(viewer_words(page, extra_attrs=['size']), key=lambda w: (round(w['top']), w['x0'])):
                if rows and abs(rows[-1][0]['top'] - w['top']) <= 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            rows = [sorted(r, key=lambda w: w['x0']) for r in rows]
            body = [r for r in rows if r[0]['size'] >= 8.4]
            left = min(round(r[0]['x0']) for r in body)
            in_note, after_head = False, True
            for r in rows:
                t = ' '.join(w['text'] for w in r)
                if re.fullmatch(r'\d{3}', t):
                    continue
                if r[0]['size'] < 8.4 or re.match(r'^\d{3}\)', t):
                    in_note = True                                           # a footnote, to the page's end
                    continue
                if in_note and r[0]['x0'] < left + 8:
                    continue
                in_note = False
                if not re.search(r'[a-zčćžšđ]{2}', t):
                    if 'ŠTAB' in t and n > 1 or t == 'ŠTAB BRIGADE':
                        unit += 1
                    elif t in DUTIES:
                        duty = t
                    after_head = True
                    continue
                if r[0]['x0'] > left + 12 or after_head:
                    PARAS.append([t, n, unit, duty, [r]])
                    after_head = False
                else:
                    p = PARAS[-1]
                    p[0] = p[0][:-1] + t if p[0].endswith('-') else p[0] + ' ' + t
                    if n == p[1]:
                        p[4].append(r)


def clean(text: str) -> str:
    """The paragraph without the footnotes' marks ("žandarm,' 03 » da bi", "... Perušića. 5041")."""
    text = re.sub(r",'\s*0\d\s*»", ',', text)
    text = re.sub(r"\s+5\d{2,3}\s*['’]*\s*$|\s+50\s*''\s*$", '', text)
    return text.replace("Junački'je", 'Junački je').strip()


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    for f in ('last_name', 'first_name'):
        _unit[f] = {}
    for s in json.load(open(UNIT, encoding='utf-8')):
        if s['soldier_id'][4:6] != '03':
            for f in _unit:
                _unit[f].setdefault(fold(s[f]), Counter())[s[f]] += 1
    read_paragraphs(pdf_path)
    for i, men in sorted(MEN.items()):
        text, page, unit, duty, lines = PARAS[i]
        text = clean(text)
        for m in men:
            last, given, father, nick, own, key = (list(m) + ['', '', '', None, None])[:6]
            POSTS.append({'last': spelled(last, 'last_name'), 'given': spelled(given, 'first_name') if given else '',
                          'father': father, 'nick': nick, 'unit': unit, 'page': page, 'lines': lines,
                          'duty': f"{own or DUTIES[duty]} {OF_UNIT[unit]}", 'text': text, 'alone': len(men) == 1,
                          'key': key or f'{fold(last)} {fold(given)}'})
    return [{'text': '§§post' + str(i), 'x': round(p['lines'][0][0]['x0'], 1), 'y': round(p['lines'][0][0]['top'], 1),
             'page': p['page']} for i, p in enumerate(POSTS)]


def parse(text: str) -> dict:
    p = POSTS[int(text[6:])]
    rec = _record(p['last'], p['given'], p['father'], '')
    rec['_post'] = int(text[6:])
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        p = POSTS[s['_post']]
        man = seen.get(p['key'])
        if man is None:
            man = seen[p['key']] = s
            s['_posts'], s['_nicks'], s['_rects'] = [], [], []
            s['unit_detail'] = UNITS[p['unit']]
            out.append(s)
        if p['father'] and not man['middle_name']:
            man['middle_name'] = man['fathers_name'] = p['father']
        man['_posts'].append(f"{p['duty'][:1].upper()}{p['duty'][1:]}: {p['text']}")   # "Komandant 1. bataljona: ..."
        if p['nick'] and p['nick'] not in man['_nicks']:
            man['_nicks'].append(p['nick'])
        # his own birth: "Žuniću, rođenom 1919. godine", "Medić Brzica, rođen u Doljanima (D. Lapac) 1913"
        at = fold(p['text']).find(fold(p['last'])[:-1] or '\0')
        y = re.match(r'\w*(?: [A-ZČĆŽŠĐ]\w+)?(?: \([^)]*\))?,? rođen\w*\b[^0-9]{0,60}?(1[89]\d\d)',
                     p['text'][at + len(p['last']) - 1:]) if at >= 0 else None
        if y and not man.get('birth_year'):
            man['birth_year'] = y.group(1)
        if p['page'] == man['pdf_page'] and not man['_rects']:
            man['_rects'] = [[round(min(w['x0'] for w in ln), 1), round(min(w['top'] for w in ln), 1),
                              round(max(w['x1'] for w in ln), 1), round(max(w['bottom'] for w in ln), 1)]
                             for ln in p['lines']]
    for s in out:
        s['additional_info'] = '; '.join([f'zvani {n}' for n in s['_nicks']] + [f"{TITLE}. {' '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0][0], r[0][1], max(x[2] for x in r), r[-1][3]
        if len(r) > 1:
            s['pdf_rects'] = r
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k in ('_post', '_posts', '_nicks', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=3, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=30001, keep_other_sources=True)
