"""
Parser: Užički NOP odred "Dimitrije Tucović" (brigade code 26) — the fallen, 1941-1945.

Source: monograph of the Užice partisan detachment, chapter "Spisak boraca Užičkog partizanskog odreda
        »Dimitrije Tucović« poginulih u narodnooslobodilačkom ratu 1941-1945."
        znaci.org  →  website/public/pdfs/uzicki-odred.pdf
Single column. p. 1 the introduction, pp. 2-80 the list (book pp. 343-423).
    АВРАМОВИЋ Рајка СВЕТОЛИК Љубо, борац 3. рачанске чете, земљорадник, рођен 1922. у Гвоздцу, ...
    АНАЋИЋ М. МИОДРАГ Мића, борац 1. ужичке чете »Радоје Марић«, ...          (a nickname after the name)
The text layer mixes scripts: most caps names are Cyrillic, some Latin, and some Cyrillic capitals were read as
the Latin letters they look like ("ABPAMOBHR" = АВРАМОВИЋ, "AAEKCHR" = АЛЕКСИЋ, "AVUIAH" = ДУШАН), which
decode_lookalikes turns back. Continuation lines are indented (_margin_entries).
"""
import itertools
import json
import re
from collections import Counter
from pathlib import Path

from _margin_entries import MarginEntries, fix_cyrillic_ocr_line, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()

# Latin letters (either case) and signs the OCR used for Cyrillic ones: the letters each can stand for (in Latin)
LOOKALIKE = {'A': ('A', 'L', 'D'), 'B': ('V', 'B'), 'C': ('S',), 'E': ('E',), 'H': ('N', 'I'), 'K': ('K',), 'M': ('M',),
             'O': ('O',), 'P': ('R',), 'T': ('T',), 'X': ('H',), 'Y': ('U',), 'J': ('J',), 'R': ('Ć',), 'U': ('U',),
             '4': ('Č',), 'III': ('Š',), 'UI': ('Š',), 'IU': ('Š',), 'A>': ('LJ',), 'H>': ('NJ',), 'N': ('N', 'I'), 'I': ('I',)}
LOOKALIKE_WORD = re.compile(r'(?:A>|H>|III|UI|IU|[ABCEHIKMNOPTXYJRU4])+')
TELL = re.compile(r'4|>|[XY]|H?R$|UI|IU|III')          # can't be a Serbian Latin spelling: "-BHR", "4", "A>"


def _names():
    last, other = Counter(), Counter()
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != 'uzicki-odred-soldiers.json':
            for s in json.loads(f.read_text(encoding='utf-8')):
                last[s['last_name'].upper()] += 1
                other[s['first_name'].upper()] += 1
    return last, other


LAST, FIRST = _names()


def decode(word: str, known: Counter) -> str | None:
    """A word written in Latin look-alikes of Cyrillic letters, read back: the reading the corpus knows best;
    for a word that can't be Latin, else "-HĆ" -> "-IĆ", H -> N, A -> A. None when it stays as it is."""
    w = word.upper()
    if not LOOKALIKE_WORD.fullmatch(w):
        return None
    parts = re.findall(r'A>|H>|III|UI|IU|.', w)
    options = [LOOKALIKE[p] for p in parts]
    if sum(len(o) > 1 for o in options) <= 7:
        best = max((''.join(c) for c in itertools.product(*options)), key=lambda c: known[c])
        if known[best] and (TELL.search(w) or not known[w]):
            return best
    if not TELL.search(w):
        return None
    return re.sub(r'NĆ$', 'IĆ', ''.join(o[0] for o in options))


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t) or ln['y'] < 125:          # page numbers; a running head on some pages
        return False
    t = t.replace('L>', 'LJ').replace('l>', 'lj').replace('N>', 'NJ').replace('n>', 'nj')      # Љ, Њ read as Л>, Н>
    t = fix_cyrillic_ocr_line(t)
    if ln['x'] <= me.left[(ln.get('file'), ln['page'])] + me.margin_tol:
        head, sep, rest = t.partition(',')
        head = re.sub(r' (?=[4>])', '', head)                    # "BU 4HREBHR": Ч read as 4 split the word
        words = head.split(' ')
        for i, w in enumerate(words):
            core = w.rstrip('.')
            if len(core) >= 3:
                parts = core.split('-')                           # "AUKHR-CTAJHR": each surname on its own
                reads = [decode(p, LAST if i == 0 else FIRST) if len(p) >= 3 else None for p in parts]
                if any(reads):
                    read = '-'.join(r or p for r, p in zip(reads, parts))
                    words[i] = (read if core.isupper() or i == 0 or not core[1:].islower() else read.capitalize()) + w[len(core):]
        t = ' '.join(words) + sep + rest
    ln['text'] = t
    return me.mark(ln)


def nicknames(soldiers: list[dict]) -> list[dict]:
    """"SVETOLIK Ljubo", "MILIVOJE Mile Štule": title-case words after the caps given name are nicknames."""
    for s in soldiers:
        words = s['first_name'].split()
        if len(words) > 1:
            s['first_name'] = words[0]
            s['additional_info'] = 'zvani ' + ' '.join(words[1:]) + ('; ' + s['additional_info'] if s['additional_info'] else '')
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '4-srpska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    # Ћ read as К/В in the Latin-read names ("BOKIV", "AJDAČIK"): "-ik"/"-iv" surnames are rare here
    soldiers = repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True)))
    return nicknames(lone_names_to_given(split_leading_aliases(soldiers), *name_counts()))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/uzicki-odred.pdf',
        brigade_code=26,
        output_path='website/public/uzicki-odred-soldiers.json',
        start_page=2,
        end_page=80,
        layout='single',
        script='cyrillic',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
