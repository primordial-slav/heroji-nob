"""
Житорађе кроз историју (Poreklo library, doc 00005907): the fighters of Žitorađe by Vladičin Han and those who fell
freeing it in 1944, as a book across units. Cyrillic. Lists:
  - "Учесници НОР-а из Житорађа" (scan p. 88): 69 names run on, "Surname Father Given", which the book counts as
    fighters ("Укупно 69 бораца"), and "Учесници НОР-а досељеници", six more; a nickname after the given name
    ("Младеновић Милана Драгољуб Дупљанац") or the father's ("Цветковић Драгутина Џека Љубомир");
  - "Рањени житорађански борци у НОБ" (pp. 88-89): six of them, numbered, the unit and the wound, joined to their
    names; the woman wounded by a shell at her father-in-law's mill is no fighter and stays out;
  - "Погинули борци из Житорађа у НОБ" (pp. 89-90): three of them, joined to their names;
  - "Погинули борци српских бригада у Житорађу приликом ослобођења села" (pp. 91-93): fifteen men of the 8. srpska,
    the 25. srpska and the 1. surdulička brigade, killed driving the German batteries out in September and October
    1944, under each brigade's heading.
The last three are typed from the OCR (`WOUNDED`, `FALLEN`, `LIBERATORS`), whose lines the page's photographs and
captions scatter. Out: "Жртве фашистичког терора у Житорађу" (pp. 90-91: a sergeant of the old army killed in 1943 and
two women hit by shells), the Balkan wars and the First World War (p. 57).

Output: data-extraction/poreklo/zitoradje-entries.json, IDs 9087xxxxxx: the 69 9087000001-069, the settlers
9087000101-106, the liberators 9087000201-215.
Usage: python data-extraction/parse_zitoradje.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
import parse_trebinjci_pali as T  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'zitoradje.json'
OUT = HERE / 'poreklo' / 'zitoradje-entries.json'
PREFIX = '9087'
OFFSET = 2                                  # scan page minus the book's page
TITLE = 'Žitorađe kroz istoriju'
VILLAGE = 'Žitorađe, Vladičin Han'
PARTICIPANTS = 'Učesnici NOR-a iz Žitorađa'
SETTLERS = 'Učesnici NOR-a doseljenici'
WOUNDED_LIST = 'Ranjeni žitorađanski borci u NOB'
FALLEN_LIST = 'Poginuli borci iz Žitorađa u NOB'
LIBERATORS_LIST = 'Poginuli borci srpskih brigada u Žitorađu prilikom oslobođenja sela i isterivanja nemačkih baterija'
# (surname, father, given) of a man of the 69 -> his text in the list of the wounded (scan p. 88-89), and his unit
WOUNDED = {('Kostić', 'Anđelka', 'Stamen'): ('borac 10. srpske brigade 22. divizije. Ranjen u desnu ruku na Lipovici kod '
                                             'Vlasotinca, u borbi protiv četnika 6. septembra 1944. godine.', [88], 88),
           ('Mladenović', 'Vojislava', 'Dragoljub'): ('borac mitraljeske čete 3. bataljona 8. srpske brigade 22. divizije. '
                                                      'Ranjen lakše na tri mesta, u borbama na Bosutu, prilikom proboja '
                                                      'Sremskog fronta sredinom aprila 1945. godine.', [87], 88),
           ('Ničić', 'Đorđa', 'Borivoje'): ('borac 3. čete 4. bataljona 27. srpske brigade 46. srpske divizije. Ranjen u '
                                            'butinu desne noge na Čestelinu 3. avgusta 1944. godine u borbama protiv '
                                            'albanskih balista.', [], 89),
           ('Stanković', 'Sente', 'Gradimir'): ('borac 3. čete 3. bataljona 26. brigade 46. srpske divizije. Ranjen u '
                                                'mišić desne noge u borbama protiv balista na zvanom mestu Čestelin.', [], 89),
           ('Stanković', 'Petra', 'Veličko'): ('borac 4. krajiške brigade 5. divizije. Ranjen 20. aprila 1945. godine u '
                                               'borbi protiv Nemaca za oslobođenje Slavonske Požege.', [11], 89),
           ('Cvetković', 'Dragutina', 'Stanko'): ('borac 3. bataljona 10. srpske brigade, 22. divizije, ranjen s jeseni '
                                                  '1944. godine u borbama sa Nemcima za oslobođenje Vlasotinca.', [88], 89)}
# the village's fallen (pp. 89-90), all of the 69
FALLEN = {('Ničić', 'Đorđa', 'Stanko'): ('NIČIĆ ĐORĐA STANKO, borac I čete, II bataljona, XXVI srpske brigade 46. divizije. '
                                         'Poginuo na položaju na zv. mestu Uši, kod Gornjeg Vrtogoša – Vranje u borbi '
                                         'protiv balista dana 23. oktobra 1944. godine. Telo preneto i sahranjeno na '
                                         'groblju u Žitorađu. Stanko je rođen 1912. godine u Žitorađu.',
                                         '1912', '1944', '1944-10-23', 'Uši kod Gornjeg Vrtogoša', [], 89),
          ('Đorđević', 'Dobrosava', 'Stamen'): ('ĐORĐEVIĆ DOBROSAVA TAZINOG STAMEN, borac VIII srpske udarne brigade. '
                                                'Poginuo je aprila 1945. godine u Sremu, prilikom probijanja Sremskog '
                                                'fronta. Otac Dobrosav preko leta 1945. uspeo je da pronađe grob '
                                                'poginulog sina, preneo ga u Žitorađe i sahranio na seoskom groblju. '
                                                'Stamen je stupio u NOV avgusta 1944. godine. Rođen je 13. septembra '
                                                '1926. godine.', '1926', '1945', '', 'Srem', [87], 90),
          ('Vukašinović', 'Stanka', 'Milorad'): ('VUKAŠINOVIĆ STANKA MILORAD, borac-kurir štaba 46. srpske divizije. Od '
                                                 'ratnih posledica umro u vojnoj bolnici u Skoplju januara 1946. godine. '
                                                 'Telo preneto i sahranjeno na žitorađskom groblju. Milorad je rođen 15. '
                                                 'avgusta 1925. godine u Žitorađu.', '1925', '1946', '', 'Skoplje', [], 90)}
# the liberators (pp. 91-93): surname, father (genitive), given, text, birth year, birthplace, death day, place, units
SEPT9 = ('1944-09-09', 'Žitorađe')        # at "Širine", a field of Žitorađe
LIBERATORS = [
    ('Aritonović', 'Mite', 'Vlajko', 'zamenik komandira čete. Rođen 1918. godine u selu Drežnici, SO Bujanovac. Telo '
     'sahranjeno u Drežnici.', '1918', 'Drežnici, Bujanovac', *SEPT9, [87], 91),
    ('Antić', 'Petra', 'Jovan', 'borac. Rođen 1928. godine u Surdulici od oca Petra i majke Nuške. Učenik IV razreda '
     'gimnazije. Sahranjen u Surdulici.', '1928', 'Surdulici, Surdulica', *SEPT9, [87], 92),
    ('Krstić', 'Stamena', 'Jovan', 'borac. Rođen u selu Goločevcu, SO Trgovište. Oženjen. Sahranjen u rodnom selu.', '',
     'Goločevcu, Trgovište', *SEPT9, [87], 92),
    ('Petković', 'Pante', 'Borivoje', 'delegat voda. Rođen 1921. godine u selu Izumnu kod Vranjske Banje od oca Pante i '
     'majke Jovanke. Sahranjen u Izumnu.', '1921', 'Izumnu, Vranjska Banja', *SEPT9, [87], 92),
    ('Radić', 'Trajka', 'Stojadin', 'politički komesar čete. Rođen 1927. godine u selu Sebevranju kod Vranjske Banje od '
     'oca Trajka i majke Mileve. Sahranjen u Sebevranju. U NOVJ stupio 1. januara 1943. godine.', '1927',
     'Sebevranju, Vranjska Banja', *SEPT9, [87], 92),
    ('Ristić', 'Zdravka', 'Stanko', 'borac, mitraljezac. Rođen 1915. godine u selu Crveni Grad, SO Trgovište od oca '
     'Zdravka i majke Zlate. Sahranjen na seoskom groblju.', '1915', 'Crveni Grad, Trgovište', *SEPT9, [87], 92),
    ('Smiljković', 'Stojana', 'Stevan', 'borac. Rođen 1923. godine u Donjem Stajevcu, SO Trgovište od oca Stojana i '
     'majke Nevke. Telo sahranjeno na groblju u selu Prekodolcu kod Vladičinog Hana.', '1923',
     'Donjem Stajevcu, Trgovište', *SEPT9, [87], 92),
    ('Stanković', 'Marka', 'Vidosav', 'borac. Rođen 1907. godine u Urmanici, SO Vranje, od oca Marka i majke Cane. '
     'Sahranjen na groblju u Urmanici.', '1907', 'Urmanici, Vranje', *SEPT9, [87], 92),
    ('Stevanović', 'Stanoja', 'Stamen', 'borac. Rođen 1925. godine u selu Prekodolcu, od oca Stanoja i majke Mare. '
     'Neoženjen. Stolarski radnik. Sahranjen na groblju u Prekodolcu.', '1925', 'Prekodolcu, Vladičin Han', *SEPT9, [87], 92),
    ('Tasić', 'Jordana', 'Božidar', 'borac. Rođen 1925. godine u Preševu od oca Jordana i majke Stane. Učenik VI '
     'razreda gimnazije. Sa roditeljima živeo u Vranju. Telo sahranjeno na Šapranačkom groblju u Vranju.', '1925',
     'Preševu, Preševo', *SEPT9, [87], 92),
    ('Tasić', 'Dragutina', 'Božidar', 'borac. Rođen 1927. godine u Vranjskoj Banji od oca Dragutina i majke Jordanke. '
     'Neoženjen. Sahranjen u Vranjskoj Banji.', '1927', 'Vranjskoj Banji, Vranjska Banja', *SEPT9, [87], 92),
    ('Dimić', 'Jovana', 'Rista', 'borac. Rođen 1924. godine u selu Katunu kod Vranja od oca Jovana i majke Stojane. '
     'Neoženjen. Sahranjen na Katunskom groblju.', '1924', 'Katunu, Vranje', *SEPT9, [87], 93),
    ('Smiljković', 'Milana', 'Stojil', 'borac. Poginuo 11. oktobra 1944. godine u borbi sa blokiranom nemačkom '
     'baterijom u Žitorađu. Rođen 1922. godine u Crvenom Gradu, SO Trgovište od oca Milana i majke Jane. Telo '
     'sahranjeno u rodnom selu.', '1922', 'Crvenom Gradu, Trgovište', '1944-10-11', 'Žitorađe', [87], 93),
    ('Ćirić', 'Jovana', 'Nikola', 'borac. Podlegao teškim ranama zadobijenim u borbi sa nemačkom baterijom u '
     'Žitorađu 12. oktobra 1944. godine. Rođen je 16. avgusta 1919. godine u selu Veliki Jovanovac kod Pirota od oca '
     'Jovana i majke Darinke. Telo preneto i sahranjeno u Velikom Jovanovcu.', '1919', 'Veliki Jovanovac, Pirot',
     '1944-10-12', 'Žitorađe', [31], 93),
    ('Stojanović', 'Vladimira', 'Miroslav', 'borac. Poginuo u borbi sa Nemcima prilikom isterivanja njihove baterije '
     'iz Žitorađa 13. oktobra 1944. godine. Rođen je u selu Zagužanju SO Surdulica 1924. godine, od oca Vladimira i '
     'majke Ljubice. Telo sahranjeno na groblju u Zagužanju.', '1924', 'Zagužanju, Surdulica', '1944-10-13',
     'Žitorađe', [], 93),
]
# fathers the OCR garbled, as the man's other entry prints him
FATHERS = {'Dobrosima': 'Dobrosava', 'Njorđa': 'Đorđa'}
HEADINGS = {87: 'Iz VIII srpske brigade iz III čete I bataljona, poginuli 9. septembra 1944. godine na mestu zv. Širine',
            31: 'Iz 25. srpske brigade 46. divizije', 0: 'Iz Prve surduličke brigade'}


def run_on(book: dict) -> list[tuple[str, list[str]]]:
    """The two lists of names run on: (list, [name, ...])"""
    text, out = [], []
    for l in level_lines(page_words(book, 88)):
        t = l.text.strip()
        if t.startswith('РАЊЕНИ'):
            break
        text.append(t)
    whole = V.unhyphen(re.sub(r"[\"'’`]+(?=[БЊЕ])", '', ' '.join(text)))
    whole = whole.replace('гЊорђевић', 'Ђорђевић').replace('Њорђевић', 'Ђорђевић').replace('Борђевић', 'Ђорђевић')
    first, _, rest = whole.partition('Укупно 69 бораца.')
    second = rest.split('ДОСЕЊЕНИЦИ', 1)[1]
    for key, part in ((PARTICIPANTS, first.split('ЖИТОРА', 1)[1].split(' ', 1)[1]), (SETTLERS, second)):
        names = [n.strip(' .') for n in re.split(r',\s*|\s+и\s+', part) if n.strip(' .')]
        merged = []
        for n in names:                                     # "Митић, Драгутина Боривоје": a comma inside a name
            if merged and len(merged[-1].split()) == 1:
                merged[-1] += ' ' + n
            else:
                merged.append(n)
        out.append((key, merged))
    return out


def split_name(n: str) -> tuple[str, str, str, str]:
    words = n.split()
    last, fath = V.name_word(words[0]), V.father(words[1]) if len(words) > 2 else ''
    fath = FATHERS.get(fath, fath)
    rest = words[2:] if len(words) > 2 else words[1:]
    # the given name: the first word of the rest that is a given name the site knows well ("Велимир Вељко"), else the
    # one it knows best ("Џека Љубомир": the father's nickname first)
    known = [T._given[T.latin(T.best_name(w.upper()))] for w in rest]
    best = next((i for i, k in enumerate(known) if k >= 20), max(range(len(rest)), key=lambda i: (known[i], -i)))
    first = V.name_word(rest[best])
    nick = ' '.join(V.name_word(w) for i, w in enumerate(rest) if i != best)
    return last, fath, first, nick


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for key, names in run_on(book):
        base = 0 if key == PARTICIPANTS else 100
        for i, n in enumerate(names, 1):
            last, fath, first, nick = split_name(n)
            printed = ' '.join(x for x in (last, fath, first, nick) if x)
            entries.append({'soldier_id': f'{PREFIX}{base + i:06d}', 'name': ' '.join(x for x in (last, fath, first) if x),
                            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
                            'birth_year': '', 'born_in': VILLAGE, 'death_year': '', 'survived': False, 'units': [],
                            'additional_info': f'{key}: {printed}', 'list': key, 'book_title': TITLE,
                            'source_url': viewer_url(book, 88), 'source_page': 88 - OFFSET})
            counts[key] += 1
    by_name = {(e['last_name'], e['fathers_name'], e['first_name']): e for e in entries}
    for k, (text, units, page) in WOUNDED.items():
        e = by_name[k]
        e['additional_info'] += f'. {WOUNDED_LIST}: {" ".join(k)}, {text}'
        e['units'] = sorted(set(e['units']) | set(units))
        counts['wounded joined'] += 1
    for k, (text, born, dyear, ddate, dplace, units, page) in FALLEN.items():
        e = by_name[k]
        e['additional_info'] += f'. {FALLEN_LIST}: {text}'
        e.update({'birth_year': born, 'death_year': dyear, **({'death_date': ddate} if ddate else {}),
                  'death_place': dplace, 'units': sorted(set(e['units']) | set(units)),
                  'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts['fallen joined'] += 1
    for i, (last, fath, first, text, born, place, ddate, dplace, units, page) in enumerate(LIBERATORS, 1):
        head = HEADINGS[units[0] if units else 0]
        entries.append({'soldier_id': f'{PREFIX}{200 + i:06d}', 'name': f'{last} {fath} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': fath, 'birth_year': born,
                        'born_in': place, 'death_year': ddate[:4], 'death_date': ddate, 'death_place': dplace,
                        'survived': False, 'units': units,
                        # the father in the heading where the bio doesn't name him ("ARITONOVIĆ MITE VLAJKO")
                        'additional_info': f'{LIBERATORS_LIST}, {head}: {last.upper()} '
                                           f'{fath.upper() + " " if "od oca" not in text else ""}{first.upper()}, {text}',
                        'list': LIBERATORS_LIST, 'book_title': TITLE,
                        'source_url': viewer_url(book, page), 'source_page': page - OFFSET})
        counts['liberators'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))


if __name__ == '__main__':
    main()
