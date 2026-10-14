"""
*Sanitetska služba u NOR-u 1941-1945, zbornik radova*, knjiga IV (znaci.org 00001/199, the chapter 199_15.htm, a web
page with no scan, kept in data-extraction/sources/sanitetska-sluzba-lekari-199_15.htm): "Spisak poginulih lekara",
the 213 doctors who lost their lives in the war, numbered, a short bio each:
    "7. BARUH SAMUEL, iz Bosanske Gradiške, rođen 1898. u Bugojnu. U NOVJ septembra 1942. Lekar u Centralnoj bolnici
     pri VŠ-a. Poginuo 10. juna 1943. na Vučevu."
a book across units. The list counts doctors who worked for the movement and were killed as civilians ("Saradnik
NOP-a od 1941. Uhapšena od ustaša ..."): only those the bio puts in the army go in, by the rule for mixed lists
(NOVJ, the partisans, a unit, a hospital of the army, an army duty). An entry gives its unit where the site has it
(`units`: the Centralna bolnica, the Vrhovni štab, an odred), the birth year and the year of death for the matcher.
Output: data-extraction/znaci/sanitetska-sluzba-lekari-entries.json, IDs 9057xxxxxx by the entry's place in the list
(the book numbers two entries 151), each with
`source_url`.
Usage: python data-extraction/parse_sanitetska_lekari.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
SRC = HERE / 'sources' / 'sanitetska-sluzba-lekari-199_15.htm'      # https://znaci.org/00001/199_15.htm
URL = 'https://znaci.org/00001/199_15.htm'
BOOK = 'sanitetska-sluzba-lekari'
OUT = HERE / 'znaci' / f'{BOOK}-entries.json'
PREFIX = '9057'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
TITLE = 'Spisak poginulih lekara (Sanitetska služba u NOR-u, knj. IV)'
# in the army: NOVJ, the partisans, a unit or an army hospital, an army duty
ARMY = re.compile(r'\bNOVJ\b|\bNOV\b|partizan|odred|brigad|divizij|korpus|bataljon|\bčet[ei]\b|bolnic|VŠ|Vrhovn\w+ štab'
                  r'|štab|sanitet|referent|NOP odred|ofanziv|jedinic', re.I)
CIVILIAN = re.compile(r'^Saradnik NOP-a')
# bios whose only sign of the army is a word in passing, read one by one: the town hospital of Karlovac, doctors
# killed for helping or hiding partisans, the underground's medical organizer, a prisoner the partisans freed
NOT_ARMY = {38, 58, 80, 84, 92, 117, 128, 132, 183, 190, 201, 209}
UNITS = [(r'Centraln\w+ bolnic', 117), (r'Vrhovn\w+ štab|\bVŠ\b', 112), (r'Čačansk\w+ (?:partizansk\w+ )?odred', 126),
         (r'Užičk\w+ (?:partizansk\w+ )?odred', 26), (r'Kalničk\w+ (?:partizansk\w+ )?odred', 58),
         (r'Prv\w+ proletersk\w+ brigad', 1), (r'Drug\w+ proletersk\w+ brigad', 39)]


def entries() -> list[tuple[int, str]]:
    t = html.unescape(re.sub(r'<[^>]+>', ' ', SRC.read_text(encoding='utf-8')))
    t = re.sub(r'\s+', ' ', t)
    t = t[t.index('Spisak poginulih lekara:'):]
    t = re.sub(r'\s*Sadržaj biblioteka\s*$', '', t)
    t = t.replace('MI JATO V', 'MIJATOV').replace('TOMIĆlĆ', 'TOMIČIĆ')  # the OCR broke a name apart, read I as l
    # an entry: its number, then the name in capitals ("Š1MČENKO": the OCR's 1 for I), or the surname in small
    # letters and the given name in capitals ("18. Brežanić CVIJETAN")
    starts = [m for m in re.finditer(rf'(?<=\s)(\d{{1,3}})\.\s+(?=[{U}1][{U}1]|[{U}][{L}]+\s[{U}]{{2}})', t)]
    res = []
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(t)
        res.append((int(m.group(1)), t[m.end():end].strip()))
    return res


def main() -> None:
    raw = entries()
    nos = [n for n, _ in raw]
    print(len(raw), 'numbered entries; missing numbers:', sorted(set(range(1, 214)) - set(nos)),
          'out of order:', [n for i, n in enumerate(nos) if i and n != nos[i - 1] + 1][:10])
    out, left = [], []
    for pos, (n, text) in enumerate(raw, 1):
        text = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'I', text)
        m = re.match(rf'^([{U}][{U}\'-]+(?:\s[{U}][{U}\'-]+)*?|[{U}][{L}]+)\s+(?:[{U}]\.\s+)?([{U}]{{2,}})(?:-([{U}]+))?'
                     rf'(?:\s*\(([^)]*)\))?\s*,?\s*(.*)$', text)
        if not m:
            m2 = re.match(rf'^([{U}]{{2,}})\s*\(ime nepoznato\),\s*(.*)$', text)   # "GANJA (ime nepoznato), Bugarin"
            if m2:
                m = None
                last, given, nick, bio = m2.group(1).capitalize(), '', '', m2.group(2)
            else:
                left.append((n, text[:80]))
                continue
        if m:
            last = '-'.join(w.capitalize() for w in m.group(1).strip().split('-'))
            last = ' '.join(w if '-' in w else w.capitalize() for w in last.split())
            given, nick, bio = m.group(2).capitalize(), (m.group(3) or '').capitalize(), m.group(5)
        bio_body = re.sub(r'^(?:[^.]*?,\s*)?iz [^,.]+[,.]\s*', '', bio)
        if CIVILIAN.search(bio_body) and not re.search(r'\bNOVJ\b|partizan|odred|brigad', bio) or not ARMY.search(bio) \
                or n in NOT_ARMY:
            left.append((n, f'{last} {given}: {bio[:90]}'))
            continue
        born = re.search(r'[Rr]ođen[a]?\s+(?:\d{1,2}\.\s*\w+\s+)?((?:18|19)\d\d)', bio)
        place = re.search(r'[Rr]ođen[a]?\s+[^.]*?(?:18|19)\d\d\.?\s+u\s+([^.,(]+)', bio)
        died = re.search(r'(?:Poginu|[Uu]mr|[Uu]bij|[Ss]trelj|[Ss]trada|[Nn]esta|[Zz]aklan|[Oo]bešen)\w*[^;]{0,60}?(194\d)', bio)
        units = sorted({code for pat, code in UNITS if re.search(pat, bio)})
        out.append({'soldier_id': f'{PREFIX}{pos:06d}', 'name': f'{last} {given}'.strip(), 'last_name': last,
                    'first_name': given, 'nick': nick, 'fathers_name': '', 'birth_year': born.group(1) if born else '',
                    # the birthplace is printed in the locative ("u Bugojnu"), which the matcher would take for
                    # another place: left out, the text has it
                    'born_in': '', 'death_year': died.group(1) if died else '',
                    'units': units, 'no': n, 'additional_info': f'{TITLE}: {n}. {text}',
                    'source_url': URL, 'source_page': None})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(out)} fighters -> {OUT.relative_to(HERE.parent)}; left out {len(left)}:')
    for n, t in left:
        print('  ', n, t)


if __name__ == '__main__':
    main()
