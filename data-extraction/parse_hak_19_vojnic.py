"""
Kotar Vojnić u narodnooslobodilačkoj borbi i socijalističkoj revoluciji (Zbornik Historijskog arhiva u Karlovcu, knj. 19; znaci.org 00003/644, the chapter 644_2.pdf) → website/public/pdfs/hak-19-vojnic.pdf: a book across
units, read by _karlovac_lists.py.

The site's PDF holds the chapter's PDF pp. 1-55, "Pali borci s područja kotara Vojnić 1941-1945.", two columns of numbered bios by općina and village, the names in capitals: "1. KESER Bože ĐURO, 1924, seljak, Srbin. Stupio u NOV 5. 12. 1942. Borac 2. brig. 8. div. ...".
The victims of fascist terror and of the war (p. 56 on) and those who died of typhus stay out.

Output: data-extraction/znaci/hak-19-vojnic-entries.json, IDs 9018xxxxxx.
Usage: python data-extraction/parse_hak_19_vojnic.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-19-vojnic.pdf',
    'prefix': '9018',
    'lists': [('fallen', range(1, 56), 2)],
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
