"""Men glued into another man's entry in the books across units' entries (2026-11-03): the parser missed the heading, so the
man is on the site under no name of his own. Each is cut out of his host's text and becomes an entry of the book, numbered
after the file's last so the others' numbers stay, his place on the page found by his heading, read as his list's others
(a list that counts the movement's people marks him by the same rule). The names are read from the heading, the alphabetical
order and the site's records of the village. python scripts/split_book_entries.py [--write], then the chain in docs/claude/ostali-borci.md
(Ostali borci, its fields, the identity pass)."""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
import entry_boxes  # noqa: E402
import parse_mosorski_odred_2 as mos  # noqa: E402
from split_glued_entries import find  # noqa: E402

# file -> host -> (where his heading starts, surname, father as the book prints him, given name, what he was called)
BOOK_SPLITS = {
    'bijelo-polje-entries.json': {
        '9095002491': [('491a) MULIB Alije RAMIZ', 'Mulić', 'Alije', 'Ramiz', '')],
    },
    'bosansko-grahovo-entries.json': {
        '9062000302': [('. Galić Mile Stojan', 'Galić', 'Mile', 'Stojan', '')],
        '9062000710': [('. Injac Steve Krsto', 'Injac', 'Steve', 'Krsto', '')],
    },
    'hak-10-korenica-udbina-entries.json': {
        '9008000707': [('(3T) PUZIC Mile DMITAR', 'Puzić', 'Mile', 'Dmitar', '')],
    },
    'hak-13-gracac-entries.json': {
        '9010000098': [("lO'O. LIČINA Mile ĐURO", 'Ličina', 'Mile', 'Đuro', '')],
        '9010000421': [('202. P.ADAKOVIC Nikole JOVO', 'Radaković', 'Nikole', 'Jovo', '')],
        '9010000598': [("133. RO'NČEVIČ Mile IVAN", 'Rončević', 'Mile', 'Ivan', '')],
        '9010000659': [('2.1. JAPUNDŽIC Luke VASO', 'Japundžić', 'Luke', 'Vaso', '')],
        '9010000737': [('1CD. ZORIC Rade LUKA', 'Zorić', 'Rade', 'Luka', '')],
        '9010000875': [('137.. NOVAKOVIĆ Sime NIKOLA', 'Novaković', 'Sime', 'Nikola', '')],
    },
    'hak-14-donji-lapac-entries.json': {
        '9009000199': [('61. šarac Jovana Nikola', 'Šarac', 'Jovana', 'Nikola', '')],
        '9009000393': [('Zunić rođ. Popović Mara', 'Žunić', '', 'Mara', 'rođ. Popović')],
        '9009000521': [('U. Bešir Nikole Marko', 'Bešir', 'Nikole', 'Marko', '')],
        '9009000579': [('U. Obradović Jove Stevo', 'Obradović', 'Jove', 'Stevo', '')],
        '9009000857': [("1. Bucalo' Janka Momčilo", 'Bucalo', 'Janka', 'Momčilo', '')],
    },
    'hak-15-duga-resa-entries.json': {
        '9028000362': [('1. DEJANOVIĆ Stevana MARIJA', 'Dejanović', 'Stevana', 'Marija', '')],
    },
    'hak-16-gornje-dubrave-entries.json': {
        '9030000041': [('1. Bartolović Ana', 'Bartolović', '', 'Ana', '')],
        '9030000056': [('3. Mikašinović Marko', 'Mikašinović', '', 'Marko', '')],
    },
    'hak-19-vojnic-entries.json': {
        '9018000611': [('. ĐAKOVIC Đurđa NIKOLA', 'Đaković', 'Đurđa', 'Nikola', '')],
    },
    'hak-7-plascanska-dolina-entries.json': {
        '9011000192': [("12 ' KORUGA Dane ĐURO", 'Koruga', 'Dane', 'Đuro', '')],
    },
    'hrvatsko-zagorje-1981-entries.json': {
        '9036000837': [('KRIŽNJAK BRANKO', 'Križnjak', '', 'Branko', '')],
    },
    'iskra-in-plamen-padli-entries.json': {
        '9039000146': [('27 . .Marenče Leopold', 'Marenče', '', 'Leopold', '')],
    },
    'jevreji-jugoslavije-ucesnici-nor-entries.json': {
        '9061000385': [('Atijas Jozefa Hanika', 'Atijas', 'Jozefa', 'Hanika', ''), ('Atijas Izidor', 'Atijas', '', 'Izidor', '')],
        '9061000393': [('Atijas Avrama Klarica', 'Atijas', 'Avrama', 'Klarica', ''), ('Atijas-Koen Jozefa Lela', 'Atijas-Koen', 'Jozefa', 'Lela', '')],
        '9061000445': [('Balog Dežea Franjo', 'Balog', 'Dežea', 'Franjo', '')],
        '9061000500': [('Baruh Elijasa Viktorija', 'Baruh', 'Elijasa', 'Viktorija', '')],
        '9061001882': [('l?.me\\ isaka ing. Leopold Poldi', 'Izrael', 'Isaka', 'Leopold', 'Poldi')],
        '9061002193': [('Kern Magda', 'Kern', '', 'Magda', ''), ('Kern Filipa Vera', 'Kern', 'Filipa', 'Vera', '')],
        '9061002230': [('Klajn Mavro', 'Klajn', '', 'Mavro', '')],
        '9061002237': [('Klajn Zdenka', 'Klajn', '', 'Zdenka', '')],
        '9061002934': [('Milanov-Liht Milana Vera', 'Milanov-Liht', 'Milana', 'Vera', '')],
        '9061003330': [('Pesah Cevia Isak', 'Pesah', 'Cevia', 'Isak', '')],
        '9061003637': [('Ruso N. Žaklen', 'Ruso', 'N.', 'Žaklen', '')],
        '9061004115': [('švabenic Ankica', 'Švabenić', '', 'Ankica', '')],
        '9061004151': [('švarc Šime', 'Švarc', '', 'Šime', '')],
    },
    'otocac-brinje-entries.json': {
        '9064000637': [('Ogrizović Pavla Виго', 'Ogrizović', 'Pavla', 'Đuro', ''), ('Bobinae T. Marko', 'Bobinac', 'T.', 'Marko', ''), ('Bobinae S. Mile', 'Bobinac', 'S.', 'Mile', ''), ('Bobinae I. Slavko', 'Bobinac', 'I.', 'Slavko', ''), ('Brajković I. Luka', 'Brajković', 'I.', 'Luka', ''), ('Brajković M. Joso', 'Brajković', 'M.', 'Joso', ''), ('Čulinović I. Ivan', 'Čulinović', 'I.', 'Ivan', ''), ('Kolaković I. Josip', 'Kolaković', 'I.', 'Josip', ''), ('Jerbić I. Mate', 'Jerbić', 'I.', 'Mate', ''), ('Laškarin M. Nikola', 'Laškarin', 'M.', 'Nikola', ''), ('Majer L. Frane', 'Majer', 'L.', 'Frane', ''), ('Nikšić M. Mate', 'Nikšić', 'M.', 'Mate', ''), ('Nikšić N. Frane', 'Nikšić', 'N.', 'Frane', ''), ('Orešković T. Ivan', 'Orešković', 'T.', 'Ivan', ''), ('Rajković D. Fabijan', 'Rajković', 'D.', 'Fabijan', ''), ('Sertić I. Nikola', 'Sertić', 'I.', 'Nikola', ''), ('Sertić I. Juraj', 'Sertić', 'I.', 'Juraj', ''), ('Šimatović F. Stjepan', 'Šimatović', 'F.', 'Stjepan', ''), ('Tonković L. Franjo', 'Tonković', 'L.', 'Franjo', ''), ('Vujić M. Katica', 'Vujić', 'M.', 'Katica', ''), ('Tonković D. Luka', 'Tonković', 'D.', 'Luka', ''), ('Laškarin F. Marko', 'Laškarin', 'F.', 'Marko', ''), ('Laškarin F. Mirko', 'Laškarin', 'F.', 'Mirko', ''), ('Dubravčić D. Franjo', 'Dubravčić', 'D.', 'Franjo', ''), ('Grčević T. Juraj', 'Grčević', 'T.', 'Juraj', ''), ('Laškarin S. Luka', 'Laškarin', 'S.', 'Luka', '')],
        '9064000329': [('Ostović M. Stipe', 'Ostović', 'M.', 'Stipe', '')],
        '9064000368': [('Cvjetićanin M. Dane', 'Cvjetićanin', 'M.', 'Dane', '')],
        '9064000411': [('Vlaisavljević M. Mile', 'Vlaisavljević', 'M.', 'Mile', '')],
        '9064000697': [("Š'tetić'Dure Božo", 'Štetić', 'Dure', 'Božo', '')],
        '9064011735': [('Stojanović D. Kaja', 'Stojanović', 'D.', 'Kaja', '')],
        '9064011742': [('Stojanović D. Nikola', 'Stojanović', 'D.', 'Nikola', '')],
    },
    'revolucionarno-grahovo-entries.json': {
        '9089000180': [('MARKOVIĆ Vidakov VOJIN', 'Marković', 'Vidakov', 'Vojin', '')],
    },
    'sanski-most-borci-entries.json': {
        '9042002337': [('ĆALIĆ-MARTIĆ D. VIDA', 'Ćalić-Martić', 'D.', 'Vida', '')],
        '9042002502': [("'GRUJČIĆ Nike BLAŽO", 'Grujčić', 'Nike', 'Blažo', '')],
        '9042004272': [('Marin Trive Marko', 'Marin', 'Trive', 'Marko', '')],
        '9042006060': [('VUKOJEVIĆ M. MILKA', 'Vukojević', 'M.', 'Milka', '')],
    },
    'seoske-hronike-entries.json': {
        '9005000080': [('20. NJUBOJEVIB M. DRAGAN', 'Ljubojević', 'M.', 'Dragan', '')],
        '9005000199': [('66. MIŠČEVIB Stevana JOVAN', 'Miščević', 'Stevana', 'Jovan', '')],
        '9005000276': [('15. BORKOVIB Milana DUŠAN', 'Borković', 'Milana', 'Dušan', '')],
        '9005000290': [("31. 'BAKOVIB Spase SAVA", 'Đaković', 'Spase', 'Sava', '')],
        '9005000295': [('37. ILIB M. GOJKO', 'Ilić', 'M.', 'Gojko', '')],
        '9005000313': [('56. KORICA D. NOVAK', 'Korica', 'D.', 'Novak', '')],
        '9005000320': [('65. KRIČKOVIB M. JOVAN', 'Kričković', 'M.', 'Jovan', '')],
        '9005000364': [('118. VURDENJA T. BOGDAN', 'Vurdelja', 'T.', 'Bogdan', ''), ('119. VURDEJBA T. DUŠAN', 'Vurdelja', 'T.', 'Dušan', '')],
        '9005000366': [('122. ZAKLAN M. MILAN', 'Zaklan', 'M.', 'Milan', '')],
        '9005000809': [('109. Zorić M. Aleksa', 'Zorić', 'M.', 'Aleksa', '')],
        '9005000873': [('175. Njiljak A. Stevo', 'Njiljak', 'A.', 'Stevo', '')],
        '9005000886': [('189. Mrđenović S. Miloš', 'Mrđenović', 'S.', 'Miloš', '')],
        '9005000928': [('235. Obradović S. Dušan', 'Obradović', 'S.', 'Dušan', '')],
        '9005000938': [('246. Potkonjak J. Milan', 'Potkonjak', 'J.', 'Milan', '')],
        '9005000939': [('248. Polovina S. Gojko', 'Polovina', 'S.', 'Gojko', ''), ('249. Polovina S. Dane', 'Polovina', 'S.', 'Dane', '')],
        '9005000945': [('256. Putnik B. Mile', 'Putnik', 'B.', 'Mile', '')],
        '9005000999': [('313. Radaković D. Mićo', 'Radaković', 'D.', 'Mićo', '')],
        '9005001032': [('348. Sudar J. Stevo', 'Sudar', 'J.', 'Stevo', '')],
        '9005001079': [('399. Crnogorac S. Miloš', 'Crnogorac', 'S.', 'Miloš', '')],
        '9005001091': [('412. Čanak J. Stevo', 'Čanak', 'J.', 'Stevo', ''), ('413. Čović M. Rade', 'Čović', 'M.', 'Rade', '')],
        '9005001094': [('417. Čugalj M. Marko', 'Čugalj', 'M.', 'Marko', '')],
        '9005001095': [('419. Čanak J. Nikola', 'Čanak', 'J.', 'Nikola', '')],
        '9005001286': [('178. Tweth "Bure Savo', 'Ćelić', 'Đure', 'Savo', '')],
        '9005001299': [('192. Halai-Tomaš Sava', 'Halai-Tomaš', '', 'Sava', '')],
        '9005001705': [('Bumath Radoja Svetolik', 'Đenadić', 'Radoja', 'Svetolik', '')],
        '9005001731': [('2. Mijajnlović ćirka Branko', 'Mijajilović', 'Ćirka', 'Branko', '')],
        '9005001833': [('15. Ivanović V. Milan', 'Ivanović', 'V.', 'Milan', '')],
    },
    'staromajdansko-entries.json': {
        '9063000032': [('STUPAR Stole MIRKO', 'Stupar', 'Stole', 'Mirko', '')],
        '9063000033': [("I'RKULJA Stojana GOJKO", 'Grkulja', 'Stojana', 'Gojko', '')],
        '9063000073': [('PREDOJEVIĆ Branka DUŠAN', 'Predojević', 'Branka', 'Dušan', '')],
    },
}

# from the men of this heading on, the list's village is another: its own heading was lost (Otočac's Sinac, after
# Drenov Klanac)
NEW_PREFIX = {'Bobinae T. Marko': 'Pali borci, Sinac: '}
# the lists that count the movement's people too: a man no fighter by the rule is marked, as their parsers mark them
MIXED = {'jevreji-jugoslavije-ucesnici-nor-entries.json': lambda e: True,
         'otocac-brinje-entries.json': lambda e: not e.get('list', '').startswith('Pali'),
         'sanski-most-borci-entries.json': lambda e: 'maja 1945' in e.get('additional_info', '')[:60]}
# these keep the fighters and mark the movement's other people; a victim of terror or a civilian is cut out and goes
FIGHTERS_AND_ACTIVISTS = {'hrvatsko-zagorje-1981-entries.json', 'imotska-krajina-pali-borci-entries.json', 'knjazevac-pomenik-entries.json',
                          'cacanski-kraj-pali-entries.json', 'pozega-pali-entries.json', 'revolucionarno-grahovo-entries.json', 'bijelo-polje-entries.json'}
# these count everyone in the war: what no word tells apart is a participant
FIGHTERS_AND_OTHERS = {'kolasin-entries.json', 'milesevski-entries.json', 'kotor-varos-entries.json', 'mosorski-odred-2-aktivisti-entries.json'}
READ_AS_ACTIVIST = {'IVF.KOVIĆ (Stjepana) KRSTO', 'DINKA PAUT'}      # the head of a district's intelligence centre; a member of the AFŽ's board the OCR spells AF2
VICTIM = re.compile(r'\bkao ŽFT\b|\bžrtv')
DEATH = re.compile(r'\b(?:pogin|umr|nesta|stri?jelj|ubijen|pal[ai]?\b|zaklan|obješen|umor)\w*[^;]{0,70}?\b(19[34]\d)\b', re.I)
DEATH_VERB = re.compile(r'\b(?:pogin|umr|nesta|stri?jelj|ubijen|pal[ai]?\b|zaklan|obješen|umor)', re.I)
STRAY_END = "'\"`’‘,;~•·-"


def fold(s: str) -> str:
    return re.sub(r'[^a-z]', '', ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower()) if unicodedata.category(c) != 'Mn'))


def split_prefix(text: str) -> tuple[str, str]:
    """The list's heading before the entry, up to its first colon, and the rest"""
    at = text.find(': ')
    if 0 < at < 170:
        head = text[:at]
        if not re.search(r'\bro[dđ]en', head) and (not re.search(r'\d{4}', head) or re.search(r'^(?:Borci|Nosioci|Spisak|Poginuli|Pali|Preživjeli|Živi|Umrli|Učesnici|Svoja|Jevreji|Spomenica)\b', head)):
            return text[:at + 2], text[at + 2:]
    return '', text


def host_end(text: str) -> str:
    """The host's text up to the cut: what a garbled number or a speck left at its end goes, a full stop stays"""
    tail = re.search(rf'[\s.{re.escape(STRAY_END)}]*$', text).group(0)
    kept = text[:len(text) - len(tail)] if tail else text
    return kept + '.' if '.' in tail else kept


def main():
    write = '--write' in sys.argv
    total = 0
    table = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--table=')), None)      # {file: {host: [where his heading starts, surname, father, given name, nick]}}; a row with no surname is only cut
    for name, hosts in (json.load(open(table, encoding='utf-8')) if table else BOOK_SPLITS).items():
        path = next(p for p in (ROOT / 'data-extraction' / d / name for d in ('poreklo', 'znaci')) if p.exists())
        raw = path.read_text(encoding='utf-8')
        data = json.loads(raw)
        by = {e['soldier_id']: i for i, e in enumerate(data)}
        next_id = max(int(e['soldier_id']) for e in data) + 1
        added = {}
        printing = sum(fold(split_prefix(e.get('additional_info') or '')[1])[:4] == fold(e.get('last_name'))[:4] for e in data) > len(data) / 2
        for hid, men in hosts.items():
            host = data[by[hid]]
            info = host['additional_info']
            pos, at = [], 0
            for cut, *_ in men:
                i = info.find(cut, at)
                assert i > 0, (hid, cut, info[:200])
                pos.append(i)
                at = i + 1
            prefix, own = split_prefix(info)
            keeps = printing or fold(own)[:4] == fold(host.get('last_name'))[:4]        # the book prints the name in the entry's text
            after = (host['pdf_page'], host['pdf_x'], host['pdf_y'], 'host') if host.get('pdf_file') else None
            new_host = host_end(info[:pos[0]])
            print(f"{hid} {host.get('name')}: ...{new_host[-70:]!r}")
            for k, (cut, last, father, given, nick, *more) in enumerate(men):
                if cut in NEW_PREFIX:
                    prefix = NEW_PREFIX[cut]
                if len(more) > 1:
                    prefix = more[1]
                piece = info[pos[k]:pos[k + 1] if k + 1 < len(men) else len(info)].strip()
                rest = piece[len(cut):].lstrip(' ,.;')
                if not last:
                    print('   CUT ONLY', cut, '|', rest[:70])
                    continue
                rest = host_end(rest) if rest.endswith(tuple(STRAY_END)) else rest
                printed = more[0] if more else re.sub(r'^(?:\S*\d\S*\s+|[A-Z]\.\s+(?=[A-ZŠ]))', '', cut).lstrip(" .'\"")
                text = prefix + (f"{printed}{' ' if rest.startswith('(') else ', '}{rest}" if keeps else rest)
                verb = DEATH_VERB.search(rest)
                by_birth = re.search(r'\b(1[89]\d\d)\b', rest[:verb.start() if verb else 60][:60])
                died = DEATH.search(rest)
                born_in = ''
                bm = re.search(r'\b[Rr]o[dđ](?:en|ei)[a]?[ ~,]*(?:\d[\d. ]*(?:godine)?,?\s*)?(?:u\s+(?:selu\s+)?)((?:[A-ZČĆŽŠĐ]\.\s*)*[A-ZČĆŽŠĐ][^,.;]*?)(?=\s+(?:pogin|umr|nesta)|[,.;]|$)', rest)
                if bm:
                    born_in = bm.group(1).strip()
                elif prefix and fold(host.get('born_in', '').split(',')[0]) and fold(host['born_in'].split(',')[0]) in fold(prefix):
                    born_in = host['born_in']
                elif prefix and fold(host.get('born_in', '').split(',')[-1]) and fold(host['born_in'].split(',')[-1]) in fold(prefix):
                    born_in = host['born_in'].split(',')[-1].strip()
                e = {k2: v for k2, v in host.items() if k2 not in ('additional_info', 'units', 'role', 'no', 'pdf_x_end', 'pdf_y_end', 'pdf_x_left', 'pdf_rects', 'death_place', 'death_date', 'unnamed')}
                sid = f'{next_id:010d}'
                next_id += 1
                e.update(soldier_id=sid, name=' '.join(x for x in (last, father, given) if x), last_name=last, first_name=given, nick='' if nick.startswith('rođ.') else nick,
                         fathers_name=father, birth_year=by_birth.group(1) if by_birth else '', born_in=born_in, death_year=died.group(1) if died else '',
                         also=[nick[5:]] if nick.startswith('rođ.') else [], additional_info=text)
                if 'units' in host:
                    e['units'] = []
                if 'no' in host:
                    no = re.match(r'\d+', cut)
                    e['no'] = int(no.group(0)) if no else host['no']
                if 'survived' in host:
                    e['survived'] = bool(host.get('survived')) and not died
                if 'death_date' in host:
                    e['death_date'] = ''
                soldier = mos.fighter(e) or mos.fighter_or_officer(e)
                if name in MIXED and MIXED[name](host) and not soldier:
                    e['role'] = 'activist'
                elif name in FIGHTERS_AND_ACTIVISTS and not soldier:
                    if cut not in READ_AS_ACTIVIST and (VICTIM.search(rest) or not mos.activist(e)):
                        print('   CUT, no one of ours:', cut, '|', rest[:400])
                        next_id -= 1
                        continue
                    e['role'] = 'activist'
                elif name in FIGHTERS_AND_OTHERS and not soldier:
                    e['role'] = 'activist' if mos.activist(e) else 'participant'
                held = next((o for o in data if o is not host and len(rest) >= 25 and rest[:40] in (o.get('additional_info') or '')
                             and fold(o.get('first_name')) == fold(given) and (fold(o.get('last_name'))[:4] == fold(last)[:4] or fold(o.get('fathers_name')) == fold(father))), None)
                if held:
                    print('   HELD by', held.get('name'), '|', cut, '|', rest[:60])
                    next_id -= 1
                    continue
                if host.get('pdf_file'):
                    try:
                        order, x, y = find(host, re.sub(r'^\S*\d\S*\s+', '', cut).lstrip(" .'\"") or printed, after, rest)
                        after = order
                        e.update(pdf_page=order[0], pdf_x=x, pdf_y=y)
                    except SystemExit as ex:
                        print('   NOT FOUND', ex)
                        e.update({k2: host[k2] for k2 in ('pdf_page', 'pdf_x', 'pdf_y') if k2 in host})     # the host's place: the scan's his, in the same column
                added.setdefault(hid, []).append(e)
                total += 1
                print(f"   {sid} {e['name']!r} {e['birth_year']} [{born_in}] d{e['death_year']} {e.get('role', '')} {('p%s y%s' % (e.get('pdf_page'), e.get('pdf_y'))) if host.get('pdf_file') else ''} | {text[:110]}")
            host['additional_info'] = new_host
        # each new man right after his host, so the list's order stays the book's
        out = []
        for e in data:
            out.append(e)
            out.extend(added.get(e['soldier_id'], ()))
        if write:
            if any(e.get('pdf_file') for e in out):
                stats = entry_boxes.fill_boxes(out)
                print('  boxes', entry_boxes.describe(stats, stats['boxed']))
            indent = 2 if raw.startswith('[\n  {') else (1 if raw.startswith('[\n {') else None)
            path.write_text(json.dumps(out, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''), encoding='utf-8')
    print(total, 'men' + ('' if write else ' (dry run)'))


if __name__ == '__main__':
    main()
