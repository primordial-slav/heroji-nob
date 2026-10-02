"""
Parser: 8. srpska NOU brigada (brigade code 87).

Source: Petar Damjanov, "8. srpska brigada" (znaci.org 00003/398.pdf, its pages 262-294, book pp. 265-297)
        →  website/public/pdfs/8-srpska.pdf. Cyrillic, one column:
    "Nezaboravnik (Spisak poginulih boraca Osme srpske NOU brigade)", 563 numbered entries, the father between slashes:
        30.ANTIĆ /STANIMIRA/ VLADIMIR, rođen 1924. godine, Pavlovac, Vranje; poginuo 12.04.1945, Batrovci, na reci Bosutu.
        13.ANĐELKOVIĆ JOVAN, iz sela Odrovce, Dimitrovgrad; poginuo 15.12.1944, Sjenica.
Л is read as J1 and З as 3. The parser sets the birthplace (the village and the municipality before the ";"), the
date and the place of death (the first place after the date, where it is printed in the nominative).
"""
import re

from _parser_scaffold import _record, death_type_from_text, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
FIXES = {'ALJOP1A': 'ALJOŠA', 'PETROV11Ć/': 'PETROVIĆ /', 'ST011ŠĆ': 'STOŠIĆ', 'MIL0SAVJBEVIĆ': 'MILOSAVLJEVIĆ'}   # read by the alphabetical order


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    t = re.sub(rf'(?<=[{U}])J1|J1(?=[{U}])', 'L', t).replace('J1', 'L').replace('j1', 'l')   # Л read as J1
    t = re.sub(rf'(?<=\.)3(?=[{U}])|(?<=[{U}])3(?=[{U}])', 'Z', t)            # "153.3LATKOV"
    if ln['page'] == 1 and (ln['y'] < 70 or ln['y'] > 375):
        return False                                                         # the heading, the source note under the list
    if ln['page'] == 33 and ln['y'] > 290:
        return False                                                         # the author's thanks after the list
    if re.fullmatch(r'[\d\W]{1,5}|\W*\w{0,2}\W*', t):
        return False
    for bad, good in FIXES.items():
        t = t.replace(bad, good)
    t = re.sub(r'^[\dOoBbZzIl]{1,4}\s*[.:]\s*(?=[A-ZČĆŽŠĐ]{2})', lambda m: '0. ' if not m.group(0)[0].isdigit() else m.group(0), t)   # "BO.GRGOV" (80.), "ZOb.MIHAJLOVIĆ" (308.), "499:"
    t = re.sub(rf'(?<=[{U}])0|0(?=[{U}])', 'O', t)                            # "ANĐELK0VIĆ"
    t = re.sub(rf'(IĆ)([{U}]\.)', r'\1 \2', t)                                 # "DIMITRIJEVIĆN. SVETOZAR"
    if re.match(rf'^\d+\s*[.:]\s*[{U}]{{2,}}', t):
        t = '§p§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    text = re.sub(r'^§p§\s*\d+\s*[.:]\s*', '', text)
    text = re.sub(r'(?<=[a-zčćžšđ])-\s+(?=[a-zčćžšđ])', '', text)            # "Sinja Gla- va"
    text = re.sub(r'\bna(?=reci\b)', 'na ', text)                              # "Batrovci nareci Bosutu"
    text = re.sub(rf'^([{U}]+IĆ)(?=[{U}]{{3,}})', r'\1 ', text)               # "ANĐELKOVIĆĐORĐE"
    text = re.sub(rf'(?<![{U}])((?![{U}]*IĆ\b)[{U}]{{2,5}}) (J[{U}]+)', r'\1\2', text)   # "STANO JE", "DO JČINA", "STO JANOVIĆ": Ј split off (not "MITIĆ JEVREM")
    text = re.sub(r'(?<=\s)3\.(?=\s)', 'Z.', text)                             # the initial З read as the digit
    m = re.search(r'\s+(?=iz\s+(?:sela\s+)?[A-ZČĆŽŠĐ]|rođen[a]?\s)', text.partition(',')[0])
    if m:
        text = text[:m.start()] + ',' + text[m.start():]                    # "ANTIĆ /ANĐELA/ VASKO iz sela Goločevca"
    head, _, rest = text.partition(',')
    rest = rest.strip()
    notes = []
    father = ''
    q = re.search(r'\s*["„“]([^"“”]+)["“”]', head)                            # "Miloš-Mića "Gočoban""
    if q:
        notes.append('zvani ' + q.group(1).strip().title())
        head = head[:q.start()] + head[q.end():]
    a = re.search(rf'\s+ILI\s+([{U}][{U}{L}-]+)', head)                       # "STOŠIĆ /JANKA/ ILI STOPIĆ MIRKO"
    if a:
        notes.append('ili ' + a.group(1).title())
        head = head[:a.start()] + head[a.end():]
    if head.count('/') == 1:                                                 # a slash lost: "/MILOJA MILAN", "LGOMČE/ BORIVOJE"
        one = re.search(r'/\s*(\S+)\s+(?=\S+$)', head) or re.search(r'\s(\S+)/', head)
        if one:
            f = re.sub(r'^(?:L(?=[a-zčćžšđ])|D"|[^A-ZČĆŽŠĐa-zčćžšđ]+)', '', one.group(1).strip('/'))
            head = head[:one.start()] + f' /{f}/ ' + head[one.end():]
    m = re.search(r'\s*/([^/]+)/\s*', head)
    if m:
        f = m.group(1).strip()
        if re.match(r'(?i)ili\s', f):
            notes.append('ili ' + f[4:].strip().title())                     # "CEPIĆ M. /ILI KONSTANTINA/ MLADEN"
        else:
            father = f.title() if f.isupper() else f                         # "/STANIMIRA/"
        head = head[:m.start()] + ' ' + head[m.end():]
    toks = head.split()
    caps = []
    while toks and re.fullmatch(rf'[{U}]{{2,}}(?:-[{U}]{{2,}})*', toks[0]):
        caps.append(toks.pop(0))
    if toks and re.fullmatch(rf'(?:[{U}]|Lj|Nj|Dž|LJ|NJ|DŽ)\.', toks[0]):
        father = father or toks[0].title()                                   # "JANIĆ V. BOŽIDAR", "Lj. ČEDOMIR"
        toks.pop(0)
    given_rest = ' '.join(toks)
    if len(caps) >= 2 or (caps and given_rest):
        last, given = caps[0], ' '.join(caps[1:] + ([given_rest] if given_rest else []))
    elif caps and re.search(r'državljanin|Rus\b', rest):
        last, given = '§', caps[0]                                           # "PETAR, državljanin SSSR-a": one name
        if father:
            notes.append('zvani ' + father)                                  # "ALJOŠA /RUS/"
            father = ''
    elif caps and father:
        last, given = '§', caps[0]                                           # "ALJOŠA /RUS/": a given name and a nickname
        notes.append('zvani ' + father)
        father = ''
    else:
        last, given = (caps[0] if caps else ''), given_rest
    rec = _record(last, given.title() if given.isupper() else given, father, '; '.join(notes + ([rest] if rest else [])))
    y = re.search(r'rođen[a]?\s+(1[89]\d\d)', rest)
    if y:
        rec['birth_year'] = y.group(1)
    b = re.match(rf'(?:rođen[a]?\s+[^,;]*?(?:godine)?,\s*|iz\s+(?:sela\s+)?)([{U}][^,;]*?)(?:,\s*([{U}][^,;]*?))?\s*[;,]', rest)
    if b:
        rec['birth_place'] = ', '.join(p.strip() for p in b.groups() if p)
    dt = death_type_from_text(rest)
    rec['death_type'] = 'umro' if re.search(r'\bumr(?:o|la)\b', rest) and not re.search(r'\bpoginu', rest) else (dt or 'poginuo')
    d = re.search(rf'(?:poginu\w+|umr\w+)\s+(\d{{1,2}}\.\s*\d{{1,2}}\.\s*19\d\d)\.?,?\s*([{U}][{L}]+(?:\s+[{U}{L}][{L}]+)?)?(?=\s*[,.;]|\s+(?:kod|na|u)\s|$)', rest)
    if d:
        rec['death_date'] = re.sub(r'\s+', '', d.group(1))
        if d.group(2):
            rec['death_place'] = d.group(2).strip()
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s['last_name'] == '§':                                            # a soldier known by one name
            s['last_name'] = ''
            s['full_name'] = s['first_name']
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/8-srpska.pdf',
        brigade_code=87,
        output_path='website/public/8-srpska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§p§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=post,
    )
