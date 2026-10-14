"""
Veseljko Huljić, *Vis 1941-1945* (Split, 1979; znaci.org 00003/804, the whole book's PDF pp. 573-577 →
website/public/pdfs/vis-zrtve-nob.pdf, book pp. 516-520): pregled g), "Žrtve tijekom NOB-e", the names on the
memorial plaques of the Vis islands, a book across units: its entries are added to the records of the soldiers it
describes (scripts/match_references.py), the rest go to Ostali borci.

Three places, each a list in two columns, numbered, surname, the father in the genitive and the given name, what he was
called after a hyphen: "1. Bakotić Živana Budimir", "11. Božanić Franje Nikola- / -Gregolevanat", a wife's husband
after "ž." ("Božanić ž. Andrije Zlatica-Kastriotić"). Vis and its villages: "Poginuli u borbama" (112) and the died of
wounds and illness got in the NOB (4); Komiža, the island of Biševo and Oključna: the fallen (96) and the died of wounds
(8); the villages of the plateau under Hum, Podšpilje and the rest (35). Who goes in: the fallen in battle and the died
of wounds. The book says the Vis list holds the ten hostages the Italians shot on 20 August 1943 too (its part one
names them, p. 157 of the PDF); they are left out (HOSTAGES: the plaque gives two of them other fathers than part one,
"Pečarević Petra Ivan" and "Radišić Nikole Nikola", the list's only Ivan Pečarević and Nikola Radišić). Komiža's ten
hostages and the two who died in Ustaša prisons stand in lists of their own and stay out.

znaci re-typeset the book from its OCR, so the page shows its slips: numbers moved to the other column's line end
("Zamberlin Pavla Marko-Belica 67.") or read as letters ("gg", "qc:", "S."), specks ("i« 16. nr Marinković • i"), lost
carons ("Bozanic", "Simuna") and broken words ("Podu je", "SviHać vicka"). Numbers and specks are dropped, the names
read back from the site's spellings (a surname or given name the site doesn't know, where one with the caron is known)
and from LINE (read from the page images).

Output: data-extraction/znaci/vis-zrtve-nob-entries.json (IDs 9071xxxxxx, by the entry's place among all the lists'
names, the hostages counted).
Usage: python data-extraction/parse_vis_zrtve_nob.py
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
import parse_ofanziva_1942 as ofz  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'vis-zrtve-nob.pdf'
OUT = HERE / 'znaci' / 'vis-zrtve-nob-entries.json'
PREFIX = '9071'
BOOK_PAGE = {p: 515 + p for p in range(1, 6)}
# the text layer's slips, read from the page images
LINE = {'Podu je Nikole': 'Poduje Nikole', 'Luci je Frane': 'Lucije Frane', 'SviHać vicka': 'Sviličić Vicka',
        'iSvilicic': 'Sviličić', 'Salvestro\\': 'Salvestrov', "Ivana 'Nikola": 'Ivana Nikola',
        'Tornić Franje': 'Tomić Franje', 'Zivana': 'Živana', 'Simuna': 'Šimuna', 'Bozanic': 'Božanić',
        'Barbaric': 'Barbarić'}
HOSTAGES = {('Ilić', 'Ante', 'Miho'), ('Mandaković', 'Lucije', 'Frane'), ('Pečarević', 'Ivana', 'Ivan'),
            ('Puhalović', 'Šimuna', 'Mate'), ('Radica', 'Marina', 'Ivan'), ('Radišić', 'Mladena', 'Nikola'),
            ('Restović', 'Kuzme', 'Josip'), ('Ruljančić', 'Nikole', 'Jakov'), ('Svičarević', 'Nikole', 'Grgo'),
            ('Tomić', 'Mate', 'Dušan')}
MOTHER = {'Katarina'}                 # "Felanda Katarina Ivan-Tvičica": a mother's name where the father's stands
PLACES = [(r'^1\. ZA MJESTO VIS', 'Vis'), (r'^2\. ZA MJESTO KOMI', 'Komiža'), (r'^a\) KOMI', 'Komiža'),
          (r'^b\) O\. BIŠEVO', 'Biševo'), (r'^c\) OKLJUČNA', 'Oključna'), (r'^3\. ZA SELA', 'Podšpilje'),
          (r'^Strijeljani kao taoci .*iz Komiže', 'Komiža')]     # Komiža's died of wounds follow its hostages
LISTS = [(r'^Poginuli u borbama|^3\. ZA SELA', 'poginuli u borbama'),
         (r'^Umrli od rana', 'umrli od rana i bolesti zadobivenih u NOB-i'),
         (r'^Strijeljani kao taoci|^Umoreni u ustaškom', None)]
JUNK = re.compile(r"^(?:['’]?\d{1,3}[.,]?|gg|qc:|S\.)$")


def page_lines(page) -> tuple[list[list[dict]], float]:
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    a, b = min(w['x0'] for w in words), max(w['x1'] for w in words)
    width = float(page.width)
    gutter = entry_boxes.find_gutter(words, width, (a + .35 * (b - a)) / width, (a + .65 * (b - a)) / width)
    return entry_boxes._cluster(words, 4), gutter


def kind(text: str) -> str:
    """'entry' (names), 'head' (a heading or prose: a list's band ends) or 'skip' (the page number)"""
    if re.fullmatch(r'\d{3}', text):
        return 'skip'
    if re.search(r'\b[a-zčćšžđ]{3,}\b', text) or text.startswith(('(', '»', 'Prema')) or re.match(r'^[a-c]\)', text):
        return 'head'
    letters = re.sub(r'[^A-Za-zČĆŠŽĐčćšžđ]', '', text)
    if len(letters) > 5 and sum(c.isupper() for c in letters) > .8 * len(letters):
        return 'head'                                              # "VISKE OPĆINE", "ŽRTVE TIJEKOM NOB-e"
    return 'entry'


def columns(band: list[list[dict]], gutter: float) -> list[list[dict]]:
    """A band's lines as column lines, the left column first: {text, x0, x1, top, bottom, no}"""
    out = []
    for side in (0, 1):
        ws = [w for ln in band for w in ln if (w['x0'] >= gutter) == bool(side)]
        for ln in entry_boxes._cluster(ws, 4):
            no = re.match(r'^(\d{1,3})\.$', ln[0]['text'])
            real = [w for w in ln if not JUNK.match(w['text']) and (re.search(r'[A-ZČĆŠŽĐ]', w['text'])
                                                                     or w['text'] == 'ž.')]
            # the slips mended before the specks go ("SviHać vicka" has a given name in small letters)
            text = fix(' '.join(w['text'] for w in ln if not JUNK.match(w['text'])))
            text = ' '.join(t for t in text.split() if re.search(r'[A-ZČĆŠŽĐ]', t) or t == 'ž.')
            if real:
                out.append({'text': text, 'x0': ln[0]['x0'],
                            'x1': max(w['x1'] for w in real), 'top': min(w['top'] for w in ln),
                            'bottom': max(w['bottom'] for w in real), 'no': int(no.group(1)) if no else None})
    return out


def fix(text: str) -> str:
    for a, b in LINE.items():
        text = text.replace(a, b)
    return text


def spell(word: str, part: str) -> str:
    """A name the site doesn't know as printed, where it knows one with a caron the page lost ("Siljić")"""
    if '-' in word:
        return '-'.join(spell(p, part) for p in word.split('-'))
    if ofz._spell[part].get(word.upper().translate(ofz.FOLD), {}).get(word.upper()):
        return word                                                # Suić of Komiža, not the Šuić of Kladuša
    n, best = ofz.known(word, part)
    return ofz.title(best) if n >= 3 and best else word


def read() -> list[dict]:
    entries, place, which = [], None, None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines, gutter = page_lines(page)
            band = []

            def flush():
                for cl in columns(band, gutter):
                    t = fix(cl['text'])
                    if entries and entries[-1]['page'] == pno and (t.startswith('-') or entries[-1]['text'].endswith('-')) \
                            and entries[-1]['side'] == (cl['x0'] >= gutter):
                        e = entries[-1]                            # "Nikola-" / "-Gregolevanat"
                        e['text'] = e['text'].rstrip('-') + '-' + t.lstrip('-')
                        e['x1'], e['bottom'] = max(e['x1'], cl['x1']), cl['bottom']
                        continue
                    entries.append({'text': t, 'place': place, 'list': which, 'page': pno, 'no': cl['no'],
                                    'side': cl['x0'] >= gutter, 'x0': cl['x0'], 'x1': cl['x1'], 'top': cl['top'],
                                    'bottom': cl['bottom']})
                band.clear()

            for ln in lines:
                text = ' '.join(w['text'] for w in ln)
                k = kind(fix(text))
                if k == 'entry':
                    band.append(ln)
                    continue
                flush()
                for rx, p in PLACES:
                    if re.match(rx, text):
                        place = p
                for rx, lst in LISTS:
                    if re.match(rx, text):
                        which = lst
            flush()
    return entries


def name(text: str) -> dict:
    t = text.split()
    last, rest = spell(t[0], 'last'), t[1:]
    husband = father = ''
    if rest[0] == 'ž.':
        husband, rest = rest[1], rest[2:]                          # "ž. Andrije": the wife of Andrija
    else:
        father, rest = rest[0], rest[1:]
    given, _, nick = rest[0].partition('-')
    nick = ' '.join(filter(None, [nick, *rest[1:]]))
    return {'last_name': last, 'fathers_name': '' if father in MOTHER else father, 'husband': husband,
            'first_name': spell(given, 'first'), 'nick': nick}


def main():
    ofz.corpus()
    recs, hostages = [], set()
    for pos, e in enumerate(read(), 1):
        if not e['list']:
            continue                                               # the hostages of Komiža, the dead in prison
        n = name(e['text'])
        key = (n['last_name'], n['fathers_name'], n['first_name'])
        if e['place'] == 'Vis' and e['list'].startswith('poginuli') and key in HOSTAGES:
            hostages.add(key)
            continue
        printed = ' '.join([n['last_name'], *e['text'].split()[1:]])
        if n['first_name'] != e['text'].split()[2 if not n['husband'] else 3].partition('-')[0]:
            printed = printed.replace(e['text'].split()[2 if not n['husband'] else 3].partition('-')[0],
                                      n['first_name'], 1)
        recs.append({'soldier_id': f'{PREFIX}{pos:06d}',
                     'name': f"{n['last_name']} {n['first_name']}" + (f" — {n['nick']}" if n['nick'] else ''),
                     'last_name': n['last_name'], 'first_name': n['first_name'], 'also': [], 'nick': n['nick'],
                     'fathers_name': n['fathers_name'], 'birth_year': '', 'born_in': '', 'death_year': '',
                     'death_date': '', 'death_type': 'poginuo' if e['list'].startswith('poginuli') else 'umro',
                     'survived': False, 'units': [], 'home': e['place'], 'no': e['no'],
                     'list': f"Žrtve tijekom NOB-e, {e['place']}: {e['list']}",
                     'additional_info': f"Žrtve tijekom NOB-e, {e['place']}, {e['list']}: {printed}.",
                     'source_page': BOOK_PAGE[e['page']], 'pdf_file': PDF, 'pdf_page': e['page'],
                     'pdf_x': round(e['x0'], 1), 'pdf_y': round(e['top'], 1), 'pdf_x_end': round(e['x1'], 1),
                     'pdf_y_end': round(e['bottom'], 1)})
    assert hostages == HOSTAGES, HOSTAGES - hostages
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)} ({len(hostages)} hostages of Vis left out)')
    from collections import Counter
    print(Counter((r['home'], r['death_type']) for r in recs))
    for r in recs:
        print(f"  {r['soldier_id'][4:]} p{r['pdf_page']} {r['no'] or '-':>3} {r['additional_info']}")


if __name__ == '__main__':
    main()
