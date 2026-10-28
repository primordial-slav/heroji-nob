"""
Бијело Поље (Poreklo library, doc 00008716), its Prilozi, as a book across units. Cyrillic, each entry numbered and
hanging, the surname and the given name in capitals:

    "Носиоци Партизанске споменице 1941." (scan pp. 736-756, book pp. 733-753): "1. БАКОЧ (Риста) МИЛОРАД рођен
        1901, Поља, срез колашински, земљорадник. Члан КПЈ од 1939. Борац Мојковачког партизанског батаљона; ...
        Умро 1977." The father in brackets; they lived through the war (`survived`).
    "Списак бораца из среза бјелопољског који су били у строју Треће санџачке бригаде и њеним јединицама на дан
        формирања бригаде 5. јуна 1942. године" (pp. 757-777): "3. ЛУКОВАЦ РАДИСАВ, командант, рођен 1915. Вранеш,
        подофицир југословенске војске, члан КПЈ од јануара 1942." By the staff, the services and each company
        (the headings between: "I. чета"), the duty and, where he fell, his death; no father.
    "Погинули борци" (pp. 781-889): "1. АЛИЛОВИЋ Дашуа РАИФ, борац, рођен 1925, Кукуље, срез бјелопољски,
        земљорадник. У НОБ-у од 1944. Борац Санџачке бригаде КНОЈ-а. Погинуо ... фебруара 1945." The father in the
        genitive between the two names in capitals.
Out: the dead of the April war (p. 890 on), the victims of terror (p. 893 on), not soldiers of this war's army.

The OCR reads the capitals' Ћ as Б (АЛИЛОВИБ), sets Latin look-alikes among them (АРХИПАВЛ OB, Т ОД OP) and spaces
them out (АЛИ ЧКОВИБ): a name is joined, set in Cyrillic and read back as the site spells it (_village_books); names
past reading stay as read. The fallen list's people who were no fighters (an activist, "члан СКОЈ-а, илегалац") are
marked by the mixed lists' rule.

Output: data-extraction/poreklo/bijelo-polje-entries.json, IDs 9095xxxxxx: the spomenica holders from 000001, the
brigade's founding list from 001001, the fallen from 002001, each by the book's number.
Usage: python data-extraction/parse_bijelo_polje.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'bijelo-polje.json'
OUT = HERE / 'poreklo' / 'bijelo-polje-entries.json'
PREFIX = '9095'
OFFSET = 3                                  # scan page minus the book's page (the foot of scan 736 prints 733)
TITLE = 'Bijelo Polje'
LISTS = [('spomenica', range(736, 757), 0, 'Nosioci Partizanske spomenice 1941.'),
         ('fallen', range(781, 890), 2000, 'Poginuli borci')]
UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
TO_CYR = str.maketrans('ABCEHKMOPTXYabceopxy', 'АВСЕНКМОРТХУавсеорху')
SREZ = {'бјелопољ': 'Bijelo Polje', 'колашин': 'Kolašin', 'беран': 'Berane', 'пљеваљ': 'Pljevlja', 'шавнич': 'Šavnik',
        'андријев': 'Andrijevica', 'пријепољ': 'Prijepolje', 'сјенич': 'Sjenica', 'никшић': 'Nikšić',
        'подгорич': 'Podgorica', 'новопазар': 'Novi Pazar', 'рожај': 'Rožaje', 'плав': 'Plav'}
# names past the rules, read from the context, the list's alphabetical order and the Spomenica crnogorskim
# antifašistima's entries of the same people (Lučić Vukašinov Milinko, 1894, Morača; Malagić Etemov Ramo, 1926,
# Nedakusi; Bulatović M. Mileva, 1928, Kolašin): (list, number) -> (surname, father, given name); '' where the print
# gives no reading
NAMES = {('spomenica', 11): ('Bulatović', '', 'Marijan'), ('spomenica', 68): ('Kujović', 'Krsta', 'Leposava'),
         ('spomenica', 86): ('Milačić', 'Milivoja', 'Grujica'), ('spomenica', 109): ('Rakočević', 'Ivana', 'Dimitrije'),
         ('fallen', 32): ('Badžić', 'Hivza', 'Hamid'), ('fallen', 72): ('Bulatović', 'Matije', 'Mileva'),
         ('fallen', 96): ('Vidaković', '', 'Kosa'), ('fallen', 128): ('Vukelić', '', 'Dragan'),
         ('fallen', 222): ('Bačić', '', 'Savo'), ('fallen', 225): ('Đukić', 'Nikole', 'Đoko'),
         ('fallen', 254): ('Žurić', '', 'Milorad'), ('fallen', 298): ('Janković', 'Milete', 'Radisav'),
         ('fallen', 343): ('Knjajević', 'Milete', 'Dobrija'), ('fallen', 377): ('Konatar', '', ''),
         ('fallen', 397): ('Kuvenjić', '', 'Gradojica'), ('fallen', 409): ('Kotlović', 'Latifa', 'Mašo'),
         ('fallen', 437): ('Lučić', 'Vukašina', 'Milinko'), ('fallen', 445): ('Malagić', 'Etema', 'Ramo'),
         ('fallen', 562): ('Perišić', 'Sava', ''), ('fallen', 577): ('Popović', '', 'Stevan'),
         ('fallen', 585): ('Rabrenović', 'Radosava', 'Vasko'), ('fallen', 628): ('Rakočević', 'Novice', 'Blažo'),
         ('fallen', 683): ('Sijarić', 'Salaha', 'Avdulah'), ('fallen', 699): ('Sošić', 'Neđeljka', 'Andrija'),
         ('fallen', 703): ('Stanić', 'Milosava', 'Milija'), ('fallen', 778): ('Cerović', 'Stanoja', 'Radoje')}
NUMBER = re.compile(r'^[·\'\s]*(\d{1,4})\s*[.,-]\s*(.*)$')


def lines(book: dict, pages) -> list[tuple[int, object]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if re.fullmatch(r'\d{3}', t):
                continue                                        # the page number at the foot
            out.append((page, l))
    return out


def is_caps(w: str) -> bool:
    letters = [c for c in w.translate(TO_CYR) if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) >= len(letters) * 0.7


def raw_entries(book: dict) -> list[dict]:
    out = []
    for kind, pages, base, title in LISTS:
        last, cur, section = 0, None, ''
        for page, l in lines(book, pages):
            t = l.text.strip()
            if kind == 'fallen' and 'ПАТРИОТИ' in t:
                break
            m = NUMBER.match(t)
            first_word = m.group(2).split()[0].translate(TO_CYR) if m and m.group(2).split() else ''
            caps_start = bool(re.match(rf'[„"“]?[{UC}]{{2}}|[{UC}]\s', first_word + ' '))
            # an entry's first line hangs out at the left (x > 2300, the text's lines at ~1750); its number as printed
            # where it follows, else the next ("703- СТ ОЖИНИБ" is 708, "7134." 713)
            if m and (int(m.group(1)) == last + 1 and first_word and not re.match(r'[a-zа-я\d]', first_word)
                      or last < int(m.group(1)) <= last + 5 and caps_start
                      or l.x0 > 2300 and caps_start and last and not last < int(m.group(1)) <= last + 5):
                last = int(m.group(1)) if last < int(m.group(1)) <= last + 5 else last + 1
                cur = {'kind': kind, 'base': base, 'list': title, 'no': last, 'page': page, 'section': section,
                       'parts': [m.group(2)]}
                out.append(cur)
            elif kind == 'founding' and not m and l.x0 > 4000 and len(t) < 40 and not t.endswith('.'):
                section = t                                     # "I. чета", "Интендантура и санитет"
            elif cur and cur['kind'] == kind and not re.match(rf'^[{UC} ]{{8,}}$', t):
                cur['parts'].append(t)
    return out


# the OCR's readings of capitals and of the italic fathers: "MHJIOIII" МИЛОШ, "Mu/tosava" Милосава, "Paguboja"
# Радивоја, "Caba" Сава, "Svet03ar" Светозар
CAPS_READ = [('JI', 'Л'), ('Jl', 'Л'), ('J1', 'Л'), ('/I', 'Л'), ('/l', 'Л'), ('/7', 'П'), ('III', 'Ш'), ('IO', 'Ю'),
             ('0', 'О'), ('3', 'З'), ('111', 'Ш'), ('17', 'П')]
ITALIC = str.maketrans('abcegmnopuxy', 'авседтпориху')


def caps_read(w: str) -> str:
    for a, b in CAPS_READ:
        w = w.replace(a, b)
    return w


def father_read(w: str) -> str:
    w = re.sub(r'/[tlrf]|ft', 'л', w)
    w = re.sub(r'(?<=[A-Za-zА-я])u', 'и', w)
    return w[:1].translate(TO_CYR) + w[1:].translate(ITALIC)


def word(w: str, given: bool = False) -> str:
    w = re.sub(r"[^\wЂЈЉЊЋЏђјљњћџ-]", '', caps_read(w).translate(TO_CYR))
    caps = re.match(rf'[{UC}]{{2,}}', w)
    if caps and re.match(rf'[{LC}]', w[caps.end():caps.end() + 1]):
        w = caps.group(0)                       # the duty glued to the name, a comma read as a letter ("ДУШАНјборац")
    if not w:
        return ''
    if not re.search(rf'[{UC}{LC}]', w):
        return w
    return V.given_word(w) if given else V.name_word(w)


def split_head(head: str, kind: str) -> tuple[str, str, str, str]:
    """surname, father, given name, nickname of the name before the first comma or "рођен" """
    nick = ''
    if re.search(r'\s[–—-]\s', head):
        head, nick = re.split(r'\s[–—-]\s', head, 1)
    paren = re.search(r'\(([^)]*)\)', head)
    if paren:                                                   # the spomenica list: "БАКОЧ (Риста) МИЛОРАД"
        sur, fath, given = head[:paren.start()], paren.group(1), head[paren.end():]
        return ' '.join(sur.split()), fath.strip(), ' '.join(given.split()), nick
    # a surname the OCR glued to the father ("ЗЕЈАКНеђељка"): parted where the capitals end
    head = re.sub(rf'(?<=[{UC}]{{2}})(?=[{UC}][{LC}]{{2}})', ' ', head.translate(TO_CYR))
    head = re.sub(rf'(?<=[{LC}])(?=[{UC}]{{2}})', ' ', head)            # the given name glued to the father
    words = head.split()
    title_i = [i for i, w in enumerate(words) if not is_caps(w) and re.match(rf'[{UC}A-Z][{LC}a-z]', w.translate(TO_CYR))]
    if kind == 'fallen' and title_i:                            # "АЛИЛОВИЋ Дашуа РАИФ"
        i = title_i[0]
        return ' '.join(words[:i]), words[i], ' '.join(words[i + 1:]), nick
    caps = [w for w in words if is_caps(w)]
    if len(caps) >= 2:                                          # "ЛУКОВАЦ РАДИСАВ"
        return caps[0], '', ' '.join(caps[1:]), nick
    return ' '.join(words), '', '', nick


def joined(part: str) -> str:
    """a name the OCR spaced out ("АЛИ ЧКОВИБ", "Т ОД OP") as one word"""
    return part.replace(' ', '')


def born_in(info: str) -> str:
    m = re.search(r'rođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?1[89]\d\d[.,]?\s*,?\s*([A-ZČĆŽŠĐ][\w]*(?:\s+[A-ZČĆŽŠĐ][\w]*)?)', info)
    if not m:
        return ''
    place = m.group(1)
    srez = re.search(r'srez[au]?\s+(\w+)', info[m.end():m.end() + 40])
    town = ''
    if srez:
        cyr = srez.group(1)
        town = next((v for k, v in SREZ.items() if V.latin(k) in cyr), '')
    return f'{place}, {town}' if town and town != place else place


def main():
    book = load(BOOK)
    entries, counts = [], Counter()
    for r in raw_entries(book):
        text = re.sub(r'\s+', ' ', V.unhyphen(' '.join(r['parts']))).strip()
        cut = re.search(r',|\s(?:рођен|рођена|роћен)\b', text)
        head, rest = (text[:cut.start()], text[cut.start():]) if cut else (text, '')
        sur, fath, given, nick = split_head(head, r['kind'])
        last = '-'.join(word(joined(p)) for p in re.split(r'\s*[–—-]\s*', sur) if p)
        first = word(joined(given), given=True)
        fath = V.father(father_read(fath)) if fath else ''
        nick = V.read_cyr(nick) if nick else ''
        if (r['kind'], r['no']) in NAMES:
            last, fath, first = NAMES[(r['kind'], r['no'])]
        info = re.sub(r'^[,.\s]+', '', V.read_cyr(rest))
        y = re.search(r'\brođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', info)
        d = V.death(info) if re.search(r'\b(?:[Pp]oginu|[Uu]mr|[Ss]trijelj|[Ss]treljan|[Ub]bij|[Nn]esta)', info) else {}
        role = None
        if r['kind'] == 'fallen' and V.role(info) == 'activist':
            role = 'activist'
        survived = r['kind'] == 'spomenica'
        if survived and d.get('year') and d['year'] <= '1945':
            d = {}                                              # a holder's later death ("Umro 1977") is no fall
        head_text = ' '.join(x for x in (last, f'({fath})' if fath else '', first, ('— ' + nick) if nick else '') if x)
        section = V.read_cyr(r['section']) if r['section'] else ''
        entries.append({
            'soldier_id': f"{PREFIX}{r['base'] + r['no']:06d}", 'name': ' '.join(x for x in (last, fath, first) if x),
            'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': fath,
            'birth_year': y.group(1) if y else '', 'born_in': born_in(info),
            'death_year': d.get('year', '') if not survived else '',
            **({'death_date': d['date']} if d.get('date') and not survived else {}),
            **({'death_place': d['place']} if d.get('place') and not survived else {}),
            'survived': survived, 'units': V.units_of(info) + ([5] if r['kind'] == 'founding' else []),
            **({'role': role} if role else {}),
            'additional_info': f"{r['list']}{', ' + section if section else ''}: {r['no']}. {head_text}, {info}",
            'list': r['list'], 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET})
        counts[r['kind'] + (' activist' if role else '')] += 1
    for kind, *_ in LISTS:
        nos = [int(e['soldier_id'][-3:]) for e in entries if e['list'] == dict((k, t) for k, _, _, t in LISTS)[kind]]
        if nos:
            print(kind, 'gaps:', [n for n in range(1, max(nos) + 1) if n not in nos][:30], 'last', max(nos))
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    print(Counter(u for e in entries for u in e['units']).most_common(12))
    if '--sample' in sys.argv:
        random.seed(7)
        for e in random.sample(entries, min(int(sys.argv[sys.argv.index('--sample') + 1]), len(entries))):
            print(f"  {e['name']} | {e['birth_year']} [{e['born_in']}] † {e['death_year']} {e.get('death_place', '')!r} "
                  f"{e['units']} | {e['additional_info'][:120]}")


if __name__ == '__main__':
    main()
