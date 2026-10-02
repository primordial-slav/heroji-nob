"""
Parser: Škofjeloški odred (brigade code 66).

Source: Tone Lotrič, "Škofjeloški odred" (Knjižnica NOV in POS 26/2, 1971; znaci.org 00003/809.pdf)
        →  website/public/pdfs/skofjeloski-odred.pdf (PDF pages 314-320 of the book): "Seznam borcev", 519 numbered
names, all the odred's surviving files give in full ("Many of them fell in the war, some have died since"):
    29. Benedičič Franc-Cvek
    515. Zontar Janez — Sv. Duh
Two columns, a soldier a line. The names only; a place after a dash tells namesakes apart.
"""
import re

from _parser_scaffold import repair_lj_ocr, run_parser
from _slovene_lists import OWN, _record, fix_ocr, name_part, surnames_and_places


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    m = re.match(r'^(\d{1,3})\.\s*(\S.*)$', t)
    if not m:
        return False                                                         # the heading, the note, page numbers
    ln['text'] = '§s§ ' + m.group(2)
    return True


def parse(text: str) -> dict:
    text = fix_ocr(re.sub(r'^§s§\s*', '', text))
    name, place = (re.split(r'\s+[—–-]\s+', text, 1) + [''])[:2]                 # "Demšar Anton - Zabukovje": his village
    last, given, notes = name_part(name)
    return _record(last, given, '', '; '.join(notes + ([place.strip()] if place.strip() else [])))



def post(soldiers: list[dict]) -> list[dict]:
    """"Demšar Anton-Zabukovje": after the hyphen a village (a place the corpus knows), not a nickname ("-Cvek")."""
    soldiers = repair_lj_ocr(soldiers)
    _, places = surnames_and_places()
    for s in soldiers:
        m = re.match(r'^zvani (.+?)(;|$)', s['additional_info'])
        if m and (places[m.group(1)] >= 1 or m.group(1).startswith('Sv.')):
            s['additional_info'] = m.group(1) + s['additional_info'][m.end(1):]
    return soldiers


if __name__ == '__main__':
    OWN['file'] = 'skofjeloski-odred-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/skofjeloski-odred.pdf',
        brigade_code=66,
        output_path='website/public/skofjeloski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        col_split_x='auto',
        script='latin',
        entry_start_re=re.compile(r'^§s§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
