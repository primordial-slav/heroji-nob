"""
Kotar Donji Lapac u narodnooslobodilačkom ratu 1941-1945. (Zbornik Historijskog arhiva u Karlovcu, knj. 14; znaci.org
00003/458) → website/public/pdfs/hak-14-donji-lapac.pdf: a book across units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 1039-1090 (book pp. 1041-1094; the site's p. 28 is a spread of two book pages,
whose page numbers the reader leaves out), "Pali borci s područja kotara Donji Lapac 1941-1945. godine", two
columns of numbered bios by općina (Donji Lapac, Srb) and village, the names in small letters: "16. Glušica Vuje Spaso
Pajo, 1920. Srbin. Stupio u NOB jula 1941, ..." (Surname Father Given, then what he was called). The victims of fascist
terror and of the war (pp. 1091-1135) and those who died of typhus (pp. 1136-1193) stay out; the volume prints no list
of the spomenica's holders.

Output: data-extraction/znaci/hak-14-donji-lapac-entries.json, IDs 9009xxxxxx.
Usage: python data-extraction/parse_hak_14_donji_lapac.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-14-donji-lapac.pdf',
    'prefix': '9009',
    'lists': [('fallen', range(1, 53), 2)],
    'names': 'title',
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
