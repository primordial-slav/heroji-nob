"""
Parser: 19. srpska NOU brigada (brigade code 73).

Source: Predrag Pejčić, "Devetnaesta srpska brigada" (znaci.org 00001/87_12.pdf, book pp. 411-614)
        →  website/public/pdfs/19-srpska.pdf:
    pp. 1-61    "Poginuli, nestali i umrli", by unit: A) iz prištapskih jedinica, B) iz 1. bataljona ... E) iz 4.
                bataljona, F) lica sa nepotpunim identitetom
    pp. 62-200  "Preživeli rat"
    pp. 201-202 the staffs of the brigade and its battalions (not read: names only, in prose)
Cyrillic, one column, a hanging indent; surname, the father's initial, the given name, then the bio:
    Андрејић П. Станко, рођен 1914. у Буровцу код Петровца на Млави, борац коморе 19. српске бригаде, нестао ...
The text layer reads Д and Л at the start of a word as А ("Арагољуб" = Драгољуб, "Аукијановић" = Лукијановић),
ђ as ћ ("роћен", "Анћелко"), and З as 3 ("Бојић 3. Милија"); names are read back where the other units know
the repaired spelling far better, words in the bios where this book itself prints them so.
"""
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_TO = 61
OWN = '19-srpska-soldiers.json'
_starts: dict = {}
_footnote: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append(ln['x'])


def margin(page: int) -> float:
    """The leftmost x that three lines of the page share (a stray mark further left doesn't count)."""
    xs = sorted(_starts.get(page, []))
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 3:
            return x
    return xs[0] if xs else 0


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.match(r'^\d[0-9%]{1,2}\s*[)>]\s', t):                              # "497> Spisak ...", "4%) Spisak ...": a footnote
        _footnote[ln['page']] = ln['y']
    if ln['page'] in _footnote and ln['y'] >= _footnote[ln['page']] - 1:
        return False
    letters = [c for c in t if c.isalpha()]
    if not re.search(rf'[{L}]{{3}}', t) and re.search(r'\d{3}|^\W', t) or len(letters) < 3:
        return False                                                         # "411", "S 440", "B . • , . •"
    if len(t) > 6 and sum(c.isupper() for c in letters) > 0.7 * len(letters):
        return False                                                         # "B) IZ 1. BATALJONA", "PREŽIVELI RAT"
    if ln['page'] == 1 and ln['y'] < 100:
        return False                                                         # the heading and Tito's words
    if ln['x'] <= margin(ln['page']) + 6 and re.match(rf'^[{U}][{L}]', t):
        t = ('§p§ ' if ln['page'] <= FALLEN_TO else '§s§ ') + t
    ln['text'] = t
    return True


NAME = re.compile(rf'^([{U}][{L}]+(?:-[{U}][{L}]+)?)\s+(?:((?:Lj|Nj|Dž|[{U}]))\.\s*)?([{U}][{L}]+)\s*(?:\(([^)]*)\))?')


def parse(text: str) -> dict:
    text = re.sub(r'^§[ps]§\s*', '', text)
    text = re.sub(r'\b3\.(?=\s+[A-ZČĆŽŠĐ])', 'Z.', text)                      # "Bojić 3. Milija"
    text = text.replace('l>', 'lj').replace('L>', 'Lj')                       # Љ read as Л>: "Dobrosavl>ević", "L>. Svetislav"
    text = re.sub(r'^(\S+\s+)(?:A>|\])\.?', lambda m: m.group(1) + ('Lj.' if '>' in m.group(0) else 'J.'), text)   # "A>.", "]."
    text = re.sub(r'^(\S+\s+)([0t])\.', lambda m: m.group(1) + m.group(2).upper().replace('0', 'O') + '.', text)   # "0.", "t."
    text = re.sub(r'^(\S+\s+)([XY])\.', lambda m: m.group(1) + {'X': 'H', 'Y': 'U'}[m.group(2)] + '.', text)   # Х, У as Latin look-alikes
    text = re.sub(r'^(\S+\s+)([A-ZČĆŽŠĐ])•?(?=\s+[A-ZČĆŽŠĐ][a-zčćžšđ])', r'\1\2.', text)   # "Kurić D Vasa", "A• Vladimir"
    text = re.sub(r'\bdp\s+med\.', 'dr med.', text)                                     # "др мед." read as dp
    text = re.sub(r'^(\S+)\s+-\s+(?=[A-ZČĆŽŠĐ])', r'\1-', text)                        # "Gajić - Milosavljević"
    text = re.sub(r'(?<=[a-zčćžš])([ĐĆČŠŽ])', lambda m: m.group(1).lower(), text)          # "BorĐević"
    pre = []
    m = re.match(r'^(\S+)\s+(dr(?: med)?\.)\s+', text)                                  # "Marinković dr med. Miodrag"
    if m:
        pre, text = [m.group(2)], m.group(1) + ' ' + text[m.end():]
    text = re.sub(rf'^(\S+\s+[{U}]),\s', r'\1. ', text)                       # "Nikolić M, Pavle"
    text = re.sub(r'\b([Rr])oćen(a?)\b', r'\1ođen\2', text)
    text = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', text)              # a word broken at the line's end
    m = NAME.match(text)
    if not m:
        head, _, rest = text.partition(',')
        toks = head.split()
        if len(toks) == 1 or not re.match(r'^[A-ZČĆŽŠĐ][a-zčćžšđ]+$', toks[1]):  # "Dušanka . ..": a given name alone
            return _record('', toks[0] if toks else '', '', '; '.join(pre + [rest.strip()]) if rest.strip() else '; '.join(pre))
        return _record(toks[0], ' '.join(toks[1:]), '', '; '.join(pre + ([rest.strip()] if rest.strip() else [])))
    last, father, given, alias = m.groups()
    rest = text[m.end():].strip().lstrip(',').strip()
    notes = [f'ili {alias.strip()}'] if alias and not re.match(r'^ili\b', alias.strip()) else ([alias.strip()] if alias else [])
    return _record(last, given, (father + '.') if father else '', '; '.join(pre + notes + ([rest] if rest else [])))


def _corpus() -> tuple[Counter, Counter]:
    last, first = Counter(), Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name == OWN:
            continue
        for s in json.loads(f.read_text(encoding='utf-8')):
            last[s.get('last_name') or ''] += 1
            first[s.get('first_name') or ''] += 1
    return last, first


def _variants(v: str) -> list[str]:
    """The spellings v may stand for: А for Д or Л at the start (Арагољуб, Аукијановић), Б or Ћ for Ђ there
    (Борћевић = Ђорђевић), ћ for ђ inside (Анћелко), each alone or together."""
    starts = {v}
    if v[:1] == 'A':
        starts |= {'D' + v[1:], 'L' + v[1:]}
    if v[:1] in ('B', 'Ć'):
        starts.add('Đ' + v[1:])
    out = set()
    for w in starts:
        out.add(w)
        inner = [i for i, ch in enumerate(w[:-1]) if ch == 'ć']                # not a final ć (-ić)
        out |= {w[:i] + 'đ' + w[i + 1:] for i in inner}
        if inner:
            out.add(''.join('đ' if i in inner else ch for i, ch in enumerate(w)))
    out.discard(v)
    return sorted(out)


# Names whose text layer is Latin look-alikes of the Cyrillic (znaci.org re-typeset the book from its OCR, so the
# page shows them so too): read from the letters ("euh" = вић, B = Ђ or В) and the alphabetical order around each
# ("Aačić" between Dačić and Dejanović, "Tpajwioeuh" among the Trajilovićs). "Awiko", "Mwroean", "Yzpuu" stay.
LOOKALIKE_LAST = {'Bopheeuh': 'Đorđević', 'Bopheeuh-Bogičić': 'Đorđević-Bogičić', 'Bypheeuh': 'Đurđević',
                  'Bypuh': 'Đurić', 'Bacitteeuh': 'Vasiljević', 'Bacivbeeuh': 'Vasiljević', 'Bejhicoeuh': 'Veljković',
                  'Mujjouieeuh': 'Milošević', 'Mwioiueeuh': 'Milošević', 'Tpajvbweuh': 'Trajilović',
                  'Tpajwioeuh': 'Trajilović', 'Aačić': 'Dačić', 'Miišć': 'Mišić'}
LOOKALIKE_FIRST = {'Bophe': 'Đorđe', 'Bypha': 'Đurđa', 'Bacwtuje': 'Vasilije', 'Mwian': 'Milan', 'Mwiuja': 'Milija',
                   'Mwioui': 'Miloš', 'MwbKO': 'Milko', 'Mwb': 'Milko', 'Armutin': 'Dragutin', 'Armoslav': 'Dragoslav',
                   'Arašša': 'Dragiša', 'Aalko': 'Lalko', 'Aale': 'Lale'}


def repair(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        s['last_name'] = LOOKALIKE_LAST.get(s['last_name'], s['last_name'])
        s['first_name'] = LOOKALIKE_FIRST.get(s['first_name'], s['first_name'])
    soldiers = repair_cyrillic_ocr(soldiers)
    last, first = _corpus()
    n = 0
    for s in soldiers:
        for field, ref in (('last_name', last), ('first_name', first)):
            v = s.get(field) or ''
            best = max(_variants(v), key=lambda c: ref[c], default=None)
            if best and ref[best] >= 5 and ref[best] >= 10 * max(ref[v], 1):
                s[field] = best
                n += 1
    # the bios: a capitalized word read with А for Д, where the book prints the Д spelling at least twice as often
    words = Counter(w for s in soldiers for w in re.findall(rf'\b[{U}][{L}]+\b', s['additional_info']))
    fix = {w: 'D' + w[1:] for w, k in words.items()
           if w.startswith('A') and words['D' + w[1:]] >= max(2, 2 * k)}
    for s in soldiers:
        info = re.sub(rf'\b[{U}][{L}]+\b', lambda m: fix.get(m.group(0), m.group(0)), s['additional_info'])
        if info != s['additional_info']:
            s['additional_info'] = info
            n += 1
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    print(f'  repaired {n} names and bios (А for Д/Л, ћ for ђ)')
    return birthplaces(soldiers)


# ── birthplaces ──────────────────────────────────────────────
# "rođen 1914. u Burovcu kod Petrovca na Mlavi", "rođen 1921. u Dobroj, Golubac", "rođen u selu Tabanovac": the
# village in the locative (or the nominative after "selu"), then the municipality (nominative, or genitive after
# "kod"). The other units' places are no help here: earlier books of this region left "Boževcu", "Melnice" and "Dobro"
# in the corpus. The village takes the nominative this book itself prints most ("selo Ranovac", "iz Melnice" no: only
# whole phrases after "u"), else a declension rule (-cu after a consonant = -ac, -ci = -ca, -oj = -a, -ovu = -ovo,
# -ju = -je, -ima = -i), else stays as printed.
BORN = re.compile(rf'rođen[a]?\s+(?:[^,;]*?1[89]\d\d\.?,?\s*(?:godine,?\s*)?)?u\s+(selu\s+)?([{U}][^,;.()]*?)'
                  rf'(?:\s+kod\s+([{U}][^,;.()]*?))?(?:\s*\(([{U}][^)]*)\))?(?:,\s*([{U}][^,;.()]*?))?(?=,|;|\.|\s+u\s+NOVJ|\s+u\s+\d|\s+stupio|\s+\(|$)')
MUNICIPALITIES = ['Petrovac na Mlavi', 'Malo Crniće', 'Kučevo', 'Golubac', 'Aleksinac', 'Despotovac', 'Modriča', 'Požarevac',
                  'Svetozarevo', 'Prokuplje', 'Majdanpek', 'Žabari', 'Niš', 'Zaječar', 'Kruševac', 'Kraljevo', 'Kuršumlija',
                  'Kragujevac', 'Lazarevac', 'Veliko Gradište', 'Soko Banja', 'Trstenik', 'Bela Palanka', 'Svrljig']
GENITIVE = {'Kučeva': 'Kučevo', 'Petrovca na Mlavi': 'Petrovac na Mlavi', 'Petrovca': 'Petrovac na Mlavi', 'Golupca': 'Golubac',
            'Golubca': 'Golubac', 'Požarevca': 'Požarevac', 'Zaječara': 'Zaječar', 'Kruševca': 'Kruševac', 'Niša': 'Niš',
            'Aleksinca': 'Aleksinac', 'Kraljeva': 'Kraljevo', 'Kuršumlije': 'Kuršumlija', 'Malog Crnića': 'Malo Crniće',
            'Modriče': 'Modriča', 'Kragujevca': 'Kragujevac', 'Despotovca': 'Despotovac', 'Prokuplja': 'Prokuplje',
            'Lazarevca': 'Lazarevac', 'Velikog Gradišta': 'Veliko Gradište', 'Soko Banje': 'Soko Banja', 'Trstenika': 'Trstenik'}
NOUN_RULES = [(r'(?<=[^aeiou])cu$', 'ac'), (r'ci$', 'ca'), (r'ki$', 'ka'), (r'gi$', 'ga'), (r'oj$', 'a'), (r'(?<=[oe]v)u$', 'o'),
              (r'(?<=in)u$', 'o'), (r'(?:(?<=[jđ])|(?<=št))u$', 'e'), (r'ima$', 'i'), (r'ama$', 'e'), (r'(?<=[^aeiou])i$', 'a'),
              (r'u$', '')]


def _noun_forms(w: str) -> list[str]:
    """Every nominative a locative noun may stand for, the most likely first."""
    out = []
    for pat, rep in NOUN_RULES:
        if re.search(pat, w):
            out.append(re.sub(pat, rep, w))
    if w.endswith('u'):
        out += [w[:-1] + 'o', w[:-1] + 'e', w[:-1] + 'a']
    return list(dict.fromkeys(out + [w]))


def _adjective(w: str, noun: str) -> str:
    """'Velikom' before Popovac = Veliki, before Polje = Veliko; 'Donjoj' = Donja."""
    if w.endswith('oj'):
        return w[:-2] + 'a'
    if re.search(r'[oe]m$', w):
        stem = w[:-2]
        neuter = 'e' if stem.endswith('j') else 'o'                       # "Donjem Ljubešu" = Donji, "Gornjem Selu" = Gornje
        return stem + ('a' if noun.endswith('a') else neuter if noun[-1:] in 'oe' else 'i')
    return w


def _municipality(m: str | None, genitive: bool) -> str:
    if not m:
        return ''
    m = re.sub(r'\s+', ' ', m.strip())
    if genitive or m in GENITIVE:
        m = GENITIVE.get(m, '')
    close = __import__('difflib').get_close_matches(m, MUNICIPALITIES, n=1, cutoff=0.8) if m else []
    return close[0] if close else m                                         # "Petrovad na Mlavi", "Mado Crniće"


def birthplaces(soldiers: list[dict]) -> list[dict]:
    found = [(s, BORN.search(s['additional_info'])) for s in soldiers]
    printed = Counter(m.group(2).strip() for _, m in found if m)            # phrases after "u": the nominatives too
    places = Counter()                                                       # the other units' birthplaces
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != OWN:
            for r in json.loads(f.read_text(encoding='utf-8')):
                for p in re.split(r',\s*', r.get('birth_place') or ''):
                    places[p] += 1
    n = 0
    for s, m in found:
        if not m:
            continue
        village = re.sub(r'\s+', ' ', m.group(2).strip())
        if not m.group(1) or re.search(r'(?:oj|cu|ci|ju|vu|nu)$', village):   # "u Burovcu", "u selu Dobroj": the locative
            head, na, tail = village.partition(' na ')                        # "Petrovcu na Mlavi": decline the first part
            words = head.split()
            nouns = _noun_forms(words[-1])
            cands = [' '.join([_adjective(a, nn) for a in words[:-1]] + [nn]) + (na + tail if na else '') for nn in nouns]
            seen = [c for c in cands if c != village and printed[c]]
            known = [c for c in cands if c != village and places[c] >= 3]
            if seen:
                village = max(seen, key=lambda c: printed[c])
            elif cands[0] != village and not re.search(r'[A-ZČĆŽŠĐ]{2}|\d', village):
                village = cands[0] if places[cands[0]] or not known else max(known, key=lambda c: places[c])
        town = __import__('difflib').get_close_matches(village, MUNICIPALITIES, n=1, cutoff=0.85)
        village = town[0] if town else village                              # "Malom Crniću" read as Mali Crnić, "Golupcu"
        muni = _municipality(m.group(4) or m.group(5), False) or _municipality(m.group(3), True)
        if village.startswith('NOVJ') or len(village) > 30:
            continue
        place = village if not muni or muni == village else f'{village}, {muni}'
        s['birth_place'] = place
        n += 1
    print(f'  birthplaces read for {n} records')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/19-srpska.pdf',
        brigade_code=73,
        output_path=f'website/public/{OWN}',
        start_page=1,
        end_page=200,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§[ps]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=repair,
    )
