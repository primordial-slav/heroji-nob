"""
*Spomen-knjiga poginulih tuzlanskih boraca NOR-a i žrtava fašističkog terora 1941-1945.* (Tuzla; znaci.org 00001/144)
→ website/public/pdfs/tuzla-spomen-knjiga.pdf: a book across units (see scripts/match_references.py).

The site's PDF holds the whole book's PDF pp. 8-292, "Poginuli borci NOR-a" (book pp. 13-300): a biography of each
participant of the war from the municipality of Tuzla who fell (born, lived or worked there, or joined the army from
there), one column, often beside a photograph, under a heading in a bold sans-serif (Impact in the text layer):
    "AHMETOVIĆ, MUJO (Ahmet)" / "Rođen je 1914. godine u selu Gornje Petrovice kod Tuzle. ... stupi u redove XVIII
    hrvatske brigade. Poginuo je 27. februara 1945. godine u selu Šepak kod Bijeljine, ..."
Surname, given name (a second one is what he was called: "MAHMUT MAŠO"), and the parents in brackets, the father first
("(Avdo i Fatima)"). The book's second part, the victims of fascist terror (pp. 301-372), stays out.

The text layer sets a page's headings after its text at times, so lines are read by their place on the page. The OCR
read the photographs as specks ("^ ^ j d t t p ^ H"): words over an image are dropped. A heading's comma may be a full
stop and its surname broken apart ("AMID OVI Ć. ŠAĆIR"); a heading's Ć may be G ("ALIO, GAZIM" over "Ćazim je ...")
and is read back from the bio, which names him. Each entry gives the brigades the site has as `units` (XXI tuzlanska =
32, XVIII hrvatska = 52, ...), its box (one rectangle around its lines on its first page; the PDF is in
entry_boxes.INLINE_ENTRIES, since the photographs leave gaps entry_boxes would stop at) and the day he fell.

Output: data-extraction/znaci/tuzla-spomen-knjiga-entries.json, IDs 9032xxxxxx.
Usage: python data-extraction/parse_tuzla_spomen_knjiga.py [--sample N]
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
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402
from pdf_coords import viewer_offset  # noqa: E402

PDF = 'tuzla-spomen-knjiga.pdf'
OUT = HERE / 'znaci' / 'tuzla-spomen-knjiga-entries.json'
PREFIX = '9032'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the brigades and detachments the bios name that are units of the site
UNITS = [
    (r'\b(?:XXI|21\.)\s*tuzlansk', 32), (r'\b(?:XVIII|18\.)\s*(?:hrvatsk|istočnobos)', 52),
    (r'\b(?:XIX|19\.)\s*birčansk', 23), (r'\b(?:VI|6\.)\s*istočnobosansk', 42), (r'\b(?:XV|15\.)\s*majevičk', 49),
    (r'\b(?:XVII|17\.)\s*majevičk', 29), (r'\bTuzlansk\w*\s+(?:NOP\s+|partizansk\w*\s+)?odred', 25),
    (r'\bPosavsko-trebavsk\w*\s+(?:NOP\s+|partizansk\w*\s+)?odred', 59), (r'\b(?:XIV|14\.)\s*srednjobosansk', 56),
    (r'\b(?:II|2\.)\s*krajišk', 24), (r'\b(?:III|3\.)\s*krajišk', 10), (r'\b(?:VII|7\.)\s*krajišk', 48),
    (r'\b(?:I|1\.)\s*krajišk', 123),
]
# a heading as the text layer has it -> as it is read: the OCR's slips in the headings' letters (O for D, G or d for Ć,
# 6 for B or G, 0 for O), read from the bio that names him ("Hamdija", "Vehid", "Radojka") or from another unit's
# record of him (Bjegović Nikola of Divoselo, Tuzlanski odred); znaci re-typeset the book from its OCR, so the page shows
# the same slips
HEADS = {
    'BEKRIĆ, MMĐIJA (Alija)': 'BEKRIĆ, HAMDIJA (Alija)', 'BJEMVHJ, NIKOLA': 'BJEGOVIĆ, NIKOLA',
    'BLA68JEVIĆ, DANILO (Simo)': 'BLAGOJEVIĆ, DANILO (Simo)', 'HAOŽIĆ, AHMET (Hasan i Fatima)': 'HADŽIĆ, AHMET (Hasan i Fatima)',
    'HADŽIAVDIĆ, A6DURAHMAN (Mahmut i Zumra)': 'HADŽIAVDIĆ, ABDURAHMAN (Mahmut i Zumra)',
    'MUJBEGOVld, dr. MUSTAFA (Abas)': 'MUJBEGOVIĆ, dr. MUSTAFA (Abas)',
    'OMEREFENOIĆ, HARIZ (Osman i Razija)': 'OMEREFENDIĆ, HARIZ (Osman i Razija)', 'VOOENIK, KARLO (Ivan)': 'VODENIK, KARLO (Ivan)',
    'BEKTIĆ, NIDŽAOA (Mustafa i Rasema)': 'BEKTIĆ, NIDŽADA (Mustafa i Rasema)',
    'LAUFER, FRIOA (Jozef i Lotika)': 'LAUFER, FRIDA (Jozef i Lotika)', 'PERIĆ, RAOQJKA (Vid i Jaglika)': 'PERIĆ, RADOJKA (Vid i Jaglika)',
    'KAVGIĆ, VAHIO (Ibrahim i Aza)': 'KAVGIĆ, VEHID (Ibrahim i Aza)', 'KONKID, DŽEMAL (Nazif i Ajka)': 'KONKIĆ, DŽEMAL (Nazif i Ajka)',
    'KANTIG, CAZIM (Osman)': 'KANTIĆ, ĆAZIM (Osman)', 'TERZIG, IBRAHIM (Mujo i Sija)': 'TERZIĆ, IBRAHIM (Mujo i Sija)',
    'DDAAUTOVIC, IBRAHIM (Avdo i Hana)': 'DAUTOVIĆ, IBRAHIM (Avdo i Hana)',
    'KUM PL, RIFKA (Haim)': 'KLIMPL, RIFKA (Haim)', 'SAOIKOVIĆ, MUHAMED ŠKHAB': 'SADIKOVIĆ, MUHAMED',
    'PAVLOVIĆ, NENAD NEMO (Dušan i Danica)': 'PAVLOVIĆ, NENAD NENO (Dušan i Danica)',      # "Neno je učestvovao ..."
    'JOVANOVIĆ, T000R TOŠO (Jovan)': 'JOVANOVIĆ, TODOR TOŠO (Jovan)', 'PANTIĆ, 00RĐE (Vladimir i Pavlija)': 'PANTIĆ, ĐORĐE (Vladimir i Pavlija)',
    'S EJ RA f\\IIĆ, MEHMED MEHO (Džafer)': 'SEJRANIĆ, MEHMED MEHO (Džafer)',
    'GRADAŠČEVIĆ, A6AZ (Hasan)': 'GRADAŠČEVIĆ, ABAZ (Hasan)',
    'HERLJEVIĆ, ZVONIMR ZVONKO (Franjo i Lucija)': 'HERLJEVIĆ, ZVONIMIR ZVONKO (Franjo i Lucija)',
}


def _key(head: str) -> str:
    return re.sub(r'\s+', '', head)


HEADS_KEYED = {_key(k): v for k, v in HEADS.items()}         # the text layer's spacing varies ("DDA AUTOVIC")
# a heading the text layer lost: (the entry's heading begins, a line begins) -> the heading of the entry that line starts
# (Abdurahman Saračević's bio ends "Kao učesnik NOB-a poginuo je i njegov stariji brat Husein.")
LOST = {('SARAČEVIĆ, ABDURAHMAN', 'Rođen je 1915. godine u Gornjoj Tuzli'): 'SARAČEVIĆ, HUSEIN'}
HEAD = re.compile(rf'^[{U}0-9][{U}0-9 \-]{{2,}}[,.]\s*(?:dr\.\s*)?[{U}(]')
HEAD_LINE = re.compile(rf'^[{U}][{U} \-]{{2,}},\s+[{U}][{U} ]+(?:\s*\([^)]*\))?$')     # one in the body's font
DEATH = re.compile(r'\b(?:poginu[oa]|nesta[oa]|nestala|ubijen[a]?|umr(?:o|la)|strijeljan[a]?|obješen[a]?|podlega?o|'
                   r'podlegla|zaklan[a]?|ubil[ei]|strijeljal[ei]|objesil[ei]|izgubi[oa]\s+je\s+život)\b', re.I)


def read() -> list[dict]:
    """The entries in the book's order: heading, lines, page and place."""
    entries = []
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            dx, dy = viewer_offset(page)
            images = [(i['x0'], i['top'], i['x1'], i['bottom']) for i in page.images
                      if (i['x1'] - i['x0']) < page.width * 0.8]          # a photograph, not the page's scan
            words = [w for w in page.extract_words(extra_attrs=['fontname'], keep_blank_chars=False)
                     if not any(a <= (w['x0'] + w['x1']) / 2 <= c and b <= (w['top'] + w['bottom']) / 2 <= d
                                for a, b, c, d in images)]
            lines = []
            for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
                head = 'Times' not in w['fontname']                         # Impact; one heading in Arial
                if lines and abs(w['top'] - lines[-1]['top']) < 4 and lines[-1]['head'] == head:
                    ln = lines[-1]
                    ln['words'].append(w)
                    ln['x1'], ln['bottom'] = max(ln['x1'], w['x1']), max(ln['bottom'], w['bottom'])
                else:
                    lines.append({'words': [w], 'top': w['top'], 'x0': w['x0'], 'x1': w['x1'], 'bottom': w['bottom'],
                                  'head': head, 'bold': 'Bold' in w['fontname']})
            for ln in lines:
                ln['words'].sort(key=lambda w: w['x0'])
                ln['text'] = ' '.join(w['text'] for w in ln['words']).strip()
                ln['x0'] = min(w['x0'] for w in ln['words'])
            for ln in sorted(lines, key=lambda l: l['top']):
                t = ln['text']
                if ln['bold'] and re.fullmatch(r'\d{1,3}', t) or re.fullmatch(r'[\W\d_]{1,4}', t):
                    continue                                                 # the page number, a speck
                if sum(c.isalpha() for c in t) < 0.5 * len(t.replace(' ', '')):
                    continue                                                 # a photograph's specks
                box = (ln['x0'] - dx, ln['top'] - dy, ln['x1'] - dx, ln['bottom'] - dy)
                lost = next((h for (a, b), h in LOST.items()
                             if entries and entries[-1]['head'].startswith(a) and t.startswith(b)), None)
                if lost:
                    entries.append({'head': lost, 'lines': [t], 'pdf_page': pno, 'pdf_x': round(box[0], 1),
                                    'pdf_y': round(box[1], 1), 'box': list(box)})
                    continue
                if ln['head']:
                    t = re.sub(r'\^+\S*\s*', '', t).translate(str.maketrans('öÖ', 'ćĆ')).strip()   # "^ ^ ^^ KARABEGOVIĆ"
                    before = re.match(r'^([^,.()]{2,40})[,.]', t)
                    if not (before and sum(c.isupper() for c in before.group(1)) >= 3) and _key(t) not in HEADS_KEYED and entries:
                        ln['head'] = False                                   # "Da": a word of the text in Impact
                if not ln['head'] and HEAD_LINE.match(t) and re.search(r'\(|^[^,]+,\s*\S+\s+\S+$|^[^,]+,\s*\S+$', t):
                    ln['head'] = True                                        # "KUM PL, RIFKA (Haim)", glued on
                if ln['head']:
                    t = HEADS_KEYED.get(_key(t), t)
                    if entries and entries[-1]['lines'] == [] and entries[-1]['pdf_page'] == pno:
                        entries[-1]['head'] += ' ' + t                       # a heading on two lines
                        continue
                    entries.append({'head': t, 'lines': [], 'pdf_page': pno, 'pdf_x': round(box[0], 1),
                                    'pdf_y': round(box[1], 1), 'box': list(box)})
                elif entries:
                    entries[-1]['lines'].append(t)
                    if entries[-1]['pdf_page'] == pno:
                        b = entries[-1]['box']
                        entries[-1]['box'] = [min(b[0], box[0]), b[1], max(b[2], box[2]), max(b[3], box[3])]
    return entries


def bio_text(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if text.endswith('-') and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln                                           # "orga-" / "nizacije"
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def split_head(head: str) -> tuple[str, str, str, str]:
    """"AHMETOVIĆ, MUJO (Ahmet)" -> surname, given, nickname, father; "AMID OVI Ć. ŠAĆIR" -> Amidović, Šaćir."""
    head = re.sub(r'\s+', ' ', head.translate(str.maketrans('öÖ', 'ćĆ'))).strip()
    m = re.search(r'\(([^)]*)\)?', head)                       # at the end, or before the given name: "BAREŠA, (Anto) RUŽICA"
    parents = m.group(1) if m else ''
    name = (head[:m.start()] + ' ' + head[m.end():]).strip() if m else head
    parts = re.split(r'\s*[,.]\s*', name, maxsplit=1)
    # l for I in capitals ("Ml LAN OVI Ć" = MILANOVIĆ), a small letter among them ("HADŽiOSMANOVIĆ"), 0 for O
    caps = lambda w: (w.replace('l', 'I') if sum(c.isupper() for c in w) >= 2 else w).upper().replace('0', 'O')
    last = caps(re.sub(r'\s*-\s*', '-', parts[0]).replace(' ', ''))
    given = [caps(w) for w in (re.sub(r'\s*-\s*', '-', parts[1]).split() if len(parts) > 1 else [])
             if not re.fullmatch(r'(?i)dr\.?|ing\.?', w)]
    # a name the OCR broke apart ("FAD IL", "TAD I JA", "M E H M E D", "HI KMETA"): a piece of one or two letters
    # belongs to its neighbour, as does a piece the corpus doesn't know as a name when the whole is one ("FEH RAT")
    i = 0
    while i < len(given) - 1:
        a, b = given[i], given[i + 1]
        if len(a) <= 2 or len(b) <= 2 or len(a) + len(b) <= 6 or (ofz.known(a + b, 'first')[0] >= 3 and ofz.known(b, 'first')[0] < 3
                                           and ofz.known(a, 'first')[0] < 3):
            given[i:i + 2] = [a + b]
        else:
            i += 1
    father = re.split(r'\s+i\s+', parents)[0].strip() if parents else ''
    return last, given[0] if given else '', ' '.join(given[1:]), father


def title(word: str) -> str:
    return '-'.join(p[:1].upper() + p[1:].lower() for p in word.split('-'))


def from_bio(given: str, bio: str) -> str:
    """The given name as the bio writes it, where the heading's OCR read a letter wrong ("GAZIM" over "Ćazim je")."""
    g = given.lower()
    if not g or re.search(rf'\b{re.escape(title(given))}\b', bio) or ofz.known(given.upper(), 'first')[0] >= 1:
        return title(given)                                     # a name as printed ("Vera", not the bio's "Veru")
    near = Counter(w for w in re.findall(rf'\b[{U}][{L}]+\b', bio)
                   if len(w) == len(g) and sum(a != b for a, b in zip(w.lower(), g)) == 1)
    return near.most_common(1)[0][0] if near else title(given)


def parse(e: dict, n: int) -> dict:
    last, given, nick, father = split_head(e['head'])
    bio = bio_text(e['lines'])
    last = '-'.join(kl.spelled(p, 'last') for p in last.upper().split('-') if p)      # "Peleš-Petaković"
    first = from_bio(given, bio)
    if first == title(given):
        first = kl.spelled(given.upper(), 'first') if given else ''
    father = title(father) if father else ''
    nick = title(nick) if nick else ''
    parents = re.search(r'\(([^)]*)\)?\s*$', re.sub(r'\s+', ' ', e['head']))
    parents = ' i '.join(title(p.strip()) for p in re.split(r'\s+i\s+', parents.group(1))) if parents else ''
    rec = {'soldier_id': f'{PREFIX}{n:06d}',              # as printed: "Ajdaslić, Mujo (Avdo i Fatima)"
           'name': f'{last}, ' + ' '.join(x for x in (first, nick) if x) + (f' ({parents})' if parents else ''),
           'last_name': last, 'also': [], 'first_name': first, 'nick': nick, 'fathers_name': father}
    # "Rođen je 1914. godine u selu ...", "Rođenje 24. marta 1921. godine u Brezi", "Rođen je u martu 1923. godine",
    # "Rođen je u Dobrnji kod Tuzle.", "Salih je stariji Džemilin brat, rođen 1922. godine u Tuzli"
    born = re.search(r'\bro[đd]en\w*\s*(?:je\s*)?(?:u\s+(?:januar|februar|mart|april|maj|jun|jul|avgust|august|septemb'
                     r'r|oktobr|novembr|decembr)u\s+)?(?:\d{1,2}\.\s*[a-zčćžšđ]+\s+)?'
                     r'(?:(1[89]\d\d)\.?\s*(?:godine\s*)?)?(.*?)(?:\.\s|$)', bio, re.I)
    rec['birth_year'] = (born.group(1) or '') if born else ''
    place = ''
    if born and born.group(2) and re.match(r'(?:u\s|selu\s)', born.group(2).strip()):
        p = re.sub(r'^(?:u\s+)?(?:selu|naselju|mjestu|zaseoku)\s+|^u\s+', '', born.group(2).strip())
        p = re.split(r',\s*(?:Republika|opština|općina)|,', p)[0].strip()
        p = re.sub(r'\s+(?:kod|blizu)\s+Tuzle$|\s+u\s+Tuzli$', ', Tuzla', p)
        place = re.sub(r'\bTuzli\b', 'Tuzla', p)
        if not re.match(rf'[{U}]', place) or len(place) > 60:
            place = ''
    rec['born_in'] = place
    # his own death closes the bio ("... poginuo je Salih Vugić.", "četnici su je ubili 23. septembra 1944."): the last
    # such word, the year after it, else the last year before it
    deaths = list(DEATH.finditer(bio))
    after = bio[deaths[-1].start():] if deaths else ''
    y = re.search(r'\b(19[34]\d)\b', after[:150])
    before = re.findall(r'\b(19[34]\d)\b', bio[max(0, deaths[-1].start() - 200):deaths[-1].start()]) if deaths else []
    rec['death_year'] = y.group(1) if y else (before[-1] if before else '')
    when = re.search(rf'\b\d{{1,2}}\.\s*(?:[{L}]+|\d{{1,2}}\.)\s*19[34]\d', after[:120])
    parsed = parse_when(when.group(0)) if when else None
    rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
    rec['units'] = sorted({code for pat, code in UNITS if re.search(pat, bio, re.I)})
    rec['additional_info'] = bio
    rec['list'] = 'Poginuli borci NOR-a'
    b = e['box']
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'],
               pdf_x_end=round(b[2], 1), pdf_y_end=round(b[3], 1))
    if b[0] < e['pdf_x'] - 1:
        rec['pdf_x_left'] = round(b[0], 1)
    return rec


def main() -> None:
    ofz.corpus()
    raw = read()
    unused = [k for k, v in HEADS.items() if not any(e['head'] == v for e in raw)]
    if unused:
        print('HEADS not found:', unused)
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}')
    print(f"no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
          f"no given name: {sum(not r['first_name'] for r in recs)}, no death year: {sum(not r['death_year'] for r in recs)}, "
          f"no birthplace: {sum(not r['born_in'] for r in recs)}, with a unit: {sum(bool(r['units']) for r in recs)}")
    print('units', Counter(u for r in recs for u in r['units']))
    # bios that hold a second "Rođen" sentence: a heading the text layer lost, two men in one entry
    two = [r for r in recs if len(re.findall(r'\bRo[đd]en\w*\s*(?:je\s*)?(?:\d{1,2}\.\s*\w+\s*)?1[89]\d\d', r['additional_info'])) > 1]
    print(f'entries with two births: {len(two)}', [(r['soldier_id'], r['name'], r['pdf_page']) for r in two[:30]])
    if '--sample' in sys.argv:
        random.seed(5)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} {r['units']} | p{r['pdf_page']}")
            print(f"      {r['additional_info'][:160]}")


if __name__ == '__main__':
    main()
