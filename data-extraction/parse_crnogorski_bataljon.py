"""
Parser: Prva proleterska brigada (brigade code 1), its Prvi crnogorski bataljon: the fighters who joined it, 1942-1945.

Source: *Prvi crnogorski bataljon Prve proleterske NOU brigade - zbornik sjećanja* (znaci.org 00003/493, the whole book's
PDF pp. 696-778, book pp. 713-795) → website/public/pdfs/crnogorski-bataljon.pdf. In Cyrillic, one column, a paragraph a
fighter, under the year he joined the battalion:
    "Spisak boraca koji su u bataljon stupili u 1942. godini" (and 1943, 1944, 1945):
        БАБИЋ Шћепана ИВО, рођен 1925, Десне, Метковић, СРХ, у НОБ од 1942. погинуо јуна 1943. на Сутјесци.
    "Borci bataljona za koje nema podataka o mjestu i godini rođenja i datuma stupanja u NOB" (pp. 771-778):
        АДАМОВИЋ ИЛИЈА, рањен 1. маја 1945. године.
The surname and the given name in capitals, the father in the genitive or an initial; the year he joined goes to the
front of the text ("u bataljon stupio 1942."). The battalion's roll at Rudo on 21 December 1941 before these lists (PDF
pp. 681-695) is not read: the brigade's line-up at Rudo is on the site already (parse_prva_proleterska_rudo.py).
These get 0001500001 on (the brigade's other books: 0001000001- to 0001400001-), and the same man in the brigade's
other lists is merged (scripts/find_source_duplicates.py --brigade 1).
Usage: python data-extraction/parse_crnogorski_bataljon.py
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}lI1\-]+'
_state = {'year': '', 'open': False}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    # capitals the OCR spaced out ("B U L A T O V I Ć", "M A T Š A")
    t = re.sub(rf'(?<!\S)[{U}](?: [{U}]){{2,}}(?!\S)', lambda m: m.group(0).replace(' ', ''), t)
    if re.fullmatch(r'[\d\W]{1,6}|\S{1,2}', t):
        return False                                     # page numbers, specks
    m = re.search(r'(?i)stupili u (19\d\d)', t)          # the 1944 and 1945 lists' titles are in small letters
    if m:
        _state['year'], _state['open'] = m.group(1), False
        return False
    if re.match(r'(?i)^(?:SPISAK|S P I S A K|BORACA KOJI SU|BORACA BATALJONA ZA KOJE|I DATUMA STUPANJA|STUPANJA U NOB)', t):
        if t.upper().startswith('BORACA BATALJONA'):
            _state['year'] = ''
        return False
    if (re.match(rf'^{CAPS}(?:\s*-\s*{CAPS})?\s+(?:[{U}][{L}]+|[{U}]\.|{CAPS}\s*[,.])', t)
            and not re.match(r'^(?:SKOJ|KPJ|NOB|NOV|NOVJ|SRH|SRS|SRCG|SRBiH|SAP|SPV|JNA)\b', t)):
        t = f"§x§ [{_state['year']}] {t}"
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    m = re.match(r'^§x§\s*\[(\d*)\]\s*(.*)$', text)
    year, t = m.group(1), m.group(2)
    t = re.sub(r'(?<=[a-zčćžšđ])- (?=[a-zčćžšđ])', '', t)                   # "земљорад- ник"
    t = re.sub(r'\broćen', 'rođen', re.sub(r'\brođei\b', 'rođen', t))
    # the name ends before "rođen" and the like where the comma is a full stop or missing ("ŠPADIJER ŠPIRO. rođen",
    # "JANKOVIĆ Mihaila MILJKO rođen", "ĐURIŠIĆ Iva VOJISLAV—VOJArođen"), a nickname after a dash
    t = re.sub(r'(?<=[A-ZČĆŽŠĐ])(?=rođen)', ' ', t, count=1)
    t = re.sub(rf'^({CAPS}(?:\s+(?:[{U}][{L}]+|[{U}]\.))?\s+{CAPS}(?:\s*[—–-]\s*[{U}][{U}{L}]+)?)\s*\.?\s+'
               r'(?=rođen|ranjen|bio\b|umro|poginuo)', r'\1, ', t, count=1)
    nick = re.match(rf'^(\S+(?:\s+(?:[{U}][{L}]+|[{U}]\.))?\s+{CAPS})\s*[—–]\s*([{U}][{U}{L}]+)\s*,', t)
    if nick:                                              # "JOVOVIĆ Vojina NIKOLA—Kolja,"
        t = f'{nick.group(1)} »{nick.group(2).title()}«,' + t[nick.end():]
    rec = k8.parse_entry(t)
    rec.pop('unit_detail', None)                          # the 8. division's brigades: not this list's
    if year:
        rec['additional_info'] = f"u bataljon stupio {year}. godine; {rec['additional_info']}".strip('; ')
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)\b', rec['additional_info'])
    rec['birth_year'] = y.group(1) if y else ''
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/crnogorski-bataljon.pdf',
        brigade_code=1,
        output_path='website/public/prva-proleterska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=k8.post,
        id_start=500001,
        keep_other_sources=True,
    )
