"""
Parser: Treća proleterska (sandžačka) brigada (brigade code 5) — the list at its formation, as the memoir book prints it.

Source: the brigade's zbornik sjećanja, "Spisak boraca i starješina na dan formiranja brigade" (compiled by the
        brigade's survivors and the SUBNOR committees of Nova Varoš, Pljevlja, Bijelo Polje and Prijepolje)
        znaci.org  →  website/public/pdfs/treca-proleterska-formiranje.pdf
The same list as Žarko Vidović's monograph prints (treca-proleterska-brigada.pdf, unit 5's first book), here in
Cyrillic: the staff and each battalion and company under its heading, a name line in capitals ("*" or "•" after
those who died), then the bio:
    КНЕЖЕВИЋ ВЛАДИМИР ВОЛОЂА *
    командант, рођен 1915, Вашково, Пљевља, поручник бивше југословенске војске; ...
Every soldier is also in the monograph's list, so merge corrections make each one record with both entries
(scripts/find_source_duplicates.py). These records get IDs from 0005020001 (the memoir book's list of the fallen
has 0005010001-) and a re-run replaces only them. The last pages (national heroes) are not part of the list.

    python data-extraction/parse_treca_proleterska_formiranje.py [--test OUT.json]
"""
import re
import sys

from _margin_entries import MARK, fix_cyrillic_ocr_line
from _parser_scaffold import _record, repair_lj_ocr, restore_diacritics, run_parser
from parse_treca_proleterska import is_section_header

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
LAST_PAGE = 68          # the list's end; then "Narodni heroji Treće proleterske"


def keep_line(ln: dict) -> bool:
    t = fix_cyrillic_ocr_line(ln['text'].strip()).replace('L>', 'Lj').replace('l>', 'lj')
    if ln['page'] == 1 or re.fullmatch(r'[\W\d]{1,6}', t) or is_section_header(t) or t.startswith('ŠTAB BRIGAD'):
        return False                                       # the title, page numbers, section headings
    if ln['page'] == 2 and ln['y'] > 435:                  # the editors' footnote
        return False
    # a heading the OCR garbled, an A read as l: "ŠTLB BLTLLJONA", "IRVI BATALJON — ZLATARSKI"
    heading = re.sub(r'(?<=[A-ZČĆŽŠĐ])l|l(?=[A-ZČĆŽŠĐ])', 'A', t)
    if ',' not in t and heading == heading.upper() and re.search(
            r'B[AL]T[AL][AL]JON|INTEND[AL]NTUR|S[AL]NITET|\bVOD\b|\bŠT[AL]B\b|NA RADU|NER[AL]SPORE|RANJENICI|PRATEĆ|\bČETA\b',
            heading):
        return False
    # a name line: short, in capitals (the OCR leaves a lowercase letter here and there: "GOLUBOVIĆ MđMČILO"),
    # maybe after a speck ("•JAKIĆ VLADIMIR"); not the end of a bio line ("SKOJ-a.")
    name = re.sub(rf'^[^{U}{L}]+', '', t)
    letters = re.sub(rf'\bdr\b|\bproto\b|[^{U}{L}]', '', name)
    caps = sum(c.isupper() for c in letters)
    if (letters and caps >= 0.8 * len(letters) and len(name) <= 45 and len(letters) >= 4
            and re.match(rf'^[{U}]\S', name) and not re.match(r'^(?:SKOJ|KPJ|NOP|NOB|AVNOJ|JNA)\b', name)):
        name = name.replace('KRVAVACJOVAN', 'KRVAVAC JOVAN')                        # two words run together
        name = re.sub(r'VJ\s*4Ć|VIT\b', 'VIĆ', name)                               # "IBIŠBEGOVJ 4Ć", "BULATOVIT"
        name = re.sub(rf'(?<=[{U}])\.T(?=[{U}])', 'J', name)                       # "KRSTA.TIĆ"
        t = re.sub(rf'^([{U}][{U}{L}\-]+)', lambda m: m.group(1).upper() + MARK, name, count=1)   # "TzUKIĆ"
    ln['text'] = t
    return True


def parse_entry(text: str) -> dict:
    """SURNAME[MARK] [dr] [F.] GIVEN [NICKNAME] [*|•] bio"""
    last, rest = text.split(MARK, 1)
    tokens = [t.strip("'`’") for t in rest.split()]
    name, i, notes = [], 0, []

    def in_caps(t):                                      # "MđMČILO": a name word with a letter misread
        letters = re.sub(rf'[^{U}{L}]', '', t)
        return bool(letters) and t[0].isupper() and sum(c.isupper() for c in letters) >= 0.6 * len(letters)

    while i < len(tokens) and (in_caps(tokens[i]) or re.fullmatch(r'[*•]+|dr|proto|[.,g]', tokens[i])):
        if tokens[i] == 'proto':                           # "KARAMATIJEVIĆ proto JEVSTATIJE": a priest's title
            notes.append('proto')
        elif tokens[i] not in ('.', ',', 'g'):             # specks between the words
            name.append(tokens[i])
        i += 1
    bio = ' '.join(tokens[i:])
    died = any('*' in t or '•' in t for t in name)
    name = [t.strip('*•').upper() for t in name if t.strip('*•')]
    if 'DR' in name:
        name.remove('DR')
        notes.append('dr')
    if 'dr' in name:
        name.remove('dr')
        notes.append('dr')
    father = name.pop(0) if name and re.fullmatch(rf'[{U}]\.', name[0]) else ''
    given = name[0] if name else ''
    if len(name) > 1:
        notes.append('zvani ' + ' '.join(n.title() for n in name[1:]))
    info = '; '.join(notes + [bio]) if bio else '; '.join(notes)
    rec = _record(last, given, father.rstrip('.'), info)
    if died and not re.search(r'\b(?:pogin|umr|strelj|nesta)', bio, re.I):
        rec['additional_info'] = (rec['additional_info'] + ' ' if rec['additional_info'] else '') + '(umro)'
    return rec


def post(soldiers: list[dict]) -> list[dict]:
    soldiers = repair_lj_ocr(restore_diacritics(soldiers))
    for s in soldiers:
        s['last_name'] = re.sub(r'^Tz', 'C', s['last_name'])                  # Ц read as "Tz": "TzUKIĆ"
        s['first_name'] = {'Mđmčilo': 'Momčilo'}.get(s['first_name'], s['first_name'])
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


if __name__ == '__main__':
    test = sys.argv[sys.argv.index('--test') + 1] if '--test' in sys.argv else None
    run_parser(
        pdf_path='website/public/pdfs/treca-proleterska-formiranje.pdf',
        brigade_code=5,
        output_path=test or 'website/public/treca-proleterska-soldiers.json',
        start_page=1,
        end_page=LAST_PAGE,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(rf'^[{U}][{U}\-]*{MARK}'),
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
        id_start=20001,
        keep_other_sources=not test,
    )
