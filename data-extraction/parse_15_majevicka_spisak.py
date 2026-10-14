"""
Parser: 15. majevička brigada (brigade code 49), second book: the roster of everyone who fought in it.

Source: *Petnaesta majevička brigada* (zbornik sjećanja; znaci.org 00002/408, the chapter 408_3.pdf, its PDF pp. 1-71,
book pp. 484-557) → website/public/pdfs/15-majevicka-spisak.pdf. Two lists, one column:
    "Borci 15. majevičke brigade — narodni heroji" (book p. 484): the heroes' short bios,
        BOSIĆ Laze PERO, rođen 1921. godine u selu Gornja Slatina kod Bosanskog Šamca, zemljoradnik, ...
    "Spisak boraca 15. majevičke NOU brigade" (book pp. 485-557), alphabetical:
        ARSENIĆ (Boke) SIMO, 1908, Vitanovići, Bukvik—Brčko, SRBiH, Srbin, zemljoradnik, u NOB od aprila 1943, u
        brigadu došao jula 1943. Poginuo avgusta 1943. godine na Gradačcu.
The surname in capitals, the father in brackets (genitive) or in small letters, the given name in capitals; a second
surname after "zv." ("MAKSIMOVIĆ zv. MARINKOVIĆ (Vase) VASILIJE"). The scan reads I as l or 1 in capitals and loses
carons ("ARSENlC"), which the corpus gives back (parse_8_kordunaska_divizija.post). The list's editors' footnote on
its first page and the book's contents after it are not read.

The unit's first book is its Borci Sutjeske chapter (parse_borci_sutjeske.py); these get 0049010001 on, and the same
man in both is merged (scripts/find_source_duplicates.py --brigade 49), as is a hero in both lists here.
Usage: python data-extraction/parse_15_majevicka_spisak.py
"""
import re

import parse_8_kordunaska_divizija as k8
from _parser_scaffold import run_parser

U = 'A-ZČĆŽŠĐ'
_state = {'note': False}


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\d\W]{1,5}|[A-Za-z]', t) or re.match(r'^(?:SPISAK BORACA|BORCI 15\.)', t):
        return False                                     # page numbers, a speck, the lists' titles
    if ln['page'] == 2 and (t.startswith('*') or _state['note']):
        _state['note'] = True                             # the editors' footnote: the rest of the page
        return False
    if ln['page'] == 3:
        _state['note'] = False
    head = re.split(r',', t, 1)[0]
    if (re.match(rf'^[{U}][{U}l1\-]{{1,}}(?=[\s,(])', t) and len(head.split()) >= 2
            and not re.match(r'^(?:SRBiH|SRS|SRH|SFRJ|KPJ|SKOJ|NOB|NOV|NOVJ|NOR)\b', t)):
        t = '§x§ ' + t
    ln['text'] = t
    return True


CAPS = rf'[{U}][{U}l1\-]+'


def parse(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text)
    head, sep, rest = text.partition(',')
    notes = []
    maiden = re.match(rf'^({CAPS})\s+rod\.\s+({CAPS})\s+', head)
    if maiden:                                           # "ANTONIO rod. ĐURlCKOVlC (Zivana) PLANINKA": her married name
        head = maiden.group(1) + ' ' + head[maiden.end():]
        notes.append(f"rođena {k8.caps_word(maiden.group(2)).title()}")
    alias = re.search(rf'^({CAPS})\s+zv\.\s+({CAPS})\s+', head)
    if alias:                                            # "MAKSIMOVlC zv. MARINKOVlC (Vase) VASILIJE": another surname
        head = alias.group(1) + ' ' + head[alias.end():]
        notes.append(f"zvani {k8.caps_word(alias.group(2)).title()}")
    head = re.sub(r'^([^(]+?)\s*\(([^),]+)\)?\s*', r'\1 \2 ', head, 1)        # "ARSENlC (Arsena) STJEPAN"
    zv = re.search(r'\s+zv\.\s*(.+)$', head)
    if zv:                                               # "GAJIC (Rajka) ZIVKO zv. Ziko"
        head = head[:zv.start()]
        notes.append(f"zvani {zv.group(1).strip()}")
    words = head.split()
    caps = [i for i, w in enumerate(words) if re.fullmatch(CAPS, w)]
    if caps and caps[-1] >= 1 and len(words) > caps[-1] + 1:
        # "BAHRIC (Todora) BRANKO Brane": the given name in capitals, a nickname after it
        notes.append(f"zvani {' '.join(words[caps[-1] + 1:])}")
        head = ' '.join(words[:caps[-1] + 1])
    elif caps == [0] and len(words) >= 4:
        # "BLAZEVIC (Milke) Josip Cigo": the given name in small letters too, then the nickname
        notes.append(f"zvani {' '.join(words[3:])}")
        head = ' '.join(words[:3])
    rec = k8.parse_entry(head + sep + rest)
    rec.pop('unit_detail', None)                         # the 8. division's brigades, not this brigade's battalions
    if notes:
        rec['additional_info'] = '; '.join(notes + [rec['additional_info']])
    return rec


if __name__ == '__main__':
    k8.corpus()
    run_parser(
        pdf_path='website/public/pdfs/15-majevicka-spisak.pdf',
        brigade_code=49,
        output_path='website/public/15-majevicka-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse,
        line_filter=keep,
        post_fn=k8.post,
        id_start=10001,
        keep_other_sources=True,
    )
