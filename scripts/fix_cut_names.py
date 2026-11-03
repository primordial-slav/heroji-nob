"""
Names the parsers cut or glued, read from the page or from the same man in another book (2026-11-02).

  HEADS    A surname cut in two, with the rest of the name left in the text ("Dogato | Vić" + "Riste DUŠAN, rođen ...": Dogatović Riste Dušan; "Za | Viša";
           "Ži | Vano" + "zvani Vić Živorad"), a double surname ("Dumić | Žafran" + "Tome ANKICA"), a nickname that opens with a surname's tail ("Šaren" + "zvani Ac":
           Šarenac), a given name glued to the surname ("Leviisak"). id -> (surname, father as printed, father in the nominative, given name, cut from the text, put instead).
  STRAYS   A line of the entry before read as a man ("Gš | Nov" + "i PO Srbije. Radio ...", the end of Kovancić Slobodan's text over a page): the line goes back, the record goes.
  NINTH    The 9. srpska's lists print some surnames spaced ("СТЕВ АНОВИЋ"), which its parser took for two names, so three Stevanovićes were one record; and men printed in two
           of its lists under two spellings or a married name are one man.
  by_books A surname the scan cut at the column's edge or misread ("Os" Raos, "Atinović" Latinović, "Uubanić" Ljubanić), from the same man in another book: the same father, given
           name and village, the birth year within a year (three where the spelling is close), the fragment borne by next to no one and the other surname by many; no double surname.
  given_by_books  The same for a given name ("Mafe" Mate, "Ljuvisav" Ljubisav) or a father ("Vrkašina" Vukašin).

Run: python scripts/fix_cut_names.py [--since ID] [--write START]; a name changed here also changes in the guards that hold it (link_name, merge_name, identity_decisions.json).
--since: texts come from the corrections from that id on where they set one (an earlier script of the same batch), else from the unit files.
"""
import collections, difflib, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
from name_utils import BRIGADE_CONFIGS

HEADS = {
    # Beogradski bataljon
    '0001300995': ('Milanović', 'Miodraga', 'Miodrag', 'Radoje', 'Miodraga RADOJE, ', ''),
    '0001301028': ('Miličević', 'Milanka', 'Milanko', 'Radojka', 'Milanka RADOJKA, ', ''),
    '0001301030': ('Miljković', 'Živana', 'Živan', 'Radovan', 'Zivana RADOVAN, ', ''),
    '0001301292': ('Paunović', '', '', 'Ljubiša', '(PAUNIĆ) LJUBISA ', '(ili Paunić) '),
    '0001301950': ('Ćirić', '', '', 'Bora', '(ĐORĐEVIĆ) BORA, poli- tički radnik ', '(ili Đorđević), politički radnik. '),
    '0001302040': ('Đukić', '', '', 'Milan', '(DUNIĆ) MILAN ', '(ili Dunić) '),
    '0001302052': ('Đuluk', '', '', 'Obrad', '(ĐULK) OBRAD ', '(ili Đulk) '),
    '0001300387': ('Goranja', 'Stanoja', 'Stanoje', 'Ilija', '(GARANJA, GARONJA) Stanoja ILIJA ', '(ili Garanja, Garonja) '),
    '0001300585': ('Josipović', '', '', 'Srbolub', '', 'zvani Srba; '),
    '0001300833': ('Levi', '', '', 'Isak', '', ''),
    '0001300419': ('Handanović', '', '', 'Islam', '', ''),
    # Borci Sutjeske
    '0001100298': ('Femić', '', '', 'Savić', '', ''),
    '0005101101': ('Čović', '', '', 'Savić', '', ''),
    '0040001274': ('Simonović', '', '', 'Lakić', '', ''),
    '0001100546': ('Katić', 'Mate', 'Mate', 'Niko', '', ''),
    '0001101174': ('Popović-Stilinović', '', '', 'Nada', 'zvana Vić Nada; ', ''),
    '0001101574': ('Vukašinović-Duletić', '', '', 'Julija', 'zvana Vić-d Uletić Julija; ', ''),
    '0001101848': ('Živanović', '', '', 'Živorad', 'zvani Vić Živorad; ', ''),
    '0005101086': ('Četković-Vidojević', 'Radoša', 'Radoš', 'Blaža', 'Radoša BLA-ŽA, ', ''),
    '0007100521': ('Beus', 'Mate', 'Mate', 'Ivan', '', ''),
    '0007100522': ('Beus', 'Ivana', 'Ivan', 'Marko', '', ''),
    '0039100152': ('Divac', '', '', 'Vojislav', 'zvani Vojislav Lala; ', 'zvani Lala; '),
    '0041001080': ('Radović', 'Mihaila', 'Mihailo', 'Vidak', 'zvani Ak Kića; ', 'zvani Kića; '),
    '0045000042': ('Biškupović', '', '', 'Branko', 'zvani Ović Branko; ', ''),
    '0045000604': ('Šaša', 'Steve', 'Stevo', 'Stevan', '', ''),
    '0045000605': ('Šaša', 'Adama', 'Adam', 'Stevo', '', ''),
    '0045000802': ('Šaša', 'Pavla', 'Pavle', 'Božo', '', ''),
    '0045000803': ('Šaša', 'Đure', 'Đuro', 'Dušan', '', ''),
    '0045000804': ('Šaša', 'Pere', 'Pero', 'Ilija', '', ''),
    '0045000805': ('Šaša', 'Ljubice', 'Ljubica', 'Lazo', '', ''),
    '0045000806': ('Šaša', 'Pere', 'Pero', 'Rade', '', ''),
    '0046001101': ('Buk', 'Jakova', 'Jakov', 'Mate', '', ''),
    '0047000013': ('Ćelap', 'Mile', 'Mile', 'Boško', '', ''),
    '0047000014': ('Arlov', 'Jandre', 'Jandre', 'Đuro', 'zvani .landre Đuro; ', ''),
    # the units' own lists
    '0003010393': ('Bubalo', 'Bože', 'Božo', 'Ilija', 'I UJA ', ''),
    '0003021335': ('Nancić', 'Devičin', '', 'Stevo', 'N STEVO ', ''),
    '0006001178': ('Dijanović-Gradišar', 'Ivana', 'Ivan', 'Dragica', 'Ivana DRAGICA, ', ''),
    '0006001339': ('Dumić-Žafran', 'Tome', 'Tomo', 'Ankica', 'Tome ANKICA, ', ''),
    '0006002507': ('Jokić-Mirković', 'Gaje', 'Gajo', 'Goša', 'Gaje GOŠA, ', ''),
    '0006002627': ('Jovašinović', '', '', 'Anton', '', ''),
    '0006003791': ('Marijančić', '', '', 'Zvonko', '', ''),
    '0006006026': ('Sabnik', '', '', 'Slavko', '', ''),
    '0006006485': ('Stević', '', '', 'Momčilo', '', ''),
    '0010000315': ('Dogatović', 'Riste', 'Risto', 'Dušan', 'Riste DUŠAN, ', ''),
    '0010000316': ('Dogatović', 'Luke', 'Luka', 'Stana', 'Luke STANA, ', ''),
    '0010000429': ('Grabovac', 'Vice', 'Vice', 'Petar', 'Vice PETAR, ', ''),
    '0010000639': ('Kalaver', 'Joje', 'Jojo', 'Čedo', 'Jo je CEDO, ', ''),
    '0010000831': ('Krajinović', 'Dane', 'Dane', 'Ilija', 'Dane ILIJA, ', ''),
    '0010000849': ('Kunovac', 'Todora', 'Todor', 'Savo', 'Todora SAVO, ', ''),
    '0010001627': ('Savić', 'Ivana', 'Ivan', 'Ruža', 'Ivana RUŽA, ', ''),
    '0010001844': ('Tasovac', 'Boška', 'Boško', 'Luka', 'Boška LUKA, ', ''),
    '0010001923': ('Ugrenović', 'Todora', 'Todor', 'Mićo', 'Todora MIĆO, ', ''),
    '0010001981': ('Vojnović', 'Ilije', 'Ilija', 'Nikola', 'Ilije NIKOLA, ', ''),
    '0010002175': ('Đurović', 'Perov', 'Pero', 'Savo', 'Perov SAVO, ', ''),
    '0010000301': ('Di Magio', '', '', 'Cosimo', '', ''),
    '0010000394': ('Gavanga', '', '', 'Francesco', '', ''),
    '0010001270': ('Pavino', '', '', 'Teodore', '', ''),
    '0010201116': ('Frassetto', '', '', '', '', ''),
    '0013000413': ('Gvozdenović', 'Nikole', 'Nikola', 'Đura', 'Nikole DURA, ', ''),
    '0013000519': ('Kaurin', '', '', 'Gojko', '', ''),
    '0013000674': ('Krajinović', 'Petra', 'Petar', 'Milka', 'Petra MILKA, ', ''),
    '0013000839': ('Marijanović', 'M', 'M', 'Nedeljko', 'M. NEDELJKO, ', ''),
    '0013001097': ('Obradović', 'I', 'I', 'Milan', 'I. MILAN, ', ''),
    '0013001098': ('Obradović', 'P', 'P', 'Milan', 'P. MILAN, ', ''),
    '0013001099': ('Obradović', 'Rade', 'Rade', 'Mile', 'Rade MILE, ', ''),
    '0013001246': ('Radinović', 'Stanka', 'Stanko', 'Đuro', 'Stanka ĐURO, ', ''),
    '0013001622': ('Zaviša', 'Steve', 'Stevo', 'Dušan', 'Steve DUŠAN, ', ''),
    '0014000985': ('Vlaisavljević', 'J', 'J', 'Milenko', '(J) MILENKO, ', ''),
    '0014000986': ('Vlaisavljević', 'J', 'J', 'Uroš', '(J) UROŠ, ', ''),
    '0014001018': ('Zaviša', 'J', 'J', 'Mile', '(J) MILE, ', ''),
    '0014010748': ('Rajak', '', '', 'Milan', '', ''),
    '0014010811': ('Savić', 'S', 'S', 'Slavko', '(S) SLAVKO, ', ''),
    '0016000845': ('Gunjević', '', '', 'Joco', 'Č JOCO, ', ''),
    '0016001013': ('Janković', 'V', 'V', 'Živojin', 'V. ŽIVOJIN, ', ''),
    '0016001311': ('Kovačić', 'T', 'T', 'Mile', 'T. MILE, ', ''),
    '0016002122': ('Nožičković', 'M', 'M', 'Stevo', 'M. STEVO, ', ''),
    '0016002172': ('Pavić', 'G', 'G', 'Božo', 'G. BOZO, ', ''),
    '0016002481': ('Pupavac', 'I', 'I', 'Sretko', 'I. SRETKO, ', ''),
    '0016002482': ('Pupavac', 'B', 'B', 'Lazo', 'B. LAZO, ', ''),
    '0016002516': ('Radinović', 'R', 'R', 'Ilija', 'R. ILIJA, ', ''),
    '0016002526': ('Radić-Pajalić', 'D', 'D', 'Alenka', 'D. ALENKA, ', ''),
    '0016002679': ('Savić', 'Z', 'Z', 'Vitomir', 'Z. VITOMIR, ', ''),
    '0016002867': ('Stojanović', 'M', 'M', 'Milutin', 'M. MILUTIN, ', ''),
    '0016002969': ('Tarlanović', 'Lj', 'Lj', 'Nenad', 'Lj. NENAD, ', ''),
    '0016003271': ('Vujasinović', 'M', 'M', 'Božo', 'M. BOZO, ', ''),
    '0016003272': ('Vujasinović', 'S', 'S', 'Dušan', 'S. DUŠAN, ', ''),
    '0017001131': ('Stjepanović', 'Nikole', 'Nikola', 'Boro', '', ''),
    '0021003128': ('Mićković', 'M', 'M', '', 'Svračkovcnj Gornji Mnjtanovac', 'Svračkovci, Gornji Milanovac'),
    '0021003545': ('Orel', '', '', 'Jovan', '', ''),
    '0021003733': ('Pejći', 'N', 'N', 'Franjo', 'N. FRANJO, ', '(ili Bajći) '),
    '0022000394': ('Brestovački-Janković', 'P', 'P', 'Julka', 'P. JULKA, ', ''),
    '0022001397': ('Kostić-Sokolović', 'L', 'L', 'Olga', 'L. OLGA, ', ''),
    '0023000272': ('Dragić', 'Petra', 'Petar', 'Korke', 'Dr. KORKE, ', 'dr, '),
    '0023000656': ('Kalajdžić', 'Mile', 'Mile', 'Sretko', 'E SRETKO, ', ''),
    '0023001060': ('Milutinović', 'Mirka', 'Mirko', 'Slobodan', 'Dr. SLOBODAN, ', 'dr, '),
    '0024000122': ('Borisavljević', 'Borisava', 'Borisav', 'Mihailo', 'Borisava MIHAILO, ', ''),
    '0024000802': ('Milenković', 'Miluna', 'Milun', 'Kostadin', 'Miluna KOSTADIN, ', ''),
    '0027000742': ('Simić-Sopić', 'Dragoljuba', 'Dragoljub', 'Života', 'Dragoljuba ŽIVOTA, ', ''),
    '0029000724': ('Stevanović', 'Aleksa', 'Aleksa', 'Časlav', 'zvani Vič Caslav; ', ''),
    '0029000731': ('Stevanović', 'Jovan', 'Jovan', 'Čedomir', 'zvani Vi C Cedomir; ', ''),
    '0035101483': ('Cvitko', '', '', 'Ivan', '', ''),
    '0035104525': ('Jus', 'Adalberta', 'Adalbert', 'Alba', 'Adalberta, ', ''),
    '0035104532': ('Kavedo Etuka', '', '', 'Valter', '', ''),
    '0035105879': ('Krvar', 'Ivana', 'Ivan', 'Vid', '', ''),
    '0035106326': ('Levak', 'Franje', 'Franjo', 'Ivan', '', ''),
    '0035106327': ('Levak', 'Franje', 'Franjo', 'Mato', '', ''),
    '0035108143': ('Pavaš', '', '', 'Kadija', '', ''),
    '0035109910': ('Savaga', '', '', 'Martin', '', ''),
    '0035111309': ('Van Broekhoven', 'Petres', 'Petres', 'Marinus', 'Petres, ', ''),
    '0035111758': ('Vrban', '', '', 'Zlatko', '', ''),
    '0035112945': ('Šlivonja', '', '', 'Ištvan', '', ''),
    '0035112968': ('Šoba', 'Franje', 'Franjo', 'Zvonko', '', ''),
    '0036011332': ('Mijakovac', '', '', 'Petar', 'zvani Ac, Petar; ', ''),
    '0040010262': ('Dimitrijević', 'M', 'M', 'Aleksandar', 'M. ALEKSANDAR, ', ''),
    '0043000056': ('Babić', 'Marka', 'Marko', 'Alija', "zvani 2.; bataljona, rođen 192l Trwicf- ^f03' podoficir Jugoslovenskc»Jske, Srbin, u NOB od 1941 član »J cd januara", 'borac 2. bataljona, rođen 1921, podoficir jugoslovenske vojske, Srbin, u NOB od 1941, član KPJ od januara'),
    '0050000197': ('Vitasović', '', '', 'Mate', '', ''),
    '0052001463': ('Topalović', 'Ivana', 'Ivan', 'Marica', 'vana MARICA, ', ''),
    '0053001225': ('Kajević', 'Đure', 'Đuro', 'Branko', 'zvani Dl; zvani Đure; BRANKO, ', ''),
    '0053001558': ('Leban', '', '', 'Ivan', '', ''),
    '0053001727': ('Marinović-Jelavić', 'Nikole', 'Nikola', 'Ana', 'Nikole ANA, ', ''),
    '0053002735': ('Stojanović', 'Mile', 'Mile', 'Đuro', 'zvani Mile; ĐURO, ', ''),
    '0053003123': ('Zenzerović', 'K', 'K', 'Jakov', 'K. JAKOV, ', ''),
    '0055000535': ('Paunović', '', '', 'Miodrag', '', ''),
    '0056000348': ('Danilović', 'M', 'M', 'Savo', 'M. SAVO, ', ''),
    '0056000388': ('Dervić', 'D', 'D', 'Salko', 'D. SALKO, ', ''),
    '0056000731': ('Imamović', 'S', 'S', 'Sakib', 'S. SAKIB ', ''),
    '0056000848': ('Kalabić', '', '', 'Bogdan', '', ''),
    '0056001293': ('Milanović', 'Đ', 'Đ', 'Ljuban', 'Đ. LJUBAN, ', ''),
    '0056001415': ('Musinović', 'M', 'M', 'Naim', 'M. NAIM, 1925, Konj uho vci', '1925, Konjuhovci'),
    '0056001419': ('Mustabašić', 'H', 'H', 'Halil', 'H. HALIL. ', ''),
    '0056001518': ('Pavić', 'D', 'D', 'Marko', 'D. MARKO, ', ''),
    '0056002001': ('Stanković', 'P', 'P', 'Bogdan', 'P. BOGDAN, ', ''),
    '0056002068': ('Suman', '', '', 'Svetko', '', ''),
    '0056002242': ('Vajukić', 'S', 'S', 'Ljubo', 'C S. LJUBO, ', ''),
    '0056002246': ('Vanjek', '', '', 'Janko', '', ''),
    '0057002527': ('Petrović', '', '', 'Nada', 'iz Sremeke Mitrovice.', 'iz Sremske Mitrovice.'),
    '0069000957': ('Lampret', '', '', 'Ciril', '', ''),
    '0069001494': ('Pribožič', '', '', 'Franc', '', ''),
    '0069001906': ('Volčenko', 'Sergejević', '', 'Boris', 'zvani Jević; ', ''),
    '0074000446': ('Lončar', '', '', 'Kata', '', ''),
    '0079000215': ('Di Luigi', '', '', 'Pietro', 'zvani Pietro; ', ''),
    '0079000222': ('Dobrijević', 'Nikole', 'Nikola', 'Jovo', 'Nikole JOVO, ', ''),
    '0079000560': ('Lavanja', '', '', 'Krsto', 'zvani Krsto; ', ''),
    '0079000797': ('Nikolajević', '', '', 'Ivan', 'zvani Ivan; ', ''),
    '0079000826': ('Osmankadić', 'Hasana', 'Hasan', 'Kemal', 'Hasana KEMAL, ', ''),
    '0079000970': ('Riplač', 'Pave', 'Pave', 'August', 'Pave AUGUST, ', ''),
    '0094010286': ('Podvorac', '', '', 'Ivan', '', ''),
    '0096000346': ('Lefik', 'Dimitrijević', '', 'Aleksej', 'Kislovac, |', 'Kislovac, SSSR'),
    '0110000260': ('Damjanović-Urošević', 'Milana', 'Milan', 'Nadežda', 'Milana NADEŽDA, ', ''),
    '0110001871': ('Ružičić-Ružić', 'Milivoja', 'Milivoje', 'Predrag', 'Milivoja PREDRAG, ', ''),
    '0120000434': ('Zjaca', '', '', 'Dušan', 'zvani Dušan; ', ''),
    '0125000385': ('Krvavac', 'M', 'M', 'Hamdija', 'zvani Ac; ', ''),
    '0125000450': ('Milavić', 'S', 'S', 'Salko', 'zvani Vic; ', ''),
    '0125000798': ('Šarenac', 'P', 'P', 'Lazar', 'zvani Ac Pop; ', 'zvani Pop; '),
    '0125000799': ('Šarenac', '', '', 'Rade', 'zvani Ac; ', ''),
    '0125000800': ('Šarenac', '', '', 'Špiro', 'zvani Ac; ', ''),
    '0126001264': ('Ajd', '', '', 'Alojz', '', ''),
    '0127000750': ('Stojanović-Stojković', '', '', 'Đuro', 'zvani Rypo; ', ''),
    '0128002384': ('Milosavljević', '', '', 'Vićentije', 'zvani Vinentije; ', ''),
    '0139000334': ('Rautar', '', '', 'S.', 'zvani R S; ', ''),
    '0140000955': ('Tavčar', 'B', 'B', 'Vojnimir', 'B. VOJNIMIR, ', ''),
    '0147000881': ('Pudjak', '', '', 'Alojz', 'Alojz; ', ''),
    '0166000114': ('Završnik', '', '', 'Miroslav', '', ''),
    '0167000517': ('Ilc', '', '', 'Kostja', '', ''),
    # the 9. srpska
    '0165000050': ('Cakić-Žikić', '', '', 'Jelena', 'zvani Jelena', None),
    '0165000061': ('Dimitrijević', '', '', 'Jovan', 'zvani IĆ Jovan Jovica', 'zvani Jovica'),
    '0165000096': ('Hadži-Nikolajević', '', '', 'Đorđe', 'zvani AJEV IĆ Đorđe Mile', 'zvani Mile'),
    '0165000102': ('Ivanković', 'Radomir', 'Radomir', 'Vera', 'zvana (Radomir) Vera Kića', 'zvana Kića'),
    '0165000103': ('Ivanović', '', '', 'Dragomir', 'zvani Dragomir', None),
    '0165000150': ('Kovačević', '', '', 'Dušan', 'zvani Dušan Kole', 'zvani Kole'),
    '0165000151': ('Kovačić', '', '', 'Žarko', 'zvani Žarko JBubuška; 20. 6.44. - 7. 44; politički komesar (Štab trećeg bataljona); zvani Žarko Ljubuška; ', 'zvani Ljubuška; 20. 6.44. - 7. 44; politički komesar (Štab trećeg bataljona); '),
    '0165000172': ('Manijašević', '', '', 'Đorđe', 'zvani Đorđe', None),
    '0165000212': ('Miljković-Stojić', '', '', 'Nadežda', 'zvani Nadežda Nada', 'zvana Nada'),
    '0165000253': ('Novaković', '', '', 'Branko', 'zvani Branko Sava', 'zvani Sava'),
    '0165000290': ('Radenković-Vujičić', '', '', 'Ljubinka', 'zvani Ljubinka', None),
    '0165000320': ('Simonović-Majstorović', '', '', 'Jelena', 'zvani Jelena', None),
    '0165000323': ('Stamenković-Bajić', '', '', 'Vera', 'zvani IĆ BAJIĆ Vera', None),
    '0165000324': ('Stanimirović', '', '', 'Stanimir', 'zvani IĆ Stanimir Mišks', 'zvani Miška'),
    '0165000342': ('Stefanović', '', '', 'Vrban', 'zvani Vrban', None),
    '0165000461': ('Živanović', '', '', 'Živko', 'zvani Živko Deva', 'zvani Deva'),
    # the record of the name, whose other men get records of their own (NINTH_ADD)
    '0165000120': ('Jovanović', '', '', 'Radomir', 'zvana Radomir Čoče; 11.3.44.- 8.6.44; bolničarka ili borac u stroju žena brigade; zvana Bogunović (Stevan) Biserka Kaća; zvana Ilić (Miladin) Dragica; zvana Milica', 'zvani Čoče; 11.3.44.- 8.6.44'),
    '0165000220': ('Milovanović', '', '', 'Dragoljub', 'zvani Dragoljub; komandir (Komanda četvrte čete četvrtog bataljona); zvani Stanislav Mile Crni', None),
    '0165000346': ('Stevanović', '', '', 'Dragoljub', 'zvani Dragoljub Milinko I.3.44.-1.10.; 44.; politički komesar (Komanda četvrte čete prvog bataljona); zvani Nikola Kole; komandir (Komanda druge čete četvrtog bataljona); zvani Jovan Jole', 'zvani Milinko; I.3.44.-1.10.44.'),
    '0165000347': ('Stojanović', '', '', 'Dušan', 'zvani Dušan Duša; politički komesar (Komanda četvrte čete četvrtog bataljona); zvani Branko', 'zvani Duša'),
    # the same man's other record, which the merges below take
    '0165000052': ('Cojić', '', '', 'Miodrag', 'zvani Miodrag Nedeljko', 'zvani Nedeljko'),
    '0165000083': ('Gocić', '', '', 'Vukadinka', 'zvani Vukadinka', None),
    '0165000090': ('Golubović', '', '', 'Branka', 'zvani Branka', None),
    '0165000144': ('Komadina', '', '', 'Darinka', 'zvani Darinka Dac; sanitetski referent; zvani Darinka Daca', 'zvana Daca; sanitetski referent'),
    '0165000176': ('Marjanović', '', '', 'Branislav', 'zvani Branislav', None),
    '0165000269': ('Perić', '', '', 'Kosara', 'zvani Kosara Desa Planinka', 'zvana Desa Planinka'),
    '0165000280': ('Piotrovski', '', '', 'Jozef', 'zvani Jozef Johan', 'zvani Johan'),
    '0165000356': ('Stojanović', '', '', 'Olga', 'zvani Olga Nada', 'zvana Nada'),
    '0165000424': ('Hajduković', '', '', 'Stojan', '', ''),
    '0165000076': ('Gligorijević', '', '', 'Ivan', '', ''),
    '0165000403': ('Videnović', '', '', 'Evstatije', 'zvani Smiljani', 'zvani Smiljanić'),
    '0165000422': ('Vučelić', '', '', 'Kosta', 'zvana Kole', 'zvani Kole'),
    '0165000463': ('Živković', '', '', 'Miodrag', '', ''),
}

# the 9. srpska's texts that only a stray "zvani" spoils, or that get another post of the man
NINTH_TEXTS = {
    '0165000125': ('zvana |', 'bolničarka ili borac u stroju žena brigade'),
    '0165000449': ('; zvana |', ''),
    '0165000455': ('zvani .; ', ''),
    '0165000177': ('; zvani -11. 4. A', ''),
    '0165000201': ('zvani Momčilo 11.3. 44.-24. 7.44,', 'zvani Momčilo; 11.3. 44.-24. 7.44'),
    '0165000410': ('zvani 1.-28. 3. 4,', '1.-28. 3. 44'),
    '0165000350': ('politički komesar (Komanda druge čete prvog bataljona)', 'politički komesar (Komanda druge čete prvog bataljona); politički komesar (Komanda četvrte čete četvrtog bataljona)'),
}

# (after, new_id, surname, father, given, text, page, y, x, x_end)
NINTH_ADD = [
    ('0165000120', '0165009001', 'Jovanović', 'Stevan', 'Biserka', 'bolničarka ili borac u stroju žena brigade; udata Bogunović; zvana Kaća', 24, 538.9, 64.4, 295.5),
    ('0165000120', '0165009002', 'Jovanović', 'Miladin', 'Dragica', 'bolničarka ili borac u stroju žena brigade; udata Ilić', 24, 549.5, 64.5, 254.0),
    ('0165000220', '0165009003', 'Milovanović', '', 'Stanislav', 'komandir (Komanda četvrte čete četvrtog bataljona); zvani Mile Crni', 20, 56.0, 179.4, 356.2),
    ('0165000346', '0165009004', 'Stevanović', '', 'Nikola', 'politički komesar (Komanda četvrte čete prvog bataljona); zvani Kole', 12, 154.3, 214.6, 342.5),
    ('0165000346', '0165009005', 'Stevanović', '', 'Jovan', 'komandir (Komanda druge čete četvrtog bataljona); zvani Jole', 20, 253.9, 180.4, 295.7),
]

# (keeper, merged away)
NINTH_MERGES = [
    ('0165000053', '0165000052'), ('0165000084', '0165000083'), ('0165000089', '0165000090'), ('0165000143', '0165000144'), ('0165000177', '0165000176'),
    ('0165000270', '0165000269'), ('0165000279', '0165000280'), ('0165000354', '0165000356'), ('0165000097', '0165000424'), ('0165000079', '0165000076'),
    ('0165000404', '0165000403'), ('0165000423', '0165000422'), ('0165000464', '0165000463'),
]

# a line of the entry before read as a man: (the line's record, the host, what goes at the host's end, the host's new given name)
STRAYS = [
    ('0015000055', '0015000103', 'GŠ NOV i PO Srbije. ', ''),
    ('0015000056', '0015000257', 'GŠ NOV i PO Srbije. ', ''),
    ('0001009697', '0001009696', 'NOV Jugoslavije', ''),
    ('0035111248', '0035113315', 'NOV 1944, ', ''),
    ('0001301560', '0001301052', '', 'Aleksa'),
]
# no man at all: a heading of a memoir read as a name
NOT_MEN = {'0036100442': 'A heading over a diary set in the list ("Iz skojevskog dnevnika"), no man'}

# what the list of by_books showed to be surnames of their own, or two men's, whatever the other book prints
NOT_THESE = set('''Hujdurović Salomon Petkovska Nemeth Jurević Hekimović Stanec Agbabić Prković Plutić Vrkelić Ojanić Joinić Šišaković Bandak Miter Aksenić Legić Školić Ajlić Radenko Uvić Vepić'''.split())
# the other book's spelling lost a caron or a stroke
SPELLED = {'Jaksić': 'Jakšić', 'Kovacević': 'Kovačević', 'Ivancević': 'Ivančević', 'Dumič': 'Dumić', 'Pavlovič': 'Pavlović', 'Mrda': 'Mrđa'}

NOT_VILLAGE = re.compile(r'^(srbij|hrvats|bosn|bih|crna g|crnag|vojvod|sloven|makedon|italij|dalmac|lika|nemač|mađars|rusij|sssr|none|$)', re.I)
TOWNS = re.compile(r'^(beograd|zagreb|split|sarajevo|novi sad|šibenik|ljubljana|rijeka|mostar|tuzla|banja ?luka|niš|subotica|maribor|zadar|osijek|karlovac|skoplje|podgorica|titograd)\b', re.I)


def fold(s):
    s = (s or '').replace('đ', 'dj').replace('Đ', 'dj')
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn' and c.isalpha())


def village(s):
    return fold((s.get('birth_place') or '').split(',')[0])[:6]


def by_books(units, leave):
    """Surnames read from the same man in another book."""
    bearers = collections.Counter()
    fbearers = collections.Counter()
    by = collections.defaultdict(list)
    for data in units.values():
        for s in data:
            bearers[fold(s.get('last_name'))] += 1
            fbearers[s.get('last_name')] += 1
            by[fold(s.get('first_name')), fold(s.get('fathers_name') or s.get('middle_name'))[:3], village(s)].append(s)
    out = {}
    for code, data in units.items():
        if code == 122 or 131 <= code <= 138:
            continue
        for s in data:
            old = s.get('last_name') or ''
            l = fold(old)
            if not l or s['soldier_id'] in leave or old in NOT_THESE or bearers[l] > 3 or not s.get('first_name') or '-' in old or ' ' in old:
                continue
            fk = fold(s.get('fathers_name') or s.get('middle_name'))[:3]
            vs = village(s)
            if not fk or not vs or NOT_VILLAGE.match(s.get('birth_place') or ''):
                continue
            y = s.get('birth_year') or ''
            cands = collections.defaultdict(list)
            for o in by[fold(s.get('first_name')), fk, vs]:
                new = o.get('last_name') or ''
                lo = fold(new)
                if o is s or lo == l or '-' in new or ' ' in new:
                    continue
                if fbearers[new] < max(5, 5 * fbearers[old]):
                    continue
                tail = len(l) >= 2 and lo.endswith(l) and len(lo) > len(l)
                r = difflib.SequenceMatcher(None, l, lo).ratio()
                if not tail and (abs(len(l) - len(lo)) > 1 or r < 0.72):
                    continue
                oy = o.get('birth_year') or ''
                gap = abs(int(y) - int(oy)) if y.isdigit() and oy.isdigit() else None
                town = TOWNS.match(s.get('birth_place') or '')
                sure = (gap is not None and gap <= 1 and (tail or r >= 0.8)) \
                    or (gap == 0 and not town and r >= 0.72 and fbearers[old] <= 2 and fbearers[new] >= 12) \
                    or (not town and r >= 0.85 and fbearers[old] <= 3 and (gap is None or gap <= 3))
                if sure:
                    cands[new].append(o)
            if not cands:
                continue
            ranked = sorted(cands, key=lambda n: -fbearers[n])
            if len(ranked) > 1 and fbearers[ranked[0]] < 5 * fbearers[ranked[1]]:
                continue
            out[s['soldier_id']] = (old, SPELLED.get(ranked[0], ranked[0]), cands[ranked[0]][0]['soldier_id'])
    return out


NOT_GIVEN = set('Dujan Vučilo Budimko Mehmedali Dušico Bogda Predan Lovica Zivodar Božidara Mihaile'.split())
NOT_FATHER = set('Radoljub Nikša Dragoš Vesko Gigo Srećo Tešimira Damin Malića Bonin Dujka Duke Suje Neše Kiće Cveje Grozdana'.split())


def given_by_books(units, leave):
    """A given name or a father the scan misread, from the same man in another book: the rest of the name, the village and the year (within one) agree, the odd form is borne by next to no one."""
    first, father = collections.Counter(), collections.Counter()
    by_f, by_m = collections.defaultdict(list), collections.defaultdict(list)
    for d in units.values():
        for s in d:
            first[s.get('first_name')] += 1
            father[s.get('fathers_name') or s.get('middle_name')] += 1
            by_f[fold(s.get('last_name')), fold(s.get('fathers_name') or s.get('middle_name'))[:3], village(s)].append(s)
            by_m[fold(s.get('last_name')), fold(s.get('first_name')), village(s)].append(s)

    def close(a, b):
        return abs(len(a) - len(b)) <= 1 and difflib.SequenceMatcher(None, fold(a), fold(b)).ratio() >= 0.66

    def within_year(s, o):
        y, oy = s.get('birth_year') or '', o.get('birth_year') or ''
        return y.isdigit() and oy.isdigit() and abs(int(y) - int(oy)) <= 1

    out = {}
    for code, d in units.items():
        if code == 122 or 131 <= code <= 138:
            continue
        for s in d:
            sid = s['soldier_id']
            vs = village(s)
            if sid in leave or not vs or NOT_VILLAGE.match(s.get('birth_place') or ''):
                continue
            f, m = s.get('first_name') or '', s.get('fathers_name') or ''
            fk = fold(m or s.get('middle_name'))[:3]
            fields = {}
            if f and first[f] <= 3 and fk and ' ' not in f and f not in NOT_GIVEN:
                c = {o.get('first_name') for o in by_f[fold(s.get('last_name')), fk, vs]
                     if o is not s and fold(o.get('first_name')) != fold(f) and first[o.get('first_name')] >= max(8, 8 * first[f]) and ' ' not in (o.get('first_name') or '') and within_year(s, o) and close(f, o.get('first_name') or '')}
                if len(c) == 1:
                    fields['first_name'] = c.pop()
            if m and father[m] <= 3 and len(m) > 2 and ' ' not in m and m not in NOT_FATHER:
                c = {o.get('fathers_name') for o in by_m[fold(s.get('last_name')), fold(f), vs]
                     if o is not s and o.get('fathers_name') and fold(o['fathers_name']) != fold(m) and father[o['fathers_name']] >= max(8, 8 * father[m]) and ' ' not in o['fathers_name'] and len(o['fathers_name']) >= 3 and within_year(s, o) and close(m, o['fathers_name'])}
                if len(c) == 1:
                    fields['fathers_name'] = c.pop()
            if fields:
                out[sid] = fields
    return out


def main():
    units = {}
    for code, cfg in sorted(BRIGADE_CONFIGS.items()):
        p = ROOT / 'website/public' / cfg['json_file']
        if p.exists():
            units[code] = json.loads(p.read_text(encoding='utf-8'))
    byid = {s['soldier_id']: s for d in units.values() for s in d}
    corr = json.loads((ROOT / 'corrections.json').read_text(encoding='utf-8'))
    since = int(sys.argv[sys.argv.index('--since') + 1]) if '--since' in sys.argv else None
    pending = {}
    if since:
        for c in corr:
            if c['id'] >= since and c['action'] == 'edit' and 'additional_info' in (c.get('fields') or {}):
                pending[c['soldier_id']] = c['fields']['additional_info']

    def text_of(sid):
        return pending.get(sid, byid[sid].get('additional_info') or '')

    edits, bad = [], []
    for sid, (last, printed, father, given, cut, put) in HEADS.items():
        s = byid.get(sid)
        if not s:
            bad.append((sid, 'no record'))
            continue
        f = {'last_name': last, 'first_name': given, 'middle_name': printed, 'fathers_name': father}
        t = text_of(sid)
        if cut:
            if cut not in t:
                bad.append((sid, repr(cut), repr(t[:90])))
                continue
            new = t.replace(cut, put or '', 1)
            new = re.sub(r';\s*;', ';', new)
            new = re.sub(r'[;,\s]+$', '', new) if put is None else new
            f['additional_info'] = new
        elif put:
            f['additional_info'] = put + t
        edits.append((sid, f, 'A name cut in two or glued, read from the page: ' + ' '.join(x for x in (last, printed, given) if x)))
    for sid, (cut, put) in NINTH_TEXTS.items():
        t = text_of(sid)
        if cut not in t:
            bad.append((sid, repr(cut), repr(t[:90])))
            continue
        edits.append((sid, {'additional_info': t.replace(cut, put, 1)}, 'The 9. srpska: the text as the page prints it'))
    deletes = []
    for sid, host, lead, given in STRAYS:
        s, h = byid.get(sid), byid.get(host)
        if not s or not h:
            bad.append((sid, host, 'no record'))
            continue
        f = {}
        tail = (lead + (s.get('additional_info') or '')).strip()
        if tail:
            f['additional_info'] = (text_of(host).rstrip() + ' ' + tail).strip()
        if given:
            f['first_name'] = given
        edits.append((host, f, 'Its last line had been read as a record of its own'))
        deletes.append((sid, 'A line of ' + (h.get('full_name') or host) + "'s entry, read as a man"))
    for sid, why in NOT_MEN.items():
        if sid in byid:
            deletes.append((sid, why))
    leave = set(HEADS) | {s for s, _, _, _ in STRAYS}
    books = by_books(units, leave)
    for sid, (old, new, via) in sorted(books.items()):
        edits.append((sid, {'last_name': new}, f'Surname the scan cut or misread ("{old}"), from the same man in another book ({via}): the same father, given name, village and year'))
    given = given_by_books(units, leave)
    for sid, fields in sorted(given.items()):
        s = byid[sid]
        edits.append((sid, fields, 'Name the scan misread (' + ', '.join(f'"{s.get(k)}"' for k in fields) + '), from the same man in another book: the rest of the name, the village and the year'))
    print('heads', len(HEADS), 'by books', len(books), 'given', len(given), 'edits', len(edits), 'deletes', len(deletes), 'adds', len(NINTH_ADD), 'merges', len(NINTH_MERGES))
    for b in bad:
        print('BAD', b)
    if '--list' in sys.argv:
        for sid, (old, new, via) in sorted(books.items()):
            s = byid[sid]
            print(sid, old, '->', new, '|', s.get('middle_name'), '|', s.get('first_name'), '|', s.get('birth_place'), s.get('birth_year'), '|', via, byid[via].get('birth_year'))
    if '--write' in sys.argv:
        assert not bad
        start = int(sys.argv[sys.argv.index('--write') + 1])
        assert not [c for c in corr if c['id'] >= start]
        # a name changed here changes in the guards that hold it
        new_full = {}
        for sid, f, _ in edits:
            if any(k in f for k in ('last_name', 'first_name', 'middle_name')):
                s = byid[sid]
                new_full[sid] = (s.get('full_name'), ' '.join(x for x in (f.get('last_name', s.get('last_name')), f.get('middle_name', s.get('middle_name')), f.get('first_name', s.get('first_name'))) if x))
        n = 0
        for c in corr:
            for idk, namek in (('link_id', 'link_name'), ('merge_id', 'merge_name')):
                if c.get(idk) in new_full and c.get(namek) == new_full[c[idk]][0]:
                    c[namek] = new_full[c[idk]][1]
                    n += 1
        add, i = [], start
        for sid, f, why in edits:
            add.append({'id': i, 'action': 'edit', 'soldier_id': sid, 'fields': f, 'reason': why})
            i += 1
        for after, new_id, last, father, given, t, page, y, x, x_end in NINTH_ADD:
            add.append({'id': i, 'action': 'add', 'soldier_id': after, 'new_id': new_id, 'record': {
                'last_name': last, 'middle_name': father, 'fathers_name': father, 'first_name': given, 'additional_info': t, 'birth_year': '',
                'pdf_file': byid[after]['pdf_file'], 'pdf_page': page, 'pdf_y': y, 'pdf_x': x, 'pdf_x_end': x_end, 'pdf_y_end': y + 10.0},
                'reason': 'A man of the 9. srpska whose spaced surname its parser joined to another of the name'})
            i += 1
        for keep, away in NINTH_MERGES:
            h = HEADS.get(away)
            s = byid[away]
            name = ' '.join(x for x in ((h[0], h[1], h[3]) if h else (s.get('last_name'), s.get('middle_name'), s.get('first_name'))) if x)
            add.append({'id': i, 'action': 'merge', 'soldier_id': keep, 'merge_id': away, 'merge_name': name, 'reason': "One man in two of the 9. srpska's lists: the same post or nickname, a spelling or a married name apart"})
            i += 1
        for sid, why in deletes:
            add.append({'id': i, 'action': 'delete', 'soldier_id': sid, 'reason': why})
            i += 1
        (ROOT / 'corrections.json').write_text(json.dumps(corr + add, ensure_ascii=False, indent=2), encoding='utf-8')
        dec_path = ROOT / 'identity_decisions.json'
        dec = json.loads(dec_path.read_text(encoding='utf-8'))
        m = 0
        for d in dec:
            for idk, namek in (('a', 'a_name'), ('b', 'b_name')):
                if d.get(idk) in new_full and d.get(namek) == new_full[d[idk]][0]:
                    d[namek] = new_full[d[idk]][1]
                    m += 1
        dec_path.write_text(json.dumps(dec, ensure_ascii=False, indent=1), encoding='utf-8')
        print('written', len(add), start, i - 1, 'guards', n, m)


if __name__ == '__main__':
    main()
