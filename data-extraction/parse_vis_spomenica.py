"""
Veseljko Huljić, *Vis 1941-1945* (Split, 1979; znaci.org 00003/804, the whole book's PDF p. 578 → website/public/pdfs/vis-spomenica-1941.pdf):
"Nosioci »Spomenice 1941.« i važnija odlikovanja" (book p. 521), the 41 holders of the spomenica from the Vis
archipelago, a book across units: its entries are added to the records of the soldiers it describes
(scripts/match_references.py), the rest go to Ostali borci.

Two columns, numbered, a name a line, surname first: "8. Božanić Andrija-Stevo", "27. Repanić Nikola-Gandi" (a nickname
after the given name's hyphen), "3. Bjažević-Jadrijević Katica" (a woman's two surnames). znaci re-typeset the page from
its OCR, so it shows the OCR's slips; four are read back here (READ). Under the list the book names Božanić Andrija a
narodni heroj; that sentence goes into his entry. The list names nothing more (no year, no village), so the matcher has
the name alone: scripts/select_vis_references.py takes a record of the name that is of the island (unit 172, the
Viški bataljon, or a birthplace on Vis, Komiža or Biševo).

Output: data-extraction/znaci/vis-spomenica-1941-entries.json (IDs 9043xxxxxx, by the book's number).
Usage: python data-extraction/parse_vis_spomenica.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402

PDF = 'vis-spomenica-1941.pdf'
OUT = HERE / 'znaci' / 'vis-spomenica-1941-entries.json'
PREFIX = '9043'
TITLE = 'Nosioci »Spomenice 1941.«, viško otočje'
# the OCR's slips on the re-typeset page: "Piamengo" is Fiamengo of Komiža, "Zaja Vicko" Žaja Vicko of Vis (11.
# dalmatinska), "Mar j an", and "Žuaniić Tomislav" the Zuanić whom the book's note names ("Tomislava Zuanića")
READ = {17: 'Fiamengo Ante', 25: 'Petric Marjan', 37: 'Žaja Vicko', 41: 'Zuanić Tomislav'}
HERO = {8: ('Ordenom narodnog heroja odlikovan je Božanić Andrija, prvoborac i organizator predratnog revolucionarnog '
            'radničkog pokreta i usmjerivač razvitka NOP-a viško-otočkog područja, a sa dužnosti člana PK odnosno '
            'Oblasnog komiteta KPH za Dalmaciju.')}


def read() -> dict[int, dict]:
    found = {}
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for col in entry_boxes.read_page(page, 2)['columns']:
                for ln in col:
                    m = re.match(r'^(\d{1,2})\.\s+(.+)$', ln['text'].strip())
                    if m and 1 <= int(m.group(1)) <= 41 and int(m.group(1)) not in found:
                        found[int(m.group(1))] = {'text': m.group(2).strip(), 'pdf_page': pno,
                                                  'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)}
    return found


def main():
    found = read()
    missing = sorted(set(range(1, 42)) - set(found))
    assert not missing, missing
    recs = []
    for no in range(1, 42):
        e = found[no]
        printed = READ.get(no, re.sub(r'\s+', ' ', e['text']))
        last, given = printed.split(' ', 1)
        nick = ''
        if '-' in given:                                   # "Andrija-Stevo", "Ivan-Cura", "Petar-Slovenko"
            given, nick = given.split('-', 1)
        also = last.split('-') if '-' in last else []      # "Bjažević-Jadrijević", "Zuanić-Backović"
        text = f'{TITLE}: {no}. {printed}.' + (f' {HERO[no]}' if no in HERO else '')
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {given}' + (f' — {nick}' if nick else ''),
                     'last_name': last, 'first_name': given, 'also': also, 'nick': nick, 'fathers_name': '',
                     'birth_year': '', 'born_in': '', 'death_year': '', 'death_date': '', 'survived': True, 'units': [],
                     'no': no, 'list': TITLE, 'additional_info': text, 'pdf_file': PDF, 'pdf_page': e['pdf_page'],
                     'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']})
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    for r in recs:
        print(f"  {r['no']:2}. {r['name']}" + (f"  (also {r['also']})" if r['also'] else ''))


if __name__ == '__main__':
    main()
