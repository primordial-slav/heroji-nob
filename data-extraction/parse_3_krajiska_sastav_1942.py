"""
Parser: 3. krajiška proleterska brigada (brigade code 10) — its roll of mid-November 1942, a fourth list.

Source: the brigade's zbornik sjećanja, knj. 1-2 (znaci.org 00001/31), the chapter "Sastav 3. krajiške proleterske
        brigade polovinom novembra 1942.", published by znaci.org only as a web page: https://znaci.org/00001/31_263.htm
        →  data-extraction/sources/3-krajiska-sastav-1942-31_263.htm (a saved copy, Word markup stripped). Every man
        and woman of the brigade staff, the Politodjel, the intendantura, the courier platoon and the four battalions'
        staffs, companies, escort and labour platoons, a paragraph each, surname in capitals, the father, the given
        name and what he was called, the duty, then the bio:
    KARANOVIĆ Milana Nikola komandant, rođen 1914, Prkosi, Bos. Petrovac, Srbin, podoficir BJV.
    STUPAR Marka David — Dako zamenik intendanta brigade, rođen 1912, ...
A paragraph that doesn't start with a name continues the one before (the page breaks some bios). Each record's text
starts with the section it stands under ("1. četa 1. bataljona: borac, rođen 1920, ..."). There is no scan: the
records carry `source_url` instead of a PDF position. The fallen are the unit's first list (IDs from 1), Borci
Sutjeske from 100001, the roll of knj. 3 from 200001; these get IDs from 300001.
"""
import html
import re
import sys
from pathlib import Path

from _parser_scaffold import _record, run_parser

SOURCE = 'data-extraction/sources/3-krajiska-sastav-1942-31_263.htm'
SOURCE_URL = 'https://znaci.org/00001/31_263.htm'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ORDINAL = {'PRVI': 1, 'DRUGI': 2, 'TREĆI': 3, 'TREĆl': 3, 'ČETVRTI': 4, 'PRVA': 1, 'DRUGA': 2, 'TREĆA': 3}
# sections of the brigade staff: the record's sub-unit and the words its text starts with
STAFF = {'ŠTAB BRIGADE': ('Štab brigade', 'Štab brigade'), 'POLITODJEL': ('Politodjel', 'Politodjel brigade'),
         'BRIGADNA INTENDANTURA': ('intendantura', 'Brigadna intendantura'),
         'ZAŠTITNI VOD (KURIRSKI)': ('zaštitni vod', 'Zaštitni vod (kurirski)')}
NAME_FIXES = {'PILIPIVIĆ': 'PILIPOVIĆ', 'Duro': 'Đuro'}


def sections_and_paragraphs(path: str) -> list[tuple[str, str, str]]:
    """(sub-unit, the words the text starts with, the paragraph), a paragraph a soldier."""
    paras = [html.unescape(re.sub(r'<[^>]+>', '', p)).strip()
             for p in re.findall(r'<p>(.*?)</p>', Path(path).read_text(encoding='utf-8'), re.S)]
    out, sub, lead, bat = [], '', '', 0
    for p in paras[1:]:                                                  # the first is the chapter's title
        if not re.search(rf'[{L}]{{2}}', p):                             # a heading in capitals
            p = p.replace('Š TAB', 'ŠTAB').replace('Č ETA', 'ČETA')
            if p in STAFF:
                sub, lead = STAFF[p]
            elif 'BATALJON' in p and 'ŠTAB' not in p:
                bat = ORDINAL[p.split()[0]]
                sub, lead = f'{bat}. bataljon', f'Štab {bat}. bataljona'
            elif p == 'ŠTAB BATALJONA':
                sub, lead = f'{bat}. bataljon', f'Štab {bat}. bataljona'
            elif p.endswith('ČETA'):
                c = ORDINAL[p.split()[0]]
                sub, lead = f'{c}. četa, {bat}. bataljon', f'{c}. četa {bat}. bataljona'
            elif p in ('PRATEĆI VOD', 'RADNI VOD'):
                v = p.split()[0].lower()
                sub, lead = f'{v} vod, {bat}. bataljon', f'{v[:1].upper()}{v[1:]} vod {bat}. bataljona'
            else:
                raise ValueError(f'heading {p!r}')
            continue
        starts = re.match(rf'^[{U}]{{2,}}', p) and p.split()[0] not in ('NOB', 'NOR', 'KPJ', 'SKOJ') or \
            re.match(rf'^[{U}][{L}]+ [{U}][{L}]+ [{U}][{L}]+ .*\brođen', p)          # "Radošević Vida Mihailo komandir"
        if starts:
            out.append([sub, lead, p])
        else:                                                           # "član KPJ od 1942, poginuo ..."
            out[-1][2] += ' ' + p
    return [tuple(x) for x in out]


def read_entries(path: str, start: int, end: int | None) -> list[dict]:
    return [{'text': f'§§n{i}', 'x': 0, 'y': float(i), 'page': 1} for i, _ in enumerate(ENTRIES)]   # not '§§123': a page number


def name_of(p: str) -> tuple[str, str, str, str, str]:
    """'STUPAR Marka David — Dako zamenik ...' -> surname, father, given name, what he was called, the rest."""
    words = p.split()
    words = [NAME_FIXES.get(w, w) for w in words]
    k = 0
    while k < len(words) and re.fullmatch(rf'[{U}][{U}-]+', words[k]):
        k += 1
    caps = words[:k] or words[:1]
    names = []
    if k == 2 and not re.fullmatch(rf'[{U}][{L}]+,?', words[k]):        # "TANKOSIĆ NIKOLA borac": the given in capitals
        caps, names = caps[:1], [caps[1].capitalize()]
    last = '-'.join(w.capitalize() for w in '-'.join(caps).split('-'))
    if not k:                                                            # "Radošević Vida Mihailo"
        k = 1
    other = ''
    if k < len(words) and re.fullmatch(rf'\([{U}]+\)', words[k]):        # "ATLAGIĆ (BULAJIĆ) Laze Pane"
        other = words[k].title()
        k += 1
    while k < len(words) and re.fullmatch(rf'[{U}][{L}]+(?:-[{U}][{L}]+)?,?', words[k]):
        names.append(words[k].rstrip(','))
        k += 1
        if words[k - 1].endswith(','):                                   # "BABIĆ Dušan, borac"
            if k + 1 < len(words) and re.fullmatch(rf'[{U}][{L}]+', words[k]) and words[k + 1][:1].islower():
                names.append(words[k])                                   # "Dušan, Pešo borac"
                k += 1
            break
    if k + 1 < len(words) and words[k] == '—' and re.fullmatch(rf'[{U}][{L}]+', words[k + 1]):
        names.append(words[k + 1])                                       # "David — Dako"
        k += 2
    rest = ' '.join(([other] if other else []) + words[k:]).lstrip(', ')
    if len(names) >= 3 and names[0][-1] in 'ćc':                        # "BOSNIĆ Pilipović Pere Bosa": a second surname
        last = f'{last}-{names.pop(0)}'
    nick = ''
    h = next((i for i, n in enumerate(names) if '-' in n), None)
    if h is not None:                                                    # "Bure Petar-Pepa", "Lazara Ilija-Ile"
        names[h], nick = names[h].split('-')
        names = names[:h + 1]
    father, given = ('', names[0]) if len(names) == 1 else (names[0], names[1])
    nick = nick or ' '.join(names[2:])
    return last, father, given, nick, rest


def parse(text: str) -> dict:
    sub, lead, p = ENTRIES[int(text[3:])]
    last, father, given, nick, rest = name_of(p)
    info = f"{lead}: {rest}"
    if nick:
        info = f'zvani {nick}; {info}'
    rec = _record(last, given, father, info)
    y = re.search(r'(?:rođen|roden|ređen|rađen|•ođen)a?[.,]?\s+(?:u\s+\S+\s+)?(1[89]\d\d)', rest)   # the page's slips
    rec['birth_year'] = y.group(1) if y else ''
    rec['unit_detail'] = sub
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        for k in ('pdf_page', 'pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = SOURCE_URL
    return soldiers


ENTRIES = sections_and_paragraphs(SOURCE)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run_parser(pdf_path=SOURCE, brigade_code=10,
               output_path=sys.argv[1] if len(sys.argv) > 1 else 'website/public/3-krajiska-proleterska-soldiers.json',
               start_page=1, end_page=1, script='latin', extract_fn=read_entries, entry_start_re=re.compile(r'^§§'),
               parse_entry_fn=parse, post_fn=post, id_start=300001, keep_other_sources=True,
               source_url_prefix=SOURCE_URL)
