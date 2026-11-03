"""
A bio's key words and years as the scan misread them, so that no date or fate could be read (2026-11-02).

  years  "poginuol943", "ožujkal943", "odl943": the year's 1 read as l and its space lost (the Kalnički odred's list); "l925"; "192b",
         "194S"; a year glued to the word before it or after it ("rođen1912", "1944godine"); "l3. juna".
  words  One letter misread in a word the entries print thousands of times, "ioginuo", "pofinuo", "zemljoradlik", "seitembra": a slip counted
         a few times where the word is counted thousands, and which no name or place of the site bears. NOT_SLIPS holds what the list showed
         to be words of their own ("vođen", "rođeni") or a place.

Run: python scripts/fix_entry_words.py [--list] [--since ID] [--write START [--entries]]: --write appends `edit` corrections for the units; --entries
also mends the entries files of the books across units (the records of Borci drugih jedinica are made from them). --since: texts come from the corrections
from that id on where they set one (an earlier script of the same batch), else from the unit files.
"""
import collections, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS

LOW = 'a-zčćžšđ'
MONTHS = 'januara|februara|marta|aprila|maja|juna|jula|avgusta|augusta|septembra|oktobra|novembra|decembra|siječnja|veljače|ožujka|travnja|svibnja|lipnja|srpnja|kolovoza|rujna|listopada|studenoga?|prosinca'


def years(t):
    t = re.sub(r'\bil(9[0-4]\d)(?!\d)', r'1\1', t)                                           # "il926"
    t = re.sub(r'\bo d[l1]?(9[0-4]\d)(?!\d)', r'od 1\1', t)                                  # "o dl942"
    t = re.sub(r'\bodv(19[0-4]\d)(?!\d)', r'od \1', t)                                       # "odv1943"
    t = re.sub(r'\b(januar|februar|avgust|august|septembr|oktobr|novembr|decembr) al(9[0-4]\d)(?!\d)', r'\1a 1\2', t)  # "januar al942"
    t = re.sub(rf'(?<=[{LOW}])l(9[0-4]\d)(?!\d)', r' 1\1', t)                                # "poginuol943"
    t = re.sub(r'(?<![\w.])l(9[0-4]\d)(?!\d)', r'1\1', t)                                    # "l925"
    t = re.sub(r'(?<![\w.])19([0-4])([OoIlZzSsBb])(?![\w])', lambda m: '19' + m.group(1) + {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'Z': '2', 'z': '2', 'S': '5', 's': '5', 'B': '8', 'b': '6'}[m.group(2)], t)
    t = re.sub(rf'(?<=[{LOW}]{{2}})(1[89]\d\d)(?!\d)', r' \1', t)                            # "rođen1912"
    t = re.sub(r'(19[0-4]\d)(?=godin)', r'\1 ', t)                                           # "1944godine"
    t = re.sub(rf'\b[lI](\d)\.\s*(?={MONTHS})', r'1\1. ', t)                                 # "l3. juna"
    t = re.sub(rf'\b(od|do|u)(\d{{1,2}}\.\s*(?:{MONTHS}))', r'\1 \2', t)                     # "od2. septembra"
    return t


# a mark inside a word had been taken out, where it stood for a lost letter or a lost space ("vodnik^u", "T^entište"), or the word was past the rule: read from the page's words
MARKS_BACK = {
    '0046000123': [("boc'", 'borac')], '0021002982': [('btaljon', 'bataljon')], '0036000904': [('bolničara', 'bolničarka')], '0038000023': [('ooktobra', 'od oktobra')],
    '0040001751': [('Vljona', 'bataljona')], '0040010815': [('pogino', 'poginuo')], '0041010008': [('inastavlja', 'i nastavlja')], '0043000097': [('bolničj,', 'bolničarka u')],
    '0043000163': [('Tentište', 'Tjentište')], '0047000186': [('borc', 'borac')], '0052000962': [('rodn', 'rođen')], '0054002438': [('pogino', 'poginuo')],
    '0054003055': [('Maklenovac', 'Makljenovac')], '0054003546': [('Lusina', 'Ljusina')], '0057001136': [('borc', 'borac')], '0057001150': [('Oloviku', 'Orloviku')],
    '0057001426': [('Aleksandroo', 'Aleksandrovo')], '0057001500': [('Inđia', 'Inđija')], '0057004138': [('Pnčeva', 'Pančeva')], '0057001835': [('komandvoda', 'komandir voda')],
    '0057002365': [('janara', 'januara')], '0057002418': [('boac', 'borac')], '0074000168': [('godinG Kolari', 'godine, Kolari')], '0074000346': [('Plilula', 'Palilula')],
    '0074000396': [('godne', 'godine')], '0080000619': [('zemloradnik', 'zemljoradnik')], '0080001010': [('diviziе', 'divizije'), ('divizie', 'divizije')], '0085000143': [('poinuo', 'poginuo')],
    '0088000369': [('MIAILO', 'MIHAILO')], '0109000139': [('muen', 'mučen')], '0109001249': [('školaopančarski', 'škola, opančarski')], '0109001276': [('slua', 'sluga')],
    '0109001400': [('roditeli', 'roditelji')], '0110000660': [('tgovački', 'trgovački')], '0110002308': [('strelan', 'streljan')], '0112000045': [('Pratećegbata', 'Pratećeg bata')],
    '0112000242': [('Pratećegbataljona', 'Pratećeg bataljona')], '0125000533': [('čln', 'član')], '0126001067': [('strelali', 'streljali')], '0021002816': [('vodniku 2.', 'vodnik u 2.')],
    '0026000537': [('nivio', 'živio')], '0003011514': [('JOB-1944', 'NOB-1944')], '0006000014': [('Läzrcväc', 'Lazarevac')], '0006002423': [('Pnlnk^', 'Palanka')],
    '0006005843': [('Lzrcvc', 'Lazarevac')], '0006008322': [('Lcslcovc', 'Leskovac')], '0006006687': [('Scžn^', 'Sežana')], '0046000393': [('slbenik', 'Šibenik')],
    '0010202594': [('zemljođnik', 'zemljoradnik')], '0010202595': [('Koraca. Mladenovac', 'Koraćica, Mladenovac')], '0018002009': [('Mačđosu', 'Manđelosu')], '0019000170': [('gutu', 'putu')],
    '0021000213': [('Brgaadi', 'Brigadi')], '0074000536': [('godine.ŠrugovGijSmederevo', 'godine, Drugovac, Smederevo')], '0021003381': [('Ravei 12. aprnjm', 'Ranjen 12. aprila')], '0021003460': [('Raven', 'Ranjen')],
    '0021004202': [('Vrčš Dolu', 'Vrčin Dolu')], '0024000538': [('napadana', 'napada na')], '0034000961': [('Spki-j nja', 'Srpkinja')], '0038000051': [('kodStajze', 'kod Stajze')],
    '0038000116': [('JOaprid,', '10. aprila')], '0039101103': [('Šreskogkomiteta', 'Sreskog komiteta')], '0040001748': [('de-/fja', 'decembra')], '0046000124': [('ćmiš', 'Omiš')],
    '0049011432': [('štsbs brisdc', 'štaba brigade')], '0057000621': [('radnik, bogn', 'radnik, borac')], '0057000973': [('zehmloradnik', 'zemljoradnik')], '0057001151': [('lJtegat', 'delegat')],
    '0057001420': [('zmljooadnik', 'zemljoradnik'), ('kodtandir', 'komandir')], '0057002268': [('Vukoevipe', 'Vukosavljevice')], '0057003135': [('ttstona', 'istočna')], '0057003376': [('kolandira', 'komandira')],
    '0057003609': [('ratena', 'ranjena')], '0057003881': [('pogišo', 'poginuo'), ('boratt', 'borac'), ('zemljopalnik', 'zemljoradnik')], '0073003032': [('urelu', 'u selu')], '0080000019': [('slmenice', 'spomenice')],
    '0074009001': [('godineSuvodolJSmederevo.]', 'godine, Suvodol, Smederevo.')], '0074000560': [('Djugovjp)', 'Drugovac')], '0082001170': [('orc', 'borac')], '0085000198': [('Vlasni', 'Vlasini')],
    '0106000171': [('poginzo', 'poginuo')], '0109000325': [('izbeglrca', 'izbeglica')], '0148009002': [('vemljo?wfThik', 'zemljoradnik')], '0127000272': [('Pljevl.a', 'Pljevlja')], '0035113012': [('Er-penja', 'Erpenja')],
}
# the 19. srpska's retyped pages print the Д of Dobra as А with a speck ("A°bra"), which the marks' rule read as "Aobra"
ALSO = [('Aobra', 'Dobra'), ('Aobri', 'Dobri'), ('Aobroj', 'Dobroj')]


# the words looked at: the bio's own, not names
MAIN = ('poginuo poginula poginuli rođen rođena borac zemljoradnik srbin hrvat hrvatica srpkinja godine bataljona bataljon bataljonu brigade brigadi brigadu '
        'politički komandir komandant komesar desetar vodnik ranjen ranjena nestao nestala umro umrla streljan streljana stupio stupila januara februara aprila '
        'avgusta septembra oktobra novembra decembra protiv ustaša radnik domaćica bolničarka sahranjen zamenik zamjenik student učenik učenica partizanske spomenice '
        'kolovoza rujna listopada studenog prosinca siječnja veljače ožujka travnja svibnja lipnja srpnja musliman muslimanka crnogorac crnogorka slovenac krojač stolar trgovac '
        'član njemaca nemaca četnika ustaša poginuo poginula nepoznat ostali podaci').split()
NOT_SLIPS = set('''poginut poginulo poginule poginuli poginula boran gorac dorac borao boric bovac rađen vođen vođena pođen rođeni rođene rođeno rođenu rođenj rojena rojen
rodine podine godinc codine zodine zemljoradnih zemljoradnič radnih radnim ratnik ladnik rodnik radlik radnik bataljoni batalion bataljom bataljon
komandar komandio učenika učeniku učenici učenice učeniće stupila stupilo stupile stupili ranjeni ranjeno ranjene ranjenu ranjenj ranjan ranjem nestale nestali nestalo streljani streljano
vodnih sodnik vodnim vodnil članu člana člane članj članica člani članom protić protič proziv prošiv umri umrli umrlo umrle umra umre
komesara komesaru hrvatski hrvatica hrvati hrvate hrvata hrvatu srbij srbik srbih subin sabin radić kadar krojači krojača stolari stolara stolaru trgovca trgovci
slovenci slovenka slovenac crnogorci crnogorske crnogorski musliman muslimani muslimana muslimanu nemaci nemacu njemaci ustaši ustašu ustaška ustana ustala ostati ostaci ostavi ostalo ostala ostale podatke podatak podacima
student studene studeni studenu studena studentica učenik spomenik domaćina domaćinu domacica desetak desetara kolovoz rujan listopad
korac brojač godinu goline bolničarki bolničarku crnogorke crnogorki muslimanke politička političke političku spomenica spomenici spomenicu podace umno umio slan zlan člen
srbim srbio srbič poginio bataliona batalionu črnogorka črnogorac domačica ripnja nemica kemaca oktobri prosince ruina trpnja streljao streljaš otupio stupit travnji zamenih zamjenih zamjenil'''.split())


def load_units():
    units = {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists() and code != 122 and not 131 <= code <= 138:
            units[code] = json.loads(p.read_text(encoding='utf-8'))
    return units


def slip_table(units):
    words = collections.Counter()
    names = set()
    for data in units.values():
        for s in data:
            words.update(w.lower() for w in re.findall(rf'[A-ZČĆŽŠĐ]?[{LOW}]{{3,}}', s.get('additional_info') or ''))
            for f in ('last_name', 'first_name', 'middle_name', 'fathers_name', 'birth_place', 'death_place'):
                names.update(re.findall(rf'[{LOW}]+', (s.get(f) or '').lower()))
    table = {}
    for main in MAIN:
        n = words.get(main, 0)
        if n < 100:
            continue
        for i in range(len(main)):
            pat = main[:i] + '.' + main[i + 1:]
            for w, c in words.items():
                if len(w) == len(main) and w != main and c <= 15 and c * 60 < n and re.fullmatch(pat, w) and w not in names and w not in NOT_SLIPS and w not in MAIN:
                    table[w] = main
    return table


def apply_words(t, table):
    def fix(m):
        w = m.group(0)
        r = table.get(w.lower())
        if not r:
            return w
        if w[0].islower():
            return r
        # in capitals it may be a name or a place: only where a sentence opens
        return r.capitalize() if re.search(r'(^|[.;]\s+)$', t[:m.start()]) else w
    return re.sub(rf'(?<![\w-])[A-ZČĆŽŠĐ]?[{LOW}]{{3,}}(?![\w-])', fix, t)


def main():
    units = load_units()
    table = slip_table(units)
    if '--list' in sys.argv:
        by = collections.defaultdict(list)
        for w, m in table.items():
            by[m].append(w)
        for m, ws in sorted(by.items()):
            print(m, ':', ' '.join(sorted(ws)))
    print('slips in the table', len(table))
    corr = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    # an earlier script of the same batch has set a text the unit files don't hold yet
    since = int(sys.argv[sys.argv.index('--since') + 1]) if '--since' in sys.argv else None
    pending = {}
    if since:
        for c in corr:
            if c['id'] >= since and c['action'] == 'edit' and 'additional_info' in (c.get('fields') or {}):
                pending[c['soldier_id']] = c['fields']['additional_info']
    edits = []
    cnt = collections.Counter()
    samples = collections.defaultdict(list)
    for code, data in units.items():
        for s in data:
            for e in [s] + [o for o in s.get('other_sources', ()) if not o.get('ref_book') and not o.get('unit_file')]:
                if not e.get('soldier_id'):
                    continue
                printed = pending.get(e['soldier_id'], e.get('additional_info') or '')
                if not printed:
                    continue
                t = printed
                for old, new in MARKS_BACK.get(e['soldier_id'], ()):
                    t = t.replace(old, new, 1)
                for old, new in ALSO:
                    t = t.replace(old, new)
                back = t != printed
                if e['soldier_id'] in MARKS_BACK and not back:
                    print('NOT FOUND', e['soldier_id'], MARKS_BACK[e['soldier_id']], repr(printed[:80]))
                a = years(t)
                b = apply_words(a, table)
                if b != printed:
                    why = []
                    if back:
                        why.append('a mark that stood for a lost letter or space')
                        cnt['marks'] += 1
                    if a != t:
                        why.append('a year the scan misread or glued')
                        cnt['years'] += 1
                        if len(samples['years']) < 25:
                            samples['years'].append((e['soldier_id'], t[-70:], a[-70:]))
                    if b != a:
                        why.append('a word the scan misread')
                        cnt['words'] += 1
                    edits.append((e['soldier_id'], b, why))
    print(cnt, 'edits', len(edits))
    for x in samples['years']:
        print('  ', x)
    if '--write' in sys.argv:
        start = int(sys.argv[sys.argv.index('--write') + 1])
        assert not [c for c in corr if c['id'] >= start]
        add = [{'id': start + i, 'action': 'edit', 'soldier_id': sid, 'fields': {'additional_info': t}, 'reason': '; '.join(why)} for i, (sid, t, why) in enumerate(edits)]
        (ROOT / 'corrections.json').write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        print('written', len(add), start, start + len(add) - 1)
        if '--entries' in sys.argv:
            total = 0
            for d in ('znaci', 'poreklo'):
                for f in (ROOT / 'data-extraction' / d).glob('*-entries.json'):
                    raw = f.read_text(encoding='utf-8')
                    data = json.loads(raw)
                    n = 0
                    for e in data:
                        t = e.get('additional_info') or ''
                        new = apply_words(years(t), table)
                        if new != t:
                            e['additional_info'] = new
                            n += 1
                    if n:
                        indent = 2 if raw.startswith('[\n  {') else (1 if raw.startswith('[\n {') else None)
                        f.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + ('\n' if raw.endswith('\n') else ''), encoding='utf-8')
                        total += n
            print('entries mended', total)


if __name__ == '__main__':
    main()
