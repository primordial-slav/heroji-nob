"""
Bosansko Grahovo u NOR-u 1941-1945 (Poreklo library, collection "Monografije sela"): "Погинули борци
народноослободилачког рата", the fallen fighters of the Grahovo area by village (scan pp. 671-726), as a book across
units. Each entry is a paragraph numbered through the list, the name, the father in the genitive and the given name,
then a short bio ("378. Тица Гаје Крстан, рођен 1921., занатлија. Ступио 20. маја 1942. у батаљон „Будућност".
Погинуо 10. октобра 1944. на Широком Бријегу, као борац IX далматинске дивизије."). The list after it, "Жртве
фашистичког терора", is of civilians and stays out, as do the two pages before it (pp. 669-670, the end of a list of
names whose title is on a page not fetched).

The OCR loses many entries' numbers (all of 1-9, and others it leaves as a lone full stop), so an entry starts at a
line that begins with three or four names and a comma before "рођен" ("роћен", the OCR's ћ for ђ). It reads this
font's л as д or А ("јуда" = јула, "седа" = села, "Аичку" = Личку): the text is read back word by word as the site's
records spell it, the names as the site's names (parse_trebinjci_pali's reader). The village headings are read from
the page (`VILLAGES`; those the OCR garbled past certainty are given as the municipality alone). Entries in Latin.

Output: data-extraction/poreklo/bosansko-grahovo-entries.json (IDs 9062xxxxxx in the list's order).
Usage: python data-extraction/parse_bosansko_grahovo.py
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
from parse_divoselo import father_word, mother  # noqa: E402
from parse_ostrvica import death_of, level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'bosansko-grahovo.json'
OUT = HERE / 'poreklo' / 'bosansko-grahovo-entries.json'
PREFIX = '9062'
PAGES = range(671, 727)
OFFSET = 29                                 # scan page minus the book's page (p. 671 is the book's 642)
TITLE = 'Bosansko Grahovo u NOR-u 1941-1945'
LIST = 'Poginuli borci narodnooslobodilačkog rata'
GRAHOVO = 'Bosansko Grahovo'
# the village headings as the OCR gives them -> the village; '' where the reading isn't certain
VILLAGES = {'РЕСАНОВЦИ': 'Resanovci', 'ПЕБИ': 'Peći', 'ЗЕБЕ': '', 'ИСЈЕК': 'Isjek', 'РАААОВИБИ': 'Radlovići',
            'ВИАОВИБИ': 'Vidovići', 'КЕСИБИ': 'Kesići', 'ТИШКОВАЦ': 'Tiškovac', 'ТИШКОВАЦ – AYAEP': 'Tiškovac',
            'ЗАСЕОК': 'Zaseok', 'МРАЧАЈ': 'Mračaj', 'ПЕЧЕНИЦЕ': 'Pečenice',
            'БОСАНСКО ГРАХОВО И МАТОЧИБИ': 'Bosansko Grahovo i Matočići', 'УГАРЦИ': 'Ugarci', 'АУКА': 'Luka',
            'МААЕШЕВЦИ': 'Maleševci', 'МАРИНКОВЦИ': 'Marinkovci', 'ТИЧЕВО': 'Tičevo', 'ПРЕОААЦ': 'Preodac',
            'ГРКОВЦИ': 'Grkovci', 'НУГААШИЦА': 'Nuglašica', 'БАСТАСИ': 'Bastasi', 'Ј АРУГА': 'Jaruga',
            'АОЊИ КАЗАНЦИ': 'Donji Kazanci', 'УНИШТЕ': 'Uništa'}
# names the reader can't make out, by the entry's printed number (read from the shapes: "Tgpi/ibyhoibihb" is
# ТРИВУНОВИЋ in Latin look-alikes, "Hju/[je" ИЛИЈЕ), and garbled words of names
HEADS = {'422': ('Тривуновић', 'Симе', 'Гојко'), '541': ('Љубоја', 'Илије', 'Симо')}
WORDS = {'Štšro': 'Špiro', 'Njikoda': 'Nikola', 'Hmm/xe': 'Ilije'}
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# a word of a name: a capital (the OCR also gives Љ and Њ small, some capitals in Latin, "љубоја", "JOBO")
NAME = rf"\[?[{UC}A-Zљњ\"'’][{LC}{UC}A-Za-z'’\-/\[\]]*\.?"
# an entry's first line: a number (or what the OCR left of it), the name's three or four words, a comma, "рођен"
START = re.compile(rf"^(?:(\d{{1,3}})\s*\.?\s*|[.,·:'“\"]\s*)?(({NAME})\s+((?:{NAME}\s*){{1,3}}?)(?:\s*[–—-]\s*({NAME}))?)"
                   # "роћен", "рзћен", "роћеиа"; an occupation may come first ("Ненадић Нике Мидош, сезонски радник, рођен")
                   rf"\s*[,.–]\s*(?:[^,\d]{{2,30}},\s*)?(?:т?р\S?[ћђз]\S{{0,2}}н|рођ)")


NUMBERED = re.compile(rf"^(\d{{1,3}})\s*\.\s*(?=[{UC}\"'’])")
# what the name of a numbered entry is: up to the comma, or the dots of an entry the book gives no bio ("39. Бајић
# В. Стево . . ."); its father may be an initial
HEAD = re.compile(rf"^(({NAME})\s+((?:[^\s,]+\s*){{1,3}}?)(?:\s*[–—-]\s*({NAME}))?)\s*(?:,|\.\s*\.|\s+т?ро[ћђ]|$)")


def entries_raw(book: dict) -> list[dict]:
    out, cur, village, last = [], None, '', 0
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            # specks before a number ("· 85.", "\" 88.") or before a name ("ш од .::. . Банић Гавре Перо, рођен")
            text = re.sub(r'^[\s·"“\'_:.,]+(?=\d)', '', l.text.strip())
            junk = re.match(rf'^[^{UC}\d]{{0,12}}?[.:]\s+(?=[{UC}][{LC}]+\s+[{UC}])', text)
            if junk and START.match(text[junk.end():]):
                text = text[junk.end():]
            if text in VILLAGES or text.startswith('ПОГИНУ'):
                if text in VILLAGES:
                    village = VILLAGES[text]
                continue
            if text.startswith('ЖРТВЕ'):
                return out
            if re.fullmatch(r'[\d\s“":.]{1,4}', text):
                continue
            n = NUMBERED.match(text)
            h = HEAD.match(text[n.end():]) if n and last < int(n.group(1)) <= last + 15 else None
            m = START.match(text)
            if h:                                   # a numbered entry, whatever follows its name
                last = int(n.group(1))
                cur = {'no': n.group(1), 'page': page, 'village': village, 'names': h.group(2, 3, 4),
                       'parts': [text[n.end() + h.end(1):]]}
                out.append(cur)
            elif m:                                 # an entry whose number the OCR lost
                if m.group(1):
                    last = max(last, int(m.group(1)))
                cur = {'no': m.group(1) or '', 'page': page, 'village': village, 'names': m.group(3, 4, 5),
                       'parts': [text[m.end(2):]]}
                out.append(cur)
            elif cur:
                cur['parts'].append(text)
    return out


def name_word(w: str) -> str:
    w = w.strip('„“"”/(),.:;\'’')
    if not w:
        return ''
    best = T.best_name(w.upper())
    if not T._names[latin(best)]:
        best = w.upper()
    word = latin(best).capitalize()
    return WORDS.get(word, word)


def main():
    T.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for i, raw in enumerate(entries_raw(book), 1):
        # the OCR's breaks and specks inside the names ("Пер-е", "Никод'е", "·Никоде", "Танасије.Аушан")
        names = [re.sub(r"[-'’·`\[\]—–]", '', re.sub(r'(?<=[^\W\d])\.(?=[^\W\d])', ' ', x or '')) for x in raw['names']]
        sur, rest_names, nick = names[0], names[1].split(), names[2]
        if raw['no'] in HEADS:
            sur, father0, given0 = HEADS[raw['no']]
            rest_names, nick = [father0, given0], ''
        if len(rest_names) > 2 and not nick:                # "Тркуља Танасије Аушан" once the stop is a space
            rest_names = rest_names[:2]
        rest_names = [x[:1].upper() + x[1:] for x in rest_names]
        father, given = (rest_names[0], rest_names[-1]) if len(rest_names) >= 2 else ('', rest_names[0])
        last, first = name_word(sur), name_word(given)
        initial = re.fullmatch(rf'[{UC}A-Z]\.', father)
        fath = '' if not father or initial or mother(father) else WORDS.get(father_word(father), father_word(father))
        nick = name_word(nick) if nick else ''
        name = f"{last} {fath + ' ' if fath else ''}{first}{' – ' + nick if nick else ''}"
        text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', ' '.join(raw['parts']))
        info = name + latin(T.decode_text(re.sub(r'\s+', ' ', text)))
        y = re.search(r'\brođen(?:a|je)?\b(?:(?!Pogin).){0,30}?(?<!\d)(1[89]\d\d)(?!\d)', info, re.I)
        death = death_of(info)
        village = raw['village']
        entries.append({
            'soldier_id': f'{PREFIX}{i:06d}',
            'name': name, 'last_name': last, 'first_name': first, 'nick': nick, 'fathers_name': fath,
            'birth_year': y.group(1) if y else '',
            'born_in': f'{village}, {GRAHOVO}' if village and village != GRAHOVO else GRAHOVO,
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': False,
            'additional_info': info,
            'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, raw['page']), 'source_page': raw['page'] - OFFSET,
            'printed_no': raw['no'],
        })
        counts['entries'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))


if __name__ == '__main__':
    main()
