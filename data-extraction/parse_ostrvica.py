"""
Ostrvica near Gospić (Poreklo library, collection "Monografije sela", no. 255, Острвица - село Острвица код Госпића):
its census of the village's households in the war, "Попис домаћинстава и чланова породица у Острвици с променама у
току Другог светског рата (1941–1945)", scan pp. 619-665 (the book's 617-663), as a book across units.

Every household of 1 April 1941 (161) is numbered, its head first ("90. Бакић уд. Максима Јања, рођ. Крањчевић, 1890,
домаћица. ..."), the spouse and the children in the head's text, then each child on a line of its own with what
became of him or her ("Миле, 1923. Ступио у НОВ 1941. Борац у саставу Јуришне чете. ..."). Only the war's fighters go
in: a member whose text the fighter rule of the mixed lists takes (parse_mosorski_odred_2.fighter: a borac, a duty in
the army, joined a unit; the book's "stupio u NOB" is its joining the NOV); civilians, the Ustaše's and the Italians'
victims, internees, field workers and the men of the NDH's army stay out (one who went over to the partisans in 1943
goes in, `FIGHTERS`). A member's surname is the household's, the father the head's given name (a widow's husband,
the genitive after "уд."; the head's own father for his brother or sister; the man the text names, "кћерка Марка и
Маре"; none for a grandson or stepson). A kinsman of another surname living with the family ("сестрић Соколин",
"пасторак Божин", a "зет") is left out, since the surname isn't printed, unless the line prints it ("Никола (Нина)
Димић, 1922"). The census says what became of each: a fighter whose text names no death lived through the war.

The scans are skewed by more than a line across the page, so each page's words are levelled before they are grouped
into lines (level_lines), and a line starts an entry by its indent from the page's slanted margin. The OCR reads
italic п as и and т as Ш ("Стуиио", "СаваШовић"), Љ as Њ or Л>, a 1 in a household's number as ], sets a name's
first letter small ("сава, 1924.") and splits a name's first capital off ("Ј ека"); names are read back as the site's
records spell them (parse_seoske_hronike.fix), and heads the OCR garbled past that are typed in `HEADS`.

Output: data-extraction/poreklo/ostrvica-entries.json (IDs 9045xxxxxx in the census's order).
Usage: python data-extraction/parse_ostrvica.py [--sample N]
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
import parse_seoske_hronike as H  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from parse_mosorski_odred_2 import fighter  # noqa: E402
from poreklo_text import lines_of as group_lines, load, page_words, viewer_url  # noqa: E402

BOOK = 'ostrvica.json'
OUT = HERE / 'poreklo' / 'ostrvica-entries.json'
PREFIX = '9045'
PAGES = range(619, 666)
OFFSET = 2                                  # scan page minus the book's page
LIST = 'Popis domaćinstava i članova porodica u Ostrvici s promenama u toku Drugog svetskog rata (1941–1945)'
TITLE = 'Ostrvica: selo Ostrvica kod Gospića'
BORN_IN = 'Ostrvica, Gospić'

UC, LC = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'
# a household's number (the OCR reads a 6 as б, "б. Димић уд. Николе Сава"), then the surname
HOUSE = re.compile(rf'^((?:\d|\](?=\.?\s)|б(?=\.)){{1,3}}[аб]?)\s*\.?\s+(?=[{UC}])')   # and a 1 as ] ("10] Радмановић")
# a head's name the OCR garbled past reading: (surname, father, given) as printed, or None for "not known"
HEADS = {'95': ('Судар', 'Илије', None),              # "Судар Илије 1060": the given name is lost
         '87': ('Бакић', 'Дмитра', 'Симо'),           # "Бакић Дмии7ра Симо"
         '101': ('Радмановић', 'Илије', 'Божо')}      # "Радмановић Илије Бджо"
# heads the fighter rule takes for their old army ranks who were no partisans: Boris Škljarevski, an officer of the
# tsar's army and the village's teacher, who moved away with his family in May 1941
NOT_FIGHTERS = {'86'}
# members the rule misses: a gendarme of the NDH who went over to the Dalmatian partisans at the end of 1943 and
# fought with them to the war's end
FIGHTERS = {('84', 'Миле')}
# the book says "joined the NOB" of those who joined the army ("Ступила у НОБ јуна 1943. Телефонисткиња у 3.
# бригади"), which the fighter rule reads as the movement: read as the NOV
JOINED = re.compile(r'\b(Stupi(?:o|la|li)\s+u\s+)NOB\b')
# a member's line: a given name (two joined by a dash, a nickname in brackets), then a comma or full stop or the
# year ("Максим 1903."); some print the year only after a widow's or maiden name ("Стана, уд. Јована, рођ. Јелић;
# 1874"), some none at all ("Ката, дете.", "Пере, молер. Ступио у НОВ 1944.")
MEMBER = re.compile(rf'^\??([{UC}][{LC}]+(?:\s*[–-]\s*\(?[{UC}][{LC}]+\)?)?)\s*(\([^)]{{1,20}}\))?\s*(?:[,.;]|(?=1[89]\d\d))')
# a kinsman of another surname prints it, and the year ("Никола (Нина) Димић, 1922, син Буре Алексиног")
MEMBER_SURNAME = re.compile(rf'^\??([{UC}][{LC}]+)\s*(\([^)]{{1,20}}\))?\s+([{UC}][{LC}]+)\s*,\s*(?:око\s+)?(1[89]\d\d)\b')
# the OCR set the first letter small ("сава, 1924.", "љуба, 1935."): only with the year right after it
MEMBER_SMALL = re.compile(rf'^([{LC}]{{3,}})\s*[,.]\s*(1[89]\d\d)\b')
# what follows a member's name before the year: a widow's husband, a maiden name, a kinship ("мајка Милетина")
YEAR = re.compile(rf'^[,.;]?\s*(?:(?:уд\.?|рођ\.?)\s*\??[{UC}{LC}]+\s*[,.;]\s*)*(?:око\s+)?(1[89]\d\d)\b')
NOT_NAMES = {'Кћерка', 'Кћерке', 'Кћи', 'Син', 'Синови', 'Супруга', 'Супруг', 'Ступио', 'Ступила', 'Погинуо',
             'Погинула', 'Умро', 'Умрла', 'Убиле', 'Убили', 'Заклале', 'Сахрањен', 'Сахрањена', 'Острвици'}
OTHER_KIN = re.compile(r'сестрић|сестричин|\bзет\b|снаха|пасторак|пасторка|кћерка\s+\w+ин[аое]?\b|син\s+\w+ин\b')
# a death in the war: the verb, then its day ("14. jula 1942", "početkom decembra 1944", "1943") within its sentence
# (the day's own full stops end none); a man mortally wounded who died later dies on the later day
DEATH = re.compile(r'\b(?:pogin[uj]\w*|umr[oal]\w*|ubi(?:jen\w*|l[aei]|o)|strelja\w*|nesta[ol]\w*|zaklal\w*|obesil\w*|'
                   r'podlega?\w*|smrtno ranjen\w*)\b', re.I)
WHEN = re.compile(r'(?:(\d{1,2})\.\s*)?(?:(januar|februar|mart|april|maj|jun|jul|avgust|septembar|septembr|oktobar|'
                  r'oktobr|novembar|novembr|decembar|decembr)\w*\s+)?(19[34]\d)\b')
MONTHS = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septemb', 'oktob', 'novemb', 'decemb']
FAMILY = re.compile(r'\b(?:Supruga|Suprug|Sinovi|Sin|Kćerke|Kćerka|Kći)\b')


def clean(text: str) -> str:
    text = re.sub(rf'(?<![{UC}{LC}])([{UC}]) (?=[{LC}]{{2,}})', r'\1', text)             # "Ј ека"
    text = re.sub(r"^[\"'’`·.,]+\s*", '', text)
    # the scan's specks ("1909,'земл>орадник. ·Краће", "._Погинуо", "· · ·-") and Љ read as Л>
    text = text.replace('л>', 'љ').replace('Л>', 'Љ')
    text = re.sub(r"(?<=[,.])['’`]|[·•_]", ' ', text)
    text = re.sub(r'(?:\s+[-–])+\s*$', '', text)
    # italic п read as и at a word's start or after a vowel ("Суируга", "аирила", "ио–моћи"): the common words only
    for wrong, right in (('Суируг', 'Супруг'), ('аирил', 'април'), ('ирил', 'прил'), ('иосле', 'после'),
                         ('ирилико', 'прилико'), ('сеит', 'септ'), ('неиоз', 'непоз'), ('Пеиица', 'Пепица'),
                         ('Паниић', 'Панић')):
        text = text.replace(wrong, right)
    text = re.sub(rf'(?<![{UC}{LC}])и(?=[ор]|а(?!ко)|у[тШ])', 'п', text)   # "иородица", "иребегао" (not "иако")
    text = re.sub(r'уи(?=и)', 'уп', text)                                   # "Стуиио"
    # italic т read as Ш, and capitals inside a word ("СаваШовић", "иочеШКом", "наПусШио")
    text = re.sub(rf'(?<=[{LC}])Ш', 'т', text)
    text = re.sub(rf'(?<=[{LC}])([ПК])(?=[{LC}])', lambda m: m.group(1).lower(), text)
    return re.sub(rf'(?<![{UC}{LC}])Њуб', 'Љуб', text)                      # "Њубица"


def margin(lines) -> tuple[float, float]:
    """The page's left margin as a slanted line, x = a + b * top (the scans are skewed by up to 100 px a page): fitted
    to the lines that start at it, the lower cluster of the lines' left edges"""
    def fit(pts):
        n = len(pts)
        mt, mx = sum(t for t, _ in pts) / n, sum(x for _, x in pts) / n
        var = sum((t - mt) ** 2 for t, _ in pts)
        b = sum((t - mt) * (x - mx) for t, x in pts) / var if var else 0.0
        return mx - b * mt, b
    pts = [(l.top, l.x0) for l in lines]
    cut = median(x for _, x in pts)
    a, b = fit([p for p in pts if p[1] <= cut] or pts)
    for _ in range(2):
        low = [p for p in pts if p[1] < a + b * p[0] + 60]
        if len(low) >= 3:
            a, b = fit(low)
    return a, b


def level_lines(words) -> list:
    """the page's lines with its skew taken out: a line of a skewed scan climbs or falls across the page by more than
    its height, and grouped as it lies it takes words of the line above or below ("Огњен При– / Погинуо ... / ца“.").
    The slope is the one under which the words' middles stack up best (a projection profile), and each word is moved
    up or down by it before the words are grouped"""
    if not words:
        return []
    h = median(w.height for w in words) or 1
    left = min(w.x0 for w in words)

    def score(s):
        bins = Counter(round((w.middle - s * ((w.x0 + w.x1) / 2 - left)) / (h / 4)) for w in words)
        return sum(n * n for n in bins.values())
    slope = max((k / 1000 for k in range(-60, 61, 2)), key=score)
    for w in words:
        shift = slope * ((w.x0 + w.x1) / 2 - left)
        w.top, w.bottom = w.top - shift, w.bottom - shift
    return group_lines(words)


def lines_of(book: dict) -> list[tuple[int, bool, str]]:
    """(scan page, indented, text) of the census's lines, page by page: an entry's first line stands about 250 px in
    from the page's margin, its other lines at it"""
    out = []
    for page in PAGES:
        lines = [l for l in level_lines(page_words(book, page)) if not re.fullmatch(r'\s*\d{1,3}\s*', l.text)]
        for l in lines:
            # a speck read in the margin before the line's first word ("' Милош (Брацо), 1929.") is not where it starts
            real = [w for w in l.words if re.search(r'\w', w.text)]
            if real and real[0] is not l.words[0]:
                l.x0 = real[0].x0
                l.text = ' '.join(w.text for w in l.words[l.words.index(real[0]):])
        if not lines:
            continue
        a, b = margin(lines)
        for l in lines:
            out.append((page, l.x0 - (a + b * l.top) > 150, clean(l.text.strip())))
    return out


def join(parts: list[str]) -> str:
    text = ' '.join(parts)
    text = re.sub(r'(\w)[–—-]\s+(\w)', r'\1\2', text)                  # words broken over lines
    return re.sub(r'\s+', ' ', text).strip()


def start_of_member(text: str) -> dict | None:
    """a member's given name, nickname, own surname (if printed) and birth year, if the line starts one"""
    m = MEMBER_SURNAME.match(text)
    if m and m.group(1) not in NOT_NAMES:
        return {'given': m.group(1), 'nick': m.group(2) or '', 'sur': m.group(3), 'year': m.group(4), 'text': text}
    m = MEMBER_SMALL.match(text)
    if m:
        given = m.group(1)[0].upper() + m.group(1)[1:]
        return {'given': given, 'nick': '', 'sur': '', 'year': m.group(2), 'text': given + text[len(m.group(1)):]}
    m = MEMBER.match(text)
    if m and m.group(1) not in NOT_NAMES and len(m.group(1)) > 2:
        y = YEAR.match(text[m.end(2) if m.group(2) else m.end(1):])
        return {'given': m.group(1), 'nick': m.group(2) or '', 'sur': '', 'year': y.group(1) if y else '',
                'text': text.lstrip('?')}
    return None


def records(book: dict) -> list[dict]:
    """households and their members, in the census's order"""
    out, house, cur = [], None, None
    started = False
    for page, indented, text in lines_of(book):
        m = HOUSE.match(text) if indented or not started else None
        if m and (started or m.group(1) == '1'):
            started = True
            house = {'no': m.group(1).replace('б', '6').replace(']', '1'), 'page': page, 'parts': [text[m.end():]],
                     'kin': False}
            cur = house
            out.append(cur)
            continue
        if not started:
            continue
        member = start_of_member(text) if indented and house else None
        if member:
            text = member.pop('text')
            cur = {'house': house, 'page': page, 'parts': [text], **member,
                   'kin': not member['sur'] and (house['kin'] or bool(OTHER_KIN.search(text)))}
            out.append(cur)
            continue
        if indented and house and cur is house and re.match(r'У овој породици|Са њима|Код њих', text):
            house['kin'] = True                     # "У овој породици су ... живела и деца пок. Милана Мандарића"
        if cur is not None:
            cur['parts'].append(text)
    return out


def head_of(house: dict) -> dict:
    """the head's surname, father (genitive as printed), given name, whether a woman, and the children's father"""
    text = join(house['parts'])
    # the name ends at the first comma or semicolon ("Радмановић Саве Петар; 1903"), not the one after "уд;"
    cut = re.search(r'(?<!уд)[,;]', text)
    name, rest = (text[:cut.start()], text[cut.end():]) if cut else (text, '')
    nick = re.search(r'\(([^)]+)\)', name)                                      # "Половина Милан (Милчић)"
    name = re.sub(r'\s*\([^)]*\)', ' ', name)
    words = [w.lstrip('?') for w in re.split(r'\s+', name.strip()) if w.lstrip('?')]
    words = [w[0].upper() + w[1:] for w in words]                                 # "Петковић саве Јован"
    widow = any(re.fullmatch(r'уд[.;]?', w, re.I) for w in words)
    words = [w for w in words if not re.fullmatch(r'уд[.;]?', w, re.I)]
    sur = words[0] if words else ''
    father, given = '', ''
    if len(words) >= 3:
        father, given = words[1], ' '.join(words[2:])
    elif len(words) == 2:
        given = words[1]
    if house['no'] in HEADS:
        sur, father, given = (x or '' for x in HEADS[house['no']])
    # a woman heads the household: a widow ("уд."), or her maiden name right after hers ("Пера, рођ. Теслић")
    woman = widow or bool(re.match(r'\s*рођ\.', rest))
    return {'sur': sur, 'father': father, 'given': given, 'nick': nick.group(1) if nick else '', 'woman': woman,
            # the children's father: the head himself, or the husband a woman's genitive names
            'kids_father': father if woman else given, 'kids_father_genitive': woman, 'text': text}


def nominative(gen: str) -> str:
    """a father's genitive in the nominative the site's names know best: Maksima Maksim, Ilije Ilija, Đure Đuro"""
    if not gen:
        return ''
    import parse_trebinjci_pali as T
    if not T._names:
        T.corpus()
    stem = gen[:-1]
    cands = ([stem + 'a', stem + 'o', gen] if gen.endswith('e') else
             [stem + 'o', stem, stem + 'e', gen[:-2] + 'ar', gen[:-2] + 'an', gen[:-2]] if gen.endswith('a') else [gen])
    if gen.endswith('eta'):                     # Mileta Mile, Daneta Dane; Gnjatija Gnjatije, Tanasija Tanasije
        cands = [gen[:-2]]
    elif gen.endswith('ija'):
        cands = [gen[:-1] + 'e', gen]
    best = max(cands, key=lambda c: T._names[c.upper()])
    return best if T._names[best.upper()] else gen


def death_of(info: str) -> dict:
    """the year, day (ISO, when printed whole) and place of a fighter's death in the war, from his own text: what
    follows his wife or children ("Supruga Sava ... Ubile je ustaše") is theirs"""
    own = FAMILY.split(info)[0]
    found = {}
    for verb in DEATH.finditer(own):
        span = own[verb.end():verb.end() + 160]
        # the sentence's end: a full stop after a word ("u s. Vrebac" is none) or a year
        end = re.search(r'(?<=[^\W\d]{2})\.\s+[A-ZČĆŽŠĐ]|(?<=\d{4})\.\s+[A-ZČĆŽŠĐ]', span)
        span = span[:end.start() + 1] if end else span
        if re.search(r'\b(?:19[5-9]\d|20\d\d)\b', span):
            continue                                                # "Umro 1967. u Gospiću": after the war
        when = WHEN.search(span)
        if not when:
            if not found:
                found = {'year': '', 'date': '', 'place': ''}      # a death without a year ("Vreme ... nepoznati")
            continue
        day, month, year = when.groups()
        place = ''
        before = span[:when.start()]
        # where: the first place after "u" or "na" ("u Mihaljevcu kod Korenice"), else after "kod" ("na položaju kod
        # Metka"), in the case the book prints it
        at = [m for p in (r'u|na', r'kod') for m in
              re.finditer(rf'\b(?:{p})\s+([A-ZČĆŽŠĐ][\w–-]*(?:\s+[A-ZČĆŽŠĐ][\w–-]*)?)', before)]
        if at:
            place = at[0].group(1)
        date = ''
        if day and month:
            m = next(i for i, x in enumerate(MONTHS) if month.startswith(x[:5]) or x.startswith(month[:5])) + 1
            date = f'{year}-{m:02d}-{int(day):02d}'
        found = {'year': year, 'date': date, 'place': place}
        if not re.match(r'smrtno', verb.group(0), re.I):
            break                                                   # the first death; a mortal wound waits for "Umro"
    return found


def father_of(text: str, member: dict, head: dict) -> tuple[str, bool]:
    """a member's father and whether he is printed in the genitive: the head (or a widow's husband) by default; the
    head's own father for a brother or sister of the head ("Милан, 1913, подофицир, брат Исин"); the man the text
    names ("кћерка Марка и Маре", "син Исиног брата Тоде", "син Буре Алексиног"); none for a grandchild, or a kinsman
    of another surname whose text names only the mother"""
    start = text[:80]
    named = (re.search(rf'\bбрата\s+([{UC}][{LC}]+)', start)
             or re.search(rf'\b(?:син|кћерка|кћи)\s+([{UC}][{LC}]+[аеи])\b(?!\s*,\s*рођ)', start))
    if named and not re.search(r'(?:ин|ов|ог)$', named.group(1)):
        return named.group(1), True
    if member['sur'] or re.search(r'\bунук|\bпосин', start):
        return '', False
    sib = re.search(rf'\b(?:брат|сестра)\s+["„]?([{UC}{LC}]+)', start)
    stem = min(3, len(head['given']) - 1)                  # "брат Исин" of Исо, "брат Павлов" of Павле
    if sib and head['given'] and sib.group(1)[:stem].lower() == head['given'][:stem].lower():
        return head['father'], True
    return head['kids_father'], head['kids_father_genitive']


def main():
    H.corpus()
    book = load(BOOK)
    recs = records(book)
    entries, counts = [], Counter()
    houses = {}
    for r in recs:
        if 'no' in r:
            houses[id(r)] = head_of(r)
            counts['households'] += 1
    for r in recs:
        if 'no' in r:
            h = houses[id(r)]
            text = h['text']
            own = re.split(r'\b(?:Супруга|Супруг|Синови|Син|Кћерке|Кћерка|Кћи)\b', text)[0]
            sur, father, given, nick, year = h['sur'], h['father'], h['given'], h['nick'], ''
            y = re.search(r'\b(1[89]\d\d)\b', own)
            year = y.group(1) if y else ''
            person_text, house_no = own, r['no']
            label = f'Domaćinstvo {house_no}'
            # a woman's genitive is her husband's name, not her father's
            father_shown = H.fix(father) if father and not h['woman'] else ''
        else:
            h = houses[id(r['house'])]
            if r['kin']:
                counts['other kin left out'] += 1
                continue
            sur, given, nick, year = r['sur'] or h['sur'], r['given'], (r['nick'] or '').strip('()'), r['year']
            person_text, house_no = join(r['parts']), r['house']['no']
            # the father: a widow's husband in the genitive as printed, else the head in the nominative, in brackets
            # as the census of 1964 writes a father it gives in the nominative
            father, genitive = father_of(person_text, r, h)
            father_shown = H.fix(father) if father else ''
            if father_shown and not genitive:
                father_shown = f'({father_shown})'
            label = f"Domaćinstvo {house_no} ({' '.join(H.fix(x) for x in (h['sur'], h['father'], h['given']) if x)})"
        info = latin(person_text)
        taken = (fighter({'additional_info': JOINED.sub(r'\1NOV', info)})
                 or ('no' not in r and (r['house']['no'], r['given']) in FIGHTERS))
        if not taken or ('no' in r and r['no'] in NOT_FIGHTERS):
            counts['not fighters'] += 1
            continue
        if not sur or not given:
            counts['unreadable'] += 1
            continue
        given_parts = re.split(r'\s*[–-]\s*', given.strip('()'))
        first = H.fix(given_parts[0])
        nick = nick or (given_parts[1].strip('()') if len(given_parts) > 1 else '')
        last = H.fix(sur)
        death = death_of(info)
        entries.append({
            'soldier_id': f'{PREFIX}{len(entries) + 1:06d}',
            'name': f"{last} {father_shown + ' ' if father_shown else ''}{first}{' – ' + H.fix(nick) if nick else ''}",
            'last_name': last, 'first_name': first, 'nick': H.fix(nick) if nick else '',
            # a member's father is the head's given name in the nominative (or a widow's husband in the genitive)
            # in the nominative (the bracketed head's name, or a genitive the census prints read back), as Ostali
            # borci takes this book's fathers (build_ostali_borci.NOMINATIVE_FATHERS)
            'fathers_name': father_shown.strip('()') if father_shown.startswith('(') else nominative(father_shown),
            'birth_year': year, 'born_in': BORN_IN,
            'death_year': death.get('year', ''),
            **({'death_date': death['date']} if death.get('date') else {}),
            **({'death_place': death['place']} if death.get('place') else {}),
            # the census gives what became of each in the war: a fighter whose text names no death lived through it
            'survived': not death,
            'additional_info': f'{label}: {info}',
            'list': LIST, 'book_title': TITLE,
            'source_url': viewer_url(book, r['page']), 'source_page': r['page'] - OFFSET,
        })
        counts['fighters'] += 1
        counts['heads' if 'no' in r else 'members'] += 1
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(entries))
    if '--sample' in sys.argv:
        n = int(sys.argv[sys.argv.index('--sample') + 1])
        import random
        random.seed(1)
        for e in random.sample(entries, min(n, len(entries))):
            print(f"{e['soldier_id']} p.{e['source_page']} | {e['name']} | {e['birth_year']} | d.{e['death_year']} "
                  f"surv={e['survived']} | {e['additional_info'][:150]}")


if __name__ == '__main__':
    main()
