"""
Franc Benedik (ed.), *Šenčursko območje med nemško okupacijo in narodnoosvobodilnim bojem* II (znaci.org 00003/1049,
its PDF pp. 121-130 and 143-146 → website/public/pdfs/sencur-padli-borci.pdf, book pp. 359-368 and 381-384), a book
across units, two of its lists, two columns, a name in capitals over each entry:
    Alda Razpotnik-Tika, "Padli borci, aktivisti in druge žrtve fašističnega nasilja z območja občine Šenčur" (PDF pp.
        1-10): the dead of the Šenčur municipality's villages, each under its village (Šenčur, Srednja vas, Milje, Luže,
        Visoko, Hotemaže, Olševek, Voglje, Voklo, Prebačevo, Hrastje), a bio each: "Janko BELEHAR -Smrekar / roj. 19. 2.
        1924 v Šenčurju, kmečki sin, samski, mladinski aktivist OF. Odšel v partizane v Kokrško četo 10. 12. 1941 ...".
        A mixed list: the fighters go in, the OF's and the party's people as activists (`role`), the hostages, the
        deported and the others the occupier killed with no part in the movement stay out (the user's rule for mixed
        lists, 2026-10-14 and 2026-10-19);
    Franc Štefe-Miško, "Borci Kokrške čete" (PDF pp. 11-14): every fighter of the Kokrška četa, December 1941 - spring
        1942, with his last home, the day he came to the company and how he fell: "Stane BEČAN -Fajfca / Tržič, v četi
        od 10. 12. 1941, padel v Udin borštu 16. 4. 1942". One who fled the Kokrški odred and became a Gestapo agent is
        left out (the user's rule on traitors). The company became the first Kokrški odred (unit 171).
Out: the same book's list of the hostages shot in Šenčur (book pp. 371-373), the captions and the memorial plaques
printed beside the lists.

The text layer sets a word with a caron a point higher than its line: the lines are built by the words' baselines.

Output: data-extraction/znaci/sencur-padli-borci-entries.json (IDs 9106xxxxxx: the dead from 000001, the company's
fighters from 001001, in the book's order, left column first).
Usage: python data-extraction/parse_sencur.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

PDF = 'sencur-padli-borci.pdf'
OUT = HERE / 'znaci' / 'sencur-padli-borci-entries.json'
PREFIX = '9106'
DEAD = ('Padli borci, aktivisti in druge žrtve fašističnega nasilja z območja občine Šenčur', range(1, 11), 0, 359)
COMPANY = ('Borci Kokrške čete', range(11, 15), 1000, 371)       # (the list, its PDF pages, the IDs' base, book - PDF)
VILLAGES = {'ŠENČUR': 'Šenčur', 'SREDNJA VAS': 'Srednja vas', 'MILJE': 'Milje', 'LUŽE': 'Luže', 'VISOKO': 'Visoko',
            'HOTEMAŽE': 'Hotemaže', 'OLŠEVEK': 'Olševek', 'VOGLJE': 'Voglje', 'VOKLO': 'Voklo',
            'PREBAČEVO': 'Prebačevo', 'HRASTJE': 'Hrastje', 'TRBOJE': 'Trboje'}
U, L = 'A-ZČŠŽĆĐ', 'a-zčšžćđ'
NAME = re.compile(rf'^([{U}][{L}]+)\s*([{U}]{{2,}}(?:\s?-\s?[{U}]{{2,}})?)\b\s*(.*)$')
TITLE_NAME = re.compile(rf'^([{U}][{L}]+) ([{U}][{L}]+)\s*(.*)$')         # "Jože Ogris": a surname set small
# the site's units a bio names
UNITS = [(r'Gradnikov', 64), (r'Kosovelov', 142), (r'Cankarjev\w* bataljon', 170), (r'Kokršk\w+ (?:odred|čet)', 171),
         (r'Šercerjev', 141), (r'Tomšičev', 70), (r'Cankarjev\w* brigad', 61), (r'Gubčev', 62), (r'Bračičev', 69),
         (r'Zidanškov', 65), (r'Škofjelošk\w+ odred', 66), (r'Prv\w+ proletarsk\w+ brigad', 1)]
FIGHTER = re.compile(r'(?i)(?<!Maistrov )\bbor(?:ec|ka|ca|cem)\b|\b(?:odšel|odšla|odšli|šel|stopil|stopila)\s+(?:v|k)\s+'
                     r'(?:partizan|enot|NOV|Kokršk|Cankarjev|Gorenjsk|Selšk)|\bv partizane\b|\bk partizanom\b|'
                     r'\bv partizanih\b|odred|\bbrigad|\bbataljon|\bdivizij|\bkomandir|\bkomandant|politkomisar|'
                     r'\bvodnik|\boficir|kurirske postaje|Vojsk\w+ državne varnosti')
ACTIVIST = re.compile(r'aktivist|\bOF\b|član\w* KP|\bKP\b|SKOJ|mladinsk\w+ organizacij|\bodbor|sekretar|terensk|kurir|'
                      r'ilegal|sodelova\w+\s+(?:z|s)\s+(?:OF|partizan)')
# the roster's intro, whose last lines head the right column of its first page
INTRO = re.compile(r'navedbo zadnjega bivališča|objavljeni v knjižici|^1989, str\. 31-38')
TRAITOR = re.compile(r'gestapovec|izdajal|izdal\b|postal domobranec')
DEATH = re.compile(r'\b(?:padel|padla|umrl|umrla|ustrelil\w*|ustreljen\w*|obešen\w*|zgorel\w*|ubil\w*|ubit\w*|usmrčen\w*|'
                   r'sežgal\w*|življenje|podlegel|ponesrečil)')


def lines_of(page) -> list[dict]:
    """the page's lines by column, left first: their text, size, place and the words' baselines"""
    words = viewer_words(page, extra_attrs=['size'])
    # the right column's left edge, where most of its lines start (a left line's last word may stand a few points
    # short of it: "Odšel v")
    edge = Counter(round(w['x0']) for w in words if w['x0'] > page.width / 2 - 25).most_common(1)[0][0]
    out = []
    for side in (False, True):
        col = sorted([w for w in words if (w['x0'] >= edge - 3) == side], key=lambda w: w['bottom'])
        rows = []
        for w in col:
            if rows and abs(w['bottom'] - rows[-1][0]['bottom']) < 3.5:
                rows[-1].append(w)
            else:
                rows.append([w])
        for r in rows:
            r.sort(key=lambda w: w['x0'])
            out.append({'text': ' '.join(w['text'] for w in r).strip(), 'x': round(r[0]['x0'], 1),
                        'y': round(min(w['top'] for w in r), 1),
                        'size': Counter(round(w['size'], 1) for w in r).most_common(1)[0][0]})
    return out


def is_name(line: dict, nxt: dict | None, company: bool) -> bool:
    t = line['text']
    if t in VILLAGES or not (NAME.match(t) or TITLE_NAME.match(t)):
        return False
    follows = (nxt or {}).get('text', '')
    if company:
        return bool(NAME.match(t)) or 'v četi' in follows
    return follows.startswith(('roj', 'p. d.')) or (bool(NAME.match(t)) and line['size'] >= 9.7)


def read(pages, company: bool) -> list[dict]:
    entries, village, cur = [], '', None
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno in pages:
            ls = lines_of(pdf.pages[pno - 1])
            for i, ln in enumerate(ls):
                t, size = ln['text'], ln['size']
                if not t or re.fullmatch(r'\d{3}', t):
                    continue
                if t in VILLAGES:
                    village, cur = VILLAGES[t], None
                    continue
                if is_name(ln, ls[i + 1] if i + 1 < len(ls) else None, company):
                    cur = {'head': t, 'lines': [], 'village': village, 'page': pno, 'x': ln['x'], 'y': ln['y']}
                    entries.append(cur)
                    continue
                if cur is None or 8.0 <= size < 9.2 or size >= 10.3 or INTRO.search(t):
                    continue                                    # a caption, a title, the roster's intro
                if size < 8.0 and not re.fullmatch(rf'[{L}][{L}{U}\s.,–-]*\.', t):
                    continue                                    # a memorial plaque, the specks of a photograph
                if t.startswith('p. d.') and not cur['lines']:
                    cur['head'] += ', ' + t                     # "Janko OSELJ - Potapljač, / p. d. Godelnikov"
                else:
                    cur['lines'].append(t)
    return entries


VOCAB: Counter = Counter()
# the text layer's glued and split words
GLUE = [(r'\b(Odšel|odšel|odšla)v\b', r'\1 v'), (r'\bZOF\b', 'Z OF'), (r'\bso delova', 'sodelova'), (r'\bV stopil', 'Vstopil'),
        (r'skiodred', 'ski odred'), (r'dvehotrok', 'dveh otrok'), (r'Vogljanskigmajni', 'Vogljanski gmajni'),
        (r'domobranskemnapadu', 'domobranskem napadu'), (r'zatočiščepartizanom', 'zatočišče partizanom'),
        (r'Bašeljskemsedlu', 'Bašeljskem sedlu'), (r'mladinskegaodbora', 'mladinskega odbora'),
        (r'spremljalranjence', 'spremljal ranjence'), (r'\b(pa|si|se)je\b', r'\1 je'), (r'\(v odnik\)', '(vodnik)'),
        (r'\bkrnet\b', 'kmet'), (r'\brajon ske\b', 'rajonske'), (r'\bnji mi\b', 'njimi')]


def joined(lines: list[str]) -> str:
    """the bio's lines as one text; a word broken at a line's end joined again where the text layer lost the hyphen
    ("sam / ski", "mladin / ske"), unless both halves are words the book uses and their join is not ("kot / borec")"""
    text = ''
    for t in lines:
        a = re.search(rf'([{U}{L}]+)$', text)
        b = re.match(rf'([{L}]+)', t)
        if text.endswith(('-', '­')) and not text.endswith(' -'):
            text = text.rstrip('-­') + t
        elif a and b and (VOCAB[(a.group(1) + b.group(1)).lower()]
                          or not (VOCAB[a.group(1).lower()] and VOCAB[b.group(1).lower()])):
            text += t
        else:
            text += (' ' if text else '') + t
    for a, b in GLUE:
        text = re.sub(a, b, text)
    return re.sub(r'\s+', ' ', text).strip()


def vocabulary() -> None:
    """the words of the lists' own lines and of the site's entries (the Slovene units' among them)"""
    for f in (HERE.parent / 'website' / 'public').glob('*soldiers.json'):
        for s in json.loads(f.read_text(encoding='utf-8')):
            VOCAB.update(w.lower() for w in re.findall(rf'[{L}{U}]{{2,}}', s.get('additional_info') or ''))
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for page in pdf.pages:
            for ln in lines_of(page):
                words = re.findall(rf'[{L}{U}]+', ln['text'])
                VOCAB.update(w.lower() for w in words[1:-1])     # not a line's ends, which may be broken words


def name_of(head: str) -> tuple[str, str, str, str]:
    """given name, surname, nickname, the rest of the heading ("p. d. Godelnikov", "st.", "ml.")"""
    m = NAME.match(head) or TITLE_NAME.match(head)
    first, last, rest = m.group(1), m.group(2), m.group(3).strip(' ,')
    last = '-'.join(p.capitalize() for p in re.split(r'\s?-\s?', last))
    nick = ''
    n = re.match(r'^[-•]\s*([^,]+?)\s*(?:,|$)\s*(.*)$', rest)
    if n:
        nick, rest = n.group(1).strip(), n.group(2)
    return first, last, nick, rest.strip(' ,')


def years(text: str) -> tuple[str, str]:
    born = re.search(r'roj\.\s*(?:\d{1,2}\.\s?[\dl]{1,2}\.\s?)?(1[89]\d\d)', text)
    death = ''
    for m in DEATH.finditer(text):
        y = re.search(r'(19[34]\d)', text[m.start():m.start() + 70]) or re.search(r'(19[34]\d)', text[max(0, m.start() - 40):m.start()])
        if y:
            death = y.group(1)
    return (born.group(1) if born else ''), death


def main():
    vocabulary()
    out, counts = [], Counter()
    for (title, pages, base, offset), company in ((DEAD, False), (COMPANY, True)):
        for no, e in enumerate(read(pages, company), 1):
            first, last, nick, rest = name_of(e['head'])
            bio = joined(e['lines']).replace('roj. l.', 'roj. 1.')
            printed = f"{first} {last.upper()}" + (f' - {nick}' if nick else '') + (f', {rest}' if rest else '')
            role = None
            if TRAITOR.search(bio):
                counts['out (traitor)'] += 1
                print('  out (traitor):', printed, '|', bio[:110])
                continue
            if not company and not FIGHTER.search(bio):
                if ACTIVIST.search(bio):
                    role = 'activist'
                else:
                    counts['out (victim)'] += 1
                    print('  out:', printed, '|', bio[:110])
                    continue
            born, died = years(bio)
            units = sorted({u for pat, u in UNITS if re.search(pat, bio)} | ({171} if company else set()))
            rec = {'soldier_id': f'{PREFIX}{base + no:06d}', 'name': ' '.join(x for x in (last, first) if x)
                   + (f' — {nick}' if nick else ''), 'last_name': last, 'first_name': first, 'also': [], 'nick': nick,
                   'fathers_name': '', 'birth_year': born, 'born_in': '', 'death_year': died, 'survived': False,
                   'units': units, 'list': title,
                   'additional_info': f"{title}{', ' + e['village'] if e['village'] else ''}: {printed.rstrip('.')}. {bio}",
                   'pdf_file': PDF, 'pdf_page': e['page'], 'pdf_x': e['x'], 'pdf_y': e['y'],
                   'source_page': e['page'] + offset}
            if role:
                rec['role'] = role
            rec['_key'] = (last, rest)
            rec['_home'] = bio.split(',')[0] if company else e['village']       # "Visoko pri Šenčurju", "Visoko"
            out.append(rec)
            counts[f"{'company' if company else 'dead'}: {role or 'fighter'}"] += 1
    # a man of the company who is among the dead too is one entry, the dead list's, with the company's line after it
    dead = [r for r in out if r['soldier_id'][4:7] == '000']
    for c in [r for r in out if r['soldier_id'][4:7] == '001']:
        # (his home and the village agree: not the roster's author, Franc Štefe-Miško of Šenčur, against the Franc
        # Štefe of Voklo who died at Mauthausen)
        fits = [d for d in dead if d['_key'] == c['_key'] and (d['first_name'] == c['first_name'] or c['nick'] and d['nick'] == c['nick'])
                and d['_home'] and c['_home'].startswith(d['_home'])]
        if len(fits) == 1 and not (fits[0]['nick'] and c['nick'] and fits[0]['nick'] != c['nick']):
            d = fits[0]
            d['additional_info'] += ' ' + c['additional_info'] + '.'
            d['units'] = sorted(set(d['units']) | {171})
            d.pop('role', None)                             # a fighter of the company, whatever the other list says
            if not d['death_year']:
                d['death_year'] = c['death_year']
            c['_joined'] = d['soldier_id']
            counts['joined'] += 1
    out = [r for r in out if not r.pop('_joined', None)]
    for r in out:
        r.pop('_key')
        r.pop('_home')
    stats = entry_boxes.fill_boxes(out)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(dict(counts), '->', OUT.name, len(out))
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")


if __name__ == '__main__':
    main()
