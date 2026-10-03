"""
Parser: 13. hercegovačka NOU brigada (brigade code 100).

Source: Mensur Seferović, "Trinaesta hercegovačka NOU brigada" (znaci.org 00001/270_7.pdf, book pp. 316-347)
        →  website/public/pdfs/13-hercegovacka.pdf. The scan repeats four pages of the roster (its pages 37-40 = 33-36)
        and two more (43-44 = 41-42); the site's PDF leaves the copies out (its pages: the chapter's 13-36, 41-42, 45-50).
    pp. 1-14    "Poginuli borci i starješine 13. hercegovačke NOU brigade (14. maj 1944 - 15. maj 1945.)", one column,
                a hanging indent, by letter:
                    ABRAMOVIĆ (Đorđa) Milan, 1926, Celebići, Konjic, 6. 4. 1945, Blažuj, 2. bat.
    pp. 15-32   "Borili su se u 13. hercegovačkoj NOU brigadi", the fighters who ended the war in it or left it before,
                names only, two columns:
                    BATLAK (Mehe) Omer
The officers' list by unit before them (book pp. 305-315) is not read. A second name after the given name in the
roster is a nickname ("BAJIĆ Veselinka Boba"). The fallen list's birthplace is the village and municipality after
the year; the date and place of death follow.
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, death_type_from_text, extract_lines_single_column, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ROSTER_FROM = 15
_starts: dict = {}


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/13-hercegovacka-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    return extract_lines_single_column(pdf_path, 1, ROSTER_FROM - 1) + columns_reader(2)(pdf_path, ROSTER_FROM, end_page)


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append(ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,6}|\W*\w{0,2}\W*', t) or re.match(r'^(?:POGINULI BORCI|NOU BRIGADE|\(14\. maj|BORILI SU SE)', t):
        return False                                                         # headings, letters, page numbers
    if ln['page'] == ROSTER_FROM and not re.match(rf'^[{U}][{U} ]{{2,}}[ (]', t):
        return False                                                         # the roster's introduction
    if ln['page'] >= ROSTER_FROM:
        if re.match(rf'^[{U}][{U}l ]{{2,}}\s*(?:\([{U}][{L}]+\)\s*)?(?:[{U}]\.\s*)?[{U}][{L}]', t):
            ln['text'] = '§r§ ' + t
            return True
        return False
    if ln['x'] <= min(_starts[ln['page']]) + 6 and re.match(rf'^[{U}][{U}l ]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    lst = text[1]
    text = re.sub(r'^§.§\s*', '', text)
    text = text.replace('Munirà', 'Mumina').replace('Hämo', 'Hamo')        # the text layer's slips
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "Po- stojna"
    head, _, info = text.partition(',')
    info = info.strip()
    father = ''
    paren = re.search(r'\(([^\W\d_]+(?:\s+[^\W\d_]+)?)\)', head)               # "(Munirà)", "(M)"
    if paren:
        father = paren.group(1)
        head = head[:paren.start()] + ' ' + head[paren.end():]
    words = head.split()
    caps = []
    while words and re.fullmatch(rf'[{U}][{U}l]*', words[0]):                # "KRV A VAC", "KLJAKI Ć": spaced apart
        caps.append(words.pop(0))
    if len(caps) > 1 and not words:
        words = [caps.pop()]                                                 # "DADIĆ (Smaila) ENVER": the name in capitals
    init = words.pop(0) if words and re.fullmatch(rf'[{U}]\.', words[0]) else ''
    father = father or init
    last = k8.join_parts([k8.caps_word(c) for c in caps], 'last_name')
    names = [w.title() if w.isupper() else w for w in words]
    notes = []
    if len(names) > 1:
        notes.append('zvani ' + ' '.join(names[1:]))                         # "BAJIĆ Veselinka Boba"
        names = names[:1]
    rec = _record(last, ' '.join(names), father, '; '.join(notes + [info] * bool(info)))
    if lst == 'p':
        y = re.match(r'(1[89]\d\d)\b', info)
        if y:
            rec['birth_year'] = y.group(1)
        parts = [p.strip() for p in re.sub(r'^1[89]\d\d,\s*', '', info).split(',')]
        places = []
        for p in parts[:2]:
            if re.fullmatch(rf'(?:s\.\s*)?[{U}][{L}]+(?:[\s-]+(?:[{U}]\.?\s*)?[{U}]?[{L}]+)*(?:\s*\([{U}][{L}]+\))?', p) and \
                    not re.match(r'(?:Poginu|Umr|kod|krajem|početkom|sredinom)', p):
                places.append(re.sub(r'^s\.\s*', '', p))
            else:
                break
        if places:
            rec['birth_place'] = ', '.join(places)
        after = parts[len(places):]                                          # "6. 4. 1945, Blažuj, 2. bat."
        if after and re.search(r'19\d\d', after[0]):
            d = re.match(r'(.*?19\d\d)\.?\s*(?:(?:na|u|kod)\s+(.+))?$', after[0])
            if d:
                rec['death_date'] = d.group(1).strip()
            where = (d.group(2) if d else '') or (after[1] if len(after) > 1 else '')
            if d and where and not re.match(r'^(?:\d\.\s*bat|umr|ranjen|bolni|komandir|komesar|desetar)', where):
                rec['death_place'] = where.strip(' .')
        rec['death_type'] = death_type_from_text(info) or 'poginuo'
    return rec


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/13-hercegovacka.pdf',
        brigade_code=100,
        output_path='website/public/13-hercegovacka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§[pr]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=k8.post,
    )
