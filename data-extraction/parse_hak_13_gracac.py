"""
Kotar Gračac u narodnooslobodilačkom ratu 1941-1945. (Zbornik Historijskog arhiva u Karlovcu, knj. 13; znaci.org
00003/638) → website/public/pdfs/hak-13-gracac.pdf: a book across units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 914-962 (book pp. 917-965), "Pali borci s područja kotara Gračac 1941-1945.",
two columns of numbered bios by općina and village, the names in capitals: "1. BANDIĆ Rade PAJO, 1905, B. Rudopolje,
seljak, Srbin. Ustanik, stupio u NOV maja 1942. ..." The list ends on its last page, where the victims of fascist
terror and of the war begin (they stay out, with those who died of typhus); a page of photos lies between.

Output: data-extraction/znaci/hak-13-gracac-entries.json, IDs 9010xxxxxx.
Usage: python data-extraction/parse_hak_13_gracac.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-13-gracac.pdf',
    'prefix': '9010',
    'lists': [('fallen', range(1, 50), 2)],
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
