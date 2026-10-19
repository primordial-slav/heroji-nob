"""
*Поменик жртава Другог светског рата подручја општине Књажевац* (Poreklo library, doc a6202620-.../00002204, 349 scan
pages; the OCR fetched into data-extraction/poreklo/knjazevac-pomenik.json): a book across units, fighters only.

Village by village under a heading in capitals ("СТАЊИНАЦ"), a paragraph each, its first line indented:
    "Најдановић Светолика Миодраг (21), рођен 1923. у Васиљу, земљорадник. Мобилисан у НОВЈ септембра 1944. Пао је
    као курир штаба 14. бригаде 3. новембра 1944. код Горње Горијевнице ..."
Surname, the father in the genitive, given name, his age in brackets. The book names everyone of the municipality who
died in the war: partisans, Chetniks ("Припадник четника ДМ", "четовођа"), the shot, civilians. Only the fighters go in
(the user's rule for mixed lists, parse_mosorski_odred_2.FIGHTER on the entry read in Latin), and never one of the
other side (`OTHER_SIDE`, after "у борби против четника" and "убијен од четника" are taken out: a partisan who fought or
fell by them is still one). A Serbian brigade the entry names by its number ("14. бригаде", "23. бригаде 45. дивизије")
gives the site's unit (`BRIGADES`). Records of the library have no scan on the site: `source_url` is the page in its
viewer, `source_page` the book's page.

Output: data-extraction/poreklo/knjazevac-pomenik-entries.json, IDs 9038xxxxxx (by the entry's place among all the
book's entries, so they stay put whatever the rule keeps).
Usage: python data-extraction/parse_knjazevac_pomenik.py [--sample N] [--dropped N]
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'scripts'))
import poreklo_text as pt  # noqa: E402
import _karlovac_lists as kl  # noqa: E402
import parse_ofanziva_1942 as ofz  # noqa: E402
from _parser_scaffold import cyrillic_to_latin  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from parse_mosorski_odred_2 import FIGHTER, REAR  # noqa: E402

BOOK = 'knjazevac-pomenik'
OUT = HERE / 'poreklo' / f'{BOOK}-entries.json'
PREFIX = '9038'
TITLE = 'Pomenik žrtava Drugog svetskog rata područja opštine Knjaževac'
FIRST_PAGE, LAST_PAGE = 40, 349                        # the list's scan pages (the photos before; it ends at LITERATURA)
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# the other side: Chetniks of the DM, Nedić's and Ljotić's men, the Bulgarian army, the old army's prisoners
OTHER_SIDE = re.compile(r'\bčetni\w*|\bčetovođ\w*|\bJVuO\b|ravnogor\w*|ljotić\w*|nedić\w*|\bSDS\b|\bSDK\b|'
                        r'državn\w*\s+straž\w*|dobrovoljačk\w*|bugarsk\w*\s+vojsk\w*|\bDM\b', re.I)
AGAINST = re.compile(r'\b(?:protiv|od|sa)\s+(?:strane\s+)?(?:\S+\s+){0,2}(?:četni\w*|ljotićev\w*|nedićev\w*|bugar\w*)'
                     r'(?:\s+DM)?', re.I)
# a man the partisans killed is none of theirs (the user's rule, 2026-10-14): his entry's first word of a death
# ("Ubijen ... od pripadnika Timočke partizanske čete", "likvidiran je od mesne partizanske desetine"); a fighter who fell
# by a comrade's hand ("Poginuo kao vodnik ... od saborca partizana") stays
DEATH_WORD = re.compile(r'\b(?:poginu\w*|pao|pala|ubijen\w*|streljan\w*|likvidiran\w*|zaklan\w*|obešen\w*|umr\w*|nesta\w*)\b',
                        re.I)
BY_PARTISANS = re.compile(r'(?:ubijen|streljan|likvidiran|zaklan|obešen)\w*\b[^;]{0,120}?\bo[dn]\s+(?:strane\s+)?'
                          r'(?:\S+\s+){0,3}?(?:partizan\w*|NOVJ?|NOP\w*)\b', re.I)
# Serbian brigades by their number (in this book "14. бригада" is the 14. srpska) -> the site's unit
BRIGADES = {4: 21, 5: 127, 7: 85, 8: 87, 9: 165, 10: 88, 12: 90, 14: 27, 15: 86, 17: 55, 18: 128, 19: 73, 20: 91, 21: 80,
            22: 74, 23: 89, 25: 31}
DIVISIONS = {25: 19, 22: 96}                            # the divisions the site has as units (25. srpska, 22.)


def entries() -> list[dict]:
    book = pt.load(f'{BOOK}.json')
    out, village = [], ''
    for pg in range(FIRST_PAGE, LAST_PAGE + 1):
        lines = pt.page_lines(book, pg)[0]
        if not lines:
            continue
        xs = sorted(l.x0 for l in lines)
        left = xs[len(xs) // 4]
        for l in lines:
            t = l.text.strip()
            if re.fullmatch(r'[\d\W]{1,5}', t) or re.search(r'(?i)www\.|poreklo|spiskovi|svetskog-rata|bivsoj', cyrillic_to_latin(t)):
                continue                                          # the page number, a speck, the scan's footer
            lat = cyrillic_to_latin(t)
            if re.fullmatch(rf'[{U}][{U}\s\-]{{2,40}}', lat) and len(t) < 40:
                if re.match(r'(?:LITERATURA|IZVORI|SADRŽAJ|REGISTAR)\b', lat):
                    return out, book                              # the list ends
                village = ' '.join(w.capitalize() for w in lat.split())
                continue                                          # "СТАЊИНАЦ"
            start = l.x0 > left + 150 and re.match(rf'^[{U}][{L}]+', lat)
            if start:
                out.append({'lines': [lat], 'page': pg, 'village': village})
            elif out:
                out[-1]['lines'].append(lat)
    return out, book


def join(lines: list[str]) -> str:
    text = ''
    for ln in lines:
        if re.search(r'[-–]$', text) and re.match(rf'[{L}]', ln):
            text = text.rstrip('-–') + ln
        else:
            text += (' ' if text else '') + ln
    return re.sub(r'\s+', ' ', text).strip()


def clean_word(w: str) -> str:
    return re.sub(rf'[^{U}{L}\-]', '', w)


def parse(e: dict, n: int, book: dict) -> dict:
    text = join(e['lines'])
    m = re.match(rf'^(.*?)\s*\(([^)]*)\)\s*[,.]?\s*', text)
    head, rest = (m.group(1), text[m.end():]) if m and len(m.group(1)) < 70 else (text.split(',')[0], text[len(text.split(',')[0]) + 1:])
    age = re.search(r'\d+', m.group(2)) if m else None
    words = [clean_word(w) for w in head.split()]
    words = [w for w in words if w]
    if len(words) >= 2 and len(words[-1]) <= 2 and words[-1][0].isupper() and len(words[-2]) > 3:
        words[-2:] = [words[-2] + words[-1].lower()]      # "Ananij E" = Ananije, a name the OCR broke
    last = words[0] if words else ''
    father, given = (words[1], words[2]) if len(words) >= 3 else ('', words[1] if len(words) > 1 else '')
    nick = ' '.join(words[3:])
    last = '-'.join(kl.spelled(p.upper(), 'last') for p in last.split('-') if p)
    given = kl.spelled(given.upper(), 'first') if given else ''
    rec = {'soldier_id': f'{PREFIX}{n:06d}', 'name': ' '.join(x for x in (last, father, given, nick) if x),
           'last_name': last, 'also': [], 'first_name': given, 'nick': nick, 'fathers_name': father}
    born = re.search(r'\bro[đd]en[a]?\s+(?:[\d.\s]*?)(1[89]\d\d)\.?\s*(?:godine\s*)?(?:u\s+([^.,]+))?', rest)
    rec['birth_year'] = born.group(1) if born else ''
    place = (born.group(2) or '').strip() if born else ''
    rec['born_in'] = ', '.join(x for x in (place or e['village'], 'Knjaževac') if x)
    death = list(re.finditer(r'\b(?:poginu[oa]|pao|pala|ubijen[a]?|streljan[a]?|umro|umrla|nesta[oa]|nestala)\b', rest, re.I))
    after = rest[death[0].start():] if death else ''
    y = re.search(r'\b(19[34]\d)\b', after[:140])
    rec['death_year'] = y.group(1) if y else ''
    rec['death_date'] = ''
    rec['units'] = sorted({BRIGADES[int(x)] for x in re.findall(r'\b(\d{1,2})\.\s*(?:srpsk\w*\s+)?brigad', rest)
                           if int(x) in BRIGADES} |
                          {DIVISIONS[int(x)] for x in re.findall(r'\b(\d{1,2})\.\s*(?:srpsk\w*\s+)?divizij', rest)
                           if int(x) in DIVISIONS})
    rec['age'] = age.group(0) if age else ''
    rec['additional_info'] = f"{e['village']}: {rest}" if e['village'] else rest
    rec['list'] = TITLE
    rec['source_url'] = pt.viewer_url(book, e['page'])
    rec['source_page'] = pt.printed_page(book, e['page'])
    return rec


def ours(rec: dict) -> bool:
    """Not a note of the book's, not one of the other side, nor a man the partisans killed"""
    if len(rec['name'].split()) > 5 or re.search(r'\s(?:iz|i|od|sa|u)\s', rec['name']):
        return False                       # a note of the book's ("Protokol umrlih ...", "Mtadići iz ..."), not a name
    info = REAR.sub('', rec['additional_info'])
    if re.search(r'\bpo\s+presudi\b|\bnov\w*\s+vlast', info):
        return False                     # tried and shot by the new authorities in 1944-45, one of the other side
    own = AGAINST.sub('', info)                           # "u borbi protiv četnika DM", "ubijen od četnika"
    death = DEATH_WORD.search(info)
    if death and BY_PARTISANS.match(info, death.start()):
        return False
    return not OTHER_SIDE.search(own)


def fighter(rec: dict) -> bool:
    return ours(rec) and bool(FIGHTER.search(REAR.sub('', rec['additional_info'])))


def kind(rec: dict) -> str:
    """'fighter', 'activist' (in too, marked, by the user's decision of 2026-10-19), or '' (out). A fighter also by his
    rank, or by a unit the entry puts him in without a verb of joining (parse_mosorski_odred_2.fighter_or_officer)."""
    if not ours(rec):
        return ''
    # (the book's notes on another record of the name, "Različit navod: ... Kao komunista uhapšen", are not his)
    own = AGAINST.sub('', re.split(r'\bRazli\w*\s+(?:i\s+dupli\s+)?(?:navod|podat)', rec['additional_info'])[0])
    if fighter(rec) or mos.fighter_or_officer({'additional_info': own}):
        return 'fighter'
    return 'activist' if mos.activist({'additional_info': own}) else ''


def main() -> None:
    ofz.corpus()
    raw, book = entries()
    every = [parse(e, i, book) for i, e in enumerate(raw, 1)]
    kinds = {r['soldier_id']: kind(r) for r in every}
    for r in every:
        if kinds[r['soldier_id']] == 'activist':
            r['role'] = 'activist'
    kept = [r for r in every if kinds[r['soldier_id']]]
    print(f"fighters by the rule {sum(fighter(r) for r in every)}, by rank or unit "
          f"{sum(kinds[r['soldier_id']] == 'fighter' and not fighter(r) for r in every)}, "
          f"activists {sum(bool(r.get('role')) for r in kept)}")
    OUT.write_text(json.dumps(kept, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(every)} entries read, {len(kept)} fighters -> {OUT.relative_to(HERE.parent)}; villages: '
          f'{len({r["additional_info"].split(":")[0] for r in every})}')
    print(f"father: {sum(bool(r['fathers_name']) for r in kept)}, birth year: {sum(bool(r['birth_year']) for r in kept)}, "
          f"death year: {sum(bool(r['death_year']) for r in kept)}, units: {Counter(u for r in kept for u in r['units'])}")
    random.seed(8)
    if '--sample' in sys.argv:
        for r in random.sample(kept, int(sys.argv[sys.argv.index('--sample') + 1])):
            print(f"  IN  {r['name']!r} [{r['born_in']}] {r['birth_year']} d{r['death_year']} {r['units']} | {r['additional_info'][:130]}")
    if '--extra' in sys.argv:
        for r in every:
            if kinds[r['soldier_id']] and not fighter(r):
                print(f"  {'ACT' if r.get('role') else 'F  '} {r['name']!r} | {r['additional_info'][:150]}")
    if '--dropped' in sys.argv:
        out = [r for r in every if not kinds[r['soldier_id']]]
        for r in random.sample(out, int(sys.argv[sys.argv.index('--dropped') + 1])):
            print(f"  OUT {r['name']!r} | {r['additional_info'][:140]}")


if __name__ == '__main__':
    main()
