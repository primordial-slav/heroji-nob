"""Names of the 3. vojvođanska's book, read back (2026-11-04).

znaci.org re-typeset this book from its OCR, so the page itself prints the
errors and shows nothing better: Ћ as Н or К at a name's end ("Јемшин" is
Jemšić), Ђ as Б ("Бурић" is Đurić), Ћ as Н, И or Б at its start ("Нирковић",
"Иирић", "Бирић" are Ćirković, Ćirić), Ј as Т ("Тавornik" is Javornik), Л as
Jt ("Jtazar" is Lazar).

Each reading here stands on one of these:
  place   the list is alphabetical, and the name stands among the Đ, Ć or J
          names (fallen pp. 6, 8-9; missing pp. 46-48; survivors pp. 80-81,
          86-88, 97-98);
  same    the same man in another book, by given name, birth year and village;
  home    a man from outside Vojvodina, where a surname in -in has no bearer
          on the site and the one in -ić many;
  shape   a letter the book always misreads so, in a name there is no doubt of.
Surnames in -in of men from Vojvodina with nothing more are left as printed:
that ending is real there (Vujin, Pejin, Stojšin).

    python scripts/fix_3_vojvodjanska_names.py          # dry run: every change
    python scripts/fix_3_vojvodjanska_names.py --write  # appends the corrections
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, 'scripts')
from name_utils import BRIGADE_CONFIGS
from safe_write import write_text

# soldier id -> surname (None: as it stands), given name (None: as it stands), why
P = '00570'
TABLE = {}


def put(why, rows):
    for sid, last, first in rows:
        TABLE[sid if len(sid) == 10 else '0057' + sid] = (last, first, why)


# Đ read as Б, among the Đ names
put('place: Đ read as B', [
    ('000139', 'Đakula', None), ('000201', 'Đekić', None), ('000443', 'Đujić', None),
    ('000452', 'Đukičin', None), ('000464', 'Đurđaković', None), ('000468', 'Đurđev', None),
    ('000470', 'Đurđić', None), ('000487', 'Đuričin', None), ('000474', 'Đurić', None),
    ('000119', 'Đajić', None), ('000137', 'Đaković', None), ('000238', 'Đemunska', None),
    ('000483', 'Đuričin', None), ('000484', 'Đuričin', None), ('000485', 'Đuričin', None),
    ('000486', 'Đuričin', None), ('000476', 'Đurić', None), ('000473', 'Đurić', None),
    ('000498', 'Đuzić', None), ('000128', 'Đak', None), ('000136', 'Đaković', None),
    ('000135', 'Đaković', None), ('000154', 'Đanić', None), ('000198', 'Đekanin', None),
    ('000202', 'Đekić', None), ('000243', 'Đerđ', None), ('000264', 'Đikić', None),
    ('000266', 'Đilasović', None), ('000323', 'Đokić', None), ('000324', 'Đokić', None),
    ('000322', 'Đokić', None), ('000329', 'Đonić', None), ('000446', 'Đukanov', None),
    ('000448', 'Đukić', None), ('000451', 'Đukić', None), ('000449', 'Đukić', None),
    ('000450', 'Đukić', None), ('000491', 'Đurčić', None), ('000492', 'Đurčić', None),
    ('000493', 'Đurčić', None), ('000490', 'Đurčić', None), ('000469', 'Đurđev', None),
    ('000466', 'Đurđev', 'Ilija'), ('000467', 'Đurđev', 'Relja'), ('000465', 'Đurđev', None),
    ('000482', 'Đuričin', 'Ilija'), ('000475', 'Đurić', None), ('000481', 'Đurić', None),
    ('000472', 'Đurić', None), ('000479', 'Đurić', None), ('000480', 'Đurić', None),
    ('000477', 'Đurić', None), ('000471', 'Đurić', None), ('000478', 'Đurić', None),
    ('000488', 'Đurkić', None),
])
# Ć read as Н, И or Б, among the Ć names
put('place: Ć read as N, I or B', [
    ('002287', 'Ćepina', None), ('002357', 'Ćirić', None), ('002356', 'Ćirić', None),
    ('002359', 'Ćirković', None), ('002358', 'Ćirković', 'Milivoje'), ('002362', 'Ćosić', None),
    ('000147', 'Ćalerovski', None), ('000274', 'Ćirić', None), ('000276', 'Ćirković', None),
    ('001013', 'Ćalović', None), ('000209', 'Ćelarović', None), ('000273', 'Ćirić', None),
    ('001440', 'Ćirić', None), ('001033', 'Ćirić', None), ('001034', 'Ćirić', 'Sava'),
    ('001035', 'Ćirić', None), ('001036', 'Ćirković', None), ('001037', 'Ćirković', None),
    ('001038', 'Ćirković', None), ('001040', 'Ćirković', None), ('001039', 'Ćirković', None),
    ('001041', 'Ćirković', None), ('001082', 'Ćorić', None), ('001083', 'Ćorlomanović', None),
    ('000344', 'Ćosić', None), ('001097', 'Ćurčić', None), ('002383', 'Ćurčin', None),
    ('002387', 'Ćurčin', None), ('002384', 'Ćurčin', None), ('002385', 'Ćurčin', None),
    ('002386', 'Ćurčin', None), ('002388', 'Ćurčić', None), ('002380', 'Ćurbin', None),
    ('002381', 'Ćurković', None), ('002382', 'Ćuroteo', None),
])
# Ј read as Т, among the J names; the Janković block of pp. 97-98
put('place: J read as T, in the Janković block', [
    ('003398', 'Janković', None), ('001176', 'Janković', None), ('001174', 'Janković', 'Nada'),
    ('001162', None, 'Cveja'), ('003383', 'Janković', None), ('003400', 'Janković', None),
    ('003399', 'Janković', None), ('003388', 'Jasina', None), ('003394', 'Javorina', None),
    ('003372', 'Javorina', None), ('003395', 'Javornik', None), ('003416', 'Ječević', None),
])
# the page in question, p. 115
put('place: the Malet- names of p. 115, the book\'s Л and Е misread', [
    ('001814', None, 'Stepan Štefika'), ('004135', 'Malenović', 'Anica Seka'),
    ('004138', 'Maletić', 'Živa'), ('004140', 'Maletković', None),
    ('001794', None, 'Đuka'), ('001802', None, 'Lazar'), ('001799', None, 'Jano'),
    ('001812', None, 'Đurica'),
])
# the same man in another book
put('same: another book has him by given name, birth year and village', [
    ('000041', 'Ađanski', None), ('000066', 'Atanacković', None), ('000195', 'Benagol', None),
    ('000447', 'Bukurecki', None), ('000454', 'Bukurecki', None), ('000652', 'Domonji', None),
    ('000661', 'Dožudić', None), ('000859', 'Gićanov', None), ('000892', 'Gradić', None),
    ('001012', 'Čabović', None), ('001032', 'Ćirin', None), ('001178', 'Jegdić', None),
    ('001188', 'Jemšić', None), ('001191', 'Jemšić', None), ('001433', 'Kečić', None),
    ('001529', 'Košprdić', None), ('001595', 'Košprdić', None), ('001600', 'Krasnik', None),
    ('001696', 'Kužnik', None), ('001698', 'Lađinović', None), ('001735', 'Leđanac', None),
    ('001767', 'Lozić', None), ('001819', None, 'Cvijetin'), ('001930', 'Mergel', None),
    ('002135', 'Mutevelić', None), ('002201', 'Mudrenić', None), ('002232', 'Naglić', None),
    ('002233', 'Najić', None), ('002439', 'Pankeričan', None), ('002477', 'Paprić', None),
    ('002547', 'Perenčević', None), ('002688', 'Pogrmić', None), ('002759', 'Postolović', None),
    ('002760', 'Postolović', None), ('003016', 'Eremić', None), ('003018', 'Repić', None),
    ('003071', 'Savičević', None), ('003159', 'Slomić', None), ('003246', 'Starčulj', None),
    ('003329', 'Stakić', None), ('003344', 'Subotički', None), ('003501', 'Puhalović', None),
    ('003514', 'Udovičić', None), ('003519', 'Ucman', None), ('003587', 'Večerkov', None),
    ('003776', 'Zalić', None), ('003820', 'Zrnić', None), ('003847', 'Čepski', None),
    ('003921', 'Šajin', None), ('004002', 'Štiglić', None), ('004013', 'Šuljmanac', None),
    ('004044', 'Šijačić', None), ('003957', 'Šijačić', 'Mita'), ('004086', 'Žigurski', None),
    ('004229', 'Stančić', None),
])
# from outside Vojvodina: -in has no bearer, -ić many
put('home: Ć read as N at the end, a man from outside Vojvodina', [
    ('004198', 'Vorkapić', None), ('004197', 'Vorkapić', None), ('003663', 'Vorkapić', None),
    ('002227', 'Mutić', None), ('002207', 'Mujkić', None), ('002208', 'Mujkić', None),
    ('001923', 'Mehić', None), ('001924', 'Mehić', None), ('001394', 'Karalić', None),
    ('002967', 'Ramić', None), ('001436', 'Kikić', None), ('000948', 'Habić', None),
    ('001003', 'Hrvić', None), ('002406', 'Omerbašić', None), ('002424', 'Osmajić', None),
    ('003803', 'Zlatić', None), ('003101', 'Sejdić', 'Ćamil'), ('000761', 'Fačić', None),
    ('001384', 'Kanić', None), ('003826', 'Zukić', None), ('000708', 'Dugalić', 'Abdul'),
    ('001774', 'Lužajić', None), ('001775', 'Lužajić', None), ('002202', 'Mudrovčić', None),
    ('002983', 'Ratić', None), ('003978', 'Škobić', None), ('003433', 'Tojagić', None),
    ('002949', 'Rajšić', None), ('003752', 'Vunčić', None), ('002653', 'Pintić', None),
    ('001722', 'Lazarić', None), ('003123', 'Simikić', None), ('002982', 'Rastić', None),
    ('003809', 'Zorbić', None), ('003555', 'Varničić', None),
])
# a letter the book misreads always so
put('shape: Jt for L, I for N or P, and the like', [
    ('003758', None, 'Laza'), ('001488', 'Kolar', 'Lazar'), ('001370', None, 'Ilija'),
    ('003026', None, 'Milan'), ('003063', None, 'Milena'), ('003066', None, 'Rudolf'),
    ('003097', None, 'Slobodan'), ('003087', None, 'Vasilije'), ('000427', None, 'Momčilo'),
    ('000263', None, 'Zdravko'), ('001811', None, 'Zlatan'), ('000022', None, 'Petar'),
    ('001386', None, 'Jovan'), ('001383', None, 'Josip'), ('001452', None, 'Josip'),
    ('001753', None, 'Nikolija'), ('003733', None, 'Borivoj'), ('001415', None, 'Nikola'),
    ('001431', None, 'Bogdan'), ('003115', 'Skakavac', 'Stanko'), ('003136', 'Skakavac', None),
    ('001429', None, 'Mlađa'), ('003217', None, 'Mlađan'), ('000148', None, 'Ferenc'),
    ('003611', None, 'Franja'), ('003353', None, 'Zagorka'), ('001506', None, 'Ilija'),
    ('001502', None, 'Matija'), ('000031', None, 'Muhidin'), ('000083', None, 'Mihalj'),
    ('000192', None, 'Ercole'), ('000965', None, 'Luigi'), ('000588', 'Adilić', None),
    ('001172', 'Jazić', None), ('003396', 'Jazić', None),
])
# other units: tt for ti in the text layer
put('shape: tt for ti', [
    ('0036100538', 'Karabatić', None), ('0043000725', 'Matković-Pipek', None),
    ('0056001371', 'Musanović', None), ('0010101148', 'Srdić-Batičanin', None),
    ('0035107110', 'Matijašec', None), ('0040000803', 'Matijaš', None),
    ('0040001310', 'Slavica-Krstić', None), ('0082003495', 'Taratić', None),
    ('0044000854', 'Šestić', None), ('0003010026', 'Aksentijević', None),
    ('0039100139', 'Cvijetićanin', None), ('0004003015', 'Vretič', None),
    ('0001101582', 'Vujović-Martinović', None), ('0005100023', 'Bajčetić', None),
    ('0112000395', 'Rutić', None),
])
# the 12. vojvođanska's roster, the given name beside the same list's "Lazika"
put('place: the roster of Crepaja; Ugrišić as the 12. krajiška prints him, Lazika as this list', [
    ('0075002232', 'Ugrišić', 'Lazika'),
])

# text and fields of the two men glued into the entries above them
EDITS = [
    ('0057003384', {'last_name': 'Janković', 'first_name': 'Jovan Senka',
                    'additional_info': 'Petrovci, Ruma.', 'birth_place': 'Petrovci, Ruma'},
     'place: the Janković block; the line under him is another man'),
    ('0057001139', {'additional_info': 'rođen 1924. Mol, Ada. Bačka.', 'birth_place': 'Mol, Ada'},
     'the line under him is another man'),
]
ADDS = [
    ('0057003384', '0057009004', {
        'last_name': 'Janković', 'middle_name': '', 'fathers_name': '', 'first_name': 'Jefta',
        'additional_info': 'iz Novog Sada.', 'birth_year': '',
        'pdf_file': '3-vojvodjanska.pdf', 'pdf_page': 98, 'pdf_y': 200.0, 'pdf_x': 78.6},
     'glued into Janković Jovan Senka: "мттеовИН ЈЕФТА, из Новог Сада."'),
    ('0057001139', '0057009005', {
        'last_name': 'Jančić', 'middle_name': '', 'fathers_name': '', 'first_name': 'Andrija',
        'additional_info': 'borac, ranjen marta 1945. Baranja.', 'birth_year': '',
        'pdf_file': '3-vojvodjanska.pdf', 'pdf_page': 97, 'pdf_y': 317.0, 'pdf_x': 50.7},
     'glued into Jakšić Živko: "тдичИБ АНДРИЈА, борац, рањен марта 1945. Барања."'),
]


def main():
    write = '--write' in sys.argv
    records = {}
    for code in sorted({int(s[:4]) for s in TABLE} | {57}):
        for s in json.load(open('website/public/' + BRIGADE_CONFIGS[code]['json_file'], encoding='utf-8')):
            records[s['soldier_id']] = s
    corrections = json.load(open('corrections.json', encoding='utf-8'))
    seen = json.dumps(corrections, ensure_ascii=False)
    for _, new_id, _, _ in ADDS:
        if new_id in seen or new_id in records:
            sys.exit(f'{new_id} is taken')
    next_id = max(c['id'] for c in corrections) + 1
    out = []
    names = {}
    missing = 0
    for sid, (last, first, why) in sorted(TABLE.items()):
        s = records.get(sid)
        if not s:
            print('NOT FOUND', sid, last, first)
            missing += 1
            continue
        fields = {}
        if last and last != s.get('last_name'):
            fields['last_name'] = last
        if first and first != s.get('first_name'):
            fields['first_name'] = first
        if not fields:
            continue
        print(sid, s.get('last_name'), '|', s.get('first_name'), '->', fields.get('last_name', s.get('last_name')), '|', fields.get('first_name', s.get('first_name')), '|', why[:6])
        out.append({'id': next_id, 'action': 'edit', 'soldier_id': sid, 'fields': fields, 'reason': why})
        next_id += 1
        names[sid] = (fields.get('last_name', s.get('last_name')), fields.get('first_name', s.get('first_name')))
    for sid, fields, why in EDITS:
        out.append({'id': next_id, 'action': 'edit', 'soldier_id': sid, 'fields': fields, 'reason': why})
        next_id += 1
    for sid, new_id, record, why in ADDS:
        out.append({'id': next_id, 'action': 'add', 'soldier_id': sid, 'new_id': new_id, 'record': record, 'reason': why})
        next_id += 1
    # links keep working: their guards name the record as it now reads
    guards = 0
    for c in corrections:
        if c.get('action') == 'link' and c.get('link_id') in names and c.get('link_name'):
            last, first = names[c['link_id']]
            s = records[c['link_id']]
            old = c['link_name']
            new = old.replace(s.get('last_name') or '\0', last)
            if s.get('first_name') and s.get('first_name') != first:
                new = new.replace(s['first_name'], first)
            if new != old:
                print('guard', c['id'], old, '->', new)
                c['link_name'] = new
                guards += 1
    print(len(out), 'corrections,', guards, 'guards,', missing, 'not found')
    if write:
        write_text('corrections.json', json.dumps(corrections + out, ensure_ascii=False, indent=2) + '\n')
        print('written, ids', out[0]['id'], '-', out[-1]['id'])


if __name__ == '__main__':
    main()
