"""
Reference book: Narodni heroji Jugoslavije (Beograd, 1982, second edition, two volumes: A-M, N-Ž), in the Digital
library of Poreklo (biblioteka.poreklo.rs, collection of biographies; for members only).

Like the Zbornik narodnih heroja (1957, parse_zbornik_heroja.py) it portrays heroes of units all over the site, so its
entries are references added to the hero's record (`reference` corrections, scripts/match_references.py), not records of
their own. Each biography opens with a heading in bold capitals and runs on in three columns:

    ABRLIĆ Jurja STJEPAN — STEVA
    Rođen je 10. travnja 1913. godine u Drežniku, Slunj, Karlovac, Hrvatska. Po zanimanju bio je kamenorezac. ...
    ... Narodnim herojem proglašen je 9. listopada 1953. godine. (I. G.)

The OCR garbles the bold headings ("Авг/ЈА Ритам водили" for ADŽIJA Damasa BOŽIDAR) and the book's contents alike, so the
headings are found here by their place on the page (a short line with a wide gap above and a narrower one below, the
biography indented under it) and their names were read from the page images, cut out by the OCR boxes; they are kept in
data-extraction/poreklo/narodni-heroji-1982-headings.json by volume, page and the OCR's text of the heading. The entry
kept is the birth sentence and the day proclaimed, read back from the OCR (commas it read as full stops, look-alike
letters in the months); the biography itself stays in the book, a click away in the library's viewer. Cities, units and
the foreign holders of the order are left out. The full OCR is cached in data-extraction/.cache/poreklo/
narodni-heroji-1982-a-m.json and -n-z.json (not in git).

Usage: python data-extraction/parse_narodni_heroji_1982.py
"""
import difflib
import json
import re
import sys
from pathlib import Path

from poreklo_text import page_lines, printed_page, viewer_url

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache' / 'poreklo'
HEADINGS = HERE / 'poreklo' / 'narodni-heroji-1982-headings.json'
OUT = HERE / 'poreklo' / 'narodni-heroji-1982-entries.json'
VOLUMES = (('a', 'narodni-heroji-1982-a-m', range(20, 601)), ('n', 'narodni-heroji-1982-n-z', range(19, 471)))
PREFIX = '9002'                                   # reference IDs: 9002 + the hero's number in the book's order
MONTHS = ['januara', 'februara', 'marta', 'aprila', 'maja', 'juna', 'jula', 'avgusta', 'augusta', 'septembra', 'oktobra',
          'novembra', 'decembra', 'siječnja', 'veljače', 'ožujka', 'travnja', 'svibnja', 'lipnja', 'srpnja', 'kolovoza',
          'rujna', 'listopada', 'studenog', 'studenoga', 'prosinca', 'januarja', 'februarja', 'aprila', 'junija', 'julija']
PLACE_END = re.compile(r'\b(?:Hrvatska|Srbija|Bosna i Hercegovina|Crna Gora|Makedonija|Slovenija|Vojvodina|Kosovo|'
                       r'Italija|Austrija|Mađarska|Albanija|Grčka|Bugarska|Rumunija|Francuska|Egipat|SAD)\b\)?\.?')


def heading_blocks(book: dict, page: int) -> list[dict]:
    """The page's headings: one or two short lines with a gap of at least ~95 OCR units above them (or the column's top),
    a gap of 50-170 below, and the biography's first line indented under them"""
    found = []
    for c, col in enumerate(page_lines(book, page, 3)):
        for i in range(len(col) - 1):
            if not 50 <= col[i + 1].top - col[i].bottom <= 160:
                continue
            j = i
            while j > 0 and col[j].top - col[j - 1].bottom < 40 and i - j < 2 and len(col[j - 1].text) < 45:
                j -= 1
            before = col[j].top - col[j - 1].bottom if j else 999
            text = ' '.join(line.text for line in col[j:i + 1])
            indent = col[i + 1].x0 - min(line.x0 for line in col[j:i + 1])
            if before < 95 or len(text) > 90 or len(re.sub(r'\W', '', text)) < 5:
                continue
            if not (35 <= indent <= 130 or re.match(r'\W{0,3}[RHFBN][o0e][dđ]', col[i + 1].text)):
                continue
            found.append({'col': c, 'top': col[j].top, 'bottom': col[i].bottom, 'head': text})
    return found


def biographies(book: dict, pages) -> list[dict]:
    """Every heading with the text under it, in reading order (column by column), to the next heading"""
    out, cur = [], None
    for page in pages:
        if str(page) not in book['pages']:
            continue
        heads = {(h['col'], round(h['top'])): h for h in heading_blocks(book, page)}
        for c, col in enumerate(page_lines(book, page, 3)):
            skip = None
            for line in col:
                if skip is not None and line.top <= skip:
                    continue
                h = heads.get((c, round(line.top)))
                if h:
                    cur = {'page': page, 'head': h['head'], 'lines': []}
                    out.append(cur)
                    skip = h['bottom']
                elif cur:
                    cur['lines'].append(line.text)
    for b in out:
        text = ' '.join(b.pop('lines'))
        text = re.sub(r'(?<=[a-zčćžšđ])[-—–~·]\s+(?=[a-zčćžšđ])', '', text)       # "poče- kom"
        b['text'] = re.sub(r'\s+', ' ', text).strip()
    return out


def month(word: str) -> str:
    w = word.lower().replace('rr', 'm').replace('rn', 'm').replace('n\'', 'm')
    best = difflib.get_close_matches(w, MONTHS, n=1, cutoff=0.6)
    return best[0] if best else word


def clean(text: str) -> str:
    """Look-alike Cyrillic letters, "и" for u, "1" or "l" for I in years"""
    text = text.translate(str.maketrans({'и': 'u', 'у': 'y', 'о': 'o', 'а': 'a', 'е': 'e', 'с': 'c', 'р': 'p', 'ј': 'j',
                                         'к': 'k', 'н': 'n', 'м': 'm', 'т': 't', 'в': 'v'}))
    return re.sub(r'\s+', ' ', text).strip()


def date_text(m) -> str:
    day, mon, year = m.group('d'), m.group('m'), m.group('y')
    return ' '.join(x for x in ((day + '.') if day else '', month(mon) if mon else '', year + '.') if x)


DATE = r'(?:(?P<d>\d{1,2})\s*[.,]\s*)?(?:(?P<m>[a-zA-Zčćžšđ\'"]{3,12})\s+)?(?P<y>1[89]\d\d)'


def birth(text: str) -> tuple[str, str, str]:
    """The birth sentence as printed, its year and place: "Rođen je 10. travnja 1913. godine u Drežniku, Slunj, Karlovac,
    Hrvatska." The OCR reads the commas as full stops and the first word in many ways ("Hoderi", "Floden", "Rođenje")"""
    head = clean(text[:700])
    m = re.match(r'^\W{0,3}(?P<w>[A-ZŠŽČĆĐ][\w]{2,7}(?:\s?je)?)\s+(?:je\s+|ie\s+)?(?=[\d(]|u\s|na\s|1\s)', head)
    start = 0
    female = False
    if m and re.search(r'[odenrh]', m.group('w').lower()):
        female = bool(re.match(r'\W*\w+a\b', head)) and not m.group('w').lower().startswith('rođenje')
        start = m.end()
    else:
        alt = re.search(r'\b(?:ro[dđ]en|rodio se|rodila se)(a?)\s+(?:je\s+)?', head, re.I)
        if not alt or alt.start() > 400:
            return '', '', ''
        female = alt.group(1) == 'a' or 'rodila' in alt.group(0).lower()
        start = alt.end()
    rest = head[start:]
    end = PLACE_END.search(rest)
    if end and end.end() < 220:
        clause = rest[:end.end()]
    else:
        stop = re.search(r'\.\s+(?=[A-ZŠŽČĆĐ][a-zšžčćđ]+\s+[a-zšžčćđ])', rest[8:])
        clause = rest[:8 + stop.start() + 1] if stop and stop.start() < 200 else rest[:160].rsplit(' ', 1)[0]
    clause = clause.rstrip(' .,') + '.'
    dm = re.search(DATE, clause)
    year = dm.group('y') if dm else ''
    if dm:
        clause = clause[:dm.start()] + date_text(dm) + clause[dm.end():].lstrip('.')
    # the place: after "godine u"/"u"; full stops between its parts were commas
    pm = re.search(r'\b(?:u|na|kod)\s+(?P<p>.+)$', clause[dm.end() if dm else 0:] if dm else clause)
    place = ''
    if pm:
        place = pm.group('p').rstrip('.')
        fixed = re.sub(r'\.\s+', ', ', place)
        clause = clause.replace(place, fixed)
        place = fixed
    sentence = ('Rođena je ' if female else 'Rođen je ') + clause.strip()
    sentence = re.sub(r'\s+,', ',', sentence).replace('..', '.')
    sentence = re.sub(r'(\d{4})\.,? (?=u |na |kod )', r'\1. ', sentence).replace('godine. u ', 'godine u ')
    sentence = sentence.replace('crna Gora', 'Crna Gora')
    return sentence, year, place


def proclaimed(text: str, female: bool) -> str:
    """"Narodnim herojem proglašen je 9. listopada 1953. godine." from the last proclamation in the biography; the OCR
    breaks the month at the line's end ("27. no verrbra", "20. de- oerrbra") and garbles the verb ("proglćen", "progISen")"""
    tail = clean(text[-700:])
    at = [m.end() for m in re.finditer(r'\b(?:herojem|heroja|her\w{2}em|pro[gq]\S{2,8})', tail)]
    if not at:
        return ''
    m = re.search(r'(\d{1,2})\s*[.,]\s*(\D{2,24}?)\s*(1[89]\d\d)\b', tail[at[-1] if len(at) == 1 else at[-2]:])
    if not m:
        m = re.search(r'(\d{1,2})\s*[.,]\s*(\D{2,24}?)\s*(1[89]\d\d)\b', tail[at[-1]:])
    if not m:
        return ''
    letters = re.sub(r'[^a-zA-Zčćžšđ]', '', m.group(2)).lower().replace('rr', 'm').replace('rn', 'm')
    mon = difflib.get_close_matches(letters, MONTHS, n=1, cutoff=0.5)
    if not mon:
        return ''
    return f'Narodnim herojem proglašen{"a" if female else ""} je {m.group(1)}. {mon[0]} {m.group(3)}. godine.'


DEATH = re.compile(r'\b(?:[Pp]oginu[oa]|[Pp]ogibe|[Ss]treljan[a]?|[Oo]bešen[a]?|[Uu]bijen[a]?|[Ss]mrtno\s+(?:je\s+)?ranjen[a]?|'
                   r'[Pp]odlegao|[Pp]odlegla|[Ii]zdahnu[oa]|[Pp]ala\s+je|[Pp]ao\s+je|[Zz]aklan[a]?|umro\s+od\s+rana|'
                   r'ubijen[a]?|[Uu]bili\s+su)\b')
SURVIVED = re.compile(r'\b(?:Posle|Poslije|Nakon|Po)\s+oslobo[dđ]enja|\bNosilac\s+(?:je\s+)?Partizanske|\bUmro\s+je\s+(?:19[5-9]\d|\d)', re.I)


def fate(text: str) -> tuple[str, bool]:
    """The year he fell (the first death word followed within 200 characters by a war year), and whether the book follows
    his life after the war"""
    t = clean(text)
    for m in DEATH.finditer(t):
        y = re.search(r'\b(194[1-5])\b', t[m.start():m.start() + 200])
        if y:
            return y.group(1), False
    return '', bool(SURVIVED.search(t))


def title(word: str) -> str:
    return '-'.join(p[:1] + p[1:].lower() for p in word.split('-')) if word else ''


def main():
    names = json.loads(HEADINGS.read_text(encoding='utf-8'))
    by_key = {(n['vol'], n['page'], n['ocr']): n for n in names}
    entries, unknown, used = [], [], set()
    for vol, name, pages in VOLUMES:
        book = json.loads((CACHE / f'{name}.json').read_text(encoding='utf-8'))
        for b in biographies(book, pages):
            n = by_key.get((vol, b['page'], b['head']))
            if not n:
                unknown.append((vol, b['page'], b['head']))
                continue
            used.add((vol, b['page'], b['head']))
            sentence, year, place = birth(b['text'])
            death_year, survived = fate(b['text'])
            last, given = title(n['last']), title(n['given'])
            nick = ', '.join(title(x.strip()) if x.strip().isupper() else x.strip() for x in re.split(r',', n['nick'])) if n['nick'] else ''
            nick = ' '.join(title(w) if w.isupper() else w for w in nick.split(' '))
            parts = [p for p in (sentence, proclaimed(b['text'], sentence.startswith('Rođena'))) if p]
            entries.append({
                'soldier_id': f'{PREFIX}{len(entries) + 1:06d}',
                'name': ' '.join(x for x in (last, n['father'], given) if x) + (f' ({nick})' if nick else ''),
                'last_name': last, 'fathers_name': n['father'], 'first_name': given, 'nick': nick,
                'birth_year': year, 'born_in': place, 'death_year': death_year, 'survived': survived,
                'additional_info': ' … '.join(parts), 'source_url': viewer_url(book, b['page']),
                'source_page': printed_page(book, b['page']),
            })
    missing = [k for k in by_key if k not in used]
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(entries)} heroes; {sum(1 for e in entries if not e["birth_year"])} without a birth year, '
          f'{sum(1 for e in entries if "proglašen" not in e["additional_info"])} without the day proclaimed; '
          f'names not found in the scan table: {len(unknown)}, table names not found on the page: {missing[:5]}')


if __name__ == '__main__':
    main()
