"""
Parser: 19. Birčanska NOU brigada (brigade code 23).

Source: "DEVETNAESTA BIRČANSKA NOU BRIGADA", chapter "Spisak boraca 19. birčanske brigade"
        znaci.org/00001/267_5.pdf  →  website/public/pdfs/19-bircanska.pdf
Two columns, Cyrillic; the gutter moves between pages (auto). p. 1 the chapter title, pp. 2-117 one
alphabetical list, pp. 118-121 the book's table of contents.
    АВДИЋ СМАЈЕ ЈУСУФ, рођен 1911. године у Тузли, Муслиман, земљорадник, у Бригаду ступио ...
    АВРАМОВИЋ МИЛУТИНА ЧЕДО-/МИР, рођен 1925. године у Парадину, СРС, Србин, ...
The father is printed in caps like the name. The OCR never reads a capital Ћ (АВДИЕ, АВДИСПАХИК, АДАМОВИБ,
АВДИН: repair_cyrillic_ocr, repair_capital_c) and reads a lowercase н as и in the bios (годиие, рођеи,
погииуо: fix_bio_words), and Љ as Л> (КРАЛ>ЕВИЋ).
"""
import json
import re
from collections import Counter
from pathlib import Path

from _margin_entries import fix_cyrillic_ocr_line, split_leading_aliases
from _parser_scaffold import (CAPITAL_C_MISREAD, parse_standard_entry, repair_capital_c, repair_cyrillic_ocr,
                              repair_lj_ocr, restore_diacritics, run_parser)


JOIN = '⁠'          # word joiner after the first word of a line that continues a name broken with a hyphen
_state = {'prev': '', 'held': None}


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or (ln['page'] == 1):
        return False
    # Љ/Њ read as "Л>"/"Н>": "КРАЛ>ЕВИЋ", "зeмл>орадник"
    t = t.replace('Л>', 'Љ').replace('л>', 'љ').replace('Н>', 'Њ').replace('н>', 'њ')
    t = t.replace('L>', 'LJ').replace('l>', 'lj').replace('N>', 'NJ').replace('n>', 'nj')
    t = fix_cyrillic_ocr_line(t)
    held = _state['held']
    if held:            # a double surname alone on the line above: "ALAJBEGOVIĆ - PRODANOVIĆ" / "HASANA RAZIJA ..."
        t = held['text'] + ' ' + t
        ln['x'], ln['y'] = held['x'], held['y']
        _state['held'] = None
    elif re.fullmatch(r'[A-ZČĆŽŠĐ]{3,} ?- ?[A-ZČĆŽŠĐ]{3,}', t):
        _state['held'] = {'text': re.sub(r' ?- ?', '-', t), 'x': ln['x'], 'y': ln['y']}
        return False
    # "... KOVAČINA-BEČANOVIĆ OBRE-" / "NA SLAVKA, rođena": the second line continues the name
    if re.search(r'[A-ZČĆŽŠĐ]-$', _state['prev']) and re.match(r'^[A-ZČĆŽŠĐ]', t):
        t = re.sub(r'^(\S+)', r'\1' + JOIN, t, count=1)
    ln['text'] = _state['prev'] = t
    return True


def parse_entry(text: str) -> dict:
    return parse_standard_entry(re.sub(r'-(\S+)' + JOIN, r'\1', text).replace(JOIN, ''))


def _corpus():
    words, first = Counter(), Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name not in CAPITAL_C_MISREAD:
            for s in json.loads(f.read_text(encoding='utf-8')):
                words.update(re.findall(r'[a-zčćžšđ]{3,}', (s.get('additional_info') or '').lower()))
                first[s['first_name']] += 1
    return words, first


def _given(g: str, first: Counter) -> tuple[str, str]:
    """A given name the OCR hyphenated at a line end, or NAME-NICKNAME: "IBRA-HIM-IBRICA" → (Ibrahim, Ibrica),
    "MA-NOJLE-NOKA" → (Manojle, Noka), "ZIH-NIJA" → (Zihnija, ''). The longest known name made of the first
    pieces is the name, the rest the nickname."""
    parts = [p.capitalize() for p in g.split('-')]
    for k in range(len(parts), 0, -1):
        name, nick = ''.join(parts[:k]).capitalize(), ''.join(parts[k:]).capitalize()
        if first[name] >= 2 and len(name) >= 3 and (not nick or first[nick] or len(nick) >= 4):
            return name, nick
    if len(parts) > 2 and first[parts[-1]]:
        return ''.join(parts[:-1]).capitalize(), parts[-1]
    return ''.join(parts).capitalize(), ''


def fix_names(soldiers: list[dict], first: Counter) -> list[dict]:
    """Given names (see _given); a possessive father before the given name: "DANILOVIĆ STJEPANOV DRAGO"; a name
    and a nickname ("VASILIĆ MAKSIMA TIMOTIJA TIMO"). Surnames: a stray lowercase end ("SELIMOVIć"), and "-in"
    for "-ić": this is a Bosnian brigade, where real "-in" surnames are rare (Kurtagin → Kurtagić), except for
    soldiers from Vojvodina."""
    for s in soldiers:
        prefix = []
        words = s['first_name'].split()
        if len(words) == 2 and not s['middle_name'] and re.search(r'(?:ov|ev|in)$', words[0]):
            s['middle_name'] = s['fathers_name'] = words[0]
            words = words[1:]
        elif len(words) == 2 and s['middle_name']:
            prefix.append('zvani ' + words[1].replace('-', ''))
            words = words[:1]
        if words and '-' in words[0]:
            name, nick = _given(words[0], first)
            words = [name]
            if nick:
                prefix.append('zvani ' + nick)
        s['first_name'] = ' '.join(words)
        last = s['last_name']
        if re.fullmatch(r'[A-ZČĆŽŠĐ]{2,}[a-zčćžšđ]', last):
            last = last.capitalize()
        if last.endswith('in') and not last.endswith('anin') and \
                not re.search(r'Vojvodin|Srem|Banat|Bačk', s['additional_info']):
            last = last[:-1] + 'ć'
        s['last_name'] = last
        if prefix:
            s['additional_info'] = '; '.join(prefix) + '; ' + s['additional_info']
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def fix_bio_words(soldiers: list[dict], words: Counter) -> list[dict]:
    """A lowercase н read as и: a bio word becomes the known word reached by reading one or two of its i's as n,
    when that word is far more common ("godiie" → "godine", "rođei" → "rođen", "radiik" → "radnik")."""
    cache: dict[str, str] = {}

    def fix(m: re.Match) -> str:
        w = m.group(0)
        lw = w.lower()
        if lw not in cache:
            best = lw
            if 'i' in lw:
                spots = [i for i, ch in enumerate(lw) if ch == 'i']
                cands = {lw[:i] + 'n' + lw[i + 1:] for i in spots}
                cands |= {c[:j] + 'n' + c[j + 1:] for c in cands for j in spots if c[j] == 'i'}
                top = max(cands, key=lambda c: words[c])
                if words[top] >= max(5, 20 * words[lw]):
                    best = top
            cache[lw] = best
        out = cache[lw]
        if out == lw:
            return w
        return out.upper() if w.isupper() else out.capitalize() if w[0].isupper() else out

    n = 0
    for s in soldiers:
        new = re.sub(r'[A-Za-zčćžšđČĆŽŠĐ]{3,}', fix, s['additional_info'])
        n += new != s['additional_info']
        s['additional_info'] = new
    print(f'  н read as и fixed in {n} bios')
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    words, first = _corpus()
    soldiers = repair_capital_c(repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True))))
    return fix_bio_words(fix_names(split_leading_aliases(soldiers), first), words)


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/19-bircanska.pdf',
        brigade_code=23,
        output_path='website/public/19-bircanska-soldiers.json',
        start_page=1,
        end_page=117,
        layout='two_column',
        col_split_x='auto',
        script='cyrillic',
        parse_entry_fn=parse_entry,
        line_filter=keep_line,
        post_fn=post,
    )
