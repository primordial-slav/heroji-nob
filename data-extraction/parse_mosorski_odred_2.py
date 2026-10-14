"""
Parser: Mosorski partizanski odred (brigade code 148), the book's part II: the fighters among "Popis boraca komandnih
mjesta, partijsko-političkih i terenskih radnika na području Mosora".

Source: Velić, Petrić, *Mosorski partizanski odred* (znaci.org 00003/794, the whole book's PDF pp. 575-650: "II dio")
→ website/public/pdfs/mosorski-odred-2.pdf. The same entries as part I (parse_mosorski_odred.py reads them):
    ALFIREVIĆ Ante ANTE, rođen 1926. u Ostrvici, Omiš, zemljoradnik, Hrvat. Bio je borac pri Komandi mjesta Omiš i u
    kotarskoj Miliciji od kolovoza 1944.
but the list mixes the komande mjesta's fighters with the party and field workers, AFŽ and NOO members of the Mosor
villages. Only the fighters go in (the user's decision of 2026-10-14, the Čačak reader's rule made stricter): an entry
that says borac, names a military duty, or puts him in a unit of the army ("u NOV od", "pripadnik radnog bataljona",
"stupio u 1. dalmatinsku brigadu"); a field worker who "collected food for the NOV", an odbornik, an AFŽ member stay
out, and a man of a komanda mjesta counts only with a military duty there. These get 0148010001 on (part I: 0148000001-),
and the same man in part I is merged (scripts/find_source_duplicates.py --brigade 148).
Usage: python data-extraction/parse_mosorski_odred_2.py [--dropped N]
"""
import random
import re
import sys
from pathlib import Path

import fitz

import parse_8_kordunaska_divizija as k8
import parse_mosorski_odred as m1
from _parser_scaffold import run_parser

HERE = Path(__file__).resolve().parent
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / 'mosorski-odred-2.pdf'
DUTY = (r'komandir\w*|komandant\w*|komesar\w*|zamjenik\w*\s+(?:komandir|komandant|komesar|političk)\w*|desetar\w*|vodnik\w*|'
        r'delegat\w*\s+vod\w*|intendant\w*|(?:pušk\w*)?mitraljez(?:ac|ca|cem|ci)\b|bombaš\w*|bolničar\w*|oficir\w*|'
        r'starješin\w*|izviđač\w*|minobacač\w*|artiljer\w*|tenkist\w*')     # not "referent" (an NOO's office), nor
#                                       "vojnik", "mornar" (the old army, a trade), nor "iz mitraljeza" (shot with one)
UNIT = r'(?:brigad|odred|bataljon|bataljun|čet[aeiu]\b|vod[ua]?\b|divizij|korpus|NOVJ?\b|partizan|mornaric|KNOJ|eskadril)'
FIGHTER = re.compile(
    rf'\bbor(?:ac|kinja)\b'                              # he is one: not "tri borca ... uspjela su" (others)
    rf'|\b(?:{DUTY})\b'
    rf'|\b(?:kurir|stražar)\w*\s+(?:\S+\s+){{0,2}}(?:komand|štab|bataljon|čet|odred|brigad|partizansk)'
    rf'|\b(?:stupi[ol]\w*|otiša?[ol]\w*|uš[ao]\w*|pristupi[ol]\w*|mobiliziran\w*|mobilisan\w*|pripadnik\w*|primljen\w*)\s+'
    rf'(?:u\s+)?(?:\S+\s+){{0,4}}{UNIT}'
    rf'|\bu\s+(?:redove\s+|sastav\s+)?(?:NOVJ?|partizan\w*)\s+(?:od|je|se)\b'
    rf'|\b(?:odlask\w*|dolask\w*|prelask\w*)\s+u\s+(?:\S+\s+){{0,3}}{UNIT}', re.I)      # "do odlaska u NOVJ"
# a word that names the duty or the unit of a civilian body, not the army ("kurir NOO", "komandir seoske straže"
# stays: the partisan guards were the army's)
CHETNIK = re.compile(r'četničk\w* (?:odred|brigad|korpus|bataljon|čet\w*|komand)|ustašk\w* (?:bojn|postroj|vojsk)|domobran', re.I)


# units of the rear that are no fighting units: a komanda mjesta's rear unit, the children's pioneer companies; the
# labour battalions (radni bataljon, mostly older men, from the autumn of 1944) count, by the user's decision of
# 2026-10-14
REAR = re.compile(r'\b(?:\w+\s+)?(?:pozadinsk\w*\s+jedinic\w*|pionirsk\w*\s+čet\w*)', re.I)   # and the word before it:
#                                                                                           "komandir pionirske čete"


def fighter(rec: dict) -> bool:
    info = REAR.sub('', rec.get('additional_info') or '')
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info)


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.match(r'^(?:II\s+DIO|P\s*O\s*P\s*I\s*S\b|BORACA KOMANDNIH|I TERENSKIH RADNIKA|MOSORA$)', t):
        return False                                     # the part's title
    if re.match(r'^(?:PK|OK|KK|MK|CK|SK)\s', t):
        m1._state['open'] = False                        # "PK SKOJ-a za Dalmaciju" carries on a bio (Krstulović's)
        ln['text'] = t
        return True
    wife = re.match(r'^([A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]{2,})\s+(?:ž\.|žena)\s+(?=[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]{2})', t)
    if wife:                                             # "JAMAN žena Mate RUŽA": a wife, under her husband's name
        ln['text'] = '§x§ ' + wife.group(1) + ' ' + t[wife.end():]
        m1._state['open'] = False
        return True
    return m1.keep(ln)


DROPPED: list = []


FIX_GIVEN = {'Jahiel-Matić Luka': ('Jahiel', 'zvani Matić Luka'), 'MARIN »Đeno-': ('Marin', 'zvani Đeno')}


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s['first_name'] in FIX_GIVEN:
            s['first_name'], note = FIX_GIVEN[s['first_name']]
            s['additional_info'] = f"{note}; {s['additional_info']}"
    soldiers = m1.post(soldiers)
    kept = [s for s in soldiers if fighter(s)]
    DROPPED[:] = [s for s in soldiers if not fighter(s)]
    print(f'{len(soldiers)} entries in part II, {len(kept)} fighters kept, {len(DROPPED)} left out')
    return kept


if __name__ == '__main__':
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_794.pdf'), fitz.open()
        out.insert_pdf(src, from_page=574, to_page=649)
        out.save(PDF, garbage=4, deflate=True)
    k8.corpus()
    run_parser(
        pdf_path=str(PDF.relative_to(HERE.parent)).replace('\\', '/'),
        brigade_code=148,
        output_path='website/public/mosorski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=m1.parse,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
    if '--dropped' in sys.argv:
        random.seed(3)
        for s in random.sample(DROPPED, min(len(DROPPED), int(sys.argv[sys.argv.index('--dropped') + 1]))):
            print(f"  OUT {s['last_name']} {s['first_name']}: {s['additional_info'][:150]}")
