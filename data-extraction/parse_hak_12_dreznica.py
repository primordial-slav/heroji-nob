"""
Partizanska Drežnica (Zbornik Historijskog arhiva u Karlovcu, knj. 12; znaci.org 00003/678, the chapter 678_2.pdf) → website/public/pdfs/hak-12-dreznica.pdf: a book across
units, read by _karlovac_lists.py.

The site's PDF holds the chapter's PDF pp. 1-12, "Pali borci s područja općine Drežnica 1941-1945.", two columns of numbered bios by općina and village, the names in capitals: "1. BOCA Đure SMILJA, 1926, radnica, Srpkinja. Stupila u NOB 1942, ...".
The victims of fascist terror and of the war (p. 13 on) stay out.

Output: data-extraction/znaci/hak-12-dreznica-entries.json, IDs 9029xxxxxx.
Usage: python data-extraction/parse_hak_12_dreznica.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-12-dreznica.pdf',
    'prefix': '9029',
    'lists': [('fallen', range(1, 13), 2)],
    'opcina': 'Drežnica',                 # one općina: the list prints only its villages
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
