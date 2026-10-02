"""
Parser: 7. krajiška brigada (brigade code 48) — "Preživeli i poginuli borci i rukovodioci", a second book.

Source: "Sedma krajiška brigada — sjećanja i spisak boraca", knjiga 2 (znaci.org 00001/186_2.pdf), "Preživeli i
        poginuli borci i rukovodioci od formiranja brigade decembra 1942. g. do kraja rata" (book p. 447 on)  →
        website/public/pdfs/7-krajiska-spisak.pdf (pages 1-224 of 186_2.pdf; pp. 1-3 the title and the editors'
        note, which counts 4,119 fighters).
Cyrillic, two columns, re-typeset by znaci.org from its OCR:
    АБЛАКОВИЋ Мехмеда МУХАМЕД, рођен 1925. у Травнику. Муслиман, радник. У НОБ-и од 1944. Борац 3. чете 3.
    батаљона.            ... ПОГИНУО 9. јуна 1943. на Сутјесци.
The text layer spells some capitalized names with Latin letters that look like Cyrillic ones ("BУKИЋ" = Вукић,
"AУIIIAH" = Душан, "TPHBУHOBИЋ" = Тривуновић) and has no capital Ђ (it prints Б or B: "BУPO" = Ђуро): the name
before the first comma is read back letter by letter, choosing among the readings (A = А/Д/Л, B = В/Ђ/Б, H = Н/И)
the one the corpus knows best. The unit's first book is its Borci Sutjeske chapter (IDs 1-); these get IDs from
10001; the same soldier in both is merged (find_source_duplicates.py).
"""
import glob
import itertools
import json
import re
from collections import Counter

from _parser_scaffold import (DEFAULT_ENTRY_START, cyrillic_to_latin, extract_lines_two_column, repair_cyrillic_ocr,
                              run_parser)

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# Latin look-alikes of Cyrillic capitals (and digits, lowercase letters), and what each can stand for
LOOK = {'A': 'АДЛ', 'B': 'ВЂБ', 'C': 'С', 'E': 'Е', 'H': 'НИ', 'K': 'К', 'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т',
        'X': 'Х', 'Y': 'У', 'J': 'Ј', 'III': 'Ш', 'R': 'ЋР', 'I': 'И', 'N': 'Н', '3': 'З', '4': 'Ч', '1': 'ИЈ',
        'a': 'адл', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'x': 'х', 'y': 'у', 'Б': 'БЂ', 'Е': 'ЕЋ', 'Н': 'НЋ',
        'iii': 'ш', 'iu': 'ш', 'ui': 'ш', '0': 'О'}
CYR_CAP = 'АБВГДЂЕЖЗИЈКЛЉМНЊОПРСТЋУФХЦЧЏШ'
CAPS = f'[{CYR_CAP}ABCEHKMOPTXYJ¥]'
# an entry glued to the end of the previous one's line: ". BABANOVIB-MILOŠEVIĆ Kovčalije ANA"
GLUED = re.compile(rf'(?<=\.)\s*(?={CAPS}[{CYR_CAP}ABCEHKMOPTXYJI\-]{{2,}}\s+[{CYR_CAP}][а-яђћџљњј]+\s+{CAPS}{{2,}})')
_known: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            for k in ('last_name', 'first_name', 'middle_name'):
                if s.get(k):
                    _known[s[k].upper()] += 1


def read_word(w: str) -> str:
    """A capitalized word with look-alikes (Latin letters, digits; a Б, Е or Н that may be Ђ or Ћ), in Cyrillic:
    the reading the corpus knows best. Б inside a name is often ђ ("МЛАБЕН" = Млађен), a final Е or Н a ћ."""
    parts = re.findall(r'III|iii|iu|ui|.', w)
    options = []
    for i, p in enumerate(parts):
        if p in ('Е', 'Н') and i != len(parts) - 1:
            options.append(p)                                               # Е, Н read as Ћ only at the end
        else:
            options.append(LOOK.get(p, p))
    letters = [c for c in w if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) >= 0.6:
        # a capitalized word: a lowercase letter in it is a misread capital ("НЕаЕЉКО" = НЕДЕЉКО)
        options = ['АДЛ' if o == 'а' else o.upper() for o in options]
    changeable = sum(len(o) > 1 for o in options)
    if all(o == p for o, p in zip(options, parts)):
        return w
    if changeable > 7:
        return ''.join(o[0] for o in options)
    printed = _known[cyrillic_to_latin(w).upper()]
    best, best_n = w, printed
    for combo in itertools.product(*options):
        cand = ''.join(combo)
        n = _known[cyrillic_to_latin(cand).upper()]
        if n > best_n:
            best, best_n = cand, n
    latin = re.search(r'[A-Za-z0-9]', w)
    if best == w and latin:
        return ''.join(o[0] for o in options)                               # unknown: the likeliest letters
    if best != w and not latin and best_n < 3 * max(printed, 1):
        return w                                                            # a Cyrillic name stays unless far rarer
    return best


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    for ln in extract_lines_two_column(pdf_path, start, end, 'auto'):
        text = ln['text'].replace('¥', 'У').replace('л>', 'љ').replace('н>', 'њ')
        text = re.sub(r'[ЛA]\s?>\s?', 'Љ', text)
        text = re.sub(r'[НH]\s?>\s?', 'Њ', text)                       # "СУA >0" = СУЉО
        for part in GLUED.split(text):
            lines.append({**ln, 'text': part})
    for ln in lines:
        head, sep, rest = ln['text'].partition(',')
        if re.match(rf'^{CAPS}', head) and len(head) < 60:
            words = head.split(' ')
            head = ' '.join('-'.join(read_word(p) for p in w.split('-')) if re.match(rf'^{CAPS}', w) else w
                            for w in words)
        ln['text'] = head + sep + rest
    return lines


def post(soldiers: list[dict]) -> list[dict]:
    """A given name split at a line's end ("ILI-JA", "SA-VKA") is joined; "DESANKA-DESA": the name and a nickname."""
    soldiers = repair_cyrillic_ocr(soldiers)                                # АДАМОВИБ, -ВИЕ, -ВИН; БУРО = Đuro
    known = lambda w: _known[w.upper()] >= 3
    for s in soldiers:
        parts = [p for p in re.split(r'[\s-]+', s['first_name']) if p]
        if len(parts) < 2:
            continue
        joined = ''.join(parts)
        if known(joined.capitalize()):
            s['first_name'] = joined.capitalize()
        elif known(parts[0]) and len(parts) == 2 and '-' in s['first_name']:
            s['first_name'] = parts[0]
            s['additional_info'] = f'zvani {parts[1]}; ' + s['additional_info']
        else:
            continue
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] <= 3 or re.fullmatch(r'[\d\W]{1,5}', t):
        return False                                                         # the title and the editors' note
    ln['text'] = t
    return True


# an entry starts with SURNAME [Father] GIVEN; or the father's name breaks at the line's end ("БАБАНОВИБ-МИЛОШЕВИЋ
# Ковча-"); a caps phrase in a bio ("ЈУ-/ГОСЛАВИЈЕ. ПОГИНУО", "КПЈ. ПОГИНУО") is no entry
ENTRY_START = re.compile(rf'^(?!\S+\.?\s+(?:POGINU|UMR|NESTA|ZAROBLJ|STRIJELJ))(?:{DEFAULT_ENTRY_START.pattern}|'
                         rf'[{U}]{{5,}}[{U}\-]*\s+[{U}][{L}]+-?$)')


if __name__ == '__main__':
    import sys
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/7-krajiska-spisak.pdf',
        brigade_code=48,
        output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/7-krajiska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=extract,
        script='cyrillic',
        entry_start_re=ENTRY_START,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=len(sys.argv) <= 1,
    )
