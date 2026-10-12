"""
Parser: 5. proleterska crnogorska brigada (brigade code 41), its second book: the brigade's women fighters.

Source: "Partizanke Pete proleterske crnogorske brigade" (352 scan pages), in the Digital library of Poreklo
        (biblioteka.poreklo.rs; for members only). The library's OCR text is kept in
        data-extraction/poreklo/5-proleterska-partizanke.json (poreklo_text.py). "Biografije" (scan pages 47-282): a
        bio of each woman who fought in the brigade, alphabetical, three columns a page; a heading in capitals, the
        father's name between (ALEKSIC Ivana DARINKA; ALEKSIC Jure JELISAVA, udata GILJEN), then her life: birth, the
        war, the brigade, wounds, decorations, often her life after the war and her death.
        The book's contents (scan pages 333-344) list every bio with its page, the names in lower case with their
        diacritics ("Aleksić Jure Jelisavka, udata Giljen"), which the OCR reads better than the headings' capitals:
        the bios are aligned with the contents in order and take their names from there.
The records get IDs from 0041010001 and go into the unit's file beside Borci Sutjeske's (keep_other_sources); a woman in
both books is merged by corrections. There is no scan on the site: records carry `source_url` and `source_page`.
"""
import difflib
import json
import re
from pathlib import Path

from _parser_scaffold import _record, run_parser
from poreklo_text import (FOLD, VIEWER_URL, load, name_counts, page_lines, printed_page, restore_diacritics,
                          viewer_url)

BOOK = load('5-proleterska-partizanke.json')
PAGES = range(47, 283)
CONTENTS = range(333, 345)
MARK = 'ꙮ '                                          # starts an entry (a letter: the scaffold strips leading marks)
BIO = '¶'                                            # where the heading ends and the bio begins
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


ACRONYM = re.compile(r'^(?:SKOJ|[A-Z]{0,3}KPJ|SKJ|AFŽ|AFZ|NOB|NOV|NOVJ|NOR|NOP|NOO|USAOJ|JNA|JA|SUBNOR|SSRN|AVNOJ|ZAVNO\w*|GK|GKKPJ|MK|OK|OKKPJ|SK|CK|PK)\b')


def caps(text: str) -> bool:
    """A heading line: the name in capitals, the father's name in lower case between ("ALEKSIC Ivana DARINKA"); a
    heading broken after the father ("BAJIĆ Glige" / "GOSPAVA"); not a bio's line that starts with "SKOJ-a"."""
    if ACRONYM.match(text):
        return False
    letters = re.sub(r'[^A-Za-zČĆŽŠĐčćžšđА-Яа-я]', '', text)
    if (len(letters) >= 4 and sum(c.isupper() for c in letters) >= 0.7 * len(letters)
            and bool(re.match(rf'^[{U}А-Я]{{2,}}', text))):
        return True
    # word by word: capitals, one father's name, "udata", "rođena", "zvana" ("BOŽOVIĆ Sava DANICA, udata")
    words = [w.strip(',.;:()') for w in re.split(r'\s+|[—–]', text) if w.strip(',.;:()–—-')]
    if not words or not re.fullmatch(rf'[{U}А-Я][{U}А-Я\-]{{2,}}\S*', words[0]):
        return False
    fathers = 0
    for w in words[1:]:
        if re.fullmatch(rf'[{U}А-Я][{U}А-Я\-]+\S*', w) or w in ('udata', 'rođena', 'zvana', 'ud', 'rođ'):
            continue
        if re.fullmatch(rf'[{U}][{L}]+', w.replace('-', '')) and fathers < 2:     # "Jure – Grge", "Jo-ksima"
            fathers += 1
            continue
        return False
    return True


def heading_more(text: str) -> bool:
    """A heading's next line that starts with the father's name: "Mirka JELKA, JELA" after "VUČKOVIĆ—GNJATOVIĆ\""""
    return bool(re.match(rf'^[{U}][{L}]+\s+[{U}]{{2,}}\b', text)) and caps(text.split(None, 1)[1])


# The foot of the last page sets two bios side by side in two columns, which the OCR mixes with the three above them;
# read from the scan (scan page 282, book p. 278). The contents print the second as "Raičević-Zeković Vukosava".
TYPED = {282: [
    ('NOVOVIĆ-SAVOVIĆ DANICA', 'Borac 3. čete 4. bataljona 5. proleterske crnogorske brigade od proljeća 1944. do kraja '
                               'rata. Poslije rata udata Sakleski; živjela u Vrnjačkoj Banji.'),
    ('RAIČEVIĆ-KEKOVIĆ VUKOSAVA', 'Borac Prateće čete 4. bataljona 5. brigade. Poslije rata udata Popović, Umrla.'),
]}
TYPED_FROM = {282: -17450}                           # the OCR's lines from this height down are left out
# what the contents print differently from the heading over the bio
CUR = ['']
REVIEW = []                                          # where the heading and the contents differ, for checking
KEEP = {'Staka', 'Kosta'}                                     # names the corpus would wrongly give a mark ("Štaka")
# the contents' lines that need a word (scan p. 343: "Puharić Jure – Grge Marica", the father known by two names)
TOC_FIX = {'Puharić Jure – Grge Marica': ('Puharić Jure Marica', 'otac Jure – Grge'),
           'Lakić Miloša Stanica – Caka': ('Lakić Miloša Stakica – Ćaka', ''),   # the heading: STAKICA ĆAKA
           'Janjević Sima Staka – Caka': ('Janjević Sima Staka – Ćaka', '')}     # the heading: STAKA ĆAKA
# headings read from the scan: the father's name set in Cyrillic look-alikes (p. 48), the father's two names (p. 207)
HEAD_FIX = {'ANDRIJAŠEVIČ Беба': 'ANDRIJAŠEVIĆ Beća', 'PUHARIC Jure Grge MARICA': 'PUHARIĆ Jure MARICA'}
CONTENTS_NOTE = {'Raičević-Keković Vukosava': 'u sadržaju knjige Raičević-Zeković'}


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out, in_head = [], False
    for page in PAGES:
        for col in page_lines(BOOK, page, 3):
            col_lines = []
            for line in col:
                if page in TYPED_FROM and line.top >= TYPED_FROM[page]:
                    continue
                # a heading's first line the OCR set on the last line of the bio before: "... za narod. IVANOVIC Milosava"
                m = re.search(r'(?<=[.!?“"»])\s+(?=\S+\s+\S+(?:\s+\S+){0,2}$)', line.text.strip())
                if m and caps(line.text.strip()[m.end():]) and not caps(line.text.strip()):
                    col_lines += [(line, line.text.strip()[:m.start()]), (line, line.text.strip()[m.end():])]
                else:
                    col_lines.append((line, line.text.strip()))
            for line, text in col_lines:
                text = re.sub(rf'^l(?=[{U}]{{2,}})|(?<=[{U}])l(?=[{U}])', 'I', text)     # "lVANOVIC": l for I
                text = re.sub(rf'^J (?=[{U}]{{2,}})', 'J', text)                  # "J OVANKA"
                if not text or re.fullmatch(r'[\d\s.]+', text) or re.fullmatch(r'[A-ZА-ЯČĆŽŠĐ]{1,2}\.?', text):
                    continue                                                 # page numbers, the letter headings
                if caps(text):
                    start = not in_head                                      # a second heading line continues it
                    out.append({'text': (MARK if start else '') + text, 'x': line.x0, 'y': line.top, 'page': page})
                    in_head = True
                    continue
                # "udata GILJEN", "dr FRIDA", "(Filipa) JELENA": the heading's next line; specks before it ("·udata",
                # "„idata DURISIC", "urdata")
                if in_head and (re.match(rf'^[^\w(]*(?:u|i|ur)data\s|^[^\w(]*(?:rođena|ud\.)\s|^dr\.?\s+[{U}]{{2,}}'
                                         rf'|^\(\w+\)\s+[{U}]{{2,}}', text) or heading_more(text)):
                    text = re.sub(r'^[^\w(]*(?:i|ur)data\b', 'udata', re.sub(r'^[^\w(]+', '', text))
                    out.append({'text': text, 'x': line.x0, 'y': line.top, 'page': page})   # "udata GILJEN"
                    continue
                out.append({'text': (BIO if in_head else '') + text, 'x': line.x0, 'y': line.top, 'page': page})
                in_head = False
        for head, bio in TYPED.get(page, []):
            out += [{'text': MARK + head, 'x': 0, 'y': TYPED_FROM[page], 'page': page},
                    {'text': BIO + bio, 'x': 0, 'y': TYPED_FROM[page], 'page': page}]
            in_head = False
    return out


def contents() -> list[dict]:
    """The contents' entries in order: the name as printed there, split into its parts, and the book page"""
    lines = []
    for page in CONTENTS:
        lines += [l.text.strip() for l in page_lines(BOOK, page)[0]]
    out, carry = [], ''
    for t in lines:
        if re.match(r'^(?:Strana|SADR|IZ |RIJEC|RIJEČ|Dr |PIONIRKE|NEKI|SPISAK|KIH )', t) or not t:
            carry = ''
            continue
        t = (carry + ' ' + t).strip() if carry else t
        t = t.replace("'", '')                                               # specks: "Grgic'ević", page "4'7"
        # a name the OCR began wrongly too ("anatić Marka Vera" for Gnjatić, "кит Sime Jelka" for Kajin)
        m = re.match(r'^(?P<name>[^\d\s.].*?\s.*?)[\s.·…]*(?P<page>\d{1,3})$', t)
        if not m:
            carry = t if re.match(rf'^[{U}]', t) else ''                     # a name wrapped to the next line
            continue
        carry = ''
        out.append({'printed': m.group('name').strip(' .'), 'page': int(m.group('page'))})
    for e in out:
        printed = re.sub(r'\s+_$', '', e['printed'])
        printed = re.sub(r'^([A-ZČĆŽŠĐ]) (?=[a-zčćžšđ])', r'\1', printed)       # "N ovović-Savović"
        printed, note = TOC_FIX.get(printed, (printed, ''))
        printed = re.sub(r'\.\s+(?=udata|rođena)', ', ', printed)           # "Stanišić Boža Jagoda. udata Mugoša"
        for slip in ('Gajović Mijata, ', 'Golović Boža, '):                  # a comma after the father's name
            printed = printed.replace(slip, slip[:-2] + ' ')
        main, _, extra = printed.partition(',')
        main = re.sub(r'\s+[—–-]+\s+', ' – ', main)                           # "Jogoda – Pil", "Burda –— Duka"
        nicks, married = [], []
        if ' – ' in main:
            main, nick = main.split(' – ', 1)
            (married if nick.strip().startswith('udata') else nicks).append(nick.strip())   # "Stana – udata Vico"
        title = 'dr' if re.search(r'\sdr\s', main) else ''
        main = main.replace(' dr ', ' ')
        alt = re.search(r'\s\((\w+)\)', main)                                # "Beća (Filipa)": the father's other name
        if alt:
            main = main.replace(alt.group(0), '')
        words = main.split()
        if len(words) >= 4:                                                  # "Brajović Milisava Danica Maca"
            rest = ' '.join(words[3:])
            (married if rest.startswith(('udata', 'rođena')) else nicks).insert(0, rest)   # "Stana udata Vico"
            words = words[:3]
        cap = lambda w: w[:1].upper() + w[1:]                               # "Brajović Petra ljubica"
        last = cap(words[0]) if words else ''
        father = cap(words[1]) if len(words) == 3 else ''
        given = cap(words[-1]) if len(words) >= 2 else ''
        if alt:
            note = f'otac {father} ({alt.group(1)})'
        for part in (p.strip(' _') for p in extra.split(',') if p.strip(' _')):
            (married if re.match(r'(?:udata|udala|rođena)\b', part) else nicks).append(part.replace('udala', 'udata'))
        nicks = [n for n in (re.sub(r'^[\W_]+', '', n) for n in nicks) if len(re.sub(r'[\W_]', '', n)) >= 2]
        e.update(last=last, father=father, given=given, nick=', '.join(nicks), extra='; '.join(married), note=note, title=title)
    return out


def fold(text: str) -> str:
    return re.sub(r'[^a-z ]', '', text.translate(FOLD).lower().replace('dj', 'd'))


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '').strip()
    head, _, bio = text.partition(BIO)
    head = re.sub(r'\s+', ' ', head).strip(' ,')
    bio = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', bio.strip())  # "organi— zovanja"
    bio = re.sub(r"^[^\w„\"(]*(?:l\s*'\s*)?", '', bio)                              # "l ' Rođena": specks
    for wrong, right in HEAD_FIX.items():
        head = head.replace(wrong, right)
    head = re.sub(r'^JAN JEVIC\b', 'JANJEVIC', head)                       # the OCR split the name after N
    head = re.sub(rf'(?<=[{L}])-(?=[{L}])', '', head)                          # "Ars-a"
    head = re.sub(rf'^([{U}]{{2,}}) ([{U}]{{1,2}})(?=[\s,])', r'\1\2', head)    # "MIN IĆ", "TOMAŠEVI C"
    head = head.replace('·', '').replace("'", '')
    head = re.sub(rf'(?<=[{L}])[,;.]+\s+(?=[{U}]{{2,}})', ' ', head)                # "LAKIČ Petra,; MAŠA", "Miloša."
    # "DRAGINJ A", "KOVILJ KA", "BULAJ IC": a word broken after a consonant (not "JAGODA PI LE", a nickname)
    head = re.sub(rf'(?<=[{U}][BCČĆDĐFGHJKLMNPRSŠTVZŽ]) (?=[{U}]{{1,2}}(?:[\s,.]|$))', '', head)
    head = re.sub(rf'(?<=[{U}]{{3}}) (?=(?:LJ|NJ)[^AEIOU\s])', '', head)          # "BOSI LJKA"
    head = re.sub(rf'\b([{U}][{L}]) ([{L}]+)\b', r'\1\2', head)                  # "Os toje", "Lj uba"
    head = re.sub(rf'(?<=[{L}])([ČĆŽŠĐ])(?=[{L}])', lambda m: m.group(1).lower(), head)   # "MikŠe"
    head = re.sub(rf'(?<=[{U}])[y1](?=[\s,]|$)', ',', head)                      # "MILICAy udata", "MILEVA1 udata"
    head = re.sub(r'\s\(\w+\)(?=\s)', '', head)                                # "Beća (Filipa)": the contents keep it
    title = re.search(r'\sdr\.?(?=\s)', head)                                   # "GUTMAN Markusa dr FRIDA"
    head = head.replace(title.group(0), '') if title else head
    m = re.match(rf'^(?P<last>[{U}А-Я][^\s,]*(?:\s?[—–-]\s?[{U}][^\s,]*)?)\s+(?:(?P<father>[{U}]?[{L}]+)\s+)?(?P<given>[^\s,]+)', head)
    if not m:
        return {}
    rec = _record(re.sub(r'\s?[—–-]+\s?', '-', m.group('last')), m.group('given').strip('.'), m.group('father') or '', bio)
    rec['_head'] = head
    rec['_title'] = 'dr' if title else ''
    # after the given name: a nickname ("STAKA CAKA", "JELKA, JELA") and a married or maiden name ("udata POPOVIČ")
    rest = head[m.end():]
    married = re.search(r'\b(udata|rođena|ud\.|rođ\.)\s+([^\s,]+)', rest)
    rec['_extra'] = f"{married.group(1)} {married.group(2).title()}" if married else ''
    nick = re.match(rf'^[\s,—–-]*([{U}]{{3,}})\b', rest[:married.start()] if married else rest)
    rec['_nick'] = nick.group(1).title() if nick else ''
    return rec


def corpus() -> dict:
    """The other units' spellings, and the brigade's own from Borci Sutjeske (its file is skipped for this book's
    records)"""
    counts = name_counts('5-proleterska-soldiers.json')
    prefix = VIEWER_URL.split('{')[0] + BOOK['id']
    path = Path(__file__).resolve().parent.parent / 'website' / 'public' / '5-proleterska-soldiers.json'
    for s in json.loads(path.read_text(encoding='utf-8')):
        if not (s.get('source_url') or '').startswith(prefix):
            for field, c in counts.items():
                c[s.get(field) or ''] += 1
    return counts


def post(soldiers: list[dict]) -> list[dict]:
    toc = contents()
    a = [fold(f"{s['_head']}") .split() for s in soldiers]
    b = [fold(f"{e['last']} {e['father']} {e['given']}").split() for e in toc]
    key_a = [' '.join(x[:1] + x[-1:]) for x in a]
    key_b = [' '.join(x[:1] + x[-1:]) for x in b]
    matcher = difflib.SequenceMatcher(None, key_a, key_b, autojunk=False)
    pairs = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                pairs[i1 + k] = j1 + k
        elif tag == 'replace':
            # blocks of different sizes: each bio to the contents' entry its name is closest to
            taken = set()
            for i in range(i1, i2):
                best = max(((difflib.SequenceMatcher(None, key_a[i], key_b[j]).ratio(), j) for j in range(j1, j2)
                            if j not in taken), default=(0, None))
                if best[0] >= 0.75:
                    pairs[i] = best[1]
                    taken.add(best[1])
    # a pair holds only when surname and given name are close (a 'replace' block may pair two different women); a bio
    # left over takes an unused entry of the contents nearby that is
    def close(i, j):
        """The same woman: the given names nearly the same (Desanka is not Stanka), the surnames close or the whole
        heading close ("MIN IĆ Veliše NJEGOSAVA"), the fathers not different (Zdilac Dragutina, Zdilar Milana Zorka)"""
        sa, sb = soldiers[i], toc[j]
        r = lambda x, y: difflib.SequenceMatcher(None, fold(x), fold(y)).ratio()
        whole = r(f"{sb['last']} {sb['father']} {sb['given']}", sa['_head'].split(',')[0])
        ocr = lambda v: fold(v).replace('b', 'd').replace('rn', 'm')       # Đ read as B, rn as m ("VEMIJA")
        given = difflib.SequenceMatcher(None, ocr(sb['given']), ocr(sa['first_name'])).ratio()
        garbled = not re.fullmatch(rf'[{U}]{{3,}}', sa['first_name'])
        if fold(sb['given']) and fold(sb['given']) == fold(sa['_nick']):      # "JOVANKA JOKA", the contents "Joka"
            given = 1.0
        return ((given >= 0.8 and (r(sb['last'], sa['last_name']) >= 0.7 or whole >= 0.85) or garbled and whole >= 0.8)
                and (not sb['father'] or not sa['middle_name'] or r(sb['father'], sa['middle_name']) >= 0.5))
    pairs = {i: j for i, j in pairs.items() if close(i, j)}
    used = set(pairs.values())
    for i in range(len(soldiers)):
        if i in pairs:
            continue
        # around where the neighbours' pairs put her: the contents and the bios drift apart where either lost one
        prev = max((k for k in pairs if k < i), default=None)
        at = pairs[prev] + (i - prev) if prev is not None else i
        near = sorted((j for j in range(max(0, at - 6), min(len(toc), at + 7)) if j not in used and close(i, j)),
                      key=lambda j: abs(j - at))
        if near:
            pairs[i] = near[0]
            used.add(near[0])
    counts = corpus()
    groups = {f: {} for f in counts}
    for f, c in counts.items():
        for v, n in c.items():
            groups[f][fold(v)] = groups[f].get(fold(v), 0) + n

    def choose(field, head, toc_v):
        """The heading's or the contents' spelling of a name. Where both are names the other units know, the heading
        over the bio (the book's own entry: JULKA, Riste, VELEMIR, RADOSAVOVIĆ where the contents print Jelka, Rasta,
        Velimir, Radosavljević); the contents' where the heading's OCR made no known name ("Gnluba", "HADUŠA") or only
        lost the diacritics. Both print Đ where the OCR reads B in one and D in the other ("Burić", "DURIČ": Đurić)."""
        head, toc_v = head.strip(' .'), toc_v.strip(' .')
        if not toc_v or not head:
            return toc_v or head
        hp, tp = head.split('-'), toc_v.split('-')
        if len(hp) != len(tp):
            return toc_v
        out = []
        for h, t in zip(hp, tp):
            known = lambda v: groups[field].get(fold(v), 0)
            fh, ft = fold(h), fold(t)
            dj = [v for v in ('Đ' + t[1:], 'Đ' + h[1:]) if known(v)]
            if t[:1] in 'BD' and h[:1] in 'BDĐ' and dj and known(max(dj, key=known)) >= 5 * max(known(t), 1):
                out.append(max(dj, key=known))                        # "Barović", "BUROVIC", "Boka": Đurović, Đoka
            elif fh == ft:
                out.append(t)
            elif {fh[:1], ft[:1]} == {'b', 'd'} and fh[1:] == ft[1:]:
                out.append('Đ' + t[1:])
            elif fh.replace('b', 'd') == ft.replace('b', 'd'):
                out.append(t)                                         # "ANBELIJA": Anđelija
            elif h[:1].isupper() and (known(h) or (not known(t) and re.fullmatch(rf'[{U}{L}]+', h, re.I))):
                out.append(h)
                REVIEW.append(f'{field}: heading {h} ({known(h)}) over contents {t} ({known(t)})  [{CUR[0]}]')
            else:
                out.append(t)
                REVIEW.append(f'{field}: contents {t} ({known(t)}) over heading {h} ({known(h)})  [{CUR[0]}]')
        return '-'.join(out)

    matched, unmatched = 0, []
    for i, s in enumerate(soldiers):
        e = toc[pairs[i]] if i in pairs else None
        head_last, head_given = s['last_name'].title(), s['first_name'].title()
        CUR[0] = f"{s['_head']} | {e['printed'] if e else ''} | p. {s['pdf_page']}"
        if e:
            s['last_name'] = choose('last_name', head_last, e['last'].replace('—', '-'))
            # "TOPIĆ Rada VUKICA" over the contents' "Vukosava – Vukica": the heading set only the nickname
            s['first_name'] = (e['given'] if e['nick'] and fold(head_given) == fold(e['nick'])
                               else choose('first_name', head_given, e['given']))
            s['middle_name'] = choose('middle_name', s['middle_name'], e['father'])
            nick, married, note = e['nick'] or s['_nick'], e['extra'].split('; ') if e['extra'] else [], e['note']
            if len(married) == 1 and s['_extra']:    # the heading's married name against the contents' ("Burišić")
                word, name = married[0].split(' ', 1)
                married = [f"{word} {choose('last_name', s['_extra'].split(' ', 1)[1], name)}"]
            married = married or ([s['_extra']] if s['_extra'] else [])
            matched += 1
        else:
            unmatched.append(s)
            s['last_name'], s['first_name'] = head_last, head_given
            nick, married, note = s['_nick'], [s['_extra']] if s['_extra'] else [], ''
        # the corpus restores letters the OCR lost ("Zivković", "Dorđa"), never one the contents print ("Žarić")
        fields = ('last_name', 'first_name', 'middle_name')
        was = {f: s[f] for f in fields}
        restore_diacritics([s], counts)
        for f in fields:                             # only the marks the OCR lost or mixed up (Č for Ć): Žarić stays
            if was[f] in KEEP or any(a != b and a not in 'CDSZcdszČĆčć' for a, b in zip(was[f], s[f])):
                s[f] = was[f]
        for f in fields:
            if s[f] != was[f] and e:
                REVIEW.append(f'restored {was[f]} -> {s[f]}')
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        for k, m in enumerate(married):              # the married or maiden name, its diacritics as the surname's
            word, name = m.split(' ', 1)
            t = {'last_name': name, 'first_name': ''}
            restore_diacritics([t], counts, fields=('last_name',))
            dj = 'Đ' + t['last_name'][1:]                # "udata Burović", "rođena Burković": Đ read as B
            if t['last_name'][:1] in 'BD' and groups['last_name'].get(fold(dj), 0) >= 5 * max(groups['last_name'].get(fold(t['last_name']), 0), 1):
                t['last_name'] = dj
            married[k] = f"{word} {t['last_name']}"
        title = (e['title'] if e else '') or s['_title']
        if nick and married and any(difflib.SequenceMatcher(None, fold(nick), fold(m.split(' ', 1)[1])).ratio() >= 0.8
                                    for m in married):
            nick = ''                                # "Ivka, Skrobica": the married name ŠKRABICA misread
        pre = [title] if title else []
        pre += [f'zvana {nick}'] if nick else []
        pre += married + ([note] if note else [])
        pre += [CONTENTS_NOTE[s['full_name']]] if s['full_name'] in CONTENTS_NOTE else []
        if pre:
            s['additional_info'] = '; '.join(pre) + '; ' + s['additional_info']
        s['fathers_name'] = s['middle_name']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s['middle_name'], s['first_name']) if x)
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file', '_head', '_nick', '_extra', '_title'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
    REVIEW.extend(f"unmatched: {s['full_name']}" for s in unmatched)
    print(f'  {len(toc)} in the contents, {len(soldiers)} bios, {matched} named from the contents;'
          f' not matched: {[s["full_name"] for s in unmatched][:30]}')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='poreklo/5-proleterska-partizanke.json',
        brigade_code=41,
        output_path='website/public/5-proleterska-soldiers.json',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
        source_url_prefix=VIEWER_URL.split('{')[0] + BOOK['id'],
    )
