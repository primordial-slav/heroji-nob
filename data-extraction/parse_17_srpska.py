"""
Parser: 17. srpska NOU brigada (brigade code 55).

Source: Predrag Milenković, "Sedamnaesta srpska brigada" (znaci.org 00001/274_8.pdf) → website/public/pdfs/17-srpska.pdf
        (its pages 1-57): pp. 1-53 "Spisak boraca 17. srpske brigade 24. divizije NOVJ koji su preživeli rat",
        pp. 54-57 "Spisak poginulih boraca 17. srpske NOU brigade".
Cyrillic, one column, a hanging indent; the surname in capitals, the father's name (genitive) or initial and the
given name not:
    ЦВЕТАНОВИЋ Јована Светислав, рођен 1924. у Печењевцима, Лесковац, Србин, земљорадник, ступио у 17. бригаду ...
"""
import re

from _parser_scaffold import _record, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
_margin: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _margin[ln['page']] = min(_margin.get(ln['page'], 10 ** 6), ln['x'])


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}', t) or re.match(r'^(?:SPISAK|24\. DIVIZIJE|PREŽIVELI RAT|17\. SRPSKE)', t):
        return False
    if ln['x'] <= _margin[ln['page']] + 5 and re.match(rf'^[{U}]{{2}}', t):
        t = '§x§ ' + t                                                       # an entry starts at the margin
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}][{U}\-]+)\s+(?:([{U}][{L}]+|[{U}][jJ]?\.)\s+)?([{U}][{L}]+(?:-[{U}][{L}]+)?)')


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    text = re.sub(rf'^([{U}]+) - ([{U}]+)', r'\1-\2', text)
    text = text.replace('J1', 'L').replace('j1', 'l')                       # Л read as Ј1: "MIJ1ENKOVIĆ" = Milenković
    text = re.sub(rf'^([{U}]{{4,}})([{U}][{L}]+)', r'\1 \2', text)          # "TOMANOVIĆLazar"
    head, comma, rest = text.partition(',')
    m = NAME.match(head)
    if not m:
        toks = head.split()
        return _record(toks[0] if toks else '', ' '.join(toks[1:]), '', rest.strip())
    last, father, given = m.groups()
    extra = head[m.end():].strip()
    info = rest.strip()
    if extra:
        info = extra + (', ' + info if info else '')
    return _record(last, given, father or '', info)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/17-srpska.pdf',
        brigade_code=55,
        output_path='website/public/17-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=repair_cyrillic_ocr,
    )
