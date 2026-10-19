"""
Jaša Romano, *Jevreji Jugoslavije 1941-1945. Žrtve genocida i učesnici narodnooslobodilačkog rata* (Beograd 1980;
znaci.org 00001/191, the chapter 191_4.pdf → website/public/pdfs/jevreji-jugoslavije-ucesnici-nor.pdf): "Spisak učesnika
u NOR" (book p. 307 on), the Jewish participants in the war of liberation with a biography each, a book across units:
its entries are added to the records of the soldiers it describes (scripts/match_references.py), the rest go to Ostali
borci.

Two columns, each entry hanging (its first line at the column's edge, the rest indented): "Abinun Benjamina Heskija,
brijački radnik iz Sarajeva, rođen 1918. U NOV od septembra 1941. Borac u 6. prolet. istočno-bosanskoj brigadi, a zatim
u 1. četi 4. bataljona 2. prolet. brigade. Poginuo 15. XII 1942. prilikom napada brigade na Livno." The name runs to
the first comma: surname (a married woman's two: "Abinun-Papo"), the father in the genitive or his initial, a title
(dr, ing., mr ph.), the given name. The list counts everyone in the NOP: political workers, the NOO's and the AFŽ's
people, the workshops and hospitals; only the fighters go in, by the rule of `parse_mosorski_odred_2.fighter`.

Output: data-extraction/znaci/jevreji-jugoslavije-ucesnici-nor-entries.json (IDs 9061xxxxxx, in the book's order:
the list has no numbers, so a re-parse must keep the entries in place).
Usage: python data-extraction/parse_jevreji_jugoslavije.py [--sample N] [--dropped N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402

PDF = 'jevreji-jugoslavije-ucesnici-nor.pdf'
OUT = HERE / 'znaci' / 'jevreji-jugoslavije-ucesnici-nor-entries.json'
PREFIX = '9061'
TITLE = 'Jevreji Jugoslavije, učesnici NOR'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
TITLES = re.compile(r'^(?:dr|ing\.?|mr|ph\.?|phil\.?|prof\.?|inž\.?|i)$', re.I)   # "dr phil. i mr ph."
# the site's brigades and odredi as the bios name them
UNITS = [(r'\b(?:1\.|I)\s*prolet\w*\.?\s+(?:udarn\w*\s+)?brigad', 1), (r'\b(?:2\.|II)\s*prolet\w*\.?\s+(?:udarn\w*\s+)?brigad', 39),
         (r'\b(?:3\.|III)\s*prolet\w*\.?\s+(?:\(?\s*)?sandžačk', 5), (r'\b(?:4\.|IV)\s*prolet\w*\.?\s+(?:\(?\s*)?crnogorsk', 40),
         (r'\b(?:5\.|V)\s*prolet\w*\.?\s+(?:\(?\s*)?crnogorsk', 41),
         (r'\b(?:6\.|VI)\s*(?:prolet\w*\.?\s+)?istočno-?\s*bosansk', 42), (r'\b(?:13\.|XIII)\s*prolet', 6),
         (r'\b(?:1\.|I)\s*dalmatinsk\w*\s+(?:prolet\w*\.?\s+)?brigad', 36), (r'\b(?:2\.|II)\s*dalmatinsk', 7),
         (r'\b(?:3\.|III)\s*dalmatinsk', 46), (r'\bUžičk\w*\s+(?:partizansk\w*\s+|NOP\s+)?odred', 26),
         (r'\b(?:1\.|I)\s*ličk', 2), (r'\b(?:2\.|II)\s*ličk', 3), (r'\b(?:10\.|X)\s*hercegovačk', 43),
         (r'\b(?:1\.|I)\s*vojvođansk\w*\s+brigad', 9), (r'\b(?:12\.|XII)\s*slavonsk', 146),
         (r'\bVrhovn\w*\s+štab', 112), (r'\bCentraln\w*\s+bolnic', 117)]


def read() -> list[dict]:
    entries = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for col in entry_boxes.read_page(page, 2)['columns']:
                body = [ln for ln in col if not re.match(r'^(?:\d{3}\s+J\.\s*Romano|J\.\s*Romano\s+\d{3}|SPISAK UČESNIKA)', ln['text'].strip())]
                if not body:
                    continue
                edge = min(ln['x0'] for ln in body)
                for ln in body:
                    t = ln['text'].strip()
                    starts = ln['x0'] < edge + 3 and re.match(rf'^[{U}][{L}]+(?:-[{U}][{L}]+)?\s+\S', t)
                    if starts:
                        entries.append({'lines': [t], 'pdf_page': pno, 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)})
                    elif entries:
                        entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[­-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('­-') + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    head, _, info = text.partition(',')
    unknown = '(prezime nepoznato)' in head                         # "Jakica (prezime nepoznato), iz Sarajeva"
    words = [w for w in head.replace('(prezime nepoznato)', '').split() if not TITLES.match(w)]
    if unknown:
        words = [''] + words
    last = words[0] if words else ''
    rest = words[1:]
    father = ''
    if last and len(rest) >= 2 and (re.fullmatch(rf'[{U}][{L}]+', rest[0]) or re.fullmatch(rf'[{U}]\.', rest[0])):
        father, rest = rest[0], rest[1:]
    first = rest[0] if rest else ''
    nick = ' '.join(rest[1:])
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': ' '.join(x for x in (last, father, first, nick) if x),
           'last_name': last, 'also': last.split('-') if '-' in last else [], 'first_name': first, 'nick': nick,
           'fathers_name': father, 'no': n}
    born = re.search(r'\b[Rr]ođen[a]?\s+(?:je\s+)?(1[89]\d\d)\.?(?:\s+(?:godine\s+)?u\s+([{U}][^,.;]+?))?(?=[,.;]|\s+(?:U|Po|Od|Pred|Kao|Do)\b)'.replace('{U}', U), info)
    rec['birth_year'] = born.group(1) if born else ''
    rec['born_in'] = born.group(2).strip() if born and born.group(2) else ''
    if not rec['born_in']:
        here = re.search(rf'\biz\s+([{U}][{L}]+(?:\s+[{U}][{L}]+)?),\s+gde\s+je\s+i\s+rođen', info)
        rec['born_in'] = here.group(1) if here else ''
    death = None
    for d in re.finditer(r'\b(?:Poginu\w*|Umr[oal]\w*|Ubijen\w*|Strelja\w*|Strijelja\w*|Nesta[ol]\w*)[^.]*?(19[45]\d)', info):
        death = d
    rec['death_year'] = death.group(1) if death else ''
    rec['death_date'] = ''
    rec['survived'] = bool(re.search(r'\b(?:Posle|Poslije)\s+(?:oslobođenja|rata)|\bŽivi\s+u\b|\bumro\s+19[5-9]\d', info))
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, info, re.I)})
    rec['additional_info'] = f'{TITLE}: {text}'
    rec['list'] = TITLE
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main() -> None:
    raw = read()
    every = [parse(e, i) for i, e in enumerate(raw, 1)]
    # the list is of the participants in the NOR: the fighters (also by a rank, a unit the entry puts them in, or "u
    # partizane"), and since the user's decision of 2026-10-19 everyone else in it too, marked as activists (the party's
    # and SKOJ's people, the NOO's, the helpers, those caught on the way to the partisans)
    for r in every:
        if not mos.fighter(r) and not mos.fighter_or_officer(r):
            r['role'] = 'activist'
    recs = every
    dropped = []
    print(f"fighters by the rule {sum(mos.fighter(r) for r in every)}, by rank or unit "
          f"{sum(not mos.fighter(r) and not r.get('role') for r in every)}, activists {sum(bool(r.get('role')) for r in every)}")
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(every)} entries; {len(recs)} fighters kept, {len(dropped)} left out; boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    print(f"  no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
          f"birthplace: {sum(bool(r['born_in']) for r in recs)}, year of death: {sum(bool(r['death_year']) for r in recs)}, "
          f"survived: {sum(r['survived'] for r in recs)}, units: {Counter(u for r in recs for u in r['units']).most_common(12)}")
    odd = [r for r in every if not re.fullmatch(rf'[{U}][{L}]+(?:-[{U}][{L}]+)?', r['last_name'] or 'X') or not r['first_name']]
    print(f'  odd names: {len(odd)}', [r['name'] for r in odd[:15]])
    if '--dropped' in sys.argv:
        k = int(sys.argv[sys.argv.index('--dropped') + 1])
        random.seed(3)
        for r in random.sample(dropped, min(k, len(dropped))):
            print(f"  OUT {r['name']}: {r['additional_info'][len(TITLE) + 2:][:170]}")
    if '--sample' in sys.argv:
        random.seed(4)
        for r in random.sample(recs, min(len(recs), int(sys.argv[sys.argv.index('--sample') + 1]))):
            print(f"   {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']}")
            print(f"      {r['additional_info'][len(TITLE) + 2:][:160]}")


if __name__ == '__main__':
    main()
