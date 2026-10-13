"""
Parser: Prva proleterska brigada (brigade code 1), second book: the brigade's fighters on the day it was formed.

Source: Miloš Vuksanović, "Prva proleterska brigada" (Narodna knjiga, ISI, Pobjeda; Beograd-Titograd 1981; znaci.org
        00003/382.pdf, its pages 463-521, book pp. 433-492, "Prilozi") -> website/public/pdfs/prva-proleterska-stroj-u-rudom.pdf.
        "Borci brigade na dan njenog osnivanja - stroj u Rudom": the men and women in the line-up at Rudo on 21 December
        1941, under the brigade's staff and medical sections, then each battalion's staff and companies. znaci.org
        re-typeset the book from its OCR, so the page shows the text layer's slips ("SR{1", "Pjenovou", "Seikovićima").
            2. Kljajić Filip Fića*, politički komesar brigade, rođen 1913. u Tremušnjaku, Petrinja, SRH, obućar, član
            KPJ od 1936. Poginuo 5. jula 1943. kod Zvornika, na dužnosti političkog komesara 1. proleterske divizije.
            Narodni heroj.
The name: surname, given name, a nickname, "dr" before the given name, a second name in brackets ("Pihler Lujza
(Denić Borka)"); ". . . Mladenko": the surname not known. An asterisk after the name marks one who fell in the war
(the footnote: "Poginuo u toku NOR-a"). Places carry their republic of 1981 (SRS, SRCG, SRH, SRBiH, SRM). The section
gives `unit_detail` in the form the brigade's other books use ("2. četa, 1. bataljon").

The records get IDs from 0001200001 (the knjiga's three volumes: 000001-, Borci Sutjeske: 100001-).
"""
import re
from collections import Counter, defaultdict

from _parser_scaffold import _record, restore_diacritics, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
BATTALIONS = [(r'^PRVI\b.*BATALJON', 1), (r'^DRUGI\b.*BATALJON', 2), (r'^TREĆI\b.*BATALJON', 3),
              (r'^ČETVRTI\b.*BATALJON', 4), (r'^PETI\b.*BATALJON', 5), (r'^ŠESTI\b.*BATALJON', 6)]
BRIGADE = {'ŠTAB PRVE PROLETERSKE BRIGADE': 'štab brigade', 'BRIGADNI SANITET': 'brigadni sanitet',
           'SANITETSKO ODJELJENJE': 'sanitetsko odjeljenje', 'HIRURŠKA EKIPA': 'hirurška ekipa'}
ORDINAL = {'Prva': 1, 'Druga': 2, 'Treća': 3, 'Četvrta': 4, 'Peta': 5, 'Šesta': 6}
# names the re-typesetting broke apart or marked with a stray sign, as the page prints them
FIX = {'Alf andari Isak': 'Alfandari Isak', 'B orj ano vic Ziva': 'Borjanović Živa', 'M and il Isak': 'Mandil Isak',
       'Pol di Ivan': 'Poldi Ivan', 'Dulie dir Vojislav': 'Dulić dr Vojislav', 'Danilović Petar* Mornar': 'Danilović Petar Mornar*',
       'Jovanović - Konstatinović': 'Jovanović-Konstatinović', 'Vučinić - Milu tino vić': 'Vučinić-Milutinović',
       'Todorović D.ragomir': 'Todorović Dragomir',
       'Tripfktmć Jezdi mir': 'Tripković Jezdimir', 'Saković Viidalk': 'Šaković Vidak'}   # the knjiga: Tripković Milenka Jezdimir, Bogojevići, Arilje
SURNAME_END = re.compile(r'(?:ić|ović|ević|ski|ska|ac)$')
_state = {'battalion': 0, 'part': '', 'detail': ''}
_margin: dict = defaultdict(lambda: 999.0)
_foot: dict = {}
_first: Counter = Counter()
_last: Counter = Counter()


def corpus() -> None:
    import glob
    import json
    for f in glob.glob('website/public/*soldiers.json'):
        if not f.replace('\\', '/').endswith('/prva-proleterska-soldiers.json'):
            for s in json.load(open(f, encoding='utf-8')):
                _first[s['first_name'].upper()] += 1
                _last[s['last_name'].upper()] += 1


def prepare(lines: list[dict]) -> None:
    for ln in lines:
        _margin[ln['page']] = min(_margin[ln['page']], ln['x'])
    for ln in lines:                                          # the footnotes at a page's foot, under "* ..."
        if ln['text'].strip().startswith('*') and ln['x'] > _margin[ln['page']] + 12:
            _foot[ln['page']] = min(_foot.get(ln['page'], 1e9), ln['y'])


def detail() -> str:
    b, part = _state['battalion'], _state['part']
    if not b:
        return part
    return f'{part}, {b}. bataljon' if part else f'{b}. bataljon'


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if ln['page'] in _foot and ln['y'] >= _foot[ln['page']] - 1:
        return False                                          # footnotes
    if ln['page'] == 1 and ln['y'] < 420:
        return False                                          # the list's title
    if re.fullmatch(r'[\d\W]{1,6}', t):
        return False
    if t in BRIGADE:
        _state.update(battalion=0, part=BRIGADE[t])
        return False
    for rx, n in BATTALIONS:
        if re.match(rx, t):
            _state.update(battalion=n, part='štab bataljona')
            return False
    sub = re.fullmatch(r'(Štab bataljona|Bataljonski sanitet|(?:(Prva|Druga|Treća|Četvrta|Peta|Šesta)(?:\s*[—–-]\s*([A-ZČĆŽŠĐ][a-zčćžšđ]+))?|([A-ZČĆŽŠĐ][a-zčćžšđ]+)) četa)\*?', t)
    if sub and not re.match(r'^\d', t):
        if sub.group(1) in ('Štab bataljona', 'Bataljonski sanitet'):
            part = sub.group(1).lower()
        elif sub.group(2):
            n = ORDINAL[sub.group(2)]
            part = f'{n}. {sub.group(3).lower()} četa' if sub.group(3) else f'{n}. četa'
        else:
            part = f'{sub.group(4).lower()} četa'              # "Kruševačka četa", "Posavska četa"
        _state['part'] = part
        return False
    if re.fullmatch(r'\d \d', t):
        _state['number'] = t.replace(' ', '')                    # "4 9" on a line of its own, the name under it
        return False
    if _state.get('number'):
        t, _state['number'] = f"{_state['number']}. {t}", ''
        ln['x'] = _margin[ln['page']] + 20
    t = re.sub(r'^(\d)-(\d)\.', r'\1\2.', t)                         # "4-8. Starostin"
    t = re.sub(r'^(\d{1,3})\s+(?=[A-ZČĆŽŠĐ][a-zčćžšđ])', r'\1. ', t) if ln['x'] > _margin[ln['page']] + 8 else t   # "28 Leksendrić"
    if re.match(r'^\d{1,3}\.\s+\S', t) and ln['x'] > _margin[ln['page']] + 8:
        t = f'§{detail()}§ ' + t
    ln['text'] = t
    return True


def parse(text: str) -> dict:
    section = text[1:text.index('§', 1)]
    text = text[text.index('§', 1) + 1:].strip()
    n = re.match(r'^(\d{1,3})\.', text)
    text = re.sub(r'^\d{1,3}\.\s*', '', text)
    for wrong, right in FIX.items():
        if text.startswith(wrong):
            text = right + text[len(wrong):]
    text = re.sub(rf'(?<=[{L}])-\s+(?=[{L}])', '', text)                     # "pu- blicista"
    unknown = bool(re.match(r'^[.\s]{2,}', text))
    text = re.sub(r'^[.\s]+', '', text)                                       # ". . . Mladenko": no surname
    m = re.match(r'^(?P<head>[^,]+?)\s*(?P<star>\*)?\s*(?:,|(?=\s+borac\b))\s*(?P<info>.*)$', text)
    head, info = (m.group('head'), m.group('info')) if m else (text, '')
    asterisk = bool(m and m.group('star')) or head.endswith('*')
    head = head.rstrip('*').strip().replace("'", '').replace('*', '')
    quoted = re.findall(r'»([^«]+)«', head)                                     # "»David«", "Branko »Doktor«": a nickname
    head = re.sub(r'»[^«]+«', '', head).strip(' .')
    other = re.search(r'\(([^)]+)\)', head)
    if other:
        head = (head[:other.start()] + head[other.end():]).strip()            # "Pihler Lujza (Denić Borka)"
    tokens = head.split()
    dr = any(t.lower() == 'dr' for t in tokens)
    father = next((t for t in tokens if re.fullmatch(rf'[{U}]\.', t)), '')         # "Božović P. Radomir Raco"
    words: list[str] = []
    for t in tokens:
        if t.lower() == 'dr' or t == father:
            continue
        if words and re.fullmatch(rf'[{L}]{{1,3}}', t):
            words[-1] += t                                                      # "Ljubom ir", "Spaso je", "Zi vor ad"
        else:
            words.append(t[0].upper() + t[1:] if t[0].islower() else t)         # "čupo": a capital the OCR lost
    words = [hook(w, _last if i == 0 else _first) for i, w in enumerate(words)]
    nick: list[str] = list(quoted)
    if not words and quoted:
        words, nick, unknown = [quoted[0]], [], True                            # "»David«...": only the nickname
    if not words:
        return _record('', '', '', info)
    if unknown or len(words) == 1:
        last, given, nick = '', words[0], words[1:]
    elif len(words) == 2:
        last, given = words
        nick = nick
    elif SURNAME_END.search(words[1]) and _first[words[1].upper()] < 3 and _first[words[2].upper()] >= 3:
        last, given, nick = words[0] + ' ' + words[1], words[2], words[3:] + nick   # "Skopskaja Ratković Bosa"
    else:
        last, given, nick = words[0], words[1], words[2:] + nick                # "Kljajić Filip Fića"
    notes = (['dr.'] if dr else []) + (['zvani ' + ' '.join(nick)] if nick else []) + (['ili ' + other.group(1)] if other else [])
    rec = _record(last or '?', given, father.rstrip('.'), '; '.join(notes + [info] * bool(info)))
    rec['_n'] = int(n.group(1)) if n else 0
    rec['_asterisk'] = asterisk
    rec['_no_surname'] = not last
    y = re.search(r'\brođen[a]?\s+(1[89]\d\d)\b', info)
    rec['birth_year'] = y.group(1) if y else ''
    if section:
        rec['unit_detail'] = section
    return rec


HOOKED = {'Z': 'Ž', 'C': 'ČĆ', 'S': 'Š', 'D': 'Đ'}


def hook(word: str, known: Counter) -> str:
    """A capital Ž, Č, Ć, Š or Đ the OCR printed without its hook: "Zivadin", "Cirović", "Cordaš" (where the other units
    spell it with the hook at least five times as often as without)"""
    if word.startswith('Ziv'):
        return 'Ž' + word[1:]
    for letter in HOOKED.get(word[:1], ''):
        if known[letter + word[1:].upper()] >= 3 and known[letter + word[1:].upper()] >= 5 * known[word.upper()]:
            return letter + word[1:]
    return word


def post(soldiers: list[dict]) -> list[dict]:
    # every section numbers its people from 1: a gap is an entry the reader missed
    by = defaultdict(list)
    for s in soldiers:
        by[s.get('unit_detail', '')].append(s.pop('_n'))
    for sec, ns in by.items():
        ns = sorted(ns)
        gaps = sorted(set(range(1, ns[-1] + 1)) - set(ns))
        if gaps or len(ns) != len(set(ns)):
            print(f'   {sec}: missing {gaps}, repeated {[x for x in set(ns) if ns.count(x) > 1]}')
    soldiers = restore_diacritics(soldiers)
    for s in soldiers:
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
        if s.pop('_no_surname', False):
            s['last_name'] = ''
            s['full_name'] = s['first_name']
    return soldiers


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='website/public/pdfs/prva-proleterska-stroj-u-rudom.pdf',
        brigade_code=1,
        output_path='website/public/prva-proleterska-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        entry_start_re=re.compile(r'^§'),
        parse_entry_fn=parse,
        prepare_fn=prepare,
        line_filter=keep,
        post_fn=post,
        asterisk_marks_death=True,
        id_start=200001,
        keep_other_sources=True,
    )
