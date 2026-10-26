"""
Soldiers' own photographs, for the record popup and the memorial card. Only certain matches:

- from the books that print one in the soldier's entry: the portrait in the entry's own cell, beside its first line;
- from the znaci.org gallery (GALLERY): a photo of one person whose caption names the soldier and agrees with our
  record on more than the name (unit, duty, place or date of death, birthplace), each checked by hand;
- from the units' own books on znaci.org (UNIT_BOOKS): a photo of one person whose printed caption names a soldier
  whose name is the only one of its kind in the unit, and agrees with the record or the book's text on more than the
  name, each checked by hand; PAGE_BOOKS the same, cut from the page where the book stores a photo as strips or prints
  several side by side (one man of a group only where the caption says which);
- from Wikimedia Commons (COMMONS): the lead photo of a narodni heroj's Wikipedia article (sh or sr), where the
  article agrees with our record on the birth year or birthplace, the file is public domain or under a free license
  (CC0, CC BY-SA: credited with the license and the author where known), and it shows that one person in a photograph
  (no drawings, graves or busts). A unit's own book wins over Commons.

  Tuzlanski NOP odred (Tuzla 1988): each cell of the list may hold a portrait, left of the stacked name. A page's
  images can hold two portraits stacked in one strip, so each portrait is found on the page itself: in the band
  left of the entry, the run of dark rows and columns around the entry's first lines, between white gaps.
  Portraits the shape test doesn't pass (a cut-off or pale print, ~50) are left out rather than guessed.

Writes website/public/portreti/<soldier id>.jpg (grey, 240 px high) and website/app/data/portrait-index.json
({soldier id: {f: the print, v: the large photo, c: credit, h: source page, same: the record that shows this man in
lists of faces, where he has more than one}}), which website/app/data/portraits.ts reads. Gallery photos are
downloaded once into data-extraction/.cache/znaci_photos/full/.

    python scripts/extract_book_portraits.py [--sheet OUT.jpg]
    python scripts/extract_book_portraits.py --new       # make only the portraits the index lacks, keep the others' files
    python scripts/extract_book_portraits.py --same      # only re-mark the same men (after links or merges change)
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
    # third batch: checked against the record and the photo, one person each
    ('0010000071', 9822, (0, 0, 1, 1), 'narodni heroj, komesar 3. krajiške brigade'),
    ('0040000013', 11751, (0, 0, 1, 1), 'borac 4. crnogorske proleterske brigade, rođen 1913. (književnik)'),
    ('0010001917', 11849, (0.25, 0, 0.7, 0.3), 'borac 3. bataljona 3. krajiške, poginuo u Sremu (kod Šida, decembra 1944)'),
    ('0040000702', 14531, (0, 0, 1, 1), 'borac 4. crnogorske proleterske brigade, rođena 1910. u Boljevićima'),
    ('0109000398', 14610, (0, 0, 1, 1), 'Radmila "Lala" Ivković, Mačvanski odred, rođena 1915. u Čačku'),
    ('0039101049', 14643, (0, 0, 1, 1), 'bolničarka u 2. proleterskoj, iz Pranjana'),
    ('0012000509', 15162, (0, 0, 1, 1), 'narodni heroj, prvi komandant 5. kozaračke brigade'),
    ('0012000762', 15163, (0, 0, 1, 1), 'narodni heroj, komandant 5. kozaračke brigade'),
    ('0070101809', 15576, (0, 0, 1, 1), 'lekar, rođen 1903. u Radgoni, poginuo 1944. kod Rakitovca'),
    ('0070104479', 15600, (0, 0, 1, 1), 'lekar, rođen 1913. u Novom Mestu, sanitetski referent Tomšičeve brigade, poginuo 1943.'),
    ('0062002747', 15601, (0, 0, 1, 1), 'lekar Gubčeve brigade, rođen 1915. u Ljubljani, poginuo 1944.'),
    ('0039101051', 11685, (0.3, 0.02, 0.75, 0.41), 'komesar 2. bataljona 2. proleterske, poginuo u Bijelim Brdima marta 1944'),
    # second pass (October 2026), over the records added since
    ('0112000079', 121, (0, 0, 1, 1), 'Milovan Đilas in Jajce, October 1943; the record: member of the Vrhovni štab, councillor of the second AVNOJ session'),
    ('0109000647', 3498, (0.08, 0.27, 0.55, 0.62), "Danilo Lekić with the 1. proleterska's flag, 1942; the record: zvani Španac, born 1913 in Kralje, narodni heroj"),
    ('0001006419', 11661, (0.27, 0.08, 0.6, 0.45), 'vodnik of the 2. četa, 2. bataljon, from Kržanja, badly wounded at Mioč 24 December 1941 (caption and record)'),
    ('0126000698', 14630, (0, 0, 1, 1), 'trgovac, born 1897 in Milićevci, organizer of the rising around Čačak (caption and record)'),
    ('0126000170', 14649, (0, 0, 1, 1), 'učiteljica, born 1920 in Prijevor, Ljubićka četa, killed by chetniks (caption and record)'),
    ('0126000328', 14654, (0, 0, 1, 1), 'zemljoradnik and poet, born 1913 in Preljina, political commissar in the Ljubićki bataljon (caption and record)'),
    ('0113000084', 15336, (0.33, 0.12, 0.72, 0.5), "Dr Đura Mešterović, October 1942; the record: chief of the division's surgical team, born 1908 in Srpski Itebej"),
    ('0001014078', 15336, (0.33, 0.12, 0.72, 0.5), 'Dr Đura Mešterović, October 1942; the record: doctor, born 1908 in Srpski Itebej (the same man as 0113000084)'),
    ('0077000256', 3844, (0, 0, 1, 1), 'Darinka Dara Dragišić, tagged narodni heroj and Kosovo; the record: born in Peć, narodni heroj'),
    ('0119000183', 4815, (0, 0, 1, 1), 'Natalija Dugošević, tagged logor Banjica; the record: shot at Banjica'),
    ('0126001179', 4820, (0, 0, 1, 1), 'Stanislava Čvorović, tagged logor Banjica; the record: shot at Banjica, August 1942'),
    ('0041001464', 11740, (0.42, 0.17, 0.78, 0.55), "operativni oficir of the 2. udarni korpus, November 1944; the record: at the war's end in the corps staff"),
    ('0041001101', 11781, (0.48, 0.22, 0.86, 0.6), "zamenik političkog komesara of the 9. crnogorska, 1944; the record: at the war's end political commissar of a brigade"),
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
    '00001/131': 'Zdravko B. Cvetković, Sedamnaesta slavonska brigada',
    '00001/168': 'Dvanaesta krajiška NOU brigada',
    '00001/186': 'Sedma krajiška brigada – sjećanja boraca, knj. 2',
    '00001/206': 'Treća proleterska sandžačka brigada – sećanja boraca, knj. 3',
    '00001/243': 'Osman Đikić, Dvanaesta hercegovačka NOU brigada',
    '00001/254': 'Bogdan Bosiočić, 21. slavonska NOU brigada',
    '00001/268': 'Četrnaesta hercegovačka omladinska brigada',
    '00001/274': 'Predrag Milenković, Sedamnaesta srpska NOU brigada',
    '00001/280': 'Dragoljub Dinić Mića, Toplički narodnooslobodilački partizanski odred',
    '00003/381': 'Radovan Timotijević, Deseta srpska NOU brigada',
    '00003/394': 'Treća krajiška brigada – zbornik sjećanja, knj. 3',
    '00003/431': 'Đorđe Momčilović, Kako do brigade',
    '00003/450': 'Zdravko B. Cvetković, Osječka udarna brigada',
    '00003/477': 'Vojislav Nikčević, 15. srpska brigada',
    '00003/537': 'Šesta crnogorska udarna brigada – zbornik sjećanja',
    '00003/547': 'Milan Rako, Slavko Družijanić, Jedanaesta dalmatinska udarna brigada',
    '00003/558': 'Žarko Miličević, Kalnički partizanski odred',
    '00003/588': 'Dragutin Grgurević, U Zlopolju (Treća dalmatinska brigada)',
    '00003/782': 'Lado Ambrožič-Novljan, Gubčeva brigada',
    '00003/787': 'Franci Strle, Tomšičeva brigada, knj. 2',
    '00003/792': 'Franci Strle, Tomšičeva brigada, knj. 3',
    '00003/811': 'Maks Zadnik, Istrski odred',
    '00003/825': 'Stanko Petelin, Gradnikova brigada',
    '00003/841': 'Dragoljub Mirčetić, 12. srpska brigada',
    '00001/51': 'Milojica Pantelić, Radovan M. Marinković, Vladimir Nikšić, Čačanski NOP odred „Dr Dragiša Mišović“',
    '00001/115': 'Predrag Pejčić, Prva i druga eskadrila NOVJ',
    '00001/238': 'Predrag Pejčić, 42. vazduhoplovna divizija',
    '00003/773': 'Stanko Petelin, Kosovelova brigada',
    '00003/769': 'Srečko Vilhar, Albert Klun, Prva in druga prekomorska brigada',
    '00003/607': 'Zagrebački partizanski odred – zbornik dokumenata i sjećanja',
    '00003/794': 'Miroslav Velić, Ante V. Petrić, Mosorski partizanski odred',
    '00003/541': 'Vukašin Karanović, Treći diverzantski odred',
    '00003/543': 'Vujo Vidaković, Prvi tenkovski bataljon',
    '00001/121': 'Deveta srpska udarna brigada u stroju i s narodom',
    '00003/783': 'Edvin Pervanje, Jože A. Hočevar, Četrta prekomorska brigada',
    '00003/499': 'Beogradski bataljon',
    '00003/493': 'Prvi crnogorski bataljon Prve proleterske NOU brigade – zbornik sjećanja',
    '00001/148': 'Blažo Janković, Četvrta proleterska crnogorska brigada',
    '00001/185': 'Milutin Milković, Prva kosovsko-metohijska proleterska brigada',
    '00001/190': 'Stanko Obradović, Antun Miletić, 4. NOU brigada Slavonije (Druga brodska brigada)',
    '00001/251': 'Osamnaesta hrvatska istočnobosanska brigada (grupa autora)',
    '00001/252': 'Živan M. Ninković, Šesta vojvođanska udarna brigada',
    '00001/270': 'Mensur Seferović, Trinaesta hercegovačka NOU brigada',
    '00001/271': 'Čedo Drulović, Četvrta sandžačka NOU brigada',
    '00001/70': 'Radovan Panić, Treća vojvođanska NOU brigada',
    '00001/81': 'Nikola Mraović, Peta vojvođanska brigada',
    '00002/427': 'Nikola Božić, Batinska bitka',
    '00003/544': 'Vladimir-Dušan Matetić, 14. primorsko-goranska brigada',
    '00003/546': 'Josip Lulik Pepo, Đuro Zatezalo, Karlovačka udarna brigada',
    '00003/579': 'Stevo Samardžija, 14. srednjobosanska NOU brigada',
    '00003/652': 'Kažimir Pribilović, Četvrti pomorski obalni sektor Mornarice NOVJ',
    '00003/767': 'Lado Ambrožič-Novljan, Cankarjeva brigada',
    '00003/775': 'Mirko Fajdiga, Bračičeva brigada',
    '00003/814': 'Lado Ambrožič-Novljan, Dvanajsta brigada',
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
    # third batch: 24 more units' books; captions read on the page, "(levo)"/"(desno)" and the books that print the caption beside the photo (Toplički) placed by hand
    ('0010101212', '00003/394.pdf', 11, 49, None, 'SIMO TADIĆ politički komesar Brigade'),
    ('0010100070', '00003/394.pdf', 13, 61, None, 'VLADO BAJIĆ zamenik komandanta Brigade'),
    ('0034000603', '00001/254_12.pdf', 1, 175, (0.3, 0.08, 0.95, 0.55), 'Ferdo Milić — Pedro „Feda" prvi komesar brigade, poginuo 4. 6. 1943. snimljen u Spaniji početkom 193'),
    ('0046000958', '00003/588.pdf', 51, 372, (0.54, 0, 1, 1), 'Narodni heroj Ante Roje, zamjenik političkog komesara brigade'),
    ('0046000263', '00003/588.pdf', 52, 378, None, 'Narodni heroj Jošo Durbaba, komandant Četvrtog, »krva\xad vog« bataljona Treće dalma\xad tinske NOU brigad'),
    ('0048000479', '00001/186_1.pdf', 304, 1407, None, 'Savo Lovre, komandir 1. čete, 4. bataljona'),
    ('0048000979', '00001/186_1.pdf', 310, 1443, None, 'Slavko Vuković, komandant 4. bat^ona i zamjenik komandanta brigade'),
    ('0048000432', '00001/186_1.pdf', 314, 1463, None, 'Risto Kuzman, komandir izvićačke grupe'),
    ('0048000051', '00001/186_1.pdf', 365, 1735, None, 'Ahmet Balić komesar kulturne ekipe, Travnik 1945.'),
    ('0048000028', '00001/186_1.pdf', 428, 2121, None, 'Ostoja Aćimović, komandir čete u 4. bataljonu'),
    ('0048012067', '00001/186_1.pdf', 439, 2189, None, 'Jovo Medić, komandant 1. bataljona'),
    ('0053000936', '00003/547.pdf', 245, 1289, (0.15, 0, 0.65, 0.3), 'Hrabra bolničarka Lucija Gospodnetić- Činda, poginula u borbama za Oštru glavicu'),
    ('0053001693', '00003/547.pdf', 596, 3033, None, 'Marević (Ivana) Stanko-Prpić'),
    ('0054000995', '00001/168_2.pdf', 40, 201, (0.05, 0, 0.55, 1), 'Sreto Jovanović (levo), k-dir čete u 3. b., poginuo aprila 1945. kod Drenovca.'),
    ('0055000067', '00001/274_7.pdf', 40, 169, None, 'Božović Dušan »Duka«, prvi pomoćiak komesara 17. brigade'),
    ('0058001821', '00003/558.pdf', 413, 1839, (0.1, 0, 0.5, 0.3), 'Ludbreg 1943. Od lijeva: Stevo Miočinović, komandir čete i Stevo Zorić, vodnik voda u KPO'),
    ('0058000195', '00003/558.pdf', 421, 1927, None, 'PETAR BIŠKUP VENO'),
    ('0058001266', '00003/558.pdf', 432, 2011, None, 'STOJAN KOMLJENOVIĆ ČOKA'),
    ('0058002796', '00003/558.pdf', 440, 2071, None, 'MARIJA VIDOVIĆ - ABESINKA'),
    ('0062002842', '00003/782.pdf', 131, 1632, (0.35, 0.08, 0.75, 0.35), 'Tone Zgonc-Vasja, komandant brigade Zvonko Vrečko-Tinč Gojčič, politični komisar brigade. Padel 8. s'),
    ('0064001962', '00003/825.pdf', 500, 2954, (0.55, 0.1, 1, 0.75), 'Alojz Mlakar-Zmaj (desno), namestnik šefa obveščevalnega cen\xad tra Gradnikove brigade in eden izmed n'),
    ('0067000987', '00003/811.pdf', 230, 1856, None, 'Ljubomir Sancin-Stojan, junaško padli komandir udarne čete 2. bataljona IO'),
    ('0070000400', '00003/787.pdf', 21, 1029, None, 'Ivan Jakič-Jerin, prvi komandant, in Mica Šlandrova, prvi politični komisar Tomšičeve brigade'),
    ('0070001283', '00003/787.pdf', 324, 2317, (0, 0, 0.48, 1), 'Puškomitraljezec Anton Stojan (levo) je padel 10. marca 1944 na Trški gori kot namestnik komandanta'),
    ('0070000269', '00003/787.pdf', 366, 2494, (0.52, 0, 1, 1), 'Komandir 1. čete Vinko Simončič-Gašper (levo) je padel kot namestnik ko\xad mandanta 14. divizije 8. no'),
    ('0070000072', '00003/787.pdf', 762, 4214, (0, 0, 0.48, 1), 'France Berčon-Andrejček z Osredka nad Stično (levo) je ranjen padel v roke belogardistom, ki so ga z'),
    ('0070000926', '00003/792.pdf', 622, 3389, None, 'Dva prizadevna snovalca in sodelavca žepnih časopisov v Tomšičevi brigadi: avtor besedila za to knji'),
    ('0084001400', '00003/431.pdf', 361, 1699, None, 'MLADEN MILOSEVIC CERCIL, VOĐA DI- VERZANTSKE GRUPE, KOMESAR ODREDA'),
    ('0084000908', '00003/431.pdf', 384, 1811, None, 'ĐURO KNEŽEVIĆ GRMEĆ, KOMANDIR KU- RIRA »DUGE LINIJE«'),
    ('0084000961', '00003/431.pdf', 385, 1819, None, 'VELJKO KOVAČ PANTA, JEDAN OD KURI- RA NA »DUGOJ I INIJI« I KOMANDIR CETE'),
    ('0084001099', '00003/431.pdf', 671, 3115, None, 'LAZAR LJUBINKOVIC SAŠA, KOMESAR XIII VOJVOĐANSKE UDARNE BRIGADE'),
    ('0086000124', '00003/477.pdf', 200, 955, None, 'Dragoljub Drekalović, pomoćnik komesara čete 3. bataljona'),
    ('0088000340', '00003/381.pdf', 551, 2297, None, 'Uroš Veljković, komandir treće čete Vukašin Mitrović, komandir prve čete trećeg bataljona, prvi star'),
    ('0101000096', '00001/243_10.pdf', 1, 147, None, 'Ante Kelava Zoro'),
    ('0104000052', '00003/450.pdf', 124, 553, None, 'Komandant brigade Milivoj Babac Obilić'),
    ('0106000241', '00003/537.pdf', 819, 3381, None, 'Momčilo Šolović, komandir 3. čet ; 1. bataljona, smrtno ranjen 21. VII 1944. podlegao ranama 22. VII'),
    ('0106000077', '00003/537.pdf', 827, 3461, None, 'Žarko Krstajić, zamjenik komandi- ra 1. čete 1. bataljona, poginuo 20. XI 1944. na Zagredi — Danilov'),
    ('0005000094', '00001/206_2.pdf', 2, 7, None, 'NaroOnč heroj Živko Ljujić'),
    ('0016002006', '00001/131_6.pdf', 13, 55, None, 'Narodni heroj Mojica Birta Zec'),
    ('0053002188', '00003/547.pdf', 597, 3041, None, 'Pecotić (Marka) Bogdan'),
    ('0054003477', '00001/168_1.pdf', 23, 141, (0.52, 0, 0.8, 0.25), 'Mile Vučenović, k-dant 12. brigade od IV 1944. do kraja rata'),
    ('0055000490', '00001/274_7.pdf', 40, 171, None, 'Mušović Miloš, prvi koman- dant 17. srpske udarne brigade'),
    ('0058000226', '00003/558.pdf', 423, 1943, None, 'FLORIJAN BOBIĆ'),
    ('0058002983', '00003/558.pdf', 425, 1959, None, 'DUŠAN ĆORKOVIĆ'),
    ('0058000398', '00003/558.pdf', 426, 1967, None, 'NIKOLA DEMONJA'),
    ('0058000431', '00003/558.pdf', 428, 1983, None, 'STEVO DOŠEN'),
    ('0058001042', '00003/558.pdf', 429, 1991, None, 'MATE JERKOVIĆ'),
    ('0058001045', '00003/558.pdf', 431, 2003, None, 'MILAN JOKA'),
    ('0058001865', '00003/558.pdf', 433, 2019, None, 'SLAVKO MRKOCI'),
    ('0058002291', '00003/558.pdf', 435, 2031, None, 'JOSIP PRŠA'),
    ('0058003104', '00003/558.pdf', 437, 2047, None, 'IVAN ŠIBL'),
    ('0058003202', '00003/558.pdf', 438, 2055, None, 'IZIDOR ŠTROK'),
    ('0067000726', '00003/811.pdf', 121, 1404, None, 'Karlo Maslo-Drago'),
    ('0067000291', '00003/811.pdf', 773, 4119, None, 'Dr. Magomed Gadžijev-Mišo'),
    ('0081001390', '00001/268_5.pdf', 2, 7, None, 'Radovan Četka Šakotić'),
    ('0081000550', '00001/268_5.pdf', 4, 19, None, 'Maksim Borda Kujundžić'),
    ('0084001328', '00003/431.pdf', 51, 251, None, 'ŽARKO MILANKOV, KOMANDANT KUMA- NACKOG ODREDA'),
    ('0084000706', '00003/431.pdf', 580, 2691, None, 'SAVO IVANČEVIĆ, KOMESAR VODA, JE- DAN OD NAJSTARIJIH U BRIGADI'),
    ('0090000304', '00003/841.pdf', 403, 2039, (0.5, 0, 1, 1), 'Čedomir-Uroš Stanković, zamenik komandanta brigade, a zatim obaveštajni oficir brigade.'),
    ('0101000260', '00001/243_10.pdf', 7, 39, None, 'Radovan Šakotić'),
    ('0104000565', '00003/450.pdf', 21, 87, (0, 0, 0.46, 1), 'Prvi komandant brigade, na- rodni heroi Milan Joka'),
    ('0104000646', '00003/450.pdf', 137, 627, None, 'Kurir 4. bataljona — Antun Klenuk'),
    ('0104001840', '00003/450.pdf', 181, 855, None, 'Komandant brigane, Franjo Šljivarić'),
    ('0093000157', '00001/280_11.pdf', 5, 31, None, 'Sreten Mladenović Mika, sekretar OK KPJ Niš (zvani Mika)'),
    ('0093000199', '00001/280_11.pdf', 5, 33, None, 'Dimitrije Pisković Trnavac, komandant odreda 1942-43'),
    ('0093000048', '00001/280_11.pdf', 5, 35, None, 'Ivan Fapčić Đuro, politički komesar, poginuo aprila 1942.'),
    ('0093000225', '00001/280_11.pdf', 5, 37, None, 'Dragi Stamenković Srba, partijski rukovodilac (zvani Dragi Srba)'),
    ('0093000084', '00001/280_11.pdf', 6, 45, None, 'Desimir Jovović Čiča, politički komesar odreda 1942.'),
    ('0093000075', '00001/280_11.pdf', 6, 49, None, 'Radoš Jovanović Selja, sekretar Poverenstva KPJ za Toplicu'),
    ('0104000888', '00003/450.pdf', 126, 567, (0, 0, 0.45, 1), 'Politički komesar brigade Antun Malić Broco (levo)'),
    # units added since the last pass and second books (October 2026): captions read on their pages; the 1941 roster
    # of the 1. crnogorski bataljon (00003/493, pp. 682-695) prints a portrait beside each entry, matched on name,
    # birth year and father or village
    ('0126001219', '00001/51_4.pdf', 27, 149, (0, 0, 0.48, 1), 'narodni heroj (caption; proclaimed 1953 in the record)'),
    ('0126000064', '00001/51_4.pdf', 29, 161, (0, 0, 0.45, 1), '"Dragan Bojović": the record\\\'s Dragoslav zvani Dragan'),
    ('0126000249', '00001/51_4.pdf', 47, 257, None, 'narodni heroj (caption; proclaimed 1953 in the record)'),
    ('0126000021', '00001/51_4.pdf', 47, 255, None, 'narodni heroj; komandir from Belo Polje, BJV podoficir (page text and record)'),
    ('0126000938', '00001/51_5.pdf', 27, 157, None, '"Sima Saraga": the record\\\'s Simon zvani Sima'),
    ('0126000548', '00001/51_5.pdf', 45, 247, None, 'student from Čačak, secretary of the district SKOJ (book p. 47 and record)'),
    ('0126000621', '00001/51_6.pdf', 3, 11, (0, 0, 0.49, 1), 'komandant partizanske artiljerije (caption and record)'),
    ('0139000053', '00001/115_4.pdf', 25, 139, (0, 0, 0.47, 1), "komandant 351. skvadrona; the book's own roster has one Aleksandar Cenić, kapetan pilot"),
    ('0140001130', '00001/238_12.pdf', 21, 89, None, 'potporučnik, pilot of the 422. puk (caption and record)'),
    ('0140000466', '00001/238_12.pdf', 21, 91, None, 'major, komandant of the 423. puk to 21 March 1945, when he fell (caption and record)'),
    ('0140000206', '00001/238_12.pdf', 23, 111, None, 'potporučnik, pilot (caption and record)'),
    ('0142000281', '00003/773.pdf', 198, 1669, (0.0, 0.26, 0.45, 0.66), 'komandant 1. bataljona, May 1944 (caption beside the photo; the record: 12 May - 21 June 1944)'),
    ('0144000367', '00003/769.pdf', 48, 596, None, 'politkomisar 2. čete 1. bataljona (caption beside it; the record: politkomisar čete)'),
    ('0144000479', '00003/769.pdf', 109, 846, None, 'pomočnik politkomisarja 2. bataljona, then komisar 5. bataljona on Hvar (caption beside it and record)'),
    ('0144000042', '00003/769.pdf', 116, 877, None, 'politkomisar of the 1., 2. and 3. prekomorska, narodni heroj (caption beside it and record)'),
    ('0144000118', '00003/769.pdf', 131, 946, None, 'politkomisar bataljona in the 1. prekomorska, of the camp at Gravina (caption beside it and record)'),
    ('0144000164', '00003/769.pdf', 241, 1400, (0.45, 0.2, 1.0, 0.62), 'Milan Kmet "na desni" of two; komandant 1. bataljona, then of the 1. prekomorska (caption and record)'),
    ('0144000040', '00003/769.pdf', 247, 1426, None, 'politkomisar 4. bataljona 1. prekomorske (caption beside it and record)'),
    ('0144000233', '00003/769.pdf', 265, 1517, None, 'politkomisar 5. bataljona, then its pomočnik politkomisarja (caption beside it and record)'),
    ('0147000172', '00003/607.pdf', 17, 517, None, '"Ante Dobrila — Vivere", sekretar-politkomesar of the first odred, lives in Opatija (book p. 19; the record: Opatija)'),
    ('0147000585', '00003/607.pdf', 67, 734, None, '"Pavao Lončar — Prigorac", writing of the party cell of Vrapče (the record: Vrapče)'),
    ('0147001169', '00003/607.pdf', 129, 1056, (0.2, 0.34, 0.8, 0.62), 'intendant Zagrebačkog odreda, January 1944 (caption); the only Vilko Šafar of the roster'),
    ('0147000857', '00003/607.pdf', 165, 1217, (0.6, 0.0, 0.98, 0.3), '"Vlado Prišlin ... (desno)", sekretar OK KPH Zagreb, fell at Oborovo 29 March 1944 (caption and record)'),
    ('0147000608', '00003/607.pdf', 260, 1644, (0.2, 0.15, 0.8, 0.45), 'kapetan, komandant Zagrebačkog odreda, July 1944 (caption); the only Jovica Mandić of the roster'),
    ('0148000136', '00003/794.pdf', 46, 879, None, "the only Ante Bakota in the book's own roster of every fighter, which the record is; the photo in the chapter on spring 1942, when he fell"),
    ('0148001882', '00003/794.pdf', 265, 1813, (0.0, 0.03, 0.38, 0.4), '"S lijeva na desno: Venko Mimica, ..." on Mosor 1944; the roster\'s only Venko Mimica, back in the odred from October 1943'),
    ('0148002099', '00003/794.pdf', 329, 2109, None, 'komesar 3. bataljona MPO (caption; the record: fell 9 September 1944 as its politkomesar)'),
    ('0161000351', '00003/541.pdf', 158, 737, None, 'FRANC VULINEC, komandir 1. čete 3. diverzantskog bataljona (caption; the record: Franjo zvani Franc)'),
    ('0161000044', '00003/541.pdf', 166, 773, (0.25, 0.12, 0.7, 0.42), 'MILAN BREZAK, desetar, killed by his own mine 4 May 1944 (caption; the record: desetar, fell 1944)'),
    ('0161000279', '00003/541.pdf', 195, 939, None, "MARIJAN PUTAK, delegat voda and zamjenik komesara čete of the diverzantski bataljon (caption); the roster's only Marijan Putak"),
    ('0162000196', '00003/543.pdf', 116, 475, None, '"Najmlađi tenkista Mihajlo Veljić" (caption); the battalion roster\'s only Mihajlo Veljić'),
    ('0161000262', '00003/541.pdf', 35, 169, (0.15, 0.0, 0.85, 0.42), 'PERO PILIPOVIĆ, prvi desetar i vodnik (caption beside it; the record: komandir voda, fell 1943)'),
    ('0161000043', '00003/541.pdf', 169, 789, (0.3, 0.03, 0.85, 0.42), "DRAGO BREZAK, intendant of the diverzantski bataljon (caption beside it); the roster's only Drago Brezak"),
    ('0161000341', '00003/541.pdf', 191, 905, (0.1, 0.0, 0.62, 0.4), "MILUTIN VIGNJEVIĆ, komandant 3. diverzantskog odreda (caption beside it); the roster's only one"),
    ('0162000163', '00003/543.pdf', 208, 861, (0, 0, 0.55, 1), '"Komandant bataljona kapetan Budislav Pribić" under the left photo'),
    ('0162000139', '00003/543.pdf', 208, 861, (0.62, 0.0, 1.0, 0.32), '"Politički komesar bataljona Milić Novaković" under the right photo'),
    ('0162000054', '00003/543.pdf', 277, 1167, (0.0, 0.05, 0.52, 0.9), '"Nikola Derikrava (levo)", politički komesar bataljona (caption); the roster\'s only one'),
    ('0162000127', '00003/543.pdf', 277, 1167, (0.5, 0.05, 1.0, 0.85), 'the man with Derikrava (levo): "politički komesar 1. tenkovske čete Ilija Mirković" (caption); the roster\'s only one'),
    ('0165000108', '00001/121_4.pdf', 19, 127, (0, 0, 0.46, 1), '"Ester Neli Jakovljević Zorka" under the left photo (the record: Neli, udata Ester, zvana Partizanka Zora)'),
    ('0165000451', '00001/121_7.pdf', 2, 7, None, 'VASILIJE ĐUROVIĆ ŽARKI, komandant of the 9. srpska (caption and record)'),
    ('0165000127', '00001/121_7.pdf', 6, 57, None, 'PETRONIJE JOVANOVIĆ PERA, zamenik komandanta (caption and record)'),
    ('0166000124', '00003/783.pdf', 93, 756, None, 'politkomisar bataljona in the 4. prekomorska (caption beside it and record)'),
    ('0166000022', '00003/783.pdf', 178, 1127, (0.18, 0.36, 0.75, 0.75), '"Sedi Adolf Dovžak, politkomisar čete", the one man seated (caption and record)'),
    ('0166000095', '00003/783.pdf', 217, 1295, (0.8, 0.08, 1.0, 0.6), '"Na desni Mihael Spolenak, komandant bataljona" (caption and record)'),
    ('0001011206', '00003/499.pdf', 181, 777, (0.5, 0.0, 1.0, 1.0), '"Marko Smajo i njegova četrnaestogodišnja kći Ankica" joined the Beogradski (VI) bataljon after Italy\'s capitulation (caption; the record: VI bataljon from September 1943)'),
    ('0001005975', '00003/499.pdf', 354, 1531, (0.0, 0.0, 0.36, 0.42), '"Milorad Lekić, na slici prvi levo gore", of the Beogradski bataljon (caption; the record: VI bataljon, komandant bataljona)'),
    ('0001009751', '00003/493.pdf', 682, 3261, None, 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Popović Petra Ivo, born 1914 in Cetinju (entry and record agree on the birth year and father and village)'),
    ('0001001841', '00003/493.pdf', 682, 3263, (0, 0.25, 1.0, 0.486), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Ćetković Petra Tomo, born 1882 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001005797', '00003/493.pdf', 682, 3263, (0, 0.503, 1.0, 0.74), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lagator Mata Špiro, born 1922 in Ugnjima (entry and record agree on the birth year and father and village)'),
    ('0001009721', '00003/493.pdf', 682, 3263, (0, 0.759, 1.0, 0.991), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Popivoda Milutina Petar, born 1918 in Lješevom Stupu (entry and record agree on the birth year and father and village)'),
    ('0001001536', '00003/493.pdf', 683, 3271, (0, 0.008, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Crnčević Rista Arsenije, born 1917 in Dupilu (entry and record agree on the birth year and father and village)'),
    ('0001001538', '00003/493.pdf', 683, 3275, (0.001, 0, 1, 0.919), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Crnčević Nika Petar, born 1921 in Dupilu (entry and record agree on the birth year and father and village)'),
    ('0001001552', '00003/493.pdf', 683, 3277, (0.001, 0.335, 1, 0.643), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Crvenko Tome Blažo, born 1914 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001001553', '00003/493.pdf', 683, 3277, (0.001, 0.673, 1, 0.98), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Crvenko Ilije Vlado, born 1923 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001013232', '00003/493.pdf', 683, 3281, (0.0, 0.015, 1, 0.926), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vojvodić Nika Gajo, born 1914 in Ljubotinju (entry and record agree on the birth year and father or village)'),
    ('0001005981', '00003/493.pdf', 683, 3285, (0.0, 0.671, 1, 0.973), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lekić Andrije Risto, born 1909 in Seocima (entry and record agree on the birth year and father and village)'),
    ('0001000553', '00003/493.pdf', 683, 3287, (0.0, 0.015, 0.999, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Barjamović Mila Jovan, born 1914 in Orahovu (entry and record agree on the birth year and father and village)'),
    ('0001001015', '00003/493.pdf', 683, 3291, (0, 0.007, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Borozan Laza Pavle, born 1907 in Bokovu (entry and record agree on the birth year and father and village)'),
    ('0001003208', '00003/493.pdf', 684, 3299, (0.0, 0.11, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Gazivoda Vasa Petar, born 1906 in Rvašima (entry and record agree on the birth year and father and village)'),
    ('0001004781', '00003/493.pdf', 684, 3303, (0, 0.007, 1, 0.985), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Jovićević Joka Pavle, born 1914 in Češljarima (entry and record agree on the birth year and father and village)'),
    ('0001001897', '00003/493.pdf', 684, 3309, (0, 0.023, 1.0, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Dabanović Labuda Špiro, born 1899 in Seocima (entry and record agree on the birth year and father and village)'),
    ('0001001962', '00003/493.pdf', 684, 3311, (0, 0.117, 1, 0.877), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Dapčević Andrije Ivo, born 1916 in SAD (entry and record agree on the birth year and father or village)'),
    ('0001002696', '00003/493.pdf', 684, 3315, (0, 0.348, 0.999, 0.649), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukanović Krsta Nikola, born 1919 in Građanima (entry and record agree on the birth year and father and village)'),
    ('0001002696', '00003/493.pdf', 684, 3315, (0, 0.348, 0.999, 0.649), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukanović Krsta Nikola, born 1919 in Građanima (entry and record agree on the birth year and father or village)'),
    ('0001005349', '00003/493.pdf', 684, 3317, (0.0, 0.022, 1, 0.315), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Kostić Draga Đoko, born 1912 in Rvašima (entry and record agree on the birth year and father and village)'),
    ('0001005967', '00003/493.pdf', 684, 3317, (0.0, 0.368, 1, 0.664), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lekić Joka Blažo, born 1914 in Seocima (entry and record agree on the birth year and father and village)'),
    ('0001005982', '00003/493.pdf', 684, 3317, (0.0, 0.704, 1, 1.0), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lekić Joka Risto, born 1897 in Seocima (entry and record agree on the birth year and father and village)'),
    ('0001200515', '00003/493.pdf', 685, 3331, None, 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Martinović-Vujović Vasa Danica, born 1913 in Bajicama (entry and record agree on the birth year and father or village)'),
    ('0001009084', '00003/493.pdf', 685, 3339, (0.001, 0.0, 0.999, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Pejaković Stevana Vlado, born 1912 in Pačarađima (entry and record agree on the birth year and father and village)'),
    ('0001006834', '00003/493.pdf', 685, 3341, None, 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Mašanović Mila Božidar, born 1919 in Orahovu (entry and record agree on the birth year and father and village)'),
    ('0001012383', '00003/493.pdf', 686, 3357, (0, 0, 1, 0.984), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Tatar Sava Labud, born 1909 (entry and record agree on the birth year and father or village)'),
    ('0001200965', '00003/493.pdf', 686, 3361, (0.0, 0.015, 1.0, 0.999), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Tomović Đura Jovo, born 1905 in Podgoru (entry and record agree on the birth year and father or village)'),
    ('0001013231', '00003/493.pdf', 686, 3367, (0.001, 0.007, 0.999, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vojvodić Ilije Đuro, born 1921 in Radomiru (entry and record agree on the birth year and father and village)'),
    ('0001013237', '00003/493.pdf', 686, 3371, (0.0, 0.535, 1, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vojvodić Jova Veliša, born 1916 in Radomiru (entry and record agree on the birth year and father and village)'),
    ('0001010147', '00003/493.pdf', 686, 3379, (0, 0.129, 1, 0.98), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Radoman Stevana Marko, born 1910 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001200826', '00003/493.pdf', 686, 3383, (0.0, 0.008, 1, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Radulović Nikole Jovo, born 1906 in Komanima (entry and record agree on the birth year and father or village)'),
    ('0001010677', '00003/493.pdf', 686, 3385, (0.0, 0.107, 1, 0.887), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Rolović Nika Vladimir, born 1916 in Brčelima (entry and record agree on the birth year and father and village)'),
    ('0001012005', '00003/493.pdf', 686, 3387, (0.0, 0.008, 0.999, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Šaban Pera Vido, born 1912 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001013444', '00003/493.pdf', 687, 3399, (0, 0.253, 1.0, 0.491), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vujović Mila Marko, born 1898 in Ljubotinju (entry and record agree on the birth year and father and village)'),
    ('0001013506', '00003/493.pdf', 687, 3399, (0, 0.509, 1.0, 0.745), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vukičević Jovana Milutin, born 1920 in Ljubotinji (entry and record agree on the birth year and father and village)'),
    ('0001013339', '00003/493.pdf', 687, 3401, (0, 0.019, 1.0, 0.488), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vučković Kosta Blažo, born 1914 in Prekornici (entry and record agree on the birth year and father and village)'),
    ('0001200772', '00003/493.pdf', 687, 3405, (0.0, 0.007, 1, 0.988), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Popović Iva Jovo, born 1915 in Očinići-ma (entry and record agree on the birth year and father or village)'),
    ('0001200005', '00003/493.pdf', 687, 3407, (0, 0.007, 0.999, 0.941), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Abramović Đorđa Vojo, born 1914 in Bjelicama (entry and record agree on the birth year and father or village)'),
    ('0001000417', '00003/493.pdf', 687, 3409, (0.001, 0.008, 1.0, 0.999), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bajagić Nikole Milić, born 1916 in Morači (entry and record agree on the birth year and father and village)'),
    ('0001005564', '00003/493.pdf', 688, 3423, (0.0, 0.134, 1, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Krivokapić Vasa Miloš, born 1912 in Donjoj Zaljuti (entry and record agree on the birth year and father and village)'),
    ('0001006570', '00003/493.pdf', 688, 3427, (0.001, 0.008, 1, 1.0), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Marinović Mata Đuro, born 1909 in Očinićima (entry and record agree on the birth year and father and village)'),
    ('0001000457', '00003/493.pdf', 688, 3429, (0.0, 0, 0.999, 0.465), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bajović Laza Filip, born 1912 in Bjelicama (entry and record agree on the birth year and father and village)'),
    ('0001000608', '00003/493.pdf', 688, 3429, (0.0, 0.532, 0.999, 0.996), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Batrićević Joka Pavle, born 1908 in Očinićima (entry and record agree on the birth year and father and village)'),
    ('0001000744', '00003/493.pdf', 688, 3435, (0.001, 0.124, 1.0, 0.889), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bigović Sava Milan, born 1909 in Trnjine (entry and record agree on the birth year and father and village)'),
    ('0001000995', '00003/493.pdf', 688, 3437, (0.001, 0.008, 1, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Boreta Nika Joko, born 1908 in Bečićima (entry and record agree on the birth year and father and village)'),
    ('0001002699', '00003/493.pdf', 688, 3439, (0, 0, 1.0, 0.456), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukanović Nikole Savo, born 1922 in Bjelicama (entry and record agree on the birth year and father or village)'),
    ('0001003037', '00003/493.pdf', 688, 3439, (0, 0.53, 1.0, 0.985), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Franović Luke Miloš, born 1907 in Reževićima (entry and record agree on the birth year and father and village)'),
    ('0001002049', '00003/493.pdf', 688, 3441, (0, 0.0, 1, 0.999), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Derviš Nika Mato, born 1912 in Cetinju (entry and record agree on the birth year and father and village)'),
    ('0001009719', '00003/493.pdf', 689, 3453, (0, 0.003, 1, 0.441), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Popivoda Marka Blažo, born 1911 in Lješevom Stupu (entry and record agree on the birth year and father and village)'),
    ('0001009806', '00003/493.pdf', 689, 3455, (0.0, 0.007, 1, 0.308), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Popović Krsta Radovan, born 1922 in Cucima (entry and record agree on the birth year and father or village)'),
    ('0001011338', '00003/493.pdf', 689, 3455, (0.0, 0.348, 1, 0.652), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Srzentić Steva Špiro, born 1916 in Petrovcu (entry and record agree on the birth year and father and village)'),
    ('0001011441', '00003/493.pdf', 689, 3455, (0.0, 0.696, 1, 0.998), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Stanišić Nikola Marko, born 1908 in Mainama (entry and record agree on the birth year and father and village)'),
    ('0001006577', '00003/493.pdf', 689, 3457, (0, 0.007, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Marinović Blaža Nikola, born 1912 in Očinićima (entry and record agree on the birth year and father and village)'),
    ('0001006806', '00003/493.pdf', 689, 3461, (0.0, 0.006, 1, 0.869), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Martinović Marka Ljubo, born 1920 in Bajicama (entry and record agree on the birth year and father and village)'),
    ('0001006975', '00003/493.pdf', 689, 3463, (0, 0.014, 1, 0.901), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Medigović Jova Krsto, born 1914 in Paštrovićima (entry and record agree on the birth year and father and village)'),
    ('0001007043', '00003/493.pdf', 689, 3465, (0, 0.005, 1, 0.305), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Mićunović Mitra Mirko, born 1918 in Cetinju (entry and record agree on the birth year and father and village)'),
    ('0001008974', '00003/493.pdf', 689, 3465, (0, 0.697, 1, 0.997), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Pavićević  Miroje, born 1914 in Danilovgradu (entry and record agree on the birth year and father or village)'),
    ('0001012003', '00003/493.pdf', 690, 3475, None, 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Šaban Jovana Dušan, born 1920 in Podgorici (entry and record agree on the birth year and father or village)'),
    ('0001012207', '00003/493.pdf', 690, 3477, (0, 0.005, 0.999, 0.492), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Špadijer  Špiro, born 1914 in Donjem kraju (entry and record agree on the birth year and father or village)'),
    ('0001013724', '00003/493.pdf', 690, 3477, (0, 0.523, 0.999, 1.0), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Zenović Andrija Marko, born 1912 in Reževićima (entry and record agree on the birth year and father and village)'),
    ('0001013490', '00003/493.pdf', 690, 3479, (0, 0.349, 1, 0.667), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vukčević Pera Đoko, born 1915 in Cetinju (entry and record agree on the birth year and father and village)'),
    ('0001013725', '00003/493.pdf', 690, 3479, (0, 0.682, 1, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Zenović Đura Milan, born 1912 in Reževićima (entry and record agree on the birth year and father and village)'),
    ('0001200038', '00003/493.pdf', 691, 3491, (0.001, 0.021, 1, 0.875), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bakočević Radovana Branka, born 1923 in U ž i c u (entry and record agree on the birth year and father or village)'),
    ('0001000467', '00003/493.pdf', 691, 3493, (0, 0.007, 1, 0.875), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bakić Radosava Radovan, born 1913 in Vrujcima (entry and record agree on the birth year and father and village)'),
    ('0001000956', '00003/493.pdf', 691, 3495, (0, 0.503, 0.999, 0.937), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bojović  Milorad, born 1913 in Bijelom Polju (entry and record agree on the birth year and father or village)'),
    ('0001000959', '00003/493.pdf', 691, 3497, (0, 0.007, 1, 0.894), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Bojović Jovana Strado, born 1918 in Bojovićima (entry and record agree on the birth year and father and village)'),
    ('0001000996', '00003/493.pdf', 691, 3499, (0, 0.008, 1.0, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Boričić Vranov Milo, born 1922 in Babinu (entry and record agree on the birth year and father and village)'),
    ('0001001864', '00003/493.pdf', 691, 3505, (0.0, 0.539, 1, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Ćorac Novaka Svetozar, born 1913 in Dapsićima (entry and record agree on the birth year and father and village)'),
    ('0001002708', '00003/493.pdf', 692, 3519, (0, 0.039, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukić Radoja Gojko, born 1922 in Polici (entry and record agree on the birth year and father and village)'),
    ('0001201147', '00003/493.pdf', 692, 3521, (0.001, 0.016, 1, 1.0), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukić  Milija, born 1910 in Polici (entry and record agree on the birth year and father or village)'),
    ('0001002736', '00003/493.pdf', 692, 3523, (0, 0.011, 1, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Đukić Mihajla Vuksan, born 1916 in Bjelojevićima (entry and record agree on the birth year and father and village)'),
    ('0001004150', '00003/493.pdf', 692, 3527, (0, 0.536, 1, 0.989), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Janković Vikote Rajko, born 1923 in Žircima (entry and record agree on the birth year and father and village)'),
    ('0001002306', '00003/493.pdf', 692, 3529, (0, 0.184, 0.999, 0.317), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Dragović Šćepana Jakša, born 1910 in Ćulićima (entry and record agree on the birth year and father or village)'),
    ('0001002011', '00003/493.pdf', 692, 3529, (0, 0.853, 0.999, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Dedeić Stevana Boško, born 1907 in Štitarci (entry and record agree on the birth year and father and village)'),
    ('0001004798', '00003/493.pdf', 693, 3539, (0.0, 0.069, 1.0, 0.468), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Jovović Jovana Vojo, born 1915 in Kosiću (entry and record agree on the birth year and father and village)'),
    ('0001006182', '00003/493.pdf', 693, 3543, (0, 0.007, 0.999, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lutovac Mijajla Milun, born 1916 in Dapsićima (entry and record agree on the birth year and father and village)'),
    ('0001006076', '00003/493.pdf', 693, 3547, (0.001, 0.007, 1.0, 0.439), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lončarević Maksima Đuro, born 1920 in Gusinju (entry and record agree on the birth year and father and village)'),
    ('0001006842', '00003/493.pdf', 693, 3549, (0.0, 0.087, 1.0, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Mašković Sekule Savo, born 1914 in Osredce (entry and record agree on the birth year and father and village)'),
    ('0001005316', '00003/493.pdf', 693, 3551, (0, 0.008, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Korać  Rajko, born 1916 in Koraćima (entry and record agree on the birth year and father or village)'),
    ('0001006181', '00003/493.pdf', 693, 3553, (0, 0.048, 1, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Lutovac Vuka Dragutin, born 1922 in Dapsićima (entry and record agree on the birth year and father and village)'),
    ('0001008265', '00003/493.pdf', 693, 3557, (0.0, 0.0, 0.999, 0.993), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Nedić Obrada Dušan, born 1901 in Pešci (entry and record agree on the birth year and father and village)'),
    ('0001012066', '00003/493.pdf', 694, 3565, (0.001, 0.181, 1, 0.333), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Šćepanović Pera Boriša, born 1921 in Kolašinu (entry and record agree on the birth year and father and village)'),
    ('0001012668', '00003/493.pdf', 694, 3565, (0.001, 0.363, 1, 0.51), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Tošić Milovana Branko, born 1920 in Kolašinu (entry and record agree on the birth year and father and village)'),
    ('0001200644', '00003/493.pdf', 694, 3573, (0.001, 0.007, 1.0, 0.15), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Nešović Milisava Mila, born 1924 in Užicu (entry and record agree on the birth year and father or village)'),
    ('0001010413', '00003/493.pdf', 694, 3573, (0.001, 0.344, 1.0, 0.492), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Rakočević Mirka Milić, born 1914 in Štitarici (entry and record agree on the birth year and father and village)'),
    ('0001010416', '00003/493.pdf', 694, 3573, (0.001, 0.516, 1.0, 0.662), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Rakočević Marka Savo, born 1913 in Mušovića Rijeci (entry and record agree on the birth year and father and village)'),
    ('0001011128', '00003/493.pdf', 694, 3573, (0.001, 0.685, 1.0, 0.831), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Simonović Milete Danilo, born 1920 in Kolašinu (entry and record agree on the birth year and father and village)'),
    ('0001013195', '00003/493.pdf', 695, 3581, (0.0, 0.007, 1, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vlahović Mitra Dragutin, born 1912 in Trmanji (entry and record agree on the birth year and father and village)'),
    ('0001013196', '00003/493.pdf', 695, 3583, (0, 0.0, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vlahović Milinkov Dušan, born 1910 in Trmanji (entry and record agree on the birth year and father and village)'),
    ('0001201004', '00003/493.pdf', 695, 3585, (0, 0.016, 1.0, 1), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vlahović Milinka Dunja, born 1914 in Trmanji (entry and record agree on the birth year and father or village)'),
    ('0001013197', '00003/493.pdf', 695, 3587, (0.0, 0.0, 0.999, 0.466), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vlahović Radosava Milija, born 1908 in Trmanji (entry and record agree on the birth year and father and village)'),
    ('0001013200', '00003/493.pdf', 695, 3587, (0.0, 0.537, 0.999, 1.0), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vlahović Dragiše Vuko, born 1906 in Trmanji (entry and record agree on the birth year and father and village)'),
    ('0001014065', '00003/493.pdf', 695, 3593, (0, 0.0, 1, 0.992), 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Žurić Luke Miloš, born 1919 in Bjelojevićima (entry and record agree on the birth year and father and village)'),
    ('0001013427', '00003/493.pdf', 695, 3595, None, 'roster of 21 December 1941 at Rudo, a portrait beside each entry: Vujošević Vučića Dušan, born 1912 in Ivangradu (entry and record agree on the birth year and father and village)'),
    ('0002000623', '00001/137_5.pdf', 18, 95, None, '"Antun Borić Tona", the record\'s zvani Tona (the book\'s own roster)'),
    ('0002002166', '00001/137_10.pdf', 16, 111, None, '"Bogdan Gašeća, referent saniteta 3. bataljona"; the record: referent saniteta, 3. kordunaški bataljon'),
    # "Narodni heroji Gradnikove brigade" (Petelin, book pp. 794-799): a portrait beside each hero's biography
    ('0064000657', '00003/825.pdf', 794, 4183, None, 'narodni heroj of the brigade, the portrait beside the biography: DRAGO FLIS-STRELA (the record: zvani Strela)'),
    ('0064001659', '00003/825.pdf', 795, 4188, None, 'narodni heroj of the brigade, the portrait beside the biography: IVAN LIKAR-SOČAN (the record: zvani Sočan)'),
    ('0064001927', '00003/825.pdf', 795, 4189, None, 'narodni heroj of the brigade, the portrait beside the biography: JOŽE MIHEVC-RUDAR (the record: zvani Rudar)'),
    ('0064002015', '00003/825.pdf', 796, 4194, None, 'narodni heroj of the brigade, the portrait beside the biography: CVETO MOČNIK-FLORJAN (the record: zvani Florjan)'),
    ('0141000419', '00003/825.pdf', 796, 4194, None, "narodni heroj of the brigade, the portrait beside the biography: CVETO MOČNIK-FLORJAN: the Šercerjeva's Močnik Cveto zvani Florjan, who holds the XXXI. divizija's entry of the same post"),
    ('0064010019', '00003/825.pdf', 796, 4195, None, 'narodni heroj of the brigade, the portrait beside the biography: DRAGO MASLO (the record holds the biography)'),
    ('0064001840', '00003/825.pdf', 796, 4195, None, "narodni heroj of the brigade, the portrait beside the biography: DRAGO MASLO: the roster's Maslo Karlo zvani Drago, born 1912 at Ostrožno brdo, as the biography"),
    ('0067000726', '00003/825.pdf', 796, 4195, None, "narodni heroj of the brigade, the portrait beside the biography: DRAGO MASLO: the Istrski odred's Maslo Karlo, its komandant from 27. 12. 1943 (zvani Drago), born 1912 at Ostrožno brdo"),
    ('0064010022', '00003/825.pdf', 797, 4200, None, 'narodni heroj of the brigade, the portrait beside the biography: DUŠAN MUNIH-DARKO (the record holds the biography)'),
    ('0064002438', '00003/825.pdf', 797, 4201, None, 'narodni heroj of the brigade, the portrait beside the biography: FRANC POKOVEC-POKI (the record: zvani Poki)'),
    ('0064003449', '00003/825.pdf', 798, 4206, None, 'narodni heroj of the brigade, the portrait beside the biography: MIHAELA ŠKAPIN-DRINA (the record: zvana Drina)'),
    ('0064002897', '00003/825.pdf', 798, 4207, None, 'narodni heroj of the brigade, the portrait beside the biography: FRANC TAVČAR-ROK (the record: zvani Rok)'),
    ('0070001315', '00003/825.pdf', 798, 4207, None, "narodni heroj of the brigade, the portrait beside the biography: FRANC TAVČAR-ROK: the Tomšičeva's Tavčar Franc zvani Rok, born 1920, who holds the same Moste-Polje and XXXI. divizija entries"),
    ('0064003055', '00003/825.pdf', 799, 4212, None, 'narodni heroj of the brigade, the portrait beside the biography: JANEZ UČAKAR (the record holds the biography)'),
]

PAGE_BOOKS = [
    # As UNIT_BOOKS, where the book stores one photo as several strips or prints several side by side: the photo is cut
    # from the page itself. Soldier, the unit's own book on znaci.org, its PDF page, the photo's box on the page (a part of
    # a group where the caption says which man: "(desno)", "s desna", "prvi sa desna"), the caption printed with it.
    ('0093000210', '00001/280_12.pdf', 34, (240.8, 36.6, 357.4, 197.9), 'DRAGOLJUB RADOSAVLJEVIĆ TO- PJ1ICA, rođen 1919. godine u Prokup- lju, metalski radnik. Pripadao je na- prednom…'),
    ('0093000015', '00001/280_12.pdf', 35, (95.9, 341.8, 213.6, 504.2), 'JELISAVETA ANDREJEVIĆ ANE- TA-MILENA, rođena 1923. godine u Beogradu, radnica. U SKOJ-u od 1940. godine. Stupi…'),
    ('0040001272', '00001/148_11.pdf', 19, (200.4, 61.3, 353.2, 230.0), 'Simo Simonović, komandir Prateće čete brigade, poginuo avgusta 1944. prilikom prelaska Ibra.'),
    ('0106000190', '00003/537.pdf', 852, (134.3, 151.7, 291.2, 350.4), 'Milutin Vasović, komesar čete naših ranjenika u Italiji, poginuo od podmetnute bomba 1945. u jednom bioskopu u…'),
    ('0094010004', '00003/546.pdf', 82, (303.3, 372.6, 484.7, 669.3), 'Boris Balaš, komandant Karlovačke udarne brigade od 8. 7. 1944. do 10. 4. 1945. i od 26. 4. 1945. do oslobođen…'),
    ('0094000921', '00003/546.pdf', 276, (308.9, 156.8, 501.4, 437.2), 'lelno s cestom na udaljenju 150—200 metara, sa zadatkom da izbije što bliže s. Luka, a potom s prostorije Zavi…'),
    ('0106000104', '00003/537.pdf', 835, (128.6, 396.0, 294.8, 610.6), 'Tomaš Miličić, komandir 3. čete 4. bataljona, poginuo 25. I 1945. kod Goražda | Komanda 1. čet1 4. paga.nopa. …'),
    ('0058000377', '00003/558.pdf', 408, (108.0, 400.3, 280.8, 686.2), 'Ljubomir Crnkovič, operativni oficir Udarnog bataljona "Matija Gubec". Ranije Odredu bio vodnik voda i komandi…'),
    ('0054003145', '00001/168_1.pdf', 25, (31.5, 278.7, 210.1, 550.2), 'Janko Toljagić, zam. pol. komesara čete u 2. bataljonu, poginuo 30. 8. 1944. kod Vlasenice.'),
    ('0054002869', '00001/168_2.pdf', 43, (241.4, 122.6, 390.0, 349.4), 'Mirko Srdić, pol. komesar čete u 3. bat., poginuo maja 1945. kod Bjelovara.'),
    ('0093000243', '00001/280_11.pdf', 4, (60.7, 207.9, 179.5, 359.8), 'P^čodije Stojanović Tatko, politički komesar od septembra 1941. do februara 1942. g. Poginuo 13. avgusta 1942.…'),
    ('0106000124', '00003/537.pdf', 812, (219.0, 417.6, 378.8, 625.2), 'Todor Nedić, komesar 1. čete 1. bataljona, poginuo u Lekovini 12. decembra 1943. | Komesar 3. bataljona Đoko K…'),
    ('0094000535', '00003/546.pdf', 82, (302.6, 137.9, 482.8, 341.2), 'Franjo Molek, komandant Karlovačke brigade od 5. 3. do 30. 6. 1944. Umro 2. 7. 1944. od zadobivenih rana.'),
    ('0056001531', '00003/579.pdf', 365, (407.5, 157.7, 507.0, 390.3), 'Ljuboje Panić (prvi sa desna), komandir čete iz 1. bataljona, poginuo januara 1944, naRudanci. Dvije drugarice…'),
    ('0055000597', '00001/274_7.pdf', 43, (181.7, 163.0, 335.9, 357.0), 'Petrović Svetislav »Piki« Milosavljević Ljuba, komandir komesar čete, zatim bataljona čete u 17. brigadi briga…'),
    ('0054000504', '00001/168_1.pdf', 20, (225.0, 15.0, 406.0, 232.0), 'Milan Egić, nar. heroj, k-dant 1. b., pog. na Viševicama 24. 8. 1943.'),
    ('0052000339', '00001/251_3.pdf', 3, (8.3, 49.9, 159.5, 287.9), 'Nakon okupacije zemlje Mirko je kao član Sreskog rukovod- stva Komunističke partije Jugoslavije u Bijeljini, b…'),
    ('0098000686', '00001/271_4.pdf', 39, (148.0, 16.9, 291.8, 226.4), 'Radisav Zečević, intendant 1. bataljona 4. brigade sa devojkama iz s. Krće 1944.'),
    ('0057000376', '00001/70_2.pdf', 10, (71.8, 89.1, 197.5, 270.2), 'smeštaja boraca, počivala je na pozadini. Narod je preio svojih NOO, organizacija NOP i vojno-pozadinskih usta…'),
    ('0111011430', '00002/427.pdf', 185, (388.5, 609.1, 562.7, 829.4), 'Pomoćnik komesara ?.. bataljona 7. vojvođanske brigade Bora Vezilic ra njen u jurišu na kotu 169. Umro od zado…'),
    ('0094000229', '00003/546.pdf', 141, (95.2, 150.6, 289.6, 484.9), 'dobrovoljnoj osnovi, uz davanje potvrde od strane Kotarskog NOO-a nad- ležnog za ovo područje. | Ivica Graho, …'),
    ('0062001263', '00003/782.pdf', 833, (196.8, 100.8, 331.7, 293.0), 'Številčno stanje je od 9. do 27. oktobra 1944 padlo kar za 183 borcev. To so bili največ mrtvi in pogrešani iz…'),
    ('0077000057', '00001/185_6.pdf', 24, (318.0, 514.4, 441.4, 670.3), '111 | Mirko Arsenijević - Glibo, politički komesar, narodni heroj'),
    ('0100000805', '00001/270_4.pdf', 39, (250.8, 135.0, 450.6, 409.7), 'Sa defilea oslobodilaca Mostara, sredinom februara 1945. | Komandant Trinaeste brigade Milorad Kujačić u selu …'),
    ('0055000599', '00001/274_7.pdf', 40, (139.1, 444.4, 287.8, 631.6), 'Petrović Živorad »Žika Bri- ca« sekretar sreskog komiteta za Pasjački srez u vreme formi- ranja i drugi po red…'),
    ('0082002279', '00001/81_4.pdf', 157, (76.9, 53.3, 208.3, 211.7), 'Rođen je 16. maja 1920. u Boviću, Kordun, u zemljorad- ničkoj porodici. Posle osnovne škole i niže gimnazije, …'),
    ('0106000231', '00003/537.pdf', 816, (127.5, 162.4, 293.7, 369.0), 'Dragutin Đurović, luškomitralje- zac u 2. četi 3. bataljona, ranjen 11. marta u selu Cerovo i podlegao ranama …'),
    ('0058000816', '00003/558.pdf', 6, (220.5, 157.0, 363.5, 356.5), 'Joža Horvat, prvi komesar Katoličkoga partizanskog odreda'),
    ('0063000163', '00003/814.pdf', 390, (210.0, 99.6, 340.3, 248.6), 'tijska organizacija si je zelo prizadevala pripraviti novince za sprejem v partijo, in jih seznaniti z delom i…'),
    ('0054002688', '00001/168_2.pdf', 51, (192.4, 20.8, 340.4, 232.2), 'Marko Repajić, pm 1. bat., poginuo 3. I. 1944. na B. Luci'),
    ('0129010052', '00001/190_6.pdf', 3, (310.4, 210.2, 439.0, 406.4), 'SI. 5 Komandant brigade Ni- kola Dolinić — Pitomi.'),
    ('0129010160', '00001/190_6.pdf', 7, (311.4, 208.7, 438.5, 396.6), 'SI. 13 Komandant 1. bataljona, Uroš Marković.'),
    ('0083010129', '00001/252_8.pdf', 36, (227.2, 338.0, 361.9, 528.0), 'VLADO OBRADOVIC KAMENI Komandant 3. bataljona od 1. maja do 2. juna 1944.'),
    ('0095000485', '00003/544.pdf', 180, (75.0, 86.1, 181.5, 250.7), 'zaustavili su dalje nadiranje 2. i 4. bataljona 14. brigade. Na intervenciju Štaba 13. divizije bataljoni su i…'),
    ('0056002144', '00003/579.pdf', 376, (488.4, 232.0, 561.0, 420.0), 'Ivanko Timkov. intendant brigade.'),
    ('0056001715', '00003/579.pdf', 376, (378.8, 477.5, 561.1, 781.6), 'Milenko Radomirović. pomoćnik obavje- štajnog oficira brigade, poginuo od četnika 1947.'),
    ('0056000513', '00003/579.pdf', 390, (307.0, 427.5, 461.8, 637.0), 'Dimitrije Grubač, jedan od starješina u | Nikola Garača. zamjenik k-đanta brigade u drugoj polovini 1944.'),
    ('0063000200', '00003/814.pdf', 173, (166.1, 96.5, 294.7, 263.8), 'Franc Turner-Kostja, brigadni po- Lojze Colarič, politični komisar litični komisar brigade'),
    ('0010100428', '00003/394.pdf', 9, (89.0, 105.0, 367.0, 509.0), '. NIKOLA KARANOVIC — KARAN komandant Brigade'),
    ('0161000190', '00003/541.pdf', 158, (96.0, 125.0, 298.0, 409.0), 'LIKER FRANJO, komandir vo- da 1. čete 3. div. bataljona | FRANC VULINEC komandir 1. čete 3. diverzantskog ba- …'),
    ('0161000252', '00003/541.pdf', 192, (115.3, 246.0, 305.4, 511.4), '6. Intendant bataljona Drago Brezak. 7. Oficir Ozne Branko Lazarus. 8. Rukovodilac Skoja Miro Trenski. 9. Zemu…'),
    ('0056000793', '00003/579.pdf', 65, (93.0, 453.0, 268.0, 699.0), 'Kojo Jotić, jedan od organizatora ustanka za- padno od Doboja. U brigadi prvi politički | Stoje: Pero Kulundži…'),
    ('0147000023', '00003/607.pdf', 85, (602.0, 622.0, 849.0, 972.0), 'Đuro Ban Mile, organizacioni sekretar Okružnog komiteta KPH Zagreb. | Fašistički razbojnici oduzeli su ženi sv…'),
    ('0147000189', '00003/607.pdf', 117, (600.0, 546.0, 779.0, 806.0), 'Stevan Došen, prvi komandant Zagrebačkog partizanskog odreda poginuo 21. prosinca 1944. kao komandant brigade …'),
    ('0147000559', '00003/607.pdf', 118, (313.0, 659.0, 495.0, 913.0), 'Milan Kuren Gubec, prvi komesar Zagrebač- kog partiznaskog odreda. | Zapaža se previranje među članovima HSS, …'),
    ('0147000334', '00003/607.pdf', 121, (608.0, 613.0, 790.0, 874.0), 'Mirko Herak Gorski, prvi zamjenik komesara Zagrebačkog partizanskog odreda, poginuo u Oborovu 29. ožujka 1944.…'),
    ('0147000183', '00003/607.pdf', 95, (622.9, 758.2, 803.8, 1023.7), 'Mijo Domiter Zima, prvi komesar Prigorske čete, poginuo u Lipovčanima — Moslavina 28. 3. 1944. | Za zamjenika …'),
    ('0168010007', '00003/652_2.pdf', 54, (101.0, 125.0, 271.0, 357.0), 'St. 105- Major Franc Podboj, prvi koman- SI. 106 - Major Niko Srzić, drugi i posljed- dant IV POS-a nji komand…'),
    ('0168001385', '00003/652_2.pdf', 54, (101.0, 424.0, 272.0, 655.0), 'SI. 107 - Josip Ilić Suro, prvi politički ko\xad mesar IV POS-a Si. 108 - Branimir Radelić, drugi politički komes…'),
    ('0168002490', '00003/652_2.pdf', 55, (139.0, 431.0, 308.0, 662.0), 'Si. 111 - Benko Matulić posljednji politički komesar IV POS-a SI. 112 - Narodni heroj Vlado Bagat, po\xad moćnik …'),
    ('0061002010', '00003/767.pdf', 785, (328.0, 241.0, 437.0, 397.0), 'Vekoslav Robič, politicai komisar brigade Stanko Mahne, komandant brigade'),
    ('0069000263', '00003/775.pdf', 174, (422.8, 379.0, 531.0, 660.5), 'Lojze Dolničar (desno), pomoćnik političnega komisarja 4. in 2. bataljona, in kurir Ciril Gregor, 1945'),
    ('0093000219', '00001/280_11.pdf', 6, (51.7, 353.6, 168.3, 504.5), 'Radoš Jovanović Selja, sekretar Poverenstva KPJ za Toplicu i partijski rukovodilac u Odredu jula 1942. g. | Mi…'),
    ('0094000788', '00003/546.pdf', 84, (143.4, 166.3, 263.4, 336.2), 'STAB BRIGADE: komandant Franjo Molek/1 politički komesar Petar Erdeljac,5 pomoćnik političkog komesara Rafael …'),
    ('0094010405', '00003/546.pdf', 193, (83.4, 149.9, 275.2, 486.4), 'uzimanja nove dužnosti, dok je privremeni vršilac dužnosti operativnog oficira brigade poručnik Viktor Furdek …'),
    ('0094000416', '00003/546.pdf', 279, (99.5, 164.8, 281.2, 461.6), 'vodnika pontonirskog voda Josip Plesa, za političkog delegata pontonir- skog voda Ilija Vajagić i za političko…'),
    ('0055000500', '00001/274_7.pdf', 41, (171.6, 160.6, 322.4, 355.4), 'Nestorović Ljubinko »Ozren«, Lazarević Radivoje, načelnik • drugi po redu komesar 17. bri- štaba 17. brigade o…'),
    ('0055000669', '00001/274_7.pdf', 65, (329.4, 159.3, 478.8, 360.5), 'Nikolić Stojan Rančić Vukoje, prvi intendant 17. brigade'),
    ('0086000453', '00003/477.pdf', 202, (277.2, 305.2, 360.8, 544.3), 'S desna Radosav Nikić, zamenik komandanta 4. bataljona | U oslobođenom Leskovcu, oktobar 1944. S leva: Vukman …'),
    ('0161000374', '00003/541.pdf', 33, (269.8, 273.2, 475.8, 545.3), 'SVETLIČIĆ IVAN »ORSI«, rodom iz sela G. Šarampov kod Ivanić- Grada, radnik Hrvat, član KP, prvi diverzant u Mo…'),
    ('0054001192', '00001/168_2.pdf', 40, (117.5, 83.1, 213.8, 250.8), 'Miloš Končar, k-dant 1. bat. (desno), kraj rata 1945.'),
    ('0054003600', '00001/168_2.pdf', 47, (143.2, 127.1, 216.5, 352.5), 'Rade Čekić, k-dant 1. bat. (desno), sa Ljubanom Ševićem, iz 5. brigade i Desom Milić-Vasić.'),
    ('0054001274', '00001/168_2.pdf', 51, (91.5, 53.2, 166.5, 234.6), 'Grupa automatičara brigade, SF — 1945. | Nikola Kovrlija (desno), zam. komesara 1. bat.'),
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
    # third batch
    ('0002000267', 'Ante_Banina.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Ante Banina, narodni heroj: birth year 1915'),
    ('0006000327', 'Ante_Banina.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Ante Banina, narodni heroj: birth year 1915'),
    ('0047000025', 'Ante_Banina.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Ante Banina, narodni heroj: birth year 1915'),
    ('0039100106', 'Boško_Buha,_1942.jpg', (0.1, 0, 0.9, 0.49), 'Public domain', '', 'Boško Buha, narodni heroj: birth year 1926; year 1941'),
    ('0005101136', 'Boško_Đuričković.jpg', (0.1, 0.18, 0.85, 0.7), 'Public domain', '', 'Boško Đuričković, narodni heroj: birth year 1914; birthplace danilovgrad'),
    ('0041000367', 'Dragiša_Ivanović,_politkom_Pete_crnogorske_brigade.jpg', (0, 0, 0.91, 0.864), 'Public domain', 'Žorž Skrigin', 'Dragiša Ivanović, narodni heroj: birth year 1914; birthplace sjenice'),
    ('0026000296', 'Dušan_Jerković_heroj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Dušan Jerković, narodni heroj: birth year 1914; birthplace ogar; year 1941'),
    ('0039000287', 'Dušan_Ječmenić.jpg', (0, 0, 1, 1), 'Public domain', '', 'Dušan Ječmenić, narodni heroj: birth year 1911'),
    ('0040010906', 'Jelica_Maskovic.jpg', (0, 0, 1, 1), 'Public domain', '', 'Jelica Mašković, narodni heroj: birth year 1924; birthplace plane; year 1942'),
    ('0110001685', 'Koča-Popovic.png', (0.119, 0, 0.923, 0.776), 'Public domain', '', 'Koča Popović, narodni heroj: birth year 1908; birthplace beograd'),
    ('0093000135', 'Kiril_Mihajlovski.jpg', (0, 0, 1, 1), 'Public domain', '', 'Kiril Mihajlovski, narodni heroj: birth year 1916'),
    ('0046001083', 'Ljubo_Truta.jpg', (0.006, 0.066, 1, 0.739), 'Public domain', '', 'Ljubo Truta, narodni heroj: birth year 1915; birthplace zlarin'),
    ('0015000042', 'Miloš_Dudić.jpg', (0.05, 0.05, 0.85, 0.55), 'Public domain', 'Radomir Rade Jokić', 'Miloš Dudić, narodni heroj: birth year 1915; birthplace klinci; year 1944'),
    ('0039100533', 'Stevan_Kragujević,_general_Nikola_Ljubičić.jpg', (0.143, 0, 0.877, 0.666), 'CC BY-SA 3.0 rs', 'Stevan Kragujević', 'Nikola Ljubičić, narodni heroj: birth year 1916; birthplace srbija'),
    ('0010100431', 'Nikola_Karanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Nikola Karanović, narodni heroj: birth year 1914; birthplace prkosi; death place split'),
    ('0010201927', 'Nikola_Karanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Nikola Karanović, narodni heroj: birth year 1914; birthplace prkosi'),
    ('0001004077', 'Pavle_Jakšić.jpg', (0.1, 0, 0.9, 0.85), 'CC BY-SA 3.0', '', 'Pavle Jakšić, narodni heroj: birth year 1913; birthplace blatusa'),
    ('0041000572', 'Savo_Kovačević.jpg', (0, 0, 1, 1), 'Public domain', '', 'Sava Kovačević, narodni heroj: birth year 1905; birthplace nudo; death place sutjeska; year 1943'),
    ('0010100138', 'Savo_Brković.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Savo Brković, narodni heroj: birth year 1906; birthplace velje'),
    ('0039100681', 'Veljko_Mićunović.jpg', (0.15, 0.05, 0.8, 0.6), 'Public domain', '', 'Veljko Mićunović, narodni heroj: birth year 1916'),
    ('0001008666', 'Sulejman_Omerović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Sulejman Omerović, narodni heroj: birth year 1923; birthplace maglaj; death place nasica; year 1945'),
    ('0040010891', 'Veselin_Masleša.jpg', (0, 0, 1, 1), 'Public domain', '', 'Veselin Masleša, narodni heroj: birth year 1906; year 1943'),
    ('0109000114', 'Vera_Blagojević.jpg', (0, 0, 1, 1), 'Public domain', '', 'Vera Blagojević, narodni heroj: birth year 1920; year 1942'),
    ('0043001188', 'Vlado_Tomanović.jpg', (0.15, 0, 0.85, 0.5), 'Public domain', '', 'Vlado Tomanović, narodni heroj: birth year 1907; birthplace velimlje; year 1943'),
    ('0041000948', 'Đoko_Pavićević.jpg', (0, 0, 1, 1), 'Public domain', '', 'Đoko Pavićević, narodni heroj: birth year 1872; birthplace pjesivacki'),
    ('0040000916', 'Vukosava_Vukica_Mićunović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Vukosava Mićunović, narodni heroj: birth year 1921; birthplace velestovo'),
    ('0001004702', 'Zdravko_Jovanovic.jpg', (0, 0, 1, 1), 'Public domain', '', 'Zdravko Jovanović, narodni heroj: birth year 1909; birthplace osladic; year 1943'),
    ('0101000135', 'Ljubo_Miljanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Љубо Миљановић, narodni heroj: birth year 1912; birthplace vrpolje; death place mostara; year 1945'),
    ('0043000515', 'Ante_Kelava.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Анте Келава, narodni heroj: birth year 1916; birthplace dobro; death place bilece; year 1943'),
    ('0041001249', 'Veljko_Todorović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Вељко Тодоровић (народни херој), narodni heroj: birth year 1914; birthplace orah; death place veljem; year 194'),
    ('0001001115', 'Božo_Božović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Божо Божовић, narodni heroj: birth year 1911; birthplace rogami'),
    ('0044000509', 'Blažo_Mraković.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Блажо Мраковић, narodni heroj: birthplace zagarac'),
    ('0040000461', 'Boško_Janković_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Бошко Јанковић (народни херој), narodni heroj: birth year 1910; birthplace zirci; year 1943'),
    ('0041000428', 'Božidar_Jovanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Божидар Јовановић, narodni heroj: birth year 1919; birthplace niksic'),
    ('0041000401', 'Veljko_Janković.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Вељко Јанковић, narodni heroj: birth year 1911; birthplace podgorica'),
    ('0052000539', 'Veljko_Janković.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Вељко Јанковић, narodni heroj: birth year 1911; death place beograd'),
    ('0049000252', 'Vojko_Milovanović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Војко Миловановић, narodni heroj: birth year 1918; birthplace vukosavci; year 1943'),
    ('0043000539', 'Danilo_Komnenović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Данило Комненовић, narodni heroj: birth year 1915; birthplace poplat'),
    ('0042000201', 'Gliša_Janković.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Глиша Јанковић, narodni heroj: birth year 1913; birthplace osjek; year 1944'),
    ('0041001075', 'Gojko_Radović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Гојко Радовић, narodni heroj: birth year 1911; birthplace podgorica'),
    ('0041001321', 'Dušan_Vujačić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Душан Вујачић, narodni heroj: birth year 1917; birthplace niksic; year 1943'),
    ('0041001378', 'Dušan_Vuković_Zećo.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Душан Вуковић, narodni heroj: birth year 1910; birthplace golubovci'),
    ('0069001559', 'Dušan_Remih.jpg', (0, 0, 1, 1), 'Public domain', '', 'Душан Ремих, narodni heroj: birth year 1922; birthplace kocevje; death place stara; year 1944'),
    ('0040010523', 'Mašo_Jelić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Машо Јелић, narodni heroj: birth year 1908; year 1944'),
    ('0060000864', 'Milos_Kljajic.jpg', (0, 0, 1, 1), 'Public domain', '', 'Милош Кљајић, narodni heroj: death place zumberak; year 1944'),
    ('0040001208', 'Nenad_Rakočević.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Ненад Ракочевић, narodni heroj: birth year 1915; birthplace stitarica; year 1943'),
    ('0042000400', 'Mitar_Minić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Митар Минић, narodni heroj: birth year 1918; birthplace odesa'),
    ('0077000934', 'Mitar_Radusinović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Митар Радусиновић, narodni heroj: birth year 1912; birthplace spuz'),
    ('0040001341', 'Niko_Strugar.jpg', (0, 0, 1, 1), 'Public domain', '', 'Нико Стругар, narodni heroj: birth year 1901; birthplace gornji'),
    ('0012000514', 'Petar_Mećava_(portrait).jpg', (0, 0, 1, 1), 'Public domain', '', 'Петар Мећава, narodni heroj: birthplace kostajnica; year 1944'),
    ('0054001717', 'Petar_Mećava_(portrait).jpg', (0, 0, 1, 1), 'Public domain', '', 'Петар Мећава, narodni heroj: birth year 1914; birthplace zivaja; death place travnik; year 1944'),
    ('0048011258', 'Rade_Jovanić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Раде Јованић, narodni heroj: birthplace ribnik; death place manjaci; year 1943'),
    ('0040001417', 'Petar_Vojvodić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Петар Војводић, narodni heroj: birth year 1914; birthplace cetinje'),
    ('0109000870', 'Radojica_Nenezić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Радојица Ненезић, narodni heroj: birth year 1921'),
    ('0005100800', 'Radomir_Rakočević.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Радомир Ракочевић, narodni heroj: birth year 1914; birthplace stitarica; death place kamena; year 1944'),
    ('0005000294', 'Radoje_Kontić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Радоје Контић (народни херој), narodni heroj: birth year 1919; birthplace pljevlja; death place pljevalja; yea'),
    ('0042000240', 'Ratko_Jovičić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Ратко Јовичић, narodni heroj: birth year 1919; birthplace gucevo'),
    ('0040011070', 'Špiro_Mugoša.jpg', (0, 0, 1, 1), 'Public domain', '', 'Шпиро Мугоша, narodni heroj: birth year 1904; birthplace podgorica; year 1942'),
    ('0042000411', 'Spasoje_Mičić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Спасоје Мичић, narodni heroj: birth year 1921; birthplace travnik'),
    # second pass (October 2026): sr.wikipedia's articles on narodni heroji, lead photo checked by eye
    ('0004002326', 'Franc_Rojšek_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Франц Ројшек, narodni heroj: birth year 1914; birthplace Slape, Polje pri Ljubljani'),
    ('0004002354', 'Janko_Rudolf.jpg', (0, 0, 1, 1), 'Public domain', '', 'Јанко Рудолф, narodni heroj: birth year 1914; birthplace Križ pri Komendi'),
    ('0006000806', 'Rade_Bulat.jpg', (0, 0, 1, 1), 'Public domain', '', 'Раде Булат, narodni heroj: birth year 1920; birthplace Podgorje, Vrginmost'),
    ('0006005137', 'Dušan_Pekić_(1951).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Душан Пекић, narodni heroj: birth year 1921; birthplace Međeđak, Vojnić'),
    ('0007002272', 'Jovo_Kapičić.jpg', (0.15, 0.0, 0.85, 0.45), 'Public domain', '', 'Јово Капичић, narodni heroj: birth year 1919; birthplace Gaeta, Italija'),
    ('0016002048', 'Radojica_Nenezić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Радојица Ненезић, narodni heroj: birth year 1921; birthplace S. Broćanac, Nikšić'),
    ('0026001182', 'Vinko_Zevnik.jpg', (0, 0, 1, 1), 'Public domain', '', 'Винко Зевник, narodni heroj: birth year 1914'),
    ('0035101419', 'Rade_Bulat.jpg', (0, 0, 1, 1), 'Public domain', '', 'Раде Булат, narodni heroj: birth year 1920; birthplace Vrginmost'),
    ('0036100488', 'Gojko_Ujdurović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Гојко Ујдуровић, narodni heroj: birth year 1918; birthplace Gradac, Ploče'),
    ('0036011674', 'Rudolf_Primorac.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Рудолф Приморац, narodni heroj: birth year 1904; birthplace Sutomoru'),
    ('0039100763', 'Stevan_Kragujevic,_Slobodan_Penezic_Krcun.JPG', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', 'Stevan Kragujević', 'Слободан Пенезић Крцун, narodni heroj: birth year 1918'),
    ('0042000385', 'Cvijetin_Mijatović.jpg', (0, 0, 1, 1), 'CC BY', '', 'Цвијетин Мијатовић, narodni heroj: birth year 1913; birthplace Lopare, Tuzla'),
    ('0043001513', 'Vlado_Segrt_EPLJ.JPG', (0, 0, 1, 1), 'Public domain', '', 'Владо Шегрт, narodni heroj: birth year 1907; birthplace Aranđelovo, Irebinje'),
    ('0043000376', 'Rade_Hamović1.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Раде Хамовић, narodni heroj: birth year 1916'),
    ('0043001507', 'Obad_Šefik.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Шефик Обад, narodni heroj: birthplace Blagaj, Mostar'),
    ('0044000452', 'Nikola_Maraković_Nina_photo.jpg', (0, 0, 1, 1), 'Public domain', 'PidgeCopetti', 'Никола Мараковић Нина, narodni heroj: birth year 1912; birthplace Kostajnica'),
    ('0048000364', 'Pero_Kecman.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Перо Кецман, narodni heroj: birth year 1921; birthplace Bukovača, Bosanski Petrovac'),
    ('0048011402', 'Perko_Kasapović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Перо Касаповић, narodni heroj: birth year 1914; birthplace Ribnik, Ključ'),
    ('0049011150', 'Ratko_Perić_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Ратко Перић, narodni heroj: birth year 1914; birthplace Priboj, Lapare'),
    ('0049011151', 'Ratko_Perić_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Ратко Перић, narodni heroj: birth year 1914; birthplace Priboj, Lopare'),
    ('0060000307', 'Милан_Чакширан.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', 'Zmaj.Ognjeni', 'Милан Чакширан, narodni heroj: birth year 1908; birthplace Kordunski Ljeskovac'),
    ('0061000061', 'Ilija_Badovinac.jpg', (0, 0, 1, 1), 'Public domain', 'Jože Petek', 'Илија Бадовинац, narodni heroj: birth year 1917; birthplace Rosalnice'),
    ('0061000194', 'Jože_Borštnar_(1).jpg', (0, 0, 1, 1), 'Public domain', '', 'Јоже Борштнар, narodni heroj: birth year 1915'),
    ('0061001135', 'Franc_Kočevar.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Кочевар, narodni heroj: birth year 1918; birthplace Metlika'),
    ('0061001410', 'Anton_Marincelj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Антон Маринцељ, narodni heroj: birth year 1917; birthplace Banja Loka'),
    ('0062000036', 'Franc_Avbelj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Авбељ, narodni heroj: birth year 1914; birthplace Trnjava pri Lukovici'),
    ('0062000037', 'Viktor_Avbelj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Виктор Авбељ, narodni heroj: birth year 1914; birthplace Prevoje'),
    ('0062000409', 'Anton_Dežman.jpg', (0, 0, 1, 1), 'Public domain', '', 'Антон Дежман, narodni heroj: birth year 1920; birthplace Lesce'),
    ('0062000763', 'Janez_Hribar.jpg', (0, 0, 1, 1), 'Public domain', 'Danilo Škofič', 'Јанез Хрибар, narodni heroj: birth year 1918; birthplace Podlipoglav'),
    ('0062000937', 'Mirko_Jerman.jpg', (0, 0, 1, 1), 'Public domain', '', 'Мирко Јерман, narodni heroj: birth year 1912; birthplace Smarca pri Kamniku'),
    ('0062000983', 'Jože_Kadunc.jpg', (0, 0, 1, 1), 'Public domain', '', 'Јоже Кадунц, narodni heroj: birth year 1925; birthplace Dobrepolje'),
    ('0062001312', 'Franc_Krese.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Кресе, narodni heroj: birth year 1919; birthplace Bogneča vas'),
    ('0062002183', 'Franc_Rojšek_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Франц Ројшек, narodni heroj: birth year 1914; birthplace Ljubljana'),
    ('0063000733', 'Franc_Krese.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Кресе, narodni heroj: birth year 1919; birthplace Ljubljana, Bogneča vas'),
    ('0064002015', 'Cveto_Močnik_narodni_heroj.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Цвето Мочник, narodni heroj: birth year 1914; birthplace Ljubljana'),
    ('0064002438', 'Franc_Pokovec_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Франц Поковец, narodni heroj: birthplace Zelena jama, Ljubljana'),
    ('0064002897', 'Franc_Tavčar.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Тавчар, narodni heroj: birth year 1920; birthplace Ljubljana, Jarše'),
    ('0064003055', 'Janez_Učakar.jpg', (0.2, 0.0, 0.8, 0.5), 'Public domain', '', 'Јанез Учакар, narodni heroj: birth year 1918; birthplace Moravče'),
    ('0064003449', 'Mihaela_Škapin.jpg', (0, 0, 1, 1), 'Public domain', '', 'Михаела Шкапин, narodni heroj: birth year 1922; birthplace Veliko polje pri Sežani'),
    ('0068000046', 'Jože_Boldan_Silni.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Јоже Болдан, narodni heroj: birth year 1915; birthplace Višnje'),
    ('0068000206', 'Jakopič_Albert.jpg', (0, 0, 1, 1), 'Public domain', '', 'Алберт Јакопич, narodni heroj: birth year 1914; birthplace Ljubljana'),
    ('0068000291', 'Ivan_Kovačič.jpg', (0, 0, 1, 1), 'Public domain', '', 'Иван Ковачич Ефенка, narodni heroj: birth year 1921; birthplace Podboršt'),
    ('0068000589', 'Vinko_Robek_(narodni_heroj).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Винко Робек, narodni heroj: birth year 1915; birthplace Vinji vrh'),
    ('0068000627', 'Jože_Slak_Silvo.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Јоже Слак, narodni heroj: birth year 1902; birthplace Gorenji Vrh pri Dobrniču'),
    ('0069000075', 'Dragomir_Benčič.jpg', (0, 0, 1, 1), 'Public domain', '', 'Драгомир Бенчић, narodni heroj: birth year 1911'),
    ('0070000108', 'Jože_Boldan_Silni.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Јоже Болдан, narodni heroj: birth year 1915; birthplace Višnje'),
    ('0070000619', 'Ivan_Kovačič.jpg', (0, 0, 1, 1), 'Public domain', '', 'Иван Ковачич Ефенка, narodni heroj: birth year 1921; birthplace Podboršt'),
    ('0070000691', 'Danila_Kumar.jpg', (0, 0, 1, 1), 'Public domain', '', 'Данила Кумар, narodni heroj: birth year 1921'),
    ('0070000781', 'Anton_Marincelj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Антон Маринцељ, narodni heroj: birth year 1917; birthplace Banjaloka'),
    ('0070100113', 'Ilija_Badovinac.jpg', (0, 0, 1, 1), 'Public domain', 'Jože Petek', 'Илија Бадовинац, narodni heroj: birth year 1917; birthplace Rosalnice'),
    ('0093000186', 'Ratko_Pavlović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Ратко Павловић Ћићко, narodni heroj: birth year 1913; birthplace Berilje, Prokuplje'),
    ('0112000010', 'Stevan_Kragujevic_Spasenija_Cana_Babovic.JPG', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Спасенија Цана Бабовић, narodni heroj: birth year 1907; birthplace Lazarevac'),
    ('0112000053', 'Josip_Broz_Tito_uniform_portrait.jpg', (0, 0, 1, 1), 'Public domain', '', 'Јосип Броз Тито, narodni heroj: birth year 1892; birthplace Kumrovec, Klanjec'),
    ('0112000161', 'Isa_Jovanović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Иса Јовановић, narodni heroj: birth year 1906; birthplace Izbište, Vršac'),
    ('0112000301', 'Gojko_Nikoliš.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Гојко Николиш, narodni heroj: birth year 1911; birthplace Sjeničak, Vrginmost'),
    ('0112000332', 'Moša_Pijade.jpg', (0, 0, 1, 1), 'Public domain', '', 'Моша Пијаде, narodni heroj: birth year 1890; birthplace Beograd'),
    ('0112000374', 'Aleksandar_Ranković_(1).jpg', (0, 0, 1, 1), 'Public domain', '', 'Александар Ранковић, narodni heroj: birth year 1909; birthplace Draževac, Obrenovac'),
    ('0114000006', 'Mitar_Bakić.jpg', (0, 0, 1, 1), 'Public domain', '', 'Митар Бакић, narodni heroj: birth year 1908; birthplace Berislavci, Podgorica'),
    ('0114000031', 'Peko-dapčević.png', (0, 0, 1, 1), 'Public domain', '', 'Пеко Дапчевић, narodni heroj: birth year 1913; birthplace Ljubotinj, Cetinje'),
    ('0115000108', 'Rudolf_Primorac.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Рудолф Приморац, narodni heroj: birth year 1904; birthplace Sutomore, Bar'),
    ('0119000780', 'Branko_Perić,_narodni_heroj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Бранко Перић, narodni heroj: birth year 1913; birthplace Brusnik'),
    ('0119000956', 'Sima_Simić.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Сима Симић, narodni heroj: birth year 1920; birthplace Rakinac'),
    ('0120000283', 'Dušan_Pekić_(1951).jpg', (0, 0, 1, 1), 'CC BY-SA 3.0', '', 'Душан Пекић, narodni heroj: birth year 1921; birthplace Međeđak, Vojnić'),
    ('0123000666', 'Jovo_Kecman.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Јово Кецман, narodni heroj: birth year 1914; birthplace Drvar'),
    ('0124000398', 'Perko_Kasapović.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Перо Касаповић, narodni heroj: birth year 1914; birthplace Ribnik, Ključ'),
    ('0125000505', 'Obad_Šefik.jpg', (0, 0, 1, 1), 'CC BY-SA 3.0 rs', '', 'Шефик Обад, narodni heroj: birth year 1922; birthplace Blagaj, Mostar'),
    ('0126000268', 'Predrag_Jeftić.jpg', (0, 0, 1, 1), 'Public domain', '', 'Предраг Јевтић, narodni heroj: birth year 1913'),
    ('0126000650', 'Ratko_Mitrović.jpg', (0, 0, 1, 1), 'Public domain', '', 'Ратко Митровић, narodni heroj: birth year 1913'),
    ('0139000166', 'Franjo_Kluz_(1).jpg', (0, 0, 1, 1), 'Public domain', '', 'Фрањо Клуз, narodni heroj: birth year 1913; birthplace Bosanska Dubica'),
    ('0170000076', 'Lojze_Kebe.jpg', (0, 0, 1, 1), 'Public domain', '', 'Лојзе Кебе, narodni heroj: birthplace Cerknica - Ljubljana'),
    ('0171010002', 'Franc_Avbelj.jpg', (0, 0, 1, 1), 'Public domain', '', 'Франц Авбељ, narodni heroj: birthplace Trnjava pri Lukovici'),
]

MEMORIAL = [
    # a book across units that prints a photograph beside the soldier's biography (the Tuzla memorial book,
    # website/public/pdfs/tuzla-spomen-knjiga.pdf = znaci 00001/144.pdf pp. 8-292): the photo beside the entry a record
    # took (its `reference`), placed by the entry's box on the page, one entry beside it; each pair checked by hand.
    # record, the book's entry, page in the site's PDF, the photo's box there, what the record and the entry share
    ('0023000123', '9032000084', 26, (217.0, 236.0, 349.8, 388.6), 'father Husein, born 1914'),
    ('0023000346', '9032000214', 62, (521.6, 486.7, 650.5, 632.5), 'father Gano, born 1927 in Tuzla, XIX birčanska, fell May 1945'),
    ('0023000974', '9032000522', 158, (493.8, 553.1, 627.4, 683.1), 'father Ahmet, born 1924'),
    ('0023001077', '9032000539', 165, (211.6, 774.7, 341.2, 921.5), 'father Niko, born 1927'),
    ('0023001550', '9032000763', 238, (199.8, 241.4, 313.2, 395.5), 'father Alija, born 1927'),
    ('0023001814', '9032000873', 276, (514.4, 740.9, 622.8, 891.3), 'father Nikola, born 1891'),
    ('0023001954', '9032000797', 248, (186.1, 587.9, 288.0, 715.0), 'father Alija, born 1914'),
    ('0024000219', '9032000158', 48, (180.2, 743.9, 312.6, 894.0), 'born 1926'),
    ('0024000281', '9032000213', 62, (218.8, 253.6, 348.7, 391.5), 'born 1926 in Gacko, II krajiška, died of wounds at the turn of 1944'),
    ('0024000939', '9032000600', 184, (506.6, 771.5, 626.1, 925.9), 'born in Moluhe, II krajiška from October 1943, fell at Orahovo Selo (Foča)'),
    ('0024001213', '9032000757', 236, (212.5, 224.3, 315.8, 355.4), 'father Suljo, II krajiška, fell November 1943 at Kijevo (Trnovo)'),
    ('0024001451', '9032000147', 46, (191.9, 447.5, 326.9, 589.7), 'zemljoradnik, II krajiška from October 1943, fell at the end of 1943'),
    ('0025000055', '9032000051', 15, (189.6, 646.4, 323.8, 802.6), 'father Junuz, born 1912'),
    ('0025000136', '9032000116', 37, (516.0, 725.1, 651.3, 879.6), 'father Osman, born 1924'),
    ('0025000184', '9032000160', 49, (217.8, 481.9, 352.1, 615.4), 'father Đulaga, born 1917, Tuzlanski odred, komandir čete'),
    ('0025000192', '9032000169', 51, (223.9, 612.5, 346.7, 749.7), 'born 1910'),
    ('0025000327', '9032000265', 75, (516.7, 571.2, 651.7, 728.2), 'born 1917 in Tuzla, Tuzlanski odred, fell January 1944'),
    ('0025000348', '9032000285', 81, (216.8, 256.3, 342.4, 412.5), 'father Salih, born 1923'),
    ('0025000371', '9032000294', 83, (521.4, 442.8, 655.6, 598.7), 'father Omer, born 1924'),
    ('0025000385', '9032000297', 84, (203.3, 627.9, 335.4, 782.3), 'father Muhamed, born 1922, Tuzlanski odred, fell 1943'),
    ('0025000447', '9032000374', 111, (521.6, 738.7, 656.9, 896.1), "father Muharem, Kladanj, Tuzlanski odred, fell at Vukovije, November 1943 (the record's 1925 is a slip: he came to Tuzla to work in 1923)"),
    ('0025000493', '9032000404', 122, (205.9, 489.4, 339.5, 645.3), 'Tuzlanski odred, fell 22 December 1943'),
    ('0025001014', '9032000870', 275, (195.5, 239.9, 305.3, 388.6), 'father Leopold, born 1927'),
    ('0025001022', '9032000879', 280, (196.2, 609.8, 319.3, 728.2), 'father Zahir, born 1900'),
    ('0025001054', '9032000138', 43, (511.4, 754.6, 641.4, 895.0), 'father Dimitrije, born 1899'),
    ('0029000216', '9032000333', 97, (215.9, 543.8, 350.9, 687.1), 'born 1925 in Kolimer, Tuzla, XVII majevička'),
    ('0029000610', '9032000681', 212, (498.6, 602.9, 630.0, 742.2), 'načelnik štaba of the XVII majevička in both'),
    ('0029000701', '9032000747', 233, (197.6, 274.5, 305.9, 402.0), 'father Hasan, born 1919'),
    ('0032000009', '9032000032', 9, (524.0, 510.0, 645.3, 632.4), 'father Hamid, born 1922'),
    ('0032000051', '9032000294', 83, (521.4, 442.8, 655.6, 598.7), 'father Omer, born 1924'),
    ('0032000116', '9032000536', 165, (215.4, 245.7, 349.0, 414.2), 'father Ilija, born 1923'),
    ('0032000178', '9032000746', 232, (182.6, 728.1, 314.7, 896.9), 'father Hasib, born 1924'),
    ('0033000019', '9032000042', 12, (180.0, 738.6, 315.3, 895.9), 'father Grga, born 1924'),
    ('0042000050', '9032000094', 29, (539.1, 519.6, 653.2, 672.6), 'father Abdulah, born 1919'),
    ('0049000345', '9032000719', 224, (184.0, 241.4, 297.7, 397.3), 'father Suljaga, born 1920'),
    ('0052000014', '9032000005', 2, (219.9, 236.4, 353.1, 393.4), 'father Ahmet, born 1914'),
    ('0052000081', '9032000041', 12, (488.1, 516.1, 622.0, 672.0), 'father Juro, born 1925'),
    ('0052000101', '9032000051', 15, (189.6, 646.4, 323.8, 802.6), 'father Junuz, born 1912 near Bileća (the books differ on the day he fell)'),
    ('0052000161', '9032000101', 32, (194.7, 251.5, 327.6, 406.7), 'father Bono, born 1924'),
    ('0052000462', '9032000275', 78, (525.7, 466.9, 653.5, 619.5), 'father Đuro, born 1904'),
    ('0052000472', '9032000290', 82, (520.3, 446.0, 652.8, 601.1), 'father Murat, born 1914'),
    ('0052000509', '9032000307', 87, (218.2, 463.0, 349.2, 618.5), 'father Petar, born 1910 on Husino, poslovođa tesara'),
    ('0052000536', '9032000329', 95, (219.4, 588.3, 349.7, 744.1), 'father Vukan/Vukadin, born 1923 in Tuzla, fell near Vareš at the end of 1943'),
    ('0052000593', '9032000360', 107, (220.6, 462.5, 350.5, 616.9), 'father Ivan, born 1898'),
    ('0052000649', '9032000399', 120, (488.8, 766.3, 621.6, 922.9), 'father Jovo, born 1922'),
    ('0052000673', '9032000412', 125, (217.7, 242.2, 351.3, 397.7), 'father Tunjo, born 1921'),
    ('0052000674', '9032000411', 124, (488.7, 696.9, 623.0, 852.8), 'father Blaško, born 1913'),
    ('0052000775', '9032000459', 140, (193.2, 258.0, 325.3, 421.8), 'father Marko, born 1924'),
    ('0052000811', '9032000474', 144, (489.5, 612.2, 623.0, 770.9), 'father Ilija, born 1914'),
    ('0052000827', '9032000483', 146, (497.7, 775.5, 630.5, 934.3), 'father Anto, born 1922'),
    ('0052000925', '9032000536', 165, (215.4, 245.7, 349.0, 414.2), 'father Ilija, born 1923'),
    ('0052000963', '9032000538', 165, (518.8, 578.1, 653.0, 746.9), 'father Božo, born 1920'),
    ('0052000977', '9032000557', 171, (168.2, 230.3, 301.8, 383.3), 'father Ilija, born 1908'),
    ('0052001102', '9032000629', 193, (197.4, 255.8, 330.6, 410.9), 'father Ilija, born 1919'),
    ('0052001145', '9032000640', 198, (193.7, 252.7, 330.5, 407.9), 'father Ibrahim, born 1907'),
    ('0052001264', '9032000701', 218, (523.4, 700.3, 641.9, 838.6), 'father Tunjo, born 1912'),
    ('0052001265', '9032000702', 219, (201.1, 236.7, 334.0, 391.9), 'father Tunjo, born 1915'),
    ('0052001424', '9032000773', 241, (209.7, 255.5, 319.5, 393.0), 'father Josip, born 1923'),
    ('0052001523', '9032000848', 265, (209.8, 474.2, 319.3, 600.9), 'father Ivan, born 1916 in Czechoslovakia'),
    ('0081000964', '9032000690', 216, (201.2, 239.0, 333.6, 394.9), 'father Tahir, born 1908 near Trebinje'),
    ('0111010761', '9032000443', 135, (223.4, 505.3, 355.8, 663.3), 'born in Tuzla, battalion commissar in the VIII vojvođanska (51. divizija), fell April 1945'),
    ('0116000095', '9032000578', 177, (479.0, 659.6, 610.8, 816.2), 'father Hasan, born 1921'),
]

MEMORIAL_CREDIT = 'Spomen-knjiga poginulih tuzlanskih boraca NOR-a (Tuzla)'

DALMATINCI = [
    # Dalmatinci u Prvoj proleterskoj (website/public/pdfs/dalmatinci-prva-proleterska.pdf = znaci 00001/207_4.pdf pp. 2-289):
    # a photo set in a fighter's biography, two or three columns a page. A photo goes to the entry whose text runs both
    # above and below it in its column (the entries found by their headings on the page, since the parser missed some),
    # never to one that gets two photos; the record must hold the book's entry, or agree with the heading on birth year
    # and birthplace. All checked on contact sheets: a woman's entry shows a woman, unclear or smeared prints left out.
    # record, page in the site's PDF, the photo's box there, why
    ('0001000073', 2, (131.0, 144.4, 245.1, 271.5), 'the photo set in the entry "ALAT Luke MILE" (its text runs above and below it)'),
    ('0001000145', 3, (338.5, 145.2, 452.6, 272.3), 'the photo set in the entry "ANĆIĆ Ante DRAGO" (its text runs above and below it)'),
    ('0001100025', 5, (97.1, 144.0, 211.2, 271.8), 'the photo set in the entry "ARAS Mate JOSO" (its text runs above and below it)'),
    ('0001000269', 5, (98.3, 514.6, 211.0, 638.4), 'the photo set in the entry "ARAS Ante LJUBO" (its text runs above and below it)'),
    ('0001100028', 6, (131.7, 141.1, 243.6, 267.1), 'the photo set in the entry "BABIĆ Šćepana IVO" (its text runs above and below it)'),
    ('0001400024', 6, (131.7, 509.0, 245.1, 633.9), 'the photo set in the entry "BABIĆ Ante MIRO" (its text runs above and below it)'),
    ('0001000402', 7, (98.0, 357.4, 211.4, 483.4), 'the photo set in the entry "BAČETIĆ Ivana IVO ŽUTI" (its text runs above and below it); born 1920 in Blato, as the record'),
    ('0001400031', 7, (343.3, 418.3, 456.7, 549.0), 'the photo set in the entry "BAIĆ Frane KAMILO" (its text runs above and below it)'),
    ('0001400036', 8, (371.7, 448.5, 490.1, 573.1), 'the photo set in the entry "BAKOTIĆ Jure ANTE" (its text runs above and below it)'),
    ('0001000478', 9, (99.2, 319.4, 210.8, 442.2), 'the photo set in the entry "BAKOVIĆ Ante STIPE" (its text runs above and below it)'),
    ('0001400041', 9, (344.8, 341.3, 457.8, 467.6), 'the photo set in the entry "BARBIR Mate JURE" (its text runs above and below it)'),
    ('0001000528', 10, (141.2, 199.7, 236.6, 321.7), 'the photo set in the entry "BARBIR Ivana MATE" (its text runs above and below it)'),
    ('0001000545', 10, (246.8, 373.0, 359.5, 498.2), 'the photo set in the entry "BARIŠIĆ Ivana MARIN" (its text runs above and below it)'),
    ('0001000568', 11, (215.9, 335.8, 329.3, 461.8), 'the photo set in the entry "BARTULICA Nikole MILORAD" (its text runs above and below it)'),
    ('0001000589', 11, (338.0, 146.9, 451.4, 272.5), 'the photo set in the entry "BAŠIĆ Mihe BRANKO" (its text runs above and below it)'),
    ('0001000603', 12, (128.8, 146.1, 241.1, 270.3), 'the photo set in the entry "BATINIĆ Jure NIKOLA" (its text runs above and below it); born 1919 in Makar, as the record'),
    ('0001400052', 12, (251.4, 338.6, 364.5, 459.9), 'the photo set in the entry "BAUČIĆ Joze RINO" (its text runs above and below it)'),
    ('0001000624', 13, (225.2, 506.6, 327.1, 629.8), 'the photo set in the entry "BEBIĆ Stjepana ANĐA" (its text runs above and below it)'),
    ('0001000627', 14, (125.2, 376.8, 237.8, 499.2), 'the photo set in the entry "BEBIĆ Joze NEDJELJKA" (its text runs above and below it)'),
    ('0001000639', 14, (371.2, 525.8, 486.0, 652.9), 'the photo set in the entry "BEDALOV Antona STIPE" (its text runs above and below it)'),
    ('0001000657', 15, (336.9, 464.8, 451.0, 592.3), 'the photo set in the entry "BELAMARIĆ Marka BRANKO" (its text runs above and below it); born 1919 in Dubra, as the record'),
    ('0001000661', 17, (101.8, 144.0, 215.2, 263.2), 'the photo set in the entry "BELAVA Tome IVAN" (its text runs above and below it)'),
    ('0001000709', 17, (347.5, 440.7, 460.2, 562.7), 'the photo set in the entry "BERIĆ Jakova PAVAO" (its text runs above and below it)'),
    ('0001000718', 18, (129.2, 307.0, 241.9, 427.9), 'the photo set in the entry "BEROVIC Sime ANTE GRUJO" (its text runs above and below it); born 1925 in Mandali, as the record'),
    ('0001000758', 18, (374.0, 144.2, 486.7, 269.2), 'the photo set in the entry "BILICIC Ante MARKO" (its text runs above and below it)'),
    ('0001000782', 20, (133.6, 148.8, 246.3, 274.4), 'the photo set in the entry "BIUK Jakova MATE" (its text runs above and below it)'),
    ('0001000805', 21, (220.7, 370.3, 333.4, 495.2), 'the photo set in the entry "BLAĆE Ivana JERKO" (its text runs above and below it)'),
    ('0001000839', 22, (128.6, 221.0, 241.6, 347.0), 'the photo set in the entry "BLAŽEVIĆ Ivana PETAR PJERO" (its text runs above and below it)'),
    ('0001000846', 22, (251.7, 423.3, 364.4, 549.3), 'the photo set in the entry "BOBAN Blaža MARIN VINKO" (its text runs above and below it); born 1923 in Solin, as the record'),
    ('0001000847', 22, (373.1, 393.6, 486.5, 518.8), 'the photo set in the entry "BOBAN Bartula MARKO" (its text runs above and below it)'),
    ('0001000867', 24, (246.9, 224.8, 359.9, 350.8), 'the photo set in the entry "BOČINA Petra JURE" (its text runs above and below it)'),
    ('0001000916', 25, (97.8, 367.9, 214, 495.7), 'the photo set in the entry "BOGUNOVIĆ Petra ANDRIJA" (its text runs above and below it)'),
    ('0001000918', 25, (214, 287.5, 335.1, 415.4), 'the photo set in the entry "BOGUNOVIĆ Jure IVAN BAČVAR" (its text runs above and below it); born 1922 in Baćina, as the record'),
    ('0001000922', 26, (371.6, 153.1, 485.8, 274.1), 'the photo set in the entry "BOGUNOVIĆ Slavka PERO" (its text runs above and below it); born 1924 in Baćina, as the record'),
    ('0001000963', 28, (371.3, 142.9, 480.7, 271.0), 'the photo set in the entry "BOKO Vicka LOVRE" (its text runs above and below it)'),
    ('0001000975', 29, (215.7, 263.5, 328.7, 381.6), 'the photo set in the entry "BONAĆIĆ Marina ANTE MARINČIĆ" (its text runs above and below it); born 1918 in Split, as the record'),
    ('0001001049', 30, (250.6, 352.8, 362.9, 478.1), 'the photo set in the entry "BOŠKOVIĆ Ante MATE" (its text runs above and below it); born 1919 in Baćina, as the record'),
    ('0001001157', 31, (338.3, 141.8, 451.7, 267.8), 'the photo set in the entry "BRALIĆ Petra JAKOV" (its text runs above and below it)'),
    ('0001001178', 32, (255.8, 145.6, 368.8, 269.8), 'the photo set in the entry "BRAŠKIN Duje VIKTOR" (its text runs above and below it)'),
    ('0001001235', 33, (337.1, 557.2, 449.8, 680.0), 'the photo set in the entry "BRLJEVIĆ Grge DUŠAN" (its text runs above and below it)'),
    ('0001001252', 34, (125.9, 432.0, 238.6, 557.2), 'the photo set in the entry "BRUSAN Jose TOMO" (its text runs above and below it)'),
    ('0001001253', 34, (247.8, 301.9, 361.2, 428.2), 'the photo set in the entry "BRUSAN Nikole VINKO" (its text runs above and below it)'),
    ('0001001256', 34, (379.3, 149.2, 483.4, 268.4), 'the photo set in the entry "BUBAK Leopolda JOSIP" (its text runs above and below it)'),
    ('0001001269', 35, (84.5, 152.9, 197.9, 275.7), 'the photo set in the entry "BUČAN Grge ALEKSANDAR" (its text runs above and below it)'),
    ('0001400132', 35, (86.9, 459.6, 201.0, 587.4), 'the photo set in the entry "BUKARICA Ilije ILIJA" (its text runs above and below it)'),
    ('0001001305', 35, (208.1, 299.6, 322, 427.0), 'the photo set in the entry "BULAT Mije DIVKO" (its text runs above and below it)'),
    ('0001001316', 35, (334.6, 561.7, 448.7, 685.5), 'the photo set in the entry "BULIĆIĆ Antona MARIN" (its text runs above and below it)'),
    ('0001001333', 36, (257.8, 148.3, 370.5, 274.0), 'the photo set in the entry "BUOVAC Paške JAKOV" (its text runs above and below it)'),
    ('0001001355', 37, (95.7, 145.9, 207.6, 271.5), 'the photo set in the entry "BUŠAC Ive MARKO" (its text runs above and below it)'),
    ('0001001177', 37, (341.2, 561.8, 455.3, 686.0), 'the photo set in the entry "BRAŠKIN-KATAVIĆ Duje ANKA" (its text runs above and below it); born 1925 in Kaštel, as the record'),
    ('0001001624', 39, (219.7, 470.2, 331.6, 585.0), 'the photo set in the entry "CVRLJE Duje ČEDOMIR" (its text runs above and below it)'),
    ('0001001642', 39, (339.7, 557.0, 453.1, 683.0), 'the photo set in the entry "ČALETA Joze ANTE" (its text runs above and below it)'),
    ('0001001644', 40, (133.0, 556.3, 247.9, 683.8), 'the photo set in the entry "ČALETA Bože PAŠKO" (its text runs above and below it)'),
    ('0001001667', 40, (255.9, 452.6, 370, 580.4), 'the photo set in the entry "ČATLAK Šime PAŠKO" (its text runs above and below it)'),
    ('0001001685', 41, (93.0, 379.7, 207.8, 503.9), 'the photo set in the entry "ČEKO Luke JOSO ILIJA" (its text runs above and below it)'),
    ('0001001709', 42, (372.1, 316.8, 484.4, 442.5), 'the photo set in the entry "ČETNIK Petra JOVAN" (its text runs above and below it)'),
    ('0001001729', 43, (223.8, 270.2, 338.0, 397.3), 'the photo set in the entry "ĆOGELJA Nikole IVO" (its text runs above and below it)'),
    ('0001001736', 44, (378.8, 323.5, 492.2, 449.9), 'the photo set in the entry "ĆOGELJA Vice NIKOLA" (its text runs above and below it)'),
    ('0001001763', 45, (212.2, 145.4, 324.9, 270.7), 'the photo set in the entry "ČOSIĆ Jandrije LJUBO" (its text runs above and below it)'),
    ('0001001780', 45, (335.6, 349.9, 448.3, 473.4), 'the photo set in the entry "ČUDINA Mije MARKO" (its text runs above and below it)'),
    ('0001001787', 46, (253.8, 143.5, 368.3, 270.6), 'the photo set in the entry "ČULAR Petra MARKO" (its text runs above and below it)'),
    ('0001001788', 47, (93.2, 141.8, 201.2, 270.3), 'the photo set in the entry "ČULIĆ Marka IVO" (its text runs above and below it)'),
    ('0001001801', 47, (216.4, 405.8, 330.5, 524.6), 'the photo set in the entry "ČVRLJAK Krste ANTE" (its text runs above and below it)'),
    ('0001001805', 48, (134.2, 556.1, 247.6, 682.4), 'the photo set in the entry "ČVRLJAK Šime JOSO" (its text runs above and below it)'),
    ('0001101711', 48, (255.4, 360.0, 368.1, 482.8), 'the photo set in the entry "ČVRLJAK Ante LJUBOMIR" (its text runs above and below it); born 1922 in Konjevrate, as the record'),
    ('0001001812', 49, (222.3, 141.4, 335.4, 267.0), 'the photo set in the entry "ČVRLJAK Šime TONA" (its text runs above and below it)'),
    ('0001001881', 49, (345.2, 361.9, 457.9, 479.3), 'the photo set in the entry "ĆUK Bože ANTE" (its text runs above and below it); born 1923 in Muć, as the record'),
    ('0001001794', 50, (128.0, 553.4, 241.4, 679.4), 'the photo set in the entry "ĆURIN Ante DARKO" (its text runs above and below it)'),
    ('0001001908', 50, (250.6, 374.6, 364.0, 501.0), 'the photo set in the entry "DADIČ Frane JOZO" (its text runs above and below it)'),
    ('0001002054', 51, (340.5, 145.9, 454.6, 273.0), 'the photo set in the entry "DESPINIĆ Rudolfa VICE" (its text runs above and below it)'),
    ('0001002069', 52, (251.0, 145.2, 365.8, 272.2), 'the photo set in the entry "DEVIĆ Augusta MARIJA" (its text runs above and below it)'),
    ('0001002185', 54, (130.4, 316.0, 244.6, 443.1), 'the photo set in the entry "DOBRIJEVIČ Miloša STANKO" (its text runs above and below it); born 1922 in Varivo, as the record'),
    ('0001002194', 54, (253.8, 148.3, 366.1, 268.2), 'the photo set in the entry "DODIG Jose MATE CIGO" (its text runs above and below it); born 1904 in Zaton, as the record'),
    ('0001002290', 55, (345.0, 144.4, 459.2, 271.5), 'the photo set in the entry "DRAGOBRATOVIĆ Pave IVO" (its text runs above and below it); born 1922 in Raba, as the record'),
    ('0001002291', 56, (126.4, 145.6, 239.1, 270.9), 'the photo set in the entry "DRAGOBRATOVIĆ Marka LOVRE" (its text runs above and below it)'),
    ('0001002326', 56, (249.3, 317.5, 362.0, 443.1), 'the photo set in the entry "DRAŠKOVIĆ Ante MARIJA" (its text runs above and below it)'),
    ('0001002334', 56, (371.7, 144.7, 467.1, 270.3), 'the photo set in the entry "DRAŠKOVIĆ Ante ZDRAVKO" (its text runs above and below it); born 1915 in Solin, as the record'),
    ('0001002388', 57, (340.5, 145.6, 453.9, 271.3), 'the photo set in the entry "DUJMIĆ Stjepana ANTE" (its text runs above and below it)'),
    ('0001002390', 57, (343.4, 557.2, 455.3, 683.6), 'the photo set in the entry "DUKIĆ Ante LAZO" (its text runs above and below it)'),
    ('0001002400', 58, (125.2, 375.3, 239.7, 502.4), 'the photo set in the entry "DULČIĆ Marina NIKOLA" (its text runs above and below it)'),
    ('0001002411', 58, (248.6, 145.9, 361.2, 271.9), 'the photo set in the entry "DUMANIĆ Josipa VELJKO" (its text runs above and below it); born 1922 in Splitu, as the record'),
    ('0001002416', 58, (371.4, 329.0, 484.8, 454.6), 'the photo set in the entry "DUPLANČIĆ Frane ANTE" (its text runs above and below it)'),
    ('0001002557', 59, (344.8, 143.8, 459.6, 271.2), 'the photo set in the entry "ĐOLONGA Mate JOZO" (its text runs above and below it)'),
    ('0001002436', 60, (125.2, 144.2, 237.1, 269.1), 'the photo set in the entry "DŽALETA Jakova MILAN" (its text runs above and below it)'),
    ('0001002894', 60, (371.2, 422.1, 484.2, 547.8), 'the photo set in the entry "ERAKOVIĆ Jovana BOŽO. rođen 1922" (its text runs above and below it)'),
    ('0001002902', 61, (221.4, 146.6, 334.1, 270.4), 'the photo set in the entry "ERCEGOVIĆ Svetina ANTE" (its text runs above and below it)'),
    ('0001002908', 62, (250.2, 462.2, 362.9, 580.6), 'the photo set in the entry "ERGIĆ Nikole DUŠAN" (its text runs above and below it)'),
    ('0001002932', 63, (98.9, 279.2, 211.2, 404.4), 'the photo set in the entry "FAKAČ Nikole KAMILO" (its text runs above and below it)'),
    ('0001400209', 63, (220.4, 138.5, 333.8, 265.2), 'the photo set in the entry "FANELI Mauricije MARIO" (its text runs above and below it)'),
    ('0001002969', 63, (344.2, 401.1, 455.4, 527.4), 'the photo set in the entry "FILIPETI Ante ANTE" (its text runs above and below it)'),
    ('0001400212', 64, (247.8, 136.3, 360.1, 264.1), 'the photo set in the entry "FISTANIĆ Ivana PAVLE" (its text runs above and below it)'),
    ('0001003052', 66, (129.6, 185.6, 242.3, 311.2), 'the photo set in the entry "FRZOP Ive BOZIDAR" (its text runs above and below it)'),
    ('0001003061', 66, (374.0, 139.7, 486.6, 265.7), 'the photo set in the entry "GABELIĆ Stjepana JOZO" (its text runs above and below it)'),
    ('0001003062', 66, (375.4, 502.4, 483.8, 627.6), 'the photo set in the entry "GABRIĆ Ante NIKOLA" (its text runs above and below it)'),
    ('0001003073', 67, (212.2, 286.8, 326.0, 411.4), 'the photo set in the entry "GAGIĆ Jandrije DUŠAN" (its text runs above and below it); born 1913 in Biljane, as the record'),
    ('0001003151', 67, (335.8, 449.8, 450.3, 576.8), 'the photo set in the entry "GARELJIĆ Jakova MILJENKO" (its text runs above and below it); born 1923 in Podgo, as the record'),
    ('0001003164', 68, (128.3, 271.6, 239.6, 393.0), 'the photo set in the entry "GAŠPAR Stipe MIJO" (its text runs above and below it)'),
    ('0001003176', 68, (249.5, 147.3, 363.6, 274.4), 'the photo set in the entry "GAVRANIĆ Ivana MILAN" (its text runs above and below it)'),
    ('0001003250', 69, (91.1, 146.6, 205.6, 272.2), 'the photo set in the entry "GILJEVIĆ Nikole PETAR" (its text runs above and below it)'),
    ('0001003263', 69, (213.8, 449.0, 327.2, 575.0), 'the photo set in the entry "GIZDIĆ Ivana KAJO" (its text runs above and below it)'),
    ('0001003265', 69, (338.3, 339.6, 448.5, 463.8), 'the photo set in the entry "GIZDIĆ Ivana MILIVOJ" (its text runs above and below it); born 1922 in Solin, as the record'),
    ('0001003267', 70, (130.2, 145.9, 244.3, 271.9), 'the photo set in the entry "GLADOVIĆ Miloša DUŠAN" (its text runs above and below it); born 1924 in Varivode, as the record'),
    ('0001003274', 70, (375.7, 145.2, 488.7, 271.2), 'the photo set in the entry "GLAVAN Ante MIJO" (its text runs above and below it)'),
    ('0001003276', 71, (98.5, 145.4, 211.2, 271.8), 'the photo set in the entry "GLAVINA Ivana NIKO" (its text runs above and below it)'),
    ('0001100324', 71, (219.7, 312.7, 332.4, 439.1), 'the photo set in the entry "GLAVINA Ante TONĆI" (its text runs above and below it)'),
    ('0001003304', 71, (343.1, 199.0, 450.0, 325.0), 'the photo set in the entry "GLUČINA Lovre NEDA" (its text runs above and below it)'),
    ('0001003338', 72, (133.2, 140.0, 245.9, 271.0), 'the photo set in the entry "GOLEŠ Mate IVAN" (its text runs above and below it)'),
    ('0001003403', 73, (105.7, 145.2, 220.5, 273.0), 'the photo set in the entry "GRANIĆ Grge MATE" (its text runs above and below it)'),
    ('0001003407', 73, (105.7, 427.5, 218.4, 552.8), 'the photo set in the entry "GRAOVAC Mile SPASE" (its text runs above and below it)'),
    ('0001003440', 73, (350.2, 280.6, 463.3, 407.0), 'the photo set in the entry "GRGA Ante IVAN" (its text runs above and below it)'),
    ('0001003441', 74, (127.8, 152.2, 241.9, 272.0), 'the photo set in the entry "GRGASOVIĆ Mije MARGARITA" (its text runs above and below it); born 1921 in Makar, as the record'),
    ('0001003447', 74, (246.6, 287.8, 361.1, 415.2), 'the photo set in the entry "GRGUREV Petra SLAVICA" (its text runs above and below it); born 1925 in Vodice, as the record'),
    ('0001003478', 75, (97.5, 143.6, 210.2, 269.2), 'the photo set in the entry "GRUBIŠIĆ Duje DUJO" (its text runs above and below it)'),
    ('0001003485', 76, (125.6, 340.1, 237.2, 465.7), 'the photo set in the entry "GRUBIŠIĆ Paška KRSTO MUS A" (its text runs above and below it); born 1924 in Šibenik, as the record'),
    ('0001400257', 76, (246.8, 236.2, 360.9, 363.2), 'the photo set in the entry "GRUPIŠIĆ Vice MARIJA" (its text runs above and below it)'),
    ('0001003488', 76, (366.8, 339.1, 483.1, 466.6), 'the photo set in the entry "GRUBIŠIĆ Kieme MARINKO" (its text runs above and below it)'),
    ('0001003561', 77, (217.0, 357.4, 330.4, 483.0), 'the photo set in the entry "GUGIĆ Ivana DRAGO" (its text runs above and below it)'),
    ('0001003570', 78, (376.2, 250.3, 491.1, 360.8), 'the photo set in the entry "GULIN Ante FRANE" (its text runs above and below it)'),
    ('0001003573', 79, (213.0, 400.1, 327.4, 527.6), 'the photo set in the entry "GULIN Ante KRSTE" (its text runs above and below it)'),
    ('0001400268', 79, (335.1, 551.3, 449.6, 678.8), 'the photo set in the entry "GULIN Ive MIRKO" (its text runs above and below it)'),
    ('0001003580', 80, (248.5, 138.0, 366, 265.3), 'the photo set in the entry "GURDULIĆ Jure IVO" (its text runs above and below it)'),
    ('0001003882', 81, (346.6, 138.2, 460.0, 263.9), 'the photo set in the entry "IVANIŠEVIĆ Ivana MIRKO" (its text runs above and below it)'),
    ('0001003883', 81, (347.1, 425.8, 464.1, 552.1), 'the photo set in the entry "IVANIŠEVIĆ Malina SPIRO" (its text runs above and below it)'),
    ('0001003887', 82, (129.7, 355.0, 243.8, 482.0), 'the photo set in the entry "IVANKOVIĆ Nikole MILE" (its text runs above and below it)'),
    ('0001003975', 82, (374.2, 362.9, 486.2, 486.0), 'the photo set in the entry "IVIĆ Grge KAJO VUKO" (its text runs above and below it); born 1923 in Vranjic, as the record'),
    ('0001003983', 83, (338.5, 151.0, 451.2, 274.4), 'the photo set in the entry "IVKOVIĆ Marka JOSIP IVAN" (its text runs above and below it); born 1921 in Dobropolj, as the record'),
    ('0001003984', 83, (340.4, 560.9, 453.8, 686.5), 'the photo set in the entry "IVKOVIĆ Ivana MARKO" (its text runs above and below it)'),
    ('0001004035', 84, (255.8, 306.4, 370.6, 434.2), 'the photo set in the entry "JAKIĆ Grge IVAN" (its text runs above and below it)'),
    ('0001004233', 85, (342.9, 473.7, 455.6, 599.7), 'the photo set in the entry "JELAVIĆ Grge LJUBO" (its text runs above and below it)'),
    ('0001004237', 86, (129.0, 558.4, 243.2, 685.9), 'the photo set in the entry "JELČIĆ Mirka LJUBO" (its text runs above and below it)'),
    ('0001004250', 86, (251.4, 367.9, 364.1, 495.0), 'the photo set in the entry "JELIĆ Paška BOŽO" (its text runs above and below it)'),
    ('0001004258', 87, (111.0, 151.9, 211.8, 273.2), 'the photo set in the entry "JELIĆ Bože LUKA" (its text runs above and below it)'),
    ('0001004266', 87, (222.4, 400.0, 335.8, 525.7), 'the photo set in the entry "JELIĆ Tome TOMISLAV TOMIŠA" (its text runs above and below it); born 1923 in Vrpolje, as the record'),
    ('0001004317', 88, (127.8, 146.6, 245.2, 273.0), 'the photo set in the entry "JERKOVIĆ Marina IVAN. rođen 1918. Kula" (its text runs above and below it)'),
    ('0001004319', 88, (255.0, 281.5, 367.7, 407.9), 'the photo set in the entry "JERKOVIĆ Stipe MATE" (its text runs above and below it); born 1915 in Drašnice, as the record'),
    ('0001004320', 89, (92.3, 147.6, 206.4, 273.6), 'the photo set in the entry "JERKOVIĆ Jure MIJO MIJUTINA" (its text runs above and below it); born 1915 in Kula, as the record'),
    ('0001004321', 89, (220.2, 283.9, 329.0, 408.1), 'the photo set in the entry "JERKOVIĆ Vlade MLADENKO" (its text runs above and below it); born 1925 in Bogomo, as the record'),
    ('0001004325', 89, (340.2, 433.4, 453.3, 558.7), 'the photo set in the entry "JERKOVIĆ Marka TOMO" (its text runs above and below it)'),
    ('0001100506', 90, (136.4, 560.4, 244.8, 686.4), 'the photo set in the entry "JOŠIĆ Todora ĐURO" (its text runs above and below it)'),
    ('0001004815', 91, (222.8, 141.6, 337.3, 268.7), 'the photo set in the entry "JUNAKOVIĆ Martina MILE" (its text runs above and below it); born 1922 in Dubrava, as the record'),
    ('0001004820', 92, (248.2, 360.6, 360.8, 481.9), 'the photo set in the entry "JURAN Krste ANTE (Toni Bukarin)" (its text runs above and below it)'),
    ('0001004827', 93, (219.7, 260.4, 332.4, 377.4), 'the photo set in the entry "JURAT Gušte MATE" (its text runs above and below it)'),
    ('0001004832', 94, (130.7, 554.9, 246.2, 682.0), 'the photo set in the entry "JURČEVIĆ Jakova SLAVKO" (its text runs above and below it)'),
    ('0001004836', 94, (256.0, 403.7, 369.4, 529.3), 'the photo set in the entry "JURICEV Sime MARKO" (its text runs above and below it); born 1926 in Vodice, as the record'),
    ('0001004837', 94, (377.4, 212.2, 490.8, 337.8), 'the photo set in the entry "JURIĆ Nike MIĆO" (its text runs above and below it)'),
    ('0001004841', 95, (94.5, 141.8, 208.6, 268.9), 'the photo set in the entry "JURIŠIĆ Ante DANE" (its text runs above and below it)'),
    ('0001004848', 96, (128.2, 141.6, 242, 268.7), 'the photo set in the entry "JURKOVIĆ Mate MARKO rođen 1907. Mandalina" (its text runs above and below it)'),
    ('0001004851', 96, (252.3, 427.7, 365.7, 554.0), 'the photo set in the entry "JURLEKA Jure ANTE" (its text runs above and below it)'),
    ('0001004886', 97, (348.4, 327.1, 456.0, 452.8), 'the photo set in the entry "KAKIĆ Petra FILIP" (its text runs above and below it)'),
    ('0001004889', 98, (123.0, 139.0, 237.1, 266.0), 'the photo set in the entry "KALAFATOVIĆ Nikole MATE" (its text runs above and below it); born 1917 in Janjina, as the record'),
    ('0001400365', 98, (245.4, 418.1, 358.8, 544.4), 'the photo set in the entry "KLAT Šime ZORKA" (its text runs above and below it)'),
    ('0001004902', 99, (92.5, 419.0, 206.6, 546.1), 'the photo set in the entry "KALAUZ Ive ROKO. rođen 1914" (its text runs above and below it)'),
    ('0001004913', 99, (341.4, 147.4, 450.4, 273.0), 'the photo set in the entry "KALITERNA Pere IVAN" (its text runs above and below it)'),
    ('0001004943', 100, (127.8, 366.2, 240.5, 491.8), 'the photo set in the entry "KAPOV Frane ANTE" (its text runs above and below it)'),
    ('0001004954', 100, (371.6, 381.1, 485.0, 506.7), 'the photo set in the entry "KARAMAN Jure MILAN" (its text runs above and below it); born 1919 in Solin, as the record'),
    ('0001400345', 101, (221.4, 328.0, 334.8, 453.7), 'the photo set in the entry "KARDOV Jose MARKO" (its text runs above and below it)'),
    ('0001005005', 102, (126.8, 141.6, 239.5, 267.6), 'the photo set in the entry "KATALINIĆ Zaharija ANDRIJA" (its text runs above and below it)'),
    ('0001005026', 103, (347.2, 557.0, 459.9, 682.6), 'the photo set in the entry "KATIĆ Jure SILVESTAR" (its text runs above and below it)'),
    ('0001400358', 104, (124.0, 554.1, 238.8, 681.9), 'the photo set in the entry "KATUNARIČ Tonča TONĆI" (its text runs above and below it)'),
    ('0001400360', 104, (369.3, 144.0, 482.3, 269.6), 'the photo set in the entry "KAZANOV Ante IVO" (its text runs above and below it)'),
    ('0001005085', 105, (93.2, 240.5, 203.8, 366.5), 'the photo set in the entry "KEZIĆ Joze STJEPAN" (its text runs above and below it)'),
    ('0001005113', 105, (237.2, 378.5, 321.1, 502.7), 'the photo set in the entry "KITAROVIĆ Jose ANTE" (its text runs above and below it); born 1920 in Šibenik, as the record'),
    ('0001005130', 106, (239.1, 335.8, 352.5, 461.8), 'the photo set in the entry "KLIŠMANIĆ Mije JOZO" (its text runs above and below it); born 1924 in Kaštel, as the record'),
    ('0001005152', 107, (99.7, 389.8, 212.4, 510.7), 'the photo set in the entry "KNEŽEVIĆ Stevana ILIJA" (its text runs above and below it)'),
    ('0001005223', 108, (129.5, 403.2, 241.4, 527.4), 'the photo set in the entry "KOKIĆ Jose ADAM" (its text runs above and below it)'),
    ('0001005233', 110, (372.6, 144.7, 485.3, 270.4), 'the photo set in the entry "KOKIĆ Frane RADE" (its text runs above and below it)'),
    ('0001005299', 111, (215.2, 146.9, 327.5, 272.5), 'the photo set in the entry "KONJEVODA Krste ANTE" (its text runs above and below it)'),
    ('0001005301', 111, (336.8, 304.3, 451.3, 431.4), 'the photo set in the entry "KONJEVODA Nikole DRAGO" (its text runs above and below it)'),
    ('0001005303', 112, (262.7, 369.4, 366.7, 495.7), 'the photo set in the entry "KONJEVODA Ivana MARKO" (its text runs above and below it)'),
    ('0001400401', 114, (376.7, 307.2, 485.8, 431.4), 'the photo set in the entry "KOVAČEVIĆ Marina ANDRIJA" (its text runs above and below it)'),
    ('0001005471', 115, (99.2, 142.0, 210.5, 269.8), 'the photo set in the entry "KOVAČIĆ Ante STIPE" (its text runs above and below it)'),
    ('0001400405', 115, (220.7, 288.9, 333.7, 414.6), 'the photo set in the entry "KOZLIĆA Marka ILIJA" (its text runs above and below it)'),
    ('0001005512', 116, (133.3, 272.4, 241.0, 398.4), 'the photo set in the entry "KRALJ Ivana IVAN" (its text runs above and below it)'),
    ('0001005556', 117, (345.3, 289.4, 458.0, 415.0), 'the photo set in the entry "KRILIĆ Mije NEDA" (its text runs above and below it)'),
    ('0001005557', 118, (126.4, 139.7, 239.0, 265.3), 'the photo set in the entry "KRILIĆ Tome NEĐO" (its text runs above and below it)'),
    ('0001005562', 119, (93.8, 140.6, 208.2, 265.5), 'the photo set in the entry "KRIVIĆ Vicka ANTE" (its text runs above and below it)'),
    ('0001005578', 119, (340.0, 409.6, 454.1, 536.7), 'the photo set in the entry "KRNIĆ Ivana IVAN" (its text runs above and below it)'),
    ('0001005581', 120, (259.6, 415.4, 372.3, 541.0), 'the photo set in the entry "KRNIĆ Nike JAKOV" (its text runs above and below it)'),
    ('0001005582', 120, (380.3, 311.2, 494.8, 428.6), 'the photo set in the entry "KRNIĆ Stipe JERE" (its text runs above and below it)'),
    ('0001005583', 121, (99.5, 275.2, 212.2, 400.9), 'the photo set in the entry "KRNIĆ Šime JOSO" (its text runs above and below it)'),
    ('0001005584', 121, (221.0, 140.4, 335.4, 267.4), 'the photo set in the entry "KRNIĆ Krste KRSTO" (its text runs above and below it)'),
    ('0001400441', 122, (369.7, 141.4, 482.4, 267.0), 'the photo set in the entry "KRSTINIĆ Jure FRANKA" (its text runs above and below it)'),
    ('0001005684', 123, (221.9, 318.4, 335.0, 444.4), 'the photo set in the entry "KRŽANIĆ Stipe RAFAEL" (its text runs above and below it)'),
    ('0001005685', 123, (343.8, 558.0, 456.9, 684.0), 'the photo set in the entry "KRŽELJ Antonija MIRKO" (its text runs above and below it)'),
    ('0001005723', 124, (248.8, 144.4, 359.3, 271.9), 'the photo set in the entry "KURTOVIĆ Josipa JERKO" (its text runs above and below it); born 1908 in Klis, as the record'),
    ('0001005746', 125, (97.1, 352.6, 209.8, 478.9), 'the photo set in the entry "KUVAĆIĆ Jure MATE" (its text runs above and below it)'),
    ('0001005750', 125, (341.2, 360.2, 455.6, 487.7), 'the photo set in the entry "KUZMANIĆ Luke LUKA. rođen 1922" (its text runs above and below it); born 1922 in Split, as the record'),
    ('0001005769', 126, (255.2, 320.9, 369.4, 448.0), 'the photo set in the entry "KUZMIĆ Vicka IVO" (its text runs above and below it)'),
    ('0001005791', 127, (215.7, 140.1, 329.8, 267.2), 'the photo set in the entry "LACMANOVIĆ Špira PANTELIJA" (its text runs above and below it)'),
    ('0001400901', 127, (338.1, 273.1, 452.6, 400.2), 'the photo set in the entry "VIĆ Krste ZORKA" (its text runs above and below it)'),
    ('0001005821', 128, (132.8, 139.0, 245.5, 264.6), 'the photo set in the entry "LALICA Štipana NIKOLA" (its text runs above and below it)'),
    ('0001005832', 129, (237.9, 357.6, 340.2, 483.2), 'the photo set in the entry "LALIĆ Uroša MIRKO" (its text runs above and below it)'),
    ('0001005833', 129, (349.5, 139.7, 462.2, 263.9), 'the photo set in the entry "LALIĆ Mihaila NIKOLA" (its text runs above and below it); born 1902 in Čista, as the record'),
    ('0001005835', 129, (349.0, 548.9, 463.9, 676.3), 'the photo set in the entry "LALIĆ Stanka PETAR" (its text runs above and below it)'),
    ('0001005837', 130, (131.4, 555.3, 244.1, 677.0), 'the photo set in the entry "LALIĆ Mihaila SLAVKO" (its text runs above and below it)'),
    ('0001005838', 130, (252.9, 329.5, 367.0, 456.6), 'the photo set in the entry "LALIĆ Jovana VUJO" (its text runs above and below it)'),
    ('0001005842', 130, (376.2, 140.6, 489.3, 266.2), 'the photo set in the entry "LAMBAŠA Mate UROŠ" (its text runs above and below it)'),
    ('0001400479', 131, (344.0, 309.6, 456.3, 435.3), 'the photo set in the entry "LELAS Ante MATE" (its text runs above and below it)'),
    ('0001005994', 132, (122.8, 149.2, 237.6, 277.0), 'the photo set in the entry "LELAS Petra MARIJA" (its text runs above and below it)'),
    ('0001006009', 132, (127.8, 564.7, 239.8, 688.2), 'the photo set in the entry "LEONE Marka MATE" (its text runs above and below it)'),
    ('0001006023', 132, (245.7, 281.0, 360.9, 408.8), 'the photo set in the entry "LESKUR Laze ILIJA" (its text runs above and below it)'),
    ('0001006024', 132, (377.0, 148.3, 481.4, 276.4), 'the photo set in the entry "LESKUR Laze MIRKO" (its text runs above and below it)'),
    ('0001300846', 134, (380.3, 441.8, 493.0, 567.4), 'the photo set in the entry "LUCJETIĆ Stipe ANTE" (its text runs above and below it)'),
    ('0001006196', 135, (102.2, 240.2, 217.7, 368.0), 'the photo set in the entry "LJUBENKOV Ante SLAVKO" (its text runs above and below it)'),
    ('0001006205', 135, (226.7, 373.4, 341.2, 500.5), 'the photo set in the entry "LJUBIČIĆ Ante MARTIN" (its text runs above and below it)'),
    ('0001006220', 135, (349.1, 145.2, 463.2, 273.0), 'the photo set in the entry "LJUBIŠIĆ Davida MILOŠ" (its text runs above and below it)'),
    ('0001400491', 135, (349.1, 506.6, 463.6, 619.6), 'the photo set in the entry "LJUTIĆ Nikole MARKO" (its text runs above and below it)'),
    ('0001006328', 136, (373.6, 246.4, 486.6, 372.1), 'the photo set in the entry "MALENICA Ante JERE" (its text runs above and below it)'),
    ('0001006388', 137, (96.9, 341.7, 209.6, 463.8), 'the photo set in the entry "MANDIĆ Luke FRANE VRANJEKA" (its text runs above and below it); born 1924 in Goriš, as the record'),
    ('0001300879', 137, (342.2, 558.9, 453.4, 684.6), 'the photo set in the entry "MARASOVIĆ Mate LUKA" (its text runs above and below it)'),
    ('0001006457', 138, (255.7, 232.1, 367.7, 357.7), 'the photo set in the entry "MARČIĆ Ante BARE" (its text runs above and below it)'),
    ('0001006604', 139, (339.4, 408.0, 452.1, 533.7), 'the photo set in the entry "MARKETIN Abrama SLAVKO" (its text runs above and below it); born 1926 in Pakošta, as the record'),
    ('0001006521', 140, (254.8, 216.4, 370, 363.0), 'the photo set in the entry "MARINČIĆ Dimitra PETAR" (its text runs above and below it); born 1913 in Ramljane, as the record'),
    ('0001006571', 140, (377.9, 432.2, 490.6, 557.8), 'the photo set in the entry "MARINOVIC Ivana FRANE" (its text runs above and below it); born 1915 in Baćina, as the record'),
    ('0001006574', 141, (218.0, 434.2, 330.6, 555.5), 'the photo set in the entry "MARINOVIĆ Jure MIJO" (its text runs above and below it); born 1918 in Baćina, as the record'),
    ('0001006811', 141, (340.6, 282.8, 453.3, 408.4), 'the photo set in the entry "MARTINOVIĆ Ivana NIKO" (its text runs above and below it); born 1923 in Baćina, as the record'),
    ('0001006772', 143, (93.0, 404.2, 205.3, 529.8), 'the photo set in the entry "MAROVIĆ Marina IVAN" (its text runs above and below it)'),
    ('0001400521', 143, (216.6, 269.0, 320.6, 395.4), 'the photo set in the entry "MARTIĆ Todora JOVO" (its text runs above and below it)'),
    ('0001006792', 143, (344.3, 559.2, 442.6, 679.1), 'the photo set in the entry "MARTINAC Mate KAŽIMIR-MIRO" (its text runs above and below it); born 1922 in Vrgo, as the record'),
    ('0001006799', 144, (256.7, 187.4, 369.4, 313.1), 'the photo set in the entry "MARTINIĆ Petra JOSIP" (its text runs above and below it); born 1921 in Nerežište, as the record'),
    ('0001400524', 145, (96.1, 389.6, 209.1, 515.9), 'the photo set in the entry "MASLOV Pave JAKIM" (its text runs above and below it)'),
    ('0001006884', 145, (340.6, 390.8, 455.1, 518.2), 'the photo set in the entry "MATIĆ Marka MARTIN" (its text runs above and below it); born 1913 in Sonković, as the record'),
    ('0001006914', 146, (135.4, 552.0, 247.4, 677.3), 'the photo set in the entry "MATIJAŠEVIĆ Petra RADE" (its text runs above and below it); born 1919 in Sutivan, as the record'),
    ('0001400527', 146, (378.8, 139.7, 491.4, 266.4), 'the photo set in the entry "MATIJEVIĆ Save NIKOLA" (its text runs above and below it)'),
    ('0001006947', 148, (133.3, 147.6, 247.8, 274.6), 'the photo set in the entry "MAZIĆ Nikole ROKO" (its text runs above and below it)'),
    ('0001006954', 148, (138.4, 558.0, 246.7, 685.8), 'the photo set in the entry "MAŽIBRADA Jakova SAVO" (its text runs above and below it); born 1926 in Kistanje, as the record'),
    ('0001006972', 148, (378.6, 147.1, 493.4, 274.2), 'the photo set in the entry "MEDIĆ Petra SPASO" (its text runs above and below it)'),
    ('0001400582', 149, (94.7, 398.9, 208.8, 519.8), 'the photo set in the entry "MIŠIN Marka MATE" (its text runs above and below it)'),
    ('0001007033', 149, (337.8, 341.8, 453.4, 462.7), 'the photo set in the entry "MIČIN Jerka NIKO" (its text runs above and below it)'),
    ('0001007120', 150, (134.1, 300.2, 246.8, 426.2), 'the photo set in the entry "MIHALJEVIĆ Šime FILIP FIĆO" (its text runs above and below it); born 1920 in Bilice, as the record'),
    ('0001007127', 150, (257.2, 468.4, 371.3, 595.5), 'the photo set in the entry "MIHIĆ Ivana BOGDAN" (its text runs above and below it)'),
    ('0001007175', 151, (103.1, 145.2, 206.1, 271.2), 'the photo set in the entry "MIKAĆIĆ Duje OSTOJA" (its text runs above and below it); born 1910 in Split, as the record'),
    ('0001007194', 151, (222.4, 288.2, 336.5, 415.3), 'the photo set in the entry "MIKULANDRA Ive DRAGO" (its text runs above and below it)'),
    ('0001007197', 151, (345.8, 558.0, 458.4, 683.6), 'the photo set in the entry "MIKULIĆ Jure POLDO" (its text runs above and below it)'),
    ('0001007246', 152, (128.1, 430.0, 240.8, 556.0), 'the photo set in the entry "MILANOVIĆ Vicka KAJO" (its text runs above and below it)'),
    ('0001007201', 152, (373.4, 145.4, 488.2, 273.2), 'the photo set in the entry "MILAČIĆ Marina ANTE" (its text runs above and below it)'),
    ('0001007380', 153, (220.7, 369.8, 326.9, 494.8), 'the photo set in the entry "MILIČEVIĆ Stjepana KREŠO" (its text runs above and below it); born 1915 in Metko, as the record'),
    ('0001007391', 153, (340.4, 565.2, 453.1, 685.1), 'the photo set in the entry "MILIČEVIĆ Stjepana VITOMIR" (its text runs above and below it)'),
    ('0001007648', 154, (373.2, 376.1, 485.9, 502.1), 'the photo set in the entry "MILOVAC Duje VELJKO CRNI" (its text runs above and below it); born 1920 in Konjevrate, as the record'),
    ('0001400562', 155, (96.6, 266.6, 206.4, 387.6), 'the photo set in the entry "MILJAK Jure BEPO" (its text runs above and below it)'),
    ('0001007795', 155, (341.4, 142.3, 454.1, 258.9), 'the photo set in the entry "MIOĆEVIĆ Marjana ANĐELKO" (its text runs above and below it); born 1921 in Gornje, as the record'),
    ('0001007804', 156, (127.8, 553.9, 239.1, 678.8), 'the photo set in the entry "MIOŠIĆ Ante DANILO" (its text runs above and below it)'),
    ('0001007847', 156, (373.6, 483.6, 488.4, 609.9), 'the photo set in the entry "MIRKOVIĆ Ante VINKO" (its text runs above and below it)'),
    ('0001007816', 157, (95.4, 247.4, 203.7, 370.2), 'the photo set in the entry "MIRKO Ante IVAN" (its text runs above and below it)'),
    ('0001007871', 157, (340.4, 142.6, 452.4, 268.2), 'the photo set in the entry "MIŠETIĆ Tome PAVE PAVAO" (its text runs above and below it); born 1925 in Hvar, as the record'),
    ('0001007884', 157, (342.6, 562.3, 456.3, 678.6), 'the photo set in the entry "MIŠIĆIN Fabjana ANDRIJA" (its text runs above and below it)'),
    ('0001008134', 159, (338.3, 554.4, 452.4, 681.5), 'the photo set in the entry "MRKUŠIĆ Grge GABRIJEL" (its text runs above and below it); born 1917 in Podgora, as the record'),
    ('0001008138', 160, (255.5, 363.4, 369.6, 490.5), 'the photo set in the entry "MRNDŽE Ante ŠIME" (its text runs above and below it)'),
    ('0001008188', 161, (219.0, 197.0, 333.5, 324.1), 'the photo set in the entry "MUŠAN Stjepana JOZO" (its text runs above and below it)'),
    ('0001008283', 162, (375.2, 141.4, 491.2, 267.0), 'the photo set in the entry "NEMČIĆ Ivana ANTE" (its text runs above and below it)'),
    ('0001400602', 163, (94.7, 145.6, 207.4, 269.8), 'the photo set in the entry "NEMLČIĆ Ante JOSIP" (its text runs above and below it)'),
    ('0001008291', 163, (216.4, 352.3, 330.5, 479.4), 'the photo set in the entry "NENADIĆ Vase STEVAN" (its text runs above and below it)'),
    ('0001008409', 163, (338.8, 144.9, 452.9, 264.1), 'the photo set in the entry "NIKOLIĆ Krste IVO" (its text runs above and below it)'),
    ('0001008471', 163, (339.5, 558.7, 452.2, 684.3), 'the photo set in the entry "NIKOLIĆ Petra RIKARD" (its text runs above and below it)'),
    ('0001008517', 164, (378.6, 323.7, 491.7, 448.6), 'the photo set in the entry "NINČEVIČ Stipe MATE" (its text runs above and below it); born 1923 in Solin, as the record'),
    ('0001008530', 165, (103.4, 146.4, 206.7, 272.0), 'the photo set in the entry "NIZIĆ Nikole MATE" (its text runs above and below it)'),
    ('0001008534', 166, (133.4, 143.0, 245.7, 271.2), 'the photo set in the entry "NOLA Ivana GRGO" (its text runs above and below it)'),
    ('0001400616', 166, (375.5, 145.9, 488.6, 271.9), 'the photo set in the entry "NUJIĆ Jakova MARIJA" (its text runs above and below it)'),
    ('0001400620', 168, (129.8, 146.8, 242.4, 270.3), 'the photo set in the entry "OLBRIH Todora PETAR" (its text runs above and below it)'),
    ('0001008690', 170, (123.4, 142.8, 236.1, 268.5), 'the photo set in the entry "ORLIĆ Roka JERKO" (its text runs above and below it)'),
    ('0001008698', 170, (245.3, 490.1, 359.8, 617.2), 'the photo set in the entry "OROŠNJAK Đure ILIJA" (its text runs above and below it); born 1913 in Vučevica, as the record'),
    ('0001008725', 170, (368.4, 368.2, 481.1, 492.4), 'the photo set in the entry "OŠTRIĆ Marka PAŠKO" (its text runs above and below it)'),
    ('0001008789', 171, (93.5, 143.8, 205.8, 269.4), 'the photo set in the entry "PALTRINJERI Jure JERKO" (its text runs above and below it)'),
    ('0001008882', 172, (128.2, 144.2, 231.6, 269.9), 'the photo set in the entry "PARAĆ Ivana JAKOV" (its text runs above and below it)'),
    ('0001008883', 172, (128.0, 555.1, 237.1, 680.8), 'the photo set in the entry "PARAĐINA Mitra MARKO" (its text runs above and below it)'),
    ('0001008958', 173, (338.0, 386.9, 450.0, 512.2), 'the photo set in the entry "PAVIČIĆ Ivana STJEPAN" (its text runs above and below it)'),
    ('0001008980', 174, (136.4, 144.7, 248.8, 268.9), 'the photo set in the entry "PAVIŠIĆ Vicka JERKO" (its text runs above and below it)'),
    ('0001009115', 175, (94.9, 409.0, 207.6, 535.3), 'the photo set in the entry "PEKAS Jakova BLAŽ" (its text runs above and below it)'),
    ('0001009131', 176, (135.0, 150.0, 247.7, 265.9), 'the photo set in the entry "PENGA Petra JOSIP" (its text runs above and below it)'),
    ('0001009137', 176, (257.7, 462.2, 370.4, 588.6), 'the photo set in the entry "PERAK Mate JAKOV" (its text runs above and below it)'),
    ('0001009153', 177, (338.5, 138.5, 453.0, 266.3), 'the photo set in the entry "PERIĆ Jure MIRKO" (its text runs above and below it)'),
    ('0001009163', 178, (132.2, 138.0, 246.3, 264.0), 'the photo set in the entry "PERIŠA Lovre ANTE" (its text runs above and below it)'),
    ('0001009165', 178, (254.8, 272.8, 367.5, 398.5), 'the photo set in the entry "PERIŠA Jerka LJUBO" (its text runs above and below it)'),
    ('0001009164', 178, (376.7, 138.9, 491.6, 266.4), 'the photo set in the entry "PERIŠA Lovre KREŠIMIR" (its text runs above and below it); born 1923 in Šibenik, as the record'),
    ('0001009183', 180, (257.6, 147.6, 372.1, 275.0), 'the photo set in the entry "PERKUŠIĆ Luke LUKA" (its text runs above and below it); born 1925 in Podbablje, as the record'),
    ('0001009184', 180, (258.3, 397.2, 371.7, 523.2), 'the photo set in the entry "PERLAN Marka PAVO" (its text runs above and below it)'),
    ('0001400664', 180, (381.0, 273.8, 494.4, 398.8), 'the photo set in the entry "PERONJA Jure TOMO" (its text runs above and below it)'),
    ('0001009203', 181, (95.4, 145.7, 208.1, 271.7), 'the photo set in the entry "PESAH Leona JOSIP" (its text runs above and below it)'),
    ('0001009209', 181, (218.8, 394.3, 330.4, 521.4), 'the photo set in the entry "PEŠIĆ Jakova MARKO" (its text runs above and below it)'),
    ('0001009249', 183, (97.4, 304.3, 211.8, 432.1), 'the photo set in the entry "PETKOVIĆ Marka MILOŠ" (its text runs above and below it)'),
    ('0001009254', 183, (220.2, 145.6, 332.9, 272.0), 'the photo set in the entry "PETKOVIĆ Frane NIKOLA" (its text runs above and below it)'),
    ('0001009281', 184, (128.3, 143.0, 237.8, 269.4), 'the photo set in the entry "PETRIĆ Andrije ĆIRO" (its text runs above and below it)'),
    ('0001009283', 184, (128.1, 556.0, 240.8, 682.4), 'the photo set in the entry "PETRIĆ Luke IVO" (its text runs above and below it)'),
    ('0001009293', 184, (250.2, 442.8, 363.3, 569.5), 'the photo set in the entry "PETRINA Martina BLAŽ" (its text runs above and below it)'),
    ('0001009295', 185, (102.8, 150.2, 215.5, 271.2), 'the photo set in the entry "PETRINA Jakova VICE" (its text runs above and below it); born 1921 in Dubrava, as the record'),
    ('0001009968', 186, (252.6, 145.7, 365.3, 271.3), 'the photo set in the entry "PUIZINA Duje BOŽO-BARIKADA" (its text runs above and below it); born 1924 in Split, as the record'),
    ('0001009967', 186, (252.1, 458.6, 365.5, 585.4), 'the photo set in the entry "PUHARIĆ Ivana ŽIVKO" (its text runs above and below it); born 1919 in Makarska, as the record'),
    ('0001009966', 186, (375.5, 337.2, 488.9, 463.6), 'the photo set in the entry "PUHARIĆ Ivana TONČI" (its text runs above and below it); born 1913 in Makarska, as the record'),
    ('0001009941', 188, (128.8, 557.3, 241.4, 679.7), 'the photo set in the entry "PROTEGA Jose JOSO" (its text runs above and below it)'),
    ('0001400714', 188, (372.1, 267.8, 485.2, 393.5), 'the photo set in the entry "PRODAN Jure NIKOLA" (its text runs above and below it)'),
    ('0001009813', 190, (251.6, 141.6, 364.3, 266.5), 'the photo set in the entry "POPOVIĆ Vase SAVO" (its text runs above and below it)'),
    ('0001009774', 190, (374.2, 330.2, 489.1, 457.7), 'the photo set in the entry "POPOVIĆ Milana MILAN" (its text runs above and below it)'),
    ('0001009724', 191, (223.3, 357.1, 335.6, 482.8), 'the photo set in the entry "POPLAŠEN Nikole DUŠAN" (its text runs above and below it); born 1922 in Mirlović, as the record'),
    ('0001009717', 191, (344.3, 563.8, 458.8, 686.5), 'the photo set in the entry "POPIĆ Ivana MARIN" (its text runs above and below it)'),
    ('0001009704', 192, (137.6, 555.1, 250.3, 681.1), 'the photo set in the entry "POPADIĆ Luke MILA" (its text runs above and below it)'),
    ('0001009698', 192, (258.4, 300.2, 372.5, 427.7), 'the photo set in the entry "POLJIČAK Mate JOSIP" (its text runs above and below it)'),
    ('0001009684', 192, (380.8, 141.8, 493.4, 268.9), 'the photo set in the entry "POLIĆ Josipa IVAN" (its text runs above and below it)'),
    ('0001009652', 193, (342.6, 141.8, 457.5, 269.6), 'the photo set in the entry "PLENKOVIĆ Ante LJUBO" (its text runs above and below it)'),
    ('0001009647', 194, (374.3, 456.4, 487.0, 582.1), 'the photo set in the entry "PLENČA Šime DUME PALIĐA" (its text runs above and below it); born 1913 in Vrpolje, as the record'),
    ('0001009646', 195, (92.5, 308.2, 205.2, 431.6), 'the photo set in the entry "PLENČA Šime BOŽO PALIDŽA" (its text runs above and below it); born 1919 in Vrpolje, as the record'),
    ('0001009645', 195, (214.9, 205.2, 327.2, 337.0), 'the photo set in the entry "PLENČA Marka ANTE" (its text runs above and below it)'),
    ('0001009640', 195, (337.1, 147.6, 447.6, 273.2), 'the photo set in the entry "PLAZONJA Jakova MARKO" (its text runs above and below it)'),
    ('0001400688', 196, (132.8, 145.9, 247.0, 273.3), 'the photo set in the entry "PIVALICA Nike ANTE" (its text runs above and below it)'),
    ('0001009608', 196, (256.4, 281.2, 369.5, 408.3), 'the photo set in the entry "PITEŠA Mate IVAN" (its text runs above and below it)'),
    ('0001009556', 198, (135.8, 146.1, 248.1, 259.5), 'the photo set in the entry "PIJANOVIĆ Jove ANA" (its text runs above and below it)'),
    ('0001010032', 198, (257.9, 275.0, 368.4, 398.8), 'the photo set in the entry "RADE Frane VINKO" (its text runs above and below it)'),
    ('0001010033', 198, (379.8, 145.9, 484.6, 271.9), 'the photo set in the entry "RADELIĆ Ante FRANE" (its text runs above and below it)'),
    ('0001010060', 199, (345.5, 145.7, 458.2, 271.7), 'the photo set in the entry "RADIĆ Marina JOSIP" (its text runs above and below it)'),
    ('0001010144', 201, (345.5, 401.7, 460.4, 529.2), 'the photo set in the entry "RADOJKOVIĆ Stipe MILOŠ" (its text runs above and below it); born 1923 in Podgora, as the record'),
    ('0001010196', 202, (369.5, 145.9, 482.2, 271.9), 'the photo set in the entry "RADOŠ Nikole MIRKO" (its text runs above and below it)'),
    ('0001400743', 203, (93.5, 402.0, 206.2, 527.6), 'the photo set in the entry "RADOVANČIĆ Perice TUGOMIR" (its text runs above and below it)'),
    ('0001010310', 203, (342.4, 403.2, 451.4, 529.2), 'the photo set in the entry "RAFANELI Anđela FRANE" (its text runs above and below it); born 1919 in Makarska, as the record'),
    ('0001010362', 206, (124.0, 262.6, 236.3, 388.2), 'the photo set in the entry "RAK Stipe MARKO" (its text runs above and below it)'),
    ('0001101254', 207, (339.0, 146.6, 453.5, 273.7), 'the photo set in the entry "RAK Mate VESELA" (its text runs above and below it)'),
    ('0001301520', 208, (239.6, 145.2, 353.4, 272.6), 'the photo set in the entry "RAOS Jure IVAN" (its text runs above and below it)'),
    ('0001010395', 209, (99.0, 144.5, 213.1, 272.3), 'the photo set in the entry "RAKIĆ Tome MIRKO" (its text runs above and below it)'),
    ('0001010403', 209, (225.9, 278.4, 335.4, 405.8), 'the photo set in the entry "RAKIĆ Joze ZVONKO" (its text runs above and below it)'),
    ('0001010506', 209, (343.5, 557.3, 457.6, 685.1), 'the photo set in the entry "RAŠKOVIĆ Obrada VASO" (its text runs above and below it)'),
    ('0001010541', 210, (129.3, 558.9, 241.6, 684.6), 'the photo set in the entry "REGOVIĆ Luke CVETKO" (its text runs above and below it)'),
    ('0001010544', 210, (256.2, 426.0, 363.2, 550.2), 'the photo set in the entry "RELIĆ Jovana UROŠ" (its text runs above and below it)'),
    ('0001010642', 211, (95.2, 350.4, 208.2, 476.0), 'the photo set in the entry "RIZVAN Ivana LJUBO" (its text runs above and below it)'),
    ('0001010664', 211, (341.2, 350.1, 453.1, 476.1), 'the photo set in the entry "ROGULJIĆ Mate KAJO" (its text runs above and below it)'),
    ('0001010656', 212, (124.9, 140.2, 238.3, 266.9), 'the photo set in the entry "ROGLIĆ Ivana MATE" (its text runs above and below it)'),
    ('0001400780', 213, (341.9, 551.0, 455.0, 677.0), 'the photo set in the entry "RONČEVIĆ Jure NIKO" (its text runs above and below it)'),
    ('0001010714', 214, (251.0, 225.3, 360.8, 351.0), 'the photo set in the entry "ROŽIĆ Joze DUJE UKIĆ" (its text runs above and below it); born 1913 in Trogir, as the record'),
    ('0001010717', 214, (373.6, 361.4, 486.6, 487.0), 'the photo set in the entry "RUBELJ Marjana IVAN" (its text runs above and below it); born 1923 in Mitlo, as the record'),
    ('0001010718', 215, (102.6, 139.9, 215.3, 264.8), 'the photo set in the entry "RUBELJ Josipa MARJAN" (its text runs above and below it)'),
    ('0001010720', 215, (226.7, 269.0, 339.4, 393.9), 'the photo set in the entry "RUBELJ Marjan TOMO" (its text runs above and below it)'),
    ('0001010722', 215, (347.9, 137.5, 461.0, 263.5), 'the photo set in the entry "RUBEŠA Zane IVO" (its text runs above and below it)'),
    ('0001010738', 216, (125.7, 552.4, 240.9, 676.6), 'the photo set in the entry "RUPIĆ Marka JURE" (its text runs above and below it)'),
    ('0001010743', 217, (100.0, 139.9, 213.4, 265.5), 'the photo set in the entry "RUPIĆ Ivana ŠIME" (its text runs above and below it)'),
    ('0001010761', 217, (344.8, 138.9, 458.2, 264.6), 'the photo set in the entry "RUŽIĆ Josipa FILIP" (its text runs above and below it)'),
    ('0001010762', 217, (348.2, 550.8, 460.8, 676.4), 'the photo set in the entry "RUŽIĆ Ante JOSIP rođen 1923" (its text runs above and below it)'),
    ('0001010783', 218, (133.7, 549.2, 242.8, 675.2), 'the photo set in the entry "SALACAN Jure NIKOLA" (its text runs above and below it)'),
    ('0001010821', 218, (254.2, 424.6, 366.9, 550.6), 'the photo set in the entry "SAMOHOD Alfonsa FILA" (its text runs above and below it)'),
    ('0001010836', 218, (376.1, 276.8, 489.2, 397.4), 'the photo set in the entry "SANSOVIĆ Jure NIKOLA" (its text runs above and below it)'),
    ('0001010969', 219, (94.2, 148.3, 207.6, 273.2), 'the photo set in the entry "SEKULA Mile MILE" (its text runs above and below it)'),
    ('0001010990', 219, (217.6, 246.7, 330.2, 369.4), 'the photo set in the entry "SEKULOVIĆ Jove MILAN "MIJO" (its text runs above and below it); born 1922 in Proložac, as the record'),
    ('0001011006', 220, (129.7, 558.2, 242.4, 685.3), 'the photo set in the entry "SERDAREVIĆ Bože LUKA" (its text runs above and below it); born 1915 in Neorić, as the record'),
    ('0001011007', 220, (372.4, 145.2, 485.4, 271.2), 'the photo set in the entry "SERDAREVIĆ Petra NIKOLA" (its text runs above and below it); born 1922 in Neorić, as the record'),
    ('0001011040', 221, (220.2, 409.9, 334.7, 537.4), 'the photo set in the entry "SIKAVICA Ivana ĆIRO" (its text runs above and below it)'),
    ('0001011157', 222, (130.2, 146.6, 242.9, 274.1), 'the photo set in the entry "SISARIĆ Ante MILJENKO" (its text runs above and below it)'),
    ('0001011158', 222, (251.9, 283.7, 359.2, 410.0), 'the photo set in the entry "SISARIĆ Dragutina RUSKO" (its text runs above and below it)'),
    ('0001011200', 223, (98.8, 337.9, 218.0, 472.9), 'the photo set in the entry "SLIŠKOVIĆ Jakova MARKO" (its text runs above and below it)'),
    ('0001011199', 223, (221.2, 140.4, 334.2, 264.9), 'the photo set in the entry "SLIŠKOVIĆ Ivana ZLATKO" (its text runs above and below it)'),
    ('0001011293', 224, (246.8, 404.4, 355.9, 523.6), 'the photo set in the entry "SPLIVALO Luke PERO" (its text runs above and below it)'),
    ('0001011430', 226, (121.6, 142.3, 235.0, 270.1), 'the photo set in the entry "STANIŠIĆ Mate ANTE" (its text runs above and below it)'),
    ('0001011485', 226, (121.8, 561.8, 236.6, 681.7), 'the photo set in the entry "STANKOVIĆ Josipa MARKO" (its text runs above and below it)'),
    ('0001011710', 227, (339.4, 143.8, 452.8, 270.1), 'the photo set in the entry "STIPIŠIĆ Mile NIKOSLAV" (its text runs above and below it); born 1915 in Vrbovska, as the record'),
    ('0001011761', 228, (124.7, 143.0, 239.2, 270.4), 'the photo set in the entry "STOJANAC Marka MILAN" (its text runs above and below it)'),
    ('0001011935', 228, (370.4, 394.8, 483.8, 509.6), 'the photo set in the entry "STORIĆ Pavla ŠIME" (its text runs above and below it)'),
    ('0001011962', 229, (221.1, 339.1, 333.8, 460.8), 'the photo set in the entry "STUPIN Ante RADE" (its text runs above and below it)'),
    ('0001011978', 230, (127.8, 143.5, 242.0, 270.6), 'the photo set in the entry "SUMIĆ Marjana IVO" (its text runs above and below it)'),
    ('0001400842', 230, (251.2, 285.6, 363.9, 411.2), 'the photo set in the entry "SUMIĆ Luke KARLO" (its text runs above and below it)'),
    ('0001012291', 230, (374.8, 427.9, 487.8, 553.9), 'the photo set in the entry "SUŠAK Đure MILOŠ" (its text runs above and below it)'),
    ('0001012022', 232, (122.0, 314.4, 234.7, 437.2), 'the photo set in the entry "ŠANTIĆ Pave ANTE" (its text runs above and below it)'),
    ('0001012027', 232, (244.0, 145.0, 356.6, 269.2), 'the photo set in the entry "ŠAPONJA Jandrije TODOR" (its text runs above and below it); born 1912 in Dobropoljci, as the record'),
    ('0001012054', 233, (95.7, 362.6, 209.8, 487.2), 'the photo set in the entry "ŠAROVIĆ Aćima JOVO" (its text runs above and below it)'),
    ('0001012080', 233, (217.8, 501.8, 331.6, 628.2), 'the photo set in the entry "ŠEGOVIĆ Nikole ZDRAVKO" (its text runs above and below it)'),
    ('0001401007', 233, (340.5, 349.4, 455.0, 476.8), 'the photo set in the entry "ŠEGVIĆ Antuna MARIJA" (its text runs above and below it)'),
    ('0001012084', 234, (126.1, 265.7, 238.8, 391.3), 'the photo set in the entry "ŠEHOVIĆ Čamila ŠUKRIJA" (its text runs above and below it)'),
    ('0001014108', 234, (249.2, 397.9, 361.9, 523.2), 'the photo set in the entry "ŠEPAROVIĆ Ivana IVO" (its text runs above and below it); born 1922 in Blato, as the record'),
    ('0001012092', 235, (94.4, 274.3, 207.1, 396.3), 'the photo set in the entry "ŠERIĆ Filipa ILIJA" (its text runs above and below it)'),
    ('0001012095', 235, (217.8, 400.0, 330.5, 523.9), 'the photo set in the entry "ŠESTIĆ Ante ANTE PIVAC" (its text runs above and below it); born 1919 in Tučepi, as the record'),
    ('0001012102', 236, (126.1, 556.8, 241.0, 684.6), 'the photo set in the entry "ŠEVERDIJA Marka ROKO" (its text runs above and below it); born 1926 in Zaton, as the record'),
    ('0001012146', 237, (337.5, 281.3, 450.2, 396.8), 'the photo set in the entry "ŠKARIĆ Šime JOSO" (its text runs above and below it)'),
    ('0001012143', 238, (128.8, 556.0, 243.6, 684.2), 'the photo set in the entry "ŠKARIČIĆ Roka JERKO" (its text runs above and below it)'),
    ('0001012151', 239, (211.3, 141.1, 326.2, 268.9), 'the photo set in the entry "ŠKARO Marka SLAVKO" (its text runs above and below it)'),
    ('0001012159', 239, (335.2, 401.8, 449.6, 525.6), 'the photo set in the entry "ŠKOMRLJ Mije MARTIN KRAKUN" (its text runs above and below it); born 1925 in Ramlja, as the record'),
    ('0001012170', 240, (255.4, 141.1, 368.5, 267.5), 'the photo set in the entry "ŠKUGOR Ante JAKOV" (its text runs above and below it)'),
    ('0001012195', 241, (341.4, 254.2, 454.0, 377.6), 'the photo set in the entry "ŠOLAJA Ilije DUŠAN" (its text runs above and below it)'),
    ('0001012198', 242, (126.6, 142.1, 240.7, 269.2), 'the photo set in the entry "ŠOLIĆ Ivana LUKA" (its text runs above and below it)'),
    ('0001101810', 243, (96.8, 145.4, 211.0, 266.4), 'the photo set in the entry "ŠPALETA Ivana VLADO" (its text runs above and below it)'),
    ('0001012210', 243, (218.8, 309.4, 332.2, 435.7), 'the photo set in the entry "ŠPANJA Guste BISERKA" (its text runs above and below it)'),
    ('0001012218', 244, (140.6, 558.5, 248.2, 684.8), 'the photo set in the entry "ŠPRLJAN Gušte NEVIN" (its text runs above and below it); born 1926 in Vodice, as the record'),
    ('0001012221', 244, (388.7, 145.2, 490.2, 271.5), 'the photo set in the entry "ŠTAMBUK Milovana ANTE" (its text runs above and below it); born 1923 in Selca, as the record'),
    ('0001012222', 245, (93.0, 145.2, 205.7, 271.2), 'the photo set in the entry "ŠTAMBUK Ante RUDOLF" (its text runs above and below it)'),
    ('0001012233', 245, (219.2, 277.7, 328.3, 391.1), 'the photo set in the entry "ŠTRADIOT Ivana VINKO" (its text runs above and below it)'),
    ('0001011963', 245, (338.0, 401.5, 451.1, 527.9), 'the photo set in the entry "ŠUBAŠIĆ Vicka JOSIP" (its text runs above and below it)'),
    ('0001012251', 246, (127.6, 156.0, 239.5, 270.1), 'the photo set in the entry "ŠUNDE Cvitka MILIVOJ" (its text runs above and below it)'),
    ('0001012264', 248, (252.2, 342.7, 365.2, 469.0), 'the photo set in the entry "ŠUPE-JURIŠIĆ Ante DARINKA" (its text runs above and below it)'),
    ('0001012267', 250, (119.2, 144.4, 231.9, 270.8), 'the photo set in the entry "ŠUPE Pere IVE" (its text runs above and below it)'),
    ('0001401065', 250, (240.4, 278.4, 354.9, 398.2), 'the photo set in the entry "ŠUPE Jose IVO" (its text runs above and below it)'),
    ('0001012271', 250, (363.0, 144.9, 477.5, 263.7), 'the photo set in the entry "ŠUPE Jose KRSTE" (its text runs above and below it)'),
    ('0001012274', 251, (220.6, 144.5, 335.5, 271.9), 'the photo set in the entry "ŠUPE Ante MILE" (its text runs above and below it)'),
    ('0001012275', 251, (220.6, 407.3, 335.8, 535.1), 'the photo set in the entry "ŠUPE Andrije MILKA" (its text runs above and below it)'),
    ('0001012289', 253, (97.6, 146.9, 208.1, 271.1), 'the photo set in the entry "ŠUSTIĆ Ivana DUJE" (its text runs above and below it)'),
    ('0001012346', 253, (222.4, 365.8, 331.8, 491.4), 'the photo set in the entry "TANBUROVIĆ Ivana TOMO" (its text runs above and below it); born 1914 in Makarska, as the record'),
    ('0001012347', 253, (343.3, 557.8, 457.4, 683.4), 'the photo set in the entry "TANFARA Nikole JERKO" (its text runs above and below it)'),
    ('0001012445', 254, (128.2, 557.8, 241.6, 684.2), 'the photo set in the entry "TICA Gliše SIMO" (its text runs above and below it)'),
    ('0001012533', 254, (251.1, 429.9, 363.8, 554.1), 'the photo set in the entry "TOLIĆ Mate IVO" (its text runs above and below it); born 1922 in Radovići, as the record'),
    ('0001012546', 255, (92.2, 217.2, 204.5, 342.9), 'the photo set in the entry "TOLJ Mate JURE" (its text runs above and below it)'),
    ('0001012557', 255, (215.1, 348.8, 328.5, 466.8), 'the photo set in the entry "TOMAŠEVIĆ Mate ANDRIJA" (its text runs above and below it)'),
    ('0001012559', 255, (337.5, 213.9, 450.9, 335.9), 'the photo set in the entry "TOMAŠEVIĆ Mate IVAN LOGORNIK" (its text runs above and below it); born 1919 in Baći, as the record'),
    ('0001012642', 256, (131.4, 137.3, 244.0, 263.3), 'the photo set in the entry "TOPIĆ Ante MARKO" (its text runs above and below it)'),
    ('0001012657', 256, (375.4, 179.5, 488.8, 305.5), 'the photo set in the entry "TORIĆ Jakova DAVOR" (its text runs above and below it)'),
    ('0001012662', 257, (110.7, 138.7, 211.9, 264.4), 'the photo set in the entry "TOSTI Nikole DONATO" (its text runs above and below it); born 1923 in Sutivan, as the record'),
    ('0001012723', 257, (221.8, 274.8, 332.4, 399.7), 'the photo set in the entry "TREŠELJ Jakova NIKOLA" (its text runs above and below it); born 1907 in Muć, as the record'),
    ('0001012760', 257, (344.5, 417.1, 457.5, 543.1), 'the photo set in the entry "TRNINIĆ Stanka SPASE SPASENIJA" (its text runs above and below it); born 1909 in Kula, as the record'),
    ('0001012781', 259, (89.2, 184.5, 201.9, 310.5), 'the photo set in the entry "TUDOR Joze MIRO" (its text runs above and below it)'),
    ('0001012802', 260, (139.4, 144.4, 243.8, 274.4), 'the photo set in the entry "TURIĆ Ante JOSIP" (its text runs above and below it)'),
    ('0001012829', 260, (378.2, 417.6, 489.8, 531.0), 'the photo set in the entry "UJEVIĆ Nikole IVAN ČUJKUŠIN" (its text runs above and below it); born 1920 in Krivodol, as the record'),
    ('0001400882', 261, (208.7, 283.2, 323.5, 411.4), 'the photo set in the entry "URLIĆ Frane DAVORKA" (its text runs above and below it)'),
    ('0001012843', 261, (331.1, 424.1, 443.8, 547.6), 'the photo set in the entry "URLIĆ Marjana VICKO" (its text runs above and below it); born 1916 in Drašnice, as the record'),
    ('0001012865', 262, (139.8, 250.1, 252.5, 376.4), 'the photo set in the entry "URSIĆ Mije MILJENKO" (its text runs above and below it); born 1919 in Donja, as the record'),
    ('0001013000', 263, (101.4, 206.9, 214.1, 332.9), 'the photo set in the entry "VELA Mate ANTE" (its text runs above and below it)'),
    ('0001013084', 264, (124.4, 146.9, 232.8, 272.5), 'the photo set in the entry "VETMA Joze LUKA" (its text runs above and below it)'),
    ('0001013093', 264, (366.8, 437.3, 479.5, 563.6), 'the photo set in the entry "VEŽA Ante RATKO" (its text runs above and below it)'),
    ('0001013132', 265, (220.0, 151.4, 332.3, 272.7), 'the photo set in the entry "VIDOŠEVIĆ Marka MARKO" (its text runs above and below it)'),
    ('0001013142', 266, (126.8, 556.3, 241.6, 683.0), 'the photo set in the entry "VIDOVIĆ Luke NIKOLA" (its text runs above and below it)'),
    ('0001013186', 266, (251.1, 330.2, 363.8, 456.2), 'the photo set in the entry "VLADIĆ Lovre RAFAEL" (its text runs above and below it); born 1923 in Veliko, as the record'),
    ('0001013280', 267, (350.8, 271.4, 457.0, 393.8), 'the photo set in the entry "VRDOLJAK Frane FABIJAN" (its text runs above and below it); born 1925 in Splitu, as the record'),
    ('0001013277', 268, (125.9, 312.7, 240.8, 439.8), 'the photo set in the entry "VRCIĆ Jure SLAVKA" (its text runs above and below it)'),
    ('0001013276', 268, (250.2, 451.4, 363.3, 577.4), 'the photo set in the entry "VRCIĆ Paške FRANE" (its text runs above and below it)'),
    ('0001013275', 268, (371.2, 324.0, 485.7, 451.0), 'the photo set in the entry "VRCIĆ Krste ANTE" (its text runs above and below it)'),
    ('0001013268', 269, (102.4, 140.4, 211.4, 268.2), 'the photo set in the entry "VRANKOVIĆ Filipa MILIVOJ" (its text runs above and below it)'),
    ('0001013629', 271, (220.2, 276.2, 330.8, 401.5), 'the photo set in the entry "VULJAN Ivana VLADIMIR" (its text runs above and below it); born 1923 in Sućuraj, as the record'),
    ('0001013624', 271, (341.4, 142.8, 454.1, 267.7), 'the photo set in the entry "VULINOVIĆ Mitra ŠPIRO" (its text runs above and below it)'),
    ('0001013608', 271, (341.4, 555.1, 450.9, 681.4), 'the photo set in the entry "VULETA Jure IVAN" (its text runs above and below it)'),
    ('0001013602', 272, (373.6, 141.3, 486.3, 266.6), 'the photo set in the entry "VUKŠA Marka PAVLE KALIĆ" (its text runs above and below it); born 1925 in Čista, as the record'),
    ('0001013558', 273, (218.1, 399.6, 331.1, 523.4), 'the photo set in the entry "VUKOVIĆ Jure JOSIP" (its text runs above and below it)'),
    ('0001013526', 273, (341.2, 554.8, 454.2, 681.2), 'the photo set in the entry "VUKOREPA Luke LJUBO" (its text runs above and below it)'),
    ('0001013525', 274, (132.2, 261.6, 245.2, 386.8), 'the photo set in the entry "VUKOREPA Luke DANE" (its text runs above and below it)'),
    ('0001013515', 274, (253.4, 141.6, 367.8, 268.6), 'the photo set in the entry "VUKO Miška IVAN IVO" (its text runs above and below it); born 1927 in Tijarica, as the record'),
    ('0001013382', 275, (214.6, 401.5, 328.4, 527.5), 'the photo set in the entry "VUJČIĆ Joze MARIJA" (its text runs above and below it)'),
    ('0001013346', 276, (130.7, 248.4, 243.4, 372.6), 'the photo set in the entry "VUČKOVIĆ Stipe LUKA" (its text runs above and below it); born 1915 in Dugopolje, as the record'),
    ('0001013660', 276, (375.2, 247.4, 487.9, 372.4), 'the photo set in the entry "ZARO Karla JOZO" (its text runs above and below it)'),
    ('0001013705', 277, (86.0, 146.6, 192.2, 272.3), 'the photo set in the entry "ZEHETNER Roberta HRVOJE" (its text runs above and below it)'),
    ('0001013783', 278, (127.8, 558.0, 243.4, 685.4), 'the photo set in the entry "ŽABICA Petra MILE ŠKAJO" (its text runs above and below it); born 1922 in Vela, as the record'),
    ('0001013803', 278, (372.6, 145.6, 486.0, 271.3), 'the photo set in the entry "ŽARNIĆ Mate MATE KRANKIN" (its text runs above and below it); born 1914 in Ma, as the record'),
    ('0001013806', 279, (95.9, 368.9, 210.0, 496.0), 'the photo set in the entry "ŽDERIĆ Nikole ZORA ZORKA" (its text runs above and below it); born 1923 in Brist, as the record'),
    ('0001013820', 279, (343.8, 241.4, 455.0, 367.1), 'the photo set in the entry "ZIDIĆ Ivana DINKO" (its text runs above and below it)'),
    ('0001013846', 280, (251.7, 336.9, 364.7, 454.6), 'the photo set in the entry "ŽIVALJ Joze ANTE ZUKO" (its text runs above and below it); born 1923 in Sinj, as the record'),
    ('0001013961', 282, (238.2, 145.4, 353.1, 263.8), 'the photo set in the entry "ŽIVKOVIĆ Tome MILJENKO" (its text runs above and below it)'),
    ('0001013967', 282, (360.6, 415.4, 475.1, 542.5), 'the photo set in the entry "ŽIVKOVIĆ Vice MLADEN" (its text runs above and below it)'),
    ('0001013968', 283, (218.5, 214.3, 333.3, 341.8), 'the photo set in the entry "ŽIVKOVIĆ Paške MOJMIR" (its text runs above and below it); born 1922 in Zaton, as the record'),
    ('0001013971', 283, (342.3, 314.4, 455.4, 440.4), 'the photo set in the entry "ŽIVKOVIĆ Vice NIKOLA" (its text runs above and below it)'),
    ('0001013972', 284, (141.2, 144.5, 246.7, 270.1), 'the photo set in the entry "ŽIVKOVIĆ Bože PETAR" (its text runs above and below it)'),
    ('0001014042', 284, (262.2, 362.4, 368.4, 486.6), 'the photo set in the entry "ŽIŽIĆ Kaje FRANE" (its text runs above and below it)'),
    ('0001014043', 284, (380.2, 287.5, 491.8, 413.9), 'the photo set in the entry "ŽIŽIĆ Luke IVANKO" (its text runs above and below it)'),
    ('0001000920', 26, (126.8, 150.5, 239.2, 272.9), 'the photo set in the entry "BOGUNOVIĆ-ĆULIBRK Jakova MANDA" (its text runs above and below it); born 1925, father Jakov, as the record (Baćina)'),
    ('0001004819', 92, (124.8, 555.2, 237.8, 679.4), 'the photo set in the entry "JURAGA Slavka MARKO POLIVAČEV" (its text runs above and below it); born 1925, "Polivačev", as the record'),
    ('0001300936', 143, (336.4, 139.4, 450.5, 253.6), 'the photo set in the entry "MARTINAC-BOBETKO Mate MAGDALENA" (its text runs above and below it); father Mate, the unit\'s only Magdalena Martinac'),
    ('0001006923', 147, (95.4, 264.5, 202.6, 385.8), 'the photo set in the entry "MATKOVIĆ Frane NIKOLA ođen 1919" (its text runs above and below it); born 1919 in Zavojane, as the record'),
    ('0001006960', 148, (257.9, 370.0, 372.0, 496.8), 'the photo set in the entry "MEDAKOVIĆ Đure TODOR" (its text runs above and below it); Kovačići, Knin, as the record'),
    ('0001010682', 213, (219.3, 138.2, 333.0, 265.3), 'the photo set in the entry "ROMAN Šime ROKO PIVĆEV" (its text runs above and below it); born 1913 on Žirje, "Pivčev", as the record'),
    ('0001013636', 276, (252.6, 146.6, 355.9, 272.3), 'the photo set in the entry "ZAGORAC Đure DUŠAN" (its text runs above and below it); born 1910 in Otišić (Otešić), as the record'),
    ('0001013947', 282, (116.1, 279.8, 228.8, 405.8), 'the photo set in the entry "ŽIVKOVIĆ Ignacija MARIN" (its text runs above and below it); born 1922 in Zečevo-Rogoznica (Rogoznica), as the record'),
    # men split out of glued entries (2026-10-17), and entries whose name had several records: the record holds the entry
    ('0001000622', 13, (90.3, 324.5, 202.6, 451.2), 'the photo set in the entry of Beara Marka Marko (its text runs above and below it; the record holds the entry)'),
    ('0001000924', 27, (91.3, 493.4, 204.0, 620.9), 'the photo set in the entry of Bogunović Ivana Petar (its text runs above and below it; the record holds the entry)'),
    ('0001000928', 28, (128.4, 402.8, 241.1, 523.0), 'the photo set in the entry of Bojanić Šimuna Nikola (its text runs above and below it; the record holds the entry)'),
    ('0001001012', 30, (128.7, 461.3, 241.4, 575.1), 'the photo set in the entry of Borovina Petra Ante (its text runs above and below it; the record holds the entry)'),
    ('0001400120', 33, (91.6, 467.5, 205.7, 595.3), 'the photo set in the entry of Bratinić-Forean Nikole Margarita (its text runs above and below it; the record holds the entry)'),
    ('0001101687', 42, (126.8, 323.6, 239.1, 442.7), 'the photo set in the entry of Čeko Ivana Vinko (its text runs above and below it; the record holds the entry)'),
    ('0001002278', 55, (223.8, 365.0, 336.5, 481.6), 'the photo set in the entry of Dragičević Josipa Mijo (its text runs above and below it; the record holds the entry)'),
    ('0001002904', 61, (358.2, 366.4, 457.2, 492.1), 'the photo set in the entry of Ercegović Stipe Josip (its text runs above and below it; the record holds the entry)'),
    ('0001003034', 65, (93.7, 288.2, 206.4, 406.7), 'the photo set in the entry of Franin-Olić Ante Blaženka (its text runs above and below it; the record holds the entry)'),
    ('0001403055', 77, (94.6, 444.8, 207.3, 570.4), 'the photo set in the entry of Gudelj-Zec Ivana Neda (its text runs above and below it; the record holds the entry)'),
    ('0001400260', 77, (339.4, 277.7, 452.1, 403.4), 'the photo set in the entry of Gulin Marka Ante (its text runs above and below it; the record holds the entry)'),
    ('0001003566', 78, (255.0, 389.5, 369.9, 517.3), 'the photo set in the entry of Gulin Jose Dane (its text runs above and below it; the record holds the entry)'),
    ('0001003614', 80, (372.3, 511.7, 486.8, 638.8), 'the photo set in the entry of Hajdarhodžić Avde Muharem (its text runs above and below it; the record holds the entry)'),
    ('0001403066', 93, (98.8, 363.6, 210.7, 490.0), 'the photo set in the entry of Jurašin-Božović Ante Anka (its text runs above and below it; the record holds the entry)'),
    ('0001004849', 95, (217.4, 276.0, 332.6, 404.1), 'the photo set in the entry of Jurković-Belamarić Jakova Milka (its text runs above and below it; the record holds the entry)'),
    ('0001400355', 103, (223.8, 295.4, 336.5, 416.0), 'the photo set in the entry of Katić Mate Nikoprpić (its text runs above and below it; the record holds the entry)'),
    ('0001005235', 108, (249.7, 187.0, 364.2, 314.0), 'the photo set in the entry of Kokić-Rak Ante Anka (its text runs above and below it; the record holds the entry)'),
    ('0001400381', 109, (99.8, 420.2, 212.4, 545.8), 'the photo set in the entry of Kocić-Rak Ivana DRAGI-CAžMIRKA (its text runs above and below it; the record holds the entry)'),
    ('0001005228', 109, (343.8, 445.2, 458.3, 570.8), 'the photo set in the entry of Kokić Krste Ive (its text runs above and below it; the record holds the entry)'),
    ('0001005227', 109, (222.2, 300.9, 335.6, 428.0), 'the photo set in the entry of Kokić Jose Ive (its text runs above and below it; the record holds the entry)'),
    ('0001005232', 110, (250.7, 283.0, 362.6, 408.6), 'the photo set in the entry of Kokić Krste Nikola (its text runs above and below it; the record holds the entry)'),
    ('0001400417', 116, (372.1, 263.5, 485.2, 389.5), 'the photo set in the entry of Krilić Luke Ivaniko (its text runs above and below it; the record holds the entry)'),
    ('0001005717', 124, (127.4, 357.3, 239.7, 477.9), 'the photo set in the entry of Kumbat Ivana Jure (its text runs above and below it; the record holds the entry)'),
    ('0001006030', 133, (97.1, 473.5, 209.4, 591.2), 'the photo set in the entry of Letunica Laze Špiro (its text runs above and below it; the record holds the entry)'),
    ('0001006244', 136, (128.3, 217.4, 242.4, 344.5), 'the photo set in the entry of Mačukat-Radin Martina Vilson (its text runs above and below it; the record holds the entry)'),
    ('0001006243', 136, (251.0, 353.5, 364.4, 479.8), 'the photo set in the entry of Mačukat-Radin Ante Mate (its text runs above and below it; the record holds the entry)'),
    ('0001006438', 138, (133.6, 361.0, 246.2, 486.6), 'the photo set in the entry of Marasović Ante Nediljko (its text runs above and below it; the record holds the entry)'),
    ('0001007805', 156, (249.8, 337.2, 362.4, 462.8), 'the photo set in the entry of Miošić Šimuna Milan (its text runs above and below it; the record holds the entry)'),
    ('0001400592', 159, (214.9, 283.9, 327.6, 409.9), 'the photo set in the entry of Mrdeža Ante Mijo Cr-Nogaća (its text runs above and below it; the record holds the entry)'),
    ('0001403259', 183, (342.6, 304.3, 456.0, 430.6), 'the photo set in the entry of Petranović-Ristić Vasa Marija (its text runs above and below it; the record holds the entry)'),
    ('0001403117', 185, (347.8, 427.7, 460.9, 553.7), 'the photo set in the entry of Putniković Konstantina Branko-Popivačev (its text runs above and below it; the record holds the entry)'),
    ('0001400695', 194, (130.5, 283.4, 243.2, 404.4), 'the photo set in the entry of Plenča Paške Mile Pi-Cunov (its text runs above and below it; the record holds the entry)'),
    ('0001403155', 201, (101.4, 257.2, 214.1, 382.2), 'the photo set in the entry of Radić Špira Nikola (its text runs above and below it; the record holds the entry)'),
    ('0001400748', 204, (124.9, 381.8, 236.1, 506.0), 'the photo set in the entry of Rak Jose Benjanin Baj-Lo (its text runs above and below it; the record holds the entry)'),
    ('0001010371', 204, (368.7, 469.7, 482.1, 595.3), 'the photo set in the entry of Rak-Masal Ive Janja (its text runs above and below it; the record holds the entry)'),
    ('0001010359', 205, (227.2, 284.6, 341.3, 399.1), 'the photo set in the entry of Rak Stipe Jere (its text runs above and below it; the record holds the entry)'),
    ('0001301499', 206, (368.8, 457.9, 482.2, 583.6), 'the photo set in the entry of Rak-Đorđević Ante Slavka (its text runs above and below it; the record holds the entry)'),
    ('0001010372', 207, (227.7, 265.2, 330.3, 390.8), 'the photo set in the entry of Rak-Orlović Ante Tonka (its text runs above and below it; the record holds the entry)'),
    ('0001010379', 208, (362.3, 274.8, 476.4, 402.2), 'the photo set in the entry of Rakić Ivana Dane (its text runs above and below it; the record holds the entry)'),
    ('0001403275', 211, (217.6, 206.8, 330.2, 332.5), 'the photo set in the entry of Rizvan Stipe Marin (its text runs above and below it; the record holds the entry)'),
    ('0001010741', 216, (372.6, 248.8, 485.3, 374.5), 'the photo set in the entry of Rupić Luke Marko (its text runs above and below it; the record holds the entry)'),
    ('0001301605', 223, (345.8, 353.5, 453.0, 471.9), 'the photo set in the entry of Smajo-Bečić Marka Ankica (its text runs above and below it; the record holds the entry)'),
    ('0001011416', 225, (222.6, 319.2, 335.0, 436.5), 'the photo set in the entry of Stanić-Šubašić Vinka Anka (its text runs above and below it; the record holds the entry)'),
    ('0001011977', 229, (343.0, 221.0, 456.4, 347.0), 'the photo set in the entry of Sulje Ante Ive (its text runs above and below it; the record holds the entry)'),
    ('0001012292', 231, (220.6, 370.8, 333.7, 491.8), 'the photo set in the entry of Šušak Marka Stevo (its text runs above and below it; the record holds the entry)'),
    ('0001012049', 232, (367.3, 436.8, 480.7, 563.5), 'the photo set in the entry of Šarić Josipa Slavko (its text runs above and below it; the record holds the entry)'),
    ('0001012144', 238, (258.2, 378.0, 363.6, 496.4), 'the photo set in the entry of Škaričić Roka Josip (its text runs above and below it; the record holds the entry)'),
    ('0001012261', 247, (226.4, 319.9, 339.5, 444.8), 'the photo set in the entry of Šupe Jakova Ante (its text runs above and below it; the record holds the entry)'),
    ('0001012262', 247, (347.2, 468.7, 461.6, 596.5), 'the photo set in the entry of Šupe Marka Ante (its text runs above and below it; the record holds the entry)'),
    ('0001012263', 248, (128.3, 198.7, 242.4, 326.5), 'the photo set in the entry of Šupe Sime Ante (its text runs above and below it; the record holds the entry)'),
    ('0001101828', 249, (223.3, 290.9, 335.6, 416.5), 'the photo set in the entry of Šupe Ante Joso (its text runs above and below it; the record holds the entry)'),
    ('0001012270', 249, (345.7, 428.2, 458.4, 541.6), 'the photo set in the entry of Šupe Tome Joso (its text runs above and below it; the record holds the entry)'),
    ('0001012280', 252, (370.6, 277.7, 483.7, 400.1), 'the photo set in the entry of Šupe-Bekavac Lovre Zorka (its text runs above and below it; the record holds the entry)'),
    ('0001012823', 260, (252.4, 282.9, 365.8, 409.3), 'the photo set in the entry of Udovičić-Birin Stipe Ilinka (its text runs above and below it; the record holds the entry)'),
    ('0001013193', 269, (345.7, 323.5, 459.1, 449.2), 'the photo set in the entry of Vlahov Lucijana Ante (its text runs above and below it; the record holds the entry)'),
    ('0001013192', 270, (134.8, 235.7, 248.9, 363.5), 'the photo set in the entry of Vlahov Ante Ante (its text runs above and below it; the record holds the entry)'),
    ('0001400931', 272, (129.3, 314.1, 241.6, 437.6), 'the photo set in the entry of Vukšić Vice Đesanko (its text runs above and below it; the record holds the entry)'),
    ('0001013603', 272, (250.7, 439.9, 363.4, 566.6), 'the photo set in the entry of Vukšić Mate Ante (its text runs above and below it; the record holds the entry)'),
    ('0001403310', 277, (331.8, 463.9, 444.1, 590.3), 'the photo set in the entry of Zlodre Božidara Tonka (its text runs above and below it; the record holds the entry)'),
    ('0001013810', 279, (217.6, 504.7, 332.0, 631.1), 'the photo set in the entry of Žegarac Šime Danilo (its text runs above and below it; the record holds the entry)'),
]

DALMATINCI_CREDIT = 'Dalmatinci u Prvoj proleterskoj'

VIROVITICA = [
    # Velagić, Virovitica u NOB (site: virovitica-spomenica-1941.pdf = znaci 00003/653.pdf pp. 221-238): each holder of the
    # spomenica's biography under his portrait and its caption. Record, page in the site's PDF, the photo's box, why
    ('0048000596', 7, (231.3, 317.1, 366.4, 506.4), '"Nedeljko Mrđen", the caption of the portrait over his biography'),
    ('0016002566', 8, (473.0, 539.8, 600.9, 714.2), '"Rudi Rajh Top", the caption of the portrait over his biography'),
    ('0058002338', 8, (473.0, 539.8, 600.9, 714.2), '"Rudi Rajh Top", the caption of the portrait over his biography'),
    ('0030000784', 13, (273.5, 573.3, 405.5, 783.0), '"Zdravko Uskoković Heroj", the caption of the portrait over his biography'),
    ('0016003238', 15, (238.4, 426.3, 368.7, 617.1), '"Dragan Volner Baćuška", the caption of the portrait over his biography'),
]
VIROVITICA_CREDIT = 'Savo Velagić, Virovitica u narodnooslobodilačkoj borbi i socijalističkoj revoluciji'

KRIZANI = [
    # Križani v boju za svobodo (site: krizani-v-boju-za-svobodo.pdf = znaci 00003/720.pdf pp. 78-108): "Padli za svobodo",
    # three portraits a page in one strip, each level with its biography. Record, page in the site's PDF, the portrait's box
    ('0142000032', 1, (170.1, 508.9, 287.2, 656.2), 'the portrait level with the biography of Bizin Edvard (the record holds the entry)'),
    ('0144000043', 2, (117.2, 205.6, 232.2, 346.5), 'the portrait level with the biography of Bogateč Drago (the record holds the entry)'),
    ('0064000245', 3, (165.4, 195.6, 282.5, 344.4), 'the portrait level with the biography of Bogateč Miroslav (the record holds the entry)'),
    ('0142000038', 3, (165.4, 195.6, 282.5, 344.4), 'the portrait level with the biography of Bogateč Miroslav (the record holds the entry)'),
    ('0142000169', 4, (114.5, 197.6, 229.0, 345.8), 'the portrait level with the biography of Guštin Karel (the record holds the entry)'),
    ('0142000194', 4, (114.5, 355.2, 229.0, 501.9), 'the portrait level with the biography of Juretič Boris (the record holds the entry)'),
    ('0070000543', 5, (174.5, 354.1, 290.2, 503.1), 'the portrait level with the biography of Kobau Franc (the record holds the entry)'),
    ('0004002405', 10, (143.7, 202.2, 273.8, 343.7), 'the portrait level with the biography of Sedmak Božič (the record holds the entry)'),
    ('0142000437', 11, (208.6, 197.3, 324.3, 344.0), 'the portrait level with the biography of Sedmak Franc (the record holds the entry)'),
    ('0142000439', 11, (208.6, 353.4, 324.3, 499.4), 'the portrait level with the biography of Sedmak Henrik (the record holds the entry)'),
    ('0142000488', 14, (126.4, 355.6, 253.8, 502.3), 'the portrait level with the biography of Sulčič Danilo (the record holds the entry)'),
]
KRIZANI_CREDIT = 'Križani v boju za svobodo / S. Croce nella lotta per la libertà'

SAME = [
    # one man under two records that aren't linked, each with a photo of its own (another photo, or another crop),
    # checked by hand: lists of faces (the Galerija page, the home page's margins) show him once
    ('0035001622', '0147000189', 'Došen Stevan, the Zagrebački odred\'s first commander, who fell commanding the brigade '
                                 '»Matija Gubec« of the 32. divizija: the same face in both books'),
    ('0018001171', '0083010129', 'Obradović Vlado "Kameni", born 1912 in Lipa (Bihać): the 2. and the 6. vojvođanska\'s books '
                                 'print the same photograph'),
    ('0002000203', '0003010121', 'Babić Petar "Pepa", narodni heroj from Lički Tiškovac: both hero books know one, '
                                 'born 1 November 1919 (the Druga lička book prints 1913)'),
    ('0005010943', '0005100800', 'Rakočević Radomir: Štitarica, father Jovan/Jovo; two crops of one Commons photo'),
    ('0026000087', '0039000094', 'Buha Boško: the book of the Druga proleterska prints another photo of him'),
    ('0035009678', '0058003202', 'Štrok Izidor: father Pavao, born 1911, in both units'),
    ('0043000515', '0101000096', 'Kelava Ante "Zoro": born 1916 in Dobro, Livno, in both units'),
    ('0081001390', '0101000260', 'Šakotić Radovan: born 1906 in Orahovac, Trebinje; two scans of one photo'),
    ('0001004941', '0007002272', 'Kapičić Jovo (Jovan), born 1919 in Gaeta, in both units'),
    ('0109000870', '0016002048', 'Nenezić Radojica, born 1921, Broćanac (Nikšić), in both units'),
    ('0163000104', '0048000364', 'Kecman Pero, father Jovo, born 1921 near Bosanski Petrovac'),
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


OLD: dict = {}   # with --new: the index as it stands, whose prints are kept rather than made again


def save(im: Image.Image, sid: str, credit: str) -> dict:
    """The print (HEIGHT high) and, where the source is much bigger, the large photo (up to LARGE high)."""
    if OLD.get(sid, {}).get('c') == credit and (OUT / OLD[sid]['f']).exists():      # --new: made before
        return {k: OLD[sid][k] for k in ('f', 'v') if k in OLD[sid]}
    small = im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS)
    small.save(OUT / f'{sid}.jpg', quality=80, optimize=True, progressive=True)
    if im.height < 1.5 * HEIGHT:                         # a book's small print: the print is all there is
        (OUT / f'{sid}-v.jpg').unlink(missing_ok=True)
        return {'f': f'{sid}.jpg'}
    if im.height > LARGE:
        im = im.resize((round(im.width * LARGE / im.height), LARGE), Image.LANCZOS)
    im.save(OUT / f'{sid}-v.jpg', quality=84, optimize=True, progressive=True)
    return {'f': f'{sid}.jpg', 'v': f'{sid}-v.jpg'}


def mark_same(index: dict) -> None:
    """Mark each portrait of a man who has another portrait under another record with `same`: the record shown for
    him in lists of faces (the first by the units' order in units.ts). One man has a record in each unit or book that
    prints him, and a narodni heroj's photo goes to each. Same man: the same print, linked records, or SAME."""
    import hashlib
    import re
    units_ts = (ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    order, linked = {}, []
    for u, data_file in enumerate(re.findall(r"dataFile:\s*'/([^']+)'", units_ts)):
        path = PUBLIC / data_file
        if not path.exists():
            continue
        for i, s in enumerate(json.loads(path.read_text(encoding='utf-8'))):
            if s['soldier_id'] in index:
                order[s['soldier_id']] = (u, i)
                linked += [(s['soldier_id'], o['soldier_id']) for o in s.get('other_sources', [])
                           if o.get('soldier_id') in index]
    parent = {sid: sid for sid in index}

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    by_print = {}
    for sid, e in index.items():
        by_print.setdefault(hashlib.md5((OUT / e['f']).read_bytes()).hexdigest(), []).append(sid)
    pairs = [(ids[0], other) for ids in by_print.values() for other in ids[1:]] + linked
    pairs += [(a, b) for a, b, _why in SAME if a in index and b in index]
    for a, b in pairs:
        parent[root(a)] = root(b)
    groups = {}
    for sid in index:
        index[sid].pop('same', None)
        groups.setdefault(root(sid), []).append(sid)
    for ids in groups.values():
        if len(ids) > 1:
            first, *rest = sorted(ids, key=lambda sid: order.get(sid, (999, 0)))
            for sid in rest:
                index[sid]['same'] = first
            print(f"  one man: {first} shown, {', '.join(rest)} not")


def main():
    if '--same' in sys.argv:              # only mark the same men in the index as it stands, rendering nothing
        index = json.loads(INDEX.read_text(encoding='utf-8'))
        mark_same(index)
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=0, sort_keys=True), encoding='utf-8')
        print(f"{sum('same' in e for e in index.values())} of {len(index)} portraits are a man shown under another record")
        return
    OUT.mkdir(exist_ok=True)
    if '--new' in sys.argv and INDEX.exists():
        OLD.update(json.loads(INDEX.read_text(encoding='utf-8')))
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
            index[s['soldier_id']] = {**save(im, s['soldier_id'], credit), 'c': credit}
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
        index[sid] = {**save(im, sid, f'znaci.org, br. {pid}'), 'c': f'znaci.org, br. {pid}',
                      'h': f'https://znaci.org/fotografija.php?br={pid}'}
    print(f'gallery: {len(GALLERY)} portraits')
    for sid, path, page, xref, crop, _why in UNIT_BOOKS:
        im = F.book_image(path, xref).convert('L')
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        credit = BOOK_TITLES[path.rsplit('_', 1)[0].removesuffix('.pdf')]
        index[sid] = {**save(im, sid, credit), 'c': credit, 'h': f'https://znaci.org/{path}#page={page}'}
    print(f"units' books: {len(UNIT_BOOKS)} portraits")
    for sid, path, page, box, _why in PAGE_BOOKS:
        pg = fitz.open(F.book_pdf(path))[page - 1]
        hits = [i for i in pg.get_image_info() if fitz.Rect(i['bbox']).intersects(fitz.Rect(box))]
        dpi = max([DPI] + [round(72 * i['width'] / (i['bbox'][2] - i['bbox'][0])) for i in hits if i['bbox'][2] > i['bbox'][0]])
        pix = pg.get_pixmap(clip=fitz.Rect(box), dpi=min(dpi, 600), colorspace=fitz.csGRAY)
        im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
        credit = BOOK_TITLES[path.rsplit('_', 1)[0].removesuffix('.pdf')]
        index[sid] = {**save(im, sid, credit), 'c': credit, 'h': f'https://znaci.org/{path}#page={page}'}
    print(f"units' books, cut from the page: {len(PAGE_BOOKS)} portraits")
    # books on the site that set a photo beside or inside the entry: cut from the site's PDF at the photo's own resolution
    for pdf, credit, href, rows in (
            ('tuzla-spomen-knjiga.pdf', MEMORIAL_CREDIT, 'https://znaci.org/00001/144.pdf#page={}', [(r[0], r[2] + 7, r[2], r[3]) for r in MEMORIAL]),
            ('dalmatinci-prva-proleterska.pdf', DALMATINCI_CREDIT, 'https://znaci.org/00001/207_4.pdf#page={}', [(r[0], r[1] + 1, r[1], r[2]) for r in DALMATINCI]),
            ('virovitica-spomenica-1941.pdf', VIROVITICA_CREDIT, 'https://znaci.org/00003/653.pdf#page={}', [(r[0], r[1] + 220, r[1], r[2]) for r in VIROVITICA]),
            ('krizani-v-boju-za-svobodo.pdf', KRIZANI_CREDIT, 'https://znaci.org/00003/720.pdf#page={}', [(r[0], r[1] + 77, r[1], r[2]) for r in KRIZANI])):
        doc = fitz.open(PUBLIC / 'pdfs' / pdf)
        n = 0
        for sid, book_page, page, box in rows:
            if sid in index:                    # the unit's own book comes first
                continue
            pg = doc[page - 1]
            hits = [i for i in pg.get_image_info() if fitz.Rect(i['bbox']).intersects(fitz.Rect(box))]
            info = max(hits, key=lambda i: (fitz.Rect(i['bbox']) & fitz.Rect(box)).get_area())
            dpi = max(DPI, round(72 * info['width'] / (info['bbox'][2] - info['bbox'][0])))   # the photo's own resolution
            pix = pg.get_pixmap(clip=fitz.Rect(box), dpi=dpi, colorspace=fitz.csGRAY)
            im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('L')
            index[sid] = {**save(im, sid, credit), 'c': credit, 'h': href.format(book_page)}
            n += 1
        print(f'{pdf}: {n} portraits')
    for sid, name, crop, license, artist, _why in COMMONS:
        if sid in index:                    # a photo from the unit's own book comes first
            continue
        im = Image.open(commons_file(name)).convert('L')
        if crop:
            w, h = im.size
            im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        credit = f'Wikimedia Commons ({license})' if license.startswith('CC BY') else 'Wikimedia Commons'
        credit = f'{artist}, {credit}' if artist else credit
        index[sid] = {**save(im, sid, credit), 'c': credit, 'h': f'https://commons.wikimedia.org/wiki/File:{name}'}
    print(f'Commons: {len(COMMONS)} portraits')
    # Portraits this script doesn't make (the Proleterski bataljon Bosanske krajine's 180, cut beside each bio when
    # its unit came to the site) stay as they are: an entry whose credit is none of this script's sources
    own = {credit for *_, credit in BOOKS} | set(BOOK_TITLES.values()) | {MEMORIAL_CREDIT, DALMATINCI_CREDIT, VIROVITICA_CREDIT, KRIZANI_CREDIT}
    old = json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {}
    kept = {sid: e for sid, e in old.items() if sid not in index and e['c'] not in own
            and not e['c'].startswith(('znaci.org, br.', 'Wikimedia Commons')) and 'Wikimedia Commons' not in e['c']}
    index.update(kept)
    print(f'kept {len(kept)} portraits made elsewhere')
    mark_same(index)
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
