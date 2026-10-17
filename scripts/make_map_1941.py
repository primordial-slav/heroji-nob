"""The map of Yugoslavia in April 1941 for the map page (/mapa), drawn the way the war books draw their sketches
(Kleut, Partizanska taktika, 1983, sl. 5 and 24): an ink outline, the rivers widening downstream, a few towns
and the lettering of a drafting pen.

Sources, fetched once into data-extraction/.cache/map1941/:
- the Kingdom of Yugoslavia, 3 Oct 1929 - 6 Apr 1941: OpenHistoricalMap relation 2747831 (CC0). Its border runs
  out at sea, so the land inside it is cut from Natural Earth's 10 m land (public domain): Istria, Rijeka, Zadar,
  Cres and Lošinj and Lastovo fall to Italy, Krk, Rab and Pag stay in
- rivers: OpenStreetMap waterway relations (ODbL, (c) OpenStreetMap contributors), one /full request each
- lakes: Natural Earth 10 m

Writes website/app/(sr)/mapa/map1941.ts, every path already projected (Lambert conformal conic, PROJ) into the
units of the SVG's viewBox; mapa/projection.ts projects a place the same way, for what the page puts on the map.

The hand: each line is generalised (simplified, its corners rounded off with Chaikin's cuts), then wobbled a
little along its normals by a smooth noise, as a pen held freehand would. Rivers are ink ribbons that widen
downstream.

Usage: python scripts/make_map_1941.py
"""
import json
import math
import random
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.ttLib import TTFont
from shapely import line_merge
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon, box, shape
from shapely.ops import polygonize, unary_union
from shapely.prepared import prep

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'data-extraction' / '.cache' / 'map1941'
PAGE = ROOT / 'website' / 'app' / '(sr)' / 'mapa'
OUT = PAGE / 'map1941.ts'
FONT = PAGE / 'fonts' / 'osifont-italic.woff2'

OHM_KINGDOM = 2747831
NE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson'
OSM_FULL = 'https://api.openstreetmap.org/api/0.6/relation/{}/full'
AREA = box(12.8, 40.3, 23.8, 47.4)                 # lon/lat: everything read is cut to this first

# Lambert conformal conic on a sphere, standard parallels through the north and the south of the country
PROJ = {'lon0': 18.4, 'lat0': 44.0, 'lat1': 42.0, 'lat2': 46.0, 'radius': 6371.0}
WIDTH = 1000.0                                      # the viewBox's width; the height follows from the margins
MARGIN = {'left': 70.0, 'right': 95.0, 'top': 70.0, 'bottom': 55.0}

# The rivers sl. 5 draws: the big ones and their main tributaries, none of the small streams.
# name, OSM relation ids (source first; 'ne:<name>' takes Natural Earth's line instead), width at the source and at
# the mouth, where its name would stand (lon, lat)
RIVERS = [
    ('Dunav', [89652], 2.0, 2.4, (21.25, 44.74)),
    ('Sava', [5810094, 1564720], 0.7, 2.2, (17.35, 45.13)),
    ('Drava', [157031], 1.3, 2.0, (17.55, 45.93)),
    ('Tisa', [88555], 1.7, 2.0, (20.12, 45.72)),
    ('Mura', [59792], 1.0, 1.4, (16.35, 46.5)),
    ('Drina', [2249121], 0.6, 1.5, (19.33, 44.25)),
    ('V. Morava', [2553374], 1.3, 1.6, (21.12, 44.3)),
    ('Z. Morava', [2520222], 0.5, 1.3, (20.55, 43.72)),
    ('J. Morava', [2553373], 0.5, 1.3, (21.85, 42.88)),
    ('Una', [2535792], 0.5, 1.2, (16.25, 44.95)),
    ('Vrbas', [6096804], 0.5, 1.1, (17.28, 44.4)),
    ('Bosna', [6096801], 0.5, 1.2, (18.12, 44.55)),
    ('Kupa', [2535729], 0.5, 1.2, (15.35, 45.55)),
    ('Neretva', [2090864], 0.5, 1.2, (17.62, 43.52)),
    ('Vardar', [5896030], 0.6, 1.5, (21.95, 41.62)),
    ('Ibar', [6148185], 0.5, 1.1, (20.62, 43.42)),
    ('Lim', [11527729], 0.5, 1.0, (19.62, 43.2)),
    ('Tamiš', [1567519], 1.0, 1.3, (20.62, 45.22)),
    ('Timok', [11721232, 7169081], 0.5, 1.1, (22.42, 43.92)),
    ('Morača', [11525414], 0.5, 1.0, (19.25, 42.62)),
    ('Nišava', [2956742], 0.5, 1.0, None),
    ('Crni Drim', [7395679], 0.5, 1.0, None),
    ('Beli Drim', [6162905], 0.5, 1.0, None),
    ('Sana', [13760451], 0.4, 0.8, None),
    ('Korana', [3485934], 0.4, 0.8, None),
    ('Cetina', [7296532], 0.4, 0.8, None),
    ('Tara', [11526845], 0.4, 0.8, None),
    ('Begej', [4450591], 0.6, 0.9, None),
    ('Treska', [5900733], 0.4, 0.8, None),
    ('Crna', [5900731], 0.4, 0.9, None),
    ('Bregalnica', ['ne:Bregalnica'], 0.4, 0.8, None),  # no OSM relation; Natural Earth's line
]
LETTER_RIVERS = False                               # sl. 5 names no river; True letters those given a place
# Smaller rivers, drawn only when the map closes in on a unit's area, as the books' detail sheets draw them
DETAIL_RIVERS = [
    ('Sutjeska', [17616332]), ('Piva', [7301977]), ('Zeta', [11526874]), ('Kolubara', [10799700]),
    ('Savinja', [2271983]), ('Krka', [3486107]), ('Krka', [2196282]), ('Sitnica', [6148073]), ('Toplica', [16713673]),
    ('Bosut', [2536046]), ('Spreča', [7846330]), ('Mlava', [11651226]), ('Zrmanja', [3573301]), ('Glina', [7297638]),
    ('Lonja', [3534904]), ('Ljubljanica', [2196672]), ('Raška', [16124647]), ('Lepenac', [5900732]),
    ('Sutla', [7297669]), ('Lašva', [6096802]), ('Rama', [17631187]), ('Unac', [7337752]),
]
MAJOR_RIVERS = {'Dunav', 'Sava', 'Drava', 'Tisa'}

# The towns sl. 5 marks, under their names of 1941 (Podgorica, not Titograd). name, lon, lat, rank (0 the capital,
# 1 the others), where the name stands
TOWNS = [
    ('Beograd', 20.4633, 44.8176, 0, 'n'),
    ('Zagreb', 15.9819, 45.8150, 1, 'e'),
    ('Ljubljana', 14.5058, 46.0569, 1, 'se'),
    ('Novi Sad', 19.8335, 45.2671, 1, 'n'),
    ('Sarajevo', 18.4131, 43.8563, 1, 'n'),
    ('Split', 16.4402, 43.5081, 1, 'ne'),
    ('Podgorica', 19.2594, 42.4304, 1, 'n'),
    ('Priština', 21.1655, 42.6629, 1, 's'),
    ('Skoplje', 21.4254, 41.9981, 1, 'ne'),
    ('Niš', 21.8958, 43.3209, 1, 'e'),
]
TOWN_SIZE = {0: 13.0, 1: 10.5}

# Towns shown as the map closes in, under their names of 1941 (Petrovgrad, not Zrenjanin; Bitolj; Podgorica):
# rank 2 from a moderate close-up, rank 3 only near. Placed by GeoNames, the town of that name nearest the rough
# position given; the page sets each name beside its town where it finds room
DETAIL_TOWNS = [
    # rank 2
    ('Banja Luka', 17.19, 44.77, 2), ('Bihać', 15.87, 44.82, 2), ('Mostar', 17.81, 43.34, 2), ('Tuzla', 18.67, 44.54, 2),
    ('Zenica', 17.91, 44.20, 2), ('Travnik', 17.67, 44.23, 2), ('Jajce', 17.27, 44.34, 2), ('Foča', 18.78, 43.51, 2),
    ('Goražde', 18.98, 43.67, 2), ('Višegrad', 19.29, 43.78, 2), ('Livno', 17.01, 43.83, 2), ('Knin', 16.20, 44.04, 2),
    ('Gospić', 15.37, 44.55, 2), ('Karlovac', 15.55, 45.49, 2), ('Sisak', 16.37, 45.47, 2), ('Osijek', 18.69, 45.55, 2),
    ('Vinkovci', 18.80, 45.29, 2), ('Slavonski Brod', 18.02, 45.16, 2), ('Bjelovar', 16.84, 45.90, 2),
    ('Varaždin', 16.34, 46.31, 2), ('Maribor', 15.65, 46.55, 2), ('Celje', 15.27, 46.23, 2), ('Šibenik', 15.89, 43.73, 2),
    ('Dubrovnik', 18.09, 42.65, 2), ('Cetinje', 18.91, 42.39, 2), ('Nikšić', 18.94, 42.77, 2), ('Pljevlja', 19.36, 43.36, 2),
    ('Bijelo Polje', 19.75, 43.04, 2), ('Kolašin', 19.52, 42.82, 2), ('Užice', 19.84, 43.86, 2), ('Valjevo', 19.89, 44.27, 2),
    ('Šabac', 19.69, 44.75, 2), ('Kragujevac', 20.91, 44.01, 2), ('Kraljevo', 20.69, 43.72, 2), ('Čačak', 20.35, 43.89, 2),
    ('Novi Pazar', 20.51, 43.14, 2), ('Mitrovica', 20.87, 42.89, 2), ('Prizren', 20.74, 42.21, 2), ('Peć', 20.29, 42.66, 2),
    ('Bitolj', 21.33, 41.03, 2), ('Ohrid', 20.80, 41.12, 2), ('Štip', 22.20, 41.74, 2), ('Vranje', 21.90, 42.55, 2),
    ('Leskovac', 21.95, 42.99, 2), ('Pirot', 22.59, 43.15, 2), ('Zaječar', 22.29, 43.90, 2), ('Smederevo', 20.93, 44.66, 2),
    ('Požarevac', 21.19, 44.62, 2), ('Pančevo', 20.64, 44.87, 2), ('Zemun', 20.40, 44.84, 2),
    ('Sremska Mitrovica', 19.61, 44.97, 2), ('Vukovar', 19.00, 45.35, 2), ('Subotica', 19.67, 46.10, 2),
    ('Sombor', 19.11, 45.77, 2), ('Petrovgrad', 20.39, 45.38, 2), ('Vršac', 21.30, 45.12, 2), ('Sušak', 14.45, 45.33, 2),
    ('Ogulin', 15.23, 45.27, 2), ('Prijedor', 16.71, 44.98, 2), ('Doboj', 18.09, 44.73, 2), ('Zvornik', 19.10, 44.39, 2),
    ('Konjic', 17.96, 43.65, 2), ('Trebinje', 18.34, 42.71, 2), ('Nova Gradiška', 17.38, 45.26, 2), ('Đakovo', 18.41, 45.31, 2),
    ('Slavonska Požega', 17.67, 45.34, 2), ('Sinj', 16.64, 43.70, 2), ('Šid', 19.23, 45.13, 2), ('Petrinja', 16.28, 45.44, 2),
    ('Drvar', 16.38, 44.37, 2), ('Bugojno', 17.45, 44.06, 2), ('Berane', 19.87, 42.84, 2),
    # rank 3
    ('Rudo', 19.37, 43.62, 3), ('Rogatica', 19.00, 43.80, 3), ('Han Pijesak', 18.95, 44.08, 3), ('Vlasenica', 18.94, 44.18, 3),
    ('Srebrenica', 19.30, 44.10, 3), ('Prača', 18.77, 43.77, 3), ('Trnovo', 18.45, 43.67, 3), ('Čajniče', 19.07, 43.56, 3),
    ('Žabljak', 19.12, 43.15, 3), ('Plužine', 18.84, 43.15, 3), ('Kalinovik', 18.45, 43.50, 3), ('Gacko', 18.53, 43.17, 3),
    ('Nevesinje', 18.11, 43.26, 3), ('Bileća', 18.43, 42.87, 3), ('Kotor Varoš', 17.37, 44.62, 3), ('Teslić', 17.86, 44.61, 3),
    ('Prnjavor', 17.66, 44.87, 3), ('Ključ', 16.78, 44.53, 3), ('Sanski Most', 16.67, 44.77, 3),
    ('Mrkonjić Grad', 17.08, 44.42, 3), ('Glamoč', 16.85, 44.05, 3), ('Bosansko Grahovo', 16.36, 44.18, 3),
    ('Šipovo', 17.09, 44.28, 3), ('Donji Vakuf', 17.40, 44.14, 3), ('Gornji Vakuf', 17.59, 43.94, 3),
    ('Prozor', 17.61, 43.82, 3), ('Jablanica', 17.76, 43.66, 3), ('Posušje', 17.33, 43.47, 3), ('Imotski', 17.22, 43.45, 3),
    ('Kupres', 17.28, 43.99, 3), ('Bosanski Petrovac', 16.37, 44.55, 3), ('Plaški', 15.37, 45.08, 3), ('Brinje', 15.13, 45.00, 3),
    ('Otočac', 15.24, 44.87, 3), ('Perušić', 15.38, 44.65, 3), ('Korenica', 15.71, 44.74, 3), ('Udbina', 15.77, 44.53, 3),
    ('Gračac', 15.85, 44.30, 3), ('Donji Lapac', 15.96, 44.55, 3), ('Srb', 16.13, 44.36, 3), ('Slunj', 15.59, 45.12, 3),
    ('Glina', 16.09, 45.34, 3), ('Dvor', 16.37, 45.07, 3), ('Kostajnica', 16.54, 45.22, 3), ('Vrbovec', 16.42, 45.88, 3),
    ('Čazma', 16.62, 45.75, 3), ('Kutina', 16.78, 45.48, 3), ('Novska', 16.98, 45.34, 3), ('Pakrac', 17.19, 45.44, 3),
    ('Daruvar', 17.22, 45.59, 3), ('Pleternica', 17.81, 45.29, 3), ('Ilok', 19.38, 45.22, 3), ('Ruma', 19.82, 45.01, 3),
    ('Bajina Bašta', 19.57, 43.97, 3), ('Kosjerić', 19.91, 43.99, 3), ('Ub', 20.07, 44.46, 3), ('Lazarevac', 20.26, 44.38, 3),
    ('Obrenovac', 20.20, 44.65, 3), ('Mladenovac', 20.70, 44.44, 3), ('Arilje', 20.10, 43.75, 3), ('Požega', 20.04, 43.85, 3),
    ('Ivanjica', 20.23, 43.58, 3), ('Nova Varoš', 19.81, 43.46, 3), ('Priboj', 19.53, 43.58, 3), ('Prijepolje', 19.65, 43.39, 3),
    ('Sjenica', 20.01, 43.27, 3), ('Mojkovac', 19.58, 42.96, 3), ('Šavnik', 19.10, 42.96, 3), ('Kotor', 18.77, 42.42, 3),
    ('Bar', 19.09, 42.10, 3), ('Ulcinj', 19.21, 41.93, 3), ('Herceg Novi', 18.54, 42.45, 3), ('Ljubuški', 17.55, 43.20, 3),
    ('Stolac', 17.96, 43.08, 3), ('Olovo', 18.58, 44.13, 3), ('Kladanj', 18.69, 44.23, 3), ('Vareš', 18.33, 44.16, 3),
    ('Bratunac', 19.33, 44.18, 3), ('Lopare', 18.85, 44.64, 3), ('Brčko', 18.81, 44.87, 3), ('Bijeljina', 19.21, 44.76, 3),
]
DETAIL_TOWN_SIZE = {2: 8.0, 3: 7.0}

# The lakes of 1941, by a point in each: Natural Earth also has the reservoirs dammed after the war (Bileća,
# Buško jezero), which must stay off
LAKES = [('Skadarsko', 19.32, 42.19), ('Ohridsko', 20.72, 41.04), ('Prespansko', 21.01, 40.91),
         ('Dojransko', 22.75, 41.22), ('Vransko', 15.57, 43.91)]

# The neighbours in April 1941 (Austria was the German Reich's since 1938), lettered spaced out in their land
NEIGHBOURS = [
    ('Italija', 13.62, 45.38, -64),
    ('Nemačka', 14.95, 46.88, 0),
    ('Mađarska', 18.35, 46.48, 0),
    ('Rumunija', 21.95, 45.62, 0),
    ('Bugarska', 23.12, 42.95, -90),
    ('Grčka', 22.05, 40.72, 0),
    ('Albanija', 19.98, 41.45, -72),
]
SEA = ('Jadransko more', [(14.85, 43.42), (15.9, 42.86), (16.95, 42.33), (17.9, 41.9)])
TITLE_AT = (21.2, 46.72)                           # the title's left end, top right of the sheet

LETTER = {'town': 0.0, 'river': 0.0, 'neighbour': 0.55, 'sea': 0.7}   # letter-spacing, in em

# The country divided, from the April war to the liberation, as OpenHistoricalMap dates each state's border (cut to
# the Kingdom's land). The map shows the zones of the month it shows: after Italy's capitulation (8 IX 1943) the NDH
# takes Dalmatia, Germany takes Montenegro, Albania's share and the Adriatic littoral; Bulgaria leaves in IX 1944,
# the German military administration in Serbia ends in X 1944.
#   tone: how firmly the land was held, as a grey of the ink: annexed darkest, occupied under the occupier's own
#   administration in the middle, the Italian military zones inside the NDH (whose civil administration stayed) the
#   lightest; at each step German a little darker than Italian, and the allies' annexations as dark as Italy's;
#   hatch: annexed (or, for Bulgaria, held as if annexed), each power its own pattern.
# Hungary's and the Reich's relations are those from after their formal annexations (14 XII and 1 VIII 1941): they
# had held Bačka, Baranja, Međimurje, Prekmurje and northern Slovenia since April. Montenegro's governorate (3 X 1941)
# is what Italy held there from April. OHM ends Hungary's annexations only with "1944": they end here with the
# liberation of Bačka (X 1944), though Međimurje and Prekmurje were held into 1945.
ANNEXED_DE, ANNEXED = 0.15, 0.12              # annexed by Germany; by Italy, Hungary, Bulgaria, Albania
OCCUPIED_DE, OCCUPIED_IT = 0.09, 0.065         # occupied, under the occupier's own administration
# key, OHM relation, what the legend says, from, to (as OHM dates them), tone, hatch
PARTITION = [
    ('ndh', 2692713, 'Nezavisna Država Hrvatska', '1941-04', '1943-09-10', 0, None),
    ('srbija', 2692357, 'Područje Vojnog zapovednika u Srbiji', '1941-04', '1944-10-22', OCCUPIED_DE, None),
    ('crnagora', 2695479, 'Crna Gora pod italijanskom upravom', '1941-04', '1943-09-08', OCCUPIED_IT, None),
    ('nemacka', 2692712, 'pripojila Nemačka', '1941-04', '1945-05-08', ANNEXED_DE, 'nemacka'),
    ('italija', 2747829, 'pripojila Italija', '1941-04', '1943-09-08', ANNEXED, 'italija'),
    ('madjarska', 2692359, 'pripojila Mađarska', '1941-04', '1944-10-20', ANNEXED, 'madjarska'),
    ('bugarska', 2695478, 'zaposela Bugarska', '1941-04', '1943-07', ANNEXED, 'bugarska'),
    ('bugarska43', 2920397, 'zaposela Bugarska', '1943-07', '1944-08-26', ANNEXED, 'bugarska'),
    ('albanija', 2695459, 'pripojeno Albaniji pod Italijom', '1941-04', '1943-09-08', ANNEXED, 'albanija'),
    ('ndh43', 2747830, 'Nezavisna Država Hrvatska', '1943-09-10', '1945-05-15', 0, None),
    ('crnagora43', 2855621, 'Crna Gora pod nemačkom okupacijom', '1943-09-12', '1944-12-15', OCCUPIED_DE, None),
    ('primorje', 2961565, 'Operativna zona Jadransko primorje, pod Nemačkom', '1943-09-10', '1945-05-08', OCCUPIED_DE, None),
    ('albanija43', 2800553, 'pripojeno Albaniji pod nemačkom okupacijom', '1943-09-08', '1944-11-29', ANNEXED, 'albanija'),
]
# Zones drawn inside a state, over its tone, with their own lines (not the borders between states):
# Banat in Serbia, under its own German administration, a touch darker; Italy's zones II and III in the NDH,
# cut from it by the traced lines (zone I is the annexed coast), each a shade of the Italian grey
# who held each zone, for its colour on the page: de, it, hu, bg, al (Albania's annexation); none for the NDH
POWER = {'ndh': None, 'srbija': 'de', 'crnagora': 'it', 'nemacka': 'de', 'italija': 'it', 'madjarska': 'hu', 'bugarska': 'bg', 'bugarska43': 'bg', 'albanija': 'al', 'ndh43': None, 'crnagora43': 'de', 'primorje': 'de', 'albanija43': 'al', 'banat': 'de', 'zona2': 'it', 'zona3': 'it'}
SUBZONES = [
    ('banat', 'Banat pod upravom folksdojčera', '1941-04', '1944-10-22', 0.04),
    ('zona2', 'italijanska zona II u NDH', '1941-04', '1943-09-08', 0.04),
    ('zona3', 'italijanska zona III u NDH', '1941-04', '1943-09-08', 0.025),
]
BANAT = 2694624                                     # in Serbia, under its own German administration
# the new states' names, lettered spaced out across them, while one of their zones is on the map, with a smaller
# line under a name where the name alone would mislead: Serbia was the "Područje Vojnog zapovednika u Srbiji" (Gebiet
# des Militärbefehlshabers in Serbien), Banat an autonomous part of it ruled by its ethnic Germans (sr.wikipedia,
# "Vojna uprava u Srbiji", "Banat u Drugom svetskom ratu"): text, lon, lat, rotation, size, zones, the line under it
ZONE_LABELS = [
    ('NEZAVISNA DRŽAVA HRVATSKA', 17.45, 44.95, -9, 12.0, ('ndh', 'ndh43'), None),
    ('SRBIJA', 20.95, 43.62, 0, 13.0, ('srbija',), 'područje Vojnog zapovednika'),
    ('BANAT', 20.62, 45.42, 0, 10.0, ('banat',), 'pod upravom folksdojčera'),
    ('CRNA GORA', 19.32, 42.78, -20, 10.5, ('crnagora', 'crnagora43'), None),
]
PARTITION_TITLE = ('PODELA JUGOSLAVIJE', 'posle aprilskog rata 1941.')
# Inside NDH: the German-Italian demarcation line and the line between Italy's zones II and III (with its variant),
# traced from the printed map in the repo root by scripts/trace_ndh_zones.py
NDH_LINES = PAGE / 'sources' / 'ndh-zones-1941.json'
# the zones' names, small, between the lines: text, lon, lat, rotation
NDH_LABELS = [
    ('zona II', 15.72, 44.62, -52),
    ('zona III', 16.86, 44.12, -38),
    ('nemačka zona', 18.05, 44.52, -30),
]



# ---------- fetching ----------

def fetch(url: str, path: Path, data: str | None = None) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['curl', '-sS', '-L', '-f', '-m', '600', '-A', 'knjiga-boraca-map/1.0', '-o', str(path), url]
    if data is not None:
        query = path.with_suffix('.query')
        query.write_text(data, encoding='utf-8')
        cmd[1:1] = ['--data-urlencode', f'data@{query}']
    for attempt in range(4):
        if subprocess.run(cmd).returncode == 0:
            time.sleep(0.5)                         # gently, one request at a time
            return path
        time.sleep(5 * (attempt + 1))
    raise SystemExit(f'could not fetch {url}')


def ohm_shape(rel_id: int, cache_name: str):
    """An OpenHistoricalMap boundary relation as one (multi)polygon: its outer ways less its inner ones"""
    path = fetch('https://overpass-api.openhistoricalmap.org/api/interpreter', CACHE / cache_name,
                 f'[out:json][timeout:280];relation({rel_id});out geom;')
    rel = [e for e in json.loads(path.read_text(encoding='utf-8'))['elements'] if e['type'] == 'relation'][0]
    lines = {'outer': [], 'inner': []}
    for m in rel['members']:
        if m['type'] == 'way' and len(m.get('geometry', [])) > 1:
            lines['inner' if m['role'] == 'inner' else 'outer'].append(LineString([(g['lon'], g['lat']) for g in m['geometry']]))
    shape_ = unary_union(list(polygonize(unary_union(lines['outer']))))
    for hole in (polygonize(unary_union(lines['inner'])) if lines['inner'] else []):
        shape_ = shape_.difference(hole)
    return shape_


def kingdom_lonlat():
    return ohm_shape(OHM_KINGDOM, 'ohm_kingdom.json')       # its one hole is Zadar, Italy's


def natural_earth(name: str):
    path = fetch(NE.format(name), CACHE / f'{name}.geojson')
    out = []
    for f in json.loads(path.read_text(encoding='utf-8'))['features']:
        g = shape(f['geometry'])
        if g.intersects(AREA):
            out.append((f['properties'], g.intersection(AREA)))
    return out


def river_lonlat(rel_id) -> list[LineString]:
    """A river's main stream as directed lines (OSM draws waterways downstream), its side channels left out"""
    if isinstance(rel_id, str) and rel_id.startswith('ne:'):
        lines = []
        for p, g in natural_earth('ne_10m_rivers_europe'):
            if p.get('name') == rel_id[3:]:
                lines += list(g.geoms) if g.geom_type == 'MultiLineString' else [g]
        return lines
    path = fetch(OSM_FULL.format(rel_id), CACHE / 'rivers' / f'{rel_id}.xml')
    root = ET.parse(path).getroot()
    nodes = {n.get('id'): (float(n.get('lon')), float(n.get('lat'))) for n in root.iter('node')}
    ways = {w.get('id'): [nodes[nd.get('ref')] for nd in w.iter('nd') if nd.get('ref') in nodes] for w in root.iter('way')}
    rel = [r for r in root.iter('relation') if r.get('id') == str(rel_id)][0]
    lines = [LineString(ways[m.get('ref')]) for m in rel.iter('member')
             if m.get('type') == 'way' and m.get('role') in ('', 'main_stream') and len(ways.get(m.get('ref'), [])) > 1]
    return [l for l in lines if l.intersects(AREA)]


# ---------- projection ----------

class Projection:
    def __init__(self, p):
        self.lon0 = math.radians(p['lon0'])
        f1, f2, f0 = (math.radians(p[k]) for k in ('lat1', 'lat2', 'lat0'))
        t = lambda f: math.tan(math.pi / 4 + f / 2)
        self.n = math.log(math.cos(f1) / math.cos(f2)) / math.log(t(f2) / t(f1))
        self.F = math.cos(f1) * t(f1) ** self.n / self.n
        self.R = p['radius']
        self.rho0 = self.R * self.F / t(f0) ** self.n
        self.k, self.x0, self.y0 = 1.0, 0.0, 0.0

    def km(self, lon, lat):
        rho = self.R * self.F / math.tan(math.pi / 4 + math.radians(lat) / 2) ** self.n
        th = self.n * (math.radians(lon) - self.lon0)
        return rho * math.sin(th), self.rho0 - rho * math.cos(th)

    def __call__(self, lon, lat):
        x, y = self.km(lon, lat)
        return (x - self.x0) * self.k, (self.y0 - y) * self.k

    def geom(self, g):
        if g.geom_type == 'Polygon':
            return Polygon([self(*c) for c in g.exterior.coords], [[self(*c) for c in r.coords] for r in g.interiors])
        if g.geom_type == 'LineString':
            return LineString([self(*c) for c in g.coords])
        if g.geom_type == 'MultiPolygon':
            return MultiPolygon([self.geom(p) for p in g.geoms])
        if g.geom_type == 'MultiLineString':
            return MultiLineString([self.geom(l) for l in g.geoms])
        if g.geom_type == 'GeometryCollection':
            return unary_union([self.geom(x) for x in g.geoms if not x.is_empty])
        raise ValueError(g.geom_type)


# ---------- the hand ----------

def chaikin(pts, closed, rounds=2):
    for _ in range(rounds):
        out = []
        n = len(pts)
        segs = range(n) if closed else range(n - 1)
        if not closed:
            out.append(pts[0])
        for i in segs:
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            out.append((0.75 * x1 + 0.25 * x2, 0.75 * y1 + 0.25 * y2))
            out.append((0.25 * x1 + 0.75 * x2, 0.25 * y1 + 0.75 * y2))
        if not closed:
            out.append(pts[-1])
        pts = out
    return pts


def resample(pts, step, closed):
    if closed:
        pts = pts + [pts[0]]
    out = [pts[0]]
    carry = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        d = math.hypot(x2 - x1, y2 - y1)
        s = step - carry
        while s < d:
            out.append((x1 + (x2 - x1) * s / d, y1 + (y2 - y1) * s / d))
            s += step
        carry = d - (s - step)
    if not closed and out[-1] != pts[-1]:
        out.append(pts[-1])
    if closed and math.hypot(out[-1][0] - out[0][0], out[-1][1] - out[0][1]) < step * 0.3:
        out.pop()
    return out


def normals(pts, closed):
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        b = pts[(i + 1) % n] if (closed or i < n - 1) else pts[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        out.append((-dy / d, dx / d))
    return out


def wobble(pts, closed, amp, seed):
    """Moves each point along its normal by a smooth noise: two long waves and a short one, as a hand drifts"""
    rnd = random.Random(seed)
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:] + ([pts[0]] if closed else [])))
    waves = []
    for wl, w in ((90.0, 0.55), (31.0, 0.35), (13.0, 0.1)):
        if closed:                                  # whole waves round the ring, so it closes without a step
            wl = length / max(1, round(length / wl))
        waves.append((2 * math.pi / wl, rnd.uniform(0, 2 * math.pi), w))
    out, s = [], 0.0
    nrm = normals(pts, closed)
    for i, (p, (nx, ny)) in enumerate(zip(pts, nrm)):
        if i:
            s += math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
        off = amp * sum(w * math.sin(f * s + ph) for f, ph, w in waves)
        out.append((p[0] + nx * off, p[1] + ny * off))
    return out


def hand(line_pts, closed, tol, amp, seed, step=2.5):
    g = (Polygon(line_pts) if closed else LineString(line_pts)).simplify(tol, preserve_topology=False)
    if g.is_empty:
        return []
    pts = list(g.exterior.coords)[:-1] if closed else list(g.coords)
    if len(pts) < (3 if closed else 2):
        return []
    pts = chaikin(pts, closed)
    pts = resample(pts, step, closed)
    if len(pts) < (3 if closed else 2):
        return []
    return wobble(pts, closed, amp, seed)


def fmt(v: float) -> str:
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def path_d(pts, closed) -> str:
    """Absolute first point, then relative steps: the shortest text for dense lines"""
    out = [f'M{fmt(pts[0][0])} {fmt(pts[0][1])}']
    px, py = round(pts[0][0], 1), round(pts[0][1], 1)
    steps = []
    for x, y in pts[1:]:
        x, y = round(x, 1), round(y, 1)
        steps.append(f'{fmt(x - px)} {fmt(y - py)}')
        px, py = x, y
    if steps:
        out.append('l' + ' '.join(steps))
    if closed:
        out.append('z')
    return ''.join(out).replace(' -', '-')


# ---------- rivers ----------

def chain(lines: list[LineString]) -> list[tuple[float, float]]:
    """Joins a river's pieces into one line from the source down: the longest run, extended at both ends by the
    piece that starts (or ends) nearest, as long as one lies within 3 km"""
    merged = line_merge(MultiLineString(lines), directed=True)
    pieces = [list(g.coords) for g in (merged.geoms if merged.geom_type == 'MultiLineString' else [merged])]
    pieces.sort(key=lambda c: -LineString(c).length)
    main = pieces.pop(0)
    gap = 0.03                                      # degrees, about 3 km
    grown = True
    while grown and pieces:
        grown = False
        for i, c in enumerate(pieces):
            if math.dist(main[-1], c[0]) < gap:
                main, grown = main + c[1:], True
            elif math.dist(c[-1], main[0]) < gap:
                main, grown = c[:-1] + main, True
            if grown:
                pieces.pop(i)
                break
    return main


def ribbon(pts, widths) -> str:
    nrm = normals(pts, False)
    left = [(x + nx * w / 2, y + ny * w / 2) for (x, y), (nx, ny), w in zip(pts, nrm, widths)]
    right = [(x - nx * w / 2, y - ny * w / 2) for (x, y), (nx, ny), w in zip(pts, nrm, widths)]
    # a round end at the mouth: half a circle from the left edge round to the right
    (ex, ey), (nx, ny), w = pts[-1], nrm[-1], widths[-1]
    tx, ty = ny, -nx                                # the direction of flow
    cap = []
    for i in range(1, 6):
        a = math.pi * i / 6
        cap.append((ex + (nx * math.cos(a) + tx * math.sin(a)) * w / 2, ey + (ny * math.cos(a) + ty * math.sin(a)) * w / 2))
    return path_d(left + cap + right[::-1], True)


def label_path(pts, text_len, near, offset):
    """The stretch of river under a label: the window around the point nearest `near`, smoothed hard and set
    `offset` units off the river on the side towards the top of the sheet, running left to right"""
    best = min(range(len(pts)), key=lambda i: math.dist(pts[i], near))
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(a, b))
    half = text_len / 2 + 6
    i0 = max(0, next((i for i in range(best, -1, -1) if cum[best] - cum[i] >= half), 0))
    i1 = min(len(pts) - 1, next((i for i in range(best, len(pts)) if cum[i] - cum[best] >= half), len(pts) - 1))
    seg = LineString(pts[i0:i1 + 1]).simplify(4.0)
    seg_pts = chaikin(list(seg.coords), False, rounds=3)
    if seg_pts[-1][0] < seg_pts[0][0]:
        seg_pts = seg_pts[::-1]
    nrm = normals(seg_pts, False)
    # the normal of a line running left to right points down the sheet: go the other way, above the river
    return path_d([(x - nx * offset, y - ny * offset) for (x, y), (nx, ny) in zip(seg_pts, nrm)], False)


# ---------- lettering ----------

class Lettering:
    def __init__(self, path: Path):
        f = TTFont(path)
        self.upm = f['head'].unitsPerEm
        self.cmap = f.getBestCmap()
        self.hmtx = f['hmtx']

    def width(self, text: str, size: float, spacing_em: float = 0.0) -> float:
        adv = sum(self.hmtx[self.cmap.get(ord(c), self.cmap[ord(' ')])][0] for c in text)
        return adv / self.upm * size + spacing_em * size * max(0, len(text) - 1)


# ---------- the sheet ----------

def gained_lonlat(kingdom, land_all):
    """The land Yugoslavia gained after the war, Italy's from 1920 (Istria, Rijeka, Zadar, Cres and Lošinj, Lastovo,
    the Slovene Littoral): today's Slovenia and Croatia, as Natural Earth draws them, less the kingdom; the slivers
    their two borders leave between them dropped (thinner than a few km)"""
    states = unary_union([g for p, g in natural_earth('ne_10m_admin_0_countries') if p.get('ADMIN') in ('Slovenia', 'Croatia')])
    gained = states.intersection(land_all).difference(kingdom).intersection(box(13.3, 42.3, 17.3, 46.6))
    return unary_union([p for p in polygons_of(gained) if p.area > 2e-4 and p.area / p.length > 0.006])


def gained_lines(proj, gained, kingdom, land_all):
    """The gained land's outline, without its edge on the kingdom (the kingdom's own line draws that): its coast, and
    its land border with Italy, each as hand-drawn lines"""
    shore = land_all.boundary
    near_kingdom = kingdom.buffer(0.012)
    coast, border = [], []
    for i, p in enumerate(polygons_of(gained)):
        ring = LineString(p.exterior.coords)
        whole = not ring.intersects(near_kingdom)
        pieces = [ring] if whole else [g for g in getattr(ring.difference(near_kingdom), 'geoms', [ring.difference(near_kingdom)])
                                       if g.geom_type == 'LineString' and g.length > 0.02]
        for j, piece in enumerate(pieces):
            # split each piece where it leaves the shore for the land border and back
            runs, run, kind = [], [], None
            for c in piece.coords:
                k = 'coast' if shore.distance(Point(c)) < 0.005 else 'border'
                if run and k != kind:
                    runs.append((kind, run + [c]))
                    run = [c]
                else:
                    run.append(c)
                kind = k
            runs.append((kind, run))
            closed = whole and len(runs) == 1
            for n, (kind, pts) in enumerate(runs):
                pts = [proj(*c) for c in (pts[:-1] if closed else pts)]
                if len(pts) < 3:
                    continue
                drawn = hand(pts, closed, 0.3, 0.2, seed=7000 + 100 * i + 10 * j + n, step=2.0)
                if drawn:
                    (coast if kind == 'coast' else border).append(path_d(drawn, closed))
    return {'coast': coast, 'border': border}


def main():
    proj = Projection(PROJ)

    kingdom = kingdom_lonlat()
    land_all = unary_union([g for _, g in natural_earth('ne_10m_land')] + [g for _, g in natural_earth('ne_10m_minor_islands')])
    land_ll = kingdom.intersection(land_all)
    gained = gained_lonlat(kingdom, land_all)

    # scale: the kingdom's width fills the sheet between the margins
    xs, ys = zip(*[proj.km(*c) for c in kingdom.exterior.coords])
    proj.k = (WIDTH - MARGIN['left'] - MARGIN['right']) / (max(xs) - min(xs))
    proj.x0 = min(xs) - MARGIN['left'] / proj.k
    proj.y0 = max(ys) + MARGIN['top'] / proj.k
    height = (max(ys) - min(ys)) * proj.k + MARGIN['top'] + MARGIN['bottom']
    print(f'sheet {WIDTH:.0f} x {height:.0f}, {proj.k:.3f} units/km')

    land = proj.geom(land_ll)
    polys = sorted(land.geoms if land.geom_type == 'MultiPolygon' else [land], key=lambda p: -p.area)
    mainland, islands = polys[0], [p for p in polys[1:] if p.area > 1.5]
    land_d = []
    rings = [(list(mainland.exterior.coords)[:-1], 0.55, 0.45)]
    rings += [(list(r.coords)[:-1], 0.3, 0.2) for r in mainland.interiors if Polygon(r).area > 1.5]
    rings += [(list(p.exterior.coords)[:-1], 0.3 if p.area < 60 else 0.45, 0.2 if p.area < 60 else 0.35) for p in islands]
    for i, (ring, tol, amp) in enumerate(rings):
        pts = hand(ring, True, tol, amp, seed=1000 + i, step=2.0 if len(ring) < 400 else 2.5)
        if pts:
            land_d.append(path_d(pts, True))
    print(f'land: mainland + {len(rings) - 1} rings')

    inside = prep(proj.geom(kingdom).buffer(1.5))

    # lakes, whole: the border runs across Skadar, Ohrid, Prespa and Dojran, as the outline draws it. Each gets one
    # water line inside its shore, the way a pen shades water
    lakes_d, lake_lines_d = [], []
    lake_shapes = [g for _, g in natural_earth('ne_10m_lakes') + natural_earth('ne_10m_lakes_europe')]
    for i, (name, lon, lat) in enumerate(LAKES):
        g = next((g for g in lake_shapes if g.distance(Point(lon, lat)) < 0.05), None)
        if g is None:
            raise SystemExit(f'no lake at {name}')
        p = proj.geom(g)
        p = max(p.geoms, key=lambda q: q.area) if p.geom_type == 'MultiPolygon' else p
        pts = hand(list(p.exterior.coords)[:-1], True, 0.3, 0.2, seed=2000 + i, step=1.8)
        lakes_d.append(path_d(pts, True))
        water = Polygon(pts).buffer(-1.7)
        for q in (water.geoms if water.geom_type == 'MultiPolygon' else [water]):
            if q.area > 8:
                lake_lines_d.append(path_d(list(q.exterior.coords)[:-1], True))
    print(f'lakes: {len(lakes_d)}')

    font = Lettering(FONT)
    rivers_out, labels_out = [], []
    for n, (name, ids, w0, w1, near) in enumerate(RIVERS):
        lines = [l for i in ids for l in river_lonlat(i)]
        if not lines:
            print(f'  {name}: nothing')
            continue
        course = [proj(*c) for c in chain(lines)]
        line = LineString(course).simplify(0.7)
        pts = chaikin(list(line.coords), False)
        pts = resample(pts, 2.0, False)
        pts = wobble(pts, False, 0.25, seed=3000 + n)
        cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            cum.append(cum[-1] + math.dist(a, b))
        total = cum[-1] or 1.0
        widths = [w0 + (w1 - w0) * math.sqrt(c / total) for c in cum]
        runs, run = [], []
        for p, w in zip(pts, widths):               # only the stretches inside the kingdom
            if inside.contains(Point(p)):
                run.append((p, w))
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        runs = [r for r in runs if len(r) > 3]
        if not runs:
            print(f'  {name}: outside')
            continue
        for r in runs:
            rivers_out.append({'name': name, 'd': ribbon([p for p, _ in r], [w for _, w in r])})
        if near and LETTER_RIVERS:
            longest = max(runs, key=len)
            size = 8.5
            tl = font.width(name, size)
            labels_out.append({'name': name, 'size': size,
                               'd': label_path([p for p, _ in longest], tl, proj(*near), w1 / 2 + 2.2)})
        print(f'  {name}: {sum(len(r) for r in runs)} points in {len(runs)} run(s)')

    # the rivers again as plain lines, for the close-ups: a ribbon would thicken as the map is enlarged
    river_lines = []
    for n, (name, ids, *_rest) in enumerate([(r[0], r[1]) for r in RIVERS] + DETAIL_RIVERS):
        lines = [l for i in ids for l in river_lonlat(i)]
        if not lines:
            continue
        course = [proj(*c) for c in chain(lines)]
        pts = chaikin(list(LineString(course).simplify(0.3).coords), False)
        pts = resample(pts, 1.2, False)
        pts = wobble(pts, False, 0.12, seed=6000 + n)
        run, runs = [], []
        for p in pts:
            if inside.contains(Point(p)):
                run.append(p)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        kind = 'major' if name in MAJOR_RIVERS else ('minor' if n >= len(RIVERS) else 'river')
        for r in runs:
            if len(r) > 3:
                river_lines.append({'name': name, 'kind': kind, 'd': path_d(r, False)})
    print(f'river lines: {len(river_lines)}')

    # the towns the close-ups add
    from make_unit_route import gazetteer, lookup  # here, not at the top: that script imports this one
    index = gazetteer()
    detail_towns = []
    for name, lon, lat, rank in DETAIL_TOWNS:
        pos, _ = lookup(index, name, (lon, lat), 25, classes=('P',))
        if pos is None:
            print(f'  town {name}: not in GeoNames near {lon}, {lat}; kept as given')
            pos = (lon, lat)
        x, y = proj(*pos)
        size = DETAIL_TOWN_SIZE[rank]
        detail_towns.append({'name': name.upper(), 'rank': rank, 'x': round(x, 1), 'y': round(y, 1), 'size': size,
                             'w': round(font.width(name.upper(), size), 1)})

    towns_out = []
    for name, lon, lat, rank, pos in TOWNS:
        x, y = proj(lon, lat)
        size = TOWN_SIZE[rank]
        w = font.width(name.upper(), size)
        gap = 5.5 if rank == 0 else 4.0
        dx = {'e': gap, 'ne': gap * 0.7, 'se': gap * 0.7, 'w': -gap, 'nw': -gap * 0.7, 'sw': -gap * 0.7, 'n': 0, 's': 0}[pos]
        anchor = 'start' if dx > 0 else 'end' if dx < 0 else 'middle'
        cap = size * 0.72
        dy = {'n': -gap - 4.0, 'ne': -gap * 0.6, 'nw': -gap * 0.6, 'e': cap / 2, 'w': cap / 2,
              's': gap + cap + 3, 'se': gap * 0.6 + cap + 2, 'sw': gap * 0.6 + cap + 2}[pos]   # room for a caron
        lx = x + dx
        x1 = lx if anchor == 'start' else lx - w if anchor == 'end' else lx - w / 2
        towns_out.append({'name': name, 'rank': rank, 'x': round(x, 1), 'y': round(y, 1),
                          'lx': round(lx, 1), 'ly': round(y + dy, 1), 'anchor': anchor, 'size': size,
                          'underline': [round(x1, 1), round(x1 + w, 1)]})

    neighbours_out = []
    for name, lon, lat, rot in NEIGHBOURS:
        x, y = proj(lon, lat)
        neighbours_out.append({'name': name.upper(), 'x': round(x, 1), 'y': round(y, 1), 'rotate': rot})

    future = gained_lines(proj, gained, kingdom, land_all)
    print(f'gained after the war: {len(polygons_of(gained))} parts, {len(future["coast"])} coast lines, '
          f'{len(future["border"])} border lines')

    sea_name, sea_pts = SEA
    sea_line = chaikin([proj(*p) for p in sea_pts], False, rounds=4)
    sea_out = {'name': sea_name.upper(), 'd': path_d(sea_line, False)}

    tx, ty = proj(*TITLE_AT)
    meta = {**PROJ, 'k': proj.k, 'x0': proj.x0, 'y0': proj.y0}

    ts = [
        '// Generated by scripts/make_map_1941.py from OpenHistoricalMap (the 1941 border, CC0), Natural Earth (land,',
        '// lakes; public domain) and OpenStreetMap (rivers, ODbL). Do not edit by hand: change the script and run it.',
        '',
        f'export const SHEET = {{ width: {WIDTH:.0f}, height: {round(height)}, unitsPerKm: {proj.k:.5f} }}',
        '',
        '// Lambert conformal conic: projection.ts turns a place\'s lon/lat into the sheet\'s units with these',
        f'export const PROJ = {json.dumps({k: round(v, 6) for k, v in meta.items()})}',
        '',
        f'export const TITLE_AT = {{ x: {tx:.1f}, y: {ty:.1f} }}',
        '',
        '// Yugoslavia\'s land: the mainland, then the islands',
        f'export const LAND: string[] = {json.dumps(land_d)}',
        '',
        f'export const LAKES: string[] = {json.dumps(lakes_d)}',
        f'export const LAKE_LINES: string[] = {json.dumps(lake_lines_d)}',
        '',
        '// each river as a filled ribbon, widening downstream',
        f'export const RIVERS: {{ name: string; d: string }}[] = {json.dumps(rivers_out, ensure_ascii=False)}',
        '',
        '// the line each river\'s name is lettered along, just above the river',
        f'export const RIVER_LABELS: {{ name: string; size: number; d: string }}[] = {json.dumps(labels_out, ensure_ascii=False)}',
        '',
        'export type Town = { name: string; rank: number; x: number; y: number; lx: number; ly: number;',
        "  anchor: 'start' | 'middle' | 'end'; size: number; underline: [number, number] }",
        f'export const TOWNS: Town[] = {json.dumps(towns_out, ensure_ascii=False)}',
        '',
        '// for the close-ups: the rivers as plain lines (major, river, minor), and more towns (rank 2, then 3), each',
        '// with its name\'s width at its size, for the page to set the names where they find room',
        f'export const RIVER_LINES: {{ name: string; kind: string; d: string }}[] = {json.dumps(river_lines, ensure_ascii=False)}',
        f'export const DETAIL_TOWNS: {{ name: string; rank: number; x: number; y: number; size: number; w: number }}[] = {json.dumps(detail_towns, ensure_ascii=False)}',
        '',
        f'export const NEIGHBOURS: {{ name: string; x: number; y: number; rotate: number }}[] = {json.dumps(neighbours_out, ensure_ascii=False)}',
        '',
        '// the land Yugoslavia gained after the war (Istria, Rijeka, Zadar, Cres and Lošinj, Lastovo, the Slovene Littoral),',
        '// for a faint outline: its coast, and its border with Italy (Natural Earth, today\'s)',
        f'export const GAINED: {{ coast: string[]; border: string[] }} = {json.dumps(future)}',
        '',
        f'export const SEA = {json.dumps(sea_out, ensure_ascii=False)}',
        '',
        f'export const LETTER_SPACING = {json.dumps(LETTER)}',
        '',
    ]
    OUT.write_text('\n'.join(ts), encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)')

    partition(proj, land_ll)
    liberated(proj, land_all.intersection(kingdom.union(gained).buffer(0.04)), land_all.intersection(kingdom.union(gained)))


def polygons_of(g) -> list:
    """The polygons in a geometry: cutting a border to the land leaves collections with stray lines and points"""
    if g.geom_type == 'Polygon':
        return [g]
    if hasattr(g, 'geoms'):
        return [p for part in g.geoms for p in polygons_of(part)]
    return []


def ring_path(poly, tol=0.5) -> str:
    """A zone's area for its hatching: smoothed, not wobbled (the lines drawn over it carry the hand)"""
    out = []
    for p in polygons_of(poly):
        for ring in [p.exterior, *p.interiors]:
            if len(ring.coords) < 4:
                continue
            simple = Polygon(ring).simplify(tol)
            pts = list(simple.exterior.coords)[:-1] if simple.geom_type == 'Polygon' else []
            if len(pts) >= 3 and Polygon(pts).area > 0.8:
                out.append(path_d(chaikin(pts, True, rounds=1), True))
    return ''.join(out)


def month_day(date: str, end: bool = False) -> str:
    """An OHM date as a day: '1943-07' -> 1943-07-01, '1944' -> 1944-01-01"""
    parts = date.split('-')
    return '-'.join(parts + ['01'] * (3 - len(parts)))


def side_of(line, far: float, toward: str):
    """The half of the sheet on one side of a traced line, the line's ends run on out: 'sw' the coast's side"""
    pts = list(line.coords)
    (x0, y0), (x1, y1) = pts[0], pts[1]
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    start = (x0 - (x1 - x0) * 400, y0 - (y1 - y0) * 400)
    stop = (xb + (xb - xa) * 400, yb + (yb - ya) * 400)
    if toward == 'sw':
        ring = [start, *pts, stop, (stop[0], far), (-far, far), (-far, start[1])]
    else:
        ring = [start, *pts, stop, (far, stop[1]), (far, -far), (start[0], -far)]
    return Polygon(ring).buffer(0)


def partition(proj, land_ll):
    """The zones from 1941 to 1945, each once; the periods in which the set of zones holds, each with its borders
    drawn by hand; Banat's line inside Serbia; the lines traced inside the NDH"""
    zones = {}
    for key, rel_id, legend, start, stop, tone, hatch in PARTITION:
        zones[key] = {'geom': proj.geom(ohm_shape(rel_id, f'ohm_{rel_id}.json').intersection(land_ll)), 'legend': legend,
                      'from': month_day(start), 'to': month_day(stop), 'tone': tone, 'hatch': hatch, 'sub': False}
        print(f'  {key}: {zones[key]["geom"].area:.0f} units2')
    outer = proj.geom(land_ll).boundary.buffer(0.9)

    # inside the NDH of 1941: Italy's zones II and III, cut by the traced lines
    traced = json.loads(NDH_LINES.read_text(encoding='utf-8'))['lines']
    as_line = lambda key: LineString([proj(lon, lat) for lon, lat in traced[key]])
    ndh = zones['ndh']['geom']
    italian = ndh.intersection(side_of(as_line('demarcation'), 5000, 'sw'))
    zone2 = italian.intersection(side_of(as_line('zone_ii_iii'), 5000, 'sw'))
    zone3 = italian.difference(zone2)
    banat = proj.geom(ohm_shape(BANAT, f'ohm_{BANAT}.json').intersection(land_ll))
    subs = {'banat': banat, 'zona2': zone2, 'zona3': zone3}
    for key, legend, start, stop, tone in SUBZONES:
        zones[key] = {'geom': subs[key], 'legend': legend, 'from': month_day(start), 'to': month_day(stop),
                      'tone': tone, 'hatch': None, 'sub': True}
        print(f'  {key}: {subs[key].area:.0f} units2')
    for key, (lon, lat) in (('zona2', (15.72, 44.62)), ('zona3', (16.86, 44.12))):
        if not zones[key]['geom'].contains(Point(*proj(lon, lat))):
            print(f'  WARNING: {key} does not hold its label point')

    # the periods: from April 1941 to May 1945, a month at a time, the zones that hold in its middle
    months = [f'{y}-{m:02d}' for y in range(1941, 1946) for m in range(1, 13) if '1941-04' <= f'{y}-{m:02d}' <= '1945-05']
    periods = []
    for ym in months:
        mid = f'{ym}-15'
        on = [k for k, z in zones.items() if z['from'] <= mid < z['to']]
        if periods and periods[-1]['zones'] == on:
            periods[-1]['to'] = ym
        else:
            periods.append({'from': ym, 'to': ym, 'zones': on})

    # each period's borders between states, by hand (the same border keeps its hand from period to period)
    drawn = {}
    for n, period in enumerate(periods):
        states = [zones[k]['geom'] for k in period['zones'] if not zones[k]['sub']]
        net = unary_union([g.boundary for g in states]) if states else None
        lines_d = []
        if net is not None and not net.is_empty:
            merged = line_merge(net.difference(outer))
            for i, l in enumerate(merged.geoms if hasattr(merged, 'geoms') else [merged]):
                if l.length <= 4:
                    continue
                sig = (round(l.coords[0][0]), round(l.coords[0][1]), round(l.coords[-1][0]), round(l.coords[-1][1]), round(l.length))
                if sig not in drawn:
                    pts = hand(list(l.coords), False, 0.6, 0.4, seed=4000 + len(drawn))
                    drawn[sig] = path_d(pts, False) if pts else ''
                if drawn[sig]:
                    lines_d.append(drawn[sig])
        period['lines'] = lines_d
        period['ndh'] = 'zona2' in period['zones']
        period['banat'] = 'banat' in period['zones']
        print(f'  period {period["from"]}..{period["to"]}: {", ".join(period["zones"])}; {len(lines_d)} lines')

    serbia_inside = zones['srbija']['geom'].simplify(0.3).buffer(-1.0)       # Banat's line with the rest of Serbia
    inner = line_merge(banat.boundary.difference(outer).intersection(serbia_inside))
    banat_d = []
    for i, l in enumerate(inner.geoms if hasattr(inner, 'geoms') else [inner]):
        pts = hand(list(l.coords), False, 0.6, 0.35, seed=4500 + i) if l.length > 4 else []
        if pts:
            banat_d.append(path_d(pts, False))
    ndh_lines = {}
    ndh_area = ndh.buffer(2.0)
    for n, (key, pts) in enumerate(traced.items()):
        line = LineString([proj(lon, lat) for lon, lat in pts]).intersection(ndh_area)
        out_d = []
        for i, l in enumerate(line.geoms if hasattr(line, 'geoms') else [line]):
            if l.geom_type == 'LineString' and l.length > 6:
                hp = hand(list(l.coords), False, 0.8, 0.35, seed=5000 + 100 * n + i)
                if hp:
                    out_d.append(path_d(hp, False))
        ndh_lines[key] = out_d
    ndh_labels = []
    for t, lon, lat, r in NDH_LABELS:
        x, y = proj(lon, lat)
        ndh_labels.append({'name': t, 'x': round(x, 1), 'y': round(y, 1), 'rotate': r})
    labels = []
    for t, lon, lat, r, size, keys, under in ZONE_LABELS:
        x, y = proj(lon, lat)
        labels.append({'name': t, 'x': round(x, 1), 'y': round(y, 1), 'rotate': r, 'size': size, 'zones': list(keys), 'under': under})
    zones_out = [{'key': k, 'legend': z['legend'], 'd': ring_path(z['geom']), 'tone': z['tone'], 'hatch': z['hatch'],
                  'power': POWER.get(k)} for k, z in zones.items()]
    out = OUT.with_name('partition1941.ts')
    out.write_text('\n'.join([
        '// Generated by scripts/make_map_1941.py: Yugoslavia divided, from the April war to the liberation, from',
        '// OpenHistoricalMap (CC0). Do not edit by hand.',
        '',
        f'export const PARTITION_TITLE = {json.dumps(PARTITION_TITLE, ensure_ascii=False)}',
        '',
        "// each zone's area once: the grey of who held it (a share of the ink) and its hatching if annexed",
        'export type Zone = { key: string; legend: string; d: string; tone: number; hatch: string | null; power: string | null }',
        f'export const ZONES: Zone[] = {json.dumps(zones_out, ensure_ascii=False)}',
        '',
        '// the months in which a set of zones holds (YYYY-MM, both ends in), with the borders between its states drawn by',
        "// hand; banat and ndh: whether Banat's line and the lines inside the NDH are drawn",
        'export type Period = { from: string; to: string; zones: string[]; lines: string[]; banat: boolean; ndh: boolean }',
        f'export const PERIODS: Period[] = {json.dumps(periods, ensure_ascii=False)}',
        f'export const BANAT_LINES: string[] = {json.dumps(banat_d)}',
        '',
        'export const ZONE_LABELS: { name: string; x: number; y: number; rotate: number; size: number; zones: string[]; under: string | null }[] = '
        + json.dumps(labels, ensure_ascii=False),
        '',
        '// inside the NDH, traced from the printed map: the German-Italian demarcation line, the line between Italy\'s',
        '// zones II and III, and that line\'s variant (until IX 1943)',
        f'export const NDH_LINES: {{ demarcation: string[]; zone_ii_iii: string[]; zone_variant: string[] }} = {json.dumps(ndh_lines)}',
        f'export const NDH_LABELS: {{ name: string; x: number; y: number; rotate: number }}[] = {json.dumps(ndh_labels, ensure_ascii=False)}',
        '',
    ]), encoding='utf-8')
    print(f'wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB), {len(periods)} periods')


# The liberated and semi-liberated territory, traced from the VII's maps by scripts/trace_liberated.py: each map is
# shown in its months; clipped to all the land in the sheet's reach (in 1943 it takes in Istria and the Slovene
# Littoral, Italian before the war)
LIBERATED = PAGE / 'sources' / 'liberated.json'


def liberated(proj, land_all, country):
    if not LIBERATED.exists():
        return
    doc = json.loads(LIBERATED.read_text(encoding='utf-8'))
    reach = land_all.intersection(box(12.8, 40.4, 23.6, 47.2))
    shape_of = lambda rings: Polygon(rings[0], rings[1:]).buffer(0)
    out = []
    for m in sorted(doc['maps'], key=lambda m: m['from']):
        entry = {k: m[k] for k in ('key', 'from', 'to', 'label', 'source')}
        entry['standIn'] = m.get('standIn', [])
        lib = unary_union([shape_of(r) for r in m['liberated']]).intersection(reach)
        semi = unary_union([shape_of(r) for r in m['semi']]).difference(lib).intersection(reach)
        entry['liberated'] = ring_path(proj.geom(lib), tol=0.8)
        entry['semi'] = ring_path(proj.geom(semi), tol=0.8)
        print(f'  liberated {m["key"]}: {proj.geom(lib).area:.0f} units2, semi {proj.geom(semi).area:.0f}')
        out.append(entry)
    # the last month of the timeline: the whole country free, the war in Yugoslavia over by 15 May 1945 (no map)
    out.append({'key': '1945-05', 'from': '1945-05', 'to': '1945-05', 'label': 'cela zemlja, 15. V 1945.', 'source': '', 'standIn': [],
                'liberated': ring_path(proj.geom(country), tol=0.8), 'semi': ''})
    path = OUT.with_name('liberated1941.ts')
    path.write_text('\n'.join([
        '// Generated by scripts/make_map_1941.py from sources/liberated.json (scripts/trace_liberated.py): the liberated',
        "// and semi-liberated territory as the war's histories map it, each map in its months. Do not edit by hand.",
        '',
        '// standIn: the months it is shown in only for want of a map of their own',
        'export type Liberated = { key: string; from: string; to: string; label: string; source: string; standIn: string[]; liberated: string; semi: string }',
        f'export const LIBERATED: Liberated[] = {json.dumps(out, ensure_ascii=False)}',
        '',
    ]), encoding='utf-8')
    print(f'wrote {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
