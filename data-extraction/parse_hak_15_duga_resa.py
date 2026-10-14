"""
Duga Resa: radovi iz dalje prošlosti, NOB-e i socijalističke izgradnje (Zbornik Historijskog arhiva u Karlovcu, knj. 15; znaci.org 00003/616, the chapter 616_3.pdf) → website/public/pdfs/hak-15-duga-resa.pdf: a book across
units, read by _karlovac_lists.py.

The site's PDF holds the chapter's PDF pp. 7-37 (Đorđe Travica's lists), "Pali borci s područja sadašnje općine Duga Resa", two columns of numbered bios by općina and village, the names in capitals, which the OCR at times spaces out ("M A L IĆ Đ ure M IL IĆ"): "1. GOJAK Janka MARKO, 1903, seljak, Hrvat. ...".
The victims of fascist terror (p. 38 on) and those who died of typhus stay out.

Output: data-extraction/znaci/hak-15-duga-resa-entries.json, IDs 9028xxxxxx.
Usage: python data-extraction/parse_hak_15_duga_resa.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-15-duga-resa.pdf',
    'prefix': '9028',
    'lists': [('fallen', range(1, 32), 2)],
    'spaced': True,
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
