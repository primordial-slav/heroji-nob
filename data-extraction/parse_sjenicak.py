"""
Mile Mrkalj, *Sjeničak, kronika kordunaškog sela* (Historijski arhiv u Karlovcu, 1980; znaci.org 00003/640) →
website/public/pdfs/sjenicak.pdf: a book across units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 330-338 and 385-389, two of its lists, one column of numbered bios under each
village (Donji, Gornji and Lasinjski Sjeničak), Surname in capitals, father, GIVEN:
    "Pali i umrli borci 1941 — 1945." (pp. 1-9): "1. CABRAJA Sime GOJKO, 1925, stupio u NOV 1. 1. 1943, poginuo kao
        borac 2. brigade 8. divizije 20. 10. 1944. kod Rakovice.";
    "Nosioci »Partizanske spomenice 1941«" (pp. 10-14), the survivors among them with their duties.
Its lists of the victims of fascist terror (pp. 339-370) and of those who died of typhus and cold (pp. 371-384) stay out.
The villages made up the wartime općina Sjeničak (kotar Vrginmost). The printer's signature at a sheet's foot ("22
SJENIČAK") is dropped. The OCR reads the names' ć as č ("ROKNIČ", "TEPŠIČ"; no name of these villages ends in -ič) and
loses a few carons the corpus doesn't restore (`FIX`).

Output: data-extraction/znaci/sjenicak-entries.json, IDs 9031xxxxxx.
Usage: python data-extraction/parse_sjenicak.py [--sample N]
"""
import json
import re

from _karlovac_lists import HERE, main

BOOK = {
    'pdf': 'sjenicak.pdf',
    'prefix': '9031',
    'lists': [('fallen', range(1, 10), 1), ('spomenica', range(10, 15), 1)],
    'opcina': 'Sjeničak',                 # one općina: the lists print only its villages
    'drop': r'\d{1,3}\s+SJENI[ČC]AK\b',
    'heads': {},
}
# names as the page prints them, read from the scan
FIX = {'Bozo': 'Božo', 'Dužan': 'Dušan', 'Tepsić': 'Tepšić', 'Manojlovic-Pejic': 'Manojlović-Pejić', 'Miče': 'Miće'}
FATHER = {('Cabraja', 'Milica', 'Rade'): 'Milića'}     # the spomenica's "CABRAJA Milica RADE": the OCR lost a caron


def fixed(word: str) -> str:
    word = FIX.get(word, word)
    return re.sub(r'ič$', 'ić', word)


if __name__ == '__main__':
    main(BOOK)
    path = HERE / 'znaci' / 'sjenicak-entries.json'
    recs = json.loads(path.read_text(encoding='utf-8'))
    for r in recs:
        old = [r['last_name']] + r['also'] + [r['fathers_name'], r['first_name']]
        r['last_name'], r['first_name'] = fixed(r['last_name']), fixed(r['first_name'])
        r['also'] = [fixed(w) for w in r['also']]
        r['fathers_name'] = FATHER.get((r['last_name'], r['fathers_name'], r['first_name']), fixed(r['fathers_name']))
        new = [r['last_name']] + r['also'] + [r['fathers_name'], r['first_name']]
        for a, b in zip(old, new):
            if a != b:
                r['name'] = re.sub(rf'(?<!\w){re.escape(a)}(?!\w)', b, r['name'], count=1)
    path.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
