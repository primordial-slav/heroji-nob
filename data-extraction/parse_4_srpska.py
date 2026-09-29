"""
Parser: 4. Srpska udarna brigada (brigade code 21).

Source: Milorad Gončin — "ČETVRTA SRPSKA UDARNA BRIGADA", chapter "Spisak boraca Četvrte srpske udarne brigade"
        znaci.org/00001/149_14.pdf  →  website/public/pdfs/4-srpska.pdf
Single column, Cyrillic. pp. 1-2 introduction (6,442 names), pp. 3-419 the alphabetical list (foreign
volunteers at the end), pp. 420-423 the book's table of contents and imprint.
    АВРАМОВИЋ Владимира ДРАГИША. рођен 1920. Голобок. Смедеревска Паланка. земљорадник. ...
    АВРАМОВИЋ Д. ВИТОМИР. рођен 1916. Ломница. Деспотовац, ...
    АВДИЋ ЈБАЉА. Кожинце. Прокупље. У Бригади од краја децембра 1943.
    САМУЕЛ ДИМИТРИЈЕ, Рус. У 3. чети 4. батаљона.
The OCR often reads the comma after the name as a period. Continuation lines are indented ~13pt, so
entries start at the left margin (_margin_entries); Cyrillic misreads as in 4. Krajiška.
"""
import json
import re
from collections import Counter

from _margin_entries import MARK, MarginEntries, fix_cyrillic_ocr_line, lone_names_to_given, split_leading_aliases
from _parser_scaffold import repair_cyrillic_ocr, repair_lj_ocr, restore_diacritics, run_parser

me = MarginEntries()


def keep_line(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.fullmatch(r'[\W\d]{1,6}', t):                   # page numbers, specks
        return False
    t = fix_cyrillic_ocr_line(t)
    # a married/maiden double surname printed with a spaced dash: "ALEKSIĆ - STEVANOVIĆ Velisava ŽIVOTA"
    t = re.sub(r'^([A-ZČĆŽŠĐ]{3,})\s+[-—–]\s+([A-ZČĆŽŠĐ][A-ZČĆŽŠĐa-zčćžšđ]{2,})(?=[\s.,])',
               lambda m: m.group(1) + '-' + m.group(2).upper(), t)
    t = re.sub(r'^([A-ZČĆŽŠĐ]{3,})\s+[-—–]\s+(?=\()', r'\1 ', t)      # "BUKUMIROVIĆ - (Krstović) Tihomira"
    # a surname split by a speck or a space: "JOS.IPOVIĆ", "BIBER.J. PAVLE", "JU GOVIĆ ILIJA"
    t = re.sub(r'^([A-ZČĆŽŠĐ]{2,})\.([A-ZČĆŽŠĐ]{2,})', r'\1\2', t)
    t = re.sub(r'^([A-ZČĆŽŠĐ]{2,})\.([A-ZČĆŽŠĐ]\.)', r'\1 \2', t)
    t = re.sub(r'^([A-ZČĆŽŠĐ]{1,2}) ([A-ZČĆŽŠĐ]{3,}IĆ)\b', r'\1\2', t)
    t = re.sub(r'^([A-ZČĆŽŠĐ]{3,})([A-ZČĆŽŠĐ][a-zčćžšđ]{2,})', r'\1 \2', t)      # "JANJIĆTrajka JOVAN"
    t = re.sub(r'^([A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]+) \(i ', r'\1 (ili ', t)            # "GAJIĆ (i GOIĆ)": another surname
    ln['text'] = t
    # a lone name followed by "iz ...": "DRAGOLJUB iz Đinđuše", "PILOT iz Beograda"
    m = re.match(r'^([A-ZČĆŽŠĐ]{3,}) (?=(?:iz|sa) )', t)
    if m and ln['x'] <= me.left[(ln.get('file'), ln['page'])] + me.margin_tol:
        ln['text'] = m.group(1) + MARK + ', ' + t[m.end():]
        return True
    # "NN. iz 2. čete 2. bataljona. Ranjen ...": a soldier whose name is unknown (NN is otherwise an abbreviation)
    if re.match(r'^NN[.,:]', t) and ln['x'] <= me.left[(ln.get('file'), ln['page'])] + me.margin_tol:
        ln['text'] = 'NN' + MARK + '.' + t[3:]
        return True
    return me.mark(ln)


def initials(soldiers: list[dict]) -> list[dict]:
    """"JAKŠIĆ J.", "STOJANOVIĆ S. (ŽIVOJIN)": the initial goes with the father's name, and a bracketed name
    after it (read as a nickname by split_leading_aliases) is the given name."""
    for s in soldiers:
        if re.fullmatch(r'[A-ZČĆŽŠĐ]\.?', s['first_name']) and not s['middle_name']:
            s['middle_name'] = s['fathers_name'] = s['first_name']
            s['first_name'] = ''
        m = re.match(r'^(?:zvani|ili) ([A-ZČĆŽŠĐ][a-zčćžšđ]+); ', s['additional_info'])
        if m and re.fullmatch(r'[A-ZČĆŽŠĐ]\.?', s['middle_name'] or '') and not s['first_name']:
            s['first_name'] = m.group(1)
            s['additional_info'] = s['additional_info'][m.end():]
    return soldiers


def unknown_names(soldiers: list[dict]) -> list[dict]:
    """NN and "NEIDENTIFIKOVANI BORAC" entries: the book's N. N."""
    for s in soldiers:
        if s['last_name'] == 'Nn' or s['last_name'].startswith('Neidentif'):
            info = s['additional_info'].lstrip(' .,:')
            if s['last_name'] != 'Nn':
                info = 'neidentifikovani borac; ' + info
            s.update(last_name='N. N.', middle_name='', fathers_name='', first_name='', additional_info=info)
    return soldiers


def tidy_names(soldiers: list[dict]) -> list[dict]:
    """A sentence or a quoted nickname left in a name field: "Bojislav. Politički komesar čete",
    'Miroslava „Bosanac"' → cut the name there and move the rest to the start of the bio."""
    for s in soldiers:
        moved, prefix = [], []
        for k in ('last_name', 'middle_name', 'first_name'):
            v = s.get(k) or ''
            q = re.search(r'\s*[„"“]([^"”“]+)["”“]?\s*', v)
            if q:
                prefix.append('zvani ' + q.group(1).strip().capitalize())
                v = (v[:q.start()] + ' ' + v[q.end():]).strip()
            p = re.search(r'(?<![A-ZČĆŽŠĐ])\.\s+(?=\S)', v)
            if p:
                moved.append(v[p.end():])
                v = v[:p.start()]
            s[k] = v.strip(' .')
        if moved or prefix:
            info = s.get('additional_info') or ''
            s['additional_info'] = '; '.join(prefix + ([' '.join(moved)] if moved else [])) + ('; ' + info if info else '')
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


# given and father names one OCR slip away from a name used elsewhere in the corpus, where the slip is
# one this scan makes (и read as н/п/нј, т as г, л as т/п/ч/јј, ...); real rare names (Josim, Sibin) are left
NAME_FIXES = {
    'Aeksandar': 'Aleksandar', 'Antonnja': 'Antonija', 'Ateksandra': 'Aleksandra', 'Atekse': 'Alekse',
    'Božida': 'Božidar', 'Branispava': 'Branislava', 'Brlnislav': 'Branislav', 'Dannjla': 'Danila',
    'Dannjča': 'Danila', 'Dannla': 'Danila', 'Dnmitrija': 'Dimitrija', 'Draeoslav': 'Dragoslav',
    'Dragoslab': 'Dragoslav', 'Drlgutin': 'Dragutin', 'Gavero': 'Gavro', 'Gavrita': 'Gavrila',
    'Iikola': 'Nikola', 'Ijjija': 'Ilija', 'Itije': 'Ilije', 'Ičije': 'Ilije', 'Josigg': 'Josip',
    'Josigl': 'Josip', 'Josiia': 'Josipa', 'Koete': 'Koste', 'Kosga': 'Kosta', 'Krsga': 'Krsta',
    'Ljubigav': 'Ljubisav', 'Ljubiš': 'Ljubiša', 'Ljutomira': 'Ljubomira', 'Marnnka': 'Marinka',
    'Mihaita': 'Mihaila', 'Mihanjla': 'Mihaila', 'Mihanjta': 'Mihaila', 'Mijjentije': 'Milentije',
    'Mijjojko': 'Milojko', 'Milgnko': 'Milenko', 'Milnvoja': 'Milivoja', 'Milojkc': 'Milojko',
    'Miodrae': 'Miodrag', 'Mipisav': 'Milisav', 'Mitana': 'Milana', 'Mitutina': 'Milutina',
    'Mnjladina': 'Miladina', 'Mnjlana': 'Milana', 'Mnjlenka': 'Milenka', 'Mnjlentija': 'Milentija',
    'Mnjlivoja': 'Milivoja', 'Mnjlića': 'Milića', 'Mnjlorada': 'Milorada', 'Mnjlosava': 'Milosava',
    'Mnjlovana': 'Milovana', 'Mnjloša': 'Miloša', 'Mnjlutina': 'Milutina', 'Mnjpivoja': 'Milivoja',
    'Mnjpovana': 'Milovana', 'Mnjtana': 'Milana', 'Mnjtenka': 'Milenka', 'Mnjtete': 'Milete',
    'Mnjtije': 'Milije', 'Mnjtisava': 'Milisava', 'Mnjtivoja': 'Milivoja', 'Mnjtića': 'Milića',
    'Mnjtoja': 'Miloja', 'Mnjtorada': 'Milorada', 'Mnjtovana': 'Milovana', 'Mnjtoša': 'Miloša',
    'Mnjtuna': 'Miluna', 'Mnjtutina': 'Milutina', 'Mnjčana': 'Milana', 'Mnjčića': 'Milića',
    'Mnjčorada': 'Milorada', 'Mnjčutina': 'Milutina', 'Mnlana': 'Milana', 'Mnlivoja': 'Milivoja',
    'Mnloja': 'Miloja', 'Mnlorada': 'Milorada', 'Mnlovana': 'Milovana', 'Mnloša': 'Miloša',
    'Mpadena': 'Mladena', 'Mpodraga': 'Miodraga', 'Mtadena': 'Mladena', 'Mčadena': 'Mladena', 'Naoda': 'Nada',
    'Nnkole': 'Nikole', 'Obrei': 'Obren', 'Osgoja': 'Ostoja', 'Petera': 'Petra', 'Prevpslava': 'Prvoslava',
    'Radoglav': 'Radoslav', 'Radomnra': 'Radomira', 'Sganimir': 'Stanimir', 'Sganimira': 'Stanimira',
    'Sganislav': 'Stanislav', 'Sganko': 'Stanko', 'Sganoje': 'Stanoje', 'Sgevan': 'Stevan',
    'Sgojadin': 'Stojadin', 'Sgojan': 'Stojan', 'Sgojana': 'Stojana', 'Staiimir': 'Stanimir',
    'Stannjmira': 'Stanimira', 'Stojadip': 'Stojadin', 'Svetistava': 'Svetislava', 'Svetisčava': 'Svetislava',
    'Svetpslava': 'Svetislava', 'Tphomira': 'Tihomira', 'Vasitija': 'Vasilija', 'Vasnjtija': 'Vasilija',
    'Vasnlija': 'Vasilija', 'Vejjimir': 'Velimir', 'Velimpra': 'Velimira', 'Velnmira': 'Velimira',
    'Vitomnra': 'Vitomira', 'Vjjada': 'Vlada', 'Vladimnra': 'Vladimira', 'Vladispav': 'Vladislav',
    'Vlasgimir': 'Vlastimir', 'Vojii': 'Vojin', 'Vojispav': 'Vojislav', 'Vojistava': 'Vojislava',
    'Vojnna': 'Vojina', 'Vukašpna': 'Vukašina', 'Ćorđa': 'Đorđa', 'Čedomnra': 'Čedomira', 'Čedomor': 'Čedomir',
    'Živadiia': 'Živadina', 'Žnvana': 'Živana', 'Žnvote': 'Živote', 'Žpvka': 'Živka', 'Žpvorada': 'Živorada',
    'Žpvote': 'Živote',
}
SURNAME_FIXES = {
    'Aiđelković': 'Anđelković', 'Cvntanović': 'Cvitanović', 'Iikolić': 'Nikolić', 'Ijjić': 'Ilić',
    'Ivkobić': 'Ivković', 'Jovlnović': 'Jovanović', 'Kosgić': 'Kostić', 'Krsgić': 'Krstić', 'Nasgić': 'Nastić',
    'Nać': 'Nađ', 'Nesgorović': 'Nestorović', 'Pavjjović': 'Pavlović', 'Pegrović': 'Petrović',
    'Petkobić': 'Petković', 'Pljić': 'Pajić', 'Radujjović': 'Radulović', 'Risgić': 'Ristić', 'Rljić': 'Rajić',
    'Sganišić': 'Stanišić', 'Sganković': 'Stanković', 'Sganojević': 'Stanojević', 'Sgefanović': 'Stefanović',
    'Sgepanović': 'Stepanović', 'Sgepić': 'Stepić', 'Sgevanović': 'Stevanović', 'Sgojaković': 'Stojaković',
    'Sgojanović': 'Stojanović', 'Sgojiljković': 'Stojiljković', 'Sgojšić': 'Stojšić', 'Sgokić': 'Stokić',
    'Siasojević': 'Spasojević', 'Vesejšnov': 'Veselinov', 'Vgljković': 'Veljković', 'Zlagković': 'Zlatković',
    'Đorđevićt': 'Đorđević',
}


def fix_names(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        for k in ('first_name', 'middle_name', 'fathers_name'):
            if s.get(k):      # Л read as ".č"/".p"/".l": "V.padimir", "Niko.če", "I.lija"
                s[k] = re.sub(r'(?<=[A-Za-zčćžšđ])\.[čpl](?=[a-zčćžšđ])', 'l', s[k])
            s[k] = ' '.join(NAME_FIXES.get(w, w) for w in (s.get(k) or '').split(' ')) if s.get(k) else s.get(k)
        s['last_name'] = SURNAME_FIXES.get(s['last_name'], s['last_name'])
        s['full_name'] = ' '.join(x for x in (s['last_name'], s.get('middle_name') or '', s['first_name']) if x)
    return soldiers


def name_counts():
    first, last = Counter(), Counter()
    for f in ('prva-proleterska-soldiers.json', 'soldiers.json', '13-proleterska-soldiers.json', '2-vojvodjanska-soldiers.json'):
        for s in json.load(open('website/public/' + f, encoding='utf-8')):
            first[s['first_name']] += 1
            last[s['last_name']] += 1
    return first, last


def post(soldiers: list[dict]) -> list[dict]:
    # a Serbian surname ending "-ik"/"-iv" is a misread "-ić" (Ћ read as К/В)
    soldiers = repair_lj_ocr(restore_diacritics(repair_cyrillic_ocr(soldiers, ik_is_ic=True)))
    soldiers = unknown_names(initials(tidy_names(split_leading_aliases(soldiers))))
    return fix_names(lone_names_to_given(soldiers, *name_counts()))


if __name__ == '__main__':
    run_parser(
        pdf_path='website/public/pdfs/4-srpska.pdf',
        brigade_code=21,
        output_path='website/public/4-srpska-soldiers.json',
        start_page=3,
        end_page=419,
        layout='single',
        script='cyrillic',
        entry_start_re=me.entry_start,
        parse_entry_fn=me.parse_entry,
        line_filter=keep_line,
        prepare_fn=me.prepare,
        post_fn=post,
    )
