"""
Karel Levičnik, *Artileristi prekomorci* (Nova Gorica 1968; znaci.org 00003/778.pdf, PDF pp. 218-226) →
website/public/pdfs/artileristi-prekomorci.pdf: two lists at the end of the history of the artillery units the
"prekomorci" (the Slovenes and Istrians who came over the sea from Italy and Africa) formed on Vis and in Italy, a book
across units:
    Bukovac, Klun, "Seznam padlih artileristov prekomorcev" (book pp. 227-228): the fallen and those who died of their
        wounds, a line or two each, "GRK Branko (r. 13. 5. 1922 — Slivje, Materija), padel 15. 11. 1944 v Sarajevu."
    Klun, "Seznam vodilnega kadra artilerijskih enot" (book pp. 231-234): the commanders, commissars and their deputies
        of each artillery group, divizion and battery, given name first and run on under each unit's heading,
        "Komandant: Nikola Šofranac; politični komisar: Drago Vajs; ..."
A man in several posts is one entry with each of them; a post he never took up (the asterisk on Božidar Kraut) says so.
The OCR's slips in names are read back (`WORDS`: "Karei" = Karel, "Mis jak" = Misjak, "!uričič" = Juričić), and an -ič
the site's records spell -ić is turned (Croatian and Serbian officers in a Slovene book), Slovene -ič kept.
Output: data-extraction/znaci/artileristi-prekomorci-entries.json, IDs 9059xxxxxx in the book's order.
Usage: python data-extraction/parse_artileristi_prekomorci.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402

BOOK = 'artileristi-prekomorci'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
SOURCE = HERE / '.cache' / 'prekomorci' / '778.pdf'                  # znaci.org/00003/778.pdf
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9059'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_PAGES, LEADER_PAGES = (3, 4), (6, 7, 8, 9)                  # the site PDF's pages
BOOK_PAGE = {3: 227, 4: 228, 6: 231, 7: 232, 8: 233, 9: 234}
FALLEN = 'Seznam padlih artileristov prekomorcev'
LEADERS = 'Seznam vodilnega kadra artilerijskih enot'
WORDS = {'Karei': 'Karel', 'Mis jak': 'Misjak', '!uričič': 'Juričić', 'Simonie': 'Simonić', 'Cedo': 'Čedo',
         'čičin-šain': 'Čičin-Šain', 'šelevinec': 'Šelevinec', 'Klaić': 'Kljaić', 'CADŽANOVIĆ': 'ČADŽANOVIĆ',
         'CERNE': 'ČERNE', 'CUPIN': 'ČUPIN', 'FERJANCIČ': 'FERJANČIČ', 'KRIZMANCIČ': 'KRIZMANČIČ',
         'SIRCA': 'ŠIRCA', 'SKAPIN': 'ŠKAPIN', 'pade]': 'padel', 'podiegei': 'podlegel', 'moja 1945': 'maja 1945',
         'šempasu': 'Šempasu', 'Ćmem Kalu': 'Črnem Kalu', 'Ivo Zivković': 'Ivo Živković'}


def build_pdf() -> None:
    if not PDF.exists():
        out = fitz.open()
        out.insert_pdf(fitz.open(SOURCE), from_page=217, to_page=225)
        out.save(PDF, garbage=4, deflate=True)


def fix(t: str) -> str:
    for a, b in WORDS.items():
        t = t.replace(a, b)
    return t


def spell(word: str, turn: bool = False) -> str:
    """A surname in the site's spelling: a caron the page lost where the site's records agree ("Zivković" =
    Živković); with `turn` (the officers, Croats and Serbs most of them) an -ič the records spell -ić more often is -ić.
    The fallen, Slovenes from the Littoral most of them, keep their -ič ("Zemljič")."""
    w = kl.title(word) if word.isupper() else word
    c = ofz._spell['last'].get(w.upper().translate(ofz.FOLD), {})
    if turn and w.endswith('ič'):
        if c.get(w.upper()[:-1] + 'Ć', 0) > c.get(w.upper(), 0):
            w = w[:-1] + 'ć'
    if c.get(w.upper(), 0) < 2:                                      # a spelling the site has once may be a slip too
        fits = [s for s, n in sorted(c.items(), key=lambda x: -x[1]) if n >= 3 and len(s) == len(w)
                and all(a == b or (a != 'Đ' and b in ofz.LOST.get(a, '')) for a, b in zip(w.upper(), s))]
        if fits:
            w = kl.title(fits[0])
    return w


def page_lines(pdf, pno: int) -> list[dict]:
    return [dict(ln, page=pno) for ln in entry_boxes.read_page(pdf.pages[pno - 1], columns=1)['columns'][0]]


def fallen(pdf) -> list[dict]:
    out = []
    for pno in FALLEN_PAGES:
        for ln in page_lines(pdf, pno):
            t = fix(re.sub(r'\s+', ' ', ln['text']).strip())
            if re.fullmatch(r'\d{1,3}\*?|\d+ Artileristi prekomorci', t):
                continue
            m = re.match(rf'^([{U}][{U}-]+)\s+([{U}][{L}]+)\b(.*)$', t)
            if m:
                out.append({'last': spell(m.group(1)), 'given': m.group(2), 'text': t, 'page': pno, 'x0': ln['x0'],
                            'top': ln['top'], 'x1': ln['x1'], 'bottom': ln['bottom']})
            elif out:
                out[-1]['text'] += ' ' + t
                out[-1]['x1'], out[-1]['bottom'] = max(out[-1]['x1'], ln['x1']), ln['bottom']   # its box: all its lines
    for e in out:
        e['text'] = re.sub(r'(?<=[a-zčšž])[-\xad] (?=[a-zčšž])', '', e['text'])
        e['born'] = (re.search(r'\(r\.\s[^)]*?((?:18|19)\d\d)', e['text']) or [None, ''])[1]
        e['died'] = (re.search(r'(?:padel|podlegel|ponesrečil|umrl)[^;]{0,40}?(194\d)|(194\d)\.?\s*$', e['text']) or [None, '', ''])
        e['died'] = e['died'][1] or e['died'][2] or ''
    return out


def leaders(pdf) -> list[dict]:
    """(unit, duty, given, surname, note, page, line) for every post: the headings in capitals (a heading of two
    lines is one: "TEŽKA MOTORIZIRANA ARTILERIJSKA BRIGADA" / "IV. ARMADE"), the posts run on to a full stop"""
    blocks, para, in_note = [], None, False                          # ('head', text, pos) / ('posts', text, pos)
    for pno in LEADER_PAGES:
        for ln in page_lines(pdf, pno):
            t = fix(re.sub(r'\s+', ' ', ln['text']).strip())
            if re.fullmatch(r'\d{3}', t) or t.startswith(('Nikdar ni nastopil', 'nega štaba.', '*')):
                continue
            pos = (pno, ln['x0'], ln['top'], ln['x1'], ln['bottom'])
            if t == t.upper() and re.search(rf'[{U}]{{3}}', t) and ':' not in t:
                if blocks and blocks[-1][0] == 'head' and para is None:
                    blocks[-1] = ('head', blocks[-1][1] + ' ' + t, blocks[-1][2])
                else:
                    blocks.append(('head', t, pos))
                para = None
                continue
            if t.startswith('(') or in_note:                            # "(prepeljan v Dubrovnik II. korpusu)",
                in_note = ')' not in t                                  # a note may take two lines
                continue
            if para is None:
                para = ['posts', t, pos]
                blocks.append(para)
            else:
                para[1] = (para[1][:-1] if re.search(r'[a-zčšžA-ZČŠŽ][-\xad]$', para[1]) else para[1] + ' ') + t
            if t.endswith('.') and not re.search(r'\b\d\.$', t):
                para = None
    posts, unit = [], ''
    for kind, text, pos in blocks:
        if kind == 'head':
            unit = text
            continue
        text = re.sub(r'\xad\s*', '', re.sub(r'\s+', ' ', text)).rstrip('.')
        text = text.replace('Vojo pović', 'Vojo Popović')                # the text layer lost the line's last "Po-"
        sub = ''
        for chunk in re.split(r'(?=\b\d\.\s*baterija\s*—)', text):
            m = re.match(r'^(\d\.\s*baterija)\s*—\s*(.*)$', chunk.strip())
            if m:
                sub, chunk = m.group(1), m.group(2)
            for part in re.split(r';\s*', chunk.strip().rstrip('.')):
                if ':' not in part:
                    continue
                duty, names = [x.strip() for x in part.split(':', 1)]
                duty = re.sub(r'\s+ja\b', 'ja', duty).lower()
                for nm in re.split(r'(?:^|,?\s+)\d\.\s+', names):
                    nm = nm.strip(' ,.')
                    words = nm.rstrip('*').split()
                    if len(words) < 2:
                        continue
                    posts.append({'unit': unit + (f', {sub}' if sub else ''), 'duty': duty,
                                  'given': words[0], 'last': spell(''.join(words[1:]), turn=True),
                                  'note': 'nikdar ni nastopil te dolžnosti' if nm.endswith('*') else '',
                                  'page': pos[0], 'x0': pos[1], 'top': pos[2], 'x1': pos[3], 'bottom': pos[4]})
    return posts


def main() -> None:
    build_pdf()
    ofz.corpus()
    with pdfplumber.open(PDF) as pdf:
        fl, ld = fallen(pdf), leaders(pdf)
    out = []
    for e in fl:
        out.append({'name': f"{e['last']} {e['given']}", 'last_name': e['last'], 'first_name': e['given'],
                    'fathers_name': '', 'birth_year': e['born'], 'born_in': '', 'death_year': e['died'],
                    'death_type': 'poginuo', 'additional_info': f"{FALLEN}: {e['text']}",
                    'source_page': BOOK_PAGE[e['page']], 'pdf_file': PDF.name, 'pdf_page': e['page'],
                    'pdf_x': round(e['x0'], 1), 'pdf_y': round(e['top'], 1), 'pdf_x_end': round(e['x1'], 1),
                    'pdf_y_end': round(e['bottom'], 1)})
    by_man: dict[tuple, dict] = {}
    for p in ld:
        key = (p['last'], p['given'])
        post = f"{p['unit']} — {p['duty']}" + (f" ({p['note']})" if p['note'] else '')
        if key in by_man:
            by_man[key]['posts'].append(post)
            continue
        by_man[key] = {'p': p, 'posts': [post]}
        out.append(by_man[key])
    recs = []
    for i, e in enumerate(out, 1):
        if 'posts' in e:
            p = e['p']
            e = {'name': f"{p['last']} {p['given']}", 'last_name': p['last'], 'first_name': p['given'],
                 'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': '',
                 'additional_info': f"{LEADERS}: {p['given']} {p['last']}: " + '; '.join(e['posts']) + '.',
                 'survived': not any('padel' in x for x in e['posts']), 'source_page': BOOK_PAGE[p['page']],
                 'pdf_file': PDF.name, 'pdf_page': p['page'], 'pdf_x': round(p['x0'], 1), 'pdf_y': round(p['top'], 1),
                 # the line his unit's posts start on (the PDF is in entry_boxes.INLINE_ENTRIES, so this box stays)
                 'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)}
            e.pop('survived')
        recs.append({'soldier_id': f'{PREFIX}{i:06d}', **e})
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(recs)} entries ({len(fl)} fallen, {len(recs) - len(fl)} officers) -> {OUT.relative_to(HERE.parent)}")
    for r in recs:
        print(f"  {r['soldier_id']} {r['name']:28} {r['birth_year']:5} {r['death_year']:5} | {r['additional_info'][:120]}")


if __name__ == '__main__':
    main()
