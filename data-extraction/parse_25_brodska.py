"""
Parser: 25. brodska NOU brigada (brigade code 30) — two lists from Nail Redžić's monograph "Brodska brigada".

    25-brodska-poginuli.pdf  (znaci.org/00001/262_14.pdf) "Spisak poginulih boraca Brodske brigade 28. divizije",
        pp. 1-25, then the book's table of contents and errata:
        ACIMOVIĆ DRAGUTIN, rođen 1921, Badovinci, Bogatić, 1. četa, 1. bataljon, poginuo 21. I 1945. ...
    25-brodska-sastav.pdf    (znaci.org/00001/262_11.pdf) "Spisak boraca i rukovodilaca koji su bili u Brodskoj
        brigadi u oktobru 1943. godine", pp. 1-15 (the author's note at the end of p. 15 is dropped):
        BALENOVIĆ MIJO — borac, Hrvat, rođen u s. Garčin (Slavonski Brod), do kraja rata postao komesar ...
        BARDAK TEODOR TEDO — komandant bataljona, ...                      (a nickname after the given name)
Many soldiers are in both lists; each keeps its own record (one source each). No fathers, except a few in the
roster ("ŽIVIĆ ANTUNA MIŠO"). Continuation lines are indented (_margin_entries).
"""
import json
import re
from collections import Counter

from _margin_entries import MarginEntries, fix_caps_head, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()
U = 'A-ZČĆŽŠĐ'


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or re.fullmatch(r'\W*\d{1,3}[»"]?\s*\d{3}', t):   # page numbers ("19» 291")
        return False
    if ln['page'] == 1 and ln['y'] < 218:                                   # the list's title
        return False
    if ln['file'] == '25-brodska-sastav.pdf' and ln['page'] == 15 and ln['y'] > 225:     # the author's note
        return False
    t = fix_caps_head(t)                                                   # "ZlVANOVlC" -> ZIVANOVIC
    t = re.sub(rf'\b(?=[{U}l]*[{U}][{U}l]*l)[{U}l]{{3,}}\b', lambda m: m.group(0).replace('l', 'I'), t, count=2)
    if ln['file'] == '25-brodska-sastav.pdf':
        t = re.sub(rf'^([{U}][^—–]*?) [—–] ', r'\1, ', t, count=1)         # "BALENOVIĆ MIJO — borac": the name ends
    ln['text'] = t
    return me.mark(ln)


def nicknames(soldiers: list[dict]) -> list[dict]:
    """"TEODOR TEDO": a second name after the given name is a nickname. Also a title read as a father ("ing"),
    and a given name the OCR spaced out ("SLA VICA")."""
    for s in soldiers:
        mid = s.get('middle_name') or ''
        if mid.lower().rstrip('.') in ('ing', 'dr'):
            s['additional_info'] = mid.lower().rstrip('.') + '.; ' + s['additional_info']
            s['middle_name'] = s['fathers_name'] = ''
        elif mid and (len(mid) <= 3 or len(s['first_name']) <= 3) and not mid.endswith('.') and s['first_name'] \
                and mid[0].isupper() and s['first_name'][0].isupper():
            s['first_name'] = (mid + s['first_name']).capitalize()
            s['middle_name'] = s['fathers_name'] = ''
        words = s['first_name'].split()
        if len(words) > 1:
            s['first_name'] = words[0]
            s['additional_info'] = 'zvani ' + ' '.join(w.capitalize() for w in words[1:]) + '; ' + s['additional_info']
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
    return nicknames(lone_names_to_given(soldiers, *name_counts()))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/25-brodska-poginuli.pdf',
        brigade_code=30,
        output_path='website/public/25-brodska-soldiers.json',
        start_page=1,
        end_page=25,
        layout='single',
        script='latin',
        additional_pdfs=[{'pdf_path': 'website/public/pdfs/25-brodska-sastav.pdf', 'start_page': 1, 'end_page': 15}],
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
