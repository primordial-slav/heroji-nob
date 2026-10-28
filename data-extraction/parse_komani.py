"""
Племе Комани (Бандићи - Бездановићи и Радуловићи) кроз вјекове (Poreklo library, doc 00003508), the Bandići of the
Komani tribe by Podgorica, as a book across units. Cyrillic, typed here from the scan's OCR:
    "Бандићи погинули у НОБ — списак на спомен плочи у Загарачу" (scan pp. 209-210): the plaque in the cooperative's
        hall at Donji Zagarač, "Погинули", the surname, the father's initial and the given name, the narodni heroj
        Barović Simon first. Its "Стријељани" and "Жртве" (the shot and the victims) stay out.
    The brotherhoods' lists of their dead in every war (pp. 205-208) mark those of the NOB ("Благота Шогов —
        Даниловград мај 1942. г. НОБ"): where such a line is a man of the plaque (the given name and the father's
        initial agree), it is joined to his entry (`DETAIL`).

Output: data-extraction/poreklo/komani-entries.json (IDs 9100xxxxxx, in the plaque's order, its left column first).
Usage: python data-extraction/parse_komani.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from poreklo_text import load, viewer_url  # noqa: E402

BOOK = 'komani.json'
OUT = HERE / 'poreklo' / 'komani-entries.json'
PREFIX = '9100'
OFFSET = -14                                # scan page minus the book's page (the foot of scan 209 prints 223)
TITLE = 'Pleme Komani (Bandići - Bezdanovići i Radulovići) kroz vjekove'
PLAQUE = 'Bandići poginuli u NOB — spisak na spomen ploči u Zagaraču, Poginuli'
BROTHERHOODS = 'Bandići poginuli u ratovima'
# the plaque, left column then right: surname, father's initial, given name
NAMES = [('Barović', 'P.', 'Simon'), ('Barović', 'M.', 'Nikola'), ('Barović', 'S.', 'Nikola'), ('Barović', 'S.', 'Marica'),
         ('Barović', 'K.', 'Vukadin'), ('Barović', 'B.', 'Janko'), ('Vuković', 'M.', 'Spasoje'), ('Vuković', 'K.', 'Milutin'),
         ('Pavićević', 'P.', 'Savo'), ('Radulović', 'V.', 'Mihailo'), ('Stanišić', 'S.', 'Mirko'), ('Sekulić', 'J.', 'Radovan'),
         ('Barović', 'F.', 'Živko'), ('Vukadinović', 'R.', 'Veljko'), ('Vukadinović', 'R.', 'Julka'),
         ('Vukadinović', 'R.', 'Radomir'), ('Vuković', 'J.', 'Ilija'), ('Vuković', 'I.', 'Spasoje'), ('Sekulić', 'J.', 'Peko'),
         ('Sekulić', 'J.', 'Novak'), ('Sekulić', 'R.', 'Anka'), ('Sekulić', 'V.', 'Vukosav'), ('Sekulić', 'I.', 'Blažo')]
# the brotherhoods' lines of the same men (as printed, the father as a possessive): plaque number -> (page, line);
# the hero's ("Симон Мргудов") names another father than the plaque's initial and stays apart
DETAIL = {2: (206, 'Баровићи 42. Никола Мргудов — Сутјеска маја 1943. г. НОБ'),
          3: (206, 'Баровићи 41. Никола Савов — Веље Брдо септ. 1941. г. НОБ'),
          4: (207, 'Баровићи 51. Марица Савова — НОВ'),
          6: (206, 'Баровићи 46. Јанко Бошков — Морача септ. 1943. г. НОБ'),
          11: (208, 'Станишићи 24. Мирко Савов — НОВ — Граково јун 1942. г.'),
          12: (207, 'Секулићи 12. Радован Јоков (Павићевић) — НОВ — Копитник 1942. г.'),
          14: (206, 'Вукадиновићи 30. Вељко Радованов — НОВ 20. XI 1943. Кучи'),
          15: (206, 'Вукадиновићи 31. Јулка Радованова — Ново Село 24. маја 1942. г. НОБ'),
          17: (206, 'Вуковићи 2. Илија Јованов — НОБ'),
          18: (206, 'Вуковићи 12. Спасоје Илин — 1944. г. НОБ'),
          19: (207, 'Секулићи 13. Пеко Јоков (Павићевић) — НОВ — Бандићи окт. 1944. г.'),
          20: (207, 'Секулићи 11. Новак Јоков (Павићевић) — НОБ — Васојевићи 1944. г.')}
DEATH = {2: ('1943', 'Sutjeska'), 3: ('1941', 'Velje Brdo'), 6: ('1943', 'Morača'), 11: ('1942', 'Grahovo'),
         12: ('1942', 'Kopitnik'), 14: ('1943', 'Kuči'), 15: ('1942', 'Novo Selo'), 18: ('1944', ''),
         19: ('1944', 'Bandići'), 20: ('1944', 'Vasojevići')}


def main():
    book = load(BOOK)
    sys.path.insert(0, str(HERE))
    from _parser_scaffold import cyrillic_to_latin as latin
    entries = []
    for no, (last, initial, first) in enumerate(NAMES, 1):
        text = f'{PLAQUE}: {last} {initial} {first}' + (' (narodni heroj)' if no == 1 else '')
        if no in DETAIL:
            text += f' — {BROTHERHOODS}, {latin(DETAIL[no][1])}'
        year, place = DEATH.get(no, ('', ''))
        entries.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {initial} {first}', 'last_name': last,
                        'also': [], 'first_name': first, 'nick': '', 'fathers_name': initial, 'birth_year': '',
                        'born_in': 'Bandići, Danilovgrad', 'death_year': year,
                        **({'death_place': place} if place else {}), 'survived': False, 'units': [],
                        'additional_info': text, 'list': PLAQUE, 'book_title': TITLE,
                        'source_url': viewer_url(book, 209), 'source_page': 209 - OFFSET})
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name)


if __name__ == '__main__':
    main()
