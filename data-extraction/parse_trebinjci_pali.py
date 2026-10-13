"""
Trebinjci pali u borbi za slobodu 1941-1945 (SUBNOR Trebinje, 1974; biblioteka.poreklo.rs): a book across units, its
entries added to the records of the soldiers it describes (see scripts/match_references.py), as the hero books are.

The book has three lists; two are fighters and are read here:
    "Pali borci" (book pp. 13-96, scan pages 18-101): the fighters of the Trebinje municipality who fell, with birth,
        father, units and death;
    "Borci iz Jugoslavije, poginuli na području Trebinja" (book pp. 159-174, scan pages 182-197): fighters from
        elsewhere who fell around Trebinje.
The third, "Žrtve fašističkog terora" (book pp. 97-156), is of civilians and stays out.

The OCR reads this font's Л (printed like a Greek lambda) as А or д ("сеАу", "седу" = селу; "ААНИАО" = ДАНИЛО, its Д
the same shape), the capital Ћ as Б ("ГБАБИБ" = АГБАБИЋ), Љ as "Ао" and some words in Latin look-alikes ("AaAMaTHHCKe"
= далматинске). Each word is read back as the spelling the site's records know best among those readings, the names
from the site's names, the rest from the words of every record's text and the book's own unambiguous words. The first
entry of each letter starts under a drop cap the OCR leaves out: its first line stands indented, and it takes the
initial of the entry after it. Entries are kept in Latin, as the site's records are.

Output: data-extraction/poreklo/trebinjci-pali-entries.json (IDs 9003xxxxxx), with the fields the matcher reads:
last_name, first_name, fathers_name (the possessive the book prints: "Muharemov"), birth_year, born_in, death_year,
survived (always false), additional_info (the entry after the name), source_url, source_page, list.

Usage: python data-extraction/parse_trebinjci_pali.py [--sample N]
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from poreklo_text import load, page_lines, viewer_url  # noqa: E402

BOOK = 'trebinjci-pali.json'
OUT = HERE / 'poreklo' / 'trebinjci-pali-entries.json'
PREFIX = '9003'
# (scan pages, scan page minus the book's page, the list)
LISTS = [(range(18, 102), 5, 'Pali borci'),
         (range(182, 198), 23, 'Borci iz Jugoslavije, poginuli na području Trebinja')]

UC = 'АБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШ'
LC = UC.lower()
# the OCR's readings of a letter, the letter first
OPTS = {'А': 'АЛД', 'Б': 'БЋЂ', 'д': 'дл', 'Д': 'ДЛ', 'ћ': 'ћђ', 'Ћ': 'ЋЂ',
        # Latin look-alikes in Cyrillic words
        'A': 'АЛД', 'a': 'а', 'B': 'ВБ', 'C': 'С', 'c': 'с', 'E': 'Е', 'e': 'е', 'H': 'НИП', 'h': 'н', 'K': 'К',
        'k': 'к', 'M': 'М', 'm': 'м', 'O': 'О', 'o': 'о', 'P': 'Р', 'p': 'р', 'T': 'Т', 'X': 'Х', 'x': 'х',
        'Y': 'У', 'y': 'у', 'J': 'Ј', 'j': 'ј', 'n': 'п', 'u': 'и', 'r': 'г'}

_names: Counter = Counter()      # NAME as spelled on the site, upper-case Latin
_words: Counter = Counter()      # words of the site's texts, as spelled (case kept)
_lower: Counter = Counter()      # the same, lower-case
_prefix: Counter = Counter()     # their first six letters, for a word the site has only in another case
_given: Counter = Counter()      # the site's given names alone


def corpus() -> None:
    for f in (HERE.parent / 'website' / 'public').glob('*soldiers.json'):
        for s in json.loads(f.read_text(encoding='utf-8')):
            for k in ('last_name', 'first_name'):
                for w in re.split(r'[\s-]+', s.get(k) or ''):
                    if w:
                        _names[w.upper()] += 1
                        if k == 'first_name':
                            _given[w.upper()] += 1
            text = ' '.join(s.get(k) or '' for k in ('additional_info', 'birth_place', 'death_place', 'unit_detail'))
            for w in re.findall(r'[A-Za-zČĆŽŠĐčćžšđ]+', text):
                add(w)


def add(w: str, n: int = 1) -> None:
    _words[w] += n
    _lower[w.lower()] += n
    if len(w) >= 6:
        _prefix[w.lower()[:6]] += n


def book_words(book: dict) -> None:
    """The book's own words that no OCR confusion touches (its villages: "Домашеву", "Добромани")"""
    for pages, _, _ in LISTS:
        for page in pages:
            for col in page_lines(book, page, 2):
                for line in col:
                    for w in re.findall(r'[А-Яа-яЂЈЉЊЋЏђјљњћџ]+', line.text):
                        if not re.search('[АБдДћЋ]', w):
                            add(latin(w))


def candidates(word: str, limit: int = 400) -> list[str]:
    """Every reading of a word: each ambiguous letter as each of the letters the OCR gives it for, "Ао" as Љ"""
    words = {word}
    # Љ read as "Ао": ВЕАоКО = ВЕЉКО, Аоубомир = Љубомир; but Аомашеву is Домашеву, so both readings are kept
    words.add(re.sub(r'(?<=[А-ЯЂЈЉЊЋЏ])[АA][оoО](?=[А-ЯЂЈЉЊЋЏ]|$)', 'Љ', word))
    words.add(re.sub(r'^[АA][оo](?=[а-яђјљњћџ])', 'Љ', word))
    for w in list(words):
        words.add(re.sub(r'[АA]\)', 'Љ', w))                                       # ГУАЕА) = ГУДЕЉ
        words.add(re.sub(r'^[АA][ОO]', 'Љ', w))                                   # АОУБО = ЉУБО
        words.add(re.sub(r'[АA][ЗзZ3]', 'Љ', w))                                  # ВЕАЗКО = ВЕЉКО
        words.add(re.sub(r'(?<=[ИI])[ВНЕBHEe]$', 'Ћ', w))                         # -ИВ, -ИН, -ИЕ for -ИЋ
        words.add(w.replace('Њ', 'Љ').replace('њ', 'љ'))                          # ЊУБИБРАТИЋ = ЉУБИБРАТИЋ
    out = []
    for w in words:
        slots = [OPTS.get(ch, ch) for ch in w]
        n = 1
        for s in slots:
            n *= len(s)
        out += [''.join(s[0] for s in slots)] if n > limit else [''.join(p) for p in itertools.product(*slots)]
    return list(dict.fromkeys(out))


def latin(cyr: str) -> str:
    return cyrillic_to_latin(cyr)


def best_name(word: str) -> str:
    """A word of a name in capitals: the reading the site's names know best; -ИБ is -ИЋ"""
    if not word or not re.search(f'[{UC}A-Z]', word):
        return word
    cands = candidates(word.upper().replace('O', 'О'))
    scored = max(cands, key=lambda c: (_names[latin(c)], c.endswith('ИЋ'), -sum(a != b for a, b in zip(c, word))))
    if _names[latin(scored)]:
        return scored
    return re.sub(r'ИБ$', 'ИЋ', candidates(word.upper())[0])


def best_word(word: str) -> str:
    """A word of the text: the reading the site's words know best (case as the site writes it); else as read, with
    an А inside a lower-case word read as л"""
    if not re.search('[АБдДћЋAaBCcEeHhKkMmOoPpTXxYyJjnur]', word):
        return word
    caps = len(word) > 1 and not re.search('[а-яђјљњћџa-z]', word[1:].replace('о', '').replace('o', ''))
    cands = candidates(word)
    if not caps:
        # a lower-case word: its letters after the first are lower case whatever the OCR gave ("сеАу" -> селу)
        cands = list(dict.fromkeys(c[:1] + c[1:].lower() for c in cands))
    pool = []
    for c in cands:
        low = latin(c).lower()
        n = _lower[low]
        if not n and len(low) >= 7:
            n = _prefix[low[:6]] / 100           # the site has the word only in another case ("Domaševu")
        if n:
            cap = latin(c)[:1].upper() + latin(c)[1:].lower()
            # a capital where the site writes one ("Luka", "Lastva", "Ljubomir", also found in lower case), lower
            # case where it hardly does ("legionarske"); a word the OCR began in lower case stays so
            if caps:
                form = c
            elif word[:1] in 'АAБ' or re.match('[A-Za-z]', word):
                # known only by its first letters (a village in another case): a name, so a capital
                lower_case = _words[low] and _words[cap] <= 0.3 * _words[low] or not _words[low] and _words[cap] == 0 and _lower[low]
                form = c[:1].lower() + c[1:] if lower_case else c
            else:
                form = c[:1].upper() + c[1:] if word[:1].isupper() else c[:1].lower() + c[1:]
            pool.append((n, -sum(a != b for a, b in zip(c, word)), form))
    if pool:
        return max(pool)[2]
    return word if caps else word[:1] + re.sub('[АA]', 'л', word[1:]).lower()


ROMAN = str.maketrans({'Х': 'X', 'П': 'II', 'Ш': 'III', '1': 'I', 'l': 'I', 'І': 'I'})
UNIT_WORD = r'(?:херцег|бригад|далмат|пролет|корпус|дивиз|батаљ|офанз|црногор|санџа|ударн|крајиш|босан|хрватс|српск)'


def romans(text: str) -> str:
    """Month and unit numerals, which the OCR gives in Cyrillic look-alikes ("ХП херцеговачке" = XII, "16. Ш 1942" =
    16. III 1942), in Latin capitals"""
    tok = r'(?<![\w])([IVXХПШ1lІ]{1,5})(?![\w])'
    text = re.sub(rf'(\d{{1,2}}\.\s*){tok}(?=\.?\s*(?:19\d\d|\d{{2}}\b))', lambda m: m.group(1) + m.group(2).translate(ROMAN), text)
    return re.sub(rf'{tok}(?=\s+{UNIT_WORD})', lambda m: m.group(1).translate(ROMAN), text, flags=re.I)


POSSESSIVE = re.compile(r'(ов|ев|ин|ова|ева|ина)$')
# the areas of the Trebinje municipality the book names a village by, by their first four letters folded ("Ponovo
# polje", "Zubni" as the OCR gives them included)
_FOLD = str.maketrans('ČĆŽŠĐčćžšđ', 'CCZSDcczsd')


def fold4(place: str) -> str:
    return re.sub(r'[^a-z ]', '', place.translate(_FOLD).lower())[:4]


TREBINJE_AREAS = {fold4(a) for a in ('Popovo polje', 'Ponovo polje', 'Zubci', 'Zubni', 'Trebinjska šuma',
                                     'Trebinjska brda', 'Bobani', 'Lastva', 'Ljubomir', 'Dživar', 'Površ', 'Zagora')}


def best_father(word: str) -> str:
    """The father's name the book gives as a possessive ("Мухаремов", "Илијин"): the reading whose name the site knows
    (Muharem, Ilija; Jovov from Jovo, Jova or Jovan)"""
    def score(c: str) -> int:
        base = POSSESSIVE.sub('', c)
        bases = [base] + ([base[:-1] + 'ц'] if base.endswith('ч') else [])     # Јовичин, Буричин: Jovica, Đurica
        return max(_names[latin(b + end).upper()] for b in bases for end in ('', 'о', 'а', 'е', 'ан'))
    cands = [c[:1] + c[1:].lower() for c in candidates(word)]
    best = max(cands, key=lambda c: (score(c), -sum(a != b for a, b in zip(c, word))))
    return best if score(best) else best_word(word)


def split_letters(text: str) -> str:
    """"Ј асену", "Г дина": a capital set apart from the rest of its word, joined where the site knows the word"""
    def join(m: re.Match) -> str:
        whole = best_word(m.group(1) + m.group(2))
        return whole if _lower[latin(whole).lower()] else m.group(0)
    return re.sub(r'(?<![\w.])([А-ЯЂЈЉЊЋЏ]) ([а-яђјљњћџ]{2,})', join, text)


def decode_text(text: str) -> str:
    text = split_letters(romans(text))
    return re.sub(r'[A-Za-zА-Яа-яЂЈЉЊЋЏђјљњћџ]+',
                  lambda m: m.group(0) if re.fullmatch(r'[IVX]+', m.group(0)) else best_word(m.group(0)), text)


def is_head(text: str) -> re.Match | None:
    """An entry's first line: the name in capitals (a maiden name in brackets may follow the surname), then a comma"""
    m = re.match(r'^[\s.,·]*(?P<head>[^,]{3,60}?)\s*,\s*(?P<rest>.*)$', text)          # ".ПОВЕРАТА ..."
    if not m:
        return None
    head = re.sub(r'\([^)]*\)', ' ', m.group('head'))
    letters = re.findall(f'[{UC}{LC}A-Za-z]', head)
    caps = [c for c in letters if c in UC or ('A' <= c <= 'Z')]
    words = [w for w in head.split() if re.search(f'[{UC}A-Z]', w)]
    if len(words) < 2 or not letters or len(caps) / len(letters) < 0.75 or not re.match(f'[{UC}A-Z]', head.strip()):
        return None
    return m


def join(lines: list[str]) -> str:
    out = ''
    for t in lines:
        t = t.strip()
        if out.endswith(('–', '-')) and t[:1].islower():
            out = out[:-1] + t
        elif out:
            out += ' ' + t
        else:
            out = t
    return re.sub(r'\s+', ' ', out).strip()


def raw_entries() -> list[dict]:
    book = load(BOOK)
    out = []
    for pages, offset, list_name in LISTS:
        cur = None
        for page in pages:
            for col in page_lines(book, page, 2):
                xs = [l.x0 for l in col if l.text.strip()]
                if not xs:
                    continue
                left = sorted(xs)[len(xs) // 5]                        # where the column's lines start
                for line in col:
                    text = line.text.strip()
                    if not text or re.fullmatch(r'[\d\s]+', text) or re.match(r'^\d+\s*[–-]\s*Спомен', text):
                        continue
                    # an entry that starts after the end of the one before, on the same line ("... годинe. ПОВЕРАТА
                    # ЛАЗАР, Буров, ...")
                    parts = re.split(rf'(?<=\.)\s+\.?(?=[{UC}]{{3,}}(?:\s+[{UC}]{{2,}})+\s*,\s*[{UC}][{LC}]+(?:ов|ев|ин|ова|ева|ина)\b)', text)
                    for k, part in enumerate(parts):
                        m = is_head(part)
                        if m:
                            cur = {'head': m.group('head'), 'lines': [m.group('rest')], 'page': page,
                                   'printed': page - offset, 'list': list_name,
                                   'drop_cap': k == 0 and line.x0 - left > 400}
                            out.append(cur)
                        elif cur:
                            cur['lines'].append(part)
    return out


def fix_head(words: list[str]) -> list[str]:
    """A heading the letter spacing broke apart ("ГОЈ КО", "СПАСОЈ Е", "БОГ ДАНОВИЋ"), a title before the name ("Др"),
    a nickname set as a word of its own ("КОВАЧЕВИЋ ВУКАШИН ВУКОТА" = Vukašin, called Vukota)"""
    words = [w for w in words if latin(w).strip('.').upper() != 'DR' and w.strip('·.–-')]
    if len(words) >= 3 and len(words[-1]) <= 2:
        words = words[:-2] + [best_name(words[-2] + words[-1])]
    if len(words) >= 3 and _names[latin(words[0] + words[1]).upper()] and not _names[latin(words[1]).upper()]:
        words = [best_name(words[0] + words[1])] + words[2:]
    if len(words) >= 3 and '-' not in words[-1] and _given[latin(words[-2]).upper()] >= 3:
        words = words[:-2] + [words[-2] + '-' + words[-1]]
    return words


def parse(e: dict) -> dict:
    head = re.sub(r'\s+', ' ', e['head']).strip()
    maiden = re.search(r'\(([^)]*)\)', head)
    words = re.sub(r'\([^)]*\)', ' ', head).split()
    # "Ј ОВО": a letter set apart from the rest of its word
    merged = []
    for w in words:
        if merged and len(merged[-1]) == 1 and merged[-1] in UC + 'J':
            merged[-1] += w
        else:
            merged.append(w)
    # each part of a name joined by a dash on its own: "БААГОЈЕ–БААЖО" = Благоје–Блажо, the second a nickname
    words = ['-'.join(best_name(p) for p in re.split(r'\s*[–—-]+\s*', w) if p) for w in merged]
    words = fix_head(words)
    given_parts = re.split(r'-', words[-1])
    surname, given = ' '.join(words[:-1]), given_parts[0]
    nick = given_parts[1] if len(given_parts) > 1 else ''
    raw = join(e['lines'])
    head_father = re.match(r'^\s*([^\s,]+)\s*,', raw)
    father_word = best_father(head_father.group(1)) if head_father else ''
    text = decode_text(raw)
    if head_father and POSSESSIVE.search(father_word):
        text = re.sub(r'^\s*[^\s,]+', father_word, text, count=1)
    father = re.match(r'^([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+(?:ов|ев|ин|ова|ева|ина))\s*,', text)
    # "рођен 1924. године у селу Хуму", "рођен у селу Дубочанима", "рођсн 1909. тодине у селу Засаду", "на Вилусима"
    birth_word = r'ро[ђћ]?[еэсc][нп][а]?'
    born = re.search(rf'{birth_word}\s+(?:(?:\d{{1,2}}\.\s*[IVXа-я.]+\s+)?_?1[89]\d\d\.?\s*\S{{0,3}}один\S*\s+)?(?:у|на)\s+'
                     r'(?:селу|засеоку|заселку|се[–\-\s]+\S{1,3}\s+)?\s*([^;.]+)', text)
    born_year = re.search(rf'{birth_word}\s+(?:\d{{1,2}}\.\s*[IVXа-я.]+\s+)?_?(1[89]\d\d)', text)
    born_in = born.group(1) if born else ''
    if not born_in:
        frm = re.search(r'\bиз\s+(?:села\s+)?([^;.]+)', text)
        born_in = frm.group(1) if frm else ''
    # the year of the death: after its word, past the dots of a date ("8. V 1943") but not past the sentence
    death = re.search(r'(?:[Пп]огину[оа]|[Уу]мр[оаи]|[Сс]тријељ\w*|[Уу]бијен\w*|[Уу]бил[иа]|[Уу]биј\w*|[Оо]бјес\w*|'
                      r'[Оо]бјешен\w*|[Пп]одлегао|[Пп]одлегла|[Нн]естао|[Нн]естала|[Сс]трада\w*|[Зз]аклал\w*|'
                      r'[Сс]пали\w*)(?:(?!\.\s+[А-ЯЂЈЉЊЋЏ])[^;]){0,220}?\b(19[34]\d)\b', text)
    # the book names a village by its area of the municipality ("Rupni Do, Površ"), the site's records mostly by the
    # municipality ("Trebinje"): an area of Trebinje gets the town after it
    parts = [p.strip() for p in latin(born_in).strip(' ,').split(',') if p.strip()]
    parts = [p[:1].upper() + p[1:] for p in parts]
    if parts and fold4(parts[-1]) in TREBINJE_AREAS and not any('Trebinj' in p for p in parts):
        parts.append('Trebinje')
    born_in = ', '.join(parts)
    return {'last_name': latin(surname).title(), 'first_name': latin(given).title(), 'nick': latin(nick).title(),
            'maiden_name': latin(maiden.group(1)) if maiden else '',
            'fathers_name': latin(father.group(1)) if father else '',
            'birth_year': born_year.group(1) if born_year else '',
            'born_in': born_in,
            'death_year': death.group(1) if death else '',
            'additional_info': latin(text)}


def main():
    corpus()
    book = load(BOOK)
    book_words(book)
    raw = raw_entries()
    # a drop cap: the letter of the entries after it
    for i, e in enumerate(raw):
        if e['drop_cap'] and i + 1 < len(raw):
            nxt = best_name(re.sub(r'\([^)]*\)', ' ', raw[i + 1]['head']).split()[0])
            e['head'] = nxt[0] + e['head'].lstrip()
    entries = []
    for n, e in enumerate(raw, 1):
        p = parse(e)
        name = (f"{p['last_name']}{' (' + p['maiden_name'] + ')' if p['maiden_name'] else ''} {p['first_name']}"
                f"{'–' + p['nick'] if p['nick'] else ''}")
        entries.append({'soldier_id': f'{PREFIX}{n:06d}', 'name': name, **{k: v for k, v in p.items() if k != 'maiden_name'},
                        'survived': False, 'list': e['list'], 'source_url': viewer_url(book, e['page']),
                        'source_page': e['printed']})
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    by_list = Counter(e['list'] for e in entries)
    print(f'{len(entries)} entries: {dict(by_list)}; with birth year {sum(1 for e in entries if e["birth_year"])}, '
          f'father {sum(1 for e in entries if e["fathers_name"])}, death year {sum(1 for e in entries if e["death_year"])}')
    if '--sample' in sys.argv:
        import random
        random.seed(5)
        for e in random.sample(entries, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"\n{e['soldier_id']} p.{e['source_page']} | {e['name']} | father {e['fathers_name']} | "
                  f"b. {e['birth_year']} {e['born_in'][:40]} | d. {e['death_year']}\n   {e['additional_info'][:300]}")


if __name__ == '__main__':
    main()
