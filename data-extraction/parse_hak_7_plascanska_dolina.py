"""
Plaščanska dolina i okolica u NOR-u 1941-1945. (Zbornik Historijskog arhiva u Karlovcu, knj. 7; znaci.org
00003/487) → website/public/pdfs/hak-7-plascanska-dolina.pdf: a book across units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 720-732 (book pp. 689-701), "Pali borci s područja Plaščanske doline i
okolice 1941-1945.", two columns of numbered bios by općina (Josipdol, Modruš, Plaški) and village, the names in
capitals, the OCR spacing some of their letters out ("M A Č AK Stevana MILICA, 1906, domaćica, Srpkinja, ..."). The victims of fascist terror and of
the war (pp. 733-757) and those who died of typhus (pp. 758-776) stay out; the volume prints no list of the spomenica's
holders.

Output: data-extraction/znaci/hak-7-plascanska-dolina-entries.json, IDs 9011xxxxxx.
Usage: python data-extraction/parse_hak_7_plascanska_dolina.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-7-plascanska-dolina.pdf',
    'prefix': '9011',
    'spaced': True,
    'lists': [('fallen', range(1, 14), 2)],
    'heads': {'LONČAR. Mile NIKOLA': 'LONČAR Mile NIKOLA'},
}

if __name__ == '__main__':
    main(BOOK)
