"""
Parser: Treća proleterska (sandžačka) brigada (brigade code 5) — the fallen, from the memoir book.

Source: the brigade's zbornik sjećanja, book 3: "Spisak poginulih i umrlih boraca i starješina" by year
        (compiled by Šućro Hadžismajlović from over 50 sources, 1,374 names)
        znaci.org  →  website/public/pdfs/treca-proleterska-poginuli-knj3.pdf
p. 1 the compiler's note; then one section a year ("Spisak poginulih i umrlih boraca i starješina u 1942. godini"),
each numbered from 1, single column, Cyrillic:
    1. АНИЧИЋ Милоја ДРАГОЈЕ, борац 1. бат. 1924. Дебеља, Нова Варош, земљорадник, члан СКОЈ-а. ...
    13. БУРЏОВИЋ Назифа РИФАТ Тршо, народни херој, ...        (a nickname after the given name)
SURNAME Father GIVEN, then the bio; the OCR reads the final Ћ as Е/Н/Б, Љ as "Л>". Unit 5's file holds the
brigade's list at its formation (treca-proleterska-brigada.pdf): these records get IDs from 0005010001, and the
fallen who were at the formation are merged with those entries (scripts/find_source_duplicates.py).
"""
import re
from collections import Counter

from _margin_entries import MARK, MarginEntries, fix_caps_head, fix_cyrillic_ocr_line, join_split_surname, \
    lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_capital_c, repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser
from parse_8_crnogorska import START, _corpus, mend_given

me = MarginEntries()
U = 'A-ZČĆŽŠĐ'
HEADING = re.compile(r'^(?:SPISAK POGINULIH|I STAR[JE]+ŠINA U|[IVX]{1,4}$)')


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] == 1 or HEADING.match(t) or re.fullmatch(r'[\W\d]{1,6}', t):
        return False                                          # the note, the year headings, page numbers, specks
    t = fix_cyrillic_ocr_line(t)
    t = re.sub(rf'L(?:[>.)]|[aoz](?=[{U}]))(?=[{U}\s])', 'LJ', t)  # Љ in capitals: "BUL>UGIK", "L.UBIŠA", "PILzAK"
    t = t.replace('L>', 'Lj').replace('l>', 'lj')                       # ... and in the bio: "zeml>oradnik"
    number = re.match(rf'^\d{{1,4}}\s*[.,]\s*(?=[{U}])', t)
    if number:
        t = join_split_surname(fix_caps_head(t[number.end():]))
        t = re.sub(r'^(\S+ )Dr\. ', r'\1dr ', t)                        # "POPOVIĆ Dr. DEJAN"
        t = t.replace('Jose ud. Tome KARMELA', 'Jose KARMELA, ud. Tome')    # her married name before her name
        t = re.sub(rf'([{U}]\.)(?=[{U}])', r'\1 ', t)                   # "ZEJAK P.RADOJE"
        t = re.sub(rf'^(\S+ [{U}][a-zčćžšđ]+), (?=[{U}]{{2}})', r'\1 ', t)   # "LONČOVIĆ Borisava, MILOVAN"
        # a numbered line starting with a surname in capitals starts an entry
        m = START.match(t) or re.match(rf'^([{U}][{U}\-]+)(?=[\s,])', t)
        if m:
            t = m.group(1) + MARK + t[m.end(1):]
    ln['text'] = t
    return True


def birth_year(info: str) -> str:
    """'borac 1. bat. 1924. Debelja, ...': the first year before "U NOB" / "borac 3. brigade od" / the death."""
    stop = re.search(r'\b[Uu] NOB|borac 3\. brig|[Pp]ogin|[Uu]mr|[Ss]trijelj|[Nn]esta', info)
    m = re.search(r'\b(1[89]\d\d)\b', info[:stop.start()] if stop else info)
    return m.group(1) if m and int(m.group(1)) <= 1936 else ''


# this book's misreads: Ђ as Б, Е or К (Đuković "Euković", Anđelija "Anbelija", Anđelko "Ankelko"), Ћ as Н, К, Е or
# П (Dragićević "Dragieević"), Д as А (Aleksandar "Aleksanaar", Dobrisav "Aobrisav"), others
SUBS = [('B', 'Đ'), ('E', 'Đ'), ('K', 'Đ'), ('b', 'đ'), ('k', 'đ'), ('N', 'Ć'), ('n', 'ć'), ('k', 'ć'), ('e', 'ć'),
        ('p', 'ć'), ('b', 'ć'), ('a', 'd'), ('A', 'D'), ('l', 'a'), ('a', 'l'), ('i', 'n'), ('k', 'h'), ('d', 'a'),
        ('k', 'd')]
GIVEN_FIXES = {'Anbelija': 'Anđelija', 'Aobrisav': 'Dobrisav', 'Borbije': 'Đorđije', 'Korbije': 'Đorđije',
               'Burbija': 'Đurđija', 'Bamil': 'Ćamil', 'Namil': 'Ćamil', 'Vukoica': 'Vukojica', 'Strain': 'Strajin',
               'Šuero': 'Šućro', 'Šubro': 'Šućro', 'Vogdan': 'Bogdan', 'Vukie': 'Vukić', 'Vukik': 'Vukić'}
NOT_NICKNAMES = {'Puškomitraljezac'}                  # "BERONJA Save PERO, Puškomitraljezac 2. bat.": the duty


def mend(name: str, known: Counter, least: int = 5) -> str:
    """A name the corpus doesn't know takes the best-known spelling one or two of SUBS give."""
    if not name or known[name] >= 3:
        return name
    cands = {name[:m.start()] + b + name[m.end():] for a, b in SUBS for m in re.finditer(re.escape(a), name)}
    cands |= {c[:m.start()] + b + c[m.end():] for c in list(cands) for a, b in SUBS for m in re.finditer(re.escape(a), c)}
    best = max(cands, key=lambda c: known[c], default=None)
    return best if best and known[best] >= least and known[best] >= 10 * (known[name] + 1) else name


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_capital_c(repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True))))
    first, last, fathers = _corpus()
    soldiers = mend_given(lone_names_to_given(split_leading_aliases(soldiers), first, last), first, fathers)
    for s in soldiers:
        nick = re.match(r'^zvani (\S+); ', s['additional_info'])
        if nick and nick.group(1) in NOT_NICKNAMES:
            s['additional_info'] = nick.group(1).lower() + ', ' + s['additional_info'][nick.end():]
        words = s['first_name'].split()
        hyphen = re.fullmatch(r'([A-ZČĆŽŠĐ][a-zčćžšđ]+)-([a-zčćžšđ]+)', s['first_name'])     # "Aleksandar-leko"
        if hyphen or len(words) > 1 and words[0].isupper():                                  # "RISTAN Čika Rista"
            given, nick = (hyphen.group(1), hyphen.group(2)) if hyphen else (words[0], ' '.join(words[1:]))
            nick = re.sub(r'ie$', 'ić', nick)
            s['first_name'] = given
            s['additional_info'] = f'zvani {nick[:1].upper() + nick[1:]}; ' + s['additional_info']
        if s['first_name'].isupper():                                   # "PERO" before a nickname
            s['first_name'] = s['first_name'].title()
        s['first_name'] = GIVEN_FIXES.get(s['first_name']) or mend(s['first_name'], first, 20)
        s['middle_name'] = s['fathers_name'] = mend(s.get('middle_name') or '', fathers, 20)
        s['last_name'] = mend(s['last_name'], last)
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
        s['birth_year'] = s['birth_year'] or birth_year(s['additional_info'])
    return soldiers


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/treca-proleterska-poginuli-knj3.pdf',
        brigade_code=5,
        output_path='website/public/treca-proleterska-soldiers.json',
        start_page=1,
        end_page=112,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(rf'^[{U}][{U}\-]*{MARK}'),
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
