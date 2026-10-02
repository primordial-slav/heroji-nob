"""
Parser: 12. srpska NOU brigada (brigade code 90).

Source: Dragoljub Mirčetić, "12. srpska brigada" (znaci.org 00003/841.pdf, its pages 357-402, Prilog 3)
        →  website/public/pdfs/12-srpska.pdf. Cyrillic, one column, a hanging indent:
    "Pregled poginulih i umrlih boraca i rukovodilaca" (the archive's lists hold 324; the author added more):
        ANĐELKOVIĆ Vlajka MIHAJLO, 1914, Jakovljevo, Vlasotince, ciglarski radnik. U NOVJ od 12. oktobra 1944,
            borac 2. bataljona. Poginuo 22. novembra 1944. kod Trepče, na Kosovu.
The same author and the same form as the 23. srpska's list, read by that parser (parse_23_srpska: Ћ read as Н, Б or
Е, Ђ as Б, Latin look-alikes of Cyrillic letters). The footnote under the author's note on p. 1 is left out.
"""
import re

import parse_23_srpska as p23
from _parser_scaffold import run_parser


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 1 and ln['y'] > 290 or re.match(r'^\d', t):
        return False                                                         # the footnote on the archive's lists
    return p23.keep(ln)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/12-srpska.pdf',
        brigade_code=90,
        output_path='website/public/12-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=p23.parse,
        prepare_fn=p23.prepare,
        line_filter=keep,
        post_fn=p23.post,
    )
