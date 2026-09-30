"""
Parser: Tuzlanski NOP odred (brigade code 25).

Source: "TUZLANSKI NARODNOOSLOBODILAČKI PARTIZANSKI ODRED" (Tuzla, 1988), chapter IV "Spisak boraca"
        znaci.org/00002/403_4.pdf  →  website/public/pdfs/tuzlanski-odred.pdf
Latin. pp. 2-113 the list, pp. 114-122 the name index, then the contents and imprint.
Each page is a grid of two columns of cells, many with a portrait; beside a portrait the name is stacked and the
narrow text is justified:
    ALIHODŽIĆ Omerov ILJAZ,               ALJUKIĆ
    borac, 1923. Lukavac. U Odredu        Đulagin
    od oktobra 1943, poginuo ...          MEHO,        borac,
                                          1921. Prokosovići, ...
Fathers are mostly possessives (Omerov, Mujin), some genitives (Bege). read_cells finds each page's gutter (the
widest word-free band near the middle) and, in each column, a cell as lines that share a left edge and follow
each other at the line pitch.
"""
import re

import pdfplumber

from _margin_entries import split_leading_aliases
from _parser_scaffold import extract_birth_year, _record, repair_lj_ocr, restore_diacritics, run_parser
from pdf_coords import viewer_words

MARK = '⁣'                  # after the first word of a cell's first line
U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'


def _gutter(words: list[dict]) -> float:
    """Middle of the widest x band in 370-470 that the fewest words cross."""
    cross = {g: sum(1 for w in words if w['x0'] < g < w['x1']) for g in range(370, 471)}
    low = min(cross.values())
    runs, cur = [], None
    for g in range(370, 471):
        if cross[g] == low:
            if cur and cur[1] == g - 1:
                cur[1] = g
            else:
                cur = [g, g]
                runs.append(cur)
    a, b = max(runs, key=lambda r: r[1] - r[0])
    return (a + b) / 2


def read_cells(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno in range(start, (end or len(pdf.pages)) + 1):
            page = pdf.pages[pno - 1]
            words = [w for w in viewer_words(page) if not re.fullmatch(r'\d{1,3}', w['text'])]
            page.close()
            if not words:
                continue
            g = _gutter(words)
            for col in ([w for w in words if w['x1'] <= g], [w for w in words if w['x0'] >= g]):
                rows = []
                for w in sorted(col, key=lambda w: (w['top'], w['x0'])):
                    if rows and abs(rows[-1][0]['top'] - w['top']) < 3:
                        rows[-1].append(w)
                    else:
                        rows.append([w])
                cell_x, last_y = None, None
                for row in rows:
                    row.sort(key=lambda w: w['x0'])
                    x, y = row[0]['x0'], row[0]['top']
                    text = ' '.join(w['text'] for w in row)
                    letters = sum(ch.isalpha() for ch in text)
                    if letters < 3 or letters < 0.5 * len(text.replace(' ', '')):      # specks over a portrait
                        continue
                    if re.match(r'^(SPISAK BORACA|TUZLANSKOG|NOP ODREDA)', text):     # the chapter title on p. 2
                        continue
                    if re.search(r'(?i)tuzlanski\s*partizanski', text):               # a photo caption
                        continue
                    # cells are 40pt+ apart; inside one a dropped line leaves a ~20pt gap
                    if cell_x is None or y - last_y > 30 or abs(x - cell_x) > 20:
                        text = re.sub(r'^(\S+)', r'\1' + MARK, text, count=1)
                        cell_x = x
                    lines.append({'text': text, 'x': x, 'y': round(y, 1), 'page': pno})
                    last_y = y
    return lines


def _join_spaced(tokens: list[str]) -> list[str]:
    """Letter-spaced caps beside a portrait: "M EH MED", "FEH IM", "STOJ AN" -> one word."""
    out = []
    for t in tokens:
        if out and re.fullmatch(rf'[{U}]+', t) and re.fullmatch(rf'[{U}]+', out[-1]) and (len(t) <= 3 or len(out[-1]) <= 3):
            out[-1] += t
        else:
            out.append(t)
    return out


def parse_entry(text: str) -> dict:
    """SURNAME [Father] GIVEN [NICKNAME], role, year place. U Odredu ..."""
    text = text.replace(MARK, '')
    # a word broken at the line end ("KARAAHMETO- VIĆ", "od- redu"), not a caps name before a lowercase word
    text = re.sub(rf'([{U}])- ([{U}])|([{L}])- ([{L}])', lambda m: (m.group(1) or m.group(3)) + (m.group(2) or m.group(4)), text)
    end = re.search(rf',|\.(?=\s+[{L}\d])', text)                            # the name ends at a comma or ". borac"
    head, bio = (text[:end.start()], text[end.end():]) if end else (text, '')
    toks = head.split()
    k = next((i for i, t in enumerate(toks[1:5], 1) if t in ('VIĆ', 'VIC', 'IĆ')), 0)
    if k and all(len(t) <= 3 for t in toks[1:k + 1]):
        toks[0:k + 1] = [''.join(toks[0:k + 1])]                              # "OKA NO VIĆ" -> OKANOVIĆ
    last = re.sub(r"[^A-Za-zčćžšđČĆŽŠĐ\-]", '', toks[0].replace('1', 'I').replace('0', 'O')) if toks else ''
    rest = toks[1:]
    if last.endswith('-') and rest:                                          # "HABIBOVIĆ- MUHAREMAGIĆ"
        last += rest.pop(0)
    father = ''
    if rest and re.match(rf'^[{U}][{L}]', rest[0]) and not (len(rest) == 1 and not bio):
        father = rest.pop(0)
        while rest and re.match(rf'^[{L}]', rest[0]):                        # "Me hin", "Šaci rov"
            father += rest.pop(0)
    # names and nicknames are printed in caps; from the first lowercase word it is the bio ("FADIL borac, 1926.")
    low = next((i for i, t in enumerate(rest) if re.match(rf'^[{L}\d]', t)), len(rest))
    rest, spill = rest[:low], rest[low:]
    if not father and rest and re.fullmatch(rf'[{U}]\.?', rest[0]) and len(rest) > 1:
        father = rest.pop(0).rstrip('.')                                     # "DRAGIĆ M. JOVO": the father's initial
    given = [re.sub(r'[^A-Za-zčćžšđČĆŽŠĐ\-]', '', t.replace('1', 'I').replace('0', 'O')) for t in _join_spaced(rest)]
    given = [t for t in given if t]
    nick = given[1:]
    info = ' '.join(spill + [bio.strip()]).strip()
    if nick:
        info = 'zvani ' + ' '.join(n.capitalize() for n in nick) + ('; ' + info if info else '')
    rec = _record(last, given[0] if given else '', father, info)
    return rec


def birth_years(soldiers: list[dict]) -> list[dict]:
    """The year after the duty is the year of birth: "borac, 1921. Lukavac. U Odredu od ..."."""
    for s in soldiers:
        info = s['additional_info']
        m = re.match(r'^(?:zvani [^;]+; )?[^.\d]*?\b(1[89]\d\d)\b', info)
        joined = info.find('U Odredu')
        if m and not s.get('birth_year') and (joined < 0 or m.start(1) < joined):
            s['birth_year'] = m.group(1)
    return soldiers


def post(soldiers: list[dict]) -> list[dict]:
    return birth_years(split_leading_aliases(repair_lj_ocr(restore_diacritics(soldiers))))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/tuzlanski-odred.pdf',
        brigade_code=25,
        output_path='website/public/tuzlanski-odred-soldiers.json',
        start_page=2,
        end_page=113,
        script='latin',
        extract_fn=read_cells,
        entry_start_re=re.compile(r'^\S+' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
