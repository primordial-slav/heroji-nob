"""
Parser: 1. Šumadijska Brigada (brigade code 15).

Source: Isidor Đuković — "PRVA ŠUMADIJSKA BRIGADA"
        znaci.org/00001/102_6.pdf  →  website/public/pdfs/1-sumadijska.pdf
Single column, Cyrillic. Two lists:
    pp. 2-28   "SPISAK POGINULIH BORACA I STAREŠINA PRVE ŠUMADIJSKE BRIGADE"
    pp. 29-53  "SPISAK BORACA I STAREŠINA ... KOJI SU PREŽIVELI RAT"
followed by the literature (54-55) and the table of contents.

Entry format (both parents, nicknames in parens and after the given name):
    АБАФИ Ћирила и Станиславе БРАНИСЛАВ (БРАНКО) Риста, политички комесар чете. Рођен
    20. II 1923. године у Земуну. Матурант. Словак. ...
The mother's name and the nicknames go to the start of the bio ("majka Stanislava; zvani
Branko, Rista; politički komesar čete. Rođen ..."), since the site has no fields for them.
"""
import re
from _parser_scaffold import repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

HEADING = re.compile(r"^(?:[':\s]*[A-ZČĆŽŠĐ]\s*$|:?\s*S ?P ?I ?S ?A ?K|POGINULIH BORACA|PRVE ŠUMADIJSKE BRIGADE$|BORACA I STAREŠINA PRVE|"
                     r"ŠUMADIJSKE NOU BRIGADE KOJI SU|PREŽIVELI RAT)")
BORN = re.compile(r'\bRođen[a]?\s+(?:\d{1,2}\.\s*(?:[IVX]+|\d{1,2})\.?\s+|\d{1,2}\.\s*[a-zčćžšđ]+\s+)?((?:18|19)\d\d)')


def keep_line(ln: dict) -> bool:
    return not HEADING.match(ln['text'].strip())


def _nominative_female(name: str) -> str:
    return name[:-1] + 'a' if name.endswith('e') else name       # Stanislave → Stanislava, Marije → Marija


def finish(soldiers):
    for s in soldiers:
        info = s['additional_info']
        nicks = []
        m = re.match(r'^zvani ([^;]+);\s*', info)
        if m:
            nicks.append(m.group(1))
            info = info[m.end():]
        m = re.match(r'^((?:[A-ZČĆŽŠĐ][a-zčćžšđ]+\s?){1,3}),\s*', info)   # "Rista, politički komesar čete."
        if m:
            nicks.append(m.group(1).strip())
            info = info[m.end():]
        prefix = []
        mother = s.pop('mothers_name', '')
        if mother:
            prefix.append('majka ' + _nominative_female(mother))
        if nicks:
            prefix.append('zvani ' + ', '.join(nicks))
        s['additional_info'] = '; '.join(prefix + [info])
        by = BORN.search(info)
        if by:
            s['birth_year'] = by.group(1)
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/1-sumadijska.pdf',
        brigade_code=15,
        output_path='website/public/1-sumadijska-soldiers.json',
        start_page=2,
        end_page=53,
        layout='single',
        script='cyrillic',
        line_filter=keep_line,
        post_fn=lambda soldiers: finish(repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers)))),
    )
