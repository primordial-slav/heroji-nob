"""
Parser: Čačanski NOP odred "Dr Dragiša Mišović" (brigade code 126).

Source: Milojica Pantelić, Radovan M. Marinković, Vladimir Nikšić, "Čačanski narodnooslobodilački partizanski odred
        'Dr Dragiša Mišović'" (znaci.org 00001/51), the chapter "Pali borci Čačanskog NOP odreda 'Dr Dragiša
        Mišović'" (51_16.pdf → website/public/pdfs/cacanski-odred.pdf): the odred's fallen, by region (Dragačevci,
        Ljubićani, Trnavci, ..., the town of Čačak) and village, each with father, trade, birth, the odred's
        battalion he fought in and how and where he died. Its last page is the book's contents.
Cyrillic, one column, each entry's first line indented (some 25pt right of the lines under it), the village headings
in capitals at the margin:
    ВИРОВО
    БОШКОВИЋ. Раденка БОГДАН, земљорадник, рођен 1906. у Вирову, борац Драгачевског батаљона; као тешког
    рањеника заробили га четници и предали Немцима, који су га стрељали код ВТЗ у Чачку 7. децембра 1941.
A full stop after the surname is the scan's ("МАРИЋ. Миљка ЉУБИША"); a nickname follows the given name after a dash
("МИОДРАГ — МИЛЕ"). The scan reads Л as 1 inside a word ("БАРАЈ1ИЋ"), б as 5 and п as 1 at a word's start ("5орац",
"1редали").
"""
import re

from _parser_scaffold import _record, repair_cyrillic_ocr, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
CAPS = rf'[{U}][{U}\-]+'
_left: dict = {}


def fix_digits(t: str) -> str:
    """The scan's digits and specks in words (after transliteration): Л as 1 and О as 0 inside a word in capitals
    ("MIJ10MIR" = Milomir, Л read as "Ј1"), a full stop inside one ("SREĆ.KO"), б as 5 and п as 1 at a word's start"""
    t = re.sub(rf'(?<=[{U}])\.(?=[{U}])', '', t)
    t = re.sub(rf'(?<=[{U}])J1(?=[0{U}])', 'L', t)
    t = re.sub(rf'(?<=[{U}1])0(?=[{U}])', 'O', t)
    t = re.sub(rf'(?<=[{U}])1(?=[{U}])', 'L', t)
    t = re.sub(rf'(?<![{U}{L}])JL(?=[{U}])|(?<=[{U}])JL(?=[{U}])', 'L', t)           # "JLAZIĆ": Л as ЈЛ
    t = re.sub(rf'(?<=[{L}])1(?=[{L}])', 'l', t)
    t = re.sub(rf'(?<![\w\d])5(?=[{L}]{{2}})', 'b', t)
    return re.sub(rf'(?<![\w\d])1(?=[{L}]{{3}})', 'p', t)


def page_number(t: str) -> bool:
    return bool(re.fullmatch(r'[\d\W]{1,5}', t))


def measure(lines: list[dict]) -> None:
    for ln in lines:
        if not page_number(ln['text'].strip()):
            _left[ln['page']] = min(_left.get(ln['page'], 10 ** 6), ln['x'])


def heading(t: str) -> bool:
    """A region or village heading: capitals only, no comma ("ВИРОВО", "БЕЛИ КАМЕН*", "ДРАГАЧЕВЦИ")"""
    return bool(re.fullmatch(rf'[{U}\s\-*.„"“”()]+', t)) and ',' not in t


def keep(ln: dict) -> bool:
    t = fix_digits(ln['text'].strip())
    if page_number(t) or ln['page'] == 1 or heading(t):
        return False
    new = ln['x'] > _left[ln['page']] + 15 and bool(re.match(rf'^{CAPS}', t))
    ln['text'] = ('§x§ ' if new else '') + t
    return True


def join_split(words: list[str]) -> list[str]:
    """A surname the text spaced apart: "MAJ STOROVIĆ" = Majstorović"""
    out = []
    for w in words:
        if out and (len(out[-1]) <= 3 or re.fullmatch(r'O?V?IĆ', w)):
            out[-1] += w
        else:
            out.append(w)
    return out


def parse_entry(text: str) -> dict:
    text = re.sub(r'^§x§\s*', '', text).strip()
    head, _, info = text.partition(',')
    parts = [p.split() for p in head.split('—')]
    words = [w.strip('.') for w in parts[0]]
    nick = []
    other = []
    # "GOJKOVIĆ — JOVANOVIĆ Bogdana ZORKA — ZORA": a woman under two surnames, then a nickname
    if len(parts) > 1 and len(parts[1]) > 1 and all(re.fullmatch(CAPS, w) for w in words) and             re.fullmatch(CAPS, parts[1][0]) and re.fullmatch(rf'[{U}][{L}]+', parts[1][1]):
        other, words = words, [w.strip('.') for w in parts[1]]
        parts = parts[1:]
    if len(parts) > 1:
        nick = [w for p in parts[1:] for w in p]
    last = []
    while words and re.fullmatch(CAPS, words[0]):
        last.append(words.pop(0))
    father = words.pop(0) if words and re.fullmatch(rf'[{U}][{L}]+', words[0]) else ''
    given = [w for w in words if re.fullmatch(CAPS, w)]
    if not given and len(last) > 1:                                          # "SRETENOVIĆ DUŠAN": no father
        last = join_split(last)
        given = [last.pop()] if len(last) > 1 else []
    last = join_split(last)
    if len(given) > 1:                                                       # "MILUTIN MIĆO": a nickname without its dash
        given, nick = given[:1], given[1:] + nick
    if not given and nick:                                                  # "LAZIĆ Milojka — VLADIMIR — MIŠA"
        given, nick = nick[:1], nick[1:]
    if not given and len(last) == 1 and not father and not other:           # "DRAGUTIN, potkivač": the given name alone
        given, last = last, ['…']
    if other:
        last = other + last
    info = info.strip()
    if nick:
        info = 'zvani ' + ' '.join(nick).title() + '; ' + info
    return _record('-'.join(last) if other else ' '.join(last), ' '.join(given), father, info)


def post(soldiers: list[dict]) -> list[dict]:
    return restore_diacritics(repair_cyrillic_ocr(soldiers))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/cacanski-odred.pdf',
        brigade_code=126,
        output_path='website/public/cacanski-odred-soldiers.json',
        start_page=2,
        end_page=78,
        layout='single',
        script='cyrillic',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        line_filter=keep,
        prepare_fn=measure,
        post_fn=post,
    )
