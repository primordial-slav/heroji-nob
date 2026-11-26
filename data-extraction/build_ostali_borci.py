"""
Ostali borci (unit 122, and 131-138 for the 1964 census): every soldier of a book across units who has no record on
the site.

The books across units (the hero books, Trebinjci pali, the village chronicles, the Karlovac archive's volumes,
Ofanziva 1942, ...) are read by their parsers into data-extraction/{poreklo,znaci}/<book>-entries.json, and
scripts/match_references.py adds each entry that belongs to a record of a unit to that record (a `reference`
correction). The entries no record took are the soldiers whose unit is not on the site yet, or whom the books name
without one: they become records of their own here, so that their names and what the books say of them are on the
site and can be found.

One man printed in several of these books is one record: entries of the same name from different books that agree
(the father and one of birth year, birthplace, year of death; or birth year and birthplace; for two hero books the
father or the birth year; for the books that give little more than the name, a unit or the place of death together
with the year of death or each other), with nothing that disagrees, are merged, the richest entry first (a page on the
site's scans before the library's, then the longest text) and the others in `other_sources`. An entry of the same man
as an entry already on the site (a record took one of his entries) is left out: he has his record.

Record IDs are kept in data-extraction/ostali_borci_ids.json (entry ID -> record ID), so a record keeps its ID however
its entries change: a man whose entries had an ID keeps it (the first entry's, if two records of before become one), a
new man gets the next free one (0122900001 on; the first records took 0122 + the book's two digits + the entry's
number). A re-run after new references only drops the records whose men have found their unit.

The 1964 census of the war's dead (Žrtve rata 1941-1945, data-extraction/zrtve-rata/, one volume a republic or
province) names 180,000 fallen partisans, most with no other book: a man only the census names is a record of his
volume's part of Ostali borci (131-138, CENSUS_VOLUMES; 160,000 men would make one unit too big for a search part or
a file in git), with the ID of his census entry under the part's code (9021004235 -> 0132004235), so the registry
doesn't hold him; a man the census and another book name is a record of 122. Two census entries are never one man:
the volumes list each of the dead once, and one name, father and year in two republics are as a rule two men. The
census gives its columns as fields (born_in, ethnicity, death_year, death_place), which become the record's fields.

Usage:
    python data-extraction/build_ostali_borci.py            # dry run: counts and samples
    python data-extraction/build_ostali_borci.py --write    # write website/public/ostali-borci*.json
Then (docs/claude/ostali-borci.md): python scripts/normalize_all_json.py --brigade 122 131 132 133 134 135 136 137 138
--apply; python scripts/extract_structured_fields.py --brigade 122 --apply; python scripts/apply_corrections.py --apply
--brigade 122 131 132 133 134 135 136 137 138; python scripts/build_relations.py --write.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from match_references import ENTRY_DIRS, HERO_BOOKS, fold, same_father, stem  # noqa: E402
from extract_structured_fields import NAME_LISTS, fix_place  # noqa: E402
from name_utils import (BRIGADE_CONFIGS, CENSUS_VOLUMES, OSTALI_CODES, REGIONAL_GENITIVES, clean_name_field,  # noqa: E402
                        genitive_to_nominative, normalize_soldier, to_title_case)
import convert_fathers_genitive as fathers_genitive  # noqa: E402
from safe_write import write_text  # noqa: E402  (E: can refuse a write for a moment, OSError 22: it stopped a rebuild 2026-11-19)

FATHER_WORD = re.compile(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+$')

CODE = 122
IDS = ROOT / 'data-extraction' / 'ostali_borci_ids.json'
ON_SITE = ROOT / 'data-extraction' / '.cache' / 'ostali_on_site.json'     # the entries left out for their man's record
FIRST_NEW = 900001
OUT = ROOT / 'website' / 'public' / 'ostali-borci.json'     # not *soldiers.json, which the parsers' corpora read
# a man whose entries name a unit on the site without doubt is a record of that unit, not of 122 (2026-11-20, the
# user's rule; scripts/unit_named.py): his record in the unit's file, its ID from UNIT_FIRST in a range no unit's books
# use, kept by entry as IDS keeps 122's (UNIT_IDS: entry -> the unit record's ID), his 122 ID in former_ids
UNIT_IDS = ROOT / 'data-extraction' / 'unit_record_ids.json'
UNIT_FIRST = 900001
MOVED = ROOT / 'website' / 'data' / 'moved-ids.json'
# one man's fix by hand, kept by entry (2026-11-22, the user: "If one soldier changes, we should just change that entry"):
# {"<entry ID>": {"for": "<record ID>", "fields": {...}, "reason", "by", "date"}}, written by scripts/patch_record.py,
# which changes the record in place in seconds; this script gives the record the same fields on every full run
# (apply_overrides), so the two agree
OVERRIDES = ROOT / 'data-extraction' / 'ostali_overrides.json'
# what an override may not set: the entry's text stays as printed and a role is a decision (both also decide whether a
# man goes to a unit, move_to_units), and the fields this script keeps for itself
OVERRIDE_REFUSED = {'soldier_id', 'additional_info', 'role', 'other_sources', 'from_columns', 'manual_fields',
                    'former_ids', 'full_name'}
CENSUS = 'zrtve-rata-1964'                                  # the census's volumes: zrtve-rata-1964-<vol>
# names a parser read wrong, by entry: the Zbornik's headings "DEMONJ A (NIKOLA)", "RAKOVAC J (OAKIM)" and one whose
# OCR took a line of the text for the name (Pal Šoti, born 19 January 1916 in Bečej, as Narodni heroji 1982 has him)
NAME_FIXES = {'9061000128': ('Albahari', 'Nisim', 'Abrahama'),   # Romano's "Avrama": the hero books' Abraham
              '9035011823': ('Jelovac', 'Milan', 'Vučetin'), '9035011826': ('Jelovac', 'Strainj', 'Vučetin'),  # "Vučegin"
              '9001000203': ('Demonja', 'Nikola', ''), '9001000908': ('Rakovac', 'Joakim', ''),
              '9001001039': ('Šoti', 'Pal', 'Pala'),
              '9093000448': ('Peratić', 'Milan', 'Ilije'),     # Sokolac's "Tterat-Tlć", П read as Tt
              '9005001062': ('Šuća', 'Miloš', 'Pere'),         # Hronika's "Ttuća" of Bojna, Glina, Ш read as Tt
              '9035015149': ('Migrović', 'Arso', 'Petrov'),   # the Spomenica prints "Ми гровић Петров Арсо" (Podgorica 128)
              # Bijelo Polje's "Borović" (749-752): Ćorović, as the Spomenica and the census print them (a reader, 2026-11-22);
              # 752's "Šahinj" given as the Spomenica prints him, so the two entries meet (the text keeps "Šahinj")
              '9095002749': ('Ćorović', 'Zaim', 'Alja'), '9095002750': ('Ćorović', 'Maho', 'Hamida'),
              '9095002751': ('Ćorović', 'Osmo', 'Džema'), '9095002752': ('Ćorović', 'Šahim', 'Šeća'),
              '9035002206': ('Bulatović', 'Milena', 'Ristova'),   # the Spomenica's "Risgova", т read as г
              # readers' reports of 2026-11-22: the census's "Erov" and "Gror" of Klokoč and Svinica are Erors (the
              # Krstinja lists print them so), its Zemelj of Dinoša the Spomenica's Kajošević Zejnel, its Jemović the
              # same census volume's Jemuović printed twice; given as the entry they join, so the two meet
              '9021052126': ('Eror', 'Miloš', 'Laze'), '9021052903': ('Eror', 'Adam', 'Damjana'),
              '9023006250': ('Kajošević', 'Zejnel', 'Zekin'), '9025027497': ('Jemuović', 'Dušan', 'Pavle')}
NO_NICK = {'9035015149'}      # entries whose parser read a given name as a nickname
# given names an OCR slip spoiled (one letter added, lost or swapped); the entry's text keeps them as printed
GIVEN_FIXES = {'9010000849': 'Milan', '9013000684': 'Mihailo', '9010000551': 'Milorad', '9013002857': 'Velimir',
               '9009000207': 'Velimir', '9010000622': 'Petar', '9007000140': 'Nikola', '9005001914': 'Miodrag',
               '9010000363': 'Dmitar', '9038001274': 'Đorđe',
               '9095002088': 'Rifat',       # Bijelo Polje's "Rifattršo": the narodni heroj Rifat Burdžović Tršo
               '9016001012': 'Dušan'}       # Čačak's "Dutttač", Ш read as ttt
# books that print the father in the nominative, as the census does: his name goes to fathers_name, not middle_name
NOMINATIVE_FATHERS = {'tuzla-spomen-knjiga', 'ostrvica',      # (Ostrvica's census names the head, the father)
                      'lezimir',                            # (Ležimir's list: "Babić (Radovan) Petar")
                      'porodicna-arhiva',                   # (a family's papers: the father as they name him)
                      'poruke-posetilaca', 'vikipedija'}    # (a visitor's message, a Wikipedia article: likewise)
# books that print him as a possessive ("Mitrov", "Jovanova"): fathers_name is the nominative the site's names know
POSSESSIVE_FATHERS = {'trebinjci-pali', 'spomenica-crnogorskim-antifasistima',
                      'revolucionarno-grahovo', 'bozice',       # (Grahovo's "Mićunov", Božiće's "Desa Veljova")
                      'popovo-polje',                           # (Popovo polje's "Akšam Ilija, Burin")
                      'grahovo-podjele',                        # (Grahovo's rear workers, "Bulajić Simov Mirko")
                      'ljesnjani',                              # (Lješnjani's "Blagojević Tomov Andrija")
                      'grahovski-kovacevici',                   # (Grahovo's Kovačevići, "Andrija Gajov")
                      'vilusi'}                                 # (Vilusi's "Babić Stevana Vidak", "Bulajić Kostov Blagota")
# books used only as references for men who have a unit record: their unmatched entries make no records; taking a book
# out of this set adds its unmatched men to Ostali borci (the Spomenica crnogorskim antifašistima was here until the
# user decided, on 2026-10-14, that every man it names counts as a partisan)
REFERENCE_ONLY: set = set()
# books printed as a table of columns, whose columns are the record's fields (as the census's are); every man of the
# Spomenica counts as a partisan who fell (the user's decision), so his death is "poginuo"; and lists of the fallen
# whose entries give only the years ("1905/44" in the Cazin region's, "1920-1942" in Iskra in plamen's) or a name, a
# birth year and a village under the battle they fell in (Ludbreg's)
COLUMN_BOOKS = {'spomenica-crnogorskim-antifasistima', 'cazinska-krajina-pali-borci', 'iskra-in-plamen-padli',
                'ludbreg-poginuli', 'xxxi-divizija-stabi', '15-brigada-stabi',   # (those two: the officers who fell)
                'licko-petrovo-selo',                  # (Ličko Petrovo Selo's table of the fallen)
                'niksicki-odred-pali-borci',   # the Nikšić region's fallen: a table of birthplace and year, death place and year
                'brod-crna-trava',             # Brod's table of the fallen: mahala, day and place of death, unit
                'knezica',                     # Knežica's fallen: "1926–1942. Kozara" (its survivors get no death)
                # Crna Trava's fallen by village: "Apostolović M. Denča 1944. Predejane", who killed him, where, his
                # unit, and no verb, so the field reader read no death (2026-11-22, the user: "fill in Crna Trava's
                # deaths"); only that list (COLUMN_LISTS)
                'crna-trava'}
# a book of which one list only is a table: its other lists' entries are read as text (Crna Trava's heroes, whose
# paragraphs give the birth and the death in words: "rođen 1924. u selu Mačkatici")
COLUMN_LISTS = {'crna-trava': 'Oni koji su u naše danas i sutra ugradili svoje živote'}


def is_column(book: str, e: dict) -> bool:
    """An entry whose book is printed as a table of columns (COLUMN_BOOKS), in the list that is one (COLUMN_LISTS)"""
    return book in COLUMN_BOOKS and (book not in COLUMN_LISTS or e.get('list') == COLUMN_LISTS[book])
# books that print one man in more than one of their chapters: the Spomenica lists the dead by municipality, and a man
# born in one and living or killed in another can stand in two or three ("Ivović Momčilo" under Bar, Pljevlja and
# Podgorica); its entries of one name are one man when they agree as printed_twice says. The census prints a man twice
# too, now and then (often side by side, the father once in the genitive: "Kasalica (Boja) Radoš" and "(Bojo) Radoš",
# 1921, Komarnica, fell 1943 at Kolašin), but two of its entries of one name and village are as often two cousins, so
# it has a stricter rule of its own (census_twice)
PRINTS_TWICE = {'spomenica-crnogorskim-antifasistima'}


# entries of men the deserters' rule takes off the site (the user's of 2026-10-14: one who went over to the enemy or
# was shot as a deserter or traitor), whose unit record was deleted: no record of their own here either
LEFT_OUT = {
    '9019000982',   # Vukas Pere Đuro of Močila, "Strijeljan kao dezerter kod Močila 11. 4. 1945." (0060002337, 2026-10-30)
}


def infant(e: dict) -> bool:
    """A child the Spomenica names who was born in the war's last years: killed in the massacres of 1943 at a year or
    two, no fighter (the user's decision of 2026-10-28: the older children stay, since children fought); another
    book that names the same child still makes his record"""
    year = str(e.get('birth_year') or '')
    return e.get('_book') == 'spomenica-crnogorskim-antifasistima' and year.isdigit() and 1942 <= int(year) <= 1945
# names the rules below can't read
SCANNED = {'Sal.ih': 'Salih', 'Ves.elin': 'Veselin', 'Mi.nša': 'Minša', 'Mi.nžac': 'Minžac', 'Vl.jko': 'Veljko', 'Mil.apov': 'Miljanov',
           'Minjanov': 'Miljanov', 'Lli.jin': 'Ilijin', 'Ve.vov': 'Vešov', 'Ve.vović': 'Vešović', '.Njuba': 'Ljuba', '.Tandre': 'Jandre', 'Mi.jo': 'Mijo',
           "Teol'ilovski": 'Teofilovski', "Kornelij'a": 'Kornelija', 'Al»ova': 'Aljova', 'S.-': 'S.', 'Lipice—glibodol': ''}
# Đ a scan read as D, in names that have no D (the census and the rosters: "Duro", "Dure", "Dorđe", "Doka"); Duka, Dujo, Duran
# and Durak are names as they stand, Dukić and Dokić surnames
LOST_STROKE = {'Duro': 'Đuro', 'Dura': 'Đura', 'Dure': 'Đure', 'Dorđe': 'Đorđe', 'Dorde': 'Đorđe', 'Dordje': 'Đorđe', 'Doka': 'Đoka',
               'Doke': 'Đoke', 'Doko': 'Đoko', 'Durđa': 'Đurđa', 'Durda': 'Đurđa', 'Durađ': 'Đurađ', 'Durad': 'Đurađ', 'Dukan': 'Đukan',
               'Dukana': 'Đukana', 'Dokana': 'Đokana', 'Dorđija': 'Đorđija', 'Dorđije': 'Đorđije'}
LOST_STROKE_SURNAME = {'Durić': 'Đurić', 'Durković': 'Đurković', 'Durović': 'Đurović', 'Durđević': 'Đurđević', 'Dordevič': 'Đorđević',
                       'Dordevic': 'Đorđević', 'Dordević': 'Đorđević', 'Durdevič': 'Đurđević', 'Durašinovič': 'Đurašinović', 'Duraš': 'Đuraš',
                       'Dordić': 'Đorđić', 'Durdov': 'Đurđov', 'Durković-Andrić': 'Đurković-Andrić'}
DURIC_MUSLIM = {'Latif', 'Muhamed', 'Šerif', 'Ekrem', 'Pašo'}          # Durić is their own name


def scanned_names(e: dict) -> None:
    """The scans' marks in a name (2026-11-03): the Spomenica's Љ and Њ read as "l»", "l," or "l.", "n.", "L»ubo" Ljubo,
    "Vel,ko" Veljko, "Drl.ević" Drljević, "Buban.a" Bubanja; the census's footnote digit after a given name, "Milan1",
    "Ivan+"; its comma in "M,irko"; a dash in two surnames ("Popović—Mitić"), or before or after a name ("Velimir-",
    "-Mijušković"); a quote before one ("'Gerzić"); a surname's Ć read as t ("Bulatovit"); the lost stroke of Đ. The
    entry's text keeps them."""
    changed = False
    for k in ('last_name', 'first_name', 'fathers_name'):
        v = e.get(k) or ''
        new = SCANNED.get(v, v)
        new = re.sub(r'(?<=[a-zčćžšđ])l[,».](?=[a-zčćžšđ])', 'lj', new)
        new = re.sub(r'(?<=[a-zčćžšđ])n\.(?=[a-zčćžšđ])', 'nj', new)
        new = re.sub(r'^L[,»](?=[a-zčćžšđ])', 'Lj', new)
        new = re.sub(r'(?<=[a-zčćžšđ])[\d+]+$', '', new)
        new = re.sub(r'^([A-ZČĆŽŠĐ]),(?=[a-zčćžšđ])', r'\1', new)
        new = re.sub(r'(?<=[a-zčćžšđ])\s*[—–]\s*(?=[A-ZČĆŽŠĐ])', '-', new)
        new = re.sub(r"^['’\s]*[-—–'’]\s*(?=\w)", '', new)
        new = re.sub(r"(?<=[a-zčćžšđ])\s*[-—–]+$", '', new)
        new = re.sub(r'\s*[(?]\s*$', '', new)                               # "Vida (", "Peleš ?"
        if k == 'fathers_name' and re.match(r'^(?:R|Rođ)\.', new):        # the census's maiden name in the father's bracket: "Rođ.šisul", "R.cuculić"
            new = ''
        new = re.sub(r'(?<=[a-zčćžšđ])\.(?=[a-zčćžšđ]{3})', '-', new) if k == 'last_name' else new      # "Martinko.kramar"
        if '-' in new and k == 'last_name':
            new = '-'.join(p[:1].upper() + p[1:] for p in new.split('-'))
        if new[:1].islower() and new[1:2].islower() and v[:1] in "'’":
            new = new.capitalize()
        if k == 'last_name':
            new = re.sub(r'(?<=[a-zčćžšđ]ov)it$', 'ić', new)
            if not (new == 'Durić' and (e.get('first_name') or '') in DURIC_MUSLIM):
                new = LOST_STROKE_SURNAME.get(new, new)
        else:
            new = LOST_STROKE.get(new, new)
        if new != v:
            e[k] = new
            changed = True
    if changed:
        e['name'] = ' '.join(x for x in (e.get('last_name'), e.get('fathers_name'), e.get('first_name')) if x)


def born_year(e: dict, year) -> str:
    """The year of birth the lead entry gives, where someone of this war can have it: the Spomenica's old people and
    children stay (1853, 1938), the scans' "Rođen je 1997" and "1814" are none, and the normalizer then reads the text
    and the man's other entries (2026-11-03)"""
    y = year(e, 'birth_year')
    return str(y) if y and 1850 <= int(y) <= 1941 else ''


# entries checked by hand to be one man, where an OCR slip in the father hides it from same_man, or where the Spomenica
# prints him in two chapters with two villages
ONE_MAN = [
    ('9060000001', '9035011183', 'Adilović Hilmo, Kovačevići 1918, fell 1943; the Spomenica\'s "Recov" is Redžov'),
    ('9060000096', '9035011488', 'Gerina Muharem, Šumani 1928, fell 1943; the Spomenica\'s "Radišin" is Rašidov'),
    ('9060000387', '9035012663', 'Popović Gruban, Kakmuži 1927 (the Spomenica\'s "Kukmuži"); "Neđelžov" is Neđeljkov'),
    ('9060000432', '9035012899', 'Soković Živan, Bobovo 1911; the father Jovo to Prilog u krvi, Jovan to the Spomenica'),
    ('9060000475', '9035013044', 'Tomašević Novica, Mataruge 1915, fell 1944; the Spomenica\'s "Ć." is Đ. (Đerosim)'),
    ('9035007827', '9035012049', 'Kontić Radoje, Andrija\'s son, fell 1943: the Spomenica\'s chapters of Nikšić '
                                 '(Pješivci, 1920) and Pljevlja (Tikava, 1919), as his brother Radoš'),
    ('9035007830', '9035012050', 'Kontić Radoš, Andrija\'s son, fell 1943: Nikšić (Pješivci, 1922) and Pljevlja '
                                 '(Tikava, 1921)'),
    ('9035017001', '9035012349', 'Maričević Radmila, born in Prijepolje 1900 or 1901, fell at the Sutjeska 1943: the '
                                 'chapters of Šavnik ("N.") and Pljevlja ("D.", Prilog u krvi\'s Danila)'),
    # the Spomenica's men under two municipalities born a year apart, whose villages and places of death differ but
    # lie together (the Šavnik chapter gives the town for the village)
    ('9035008310', '9035014511', 'Nikolić Radivoje, Nikola\'s son, fell 1944 in Bosnia: Nikšić (Broćanac, 1907, '
                                 '"Bosna") and Podgorica (Rubež by Nikšić, 1908, Busovačka stijena)'),
    ('9035008022', '9035017034', 'Marković Savo, Rade\'s son, fell 1944: Nikšić (Bubrežak, 1887, Danilovgrad) and '
                                 'Šavnik (Nikšić, 1888, Pješivci by Danilovgrad)'),
    ('9035008463', '9035017386', 'Perović Danilo, Petar\'s son ("Pegrov"), fell 1943: Nikšić (Rudine, 1918, Trubjela) '
                                 'and Šavnik (Nikšić, 1919, Nikšić)'),
    ('9035001203', '9035003363', 'Raičević Dušan, Niko\'s son, fell 1942 by Petrovac: Bar (Bukovik, 1912, Petrovac) '
                                 'and Budva (Buljarica, 1913, Novoselje)'),
    ('9035002709', '9035006704', 'Medojević Vlastimir, "B.", fell 1944: Bijelo Polje (Prošćenje, 1927) and Mojkovac '
                                 '(Stevanovac, 1926, Trnovica)'),
    # the Slovene staff lists name an officer and what he was called, nothing more
    ('9072000059', '9075000001', 'Jernejc Franc-Milče, the Prešernova\'s and Vojkova\'s officer to August 1944, then '
                                 'the Jeseniško-bohinjski odred\'s commander from 30 August 1944'),
    ('9072000005', '9002000690', 'Matejka Evgen-Pemc, the XXXI. divizija\'s commander who fell at the Soča in May '
                                 '1945, and the narodni heroj of the 1982 book'),
    ('9074000011', '9002000519', 'Kolman Alojz-Marok, the 15. divizija\'s deputy commander in 1943, and the narodni '
                                 'heroj'),
    ('9001000469', '9002000519', 'Kolman Alojz-Marok in the two hero books: born 1 July in Zabukovje, proclaimed '
                                 '20 December (1911 and 1951 against 1913 and 1952)'),
    ('9070000013', '9061004420', 'Volner Zdenko-Sanjo of Virovitica, a spomenica holder, and the Jewish student of '
                                 'Virovitica in the NOV from 1941 (born 1922 and 1921)'),
    ('9070000003', '9002000320', 'Fiket Mirko-Mesarić, proclaimed a narodni heroj on 24 July 1953 in both books'),
    # the chronicles of Medak and of Prigrevica are one book here, and Prigrevica's settlers came from these villages
    ('9005001963', '9005001987', 'Zaklan M. Milan of Mogorić, delegat voda of the 6. divizija, fell in Mogorić in 1943'),
    ('9005000654', '9005001998', 'Njegomir Dane Jovan of Zavođe, born 1914, a spomenica holder in both chronicles'),
    ('9005002010', '9005000996', 'Radaković Milanka Janko of Mogorić, born 1920, in both chronicles'),
    ('9005002014', '9005001202', 'Maljković Mile Miloš of Mogorić, a spomenica holder in both chronicles'),
    ('9005000343', '9005001992', 'Radaković Đuro of Mogorić, Paje or Pavla, fell at Korenica in 1942'),
    ('9019000641', '9105000315', 'Sekulić Miloš, son of Mane, of Zbjeg, born 1916, commissar of a battalion, fell at Žumberak '
                                 'in 1944: the Slunj-Veljun book and the 1964 census print Mane as the father, the Primišlje '
                                 'list "Miloša Mane" turns it round'),
    ('9035001457', '9035002190', 'Bubanja Miljanov Milonja of Bubanje, born 1912, fell at Kolašin: under Berane and under Bijelo Polje, the scan reading "Minjanov"'),
    # one man until the Spomenica's surnames were read by its alphabetical order (2026-11-03): the census's text has
    # him as Usović, as the Spomenica's scan had, and the record kept only the census's father, from an entry it no
    # longer held
    ('9035005111', '9023007234', 'Ćosović Veljko of Vrela (Žabljak), son of Đorđije ("Đ."), born 1907, fell 1944: '
                                 'the census\'s "Usović"'),
    # Anica-Anđa, Vučić's daughter, of Podbišće by Polja, born 1922, fell at Javorje in Gornja Morača in 1944, a youth
    # leader of the 7. crnogorska omladinska brigada: the Kolašin book and the Spomenica's chapters of Kolašin ("V.",
    # Polja, G. Morača) and Mojkovac (no father, Podbišće, Javorje); one record until 2026-11-03
    ('9090000524', '9035005457', 'Đurašinović Vučića Anica of Podbišće, born 1922, fell 1944 in Gornja Morača: the '
                                 'Kolašin book and the Spomenica\'s Kolašin chapter ("V.")'),
    ('9035005457', '9035006621', 'Đurašinović Anica, born 1922, fell 1944: the Spomenica\'s Kolašin (Polja, G. Morača) '
                                 'and Mojkovac (Podbišće, Javorje) chapters'),
    # his Wikipedia article, which a visitor pointed us to, on a man whose record 122 holds
    ('9991000004', '9001000086', 'Bogavac Vukašina Dragoslav of Veliđe (Berane), born 1910, the narodni heroj who fell '
                                 'at Vrbnica in the spring of 1942 (F. Adžić, 2026-11-20)'),
    ('9111000275', '9001000532', 'Kupres Marka Miloš of Kožuhe (Doboj), the narodni heroj who fell at Turija in January '
                                 '1942: Kožuhe\'s list of the fallen (born 1907) and the hero book (born 1920); found by '
                                 'the email session on 2026-11-21, the records stood side by side'),
    # a reader's reports of 2026-11-22: Bijelo Polje's "Borović" of Lozna and Ivanje is Ćorović, as the Spomenica
    # (Bijelo Polje 929-932) and the census print them; the surname in NAME_FIXES, the pairs here
    ('9095002749', '9035003058', 'Ćorović Aljov Zaim of Lozna, born 1919, fell 1945 at Pale near Sarajevo'),
    ('9095002750', '9035003059', 'Ćorović Hamidov Maho of Lozna, born 1919, fell 1945 at Jabuka near Goražde'),
    ('9095002751', '9035003060', 'Ćorović Džemov Osmo of Ivanje, born 1925, fell 1944 at Obrovo'),
    ('9095002752', '9035003061', 'Ćorović Šećov Šahim of Lozna, born 1915, died 1945 near Sjenica (Bijelo Polje '
                                 'reads Šahinj)'),
    # the Spomenica's "Risgova" (Bijelo Polje 76, the scan's т read as г) is Ristova: Bijelo Polje's 71, her father
    # Risto (a reader's report of 2026-11-22)
    ('9095002071', '9035002206', 'Bulatović Rista Milena of Štitari, born 1905, a political worker, fell 1944 at Lozna'),
    # Crna Trava's list of the fallen (2026-11-22): its Nikolić B. Tihomir of Bistrica, killed at Niš in 1945 in the 12.
    # brigade, is the census's Nikolić (Božil) Tihomir of Kozilo (Crna Trava), dead in 1944 in the military hospital of
    # Niš; each lists one Tihomir Nikolić of Crna Trava (the rules had joined Crna Trava's to an Obrenovac man)
    ('9125001262', '9025009722', 'Nikolić Božila Tihomir of Crna Trava, died at Niš in 1944 or 1945'),
    # readers' reports and a family's form of 2026-11-22 (05; cases in the ops repo)
    ('9018000466', '9021052126', 'Eror Laze Miloš of Klokoč, born 1909, died of typhus in 1943 (the census: Erov)'),
    ('9018000686', '9021052903', 'Eror Damjana Adam of Svinica, born 1911, fell 1943 in Montenegro (the census: Gror)'),
    ('9035014161', '9023006250', 'Kajošević Zekin Zejnel of Dinoši, fell 1944 there (the census: Zeko Zemelj, b. 1915)'),
    ('9025027497', '9025027498', 'Jemuović Pavla Dušan of Baljevac, fell 1941 at Raška: the census prints him twice'),
    ('9064010613', '9990000012', 'Orlić Marka Đuro of Vodoteč, b. 1922: his great-grandson\'s form (spomenica, d. 1982)'),
    # forms of 2026-11-23: the Spomenica's (under Šavnik) and the Lovćenski odred's list's Čelebić Ilijin Jovan of Štitari
    # (Cetinje), b. 1921, fell 1. 12. 1941 at Pljevlja: one man (his nephew's form and a report of his village)
    ('9035017817', '9084000711', 'Čelebić Ilije Jovan of Štitari (Cetinje), b. 1921, fell 1. 12. 1941 at Pljevlja'),
    ('9084000716', '9990000022', "Čelebić Ilije Novak of Štitari: his nephew's form (wounded at Cres 1945, died 1946 in Zagreb)"),
    # form of 2026-11-24 10:04: Petrenj Stevan Mara of Bosut (census Vojvodina) of the 3. vojvođanska, her grave at Mala Moštanica;
    # joined so that the family's unit takes her there (the user's rule, the lead's word of 2026-11-24)
    ('9027007909', '9990000060', 'Petrenj Stevana Mara of Bosut, b. 1924, fell 1944 (Mala Moštanica): her family names the 3. vojvođanska'),
    # form of 2026-11-24 11:36: Lekić Muratov Mahmut of Tuzi, the Spomenica's (Podgorica), fell 1944 at Crkvine near Kolašin (Mateševo)
    ('9035014250', '9990000061', 'Lekić Muratov Mahmut of Tuzi, b. 1917, fell 1944: his relative names the 5. proleterska crnogorska'),
    # forms of 2026-11-24 evening: Mrkonjić Ilija's grandson; the Stipeč brothers' niece (the Spomenica, the census's "Stipeć")
    ('9018000893', '9990000075', 'Mrkonjić Jovana Ilija of Gaćeša Selo, killed by accident 10. 4. 1942 near Plaški'),
    ('9021003534', '9990000076', 'Stipeč Ljudevita Ivan of Bribir, b. 1924, fell 1942 (Otočac): his niece (the Spomenica)'),
    ('9021003535', '9990000077', 'Stipeč Ljudevita Mihovil of Bribir, b. 1925, fell 1943 (Drežnica): his niece (the Spomenica)'),
    # forms of 2026-11-26 evening, S. Brozović (05): his aunt Brozović Jurja Katica of the Selce list is the census's
    # Katarina ("Pravo ime Katarina, nalazi se pod tim imenom u spisku"; b. 1925, Selce, killed there 4. 1. 1944); his
    # uncle Volf Antun Bogdan of Tršće (census Croatia) held the Spomenica, by his family's entry
    ('9052000013', '9021003892', 'Brozović Jurja Katarina of Selce, b. 1925, killed 4. 1. 1944 at Selce: her nephew\'s form'),
    ('9021002962', '9990000113', 'Volf Antuna Bogdan of Tršće, b. 1917, fell 1941: his nephew\'s form (the Spomenica)'),
]
ONE_MAN_PAIRS = {frozenset(p[:2]) for p in ONE_MAN}
# the IDs two records of 122 had before ONE_MAN joined them: the one that went still opens the man's card (old 122 ID
# -> the record's, written into moved-ids.json with the men moved to a unit), since links to it may be out
MERGED_IDS = {
    '0122010532': '0122957805',   # Kupres Marka Miloš: the hero book's record, joined to Kožuhe's (2026-11-21)
    # Bijelo Polje's records, joined to the Spomenica's (2026-11-22): the four Ćorović of Lozna and Ivanje, Bulatović Milena
    # readers' reports of 2026-11-22: U rovovima Srema's "Erar Jovo" is the 1. krajiška's Eror Jeke Jovo (a reference);
    # the census's Jemuović printed twice
    '0122130469': '0123000355', '0136027498': '0136027497',
    '0122926735': '0122940691',   # Čelebić Ilijin Jovan: the Spomenica's record, joined to the Lovćenski odred's list's (2026-11-23)
    # records the units held until unit_named's fix of 2026-11-23 found them naming two units on the site: back in 122, their
    # unit addresses open the record (Janjić Miladinov Božidar, Dizdarević Fehrat, Šuković Venjko; Levi Moric stayed in the 4. krajiška)
    '0069900001': '0122954956',   # (0039900251 and 0042900015 went back into their units: their entries dropped, 2026-11-25)
    # back in 122 (2026-11-24): a street named after a brigade, a relative's unit (unit_named 1a019796, d2d4b015)
    '0042900188': '0122909100', '0042900189': '0122909101', '0029900027': '0122909264',
    '0122961381': '0008002961',   # Vučković Frane Nikola: his family's record, joined to the 4. splitska's Nikola of Brnaze (the user, 2026-11-23)
    '0122954911': '0122913485', '0122954912': '0122913486', '0122954913': '0122913487', '0122954914': '0122913488',
    '0122954539': '0122912799',
    # the records the Poreklo books 9115-9128 joined to others (2026-11-22): a book's entry agreed with two records of
    # one man; until then these lived in moved-ids.json alone, and a rebuild dropped them
    '0122030023': '0122916895', '0122941004': '0122916895', '0122941137': '0122917515', '0122941177': '0122917637',
    '0122941542': '0122917225', '0122954028': '0122917150', '0122030136': '0126900001',
    '0122930284': '0122010961',   # Sotirović Velina Mirko: the two hero books' records, joined through Crna Trava's
    '0122010673': '0122930277',   # Milenović Jeftimije Sinadin: the same
    # the records whose man a unit's record holds through a Poreklo book's entry (the builder leaves their entries out,
    # scripts/attach_left_out.py gives them to that record): his record there, each read against it (2026-11-22)
    '0122924812': '0102000010',   # Bijelić Lukin Petar (1. bokeljska)
    '0122941037': '0117000096', '0122030100': '0117000096', '0122917026': '0117000096',   # dr Bulajić Novice Jovan
    '0122941034': '0040020093',   # Bulajić Božov Vlado (4. proleterska)
    '0122924952': '0102000059',   # Kosić Markov Vojislav (1. bokeljska)
    '0122917636': '0041010159',   # Kovačević Andrijina Bosa (5. proleterska)
    '0122941172': '0041000581',   # Kovačević Spasoja Đorđo (5. proleterska; the 7. crnogorska's 0028000154 too)
    '0122917669': '0125000367',   # Kovačević Petrov Radosav (Mostarski bataljon, its Radoslav)
    '0122917670': '0001005446',   # Kovačević Stevanov Radosav (Prva proleterska, its Radomir "Rašo")
    '0122958866': '0102012633',   # Tomašević Novaka Simo (1. bokeljska; Sutorina's footnote names the Kruševice list)
    '0122941540': '0125000708', '0122917119': '0125000708',   # Vujačić Ilije Simo (Mostarski bataljon)
    '0122941528': '0001013391',   # Vujičić Mila Jakov (Prva proleterska)
    '0122917135': '0041001335',   # Vujičić Ristov Krsto (5. proleterska)
    '0122941526': '0041001338',   # Vujičić Ristov Vaso (5. proleterska)
    # Crna Trava's list read again (2026-11-22): a unit's record holds the man through his entry now (12. srpska,
    # Kostić M. Božilo of the 7. srpska), and two census fighters of other lands stand alone again, since the victims of
    # terror whose records they had joined are out (Bajince's Petrović M. Milorad, Pavličine's Krstić J. Dušan)
    '0122959818': '0085000362', '0122959827': '0090000345', '0122959853': '0090000341',
    '0122959742': '0136023735', '0122959790': '0138003753',
    # Staromajdansko's headings read again (2026-11-22, a reader's report): six holders of the spomenica each joined
    # his entry in the list of 1983, once the village over both was read (Husimovci and Koprivna had been "Movci",
    # Rasavci "Avci"); Dodik Ilije Petar and Štrbac Koste Lazar to their records of the 6. krajiška
    # Radinović Ostoje Đurađ of Koprivna: his 1983 entry and the Spomenica's meet in the Spomenica's record (05's chain, 2026-11-23)
    '0122953273': '0122935348', '0122953272': '0122935348', '0122953564': '0122953284', '0122953570': '0122953101', '0122953571': '0122953107',
    '0122953232': '0013010286', '0122953249': '0013011788',
    # Bulajić Jovana Desanka of the Nikšić list (b. 1925, Viluse), joined to the Spomenica's record of her (b. 1927, Trebinje)
    # through Trebinje's book, once the census's two entries of her (9022033299, 9022033300) were one woman (census_twice,
    # 2026-11-26); joined before redirects_122 read the registry as it was, so by hand
    '0122941038': '0122930327',
    '0132003892': '0122938109',   # Brozović Jurja Katarina: the census's record, joined to the Selce list's (2026-11-26)
}
# entries checked by hand to be two men, where the rules would join them (a hero and an entry that names no father,
# of one name and birth year)
TWO_MEN = [
    ('9085000107', '9001000745', 'Nikolić Živojin-Žoja of Stubline (Obrenovac), killed at Han Pijesak in January 1942, '
                                 'is not the narodni heroj Nikolić Vujice Živojin-Brka of Stol (Babušnica)'),
    ('9085000107', '9002000819', 'the same, against Narodni heroji Jugoslavije\'s entry of Brka'),
    ('9023003762', '9035007769', 'Kovačević Pajov Dušan of Osječenica (Nikšić), born 1923, fell in 1945 (the Spomenica; '
                                 'his nephew wrote the site) is not the census\'s Kovačević (Pajo) Dušan of Brestica '
                                 '(Mojkovac), born 1922, dead of wounds in Zagreb'),
    ('9023003762', '9089000148', 'the same, against Revolucionarno Grahovo\'s entry of the Osječenica man'),
    # Crna Trava's lists give a father's initial, the year and his village; the rules joined them to namesakes of other
    # lands (2026-11-22, each read against the census, which names one man of the name in Crna Trava or none)
    ('9125000003', '9025000942', 'the narodni heroj Pavlović Ratko-Ćićko of Berilje (Prokuplje), fallen at Preslap in '
                                 '1943, is not the census\'s Pavlović (Stanko) Ratko of Trnjane (Aleksinac), killed at '
                                 'Požega in 1944; his census entry is Pavlović (Veljko) Ratko of Berilje'),
    ('9125001016', '9022031803', 'Crna Trava\'s Ivanović S. Dušan, dead at Belgrade in 1944, is not the census\'s Ivanović '
                                 '(Stevan) Dušan of Razboj Župski (Srbac), killed at Banja Luka'),
    ('9125001067', '9025017281', 'Crna Trava\'s Ristić S. Svetozar, killed at Crna Trava in 1944, is not the census\'s '
                                 'Ristić (Stojan) Svetozar of Buvce (Lebane), killed at Leskovac'),
    ('9125001085', '9080000985', 'Crna Trava\'s Stojanović V. Radomir, killed at Crna Trava in 1945, is not Stojanović '
                                 'Vaska Radomir of Šipačno (Nikšić), killed at Trnovo'),
    ('9125001085', '9023004516', 'the same, against the census\'s entry of the Šipačno man'),
    ('9125001262', '9025023258', 'Crna Trava\'s Nikolić B. Tihomir is not the census\'s Nikolić (Bogosav) Tihomir of '
                                 'Stubline (Obrenovac)'),
    ('9118000087', '9022020829', 'Savić Miloša Savo of Eminovo Selo (Duvno), killed at Travnik in 1944, is not the '
                                 'census\'s Savić (Miloš) Savo of Kosjerovo (Laktaši), killed at Doboj; his census entry is '
                                 'Eminovo Selo\'s'),
]
TWO_MEN_PAIRS = {frozenset(p[:2]) for p in TWO_MEN}


NO_FATHER = re.compile(r'^(?:nema|nepoznat[aoi]?|nn\.?|n\.\s?n\.?)$', re.I)
# the census's column of the place of death often names his unit, no place ("7 banijska divizija", "18 brigada",
# "Prešernova brigada", "Kozjanski odred"): the record's sub-unit, its number written "7. " (2026-10-30), shown on the
# card as "U jedinici"; "Pogrešan od 9.1944" (missing) is neither
UNIT_IN_COLUMN = re.compile(r'(?<![a-zčćžšđ])(?:(?<!Široki )(?<!Široko )(?<!Gornja )(?<!Donja )brig)|\d\s*\.?\s*(?:bri|br\b|br\.|div|ud\b|ud\.|kub|snoub|kr\.|kr\b|peš\.?\s|'
                            r'koz|brod|osječ|istočn|sr\.|kosov|kosmet|terensk|šumad|nikš|maslov|moslov|srbijan|hercreg|ljublj|krašk|roš|pohor|istar|bačin|btig|biragad|'
                            r'č\b|č\.|ć\b|ć\.|ba\.|ivizij|grupa|grupe|sjevero)|\bdiv\b|\bdiv\.|diviz|odred|bataljon|batalj\b|korpus|\bčeta\b|^\d\s*Prol|'
                            # a number and his unit's word, no "brigada" ("6 lička", "2.dalmatinska", "17 majevička"; 2026-11-03)
                            r'^\s*\d+\s*\.?\s*(?:prolet|dalm|lič|kraj|kraišk|majev|moslav|slavon|vojv|vovođ|banij|banin|kordun|udarn|'
                            r'primorsk|hercegov|bosan|crnog|sandž|srps|jugosl|goran|makedon|muslim|omlad|virovit|romanij|južnomor|'
                            r'srednjebos|srednjobos|armij|čet|bat\b|bat\.|batalj)', re.I)
# what the column cut or spelled: its units in one form (2026-11-04)
UNIT_WORDS = [(r'\bbrigad$|\bbriga$|\bbrig\.?$|\bbr\.$|\bbri\.$', 'brigada'), (r'\bdivizij$|\bdivizi$|\bdiviz\.?$|\bdiv\.?$', 'divizija'),
              (r'\bbrig\.\s*', 'brigada '), (r'\bdiviz\.\s*', 'divizija '), (r'\bdalmat\.\s*', 'dalmatinska '), (r'\bdalm\.?\s+', 'dalmatinska '),
              (r'\bvojv(?:o[đd]j?)?\.\s*', 'vojvođanska '), (r'\bprol(?:et)?\.\s*', 'proleterska '), (r'\bherc\.\s*', 'hercegovačka '), (r'\bkraj\.\s*', 'krajiška '),
              (r'\bslav\.?\s+', 'slavonska '), (r'\bsandž\.\s*', 'sandžačka '), (r'\b[Mm]aslovačk', 'moslavačk'), (r'\b[Mm]oslovačk', 'moslavačk'), (r'\bkraišk', 'krajišk'),
              (r'\bkrajšk', 'krajišk'), (r'\b[Mm]ajevačk', 'majevičk'), (r'\bCankarev|\bCankarj\b', 'Cankarjev'), (r'\bTomšićev|\bTompićev', 'Tomšičev'), (r'\bTomš\.\s*', 'Tomšičeva '),
              (r'\bPreš\.', 'Prešernova'), (r'\bPrešernev', 'Prešernov'), (r'\bGupčev', 'Gubčev'), (r'\bPetefijev', 'Petefi'), (r'\b[Pp]roleter\b', 'proleterska'),
              (r'\bProleterska\b', 'proleterska'), (r'\bbraće radića?\b|\bbraća radić\b', 'Braća Radić'), (r'\bm\.\s?gupca\b|\bmatije gupca\b|\bmatije gubca\b|\bm\.\s?gubca\b|\bmatija gube\b', 'Matija Gubec'),
              (r'\bivan cankar\b', 'Ivan Cankar'), (r'\bt\.\s?tomšičrva\b', 'Tomšičeva')]


def unit_form(v: str) -> str:
    for rx, to in UNIT_WORDS:
        v = re.sub(rx, to, v)
    return re.sub(r'\s+', ' ', v).strip(' ,+')

MISSING_COLUMN = re.compile(r'^pogrešan\b', re.I)


def place_or_unit(place: str) -> dict:
    """The column of the place of death as the record's death_place, or its unit as unit_detail"""
    if MISSING_COLUMN.match(place):
        return {}
    if UNIT_IN_COLUMN.search(place):
        unit = re.sub(r'(\d+)\s*\.?\s*(?=[^\W\d_])', r'\1. ', place.strip())     # "7 banijska", "13.divizija"
        return {'unit_detail': unit_form(re.sub(r'\s*,\s*', ', ', unit))}
    return {'death_place': death_column(place)}


# a book whose born_in is the area of the list, not the man's
BORN_IN_NOT_HIS = {'moste-polje-spomenica-1941'}

# Places of death read by hand where the reader's reading of his own entry is a misreading no rule tells (2026-11-20,
# the 933 places the map can't place read beside the census's, at 00-TEAM LEAD's request): record -> the place his
# entry names, or '' where the census's place stands (the same place garbled: "kod Njubovije", "u Hraliji"; or no place:
# a man's name, "u Markosovim partizanima", "na putu za Dalmaciju"). His entry stays as printed.
DEATH_PLACE_READS = {
    # Sotirović Velina Mirko, the narodni heroj: Crna Trava's list prints "Duga Luka", the census "Duga l., V. Banja"
    # (2026-11-22, when his census entry joined his record)
    '0122010961': 'Duga Luka',
    # the census's place: his entry names it garbled, or names no place
    '0122925609': '', '0122926849': '', '0122916381': '', '0122927195': '', '0122010645': '', '0122915799': '',
    '0122927049': '', '0122930320': '', '0122906239': '', '0122906338': '', '0122925180': '', '0122940823': '',
    '0122915852': '', '0122924710': '', '0122927166': '', '0122050903': '', '0122010392': '', '0122909197': '',
    '0122915941': '', '0122926314': '', '0122908690': '', '0122932906': '', '0122924592': '', '0122908379': '',
    '0122925325': '', '0122909592': '', '0122923439': '', '0122943346': '', '0122080817': '', '0122911643': '',
    '0122905597': '', '0122926176': '', '0122926900': '', '0122925147': '', '0122906298': '', '0122913038': '',
    '0122011077': '', '0122110224': '',
    '0122916882': '', '0122925112': '',            # Nikšić's fallen's "Anrijevica", its "Lika" against two books' Gorski kotar
    # the place his entry names, read by hand
    '0122924953': 'Meljine',                        # Kruševice's "umire u vojnoj bolnici Meljine" (Herceg Novi's fallen: Kotor)
    '0122090222': 'Valjevo',                        # "Vaijevo"
    '0122926148': 'Zagarač', '0122916270': 'Zagarač', '0122926515': 'Zagarač',     # "u Zagarču"
    '0122915769': 'Sinjajevina',                    # "na Sinjavini"
    '0122927223': 'Gradačac',                       # "kod Gradačpa u Bosni"
    '0122932864': 'Štrpci, Prnjavor',               # "u Štrpcima Prnj"
    '0122925363': 'Zabjelo, Podgorica',             # "na Zabjelu kod Podgovice"
    '0122917119': 'Dramiševo, Nevesinje',           # "u selu Dramiševo kod Nevesnnja"
    '0122911535': 'Sozina',                         # "na Soziki"
    '0122100457': 'Žegar',                          # "u Zsgaru"
    '0122100634': 'na Bukovom vrhu kod Gračaca',    # "vrbu"
    '0122925206': 'Piperi', '0122912005': 'Piperi', # "u Pilerima", "u Šiperima"
    '0122924623': 'Bogdašići',                      # "kod Bog dašića"
    '0122940654': 'Danilovgrad',                    # "kod Danilovgra"
    '0122958471': 'Obrade',                         # "u Obradama prtiv Nemaca"
    '0122935413': 'Han Kola',                       # "kod Han Kola. borac"
    '0122956101': 'Japaga, Han Pijesak',            # "u Japagi kod Hai Pijeska"
    '0122932983': 'Pitomača',                       # "u Pitomači Slav"
    '0122914312': 'kod Trešnjevika',                # "... zadobijenim"
    '0122915797': 'Babska, Šid',                    # "Novak Babska, Šid"
    '0122908944': 'na Jurinim brdima',              # "... kraj sela"
    '0122924963': 'Luštica',                        # "Luštici"
    '0122959211': 'Srpska Crnica',                  # "kod Srpske Criice u Bosni"
    '0122940904': 'Nikšić',                         # "u Nikšiću zadobijenim"
    '0122939280': 'Ljubovija',                      # "JBubovija"
    '0122927190': 'Goražde',                        # "kod Goražda u Boga–Jiz"
    '0122910548': 'Grubišno Polje',                 # "na Grubišnom poiiu kraj Bilogore"
    '0122905925': 'Komletinci',                     # "u Komletincima na oremskom frontu"
    '0122905814': 'Otok',                           # "Otokoc na oremskom frontu"
    '0122906421': 'Bratunac',                       # "kod Bratunca u Bosni maota"
    '0122090855': 'Rastičevo',                      # "kod Rasti čeva"
    '0122956010': 'Romanija, Sokolac',              # "u Romaniji – Sokolac y borbi"
    '0122050794': 'Gospić',                         # "u Gospiđu"
    '0122070109': 'Papuča',                         # "u Papuči i tamo je"
    '0122905514': 'Užice',                          # "Užipu"
    '0122925645': 'Trešnjevo, Cuce',                # "na Trešnje vu u Cucama"
    '0122939981': 'Bugojno',                        # "kod Bupojna"
    '0122906219': 'Nemci',                          # "u selu Nemcima na sremskom frontu janzgara"
    '0122926793': 'Meterizi, Rijeka Crnojevića',    # "na Metprizima kod Rijeks Crnojevića"
    '0122906048': 'Đakovo',                         # "kod Ćakova u Slavoniji"
    '0122910739': 'Nožice, Slovenija',              # "... borac u srijemskim jedinicama"
    '0122910552': 'kraj Trsta',                     # "... u završnim borbama za oslobođenje Istre"
    '0122909196': 'Babina Greda',                   # "... kod Slavinskog Broda, Republika Hrvatska"
    '0122958446': 'u Sitnicama na albanskoj granici',   # "alabanskoj"
    '0122070032': 'Sutjeska',                       # "Stujeska"
    '0122958573': 'Bojovića gumno',                 # "na Bojovića gumnu (zajedno)"
    '0122916162': 'Grbalj',                         # "u Grblju u saobraćajnoj nesreći"
    '0122953773': 'Malo Polje',                     # "pri Komandi mjesta Stogulje u Malom Polju"
    '0122030400': 'Mjedenik',                       # "na Borču milicije u selu Mjedeniku"
    '0122070935': 'Srb',                            # "u Srbi"
    '0122070493': 'Bilaj',                          # "pri Komandi mjesta Medak u Bilaju"
    '0122010866': 'Šćepan Polje',                   # "u Sćepan Polju"
    '0122906658': 'Zaselje',                        # "u Zaeelju"
    '0122100540': 'Ilirska Bistrica',               # "u Novoj Kročini kod Ilirske Bistrice"
    # board 67 (2026-11-26, 00-TEAM LEAD): the place the new rules gave, set by hand where it is a phrase or a case form
    '0122917333': 'Ubli, Čevo',                     # Denda Dragov Mirko: "u Ublima Čevskim"
    '0122070132': 'Ranovac, Žabari',                # Vujnović Laze Đuro: "u s. Ranovcu /Žabari/"
    '0122955354': 'Obodnik, Kotor Varoš',           # Novaković Jefto: "Obodnik", the census's "Obadnik kotor v"
    '0122953854': 'Žljebovi, Sokolac',              # Pušonja Save Savo: the municipality the census gives
    '0122955697': 'Bubanj, Niš',                    # Tomić Lazara Nadežda: "Bubnja" is a case form
    '0122947464': 'Podgorje Bistričko',             # Papić Petra Pavao: the census's "Pogorje bistrič" (by Marija Bistrica)
    '0122910081': 'Novoselec, Križ',                # Gašparinčić Stjepana Stjepan: "Novoselec Križ"
    '0122905701': 'Babski Novak, Šid',              # Topalović Miodraga Miloljub: the census's "Babek novac, Šid"
    # ... and where the place the rules gave says less than main's (a municipality dropped, a region for a village)
    # or garbles it: main's place stands
    '0122911489': 'Trnovo, Sarajevo', '0122911957': 'Trnovo, Sarajevo',          # not "Trnovo, Bosna"
    '0122910195': 'Jakopovac, Bilogora',            # not "Bilogora"
    '0122910246': 'Dubrovica, Klan',                # not "Dubravica"
    '0122956157': 'Žljebovi, Sokolac',              # not "Žljebovi"
    '0122910454': 'Krivajci, Maslovare',            # not "Krivaja, Bosna"
    '0122957410': 'Bašel',                          # not "nad Bašljem pod Storžičem"
    # ... and where a full chain on board 67's code gives his entry's phrase, a case form or a garble that main's data
    # never held (the Slovene session's rerun on board 68, 2026-11-26): the place his entries name, in its one form
    '0122030230': 'Turija, Tuzla',                  # Dokić Ivanov Petar: "kod Turije, Tuzla", not "Turje, Tuzla"
    '0122910069': 'Dotršćina, Zagreb',              # Filković Dragutina Stjepan: "u Dotršćini kod Zagreba"
    '0122925875': 'Rokoči, Grahovo',                # Knežević Đura Nikola: "u Rokočima kod Grahova", not "Rokoči"
    '0122911803': 'Bari, Italija',                  # Nikić Jovana Vasilije: "u Bariju u Italiji"
    '0122911807': 'Sozina, Bar',                    # Niklan Ilije Milo: "na Sozini", the Spomenica's "Sozina-Bar"
    '0122959145': '',                               # Nikšić M Mate: the census's "Čoviće-otočac", not "u Čoviću"
    '0122070770': 'Drenovača, Kamensko',            # Novković Mane Dušan: "na Drenovači kod Kamenskog"
    '0122913246': 'Užice',                          # Novović Nikov Jovo: "u Užicama", not the census's "T.užice"
    '0122923870': 'Broćanac',                       # Pejović Lazarev Nikola: "kod Broćanca", the Spomenica's "Braćanac"
    '0122070102': 'Pećane, Udbina',                 # Radaković Đure Dmitar: "u s. Pećani", the census's "Pećani kod udbi"
    #                                                 (the village is Pećane: the census's "Jamani-pećane", 00-TEAM LEAD)
    '0122924036': 'Trnovo, Sarajevo',               # Radulović Joka Savo: "kod Trnova, blizu Sarajeva"
    '0122915951': 'Sajmište, Beograd',              # Simonović Milovana Manojle: "na Sajmištu u Beogradu"
    '0122010963': 'Brajkovac',                      # Spasojević Jevrema Luka: "u Brajkovcu", not "Selo brajkovac"
    '0122926706': 'Gornji Orahovac',                # Tomašević Marka Radovan: "u Gornjem Orahovcu"
}


EXACT_DAY = re.compile(r'1[89]\d\d-\d\d-\d\d')     # a column book's death_date to the day (ISO), as its parser writes it
DEATH_KEYS = ('death_type', 'death_date', 'death_place')
# a word that says how he died, in the entry's text or its list's title ("Poginuli 1941-1945.", "koji su poginuli u
# Ludbregu", "Padel je", "umro", "streljan")
DEATH_WORD = re.compile(r'\b(?:pogin|umr|ubi[jt]|nesta|stre?ljan|strijeljan|obeš|obješ|pao\b|pala\b|zaklan|spaljen|'
                        r'padel|padl|ustrel|ustrijel)', re.I)


def type_stated(e: dict) -> bool:
    """A death type the entry states (a death word in its text, or a type other than poginuo, which the parsers and
    column_fields give where the entry says nothing: Crna Trava's list of the fallen prints no verb), as against a
    default (00-TEAM LEAD's rule of 2026-11-24: a stated type beats a default; the census's "umro" for Nikolić B Tihomir,
    whom Crna Trava's list gives "23. 4. 1945. Četnika Niš")"""
    t = e.get('death_type')
    return bool(t and t != 'poginuo') or bool(DEATH_WORD.search(e.get('additional_info') or ''))


def column_fields(e: dict) -> dict:
    # a list of officers names who fell and who lived (the XXXI. divizija's staffs): no death for one who lived
    if e.get('survived') and not e.get('death_date'):
        return {'birth_place': e['born_in']} if e.get('born_in') else {}
    day = re.fullmatch(r'(\d{4})-(\d\d)-(\d\d)', e.get('death_date') or '')     # the Ludbreg lists give the battle's day
    out = {'birth_place': e.get('born_in') or '', 'death_type': e.get('death_type') or 'poginuo',
           'death_date': f'{int(day[3])}. {int(day[2])}. {day[1]}.' if day else e.get('death_year') or '',
           **place_or_unit(e.get('death_place') or '')}
    return {k: v for k, v in out.items() if v}
SOURCE_FIELDS = ('source_url', 'source_page', 'pdf_file', 'pdf_page', 'pdf_x', 'pdf_y', 'pdf_x_end', 'pdf_y_end',
                 'pdf_x_left', 'pdf_rects')


def books() -> dict[str, list[dict]]:
    out = {}
    for d in ENTRY_DIRS:
        for p in sorted(d.glob('*-entries.json')):
            name = p.name[:-len('-entries.json')]
            if name not in REFERENCE_ONLY:
                out[name] = json.loads(p.read_text(encoding='utf-8'))
    return out


def census_fields(e: dict) -> dict:
    """A census entry's columns as the record's fields: "rođen 1888, Arbnež (Bar). Crnogorac, poginuo 1942. u NOBu, Zec
    Planina" (born_in "Arbnež, Bar", ethnicity, death_year, death_place; "Nepoznato" is no place)"""
    # its wordings: poginuo/poginula (157,000), umro/umrla (10,700, "od bolesti", "od ranjavanja"), ubijen (4,400),
    # nestao, streljan, obešen
    m = re.search(r'\b(poginu|umr|ubijen|nesta|streljan|obešen)', e['additional_info'])
    kind = ({'poginu': 'poginuo', 'umr': 'umro', 'nesta': 'nestao', 'obešen': 'ubijen'}.get(m.group(1), m.group(1))
            if m else 'poginuo')                       # the site's types: poginuo, umro, nestao, streljan, ubijen
    out = {'birth_place': e.get('born_in') or '', 'ethnicity': e.get('ethnicity') or '', 'death_type': kind,
           'death_date': e.get('death_year') or '', **place_or_unit(e.get('death_place') or '')}
    return {k: v for k, v in out.items() if v}


def death_column(place: str) -> str:
    """A census column's place of death without a cause of death written into it: "Beograd-od rana" is Beograd,
    "Kuća-od tifusa" Kuća, "Umro od tifusa" and "Umrla od bolesti" no place"""
    place = re.sub(r'\s*-?\s*\b(?:umr[oal]\w*\s+)?od\s+(?:tifusa|rana|rane|bolesti|posledica|posljedica|ranjavanja|zadob\w*)\b.*$',
                   '', place, flags=re.I)
    return '' if re.fullmatch(r'\s*(?:umr[oal]\w*)?\s*', place, re.I) else fix_place(place.strip(' ,-'))


def year(e: dict, key: str) -> int | None:
    m = re.search(r'1[89]\d\d', str(e.get(key) or ''))
    return int(m.group(0)) if m else None


def places(e: dict) -> set[str]:
    return {stem(w) for w in fold(e.get('born_in') or '').split() if len(w) >= 4} - {'selu', 'opst', 'opsti', 'kotar', 'srez', 'okrug', 'kod'}


def father_of(e: dict) -> str:
    return fold(e.get('fathers_name') or '')


def father_forms(e: dict) -> set[str]:
    """the father as printed and, for a possessive ("Vukadinov", "Mićov"), in the nominative the site's names know, so
    that it meets another book's genitive ("Vukadina", "Mića")"""
    father = e.get('fathers_name') or ''
    forms = {fold(father)}
    if e.get('_book') in POSSESSIVE_FATHERS and len(father) > 2:
        forms.add(fold(from_possessive(father)))
    return {f for f in forms if f}


def one_slip(x: str, y: str) -> bool:
    """two fathers a letter apart once their endings are cut ("pegrov"/"petra", "colov"/"dola", "jusufof"/"jusufa")"""
    cut = lambda s: re.sub(r'(?:ov|ev|of|in|a|e|o|u)$', '', s)
    x, y = cut(x), cut(y)
    if min(len(x), len(y)) < 3 or abs(len(x) - len(y)) > 1:
        return False
    if len(x) == len(y):
        return sum(c != d for c, d in zip(x, y)) <= 1
    short, long_ = sorted((x, y), key=len)
    return any(long_[:i] + long_[i + 1:] == short for i in range(len(long_)))


def fathers_agree(x: str, y: str) -> bool:
    return x == y or (len(x) <= 2 and y.startswith(x)) or (len(y) <= 2 and x.startswith(y)) or same_father(x, y)   # "Lj"


def village(e: dict) -> set[str]:
    """The village alone, without the municipality after it ("Kosanica, Pljevlja": the Spomenica's chapter and the
    Pljevlja lists name the municipality in every entry, so it tells no two men apart)"""
    first = (e.get('born_in') or '').split(',')[0]
    return {stem(w) for w in fold(first).split() if len(w) >= 4} - {'selu', 'opst', 'opsti', 'kotar', 'srez', 'okrug', 'kod'}


def overlap(x: set[str], y: set[str]) -> bool:
    return any(p[:4] == q[:4] for p in x for q in y)


def agreement(a: dict, b: dict) -> set[str] | None:
    """What two entries of different books agree on when they are one man (see the module's note), else None"""
    if frozenset((a['soldier_id'], b['soldier_id'])) in ONE_MAN_PAIRS:
        return {'checked by hand'}
    if frozenset((a['soldier_id'], b['soldier_id'])) in TWO_MEN_PAIRS:
        return None
    agree = set()
    fa, fb = father_forms(a), father_forms(b)
    ya, yb = year(a, 'birth_year'), year(b, 'birth_year')
    if fa and fb:
        if any(fathers_agree(x, y) for x in fa for y in fb):
            agree.add('father')
        elif not ((a.get('_book') in POSSESSIVE_FATHERS) != (b.get('_book') in POSSESSIVE_FATHERS) and
                  any(one_slip(x, y) for x in fa for y in fb) and ya and ya == yb and overlap(places(a), places(b))):
            return None
        else:
            agree.add('father')              # an OCR slip in a possessive father ("Pegrov" Petrov, "Jueov" Jusov), where
            #                                  the birth year and the village agree as well
    if ya and yb:
        if abs(ya - yb) > 1:
            return None
        agree.add('birth year')
    sa, sb = death_years(a), death_years(b)
    qa, qb = death_places(a), death_places(b)
    if sa and sb:
        if not sa & sb:
            # the books often disagree on the year he fell: no clash where the father, the exact birth year and the
            # village agree ("Joknić Mihailo" of Jugovo, 1908: 1943 and 1945), or they and the place he fell, a year
            # apart ("Markišić Aleksa", 1908: Soko Banja, 1941 and 1942)
            same = 'father' in agree and ya and ya == yb
            if not (same and (overlap(village(a), village(b)) or
                              (overlap(qa, qb) and min(abs(x - y) for x in sa for y in sb) == 1))):
                return None
            agree.add('death year differs')
        elif len(sa) == len(sb) == 1 or sa == sb:
            agree.add('death year')                        # or the same front's years (Gončin's and Tmušić's Srem)
    da, db = max(sa, default=None), max(sb, default=None)
    if (a.get('survived') and db and db <= 1945) or (b.get('survived') and da and da <= 1945):
        return None
    if overlap(places(a), places(b)):
        agree.add('birthplace')
    if set(a.get('units') or ()) & set(b.get('units') or ()) or (
            not a.get('units') and not b.get('units') and unit_key(a) and unit_key(a) == unit_key(b)):
        agree.add('unit')
    if overlap(qa, qb):
        agree.add('death place')
    core = agree & {'birth year', 'birthplace', 'death year'}
    if 'father' in agree and core:
        return agree
    if {'birth year', 'birthplace'} <= agree:
        return agree
    # the lists that give a name, a brigade and where he fell (Gončin's Srem): the unit or the place of his death,
    # with the year of it or with each other
    if ('unit' in agree or 'death place' in agree) and len(agree & {'unit', 'death place', 'death year'}) >= 2:
        return agree
    # a narodni heroj and an entry that names no father (a spomenica list's "Maček Ivan, 1908", Romano's "Albahari Nisim"):
    # the hero's name and his birth year
    if bool(a.get('_hero')) != bool(b.get('_hero')) and 'birth year' in agree and not (father_of(a) and father_of(b)):
        return agree
    return agree if a.get('_hero') and b.get('_hero') and agree & {'father', 'birth year'} else None


def same_man(a: dict, b: dict) -> bool:
    return agreement(a, b) is not None


def closeness(a: dict, b: dict) -> tuple[int, int]:
    """How much two entries that are one man agree on, to choose between two of a book's entries that both fit: a pair
    whose years of death differ comes after every pair whose don't, then the more they agree on, an exact birth year
    counting once more"""
    agree = agreement(a, b)
    if agree is None:
        return (-1, 0)
    if 'checked by hand' in agree:
        return (2, 0)
    exact = bool(year(a, 'birth_year') and year(a, 'birth_year') == year(b, 'birth_year'))
    return (0 if 'death year differs' in agree else 1, len(agree - {'death year differs'}) + exact)


def printed_twice(a: dict, b: dict) -> bool:
    """Two entries of one book that prints a man in more than one chapter (PRINTS_TWICE), or that ONE_MAN ties: the same
    father (an initial, an OCR slip: "Risga" and "Ristov"), birth year and year of death, and the same place of death
    or village ("Minić Milisav", 1926, Perišin and Nerišin, fell at Polja in 1944; "Ivović Momčilo", 1923, born in
    Podgorica, in the chapters of Bar, Pljevlja and Podgorica)"""
    if a['_book'] != b['_book']:
        return False
    if frozenset((a['soldier_id'], b['soldier_id'])) in ONE_MAN_PAIRS:
        return True
    if a['_book'] == CENSUS:
        return census_twice(a, b)
    if a['_book'] not in PRINTS_TWICE:
        return False
    fa, fb = father_forms(a), father_forms(b)
    if not (fa and fb and any(fathers_agree(x, y) or one_slip(x, y) for x in fa for y in fb)):
        return False
    ya, yb, sa, sb = year(a, 'birth_year'), year(b, 'birth_year'), death_years(a), death_years(b)
    if not (ya and yb and sa and sa == sb and
            (overlap(death_places(a), death_places(b)) or overlap(village(a), village(b)))):
        return False
    if ya == yb:
        return True
    # born a year apart: only under two municipalities (one chapter's two of a name are as likely two cousins), and
    # the father in full, not a letter off ("Burić Stanko", Đuro's son, 1912 under Danilovgrad and 1911 under Šavnik,
    # fell at Pljevlja in 1941; not "Jovanović Veselin", Marko's or Mirko's)
    return (abs(ya - yb) == 1 and a.get('opstina') != b.get('opstina') and
            any(fathers_agree(x, y) for x in fa for y in fb))


QUALIFIERS = {'gornji': 'g', 'gornja': 'g', 'gornje': 'g', 'gor': 'g', 'donji': 'd', 'donja': 'd', 'donje': 'd',
              'veliki': 'v', 'velika': 'v', 'veliko': 'v', 'vel': 'v', 'mali': 'm', 'mala': 'm', 'malo': 'm',
              'zgornji': 'g', 'zgornja': 'g', 'zgornje': 'g', 'spodnji': 'd', 'spodnja': 'd', 'spodnje': 'd',
              'stari': 's', 'stara': 's', 'staro': 's', 'novi': 'n', 'nova': 'n', 'novo': 'n'}


def qualifier(e: dict) -> str:
    """The village's Gornja/Donja, Velika/Mala, Stari/Novi ("Japra Donja" and "Japra Gornja" are two villages)"""
    words = fold((e.get('born_in') or '').split(',')[0]).split()
    return next((QUALIFIERS[w] for w in words if w in QUALIFIERS), '')


def census_twice(a: dict, b: dict) -> bool:
    """Two entries of one census volume that are one man (2026-11-26, for the lead's review; measured over the eight
    volumes: 249 pairs, 43 more left apart by the guards): the father (in another case, or a letter off: "Boja" and
    "Bojo"), the exact birth year and the year of death agree, and the place of death; or the village, where the two
    stand side by side in the volume or one gives no place of death; or, born a year apart, under two municipalities
    with the father in full and the same place of death. Never two villages a Gornja/Donja or Velika/Mala apart (two
    cousins as often). Two volumes (one name, father and year in two republics are as often two men) only with the
    exact birth year and the same place of death (11 pairs; 6 more across volumes left for review)."""
    fa, fb = father_forms(a), father_forms(b)
    if not (fa and fb):
        return False
    full = any(fathers_agree(x, y) for x in fa for y in fb)
    if not (full or any(one_slip(x, y) for x in fa for y in fb)):
        return False
    ya, yb, sa, sb = year(a, 'birth_year'), year(b, 'birth_year'), death_years(a), death_years(b)
    if not (ya and yb and sa and sa == sb):
        return False
    qa, qb = qualifier(a), qualifier(b)
    if qa and qb and qa != qb:
        return False
    place = overlap(death_places(a), death_places(b))
    if a.get('_vol') != b.get('_vol'):
        return ya == yb and place
    if ya != yb:
        municipality = lambda e: (e.get('born_in') or '').split(',')[-1].strip()
        return abs(ya - yb) == 1 and full and place and municipality(a) != municipality(b)
    if place:
        return True
    side_by_side = a['soldier_id'][:4] == b['soldier_id'][:4] and abs(int(a['soldier_id'][4:]) - int(b['soldier_id'][4:])) == 1
    no_place = not (a.get('death_place') and b.get('death_place'))
    return overlap(village(a), village(b)) and (side_by_side or no_place)


def tied(members: list[dict]) -> list[list[dict]]:
    """A cluster's entries with each book's entries of one man (printed_twice) together, and a narodni heroj's entries
    of the hero books ("Rolović Niko": the Zbornik's of 1910 and Narodni heroji's of 1909, whom the Spomenica and the
    census each print twice)"""
    parent = {m['soldier_id']: m['soldier_id'] for m in members}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            if printed_twice(a, b) or (a['_book'] != b['_book'] and a['_book'] in HERO_BOOKS and
                                       b['_book'] in HERO_BOOKS and same_man(a, b)):
                parent[find(a['soldier_id'])] = find(b['soldier_id'])
    out = defaultdict(list)
    for m in members:
        out[find(m['soldier_id'])].append(m)
    return list(out.values())


ORDINALS = [('jedanaest', 11), ('dvanaest', 12), ('trinaest', 13), ('cetrnaest', 14), ('petnaest', 15),
            ('sesnaest', 16), ('sedamnaest', 17), ('osamnaest', 18), ('devetnaest', 19), ('prv', 1), ('drug', 2),
            ('trec', 3), ('cetvrt', 4), ('pet', 5), ('sest', 6), ('sedm', 7), ('osm', 8), ('devet', 9), ('deset', 10)]
ADJECTIVES = ('proletersk', 'krajisk', 'lick', 'srpsk', 'vojvodansk', 'crnogorsk', 'makedonsk', 'majevick',
              'istocnobosansk', 'konjick', 'kordunask', 'banijsk', 'dalmatinsk', 'slavonsk', 'hercegovack')
_keys: dict[str, str] = {}


def unit_key(e: dict) -> str:
    """A brigade not on the site, as two lists of one front name it ("Trideset prva srpska udarna brigada" and "Trideset
    prve srpske narodnooslobodilačke brigade": "31 srpsk"; an artillery brigade or the staff units of a division:
    "art 5 krajisk"; the brigade formed in the USSR, "Prva jugoslovenska" to Gončin): '' when the entry names none"""
    label = e.get('unit') or ''
    if label not in _keys:
        words = fold(label).split()
        key = ''
        if 'sssr' in words or 'jugoslovenska' in words:
            key = 'novj sssr'
        else:
            for i, w in enumerate(words):
                n = next((v for s, v in ORDINALS if w.startswith(s)), None)
                if w in ('dvadeset', 'trideset', 'cetrdeset', 'pedeset') and i + 1 < len(words):
                    n = {'dvadeset': 20, 'trideset': 30, 'cetrdeset': 40, 'pedeset': 50}[w] + next(
                        (v for s, v in ORDINALS if words[i + 1].startswith(s)), 0)
                    i += 1
                if n:
                    adj = next((a for x in words[i + 1:i + 4] for a in ADJECTIVES if x.startswith(a)), None)
                    if adj:
                        kind = ('art ' if any(x.startswith('artiljerij') for x in words) else
                                'stab ' if any(x.startswith('pristap') for x in words) else '')
                        key = f'{kind}{n} {adj}'
                    break
        _keys[label] = key
    return _keys[label]


def death_years(e: dict) -> set[int]:
    """The years he can have died in: the year the entry gives, or the span a list gives (`death_years`)"""
    ys = {int(y) for y in e.get('death_years') or () if re.fullmatch(r'19[34]\d', str(y))}
    y = year(e, 'death_year') or year(e, 'death_date')
    return {y} if y else ys


def death_places(e: dict) -> set[str]:
    return {stem(w) for w in fold(e.get('death_place') or '').split() if len(w) >= 4} - {'selu', 'kod', 'blizu'}


_given: Counter = Counter()


_father_forms: Counter = Counter()


def given_names() -> None:
    """The site's given names, for a father the book gives as a possessive or a genitive; and how often each father's
    form stands in the units, for convert_fathers_genitive's stricter test of a rare one"""
    for code, cfg in BRIGADE_CONFIGS.items():
        path = ROOT / 'website' / 'public' / cfg['json_file']
        if code not in OSTALI_CODES and path.exists():
            for r in json.loads(path.read_text(encoding='utf-8')):
                if r.get('first_name'):
                    _given[r['first_name']] += 1
                if r.get('fathers_name'):
                    _father_forms[r['fathers_name']] += 1


def from_genitive(word: str, local: Counter | None = None) -> str:
    """The father's nominative for a genitive the book prints ("Miloša" Miloš, "Janka" Janko, "Franca" Franc), chosen
    as convert_fathers_genitive.py chooses it for the units' records (which get it as corrections, and 122's can't):
    the form the book's own given names clearly favour (local: the Spomenica's "Mila" is Milo, Lika's Mile), else the
    site's; '' when none does or it is the printed form itself"""
    if not FATHER_WORD.match(word) or not word.endswith(('a', 'e')):
        return ''
    if word in fathers_genitive.OVERRIDES:
        return fathers_genitive.OVERRIDES[word][1]
    nom = fathers_genitive.pick(word, local or _given, _given, rare=_father_forms[word] <= 3)
    return nom if nom and nom != word else ''


def normalizer_reads(word: str) -> bool:
    """normalize_all_json.py will put this printed genitive in the nominative (its own dictionary: "Milivoja", which
    from_genitive leaves, Milivoje and Milivoj being both common)"""
    word = to_title_case(clean_name_field(word))
    return word not in REGIONAL_GENITIVES and genitive_to_nominative(word) not in ('', word)


def from_possessive_or_genitive(word: str, local: Counter | None = None) -> str:
    """A book of possessive fathers prints some in the genitive too: "Jova" and "Steva" are Jovo's and Stevo's, not a
    daughter's possessive of "J" and "St" (from_possessive alone gave "J" and "Sto"): the reading whose name the site
    knows best"""
    found = [n for n in (from_possessive(word), from_genitive(word, local)) if n]
    return max(found, key=lambda n: _given[n], default='')


def from_possessive(word: str) -> str:
    """The father's name from the possessive Trebinjci pali prints, -ov/-ev of a name without -a ("Mitrov" Mitar, "Vulov"
    Vule or Vulo), -in of a name in -a ("Lučin" Luka, "Savin" Sava): the form the site's given names know best; '' when
    none of them is a name"""
    word = re.sub(r'(ov|ev|in)a$', r'\1', word)          # a daughter's: "Đokova", "Lučina"
    m = re.match(r'^(.+?)(ov|ev|in)$', word)
    if not m:
        return ''
    base, end = m.groups()
    if end in ('ov', 'ev'):
        cands = [base, base + 'o', base + 'e', re.sub(r'([^aeiou])([rl])$', r'\1a\2', base)]
    else:
        soft = base[:-1] + {'č': 'k', 'ž': 'g', 'š': 'h'}.get(base[-1], base[-1])      # Lučin: Luka
        cands = [base + 'a', soft + 'a'] + ([base[:-1] + 'ca'] if base.endswith('č') else [])   # Jovičin: Jovica;
        #                                                       not Milijin: Milica, Perišin: Perica (Milija, Periša)
    best = max(cands, key=lambda c: _given[c])
    return best if _given[best] else ''


def registry() -> dict[str, str]:
    """Entry ID -> record ID; started from the file the first records were written to (0122 + the book's two digits +
    the entry's number, and the record's other entries)"""
    if IDS.exists():
        return json.loads(IDS.read_text(encoding='utf-8'))
    out = {}
    if OUT.exists():
        for r in json.loads(OUT.read_text(encoding='utf-8')):
            for o in r.get('other_sources') or ():
                if re.fullmatch(r'90\d{8}', o.get('soldier_id') or ''):
                    out[o['soldier_id']] = r['soldier_id']
            out.setdefault(f"90{r['soldier_id'][4:6]}00{r['soldier_id'][6:]}", r['soldier_id'])
    return out


def chosen_fathers() -> dict[str, tuple[str, str]]:
    """Record ID -> (the father as printed, the nominative chosen for him) in the file a run replaces (unit 122): the
    choice reads the site's given names and how often a form still stands unconverted in the units, which change as
    the units' own fathers are put in the nominative (by corrections), so a run of the same entries would choose
    otherwise ("Mila" Milo or Mile, "Save" Sava or as printed). 122's records have no corrections to hold the choice:
    it stays while he is printed so, as his ID does. Blank a fathers_name in the file to have it chosen again.
    The printed form is kept as the normalizer leaves it, whichever file this run reads: one a run of this script wrote
    still holds him as printed ("Đ.", "JOSIPA", "Marka."), and a second run before normalize_all_json had compared
    that with the cleaned form and lost the choice (2026-11-19: Ćosović Veljko's Đorđije became the initial "Đ").
    An initial is never a choice to keep."""
    out = {}
    # (and the men this script gave to their units, by their 122 ID: the choice goes with him)
    for path, moved in [(OUT, False)] + [(unit_file(code), True) for code in unit_codes()]:
        if not path.exists():
            continue
        for r in json.loads(path.read_text(encoding='utf-8')):
            if moved and not is_moved(r):
                continue
            printed = to_title_case(clean_name_field(r.get('middle_name') or ''))
            nom = r.get('fathers_name') or ''
            if printed and len(re.sub(r'\W', '', nom)) > 2 and nom != printed:
                out[r['former_ids'][0] if moved else r['soldier_id']] = (printed, nom)
    return out


def unit_file(code: int) -> Path:
    return ROOT / 'website' / 'public' / BRIGADE_CONFIGS[code]['json_file']


def unit_registry() -> dict[str, str]:
    return json.loads(UNIT_IDS.read_text(encoding='utf-8')) if UNIT_IDS.exists() else {}


def census_ids_on_disk() -> set[str]:
    """The IDs of the census parts' records as the files on disk hold them (read as text: the parts are large)"""
    out = set()
    for code in CENSUS_VOLUMES.values():
        path = unit_file(code)
        if path.exists():
            out |= set(re.findall(r'"soldier_id": "(\d{10})"', path.read_text(encoding='utf-8')))
    return out


def unit_ids_on_disk() -> set[str]:
    """The IDs in the units' files on disk (122's and the census parts' not): their records', and the entries merged
    into them, whose addresses lead to the record too"""
    out = set()
    for code, cfg in BRIGADE_CONFIGS.items():
        path = ROOT / 'website' / 'public' / cfg['json_file']
        if code not in OSTALI_CODES and path.exists():
            out |= set(re.findall(r'"soldier_id": "(\d{10})"', path.read_text(encoding='utf-8')))
    return out


def census_redirects(old_ids: set[str], new_ids: set[str], previous: dict[str, str], census_entry: dict[str, str],
                     holder_of) -> dict[str, str]:
    """Old census record -> the record that holds the man's entry now, for each census record that has left its part:
    those on disk less those written now, and the census IDs the redirects had before (followed to the entry's record
    of today; dropped where the census record is back or no record holds the entry)"""
    codes = {f'{c:04d}' for c in CENSUS_VOLUMES.values()}
    out = {}
    for rid in sorted((old_ids - new_ids) | {k for k in previous if k[:4] in codes}):
        if rid in new_ids or rid not in census_entry:
            continue
        to = holder_of(census_entry[rid])
        if to:
            out[rid] = to
    return out


def redirects_122(old_ids: set[str], new_ids: set[str], previous: dict[str, str], ids_before: dict[str, str],
                  holder_of) -> dict[str, str]:
    """Old record of 122 -> the record that holds the man's entry now, for each record of 122 that has left it and is
    neither moved to a unit nor joined by hand (MERGED_IDS): its entry taken by a unit's record (a reference), or
    joined to another record. Those on disk less those written now, and the 122 IDs the redirects had before (followed
    to the entry's record of today; dropped where the record is back or no record holds an entry of it). 2026-11-26:
    the Slovene run's references took 41 records of 122 (Belehar Janko, 0122957334, to the Jeseniško-bohinjski odred's
    0171010007), whose addresses had gone nowhere; until then such records were redirected by hand in MERGED_IDS."""
    code = f'{CODE:04d}'
    entries_of = defaultdict(list)
    for e, rid in ids_before.items():
        entries_of[rid].append(e)
    out = {}
    for rid in sorted((old_ids - new_ids) | {k for k in previous if k[:4] == code}):
        if rid in new_ids or rid in MERGED_IDS:
            continue
        to = next((t for e in sorted(entries_of.get(rid, ())) for t in [holder_of(e)] if t and t != rid), None)
        if to:
            out[rid] = to
    return out


def load_overrides() -> dict[str, dict]:
    """The fixes by hand, by entry (OVERRIDES)"""
    return json.loads(OVERRIDES.read_text(encoding='utf-8')) if OVERRIDES.exists() else {}


def apply_overrides(rec: dict, g: list[dict], overrides: dict[str, dict], family: dict, applied: set[str]) -> None:
    """The fields set by hand for any of the record's entries, on the record as assembled; marked in manual_fields, so no
    later step reads them otherwise (the normalizer, the field reader, the places and the one form). A family's field
    stands over an override of the same field (the user's rule: the family's report wins), which is printed."""
    manual = set(rec.get('manual_fields') or ())
    for m in g:
        o = overrides.get(m['soldier_id'])
        if not o:
            continue
        applied.add(m['soldier_id'])
        if o.get('for') and o['for'] != rec['soldier_id']:
            print(f"  OVERRIDE {m['soldier_id']}: written for {o['for']}, now on {rec['soldier_id']}: check it")
        for k, v in (o.get('fields') or {}).items():
            if k in OVERRIDE_REFUSED:
                print(f"  OVERRIDE {m['soldier_id']}: {k} may not be set by hand, left out")
            elif k in family and family[k] != v:
                print(f"  OVERRIDE {m['soldier_id']}: {k} {v!r} against the family's {family[k]!r}: the family's stands")
            else:
                if v == '':
                    rec.pop(k, None)
                else:
                    rec[k] = v
                manual.add(k)
    if manual:
        rec['manual_fields'] = sorted(manual)
        cols = [k for k in rec.get('from_columns') or () if k not in manual]
        if cols:
            rec['from_columns'] = cols
        else:
            rec.pop('from_columns', None)


def unit_codes() -> set[int]:
    """the units that hold men this script gave them"""
    return {int(v[:4]) for v in unit_registry().values()}


def is_moved(r: dict) -> bool:
    return bool(r.get('former_ids')) and int(r['soldier_id'][4:]) >= UNIT_FIRST


def move_to_units(recs: list[dict], ids: dict[str, str]) -> tuple[dict, dict, Counter]:
    """Take out of 122's records those whose entries name a unit on the site without doubt (scripts/unit_named.py),
    each with its ID in the unit: unit code -> the records, the registry, and why the others stay. Not a man of the
    movement who was no fighter (role), nor one whose entries include the unit's own book, whose parser left him out
    (the Mosor list's activists: "držao u ilegalnosti 2. četu ... Mosorskog PO")."""
    import unit_named
    registry_ = unit_registry()
    entries_of = defaultdict(list)
    for e, rid in ids.items():
        entries_of[rid].append(e)
    nxt = {}
    for v in registry_.values():
        nxt[int(v[:4])] = max(nxt.get(int(v[:4]), UNIT_FIRST), int(v[4:]) + 1)
    moved, keep, why, taken_ids = defaultdict(list), [], Counter(), set()
    for r in recs:
        if r.get('role'):
            keep.append(r)
            why['a man of the movement, no fighter'] += 1
            continue
        texts = [r.get('additional_info') or ''] + [o.get('additional_info') or '' for o in r.get('other_sources') or ()]
        code, how = unit_named.unit_of(texts)
        pdfs = {r.get('pdf_file')} | {o.get('pdf_file') for o in r.get('other_sources') or ()}
        if code and pdfs & unit_named.own_books(code):
            code, how = None, "an entry of the unit's own book, which its parser left out"
        if not code:
            keep.append(r)
            why[how] += 1
            continue
        es = sorted(entries_of[r['soldier_id']])
        had = sorted(v for e in es for v in [registry_.get(e, '')] if v[:4] == f'{code:04d}' and v not in taken_ids)
        if had:
            nid = had[0]
        else:
            nid = f'{code:04d}{nxt.setdefault(code, UNIT_FIRST):06d}'
            nxt[code] += 1
        taken_ids.add(nid)
        for e in es:
            registry_[e] = nid
        moved[code].append({**r, 'soldier_id': nid, 'former_ids': [r['soldier_id']]})
        why['to its unit'] += 1
    recs[:] = keep
    return moved, registry_, why


def full_name(rec: dict, code: int) -> str:
    """The name scripts/normalize_all_json.py (step 2 of the chain) gives the record in its unit: the names as it cleans
    them, a name set by hand (manual_fields) as set. This script writes all nine files and every unit that holds moved
    men, and a chain run over fewer of them left the others' names empty: on 2026-11-25 the run over 122 and the batch's
    units left every census record nameless, and Banović Ivan Ljubo 0132024064, kept from that run for his override,
    lost his name on the site's card"""
    out = normalize_soldier(rec, code)
    names = ('last_name', 'middle_name', 'first_name')
    manual = set(rec.get('manual_fields') or ()) & set(names)
    if not manual:
        return out['full_name']
    return ' '.join(p for p in (rec.get(n) if n in manual else out.get(n) for n in names) if p)


def source_entry(e: dict) -> dict:
    out = {'soldier_id': e['soldier_id'], 'name': e['name'], 'additional_info': e['additional_info']}
    out.update({k: e[k] for k in SOURCE_FIELDS if e.get(k) not in (None, '')})
    if e.get('role'):
        out['role'] = e['role']
    return out


def main():
    write = '--write' in sys.argv
    given_names()
    corrections = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    # an entry a record of a unit took (not one of this unit's: those come and go with this script)
    ostali = {f'{c:04d}' for c in OSTALI_CODES}
    holders = defaultdict(set)                                # the entry -> the records of units that hold it
    for c in corrections:
        if c['action'] == 'reference' and c['soldier_id'][:4] not in ostali:
            holders[c['ref_id']].add(c['soldier_id'])
    taken = set(holders)
    entries = []
    for book, es in books().items():
        # the census's volumes are one book, its volume kept for the part of Ostali borci its men go to
        vol = book[len(CENSUS) + 1:] if book.startswith(CENSUS + '-') else ''
        for e in es:
            e = dict(e, _book=CENSUS if vol else book, _vol=vol,
                     _hero=book in HERO_BOOKS or bool(re.search(r'narodn\w*\s*heroj', e['additional_info'], re.I)))
            if e['soldier_id'] in NAME_FIXES:
                e['last_name'], e['first_name'], e['fathers_name'] = NAME_FIXES[e['soldier_id']]
                e['name'] = f"{e['last_name']} {e['first_name']}"
                if e['soldier_id'] in NO_NICK:
                    e.pop('nick', None)
            if e['soldier_id'] in GIVEN_FIXES:
                e['first_name'] = GIVEN_FIXES[e['soldier_id']]
                e['name'] = f"{e['last_name']} {e['first_name']}"
            # the census's "Ćurković (Nema) Jure", "Feljan (Nepoznat) Franjo": no father, no word in his name
            if NO_FATHER.match(e.get('fathers_name') or ''):
                e['fathers_name'] = ''
            scanned_names(e)
            # a man the book names by one name is still its man (Romano's "Ašer (prezime nepoznato)", Oborovo's "Ivica
            # ...", Gončin's "Janković"; the user's decision of 2026-10-14); one it could not name ("Nepoznati borac"),
            # or a number its parser keeps with no one, is no one a search can find
            if ((e.get('last_name') or e.get('first_name')) and not e.get('unnamed') and not infant(e)
                    and e['soldier_id'] not in LEFT_OUT):
                entries.append(e)
    # each book's own given names, to read its genitive fathers by its region's names (from_genitive)
    book_given: dict[str, Counter] = defaultdict(Counter)
    for e in entries:
        if e.get('first_name'):
            book_given[e['_book']][e['first_name']] += 1
    by_name = defaultdict(list)
    for e in entries:
        # one name alone is too little to make two books' entries one man: such an entry stays apart
        key = (fold(e['last_name']), fold(e['first_name'])) if e.get('last_name') and e.get('first_name') else e['soldier_id']
        by_name[key].append(e)

    # one man across books: the entries of a name joined pair by pair (never two entries of one book)
    parent = {e['soldier_id']: e['soldier_id'] for e in entries}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for group in by_name.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if (a['_book'] != b['_book'] and same_man(a, b)) or printed_twice(a, b):
                    parent[find(a['soldier_id'])] = find(b['soldier_id'])
    for x, y, _ in ONE_MAN:
        if x in parent and y in parent:
            parent[find(x)] = find(y)
    clusters = defaultdict(list)
    for e in entries:
        clusters[find(e['soldier_id'])].append(e)

    ids = registry()
    ids_before = dict(ids)        # as read: a record of 122 that leaves is found by its entries (redirects_122)
    chosen = chosen_fathers()
    next_number = max([int(v[4:]) for v in ids.values() if int(v[4:]) >= FIRST_NEW], default=FIRST_NEW - 1) + 1
    used = set()

    def record_id(group: list[dict]) -> str:
        """The ID the group's man had (its first entry's, if two records of before become one), else a new one"""
        nonlocal next_number
        for m in group:
            rid = ids.get(m['soldier_id'])
            if rid and rid not in used:
                return rid
        rid = f'{CODE:04d}{next_number:06d}'
        next_number += 1
        return rid

    records, counts, on_site = [], Counter(), []
    overrides, overridden = load_overrides(), set()       # fixes by hand, by entry (OVERRIDES)
    for members in clusters.values():
        # a cluster that took two entries of one book (not one man it prints twice) is two men: the entries of that
        # book stay apart, and an entry of another book joins the one it agrees with, or the one it agrees with best
        # ("Vujošević Stanko": the census's two of Mataguži, 1910 and 1911, and the Spomenica's of 1910); one that
        # agrees with two alike (or with neither) joins the other books' entries it is one man with ("Tešović
        # Neđeljko": the census prints him twice, the Spomenica crnogorska and Prilog u krvi once each), else stays alone
        units = tied(members)
        books_of = lambda g: {x['_book'] for x in g}
        per_book = Counter(b for u in units for b in books_of(u))
        if max(per_book.values()) > 1:
            book = per_book.most_common(1)[0][0]
            groups = [list(u) for u in units if book in books_of(u)]
            loose, left = [], []
            # the entry that fits the fewest groups first, each scored against all a group holds by then ("Burić
            # Stanko": the Spomenica's, which fits only the census's 1919, before the hero books', which then follow
            # it there rather than to the census's 1920)
            pending = [u for u in units if book not in books_of(u)]
            while pending:
                scored = []
                for u in pending:
                    score = [max(closeness(x, y) for x in g for y in u)
                             if not books_of(u) & books_of(g) else (-1, 0) for g in groups]
                    scored.append((sum(s[0] >= 0 for s in score), u, score))
                fits, u, score = min(scored, key=lambda t: (t[0] if t[0] else 99, [-x for x in max(t[2])]))
                pending.remove(u)
                best = max(score)
                if best[0] >= 0 and score.count(best) == 1:
                    groups[score.index(best)].extend(u)
                    continue
                # a man printed twice who fits two of the doubled book's entries alike, each of his entries best
                # another, is as likely two men that book prints too ("Martinović Ljubica", Marko's, of 1923 and 1924
                # in the Spomenica and in the census): each entry goes to its own
                picks = []
                for m in (u if len(u) > 1 and best[0] >= 0 else ()):
                    s = [max(closeness(x, m) for x in g) if m['_book'] not in books_of(g) else (-1, 0) for g in groups]
                    picks.append(s.index(max(s)) if max(s)[0] >= 0 and s.count(max(s)) == 1 else None)
                if picks and None not in picks and len(set(picks)) == len(picks):
                    for m, i in zip(u, picks):
                        groups[i].append(m)
                else:
                    left.append(u)
            for u in left:
                fit = lambda g: not books_of(u) & books_of(g) and all(same_man(x, y) for x in g for y in u)
                joins = [g for g in loose if fit(g)]          # another book's entry left over as well
                if joins:
                    joins[0].extend(u)
                    continue
                # else the one group of most books it agrees with whole, if that already joined another book's entry to
                # the doubled book's ("Anđelić Vukoman": the census man who took Prilog u krvi's entry, and the
                # Spomenica's)
                cands = [g for g in groups if fit(g)]
                best = max((len(books_of(g)) for g in cands), default=0)
                top = [g for g in cands if len(books_of(g)) == best]
                if best > 1 and len(top) == 1:
                    top[0].extend(u)
                else:
                    loose.append(list(u))
            groups += loose
            counts['clusters split (two entries of one book)'] += 1
        else:
            groups = [members]
        for g in groups:
            if any(m['soldier_id'] in taken for m in g):
                with_ = [x['soldier_id'] for x in g if x['soldier_id'] in taken]
                on_site += [dict(m, _with=with_) for m in g if m['soldier_id'] not in taken]
                continue
            g.sort(key=lambda m: (not m.get('pdf_file'), -len(m['additional_info']), m['soldier_id']))
            first, rest = g[0], g[1:]
            text = first['additional_info'].strip()
            if first.get('nick') and first['nick'] not in text:
                text = f"zvani {first['nick']}; {text}"
            # the father as the lead entry gives him, else (it names none, or only an initial) as the first entry that
            # gives him in full ("Bukovec Franc": Dolomiti's scanned entry leads, the hero books name Franc his father),
            # read as that entry's book prints him (nominative, possessive or genitive)
            given = lambda m, n: len(re.sub(r'\W', '', m.get('fathers_name') or '')) > n
            fsrc = first if given(first, 2) else next((m for m in g if given(m, 2)), None)
            # a possessive the scan spoiled, which no name reads from ("Milivojsv", "Sgankov"), gives way to an entry
            # whose father its book's rule reads (another book's "Milivoja", "Stanka", the census's nominative):
            # Drašković Ilija had kept the lead's initial, others the spoiled form; a rare name's "Mišurov" stays where
            # the other book's "Mišura" reads no better, and a book's own nominative ("Đuro") is never set aside
            # (a genitive also where the normalizer's own dictionary reads it, as it will: "Milivoja" Milivoje)
            reads = lambda m: given(m, 2) and bool(
                m['fathers_name'] if m['_vol'] or m['_book'] in NOMINATIVE_FATHERS else
                from_possessive_or_genitive(m['fathers_name'], book_given[m['_book']])
                if m['_book'] in POSSESSIVE_FATHERS else
                from_genitive(m['fathers_name'], book_given[m['_book']]) or normalizer_reads(m['fathers_name']))
            if fsrc and fsrc['_book'] in POSSESSIVE_FATHERS and not reads(fsrc):
                fsrc = next((m for m in g if reads(m)), fsrc)
            fsrc = fsrc or (first if given(first, 0) else next((m for m in g if given(m, 0)), first))
            father = fsrc.get('fathers_name') or ''
            census = [m for m in g if m['_vol']]
            if census and len(census) == len(g):
                # only the census names him: his volume's part, his census entry's number (no registry)
                code = CENSUS_VOLUMES[first['_vol']]
                rid = f"{code:04d}{first['soldier_id'][4:]}"
            else:
                code = CODE
                rid = record_id(g)
                for m in g:
                    ids[m['soldier_id']] = rid
            used.add(rid)
            # the census prints the father in the nominative ("Marković (Rade) Tomo"): as printed in its parts (their
            # config says nominative), only as fathers_name in 122, whose normalization reads a middle name as genitive
            # (and so does the Tuzla memorial book: "AJDASLIĆ, MUJO (Avdo i Fatima)")
            nominative = fsrc['_vol'] or fsrc['_book'] in NOMINATIVE_FATHERS
            rec = {'soldier_id': rid, 'last_name': first['last_name'],
                   'middle_name': '' if nominative and code == CODE else father, 'first_name': first['first_name'],
                   'fathers_name': (from_possessive_or_genitive(father, book_given[fsrc['_book']])
                                    if fsrc['_book'] in POSSESSIVE_FATHERS else
                                    father if nominative else ''),
                   'full_name': '', 'additional_info': text,
                   'birth_year': born_year(first, year)}
            if fsrc is not first and given(first, 0) and (nominative or fsrc['_book'] in POSSESSIVE_FATHERS):
                rec['middle_name'] = first['fathers_name']     # the lead's initial stays in the name ("Zec B. Drago"),
                #                                                his father in full from the census beside it (Bojan)
            if rec['middle_name'] and not rec['fathers_name']:
                rec['fathers_name'] = from_genitive(rec['middle_name'], book_given[fsrc['_book']])   # "Miloša": Miloš (the normalizer's
                #                                                           own dictionary leaves most as printed)
            # a father printed in the genitive or as a possessive keeps the nominative the last run chose (chosen_fathers)
            was = chosen.get(rid) if code == CODE and not nominative else None
            if was and was[0] == to_title_case(clean_name_field(rec['middle_name'])):
                rec['fathers_name'] = was[1]
            rec.update({k: first[k] for k in SOURCE_FIELDS if first.get(k) not in (None, '')})
            # a names-only list of the fallen (Gončin's and Tmušić's Srem, Oborovo) holds no bio for the field
            # extractor: the death from its entries' fields, the village he fell at and the day where it gives them (not
            # a names-only list of survivors: the Vis spomenica's holders)
            listed = [m for m in g if m.get('pdf_file') in NAME_LISTS and not m.get('survived')]
            if listed:
                # (an entry may say how: the Vis plaques' died of wounds are "umro")
                rec['death_type'] = next((m['death_type'] for m in listed if m.get('death_type')), 'poginuo')
                place = next((m['death_place'] for m in listed if m.get('death_place')), '')
                day = next((m['death_date'] for m in listed if re.fullmatch(r'\d{4}-\d\d-\d\d', m.get('death_date') or '')), '')
                if place:
                    rec['death_place'] = place
                if day:
                    y, mo, d = day.split('-')
                    rec['death_date'] = f'{int(d)}. {int(mo)}. {y}.'
            # the census's and the column books' fields, where a list gave none; their death is marked (from_columns), so
            # the field reader may put the man's own biography first: "Strijeljana od četnika 1942." is streljan, not
            # the Spomenica's "poginuo", and "poginuo 9. juna 1943." the day, not its year (2026-10-28)
            filled = []
            columns = [m for m in g if is_column(m['_book'], m)]
            # a column book's day of death goes before the census's bare year, with its place (the user's rule of
            # 2026-11-23: "yes, if exact date. Family record trumping all of it"): Brod's "Veljković Mika, 15. 5. 1944.,
            # Plana" had shown the census's "1944, Crna Trava"; the census's year and place then show after "ili" where
            # they differ (record_sources.variants), and its place fills in only for the same year. A book that gives
            # the year alone (the Spomenica) still comes after the census
            exact = next((m for m in columns if EXACT_DAY.fullmatch(m.get('death_date') or '')), None)
            if exact:
                for k, v in column_fields(exact).items():
                    if k == 'death_type' and census and not type_stated(exact) and type_stated(census[0]):
                        continue                         # the census's stated type, over the list's default
                    if k in DEATH_KEYS and k not in rec:
                        rec[k] = v
                        filled.append(k)
            census_place = ''
            if census:
                c = census_fields(census[0])
                if exact and c.get('death_date') and c['death_date'] != exact['death_date'][:4]:
                    c.pop('death_place', None)               # another year's place: shown with its year after "ili"
                for k, v in c.items():
                    # his unit from the census's column only where no book's biography tells it (the field reader's)
                    if k not in rec and not (k == 'unit_detail' and len(census) < len(g)):
                        rec[k] = v                           # the census's columns, where a list gave no death
                        filled.append(k)
                        census_place = v if k == 'death_place' else census_place
            # the census's place gives way where it says less, to a column book's of the year alone, as in a unit's record
            # (record_sources.census_gives_way, board 36's rules; board 67): off the map ("Kučaevica": the Spomenica's
            # Kučajevica), a region alone ("Dolenjsko": Iskra in plamen's Krvava peč), one place in a form that says
            # less ("Plevlja": Pljevlja); not where his place was read by hand (DEATH_PLACE_READS)
            if census_place and rec.get('death_place') == census_place and rid not in DEATH_PLACE_READS:
                import record_sources
                from standardize_fields import place_form       # (compared as the site writes them: "Trnovo-sarajevo"
                site = lambda v: place_form(v) or v             # is Trnovo, Sarajevo, which the map puts)
                year_alone = [dict(f, death_place=site(f['death_place'])) for f in
                              (column_fields(m) for m in columns if not EXACT_DAY.fullmatch(m.get('death_date') or ''))
                              if f.get('death_place')]
                # (strict: here the map knows too few places for off the map to tell a garble)
                spot = record_sources.census_gives_way(site(census_place), rec.get('death_date'), year_alone, OUT.name,
                                                       strict=True)
                if spot:
                    rec['death_place'] = spot
                    counts['census place gives way (board 67)'] += 1
            if columns:
                for k, v in column_fields(columns[0]).items():
                    if k not in rec and not (k == 'unit_detail' and len(columns) + len(census) < len(g)):
                        rec[k] = v                           # the Spomenica's columns
                        filled.append(k)
            # a family's papers (Porodična arhiva), a visitor's message, a Wikipedia article: the fields its entry sets by
            # hand, what the prose tells that the field reader can't read ("u Prvoj krajiškoj brigadi ... prešao u Treću
            # krajišku", "komesar Fočansko-čelebićkog odreda"): every fact the text gives stands in its row on the card
            # (the user's rule of 2026-11-20)
            family = {}
            for m in g:
                if m['_book'] in ('porodicna-arhiva', 'poruke-posetilaca', 'vikipedija'):
                    rec.update(m.get('fields') or {})        # set by hand: over the census's column (Bogavac's Kraljevo)
                    if m['_book'] == 'porodicna-arhiva':
                        family.update(m.get('fields') or {})
            if not rec.get('birth_place'):
                # what the book's parser read of where he is from (often in a case): extract_structured_fields.read_all
                # takes it where no entry's text names a place, and the reader leaves no trace of it on the record
                seen = next((m['born_in'] for m in g if m.get('born_in') and m['_book'] not in BORN_IN_NOT_HIS), '')
                if seen:
                    rec['born_in'] = seen
            # the place too (2026-11-19): Sekulić Mane Miloš's own "u Žumberku 10. 9. 1944." over the census's
            # "Bosiljevo slove"; the census's place then shows after "ili" where it lies far off (record_sources.variants)
            # (not those a family's papers set: the family's stand, and the field reader must not put a book's first, 2026-11-23,
            # Čelebić Ilije Novak's 1946 against the Lovćenski list's 1945)
            death_cols = [k for k in ('death_type', 'death_date', 'death_place') if k in filled and k not in family]
            read = DEATH_PLACE_READS.get(rid)
            if read is not None and 'death_place' in death_cols:
                death_cols.remove('death_place')         # the census's place stands, or the place read by hand
                if read:
                    rec['death_place'] = read
            if death_cols and any(not is_column(m['_book'], m) and not m['_book'].startswith('zrtve-rata-1964')
                                  for m in g):
                rec['from_columns'] = death_cols
            if rest:
                rec['other_sources'] = [source_entry(m) for m in rest]
            # a man of the movement whom a mixed list names and no book calls a fighter (the user's decision of
            # 2026-10-19: such lists' activists go in, marked, so the site can tell them apart); 'participant' where
            # the book doesn't say which he was (Staromajdansko's names-only "borci i učesnici rata", 2026-10-20)
            roles = {m.get('role') for m in g}
            if None not in roles:
                rec['role'] = 'activist' if 'activist' in roles else 'participant'
            # the fields set by hand for one of his entries (scripts/patch_record.py), last, over every reading above,
            # and before move_to_units, so a man who goes to his unit takes them along
            apply_overrides(rec, g, overrides, family, overridden)
            records.append(rec)
            counts[f'{len(g)} book(s)'] += 1
            counts['from ' + first['_book'] + (f" ({first['_vol']})" if first['_vol'] else '')] += 1
    # an override whose entry made no record (a unit's record holds it, it waits as the same man as an entry on the site,
    # or it is left out): its fix belongs on that record, as an edit correction
    for e in sorted(set(overrides) - overridden):
        print(f"  OVERRIDE {e} ({overrides[e].get('for', '?')}): its entry made no record here; "
              f"fix the record that holds it with an edit correction")
    n_ids = Counter(r['soldier_id'] for r in records)
    assert max(n_ids.values()) == 1, [i for i, n in n_ids.items() if n > 1][:5]
    parts = defaultdict(list)                                 # code -> its records
    for r in records:
        parts[int(r['soldier_id'][:4])].append(r)
    # the men whose entries name their unit on the site go to it (move_to_units)
    to_units, unit_ids, why = move_to_units(parts[CODE], ids)
    for code, recs in [*parts.items(), *to_units.items()]:
        for r in recs:
            r['full_name'] = full_name(r, code)     # never empty, whichever files the chain then takes (full_name)
    by_name = lambda r: (fold(r['last_name']), fold(r['first_name']), fold(r['middle_name']), r['soldier_id'])  # noqa: E731
    for recs in list(parts.values()) + list(to_units.values()):
        recs.sort(key=by_name)
    print(f'{len(entries)} entries, {len(taken)} on records of units; {len(records)} records')
    print(f'{sum(len(v) for v in to_units.values())} records of {CODE} go to {len(to_units)} units:')
    for k, v in why.most_common():
        print(f'  {v:6d}  {k}')
    for code, recs in sorted(to_units.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(recs):5d}  {code} {BRIGADE_CONFIGS[code]['name']}")
    print(f'{len(on_site)} more entries are the same man as an entry on the site and stay out')
    for k, v in sorted(counts.items()):
        print(f'  {k}: {v}')
    for code in sorted(parts):
        print(f"  {code}: {len(parts[code])} records")
    print(f'{sum(1 for r in parts[CODE] if int(r["soldier_id"][4:]) >= FIRST_NEW)} records of {CODE} with a new ID')
    if write:
        # a census record that leaves its part (its entry joined a record of 122 or went to a unit's record) still
        # opens the man's card: its ID -> the record that holds his entry, read before the parts are written over
        # (2026-11-22: /borac/0133000764 had gone nowhere since the Poreklo books took 117 and 111 such men)
        present, moved_now = {r['soldier_id'] for r in parts[CODE]}, {r['soldier_id'] for v in to_units.values() for r in v}
        with_of = {m['soldier_id']: m['_with'] for m in on_site}

        # a reference whose record a merge took away or a delete removed would send the address nowhere: only the
        # records on the site count (the units' files as on disk, as scripts/backfill_census_redirects.py reads them)
        live = unit_ids_on_disk() | moved_now
        # the record of 122 or of a census part written now that holds the entry among its others: a census entry
        # printed twice joins the other's record (census_twice; 2026-11-26, 229 census records had gone nowhere)
        in_parts = {o['soldier_id']: r['soldier_id'] for code in [CODE, *CENSUS_VOLUMES.values()]
                    for r in parts.get(code, []) for o in r.get('other_sources') or () if o.get('soldier_id')}

        def holder_of(e: str) -> str | None:
            held = sorted(r for r in holders.get(e, ()) if r in live)
            if held:
                return held[0]
            if unit_ids.get(e) in moved_now:
                return unit_ids[e]
            if ids.get(e) in present:
                return ids[e]
            if e in in_parts:
                return in_parts[e]
            held = sorted(r for w in with_of.get(e, ()) for r in holders.get(w, ()) if r in live)
            return held[0] if held else None
        census_moved = census_redirects(
            old_ids=census_ids_on_disk(),
            new_ids={r['soldier_id'] for code in CENSUS_VOLUMES.values() for r in parts.get(code, [])},
            previous=json.loads(MOVED.read_text(encoding='utf-8')) if MOVED.exists() else {},
            census_entry={f"{CENSUS_VOLUMES[m['_vol']]:04d}{m['soldier_id'][4:]}": m['soldier_id'] for m in entries if m['_vol']},
            holder_of=holder_of)
        print(f'{len(census_moved)} census records that left their part redirect to the record holding the man')
        moved_122 = redirects_122(
            old_ids=set(re.findall(r'"soldier_id": "(\d{10})"', OUT.read_text(encoding='utf-8'))) if OUT.exists() else set(),
            new_ids=present | moved_now,
            previous=json.loads(MOVED.read_text(encoding='utf-8')) if MOVED.exists() else {},
            ids_before=ids_before, holder_of=holder_of)
        print(f'{len(moved_122)} records of {CODE} that left it redirect to the record holding the man')
        for code in [CODE, *CENSUS_VOLUMES.values()]:
            path = ROOT / 'website' / 'public' / BRIGADE_CONFIGS[code]['json_file']
            write_text(path, json.dumps(parts.get(code, []), ensure_ascii=False, indent=2))
            print('Written', path)
        write_text(IDS, json.dumps(dict(sorted(ids.items())), ensure_ascii=False, indent=0))
        print('Written', IDS)
        # the unit files: their own records as they are, this script's range replaced (a unit that held men of an
        # earlier run and holds none now is written too)
        for code in sorted(set(to_units) | unit_codes()):
            path = unit_file(code)
            own = [r for r in json.loads(path.read_text(encoding='utf-8')) if not is_moved(r)]
            write_text(path, json.dumps(own + to_units.get(code, []), ensure_ascii=False, indent=2))
        print(f'Written {len(set(to_units) | unit_codes())} unit files')
        write_text(UNIT_IDS, json.dumps(dict(sorted(unit_ids.items())), ensure_ascii=False, indent=0))
        print('Written', UNIT_IDS)
        # his old address still finds him: old 122 or census ID -> his record's (website/scripts/prepare-data.ts writes
        # each into the where-files of the part that had it, and /borac/<old> answers with the new one)
        moved = {**moved_122, **census_moved, **MERGED_IDS,
                 **{r['former_ids'][0]: r['soldier_id'] for recs in to_units.values() for r in recs}}
        # an old ID goes straight to the man's record of today: a chain (old -> an ID that moved on -> today's) is followed
        # to its end, and an entry that would lead back to itself is dropped (2026-11-25, the lead's check of the live site)
        def follow(k):
            seen, v = {k}, moved[k]
            while v in moved and v not in seen:
                seen.add(v); v = moved[v]
            return None if v in seen else v
        moved = {k: t for k in moved for t in [follow(k)] if t and t != k}
        write_text(MOVED, json.dumps(moved, ensure_ascii=False, indent=0, sort_keys=True) + '\n')
        print('Written', MOVED)
        # the entries left out, with the entries on the site they go with: scripts/attach_left_out.py gives each to the
        # records that hold its man (2026-10-31: they had shown nowhere)
        ON_SITE.parent.mkdir(parents=True, exist_ok=True)
        # (through safe_write too: a run stopped here by E:'s OSError 22 leaves the files written, and run again it
        # reads its own output before normalize_all_json has cleaned it; see chosen_fathers)
        write_text(ON_SITE, json.dumps([{'entry': m['soldier_id'], 'book': f"{CENSUS}-{m['_vol']}" if m['_vol'] else m['_book'],
                                         'name': m['name'], 'with': m['_with']} for m in on_site],
                                       ensure_ascii=False, indent=0))
    else:
        import random
        random.seed(1)
        for r in random.sample([r for r in records if r.get('other_sources')], 5):
            print(json.dumps(r, ensure_ascii=False)[:500])


if __name__ == '__main__':
    main()
