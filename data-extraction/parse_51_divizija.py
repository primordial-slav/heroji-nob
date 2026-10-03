"""
Parser: 51. vojvođanska udarna divizija (brigade code 111) — its fallen and missing in the battle of Batina.

Source: Nikola Božić, "Batinska bitka" (znaci.org 00002/427.pdf, its pages 489-521, book pp. 469-501)  →
        website/public/pdfs/51-divizija.pdf. Latin, one column, numbered 1-648 through three lists:
    1-457    "Borci 51. vojvođanske udarne divizije poginuli u batinskoj bici, novembra 1944. godine"
                 1. ACEGAN VASE STEVAN, rođ. 1925, Pančevo, borac, pog. 12. 11. 1944.
    458-622  "Borci 51. vojvođanske divizije nestali u toku batinske bitke" ("... borac, nestao 12. 11. 1944, Batina.")
    623-648  fallen the author found elsewhere: the 12. vojvođanska's list in "Heroj", relatives, Dušan Popović
The name in capitals, a father in the genitive (in capitals too) or an initial. The parser sets the birth year and
place, the duty, and the death (pog. = poginuo, nestao, umro od rana, zarobljen) with its date and place. The
author's footnote (p. 500-501) is not read; the Soviet soldiers' list after it neither (not the NOVJ's).
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import _record, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
# 647 and 648 stand beside the footnote's last lines on p. 33; their text as the page prints it
FIXED = {'647': 'SUDAR STANKA GOJKO, s. Kakinac (Rovišće), borac 12. vojv. brig., pog. u Batini.',
         '648': 'VUCKOVIĆ TIMA, Gornja Kovačica (Bjelovar), borac 12. vojv. brig., pog. u Batini.'}
_note = {'on': False}


def corpus() -> None:
    import glob
    import json
    from collections import Counter, defaultdict
    for f in ('last_name', 'first_name', 'middle_name'):
        k8._spell[f] = defaultdict(Counter)
    for fn in glob.glob('website/public/*soldiers.json'):
        if not fn.replace('\\', '/').endswith('/51-divizija-soldiers.json'):
            for s in json.load(open(fn, encoding='utf-8')):
                for f in k8._spell:
                    if s.get(f):
                        k8._spell[f][k8.fold(s[f])][s[f].upper()] += 1


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.match(r'^(?:BORCI 51|U BATINSKOJ BICI|BATINSKE B)', t) or re.fullmatch(r'[\d\W]{1,6}', t):
        return False                                                         # the headings, page numbers
    if t.startswith('1 Imena poginulih'):
        _note['on'] = True                                                   # the author's footnote runs to the end
    if _note['on'] or ln['page'] == 33:
        m = re.match(r'^(64[78])\.', t)
        if not m:
            return False
        t = f'{m.group(1)}. {FIXED[m.group(1)]}'
    t = re.sub(r'^["\']\s*', '', t)                                          # '625. "DOBRIČKI': a speck
    m = re.match(r'^(\d{1,3})\.\s*["\']?\s*(?=[A-ZČĆŽŠĐ])', t) or re.match(r'^(\d{1,3})\s+(?=[A-ZČĆŽŠĐ]{2})', t)   # "302 PETREŠ"
    if m:
        t = '§d§ ' + t[m.end():]
    ln['text'] = t
    return True


DEATH = re.compile(r'\b(pog\.|poginu[ol]a?|nesta[ol]a?|umr[lo]a?\s+od\s+rana|umr[lo]a?|zarobljen[a]?)\s*', re.I)


def parse(text: str) -> dict:
    text = re.sub(r'^§d§\s*', '', text)
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "ne- stao"
    text = text.replace("pog.'u", 'pog. u').replace('brig7', 'brig.')
    text = re.sub(rf'^([{U}]+),\s+(?=(?:[{U}]+\s+)?[{U}]+\s*,)', r'\1 ', text)   # "GRADINAC, SAVE ĐORĐE,", "RADOVANOV MILENKA, STEVAN,"
    text = re.sub(rf'^([{U}]+\s+[{U}]+),\s+(?=[{U}]+\s*,)', r'\1 ', text)
    head, info = (re.split(r',|\s+(?=iz\s)', text, 1) + [''])[:2]
    info = info.strip()
    words = head.replace('(?)', '').split()
    nick = ''
    if 'zv.' in words:                                                       # "TOPALOV (?) zv. LAKURA"
        i = words.index('zv.')
        nick, words = ' '.join(words[i + 1:]), words[:i]
    initial = next((w for w in words if re.fullmatch(rf'[{U}]\.', w)), '')
    words = [w for w in words if w != initial]
    if len(words) >= 3:
        last, father, given = words[0], words[1], ' '.join(words[2:])       # "ACEGAN VASE STEVAN"
    elif len(words) == 2:
        last, father, given = words[0], initial, words[1]
    else:
        last, father, given = (words[0] if words else ''), initial, ''
    given = given.replace('-', ' - ') if '-' in given else given
    notes = [f'zvani {nick.title()}'] if nick else []
    if ' - ' in given:                                                       # "SLOBODAN-BATA"
        given, alias = given.split(' - ', 1)
        notes.append(f'zvani {alias.title()}')
    rec = _record(last, given.title(), father.title() if len(father) > 2 else father, '; '.join(notes + [info] * bool(info)))
    y = re.search(r'\bro[dđ]\.\s*(1[89]\d\d)', info)
    rec['birth_year'] = y.group(1) if y else ''
    b = re.search(rf'\bro[dđ]\.\s*1[89]\d\d[.,]?\s*,?\s*((?:s\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)*(?:\s*\([^)]*\))?)', info) or \
        re.match(rf'^((?:s\.\s*)?[{U}][{L}]+(?:\s+[{U}][{L}]+)*(?:\s*\([^)]*\))?)\s*,', info)
    if b:
        rec['birth_place'] = re.sub(r'^s\.\s*', '', b.group(1))              # "Mramorak (Kovin)"
    d = DEATH.search(info)
    if d:
        kw = d.group(1).lower()
        rec['death_type'] = ('nestao' if kw.startswith('nesta') else 'umro' if kw.startswith('umr') else
                             'zarobljen' if kw.startswith('zaroblj') else 'poginuo')
        rest = info[d.end():]
        when = re.match(r'(\d{1,2}\.\s*\d{1,2}\.\s*19\d\d|novembra\s+19\d\d|decembra\s+19\d\d)[.,]?\s*', rest)
        if when:
            rec['death_date'] = re.sub(r'\s+', ' ', when.group(1))
            rest = rest[when.end():]
        at = re.match(rf'(?:(?:u|na|kod)\s+)?([{U}][{L}]+(?:\s+[{U}][{L}]+)?)', rest.strip())
        if at:
            rec['death_place'] = {'Batini': 'Batina', 'Batine': 'Batina', 'Ba': 'Batina', 'Somboru': 'Sombor', 'Zmajevcu': 'Zmajevac', 'Bezdana': 'Bezdan', 'Dunavu': 'Dunav', 'Belja': 'Belje', 'Luga': 'Lug'}.get(at.group(1), at.group(1))
        duty = re.search(rf',\s*([{L}]+(?:\s+[{L}]+){{0,2}})(?:\s+12\.\s*vojv\w*\.?\s*brig\.?)?\s*,?\s*$', info[:d.start()])
        if duty and duty.group(1) not in ('rođ', 'rod'):
            rec['rank'] = duty.group(1)                                      # "borac", "komesar čete", "bolničarka"
    if re.search(r'12\.\s*(?:vojv\w*\.?\s*)?brig', info):
        rec['unit_detail'] = '12. vojvođanska brigada'
    return rec


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/51-divizija.pdf',
        brigade_code=111,
        output_path='website/public/51-divizija-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§d§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=k8.post,
    )
