"""
Entries glued into the one before, in units whose parser missed a heading: the next man's heading and bio stayed in
another man's text ("... borac. BEATOVIK - ŠEVKUŠIK JOVANKA, rođena 1925. godine ..."). Each case is read by hand
from the record's text and listed in SPLITS below: the host keeps its text up to the first glued heading (an edit;
for an entry merged into another record it lands in that record's other_sources), each glued man becomes a record of
the host's unit (an add) with the name as the heading prints it, put in the unit's spelling where the scan garbled it
("PETROVIN" = Petrović, "NNKOANR" = Nikolić), his text from his heading to the next, and his place on the page: the
heading's surname in capitals, the first after the host's start in reading order (the next column, then the next
page). Page furniture glued in between (a list's title, a number) is cut off (JUNK). The boxes are drawn by
entry_boxes.py from the new starts; in a list whose parser draws them (entry_boxes.INLINE_ENTRIES: the Proleterski
bataljon Bosanske krajine's Karasijević) the new record has none and the host keeps its box.
Found with a scan for capitals after a sentence's end (see CLAUDE.md, Known OCR Issues); done on 2026-10-17.
Usage, from the project root: python scripts/split_glued_entries.py --range=LO-HI [--write]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'data-extraction'))
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber  # noqa: E402

from _parser_scaffold import cyrillic_to_latin  # noqa: E402
from pdf_coords import viewer_words  # noqa: E402

R = 'the entry was glued into the one before (its heading missed by the parser), read from the record and the page, 2026-10-17'
# unit data file: {host id: [(heading as in the text, last, father as printed, father in the nominative, given, nickname)]}
SPLITS = {
    '1-dalmatinska-soldiers.json': {
        '0036011112': [('MANDIC Vida GLIGORIJE GLIGO', 'Mandić', 'Vida', 'Vido', 'Gligorije', 'Gligo')],
        '0036012014': [('VOJVODIĆ Feda DIMITRIJE ZEKO', 'Vojvodić', 'Feda', 'Fedo', 'Dimitrije', 'Zeko')],
        '0036010050': [('BILIC Jovana BOZO MARIJAN', 'Bilić', 'Jovana', 'Jovan', 'Božo', 'Marijan'),
                       ('BOGDAN Marka PETAR PEKO', 'Bogdan', 'Marka', 'Marko', 'Petar', 'Peko'),
                       ('CETKOVIC Tome PETAR PERO', 'Ćetković', 'Tome', 'Tomo', 'Petar', 'Pero')],
        '0036010519': [('ĐAPIC Nikole ĐURO BUKETA', 'Đapić', 'Nikole', 'Nikola', 'Đuro', 'Buketa'),
                       ('GALIC Marjana JURE VELIKI', 'Galić', 'Marjana', 'Marjan', 'Jure', 'Veliki'),
                       ('IVAN GUVO', 'Guvo', '', '', 'Ivan', '')],
        '0036011514': [('REIC Ante SREČKO PETICA', 'Reić', 'Ante', 'Ante', 'Srećko', 'Petica'),
                       ('ROMAC Radeta PASKO ZDRAVKO', 'Romac', 'Radeta', 'Rade', 'Paško', 'Zdravko'),
                       ('SCEKIC Gavra VLADIMIR VLADO', 'Šćekić', 'Gavra', 'Gavro', 'Vladimir', 'Vlado')],
    },
    '11-dalmatinska-soldiers.json': {
        '0053000195': [('BAČIĆ (Mate) SREĆKO', 'Bačić', 'Mate', 'Mate', 'Srećko', ''),
                       ('BADELJ (Ivana) VLADIMIR', 'Badelj', 'Ivana', 'Ivan', 'Vladimir', ''),
                       ('BALIĆ (Jakova) DINKO', 'Balić', 'Jakova', 'Jakov', 'Dinko', ''),
                       ('BALOLJ (Ivana) IVAN', 'Balolj', 'Ivana', 'Ivan', 'Ivan', ''),
                       ('BANDALOVIĆ (Jure) ANDRIJA', 'Bandalović', 'Jure', 'Jure', 'Andrija', ''),
                       ('BANDELJ (Angela) ALOJZ', 'Bandelj', 'Angela', 'Angel', 'Alojz', ''),
                       ('BANDELJ (Alojza) ANGEL', 'Bandelj', 'Alojza', 'Alojz', 'Angel', '')],
        '0053000966': [('GREGOV (Silvestra) JOSIP-Moreto', 'Gregov', 'Silvestra', 'Silvestar', 'Josip', 'Moreto')],
        '0053001123': [('JURIĆ (Petra) NIKOLA', 'Jurić', 'Petra', 'Petar', 'Nikola', ''),
                       ('LIVEŠĆEK (Ivana) STANKO', 'Livešček', 'Ivana', 'Ivan', 'Stanko', ''),
                       ('MARENTA (Jakova) MILKO', 'Marenta', 'Jakova', 'Jakov', 'Milko', ''),
                       ('OLIVADIĆ LUKA', 'Olivadić', '', '', 'Luka', ''),
                       ('PETROSIĆ (Luke) IVAN', 'Petrosić', 'Luke', 'Luka', 'Ivan', ''),
                       ('RAŽNJEVIĆ ŠIME', 'Ražnjević', '', '', 'Šime', ''),
                       ('RIZZO (Carmelov) GIOVANNI', 'Rizzo', 'Carmelov', 'Carmelo', 'Giovanni', ''),
                       ('ROKI JURAJ', 'Roki', '', '', 'Juraj', ''),
                       ('ROSIĆ (Tode) TODOR', 'Rosić', 'Tode', 'Todo', 'Todor', ''),
                       ('STIPANOVIĆ ANDRIJA', 'Stipanović', '', '', 'Andrija', ''),
                       ('ŠPILJAK (Ecilijin) FILIP', 'Špiljak', 'Ecilijin', 'Ecilija', 'Filip', ''),
                       ('TOMASIĆ (Marina) MARIN', 'Tomasić', 'Marina', 'Marin', 'Marin', ''),
                       ('VRŽINA (Filipa) ANTE', 'Vržina', 'Filipa', 'Filip', 'Ante', ''),
                       ('VUKELIC (Joze) MATO', 'Vukelić', 'Joze', 'Jozo', 'Mato', ''),
                       ('ZAMBULIN (Andrije) NIKOLA', 'Zambulin', 'Andrije', 'Andrija', 'Nikola', ''),
                       ('ŽANETIĆ FRANE', 'Žanetić', '', '', 'Frane', '')],
        '0053002909': [('URLIČ (Šimuna) ANTE', 'Urlić', 'Šimuna', 'Šimun', 'Ante', '')],
    },
    '12-srpska-soldiers.json': {'0090000426': [('LEPOJEVIĆ Ljubomira MILORAD', 'Lepojević', 'Ljubomira', 'Ljubomir', 'Milorad', '')]},
    '15-majevicka-soldiers.json': {'0049011911': [('ŠAŠKINOVIC (Mileka) MIKAJLO', 'Šaškinović', 'Mileka', 'Milek', 'Mikajlo', '')]},
    '19-bircanska-soldiers.json': {
        '0023000098': [('BEATOVIK - ŠEVKUŠIK JOVANKA', 'Beatović-Ševkušić', '', '', 'Jovanka', '')],
        '0023000132': [('BILIB - JOKIB DANILA OLGA', 'Bilić-Jokić', 'Danila', 'Danilo', 'Olga', '')],
        '0023000771': [('KRSTIK - KOSARIK MILUNKA', 'Krstić-Kosarić', '', '', 'Milunka', '')],
        '0023000932': [('MEBIKOVIK - KOMORAŠ BAJRE FATIMA', 'Mehiković-Komoraš', 'Bajre', 'Bajro', 'Fatima', '')],
        '0023001368': [('PRODANOVIK - PERIK SAVE DANICA', 'Prodanović-Perić', 'Save', 'Savo', 'Danica', '')],
    },
    '22-srpska-soldiers.json': {
        '0074000414': [('KRSTIĆ Uroša MILOSAV', 'Krstić', 'Uroša', 'Uroš', 'Milosav', '')],
        '0074001210': [('ĐEEKOVIĆ Radomira MILOSAV', 'Đeković', 'Radomira', 'Radomir', 'Milosav', '')],
    },
    '23-srpska-soldiers.json': {'0089000469': [('NNKOANR Vladimira DRAGIVOJE', 'Nikolić', 'Vladimira', 'Vladimir', 'Dragivoje', '')]},
    '3-krajiska-proleterska-soldiers.json': {'0010204167': [('RANCIC (Rajšić) MILOŠ', 'Rančić', '', '', 'Miloš', '')]},
    '4-proleterska-soldiers.json': {
        '0040010241': [('DUBLJEVIĆ M. ŽARKO', 'Dubljević', 'M.', '', 'Žarko', '')],
        '0040010401': [('GUBEROVIĆ B. VUKAŠIN', 'Guberović', 'B.', '', 'Vukašin', '')],
        '0040011381': [('RADOVIĆ R. DRAGOJE', 'Radović', 'R.', '', 'Dragoje', '')],
        '0040011944': [('ĐUKIĆ M. MILOSAV', 'Đukić', 'M.', '', 'Milosav', '')],
    },
    '5-srpska-soldiers.json': {'0127000396': [('IMILENKOVIN Tihomira SAVA', 'Milenković', 'Tihomira', 'Tihomir', 'Sava', '')]},
    '6-dalmatinska-soldiers.json': {
        '0103000081': [('EVELJA ANTE', 'Evelja', '', '', 'Ante', '')],
        '0103000095': [('GOCLIO ANTE', 'Goclio', '', '', 'Ante', '')],
        '0103000250': [('PURCINOV NIKOLA', 'Purcinov', '', '', 'Nikola', '')],
    },
    '7-krajiska-soldiers.json': {'0048013526': [('VASILJEVIĆ Ilije ĐORĐE', 'Vasiljević', 'Ilije', 'Ilija', 'Đorđe', '')]},
    '8-krajiska-soldiers.json': {'0014010471': [('KUKIČ (D2) MEHMED', 'Kukić', '', '', 'Mehmed', '')]},
    'druga-licka-soldiers.json': {
        '0003013290': [('RASETA -PLEĆAS LAZE SARA', 'Rašeta-Plećaš', 'Laze', 'Lazo', 'Sara', '')],
        '0003013960': [('VIGNJEVIĆ - DRAĆA NIKOLE DUKA', 'Vignjević-Draća', 'Nikole', 'Nikola', 'Duka', '')],
        '0003014200': [('ZORIC - JAG LICA PERE DOBRI NKA DOJA', 'Zorić-Jaglica', 'Pere', 'Pero', 'Dobrinka', 'Doja'),
                       ('ZORIC - TRSTENJAK JOVE MARA', 'Zorić-Trstenjak', 'Jove', 'Jovo', 'Mara', ''),
                       ('ZRNIĆ - VORKAPIC MILICA', 'Zrnić-Vorkapić', '', '', 'Milica', '')],
    },
    'kalnicki-odred-soldiers.json': {'0058003188': [('STIMEC FRANJO', 'Štimec', 'Matije', 'Matija', 'Franjo', '')]},
    'mosorski-odred-soldiers.json': {
        '0148001449': [('LEKŠIĆ Ante MATE', 'Lekšić', 'Ante', 'Ante', 'Mate', '')],
        '0148001512': [('LONČAR Simuna IVAN', 'Lončar', 'Simuna', 'Šimun', 'Ivan', '')],
    },
    'mostarski-bataljon-soldiers.json': {
        '0125000313': [('DŽEVAD M. JUSUFBEGOVIĆ', 'Jusufbegović', 'M.', '', 'Dževad', '')],
        '0125000370': [('AISA O. KRPO', 'Krpo', 'O.', '', 'Aisa', '')],
        '0125000526': [('2IVKO G. PAPO HENĆI', 'Papo', 'G.', '', 'Živko', 'Henći')],
    },
    'osjecka-soldiers.json': {'0104000527': [('IVANOVIC-KARIC Mladena SAVO', 'Ivanović-Karić', 'Mladena', 'Mladen', 'Savo', '')]},
    'posavski-odred-soldiers.json': {
        '0110001656': [('PETROVIN Živane ŽIVKO', 'Petrović', 'Živane', 'Živana', 'Živko', '')],
        '0110001838': [('RANKOVIE Janka ŽIVORAD', 'Ranković', 'Janka', 'Janko', 'Živorad', '')],
        '0110002306': [('VLAJKOVIN', 'Vlajković', '', '', 'Milka', '')],
    },
    'proleterski-bataljon-bk-soldiers.json': {'0163000126': [('KARASIJEVIĆ J. DRAGO', 'Karasijević', 'J.', '', 'Drago', '')]},
    'toplicki-odred-soldiers.json': {'0093000075': [('RATOMIR VUKAŠINOVIĆ JANIĆIJE', 'Vukašinović', '', '', 'Ratomir', 'Janićije')]},
    'treca-proleterska-soldiers.json': {'0005010459': [('KOSOVIK GAVRO', 'Kosović', '', '', 'Gavro', '')]},
}
# the second batch (2026-10-31): the field checks' glued headings (scripts/check_fields.py, glued), read from the
# records and the pages; python scripts/split_glued_entries.py --batch=2026-10-31 --range=LO-HI [--write]
SPLITS_2026_10_31 = {
    'prva-proleterska-soldiers.json': {
        '0001400149': [('ĆEKO STANKO', 'Ćeko', '', '', 'Stanko', '')],
        '0001401054': [('ŠUBIĆ TONKO', 'Šubić', '', '', 'Tonko', '')],
        '0001500429': [('FRANIĆ JURE IVAN', 'Franić', 'Jure', 'Jure', 'Ivan', '')],
        '0001500469': [('GOCIĆ SVETOZARA ŽIVORAD', 'Gocić', 'Svetozara', 'Svetozar', 'Živorad', '')],
        '0001500845': [('KOČAŠEVIĆ RADOSAV', 'Kočašević', '', '', 'Radosav', '')],
        '0001500931': [('KOVAČEVIĆ ĆETNA „ĆANA"', 'Kovačević', '', '', 'Ćetna', 'Ćana')],
        '0001501583': [('PERVAN KLADNIČANIN Omera ŠEFIKA', 'Pervan-Kladničanin', 'Omera', 'Omer', 'Šefika', '')],
        '0001501645': [('OBRADOVIĆ MIRKO', 'Obradović', '', '', 'Mirko', '')],
        '0001501648': [('OMEROVIĆ SULEJMAN—CAR', 'Omerović', '', '', 'Sulejman', 'Car')],
        '0001502480': [('VRČIĆ PAŠE FRANJO', 'Vrčić', 'Paše', '', 'Franjo', '')],
        '0001502498': [('VUJOŠEVIĆ RADOMIR LJAKA', 'Vujošević', '', '', 'Radomir', 'Ljaka')],
        '0001502705': [('BAJA JOŽE', 'Baja', '', '', 'Jože', '')],
        '0001600013': [('JUŠKOVIĆ NOVAK', 'Jušković', '', '', 'Novak', ''),
                       ('KALEMBER BOZO', 'Kalember', '', '', 'Božo', ''),
                       ('KORAC MILOŠ', 'Korać', '', '', 'Miloš', ''),
                       ('KRSTONOŠIC ALEKSANDRA NANICA', 'Krstonošić', 'Aleksandra', 'Aleksandar', 'Nanica', '')],
    },
    '3-krajiska-proleterska-soldiers.json': {
        '0010202606': [('LUKIČIĆ (Stojana STEVAN', 'Lukičić', 'Stojana', 'Stojan', 'Stevan', '')],
    },
    '4-srpska-soldiers.json': {
        '0021001902': [('(KRA)GUJEVIĆ (IS)IDOR', 'Kragujević', '', '', 'Isidor', '')],
        '0021003397': [('(NI)KOLIĆ RADOMIR', 'Nikolić', '', '', 'Radomir', '')],
    },
}
# the third batch (2026-11-02): headings in every form a list prints, found by scanning the texts for a name after a
# sentence's end, read from the record and the page; python scripts/split_glued_entries.py --batch=2026-11-02 --range=LO-HI [--write]
SPLITS_2026_11_02 = {
    'prva-proleterska-soldiers.json': {
        '0001500154': [('BLAGOJEVIĆ—MIĆIĆ Vidoja MILIJANA', 'Blagojević-Mićić', 'Vidoja', 'Vidoje', 'Milijana', '')],
        '0001500163': [('BOGDANOVIĆ DRAGUHIN', 'Bogdanović', '', '', 'Dragutin', '')],
        '0001400963': [('ĆERIĆ M. MILE', 'Ćerić', 'M.', 'M.', 'Mile', '')],
        '0001500333': [('DIMITRIJEVIĆ TODOR', 'Dimitrijević', '', '', 'Todor', '')],
        '0001600008': [('15.. ĐUROVIC MILAN ŠABAN', 'Đurović', '', '', 'Milan', 'Šaban')],
        '0001502741': [('ĐUROVIĆ MITRA RADOVAN', 'Đurović', 'Mitra', 'Mitar', 'Radovan', '')],
        '0001500434': [('fILOŠEVIĆ ZDENKO', 'Filošević', '', '', 'Zdenko', '')],
        '0001500656': [('JAŠIĆ ŽIVORAD', 'Jašić', '', '', 'Živorad', '')],
        '0001500752': [('JOVANOVIĆ VASA JOVAN', 'Jovanović', 'Vasa', 'Vasa', 'Jovan', '')],
        '0001500812': [('JOVOVIĆ MILAN', 'Jovović', '', '', 'Milan', '')],
        '0001500976': [('KRILIĆ—MARINOVIĆ Mije MANDA', 'Krilić-Marinović', 'Mije', 'Mijo', 'Manda', '')],
        '0001501126': [('LOVRETA—JAKIĆ Marjana DANICA', 'Lovreta-Jakić', 'Marjana', 'Marjan', 'Danica', '')],
        '0001300999': [('MILpNKOVIĆ DRAGOSLAV', 'Milenković', '', '', 'Dragoslav', '')],
        '0001501472': [('MIRKOVIĆ BAJA VOJIN', 'Mirković', 'Baja', 'Baja', 'Vojin', '')],
        '0001501597': [('NIKOLIĆ RADOMIR', 'Nikolić', '', '', 'Radomir', '')],
        '0001502078': [('SAVIĆ-PERUNIČIĆ MILA', 'Savić-Peruničić', '', '', 'Mila', '')],
        '0001301336': [('ROMANO — DOKOVI Ć Jovana ĐURĐA — DUKA', 'Romano-Đoković', 'Jovana', 'Jovan', 'Đurđa', 'Duka')],
        '0001300628': [('KA.ČIĆ Rudolfa IVAN', 'Kačić', 'Rudolfa', 'Rudolf', 'Ivan', '')],
        '0001400345': [('KARDUN S. JOZO', 'Kardun', 'S.', 'S.', 'Jozo', '')],
        '0001500208': [('BRAJ1IĆ ŠPIRE ANTE', 'Brajlić', 'Špire', 'Špiro', 'Ante', '')],
        '0001501018': [('KULIĆ—SINKO Rista RADOJKA', 'Kulić-Sinko', 'Rista', 'Risto', 'Radojka', '')],
        '0001501887': [('Š ŠAK MARKO', 'Šišak', '', '', 'Marko', '')],
        '0001502795': [('ŠEVIĆ—ERCEG Ivana MARIJA', 'Šević-Erceg', 'Ivana', 'Ivan', 'Marija', '')],
    },
    '2-dalmatinska-soldiers.json': {'0007100468': [('jULIĆ Srđana MILE', 'Julić', 'Srđana', 'Srđan', 'Mile', '')]},
    '3-krajiska-proleterska-soldiers.json': {
        '0010202467': [('LATINO ViC-PERKOVI C Sime MILKA', 'Latinović-Perković', 'Sime', 'Simo', 'Milka', '')],
        '0010202056': [('KERKEZ -DE JANO VIĆ Nikole MILKA', 'Kerkez-Dejanović', 'Nikole', 'Nikola', 'Milka', '')],
        '0010202221': [('KOSPIĆ Luke SMILJA', 'Kospić', 'Luke', 'Luka', 'Smilja', '')],
        '0010202213': [('KORDIĆ—(BUKVIC Blagoje ANĐA', 'Kordić-Bukvić', 'Blagoje', 'Blagoje', 'Anđa', '')],
        '0010203458': [('NINIĆ Jose ANTE', 'Ninić', 'Jose', 'Joso', 'Ante', '')],
        '0010204102': [('R AD OSA VL JEVIĆ R. BOZIDAR', 'Radosavljević', 'R.', 'R.', 'Božidar', '')],
    },
    '17-slavonska-soldiers.json': {
        '0016000419': [('CICVAR A I. IVO', 'Cicvara', 'I.', 'I.', 'Ivo', '')],
        '0016003149': [('VLAISAVLJEVI C M. SAVO', 'Vlaisavljević', 'M.', 'M.', 'Savo', '')],
    },
    '4-srpska-soldiers.json': {'0021000566': [('I [VNTANOVIĆ Dragoljuba ALEKSANDAR', 'Cvetanović', 'Dragoljuba', 'Dragoljub', 'Aleksandar', '')]},
    '7-crnogorska-soldiers.json': {
        '0028010090': [('GOJ1UBOVIĆ Boškov MARKO', 'Golubović', 'Boškov', 'Boško', 'Marko', '')],
        '0028010305': [('1TOPOVIĆ Radev ĐORĐIJE', 'Popović', 'Radev', 'Rade', 'Đorđije', '')],
        '0028010326': [('RADUJ10VIĆ Petrov IVO', 'Radulović', 'Petrov', 'Petar', 'Ivo', '')],
        '0028010388': [(".Č:'JJJŠ FIJ1IP0VIĆ Petra NEĐELJKO", 'Filipović', 'Petra', 'Petar', 'Neđeljko', '')],
        '0028010088': [('GJ10MAZIĆ Tomov MOMIR MUJO', 'Glomazić', 'Tomov', 'Tomo', 'Momir', 'Mujo')],
        '0028010204': [('PUJ1TIĆ Manov NELO', 'Pultić', 'Manov', 'Mane', 'Nelo', '')],
    },
    '21-slavonska-soldiers.json': {'0034000738': [('Picek Stjepan', 'Picek', '', '', 'Stjepan', '')]},
    '1-dalmatinska-soldiers.json': {
        '0036100012': [('AKI.IAR Nikole VINKO VICO', 'Akmar', 'Nikole', 'Nikola', 'Vinko', 'Vico')],
        '0036019010': [('STANICIĆ Nikole MATE', 'Staničić', 'Nikole', 'Nikola', 'Mate', '')],
        '0036011845': [('1889a. Sarić Ivan', 'Sarić', '', '', 'Ivan', '')],
    },
    '8-crnogorska-soldiers.json': {'0038000365': [('MI/\\UTINOVIK Jagoša SAVO', 'Milutinović', 'Jagoša', 'Jagoš', 'Savo', '')]},
    '4-proleterska-soldiers.json': {'0040012067': [('31- ZEKOVIĆ. Tomov VASO', 'Zeković', 'Tomov', 'Tomo', 'Vaso', '')]},
    '6-istocnobosanska-soldiers.json': {
        '0042010012': [('Branković Slobodan', 'Branković', '', '', 'Slobodan', '')],
        '0042010058': [('Karić Božidar', 'Karić', '', '', 'Božidar', '')],
        '0042010101': [('Nedeljković Jovan', 'Nedeljković', '', '', 'Jovan', '')],
        '0042010210': [('Blagojević Ljubisav', 'Blagojević', '', '', 'Ljubisav', '')],
    },
    '7-banijska-soldiers.json': {
        '0044000896': [('RUBJEŠIĆ-BOGDANOVIĆ Nikole DANICA', 'Grubješić-Bogdanović', 'Nikole', 'Nikola', 'Danica', '')],
        '0044010231': [('D2AKULA Mile JOVO', 'Džakula', 'Mile', 'Mile', 'Jovo', '')],
        '0044010840': [('SEKÜLIC I. MILAN', 'Sekulić', 'I.', 'I.', 'Milan', '')],
        '0044011020': [('CUÖKOVIC Dure SVETOZAR', 'Čučković', 'Dure', 'Đuro', 'Svetozar', '')],
        '0044011027': [('D AKO VIC N. STEVO', 'Đaković', 'N.', 'N.', 'Stevo', '')],
    },
    '7-krajiska-soldiers.json': {
        '0048010714': [('1DEVER Marka STEVO', 'Džever', 'Marka', 'Marko', 'Stevo', '')],
        '0048011493': [('KLoAJIĆ MLADEN', 'Kljajić', '', '', 'Mladen', '')],
        '0048000699': [('PON.TEVIĆ Mile BOGOLJUB', 'Ponjević', 'Mile', 'Mile', 'Bogoljub', '')],
        '0048012829': [('RADUAa ICA Mile BRANKO', 'Raduljica', 'Mile', 'Mile', 'Branko', '')],
        '0048010017': [('A DŽŽ Spasoja MLADEN', 'Adžić', 'Spasoja', 'Spasoje', 'Mladen', '')],
        '0048010645': [('DRAGOL)EVIĆ Mihajla MILAN', 'Dragoljević', 'Mihajla', 'Mihajlo', 'Milan', '')],
        '0048010740': [('FRAzAK Saliha KASIM', 'Fraljak', 'Saliha', 'Salih', 'Kasim', '')],
        '0048010874': [('rOAUBOBIĆ Jove MITAR', 'Golubović', 'Jove', 'Jovo', 'Mitar', '')],
        '0048010876': [('rOTOBULUA Dede XUCO', 'Gotobulija', 'Dede', 'Dedo', 'Huso', '')],
        '0048011355': [('KALzALIK SALIH', 'Kaljalik', '', '', 'Salih', '')],
        '0048011496': [('KLzAJIĆ Stojana STANKO', 'Kljajić', 'Stojana', 'Stojan', 'Stanko', '')],
        '0048011690': [('KRKELzAŠ Milana STANKO', 'Krkeljaš', 'Milana', 'Milan', 'Stanko', '')],
        '0048012404': [('OAaAČA Mirka DANE', 'Oljača', 'Mirka', 'Mirko', 'Dane', '')],
        '0048012599': [('PLEVLoAK Ibrahima ALIJA', 'Plevljak', 'Ibrahima', 'Ibrahim', 'Alija', '')],
        '0048013790': [('3VKIĆ Burća MILOŠ', 'Zukić', 'Burća', 'Đurađ', 'Miloš', '')],
        '0048013833': [('4UBPHAO Pere MILAN', 'Čubrilo', 'Pere', 'Pero', 'Milan', '')],
        '0048013834': [('4UPO Hašima AAEM', 'Čupo', 'Hašima', 'Hašim', 'Adem', ''), ('4UTUPA AUIIIAH', 'Čutura', '', '', 'Dušan', '')],
        '0048013952': [('1IIAPAMU3UPOB ZUJEVIČ', 'Šaramuzov', '', '', 'Zujevič', '')],
        '0048014054': [('Ž U Ž IĆ Derviša SEKIBA', 'Žužić', 'Derviša', 'Derviš', 'Sekiba', '')],
    },
    '3-vojvodjanska-soldiers.json': {'0057003446': [('T0PAJ10VIN LJUBICA', 'Topalović', '', '', 'Ljubica', '')]},
    'kalnicki-odred-soldiers.json': {'0058001825': [('Mmović IVAN, Valenta', 'Mirković', 'Valenta', 'Valent', 'Ivan', '')]},
    '8-kordunaska-divizija-soldiers.json': {
        '0060002585': [('SAUL A Mihajla JOVAN', 'Šaula', 'Mihajla', 'Mihajlo', 'Jovan', '')],
        '0060002627': [('5TJPICA Damjana ILIJA', 'Šupica', 'Damjana', 'Damjan', 'Ilija', '')],
        '0060002669': [('2IVKOVIĆ Marka GLIŠO', 'Živković', 'Marka', 'Marko', 'Glišo', '')],
        '0060002670': [('2IVKOVIĆ Mile DUŠAN', 'Živković', 'Mile', 'Mile', 'Dušan', '')],
    },
    '22-srpska-soldiers.json': {
        '0074000193': [('J FILIPOVIĆ Bogosava TIHOMIR', 'Filipović', 'Bogosava', 'Bogosav', 'Tihomir', '')],
        '0074000557': [('/mILJUŠEVIĆ DUŠAN', 'Miljušević', '', '', 'Dušan', '')],
    },
    '19-sjevernodalmatinska-soldiers.json': {
        '0079000988': [('RÜSTEN Nasen HAMID', 'Rusten', 'Nasen', 'Nasen', 'Hamid', '')],
        '0079001235': [('VÜLIC Šime JOZO', 'Vulić', 'Šime', 'Šime', 'Jozo', '')],
    },
    '7-srpska-soldiers.json': {
        '0085000407': [('248. L.UBENOVIĆ R. JOCA', 'Ljubenović', 'R.', 'R.', 'Joca', '')],
        '0085000740': [('404. G10P0VIĆ D. MILUTIN', 'Popović', 'D.', 'D.', 'Milutin', '')],
    },
    '15-srpska-soldiers.json': {'0086000079': [('1IAKIĆ DUŠAN', 'Ćakić', '', '', 'Dušan', '')]},
    '10-srpska-soldiers.json': {
        '0088000032': [('CVETANOVIĆ Alekse STANKO', 'Cvetanović', 'Alekse', 'Aleksa', 'Stanko', '')],
        '0088000076': [('d ILIĆ Milana NOVICA', 'Ilić', 'Milana', 'Milan', 'Novica', '')],
        '0088000111': [('1SOSTIĆ Ranđela VIDEN', 'Kostić', 'Ranđela', 'Ranđel', 'Viden', '')],
        '0088000130': [('S MANIĆ Vukadina STANKO', 'Manić', 'Vukadina', 'Vukadin', 'Stanko', '')],
        '0088000190': [('L1.LAPKNOVIĆ STANKO', 'Mladenović', '', '', 'Stanko', '')],
    },
    '23-srpska-soldiers.json': {
        '0089000097': [('JAnUNIJNR Ilije MILEVA', 'Japundžić', 'Ilije', 'Ilija', 'Mileva', '')],
        '0089000144': [('JjEOŽAKOVIN Božidara ŽIVOTA', 'Kožaković', 'Božidara', 'Božidar', 'Života', '')],
        '0089000255': [('NVdEAzKOVIK BORIVOJE', 'Nedeljković', '', '', 'Borivoje', '')],
        '0089000347': [('CnACNR Božidara DUŠAN', 'Spasić', 'Božidara', 'Božidar', 'Dušan', '')],
    },
    '12-srpska-soldiers.json': {'0090000132': [('K.OCIĆ I. ALEKSANDAR', 'Kocić', 'I.', 'I.', 'Aleksandar', '')]},
    '14-primorsko-goranska-soldiers.json': {
        '0095000079': [('Car Milan', 'Car', '', '', 'Milan', '')],
        '0095000082': [('Cetinski Ivan', 'Cetinski', '', '', 'Ivan', '')],
    },
    '6-dalmatinska-soldiers.json': {'0103000153': [('KR1VIC FILIP', 'Krivić', '', '', 'Filip', ''), ('KRIV1C F. FILIP', 'Krivić', 'F.', 'F.', 'Filip', '')]},
    'osjecka-soldiers.json': {
        '0104000016': [('ALEKSIC rođena LEKŠAN KATA', 'Aleksić', '', '', 'Kata', 'rođ. Lekšan')],
        '0104001049': [('MISANUK MIJO', 'Misanuk', '', '', 'Mijo', '')],
        '0104001218': [('SERTIČ rođena RADIVOJEVIC MILEVA', 'Sertić', '', '', 'Mileva', 'rođ. Radivojević')],
        '0104001412': [('5PAK IVAN', 'Špak', '', '', 'Ivan', '')],
        '0104001561': [('TÜRK Jakoba VIKTOR', 'Turk', 'Jakoba', 'Jakob', 'Viktor', '')],
        '0104001811': [('ŠARIRI rođena HOVANJEC JELKA', 'Šarić', '', '', 'Jelka', 'rođ. Hovanjec')],
        '0104001842': [('Š TE VIC Josipa ANTUN', 'Štević', 'Josipa', 'Josip', 'Antun', '')],
    },
    'posavski-odred-soldiers.json': {
        '0110000527': [('IVKOVIN Lj. MIHAIAO', 'Ivković', 'Lj.', 'Lj.', 'Mihailo', '')],
        '0110002313': [('VŠ1ETA NIKOLA', 'Vuleta', '', '', 'Nikola', '')],
    },
    '3-licka-soldiers.json': {
        '0118000804': [('SOVI—LJ J. MILE', 'Sovilj', 'J.', 'J.', 'Mile', '')],
        '0118000871': [('VOJINOVIC M. JOV O', 'Vojinović', 'M.', 'M.', 'Jovo', '')],
    },
    'mostarski-bataljon-soldiers.json': {'0125000593': [('MILAN SAKOTIĆ', 'Šakotić', '', '', 'Milan', '')]},
    'cacanski-odred-soldiers.json': {'0126001074': [('IgPIĆ. Slavke DUŠAN', 'Ilić', 'Slavke', 'Slavko', 'Dušan', '')]},
    '5-srpska-soldiers.json': {
        '0127000123': [('TA4HR Milorada MILETA', 'Tačić', 'Milorada', 'Milorad', 'Mileta', '')],
        '0127000281': [('KY3MAH0BHR STEVAN', 'Kuzmanović', '', '', 'Stevan', '')],
        '0127000838': [('BY4KOBHR BLAGOJE', 'Vučković', '', '', 'Blagoje', ''), ('BY4KOBHR Tome BOŽIDAR', 'Vučković', 'Tome', 'Toma', 'Božidar', '')],
        '0127000849': [('B0KOVIB ALEKSANDAR', 'Đoković', '', '', 'Aleksandar', '')],
    },
    '18-srpska-soldiers.json': {
        '0128000709': [('HAHnOBHR SAVA', 'Filipović', '', '', 'Sava', '')],
        '0128000715': [('HAHnOBHR MIRKO', 'Filipović', '', '', 'Mirko', '')],
        '0128004687': [('3APHR RAFAJLO', 'Zarić', '', '', 'Rafajlo', '')],
        '0128004702': [('3E4EBHR BOGDAN', 'Zečević', '', '', 'Bogdan', ''), ('3E4EBHR BOŽIDAR', 'Zečević', '', '', 'Božidar', ''),
                       ('3E4EBHR ILIJA', 'Zečević', '', '', 'Ilija', ''), ('3E4EBHR JOVAN', 'Zečević', '', '', 'Jovan', '')],
        '0128004703': [('3E4EBHR TIHOMIR', 'Zečević', '', '', 'Tihomir', '')],
        '0128004704': [('3AATAHOBHR SVETOZAR', 'Zlatanović', '', '', 'Svetozar', ''), ('3AATAHOBHR SLAVKO', 'Zlatanović', '', '', 'Slavko', ''),
                       ('3AORAHOBHR BRANISLAV', 'Zloganović', '', '', 'Branislav', '')],
        '0128004706': [('3PHHR RADOSLAV', 'Zrnić', '', '', 'Radoslav', ''), ('3YEHR NIKOLA', 'Zubić', '', '', 'Nikola', '')],
        '0128004707': [('30PBHR MILOSAV', 'Zorvić', '', '', 'Milosav', ''), ('30PHR ŽIVKO', 'Zorić', '', '', 'Živko', '')],
        '0128004708': [('30PBHR DIMITRIJE', 'Zorvić', '', '', 'Dimitrije', '')],
        '0128004726': [('40PHR MIRKO', 'Čorić', '', '', 'Mirko', '')],
    },
    '42-vazduhoplovna-soldiers.json': {'0140001140': [('BABIĆ N. DUŠAN', 'Babić', 'N.', 'N.', 'Dušan', '')]},
    'mosorski-odred-soldiers.json': {
        '0148000095': [('ARMAND A Jure MARKO', 'Armanda', 'Jure', 'Jure', 'Marko', '')],
        '0148003314': [('dUKIC Petra LOVRE', 'Đukić', 'Petra', 'Petar', 'Lovre', '')],
    },
}
# a man's heading at the end of another's text, whose own record stands already: the host's text is only cut there
SPLITS_2026_11_02.setdefault('21-slavonska-soldiers.json', {})['0034000904'] = [('Stojčević Milka', 'Stojčević', '', '', 'Milka', ''), ('Stojčig. Milan', 'Stojčić', 'G.', 'G.', 'Milan', '')]
SPLITS_2026_11_02.setdefault('8-crnogorska-soldiers.json', {})['0038000622'] = [('VIŽNITIN IvadaSAVO', 'Vižnitin', 'Ivada', 'Ivan', 'Savo', '')]
SPLITS_2026_11_02.setdefault('22-srpska-soldiers.json', {})['0074001298'] = [('jUNIĆ ZORICA', 'Žunić', '', '', 'Zorica', '')]
SPLITS_2026_11_02.setdefault('osjecka-soldiers.json', {})['0104001049'] = [('MISANUK MIJO', 'Mišanuk', '', '', 'Mijo', '')]
CUT_2026_11_02 = {'0001400252': 'GRUBIĆIŠ Ante LJUBO', '0001400706': 'POPOVIĆ Milivoja MAR', '0001400813': 'SLADOLJEV Ante KAR', '0103000151': 'KOVACEVIC F. VJEKO',
                  '0060002000': 'SA VIC Nikole SAVO', '0126001199': 'BOKOVIĆ. Živorada SLAVKO', '0128003566': 'ADULOVIE DRAGUTIN', '0001400236': 'GRLIĆ J. ANKA'}
# the same on 2026-11-03: men in the small letters of their lists, after a sentence's end; python scripts/split_glued_entries.py --batch=2026-11-03 --range=LO-HI [--write]
SPLITS_2026_11_03 = {
    '1-dalmatinska-soldiers.json': {
        '0036010439': [('Delonga J. Jakov', 'Delonga', 'J.', 'J.', 'Jakov', '')],
        '0036011125': [('Letica A. Petar', 'Letica', 'A.', 'A.', 'Petar', '')],
        '0036011280': [('Matijaš J. Marko', 'Matijaš', 'J.', 'J.', 'Marko', '')],
        '0036011424': [('Morožin L. Marko', 'Morožin', 'L.', 'L.', 'Marko', '')],
        '0036011462': [('Novak Đ. Tomo', 'Novak', 'Đ.', 'Đ.', 'Tomo', '')],
        '0036011486': [('Oštrlć M. Marko', 'Oštrić', 'M.', 'M.', 'Marko', '')],
        '0036019013': [('Sarić I. Jure', 'Sarić', 'I.', 'I.', 'Jure', '')],
    },
    '6-istocnobosanska-soldiers.json': {
        '0042010107': [('Njevdić R. Srećko', 'Njevdić', 'R.', 'R.', 'Srećko', '')],
        '0042019004': [('Čolić Milosava Dragomir', 'Čolić', 'Milosava', 'Milosav', 'Dragomir', ''), ('Bokić Milovana Dobrosav', 'Đokić', 'Milovana', 'Milovan', 'Dobrosav', ''),
                       ('Desivojević Petlja Ljubiša', 'Desivojević', 'Petlja', 'Petlja', 'Ljubiša', ''), ('Ivanović Jovana Živadin', 'Ivanović', 'Jovana', 'Jovan', 'Živadin', ''),
                       ('Jakovljević Dušana Dragan', 'Jakovljević', 'Dušana', 'Dušan', 'Dragan', ''), ('Jakovljević Radoja Miroslav', 'Jakovljević', 'Radoja', 'Radoje', 'Miroslav', ''),
                       ('Jakovljević Jovana Božidar', 'Jakovljević', 'Jovana', 'Jovan', 'Božidar', ''), ('Joksimović Živana Radosav', 'Joksimović', 'Živana', 'Živan', 'Radosav', ''),
                       ('Karić Radojka Milovan', 'Karić', 'Radojka', 'Radojko', 'Milovan', ''), ('Mitrovnć Živote Vukosav', 'Mitrović', 'Živote', 'Života', 'Vukosav', ''),
                       ('Nektorijević Dragoljuba Branko', 'Nektorijević', 'Dragoljuba', 'Dragoljub', 'Branko', ''), ('Nešović Žika Radojica', 'Nešović', 'Žika', 'Žika', 'Radojica', ''),
                       ('Pantelić Živojina Dragoljub', 'Pantelić', 'Živojina', 'Živojin', 'Dragoljub', ''), ('Savović Radojice Stojan', 'Savović', 'Radojice', 'Radojica', 'Stojan', ''),
                       ('Savović Mihajla Dušan', 'Savović', 'Mihajla', 'Mihajlo', 'Dušan', ''), ('Slavković Mijodraga Rajko', 'Slavković', 'Mijodraga', 'Mijodrag', 'Rajko', ''),
                       ('Zorić Vojislava Mihajilo', 'Zorić', 'Vojislava', 'Vojislav', 'Mihajilo', ''), ('Katanić Milana Branko', 'Katanić', 'Milana', 'Milan', 'Branko', ''),
                       ('Milutinović Milana Živomir', 'Milutinović', 'Milana', 'Milan', 'Živomir', ''), ('Ristović Riste Radiša', 'Ristović', 'Riste', 'Rista', 'Radiša', '')],
    },
    '19-srpska-soldiers.json': {
        '0073001928': [('ćuguz Nikola', 'Ćuguz', '', '', 'Nikola', ''), ('ćuguz Miloš', 'Ćuguz', '', '', 'Miloš', '')],
        '0073003127': [('ćirkić K. Živorad', 'Ćirkić', 'K.', 'K.', 'Živorad', '')],
    },
    '6-vojvodjanska-soldiers.json': {
        '0083000167': [('Milaš Aleksandar', 'Milaš', '', '', 'Aleksandar', '')],
    },
    '14-primorsko-goranska-soldiers.json': {
        '0095000082': [('Cenčić A. Zivko', 'Cenčić', 'A.', 'A.', 'Živko', '')],
        '0095000086': [('Crljenko Jadra Jadre', 'Crljenko', 'Jadra', 'Jadre', 'Jadre', ''), ('Grljenko Pavo', 'Crljenko', '', '', 'Pavo', '')],
        '0095000092': [('Cvitković F. Stjepan', 'Cvitković', 'F.', 'F.', 'Stjepan', '')],
    },
}

# what a heading's own words leave in the man's text: the name's rest up to the bio
NAME_TAIL = re.compile(r'^\s*(?:\((?:VESIN|Rajšić)\)\s*)?(?:MILKA\s*)?')
# page furniture glued in between: a list's title, an entry's number, a speck
JUNK = [r'\s*A VODE SE U EVIDENCIJI:\.?$', r"\s*[,']?\s*(?:AÓ 4G3|109G|1256|138Ö|14\.,,n|1447|1889b)\.$", r'\s*AESTE DALMATINSKE BRIGADE LI BORCI$', r'\s*PREŽIVJELI BO \(na dan 15\.$', r'\s*[:•«■]\s*\d{1,3}\.$',
        r'\s*-i\.$', r'\s*I$', r'\s*N E M C I :$']


def cleaned(text: str) -> str:
    text = text.strip()
    for p in JUNK:
        text = re.sub(p, '', text).strip()
    return text


def fold(s: str) -> str:
    return re.sub(r'[^A-Z]', '', s.upper().translate(str.maketrans('ČĆŽŠĐ', 'CCZSD')))


_pages = {}


def words(pdf_file: str, page: int) -> list:
    key = (pdf_file, page)
    if key not in _pages:
        with pdfplumber.open(ROOT / 'website' / 'public' / 'pdfs' / pdf_file) as pdf:
            _pages[key] = viewer_words(pdf.pages[page - 1]) if page <= len(pdf.pages) else []
    return _pages[key]


def find(host: dict, heading: str, after: tuple, body: str = '') -> tuple:
    """(page, x, y, box words) of the heading's first word in capitals: the first after `after` (page, column, y) in
    reading order, the columns of a page split at its middle"""
    for first in (heading.split()[0].rstrip(','), heading.split()[-1].rstrip(',')):   # the surname, else the given name
        hit = _find(host, first, after)                                # (the scan's ДУБЈБЕВИЋ for Dubljević)
        if hit:
            return hit
    hit = _by_body(host, body, after)
    if hit:
        return hit
    raise SystemExit(f"not found: {heading} after {after} in {host['pdf_file']}")


def _by_body(host: dict, body: str, after: tuple):
    """A name's capitals past reading: the line that holds the words after it, the first after `after` in reading order."""
    want = fold(cyrillic_to_latin(body))[:14]
    if len(want) < 6:
        return None
    for p in range(host['pdf_page'], host['pdf_page'] + 3):
        ws = words(host['pdf_file'], p)
        if not ws:
            continue
        mid = (min(w['x0'] for w in ws) + max(w['x1'] for w in ws)) / 2
        if len(after) == 4:
            after = (after[0], after[1] > mid, after[2] + 3)
        lines = {}
        for w in ws:
            lines.setdefault((w['x0'] > mid, round(w['top'] / 4)), []).append(w)
        for (right, _), line in sorted(lines.items(), key=lambda kv: (kv[0][0], min(w['top'] for w in kv[1]))):
            line.sort(key=lambda w: w['x0'])
            order = (p, right, line[0]['top'])
            if order > after and want[:8] in fold(cyrillic_to_latin(' '.join(w['text'] for w in line))):
                return order, round(line[0]['x0'], 1), round(line[0]['top'], 1)
    return None


def _find(host: dict, first: str, after: tuple):
    for p in range(host['pdf_page'], host['pdf_page'] + 9):          # a bio can run over pages
        ws = words(host['pdf_file'], p)
        if not ws:
            continue
        mid = (min(w['x0'] for w in ws) + max(w['x1'] for w in ws)) / 2
        if len(after) == 4:                                            # the host's place: (page, x, y, 'host')
            after = (after[0], after[1] > mid, after[2] + 3)            # below the host's own heading, in its column
        cands = []
        for w in ws:
            plain = cyrillic_to_latin(w['text']).rstrip(',.')
            t = plain.replace('l', 'I')                                 # "ĐAPlC": the scan's l for I in capitals
            if plain == first or t == first or (t.isupper() and len(t) > 2 and fold(t) == fold(first)):
                order = (p, w['x0'] > mid, w['top'])
                if order > after:
                    cands.append((order, w))
        if cands:
            order, w = min(cands, key=lambda c: c[0])
            # the line's start in that column ("•21. GUBEROVIĆ", or the given name the fallback found)
            line = [v for v in ws if abs(v['top'] - w['top']) < 2 and (v['x0'] > mid) == (w['x0'] > mid) and v['x0'] <= w['x0']]
            return order, round(min(v['x0'] for v in line), 1), round(w['top'], 1)
    return None


def _unit_file(soldier_id: str) -> str:
    sys.path.insert(0, str(ROOT / 'scripts'))
    from name_utils import BRIGADE_CONFIGS
    return BRIGADE_CONFIGS[int(soldier_id[:4])]['json_file']


def main():
    lo, hi = [int(v) for v in next(a for a in sys.argv if a.startswith('--range=')).split('=')[1].split('-')]
    corr = json.load(open(ROOT / 'corrections.json', encoding='utf-8'))
    nid = max([c['id'] for c in corr if lo <= c['id'] <= hi] + [lo - 1]) + 1
    taken = {c.get('new_id') for c in corr if c['action'] == 'add'}
    taken |= {c['merge_id'] for c in corr if c['action'] == 'merge'} | {c['soldier_id'] for c in corr if c['action'] == 'delete'}    # an id an older correction names, though no record holds it now
    table = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--table=')), None)                                   # {unit file: {host: [heading, surname, father as printed, father, given name, nick]}}
    new = []
    third = '--batch=2026-11-02' in sys.argv
    fourth = '--batch=2026-11-03' in sys.argv
    second = '--batch=2026-10-31' in sys.argv or third or fourth
    reason = R.replace('2026-10-17', '2026-11-03' if fourth else '2026-11-02' if third else '2026-10-31') if second else R
    if third:
        for hid, tail in CUT_2026_11_02.items():
            for s in json.load(open(ROOT / 'website' / 'public' / _unit_file(hid), encoding='utf-8')):
                for e in [s] + [o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book')]:
                    if e.get('soldier_id') == hid and tail in (e.get('additional_info') or ''):
                        new.append({'action': 'edit', 'soldier_id': hid, 'fields': {'additional_info': cleaned(e['additional_info'][:e['additional_info'].index(tail)])},
                                    'reason': f"{e.get('full_name') or e.get('name')}: the next man's heading glued into its text, his own record stands; {reason}"})
    for unit_file, hosts in (json.load(open(table, encoding='utf-8')) if table else SPLITS_2026_11_03 if fourth else SPLITS_2026_11_02 if third else SPLITS_2026_10_31 if second else SPLITS).items():
        recs = json.load(open(ROOT / 'website' / 'public' / unit_file, encoding='utf-8'))
        code = recs[0]['soldier_id'][:4]
        used = {s['soldier_id'] for s in recs} | {o.get('soldier_id') for s in recs for o in s.get('other_sources', ())} | taken
        found = {}
        for s in recs:
            for e in [s] + [o for o in s.get('other_sources', ()) if not o.get('unit_file') and not o.get('ref_book')]:
                if e.get('soldier_id') in hosts:
                    found[e['soldier_id']] = (s, e)
        for hid, men in hosts.items():
            keeper, host = found[hid]
            info = host['additional_info']
            pos = []
            for heading, *_ in men:
                i = info.find(heading, pos[-1] + 1 if pos else 0)
                assert i > 0, (hid, heading)
                pos.append(i)
            new.append({'action': 'edit', 'soldier_id': hid, 'fields': {'additional_info': cleaned(info[:pos[0]])},
                        'reason': f"{host.get('full_name') or host.get('name')}: the next entries were glued into its text; {reason}"})
            after = (host['pdf_page'], host['pdf_x'], host['pdf_y'], 'host') if host.get('pdf_file') else None    # a list on a web page has no place on a page
            # the glued men take ids in the host's list's block, from 9001 (0053000195 -> 0053009001-)
            block = int(hid[4:]) // 10000 * 10000
            for k, (heading, last, fgen, fnom, given, nick) in enumerate(men):
                body = info[pos[k] + len(heading):(pos[k + 1] if k + 1 < len(men) else len(info))]
                body = cleaned(NAME_TAIL.sub('', body).lstrip(' ,.' if second else ' ,'))
                if heading == 'STIMEC FRANJO':
                    body = re.sub(r'^Matije,\s*', '', body)
                if nick:
                    body = f'{nick}; {body}' if nick.startswith('rođ.') else f'zvani {nick}; {body}'
                if table:
                    # the list holds him already, under a name its parser read, or a row marked no one of ours: the host is only cut
                    held = next((r for r in recs if r is not host and len(body) >= 25 and fold(r.get('last_name') or '')[:4] == fold(last)[:4] and fold(r.get('first_name') or '') == fold(given)
                                 and cleaned(r.get('additional_info') or '').lstrip(' ,.').startswith(body[:40])), None)
                    if held or not last:
                        print('   HELD', heading, '|', held.get('full_name') if held else 'no record', '|', body[:60])
                        continue
                rec = {'last_name': last, 'middle_name': fgen, 'fathers_name': fnom, 'first_name': given, 'additional_info': body}
                if host.get('pdf_file'):
                    try:
                        order, x, y = find(host, heading, after, body)
                    except SystemExit:
                        if not table:
                            raise
                        print('   NO PLACE', heading, 'after', after, host['pdf_file'])
                        order = (after[0], False, after[2] + 11) if len(after) == 3 else (after[0], after[1] > 280, after[2] + 11)
                        x, y = host['pdf_x'], round(order[2], 1)
                    after = order
                    rec.update(pdf_file=host['pdf_file'], pdf_page=order[0], pdf_x=x, pdf_y=y)
                else:
                    order, x, y = (0,), 0, 0
                    rec.update({k: host[k] for k in ('source_url', 'source_page') if host.get(k)})
                seq = block + 9001
                while f'{code}{seq:06d}' in used:
                    seq += 1
                new_id = f'{code}{seq:06d}'
                used.add(new_id)
                new.append({'action': 'add', 'soldier_id': keeper['soldier_id'], 'new_id': new_id, 'record': rec,
                            'reason': f"{last} {fgen + ' ' if fgen else ''}{given}: glued into the entry of "
                                      f"{host.get('full_name') or host.get('name')}; {reason}"})
                print(new_id, last, fgen, given, nick, f"p{order[0]} x{x} y{y}", '|', body[:70])
    for i, c in enumerate(new):
        c['id'] = nid + i
    assert nid + len(new) - 1 <= hi, 'past the range'
    print(len(new), 'corrections,', sum(c['action'] == 'add' for c in new), 'men')
    if '--write' in sys.argv:
        corr += new
        open(ROOT / 'corrections.json', 'w', encoding='utf-8', newline='\n').write(json.dumps(corr, ensure_ascii=False, indent=2) + '\n')
        print('written', new[0]['id'], '-', new[-1]['id'])


if __name__ == '__main__':
    main()
