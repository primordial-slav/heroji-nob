"""
Parser: 3. Krajiška Proleterska Brigada (brigade code 10).

Source: Savo Trikić — "TREĆA KRAJIŠKA PROLETERSKA BRIGADA"
        znaci.org/00001/224_18.pdf  →  website/public/pdfs/3-krajiska-proleterska.pdf
Chapter: "Spisak palih boraca Treće proleterske krajiške brigade s osnovnim matičnim
         podacima poginulih" — pages 3-126, two columns, Latin. Pages 1-2 are sources,
         127-129 the table of contents.

Entry format:
    ČOVIĆ Miodraga PETRONIJE, rođen 1924. ..., zemljoradnik, Srbin, u NOB i u Brigadi od
    1942, borac, poginuo 11. 6. 1944. kod Kupresa
The column gutter moves between odd and even pages, so it is found per page (col_split_x='auto').
"""
import re
from _parser_scaffold import repair_lj_ocr, restore_diacritics, run_parser

INTRO_END_Y = {3: None}      # p.3 opens with the chapter title and an explanatory note
TITLE = re.compile(r'^(?:Spisak palih boraca|proleterske krajiške brigade|s osnovnim matičnim|podacima poginulih|\*|'
                   r'Osim popisa|i borci koji|Prema raspoloživoj|podaci:|tina i SR|NOB i u Brigadu|nost na kojoj|gde je sahranjen|[A-ZČĆŽŠĐ]$)')


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip().replace('­', '-')
    if ln['page'] == 3 and TITLE.match(t):
        return False
    if re.fullmatch(r'[A-ZČĆŽŠĐ]', t) or re.match(r'^(?:NA)?RODNI HEROJ', t):   # section letters; photo captions
        return False
    ln['text'] = t
    return True


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/3-krajiska-proleterska.pdf',
        brigade_code=10,
        output_path='website/public/3-krajiska-proleterska-soldiers.json',
        start_page=3,
        end_page=126,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        line_filter=keep_line,
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(soldiers)),
    )
