"""
Parser: 7. Vojvođanska udarna brigada (brigade code 22).

Source: Nikola Božić — "SEDMA VOJVOĐANSKA UDARNA BRIGADA", chapter "Spisak boraca 7. vojvođanske
        udarne brigade (preživeli — poginuli i umrli posle rata)", book pp. 421-567
        znaci.org/00001/73_8.pdf  →  website/public/pdfs/7-vojvodjanska.pdf
Single column, Cyrillic. pp. 1-149 one alphabetical list (p. 1 ends with the author's footnote),
pp. 150-154 the book's table of contents and imprint. No fathers' names:
    АБАДОВИЋ АНТУН, 1908, Валпово, 11.12.1944, Белишће, пог., борац 7. ВУБ.
    АЛЕКСАНДРОВИЧ С. ВИКТОР, 1907, Кимзи, СССР, борац 4. (руског) батаљона, 2.07.1944.
Continuation lines are indented ~17pt, so entries start at the left margin (_margin_entries).
The OCR never reads a capital Ћ (Н/Б/Е/К) and reads Ђ as Б (АБАДОВИН, ШИЛИБ БОКА = Šilić Đoka):
repair_cyrillic_ocr, repair_capital_c.
"""
import glob
import json
import re
from collections import Counter

from _margin_entries import MarginEntries, fix_cyrillic_ocr_line, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_capital_c, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

P1_FOOTNOTE_Y = 275          # p. 1: "* Jedan od najtežih i najodgovornijih zadataka ..." down to the page end
me = MarginEntries()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or (ln['page'] == 1 and ln['y'] >= P1_FOOTNOTE_Y):
        return False
    if ln['page'] == 1 and re.match(r'^(SPISAK|BORACA 7)', t):          # the chapter title
        return False
    ln['text'] = fix_cyrillic_ocr_line(t)
    return me.mark(ln)


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-vojvodjanska-soldiers.json', '2-vojvodjanska-soldiers.json', 'prva-proleterska-soldiers.json',
              '13-proleterska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


SURNAME_END = re.compile(r'(?:ić|in|ov|ev|ski|ački|ac|ak)$')


def tidy_names(soldiers: list[dict], first_counts: Counter, last_counts: Counter) -> list[dict]:
    """Entries print SURNAME [X.] GIVEN; a few Novi Sad ones also a father ("SIMIĆ KOSTE ALEKSANDAR"), which the
    scaffold reads the same way as a given name plus a nickname ("JEREMIĆ EVICA KANA", "JEŠIĆ MILAN IBRA") or a
    second surname ("MUŠICKI ČULJAK SIDA"). A common given name followed by an uncommon word is name + nickname;
    a surname-shaped word before the given name is a second surname. Soviet volunteers: "ALEKSJUK — SSSR"."""
    common = lambda w: first_counts[w] >= 20
    given, father = Counter(), Counter()       # all units: how often a word is a given name / a father as printed
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.endswith('7-vojvodjanska-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                given[s['first_name']] += 1
                father[s.get('middle_name') or ''] += 1
    for s in soldiers:
        prefix = []
        info = s['additional_info']
        if s['first_name'] in ('Sssr', 'Ssssr') or info.startswith('zvani Ssssr; '):
            s['first_name'] = '' if s['first_name'] in ('Sssr', 'Ssssr') else s['first_name']
            info = 'SSSR, ' + re.sub(r'^zvani Ssssr; ', '', info)
        if s['middle_name'] in ('—', '-'):
            s['middle_name'] = s['fathers_name'] = ''
        for k in ('middle_name', 'first_name'):
            if re.match(r'^[Dd]r\b', s[k]):
                prefix.append('dr')
                s[k] = re.sub(r'^[Dd]r\b\.?\s*', '', s[k]).capitalize()
        m = re.fullmatch(r'([A-ZČĆŽŠĐ])\.([A-Za-zčćžšđ]+)', s['first_name'])       # "J.luka"
        if m and not s['middle_name']:
            s['middle_name'] = s['fathers_name'] = m.group(1) + '.'
            s['first_name'] = m.group(2).capitalize()
        words = s['first_name'].split()
        if len(words) == 2 and 'SSSR' not in info:
            w1, w2 = words
            if SURNAME_END.search(w1) and not common(w1):
                if w1.endswith('in') and last_counts[w1[:-1] + 'ć'] >= 2 and not last_counts[w1]:
                    w1 = w1[:-1] + 'ć'
                s['last_name'], s['first_name'] = f"{s['last_name']}-{w1}", w2
            elif common(w1) and not common(w2):
                s['first_name'] = w1
                prefix.append('zvani ' + w2)
        mid = s['middle_name'] or ''
        is_given = mid and (common(mid) or given[mid] >= 1 and father[mid] <= max(1, given[mid] // 5))
        if is_given and s['first_name'] and not common(s['first_name']) and len(mid) > 2:
            s['first_name'], prefix = mid, prefix + ['zvani ' + s['first_name']]
            s['middle_name'] = s['fathers_name'] = ''
        elif mid and SURNAME_END.search(mid) and not common(mid) and len(mid) > 2:
            if mid.endswith('in') and last_counts[mid[:-1] + 'ć'] >= 2 and not last_counts[mid]:
                mid = mid[:-1] + 'ć'
            s['last_name'] = f"{s['last_name']}-{mid}"
            s['middle_name'] = s['fathers_name'] = ''
        if prefix:
            info = '; '.join(prefix) + ('; ' + info if info else '')
        s['additional_info'] = info
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_capital_c(repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers))))
    first, last = name_counts()
    return tidy_names(lone_names_to_given(split_leading_aliases(soldiers), first, last), first, last)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/7-vojvodjanska.pdf',
        brigade_code=22,
        output_path='website/public/7-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=149,
        layout='single',
        script='cyrillic',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
