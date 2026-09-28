"""
Parser: 6. Krajiška NOU Brigada (brigade code 13).

Source: Branko Damjanović, Savo Popović — "ŠESTA KRAJIŠKA NOU BRIGADA"
        znaci.org/00003/711_2.pdf  →  website/public/pdfs/6-krajiska.pdf
Chapter: "Spisak poginulih i umrlih boraca i starješina Šeste krajiške NOU brigade".
Single column, Latin. p.1 title, p.2 preface (sources), then three lists:
    pp. 3-63   main alphabetical list        ABRAMOVIĆ IVAN, borac, rođen u Travniku. Poginuo ...
                                             ADAMOVIĆ Nikole BORIŠA, borac, rođen 1910. godine u ...
    pp. 63-68  "DOPUNSKI SPISAK"              1. ADAMOVIĆ (Stojana) PERO, rođen 1911. godine u ...
    pp. 68-69  "NAKNADNO PRIKUPLJENI PODACI"  1. AGBABA Stojana PETAR, rođen 1921. godine ...
The supplementary lists are numbered and put the father's name in parens; both are
normalized to the main list's form before grouping.
"""
import re
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEADINGS = re.compile(r'^(?:DOPUNSKI SPISAK|poginulih boraca Šeste krajiške|NAKNADNO PRIKUPLJENI PODACI|[{}])$'.format(U))
NUMBERED = re.compile(rf'^\d{{1,3}}\.\s+(?=[{U}]{{2,}})')
FATHER_IN_PARENS = re.compile(rf'^([{U}][{U}\-]+(?:\s-\s[{U}][{U}\-]+)?)\s+\(([{U}][{L}]+)\)\s+')


def _join_split_surname(m: re.Match) -> str:
    return m.group(1).replace(' ', '') + ' '


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip().replace('­', '-')    # soft hyphen at line ends ("Kru­ pa")
    if HEADINGS.match(t):
        return False
    t = re.sub(rf'^[(\s,.\']+(?=[{U}]{{2}}|[{U}] [{U}])', '', t)   # "( PRAĆA", ",P RAŠTALO"
    t = NUMBERED.sub('', t)                          # "1. ADAMOVIĆ (Stojana) PERO" → "ADAMOVIĆ Stojana PERO"
    t = FATHER_IN_PARENS.sub(r'\1 \2 ', t)
    t = re.sub(rf'^([{U}](?: [{U}]{{2,}})+)\s(?=[{U}][{L}]+\s+[{U}]{{2,}})', _join_split_surname, t)   # "B JELO VUK Lazara BRANKO"
    t = re.sub(rf'^([{U}]{{2,}}) - ([{U}]{{2,}})\b', r'\1-\2', t)                                      # "AHMETOVIĆ - BEŠIĆ"
    t = re.sub(rf'^([{U}][{U}\-]+\s+[{U}][{L}]+\s+)([{U}][{L}]+)(?=,)', lambda m: m.group(1) + m.group(2).upper(), t)   # "LJEVAR Vase Mladen,"
    ln['text'] = t
    return True


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/6-krajiska.pdf',
        brigade_code=13,
        output_path='website/public/6-krajiska-soldiers.json',
        start_page=3,
        end_page=None,
        layout='single',
        script='latin',
        line_filter=keep_line,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
