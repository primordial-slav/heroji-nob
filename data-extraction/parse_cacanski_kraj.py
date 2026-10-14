"""
Čačanski kraj u NOB — pali borci i žrtve (grupa autora; znaci.org 00003/698) → website/public/pdfs/cacanski-kraj-pali.pdf:
a book across units, its fighters added to the records of the soldiers it describes (see scripts/match_references.py).

The book names the dead of the Čačak region, 1941-1945, by region (Dragačevci, Ljubićani, Takovci, Trnavci, Čačani:
the chapters 698_1-698_5, joined into one PDF, 313 pages) and village: the fallen fighters, and the civilians shot,
killed or dead in camps. Only the fighters are read: an entry that names a partisan unit or calls the man a "borac",
"borac NOVJ", a commander, commissar, courier or medic of one; never an entry of the Chetnik side ("borac Jeličkog
četničkog odreda"), nor a civilian victim, a "saradnik NOP-a" or an "odbornik NOO" without a fighter's word. The
book's "Narodni heroji pali u NOR-u", its documents and the "Poginuli posle 1948. godine" are not read.
Cyrillic, one column, each entry's first line indented (some 30pt right of the lines under it), the village headings
spaced out ("Б Е Л И  К А М Е Н"):
    ПАЈИЋ Живојина МИЛИСАВ, зидар, рођен 1906. у Вирову; борац Драгачевског батаљона; заробили га четници и предали
    Немцима, који су га стрељали код ВТЗ у Чачку 7. децембра 1941.
Surname, father (genitive), given name, a nickname after a dash, as in the Čačanski odred's list of its fallen (unit
126), whose battalions most of these men served in: the odred's battalions and the odred give the entry unit 126, the
2. proleterska 39.

Output: data-extraction/znaci/cacanski-kraj-pali-entries.json (IDs 9016xxxxxx, in the book's order; the 29 entries the
reader first left inside the one before, from 9016004600 on) with the fields
the matcher reads, the region and village, and the entry's place on the page and its box.

Usage: python data-extraction/parse_cacanski_kraj.py [--sample N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import entry_boxes  # noqa: E402
from _parser_scaffold import cyrillic_to_latin, extract_lines_single_column  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from parse_cacanski_odred import fix_digits  # noqa: E402

PDF = 'cacanski-kraj-pali.pdf'
PDF_PATH = HERE.parent / 'website' / 'public' / 'pdfs' / PDF
OUT = HERE / 'znaci' / 'cacanski-kraj-pali-entries.json'
PREFIX = '9016'
CHAPTERS = ['698_1.pdf', '698_2.pdf', '698_3.pdf', '698_4.pdf', '698_5.pdf']     # znaci.org/00003/...
REGIONS = ['Dragačevci', 'Ljubićani', 'Takovci', 'Trnavci', 'Čačani']
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
FIGHTER = re.compile(r'\bbor(?:ac|ca|kinja)\b|\bbolničar|\bkurir|\bkomandir|\bkomandant|\bkomesar|\bdesetar|\bvodnik|'
                     r'\bpartizan|\bNOVJ?\b|\bNOP odred|\bbrigad|\bbataljon', re.I)
CHETNIK = re.compile(r'četničk\w* (?:odred|brigad|korpus|bataljon|čet\w*|komand)|ravnogor|ljotićev|nedićev\w* (?:odred|straž)|'
                     r'srpsk\w* državn\w* straž|dobrovolj', re.I)
UNITS = [(re.compile(r'(?:Dragačevsk|Ljubićk|Takovsk|Trnavsk|Čačansk|Gradsk)\w* (?:NOP |partizansk\w* )?(?:bataljon|čet|odred)|'
                     r'Čačansk\w* (?:NOP |partizansk\w* )?odred'), 126),
         (re.compile(r'Drug\w* proletersk\w* brigad'), 39)]
# heads the scan garbled past the rules of tolerant(), read from the page images: the text layer's start -> as printed
# (parse_pozega_pali.py's too: its entries start the same way)
HEADS = {
    'PJGAZINIĆ Milutina MIHAIL0.': 'PLAZINIĆ Milutina MIHAILO,',
    'ĐUROVIĆ JBubomioa RADOMIr': 'ĐUROVIĆ Ljubomira RADOMIR,',
    'KOMaDINIĆ Radomira MANOLO': 'KOMADINIĆ Radomira MANOJLO',
    'RAŠzIĆ Milisava MILOVAN': 'RANJIĆ Milisava MILOVAN',
    'KA11LAREBIĆ Veselina VEJBKO': 'KAPLAREVIĆ Veselina VELJKO',
    'NENADIĆ Radovana Boško': 'NENADIĆ Radovana BOŠKO',                    # the given name printed in small letters
    'PL/Gj^OBI N Đor^a ŠLASTIMIR': 'PETROVIĆ Đorđa VLASTIMIR',
    # the book prints "НЕЛЕЉКОВИЋ", the Čačanski odred's list the same man as Nedeljković (0126000665)
    'NELELJKOVIĆ Vesel^n-, MILOMIR': 'NEDELJKOVIĆ Veselina MILOMIR',
    'BOJOBIĆ Radosava DESIMIJg1': 'BOJOVIĆ Radosava DESIMIR',
    'PAUNOVIĆ VuJice V&LIMIR': 'PAUNOVIĆ Vujice VELIMIR',
    'PAUpOVIĆ Milijana MILAN': 'PAUNOVIĆ Milijana MILAN',
    'PAUIO^>IĆ Miroslava MILAN': 'PAUNOVIĆ Miroslava MILAN',
    'GAVRILOT^IĆ Božilara RADISAV.': 'GAVRILOVIĆ Božidara RADISAV,',
    'BOGOSaVLJEBIĆ Miluna BOŠKO': 'BOGOSAVLJEVIĆ Miluna BOŠKO',
    'PANTELŠa Mihaila MILOJE': 'PANTELIĆ Mihaila MILOJE',
    'GLIŠOBIl Dragojla DRAGOJBUB': 'GLIŠOVIĆ Dragojla DRAGOLJUB',
    'MAJ^INKOVIĆ Dušana MIODRAG': 'MARINKOVIĆ Dušana MIODRAG',
    'ĐURĐEVIĆ Milenka OBRlD': 'ĐURĐEVIĆ Milenka OBRAD',
    'JEVl,jg’IČIĆ Živojina MILUN': 'JEVERIČIĆ Živojina MILUN',
    'JEjzTIĆ Mihaila PREDRAG': 'JEVTIĆ Mihaila PREDRAG',
    'JAKOVJJzE.vIĆ Radoja SVETOJŠK': 'JAKOVLJEVIĆ Radoja SVETOLIK',
    'MILOSlVLJE#I.ć. J^adiča MIODRAG': 'MILOSAVLJEVIĆ Radiča MIODRAG',
    'MAĆIĆ Milisava RlDENKO': 'MAĆIĆ Milisava RADENKO',
    'NIKOLIĆ Mihamla MILENK0': 'NIKOLIĆ Mihaila MILENKO',
    'PAR123ANOVIĆ Velizara RATKO': 'PAREZANOVIĆ Velizara RATKO',
    'BOŠj^sšmĆ Maksima VASILIJE': 'BOŠKOVIĆ Maksima VASILIJE',
    'JOVANOVIĆ. — CUKAVAC M. PANTEJŠJA': 'JOVANOVIĆ — CUKAVAC M. PANTELIJA',
    "KRUNIĆ Đorđa 'GIHOMIR": 'KRUNIĆ Đorđa TIHOMIR',
    'STRANJlNČEVIĆ Bojana DESIMIR': 'STRANJANČEVIĆ Bojana DESIMIR',
    'COGOJBEVIĆ Nedeljka DgAGIŠl.': 'COGOLJEVIĆ Nedeljka DRAGIŠA',
    'ĐOKOVIĆ I. DRlGOSLAV': 'ĐOKOVIĆ I. DRAGOSLAV',
    'STANiŠIĆ Nasilija MILOŠ': 'STANIŠIĆ Vasilija MILOŠ',
    # the entries the reader first left inside the one before (`late`), some the scan garbled past a start's look
    'KaiLAREVIĆ Svetozara MLADEN': 'KAPLAREVIĆ Svetozara MLADEN',
    'Ka PLAREVIĆ Stevana MILAN': 'KAPLAREVIĆ Stevana MILAN',
    'MilOVANOVIĆ Tadije MILIBOJE': 'MILOVANOVIĆ Tadije MILIVOJE',
    "S (JKI 'ć Čedomira D^INKA": 'SOKIĆ Čedomira DRINKA',
    'iETROBIĆ Gojka MILENIJA': 'PETROVIĆ Gojka MILENIJA',
    "1'ODOROVIĆ Vladimira DOBRIVOJE": 'TODOROVIĆ Vladimira DOBRIVOJE',
    '(^ap d p Ć AndriJe JE^EMIJA': 'SANDIĆ Andrije JEREMIJA',
    'Uj^OŠEVIĆ Miljka SIMEUN': 'UROŠEVIĆ Miljka SIMEUN',
    'T011ALOVIĆ. Branislava BOGDAN': 'TOPALOVIĆ Branislava BOGDAN',
    'V^.SKOVIĆ Milana NOVAK': 'VESKOVIĆ Milana NOVAK',
    'B^a LOVIĆ Vladislava PETAR': 'ĐRALOVIĆ Vladislava PETAR',
    'tttgtcgić Milisava OLGA': 'CENDIĆ Milisava OLGA',
    'CoKOjzIĆ Anđelka DOBROSAV — DŽOKOVAC': 'COKOVIĆ Anđelka DOBROSAV — COKOVAC',
}


def join_chapters() -> None:
    """The five chapters as one PDF (the site's), once"""
    if PDF_PATH.exists():
        return
    out = fitz.open()
    for ch in CHAPTERS:
        out.insert_pdf(fitz.open(HERE / '.cache' / 'cacanski_kraj' / ch))
    out.save(PDF_PATH, garbage=3, deflate=True)


def chapter_starts() -> list[int]:
    """Each chapter's first page in the joined PDF (its region's title page), so the chapters needn't be cached"""
    return [1, 61, 144, 232, 277]


def read() -> list[dict]:
    lines = extract_lines_single_column(str(PDF_PATH), 1, None)
    starts = chapter_starts()
    left: dict = {}
    for ln in lines:
        ln['text'] = fix_digits(cyrillic_to_latin(ln['text'].strip()))
        if re.search(rf'[{L}]', ln['text']):                           # the text's margin: where the lines under it start
            left[ln['page']] = min(left.get(ln['page'], 10 ** 6), ln['x'])
    entries, village = [], ''
    for ln in lines:
        t, page = ln['text'], ln['page']
        region = REGIONS[max(i for i, s in enumerate(starts) if s <= page)]
        if re.fullmatch(r'[\d\W]{1,5}', t):
            continue                                                   # the page number
        if not re.search(rf'[{L}\d,;]', t):
            # a village (or region) heading, its letters spaced out ("B E L I K A M E N": the word gap is lost)
            village = re.sub(r'\s+', '', t) if re.fullmatch(rf'(?:[{U}]\s+)+[{U}]', t) else t
            continue
        indent = ln['x'] > left.get(page, 0) + 15
        lead = re.sub(r"^[\s'’,.\-–—]+", '', t)
        if indent and re.match(rf'^{CAPS}', t):
            entries.append({'lines': [t], 'pdf_page': page, 'pdf_x': ln['x'], 'pdf_y': ln['y'], 'region': region,
                            'village': village})
        elif indent and entries and (bool(lead) and is_caps(lead.split()[0]) and ',' in t[:60]
                                     or any(t.startswith(p) for p in HEADS)):
            # a surname the scan garbled or set a speck before ("CoKOjzIĆ Anđelka DOBROSAV", "1'ODOROVIĆ", "' MEČANIN",
            # "(^ap d p Ć AndriJe" for САНДИЋ Андрије): the reader once left the entry inside the one before, so it
            # is numbered after the book's last (`late`) and the others keep theirs
            entries.append({'lines': [t], 'pdf_page': page, 'pdf_x': ln['x'], 'pdf_y': ln['y'], 'region': region,
                            'village': village, 'late': True})
        elif entries:
            entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln
        else:
            text += ' ' + ln
    return re.sub(r'\s+', ' ', text).strip()


def village_name(spaced: str) -> str:
    return ' '.join(w[:1] + w[1:].lower() for w in spaced.split())


def is_caps(w: str) -> bool:
    """A word in capitals as the scan gives it: most of its letters capitals ("DRaGIŠa", "alEKSANDAR", "MIHAIL0")"""
    letters = [c for c in w if c.isalpha()]
    return len(letters) >= 2 and sum(c.isupper() for c in letters) >= .6 * len(letters)


def is_father(w: str) -> bool:
    """The father's name in small letters ("Svetislava", "Vesel^n-", "JBubomioa") or his initial ("M.")"""
    return bool(re.match(rf'[{U}]', w)) and (not is_caps(w) or bool(re.fullmatch(rf'[{U}]\.', w)))


def name_word(w: str) -> str:
    """A name in capitals as written on the site, the scan's specks and stray letters' case left out ("MIHAIL0." = Mihailo)"""
    w = re.sub(r'(?<=\w)0|0(?=\w)', 'O', w)
    w = re.sub(rf'[^{U}{L}\-]', '', w.upper()).strip('-')
    return '-'.join(p[:1] + p[1:].lower() for p in w.split('-') if p)


def tolerant(text: str) -> tuple[list[str], str, list[str], list[str], str]:
    """A head the strict reading left without a surname or given name, read word by word with the scan's noise: a
    word mostly in capitals is a name, a full stop or comma inside the head is the scan's ("ŽUNIĆ. DRAgOMIR",
    "ILIĆ Vasilija ,ĐORĐE"), the trade may follow without a comma ("RADOMIr zemljoradnik"); a dash after the first
    surname and before a second one with the father or given name after it joins two surnames ("BOJOVIĆ — TRNINIĆ
    Matije ĐURĐE — ĐUKA": "VUJIČIĆ — NEDIĆ MILOJKA", as the Čačanski odred's list writes them), one after the given name
    starts the nickname. Returns surnames, father, given names, nickname and the text after the name"""
    text = re.sub(rf'(?<=[{U}0])\.(?=[{L}])', '. ', text)                    # "JEZDIMIR.zemljoradnik"
    text = re.sub(r"^[\s'’,.\-–—]+", '', text)                                 # a speck before the surname ("- ALEKSIĆ")
    toks = [(m.group().strip(".'’`"), m.end()) for m in re.finditer(r'—|[^\s,;—]+', text)]
    toks = [(t, end) for t, end in toks if t]
    i, end, n = 0, 0, len(toks)
    tok = lambda k: toks[k][0] if k < n else ''

    def take(k: int) -> str:
        nonlocal i, end
        i, end = k + 1, toks[k][1]
        return toks[k][0]
    last, other, father, given, nick = [], [], '', [], []
    while is_caps(tok(i)):
        last.append(take(i))
    if tok(i) == '—' and is_caps(tok(i + 1)) and (is_father(tok(i + 2)) or is_caps(tok(i + 2))):
        other, last = last, [take(i + 1)]
    if is_father(tok(i)):
        father = take(i)
    if is_caps(tok(i)):
        given.append(take(i))
    if given and tok(i) == '—' and is_caps(tok(i + 1)):
        nick.append(take(i + 1))
        if nick[-1].endswith('-') and tok(i):                                 # "TROS- KO", the line's break
            nick[-1] = nick[-1][:-1] + take(i)
    if not given and not father and len(last) > 1:                             # "COKIĆ MIHAJL0": no father
        given = [last.pop()]
    if not given and not father and not other and len(last) == 1 and not re.search(r'IĆ$', last[0].upper()):
        given, last = last, []                                                 # "DRAGUTIN, potkivač": the given name alone
    return other + last if other else last, father, given, nick, text[end:].lstrip(' ,;.:')


def name_of(text: str) -> tuple[str, str, str, str, str]:
    """The head (surname, father, given name, a nickname after a dash) and the text after it: the strict reading of
    the list's heads, else (or for a head read from the page image) tolerant()'s"""
    read = next((HEADS[p] + text[len(p):] for p in HEADS if text.startswith(p)), None)
    head, _, info = text.partition(',')
    parts = [p.split() for p in re.split(r'\s+[—–-]\s+', head)]
    words = [w.strip('.') for w in parts[0]]
    nick = ' '.join(w for p in parts[1:] for w in p).title()
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = words.pop(0) if words and re.fullmatch(rf'[{U}][{L}]+', words[0]) else ''
    given = [w for w in words if re.fullmatch(CAPS, w)]
    if not given and len(last) > 1:
        given = [last.pop()]
    if len(given) > 1 and not nick:
        given, nick = given[:1], ' '.join(given[1:]).title()
    last_name = ' '.join(w[:1] + w[1:].lower() for w in last)
    first_name = ' '.join(w[:1] + w[1:].lower() for w in given)
    if read or not (last_name and first_name):
        surnames, fathers, given, nicks, rest = tolerant(read or text)
        if given or surnames:
            words = [name_word(w) for w in surnames]
            # two surnames joined as in the Čačanski odred's list ("Bojović-Trninić"), a name the scan split kept apart
            last_name = '-'.join(words) if len(words) > 1 and all(len(w) > 3 for w in words) else ' '.join(words)
            first_name = ' '.join(name_word(w) for w in given)
            father = f'{fathers}.' if len(fathers) == 1 else name_word(fathers)        # "M." keeps its full stop
            nick = ' '.join(name_word(w) for w in nicks)
            info = rest
    return last_name, father, first_name, nick, info


def parse(e: dict, n: int) -> dict:
    text = join(e['lines'])
    last_name, father, first_name, nick, info = name_of(text)
    info = re.sub(r'\bro[đćdcnN]e{1,2}n(a?)\b', r'rođen\1', info.strip())    # "roćen", "roden", "rođeen"
    info = re.sub(r'\bbo[oa]ac\b', 'borac', info)                         # "booac"
    rec = {'soldier_id': f'{PREFIX}{n:06d}',
           'name': ' '.join(x for x in (last_name, father, first_name) if x) + (f' — {nick}' if nick else ''),
           'last_name': last_name, 'first_name': first_name, 'nick': nick, 'fathers_name': father}
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?\s*)?u\s+([{U}][{L}]+(?:\s+[{U}]?[{L}]+){{0,2}})', info)
    rec['born_in'] = b.group(1) if b else (village_name(e['village']) if len(e['village']) >= 4 else '')
    years = re.findall(r'\b(19[34]\d)\b', info[b.end() if b else 0:])
    rec['death_year'] = years[-1] if years else ''
    when = re.search(rf'\b\d{{1,2}}\.\s*(?:[{L}]+|\d{{1,2}}\.)\s*19[34]\d', info)
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for rx, code in UNITS if rx.search(info)})
    rec['region'], rec['village'] = e['region'], village_name(e['village'])
    rec['additional_info'] = info
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=round(e['pdf_x'], 1), pdf_y=round(e['pdf_y'], 1))
    return rec


def fighter(rec: dict) -> bool:
    info = rec['additional_info']
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info)


def main():
    join_chapters()
    raw = read()
    ordered = [e for e in raw if not e.get('late')] + [e for e in raw if e.get('late')]
    recs = sorted((parse(e, i) for i, e in enumerate(ordered, 1)), key=lambda r: r['soldier_id'])
    kept = [r for r in recs if fighter(r)]
    stats = entry_boxes.fill_boxes(kept)
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    by = {}
    for r in kept:
        by[r['region']] = by.get(r['region'], 0) + 1
    print(f'{len(recs)} entries read, {len(kept)} fighters -> {OUT.relative_to(HERE.parent)}; {by}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    if '--sample' in sys.argv:
        random.seed(2)
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | {r['units']}")
            print(f"      {r['additional_info'][:150]}")
        print('-- left out:')
        for r in random.sample([r for r in recs if not fighter(r)], 6):
            print(f"  {r['name']!r}: {r['additional_info'][:140]}")


if __name__ == '__main__':
    main()
