"""
Parser: Karlovačka udarna brigada (brigade code 94).

Source: Josip Lulik Pepo, Đuro Zatezalo, "Karlovačka udarna brigada" (znaci.org 00003/546.pdf, its pages 378-413,
        book pp. 379-414)  →  website/public/pdfs/karlovacka.pdf. Latin, two columns, numbered entries, two lists:
    pp. 1-21    "Popis boraca i rukovodilaca Karlovačke brigade na dan formiranja u Hrašću 5. ožujka 1944." (640),
                the father as an initial:
                    2. ANTONAC M. MATO, 1922, Veliki Modruš Potok, Netretić. Stupio u NOV 3. 3. 1944, borac 4. bat.
    p. 22       the authors' note on the list's sources (not read)
    pp. 23-36   "Popis poginulih boraca i rukovodilaca Karlovačke udarne brigade 34. udarne divizije NOVJ" (337),
                the father's name in the genitive:
                    20. BERT Janka IVAN, 1904, Ribnik. Stupio u NOV 1. 8. 1944, borac 4. bat. Poginuo ...
The same archive's form as the 8. kordunaška division's list, and the same scan faults: carons lost in the capitals
("BABIC"), I read as l ("BANJAVClC"), names spaced apart ("BELA VIC"), stray small letters ("AiNlTUN"). Names are
put right from the spellings the other units print (parse_8_kordunaska_divizija's helpers). Some entry numbers sit
on their own line beside the name; they are put back before the entries are read.
"""
import glob
import json
import re
from collections import Counter, defaultdict
from itertools import product

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, death_type_from_text, run_parser
from _slovene_lists import columns_reader

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FALLEN_FROM = 23
NUMBER = r'^(?![\dS]{4})[!\d](?:[\d:.]|S(?=\d)){0,3}[.,:]*\s*'                 # "13:5.", "2S6.", "!92.", "3.28."
INITIAL = re.compile(r'(?:[A-ZČĆŽŠĐ]|LJ|Lj|NJ|Nj|DŽ|Dž|Ig|g)\.')
TEXT_FIXES = [('BLA2', 'BLAŽ'), ('SEKULICJ.', 'SEKULIC J.'), ('J.VILKO', 'J. VILKO'), ('GRDASIĆ Josipa,', 'GRDASIĆ Josipa'),
              ('SLANAC Antuna,', 'SLANAC Antuna'), ('KRANJCE,C', 'KRANJCEC'), ('RA TKA .7', 'RATKAJ'), ('MiALOVI-Ć', 'MIHALOVIĆ'),
              ('R.OZlĆ', 'ROZIĆ'), ('TOOVIilČIĆ', 'TOMIČIĆ'), ('SläKETA', 'SEKETA'), ('PALČIĆ Tome SLAVKA', 'PALČIĆ Tome SLAVKA,'),
              ('MARI Cl C', 'MARIČIĆ'), ("BRKAS'IC", 'BRKAŠIĆ'), ("PRI'NC", 'PRINC'), ('SIAMO VOJSKA', 'SAMOVOJSKA'),
              ('SAMO VOJSKA', 'SAMOVOJSKA'), ('ZuZlNJAK', 'ŽUŽINJAK'), ('PAVLINlIČ', 'PAVLINIĆ'), ('ŠUPE-LJAK', 'ŠUPELJAK'),
              ('DVGRABIC', 'DVORABIĆ'), ('ŠLA>T', 'ŠLAT'), ('Vilimai', 'Vilima')]   # misreadings (the order and the other list tell)


def corpus() -> None:
    """Every spelling of a name the other units print (k8.known, k8.respell read it)."""
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if fn.replace('\\', '/').endswith('/karlovacka-soldiers.json'):
            continue
        for s in json.load(open(fn, encoding='utf-8')):
            for f in k8._spell:
                if s.get(f):
                    k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def prepare(lines: list[dict]) -> None:
    """An entry number the text layer set on a line of its own ("60.") goes back before its name's line."""
    for ln in lines:
        if re.fullmatch(r'\d{1,3}[.,]?', ln['text'].strip()):
            near = [o for o in lines if o is not ln and o['page'] == ln['page'] and abs(o['y'] - ln['y']) < 7
                    and 0 < o['x'] - ln['x'] < 25 and re.match(rf'^[{U}]{{2,}}', o['text'])]
            if near:
                name = min(near, key=lambda o: abs(o['y'] - ln['y']))
                name['text'] = ln['text'].strip().rstrip('.,') + '. ' + name['text']
                ln['text'] = ''


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if not t or ln['page'] == 22 or re.match(r'^\d*\s*Karlova[čc]ka udarna brigada$', t) or re.fullmatch(r'[\d\W]{1,5}', t):
        return False                                                         # the authors' note, running heads, page numbers
    if ln['page'] in (1, FALLEN_FROM) and ln['y'] < 300 and not re.match(r'^\d', t):
        return False                                                         # the lists' headings
    for bad, good in TEXT_FIXES:
        t = t.replace(bad, good)
    t = re.sub(r"^[,.'\s]+(?=\d)", '', t)                                     # ", 38. BENKOVIĆ"
    t = re.sub(r'^[LlI](?=\d\d[.,])', '1', t)                                  # "L00. DEJANOVlC" = 100
    if re.match(NUMBER + rf'[{U}](?:[{U}lui]|\.[{U}])', t) and not re.match(r'^\d+\.\s*(?:bat|brig|[IVX]+\.)', t):
        t = '§k§ ' + t
    ln['text'] = t
    return True


def fix_caps(w: str, field: str) -> str:
    """A name in capitals with the scan's small letters in it: "l" is I or a speck, "i" a speck or I ("AiNlTUN" =
    ANTUN, "BANJAVClC" = BANJAVCIC); the reading the corpus knows, else l = I and i dropped."""
    w = k8.caps_word(w) if not re.search(r'[a-zäö]', w.replace('l', '')) else w
    small = [i for i, c in enumerate(w) if c.islower()]
    if not small:
        return w
    if len(small) <= 4:
        best, n = None, 0
        for choice in product(*(('I', '') if w[i] in 'li' else ('',) for i in small)):
            v = list(w)
            for i, c in zip(small, choice):
                v[i] = c
            v = ''.join(v)
            if k8.known(v, field) > n:
                best, n = v, k8.known(v, field)
        if best:
            return best
    return re.sub(r'[a-z]', '', w.replace('l', 'I'))


def parse(text: str) -> dict:
    text = re.sub(r'^§k§\s*', '', text)
    for a, b in TEXT_FIXES:
        text = text.replace(a, b)
    text = re.sub(NUMBER + rf'(?=[{U}])', '', text)
    head = re.split(r',|\(|\s(?=1[89]\d\d\b)', text, 1)[0]
    info = text[len(head):].lstrip(',').strip()
    nick = re.match(r'\(([^)]+)\),?\s*', info)                               # "TABOR I. RAFAEL (Rafko), 1921"
    if nick:
        info = info[nick.end():]
    head = re.sub(rf'(?<=[{U}])\.(?=[{U}])', '', head)                         # "LOV.RINIC"
    head = re.sub(rf'^([{U}]{{3,}})([{U}])\.(?=\s)', r'\1 \2.', head)          # "MIHALICJ. DRAGUTIN"
    words = [w.rstrip('.') if re.fullmatch(rf'[{U}][{L}]{{2,}}\.', w) else w for w in head.split()]   # "Janka. DRAGUTIN"
    at = next((i for i, w in enumerate(words) if i and (INITIAL.fullmatch(w) or re.fullmatch(rf'[{U}][{L}]+', w))), None)
    if at is not None:
        father = words[at]
        father = father.upper() if INITIAL.fullmatch(father) and len(father) > 2 and father[1].isupper() else father
        father = {'g.': '', 'Ig.': 'Ig.'}.get(father, father)
        if father.endswith('ia') and k8.known(father[:-2] + 'la', 'middle_name') > 20 * k8.known(father, 'middle_name'):
            father = father[:-2] + 'la'                                      # "Pavia" = Pavla
        last = k8.join_parts([fix_caps(w, 'last_name') for w in words[:at]], 'last_name')
        given = k8.join_parts([w if re.fullmatch(rf'[{U}][{L}]+', w) else fix_caps(w, 'first_name')
                               for w in words[at + 1:]], 'first_name')       # "BENKOVIC Mije Franjo"
    else:
        caps = [fix_caps(w, 'last_name' if i == 0 else 'first_name') for i, w in enumerate(words)]
        father = ''
        if len(caps) >= 3 and (k8.known(caps[0] + caps[1]) or min(len(caps[0]), len(caps[1])) <= 3):
            caps = [caps[0] + caps[1]] + caps[2:]                            # "BOROV AC"
        last, given = (caps[0], ' '.join(caps[1:])) if caps else ('', '')
    notes = ['zvani ' + nick.group(1).strip()] if nick else []
    rec = _record(last, given.title(), father, '; '.join(notes + [info]))
    y = re.match(r'[.,]?\s*(1[89]\d\d)\b', info)
    if y:
        rec['birth_year'] = y.group(1)
    parts = [p.strip() for p in re.split(r',\s*|\.\s+', re.sub(r'^[.,]?\s*1[89]\d\d[,.]?\s*', '', info))]
    places = []
    for p in parts[:2]:
        if re.fullmatch(rf'(?:[{U}][{L}]*\.?|[{L}]+)(?:\s+(?:[{U}]?[{L}]+\.?|na|kod))*', p) and \
                not re.match(r'(?:Stupi|Učesnik|Pogin|Umr|Ranjen|U\s)', p) and p[0].isupper():
            places.append(p)
        else:
            break
    if places:
        rec['birth_place'] = ', '.join(places)
    rec['death_type'] = death_type_from_text(info)
    if rec['death_type'] in ('', 'zarobljen'):
        fate = re.search(r'(?i)\b(?:ubijen|strijeljan|streljan|umro|umrla|poginu)', info)
        rec['death_type'] = ('streljan' if fate and 'ljan' in fate.group(0) else 'umro' if fate and fate.group(0).lower().startswith('umr')
                             else 'poginuo' if fate else rec['death_type'])
    return rec


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/karlovacka.pdf',
        brigade_code=94,
        output_path='website/public/karlovacka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='two_column',
        extract_fn=lambda p, s, e: columns_reader(2)(p, s, e),
        script='latin',
        entry_start_re=re.compile(r'^§k§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=k8.post,
    )
