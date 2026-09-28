"""
Parser: 8. Krajiška NOU Brigada (brigade code 14).

Source: Izudin Čaušević — "OSMA KRAJIŠKA NOU BRIGADA"
        znaci.org/00001/146_7.pdf  →  website/public/pdfs/8-krajiska.pdf
Chapter: "Spisak poginulih i umrlih u toku NOR-a iz 8. Krajiške brigade" — pages 1-58,
single column, Latin. The table of contents and colophon follow on pages 58-63.

Entry format (father's initial in parens):
    ABDIHODŽIĆ (R) ASIM, rođen 1929, Bihać, umro maja 1943. od pjegavog tifusa.
    ADAMOVIĆ SAVO, rođen u Benakovcu, Bosanska Krupa, poginuo 28. septembra 1944. ...
    ADAMOVIĆ STEVAN - Stevo, rođen u Bihaću, ...          (nickname → additional_info)

OCR damage handled here: the father's initial ("LABUS (£>) MILAN", "LAVRNJA (š) DUŠAN"),
digits and umlauts in caps names ("PIPO (H) H1LMÖ"), a title-case given name after the
initial ("ĆAVKIĆ (H) Šukreta"), and "LJ" read as "U" (KRAGUU, UUBO → repair_lj_ocr).
"""
import re
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
TOC = re.compile(r'^S\s?A\s?D\s?R\s?Ž\s?A\s?J')
INITIAL = re.compile(rf"^(\W*[{U}][{U}\-]+(?:\s[{U}][{U}\-]+)?)\s*\(([^)\s]{{1,3}})\)'?\s+(\S+)")
_state = {'toc': False}


def _fix_initial(m: re.Match) -> str:
    letters = [c for c in m.group(2) if c.isalpha()]
    initial = f' ({letters[0].upper()})' if letters else ''
    given = m.group(3)
    if re.fullmatch(rf'[{U}][{L}]+,?', given):
        given = given.upper()                                        # "ĆAVKIĆ (H) Šukreta,"
    return f'{m.group(1)}{initial} {given}'


def keep_line(ln: dict) -> bool:
    """Drop the table of contents ("S A D R Ž AJ", p.58) and everything after it; repair name OCR."""
    if TOC.match(ln['text'].strip()):
        _state['toc'] = True
    if _state['toc']:
        return False
    t = INITIAL.sub(_fix_initial, ln['text'].strip())
    head, _, tail = t.partition(',')
    head = re.sub(rf'(?<=[{U}])1|1(?=[{U}])', 'I', head).replace('Ö', 'O').replace('Ü', 'U')   # "H1LMÖ" → HILMO
    ln['text'] = head + _ + tail
    return True


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/8-krajiska.pdf',
        brigade_code=14,
        output_path='website/public/8-krajiska-soldiers.json',
        start_page=1,
        end_page=58,
        layout='single',
        script='latin',
        line_filter=keep_line,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
