"""
Kotar Gospić i kotar Perušić u narodnooslobodilačkom ratu 1941-1945. (Zbornik Historijskog arhiva u Karlovcu, knj. 20;
znaci.org 00003/642, the lists' chapter 642_2.pdf by Zdenka Krivokuća) → website/public/pdfs/hak-20-gospic-perusic.pdf:
a book across units, read by _karlovac_lists.py.

The site's PDF holds two of the chapter's four lists:
    PDF pp. 1-60 (book pp. 986-1045), "Pali borci s područja kotara Gospić i kotara Perušić 1941-1945.", two columns,
    the right column's numbers in the gutter;
    PDF pp. 61-76 (book pp. 1194-1209), "Nosioci partizanske spomenice 1941. godine", a line each.
The victims of fascist terror and of the war (civilians) and those who died of typhus stay out.

Output: data-extraction/znaci/hak-20-gospic-perusic-entries.json, IDs 9007xxxxxx.
Usage: python data-extraction/parse_hak_20_gospic_perusic.py [--sample N]
"""
from _karlovac_lists import main

BOOK = {
    'pdf': 'hak-20-gospic-perusic.pdf',
    'prefix': '9007',
    'lists': [('fallen', range(1, 61), 2), ('spomenica', range(61, 77), 1)],
    # what the page prints -> how the name is read
    'heads': {'ČANAK Jovana STEVAN STEVI-': 'ČANAK Jovana STEVAN', 'RADAKOVIĆ Janka MILICA MI KA': 'RADAKOVIĆ Janka MILICA — MIKA'},
}

if __name__ == '__main__':
    main(BOOK)
