"""
Kotar Gospić i kotar Perušić u narodnooslobodilačkom ratu 1941-1945. (Zbornik Historijskog arhiva u Karlovcu, knj. 20;
znaci.org 00003/642, the lists' chapter 642_2.pdf by Zdenka Krivokuća) → website/public/pdfs/hak-20-gospic-perusic.pdf:
a book across units, its entries added to the records of the soldiers it describes (see scripts/match_references.py).

The site's PDF holds two of the chapter's four lists, by općina and village under centred headings:
    PDF pp. 1-60 (book pp. 986-1045), "Pali borci s područja kotara Gospić i kotara Perušić 1941-1945.", two columns
    of numbered bios: "3. KRAJNOVIĆ Tome DUŠAN, 1917, kožarski radnik, Srbin. Stupio u NOB 1941, borac PO Divoselo.
    ... Ubili ga četnici kao borca 6. div. kod Gračaca 18. 12. 1942.";
    PDF pp. 61-76 (book pp. 1194-1209), "Nosioci partizanske spomenice 1941. godine", one line each: "1. BAKIĆ Maksima
    MILE, 1923, seljak, Srbin." (the living and the dead).
The other two, the victims of fascist terror and of the war (civilians) and those who died of typhus, stay out.
In the right column the entry's number stands in the gutter, left of the text; a woman may carry two surnames, the
married one first ("HRŽENJAK KRAJNOVIĆ Ilije JANJA"), and the matcher tries both.

Output: data-extraction/znaci/hak-20-gospic-perusic-entries.json (IDs 9007xxxxxx, in the book's order), with the fields
the matcher reads (last_name, also: the other surname, first_name, nick, fathers_name in the genitive as printed,
birth_year, born_in: the village heading and its općina, death_year and death_date for the fallen), the list, and the
entry's place on the page and its box. The entry's text starts with the village (and, for the spomenica, the list's
title, which gives the record the medal).

Usage: python data-extraction/parse_hak_20_gospic_perusic.py [--sample N]
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
import parse_ofanziva_1942 as ofz  # noqa: E402
from extract_life_events import iso, parse_when  # noqa: E402

PDF = 'hak-20-gospic-perusic.pdf'
OUT = HERE / 'znaci' / 'hak-20-gospic-perusic-entries.json'
PREFIX = '9007'
FALLEN, SPOMENICA = range(1, 61), range(61, 77)          # the PDF's pages of each list
LISTS = {'fallen': 'Pali borci', 'spomenica': 'Nosioci partizanske spomenice 1941. godine'}
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# an entry's number ("63" may have lost its period) before the surname; in the spomenica list the surname may be
# printed in small letters ("5. Graovac Tanasije JANJA")
START = re.compile(rf'^(\d{{1,3}})\s?(?:[.,]\s*|\s+)(?=[{U}]{{3}})')
START_LINE = re.compile(rf'^(\d{{1,3}})\s?[.,]\s*(?=[{U}])')
NATION = re.compile(r'(?:Srbin|Srpkinja|Hrvat|Hrvatica|Musliman|Muslimanka|Slovenac|Slovenka|Crnogorac|Jevrej|Rus|Talijan)\b')
# a start whose number the OCR lost: SURNAME Father GIVEN
NAME = re.compile(rf'^[{U}]{{3,}}(?:\s+[{U}]{{3,}})?\s+(?:[{U}][{L}]+|[{U}]\.)\s+[{U}]{{3,}}\b')
# how a fallen fighter's entry tells his death ("Ubile ga ustaše", "ranjena ... i umrla"): the first such word, and the
# first year after it
DEATH = re.compile(r'\b(?:pogin\w*|poeinu\w*|po\W?\s?g[mi]nu\w*|ubil\w*|ubijen\w*|ubi[oj]|[sš]tr[ie]*jelja\w*|zaklal\w*|'
                   r'zaklan\w*|umr\w*|nesta[lo]\w*|objesil\w*|obješen\w*|spalil\w*|uhvatil\w*|zarobil\w*|podleg\w*|'
                   r'izgubi\w*|likvidir\w*|smrz\w*)\b', re.I)


def title(word: str) -> str:
    return '-'.join(p[:1] + p[1:].lower() for p in word.split('-'))


def place(heading: str) -> str:
    """"LIČKI OSIK" -> "Lički Osik", "PAVLOVAC—VREBAC—ZAVODE" -> "Pavlovac—Vrebac—Zavode"."""
    return re.sub(rf'[{U}]+', lambda m: title(m.group(0)), heading)


def spelled(word: str, part: str) -> str:
    """A name in the site's spelling where the OCR lost a caron ("BAKIC" = Bakić, "DURO" = Đuro); see
    parse_ofanziva_1942.known. Other slips are left as printed."""
    if ofz._spell[part].get(word.upper().translate(ofz.FOLD), {}).get(word.upper(), 0) >= 2:
        return title(word)
    n, best = ofz.known(word, part)
    return title(best) if n >= 3 else title(word)


def read() -> list[dict]:
    """The entries of both lists in the book's order: their lines, page, start and the headings over them."""
    entries, opcina, village = [], '', ''
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            two = pno in FALLEN
            data = entry_boxes.read_page(page, columns=2 if two else 1, numbers_in_gutter=True,
                                         gutter=entry_boxes.GUTTER.get((PDF, pno)))
            if pno == SPOMENICA[0]:
                opcina = village = ''
            for col in data['columns']:
                lines = [dict(ln) for ln in col]
                # an entry's number hangs left of its text, where the lines run on: a line that starts with a number
                # there ("1. LPO »Velebit«", "2. bat.") runs on; in the spomenica list most lines are entries
                xs = sorted(ln['x0'] for ln in lines)
                text_x = xs[len(xs) // 2] if xs else 0
                # a number the right column sets in the gutter, a little higher or lower than its line
                merged = []
                for ln in lines:
                    if merged and re.fullmatch(r'\d{1,3}\s?[.,]', merged[-1]['text']) and abs(ln['top'] - merged[-1]['top']) < 6:
                        merged[-1] = dict(ln, text=merged[-1]['text'] + ' ' + ln['text'], x0=merged[-1]['x0'],
                                          top=min(ln['top'], merged[-1]['top']))
                    else:
                        merged.append(ln)
                for ln in merged:
                    t = ln['text'].replace('­', '-').strip()
                    if ln['top'] > data['height'] - 40 and re.fullmatch(r'\d{3,4}', t):
                        continue                                           # the page number
                    if re.match(r'^(?:Pali borci|kotara|Gospić i|Nosioci partizanske)', t) and not opcina:
                        continue                                           # a list's title
                    m = re.fullmatch(rf'OPĆINA\s+([{U} -]+)', t)
                    if m:
                        opcina, village = place(m.group(1)), ''
                        continue
                    if re.fullmatch(rf'[{U}][{U} .—–-]+', t) and not START.match(t) and len(t) < 40:
                        village = place(t)                                 # "ČITLUK", "PAVLOVAC—VREBAC—ZAVODE"
                        continue
                    if not opcina:
                        continue
                    hanging = ln['x0'] < text_x - 5 if two else ln['x0'] < text_x + 5
                    m = (START if two else START_LINE).match(t) if hanging else None
                    lost = not m and NAME.match(t) and entries and entries[-1]['list'] == ('fallen' if two else 'spomenica')
                    if m or lost:
                        no = int(m.group(1)) if m else entries[-1]['no'] + 1
                        entries.append({'no': no, 'lines': [t[m.end():] if m else t], 'pdf_page': pno,
                                        'pdf_x': round(ln['x0'], 1), 'pdf_y': round(ln['top'], 1),
                                        'list': 'fallen' if two else 'spomenica', 'opcina': opcina, 'village': village})
                    elif entries and entries[-1]['pdf_page'] in (pno, pno - 1) and entries[-1]['list'] == ('fallen' if two else 'spomenica'):
                        entries[-1]['lines'].append(t)
    return entries


def join(lines: list[str]) -> str:
    text = lines[0]
    for ln in lines[1:]:
        if re.search(rf'[{L}{U}]-$', text) and re.match(rf'[{L}]', ln):
            text = text[:-1] + ln                                          # "se-" / "ljak"
        elif re.search(rf'(?:^|\s)[{U}-]*[{U}]-$', text) and re.match(rf'[{U}]{{2,}}\b', ln):
            text = text[:-1] + ln                                          # a name: "VLADI-" / "MIR,", "PO-" / "BRO,"
        else:
            text += ' ' + ln
    return re.sub(r'\s+', ' ', text).strip()


def split_name(head: str) -> tuple[list[str], str, str, str]:
    """"KRAJNOVIĆ Jovana MILE" -> (surnames, father, given, nick); the father may be an initial ("T.") or missing.
    A married woman's maiden name follows "r." ("RAŠETA r. PLEĆAŠ Laze SARA"); it is left out of the surnames here
    and shown in the name."""
    head = re.sub(r'\s*[—–]\s*', ' — ', head.strip().rstrip('.'))
    nick = ''
    if ' — ' in head:                                                     # "DUŠAN — MILOŠ", "IVAN — VANJA"
        head, nick = head.split(' — ', 1)
    words = [w for w in head.split() if w not in ('r.', 'rođ.')]
    caps = lambda w: w.replace('-', '').isupper() and len(w.rstrip('.')) > 1
    i = 0
    while i < len(words) and caps(words[i]):
        i += 1
    if i == len(words):                                                    # "ČUBRIĆ BOJA": no father
        return words[:-1] or words, '', (words[-1] if len(words) > 1 else ''), nick
    surnames, rest = words[:i] or words[:1], words[i:] if i else words[1:]
    if not rest:
        return surnames, '', '', nick
    if len(rest) == 1:                                                     # "PLAVŠIĆ Mile": the given name in small letters
        return surnames, '', rest[0], nick
    father, given = rest[0], ' '.join(rest[1:])
    return surnames, father, given, nick


# the OCR's slips in this book: accents it put on letters, j read as ".T", i as "1", 1943 as "i 943"
OCR = str.maketrans('äàáâöòóüùúèéÄÀÁÖÜÈÉ', 'aaaaooouuueeAAAOUEE')
# heads the reader can't take apart: what the page prints, as the name is read
HEADS = {'ČANAK Jovana STEVAN STEVI-': 'ČANAK Jovana STEVAN', 'RADAKOVIĆ Janka MILICA MI KA': 'RADAKOVIĆ Janka MILICA — MIKA'}


def parse(e: dict, n: int) -> dict:
    text = join(e['lines']).translate(OCR)
    text = re.sub(rf'(?<=[{U}])\.T(?=[{U}])', 'J', text)                     # "BAN.TEGLAV"
    text = re.sub(rf'(?<=[{U}{L}])1(?=[{U}{L}])', 'i', text)                  # "TODOR1Ć"
    text = re.sub(r'(?<![\w.])[iIlÌÍ] ?(9[34]\d)\b', r'1\1', text)            # "augusta i 943", "6. 12. Ì944"
    text = re.sub(r'^([^,]*?[a-zčćžšđA-ZČĆŽŠĐ])\.\s+(?=1[89]\d\d)', r'\1, ', text)   # "Nikola. 1918"
    head, info = (re.split(r',\s*', text, 1) + [''])[:2]
    y0 = re.search(r'[\s.,]+(1[89]\d\d)\b[.,]?\s*', head)
    if y0:                                                                  # "MARKO 1922 seljak."
        head, info = head[:y0.start()], f'{y0.group(1)}, ' + head[y0.end():] + (', ' + info if info else '')
    head = HEADS.get(head, head)
    trade = re.search(r'\s([a-zčćžšđ]{4,})$', head)
    if trade:                                                               # "DANICA seljanka, Srpkinja"
        head, info = head[:trade.start()], f'{trade.group(1)}, {info}'
    # a nickname after the given name, before the year: "JOSO, Brico, 1912", "MILAN, MIĆA, 1924"
    alias = re.match(r'^([^,\d]{2,25}),\s*(?=1[89]\d\d)', info)
    surnames, father, given, nick = split_name(head)
    if alias and not nick:
        nick, info = alias.group(1).replace('- ', '').strip(), info[alias.end():]
    if '-' in given and all(len(p) > 2 for p in given.split('-')):        # "IVAN-Ćujo", "PETAR-PEKISA"
        given, nick = given.split('-', 1)[0], nick or given.split('-', 1)[1]
    if len(given.split()) == 2 and not nick:                               # "MILAN MIĆO": the second is what he was called
        given, nick = given.split()
    surnames = [spelled(w, 'last') for w in surnames]
    last = surnames[-1]
    first = ' '.join(spelled(w, 'first') for w in given.split())
    shown = (' r. ' if re.search(r'\sr\.\s', head) else ' ').join(surnames)
    name = ' '.join([shown] + ([father] if father else []) + ([first] if first else []))
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': name + (f' — {title(nick)}' if nick else ''),
           'last_name': last, 'also': surnames[:-1], 'first_name': first, 'nick': title(nick),
           'fathers_name': father}                       # an initial too ("B."): the matcher compares it
    y = re.match(r'(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    where = f"{e['village']}, općina {e['opcina']}" if e['village'] and e['village'] != e['opcina'] else f"općina {e['opcina']}"
    # a village the entry names after the year ("1921, Pavlovac, seljak") is his own, under a heading of several
    # ("PAVLOVAC—VREBAC—ZAVODE") or none
    segs = [x.strip() for x in info.split(',')]
    own = segs[1] if y and len(segs) > 2 and re.match(rf'[{U}][{L}]', segs[1]) and not NATION.match(segs[1]) else ''
    village = own or e['village']
    rec['born_in'] = f"{village}, {e['opcina']}" if village else e['opcina']
    if e['list'] == 'fallen':
        d = DEATH.search(info)
        years = re.findall(r'\b(19[34]\d)\b', info[d.start():]) if d else []
        rec['death_year'] = years[0] if years else ''
        when = re.search(r'\b\d{1,2}\.\s?\d{1,2}\.\s?19[34]\d', info[d.start():]) if d else None
        parsed = parse_when(when.group(0)) if when else None
        rec['death_date'] = iso(parsed[0]) if parsed and parsed[0][2] else ''
        rec['additional_info'] = f'{where}: {info}'
    else:
        rec['death_year'] = rec['death_date'] = ''
        rec['additional_info'] = f"{LISTS['spomenica']}, {where}: {info}"
    rec['list'] = LISTS[e['list']]
    rec['no'] = e['no']
    rec.update(pdf_file=PDF, pdf_page=e['pdf_page'], pdf_x=e['pdf_x'], pdf_y=e['pdf_y'])
    return rec


def main():
    ofz.corpus()
    raw = read()
    recs = [parse(e, i) for i, e in enumerate(raw, 1)]
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; {dict(Counter(r["list"] for r in recs))}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")
    # the numbers run 1, 2, 3 ... under each village: a gap is an entry the reader missed
    gaps, prev = [], None
    for r, e in zip(recs, raw):
        key = (e['list'], e['opcina'], e['village'])
        if prev and prev[0] == key and r['no'] != prev[1] + 1:
            gaps.append(f"{e['village']} {prev[1]}->{r['no']} (p{r['pdf_page']})")
        prev = (key, r['no'])
    print(f'number gaps: {len(gaps)}', gaps[:30])
    print(f"no birth year: {sum(not r['birth_year'] for r in recs)}, no father: {sum(not r['fathers_name'] for r in recs)}, "
          f"no given name: {sum(not r['first_name'] for r in recs)}, fallen without a death year: "
          f"{sum(not r['death_year'] for r in recs if r['list'] == LISTS['fallen'])}")
    if '--sample' in sys.argv:
        random.seed(3)
        for r in random.sample(recs, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['death_date']} | p{r['pdf_page']}")
            print(f"      {r['additional_info'][:150]}")


if __name__ == '__main__':
    main()
