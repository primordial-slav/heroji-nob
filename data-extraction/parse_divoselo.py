"""
Divoselo, Čitluk and Ornice near Gospić (Poreklo library, collection "Monografije sela", Дивосело, Читлук и Орнице у
времену и трајању): the book's lists of the villages' fallen fighters, as a book across units.

    Prilog 12, "Погинули борци Дивосела 1941–1945." (scan pp. 431-437, 112 entries);
    Prilog 13, "Погинули официри Дивосела у НОБ-у 1941–1945." (pp. 438-439);
    Prilog 14, "Погинули борци и официри с. Читлука у НОБ-у 1941–1945." (pp. 440-441);
    Prilog 15, "Погинули борци и официри с. Орнице у НОБ-у 1941–1945." (p. 441).
The book's other lists (the hanged of Čitluk and Lipe, Prilog 10-11; the victims of the Ustaše's pogrom, Prilog 16 on)
are of civilians and stay out. The lists are titled as the villages' fallen fighters and all their entries go in, but
for a soldier of the royal army killed by the Germans in April 1941 (`NOT_FIGHTERS`).

Each entry is a paragraph, numbered from 10 (the OCR lost the numbers 1-9: those start where a line begins with a
surname and a name after a line that ended a sentence): "12. Јерковић Јове Милан–Бабурица, рођен 1922.године у
Дивоселу, засеоак Велики Крај. Погинуо 1942.године као борац 2. батаљона „Пекиша Вуксан“ ...". The name is the
surname, the father in the genitive and the given name, a nickname after a dash; the officers' list often gives the
father in the text ("Бјеговић Никола, учитељ, 40 година, син Бјеговић Стеве и Саре").

The OCR reads this font's л as А or д ("ДивосеАу", "Дивоседу", "Никода"), sets capitals inside words ("МИАан"), Ђ as
"Е (""Еуро"), л as их or /х ("Никоиха", "Михај/ко") and о, б as 0, 6 ("г0дине", "60Анице"): each word is read back as
the spelling the site's records know best among those readings (parse_trebinjci_pali's reader). The scans are
skewed, so the lines are levelled first (parse_ostrvica.level_lines). Entries are kept in Latin.

Output: data-extraction/poreklo/divoselo-entries.json (IDs 9046xxxxxx in the lists' order).
Usage: python data-extraction/parse_divoselo.py [--sample N]
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
from parse_ostrvica import death_of, level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'divoselo.json'
OUT = HERE / 'poreklo' / 'divoselo-entries.json'
PREFIX = '9046'
PAGES = range(431, 442)
OFFSET = 6                                  # scan page minus the book's page
TITLE = 'Divoselo, Čitluk i Ornice u vremenu i trajanju'
LISTS = {
    '12': ('Poginuli borci Divosela 1941–1945.', 'Divoselo, Gospić'),
    '13': ('Poginuli oficiri Divosela u NOB-u 1941–1945.', 'Divoselo, Gospić'),
    '14': ('Poginuli borci i oficiri s. Čitluka u NOB-u 1941–1945.', 'Čitluk, Gospić'),
    '15': ('Poginuli borci i oficiri s. Ornice u NOB-u 1941–1945.', 'Ornice, Gospić'),
}
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# soldiers and gendarmes of the royal army who fell in the April war, whom the list counts among the village's fallen
# ("Poginuo 1941. godine kao vojnik bivše jugoslovenske ... vojske u borbi s Nijemcima", "kao oficir bivše
# jugoslovenske vojske 06. aprila 1941", "u vrijeme agresije na Jugoslaviju")
NOT_FIGHTERS = re.compile(r'(?:vojnik|oficir)\s+bivše\s+jugoslovensk\w+\s+(?:\w+\s+)?vojske[^.]*?(?:1941|Nijemcima)|'
                          r'agresije\s+na\s+Jugoslaviju', re.I)
# men's names in -a (Sava, Laza, Đura), which the site's name lists keep apart from the women's
MEN_A = set(json.loads((HERE.parent / 'website' / 'app' / 'data' / 'name-genders.json').read_text(encoding='utf-8'))['menA'])
NUMBER = re.compile(rf'^(\d[\dОOоЗl]{{0,2}})\s*(?:\.\s*|\s+)(?=["„]?[{UC}])')
DIGITS = str.maketrans('ОOоЗl', '00031')
# an unnumbered entry's first line: a surname and a name (or a father) in capitals, a comma or dash soon after
UNNUMBERED = re.compile(rf'^[{UC}][{LC}{UC}]+\s+["„/(]?[{UC}][^\s,]*(?:\s+\S+){{0,4}}?\s*[,–-]')
NOT_SURNAMES = {'Погинуо', 'Погинула', 'Ступио', 'Ступила', 'Рођен', 'Рођена', 'Убили', 'Ухватиле'}


def pre(text: str) -> str:
    """the OCR's slips the word reader doesn't know: "Еуро (Ђуро), л as их or /х, о and б as 0 and 6"""
    text = re.sub(r'["“”„]\s*Е(?=[{}])'.format(LC), 'Ђ', text)
    text = re.sub(rf'(?<=[{LC}{UC}]),?/[хк]|(?<=о)их(?=[аеу])', 'л', text)
    text = re.sub(rf'(?<=[{LC}{UC}])0|0(?=[{LC}])', 'о', text)
    text = re.sub(rf'(?<=\d)[ОO]|[ОO](?=\d)', '0', text)
    text = re.sub(rf'(?<![\d\w])6(?=[{LC}{UC}]{{3,}})', 'б', text)
    return re.sub(rf'(?<=\d\.)(?=[{LC}{UC}])', ' ', text)                 # "3.бригаде"


def lines(book: dict) -> list[tuple[int, str, str]]:
    """(scan page, list, text) of the lists' lines"""
    out, current = [], None
    for page in PAGES:
        for l in level_lines(page_words(book, page)):
            text = l.text.strip()
            m = re.match(r'Прилог\s+број\s+(\d+)', text)
            if m:
                current = m.group(1) if m.group(1) in LISTS else None
                continue
            if current and not re.fullmatch(r'\d{1,3}', text):
                out.append((page, current, text))
    return out


def number(text: str, last: int) -> re.Match | None:
    """an entry's number, the next of its list or a few on (the OCR loses some), its full stop sometimes lost ("100
    Вујновић"); a line of the text that starts with a number ("6. личке дивизије") is none"""
    m = NUMBER.match(text)
    if not m:
        return None
    n = int(m.group(1).translate(DIGITS))
    return m if 10 <= n and last < n <= max(last, 9) + 8 else None


def entries_raw(book: dict) -> list[dict]:
    out, cur, count, last = [], None, Counter(), Counter()
    for page, lst, text in lines(book):
        m = number(text, last[lst])
        starts = bool(m)
        if not m and count[lst] < 9 and not last[lst]:
            prev = cur['parts'][-1] if cur and cur['list'] == lst else ''
            first = text.split()[0] if text.split() else ''
            # one of the nine entries whose numbers the OCR lost: a surname and a name at the line's start, after a
            # line that ended a sentence, or with the entry's birth, father or age soon after
            starts = (bool(UNNUMBERED.match(text)) and first not in NOT_SURNAMES
                      and (not prev or re.search(r'[.“”"/)]\s*$', prev) or re.search(r'рођен|\bсин\b|годин', text[:90])))
            # the list's title lines stand before its first entry
            if not starts and (cur is None or cur['list'] != lst):
                continue
        if starts:
            count[lst] += 1
            if m:
                last[lst] = int(m.group(1).translate(DIGITS))
            cur = {'list': lst, 'page': page, 'no': str(last[lst]) if m else '',
                   'parts': [text[m.end():] if m else text]}
            out.append(cur)
        elif cur:
            cur['parts'].append(text)
    return out


def join(parts: list[str]) -> str:
    text = ' '.join(parts)
    text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()


def name_word(w: str) -> str:
    """a word of a name as the site spells it"""
    w = w.strip('„“"”/()').strip()
    if not w:
        return ''
    best = T.best_name(w.upper())
    if not T._names[latin(best)]:
        best = T.candidates(w.upper())[0] if re.search('[A-Za-z]', w) else w.upper()   # unknown: as printed
    return latin(best).capitalize() if best else ''


def nominatives(gen: str) -> list[str]:
    """the nominatives a father's genitive can come from: Николе Никола, Саве Саво, Миле Миле, Илије Илија, Јанка
    Јанко, Јована Јован, Петра Петар"""
    stem = gen[:-1]
    if gen.endswith('Е'):
        return [stem + 'А', stem + 'О', gen]
    if gen.endswith('А'):
        return [stem + 'О', stem, stem + 'Е', gen[:-2] + 'АР', gen[:-2] + 'АН']          # and Павла Павле
    return [gen]


def father_word(w: str) -> str:
    """a father's genitive as the site spells it: the reading whose nominative the site's names know best ("Идије" =
    Илије, "Никоде" = Николе)"""
    w = w.strip('„“"”/()').strip()
    if not w:
        return ''
    def score(c):
        return max(T._names[latin(n)] for n in nominatives(c))
    cands = T.candidates(w.upper())
    best = max(cands, key=lambda c: (score(c), -sum(a != b for a, b in zip(c, w.upper()))))
    return latin(best if score(best) else w.upper()).capitalize()


def head_of(text: str) -> dict:
    """surname, father (genitive), given name, nickname from the text before the first comma"""
    head = re.split(r',', text, maxsplit=1)[0]
    head = re.sub(r'/[^/]*/|\([^)]*\)', ' ', head)                          # "/Миле Јанкићев/", "(Миле Божина)"
    # a dash, or the OCR's · and ~ for it, before what he was called
    parts = re.split(r'\s+[–\-·~]\s+|\s*[–-]\s*(?=["„“]?[' + UC + '])', head, maxsplit=1)
    left = parts[0]
    nick = parts[1] if len(parts) > 1 else ''
    words = [w for w in re.split(r'\s+', left.strip('„“" ')) if w.strip('„“"')]
    mother = ''
    if 'и' in words:                                                       # "Дане и Марије Војислав"
        i = words.index('и')
        mother = words[i + 1] if i + 1 < len(words) else ''
        words = words[:i] + words[i + 2:]
    sur = words[0] if words else ''
    father, given, extra = '', '', []
    if len(words) >= 3:
        # a given name ends in a consonant or -о (Душан, Мићо, Максим): "Радаковић Бранко Брања" is Бранко called Брања;
        # a father's genitive in -а or -е ("Јанка", "Николе")
        if re.search(rf'[бвгдђжзклљмнњпрстћфхцчџшо]$', words[1].lower()):
            given, extra = words[1], words[2:]
        else:
            father, given, extra = words[1], words[2], words[3:]
    elif len(words) == 2:
        given = words[1]
    # "Симо–Шима" in one word
    if re.search(r'[–-]', given):
        given, n2 = re.split(r'[–-]', given, maxsplit=1)
        nick = nick or n2
    # what he was called: the word after a dash, or a second name ("Максим Максо Марканов"), not a possessive
    nicks = [x for x in re.split(r'\s+', nick.strip()) if x] + [x for x in extra if not re.search(r'(?:ов|ев|ин)$', x)]
    return {'sur': sur, 'father': father, 'given': given, 'nick': nicks[0] if nicks else '', 'mother': mother}


def mother(gen: str) -> bool:
    """a genitive that is a woman's ("Милице", "Анке", "Јање"): its nominative in -а a woman's name, and no man's name
    the genitive could come from (Миле, Саво)"""
    g = father_word(gen)
    if not g.endswith('e'):
        return False
    stem = g[:-1]
    woman, men = T._given[(stem + 'a').upper()], T._given[(stem + 'o').upper()] + T._given[g.upper()]
    return stem + 'a' not in MEN_A and woman > 5 * men


def father_in_text(text: str, sur: str) -> str:
    """the father the text names: "син Бјеговић Стеве и Саре", "син Марка Бјеговић", "син Стевана Јерковића", the
    man of "син Јање и Марка" """
    m = re.search(rf'\bсин\s+((?:[{UC}][{LC}]+\s+){{0,2}}[{UC}][{LC}]+(?:\s+и\s+[{UC}][{LC}]+)?)', text[:160])
    if not m:
        return ''
    words = [w for w in m.group(1).split() if not w.startswith(sur[:5]) and w != 'и']
    men = [w for w in words if not mother(w)]
    return men[0] if men else ''


def main():
    T.corpus()
    book = load(BOOK)
    entries, counts = [], Counter()
    for raw in entries_raw(book):
        text = pre(join(raw['parts']))
        h = head_of(text)
        if h['father'] and mother(h['father']):
            h['father'] = ''                                               # "Поткоњак Анке Милан": his mother
        if not h['father']:
            h['father'] = father_in_text(text, h['sur'])
        info = latin(T.decode_text(text))
        title, born = LISTS[raw['list']]
        counts[raw['list']] += 1
        if NOT_FIGHTERS.search(info):
            counts['not fighters'] += 1
            continue
        last, first = name_word(h['sur']), name_word(h['given'])
        father, nick = father_word(h['father']), name_word(h['nick'])
        nick = '' if nick == first else nick
        if not last or not first:
            counts['unreadable'] += 1
            print('unreadable:', raw['page'], text[:100])
            continue
        # the birth year after "rođen" ("40 godina" and a death year are none)
        y = re.search(r'\brođena?\b(?:(?!Pogin).){0,60}?\b(1[89]\d\d)\b', info[:200], re.I)
        # the name as read above, where the text's reader spelled it otherwise ("Dučić" for Lučić)
        lead = info.split(' ', 1)
        if lead[0] != last and (lead[0][:1] == last[:1] or lead[0][1:] == last[1:]):
            info = last + (' ' + lead[1] if len(lead) > 1 else '')
        death = death_of(info)
        entries.append({
            'soldier_id': f'{PREFIX}{len(entries) + 1:06d}',
            'name': f"{last} {father + ' ' if father else ''}{first}{' – ' + nick if nick else ''}",
            'last_name': last, 'first_name': first, 'nick': nick, 'fathers_name': father,
            'birth_year': y.group(1) if y else '',
            'born_in': born,
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            'survived': False,
            'additional_info': info,
            'list': title, 'book_title': TITLE,
            'source_url': viewer_url(book, raw['page']), 'source_page': raw['page'] - OFFSET,
        })
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
