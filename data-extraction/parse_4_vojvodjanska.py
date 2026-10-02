"""
Parser: 4. vojvođanska NOU brigada (brigade code 76).

Source: Špiro Lagator, "Četvrta vojvođanska brigada" (znaci.org 00001/230_12.pdf, its pages 24-77)
        →  website/public/pdfs/4-vojvodjanska.pdf (book pp. 281-334):
    pp. 1-31    "Spisak pripadnika 4. brigade na dan 7. oktobra 1943." (the day it was formed), entries end with ";"
                    Агбаба Милан, земљорадник, рођен 1918. у Карађорђеву (Банат), у НОВ од 1943, десетар, погинуо;
    pp. 32-54   "Spisak poginulih i umrlih od 27. 9. 1943. do 1. 3. 1946."
                    Андрић Јелица, домаћица, рођена 1925, Павина Глава, водник, погинула 14. IV 1944. у З. Гора
Cyrillic, one column, a hanging indent; the father, where given, between the surname and the given name, as an
initial or a name ("Аћимовић Б. Саво", "Андрић Миле Сава"). Footnotes at a page's foot are left out.
"""
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, cyrillic_to_latin, repair_cyrillic_ocr, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
MEMBERS_TO = 31
_starts: dict = {}
_note: dict = {}


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _starts.setdefault(ln['page'], []).append((ln['y'], ln['x']))


def margin(ln: dict) -> float:
    """The leftmost x that three lines within 60 pt share: a block pasted further right has its own (p. 49)."""
    xs = sorted(x for y, x in _starts.get(ln['page'], []) if abs(y - ln['y']) <= 60)
    for x in xs:
        if sum(1 for o in xs if abs(o - x) <= 3) >= 3:
            return x
    return xs[0] if xs else ln['x']


# two entries the text layer interleaves with the line under them (p. 52), typed from the page image
TYPED = {(52, 268): 'Шот Лајош, ратар, рођен 1916, Пећир — Бачка, погинуо 16. IV 1945. у с. Феричанци',
         (52, 482): 'Видинки Марко, писар, рођен 1925, Деч — Срем, погинуо 18. 1944. у с. Стублини'}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    typed = next((v for (pg, y), v in TYPED.items() if pg == ln['page'] and abs(ln['y'] - y) < 3), None)
    if typed:
        t = cyrillic_to_latin(typed)
    m = margin(ln)
    if re.match(rf'^\d[\d,.]*\s+[{U}][{L}]*\s+[{L}]', t) and ln['x'] > m + 8 and ln['y'] > 250:   # "1,4 Spisak je ...", "185 U spisak": a footnote
        _note[ln['page']] = ln['y']
    if ln['page'] in _note and ln['y'] >= _note[ln['page']] - 1:
        return False
    if re.fullmatch(r'[\d\W]{1,6}', t) or re.match(r'^(?:S ?P ?I ?S ?A ?K|PRIPADNIKA 4|POGINULIH I UMRLIH)', t):
        return False
    if ln['x'] <= m + 5 and re.match(rf'^[{U}][{L}]', t):
        t = ('§s§ ' if ln['page'] <= MEMBERS_TO else '§p§ ') + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    fell = text.startswith('§p§')
    text = re.sub(r'^§[sp]§\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', text)               # a word broken at the line's end
    text = re.sub(r'\brođvn\b', 'rođen', text).strip().rstrip(';').strip()
    text = re.sub(r'^(\S+)\s+[—–-]\s+', r'\1-', text)                          # "Kepčija — Marković Sofija"
    text = re.sub(r'^(\S+)-(?=ć\b)', r'\1', text)                             # "Stoji-ć"
    text = re.sub(r'^(\S+?[a-zčćžšđ])[NK](?=\s+[A-ZČĆŽŠĐ])', r'\1ć', text)       # "JovanoviN", "StaisavljeviK": Ћ
    notes = []
    br = re.match(r'^(\S+)\s+\(([^)]+)\)\s+', text)                           # "Savatović (Stefanović) Rade Smilja"
    if br:
        notes.append('ili ' + br.group(2))
        text = br.group(1) + ' ' + text[br.end():]
    # the name: capitalized words and initials, up to a comma, a full stop, or the first word of the bio
    m = re.match(rf'^((?:[{U}][{L}]+(?:-[{U}][{L}]+)?|[{U}]{{1,2}}[{L}]?\.)(?:\s+(?:[{U}][{L}]+|[{U}][{L}]?\.))*)[.,]?\s*(.*)$', text)
    head, rest = (m.group(1), m.group(2)) if m else (text, '')
    if re.match(r'^(?:iz|rođen[a]?|u)$', head.split()[-1] if head.split() else ''):
        head = ' '.join(head.split()[:-1])
    toks = head.split()
    if toks and toks[-1] in ('Iz', 'Rođen', 'Rođena'):
        rest = toks.pop().lower() + ' ' + rest
    last = re.sub(r'N$', 'ć', toks[0]) if toks else ''                         # "JovanoviN": a final Ћ read as N
    father, given = '', ' '.join(toks[1:])
    if len(toks) >= 3:                                                       # "Aćimović B. Savo", "Andrić Mile Sava"
        father, given = toks[1], toks[2]
        notes += ['zvani ' + ' '.join(toks[3:])] if len(toks) > 3 else []   # "Milanović R. Zdravko Taga"
    rec = _record(last, given, father, '; '.join(notes + ([rest.strip()] if rest.strip() else [])))
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)\b', rest)
    if y:
        rec['birth_year'] = y.group(1)
    if fell:
        rec['death_type'] = 'umro' if re.search(r'\bumr(?:o|la)\b', rest) and not re.search(r'\bpogin', rest) else 'poginuo'
    return rec


def birthplaces(soldiers: list[dict]) -> list[dict]:
    """The members' list gives the village in the locative with its region ("rođen 1918. u Karađorđevu (Banat)"),
    the list of the fallen in the nominative ("Kruščica — Banat"): a member's village takes the nominative the
    fallen list prints, else the declension rules of parse_19_srpska; written "Karađorđevo, Banat"."""
    from parse_19_srpska import _adjective, _noun_forms
    places = Counter()                                                       # the other units' birthplaces
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != '4-vojvodjanska-soldiers.json':
            for r in json.loads(f.read_text(encoding='utf-8')):
                for p in re.split(r',\s*', r.get('birth_place') or ''):
                    places[p] += 1
    printed = Counter()
    for s in soldiers:
        m = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?,?\s+)?([{U}][^,—]*?)\s+—\s+([{U}]\w+)', s['additional_info'])
        if m:
            printed[m.group(1).strip()] += 1
    for s in soldiers:
        m = re.search(rf'\brođen[a]?\s+(?:1[89]\d\d\.?\s+)?u\s+([{U}][^,(;]*?)\s*\(([^)]+)\)', s['additional_info'])
        if not m:
            continue
        words = m.group(1).split()
        nouns = _noun_forms(words[-1])
        if re.search(r'[^aeiou][kc]u$', words[-1]):                           # "Laćarku" = Laćarak
            nouns.append(words[-1][:-2] + 'a' + words[-1][-2])
        cands = [' '.join([_adjective(a, n) for a in words[:-1]] + [n]) for n in nouns]
        seen = [c for c in cands if printed[c]]
        known = [c for c in cands if places[c] >= 3]
        village = (max(seen, key=lambda c: printed[c]) if seen else cands[0] if places[cands[0]] or not known
                   else max(known, key=lambda c: places[c]))                  # "Surčinu" = Surčin, not Surčino
        s['birth_place'] = f'{village}, {m.group(2).strip()}'
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-vojvodjanska.pdf',
        brigade_code=76,
        output_path='website/public/4-vojvodjanska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§[sp]§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=lambda soldiers: birthplaces(repair_cyrillic_ocr(soldiers)),
    )
