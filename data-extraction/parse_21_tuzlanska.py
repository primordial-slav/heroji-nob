"""
Parser: 21. tuzlanska istočnobosanska NOU brigada (brigade code 32) — the fallen.

Source: monograph "21. tuzlanska istočnobosanska narodnooslobodilačka udarna brigada" (Univerzal, Tuzla 1988),
        chapter "Spisak poginulih boraca i starješina 21. tuzlanske NOU brigade" (book pp. 389-397)
        znaci.org  →  website/public/pdfs/21-tuzlanska.pdf
Single column, Latin. pp. 1-9 the list, then the index of names, the contents and the imprint.
    ADEMOVIĆ ALIJIN SAJDI, borac, 1920, Valjak - Orahovica, u NOB od 26. 10. 1944, poginuo 10. 2. 1945, ...
    VESIĆ VLAJKOV MILORAD KURJAK, borac, 1913, ...                     (a nickname after the given name)
    CIPURKOVIĆ MUSTAFINA RASEMA. 1927, Tuzla, ...                       (a woman: the father's name is feminine)
SURNAME, the father's name as a possessive (`fathers_name_form: 'possessive'`), the given name; then the duty,
the year of birth and the birthplace. An entry's first line is indented ~30pt.
"""
import json
import re
from collections import Counter, defaultdict

from _margin_entries import fix_caps_head, lone_names_to_given
from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser, title_case

MARK = '⁣'
U = 'A-ZČĆŽŠĐ'
_margin: dict = defaultdict(lambda: 1e9)


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        if len(ln['text'].strip()) > 20:                      # body lines, not page numbers
            key = (ln.get('file'), ln['page'])
            _margin[key] = min(_margin[key], ln['x'])


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or (ln['page'] == 1 and ln['y'] < 150):   # page numbers, the title
        return False
    if re.match(r'^\d+\*\s+21\. tuzlanska', t):                    # the printer's signature: "26* 21. tuzlanska NOU brigada"
        return False
    t = re.sub(r'(?<=\d)[„^](?=\s?\S)', ', ', t).replace(',  ', ', ')          # "1945„Đevanje", "1945^ od"
    t = fix_caps_head(t).translate(str.maketrans('äàèìòù', 'aaeiou'))            # "zämjenik"
    t = re.sub(r'\bBri gad', 'Brigad', t)
    if ln['x'] > _margin[(ln.get('file'), ln['page'])] + 10 and re.match(rf'^[{U}]{{2,}}', t):
        t = re.sub(r'^(\S+)', r'\1' + MARK, t, count=1)
    ln['text'] = t
    return True


POSSESSIVE = r'(?:OV|EV|IN|OVA|EVA|INA)'
_first_names: Counter = Counter()


def _is_fragment(tok: str) -> bool:
    """A piece of a name the OCR split off: "SA VIĆ", "MARINKO VIĆ", "ŽIVO RA DO V", "ŠEFKIJ IN" (not a short
    name such as VUK or the nickname POP)."""
    return bool(re.fullmatch(rf'[{U}]{{1,2}}|V?IĆ', tok))


def parse_entry(text: str) -> dict:
    """SURNAME [FATHER'S | F.] GIVEN [NICK], duty, year, birthplace, ... — the name ends at a comma or at a full
    stop after a caps word ("RASEMA. 1927")."""
    text = text.replace(MARK, '')
    text = re.sub(rf'^((?:[{U}]+ ){{2,3}}[{U}]+) [{U}]\.\s(?=[a-z])', r'\1, ', text)   # "LJUBISA V. borac"
    end = re.search(rf',|(?<=[{U}]{{2}})\.\s', text)
    head, bio = (text[:end.start()], text[end.end():].strip()) if end else (text, '')
    note = []
    nick = re.search(r'\s+zvani\s+(.+)$', head)                  # "MIRKO zvani KRAJIŠNIK": no surname
    if nick:
        note.append('zvani ' + title_case(nick.group(1)))
        head = head[:nick.start()]
    head = re.sub(rf'^([{U}]+IĆ)([{U}]{{3,}}{POSSESSIVE})\b', r'\1 \2', head)     # "MILJANOVIĆILIJIN"
    toks = [t.replace("'", '') for t in head.split()]
    i = 1
    while i < len(toks):
        if _is_fragment(toks[i]):
            toks[i - 1:i + 1] = [toks[i - 1] + toks[i]]
        else:
            i += 1
    if len(toks) > 1 and _is_fragment(toks[0]):
        toks[0:2] = [toks[0] + toks[1]]
    for i in range(len(toks) - 1, 1, -1):                        # "RISTIĆ STOJ ANOV ČEDOMIR"
        if re.fullmatch(rf'[{U}]{{1,2}}{POSSESSIVE}', toks[i]) and not re.search(rf'{POSSESSIVE}$', toks[i - 1]):
            toks[i - 1:i + 1] = [toks[i - 1] + toks[i]]
    if len(toks) == 2 and re.fullmatch(rf'[{U}]+{POSSESSIVE}[{U}]{{3,}}', toks[1]):   # "ŽIVOJINOVSTANOJE"
        m = max((m for m in re.finditer(POSSESSIVE, toks[1]) if _first_names[title_case(toks[1][m.end():])] >= 5),
                key=lambda m: _first_names[title_case(toks[1][m.end():])], default=None)
        if m:
            toks[1:2] = [toks[1][:m.end()], toks[1][m.end():]]
    if nick and len(toks) == 1:                                   # lone_names_to_given makes it the given name
        return _record(toks[0], '', '', '; '.join(note + ([bio] if bio else [])))
    last, rest = (toks[0] if toks else ''), toks[1:]
    if len(rest) >= 2 and re.search(r'IĆ$', rest[0]):             # "BJELIĆ NIKOLIĆ BOŽIDAR": a double surname
        last = last + '-' + rest.pop(0)
    father = ''
    if len(rest) >= 2:
        father = rest.pop(0).rstrip('.')
    if len(rest) > 1:                                         # "MILORAD KURJAK"
        note.append('zvani ' + ' '.join(title_case(w) for w in rest[1:]))
    info = '; '.join(note + ([bio] if bio else []))
    return _record(last, rest[0] if rest else '', father, info)


def birth_years(soldiers: list[dict]) -> list[dict]:
    """The year after the duty is the year of birth ("borac, 1920, Valjak"); a year after the enlistment or the
    death is not ("zamjenik komandanta bataljona, poginuo 16. 11. 1944")."""
    for s in soldiers:
        info = s['additional_info']
        m = re.search(r'\b(1[89]\d\d)\b', info)
        if m and not s.get('birth_year') and not re.search(r'pogin|umr|nesta|strijelj|NOB|Brigad|\bod\b', info[:m.start()]):
            s['birth_year'] = m.group(1)
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', 'tuzlanski-odred-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    return birth_years(lone_names_to_given(repair_lj_ocr(restore_diacritics(soldiers)), *name_counts()))


if __name__ == '__main__':
    _first_names.update(name_counts()[0])
    run_parser(
        pdf_path='website/public/pdfs/21-tuzlanska.pdf',
        brigade_code=32,
        output_path='website/public/21-tuzlanska-soldiers.json',
        start_page=1,
        end_page=9,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        prepare_fn=prepare,
        post_fn=post,
    )
