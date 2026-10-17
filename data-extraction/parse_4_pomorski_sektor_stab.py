"""
Parser: IV pomorski obalni sektor (brigade code 168) — its staff, a second list.

Source: Kažimir Pribilović, *Četvrti pomorski obalni sektor* (znaci.org 00003/652, the chapter 652_1.pdf, its PDF
        p. 70, book p. 485, Prilog X)  →  website/public/pdfs/4-pomorski-sektor-stab.pdf: "Štab IV POS-a", the
        sektor's commanders, political commissars, their assistants and chiefs of staff with the days each held
        the post, a name a line in capitals, given name first:
    Komandanti:
    FRANC PODBOJ 30.10-22.11.1943.
        The text layer glues some names ("BENKOMATULIĆ", "BALDOMIRSAJE") and spaces others ("MAR JAN"), so the
        posts are typed from the page (POSTS, in the page's order) and each is boxed at its line, found by the
        dates that follow the name. A man in two posts is one record with both. The roll is the unit's first list
        (IDs from 1); these get IDs from 10001.
"""
import re
import sys
from pathlib import Path

import pdfplumber

from _parser_scaffold import _record, run_parser
from parse_2_dalmatinska_stabovi import rows_of
from pdf_coords import viewer_words

PDF = 'website/public/pdfs/4-pomorski-sektor-stab.pdf'
UNIT = 'website/public/4-pomorski-sektor-soldiers.json'
SOURCE = Path(__file__).parent / '.cache' / 'znaci_photos' / 'books' / '00003_652_1.pdf'   # znaci.org 00003/652_1.pdf
PAGE = 70
TITLE = 'Štab IV POS-a'
# (surname, given name, what he was called, duty, the days as printed, a note)
POSTS = [
    ('Podboj', 'Franc', '', 'komandant', '30. 10. – 22. 11. 1943', ''),
    ('Srzić', 'Niko', '', 'komandant', '22. 11. 1943. – 3. 12. 1944', ''),
    ('Ilić', 'Josip', 'Šuro', 'politički komesar', '30. 10. – 25. 11. 1943', ''),
    ('Radelić', 'Branko', '', 'politički komesar', '25. 11. 1943. – 8. 5. 1944', ''),
    ('Dujmić', 'Jozo', '', 'politički komesar', '31. 5. 1944. – 16. 7. 1944', 'vršilac dužnosti'),
    ('Žuvić', 'Marjan', 'Karlo', 'politički komesar', '16. 7. 1944. – 15. 1. 1945', ''),
    ('Matulić', 'Benko', '', 'politički komesar', '15. 1. – 19. 3. 1945', ''),
    ('Bagat', 'Vlado', '', 'pomoćnik političkog komesara', '30. 10. 1943. – 30. 3. 1944', ''),
    ('Vukadin', 'Nenad', '', 'pomoćnik političkog komesara', '10. 4. 1944. – 19. 3. 1945', ''),
    ('Rebula', 'Ivo', '', 'načelnik štaba', '30. 10. – 7. 12. 1943', ''),
    ('Canjko', 'Augustin', '', 'načelnik štaba', '7. 12. – 28. 12. 1943', 'vršilac dužnosti'),
    ('Tomšič', 'Janez', '', 'načelnik štaba', '28. 12. 1943. – 30. 1. 1944', ''),
    ('Saje', 'Baldomir', '', 'načelnik štaba', '30. 1. 1944. – 24. 5. 1944', ''),
    ('Vrtačnik', 'Josip', '', 'načelnik štaba', '24. 5. 1944. – 8. 9. 1944', ''),
    ('Kobol', 'Viktor', '', 'načelnik štaba', '8. 9. 1944. – 19. 3. 1945', ''),
    ('Kobol', 'Viktor', '', 'vršilac dužnosti komandanta', '3. 12. 1944. – 19. 3. 1945', ''),
]
BOXES: list = []


def cut_pdf() -> None:
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(SOURCE)), PdfWriter()
    w.add_page(r.pages[PAGE - 1])
    with open(PDF, 'wb') as f:
        w.write(f)


def extract(pdf_path: str, start_page: int, end_page: int | None) -> list[dict]:
    """A name's line is a line in capitals followed by its days; Kobol's second post is in the note on his line."""
    with pdfplumber.open(pdf_path) as pdf:
        rows = rows_of(viewer_words(pdf.pages[0]))
    lines = [r for r in rows if re.match(r'^[A-ZČĆŽŠĐ]{2,}', r[0]['text']) and re.search(r'\d', ' '.join(w['text'] for w in r))
             and not r[0]['text'].startswith(('PRILOG', 'POS'))]
    assert len(lines) == len(POSTS) - 1, len(lines)
    for r in lines + [lines[-1]]:
        name = r[:next((i for i, w in enumerate(r) if not re.match(r'^[A-ZČĆŽŠĐ-]+$', w['text'])), len(r))]
        BOXES.append([round(min(w['x0'] for w in name), 1), round(min(w['top'] for w in name), 1),
                      round(max(w['x1'] for w in name), 1), round(max(w['bottom'] for w in name), 1)])
    return [{'text': '§§post' + str(i), 'x': b[0], 'y': b[1], 'page': 1} for i, b in enumerate(BOXES)]


def parse(text: str) -> dict:
    i = int(text[6:])
    rec = _record(POSTS[i][0], POSTS[i][1], '', '')
    rec['_post'] = i
    return rec


def men(soldiers: list[dict]) -> list[dict]:
    out, seen = [], {}
    for s in soldiers:
        last, given, nick, duty, days, note = POSTS[s['_post']]
        man = seen.get((last, given))
        if man is None:
            man = seen[(last, given)] = s
            s['_posts'], s['_nick'], s['_rects'] = [], nick, []
            s['unit_detail'] = 'Štab IV POS-a'
            out.append(s)
        man['_posts'].append(f"{duty}, {days}." + (f' ({note})' if note else ''))
        if BOXES[s['_post']] not in man['_rects']:
            man['_rects'].append(BOXES[s['_post']])
    for s in out:
        s['additional_info'] = '; '.join(([f"zvani {s['_nick']}"] if s['_nick'] else [])
                                         + [f"{TITLE}: {'; '.join(s['_posts'])}"])
        r = s['_rects']
        s['pdf_x'], s['pdf_y'], s['pdf_x_end'], s['pdf_y_end'] = r[0]
        if len(r) > 1:
            s['pdf_rects'] = r
        for k in ('_post', '_posts', '_nick', '_rects'):
            s.pop(k)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not Path(PDF).exists():
        cut_pdf()
    run_parser(pdf_path=PDF, brigade_code=168, output_path=sys.argv[1] if len(sys.argv) > 1 else UNIT,
               extract_fn=extract, entry_start_re=re.compile(r'^§§'), parse_entry_fn=parse, post_fn=men,
               id_start=10001, keep_other_sources=True)
