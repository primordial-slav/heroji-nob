"""
Soldiers' own photographs, for the record popup and the memorial card. Only certain matches:

- from the books that print one in the soldier's entry: the portrait in the entry's own cell, beside its first line;
- from the znaci.org gallery (GALLERY): a photo of one person whose caption names the soldier and agrees with our
  record on more than the name (unit, duty, place or date of death, birthplace), each checked by hand;
- from the units' own books on znaci.org (UNIT_BOOKS): a photo of one person whose printed caption names a soldier
  whose name is the only one of its kind in the unit, and agrees with the record or the book's text on more than the
  name, each checked by hand;
- from Wikimedia Commons (COMMONS): the lead photo of a narodni heroj's Wikipedia article (sh or sr), where the
  article agrees with our record on the birth year or birthplace, the file is public domain or under a free license
  (CC0, CC BY-SA: credited with the license and the author where known), and it shows that one person in a photograph
  (no drawings, graves or busts). A unit's own book wins over Commons.

  Tuzlanski NOP odred (Tuzla 1988): each cell of the list may hold a portrait, left of the stacked name. A page's
  images can hold two portraits stacked in one strip, so each portrait is found on the page itself: in the band
  left of the entry, the run of dark rows and columns around the entry's first lines, between white gaps.
  Portraits the shape test doesn't pass (a cut-off or pale print, ~50) are left out rather than guessed.

Writes website/public/portreti/<soldier id>.jpg (grey, 240 px high) and website/app/data/portrait-index.json
({soldier id: {f: the print, v: the large photo, c: credit, h: source page}}), which website/app/data/portraits.ts reads. Gallery photos are
downloaded once into data-extraction/.cache/znaci_photos/full/.

    python scripts/extract_book_portraits.py [--sheet OUT.jpg]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'website' / 'public'
OUT = PUBLIC / 'portreti'
INDEX = ROOT / 'website' / 'app' / 'data' / 'portrait-index.json'
DPI = 200
S = DPI / 72
HEIGHT = 240          # the print in the record
LARGE = 900           # the photo opened from it, at most (never enlarged)

BOOKS = [
    # unit data file, PDF, credit shown under the name
    ('tuzlanski-odred-soldiers.json', 'tuzlanski-odred.pdf', 'Tuzlanski NOP odred (Tuzla, 1988)'),
]

GALLERY = [
    # soldier, znaci.org photo, head and shoulders in it (fractions of the photo), what the caption and record share
    ('0039000807', 11685, (0.30, 0.02, 0.75, 0.41), 'komesar 2. bataljona 2. proleterske, poginuo u Bijelim Brdima marta 1944'),
    ('0010000433', 11864, (0.05, 0.0, 0.95, 0.876), 'komandir čete 3. krajiške, poginuo kod Vrbovca maja 1945'),
    ('0026000738', 14608, (0.08, 0.0, 0.75, 0.62), 'stolar, rođen 1899. u Virovu, član Sreskog komiteta KPJ'),
    ('0001003638', 13283, (0.32, 0.06, 0.72, 0.42), 'hodža iz Slatine kod Foče, verski referent'),
    ('0002008648', 10342, (0.1, 0.0, 0.9, 0.70), 'komandant bataljona (drugi Milan Tankosić je rođen 1928)'),
    ('0006008279', 12072, (0.30, 0.06, 0.58, 0.66), 'komandant 13. proleterske; rođen 1917. u Srbu'),
    ('0005000433', 12431, (0.1, 0.02, 0.9, 0.715), 'rukovodilac SKOJ-a 3. sandžačke; jedina Desa Bulatović u brigadi'),
    ('0002000133', 11472, (0.25, 0.06, 0.75, 0.49), 'borac 1. ličkog odreda, "Primorac", rodom iz Novigrada kod Zadra'),
]

BOOK_TITLES = {
    # the units' books on znaci.org, as the photo's credit
    '00001/188': 'Četvrta banijska brigada – zbornik sjećanja',
    '00001/196': 'Nikola Ljubičić, Užički odred „Dimitrije Tucović“',
    '00001/215': 'Milorad Madić, Dušan Jončić, 25. srpska brigada',
    '00001/262': 'Nail Redžić, Dvadeset peta brodska brigada',
    '00001/275': 'Osma crnogorska NOU brigada – zbornik sjećanja',
    '00001/72': 'Žarko Atanacković, Druga vojvođanska NOU brigada',
    '00001/89': 'Mate Šalov, Četvrta dalmatinska (splitska) brigada',
    '00003/542': '32. divizija NOVJ',
    '00003/712': 'Mladen Vukosavljević, Drago Karasijević, 53. srednjobosanska NOU divizija',
    '00001/54': 'Prva proleterska brigada – ilustrovana monografija',
    '00001/55': '50 godina Druge proleterske brigade – ilustrovana monografija',
    '00001/137': 'Jovo Popović, Prva lička proleterska brigada „Marko Orešković“',
    '00001/110': 'Druga lička proleterska brigada – sjećanja boraca',
    '00001/224': 'Savo Trikić, Treća krajiška proleterska brigada',
    '00001/146': 'Izudin Čaušević, Osma krajiška NOU brigada',
    '00001/73': 'Nikola Božić, Sedma vojvođanska NOU brigada',
    '00001/108': 'Mirko Novović, Stevan Petković, Prva dalmatinska proleterska brigada',
}

UNIT_BOOKS = [
    # soldier, the unit's own book on znaci.org, its PDF page and the photo's xref, head and shoulders in it (or the
    # whole photo), what the caption printed with the photo and our record share. The name is the only one of its
    # kind in the unit's records.
    ('0020000398', '00001/188_1.pdf', 45, 185, None, 'zamenik komandanta 2. bataljona, poginuo 1943. u Prekopi'),
    ('0020000521', '00001/188_1.pdf', 178, 763, (0.32, 0.22, 0.75, 0.66), 'omladinski rukovodilac 4. bataljona'),
    ('0020000397', '00001/188_1.pdf', 180, 775, None, 'komesar 2. i 3. bataljona, poginuo 1944. u Gorama'),
    ('0020001636', '00001/188_1.pdf', 188, 811, None, 'komandant 2. bataljona, poginuo 1944. u Komarevu'),
    ('0020000929', '00001/188_2.pdf', 24, 95, (0.05, 0.18, 0.8, 0.92), 'komesar čete u 4. bataljonu'),
    ('0020001414', '00001/188_3.pdf', 3, 11, None, 'borac brigade 1944.'),
    ('0020000023', '00001/188_3.pdf', 77, 349, (0.27, 0.05, 0.62, 0.39), 'komandant 2. bataljona, poginuo 1945. kod Brekovice'),
    ('0026000102', '00001/196_7.pdf', 4, 29, None, 'sekretar Okružnog komiteta KPJ za užički okrug, narodni heroj'),
    ('0026001218', '00001/196_7.pdf', 15, 137, None, 'politički komesar Ariljskog bataljona, narodni heroj'),
    ('0026000001', '00001/196_7.pdf', 17, 157, None, 'član Okružnog komiteta KPJ, komandant mesta u Užicu 1941.'),
    ('0026000520', '00001/196_7.pdf', 17, 161, None, 'član Okružnog komiteta KPJ, politički komesar Moravičke čete'),
    ('0031000309', '00001/215_5.pdf', 52, 289, (0.28, 0.0, 0.7, 0.39), 'zamenik komesara bataljona, poginuo januara 1945.'),
    ('0030000171', '00001/262_3.pdf', 11, 43, (0.38, 0.0, 0.78, 0.35), 'prvi komesar Brodske brigade, "Omega"'),
    ('0030000246', '00001/262_4.pdf', 20, 83, None, 'komesar 2. bataljona, "Grga", posle rata poginuo kao pilot'),
    ('0030000743', '00001/262_6.pdf', 4, 15, (0.28, 0.0, 0.74, 0.39), 'komandant 1. bataljona, "Tuna", poginuo 16. jula 1944. u Severinu'),
    ('0038000317', '00001/275.pdf', 431, 1939, None, 'narodni heroj, komandant brigade, poginuo 3. decembra 1944. u Sremu'),
    ('0018001884', '00001/72_13.pdf', 19, 75, None, 'narodni heroj brigade, rođen 1912. u Doljanima'),
    ('0018000895', '00001/72_13.pdf', 22, 95, None, '"Grozda", rođena 1918. u Irigu'),
    ('0018000957', '00001/72_13.pdf', 23, 103, None, 'narodni heroj brigade, rođen 1919. u Dicmu kod Sinja'),
    ('0018001171', '00001/72_13.pdf', 24, 111, None, 'narodni heroj brigade, rođen 1912. u Lipi kod Bihaća'),
    ('0018001580', '00001/72_13.pdf', 27, 131, None, 'narodni heroj brigade, iz Manđelosa'),
    ('0018000572', '00001/72_2.pdf', 11, 51, (0.22, 0.13, 0.58, 0.46), 'prvi komandant 2. vojvođanske brigade, "Miško"'),
    ('0008000017', '00001/89_13.pdf', 16, 71, None, 'rođena 1928. u Splitu, umrla od rana kod Nedeljščine'),
    ('0008000173', '00001/89_7.pdf', 12, 51, None, 'rođen 1928. u Splitu, ranjen u Kijevu 1944, umro u Italiji'),
    ('0008000935', '00001/89_7.pdf', 21, 99, None, 'mitraljezac 2. bataljona, ranjen 1944, iz Solina (posleratna fotografija)'),
    ('0008001557', '00001/89_8.pdf', 19, 83, None, 'mitraljezac 1. čete 2. bataljona'),
    ('0035009427', '00003/542.pdf', 324, 1607, (0.0, 0.0, 1.0, 0.85), 'sekretar bataljonskog komiteta SKOJ-a'),
    ('0035009678', '00003/542.pdf', 360, 1781, None, 'narodni heroj, prvi komandant 32. divizije'),
    ('0035001622', '00003/542.pdf', 363, 1805, None, 'narodni heroj, poginuo kao komandant brigade "Matija Gubec"'),
    ('0033000720', '00003/712.pdf', 243, 1400, (0.1, 0.08, 0.55, 0.36), 'narodni heroj, pomoćnik komesara bataljona 14. brigade, poginuo 1944.'),
    ('0036000184', '00001/108_21.pdf', 11, 61, (0.263, 0, 1, 0.604), 'za radnička prava, 1936. godine otišao je u Spaniju da u oružanoj borbi brani republiku od reak'),
    ('0003010121', '00001/110_6.pdf', 3, 19, (0, 0, 1, 1), 'Rođen 1. novembra 1919. godine u selu Lički Tiškovac, Donji Lapac. Ma- šinski bravar. Clan KPJ'),
    ('0003000664', '00001/110_6.pdf', 10, 59, (0, 0, 1, 1), 'tojan Matić rođen je u siromašnoj seljačkoj porodici. Nakon završetka osnovne škole u svom rodn'),
    ('0003012981', '00001/110_6.pdf', 19, 113, (0, 0, 1, 1), 'LAZO RADAKOVIĆ'),
    ('0003013153', '00001/110_6.pdf', 21, 125, (0, 0, 1, 1), 'Rođen 10. oktobra 1914. u Širokoj Kuli Zemljoradnik. Clan KPJ od juna 1941. U NOB stupio 27. ju'),
    ('0003014440', '00001/110_6.pdf', 24, 141, (0, 0, 1, 1), 'očeo je da se interesira za politička kretanja još u učiteljskoj školi. Kao učitelj u Ondiću i'),
    ('0002001146', '00001/137_22.pdf', 17, 87, (0, 0, 1, 1), 'Dušan Čubrilo Duja'),
    ('0002003091', '00001/137_5.pdf', 19, 109, (0, 0, 1, 1), 'Boško Jokić'),
    ('0014000051', '00001/146_4.pdf', 107, 461, None, 'Miloš Balać, poginuo 1943. kao komandant bataljona.'),
    ('0010000115', '00001/224_2.pdf', 3, 15, (0, 0, 1, 1), 'Miloš Bauk, zamenik prvog političkog komesara brigade'),
    ('0001001856', '00001/54_10.pdf', 20, 239, (0.288, 0, 0.806, 0.625), 'Janko Čirović, rođen 1904, Bare Radovića, Kolašin; zemljoradnik; član KPJ od 1940. Stu- pio u N'),
    ('0001001840', '00001/54_2.pdf', 7, 67, (0, 0, 1, 1), 'Petar Ćetković Pero - komandant, rođen je 1907. godine, Muže vici, Ljubotinj, Cetinje; kapetan'),
    ('0001006075', '00001/54_2.pdf', 7, 73, (0, 0, 1, 1), 'Andrija Lompar Andro - zamenik komandan- ta, rođen 1907. godine, Bokovo, Cetinje; ra- dnik; čla'),
    ('0001008256', '00001/54_2.pdf', 9, 91, (0, 0, 1, 1), 'Radisav Nedeljković Raja - komandant, ro- đen 1911. godine, Kragujevac; diplomirani pravnik; čl'),
    ('0001005314', '00001/54_2.pdf', 9, 95, (0, 0, 1, 1), 'Dušan Korać - zamenik političkog komesara, rođen 1920. godine, Mrčajevci, Kraljevo; ra- dnik; č'),
    ('0001010077', '00001/54_2.pdf', 9, 97, (0, 0, 1, 1), 'Vojislav Radić Voja - zamenik komandanta, rođen 1902. godine, Donji Konjuvci, Lesko- vac; radni'),
    ('0001003770', '00001/54_2.pdf', 12, 143, (0, 0, 1, 1), 'Pavle Ilič Veljko - zamenik komandanta, ro- đen 1910. godine, Brusnik, Negotin; inženje- rijski'),
    ('0001004742', '00001/54_5.pdf', 7, 63, (0, 0, 1, 1), 'Olga Jovičić Rita, rođena 1920. godine, Kra- ljevo; student; član KPJ od 1940. Stupila u NOB ju'),
    ('0001010679', '00001/54_5.pdf', 9, 85, (0, 0, 1, 1), 'Sa Biokova smo otišli sa vjerom u srci- ma, slijedeći zov Partije i shvatajući da bez zajedničk'),
    ('0001013228', '00001/54_6.pdf', 4, 37, (0, 0, 1, 1), 'Dimitrije Vojvodić Zeko, rođen 1908. godine Konjusi, Andrijevica, SRCG; činovnik; član KPJ od 1'),
    ('0001006830', '00001/54_6.pdf', 17, 173, (0, 0, 1, 1), 'Vojislav Maslovarić, rođen 1914. godine, Dragosava, Berane-Ivangrad; zemljora- dnik, član KPJ o'),
    ('0001000227', '00001/54_6.pdf', 17, 175, (0, 0, 0.855, 0.898), 'Milan-Velebit Antončić, rođen 1918. godi- ne, Gospić, SRH; podoficir jugoslovenske vojske; član'),
    ('0001013347', '00001/54_6.pdf', 24, 251, (0, 0, 1, 1), 'Miloš Vučkovič, rođen 1914. godine, Ulcinj; vojni muzičar; član KP] od 1941. Stupio u NOB jula'),
    ('0001009913', '00001/54_7.pdf', 7, 71, (0, 0, 1, 1), 'Petar Prlja, rođen 1911. godine, Cetinje, ra- dnik; član KP] od 1936. Stupio u NOB jula 1941. P'),
    ('0001013454', '00001/54_7.pdf', 7, 73, None, 'Špiro Vujović, rođen 1918. godine, Ubli Čev- ski, Cetinje; zemljoradnik; član KP] od 1942. Stup'),
    ('0001001120', '00001/54_7.pdf', 7, 75, (0, 0, 1, 1), 'Dragoljub-Žuča Božovič, rođen 1922. godine, Borač, Knić, Kragujevac; đak; član KPJ od 1941. Stu'),
    ('0001003538', '00001/54_7.pdf', 8, 85, (0, 0, 1, 1), 'Vojislav Grujić. rođen 1913. godine, Klopot, Podgorica-Titograd; zemljoradnik; član KP] od 1942'),
    ('0001002311', '00001/54_7.pdf', 8, 87, (0, 0, 1, 1), 'Spasoje Dragović, rođen 1919. godine, Vojko- vići, Kolašin; student; član KP] od 1938. Stu- pio'),
    ('0001013473', '00001/54_7.pdf', 10, 117, (0.065, 0.084, 0.768, 0.931), 'Jovan Vukanovič, rođen 1912. godine, Roga- mi, Podgorica-Titograd; činovnik; član KPJ od 1936.'),
    ('0001007514', '00001/54_7.pdf', 14, 169, (0, 0, 1, 1), 'Miloje Milojević, rođen 1912. godine, Ursule, Jagodina-Svetozarevo; vojni činotmik; član KPJ od'),
    ('0001010512', '00001/54_7.pdf', 15, 179, (0.005, 0, 1, 1), 'Ante Raštegorac, rođen 1924. godine, Zlosela, Kupres; radnik, član KP] od 1942. Stupio u NOB 19'),
    ('0001012029', '00001/54_8.pdf', 8, 77, (0.3, 0.03, 0.85, 0.43), 'Milan Šarac, rođen 1917. godine, Đedovci, Sokolac; podoficir jugoslovenske vojske, član KPJ od'),
    ('0001006472', '00001/54_8.pdf', 8, 79, (0, 0, 0.81, 1), 'Živan Maričič (gore), rođen 1911, godine, Ži- ca, Kraljevo; radnik; član KPJ od 1941. Stupio u'),
    ('0001000727', '00001/54_8.pdf', 8, 81, (0, 0, 1, 1), 'Hamid Beširevič (dole), rođen 1919. godine, Višegrad, student teologije; član KPJ od 1942. Stup'),
    ('0001000765', '00001/54_8.pdf', 23, 267, (0, 0, 1, 1), 'Ante Bilobrk, rođen 1919. godine, Brštanovo, Split; radnik; član KPJ od 1940. Stupio u NOB sept'),
    ('0001003147', '00001/54_8.pdf', 25, 295, (0.2, 0, 0.8, 0.7), 'Radovan Gardašević, rođen 1916. godine, Ubli-Čevski, Cetinje; student; član KPJ od 1941. Stupio'),
    ('0001008364', '00001/54_8.pdf', 25, 299, (0, 0, 1, 1), 'Siniša Nikolajević, rođen 1914. godine, Phot; poručnik jugoslovenske vojske; član KP] od 1941.'),
    ('0001005276', '00001/54_8.pdf', 26, 307, (0, 0, 1, 1), 'Miloš Komatina, roden 1885. godine, Donja Ržanica, Berane-lvangrad; zemljoradnik. Stu- pio u NO'),
    ('0001008578', '00001/54_8.pdf', 30, 349, (0.303, 0, 0.961, 0.801), 'Mirko Novović, rođen 1917. Cecuni, Bera- ne-Ivangrad; student; član KPJ od 1936. Stu- pio u NOB'),
    ('0001013345', '00001/54_9.pdf', 16, 167, (0, 0, 1, 1), 'Jovan Vučković, rođen 1913. godine, Prekor- nica, Ljubotinja Cetinje; radnik, član KP] od 1934.'),
    ('0001013502', '00001/54_9.pdf', 24, 281, (0.046, 0, 1, 1), 'Đoko Vukičevič rođen 1914. godine, Ljuboti- nja, Cetinje; zemljoradnik, revolucionar; član KPJ'),
    ('0001009112', '00001/54_9.pdf', 28, 321, (0, 0, 1, 1), 'Vasilije Pejović, rođen 1911. godine, Miljko- vač, Plužine; zemljoradnik; član KP] od 1941. Stu'),
    ('0039000942', '00001/55_2.pdf', 11, 115, (0, 0, 1, 1), 'Dragoslav Đorđević Go- ša, zamenik političkog komesara, radnik, član KPJ'),
    ('0039000731', '00001/55_3.pdf', 72, 789, (0, 0, 1, 1), 'Aleksija Savić, bolničarka u 1. četi 1. bataljona poginula 17. 06. 1943.'),
    ('0039000932', '00001/55_3.pdf', 93, 1015, (0.027, 0, 1, 1), 'Bogoljub Čukić, poginuo 21. avgusta 1943. kod Carevog Hana, blizu Zavidovića. Narod- ni heroj.'),
    ('0039000094', '00001/55_3.pdf', 95, 1041, (0, 0, 1, 1), 'Boško Buha, proglašen za narodnog heroja.'),
    ('0039000906', '00001/55_4.pdf', 17, 161, (0, 0, 1, 1), 'Đurađ Zrilić, narodni heroj Poslednje naređenje'),
    ('0039000240', '00001/55_5.pdf', 4, 23, (0, 0, 1, 1), 'Petar Ivanović Perica, narodni heroj, poginuo 22. januara 1945. u selu Novak -Bapska, kraj Šida'),
    ('0022001121', '00001/73_7.pdf', 2, 7, (0, 0, 1, 1), 'Milan Ješić Ibra, koman- dant 7. vojvođanske brigade — narodni heroj'),
    ('0022001927', '00001/73_7.pdf', 2, 11, (0, 0, 1, 1), 'Živan Milovanović Ćata, komandant 2. bataljona 7. voj- vođanske brigade — narodni heroj'),
    ('0022001752', '00001/73_7.pdf', 3, 19, (0, 0, 1, 1), 'Lazar Marković Čađa, za- menik komandanta 7. vojvo- đanske brigade — narodni heroj'),
    ('0001013439', '00001/54_8.pdf', 9, 95, (0, 0, 1, 1), 'Đuro Vujović Španac (desno), rođen 1911, Ljubotinj, Cetinje'),
    ('0003012903', '00001/110_6.pdf', 17, 101, (0, 0, 1, 1), 'TOMICA POPOVIĆ'),
    ('0001011588', '00001/54_8.pdf', 9, 93, None, 'Momčilo Stanojlović Moma (levo), rođen 1916, Kragujevac; vazduhoplovni poručnik pilot'),
    ('0005011038', '00001/54_8.pdf', 9, 93, None, 'the same Momčilo Stanojlović Moma (1916, Kragujevac, pilot), narodni heroj'),
]


COMMONS = [
    # soldier, the file on Wikimedia Commons (the lead photo of the narodni heroj's Wikipedia article), head and
    # shoulders in it, license, author where known, what the article and our record share
    ('0001000455', 'Filip_Bajković.jpg', (0, 0, 1, 1), 'Public domain', '', 'Filip Bajković, narodni heroj: birth year 1910; birthplace Kairo, Egipat'),
    ('0001001130', 'Radomir_Božović_Raco.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Radomir Božović, narodni heroj: birth year 1915; birthplace Stijena, Titograd, Crna Gora'),
    ('0001001343', 'Savo_Burić.jpg', (0.093, 0.029, 1, 0.644), 'Public domain', '', 'Savo Burić, narodni heroj: birth year 1915; birthplace Zagrade, Danilovgrad'),
    ('0001003908', 'Dragiša_Ivanović,_politkom_Pete_crnogorske_brigade.jpg', (0, 0, 0.91, 0.864), 'Public domain', 'Žorž Skrigin', 'Dragiša Ivanović, narodni heroj: birth year 1914; birthplace Sjenica, Titograd, Crna Gora'),
    ('0001004598', 'Mirko_Jovanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Mirko Jovanović, narodni heroj: birth year 1923; birthplace Kragujevac, Srbija'),
    ('0001004941', 'Jovo_Kapičić.jpg', (0.169, 0, 0.791, 0.605), 'Public domain', '', 'Jovan Kapičić, narodni heroj: birth year 1919'),
    ('0001005970', 'Danilo_Lekić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Danilo Lekić, narodni heroj: birth year 1913'),
    ('0001006209', 'Stevan_Kragujević,_general_Nikola_Ljubičić.jpg', (0.143, 0, 0.877, 0.666), 'CC BY-SA 3.0 rs', 'Stevan Kragujević', 'Nikola Ljubičić, narodni heroj: birth year 1916; birthplace Lelići, Titovo Užice, Srbija'),
    ('0001007563', 'Milosav_Milosavljević,_septembra_1941.jpg', (0, 0, 1, 1), 'Public domain', '', 'Milosav Milosavljević, narodni heroj: birth year 1911; birthplace Leušić, Gornji Milanovac, Srbija'),
    ('0001009758', 'Koča-Popovic.png', (0.119, 0, 0.923, 0.776), 'Public domain', '', 'Konstantin Popović, narodni heroj: birth year 1908; birthplace Beograd, Srbija'),
    ('0001009880', 'Bojo_Prelević.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Božina Prelević, narodni heroj: years 1943'),
    ('0001011440', 'Marko_Stanišić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Marko Stanišić, narodni heroj: birth year 1919; birthplace Stanišići, Budva, Crna Gora'),
    ('0001012491', 'Stevan_Kragujevic,_Mijalko_Todorovic_corp.JPG', (0.032, 0, 0.976, 1), 'CC BY-SA 3.0 rs', 'Стеван Крагујевић', 'Mijalko Todorović, narodni heroj: birth year 1913; birthplace Dragušica, Knić, Srbija'),
    ('0001013229', 'Đoko_Vojvodić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Đoko Vojvodić, narodni heroj: birth year 1914; birthplace Radomir, Građani, Cetinje; years 1942'),
    ('0001013476', 'Radovan_Vukanović.jpg', (0.102, 0, 0.81, 0.681), 'Public domain', '', 'Radovan Vukanović, narodni heroj: birth year 1906; birthplace Rogami, Titograd, Crna Gora'),
    ('0001014052', 'Komnen_Žugić.jpg', (0.027, 0, 0.825, 0.701), 'Public domain', '', 'Komnen Žugić, narodni heroj: birth year 1922; birthplace Novaković, Žabljak, Crna Gora'),
    ('0002000203', 'Petar_Babić.jpg', (0.19, 0, 0.846, 0.78), 'Public domain', '', 'Petar Babić, narodni heroj: birth year 1919; birthplace Lički Tiškovac'),
    ('0002007028', 'Ilija_Radaković1.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Ilija Radaković, narodni heroj: birth year 1923; birthplace Jošani, T. Korenica'),
    ('0002008480', 'Milan_Šijan.jpg', (0, 0, 1, 1), 'Public domain', '', 'Milan Šijan, narodni heroj: birth year 1914; birthplace Kupirovo, Donji Lapac'),
    ('0003000649', 'Dacina_majstorovic.JPG', (0, 0, 1, 1), 'CC BY-SA 4.0', 'Pendzeras88', 'Dane Majstorović, narodni heroj: birthplace Udbina; years 1944'),
    ('0003014459', 'Milan_Šijan.jpg', (0, 0, 1, 1), 'Public domain', '', 'Milan Šijan, narodni heroj: birth year 1914; birthplace Kupirovo'),
    ('0005000002', 'Velimir_Jakić.jpg', (0.057, 0, 0.853, 0.819), 'Public domain', '', 'Velimir Jakić, narodni heroj: birth year 1911; birthplace Dobra Sela, Šavnik; years 1946'),
    ('0005000080', 'Momir_Pucarević.jpg', (0, 0, 0.829, 0.785), 'Public domain', '', 'Momir Pucarević, narodni heroj: birth year 1918; birthplace Drmanovići, Nova Varoš; years 1942'),
    ('0005000413', 'Рада_Миљковић.jpg', (0, 0, 1, 1), 'CC BY-SA 4.0', '', 'Rada Miljković, narodni heroj: birth year 1917; birthplace Belica, Svetozarevo; years 1942'),
    ('0005000736', 'Danilo_Jauković.jpg', (0.176, 0.119, 0.804, 0.593), 'Public domain', '', 'Danilo Jauković, narodni heroj: birth year 1918; birthplace Bukovica, Šavnik'),
    ('0005010943', 'Radomir_Rakočević.jpg', (0.165, 0, 0.803, 0.637), 'CC BY-SA 3.0 rs', '', 'Radomir Rakočević, narodni heroj: years 1944'),
    ('0007000828', 'Savo_Burić.jpg', (0.093, 0.029, 1, 0.644), 'Public domain', '', 'Savo Burić, narodni heroj: birth year 1915'),
    ('0007001505', 'Milinko_Đurović.jpg', (0, 0, 1, 0.777), 'Public domain', '', 'Milinko Đurović, narodni heroj: birth year 1910; birthplace Zagrad, Nikšić'),
    ('0007004797', 'Ratko_Sofijanić.jpg', (0.15, 0.05, 0.8, 0.7), 'CC BY-SA 3.0', '', 'Ratko Sofijanić, narodni heroj: birth year 1915; birthplace Dubrava, Čačak'),
    ('0007005334', 'Ljubo_Truta.jpg', (0.006, 0.066, 1, 0.739), 'Public domain', '', 'Ljubo Truta, narodni heroj: birth year 1915; birthplace Zlarin, Šibenik'),
    ('0007005598', 'Načelnik_štaba_2._armije_NOVJ_general-major_Ljubo_Vučković.jpg', (0, 0, 1, 1), 'Public domain', '', 'Ljubo Vučković, narodni heroj: birth year 1915'),
    ('0010000593', 'Marko_Jokić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Marko Jokić, narodni heroj: birthplace Vodenica, Bosanski Petrovac; years 1944'),
    ('0014000307', 'Mahmut_Ibrahimpašić_Mašo.jpg', (0.033, 0, 0.973, 0.994), 'Public domain', '', 'Mahmut Ibrahimpašić, narodni heroj: birthplace Bjelaju, Bosanski Petrovac; years 1944'),
    ('0015000090', 'Radivoje_Jovanović_Bradonja_1942.jpg', (0, 0, 0.8, 0.62), 'Public domain', 'Radomir Rade Jokić', 'Radivoje Jovanović, narodni heroj: birth year 1918; birthplace Zarube, Valjevo'),
    ('0023000628', 'Ratko_Jovičić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Ratko Jovičić, narodni heroj: birth year 1919; birthplace Gučevu, Rogatica'),
    ('0026000087', 'Boško_Buha,_1942.jpg', (0.1, 0, 0.9, 0.49), 'Public domain', '', 'Boško Buha, narodni heroj: birthplace Gradina; years 1943'),
    ('0029000349', 'Veljko_Lukic_Kurjak.jpg', (0, 0, 1, 1), 'Public domain', '', 'Veljko Lukić, narodni heroj: birth year 1917; birthplace Donja Bukovica, Bijeljina; years 1944'),
]

def portrait_box(pg: fitz.Page, rects: list[fitz.Rect], x: float, y: float) -> list[float] | None:
    """The portrait left of an entry whose first line starts at (x, y), or None."""
    band = fitz.Rect(x - 100, y - 30, x - 2, y + 110)
    hits = [r for r in rects if r.intersects(band) and r.x1 <= x + 2]
    if not hits:
        return None
    clip = fitz.Rect(min(r.x0 for r in hits), band.y0, max(r.x1 for r in hits), band.y1) & band
    pix = pg.get_pixmap(clip=clip, dpi=DPI, colorspace=fitz.csGRAY)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    dark_rows = (a < 225).mean(1) > 0.35
    start = int((y + 25 - clip.y0) * S)                      # inside the photo: a little below the first line
    if not dark_rows[min(start, len(dark_rows) - 1)]:
        near = np.nonzero(dark_rows)[0]
        if not len(near):
            return None
        start = int(near[np.argmin(np.abs(near - start))])
    gap = int(3 * S)
    top = start
    while top > 0 and dark_rows[max(0, top - gap):top].any():
        top -= 1
    bot = start
    while bot < len(dark_rows) - 1 and dark_rows[bot + 1:bot + 1 + gap].any():
        bot += 1
    cols = np.nonzero((a[top:bot + 1] < 225).mean(0) > 0.35)[0]
    if not len(cols):
        return None
    left, right = int(cols.min()), int(cols.max())
    h, w = (bot - top) / S, (right - left) / S
    if h < 60 or not 0.55 < w / h < 1.0:                      # cut off, or two prints run together
        return None
    return [clip.x0 + left / S, clip.y0 + top / S, clip.x0 + right / S, clip.y0 + bot / S]


def commons_file(name: str) -> Path:
    """A Commons photo, as its standard 500-px thumbnail (Wikimedia asks scripts not to pull originals), cached."""
    local = ROOT / 'data-extraction' / '.cache' / 'commons' / name
    if not local.exists():
        import subprocess
        import urllib.parse
        ua = 'User-Agent: KnjigaBoraca-portraits/0.1 (research script; low volume)'
        q = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'formatversion': '2', 'prop': 'imageinfo',
                                    'iiprop': 'url', 'iiurlwidth': '500', 'titles': f'File:{name}'})
        r = subprocess.run(['curl', '-s', '-H', ua, '--data', q, 'https://commons.wikimedia.org/w/api.php'], capture_output=True)
        ii = json.loads(r.stdout)['query']['pages'][0]['imageinfo'][0]
        local.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['curl', '-s', '-f', '-L', '-H', ua, '-o', str(local), ii.get('thumburl') or ii['url']], check=True)
    return local


def save(im: Image.Image, sid: str) -> dict:
    """The print (HEIGHT high) and, where the source is much bigger, the large photo (up to LARGE high)."""
    small = im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS)
    small.save(OUT / f'{sid}.jpg', quality=80, optimize=True, progressive=True)
    if im.height < 1.5 * HEIGHT:                         # a book's small print: the print is all there is
        (OUT / f'{sid}-v.jpg').unlink(missing_ok=True)
        return {'f': f'{sid}.jpg'}
    if im.height > LARGE:
        im = im.resize((round(im.width * LARGE / im.height), LARGE), Image.LANCZOS)
    im.save(OUT / f'{sid}-v.jpg', quality=84, optimize=True, progressive=True)
    return {'f': f'{sid}.jpg', 'v': f'{sid}-v.jpg'}


def main():
    OUT.mkdir(exist_ok=True)
    index, sheet = {}, []
    for data_file, pdf, credit in BOOKS:
        soldiers = json.loads((PUBLIC / data_file).read_text(encoding='utf-8'))
        doc = fitz.open(PUBLIC / 'pdfs' / pdf)
        rects: dict[int, list[fitz.Rect]] = {}
        n = 0
        for s in soldiers:
            if s.get('pdf_file') != pdf or not s.get('pdf_page'):
                continue
            pg = doc[s['pdf_page'] - 1]
            if s['pdf_page'] not in rects:
                rects[s['pdf_page']] = [fitz.Rect(r) for img in pg.get_images(full=True)
                                        for r in pg.get_image_rects(img[0]) if r.width > 30]
            box = portrait_box(pg, rects[s['pdf_page']], s['pdf_x'], s['pdf_y'])
            if not box:
                continue
            pix = pg.get_pixmap(clip=fitz.Rect(box), dpi=DPI, colorspace=fitz.csGRAY)
            im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
            index[s['soldier_id']] = {**save(im, s['soldier_id']), 'c': credit}
            sheet.append((s['full_name'], im))
            n += 1
        print(f'{data_file}: {n} portraits')
    sys.path.insert(0, str(ROOT / 'scripts'))
    import find_unit_photos as F
    for sid, pid, (a, b, c, d), _why in GALLERY:
        path = F.CACHE / 'full' / f'{pid}.jpg'
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(F._get(f'{F.BASE}/images/{pid}.jpg'))
        im = Image.open(path).convert('L')
        w, h = im.size
        im = im.crop((int(a * w), int(b * h), int(c * w), int(d * h)))
        index[sid] = {**save(im, sid), 'c': f'znaci.org, br. {pid}', 'h': f'https://znaci.org/fotografija.php?br={pid}'}
    print(f'gallery: {len(GALLERY)} portraits')
    for sid, path, page, xref, crop, _why in UNIT_BOOKS:
        im = F.book_image(path, xref).convert('L')
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        index[sid] = {**save(im, sid), 'c': BOOK_TITLES[path.rsplit('_', 1)[0].removesuffix('.pdf')],
                      'h': f'https://znaci.org/{path}#page={page}'}
    print(f"units' books: {len(UNIT_BOOKS)} portraits")
    for sid, name, crop, license, artist, _why in COMMONS:
        if sid in index:                    # a photo from the unit's own book comes first
            continue
        im = Image.open(commons_file(name)).convert('L')
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        credit = f'Wikimedia Commons ({license})' if license.startswith('CC BY') else 'Wikimedia Commons'
        index[sid] = {**save(im, sid), 'c': f'{artist}, {credit}' if artist else credit,
                      'h': f'https://commons.wikimedia.org/wiki/File:{name}'}
    print(f'Commons: {len(COMMONS)} portraits')
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')
    print(f'{len(index)} portraits → {OUT}')
    if '--sheet' in sys.argv:
        tiles = sheet[:80]
        out = Image.new('L', (10 * 130, 8 * 170), 255)
        for k, (_, im) in enumerate(tiles):
            t = im.copy()
            t.thumbnail((120, 160))
            out.paste(t, ((k % 10) * 130, (k // 10) * 170))
        out.save(sys.argv[sys.argv.index('--sheet') + 1])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
