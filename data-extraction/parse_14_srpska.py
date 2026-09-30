"""
Parser: 14. srpska (niška) NOU brigada (brigade code 27) — the fallen.

Source: monograph "Četrnaesta srpska (niška) NO brigada", chapter "Spisak poginulih boraca i starešina odreda i
        brigade" (book pp. 461-543)
        znaci.org  →  website/public/pdfs/14-srpska.pdf
Single column, Cyrillic. pp. 1-83 the list (p. 1 ends with the author's note on the sources), then the book's
table of contents.
    АДАМОВИЋ Петра ВОЈИСЛАВ (рођен 1923. у селу Витовница, срез млавски, Пожаревац). У НОВЈ ступио ...
    АЛЕКСАНДРОВИЋ Милоша МИЛОШ (1923, Малајница, хомољски срез). У НОВЈ од 26. X 1944, погинуо ...
The year of birth is the first thing in the brackets. Continuation lines are indented (_margin_entries).
"""
import json
import re
from collections import Counter

from _margin_entries import MarginEntries, fix_cyrillic_ocr_line, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()
P1_NOTE_Y = 430             # p. 1: the author's note on the sources, down to the page end


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or (ln['page'] == 1 and (ln['y'] >= P1_NOTE_Y or ln['y'] < 200)):
        return False
    t = fix_cyrillic_ocr_line(t)
    t = re.sub(r'^([A-ZČĆŽŠĐ]{3,})\s+-\s+([A-ZČĆŽŠĐ]{3,})', r'\1\2', t)          # "ALIH - HODŽIĆ"
    t = re.sub(r'^(\S+(?: [^\s,(]+)+?) \((?=\d|rođ|iz|u |\d)', r'\1, (', t, count=1)   # "Milan (1924, ..." ends the name
    ln['text'] = t
    return me.mark(ln)


def nicknames(soldiers: list[dict]) -> list[dict]:
    """"DOBRIVOJE Čelik", "DRAGOMIR Brale": words after the given name are a nickname (or, for the Italians,
    "Italijan")."""
    for s in soldiers:
        words = s['first_name'].split()
        if len(words) > 1:
            s['first_name'] = words[0]
            rest = ' '.join(w.capitalize() for w in words[1:])
            s['additional_info'] = (rest if rest == 'Italijan' else 'zvani ' + rest) + '; ' + s['additional_info']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def birth_years(soldiers: list[dict]) -> list[dict]:
    """"(1921, Manjinac, ...)" or "(rođen 1923. u ...)": the year that opens the bio."""
    for s in soldiers:
        m = re.match(r'^(?:[^;(]*; )*\(?(?:rođen[a]?\s+)?(1[89]\d\d)\b', s['additional_info'].lstrip())   # after "zvani X; "
        if m and not s.get('birth_year'):
            s['birth_year'] = m.group(1)
        if s.get('middle_name', '')[:1].islower():                        # "živote": a lowercase Ж in the scan
            s['middle_name'] = s['fathers_name'] = s['middle_name'].capitalize()
            s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '4-srpska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers)))
    return birth_years(nicknames(lone_names_to_given(split_leading_aliases(soldiers), *name_counts())))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/14-srpska.pdf',
        brigade_code=27,
        output_path='website/public/14-srpska-soldiers.json',
        start_page=1,
        end_page=83,
        layout='single',
        script='cyrillic',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
