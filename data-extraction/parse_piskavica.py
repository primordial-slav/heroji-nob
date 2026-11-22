"""
*Пискавица, мој завичај и моји доживљаји* (Nikola Pavić, Prometej, Novi Sad 2015; Poreklo library, doc 00004721), a
book across units: "Погинули и преживјели борци у Другом свјетском рату из Пискавице" (scan pp. 35-51), taken by its
author from the book *Timar u Bosanskoj krajini*, village by village (Piskavica, Radosavska, Niševići, by Ivanjska and
Banja Luka):

    "Погинули борци" (pp. 35-39): "Бузаџија Милоша Дмитар 1910–1942 (борац 2. крајишког одреда од 1941);"; Niševići's
        as "Беговић Симе Урош (1925–1944), борац 11. крајишке од 1944."
    "Преживјели борци" (pp. 42-51): "Бањац Лазе Саво (1910), борац 2. крајишког одреда од 1941;", and the movement's
        other people: "Гранула Марка Мијат (1909), одборник НОО од 1942;", in the command of a place, SKOJ, AFŽ.

Every name is a fighter's or the movement's: the fighters and the men of the commands (komanda mjesta) without a
role, the committee members, SKOJ, AFŽ and the youth organisation as activists, the rest as participants.

The OCR swaps letters as no other book's: у for д on some pages ("оуреуа" одреда, "Рауомир"), Т and Г for г
("бриТаде", "ДраГо"), и for п and т ("Сиасоје" Спасоје, "СИојака" Стојака), ш for т ("Сшојке"), ] for Ј, and a Latin
H for П or Н, g for д, s for в, u for и ("Hpepag" Прерад, "Jose" Јове, "Bug" Вид). Each word of a name is read as the
variant of its letters the site's names know best (`best`), the words of the duty against the words the list uses
(`VOCAB`).

Output: data-extraction/poreklo/piskavica-entries.json (IDs 9116xxxxxx: the fallen from 000001, the survivors from
001001, in the list's order).
Usage: python data-extraction/parse_piskavica.py
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _village_books as V  # noqa: E402
from parse_ostrvica import level_lines  # noqa: E402
from _parser_scaffold import cyrillic_to_latin as latin  # noqa: E402
from poreklo_text import load, page_words, viewer_url  # noqa: E402

BOOK = 'piskavica.json'
OUT = HERE / 'poreklo' / 'piskavica-entries.json'
PREFIX = '9116'
OFFSET = -2                                  # scan page minus the book's page (scan 35 is p. 37)
TITLE = 'Piskavica, moj zavičaj i moji doživljaji'
FALLEN = 'Poginuli borci'
SURVIVED = 'Preživjeli borci'
VILLAGES = {'ПИСКАВИЦА': 'Piskavica, Banja Luka', 'РАДОСАВСКА': 'Radosavska, Banja Luka', 'НИШЕВИЋИ': 'Niševići, Prijedor',
            'НИШЕВИБИ': 'Niševići, Prijedor'}
CU, CL = 'А-ЯЂЈЉЊЋЏ', 'а-яђјљњћџ'

# what an OCR letter may stand for (a Latin letter for its Cyrillic look-alike)
CONF = {
    'у': 'уд', 'Т': 'Тг', 'Г': 'Гг', 'И': 'Ипт', 'и': 'ипт', 'ш': 'шт', ']': 'Ј', ')': 'Ј', 'l': 'Јл', 'H': 'ПН',
    'h': 'ћ', 'p': 'р', 'P': 'Р', 'e': 'е', 'E': 'Е', 'a': 'а', 'A': 'А', 'g': 'д', 's': 'в', 'u': 'и', 'o': 'о',
    'O': 'О', 'c': 'с', 'C': 'С', 'B': 'В', 'b': 'бђ', 'm': 'шт', 'i': 'лиј', 'J': 'Ј', 'j': 'ј', 'K': 'К', 'k': 'к',
    'M': 'М', 'T': 'Т', 'x': 'х', 'X': 'Х', 'y': 'у', 'n': 'п', 'Б': 'БЂ', 'б': 'бђ', '1': 'г', '7': 'т',
    'Њ': 'ЊЉ', 'њ': 'њљ', 'П': 'ПЛ', 'L': 'ЈЛ', '[': 'Ј', 'w': 'ш',
}
# words no letter swap reads: as the alphabetical order, the other list and the fallen brothers name them
FIX = {'Hamaiuh': 'Пашагић', ']oршћ': 'Јоргић', ']оршћ': 'Јоргић', ']opiuh': 'Јоргић', 'СњТхојан': 'Стојан', 'Бузаиија': 'Бузаџија',
       'ДраТичеоић': 'Драгичевић', 'Драшчевић': 'Драгичевић'}
LFIX = {'Drađpdina': 'Dragutina', 'Drađšjina': 'Dragutina', 'Drađnjćin': 'Dragutin', 'Draeušin': 'Dragutin',
        'Drgoljub': 'Dragoljub', 'Ljuba/pir': 'Ljubomir', 'Miourat': 'Miodrag', 'Midan': 'Milan', 'Granu/li': 'Granula',
        'Jakovljevioć': 'Jakovljević', 'Kumgnović': 'Kumenović', 'Lašinčić': 'Latinčić', 'Satnivuković': 'Stanivuković',
        'Stanivukooić': 'Stanivuković', 'Stjeaanović': 'Stjepanović', 'Šokčevcć': 'Šokčević', 'Šuptjilović': 'Šušilović',
        'Grakovac': 'Grahovac', 'Miloivana': 'Milovana', 'Saiasoje': 'Spasoje', 'Sttšnka': 'Stanka', 'Stajaka': 'Stojaka',
        'Alekee': 'Alekse', 'Blaeoje': 'Blagoje', 'Gliee': 'Gliše', 'Malaki': 'Milaka', 'Likić': 'Lakić', 'Love': 'Jove',
        'Pazara': 'Lazara', 'Pazo': 'Lazo', 'Puke': 'Luke', 'Osše': 'Oste', 'Njuban': 'Ljuban', 'Njubana': 'Ljubana',
        'Njubo': 'Ljubo', 'Prokoiija': 'Prokopija', 'Mliđan': 'Mlađan', 'Mlađem': 'Mlađen', 'Sševan': 'Stevan',
        'Sšojaka': 'Stojaka', 'S11asoje': 'Spasoje', 'Si7evana': 'Stevana', 'Si7anoje': 'Stanoje', '[akov': 'Jakov',
        'Pawalić': 'Pašagić', ']e95i7e': '', "Si'šve": 'Steve', "Si'šjai": 'Stojan'}
# the names nothing reads (the scans could not be checked): as the OCR has them, the dash dropped
UNREAD = {'Sesi—šo': 'Sesišo', 'Gezi—šo': 'Gezišo', 'Osi—ae': 'Osiae', 'Kazu—mh': 'Kazumh', 'Koca—mh': 'Kocamh'}
VOCAB = {'борац', 'крајишког', 'крајишке', 'одреда', 'бригаде', 'од', 'одборник', 'НОО', 'у', 'команди', 'команда',
         'мјеста', 'омладинској', 'организацији', 'СКОЈ', 'СКОЈ-у', 'скојевац', 'АФЖ', 'Приједор', 'Приједора',
         'Ивањској', 'Ивањске', 'устаничке', 'групе', 'козарског', 'Тимарског', 'марта', 'батаљона', 'Божићима',
         'команде', 'одреда', 'мјесни', 'мјесног', 'НОО-а', 'одбора', 'члан', 'Приједору', 'Ивањска', 'кр.', 'и'}


def variants(word: str, limit: int = 4096):
    """the word's readings, each ambiguous letter as each letter it may stand for"""
    choices = [CONF.get(c, c) for c in word]
    n = 1
    for c in choices:
        n *= len(c)
    if n > limit:
        return [word]
    return [''.join(p) for p in itertools.product(*choices)]


def nominatives(gen: str):
    """the nominatives a father's genitive may stand for: Симе Sima, Simo; Николе Nikola; Милоша Miloš; Спасоје
    Spasoja, Spasoje"""
    yield gen
    if gen.endswith('е'):
        yield gen[:-1] + 'а'
        yield gen[:-1] + 'о'
    if gen.endswith('а'):
        yield gen[:-1]
        yield gen[:-1] + 'о'
    if gen.endswith('је'):
        yield gen[:-1] + 'а'


def score(w: str, part: str) -> int:
    key = latin(w.upper())
    if part == 'last':
        return V.T._names[key] - V.T._given[key] // 2
    if part == 'father':
        return max(max(V.T._given[k], V.T._names[k]) for k in (latin(n.upper()) for n in nominatives(w)))
    return V.T._given[key]


def best(word: str, part: str) -> str:
    """the reading of an OCR'd name word the site's names know best, in title case; as printed if none is known"""
    word = word.lstrip('.,;:\'"’(').rstrip('.,;:\'"’()]')
    word = FIX.get(word, word)
    if not word:
        return ''
    word = word[0].upper() + word[1:]
    for a, b in (('и7', 'т'), ('И7', 'Т'), ('i7', 'т'), ('11', 'п')):
        word = word.replace(a, b)
    cands = variants(word)
    top = max(cands, key=lambda c: (score(c, part), -sum(a != b for a, b in zip(c, word))))
    if score(top, part) <= 0:
        top = ''.join(CONF.get(c, c)[0] if c.isascii() and c.isalpha() else c for c in word)
    out = latin(top[0] + top[1:].lower())
    out = LFIX.get(out, out)
    return UNREAD.get(out, out)


def fix_word(word: str) -> str:
    """a word of the duty or unit, read against the words the list uses"""
    core = word.strip('.,;:()')
    if not core or core in VOCAB or re.fullmatch(r'[\d.]+', core):
        return word
    for v in variants(core, 512):
        if v in VOCAB:
            return word.replace(core, v)
    return word


def clean_info(t: str) -> str:
    t = re.sub(r'(\d)\s*\.\s*(?=кр)', r'\1. ', t)
    t = re.sub(r'о[ду]р\S{0,2}е[ду]а|агпега|agpega', 'одреда', t)
    t = re.sub(r'\b(?:[i1]р[уy]ае|ipyae|[i1]руае|žpyae)', 'групе', t)
    t = re.sub(r'([КкK])озарск\S{0,2}(?=\s+одреда)', lambda m: m.group(1) + 'озарског', t)
    t = re.sub(r'\b(?:иод|су)(?=\s+19)', 'од', t)
    t = re.sub(r'(борац|од)(?=\d)', r'\1 ', t)
    t = re.sub(r'бри\S{0,2}а[ду]е', 'бригаде', t)
    t = re.sub(r'крај\S{0,6}(?=\s+о[ду]ре[ду]а|\s+бриг|\s+од\b)', lambda m: 'крајишке', t)
    t = ' '.join(fix_word(w) for w in t.split())
    t = re.sub(r'крајишке(?=\s+одреда)', 'крајишког', t)
    t = re.sub(r'\bкр\.\s*одреда', 'крајишког одреда', t)
    t = re.sub(r'\b(\d{1,2})\.\s*крајишке\s+(?=од\b)', r'\1. крајишке бригаде ', t)   # "борац 11. крајишке од 1944"
    t = re.sub(r'(19\d\d)\d\b', r'\1', t)                                            # "од 19449"
    t = re.sub(r'\bбиорац\b', 'борац', t)
    return t.strip(' ;.,-')


ENTRY = re.compile(rf'^(?P<last>[{CU}{CL}\]\)HPBKMTEAOC][^\s]*(?:\s*[–—-]\s*[{CU}][{CL}]+)?)\s+'
                   rf'(?:(?P<father>[^\s(\d][^\s(]*)\s+)?(?P<given>[^\s(\d][^\s(]*)\s*'
                   r'(?:\(?\s*[8(]?\s*(?:жена[.,]?\s*)?(?P<born>1[89]\d\d)\s*(?:[–—\-←]\s*(?P<died>19\d\d))?\s*\)?)\s*[.,]?\s*(?P<rest>.*)$')


def raw_lines(book: dict, pages) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for l in level_lines(page_words(book, page)):
            t = l.text.strip()
            if l.x0 > 5000 or re.search(r'ЗА\s+\S*\s+И\s+\S*\s+\S*\s+\S*\s+\S*$', t) and len(t) < 70 and '|' in t:
                continue                                                  # the running head
            if re.match(r'^\d{1,3}\s*[|\]I]\s', t) or re.search(r'[|)]\s*\d{1,3}$', t) and 'ЗА' in t:
                continue
            t = re.sub(rf'\b([{CU}]) (?=[{CL}])', r'\1', t)                  # "Г ранула", "Т ома"
            t = re.sub(rf'([{CL}])(1[89]\d\d)', r'\1 \2', t)                     # "Милан1906–1942"
            t = re.sub(rf"(?<=[{CL}])'(?=[{CU}])", ' ', t.lstrip("'’\" "))         # "]ове'Цвијо"
            out.append((page, t))
    return out


def entries_of(book: dict, pages, start: str, stop: str) -> list[dict]:
    lines = raw_lines(book, pages)
    on, village, out = False, '', []
    for page, t in lines:
        if not on:
            on = start in t
            continue
        if stop in t:
            break
        if 'Извод' in t:                                                  # the footnote on its source
            continue
        bare = re.sub(r'[^А-ЯЂЈЉЊЋЏ]', '', t)
        if bare in VILLAGES and len(t) < 20:
            village = VILLAGES[bare]
            continue
        m = ENTRY.match(t)
        if m and (m.group('rest') or m.group('died')) and not re.match(r'^\d', t):
            out.append({'page': page, 'village': village, 'm': m.groupdict(), 'text': t})
        elif out and (re.match(r'^[\d(]', t) or len(t) < 12):
            out[-1]['m']['rest'] = (out[-1]['m']['rest'] or '') + ' ' + t        # "1943)." of a wrapped entry
        else:
            print('   unread:', page, t[:100])
    return out


def role_of(info: str) -> str | None:
    if re.search(r'\b(?:borac|brigad|odred|komand|bataljon|četa|čete|grupe)\w*', info, re.I):
        return None
    if re.search(r'odbornik|NOO|SKOJ|skojevac|AFŽ|omladinsk|USAOJ|NOF', info, re.I):
        return 'activist'
    return 'participant'


def build(book: dict, raw: list[dict], list_name: str, first: int, survived: bool) -> list[dict]:
    out = []
    for i, r in enumerate(raw):
        m = r['m']
        last = '-'.join(best(x, 'last') for x in re.split(r'\s*[–—-]\s*', m['last']))
        father = best(m['father'], 'father') if m['father'] else ''
        given = best(m['given'], 'first')
        rest = clean_info(re.sub(r'^[(\s]*|[);.,\-\s]*$', '', m['rest'] or '').strip())
        info = V.read_cyr(rest).strip(' .;,')
        years = f"{m['born']}–{m['died']}" if m['died'] else m['born']
        name = ' '.join(x for x in (last, father, given) if x)
        e = {'soldier_id': f'{PREFIX}{first + i:06d}', 'name': name, 'last_name': last, 'also': [], 'first_name': given,
             'nick': '', 'fathers_name': father, 'birth_year': m['born'],
             'born_in': r['village'],
             'death_year': m['died'] or '', 'survived': survived, 'units': V.units_of(info),
             'additional_info': f"{list_name}, {r['village'].split(',')[0]}: {name} ({years}), {info}.",
             'list': list_name, 'book_title': TITLE, 'source_url': viewer_url(book, r['page']),
             'source_page': r['page'] - OFFSET}
        role = role_of(info)
        if role:
            e['role'] = role
        out.append(e)
    return out


def main():
    V.corpus()
    book = load(BOOK)
    fallen = build(book, entries_of(book, range(35, 41), 'ПОГИНУ', 'На споменику'), FALLEN, 1, False)
    alive = build(book, entries_of(book, range(42, 52), 'ПРЕЖИВЈЕ', 'Убијање'), SURVIVED, 1001, True)
    entries = fallen + alive
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    counts = Counter(f"{e['list']} {e.get('role', 'fighter')}" for e in entries)
    print(len(entries), 'entries ->', OUT.name, dict(counts))
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']} | {e['birth_year']}-{e['death_year']} {e['born_in']} | {e['units']} "
              f"{e.get('role', '')} | {e['additional_info'].split(': ', 1)[1][:90]}")


if __name__ == '__main__':
    main()
