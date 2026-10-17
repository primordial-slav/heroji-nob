"""
The posts a unit's own entries name (local only, like the map scripts; kept out of git by .git/info/exclude), for the
unit overview page /jedinica/<id>: who was komandant, komesar, their deputies, načelnik štaba and the other officers of
the brigade, of each battalion, company and platoon, with the time the entry gives for the post ("od 19. februara do
24. oktobra 1944"), the fate (death_type, death_date) and the narodni heroj mark. Only the unit's own entry
(additional_info) is read: entries of other units linked to a record speak of other brigades.

    python scripts/make_unit_overview.py prva-licka-brigada
writes website/app/(sr)/jedinica/_data/<id>.posts.json. The page puts these beside what it takes from the unit's book
by hand (the staffs on a day, the narrative's changes) in _data/<id>.ts.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))


MONTHS = {'januar': 1, 'februar': 2, 'mart': 3, 'april': 4, 'maj': 5, 'jun': 6, 'jul': 7, 'avgust': 8, 'august': 8,
          'septembar': 9, 'oktobar': 10, 'novembar': 11, 'decembar': 12, 'siječanj': 1, 'veljač': 2, 'ožujak': 3,
          'travanj': 4, 'svibanj': 5, 'lipanj': 6, 'srpanj': 7, 'kolovoz': 8, 'rujan': 9, 'listopad': 10,
          'studeni': 11, 'prosinac': 12}
MONTH = r'(?:januar|februar|mart|april|maj|jun|jul|avgust|august|septembar|septemb|oktobar|oktob|novembar|novemb|decembar|decemb)\w*'
DATE = (rf'(?:\d{{1,2}}\.\s*\d{{1,2}}\.\s*(?:19[34]\d)?|\d{{1,2}}\.\s*{MONTH}(?:\s+19[34]\d)?|{MONTH}\s+19[34]\d|{MONTH}|'
        rf'(?:u\s+)?(?:proljeće|leto|ljeto|jesen|zimu|zima|početkom|krajem|sredinom)\s+(?:19[34]\d)?|19[34]\d)\.?')
SPAN = rf'(?:\(?\s*(?:od\s+)?{DATE}(?:\s*(?:-|–|—|do)\s*(?:{DATE}|kraja rata|pobjede|pobede))?\s*\)?|do\s+{DATE}|od\s+{DATE})'

ROLES = [  # (key, pattern of the post without its level)
    ('komandant', r'(?:prvi\s+|posljednji\s+|poslednji\s+)?(?:v\.\s*d\.\s*)?komandant\w*'),
    ('komesar', r'(?:prvi\s+|posljednji\s+|poslednji\s+)?(?:v\.\s*d\.\s*)?(?:politi\w+\s+)?komesar\w*'),
    ('zamjenik komandanta', r'(?:prvi\s+)?(?:zam[j]?enik\w*|pomoćnik\w*)\s+komandanta'),
    ('zamjenik komesara', r'(?:prvi\s+)?(?:zam[j]?enik\w*|pomoćnik\w*)\s+(?:političkog\s+)?komesara'),
    ('načelnik štaba', r'(?:prvi\s+|posljednji\s+)?načelnik\w*\s+štaba'),
    ('operativni oficir', r'(?:prvi\s+)?operativn\w+\s+oficir\w*'),
    ('obavještajni oficir', r'(?:prvi\s+)?(?:obavještajn|obaveštajn|informativn)\w+\s+oficir\w*'),
    ('intendant', r'(?:prvi\s+)?intendant\w*'),
    ('referent saniteta', r'referent\w*\s+saniteta'),
    ('komandir', r'(?:v\.\s*d\.\s*)?komandir\w*'),
    ('zamjenik komandira', r'zam[j]?enik\w*\s+komandira'),
    ('komandant pozadine', r'komandant\w*\s+pozadine'),
    ('delegat voda', r'(?:politički\s+)?delegat\w*\s+voda'),
]
LEVEL = (r'\s+(?:(?P<no>\d)\.\s*)?(?:(?P<kind>izviđačk|prateć|inžinjerijsk|sanitetsk|protiv\w+|štabn)\w*\s+)?'
         r'(?:(?P<land>kordunašk|banijsk|mitraljesk|rusk|makedonsk)\w*\s+)?(?P<level>brigad|bataljon|čet|vod)\w*'
         r'(?:\s+(?:(?P<no2>\d)\.\s*)?(?P<level2>bataljon|čet)\w*)?')


def sort_key(when: str) -> str:
    """'od 19. februara do 24. oktobra 1944' -> '1944-02-19': the start, its year taken from the end when it has none."""
    years = re.findall(r'19[34]\d', when)
    if not years:
        return ''
    num = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(19[34]\d)?', when)
    word = re.search(rf'(?:(\d{{1,2}})\.\s*)?({MONTH})', when, re.I)
    y = years[0]
    if num and (not word or num.start() <= word.start()):
        return f'{num.group(3) or y}-{int(num.group(2)):02d}-{int(num.group(1)):02d}'
    if word:
        m = next((v for k, v in MONTHS.items() if word.group(2).lower().startswith(k[:5])), 0)
        return f'{y}-{m:02d}' + (f'-{int(word.group(1)):02d}' if word.group(1) else '')
    return y


def posts(s: dict) -> list[dict]:
    text = (s.get('additional_info') or '')
    rank = s.get('rank') or ''
    detail = s.get('unit_detail') or ''
    out = []
    for key, role in ROLES:
        for m in re.finditer(role + LEVEL, text, re.I):
            level = m.group('level').lower()
            no = m.group('no')
            # "zamjenik komandanta brigade" is no komandant, "pratioc komandanta brigade" no post of the staff
            if key in ('komandant', 'komesar', 'komandir') and re.search(
                    r'(?:zam[j]?enik|pomoćnik|pratioc|pratilac|ađutant|kurir|šef)\w*\s+(?:političkog\s+)?$',
                    text[max(0, m.start() - 30):m.start()], re.I):
                continue
            bat = None
            if level == 'bataljon':
                bat = no or (re.search(r'(\d)\. bataljon', detail).group(1) if re.search(r'(\d)\. bataljon', detail) else None)
                if m.group('land'):
                    bat = f"{no or ''}{m.group('land').lower()}"
            elif level in ('čet', 'vod'):
                bat = m.group('no2') if m.group('level2') == 'bataljon' else None
                if not bat:
                    near = re.search(r'(\d)\.\s*bataljon', text[m.end():m.end() + 30]) or re.search(r'(\d)\. bataljon', detail)
                    bat = near.group(1) if near else None
            company = (m.group('kind') or no) if level == 'čet' else None
            if level in ('čet', 'vod') and not (m.group('kind') if level == 'čet' else m.group('no2')):
                # the company from the soldier's sub-unit ("2. četa, 1. bataljon") where it is of that battalion
                d = re.search(r'(\d)\. četa, (\d)\. bataljon', detail)
                if d and (bat is None or bat == d.group(2)):
                    if level == 'čet' and not no:
                        company = d.group(1)
                    bat = bat or d.group(2)
            tail = text[m.end():m.end() + 70]
            span = re.match(r'[\s,]*' + SPAN, tail, re.I)
            # a time printed before the post ("1942. komandant 1. bataljona", "od septembra 1943. komandant"), never
            # the date he joined ("u NOB od 1941, zamjenik komesara čete")
            head = text[max(0, m.start() - 45):m.start()]
            before = re.search(r'(?:^|[,;.]\s+)((?:od\s+|u\s+|do\s+)?(?:[\w.]+\s+){0,2}19[34]\d)\.?\s*,?\s*$', head)
            if before and re.search(r'(?:NOB|NOV|NOP|partizan\w*|brigadi|bataljonu|rođen\w*)\w*\s*(?:-|od)?\s*[\d.\s]*$',
                                    head[:before.start(1)], re.I):
                before = None
            if before and re.match(r'\d', before.group(1)) and not re.match(r'(?:\d{1,2}\.\s*){0,2}19[34]\d$', before.group(1)):
                before = None                                       # a part of a date ("7. 1941" of "27. 7. 1941")
            when = (span.group(0) if span else before.group(1) if before else '').strip(' ,;')
            if re.fullmatch(r'\(?\s*(?:u\s+)?(?:NOB|brigadi)\b.*', when) or not re.search(r'19[34]\d|' + MONTH, when, re.I):
                when = ''
            out.append({
                'id': s['soldier_id'], 'name': s.get('full_name') or '', 'role': key,
                'level': {'brigad': 'brigada', 'bataljon': 'bataljon', 'čet': 'četa', 'vod': 'vod'}[level],
                'battalion': bat, 'company': company,
                'platoon': no if level == 'vod' else None,
                'company_of_platoon': ((m.group('no2') if m.group('level2') == 'čet' else None)
                                       or (re.search(r'(\d)\. četa', detail).group(1) if re.search(r'(\d)\. četa', detail) else None))
                                      if level == 'vod' else None,
                'when': when.strip('()'), 'start': sort_key(when), 'text': text[max(0, m.start() - 10):m.end() + 60],
                'death_type': s.get('death_type') or '', 'death_date': s.get('death_date') or '',
                'death_place': s.get('death_place') or '',
                'hero': bool(re.search(r'narodn\w*\s+heroj', text + ' ' + rank, re.I)),
            })
    # the same post read twice (komesar / politički komesar): once
    seen, unique = set(), []
    for p in out:
        k = (p['role'], p['level'], p['battalion'], p['company'], p['platoon'], p['when'])
        if k not in seen:
            seen.add(k)
            unique.append(p)
    return unique


def main():
    unit = sys.argv[1]
    ts =(ROOT / 'website' / 'app' / 'data' / 'units.ts').read_text(encoding='utf-8')
    m = re.search(rf"id: '{re.escape(unit)}',.*?dataFile: '/([^']+)'", ts, re.S)
    recs = json.loads((ROOT / 'website' / 'public' / m.group(1)).read_text(encoding='utf-8'))
    found = [p for s in recs for p in posts(s)]
    out = ROOT / 'website' / 'app' / '(sr)' / 'jedinica' / '_data' / f'{unit}.posts.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(found, ensure_ascii=False, indent=1), encoding='utf-8')
    from collections import Counter
    print(len(found), 'posts;', Counter((p['level'], p['role']) for p in found).most_common(40))


if __name__ == '__main__':
    main()
