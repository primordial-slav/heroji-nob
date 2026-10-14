"""
Parser: Kokrški odred (brigade code 171), its second list: the first Kokrški odred, 18 June 1942 - January 1943.

Source: Ivan Jan, "Kokrški odred - narodnoosvobodilni boj pod Karavankami" I (Knjižnica NOV in POS 26/4; znaci.org
        00003/1047.pdf, the volume's second part) →  website/public/pdfs/kokrski-odred-1.pdf (book pp. 509-525):
        "Seznam borcev Kokrškega odreda prve sestave", numbered, each entry hanging, by staff, battalion and company:
            2. Blejec Matija-Matevž (drugo ime: Kamnikar Silvo)
               Mengeš, komandant od septembra 1942 do 24. 12. 1942, ko je padel na Kostanjski planini v Tuhinjski
               dolini, narodni heroj.
        The place after the name is where he was born or lived before he joined, the place at the end where a
        survivor lives now (the book's footnote). A man counted under the odred's staff is repeated, unnumbered, under
        his battalion's ("štet pri štabu odreda"); the repeat is left out, and so is "Neznan borec", the fighter the
        book could not name.
The unit's first list, the second odred of 1944-45, is parse_kokrski_odred.py; this one keeps to its own ID range.
"""
import re

from _parser_scaffold import _record, extract_lines_single_column, run_parser

U, L = 'A-ZČĆŽŠĐ', 'a-zčćžšđ'
HEAD = re.compile(rf'^(?:\d{{1,3}}|J|l)\.\s+[{U}šžč]')                       # every entry is numbered


def extract(pdf_path: str, start: int, end: int | None) -> list[dict]:
    lines = extract_lines_single_column(pdf_path, start, end)
    out, top, sub, skip_note = [], '', '', False
    for i, ln in enumerate(lines):
        t = ln['text'].strip().replace('A vgust', 'Avgust')
        if re.fullmatch(r'\d{3}', t) or t.startswith('SEZNAM BORCEV'):
            continue
        if re.match(r'^Dezer-', t):                                      # the totals table under the list
            break
        if t.startswith('•') or t.startswith('* Kraj'):
            skip_note = True
            continue
        if skip_note and t.startswith('v NOV, kraj na koncu'):
            skip_note = False
            continue
        if re.fullmatch(rf'[\dl]\.\s+\([{U}]+\)\s+BATALJON|[{U}\s().\d]+BATALJON', t):
            top, sub = re.sub(r'^l\.', '1.', t).title().replace('Bataljon', 'bataljon'), ''
            continue
        if t.endswith(':') and len(t) < 60:
            sub = re.sub(r'^l\.', '1.', t.rstrip(':'))
            continue
        nxt = lines[i + 1]['text'] if i + 1 < len(lines) else ''
        starts = bool(HEAD.match(t)) or ('(štet pri' in nxt and re.match(rf'^[{U}{L}][{L}]+ [{U}][{L}]+', t))
        ctx = ', '.join(x for x in (top, sub) if x)
        out.append(dict(ln, text=(f'§x§{ctx}§ ' + t + ' ¶' if starts else t)))   # ¶: the name's line ends
    return out


def parse_entry(text: str) -> dict:
    m = re.match(r'^§x§([^§]*)§\s*(.*)$', text, re.S)
    ctx, t = m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip()
    if 'štet pri' in t or re.match(r'^\S+\s+Neznan borec', t):
        return {}                                                   # the staff's repeat; the unnamed fighter
    t = re.sub(r'^[\dlJ]{1,3}\.\s+', '', t)
    t = re.sub(r'(?<=\d\. )l\.', '1.', t).replace(':Z', 'Ž')
    head, _, bio = t.partition(' ¶')
    head = re.sub(r'^([{U}{L}][{L}]+) \(([{U}][{L}]+)\)'.format(U=U, L=L), r'\1, roj. \2', head)   # "Juvan (Rožanc) Milan"
    nm = re.match(rf'^([{U}{L}][{L}]+(?:,\s*roj\.\s*[{U}][{L}]+)?)\s+(dr\.\s+)?([{U}][{L}]+)(?:-([{U}][{L}]+(?: [{U}][{L}]+)?))?'
                  rf'(\s+(?:st|ml)\.)?(?:\s+\(([^)]*)\))?\s*$', head.strip())
    if not nm:
        one = re.match(rf'^([{U}][{L}]+)\s+\(priimek neugotovljen\)\s*$', head.strip())   # "Iztok (priimek neugotovljen)"
        if not one:
            return {}
        last, given, alias, age, other, dr = one.group(1), '', None, None, 'priimek neugotovljen', None
    else:
        last, dr, given, alias, age, other = nm.groups()
    bio = bio.replace('Zg. ', 'Zg. ').replace('Sp. ', 'Sp. ').replace('Sv. ', 'Sv. ')
    last = last[0].upper() + last[1:]
    married = re.search(r',\s*roj\.\s*([{U}][{L}]+)'.format(U=U, L=L), last)
    if married:                                                     # "Peraič, roj. Košir Minka-Nežka"
        last = last[:married.start()]
    notes = ([f'zvani {alias}'] if alias else []) + ([f'roj. {married.group(1)}'] if married else []) \
        + (['dr.'] if dr else []) + ([age.strip()] if age else []) + ([f'({other})'] if other else [])
    bio = bio.strip()
    info = '; '.join(notes + ([bio] if bio else []) + ([ctx] if ctx else []))
    rec = _record(last, given, '', info)
    rec['birth_year'] = ''
    place = re.split(r',|\s\(roj', bio)[0].strip(' .')
    if place and not re.search(r'\d|ni znano|neznan', place, re.I):
        rec['birth_place'] = place
    fell = re.search(r'\b(padel|padla|ustreljen\w*|pogrešan\w*|umrl\w*)\b', bio) or re.search(r'\b(ujet\w*)\b', bio)
    if fell:
        w = fell.group(1)
        if re.search(r'kot (?:dezerter|talec)|gestapovski|ubit kot', bio) and not w.startswith('pad'):
            rec['death_type'] = 'streljan' if 'kot talec' in bio else None
        elif w.startswith('pad'):
            rec['death_type'] = 'poginuo'
        elif w.startswith('ustrel'):
            rec['death_type'] = 'streljan'
        elif w.startswith('pogreš'):
            rec['death_type'] = 'nestao'
        elif w.startswith('umr'):
            rec['death_type'] = 'umro'
        elif re.search(r'umrl|kjer je umrl', bio):
            rec['death_type'] = 'umro'
        else:
            rec['death_type'] = 'zarobljen'
        if not rec.get('death_type'):
            rec.pop('death_type', None)
        after = bio[fell.end():fell.end() + 80]
        d = re.match(r'\s*(?:kot \w+\s+)?(\d{1,2})\.(?:-\d{1,2}\.)?\s*(\d{1,2})\.\s*(19\d\d)', after)
        y = re.match(r'\s*(?:\w+\s+)?(19\d\d)', after)
        if rec.get('death_type') in ('poginuo', 'streljan', 'umro', 'nestao') and not re.search(r'po vojni', after[:12]):
            before = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(19\d\d)\s*(?:,\s*ko je(?: bil)?)?\s*$', bio[:fell.start()])
            if d:
                rec['death_date'] = f'{int(d.group(1))}. {int(d.group(2))}. {d.group(3)}'
            elif y:
                rec['death_date'] = y.group(1)
            elif before:                                            # "... 17. 2. 1944 padel", "do 14. 9. 1942, ko je padel"
                rec['death_date'] = f'{int(before.group(1))}. {int(before.group(2))}. {before.group(3)}'
            where = re.search(r'\s(?:v|na|nad|pri|pod)\s+([^,.]+)', after)
            if where and rec['death_type'] == 'poginuo':
                rec['death_place'] = where.group(0).strip().replace(' ', ' ')
    rec['additional_info'] = rec['additional_info'].replace(' ', ' ')
    duty = re.search(r'\b(komandant|komandir|politkomisar|namestnik \w+|intendant|kurir|bolničar(?:ka)?|administrator|'
                     r'mitraljezec|vodnik|desetar|zdravnik|obveščevalec|politdelegat)\b', bio)
    if duty:
        rec['rank'] = duty.group(1)
    bat = re.search(r'(\d)\. \((\w+)\) bataljon', ctx, re.I)
    cet = re.search(r'(\d)\. (?:\(\w+\) )?četa|(\d)\. in \d\. četa', ctx)
    if bat:
        rec['unit_detail'] = ', '.join(x for x in ((f'{cet.group(1) or cet.group(2)}. četa' if cet else ''),
                                                   f'{bat.group(1)}. bataljon') if x)
    elif ctx.startswith('štab odreda') or 'pri štabu odreda' in ctx:
        rec['unit_detail'] = 'štab odreda'
    return rec


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/kokrski-odred-1.pdf',
        brigade_code=171,
        output_path='website/public/kokrski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        extract_fn=extract,
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=parse_entry,
        id_start=10001,
        keep_other_sources=True,
    )
