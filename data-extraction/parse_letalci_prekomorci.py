"""
Rafael Perhauc, *Letalci prekomorci* (Ljubljana 1968; znaci.org 00003/786, the whole book's PDF pp. 319-322 →
website/public/pdfs/letalci-prekomorci-kader.pdf, book pp. 322-325): "Seznam vodilnega kadra prve in druge lovske
eskadrilje ter letalskega detašmana NOVJ v Alžiriji", the leaders of the 1. and 2. eskadrila NOVJ (RAF 352 and 351
Squadrons, unit 139), of the NOVJ's air detachment in Algeria (Maison Blanche, Boufarik) and of the first air regiment,
a book across units: its entries are added to the records of the men it names, the rest go to Ostali borci.

Tables of a rank and a name ("major PROTIĆ Mileta") beside a duty and its days, which the text layer gives as two runs,
the names and then the duties; each table's rows pair in order (checked on the page images), so the posts are typed here
(`POSTS`) and each name's place is found on its page. A man in several posts is one entry with each of them.

Output: data-extraction/znaci/letalci-prekomorci-kader-entries.json (IDs 9076xxxxxx, by each man's first post).
Usage: python data-extraction/parse_letalci_prekomorci.py
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
from pdf_coords import viewer_words  # noqa: E402

PDF = 'letalci-prekomorci-kader.pdf'
OUT = HERE / 'znaci' / 'letalci-prekomorci-kader-entries.json'
PREFIX = '9076'
BOOK_PAGE = {1: 322, 2: 323, 3: 324, 4: 325}
E1, E2 = '1. lovska eskadrila NOVJ', '2. lovska eskadrila NOVJ'
MB, BF1, BF2 = ('Letalski detašman NOVJ v Alžiriji, Maison Blanche',
                'Letalski detašman NOVJ v Alžiriji, Boufarik do 15. novembra 1944',
                'Letalski detašman NOVJ v Alžiriji, Boufarik od 15. novembra 1944 do 22. marca 1945')
POLK = '1. letalski polk'
# (page, unit, rank, surname as printed, given name, duty)
POSTS = [
    (2, E1, 'major', 'PROTIĆ', 'Mileta', 'komandant eskadrilje od začetka do 19. 11. 1944'),
    (2, E1, 'poročnik', 'ŽOIĆ', 'Hinko', 'komandant eskadrilje od 19. 11. 1944 do konca vojne'),
    (2, E1, 'major', 'JOVANOVIČ', 'Ratko', 'komandir »A« oddelka od začetka do 4. 10. 1944'),
    (2, E1, 'major', 'KRAUS', 'Branko', 'komandir »A« oddelka od 4. 10. 1944 do 22. 11. 1944'),
    (2, E1, 'kapetan', 'PAJIĆ', 'Nedeljko', 'komandir »A« oddelka od 22. 11. 1944 do konca vojne'),
    (2, E1, 'poročnik', 'SRDANOVIĆ', 'Milan', 'zastopnik komandirja »A« oddelka do konca vojne'),
    (2, E1, 'major', 'POPOV', 'Arkadije', 'komandir »B« oddelka od začetka do 16. 10. 1944'),
    (2, E1, 'major', 'IVANIŠEVIČ', 'Djuro', 'komandir »B« oddelka od 16. 10. 1944 do konca vojne'),
    (2, E1, 'poročnik', 'DELIĆ', 'Milan', 'zastopnik komandirja »B« oddelka do konca vojne'),
    (2, E1, 'kapetan', 'LOLIĆ', 'Franjo', 'tehnični oficir'),
    (2, E1, 'major', 'NAJBERGER', 'Hubert', 'adjutant'),
    (2, E1, 'major', 'ZOBUNDŽIJA', 'Ladislav', 'obveščevalni oficir'),
    (2, E1, 'poročnik', 'DVORNIK', 'Mirko', 'politkomisar'),
    (2, E1, 'poročnik', 'ZELJKOVIĆ', 'Djuro', 'zastopnik komisarja'),
    (2, E1, 'podporočnik', 'GATI', 'Jožko', 'vodja SKOJ'),
    (2, E1, 'vodnik', 'PERAT', 'Janko', 'vodja SKOJ'),
    (2, E1, 'kapetan', 'FERRI', 'Ivo', 'intendant'),
    (2, E1, 'podporočnik', 'PODBEVŠEK', 'Franc', 'vodja avtomobilske sekcije'),
    (2, E1, 'poročnik', 'MLADENOVIČ', 'Mika', 'vodja signalne sekcije'),
    (2, E1, 'podporočnik', 'GATI', 'Jožko', 'vodja električarjev'),
    (2, E1, 'major', 'NAJBERGER', 'Hubert', 'predsednik kulturnoprosvetnega odbora do 31. 12. 1944'),
    (2, E1, 'podporočnik', 'GATI', 'Jožko', 'predsednik kulturnoprosvetnega odbora od 1. 1. 1945 do konca vojne'),
    (3, E2, 'kapetan', 'CENIČ', 'Aleksander', 'komandant eskadrilje'),
    (3, E2, 'kapetan', 'MARINOVIC', 'Miloš', 'komandir »A« oddelka'),
    (3, E2, 'kapetan', 'ZDRAJEVSKI', 'Cirilo', 'zastopnik komandirja »A« oddelka'),
    (3, E2, 'poročnik', 'MAJCEN', 'Branivoj', 'komandir »B« oddelka'),
    (3, E2, 'kapetan', 'JEZ', 'Franjo', 'zastopnik komandirja »B« oddelka'),
    (3, E2, 'kapetan', 'RADALJAC', 'Rudi', 'tehnični oficir'),
    (3, E2, 'kapetan', 'FILIPIČ', 'Rihard', 'adjutant'),
    (3, E2, 'major', 'KOCIJANČIČ', 'Maks', 'obveščevalni oficir'),
    (3, E2, 'kapetan', 'GRGIČ', 'Miro', 'intendant'),
    (3, E2, 'kapetan', 'VALES', 'Mirko', 'vodja signalne sekcije'),
    (3, E2, 'vodnik', 'ŽERJAL', 'Oskar', 'vodja avtomobilske sekcije'),
    (3, E2, 'borec', 'RUDIČ', 'Jakov', 'politkomisar'),
    (3, MB, 'major', 'HUBMAJER', 'Danilo', 'komandant od 2. 6. do 10. 9. 1944, komandi RAF, odgovoren tudi za Boufarik'),
    (3, MB, 'kapetan', 'PERHAUC', 'Rafael', 'komandant od 10. 9. do 15. 11. 1944'),
    (3, MB, 'kapetan', 'ČURGUS', 'Ljubiša', 'namestnik komandanta od 2. 6. do 15. 11. 1944'),
    (3, MB, 'podporočnik', 'TRTICA', 'Stevo', 'administrativni oficir od 20. 6. do 15. 11. 1944'),
    (3, MB, 'kapetan', 'PERHAUC', 'Rafael', 'delavnica za motorje »Merlin« od 20. 6. do 15. 11. 1944'),
    (3, MB, 'podporočnik', 'RUPNIK', 'Zdenko', 'elektrotehnični oddelek od 2. 6. do 15. 11. 1944'),
    (3, MB, 'podporočnik', 'KOS', 'Zvonko', 'delavnica motorjev »Pratt & Whitney« od 12. 7. do 15. 11. 1944'),
    (3, MB, 'podporočnik', 'KASTELIC', 'Tone', 'delavnica za avtoremonte od 20. 6. do 15. 11. 1944'),
    (3, MB, 'poročnik', 'RENAC', 'Milan', 'sekcija za oborožitev od 12. 7. do 15. 11. 1944'),
    (3, MB, 'podporočnik', 'ILIČ', 'Ivan', 'montaža letal, hangar »B« od 11. 5. do 15. 11. 1944'),
    (3, MB, 'major', 'HUBMAJER', 'Danilo', 'montaža letal, hangar »B« od 2. 6. do 10. 9. 1944'),
    (3, BF1, 'kapetan', 'RODIČ', 'Mile', 'namestnik komandanta od 20. 6. do 15. 11. 1944'),
    (4, BF2, 'poročnik', 'ZRILIĆ', 'Milan', 'motorska delavnica od 12. 7. do 15. 11. 1944'),
    (4, BF2, 'poročnik', 'DIBATISTA', 'Henrik', 'montaža letal od 12. 7. do 15. 11. 1944'),
    (4, BF2, 'podporočnik', 'KOS', 'Zvonko', 'motorska delavnica od 20. 6. do 12. 7. 1944 (nato v Maison Blanche)'),
    (4, BF2, 'podporočnik', 'DRAGICEVIĆ', 'Ivo', 'motorska delavnica od 2. 6. do 15. 11. 1944'),
    (4, BF2, 'major', 'PERHAUC', 'Rafael', 'komandant od 15. 11. 1944 do 22. 3. 1945'),
    (4, BF2, 'poročnik', 'KASTELIC', 'Tone', 'motorska delavnica od 15. 11. 1944 do 22. 3. 1945'),
    (4, BF2, 'poročnik', 'DRAGICEVIĆ', 'Ivo', 'motorska delavnica od 15. 11. 1944 do 22. 3. 1945'),
    (4, POLK, 'komandant', 'POLJANEC', 'Srečko', 'komandant'),
    (4, POLK, 'politkomisar', 'DVORNIK', 'Mirko', 'politkomisar'),
]


def title(w: str) -> str:
    return '-'.join(p[:1] + p[1:].lower() for p in w.split('-'))


def main():
    found: dict[tuple, list] = {}
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for w in viewer_words(page, keep_blank_chars=False):
                found.setdefault((pno, w['text'].strip(',')), []).append(w)
    used: dict[tuple, int] = {}
    people: dict[str, dict] = {}
    for page, unit, rank, last, given, duty in POSTS:
        k = (page, last)
        ws = found.get(k, [])
        i = used.get(k, 0)
        assert ws, (page, last)
        w = ws[min(i, len(ws) - 1)]                                 # the n-th time the surname stands on its page
        used[k] = i + 1
        name = f'{title(last)} {given}'
        e = people.setdefault(name, {'last': title(last), 'given': given, 'posts': [], 'rank': rank, 'page': page,
                                     'x0': w['x0'], 'top': w['top'], 'x1': w['x1'], 'bottom': w['bottom']})
        e['posts'].append(f'{unit}, {duty}')
    recs = []
    for no, e in enumerate(people.values(), 1):
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f"{e['last']} {e['given']}", 'last_name': e['last'],
                     'first_name': e['given'], 'also': [], 'nick': '', 'fathers_name': '', 'birth_year': '',
                     'born_in': '', 'death_year': '', 'death_date': '', 'survived': True,
                     'units': [139] if any(p.startswith(('1. lovska', '2. lovska')) for p in e['posts']) else [],
                     'no': no, 'list': 'Seznam vodilnega kadra eskadrilj in letalskega detašmana NOVJ',
                     'additional_info': f"Vodilni kader letalcev prekomorcev: {e['rank']}; {'; '.join(e['posts'])}.",
                     'source_page': BOOK_PAGE[e['page']], 'pdf_file': PDF, 'pdf_page': e['page'],
                     'pdf_x': round(e['x0'], 1), 'pdf_y': round(e['top'], 1),
                     # the surname of his first post (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(e['x1'], 1), 'pdf_y_end': round(e['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(POSTS)} posts, {len(recs)} men -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:3} {r['name']}: {r['additional_info'][36:170]}")


if __name__ == '__main__':
    main()
