"""
Općina Gornje Dubrave (Zbornik Historijskog arhiva u Karlovcu, knj. 16; znaci.org 00003/681, the chapter 681_2.pdf) → website/public/pdfs/hak-16-gornje-dubrave.pdf: a book across
units, read by _karlovac_lists.py.

The site's PDF holds the chapter's PDF pp. 1-11, "Pali borci s područja općine Gornje Dubrave 1941-1945.", two columns of numbered bios by općina and village, the names in small letters, Surname Father Given: "1. Dimić Miće Petar, 1919, seljak, Srbin. Stupio u NOB 1942. ...".
The list ends on its last page, where the victims of fascist terror and of the war begin (they stay out).

Output: data-extraction/znaci/hak-16-gornje-dubrave-entries.json, IDs 9030xxxxxx.
Usage: python data-extraction/parse_hak_16_gornje_dubrave.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-16-gornje-dubrave.pdf',
    'prefix': '9030',
    'lists': [('fallen', range(1, 12), 2)],
    'opcina': 'Gornje Dubrave',           # one općina: the list prints only its villages
    'names': 'title',
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
