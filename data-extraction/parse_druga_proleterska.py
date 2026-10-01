"""
Parser: Druga proleterska brigada (brigade code 39) — "Poginuli, umrli i nestali borci Brigade".

Source: "Druga proleterska brigada 1942-1992", the brigade's illustrated monograph (Beograd 1992), the chapter
        "Crvena nit Brigade", znaci.org/00001/55_6.pdf pages 4-8  →  website/public/pdfs/druga-proleterska.pdf
Three columns in Cyrillic, ordered by where and when the soldiers fell, not by name:
    Сутјеска                                            a campaign, in large type,
    (15. мај — 19. јун 1943)                            and its period
    Тјентиште (Сутјеска), 1. јуни.                      a place and date, in italics,
    Балаћ В. Владо, Бараш С. Марко, Бе-                 then the soldiers who fell there, run on:
    кић Перо, Беус Недељко, ...                         surname, father's initial, given name, nickname
The last campaign (Sremski front) is one list in alphabetical order, without places or dates.
Each soldier gets the place and date of his heading (death_place, death_date) and his own box on the page: the
words of his name, two boxes (pdf_rects) when the name runs on to the next line.
entry_boxes.py leaves these boxes alone (INLINE_ENTRIES).

    python data-extraction/parse_druga_proleterska.py [--test OUT.json]
    python data-extraction/parse_druga_proleterska.py --headings | --items     # what it reads, for checking
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402
from scripts import feminine_alias  # noqa: E402
from scripts.soldier_id_utils import assign_ids_to_soldiers  # noqa: E402

PDF = 'website/public/pdfs/druga-proleterska.pdf'
OUT = 'website/public/druga-proleterska-soldiers.json'
CODE = 39
# viewer x just left of each page's second and third column (a column's last word can end a few points before the next)
COLUMN_SPLITS = {1: (316, 508), 2: (324, 516), 3: (332, 524), 4: (316, 512), 5: (324, 520)}

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
MONTH = (r'(?:j[ae][npi]u?ar\w*|februar\w*|mart\w*|april\w*|maj\w*|ju[npi][aiu]\w*|jul\w*|avgust\w*|'
         r'septemb\w*|oktob\w*|[np]ovemb\w*|decemb\w*)')
# the end of a place-and-date heading: "..., 1. juni.", "..., 21—25 maja.", "..., 2. i 3. juni.", "..., krajem marta 1944."
DATE_END = re.compile(rf'(?:,|\)|\.|H)\s*((?:krajem\s+|kraj\s+|sredi[npi]a\s+|polovi[npi]a\s+)?'
                      rf'(?:\d{{1,2}}\.?\s*(?:[—–-]\s*\d{{1,2}}\.?|i\s+\d{{1,2}}\.)?\s*)?{MONTH},?(?:\s*19\d\d)?)\.$', re.I)
DATELESS_END = {'Sutjeske.'}     # "Nastradali i umrli u centralnoj bolnici od Pive do Sutjeske."
LINE_FIXES = {'Bondžulić Milorad': 'Bondžulić Milorad.'}    # the period the text layer lost before a heading

SECTIONS = {
    # printed campaign heading: (its name on the site, its period, the year of its dates)
    'Sutjeska': ('bitka na Sutjesci', '15. maj — 19. jun 1943', 1943),
    'Istočna Bosna': ('istočna Bosna', '24. jun — 31. avgust 1943', 1943),
    'Pljevlja, Prijepolje': ('Pljevlja, Prijepolje', '27. septembar — 5. decembar 1943', 1943),
    'Zapadna Srbija': ('zapadna Srbija', '23. decembar 1943 — 30. maj 1944', 1944),
    'Sremski front': ('Sremski front', '2. novembar 1944 — 15. april 1945', None),
}

# Each place-and-date heading as the text layer reads it (italic н comes out as п or и, and so on) → as printed,
# and the place to give as death_place. Names checked against the other books' bios: Miljevina (Foča — Kalinovik
# road), Gornje Bare, Sokolica (Prijepolje), Mravinci (Valjevo), Mazline (Jahorina).
HEADINGS = {
    'Kod Foče, sredipa maja.': ('Kod Foče, sredina maja.', 'kod Foče'),
    'Rudiie (pl. Piva), polovipa maja.': ('Rudine (pl. Piva), polovina maja.', 'Rudine'),
    'Crii Vrh (kod Foče), 16. maj.': ('Crni Vrh (kod Foče), 16. maj.', 'Crni Vrh'),
    'Kruščica (kod Foče), 18. maj.': ('Kruščica (kod Foče), 18. maj.', 'Kruščica'),
    'Crna Gora, 19. maj.': ('Crna Gora, 19. maj.', 'Crna Gora'),
    'Pliješ (kod Foče), 19. maj.': ('Pliješ (kod Foče), 19. maj.', 'Pliješ'),
    'Zlatpi Bor (kod Foče), 20. maj.': ('Zlatni Bor (kod Foče), 20. maj.', 'Zlatni Bor'),
    'Mazoče (kod Foče), 20. maj.': ('Mazoče (kod Foče), 20. maj.', 'Mazoče'),
    'Žabljak, 20. maj.': ('Žabljak, 20. maj.', 'Žabljak'),
    'Šćepap polje, 21—25 maja.': ('Šćepan Polje, 21—25. maja.', 'Šćepan Polje'),
    'Vikoč, 22. maj.': ('Vikoč, 22. maj.', 'Vikoč'),
    'Kruševo (pa Pivi), 23—25. maja.': ('Kruševo (na Pivi), 23—25. maja.', 'Kruševo'),
    'Vučevo, 26—31. maja.': ('Vučevo, 26—31. maja.', 'Vučevo'),
    'Dragoš Sedlo (između Vučeva i dolipe Sutjeske), 26—31. maja.':
        ('Dragoš Sedlo (između Vučeva i doline Sutjeske), 26—31. maja.', 'Dragoš Sedlo'),
    'Đurevo (dolipa Sutjeske), 26—31. maja.': ('Đurevo (dolina Sutjeske), 26—31. maja.', 'Đurevo'),
    'Suha (u kanjopu Sutjeske), 26—30. maja.': ('Suha (u kanjonu Sutjeske), 26—30. maja.', 'Suha'),
    'Zavajit, maj.': ('Zavajit, maj.', 'Zavajit'),
    'Kod Foče, kraj maja.': ('Kod Foče, kraj maja.', 'kod Foče'),
    'Borovpa (više Sutjeske), 1. jupi.': ('Borovna (više Sutjeske), 1. juni.', 'Borovna'),
    'Tjeptište (Sutjeska), 1. jupi.': ('Tjentište (Sutjeska), 1. juni.', 'Tjentište'),
    'Dolipa Sutjeske, 1—9. jupa.': ('Dolina Sutjeske, 1—9. juna.', 'dolina Sutjeske'),
    'Gori e Bare (izpad kanjopa Sutjeske), 2. i 3. jupi.':
        ('Gornje Bare (iznad kanjona Sutjeske), 2. i 3. juni.', 'Gornje Bare'),
    'Košur, 3—8. jupa.': ('Košur, 3—8. juna.', 'Košur'),
    'Rudipe (pl. Piva), 5. jupi.': ('Rudine (pl. Piva), 5. juni.', 'Rudine'),
    'Vrbpica (selo blizu r. Sutjeske), 8. jupi.': ('Vrbnica (selo blizu r. Sutjeske), 8. juni.', 'Vrbnica'),
    'Milipklade (između Sutjeske i Lučkih koliba), 8—9. jupa.':
        ('Milinklade (između Sutjeske i Lučkih koliba), 8—9. juna.', 'Milinklade'),
    'Hrčavka (kanjoi), 9. jupi.': ('Hrčavka (kanjon), 9. juni.', 'Hrčavka'),
    'Mala Košuta, 10. jupi.': ('Mala Košuta, 10. juni.', 'Mala Košuta'),
    'Lučke kolibe, 10—11. Jupa.': ('Lučke kolibe, 10—11. juna.', 'Lučke kolibe'),
    'Stružipsko Brdo (Zelepgora), 11. jupi.': ('Stružinsko Brdo (Zelengora), 11. juni.', 'Stružinsko Brdo'),
    'Od Vrbpičke reke do katupa Retkovac (proboj prvog isprija telj skog obruča), 11. jupi.':
        ('Od Vrbničke reke do katuna Retkovac (proboj prvog neprijateljskog obruča), 11. juni.',
         'od Vrbničke reke do katuna Retkovac'),
    'Zakmur (selo između Foče i Sutjesks), 12. jupi.': ('Zakmur (selo između Foče i Sutjeske), 12. juni.', 'Zakmur'),
    'Milsvtš (iroboj drugog isprijateljskog obruča pa putu Foča — Kalipovpik), 13. juii.':
        ('Miljevina (proboj drugog neprijateljskog obruča na putu Foča — Kalinovik), 13. juni.', 'Miljevina'),
    'Pogipuli i pestali u bici, jupa.': ('Poginuli i nestali u bici, juna.', ''),
    'Nastradali i umrli u ceptralpoj bolpici od Pive do Sutjeske.':
        ('Nastradali i umrli u centralnoj bolnici od Pive do Sutjeske.', 'centralna bolnica (od Pive do Sutjeske)'),
    'Proboj ia komušpsaciji Sarajevo — Višegrad, 17—19. jupa.':
        ('Proboj na komunikaciji Sarajevo — Višegrad, 17—19. juna.', 'komunikacija Sarajevo — Višegrad'),
    '— Podgrab, 17. juni.': ('Podgrab (proboj na komunikaciji Sarajevo — Višegrad), 17. juni.', 'Podgrab'),
    '— Stambolčić, 17. juni.': ('Stambolčić (proboj na komunikaciji Sarajevo — Višegrad), 17. juni.', 'Stambolčić'),
    '— Vitez, 18. juni.': ('Vitez (proboj na komunikaciji Sarajevo — Višegrad), 18. juni.', 'Vitez'),
    '— Krčava (selo ispod Romanije), 19. juni.': ('Krčava (selo ispod Romanije), 19. juni.', 'Krčava'),

    'Olovo, 24. jupi 1943.': ('Olovo, 24. juni 1943.', 'Olovo'),
    'Kladln , 28. jupi.': ('Kladanj, 28. juni.', 'Kladanj'),
    'Šahići, Berići, Brkica, Đedipa, 5. juli.': ('Šahići, Berići, Brkica, Đedina, 5. juli.', 'Šahići, Berići, Brkica, Đedina'),
    'Omazići (zaselak Beširovići, blizu Živipica), 7. juli.':
        ('Omazići (zaselak Beširovići, blizu Živinica), 7. juli.', 'Omazići'),
    'Poljice (između Ozrepa i dolipe Spreče), 10. juli.': ('Poljice (između Ozrena i doline Spreče), 10. juli.', 'Poljice'),
    'Đurđevik (ispod Kon uh - plapipe), 17. juli.': ('Đurđevik (ispod Konjuh-planine), 17. juli.', 'Đurđevik'),
    'Tumare (pa Ozrepu, istočpa Bospa), 19. juli.': ('Tumare (na Ozrenu, istočna Bosna), 19. juli.', 'Tumare'),
    'Gradišpik, Jelova Gorica (više Ozrep-mapastira), 20. juli.':
        ('Gradišnik, Jelova Gorica (više Ozren-manastira), 20. juli.', 'Gradišnik, Jelova Gorica'),
    'Omerove vode (pa Ozrepu, istočpa Bosia), 22. juli.': ('Omerove vode (na Ozrenu, istočna Bosna), 22. juli.', 'Omerove vode'),
    'Pod Kmuhom, 26. juli.': ('Pod Konjuhom, 26. juli.', 'pod Konjuhom'),
    'Šekovići (pogipuli u bolpici ispod Majevice), juli.': ('Šekovići (poginuli u bolnici ispod Majevice), juli.', 'Šekovići'),
    'Ribiica (doliia Krivaje), 10. avgust.': ('Ribnica (dolina Krivaje), 10. avgust.', 'Ribnica'),
    'U doliii reke Spreče, avgust.': ('U dolini reke Spreče, avgust.', 'dolina reke Spreče'),
    'Carev Haš — Ćuprija (dolipa Krivaje), 21. avgust.': ('Carev Han — Ćuprija (dolina Krivaje), 21. avgust.', 'Carev Han — Ćuprija'),
    'Željava (selo pod Konjuhom), avgust.': ('Željava (selo pod Konjuhom), avgust.', 'Željava'),
    'Pohovac (blizu Sokolca). 24. avgust.': ('Pohovac (blizu Sokolca), 24. avgust.', 'Pohovac'),
    'Bijela Voda (pa Romapiji), 24. avgust.': ('Bijela Voda (na Romaniji), 24. avgust.', 'Bijela Voda'),
    'Jabuka (ia Jahoripi), avgust.': ('Jabuka (na Jahorini), avgust.', 'Jabuka'),
    'Mazlipe (Jahoripa), avgust.': ('Mazline (Jahorina), avgust.', 'Mazline'),
    'Foča, avgust.': ('Foča, avgust.', 'Foča'),
    'Kod Ustikolipe (pa Dripi blizu Goražda), avgust.': ('Kod Ustikoline (na Drini blizu Goražda), avgust.', 'kod Ustikoline'),

    'Meljak (kod Pljevalja), septembar.': ('Meljak (kod Pljevalja), septembar.', 'Meljak'),
    'Jabuka (Pljevlja — Prijepalje), 27. septembar.': ('Jabuka (Pljevlja — Prijepolje), 27. septembar.', 'Jabuka'),
    'Ljubiš (Smipapića brdo pa Zlatiboru), 6. oktobar.': ('Ljubiš (Smiljanića brdo na Zlatiboru), 6. oktobar.', 'Ljubiš'),
    'Ustibar (Priboj), 21. oktobar.': ('Ustibar (Priboj), 21. oktobar.', 'Ustibar'),
    'Priboj, 29. oktobar.': ('Priboj, 29. oktobar.', 'Priboj'),
    'Ursule (Sjepica), 3. povembar.': ('Ursule (Sjenica), 3. novembar.', 'Ursule'),
    'Haiipovići (Sjepica), povembar.': ('Haiipovići (Sjenica), novembar.', 'Haiipovići'),
    'Prijepolje (pepozpato mesto pogibije), 4. decembar.': ('Prijepolje (nepoznato mesto pogibije), 4. decembar.', 'Prijepolje'),
    'Sokolpca (više Prijelolja), 4. decembar.': ('Sokolica (više Prijepolja), 4. decembar.', 'Sokolica'),
    'Lim (utopili se u Limu), 4. decembar.': ('Lim (utopili se u Limu), 4. decembar.', 'Lim'),
    'Gradipa (položaj pa levoj obali Lima), 4. decembar.': ('Gradina (položaj na levoj obali Lima), 4. decembar.', 'Gradina'),
    'Mioska (i ostali položaji pa levoj obali Lima), 4. decembar.':
        ('Mioska (i ostali položaji na levoj obali Lima), 4. decembar.', 'Mioska'),
    'Jabuka (Prijepolje — Pljevl,a), 5. decembar.': ('Jabuka (Prijepolje — Pljevlja), 5. decembar.', 'Jabuka'),
    'Plevlja, 5. decembar.': ('Pljevlja, 5. decembar.', 'Pljevlja'),

    'Rudo (pa Lpmu), decembar, 1943.': ('Rudo (na Limu), decembar 1943.', 'Rudo'),
    'Brezovac (kod sela Jablappce pa ZlatiboruH 23. decembar.':
        ('Brezovac (kod sela Jablanice na Zlatiboru), 23. decembar.', 'Brezovac'),
    'Ivanjica, 9. japuar 1944.': ('Ivanjica, 9. januar 1944.', 'Ivanjica'),
    'Katići (selo između Ivškice i Arilja), 16. japuar.': ('Katići (selo između Ivanjice i Arilja), 16. januar.', 'Katići'),
    'Bela Glava (G. Jablašca ia Zlatiboru), 21. jaiuar.': ('Bela Glava (G. Jablanica na Zlatiboru), 21. januar.', 'Bela Glava'),
    'Bijela Brda (pa komuiikaciji Priboj — Dobrui), 21. mart.':
        ('Bijela Brda (na komunikaciji Priboj — Dobrun), 21. mart.', 'Bijela Brda'),
    'Štrpci (ia komuiikaciji Priboj — Bijela Brda), 22. mart.':
        ('Štrpci (na komunikaciji Priboj — Bijela Brda), 22. mart.', 'Štrpci'),
    'Radal evo (kod Ivakice), krajem marta 1944.': ('Radaljevo (kod Ivanjice), krajem marta 1944.', 'Radaljevo'),
    'Čečiia (Vioiica kod pl. Golije), 1. april.': ('Čečina (Vionica kod pl. Golije), 1. april.', 'Čečina'),
    'Vrmbaje (Pridvorica, doliia Studeiice), 4. april.': ('Vrmbaje (Pridvorica, dolina Studenice), 4. april.', 'Vrmbaje'),
    'Gorjapi — Uzići (ia pruzi Požega — Užice), 29. april.':
        ('Gorjani — Uzići (na pruzi Požega — Užice), 29. april.', 'Gorjani — Uzići'),
    'Kaoia (Dragačevo), 8. april.': ('Kaona (Dragačevo), 8. april.', 'Kaona'),
    'Kušići (Pva^ica), 24. april.': ('Kušići (Ivanjica), 24. april.', 'Kušići'),
    'Brezova (kod Ivanjice), april.': ('Brezova (kod Ivanjice), april.', 'Brezova'),
    'Grivska (kod Arilja), krajem aprila.': ('Grivska (kod Arilja), krajem aprila.', 'Grivska'),
    'Mravšci (Valjevo), 1. i 2. maj.': ('Mravinci (Valjevo), 1. i 2. maj.', 'Mravinci'),
    'Bukovi (Kosjerić — Vagkevo), 2. maj.': ('Bukovi (Kosjerić — Valjevo), 2. maj.', 'Bukovi'),
    'Varda (Kosjerići), maj.': ('Varda (Kosjerići), maj.', 'Varda'),
    'Tara plapipa, maj.': ('Tara planina, maj.', 'Tara'),
    'Veliki Krš (između Prijepolja i Sjeiice), 19. maj.': ('Veliki Krš (između Prijepolja i Sjenice), 19. maj.', 'Veliki Krš'),
    'Kladpica (Sjeiica), maj.': ('Kladnica (Sjenica), maj.', 'Kladnica'),
    'Štitkovo (Sapdžak), 19. maj.': ('Štitkovo (Sandžak), 19. maj.', 'Štitkovo'),
    'Mojkovac (Crpa Gora), 30. maj.': ('Mojkovac (Crna Gora), 30. maj.', 'Mojkovac'),
}
# Headings that say how they died: (the man's words, the woman's, death_type); the others list the fallen
FATES = {
    'Poginuli i nestali u bici, juna.': ('poginuo ili nestao u bici', 'poginula ili nestala u bici', ''),
    'Nastradali i umrli u centralnoj bolnici od Pive do Sutjeske.':
        ('nastradao ili umro u centralnoj bolnici od Pive do Sutjeske',
         'nastradala ili umrla u centralnoj bolnici od Pive do Sutjeske', ''),
    'Lim (utopili se u Limu), 4. decembar.': ('utopio se u Limu', 'utopila se u Limu', ''),
}
GENITIVE = {'januar': 'januara', 'februar': 'februara', 'mart': 'marta', 'april': 'aprila', 'maj': 'maja',
            'jun': 'juna', 'juni': 'juna', 'juna': 'juna', 'juli': 'jula', 'jul': 'jula', 'avgust': 'avgusta',
            'septembar': 'septembra', 'oktobar': 'oktobra', 'novembar': 'novembra', 'decembar': 'decembra',
            'maja': 'maja', 'marta': 'marta', 'aprila': 'aprila'}
MONTHS_GENITIVE = ['januara', 'februara', 'marta', 'aprila', 'maja', 'juna', 'jula', 'avgusta', 'septembra',
                   'oktobra', 'novembra', 'decembra']
QUALIFIER = {'kraj': 'krajem', 'krajem': 'krajem', 'sredina': 'sredinom', 'polovina': 'polovinom'}
# Words the text layer garbled in the names: a Cyrillic letter read as another (З as 3, Љ as JB, и as ш, н as п),
# told by the names the list prints elsewhere and by its alphabetical order under each heading ("Manšć" stands
# between Milivojević and Milošević: Milić)
WORD_FIXES = {
    '3': 'Z', '0': 'O', 'JT': 'L', 'JBuboja': 'Ljuboja', 'JBubomir': 'Ljubomir', 'Lubora': 'Ljuboja',
    'Apdrija': 'Andrija', 'Aleksacdar': 'Aleksandar', 'Trnfunovnć': 'Trifunović', 'Grkššć': 'Grkinić',
    'Glipšć': 'Glišić', 'Gapšć': 'Gašić', 'Rapšć': 'Rašić', 'Manšć': 'Milić', 'Jurij': 'Jurić', 'Kisa': 'Kiso',
    'Martiznić': 'Martinić', 'Milošsvić': 'Milošević', 'Driičić': 'Drinčić', 'Maripković': 'Marinković',
    'Ekmepgšć': 'Ekmeščić', 'Kupšć': 'Kušić', 'Vlasgimir': 'Vlastimir', 'Đilerdžić': 'Ćilerdžić',
    'Kujuncić': 'Kujundžić', 'Samarcić': 'Samardžić', 'Hacić': 'Hadžić',             # џ read as ц
}
# Names the list runs together or prints in another order
NAME_TEXT_FIXES = {
    'Čeliković Milosavljević N. Dušan': 'Čeliković-Milosavljević N. Dušan',    # "Čeliković Milosav-/ljević"
    'Ječmenić Ječmenica Dušan': 'Ječmenić Dušan Ječmenica',
}
# A name printed alone that is a given name, not a surname ("Anka (Dalmatinka)")
GIVEN_ALONE = {'Anka', 'Jure', 'Đura', 'Nura', 'Radoica'}
# Whose given name says the wrong gender: Raša, Slaviša and Rajica are men's names, Vuka "Vukica" a woman's
MEN = {'Đurđić Raša', 'Faruka Mandžuka', 'Gačanović Slaviša', 'Matić Rajica', 'Obradović Rajica'}
WOMEN = {'Drljača Vuka'}
HEADING_DATE = re.compile(r',\s*(?:(kraj|krajem|sredina|polovina)\s+)?(?:(\d{1,2}(?:—\d{1,2}|\. i \d{1,2})?)\.?\s+)?'
                          r'([a-z]+)(?:,?\s*(19\d\d))?\.$')


def column(w: dict) -> int:
    return sum(w['x0'] >= s for s in COLUMN_SPLITS[w['page']])


def read_lines(pdf_path: str) -> list[dict]:
    """The list's lines in reading order (page, column, top): {page, col, words, text}, plus {section} markers."""
    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn, page in enumerate(pdf.pages, 1):
            words = [w for w in viewer_words(page, extra_attrs=['fontname', 'size']) if w['text'] not in ('_', '^')]
            for w in words:
                w['text'] = cyrillic_to_latin(w['text'])
                w['page'] = pn
                w['col'] = column(w)
            cols: dict[int, list[list[dict]]] = {0: [], 1: [], 2: []}
            for w in sorted(words, key=lambda w: (w['col'], w['top'], w['x0'])):
                lines = cols[w['col']]
                if lines and abs(lines[-1][0]['top'] - w['top']) < 4:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            for c in (0, 1, 2):
                stop = False
                for ws in cols[c]:
                    ws.sort(key=lambda w: w['x0'])
                    text = ' '.join(w['text'] for w in ws)
                    size = max(w['size'] for w in ws)
                    if stop:
                        continue
                    if size >= 15:
                        if text in SECTIONS:
                            out.append({'section': text, 'page': pn, 'col': c})
                        continue                                 # the list's title, page numbers
                    if size > 20 or (pn == 3 and c == 1 and size < 9):
                        continue                                 # "Ratni sastav Brigade": the brigade in numbers
                    if text == '*' or text.startswith('obeležja:'):
                        stop = text == '*'                       # the sources after the list; a photo caption
                        continue
                    out.append({'page': pn, 'col': c, 'words': ws, 'text': text})
    # a campaign's period, in parentheses after its name
    keep, skipping = [], False
    for ln in out:
        if 'section' in ln:
            skipping = True
        elif skipping and (ln['text'].startswith('(') or not keep[-1].get('closed', True)):
            closed = ')' in ln['text']
            keep[-1]['closed'] = closed
            skipping = not closed
            continue
        else:
            skipping = False
        keep.append(ln)
    return keep


def mark_headings(lines: list[dict]) -> None:
    """Mark each place-and-date heading's lines: the heading ends at a line ending in a date, and starts after the
    last line that ends in a period (the end of the list above it)."""
    for i, ln in enumerate(lines):
        if 'section' in ln:
            continue
        text = LINE_FIXES.get(ln['text'], ln['text'])
        ln['text'] = text
        prev = lines[i - 1] if i else None
        j = i
        if not (DATE_END.search(text) or text in DATELESS_END):
            # the date starts on the line above: "8. ju-" + "ni.", "..., 19." + "juni.", "krajem" + "marta 1944."
            if not (prev and 'words' in prev and not prev.get('heading')
                    and DATE_END.search(join_text([prev['text'], text]))):
                continue
            j = i - 1
        while j > 0 and 'words' in lines[j - 1] and not lines[j - 1]['text'].endswith('.') \
                and not lines[j - 1].get('heading'):
            j -= 1
        raw = join_text([lines[k]['text'] for k in range(j, i + 1)])
        for k in range(j, i + 1):
            lines[k]['heading'] = raw
        lines[j]['heading_start'] = True


def join_text(parts: list[str]) -> str:
    text = ''
    for p in parts:
        if text.endswith('-') and not text.endswith(' -'):
            text = text[:-1] + p
        else:
            text = (text + ' ' + p).strip()
    return text


def heading_parts(clean: str, section: str) -> tuple[str, str]:
    """A heading as printed → the place as printed ("Tjentište (Sutjeska)") and the date ("1. juna 1943")."""
    m = HEADING_DATE.search(clean)
    if not m:                                                # the central hospital: no date
        return clean.rstrip('.'), ''
    qualifier, days, month, year = m.groups()
    if not year:
        year = SECTIONS[section][2]
        if section == 'Zapadna Srbija' and month.startswith('decemb'):
            year = 1943
    date = ' '.join(p for p in (QUALIFIER.get(qualifier or ''), f'{days}.' if days else '', GENITIVE[month], str(year)) if p)
    return clean[:m.start()], date


INITIAL = re.compile(rf'^(?:[{U}]|Lj|Nj|Dž)\.?$')


def list_tokens(lines: list[dict]) -> list[dict]:
    """The names' words in reading order, each with its section and heading; a word broken at a line end ("Be-" +
    "kić") is one token of two words."""
    toks, section, heading = [], None, None
    for ln in lines:
        if 'section' in ln:
            section, heading = ln['section'], None
            toks.append({'boundary': True})
            continue
        if ln.get('heading'):
            if ln.get('heading_start'):
                assert ln['heading'] in HEADINGS, f"unknown heading: {ln['heading']!r}"
                heading = HEADINGS[ln['heading']]
                toks.append({'boundary': True})
            continue
        for k, w in enumerate(ln['words']):
            prev = toks[-1] if toks else None
            if (k == 0 and prev and not prev.get('boundary') and prev['line_end'] and prev['text'].endswith('-')
                    and len(prev['text']) > 1):
                prev['text'] = (prev['text'][:-1] if w['text'][:1].islower() else prev['text']) + w['text']
                prev['words'].append(w)
                prev['line_end'] = len(ln['words']) == 1
                continue
            core = w['text'].rstrip(',.')
            text = WORD_FIXES.get(core, core) + w['text'][len(core):]
            toks.append({'text': text, 'words': [w], 'section': section, 'heading': heading,
                         'line_end': k == len(ln['words']) - 1})
    return toks


def split_items(toks: list[dict]) -> list[list[dict]]:
    """Cut the run-on names at their commas and periods (not inside parentheses, nor after a father's initial).
    "Žarko N." ends at its N. (surname unknown) when a whole name follows: "Reco N. Rovčanin Milomir"."""
    items, cur, depth = [], [], 0
    for k, t in enumerate(toks):
        if t.get('boundary'):
            if cur:
                items.append(cur)
            cur, depth = [], 0
            continue
        cur.append(t)
        depth = max(0, depth + t['text'].count('(') - t['text'].count(')'))
        text = t['text']
        if depth or not text.endswith((',', '.')):
            continue
        if text.endswith('.') and INITIAL.match(text) and text != '(':
            if text != 'N.' or len(cur) != 2:
                continue
            nxt = []
            for u in toks[k + 1:]:
                if u.get('boundary'):
                    break
                nxt.append(u)
                if u['text'].endswith(',') or (u['text'].endswith('.') and not INITIAL.match(u['text'])):
                    break
            if len(nxt) < 2:
                continue
        items.append(cur)
        cur = []
    if cur:
        items.append(cur)
    merged = []
    for it in items:                                     # "Ninković S. Jovo, (28. 05)": a note of the name before
        if merged and not re.sub(r'\([^)]*\)|[\s,.]', '', ' '.join(t['text'] for t in it)):
            merged[-1] = merged[-1] + it
        else:
            merged.append(it)
    return merged


def boxes(words: list[dict]) -> dict:
    """The entry's place on its page: its first word, and the box (or boxes, when the name runs on to the next line or
    column) around its words."""
    page = words[0]['page']
    segs: list[list[dict]] = []
    for w in words:
        if w['page'] != page:
            break                                        # the rest is on the next page
        if segs and segs[-1][-1]['col'] == w['col'] and abs(segs[-1][-1]['top'] - w['top']) < 4:
            segs[-1].append(w)
        else:
            segs.append([w])
    rects = [[round(min(w['x0'] for w in s), 1), round(min(w['top'] for w in s), 1),
              round(max(w['x1'] for w in s), 1), round(max(w['bottom'] for w in s), 1)] for s in segs]
    out = {'pdf_file': Path(PDF).name, 'pdf_page': page, 'pdf_x': rects[0][0], 'pdf_y': rects[0][1],
           'pdf_x_end': max(r[2] for r in rects), 'pdf_y_end': max(r[3] for r in rects)}
    left = min(r[0] for r in rects)
    if left < rects[0][0]:
        out['pdf_x_left'] = left
    if len(rects) > 1:
        out['pdf_rects'] = rects
    return out


NOTES = {
    'zar. ital. lekar': 'zarobljeni italijanski lekar',
}


def parse_item(text: str) -> dict:
    """"Surname [F.] Given [Nickname] [(note)]" → name fields, the notes, and what a note says of birth or death."""
    out = {'notes': [], 'born': '', 'died_at': '', 'died_on': ''}
    for note in re.findall(r'\(([^)]*)\)', text):
        note = note.strip()
        born = re.fullmatch(r'(?:r\. )?(1[89]\d\d)', note)          # "(r. 1905)", "(1920)": two men of one name
        day = re.fullmatch(r'(\d{1,2})\. ?(\d{1,2})', note)         # "(28. 05)": the day he fell
        if born:
            out['born'] = born.group(1)
            out['notes'].append(f'rođen {born.group(1)}')
        elif day:
            out['died_on'] = (int(day.group(1)), int(day.group(2)))
        elif note == 'V. Košuta':                                   # fell at Velika, not Mala Košuta
            out['died_at'] = 'Velika Košuta'
        else:
            out['notes'].append(NOTES.get(note, note))
    name = re.sub(r'\s*\([^)]*\)?', '', text).strip(' ,.')
    name = re.sub(rf'(?<=[{L}])\s*[-—–]\s*(?=[{U}])', '-', name)      # "Đulić - Mladenović" → "Đulić-Mladenović"
    name = NAME_TEXT_FIXES.get(name, name)
    words = [WORD_FIXES.get(w, w) for w in name.split()]
    last = father = given = ''
    nick = []
    if name == 'Mali pekar':                                        # "the little baker": known only so
        last = name
    elif len(words) == 2 and words[1] in ('N', 'N.'):                 # "Hasan N", "Žarko N.": surname unknown
        given = words[0]
    elif len(words) == 1:                                           # "Anka (Dalmatinka)", "Magovac (Ličanin)"
        if words[0] in GIVEN_ALONE:
            given = words[0]
        else:
            last = words[0]
    else:
        last, rest = words[0], words[1:]
        if len(rest) >= 2 and INITIAL.match(rest[0]):
            father = rest.pop(0).rstrip('.')
        given, nick = rest[0], rest[1:]
    if nick:
        out['notes'].insert(0, 'zvani ' + ' '.join(nick))
    out.update(last=last, father=father, given=given)
    return out


def build_record(item: list[dict], women: set, men: set) -> dict | None:
    text = ' '.join(t['text'] for t in item)
    p = parse_item(text)
    if not (p['last'] or p['given']):
        return None
    section = item[0]['section']
    heading = item[0]['heading']
    sec_name, period, _ = SECTIONS[section]
    key = ' '.join(x for x in (p['last'], p['father'], p['given']) if x)
    woman = key in WOMEN or (key not in MEN and p['given'] and feminine_alias.is_woman(
        {'soldier_id': '', 'first_name': p['given'], 'additional_info': ''}, women, men))
    if heading:
        clean, place = heading
        place_text, date = heading_parts(clean, section)
        if p['died_on']:                                     # "(28. 05)" under "Dolina Sutjeske, 1—9. juna"
            day, month = p['died_on']
            date = f'{day}. {MONTHS_GENITIVE[month - 1]} {date.split()[-1]}'
        man_word, woman_word, death_type = FATES.get(clean, ('poginuo', 'poginula', 'poginuo'))
        fate = woman_word if woman else man_word
        if clean in FATES:
            said = ' '.join(x for x in (fate, date) if x)
        else:
            said = f'{fate} {date}, {place_text}'
        said += f'; {section} ({period})'
    else:                                                    # Sremski front: one list, no places or dates
        place, date, death_type = 'Sremski front', '', 'poginuo'
        said = f"{'poginula' if woman else 'poginuo'} na Sremskom frontu ({period})"
    if p['died_at']:
        place = p['died_at']
        said = said.replace(', Mala Košuta;', ', Velika Košuta;')
    info = '; '.join(p['notes'] + [said])
    rec = {
        'last_name': p['last'],
        'middle_name': p['father'],
        'first_name': p['given'],
        'fathers_name': p['father'],
        'full_name': ' '.join(x for x in (p['last'], p['father'], p['given']) if x),
        'additional_info': info,
        'birth_year': p['born'],
    }
    if place:
        rec['death_place'] = place
    if date:
        rec['death_date'] = date
    if death_type:
        rec['death_type'] = death_type
    rec.update(boxes([w for t in item for w in t['words']]))
    return rec


def corpus_genders() -> tuple[set, set]:
    soldiers = []
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != Path(OUT).name:
            soldiers.extend(json.loads(f.read_text(encoding='utf-8')))
    return feminine_alias.name_genders(soldiers)


def main():
    lines = read_lines(PDF)
    mark_headings(lines)
    if '--headings' in sys.argv:
        seen = set()
        for ln in lines:
            if 'section' in ln:
                print('### SECTION', ln['section'], ln['page'], ln['col'])
            elif ln.get('heading') and ln['heading'] not in seen:
                seen.add(ln['heading'])
                print(f"  H p{ln['page']} c{ln['col']}: {ln['heading']}")
            elif not ln.get('heading'):
                print(f"      p{ln['page']} c{ln['col']} {ln['text']}")
        return
    items = split_items(list_tokens(lines))
    women, men = corpus_genders()
    soldiers = [r for r in (build_record(it, women, men) for it in items) if r]
    if '--items' in sys.argv:
        for r in soldiers:
            print(f"{r['pdf_page']} {r['full_name']:40} | {r.get('death_place', ''):25} | {r.get('death_date', ''):18} | "
                  f"{r['additional_info'][:70]}")
        return
    soldiers.sort(key=lambda s: (s['last_name'].lower(), s['first_name'].lower()))
    assign_ids_to_soldiers(soldiers, CODE)
    out = sys.argv[sys.argv.index('--test') + 1] if '--test' in sys.argv else OUT
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)
    print(f'[{CODE}] {len(soldiers)} soldiers → {out}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
