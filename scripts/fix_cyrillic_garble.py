"""Cyrillic books with the 3. vojvođanska's garble, read back (2026-11-06; see scripts/fix_3_vojvodjanska_names.py).

IN: a surname in -in whose -ić form others bear and the -in no one, in a Cyrillic book outside Vojvodina (Ћ read as Н at
the name's end; "Алибегин", "Гњатин" are no names), or anywhere the same man in another book has the -ić. A Latin book's
-in (Dalmatia, Zagorje, Slovenia) and Vojvodina's stay as printed. ORDER: a surname out of its list's alphabetical order,
read back by its section and the book's own misread letter, or by the same man elsewhere.

    python scripts/fix_cyrillic_garble.py          # dry run
    python scripts/fix_cyrillic_garble.py --write  # appends the corrections
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, 'scripts')
from name_utils import BRIGADE_CONFIGS
from safe_write import write_text

# soldier id -> (surname, why)
IN = {
    "0001502763": ("Škočić", "cyrillic: Ћ read as Н at the end"),
    "0005010060": ("Bilušić", "same: the same man elsewhere has -ić"),
    "0005010142": ("Cmiljanić", "same: the same man elsewhere has -ić"),
    "0005010143": ("Cmiljanić", "same: the same man elsewhere has -ić"),
    "0005010397": ("Joknić", "same: the same man elsewhere has -ić"),
    "0005010458": ("Kepić", "cyrillic: Ћ read as Н at the end"),
    "0005010755": ("Ninčić", "same: the same man elsewhere has -ić"),
    "0005010756": ("Ninčić", "same: the same man elsewhere has -ić"),
    "0005011135": ("Vatić", "cyrillic: Ћ read as Н at the end"),
    "0011000118": ("Benić", "cyrillic: Ћ read as Н at the end"),
    "0011000327": ("Gnjatić", "cyrillic: Ћ read as Н at the end"),
    "0011000328": ("Gnjatić", "cyrillic: Ћ read as Н at the end"),
    "0011000330": ("Golić", "same: the same man elsewhere has -ić"),
    "0011000437": ("Jarić", "cyrillic: Ћ read as Н at the end"),
    "0011000438": ("Jarić", "cyrillic: Ћ read as Н at the end"),
    "0011001654": ("Jeličić", "same: the same man elsewhere has -ić"),
    "0011000446": ("Jeličić", "cyrillic: Ћ read as Н at the end"),
    "0011000570": ("Konjikušić", "cyrillic: Ћ read as Н at the end"),
    "0011000632": ("Kuburić", "cyrillic: Ћ read as Н at the end"),
    "0011000680": ("Lošić", "cyrillic: Ћ read as Н at the end"),
    "0011001209": ("Rogulić", "cyrillic: Ћ read as Н at the end"),
    "0011001306": ("Stanojčić", "cyrillic: Ћ read as Н at the end"),
    "0011001402": ("Trninić", "cyrillic: Ћ read as Н at the end"),
    "0011001463": ("Vladušić", "same: the same man elsewhere has -ić"),
    "0011001615": ("Šundić", "cyrillic: Ћ read as Н at the end"),
    "0013011640": ("Ćopić", "cyrillic: Ћ read as Н at the end"),
    "0022000051": ("Anušić", "same: the same man elsewhere has -ić"),
    "0022000132": ("Bakšić", "same: the same man elsewhere has -ić"),
    "0022000613": ("Dostanić", "same: the same man elsewhere has -ić"),
    "0022000759": ("Ganić", "same: the same man elsewhere has -ić"),
    "0022000858": ("Grudenić", "same: the same man elsewhere has -ić"),
    "0022001223": ("Kalenić", "same: the same man elsewhere has -ić"),
    "0022001241": ("Kantardžić", "same: the same man elsewhere has -ić"),
    "0022001242": ("Kantardžić", "same: the same man elsewhere has -ić"),
    "0022001243": ("Kanurić", "same: the same man elsewhere has -ić"),
    "0022001535": ("Kupinić", "same: the same man elsewhere has -ić"),
    "0022001812": ("Medančić", "same: the same man elsewhere has -ić"),
    "0022002566": ("Rajnić", "same: the same man elsewhere has -ić"),
    "0026000957": ("Sokić", "cyrillic: Ћ read as Н at the end"),
    "0028010313": ("Poćanić", "cyrillic: Ћ read as Н at the end"),
    "0038000396": ("Nikoletić", "cyrillic: Ћ read as Н at the end"),
    "0038000535": ("Seratlić", "cyrillic: Ћ read as Н at the end"),
    "0048010044": ("Ajkić", "cyrillic: Ћ read as Н at the end"),
    "0048010061": ("Alibegić", "cyrillic: Ћ read as Н at the end"),
    "0048010851": ("Glamočić", "cyrillic: Ћ read as Н at the end"),
    "0048011692": ("Kretić", "cyrillic: Ћ read as Н at the end"),
    "0048013364": ("Tirić", "cyrillic: Ћ read as Н at the end"),
    "0089000031": ("Cakić", "same: the same man elsewhere has -ić"),
    "0089000072": ("Gvojić", "cyrillic: Ћ read as Н at the end"),
    "0089000159": ("Magić", "cyrillic: Ћ read as Н at the end"),
    "0089000398": ("Timić", "cyrillic: Ћ read as Н at the end"),
    "0102013051": ("Đapić", "cyrillic: Ћ read as Н at the end"),
    "0110000027": ("Aksentić", "same: the same man elsewhere has -ić"),
    "0110000104": ("Bajagić", "cyrillic: Ћ read as Н at the end"),
    "0110000133": ("Bikić", "cyrillic: Ћ read as Н at the end"),
    "0110000226": ("Bukovčić", "cyrillic: Ћ read as Н at the end"),
    "0110000400": ("Gledić", "cyrillic: Ћ read as Н at the end"),
    "0110001592": ("Petronić", "same: the same man elsewhere has -ić"),
    "0110001954": ("Sofranić", "same: the same man elsewhere has -ić"),
    "0110001979": ("Stamenić", "cyrillic: Ћ read as Н at the end"),
    "0110001980": ("Stamenić", "cyrillic: Ћ read as Н at the end"),
    "0110002041": ("Stekić", "cyrillic: Ћ read as Н at the end"),
    "0110002042": ("Stekić", "same: the same man elsewhere has -ić"),
    "0110002176": ("Todosić", "same: the same man elsewhere has -ić"),
    "0110002177": ("Todosić", "cyrillic: Ћ read as Н at the end"),
    "0110002287": ("Vikentić", "cyrillic: Ћ read as Н at the end"),
    "0110002362": ("Čanić", "cyrillic: Ћ read as Н at the end"),
    "0110002363": ("Čanić", "cyrillic: Ћ read as Н at the end"),
    "0110002364": ("Čanić", "cyrillic: Ћ read as Н at the end"),
    "0127000057": ("Bjelić", "cyrillic: Ћ read as Н at the end"),
    "0127000063": ("Bojičić", "cyrillic: Ћ read as Н at the end"),
    "0127000102": ("Didić", "cyrillic: Ћ read as Н at the end"),
    "0127000248": ("Kitić", "same: the same man elsewhere has -ić"),
    "0127000254": ("Kondić", "cyrillic: Ћ read as Н at the end"),
    "0127000255": ("Konjić", "cyrillic: Ћ read as Н at the end"),
    "0127000273": ("Kragić", "cyrillic: Ћ read as Н at the end"),
    "0127000440": ("Mirčetić", "cyrillic: Ћ read as Н at the end"),
    "0127000682": ("Savatić", "cyrillic: Ћ read as Н at the end"),
    "0127000741": ("Stevčić", "cyrillic: Ћ read as Н at the end"),
    "0127000799": ("Vajić", "cyrillic: Ћ read as Н at the end"),
    "0127000800": ("Vakić", "cyrillic: Ћ read as Н at the end"),
    "0128000225": ("Barzić", "cyrillic: Ћ read as Н at the end"),
    "0128000380": ("Bojnić", "cyrillic: Ћ read as Н at the end"),
    "0128000381": ("Bojnić", "cyrillic: Ћ read as Н at the end"),
    "0128000387": ("Bolčić", "cyrillic: Ћ read as Н at the end"),
    "0128000412": ("Bradić", "cyrillic: Ћ read as Н at the end"),
    "0128000481": ("Burkić", "cyrillic: Ћ read as Н at the end"),
    "0128000483": ("Burnić", "cyrillic: Ћ read as Н at the end"),
    "0128000567": ("Debić", "cyrillic: Ћ read as Н at the end"),
    "0128000700": ("Fatić", "cyrillic: Ћ read as Н at the end"),
    "0128000769": ("Gergić", "cyrillic: Ћ read as Н at the end"),
    "0128000770": ("Gergić", "cyrillic: Ћ read as Н at the end"),
    "0128000774": ("Glavić", "cyrillic: Ћ read as Н at the end"),
    "0128000847": ("Gržobić", "same: the same man elsewhere has -ić"),
    "0128001007": ("Ivezić", "cyrillic: Ћ read as Н at the end"),
    "0128001038": ("Jacić", "cyrillic: Ћ read as Н at the end"),
    "0128001042": ("Jajić", "cyrillic: Ћ read as Н at the end"),
    "0128001279": ("Jonić", "cyrillic: Ћ read as Н at the end"),
    "0128001516": ("Kalelić", "cyrillic: Ћ read as Н at the end"),
    "0128001524": ("Kanić", "cyrillic: Ћ read as Н at the end"),
    "0128001666": ("Krčić", "same: the same man elsewhere has -ić"),
    "0128001774": ("Lilić", "cyrillic: Ћ read as Н at the end"),
    "0128001818": ("Maksić", "cyrillic: Ћ read as Н at the end"),
    "0128002123": ("Mihaljčić", "cyrillic: Ћ read as Н at the end"),
    "0128002150": ("Miklejić", "cyrillic: Ћ read as Н at the end"),
    "0128002673": ("Mršić", "cyrillic: Ћ read as Н at the end"),
    "0128002722": ("Nejić", "cyrillic: Ћ read as Н at the end"),
    "0128002906": ("Novičić", "cyrillic: Ћ read as Н at the end"),
    "0128003697": ("Redić", "cyrillic: Ћ read as Н at the end"),
    "0128003698": ("Redić", "cyrillic: Ћ read as Н at the end"),
    "0128003886": ("Srejić", "cyrillic: Ћ read as Н at the end"),
    "0128004253": ("Stojičić", "same: the same man elsewhere has -ić"),
    "0128004499": ("Trujić", "cyrillic: Ћ read as Н at the end"),
    "0128004500": ("Trujić", "cyrillic: Ћ read as Н at the end"),
    "0128004676": ("Zakić", "cyrillic: Ћ read as Н at the end"),
    "0128004727": ("Čukić", "cyrillic: Ћ read as Н at the end"),
    "0128004728": ("Čukić", "cyrillic: Ћ read as Н at the end"),
    "0128004842": ("Škodrić", "cyrillic: Ћ read as Н at the end"),
    "0128004843": ("Šljivić", "cyrillic: Ћ read as Н at the end"),
    "0128004853": ("Šoldić", "cyrillic: Ћ read as Н at the end"),
    "0128005026": ("Žurkić", "cyrillic: Ћ read as Н at the end"),
    "0128005027": ("Žurkić", "cyrillic: Ћ read as Н at the end"),
}
ORDER = {
    "0001501071": ("Pavišić", "place: Л for П"),
    "0001500445": ("Raičević", "place: Г for Р"),
    "0001500414": ("Božić", "place: Е for Б"),
    "0001500567": ("Petrović", "place: И for П"),
    "0003022347": ("Ljubojević-Kuga", "place: Lj read as UU"),
    "0003013861": ("Ljubisavljević", "place: Lj read as UU"),
    "0006005735": ("Radosavljević", "place: \"RADOSA VUEVIĆ\", the surname broken"),
    "0006005742": ("Radosavljević", "place: \"RADOSA VUEVIĆ\", the surname broken"),
    "0006005098": ("Pavlović-Ivanišević", "place: \"PAVLOVIČ IVANIŠEVIĆ\" among the P names"),
    "0010101362": ("Ćurgus", "place: \"XJRGUS\", the first letter garbled"),
    "0010100845": ("Bošnjak-Dagatović", "place: the first letter cut"),
    "0010100001": ("Dacić-Petković", "place: the first letter cut"),
    "0018001225": ("Ratkov", "shape: Latin look-alikes, \"Patkob\" = Ратков"),
    "0021000933": ("Pavličević", "place: this book prints П as Г1"),
    "0021000921": ("Palić", "place: this book prints П as Г1"),
    "0021000928": ("Pantić", "place: this book prints П as Г1"),
    "0021000927": ("Pantić", "same: П as Г1, the 22. srpska has him"),
    "0021000929": ("Patrnogić", "place: this book prints П as Г1"),
    "0021000939": ("Petrović", "place: this book prints П as Г1"),
    "0021000944": ("Petrović", "place: this book prints П as Г1"),
    "0021000974": ("Popović", "place: this book prints П as Г1"),
    "0021000932": ("Pavić", "same: П as Г1, the 22. srpska has him"),
    "0021000982": ("Todorčević", "place: Г for Т"),
    "0028010204": ("Prodanović", "place: Л for П"),
    "0039100273": ("Tepčević", "place: the first letter cut"),
    "0041000417": ("Lješković-Vujović", "place: the first letter cut"),
    "0043001206": ("Ljubunčić-Šanjta", "place: Lj read as UU"),
    "0048011034": ("Šešum", "shape: Latin look-alikes, \"IIIEIIIУM\" = Шешум"),
    "0073003238": ("Đorđević", "place: Ђ read as В among the Đ names"),
    "0073003236": ("Đorđević", "place: Ђ read as В among the Đ names"),
    "0074001182": ("Stevčić-Ignjatović", "place: С read as З"),
    "0089000016": ("Đerić", "place: Ђ read as Б among the Đ names"),
    "0089000278": ("Ranđelović", "shape: Latin look-alikes, \"PAНREAOBНR\" = Ранђеловић"),
    "0128000211": ("Valić", "shape: Latin look-alikes, \"BAAHR\" = Валић"),
    "0128004552": ("Đekić", "place: Ђ read as В among the Đ names"),
    "0128000385": ("Đokić", "place: Ђ read as Б among the Đ names"),
    "0001002687": ("Đorić", "same: Б for Đ, the census has him"),
    "0001509026": ("Paušak", "same: the roster has him"),
    "0008001235": ("Ferić", "same: P for F, the Mosorski odred has him"),
    "0024000610": ("Đulai", "same: the left edge cut, the census has him"),
    "0024000001": ("Žabić", "same: the left edge cut, the census has him"),
    "0043000266": ("Pidro", "same: the left edge cut, the Mostarski bataljon has him"),
    "0043000416": ("Tuce", "same: the left edge cut, the Mostarski bataljon has him"),
    "0048000911": ("Ljepić", "same: Lj read as U"),
    "0048013650": ("Đujić", "same: Б for Đ"),
    "0073000143": ("Đekić", "same: Б for Đ, the census has him"),
    "0082003072": ("Komanov", "same: R for K, the Prva proleterska has him"),
    "0111010067": ("Galić", "same: B for G, the 8. vojvođanska has him"),
    "0148002010": ("Fakač", "same: the Prva proleterska has him"),
}
EDITS = [
    ("0018000236", {"last_name": "Stankov", "first_name": "Milan", "middle_name": "Laze", "fathers_name": "Laza", "additional_info": "rođen 1924, Dobrica, Srbin, zemljoradnik, stupio u NOVJ 1944, borac."}, "shape: Latin look-alikes, \"CTAHKOB JIA3E МИЛАН\" = Станков Лазе Милан; the given name had run into the text"),
    ("0018000237", {"last_name": "Strajnev", "middle_name": "Stevana", "fathers_name": "Stevan"}, "shape: Latin look-alikes, \"CTPAJHEB CTEBAHA\" = Страјнев Стевана"),
]

def main():
    write = '--write' in sys.argv
    records = {}
    for code in sorted({int(s[:4]) for s in list(IN) + list(ORDER) + [e[0] for e in EDITS]}):
        for s in json.load(open('website/public/' + BRIGADE_CONFIGS[code]['json_file'], encoding='utf-8')):
            records[s['soldier_id']] = s
    corrections = json.load(open('corrections.json', encoding='utf-8'))
    next_id = max(c['id'] for c in corrections) + 1
    out, names = [], {}
    for table in (IN, ORDER):
        for sid, (last, why) in sorted(table.items()):
            s = records.get(sid)
            if not s:
                print('NOT FOUND', sid, last)
                continue
            if s.get('last_name') == last:
                continue
            print(sid, s.get('last_name'), '->', last, '|', s.get('first_name'), '|', why[:40])
            out.append({'id': next_id, 'action': 'edit', 'soldier_id': sid, 'fields': {'last_name': last}, 'reason': why})
            names[sid] = (s, last, s.get('first_name'))
            next_id += 1
    for sid, fields, why in EDITS:
        s = records[sid]
        if any(s.get(k) != v for k, v in fields.items()):
            out.append({'id': next_id, 'action': 'edit', 'soldier_id': sid, 'fields': fields, 'reason': why})
            names[sid] = (s, fields.get('last_name', s.get('last_name')), fields.get('first_name', s.get('first_name')))
            next_id += 1
    # links keep working: their guards name the record as it now reads
    guards = 0
    for c in corrections:
        if c.get('action') == 'link' and c.get('link_id') in names and c.get('link_name'):
            s, last, first = names[c['link_id']]
            new = c['link_name']
            if s.get('last_name'):
                new = new.replace(s['last_name'], last)
            if s.get('first_name') and first:
                new = new.replace(s['first_name'], first)
            if new != c['link_name']:
                print('guard', c['id'], c['link_name'], '->', new)
                c['link_name'] = new
                guards += 1
    print(len(out), 'corrections,', guards, 'guards')
    if write and out:
        write_text('corrections.json', json.dumps(corrections + out, ensure_ascii=False, indent=2) + chr(10))
        print('written, ids', out[0]['id'], '-', out[-1]['id'])


if __name__ == '__main__':
    main()
