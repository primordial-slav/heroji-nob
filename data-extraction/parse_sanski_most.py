"""
Branko J. Bokan, *Srez Sanski Most u NOB 1941–1945. godine* III (znaci.org 00003/796, PDF pp. 403-726, "Za vječitu
spomen i zahvalnost borcima narodnooslobodilačke borbe i žrtvama fašističkog terora") →
website/public/pdfs/sanski-most-borci.pdf: a book across units.

The lists stand village by village (a heading in capitals, some letter-spaced: "D E D O V A Č A"), each village's in
this order: "Borci poginuli u NOB", "Nosioci Partizanske spomenice 1941. godine", "Borci NOB 15. maja 1945. godine"
(the rest of its fighters, alive at the war's end) and "Žrtve fašističkog terora" (names only: left out). One column,
each entry hanging:
    "ADAMOVIĆ Nikole VITOMIR, rođen 1910, zemljoradnik, samouk, stupio u NOB 1942. godine, poginuo 1942. kod
     Sanskog Mosta;"
The fallen and the holders of the Spomenica go in whole (the book names them fighters, and the Spomenica was given
for joining in 1941); the third list also counts members of village NOOs, odbornici and party officials, so it keeps
only fighters, by the rule for mixed lists (parse_mosorski_odred_2.fighter: borac, a military duty or an army unit).
Output: data-extraction/znaci/sanski-most-borci-entries.json, IDs 9042xxxxxx (by the entry's place among all the
book's entries, left-out ones included, so the IDs stay put), each with its box.
Usage: python data-extraction/parse_sanski_most.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import fitz
import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import _karlovac_lists as kl  # noqa: E402
import entry_boxes  # noqa: E402
import parse_mosorski_odred_2 as mosor  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402

BOOK = 'sanski-most-borci'
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / f'{BOOK}.pdf'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9042'
FIRST, LAST = 403, 726                  # the book's PDF pages: the lists' introduction to the last village (Trnova)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LISTS = [(re.compile(r'^(?:Borci\s+pogin|Poginul\w*\s+borc)', re.I), 'fallen', 'Borci poginuli u NOB'),   # "Poginuli borci NOB" too
         (re.compile(r'^Nosioc\w*\s+Partiz', re.I), 'spomenica', 'Nosioci Partizanske spomenice 1941. godine'),
         (re.compile(r'^Borci\s+NO[BR]', re.I), 'alive', 'Borci NOB 15. maja 1945. godine'),
         (re.compile(r'^Žrtve\s+faš', re.I), 'victims', '')]
# "MILOJICA Mile", "DOŠENOVIĆ LÄZO", "VRUĆINIĆ,"; not a line of a bio that begins with an organisation ("KPJ u Beogradu")
START = re.compile(rf'^(?!(?:KPJ|NOB|NOV|NOO|NOR|NOP|NOF|SKOJ|KNOJ|KNOU|AFŽ|USAOJ|SNOO|ZAVNOBIH|AVNOJ)\b)'
                   rf'[{U}][{U}Ä\d\-]*[{U}Äčćžšđ](?:,| +[{U}]?[{L}]|\s+[{U}Ä]{{2,}})')
# how he died; the year after it, past a day or a month ("poginuo februara 1943") or the place ("poginuo kod Starog
# Majdana 1941. godine"); the place after kod, na, u ("u NOB" is no place)
DEATH = re.compile(r'\b(?:pogi\w+|pognu\w+|umr\w+|ubijen\w*|strijelj\w+|streljan\w*|nesta\w+|zaklan\w*|stradal\w*)\b')
PLACE = re.compile(rf'\b(?:kod|na|u|iznad|pod)\s+(?!NOB\b|NOV\b)((?:[{U}][{L}]+(?:-[{U}][{L}]+)?\s?)+)')


# the duty at the list's end may be an army rank, or the labour battalion (which the user counts) or a battalion's
# workshop, none of which the mixed-list rule names
MILITARY = re.compile(r'\b(?:pot?poručnik|poručnik|kapetan|major|potpukovnik|pukovnik|zastavnik|podoficir|'
                      r'vodni\s+delegat|delegat\s+voda|vojn\w*\s+radn\w*\s+bataljon\w*|radn\w*\s+(?:vojn\w*\s+)?bataljon\w*|'
                      r'vojn\w*\s+radion\w*)\b', re.I)


def fighter(rec: dict) -> bool:
    return mosor.fighter_or_officer(rec) or (bool(MILITARY.search(rec['additional_info']))
                                             and not mosor.CHETNIK.search(rec['additional_info']))


def build_pdf() -> None:
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_796.pdf'), fitz.open()
        out.insert_pdf(src, from_page=FIRST - 1, to_page=LAST - 1)
        out.save(PDF, garbage=4, deflate=True)


def unspace(t: str) -> str:
    """"D E D O V A Č A" -> "DEDOVAČA", "N A P R E L JE" -> "NAPRELJE"; "LUŠCI PALANKA" stays"""
    words = t.split()
    return ''.join(words) if len(words) > 2 and all(len(w) <= 2 for w in words) else ' '.join(words)


def is_village(t: str) -> bool:
    return (bool(re.fullmatch(rf'[{U}Ä][{U}Ä\s.\-]+', t)) and 2 < len(t) < 45
            and not t.startswith(('ZA VJEČITU', 'BORCIMA', 'ŽRTVAMA')))


def read() -> list[dict]:
    entries, village, kind, title = [], '', '', ''
    with pdfplumber.open(PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            lines = [ln for ln in entry_boxes.read_page(page)['columns'][0] if ln['text'].strip()]
            body = [ln for ln in lines if not re.fullmatch(r'\d{1,3}', ln['text'].strip())]
            # the entries' margin: specks the OCR read at the page's edge ("t", "l") are no lines of text
            margin = min((ln['x0'] for ln in body if len(ln['text'].strip()) >= 20), default=0)
            ended = True                    # the line before closed an entry (";", "."), or a heading stood there
            for ln in body:
                t = re.sub(r'^[•·■*^]+\s*', '', ln['text'].strip())
                if is_village(t):
                    village, kind, ended = unspace(t), '', True
                    continue
                for pat, k, name in LISTS:
                    if pat.match(t):
                        kind, title, ended = k, name, True
                        break
                else:
                    was_ended, ended = ended, bool(re.search(r'[;.:]\s*$', t))
                    if not kind:
                        if START.match(t) and ',' in t:
                            print(f'  p{pno + FIRST - 1} under no list: {t!r}')
                        continue
                    # an entry starts at the margin, or (on a skewed scan, whose margin drifts) after one that closed
                    if START.match(t) and re.match(r'^[^,]{3,70},', t) and (ln['x0'] <= margin + 5 or was_ended):
                        entries.append({'kind': kind, 'list': title, 'village': village, 'lines': [t],
                                        'pdf_page': pno, 'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1)})
                    elif entries and entries[-1]['kind'] == kind and kind != 'victims':
                        entries[-1]['lines'].append(t)
                    elif kind != 'victims':
                        print(f'  p{pno + FIRST - 1} not read: {t!r}')
    return entries


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[\xad-]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('\xad-') + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text.replace('\xad', '')).strip().rstrip(';.').strip()


def village_name(v: str) -> str:
    return ' '.join(kl.title(w) if w.isupper() else w for w in v.replace('Ä', 'A').split())


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    head = re.split(r',\s*(?=ro[dđ]en\w*|r\.\s*1[89]|1[89]\d\d)', text, maxsplit=1)
    name, rest = (head[0], head[1]) if len(head) == 2 else (text.split(',')[0], ','.join(text.split(',')[1:]))
    name = name.replace('Ä', 'A')
    # a name in capitals with a lowercase caron ("BRAJIć") or digits the OCR read for letters ("B0DIR02A" = Bodiroža,
    # "M4JKIĆ" = Majkić)
    name = re.sub(rf'\b[{U}\d]*[{U}][{U}\d]*[čćžšđ]?\b', lambda m: m.group(0).upper().translate(str.maketrans('0124', 'OIŽA'))
                  if re.search(r'\d', m.group(0)) or m.group(0)[-1] in 'čćžšđ' else m.group(0), name)
    nick = ''
    m = re.search(r'\s+[—–-]\s+([{U}][{U}{L}]+)$'.replace('{U}', U).replace('{L}', L), name) or \
        re.search(r',?\s*»([^«]+)«,?', name)                                       # "MORICA Đuro, »Dalmatinac«"
    if m:
        nick, name = kl.title(m.group(1)), name[:m.start()] + name[m.end():]
    also = []
    maiden = re.search(rf',?\s*(?:r\.|rođ\.|rođena)\s+([{U}][{L}]+),?', name)       # "VRUĆINIĆ, r. Delić, SMILJA"
    if maiden:
        also, name = [maiden.group(1)], name[:maiden.start()] + ' ' + name[maiden.end():]
    words = [w.strip(',-') for w in name.split() if w.strip(',-')]
    # the surname first, in capitals or half ("ŠABIĆ-Mujadžič"); the father in small letters; the given name last,
    # in capitals, a nickname after a hyphen ("BOŠKO-Bođa")
    last = '-'.join(kl.spelled(p, 'last') if p.isupper() else p for p in words[0].split('-')) if words else ''
    others = words[1:]
    given = next((w for w in reversed(others) if w.split('-')[0].isupper() and len(w) > 1), '')
    if given and '-' in given and not given.split('-', 1)[1].isupper():
        given, nick = given.split('-', 1)[0], nick or given.split('-', 1)[1]
    first = kl.spelled(given, 'first') if given else (others[-1] if others else '')
    fathers = [w for w in others if not w.split('-')[0].isupper()]
    father = fathers[0].strip("'’") if fathers and (given or len(fathers) > 1) else ''
    # two surnames ("BABIĆ KOVAČEVIĆ Mile MILKA"): the capitals before the father; bits of three letters or fewer are a
    # surname the OCR broke ("BAS ARA" = Basara)
    before = [w for w in others[:others.index(fathers[0]) if fathers else 0] if w.isupper()]
    if before and all(len(w) <= 3 for w in before):
        last = kl.spelled(words[0] + ''.join(before), 'last')
    else:
        also = also + [kl.spelled(w, 'last') for w in before]
    by = re.search(r'ro[dđ]en\w*\s+(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[89]\d\d)|r\.\s*(1[89]\d\d)', rest or '')
    d = DEATH.search(rest or '')
    death_year, death_place = '', ''
    if d:
        after = rest[d.end():]
        y = re.search(r'\b(19[34]\d)\b', after[:90])
        p = PLACE.search(after[:120])
        death_year, death_place = (y.group(1) if y else ''), (p.group(1).strip() if p else '')
    village = village_name(e['village'])
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {first}'.strip(), 'last_name': last, 'also': also,
           'first_name': first, 'nick': nick, 'fathers_name': father,
           'birth_year': (by.group(1) or by.group(2)) if by else '',
           'born_in': village if village == 'Sanski Most' else f'{village}, Sanski Most',
           'death_year': death_year, 'death_place': death_place,
           'additional_info': f"{e['list']}, {village}: {text}", 'list': e['list'], 'kind': e['kind'],
           'pdf_file': PDF.name, 'pdf_page': e['pdf_page'], 'pdf_x': e['pdf_x'], 'pdf_y': e['pdf_y']}
    if e['kind'] == 'alive':
        rec['survived'] = True
    return rec


def main() -> None:
    build_pdf()
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    # the list of 15 May 1945 names the village's people in the movement: the fighters, and the activists, who go in
    # too, marked (the user's decision of 2026-10-19)
    for r in recs:
        if r['kind'] == 'alive' and not fighter(r):
            r['role'] = 'activist'
    kept = [r for r in recs if r['kind'] != 'alive' or fighter(r) or not mosor.CHETNIK.search(r['additional_info'])]
    print('activists:', sum(r.get('role') == 'activist' for r in kept))
    print(f'{len(recs)} entries, {len(kept)} kept -> {OUT.relative_to(HERE.parent)}')
    print(Counter(r['kind'] for r in recs), 'kept:', Counter(r['kind'] for r in kept))
    stats = entry_boxes.fill_boxes(kept)
    for r in kept:
        r.pop('kind')
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    print(f"villages: {len({r['born_in'] for r in kept})}; birth year: {sum(bool(r['birth_year']) for r in kept)}, "
          f"father: {sum(bool(r['fathers_name']) for r in kept)}, death year: {sum(bool(r['death_year']) for r in kept)}, "
          f"death place: {sum(bool(r['death_place']) for r in kept)}")
    if '--sample' in sys.argv:
        random.seed(6)
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['last_name']}|{r['fathers_name']}|{r['first_name']} {r['also']} {r['birth_year']} [{r['born_in']}] "
                  f"† {r['death_year']} {r['death_place']!r} | {r['additional_info'][:120]}")


if __name__ == '__main__':
    main()
