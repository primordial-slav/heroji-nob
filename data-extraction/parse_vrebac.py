"""
Vrebac, Zavođe and Pavlovac near Gospić (Poreklo library, collection "Monografije sela", Вребац, Завође, Павловац:
Корени вековног трајања): "Погинули борци НОР-а Врепца, Завођа и Павловца од 1941. до 1945. године", as a book across
units: three lists, one a village, numbered, two columns, a bio each ("6. БОГДАНОВИЋ ЂУРЕ МИЛОШ, рођен 1923. године.
Земљорадник. Децембра 1941. године ступио у 1. чету, 2. батаљона 1. ЛПО „Велебит“. Погинуо у борби са усташама
приликом напада на Широку Кулу 3. августа 1942. године. Сахрањен у Врепцу.").

    "Погинули борци Врепца" (scan pp. 303-308), "Погинули борци Завођа" (pp. 309-311), "Погинули борци Павловца"
    (pp. 312-316).
The tables after them and the bios of the most prominent fighters (pp. 320-340) are not read.

The name is the surname, the father in the genitive and the given name in capitals, a nickname after it ("ЦЕТИНА МАНЕ
ЈОВО ЈОЈА"). The OCR reads Ћ and Ђ as 'Б, 'ћ, Т: or ТЈ ("БОГДАНОВИ'Б", "ЗАВОТЈА") and capitals in Latin look-alikes
("HETPA"); names are read back as the site's records spell them. The scans are skewed: each column's words are
levelled before they are grouped into lines. Entries are kept in Latin.

Output: data-extraction/poreklo/vrebac-entries.json (IDs 9048xxxxxx: Vrebac by its number, Zavođe from 101, Pavlovac
from 201).
Usage: python data-extraction/parse_vrebac.py [--sample N]
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

BOOK = 'vrebac.json'
OUT = HERE / 'poreklo' / 'vrebac-entries.json'
PREFIX = '9048'
PAGES = range(303, 317)
OFFSET = 5                                  # scan page minus the book's page
TITLE = 'Vrebac, Zavođe, Pavlovac: koreni vekovnog trajanja'
LISTS = {'ВРЕПЦА': (0, 'Poginuli borci Vrepca', 'Vrebac, Gospić'),
         'ЗАВОЂА': (100, 'Poginuli borci Zavođa', 'Zavođe, Gospić'),
         'ПАВЛОВЦА': (200, 'Poginuli borci Pavlovca', 'Pavlovac, Gospić')}
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
CAPS = rf"[{UC}A-Z\"'’”][{UC}A-Z\"'’”:;1)\]]*"
NUMBER = re.compile(r'^(\d{1,2})\s*[.,]\s*(?=\S)')
# names the reader gets wrong, as printed (after pre) -> as read from the page
NAMES = {'МИТ1Е': 'МИТЕ', 'HETPA': 'ПЕТРА', 'ЂУРan': 'ЂУРАН', '”BYPan': 'ЂУРАН', 'HtKAHA': 'НИКАНА'}
# heads the OCR broke past that, by list and number: (surname, father, given name, nickname); "ЗОРОЈ А", "Ј ОВАН"
# split, "”BS/PO" for ЂУРО, "СПАЈ И] Е", "HEJ E" (a word of the father's that the page doesn't make out) left out
HEADS = {
    ('ВРЕПЦА', 4): ('БОГДАНОВИЋ', 'МИЛОША', 'ЈОВО', ''), ('ВРЕПЦА', 5): ('БОГДАНОВИЋ', 'БОГДЕ', 'МИЛОШ', ''),
    ('ВРЕПЦА', 11): ('ЦРНОКРАК', 'ЈОВЕ', 'ПЕТАР', 'ЧИЛЕ'), ('ВРЕПЦА', 12): ('ЂУРАН', 'МАРКА', 'ЂУРО', ''),
    ('ВРЕПЦА', 17): ('ДРАГОСАВАЦ', 'ПЕРЕ', 'ЂУРО', ''), ('ВРЕПЦА', 20): ('ДРАГОСАВАЦ', 'САВЕ', 'НИКОЛА', 'РАЖОВИНА'),
    ('ВРЕПЦА', 21): ('ДРАГОСАВАЦ', 'ЈОВЕ', 'НИКОЛА', 'ЈОРИЋ'), ('ВРЕПЦА', 24): ('ДРАГОСАВАЦ', 'НИКОЛЕ', 'ПЕТАР', 'ПЕРИЋ'),
    ('ВРЕПЦА', 27): ('ГРАОВАЦ', 'ЛУКЕ', 'ДУШАН', ''), ('ВРЕПЦА', 28): ('ГРУБИЋ', 'САВИНА', 'БОЖО', 'БОЋА'),
    ('ВРЕПЦА', 31): ('МАНДАРИЋ', 'ЂУКАНА', 'ЈОЈА', ''), ('ВРЕПЦА', 33): ('МАНДАРИЋ', 'ПЕТРА', 'МИЛЕ', 'ПЕКАР'),
    ('ВРЕПЦА', 48): ('ПОПОВИЋ', 'ЂУРЕ', 'МАРКО', ''), ('ВРЕПЦА', 52): ('СУНАЈКО', 'БОЖЕ', 'ПЕТАР', ''),
    ('ВРЕПЦА', 54): ('УГАРАК', 'ЈОЈЕ', 'ЂУРО', 'ЦОГО'), ('ВРЕПЦА', 56): ('УГАРАК', 'МАНЕ', 'МИЛАН', ''),
    ('ЗАВОЂА', 1): ('ЂУРАН', 'ПЕТРА', 'МИЛЕ', ''), ('ЗАВОЂА', 9): ('МИШЧЕВИЋ', 'СТЕВАНА', 'ЈОВАН', ''),
    ('ЗАВОЂА', 11): ('НОВКОВИЋ', 'ПЕТРА', 'МИЛОШ', ''), ('ЗАВОЂА', 15): ('ЊЕГОМИР', 'МИЋЕ', 'ЂУРО', ''),
    ('ЗАВОЂА', 21): ('ЊЕГОМИР', 'ТАНАСИЈЕ', 'РАДЕ', ''), ('ЗАВОЂА', 23): ('ЊЕГОМИР', 'ТАНАСИЈЕ', 'СТАНКО', ''),
    ('ПАВЛОВЦА', 3): ('БУРСАЋ', 'МИЈАТА', 'ЈАНКО', ''), ('ПАВЛОВЦА', 4): ('БУРСАЋ', 'ИЛИЈЕ', 'МАРИЈА', ''),
    ('ПАВЛОВЦА', 7): ('ГРАОВАЦ', 'ПЕТРА', 'ЂУРО', ''), ('ПАВЛОВЦА', 8): ('ГРАОВАЦ', 'ВАСЕ', 'ЈОВАН', ''),
    ('ПАВЛОВЦА', 10): ('КОРАЋ', 'МАРКА', 'ПЕРА', ''), ('ПАВЛОВЦА', 11): ('КРИЧКОВИЋ', 'НИКОЛЕ', 'ПЕТАР', ''),
    ('ПАВЛОВЦА', 22): ('НОВКОВИЋ', 'ГОЈКА', 'МАНЕ', ''), ('ПАВЛОВЦА', 37): ('ТОМАШ', 'ВАСЕ', 'НИКОЛА', ''),
    ('ПАВЛОВЦА', 42): ('ЗОРОЈА', 'ТОМЕ', 'БОГДАН', ''), ('ПАВЛОВЦА', 43): ('ЗОРОЈА', 'ПЕТРА', 'ДУШАН', ''),
    ('ПАВЛОВЦА', 44): ('ЗОРОЈА', 'ТОМЕ', 'ЂУРО', ''), ('ПАВЛОВЦА', 45): ('ЗОРОЈА', 'НИКОЛЕ', 'ГЛИШО', ''),
    ('ПАВЛОВЦА', 46): ('ЗОРОЈА', 'ЂУРЕ', 'САВА', ''),
}


def pre(text: str) -> str:
    """Ћ and Ђ the OCR reads as 'Б, 'ћ, Т:, ТЈ or Т) at a name's end, and as 'Б or "Б at its start"""
    text = re.sub(r"И(?:['’\"]?[БбНћ]|Т[:;Ј)\]]|ТЈ|Тт)(?=[\s,.]|$)", 'ИЋ', text)
    text = re.sub(r"(?<![\w])['’\"”]\s*[БЕћ](?=[{}{}])".format(UC, LC), 'Ђ', text)
    text = re.sub(r"['’]ћ", 'Ћ', text)                                       # "МИ'ћЕ"
    text = re.sub(r"(?<=[{0}])['’](?=[{0}])".format(UC), '', text)           # "ЦЕТ'ИНА"
    return text.replace('ЗАВОТЈА', 'ЗАВОЂА').replace('ЗАВОБА', 'ЗАВОЂА')


def columns(book: dict, page: int) -> list:
    """the page's lines, its left column first: the columns part where the fewest words cross"""
    words = page_words(book, page)
    if not words:
        return []
    left, right = min(w.x0 for w in words), max(w.x1 for w in words)
    cut = min(range(int(left + (right - left) * 0.38), int(left + (right - left) * 0.62), 5),
              key=lambda x: sum(1 for w in words if w.x0 < x < w.x1))
    return [l for side in (True, False) for l in level_lines([w for w in words if ((w.x0 + w.x1) / 2 < cut) == side])]


def raw_entries(book: dict) -> list[dict]:
    out, cur, lst, last = [], None, None, 0
    for page in PAGES:
        for l in columns(book, page):
            text = pre(l.text.strip())
            # a list's heading, "ПОГИНУЛИ / БОРЦИ ВРЕПЦА:", its halves atop the two columns: the next list starts
            if re.match(r'ПОГИНУЛИ(?:\s+БОРЦИ)?\b', text):
                lst, last, cur = list(LISTS)[list(LISTS).index(lst) + 1] if lst else list(LISTS)[0], 0, None
                continue
            if not lst or re.fullmatch(r'\d{1,3}|БОРЦИ.*', text):
                continue
            n = NUMBER.match(text)
            if n and last < int(n.group(1)) <= last + 3 and re.match(CAPS, text[n.end():]):
                last = int(n.group(1))
                cur = {'list': lst, 'no': last, 'page': page, 'parts': [text[n.end():]]}
                out.append(cur)
            elif cur:
                cur['parts'].append(text)
    return out


def name_word(w: str) -> str:
    w = NAMES.get(w, w).strip('„“"”/(),.:;')
    if not w:
        return ''
    best = T.best_name(w.upper())
    if not T._names[latin(best)]:
        best = w.upper()
    return latin(best).capitalize()


def main():
    T.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for raw in raw_entries(book):
        text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', ' '.join(raw['parts']))
        text = re.sub(r'\s+', ' ', text)
        # the name in capitals up to the comma or "рођен"
        m = re.match(rf'^((?:{CAPS}\s*)+?)(?:,|\s+(?=рођен)|\.\s)', text)
        head = m.group(1) if m else ' '.join(text.split()[:3])
        words = [NAMES.get(w, w) for w in head.split() if re.search(rf'[{UC}A-Z]', w)]
        rest = text[m.end():].strip() if m else text[len(head):]
        sur = words[0] if words else ''
        father = words[1] if len(words) >= 3 else ''
        given = words[2] if len(words) >= 3 else words[-1] if len(words) == 2 else ''
        nick = words[3] if len(words) >= 4 else ''
        if (raw['list'], raw['no']) in HEADS:
            sur, father, given, nick = HEADS[(raw['list'], raw['no'])]
            cut = re.search(r',\s*|\s+(?=рођен)', text)
            rest = text[cut.end():].strip() if cut else rest
        last, first = name_word(sur), name_word(given)
        fath = father_word(father) if father else ''
        nick = name_word(nick) if nick else ''
        if not last or not first:
            counts['unreadable'] += 1
            print('unreadable:', raw['page'], text[:80])
            continue
        start, title, born = LISTS[raw['list']]
        name = f"{last} {fath + ' ' if fath else ''}{first}{' – ' + nick if nick else ''}"
        info = name + ', ' + latin(T.decode_text(rest))
        y = re.search(r'\brođen(?:a|je)?\b(?:(?!Pogin).){0,40}?(?<!\d)(1[89]\d\d)(?!\d)', info, re.I)
        death = death_of(info)
        entries.append({
            'soldier_id': f'{PREFIX}{start + raw["no"]:06d}',
            'name': name, 'last_name': last, 'first_name': first, 'nick': nick, 'fathers_name': fath,
            'birth_year': y.group(1) if y else '', 'born_in': born,
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': False,
            'additional_info': info,
            'list': title, 'book_title': TITLE,
            'source_url': viewer_url(book, raw['page']), 'source_page': raw['page'] - OFFSET,
        })
        counts[raw['list']] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))


if __name__ == '__main__':
    main()
