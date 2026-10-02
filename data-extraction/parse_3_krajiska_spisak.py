"""
Parser: 3. Krajiška Proleterska Brigada (brigade code 10) — the roster of everyone who fought in the brigade.

Source: "Treća krajiška brigada — zbornik sjećanja", knjiga 3 (znaci.org 00003/394.pdf), the closing list
        "Spisak boraca III proleterske krajiške brigade koji su se borili u njenom sastavu od 22. 08. 1942. do
        09. 05. 1945. godine" (book p. 579 on)  →  website/public/pdfs/3-krajiska-spisak-boraca.pdf (PDF pages
        580-1074 of the book: pp. 1-2 the editors' note, 3-477 the list, 479-486 "Dopuna spiska boraca",
        487-495 "Prilog spisku boraca — podaci prikupljeni u toku štampanja knjige").
One column, Latin; znaci.org re-typeset the book from its OCR, so the page shows the text layer's errors:
    ADAMOVIĆ Velimira DRAGOLJUB, rod. 1927, Pružatovac, Mladenovac, zemljoradnik, Srbin, u NOB i brigadi od
    10. 10. 1944, borac, umro 1946.
Survivors and the fallen alike: where each came from, the occupation and nationality, when he joined the NOB
and the brigade, his duty, and his fate. This is the unit's third book: its records get IDs from 200001
(the fallen list has 1-, Borci Sutjeske 100001-); the same soldier in the other books is merged
(find_source_duplicates.py).

The OCR spaced out some surnames ("TANASI JEVIĆ Živote MILORAD", "STE VANO VIC Živana ALEKSANDAR"): the caps
words before the father's name are one surname, two whole surnames being a married woman's double one
("PILIPOVIĆ SJERIĆ" → Pilipović-Sjerić). A few entries start mid-line after the previous one's full stop.
"""
import glob
import json
import re
from collections import Counter

from _parser_scaffold import extract_lines_single_column, repair_caps_ocr, repair_lj_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEADINGS = re.compile(r'^(?:DOPUNA SPISKA BORACA|TREĆE PROLETERSKE KRAJIŠKE BRIGADE|P R I L ?OG|'
                      r'SPISKU BORACA TREĆE PROLETERSKE KRAJIŠKE BRIGADE|— Podaci prikupljeni u toku štampanja knjige —|'
                      r'[A-ZČĆŽŠĐ]|LJ|NJ|DŽ)$')
CAPS = re.compile(rf"[{U}][{U}Ö0-9'\-—|]*")
TITLE = re.compile(rf'[{U}][{L}]+\.?')
PARTICLES = {'DE', 'DI', 'DEL', 'DELLA', 'DA', 'DAL', 'LO', 'LA', 'LE'}
SURNAME_END = re.compile(r'(?:IĆ|IC|SKI|SKA|AC|AR|IN|OV|EV|AK|EK|UK|OVA|EVA)$')
# an entry glued to the end of the previous one's line: ". AND'RIJEVIĆ Dragomira CEDOMIR", ". MlClC Mihaila
# ALEKSANDAR,", ". šOBOT Pere ILIJA,", ". KlS MIHAJLO,": a caps surname (OCR l and i inside) and, before the first
# comma, a caps given name
GLUED = re.compile(rf"(?<=\.)\s*(?=\(?[{U}šžčćđ][{U}lIi'\-—(]+[{U}][{U}lIi'\-—]*\s[^,.]{{0,50}}?\b[{U}][{U}lI]{{2,}},)")

_first: Counter = Counter()


def corpus() -> None:
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('3-krajiska-proleterska-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name'].upper()] += 1


def join_surname(parts: list[str]) -> str:
    """Spaced-out caps words of one surname: concatenated, or hyphened when each is a whole surname."""
    out = parts[0]
    for p in parts[1:]:
        if out in PARTICLES:
            out += '-' + p                                                   # DE SANTIS (a space again in post)
        elif (len(out.split('-')[-1]) >= 5 and SURNAME_END.search(out) and len(p.split('-')[0]) >= 5
              and SURNAME_END.search(p.split('-')[0])):
            out += '-' + p                                                   # PILIPOVIĆ SJERIĆ
        else:
            out += p                                                         # TANASI JEVIĆ, STE VANO VIC
    return out


def fix_name(t: str) -> str:
    toks = t.split(' ')
    n = 0
    while n < len(toks) and CAPS.fullmatch(toks[n].rstrip(',')):
        n += 1
        if toks[n - 1].endswith(','):
            break
    clean = lambda w: re.sub(r"['|]", '', w).replace('—', '-').replace('1', 'I').replace('0', 'O').replace('2', 'Ž').replace('Ö', 'Č')
    if n == 0:
        return t
    names = [clean(w) for w in toks[:n]]
    father = n < len(toks) and not toks[n - 1].endswith(',') and TITLE.fullmatch(toks[n]) is not None
    if father and n >= 2:
        names = [join_surname([w.rstrip(',') for w in names])]
    elif not father and n >= 3 and toks[n - 1].endswith(','):
        rest = ''.join(w.rstrip(',') for w in names[1:])
        if len(names[0]) >= 5 and SURNAME_END.search(names[0]) and _first[rest]:
            names = [names[0], rest + ',']                                   # "JOVANOVIĆ DRAGO MIR," → DRAGOMIR
        else:
            names = [join_surname(names[:-1]), names[-1]]
    if father:
        # the given name after the father's: "BRASNIĆ Ive TAD I JA," → TADIJA when the corpus knows it
        k = n + 1
        while k < len(toks) and CAPS.fullmatch(toks[k].rstrip(',')):
            k += 1
            if toks[k - 1].endswith(','):
                break
        given = [clean(w) for w in toks[n + 1:k]]
        if len(given) >= 2 and _first[title(''.join(given).rstrip(','))]:
            given = [''.join(given)]
        if toks[n] == 'Pavia':
            toks[n] = 'Pavla'                                                # OCR for "Pavla"
        return ' '.join(names + [toks[n]] + given + toks[k:])
    return ' '.join(names + toks[n:])


def title(w: str) -> str:
    return w.upper()


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    for ln in extract_lines_single_column(pdf_path, start, end):
        parts = GLUED.split(ln['text'])
        lines.append({**ln, 'text': parts[0]})
        for p in parts[1:]:
            lines.append({**ln, 'text': p})
    return lines


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip().replace('­', '-')
    t = re.sub(rf'^\(?([šžčćđ])(?=[{U}]{{2}})', lambda m: m.group(1).upper(), t)   # "šOBOT", "(LATINOVIC"
    t = re.sub(rf'^\((?=[{U}]{{2}})', '', t)
    t = re.sub(rf"^[{U}][{U}lIi'\-—]*[{U}](?=[\s,])",
               lambda m: m.group(0).replace('l', 'I').replace('i', 'I'), t)     # "KlS", "MILOVANOViC-BANJAC"
    t = repair_caps_ocr(t)
    if ln['page'] <= 2 or HEADINGS.match(t):
        return False
    if re.fullmatch(r'[\W\d]{0,4}|[a-zA-Zä]{1,2}', t):                 # specks: "•", "jä", "n", "T"
        return False
    t = re.sub(rf'^([{U}])\s([{U}]{{3,}}[{U}\s]*?)(?=\s+[{U}][{L}]|\s+[{U}]{{2,}},)',
               lambda m: m.group(1) + m.group(2).replace(' ', ''), t)       # "B RILO VIC IVO" → "BRILOVIC IVO"
    t = re.sub(rf'^([{U}]+),([{U}]+)', r'\1\2', t)                            # "MI,LOVAC"
    t = re.sub(r'\s*—\s*(?=[A-ZČĆŽŠĐ]{2,})', '—', t, count=1) if re.match(rf'^[{U}]{{2,}}\s*—', t) else t
    ln['text'] = fix_name(t)
    return True


BIRTH = re.compile(r'^(?:(?:zvani|ili|rođ\.\s+[A-ZČĆŽŠĐ])[^;]*;\s*)*-?(?:ro[dđ]\.?,?\s*)?(1[89]\d\d)\b')


def restore_parts(name: str) -> str:
    """A double surname's parts get their carons back one by one ("Banovic-Balaban" → Banović-Balaban)."""
    out = []
    for p in name.split('-'):
        options = _last_by_fold.get(_fold(p))
        if options:
            best, n = options.most_common(1)[0]
            if best != p and n >= 0.8 * sum(options.values()):
                p = best
        out.append(p)
    return '-'.join(out)


_FOLD = str.maketrans('čćžšđČĆŽŠĐ', 'cczsdCCZSD')
_fold = lambda s: s.translate(_FOLD)
_last_by_fold: dict = {}


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for f in glob.glob('website/public/*soldiers.json'):
        for s in json.load(open(f, encoding='utf-8')):
            _last_by_fold.setdefault(_fold(s['last_name']), Counter())[s['last_name']] += 1
    for s in soldiers:
        if '-' in s['last_name']:
            s['last_name'] = restore_parts(s['last_name'])
        s['last_name'] = re.sub(r'^(De|Di|Del|Della|Da|Dal|Lo|La|Le)-', r'\1 ', s['last_name'])
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
        m = BIRTH.match(s['additional_info'])
        if m and not s['birth_year']:
            s['birth_year'] = m.group(1)
    return soldiers


if __name__ == '__main__':
    import sys
    corpus()
    out = sys.argv[1] if len(sys.argv) > 1 else 'website/public/3-krajiska-proleterska-soldiers.json'
    run_parser(
        pdf_path='website/public/pdfs/3-krajiska-spisak-boraca.pdf',
        brigade_code=10,
        output_path=out,
        start_page=3,
        end_page=None,
        layout='single',
        script='latin',
        line_filter=keep_line,
        extract_fn=extract,
        post_fn=post,
        id_start=200001,
        keep_other_sources=len(sys.argv) <= 1,
    )
