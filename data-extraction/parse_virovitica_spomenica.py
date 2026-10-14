"""
Savo Velagić, *Virovitica u narodnooslobodilačkoj borbi i socijalističkoj revoluciji* (Virovitica, 1979; znaci.org
00003/653, the whole book's PDF pp. 221-238 → website/public/pdfs/virovitica-spomenica-1941.pdf, book pp. 221-239):
part IV, "Nosioci partizanske spomenice 1941.", the fourteen holders of the spomenica of the Virovitica municipality, a
biography each under a portrait, a book across units: its entries are added to the records of the soldiers it describes
(scripts/match_references.py), the rest go to Ostali borci.

Each bio stands under its portrait's caption and a heading in capitals, given name first, the surname, then what he was
called: "BENEDIKT AUDI GRGA", "AGNEZA AMANOVIĆ DARINKA (rođena Vostrel)" (the book's index has them surname first, "Audi
Benedikt Grga", "Fiket Mirko Mesarić"). A bio runs on to the next page, and a portrait's caption may stand in it (Dragan
Volner's); the captions are dropped by their place (centred, no figures or stops). The entry keeps the whole bio, under
the list's title (which gives the record the medal).

Output: data-extraction/znaci/virovitica-spomenica-1941-entries.json (IDs 9070xxxxxx, in the book's order).
Usage: python data-extraction/parse_virovitica_spomenica.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from statistics import median

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'virovitica-spomenica-1941.pdf'
OUT = HERE / 'znaci' / 'virovitica-spomenica-1941-entries.json'
PREFIX = '9070'
TITLE = 'Nosioci partizanske spomenice 1941., općina Virovitica'
# the PDF's first page is the part's title (book p. 221); the bios begin on p. 223
BOOK_PAGE = {1: 221, **{p: 221 + p for p in range(2, 19)}}
# the headings as printed, given name first: (surname, given name, what he was called, other surnames)
PEOPLE = {
    'AGNEZA AMANOVIĆ DARINKA': ('Amanović', 'Agneza', 'Darinka', ['Vostrel']),
    'BENEDIKT AUDI GRGA': ('Audi', 'Benedikt', 'Grga', []),
    'MIRKO FIKET MESARIĆ': ('Fiket', 'Mirko', 'Mesarić', []),
    'SRĐAN MILJANOVIĆ RASKO': ('Miljanović', 'Srđan', 'Rasko', []),
    'NEDELJKO MRĐEN': ('Mrđen', 'Nedeljko', '', []),
    'RUDI RAJH TOP': ('Rajh', 'Rudi', 'Top', []),
    'JAKŠA REBIĆ': ('Rebić', 'Jakša', '', []),
    'DRAGAN ROLLER': ('Roller', 'Dragan', '', []),
    'IVAN SAMBOLIČEK SLAVKO': ('Samboliček', 'Ivan', 'Slavko', []),
    'STEVO TARBUK': ('Tarbuk', 'Stevo', '', []),
    'ZDRAVKO USKOKOVIĆ HEROJ': ('Uskoković', 'Zdravko', 'Heroj', []),
    'DRAGAN VOLNER BAĆUŠKA': ('Volner', 'Dragan', 'Baćuška', []),
    'ZDENKO VOLNER SANJO': ('Volner', 'Zdenko', 'Sanjo', []),
    'MIROSLAV VOSTREL': ('Vostrel', 'Miroslav', '', []),
}
# the site's units a bio names
UNITS = [
    (r'\b12\.\s*(?:slavonsk|NO brigad|proletersk)', 146),
    (r'\b16\.\s*(?:slavonsk|omladinsk)', 37),
    (r'\b17\.\s*(?:slavonsk|NO brigad)', 16),
    (r'\b18\.\s*slavonsk', 17),
    (r'\b21\.\s*slavonsk', 34),
    (r'\b25\.\s*brodsk|\bBrodsk\w*\s+(?:NO\s+|udarn\w*\s+)?brigad', 30),
    (r'\bKalničk\w*\s+(?:NOP\s+|partizansk\w*\s+)?odred', 58),
    (r'\b(?:sedm\w*|7\.)\s*krajišk', 48),
    (r'\bOsječk\w*\s+(?:udarn\w*\s+)?(?:NO\s+)?brigad', 104),
    (r'\b32\.\s*divizij', 35),
]
MONTHS = ('siječnja veljače ožujka travnja svibnja lipnja srpnja kolovoza rujna listopada studenog prosinca').split()


def lines_of(page) -> list[dict]:
    """The page's lines, keeping what entry_boxes.group_lines takes for a speck: a justified line's last short word
    stands far from the one before it ("organizacijama   u", "SUBNOR-a   Vi-")."""
    words = [w for w in viewer_words(page, keep_blank_chars=False) if w['text'].strip()]
    h = median(w['bottom'] - w['top'] for w in words)
    out = []
    for ws in entry_boxes._cluster(words, 0.45 * h):
        out.append({'x0': min(w['x0'] for w in ws), 'x1': max(w['x1'] for w in ws), 'top': min(w['top'] for w in ws),
                    'bottom': max(w['bottom'] for w in ws), 'text': ' '.join(w['text'] for w in ws)})
    return out


def is_heading(t: str) -> bool:
    letters = [c for c in t.split('(')[0] if c.isalpha()]
    return len(letters) > 5 and sum(c.isupper() for c in letters) / len(letters) > .8


def read() -> list[dict]:
    people, cur = [], None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            if pno == 1:
                continue                                           # "IV DIO / Nosioci partizanske spomenice 1941."
            lines = lines_of(page)
            left = min(ln['x0'] for ln in lines)
            for ln in lines:
                t = ln['text'].strip()
                if re.fullmatch(r'\d{1,3}', t):
                    continue                                       # the page number
                if is_heading(t):
                    key = re.sub(r'\s+', ' ', t.split('(')[0]).strip()
                    assert key in PEOPLE, key
                    cur = {'key': key, 'heading': t, 'lines': [], 'page': pno, 'top': ln['top'], 'left': left,
                           'x1': ln['x1'], 'bottom': ln['bottom']}
                    people.append(cur)
                    continue
                if ln['x0'] > left + 60 and not re.search(r'[\d.,;]', t) and t[:1].isupper():
                    continue                                       # a portrait's caption
                if cur is None:
                    continue
                cur['lines'].append(t)
                if pno == cur['page']:
                    cur['x1'], cur['bottom'] = max(cur['x1'], ln['x1']), ln['bottom']
    assert len(people) == len(PEOPLE), len(people)
    return people


def join(lines: list[str]) -> str:
    text = ''
    for t in lines:
        if re.search(r'[a-zčćšžđ][\xad-]$', text) and t[:1].islower():
            text = text[:-1] + t                                   # a word broken at the line's end
        else:
            text = (text + ' ' + t).strip()
    return re.sub(r'\s+', ' ', text.replace('\xad', ''))


def main():
    recs = []
    for no, p in enumerate(read(), 1):
        last, given, nick, also = PEOPLE[p['key']]
        bio = join(p['lines'])
        born = re.search(r'\bRođen[a]? je (?:(\d{1,2})\. (\w+) )?(\d{4})\. u ([^.]+?)\.(?:\s|$)', bio)
        birth_year, born_in = (born.group(3), born.group(4).strip()) if born else ('', '')
        birth_date = ''
        if born and born.group(2) in MONTHS:
            birth_date = f'{born.group(3)}-{MONTHS.index(born.group(2)) + 1:02d}-{int(born.group(1)):02d}'
        units = sorted({code for rx, code in UNITS if re.search(rx, bio)})
        heading = re.sub(r'\s+', ' ', p['heading'])
        recs.append({'soldier_id': f'{PREFIX}{no:06d}', 'name': f'{last} {given}' + (f' — {nick}' if nick else ''),
                     'last_name': last, 'first_name': given, 'also': also, 'nick': nick, 'fathers_name': '',
                     'birth_year': birth_year, 'birth_date': birth_date, 'born_in': born_in, 'death_year': '',
                     'death_date': '', 'survived': True, 'units': units, 'no': no, 'list': TITLE,
                     'additional_info': f'{TITLE}: {heading}. {bio}', 'source_page': BOOK_PAGE[p['page']],
                     'pdf_file': PDF, 'pdf_page': p['page'], 'pdf_x': round(p['left'], 1), 'pdf_y': round(p['top'], 1),
                     # the heading and the bio down to its page's end (the PDF is in entry_boxes.INLINE_ENTRIES)
                     'pdf_x_end': round(p['x1'], 1), 'pdf_y_end': round(p['bottom'], 1)})
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}')
    for r in recs:
        print(f"  {r['no']:2}. {r['name']}, {r['birth_date'] or r['birth_year']}, {r['born_in']}, units {r['units']}, "
              f"p. {r['source_page']}, {len(r['additional_info'])} chars")


if __name__ == '__main__':
    main()
