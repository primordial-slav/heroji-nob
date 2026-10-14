"""
Kotar Slunj i kotar Veljun u NOR i socijalističkoj izgradnji, 2. dio (Zbornik Historijskog arhiva u Karlovcu, knj. 18; znaci.org 00003/497) → website/public/pdfs/hak-18-slunj-veljun.pdf: a book across
units, read by _karlovac_lists.py.

The site's PDF holds the book's PDF pp. 231-287, "Pali borci s područja kotara Slunja i kotara Veljuna 1941-1945", two columns of numbered bios by općina and village, the names in capitals: "1. PAULIČ Franje MILE, 1918, seljak, Hrvat. Stupio u NOV jula ...".
The victims of fascist terror and of the war (PDF p. 288 on) and those who died of typhus stay out.

Output: data-extraction/znaci/hak-18-slunj-veljun-entries.json, IDs 9019xxxxxx.
Usage: python data-extraction/parse_hak_18_slunj_veljun.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-18-slunj-veljun.pdf',
    'prefix': '9019',
    'lists': [('fallen', range(1, 58), 2)],
    'heads': {},
}

if __name__ == '__main__':
    main(BOOK)
