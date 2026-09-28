"""
Parser: 4. Krajiška NOU Brigada (brigade code 11).

Source: Rade Zorić — "ČETVRTA KRAJIŠKA NOU BRIGADA"
        znaci.org/00001/94_5.pdf  →  website/public/pdfs/4-krajiska.pdf
Chapter: "SPISAK POGINULIH, UMRLIH I NESTALIH BORACA I STAREŠINA 4. KRAJIŠKE BRIGADE"
— pages 2-105, single column, Cyrillic. Photo captions (106-128) and the table of contents follow.

Entry format:
    АБАЏИЋ Етхема НАСИХ, борац 2. батаљона, рођен 1926, Паланка, Брчко, Муслиман,
    трговац, у НОБ од 13. IV 1945, погинуо 27. IV 1945. код села Херцеговца, Грубишно Поље.

The OCR is poor: Ћ at the end of a surname comes out as Б/Е/Н/К/В (АДАМОВИБ, АДАМОВИЕ),
Ђ as Б or Ћ (БУРО, роћен), and Л as "Ј1" (СЈ1АВКО). The line filter fixes "roćen" and "J1";
repair_cyrillic_ocr fixes names against the spellings already on the site.
"""
import re
from _parser_scaffold import repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

HEADING = re.compile(r'^(?:S P I S A K|POGINULIH, UMRLIH|I STAREŠINA 4\. KRAJIŠKE)')


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if HEADING.match(t) or (ln['page'] == 2 and t.startswith('*')):
        return False
    t = re.sub(r'\bro[ćc]en', 'rođen', t)            # Ђ read as Ћ
    t = t.replace('J1', 'L').replace('j1', 'l')       # Л read as "Ј1": SJ1AVKO → SLAVKO
    head, sep, tail = t.partition(' ')
    if re.fullmatch(r'[A-ZČĆŽŠĐ03]{4,}', head) and re.search(r'[03]', head):
        t = head.replace('0', 'O').replace('3', 'Z') + sep + tail   # "GV03DEN0VIB" → GVOZDENOVIB
    name, comma, rest = t.partition(',')
    # digits inside caps names: О → 0, З → 3, Л → 1, Ј → 1 ("MIL0Š" → MILOŠ, "DRAGIV 01" → DRAGIVOJ,
    # "LA 30" → LAZO, "ŽU1IE" → ŽULIE); a digit group split off with a space belongs to the name before it
    name = re.sub(r'\b([A-ZČĆŽŠĐ]{2,})\s+(?=[013][A-ZČĆŽŠĐ013]*\b)', r'\1', name)

    def _digits(m: re.Match) -> str:
        w = m.group(0).replace('0', 'O').replace('3', 'Z')
        w = re.sub(r'(?<=O)1$', 'J', w)
        return w.replace('1', 'L')
    name = re.sub(r'\b(?=[A-ZČĆŽŠĐ013]*[A-ZČĆŽŠĐ])(?=[A-ZČĆŽŠĐ013]*[013])[A-ZČĆŽŠĐ013]{3,}\b', _digits, name)
    t = name + comma + rest
    ln['text'] = t
    return True


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-krajiska.pdf',
        brigade_code=11,
        output_path='website/public/4-krajiska-soldiers.json',
        start_page=2,
        end_page=105,
        layout='single',
        script='cyrillic',
        line_filter=keep_line,
        # in this Krajina book a surname ending "-ik"/"-iv" is always a misread "-ić" (ЉУЈИК, ЖМУРИК)
        post_fn=lambda soldiers: repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True))),
    )
