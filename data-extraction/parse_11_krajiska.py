"""
Parser: 11. krajiška (kozaračka) NOU brigada (brigade code 107).

Source: Đuro Milinović, Drago Karasijević, "Jedanaesta krajiška NOU brigada" (znaci.org 00001/167_12.pdf, the chapter
        "Spiskovi"). Latin, one column; two lists, two PDFs:
    11-krajiska-zene.pdf (its page 5, book p. 425): "Spisak žena boraca koje su se nalazile u 11. KNOU brigadi", the
        names run on, comma after comma ("Adamović Aleksandra-Lesa, Adamović Milka, Alavuk Dra- / gica, ...");
    11-krajiska-poginuli.pdf (its pages 18-43, book pp. 439-463): "Spisak poginulih boraca 11. kozaračke NOU
        brigade", by municipality ("OPŠTINA BOSANSKA DUBICA"), numbered anew under each, the first line indented:
            1. — Hrkec J. Ivica, rod. 1920. u Bos. Dubici, trg. pom. Stupio u NOV 13. U. 1943. Poginuo 25. VIII
            1944. u Bos. Novi.
        An entry starts at an indented number, with or without its dash ("37 — Goronja", "109. Subotić").
The father as an initial or in the genitive ("Đurić Teodora Branko"). The parser sets the birthplace (a village
"u s." as printed, a town in the nominative the other units know, with the heading's municipality) and the death:
date, place and the duty "kao vodnik". Each woman of the run-on list gets her own box on the page (pdf_rects for a
name broken over two lines); entry_boxes.py leaves these alone (INLINE_ENTRIES). The narodni heroji and the bios of
the fallen leaders (book pp. 421-438) are not read.
"""
import re
from itertools import product

import pdfplumber

import parse_toplicki_odred as top
from _parser_scaffold import _record, death_type_from_text, extract_lines_single_column, run_parser
from pdf_coords import viewer_words

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
WOMEN, FALLEN = 'website/public/pdfs/11-krajiska-zene.pdf', 'website/public/pdfs/11-krajiska-poginuli.pdf'
MUNI = {'Metkovlcl': 'Metković', 'Busovaca': 'Busovača'}
# The women's list: the scan's slips, and a name printed given name first.
WOMAN = {'Lekib Milja': ('Lekić', 'Milja'), 'Štefica Faraga': ('Faraga', 'Štefica')}
_muni = {'name': ''}
_box: dict = {}


def _boxes(words: list[dict]) -> dict:
    segs: list[list[dict]] = []
    for w in words:
        if segs and abs(segs[-1][-1]['top'] - w['top']) < 4:
            segs[-1].append(w)
        else:
            segs.append([w])
    rects = [[round(min(w['x0'] for w in s), 1), round(min(w['top'] for w in s), 1),
              round(max(w['x1'] for w in s), 1), round(max(w['bottom'] for w in s), 1)] for s in segs]
    out = {'pdf_x_end': max(r[2] for r in rects), 'pdf_y_end': max(r[3] for r in rects)}
    if min(r[0] for r in rects) < rects[0][0]:
        out['pdf_x_left'] = min(r[0] for r in rects)
    if len(rects) > 1:
        out['pdf_rects'] = rects
    return out


def women(pdf_path: str) -> list[dict]:
    """One line per name of the run-on list: '§z§ Surname Given' at its first word."""
    with pdfplumber.open(pdf_path) as pdf:
        words = [w for w in viewer_words(pdf.pages[0]) if w['top'] > 170 and not re.fullmatch(r'\d+»', w['text'])]
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w['top'], w['x0'])):
        if lines and abs(lines[-1][0]['top'] - w['top']) < 4:
            lines[-1].append(w)
        else:
            lines.append([w])
    toks: list[dict] = []                                                    # words, a word broken at a line end made whole
    for ln in lines:
        for k, w in enumerate(sorted(ln, key=lambda w: w['x0'])):
            prev = toks[-1] if toks else None
            if k == 0 and prev and prev['text'].endswith('-') and prev['end']:
                if w['text'][:1].islower():                                  # "Dra- / gica"
                    prev['text'] = prev['text'][:-1] + w['text']
                    prev['words'].append(w)
                    prev['end'] = len(ln) == 1
                    continue
                if w['text'].startswith('-'):                                # "Bjelovuk- / -Bjelić"
                    prev['text'] += w['text'][1:]
                    prev['words'].append(w)
                    prev['end'] = len(ln) == 1
                    continue
                prev['text'] = prev['text'][:-1]                             # "Lončar- / Jovanka": a slip for a space
            toks.append({'text': w['text'], 'words': [w], 'end': k == len(ln) - 1})
    items: list[list[dict]] = [[]]
    for t in toks:
        if t['text'] == 'i':
            items.append([])
            continue
        text = t['text'].rstrip(',.')
        if text:
            items[-1].append({**t, 'text': text})
        if t['text'].rstrip('.').endswith(','):
            items.append([])                                                 # a comma ends a name ("Janjuš. / Zdravka": a speck)
    out = []
    for it in items:
        if not it:
            continue
        ws = [w for t in it for w in t['words']]
        x, y = round(ws[0]['x0'], 1), round(ws[0]['top'], 1)
        _box[('11-krajiska-zene.pdf', 1, x, y)] = _boxes(ws)
        out.append({'page': 1, 'x': x, 'y': y, 'text': '§z§ ' + ' '.join(t['text'] for t in it)})
    return out


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    return women(pdf_path) if pdf_path == WOMEN else extract_lines_single_column(pdf_path, start, end)


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if t.startswith('§z§'):
        return True
    if re.match(r'^(?:SPISAK POGINULIH|11\. KOZARACKE)', t) or re.fullmatch(r'[:\d\W]{1,8}|\d+\s+L|\d+\s+XI krajiška brigada \d+|\d+«\s*\d+', t):
        return False                                                         # the title, the page numbers
    m = re.match(r'^OPŠTINA\s+(.+)$', t)
    if m:
        name = ' '.join(w.capitalize() for w in m.group(1).split())
        _muni['name'] = MUNI.get(name, name)
        return False
    t = re.sub(r'(?<![\w.])2(?=[a-zčćžšđ])', 'Ž', t)                         # "2uljevci" = Žuljevci
    t = re.sub(r"^['‘’`]\s*(?=\d)", '', t)                                  # "' 27. — Golub": a speck before the number
    m = re.match(r'^\d{1,3}\s*[.,]?\s*[—–_-]+\s*', t) or (ln['x'] >= 79 and re.match(rf'^\d{{1,3}}\.\s+(?=[{U}])', t))
    if m:
        t = f'§p§{_muni["name"]}§ ' + t[m.end():]
    ln['text'] = t
    return True


def parse_woman(name: str) -> dict:
    words = name.split()
    if len(words) == 1 and '-' in words[0]:
        words = words[0].split('-', 1)
    last, given = WOMAN.get(' '.join(words), (' '.join(words[:-1]), words[-1]))
    return _record(last, given, '', '')


DEATH = re.compile(r'\b([Pp]oginu[ol]a?|[Uu]mr[lo]a?|[Uu]bijen[a]?|[Ss]treljan[a]?|[Ss]trijeljan[a]?|[Nn]esta[lo]a?)\b')
MONTHS = 'januara|februara|marta|aprila|maja|juna|jula|avgusta|augusta|septembra|oktobra|novembra|decembra'
DATE = re.compile(rf'(?:(\d{{1,2}})\.\s*([IVX]+|\d{{1,2}})\.?\s*|(?:(\d{{1,2}})\.\s*)?({MONTHS})\s+(?:mjeseca\s+|meseca\s+)?)?(19[45]\d)\.?(?:\s*godine)?')
OCCUPATION = {'zemlj': 'zemljoradnik', 'zemljradnik': 'zemljoradnik', 'dak': 'đak', 'trg. pom': 'trgovački pomoćnik',
              'trg. pomoćnik': 'trgovački pomoćnik'}
PLACE = rf'((?:[{U}][{L}]*\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)?(?:\s*[—–-]\s*[{U}][{L}]+(?:\s+[{U}][{L}]+)?)?)'


def parse(text: str) -> dict:
    if text.startswith('§z§'):
        return parse_woman(text[4:].strip())
    muni = text[3:text.index('§', 3)]
    text = text[text.index('§', 3) + 1:].strip()
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "zem- ljoradnik"
    text = text.replace('boracu s.', 'borac u s.')
    text = re.sub(rf'^([{U}{L}]+),\s+(?=[{U}]\.\s+[{U}][{L}]+\s*,)', r'\1 ', text)   # "Kadrić, O. Mujo,"
    head, info = (text.split(',', 1) + [''])[:2]
    info = info.strip()
    words = re.sub(rf'(?<=[{L}])-(?=[{L}])', '', head.replace('2.', 'Ž.')).split()   # "Gi-gić": a line-break hyphen
    if len(words) >= 4 and re.fullmatch(rf'[{U}]\.', words[-2]):
        words = [' '.join(words[:-2])] + words[-2:]                          # "Stojaković Kukić R. Petra"
    last, given = words[0][:1].upper() + words[0][1:], (words[-1] if len(words) > 1 else '')   # "gorgo N. Mićo"
    father = ' '.join(words[1:-1])
    rec = _record(last, given, father, info)
    d = DEATH.search(info)
    pre = info[:d.start()] if d else info
    pre = re.split(r'\b[Ss]tupi(?:o|la)\b', pre)[0]
    y = re.search(r'\b(1[89]\d\d)\b', pre)
    rec['birth_year'] = y.group(1) if y else ''
    occ = None
    for seg in pre.split(','):                                               # the occupation: "zemlj.", "trg. pom.", "radnik"
        occ = re.match(r'^([a-zčćžšđ]+\.?(?:\s+[a-zčćžšđ]{2,}\.?)?)(?=\s+ro[dđ]|\s+i$|\s*$)', seg.strip())
        if occ and not re.match(r'^(?:ro[dđ]|u\b|i\b)', seg.strip()):
            break
        occ = re.match(r'^(zemlj)\.', seg.strip())                           # "zemlj. iz Bereka", "zemlj. Borac, poginuo"
        if occ:
            break
    occ = occ or re.search(r'(?<=\d\.\s)(zemlj)\.', pre)                     # "Hrvat, rođ. 1910. zemlj."
    if occ:
        word = OCCUPATION.get(occ.group(1).rstrip('.'), occ.group(1).rstrip('.'))
        woman = re.search(r'\bSrpkinja|\b[Ss]tupila|\b[Pp]oginula|\b[Uu]mrla', info)
        rec['occupation'] = 'zemljoradnica' if woman and word == 'zemljoradnik' else word
    b = re.search(rf'(?:\bu\s+(s\.|selu)\s*|\b(u|iz)\s+|(?<=\d\.)\s+)' + PLACE, pre)
    if b:
        rec['_birth'] = (b.group(3), muni, bool(b.group(1)) or not b.group(2), b.group(2) or '')
    if d:
        rest = info[d.end():]
        rec['death_type'] = death_type_from_text(d.group(1).lower()) or 'poginuo'
        rank = re.search(rf'\bkao\s+((?:[{L}]+\.?\s*){{1,4}}?)(?=\s*(?:\d|u\s|na\s|kod\s|pri\s|iz\s|{MONTHS}|[{U}])|,|$)', rest)
        if rank:
            r = rank.group(1).strip()
            rec['rank'] = r[:-1] if r.endswith('.') and len(r.split()[-1]) > 4 else r     # "borac." / "int. bat."
        when = DATE.search(rest)
        if when:
            day, month, mday, mname, year = when.groups()
            rec['death_date'] = (f'{day}. {month}. {year}' if day else f'{mday}. {mname} {year}' if mday else
                                 f'{mname} {year}' if mname else year)
        at = re.search(rf'(?:\bu\s+s(?:elu|\.)\s*|\bu\s+|\bna\s+|\bkod\s+)' + PLACE, rest)   # before the date or after it
        if at:
            rec['_death_at'] = at.group(1)
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    import sys
    sys.path.insert(0, 'scripts')
    from extract_structured_fields import Extractor
    known = top._corpus()[0]

    def nominative(place: str) -> str:
        head, sep, tail = place.partition(' — ')
        forms = [' '.join(c) for c in product(*(Extractor._variants(Extractor, w) for w in head.split()))]
        forms = [f for f in forms if f != head and known[f] > known[head]]
        return (max(forms, key=lambda f: known[f]) if forms else head) + sep + tail

    for s in soldiers:
        box = _box.get((s.get('pdf_file'), s.get('pdf_page'), s.get('pdf_x'), round(s.get('pdf_y') or 0, 1)))
        if box:
            s.update(box)
        at = s.pop('_death_at', None)
        if at:
            s['death_place'] = nominative(at)                                # "na Kozarcu" = Kozarac
        birth = s.pop('_birth', None)
        if birth:
            place, muni, as_printed, prep = birth
            nom = place if as_printed else nominative(place)                 # "u s. Suvaja" as printed, "u Bos. Dubici" = Bos. Dubica
            printed_ok = known[place] >= 3 and not re.search(r'(?:oj|om|em)\b', place)   # "u Mašići": the nominative after "u"
            if nom == place and not as_printed and not printed_ok and re.search(r'(?:u|ju|i|a|e)$', place.split(' — ')[0]):
                continue                                                     # a locative or genitive no unit knows stays in the text
            s['birth_place'] = nom + (', ' + muni if muni and muni not in nom else '')
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path=FALLEN,
        brigade_code=107,
        output_path='website/public/11-krajiska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        extract_fn=extract,
        additional_pdfs=[{'pdf_path': WOMEN, 'start_page': 1, 'end_page': 1}],
        script='latin',
        entry_start_re=re.compile(r'^§[pz]§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
