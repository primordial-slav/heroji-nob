"""
*Хроника села Водице у Доњој Јасеници* (Nikola Vladisavljević, Biblioteka "Hronika sela", Čačak 1991; Poreklo library,
doc 00000051), a book across units: the village's fighters by Smederevska Palanka, in Cyrillic, a paragraph each:

    the three "првоборци" of 1941 (scan pp. 254-256): "Глигоријевић Радивоја Ђурђе (Ђура Тодоровић), рођен 1. новембра
        1912. године у Водицама, ..." (only the paragraph that opens with his name; the chapter's story of him
        goes on in the text);
    "Погинули у борбама за коначно ослобођење" (pp. 259-264): the men who joined in October-December 1944 and fell or
        died of wounds and illness: "Браконвић Станимира Милан, рођен 1921. године, земљорадник. У НОБ ступио 14.
        новембра 1944, погинуо 27. јануара 1945. године, на Голом Брду код Бјељине."

Output: data-extraction/poreklo/vodice-entries.json (IDs 9122xxxxxx in the book's order).
Usage: python data-extraction/parse_vodice.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'vodice.json'
OUT = HERE / 'poreklo' / 'vodice-entries.json'
PREFIX = '9122'
OFFSET = 2                                   # scan page minus the book's page (scan 254 is p. 252)
TITLE = 'Hronika sela Vodice u Donjoj Jasenici'
FIRST = 'Prvoborci'
FALLEN = 'Poginuli u borbama za konačno oslobođenje'
VILLAGE = 'Vodice, Smederevska Palanka'
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
FIX = {'Браконвић': 'Бранковић', 'Бурће': 'Ђурђе', 'Бура': 'Ђура', 'Бурћа': 'Ђурђа', '}Кивојина': 'Живојина', 'Њубисава': 'Љубисава',
       'Њубомира': 'Љубомира', 'роћен': 'рођен', 'Роћен': 'рођен', 'Бен ': 'ђен ', 'стушо': 'ступио'}
NAME = re.compile(rf'^([{CU}][{CL}]+)\s+([{CU}][{CL}]+)\s+([{CU}][{CL}]+)(?:\s*\(([^)]*)\))?\s*,?\s*(.*)$')


def paragraphs(book: dict, pages):
    for page in pages:
        lines = [l for l in level_lines(page_words(book, page)) if l.text.strip()]
        if not lines:
            continue
        base = median(l.x0 for l in lines)
        para = None
        for l in lines:
            t = l.text.strip()
            for a, b in FIX.items():
                t = t.replace(a, b)
            if re.fullmatch(r'\d{1,3}', t) or re.match(r'^\d{3}\)', t) or l.x0 > base + 900:
                continue                                            # page numbers, footnotes, captions
            if l.x0 > base + 100:
                if para:
                    yield page, para
                para = [t]
            elif para is not None:
                para.append(t)
        if para:
            yield page, para


def main():
    V.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for page, para in paragraphs(book, range(254, 265)):
        m = NAME.match(para[0])
        text = re.sub(r'\s+', ' ', V.unhyphen(' '.join(para)) if hasattr(V, 'unhyphen') else ' '.join(para))
        if not m or not re.search(r'рођен|ступио', text[:120]):
            continue
        listname = FIRST if page <= 256 else FALLEN
        last, fath, given, nick = V.name_word(m.group(1)), latin(m.group(2)), V.given_word(m.group(3)), m.group(4)
        body = text[m.end(3):].lstrip(' ,')
        if nick:
            body = body[len(nick) + 2:].lstrip(' ,')
        info = V.read_cyr(body).strip(' .')
        if listname == FIRST:                                       # the first sentences, up to his fate
            cut = re.search(r'(?:[Пп]огинуо|[Уу]мро|стрељан)[^.]*\.', info)
            info = info[:cut.end()] if cut else info[:400]
        d = V.death(info)
        born = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
        name = f'{last} {fath} {given}'
        nick_l = latin(nick) if nick else ''
        e = {'soldier_id': f'{PREFIX}{len(entries) + 1:06d}', 'name': name, 'last_name': last, 'also': [],
             'first_name': given, 'nick': nick_l, 'fathers_name': fath, 'birth_year': born.group(1) if born else '',
             'born_in': VILLAGE, 'death_year': d.get('year', '') if d.get('year', '') <= '1945' else '',
             **({'death_date': d['date']} if d.get('date') and d['date'][:4] <= '1945' else {}),
             **({'death_place': d['place']} if d.get('place') else {}),
             'survived': False, 'units': V.units_of(info),
             'additional_info': f"{listname}: {name}{' (' + nick_l + ')' if nick_l else ''}, {info}.", 'list': listname,
             'book_title': TITLE, 'source_url': viewer_url(book, page), 'source_page': page - OFFSET}
        entries.append(e)
        counts[listname] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(entries), 'entries ->', OUT.name, dict(counts))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} {e['nick']} | {e['birth_year']} | {e['death_year']} "
              f"{e.get('death_place', '')} {e['units']} | {e['additional_info'][:110]}")


if __name__ == '__main__':
    main()
