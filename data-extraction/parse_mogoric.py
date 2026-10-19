"""
Mogorić in Lika (Poreklo library, collection "Monografije sela", Могорић (Лика)): two lists of the village's fighters,
as a book across units.

    "24. 4. Могорићани погинули у борби против фашизма, борећи се у партизанским јединицама" (scan pp. 195-203): the
        110 fallen fighters of the memorial plaque at the village's hall, numbered, a short bio each ("4. БАСАРИЋ Јове
        ПЕТАР, рођен 1917. године. Ступио у НОБ 27. јула 1941. године, борац чете „Могорић“, ... Погинуо је 5. маја
        1945. године у Словенији, као командир чете 3. бригаде 6. дивизије.");
    "24. 4. 2. Носиоци партизанске споменице 1941." (p. 205): the village's holders of the Partizanska spomenica 1941,
        surname, father and name, three columns read down (each entry's text names the list, which gives the record
        the medal).
The book's other lists (the prisoners of war in Germany and Italy, the victims of the Ustaše) stay out.

The OCR reads Ћ and Ђ as 'Б or 'Н ("БАСАРИ'Б", "'Буре"), Л as П ("МИПАН", "НИКОПА"), and some capitals in Latin
look-alikes ("HETAP", "CABO"); names are read back as the site's records spell them (parse_trebinjci_pali's reader,
with П as Л too). Entries are kept in Latin.

Output: data-extraction/poreklo/mogoric-entries.json (IDs 9047xxxxxx: the fallen by their number, the spomenica's
holders from 9047000201 in the columns' order).
Usage: python data-extraction/parse_mogoric.py [--sample N]
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
import parse_trebinjci_pali as T  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_divoselo import father_word  # noqa: E402
from parse_ostrvica import death_of, level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'mogoric.json'
OUT = HERE / 'poreklo' / 'mogoric-entries.json'
PREFIX = '9047'
FALLEN_PAGES = range(195, 204)
SPOMENICA_PAGE = 205
OFFSET = 4                                  # scan page minus the book's page
TITLE = 'Mogorić (Lika)'
FALLEN = 'Mogorićani poginuli u borbi protiv fašizma, boreći se u partizanskim jedinicama'
SPOMENICA = 'Nosioci Partizanske spomenice 1941.'
BORN_IN = 'Mogorić, Gospić'
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
T.OPTS['П'] = 'ПЛ'                          # "МИПАН", "НИКОПА"
NUMBER = re.compile(r'^(\d{1,3})\s*\.?\s+(?=\S)')
# names the reader gets wrong, as printed -> as read from the page
# fallen fighters whose name the OCR garbled past the reader, by their number: (surname, father, given, nickname)
HEADS = {17: ('ВУЧКОВИЋ', 'Миле', 'ИЛИЈА', ''), 22: ('ЂАКОВИЋ', 'М.', 'ЂУРО', ''), 33: ('ИЛИЋ', 'Станише', 'ДМИТАР', ''),
         34: ('ИЛИЋ', 'Дане', 'ДУШАН', ''), 49: ('КОРИЦА', 'Ђ.', 'НИКОЛА', ''), 55: ('КОРИЦА', 'Илије', 'СТЕВАН', 'ЛОЛА'),
         59: ('КРИЧКОВИЋ', 'М.', 'ГОЈКО', ''), 62: ('КРИЧКОВИЋ', 'Ј.', 'НИКОЛА', ''), 79: ('РАДАКОВИЋ', 'Дане', 'ДМИТАР', ''),
         86: ('РАДАКОВИЋ', 'Н.', 'МИЋО', ''), 92: ('РАДАКОВИЋ', 'Ђ.', 'МИЛЕ', ''), 104: ('ЧАНКОВИЋ', 'Јове', 'ГОЈКО', ''),
         52: ('КОРИЦА', 'Миле', 'РАДЕ', 'ЛУЛИЦА')}
NAMES = {'ПЕТАЕ': 'ПЕТАР', 'ПЕТАЕ,': 'ПЕТАР', 'CMI/HBA': 'СМИЉА', 'ДуШан': 'Душан', 'Николв': 'Николе', 'Кориш': 'Корица',
         'Снасе': 'Спасе', 'Сојана': 'Стојана'}


def pre(text: str) -> str:
    """Ћ and Ђ the OCR reads as 'Б, 'Н or Т): Ћ at a word's end, Ђ at its start"""
    text = re.sub(r"И['’\"]?[БНТ]\)?(?=[\s,.]|$)", 'ИЋ', text)
    return re.sub(r"(?<![\w])['’\"]\s*[БЕ](?=[{}{}])".format(UC, LC), 'Ђ', text)


def name_word(w: str) -> str:
    w = NAMES.get(w, w).strip('„“"”/(),.')
    if not w:
        return ''
    best = T.best_name(w.upper())
    if not T._names[latin(best)]:
        best = w.upper()                    # a name the site doesn't know stays as printed ("Бањеглавић")
    return latin(best).capitalize() if best else ''


def fallen(book: dict) -> list[dict]:
    out, cur, last = [], None, 0
    for page in FALLEN_PAGES:
        for l in level_lines(page_words(book, page)):
            text = l.text.strip()
            m = NUMBER.match(text)
            if m and last < int(m.group(1)) <= last + 3 and re.match(rf"['’\"]?[{UC}A-Z]", text[m.end():]):
                last = int(m.group(1))
                cur = {'no': last, 'page': page, 'parts': [text[m.end():]]}
                out.append(cur)
            elif cur and not cur.get('done'):
                if re.match(r'Напомена|24\.\s*4\.', text):          # the note after the list
                    cur['done'] = True
                elif not re.fullmatch(r'\d{1,3}', text):
                    cur['parts'].append(text)
    return out


HERO_NO = 55                                # Корица Илије Стеван – Лола, narodni heroj


def hero_bio(book: dict) -> str:
    """"24. 4. 1. Народни хероји": the bio of Stevan Korica under his heading, on the list's last page"""
    out, on = [], False
    for l in level_lines(page_words(book, 203)):
        if l.text.startswith('КОРИЦА Илије'):
            on = True
        elif on and re.match(r'Са отварања|\d{2,3}\s+Подаци', l.text):
            break
        elif on and l.x0 < 1000:
            out.append(l.text)
    return 'Народни херој. ' + re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', ' '.join(out))


def spomenica(book: dict) -> list[dict]:
    """the holders, column by column: each column's entries are surname, father, name"""
    cols = [[], [], []]
    for l in level_lines(page_words(book, SPOMENICA_PAGE)):
        if not re.match(rf"['’\"]?[{UC}][{LC}]", l.text) or l.x0 > 400:
            continue
        if l.text.startswith('Партизанска') or not re.search(r'ић\b', l.text):
            continue
        for w in l.words:
            col = 0 if w.x0 < 1400 else 1 if w.x0 < 2600 else 2
            if not cols[col] or len(cols[col][-1]) == 3:
                cols[col].append([])
            cols[col][-1].append(w.text)
        if re.match(r'Илић Милоша Душан', l.text):
            break
    return [{'page': SPOMENICA_PAGE, 'words': words} for col in cols for words in col]


def main():
    T.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for raw in fallen(book):
        text = pre(' '.join(raw['parts']))
        text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', text)
        # the name: surname, father (or his initial), given name in capitals, then a nickname after a dash or a comma
        # ("КОРИЦА И. СТЕВАН– ЛОЛА– Народни херој", "КОРИЦА Миле РАДЕ, ЛУЛИЦА, рођен је"); the rest is the bio
        m = re.match(rf"^(\S+)\s+(?:(\S+?)\s+)?([{UC}A-Z\][/'’]{{2,}}[{UC}A-Z\][/'’Ђ]*)\s*"
                     rf"(?:[–-]\s*([{UC}]{{3,}})\s*[–-]?|,\s*([{UC}A-Z]{{3,}})(?=,))?\s*[,.]?\s*", text)
        sur, father, given, nick = (m.group(1), m.group(2) or '', m.group(3), m.group(4) or m.group(5) or '') if m \
            else (text.split()[0], '', text.split()[-1], '')
        rest = text[m.end():] if m else ''
        if raw['no'] == HERO_NO:
            rest = hero_bio(book)               # the plaque's "Народни херој" and the book's bio of him after the list
        if raw['no'] in HEADS:
            sur, father, given, nick = HEADS[raw['no']]
        initial = re.fullmatch(rf"[{UC}\]]['.,]?|['’]Б\.?", father)       # "М.", "Ј.", "'Б" (Ђ.): the father's initial
        last, first = name_word(sur), name_word(given)
        fath = '' if initial or not father else father_word(father)
        letter = father.strip("'’.,").replace(']', 'Ј').replace('Б', 'Ђ')[:1]
        shown = latin(letter) + '.' if initial else fath
        head = f"{last} {shown + ' ' if shown else ''}{first}{' – ' + name_word(nick) if nick else ''}"
        info = head + (', ' + latin(T.decode_text(rest)) if rest else '')
        # "rođen je1923", "rođenje 1925" (the OCR's spacing)
        y = re.search(r'\brođen(?:a|je)?\b(?:(?!Pogin).){0,40}?(?<!\d)(1[89]\d\d)(?!\d)', info, re.I)
        death = death_of(info)
        entries.append({
            'soldier_id': f'{PREFIX}{raw["no"]:06d}',
            'name': head,
            'last_name': last, 'first_name': first, 'nick': name_word(nick) if nick else '',
            'fathers_name': fath,
            'birth_year': y.group(1) if y else '', 'born_in': BORN_IN,
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': False,
            'additional_info': info,
            'list': FALLEN, 'book_title': TITLE,
            'source_url': viewer_url(book, raw['page']), 'source_page': raw['page'] - OFFSET,
        })
        counts['fallen'] += 1
    for i, raw in enumerate(spomenica(book), 1):
        words = [NAMES.get(w, w) for w in raw['words']]
        sur, father, given = [pre(w) for w in words]
        last, first, fath = name_word(sur), name_word(given), father_word(father)
        entries.append({
            'soldier_id': f'{PREFIX}{200 + i:06d}',
            'name': f'{last} {fath} {first}',
            'last_name': last, 'first_name': first, 'nick': '', 'fathers_name': fath,
            'birth_year': '', 'born_in': BORN_IN, 'death_year': '', 'survived': True,
            'additional_info': f'{SPOMENICA} {last} {fath} {first}, Mogorić.',
            'list': SPOMENICA, 'book_title': TITLE,
            'source_url': viewer_url(book, raw['page']), 'source_page': raw['page'] - OFFSET,
        })
        counts['spomenica'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    if '--sample' in sys.argv:
        n = int(sys.argv[sys.argv.index('--sample') + 1])
        import random
        random.seed(1)
        for e in random.sample(entries, min(n, len(entries))):
            print(f"{e['soldier_id']} p.{e['source_page']} | {e['name']} | {e['birth_year']} | d.{e['death_year']} "
                  f"{e.get('death_date', '')} {e.get('death_place', '')} | {e['additional_info'][:150]}")


if __name__ == '__main__':
    main()
