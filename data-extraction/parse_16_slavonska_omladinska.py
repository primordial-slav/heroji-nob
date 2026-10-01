"""
Parser: 16. slavonska omladinska NOU brigada "Jože Vlahović" (brigade code 37) — the fallen.

Source: Stevo Pravdić, Nail Redžić — "16. slavonska omladinska NOU brigada »Jože Vlahović«", pp. 387-423 of
        znaci.org/00002/407.pdf (the whole book; printed pp. 389-425) → website/public/pdfs/16-slavonska-omladinska.pdf:
    pp. 1-33  "Spisak poginulih boraca i rukovodilaca brigade" (from the lists in the VII archive)
    pp. 34-37 "Spisak poginulih boraca i rukovodilaca brigade u Pokuplju i na Žumberku" (1943-1944)
        ABRAMOVIC Pero, rođen 1903. u Rezovcu kod Virovitice, poginuo 17. veljače 1945. kod Sažija.
        KOMLENOVIC Stojan Coka, rođen 1924. u Novom Gradcu ...          (a nickname after the given name)
        ARAMBAŠIČ Slavko, borac.
Continuation lines are indented (_margin_entries). The list titles, their footnotes and the closing note ("Drugih
podataka u knjigama poginulih ... nije bilo") are dropped. The book's list of leaders (pages 38-40) is read by
parse_16_slavonska_rukovodioci.py; after re-running this parser, re-run that one too (leaders merged into these
records come back from it).
"""
import json
import re
from collections import Counter

from _margin_entries import MarginEntries, fix_caps_head, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()
U = 'A-ZČĆŽŠĐ'
POKUPLJE_FIRST_PAGE = 34


def _last_names() -> Counter:
    last = Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '17-slavonska-soldiers.json',
              '21-slavonska-soldiers.json'):
        last.update(s['last_name'] for s in json.load(open('website/public/' + f, encoding='utf-8')))
    return last


LAST = _last_names()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    p, y = ln['page'], ln['y']
    if re.fullmatch(r'[\W\d]{1,6}', t) or re.match(r'^\S{1,3}\s+16\.?\s+slavonska', t):   # page numbers, signatures
        return False
    if p == 1 and (y < 200 or y > 445) or p == POKUPLJE_FIRST_PAGE and (y < 370 or y > 630) \
            or p == 37 and y > 420:                                               # titles, footnotes, closing note
        return False
    t = fix_caps_head(t)                                                          # "ČULlC" -> ČULIC
    t = re.sub(rf'\b(?=[{U}l]*[{U}][{U}l]*l)[{U}l]{{3,}}\b', lambda m: m.group(0).replace('l', 'I'), t, count=1)
    m = re.match(rf'^([{U}]{{2,}}) ([{U}]{{2,}})(?=\s[{U}][a-zčćžšđ])', t)          # "KATUN AR Franjo", "HR SEK Rudolf"
    if m and (min(len(m.group(1)), len(m.group(2))) <= 3 or LAST[(m.group(1) + m.group(2)).capitalize()]):
        t = m.group(1) + m.group(2) + t[m.end():]
    ln['text'] = t
    return me.mark(ln)


def nicknames(soldiers: list[dict], first: Counter) -> list[dict]:
    """"KOMLENOVIC Stojan Coka": a second name after the given name is a nickname; but "KAHVEDZIĆ Derviša
    Krešimir" prints the father in the genitive. Given names the OCR ended in a speck ("Rade;", "Markq", "StevQ")."""
    for s in soldiers:
        mid = s.get('middle_name') or ''
        if mid and not re.search(r'[ae]$', mid):                          # not a genitive: the given name
            s['first_name'] = mid + ' ' + s['first_name']
            s['middle_name'] = s['fathers_name'] = ''
        g = s['first_name'].rstrip(';*,.')
        if g and not first[g] and ' ' not in g:
            for cand in (g[:-1] + 'o', g[:-1]):                              # "Markq" Marko, "Savoi" Savo
                if first[cand] >= 10:
                    g = cand
                    break
        s['first_name'] = g
        words = s['first_name'].split()
        if len(words) > 1:
            s['first_name'] = words[0]
            s['additional_info'] = 'zvani ' + ' '.join(w.capitalize() for w in words[1:]) + '; ' + s['additional_info']
        if s['pdf_page'] >= POKUPLJE_FIRST_PAGE:                               # the second list, by its title
            s['additional_info'] = (s['additional_info'].rstrip('.') + '. ' if s['additional_info'] else '') + \
                'Iz spiska poginulih boraca i rukovodilaca brigade u Pokuplju i na Žumberku.'
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '17-slavonska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = split_leading_aliases(repair_lj_ocr(restore_diacritics(soldiers)))
    first, last = name_counts()
    return nicknames(lone_names_to_given(soldiers, first, last), first)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/16-slavonska-omladinska.pdf',
        brigade_code=37,
        output_path='website/public/16-slavonska-omladinska-soldiers.json',
        start_page=1,
        end_page=37,
        layout='single',
        script='latin',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
        keep_other_sources=True,        # the leaders' list (parse_16_slavonska_rukovodioci.py, pages 38-40)
    )
