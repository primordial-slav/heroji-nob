"""
Parser: 3. lička proleterska brigada (brigade code 118).

Source: Đuro Zatezalo (ed.), "3. lička brigada" (465 scan pages), in the Digital library of Poreklo
        (biblioteka.poreklo.rs, collection "Drugi svetski rat"; for members only). The library's OCR text of the
        list pages is kept in data-extraction/poreklo/3-licka.json (poreklo_text.py). Two lists:
        - Prilog br. 2, "Spisak poginulih, umrlih i nestalih boraca 3. ličke proleterske brigade" (scan pages
          366-414, book pp. 361-409), one entry a paragraph, the name in capitals, the father's initial between:
              ZORAJA N. GLISO, iz Pavlovca, Medak, Gospić, poginuo 28. IV 1943. u Brušanima. Sahranjen u Divoselu.
          The editors note they could not check every name, place and date and print them as the author sent them.
        - Prilog br. 3, "Narodni heroji koji su se borili u ovoj brigadi" (scan pages 415-418, book pp. 410-413):
          ten heroes, the name as a heading ("PETAR KESIC BICO": given name first, a nickname after), then a bio.
        Prilog br. 1, the staffs and commands on the day of formation, is not read: its two columns of names and
        duties are partly garbled in the OCR.

The OCR drops the diacritics of capitals (ALEKSIC = Aleksić; restored from the corpus), reads some capitals as the
Cyrillic letters that look like them ("Ј.", "В."), and splits names ("J OVO", "DRAGOLJ UB"; joined back where the
corpus knows the result). There is no scan on the site: records carry `source_url` (the page in the library's viewer)
and `source_page` (the book's page) instead of a PDF position.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, run_parser
from poreklo_text import load, page_lines, printed_page, viewer_url

BOOK = load('3-licka.json')
FALLEN = range(366, 415)
HEROES = range(415, 419)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
MARK = 'ꙮ '                                           # starts an entry (a letter: the scaffold strips leading marks)

# Cyrillic capitals the OCR gives for Latin ones in this Latin book
LOOKALIKE = str.maketrans({'Ј': 'J', 'В': 'B', 'А': 'A', 'Е': 'E', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
                           'Н': 'H', 'К': 'K', 'М': 'M', 'Х': 'X', 'І': 'I',
                           'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y', 'і': 'i', 'ј': 'j'})
ROMAN = r'(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)'
# The head of an entry: the name in capitals (with the father's initial) up to the comma or " iz "
HEAD = re.compile(rf'^(?P<head>[{U}](?:[{U}\-]|\s(?=[{U}])|\s[a-z]\.(?=\s?[{U}])|\.(?=\s?[{U}])|[.\s]{{2}}(?=[{U}]))+?)\.?\s*(?:[,;:]\s*|\s(?=[\'’]?iz\s)|[\s.\'’]*$)')

# Where the heroes were born, read from their bios (the names as the OCR gives them, before the diacritics are restored)
HERO_BIRTHPLACES = {
    ('Babic', 'Petar'): 'Lički Tiškovac, Donji Lapac',          # "u selu Lički Tiškovac, opština Donji Lapac"
    ('Kesic', 'Petar'): 'Gračac',                               # "u Gračacu"
    ('Kuprešanin', 'Milan'): 'Metak, Gospić',                   # "u Metku, opština Gospić"
    ('Novkovic', 'Momčilo'): 'Vrebac, Gospić',                  # "u s. Vrepcu, opština Gospić"
    ('Radakovic', 'Lazo'): 'Mogorić, Gospić',                   # "u selu Mogorić, opština Gospić"
    ('Zaklan', 'Dmitar'): 'Šalamunić, Titova Korenica',         # "u selu Šalamuniću, opština Titova Korenica"
    ('Šijan', 'Milan'): 'Kupirovo, Donji Lapac',                # "u selu Kupirovu, opština Donji Lapac"
    ('Štulic', 'Mirko'): 'Ploča, Gračac',                       # "u selu Ploča, opština Gračac"
}

_last: Counter = Counter()
_first: Counter = Counter()
_spelled: dict[str, Counter] = {'last_name': Counter(), 'first_name': Counter()}
FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def corpus() -> None:
    """Surnames and given names of every other unit on the site: folded to plain capitals, for joining split
    names; as spelled, for giving the capitals back their diacritics"""
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name == '3-licka-soldiers.json':
            continue
        for s in json.loads(f.read_text(encoding='utf-8')):
            for field, folded in (('last_name', _last), ('first_name', _first)):
                v = s.get(field) or ''
                folded[v.upper().translate(FOLD)] += 1
                _spelled[field][v] += 1


def restore(soldiers: list[dict]) -> list[dict]:
    """The capitals lost their diacritics (ALEKSIC, ZIVKO): a name takes the spelling with diacritics that the
    other units use at least five times as often as the plain one (Živko; but Kosta stays, as Košta is not five
    times as common); a surname nobody spells ends in -ić for -ic"""
    by_fold = {f: {} for f in _spelled}
    for field, counts in _spelled.items():
        for v, n in counts.items():
            by_fold[field].setdefault(v.translate(FOLD), Counter())[v] = n
    changed = 0
    for s in soldiers:
        for field in ('last_name', 'first_name'):
            v = s[field]
            cands = by_fold[field].get(v, Counter())
            best = max((c for c in cands if c != v), key=lambda c: cands[c], default=None)
            new = best if best and cands[best] >= 5 * max(cands[v], 1) else v
            if new == v and field == 'last_name' and v.endswith('ic') and not cands[v]:
                new = v[:-2] + 'ić'
            if new != v:
                s[field] = new
                changed += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f'  diacritics restored in {changed} names')
    return soldiers


def clean(text: str) -> str:
    text = text.translate(LOOKALIKE)
    return re.sub(r'^[^\w]+', '', text)                                       # specks before the name: „ ~ ' _


def is_start(text: str) -> bool:
    """A line that opens an entry: a name in capitals; not a date carried over ("IV 1945. u Slatniku")"""
    if re.match(rf'^{ROMAN}\.?\s+\d', text) or re.match(r'^\d', text):
        return False
    m = HEAD.match(text)
    if not m:
        return False
    letters = re.sub(r'[^A-Za-zČĆŽŠĐčćžšđ]', '', m.group('head'))
    return len(letters) >= 5 and sum(c.isupper() for c in letters) >= 0.85 * len(letters) and ' ' in m.group('head').strip()


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out = []
    for page in list(FALLEN) + list(HEROES):
        lines = page_lines(BOOK, page)[0]
        footnote = False
        for i, line in enumerate(lines):
            text = clean(line.text)
            if not text or re.fullmatch(r'[\d\s\'.]+', text):
                continue                                                     # the page number
            if page in FALLEN:
                if text.startswith('*') or footnote:
                    footnote = True                                          # the editors' note under the title
                    continue
                if re.match(r'(?:Prilog|S P I S A K|POGINULIH, UMRLIH|PROLETERSKE BRIGADE)', text):
                    continue
                start = is_start(text)
            else:
                if re.match(r'(?:Prilog|NARODNI HEROJI KOJI)', text):
                    continue
                start = bool(re.fullmatch(rf'[{U}][{U}\s]+', text)) and len(text.split()) >= 2
                if start:
                    text = '§' + text                                        # a hero's heading: given name first
            out.append({'text': (MARK if start else '') + text, 'x': line.x0, 'y': line.top, 'page': page})
    return out


def split_name(words: list[str]) -> tuple[str, str]:
    """Surname and given name from the capitals of a head without an initial; split words joined back where the
    corpus knows the result ("J AKSIC MILAN", "GNJ AJ ALI JULIO")"""
    best, pick = None, (words[0], ' '.join(words[1:]))
    for k in range(1, len(words)):
        last, given = ''.join(words[:k]), ''.join(words[k:])
        score = (min(_last[last], 50) + 1) * (min(_first[given], 50) + 1) - 3 * (len(words) - 2)
        if best is None or score > best:
            best, pick = score, (last, given)
    return pick


def name_parts(head: str) -> tuple[str, str, list[str]]:
    """'ZORAJA N. GLISO' -> ('ZORAJA', 'N', ['GLISO']); 'CURCIC I. MILE I NIKOLA' -> two given names"""
    head = re.sub(r'\s+', ' ', head.replace('..', '.')).strip(' .')
    m = re.match(rf'^(?P<last>[{U}][{U}\- ]*?)\s+(?P<init>[{U}][JA-Z]?|[a-z])\.\s*(?P<given>[{U}].*)$', head)
    if m:
        last = m.group('last').replace(' ', '')
        given = [g.replace(' ', '') for g in re.split(r'\s+I\s+', m.group('given'))]
        return last, m.group('init').upper(), given
    words = head.split()
    if ' I ' in head:                                                        # brothers without the father's initial
        last, rest = words[0], ' '.join(words[1:])
        return last, '', [g.replace(' ', '') for g in re.split(r'\s+I\s+', rest)]
    last, given = split_name(words)
    return last, '', [given]


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '').strip()
    if text.startswith('§'):                                                 # a hero: "PETAR KESIC BICO" + bio
        m = re.match(rf'§(?P<head>[{U}][{U}\s]+?)\s+(?=[{U}][{L}])(?P<bio>.*)$', text)
        words = m.group('head').split()
        given, rest = words[0], words[1:]
        # the surname may be split ("MILAN ŠIJ AN"); what follows it is a nickname ("PETAR KESIC BICO")
        k = max(range(1, len(rest) + 1), key=lambda k: (_last[''.join(rest[:k]).translate(FOLD)] > 0, -k))
        last, nick = ''.join(rest[:k]), rest[k:]
        info = (('zvani ' + ' '.join(w.title() for w in nick) + '; ') if nick else '') + 'narodni heroj; ' + m.group('bio')
        rec = _record(last, given, '', info)
        rec['_list'] = 'heroes'
        return rec
    m = HEAD.match(text)
    head, info = m.group('head'), text[m.end():].strip().lstrip('\'’ ')
    info = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', info)         # "po— ginuo": broken at the line's end
    # "poginuo 23. I 19515. u Ilincima" (Biljetina Nikola): the OCR's year; the brigade's men fell at Ilinci on 23. I 1945
    info = info.replace('23. I 19515. u Ilincima', '23. I 1945. u Ilincima')
    # the book's months are Roman: "14. 1 1944", "24. 11 1945" are the OCR's I and II
    info = re.sub(r'\b(\d{1,2}\.\s?)(1{1,3})(?=\.?\s+19[34]\d)', lambda m: m.group(1) + 'I' * len(m.group(2)), info)
    last, init, given = name_parts(head)
    recs = [_record(last, g, init, info) for g in given]
    for r in recs:
        r['_list'] = 'fallen'
    if len(recs) > 1:
        recs[0]['_also'] = recs[1:]                                          # one entry for two brothers
    return recs[0]


def post(soldiers: list[dict]) -> list[dict]:
    out = []
    for s in soldiers:
        out.append(s)
        out.extend(dict(s, **{k: v for k, v in a.items() if k not in ('additional_info',)}) for a in s.pop('_also', []))
    # The heroes' birthplaces as their bios give them ("u selu Kupirovu, opština Donji Lapac"), in the nominative
    for s in out:
        if s['_list'] == 'heroes' and (s['last_name'], s['first_name']) in HERO_BIRTHPLACES:
            s['birth_place'] = HERO_BIRTHPLACES[(s['last_name'], s['first_name'])]
    # A hero who is also in the list of the fallen is one man with two entries (Sovilj Nikola Nina: "iz Zrmanje,
    # Gračac, poginuo 1. VIII 1944. u Orahovici" and his bio, born in Gubavčevo Polje by Zrmanja, killed 9. VIII
    # 1944 by Prača): same name and the same municipality in both texts
    heroes = [s for s in out if s['_list'] == 'heroes']
    for h in heroes:
        towns = set(re.findall(r'opština ([A-ZČĆŽŠĐ][a-zčćžšđ]+)', h['additional_info']))
        same = [s for s in out if s['_list'] == 'fallen' and (s['last_name'], s['first_name']) == (h['last_name'], h['first_name'])
                and any(t in s['additional_info'] for t in towns)]
        if len(same) == 1:
            same[0]['_merged'] = h
            out.remove(h)
            print(f"  merged the hero {h['last_name']} {h['first_name']} into his entry in the list of the fallen")
    for s in out:
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file', '_list'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
        h = s.pop('_merged', None)
        if h:
            s['other_sources'] = [{'name': f"{h['last_name']} {h['first_name']}", 'additional_info': h['additional_info'],
                                   'source_url': viewer_url(BOOK, h['pdf_page']), 'source_page': printed_page(BOOK, h['pdf_page'])}]
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return restore(out)


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='poreklo/3-licka.json',
        brigade_code=118,
        output_path='website/public/3-licka-soldiers.json',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
