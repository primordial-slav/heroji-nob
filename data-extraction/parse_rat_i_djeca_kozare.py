"""
Dragoje Lukić, *Rat i djeca Kozare* (znaci.org 00001/106, the chapter "VII - Pali kao borci narodnooslobodilačkog rata",
106_8.htm, book pp. 376-382; a web page, no scan): the 370 Kozara children under fifteen who fell as fighters, by
opština (Banja Luka, Bosanska Dubica, Bosanska Gradiška, Bosanski Novi, Laktaši, Prijedor, Srbac, each heading with
its count), a line each:
    "Bundalo M. Bogdan, Banja Luka, 1927-1944."   (surname, the father's initial, given name, village, born-fell)
The page keeps znaci's typing slips ("M.Simo", "Milorad.Gornji Podgradci", "Kos. V. Sveto", a comma lost before the
village) and the book's page marks ("{378}"), which may break an entry in two.
Output: data-extraction/znaci/rat-i-djeca-kozare-entries.json, IDs 9050xxxxxx; each entry links the page
(`source_url`) and names the book's page (`source_page`).
Usage: python data-extraction/parse_rat_i_djeca_kozare.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
SRC = HERE / 'sources' / 'rat-i-djeca-kozare-106_8.htm'          # https://znaci.org/00001/106_8.htm
URL = 'https://znaci.org/00001/106_8.htm'
OUT = HERE / 'znaci' / 'rat-i-djeca-kozare-entries.json'
PREFIX = '9050'
TITLE = 'Pali kao borci narodnooslobodilačkog rata (Rat i djeca Kozare)'
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
ENTRY = re.compile(rf'^(?P<last>[{U}][{L}]+(?:-[{U}][{L}]+)?)\.?\s+(?:(?P<father>[{U}](?:[{L}])?)\.\s*)?'
                   rf'(?P<first>[{U}][{L}]+)[,.]?\s*(?P<village>[{U}][^,]*?),\s*(?P<by>1[89]\d\d)\s*-\s*(?P<dy>19[34]\d)\.?$')


def lines() -> list[tuple[int, str]]:
    """The list's lines with the book page each stands on; an entry the page mark broke in two is joined"""
    text = re.sub(r'<[^>]+>', ' ', html.unescape(SRC.read_text(encoding='utf-8'))).replace('\r', '')
    text = text[re.search(r'PALI BORCI NARODNOOSLOBODILAČKOG RATA\s*\n', text).start():text.rindex('Sadržaj')]
    out, page, carry = [], 377, ''
    for raw in text.split('\n'):
        t = re.sub(r'\s+', ' ', raw).strip()
        m = re.match(r'^\{(\d+)\}\s*', t)
        if m:
            page, t = int(m.group(1)), t[m.end():]
        if not t:
            continue
        if carry:
            t, carry = carry + ' ' + t, ''
        if re.search(r',$|\s[A-ZČĆŽŠĐ]\.$', t) and not re.search(r'\d{4}\.?$', t):      # "Pajić S. Teodor," / "Popović M."
            carry = t
            continue
        out.append((page, t))
    return out


def main() -> None:
    entries, opstina, counts, said = [], '', Counter(), {}
    for page, t in lines():
        m = re.fullmatch(r'OPŠTINA (.+)', t)
        if m:
            opstina = ' '.join(w.capitalize() for w in m.group(1).split())
            continue
        m = re.fullmatch(r'(\d+) poginulih', t)
        if m:
            said[opstina] = int(m.group(1))
            continue
        if t.startswith('PALI BORCI'):
            continue
        # znaci's slips: no space after the initial or the comma, a full stop for a comma ("Milorad.Gornji")
        fixed = re.sub(r'(?<=[A-ZČĆŽŠĐ]\.)(?=[A-ZČĆŽŠĐ])', ' ', t)
        fixed = re.sub(rf'(?<=[{L}])[.,](?=[{U}])', ', ', fixed)
        fixed = re.sub(rf'^([{U}][{L}]+)\.\s', r'\1 ', fixed)                               # "Kos. V. Sveto"
        e = ENTRY.match(fixed)
        if not e:
            # the comma lost before the village: "Vukelja D. Nikola Donja Dragotinja, 1927-1943."
            e = ENTRY.match(re.sub(rf'^([{U}][{L}]+\s+[{U}]\.\s*[{U}][{L}]+)\s+(?=[{U}])', r'\1, ', fixed))
        if not e:
            print(f'  not read: {t!r}')
            continue
        n = len(entries) + 1
        counts[opstina] += 1
        village = e.group('village').strip()
        entries.append({
            'soldier_id': f'{PREFIX}{n:06d}', 'name': f"{e.group('last')} {e.group('first')}",
            'last_name': e.group('last'), 'also': [], 'first_name': e.group('first'), 'nick': '',
            'fathers_name': (e.group('father') + '.') if e.group('father') else '',
            'birth_year': e.group('by'), 'death_year': e.group('dy'),
            'born_in': village if village == opstina else f'{village}, {opstina}',
            'additional_info': f'{TITLE}, opština {opstina}: {t}', 'list': TITLE,
            'source_url': URL, 'source_page': page})
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(entries)} fallen children -> {OUT.relative_to(HERE.parent)}')
    for o, n in said.items():
        print(f'  {o}: {counts[o]} read, the book says {n}' + ('' if counts[o] == n else '  <-- differs'))


if __name__ == '__main__':
    main()
