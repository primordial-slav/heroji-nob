"""
Parser: Istrski odred (brigade code 67).

Source: Maks Zadnik, "Istrski odred" (Knjižnica NOV in POS 27/1, 1975; znaci.org 00003/811.pdf)
        →  website/public/pdfs/istrski-odred.pdf (PDF pages 827-852 of the book):
    pp. 1-22    Seznam borcev   "Abram Edvard, 11. 5. 1915, Dolina—Trst"
    pp. 23-26   Padli           "Bančič Anton, roj. 16. januarja 1927 v Pazinu, padel 18. marca 1944 v Jelšanah"
Two columns, a hanging indent. Read by _slovene_lists; the fallen's bios are left to the field extractor.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, Indent, _record, columns_reader, fix_ocr, name_part, parse_roster

INDENT = Indent(padli_from=23, headings=re.compile(r'^(?:SEZNAM BORCEV|PADLI|PAD)\b'))



def keep(ln: dict) -> bool:
    """The editors' note under the roster's last column (page 22, from y 170) and the running footer go."""
    if (ln['page'] == 22 and ln['y'] > 170) or re.fullmatch(r'\d+\s+Istrski odred', ln['text'].strip()):
        return False
    return INDENT(ln)


def parse(text: str) -> dict:
    """Both lists open with the name and a comma; the roster gives the date of birth in figures."""
    if text.startswith('§p§'):                                              # the fallen: the bio as printed
        head, _, rest = fix_ocr(text[3:].strip()).partition(',')
        last, given, notes = name_part(head)
        rec = _record(last, given, '', '; '.join(notes + [rest.strip()]))
        m = re.search(r'roj\.\s*(?:\d{1,2}\.\s*\w+\s+)?(1[89]\d\d)', rest)
        if m:
            rec['birth_year'] = m.group(1)
        rec['death_type'] = 'poginuo'
        return rec
    rec = parse_roster(text)
    m = re.search(r'\b(1[89]\d\d)\b', rec['additional_info'].split(' v ')[0])
    if m and not rec.get('birth_year'):
        rec['birth_year'] = m.group(1)
    return rec


if __name__ == '__main__':
    OWN['file'] = 'istrski-odred-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/istrski-odred.pdf',
        brigade_code=67,
        output_path='website/public/istrski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=columns_reader(2),
        script='latin',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=INDENT.prepare,
        line_filter=keep,
        post_fn=repair_lj_ocr,
    )
