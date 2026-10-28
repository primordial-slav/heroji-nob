"""
Zdravko Klanjšček, *Narodnooslobodilački rat u Sloveniji 1941—1945.* (Vojnoistorijski institut, Beograd 1984; znaci.org
00002/418, its PDF pp. 379-386 → website/public/pdfs/klanjscek-komandni-sastav.pdf, book pp. 393-400): Prilog 1,
"Spisak komandnog sastava viših jedinica NOV i PO Slovenije", a book across units. Under the Glavni štab, its
operational staff, the provincial staffs, the groups of partisan odredi, the operational zones, the corps, the
divisions (the 14., 15., 18., 30., 31., the Tršćanska, the VDV's command and the Garibaldi Natisone) and the
operational staffs, a post a line: "Komandant Franc Rozman Stane, 13. 7. 1943 — 7. 11. 1944. Pog. Lokve, Črnomelj."
(the duty, the given name, surname and partisan name, the days, a note: "Pog." where he fell, "Nije primio duž.").
A man in several posts is one entry with each of them; the footnote's three assistants of the Glavni štab's
commissar (1 October 1942 - 23 May 1943) are posts too. The book names no fate but where he fell; the pairs are
chosen by hand (`rematch_references.HAND`).

The text layer reads ž as i ("Joie", "Tomai", "Ambroiič"), parts words ("Gor jan", "Vel j ko") and sets the -ić of
the Serbian and Montenegrin officers as -ič in some lines and not in others ("Saranovič", "Šaranović"): `FIX`.

Output: data-extraction/znaci/klanjscek-komandni-sastav-entries.json (IDs 9107xxxxxx, by each man's first post).
Usage: python data-extraction/parse_klanjscek.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'klanjscek-komandni-sastav.pdf'
OUT = HERE / 'znaci' / 'klanjscek-komandni-sastav-entries.json'
PREFIX = '9107'
TITLE = 'Spisak komandnog sastava viših jedinica NOV i PO Slovenije'
BOOK_PAGE = 392                                     # book page minus the PDF's
DUTIES = [(r'[KkF]omandant', 'komandant'), (r'[PF]ol\. kom\.', 'politički komesar'), (r'Zam\. kom\.', 'zamenik komandanta'),
          (r'Zam\. pol\. (?:kom\.\*?|k\.)', 'zamenik političkog komesara'),
          (r'Pom\. pol\. k(?:om)?\.', 'pomoćnik političkog komesara'), (r'Nač\. štaba', 'načelnik štaba')]
DUTY = re.compile(rf"^({'|'.join(p for p, _ in DUTIES)})\s+(.*)$")
GROUPS = {'Glavni štab NOV i PO Slovenije': '', 'Operativni štab Glavnog štaba za zapadnu Sloveniju': '',
          'Pokrajinski štabovi': 'Pokrajinski štab {}', 'Grupe partizanskih odreda': '{} grupa partizanskih odreda',
          'Operativne zone': '{} operativna zona', 'Korpusi': '{} korpus', 'Divizije': '{} divizija',
          'Operativni štabovi': 'Operativni štab {}', 'Štab Baze Glavnog štaba Slovenije — Dalmacija': ''}
NOT_ORDINAL = ('Komanda VDV', 'Prva divizija')     # a division the heading names in full
# the text layer's slips, read from the other lines of the list and the site's records
FIX = {'Joie': 'Jože', 'Borts': 'Boris', 'Tomai': 'Tomaž', 'Ambroiič': 'Ambrožič', 'Amrožič': 'Ambrožič',
       'Čiimek': 'Čižmek', 'Cižmek': 'Čižmek', 'Gor jan': 'Gorjan', 'Vel j ko': 'Veljko', 'Kost ja': 'Kostja',
       'Laz.ar': 'Lazar', 'Raj ko': 'Rajko', 'üaki': 'Daki', 'Fratte': 'Franc', 'žokalj Diidži': 'Žokalj Džidži',
       'Janez.': 'Janez', 'Svara': 'Švara', 'Znidaršič': 'Žnidaršič', 'Tornine': 'Tominec', 'Gašpar': 'Gašper',
       'Babic': 'Babič', 'Crni': 'Črni', 'Svarim': 'Svarun', 'Janušik': 'Janošik', 'Petar Stante': 'Peter Stante',
       'Marjanovič': 'Marjanović', 'Vojnovič': 'Vojnović', 'Marušič': 'Marušić', 'Saranovič': 'Šaranović',
       'Dapčevič': 'Dapčević', 'Brajovič': 'Brajović', 'Tanaskovič': 'Tanasković', 'Božovič': 'Božović',
       'Jevtič': 'Jevtić', 'Došenovič': 'Došenović', 'Jovanovič': 'Jovanović', 'Natizone': 'Natisone',
       'Dob rovi j e': 'Dobrovlje', 'Stefan Pavšič': 'Štefan Pavšič', 'KNO.l': 'KNOJ',
       'Lojze Žokalj': 'Alojz Žokalj', 'Cubrič': 'Čubrić'}
# the footnote under the Glavni štab: the assistants of its political commissar
FOOTNOTE = [('dr Jože Brilej', 'Bolko'), ('Štefan Pavšič — Jurij Dobravec', ''), ('Lojze Vrhovec — Slavko Grum', '')]


def fixed(t: str) -> str:
    for a, b in FIX.items():
        t = re.sub(rf'(?<!\w){re.escape(a)}(?!\w)', b, t)
    return t


def lines() -> list[dict]:
    out = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            ws = sorted(viewer_words(page), key=lambda w: w['bottom'])
            rows = []
            for w in ws:
                if rows and abs(w['bottom'] - rows[-1][0]['bottom']) < 3:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            for r in rows:
                r.sort(key=lambda w: w['x0'])
                out.append({'text': fixed(' '.join(w['text'] for w in r).strip()), 'page': pno,
                            'x': round(r[0]['x0'], 1), 'y': round(min(w['top'] for w in r), 1)})
    return out


def name_of(name: str) -> dict:
    """"Franc Leskošek Luka", "Jaka Avšič — Branko Hrast", "dr Aleš Bebler Primož", "Boris Krajger Janez (Kraigher)" """
    title = 'dr ' if name.startswith('dr ') else ''
    name = name[len(title):].strip()
    also = re.findall(r'\(([^)]+)\)', name)
    name = re.sub(r'\s*\([^)]*\)', '', name)
    alias = ''
    if ' — ' in name:
        name, alias = name.split(' — ', 1)
    words = name.split()
    first, last = words[0], words[1] if len(words) > 1 else ''
    nick = ' '.join(words[2:]) or alias
    return {'first': first, 'last': last, 'nick': nick, 'alias': alias, 'also': also, 'title': title}


def main():
    people, order = {}, []
    group, unit, last_post = '', '', None
    for ln in lines():
        t = ln['text']
        if t.startswith(('Prilog', 'SPISAK')) or re.fullmatch(r'\d{3}\.?|!', t):
            continue
        if t in GROUPS:
            group, unit, last_post = t, (t if not GROUPS[t] else ''), None
            continue
        if t.startswith('— '):
            sub = t[2:].strip()
            if group in ('Korpusi', 'Divizije', 'Grupe partizanskih odreda') and not sub.startswith(NOT_ORDINAL):
                unit = GROUPS[group].format(sub)
            elif group == 'Operativne zone':
                m = re.match(r'(\w+),?\s*(\(.*\))?', sub)
                unit = f"{m.group(1)} {m.group(2) + ' ' if m.group(2) else ''}operativna zona" if sub != 'Primorska' else 'Primorska operativna zona'
            elif group in ('Pokrajinski štabovi', 'Operativni štabovi'):
                unit = GROUPS[group].format(sub)
            else:
                unit = sub
            last_post = None
            continue
        if t.startswith('«') or ln['page'] == 1 and ln['y'] > 600:
            continue                                    # the footnote (read below)
        m = DUTY.match(t)
        if not m:
            if last_post:                                   # a line run on: "Črnomelj.", "1943 — 26. 3. 1944)", "Up- / niška pl."
                last_post['text'] = re.sub(r'(\w)- (?=[a-zčćžšđ])', r'\1', last_post['text'] + ' ' + t)
            continue
        duty = next(d for p, d in DUTIES if re.fullmatch(p, m.group(1)))
        rest = m.group(2)
        parts = re.split(r',\s*|\s(?=(?:\d|poč\.|kr\.|sr\.|dr\. pol|prva pol|febr|kraj|dee|mart|apr))', rest, 1)
        n = name_of(parts[0].strip())
        key = (n['first'], n['last'])
        if key not in people:
            people[key] = {**n, 'posts': [], 'page': ln['page'], 'x': ln['x'], 'y': ln['y']}
            order.append(key)
        p = people[key]
        p['nick'] = p['nick'] or n['nick']
        p['alias'] = p['alias'] or n['alias']
        last_post = {'unit': unit or group, 'duty': duty, 'text': parts[1].strip() if len(parts) > 1 else ''}
        p['posts'].append(last_post)
    for name, nick in FOOTNOTE:
        n = name_of(name)
        key = (n['first'], n['last'])
        if key not in people:
            people[key] = {**n, 'nick': n['nick'] or nick, 'posts': [], 'page': 1, 'x': 46.0, 'y': None}
            order.append(key)
        people[key]['posts'].append({'unit': 'Glavni štab NOV i PO Slovenije', 'duty': 'pomoćnik političkog komesara',
                                     'text': '1. 10. 1942 — 23. 5. 1943 (napomena)'})
    recs = []
    for no, key in enumerate(order, 1):
        p = people[key]
        posts = '; '.join(f"{q['unit']}, {q['duty']}, {q['text'].rstrip('.')}" for q in p['posts'])
        printed = f"{p['title']}{p['first']} {p['last']}" + (f" — {p['alias']}" if p['alias'] else f" {p['nick']}" if p['nick'] else '')
        rec = {'soldier_id': f'{PREFIX}{no:06d}', 'name': f"{p['last']} {p['first']}" + (f" — {p['nick']}" if p['nick'] else ''),
               'last_name': p['last'], 'first_name': p['first'], 'also': p['also'], 'nick': p['nick'],
               'fathers_name': '', 'birth_year': '', 'born_in': '', 'death_year': '', 'survived': False, 'units': [],
               'no': no, 'list': TITLE, 'additional_info': f'{TITLE}: {printed}: {posts}.',
               'source_page': p['page'] + BOOK_PAGE, 'pdf_file': PDF, 'pdf_page': p['page'], 'pdf_x': p['x']}
        if p['y'] is not None:
            rec['pdf_y'] = p['y']
        # in his post on the war's last days: he lived through it
        # (not Evgen Matejka, who fell on 3 May 1945)
        rec['survived'] = not any('Pog.' in q['text'] for q in p['posts']) and \
            any(re.search(r'—\s*(?:\d{1,2}\.\s*)?5\.\s*1945', q['text']) for q in p['posts'])
        fell = next((q for q in p['posts'] if re.search(r'\bPog\.', q['text'])), None)
        if fell:
            rec['death_place'] = re.split(r'\bPog\.\s*', fell['text'])[1].strip(' .')
            years = re.findall(r'19[34]\d', re.split(r'\bPog\.', fell['text'])[0])
            rec['death_year'] = years[-1] if years else ''
        recs.append(rec)
    stats = entry_boxes.fill_boxes(recs)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(recs)} men, {sum(len(people[k]['posts']) for k in order)} posts -> {OUT.name}")
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for r in recs:
        print(f"  {r['no']:3} {r['name']} | {r.get('death_year')} {r.get('death_place', '')} | {r['additional_info'][len(TITLE) + 2:][:150]}")


if __name__ == '__main__':
    main()
