"""
Kotar Korenica i kotar Udbina u NOR-u i socijalističkoj izgradnji (Zbornik Historijskog arhiva u Karlovcu, knj. 10;
znaci.org 00003/489; the lists brought together by Gojko Vezmar) → website/public/pdfs/hak-10-korenica-udbina.pdf: a
book across units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 986-1035 (book pp. 990-1039), "Pali borci s područja kotara Korenica i kotara
Udbina 1941-45.",
two columns of numbered bios by općina and village: "1. BELIC Mojsije PETAR, 1920. Clan KPJ od 1940. Stupio u NOB 1941.
Kurir Glavnog štaba Hrvatske. Poginuo kod Plitvičkih jezera 25. 12. 1941." (the OCR lost the carons). The victims of
fascist terror and of the war (pp. 1036-1111) and those who died of typhus (pp. 1112-1149) stay out; the volume prints
no list of the spomenica's holders.

Output: data-extraction/znaci/hak-10-korenica-udbina-entries.json, IDs 9008xxxxxx.
Usage: python data-extraction/parse_hak_10_korenica_udbina.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-10-korenica-udbina.pdf',
    'prefix': '9008',
    'lists': [('fallen', range(1, 51), 2)],
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
