// What Jovo Popović's book on the Prva lička (Beograd 1988) writes of its 2. bataljon „Pekiša Vuksan“, as episodes
// a reader steps through: each step a moment the book dates, with what the map shows of it. Places are [lon, lat];
// the railway's points are snapped to OpenStreetMap's line, the heights ("kota") found in the elevation by
// scripts/make_battalion_map.py, the churches are OpenStreetMap's. Text is the site's own (ekavica), the quoted
// words the book's. The book's page is the PDF's page plus four.
//
// Each action is read whole, from its start to its end, before it is drawn. What the book places is drawn solid;
// what it gives only as a direction, a relation or not at all is drawn dotted with "(?)" (`guess`), and the step's
// `notes` say what was worked out and from what. Times are the book's; where it gives none, the step says only
// what came before and after ("zatim", "za to vreme").

export type LL = [number, number]
// own: the 2. bataljon; friend: the brigade's other battalions; ally: other partisan units, brigades and odredi
export type Side = 'own' | 'friend' | 'ally' | 'enemy'
// where a label stands from its mark
export type Pos = 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw'
// whose an enemy mark is, for its colour: the Italians, the NDH's ustaše, gendarmes and domobrani, the Chetniks, the
// Germans. A mark that doesn't say takes it from its label's words, else from its episode (`foe`)
export type Force = 'it' | 'ndh' | 'cet' | 'de'
// the sheet an episode is drawn on: scripts/make_battalion_map.py writes each region's ground to terrain/<region>.ts
export type Region = 'kapela' | 'kosinj' | 'glina' | 'slunj' | 'dvor' | 'lovinac'

export type Mark = (
  // a unit's place: an ellipse (rx, ry in km, turned by rot degrees) round `at`
  | { t: 'area'; side: Side; at: LL; rx: number; ry: number; rot?: number; label?: string; lp?: Pos; guess?: boolean; force?: Force }
  // a move: a march, an attack, one stopped short (a bar at its end), a withdrawal (dashed), fire (dotted), and a
  // march into an ambush, which ends in the red cross of a unit smashed or taken
  | { t: 'move'; side: Side; path: LL[]; kind: 'march' | 'attack' | 'stopped' | 'back' | 'fire' | 'caught'; label?: string; lp?: Pos; at?: number; force?: Force; guess?: boolean }
  // an ambush: an arc open toward the way the enemy comes (`face`), the strokes of its fire across it
  | { t: 'ambush'; at: LL; face: LL; label?: string; lp?: Pos; guess?: boolean }
  // a garrison or strongpoint; `taken` crosses it out in red
  | { t: 'post'; at: LL; label: string; lp?: Pos; taken?: boolean; small?: boolean; guess?: boolean; force?: Force }
  // a train on the line; an armoured one filled
  | { t: 'train'; at: LL; label: string; lp?: Pos; armoured?: boolean; force?: Force; guess?: boolean }
  // track torn up or a road dug up: crosses along it
  | { t: 'cut'; path: LL[]; label?: string; lp?: Pos; guess?: boolean }
  | { t: 'fight'; at: LL }
  // a height the book names
  | { t: 'kota'; at: LL; label: string; lp?: Pos; guess?: boolean }
  // a named spot that is neither a height nor a strongpoint: a tunnel
  | { t: 'spot'; at: LL; label: string; lp?: Pos; guess?: boolean }
) & {
  until?: number               // what stands all through an episode is gone from its step `until` on (0-based)
  id?: string                  // which unit a standing mark is, where its label can't tell (two companies of the II)
}

export type Step = {
  date: string                 // as the title block prints it: "15. jula 1942."
  time?: string                // the hour, where the book gives one: "6.00"
  when?: string                // else what the book says of when: "pre zore", "zatim"
  text: string
  marks: Mark[]
  view?: [number, number, number, number]   // [west, south, east, north]: the step's own frame, else the episode's
  notes?: string[]             // what the map shows that the book does not say, and how it was worked out
}

export type Person = { name: string; id?: string; note?: string }

export type Episode = {
  key: string
  title: string
  short: string                // on the timeline
  dates: string
  start: string                // ISO days, for the timeline
  end: string
  about: string                // what it was, in a sentence or two
  region: Region
  view: [number, number, number, number]
  places: string[]             // the sheet's names the text uses, set first and a little larger
  foe: Force                   // whose an enemy mark is when neither it nor its label says
  base: Mark[]                 // what stands all through: garrisons and the like
  steps: Step[]
  enemy: string[]
  friends: string[]
  result: string
  fallen?: Person[]
  wounded?: Person[]
  pages: [number, number]      // the book's pages
}

export const SOURCE = {
  author: 'Jovo Popović',
  title: 'Prva lička proleterska NOU brigada „Marko Orešković“',
  place: 'Beograd 1988',
  pdf: '/pdfs/prva-licka-proleterska.pdf',
  pdfOffset: -4,               // the PDF's page = the book's page - 4
  missing: [146, 147],         // book pages the scan lacks: from 148 on the PDF's page is the book's - 6
  unitPath: '/units/prva-licka-brigada',
}

// Rest and marches between the episodes, where the book says where the battalion was
export const BETWEEN: { start: string; end: string; label: string }[] = [
  { start: '1942-07-16', end: '1942-07-18', label: 'Glibodol, Kunić-Selo' },
  { start: '1942-07-20', end: '1942-07-21', label: 'Kunić-Selo' },
  { start: '1942-07-23', end: '1942-07-31', label: 'Letište, Kunić-Selo' },
  { start: '1942-08-25', end: '1942-08-29', label: 'kod Škara' },
  { start: '1942-09-11', end: '1942-09-13', label: 'ofanziva na Škare' },
  { start: '1942-09-14', end: '1942-09-16', label: 'Kapela, iznad Škara' },
  { start: '1942-09-17', end: '1942-09-19', label: 'Crna Vlast, Ramljani, Krš' },
  { start: '1942-09-22', end: '1942-09-25', label: 'prema Pazarištima' },
  { start: '1942-10-04', end: '1942-10-10', label: 'Krbavica' },
  { start: '1942-10-11', end: '1942-10-20', label: 'na Baniju, Klasnić' },
  { start: '1942-10-24', end: '1942-10-27', label: 'Rudić, Klasnić' },
  { start: '1942-10-28', end: '1942-11-04', label: 'marš na Slunj' },
  { start: '1942-11-09', end: '1942-11-10', label: 'Zbjeg' },
  { start: '1942-11-15', end: '1942-11-20', label: 'Slunj, Veljun' },
  { start: '1942-11-21', end: '1942-11-25', label: 'Kladuša, Rujevac' },
  { start: '1942-11-30', end: '1942-12-02', label: 'Podzvizd' },
  { start: '1942-12-03', end: '1942-12-13', label: 'povratak u Liku' },
  { start: '1942-12-31', end: '1943-01-14', label: 'Mogorić, Vrebac, Pavlovac' },
]

// places used more than once
const P = {
  kunic: [15.3321, 45.1021] as LL,
  krasnica: [15.3443, 45.0446] as LL,          // JNA map: Krasnički vrh
  krmesac: [15.3284, 45.0519] as LL,           // JNA map: Krmesac, 947 m; the book's 937
  ridge: [15.3385, 45.0478] as LL,             // JNA map: the ridge Kupusarica (892) between Krasnički vrh and Krmesac
  kota816: [15.3985, 44.9773] as LL,           // an 820 m top of the elevation, 1.7 km above the line
  descent: [15.4182, 44.9849] as LL,           // the line's nearest point to it
  jesenicaSt: [15.4298, 44.9776] as LL,
  sisaljka: [15.4268, 44.9795] as LL,          // 0.4 km up the line from the station
  vakt27: [15.4394, 44.9652] as LL,            // 1.6 km down it, toward Javornik
  blataSt: [15.3988, 45.0330] as LL,
  javornikSt: [15.4595, 44.9260] as LL,
  jesenica: [15.4418, 44.9967] as LL,
  jesenicaChurch: [15.44036, 44.99605] as LL,  // OSM: crkva svetog Ilije proroka (Serbian Orthodox)
  potpolje: [15.4461, 45.0061] as LL,
  vezmari: [15.4174, 45.0146] as LL,
  lake: [15.4081, 45.0214] as LL,              // GeoNames: Jezero Begovac, the only lake by Blata
  vukelicPoljana: [15.4525, 44.9792] as LL,
  saborsko: [15.4778, 44.9836] as LL,
  blata: [15.4008, 45.0320] as LL,
  plaski: [15.3624, 45.0810] as LL,
  plaskiSt: [15.3681, 45.0783] as LL,
  vojnovac: [15.3342, 45.1500] as LL,
  ambush: [15.3498, 45.1369] as LL,            // the line at the northern Vorkapići, by the 388 crossing (JNA map), 7 km from Plaški
  north: [15.3448, 45.1397] as LL,             // 0.5 km up the line, short of the tunnel and Vojnovac
  south: [15.3613, 45.1242] as LL,             // 1.6 km down it, at the southern Vorkapići by the 408 crossing
  tunnel: [15.3398, 45.1414] as LL,            // OSM and the JNA map: the short tunnel under the road junction 413
  hum: [15.3898, 45.1360] as LL,               // OSM and the JNA map: Hum, 861 m
  brinje: [15.1313, 44.9998] as LL,
  kip: [15.1503, 45.0105] as LL,               // JNA map and OSM: Kip, 578 m
  k586: [15.1558, 45.0188] as LL,              // a knoll of some 590 m by the road 1 km north of Kip (JNA map: no height printed)
  krispolje: [15.1661, 45.0271] as LL,
  jezerane: [15.2063, 45.0519] as LL,
  maljen: [15.1918, 45.0460] as LL,            // JNA map: Maljen, 682 m; the book's 684
  pernari: [15.1985, 45.0122] as LL,
  letinac: [15.2246, 44.9818] as LL,
  dabar: [15.3105, 44.9545] as LL,
  dabarChurch: [15.30691, 44.95520] as LL,     // OSM: crkva svetog Mihovila arkanđela
  rudopoljeSt: [15.4884, 44.8666] as LL,       // GeoNames
  vakt33: [15.4658, 44.9035] as LL,            // on the line 2.7 km below Javornik, toward Rudopolje
}

// The Lika valley under Velebit: OpenStreetMap's villages, GeoNames' where OSM has none
const K = {
  krs: [15.3199, 44.7292] as LL,
  poljan: [15.3127, 44.7148] as LL,
  bakovac: [15.2122, 44.7108] as LL,           // OSM: Bakovac Kosinjski
  antinovica: [15.2314, 44.6900] as LL,        // OSM: Antinovica, the book's Antinovac
  velikiVrh: [15.2481, 44.6960] as LL,         // JNA map and OSM: Veliki vrh, 910 m
  k788: [15.1874, 44.7178] as LL,              // JNA map: Brneci vršak, 788 m, north-west of Bakovac
  k894: [15.2246, 44.7162] as LL,              // JNA map: a top of 891 m north-east of Bakovac, for the book's 894
  gornjiKosinj: [15.2754, 44.7164] as LL,
  podjelar: [15.2682, 44.7094] as LL,
  kruscica: [15.2621, 44.6781] as LL,
  duliba: [15.2405, 44.6750] as LL,            // JNA map: the clearing Duliba, 732 m, west of Kruščica
  poljanka: [15.2809, 44.7041] as LL,          // OSM and the JNA map: the hamlet Poljanka by Sušanj, the book's Poljanak
  vukelici: [15.2698, 44.7449] as LL,          // OSM: Vukelići between Gornji and Donji Kosinj, the book's Vukelić-Selo
  susanj: [15.2801, 44.7086] as LL,
  lipovoPolje: [15.2164, 44.7509] as LL,
  klanac: [15.2975, 44.6328] as LL,            // the heart of Pazarišta
  kaludjerovac: [15.3111, 44.6535] as LL,
  metlaca: [15.3066, 44.6572] as LL,           // OSM: Metlača, 800 m
  vaganac: [15.2616, 44.6512] as LL,
  otes: [15.2811, 44.6160] as LL,
}

// Glina and the Maja's valley
const G = {
  glina: [16.0908, 45.3383] as LL,
  station: [16.0926, 45.3315] as LL,           // GeoNames: the old line's station
  kozarica: [16.0815, 45.3250] as LL,          // OSM: Kozarica, 184 m
  church: [16.08922, 45.34189] as LL,          // OSM: crkva svetog Ivana Nepomuka
  battery: [16.1000, 45.3402] as LL,           // "kod klaonice": the town's east side, where the I attacked
  jukinacMost: [16.1094, 45.3470] as LL,       // JNA map: where the road from Jukinac crosses the Maja
  ciglana: [16.0985, 45.3439] as LL,           // JNA map: the brickworks (cg.) and its clay pits, between the centre and Jukinac
  crniLug: [16.1060, 45.3268] as LL,           // JNA map: Crni Lug Glinski
  majskePoljane: [16.1169, 45.3408] as LL,
  klasnic: [16.1748, 45.2407] as LL,           // OSM: Donji Klasnić
  rudici: [16.1643, 45.2298] as LL,
  drenovac: [16.2321, 45.3067] as LL,          // OSM: Drenovac Banski
  majskiTrtnik: [16.1653, 45.2989] as LL,
  ravnoRasce: [16.1449, 45.3041] as LL,
  roviska: [16.1199, 45.3062] as LL,
  gredjani: [15.9686, 45.3100] as LL,
  hrastovica: [16.2889, 45.3986] as LL,
}

// Slunj, the Slunjčica (the book's Slušnica) and Melnice
const S = {
  slunj: [15.5850, 45.1145] as LL,
  church: [15.58751, 45.11560] as LL,          // OSM: crkva Presvetog Trojstva
  k471: [15.5863, 45.0879] as LL,              // JNA map: Lalića vrh, 473 m, the top of Mala Melnica
  k518: [15.5729, 45.0974] as LL,              // Velika Melnica, 518 m
  plijes: [15.5614, 45.1124] as LL,            // JNA map: Plješ, 387 m, west of Podmelnica; the book's Pliješ, 389
  k292: [15.5798, 45.1182] as LL,              // JNA map: 295, north-west of the town, for the book's 292
  k402: [15.6131, 45.0928] as LL,              // JNA map: V. Pluznik, 400 m, between Slunj and Lađevac, for the book's 402
  izvor: [15.5883, 45.0784] as LL,             // JNA map: the spring of the Slunjčica (Slušnica), 241 m
  lumbardenik: [15.5976, 45.1021] as LL,
  ladjevac: [15.6316, 45.0888] as LL,          // OSM: Donji Lađevac
  zbjeg: [15.5333, 45.1000] as LL,             // GeoNames: Zbjeg Močilski
}

// The Una between Dvor and Kostajnica
const D = {
  dvor: [16.3785, 45.0696] as LL,
  zamlaca: [16.3839, 45.0891] as LL,
  uncani: [16.4153, 45.1291] as LL,
  golubovac: [16.4260, 45.1354] as LL,         // OSM: Golubovac Divuški
  golupsko: [16.4345, 45.1457] as LL,          // OSM: the 228 m top Golubovac, the book's Golupsko brdo, 225 m
  krstovo: [16.4131, 45.1362] as LL,           // a 215 m height above Golubovac and Unčani
  divusa: [16.4450, 45.1427] as LL,
  segestin: [16.3892, 45.1568] as LL,
  zrin: [16.3688, 45.1914] as LL,
  kirisnica: [16.4584, 45.1816] as LL,
  crljesnica: [16.4683, 45.1913] as LL,        // OSM: Crlješnica, 288 m; the book's 284
  k219: [16.4642, 45.1841] as LL,              // the elevation's 218 m top under it
  volinja: [16.4862, 45.2015] as LL,
}

// Udbina, Komić and the railway from Medak to Lovinac: OpenStreetMap's villages and tops, GeoNames' stations
const L = {
  udbina: [15.7656, 44.5306] as LL,
  baste: [15.7208, 44.4923] as LL,             // JNA map: Kurjak's hamlet Baste, where the roads to Ploča and to Komić part
  komic: [15.7403, 44.4509] as LL,
  poljice: [15.7886, 44.4558] as LL,
  // the valley Paklarić east of Mirkača and Opačić vrh, by its hamlets Pavlice (723), Račići, Šarići and Krtinići
  // on the JNA map 1:25,000 (470-2-1); GeoNames puts a Paklarić 1.9 km west, in the saddle between the two heights
  paklaric: [15.7795, 44.4275] as LL,
  mirkaca: [15.7563, 44.4370] as LL,           // OSM: Mirkača, 1131 m; the book's 1130
  komaca: [15.7269, 44.4413] as LL,            // OSM: Komača, 1177 m
  okrugla: [15.7324, 44.4225] as LL,           // OSM: Okrugla, 967 m; the book's 969
  catrnja: [15.7365, 44.4391] as LL,           // JNA map: the spring Čatrnja, 826 m, in the cut between Komača and M. Komić
  korita: [15.7385, 44.4284] as LL,            // JNA map: the hollow Korita, at the cut's southern end
  kopjuv: [15.7419, 44.4206] as LL,            // JNA map: Kapljuv, 1003 m; the book's Kopjuv, 1007 m
  lovinac: [15.6856, 44.3914] as LL,
  station: [15.6031, 44.4159] as LL,           // GeoNames: the station Raduč
  raduc: [15.5817, 44.4004] as LL,
  kruskovac: [15.5675, 44.4306] as LL,
  bogunica: [15.5444, 44.4417] as LL,          // GeoNames
  k706: [15.5416, 44.4352] as LL,              // JNA map and OSM: Bagunica, 703 m, south of Bogunica; the order's "Bogunici kota 706"
  k592: [15.5491, 44.4558] as LL,              // JNA map: Visoko br., 592.0, north of Bogunica; the order's "i 592"
  k601: [15.5625, 44.4378] as LL,              // JNA map: 599.6, east of Uzelci by the spring Popovac, for the book's 601
  miletic: [15.6603, 44.3572] as LL,           // OSM: the hamlet Miletić by Sveti Rok, the order's "Miletić Gaj"
  papuca: [15.5453, 44.4265] as LL,
  rastik: [15.5404, 44.4215] as LL,            // OSM: Rastik, 613 m; the book's 630
  zir: [15.6144, 44.4302] as LL,               // OSM: Zir, 850 m; the book's Žir, 852
  ploca: [15.6492, 44.4605] as LL,             // OSM: Gornja Ploča
  parcici: [15.6601, 44.4221] as LL,
  mogoric: [15.5911, 44.4895] as LL,
  medakSt: [15.5184, 44.4559] as LL,           // GeoNames: the station Medak
}

export const EPISODES: Episode[] = [
  {
    key: 'kapelska-pruga',
    foe: 'it',
    region: 'kapela',
    title: 'Na kapelskoj pruzi',
    short: 'Kapelska pruga',
    dates: '14–15. jula 1942.',
    start: '1942-07-14', end: '1942-07-15',
    about: 'Prva akcija brigade na pruzi Ogulin–Gospić, na odseku Blata–Rudopolje kroz Malu Kapelu. Drugi bataljon '
      + 'dobio je deo pruge kod stanice Lička Jesenica.',
    view: [15.385, 44.958, 15.468, 45.000],
    places: ['Lička Jesenica', 'Blata', 'Potkapela', 'Kunić', 'Glibodol'],
    base: [
      { t: 'area', side: 'enemy', at: P.jesenicaSt, rx: 0.32, ry: 0.2, rot: -35, label: 'stanica Jesenica: oko 100 Ital.', lp: 'se' },
      { t: 'area', side: 'enemy', at: P.blataSt, rx: 0.25, ry: 0.17, label: 'Blata: Italijani', lp: 'e' },
      { t: 'area', side: 'enemy', at: P.javornikSt, rx: 0.25, ry: 0.17, label: 'Javornik: Italijani', lp: 'e' },
      { t: 'area', side: 'enemy', at: P.jesenica, rx: 0.42, ry: 0.3, label: 'jesenički četnici', lp: 'ne' },
      { t: 'kota', at: P.kota816, label: '816', lp: 'w', guess: true },
    ],
    steps: [
      {
        date: '14. jula 1942.', time: '4.00',
        text: 'Brigada kreće iz Kunić-Sela u nekoliko kolona, bespućem preko Male Kapele, da zaobiđe četnike i '
          + 'Italijane. S Drugim bataljonom ide pedesetak ljudi s alatom za rušenje pruge. Put traje 12 do 14 sati; '
          + 'kod Krasnice se Prvi bataljon odvaja na jug.',
        view: [15.300, 44.925, 15.480, 45.112],
        notes: [
          'Put kolone knjiga daje mestima (zapadno od Plaškog, Crni potok, Prokos, Bijeli potok, Krasnica, greben između '
            + 'Krasnice i Krmesača); linija između njih prati teren i nije zapisana.',
          'Kotu 816 knjiga ne smešta na kartu, a topografska karta JNA 1:25.000 kote te visine blizu pruge nema. '
            + 'Nacrtana je na visu od oko 820 m iznad pruge zapadno od stanice Jesenica, na strani odakle je bataljon '
            + 'dolazio, kod kota 805 i 820 na karti JNA.',
          'Put Prvog bataljona na jug, preko Krasničke uvale i Vrletne drage do pruge kod Leskove strane, samo je naznačen.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'march', path: [P.kunic, [15.319, 45.088], [15.315, 45.068], [15.324, 45.053], P.ridge,
            [15.358, 45.022], [15.381, 44.996], P.kota816, P.descent], label: 'II bat.', lp: 'e', at: 0.3 },
          { t: 'kota', at: P.krmesac, label: 'Krmesač 937', lp: 'w' },
          // south across the roads to Jezerane and Dabar, then down the east side of Veliki Lisac toward the line
          { t: 'move', side: 'friend', kind: 'march', path: [P.ridge, [15.326, 45.022], [15.318, 44.990], [15.360, 44.976],
            [15.406, 44.968], [15.416, 44.950], [15.420, 44.934]], label: 'I bat., na jug', lp: 'w', at: 0.3 },
        ],
      },
      {
        date: '15. jula 1942.', when: 'noću',
        text: 'Napad je za sve bataljone određen između 2 i 3 sata. Bataljon se po planu spušta na prugu podno kote '
          + '816. Šine razmaknu brzo i nestručno. Odmah naiđe voz pun italijanskih vojnika, pređe preko njih i '
          + 'produži za Plaški: šine nisu bile dovoljno razmaknute.',
        notes: ['Mesto na pruzi je najbliža tačka pruge ispod kote 816; knjiga kaže samo „podno kote 816“.'],
        marks: [
          { t: 'area', side: 'own', at: P.descent, rx: 0.5, ry: 0.28, rot: -40, label: 'II bat.', lp: 'w', guess: true },
          { t: 'train', at: [15.4236, 44.9824], label: 'voz s Italijanima', lp: 'e' },
          { t: 'move', side: 'enemy', kind: 'attack', path: [[15.4276, 44.9801], [15.4204, 44.9846], [15.4191, 44.9911], [15.4107, 44.9967]],
            label: 'za Plaški', lp: 'e', at: 0.85 },
        ],
      },
      {
        date: '15. jula 1942.', time: 'do 18.30',
        text: 'Borci se ponovo spuštaju na prugu i ovog puta je ruše uporno, sve do 18.30.',
        notes: [
          'Deo pruge koji su srušili knjiga ne određuje; nacrtan je kod mesta gde su se prvi put spustili.',
          'Dan ovog i sledećih koraka knjiga ne kaže izričito: po redu događaja je 15. jul, a prva faza akcije na pruzi '
            + 'završena je 16. jula.',
        ],
        marks: [
          { t: 'area', side: 'own', at: P.descent, rx: 0.5, ry: 0.28, rot: -40, guess: true },
          { t: 'cut', path: [[15.4181, 44.9908], [15.4180, 44.9872], [15.4195, 44.9839], [15.4236, 44.9824]], label: 'porušena pruga', lp: 'w', guess: true },
        ],
      },
      {
        date: '15. jula 1942.', when: 'posle 18.30',
        view: [15.411, 44.961, 15.444, 44.986],
        text: 'Bataljon zauzima položaje prema Jesenici i posle kraće borbe razoružava italijansku posadu kod sisaljke '
          + '(vodocrpa) blizu stanice: 13 zarobljenih. Četa osamnaestogodišnjeg Jove Bogdanovića zauzima na juriš '
          + 'vaktarnicu br. 27, prvu od stanice prema Javorniku, „vrlo dobro utvrđenu za odbranu“: 19 zarobljenih.',
        notes: [
          'Položaj bataljona „prema Jesenici“ i mesto sisaljke („u blizini stanice“) knjiga ne određuje bliže.',
          'Vaktarnica br. 27 je prva od stanice prema Javorniku; nacrtana je oko 1,6 km niz prugu, a tačno mesto nije zapisano.',
          'Bogdanović je bio komandir Druge čete (knjiga, str. 36–37), pa je njegova četa označena kao 2/II.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.4218, 44.9800], rx: 0.55, ry: 0.3, rot: -20, label: 'II bat.', lp: 'nw', guess: true },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.4215, 44.9812], [15.4245, 44.9803], [15.4262, 44.9798]] },
          { t: 'post', at: P.sisaljka, label: 'sisaljka: 13 zarobljenih', lp: 'ne', taken: true, small: true, guess: true },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.4205, 44.9785], [15.4235, 44.9700], [15.4330, 44.9655], [15.4385, 44.9652]],
            label: '2/II (J. Bogdanović)', lp: 'sw', at: 0.45, guess: true },
          { t: 'post', at: P.vakt27, label: 'vaktarnica 27: 19 zarobljenih', lp: 'e', taken: true, small: true, guess: true },
        ],
      },
      {
        date: '15. jula 1942.', when: 'zatim',
        view: [15.415, 44.9735, 15.435, 44.9855],
        text: 'Italijani, predvođeni jeseničkim četnicima, krenu sa stanice u šumu između ceste i pruge. Čete '
          + 'bataljona ih razjure, uz osetne gubitke Italijana, koji se „u paničnom bjekstvu“ vrate u stanicu i više '
          + 'ne pokušavaju da napadnu.',
        marks: [
          { t: 'area', side: 'own', at: [15.4218, 44.9800], rx: 0.55, ry: 0.3, rot: -20, guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.4290, 44.9780], [15.4266, 44.9782], [15.4244, 44.9788]],
            label: 'Italijani i četnici', lp: 'n', at: 0.4 },
          { t: 'fight', at: [15.4236, 44.9781] },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.4240, 44.9768], [15.4262, 44.9758], [15.4286, 44.9764]],
            label: 'beže natrag u stanicu', lp: 's', at: 0.5 },
        ],
      },
      {
        date: '15. jula 1942.', when: 'posle toga',
        view: [15.415, 44.9735, 15.435, 44.9855],
        text: 'Štab brigade odluči da se napadne i sama stanica, gde je oko 100 Italijana s oficirima, dobro '
          + 'utvrđenih. Borci su iscrpljeni i napad ne uspeva, ali bataljon drži Italijane „u šahu“ dok se akcija ne '
          + 'završi na drugim mestima.',
        marks: [
          { t: 'area', side: 'own', at: [15.4218, 44.9800], rx: 0.55, ry: 0.3, rot: -20, guess: true },
          { t: 'move', side: 'own', kind: 'stopped', path: [[15.4232, 44.9810], [15.4262, 44.9796], [15.4284, 44.9786]],
            label: 'napad na stanicu', lp: 'ne', at: 0.3 },
          { t: 'fight', at: [15.4292, 44.9779] },
        ],
      },
    ],
    enemy: [
      'Italijani u Blatima, Ličkoj Jesenici, na Javorniku i u Rudopolju: oko 200 na 24 km pruge',
      'U tri vaktarnice između Rudopolja i Javornika: 60 Italijana',
      'Na stanici Jesenica: oko 100, s oficirima, dobro utvrđeni',
      'Jesenički četnici',
      'Blindirani voz iz Vrhovina, na Prvi bataljon',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: vaktarnica br. 32, južnije',
      'Treći, kordunaški bataljon: osiguranje i rezerva',
      'Četvrti, banijski bataljon: stanica Javornik',
    ],
    result: 'Bataljon je zarobio 32 Italijana. Cela brigada: 44 zarobljena, više od 40 pušaka i 3 puškomitraljeza, oko '
      + '8 km porušene pruge i 9 km telefonske linije. Komandant i komesar brigade posebno su pohvalili Drugi bataljon.',
    pages: [26, 29],
  },
  {
    key: 'vorkapic',
    foe: 'it',
    region: 'kapela',
    title: 'Zaseda kod Vorkapića',
    short: 'Vorkapić',
    dates: '19. jula 1942.',
    start: '1942-07-19', end: '1942-07-19',
    about: 'Ogulinski ilegalci javili su da 19. jula iz Ogulina vozom kreće oko 150 Italijana za osiguranje kapelske '
      + 'pruge. Zaseda je postavljena 7 km severno od Plaškog, kod Vorkapića.',
    view: [15.322, 45.085, 15.400, 45.155],
    places: ['Vojnovac', 'Vorkapići', 'Pothum Plaščanski', 'Lički Podhum', 'Plaški', 'Kunić'],
    base: [
      { t: 'area', side: 'enemy', at: P.vojnovac, rx: 0.45, ry: 0.3, label: 'Vojnovac: 200 Ital.', lp: 'w' },
      { t: 'area', side: 'enemy', at: P.plaski, rx: 0.65, ry: 0.42, label: 'Plaški: 800 Ital.', lp: 'w' },
    ],
    steps: [
      {
        date: '19. jula 1942.', when: 'pre zore',
        text: 'Treći, kordunaški bataljon zaposeda prugu i prekida šine da voz iskoči. Čete Drugog bataljona čuvaju '
          + 'bokove zasede: prema Vojnovcu na severu i prema Plaškom na jugu.',
        notes: [
          'Koja je četa bila gde, knjiga kaže tek po onome što su radile: Treća je dočekala patrolu iz Vojnovca, Prva '
            + 'voz iz Plaškog. Mesto Druge nije zapisano.',
          'Na topografskoj karti JNA 1:25.000 Vorkapića su dva zaseoka uz prugu, kod prelaza 388 i kilometar i po '
            + 'južnije, kod prelaza 408. Zaseda je nacrtana kod severnog, sedam kilometara od Plaškog, kako knjiga kaže, '
            + 'i blizu tunela u koji su Kordunaši kasnije uleteli.',
          'Udaljenost bočnih četa od zasede nije zapisana: Treća je nacrtana pola kilometra uz prugu, pred tunelom i '
            + 'stanicom Vojnovac, Prva kilometar i po niz prugu, kod južnih Vorkapića.',
        ],
        marks: [
          { t: 'area', side: 'friend', at: P.ambush, rx: 0.55, ry: 0.3, rot: -40, label: 'III (kordunaški) bat.', lp: 'e' },
          { t: 'cut', path: [[15.3488, 45.1378], [15.3508, 45.1360]] },
          { t: 'ambush', at: [15.3483, 45.1360], face: [15.3507, 45.1371], label: 'zaseda', lp: 'sw' },
          { t: 'area', side: 'own', at: P.north, rx: 0.3, ry: 0.18, rot: -20, label: '3/II', lp: 'n', guess: true },
          { t: 'area', side: 'own', at: P.south, rx: 0.55, ry: 0.22, rot: 58, label: '1/II', lp: 'e', guess: true },
          { t: 'area', side: 'own', at: [15.3445, 45.1340], rx: 0.3, ry: 0.2, label: '2/II', lp: 'w', guess: true },
        ],
      },
      {
        date: '19. jula 1942.', time: '6.00',
        view: [15.329, 45.127, 15.366, 45.153],
        text: 'Od Vojnovca naiđe italijanska patrola, oficir i 15 vojnika. Treća četa pokuša da je zarobi bez borbe, '
          + 'ali Italijani na poziv na predaju otvore vatru. Sedmorica poginu, a oficir i osmorica su zarobljeni. '
          + 'Pucnjava je uzbunila garnizon u Plaškom.',
        notes: ['Patrola je nacrtana kraj pruge, kojom je išla prema vaktarnici; put joj knjiga ne opisuje.'],
        marks: [
          { t: 'ambush', at: [15.3455, 45.1390], face: [15.3420, 45.1406], label: 'zaseda 3/II', lp: 'se', guess: true },
          { t: 'move', side: 'enemy', kind: 'caught', path: [[15.3343, 45.1483], [15.3368, 45.1467], [15.3389, 45.1422], [15.3428, 45.1402]],
            label: 'patrola, 16 ljudi', lp: 'w', at: 0.4 },
        ],
      },
      {
        date: '19. jula 1942.', when: 'odmah zatim',
        view: [15.344, 45.074, 15.384, 45.130],
        text: 'Iz Plaškog, uzbunjenog pucnjavom, krene voz s Italijanima, koji pucaju čim krenu sa stanice. Prva četa '
          + 'ga dočeka žestokom vatrom iz zaklona duž pruge, i voz posle prvih plotuna uzmakne prema Plaškom. Iz '
          + 'Plaškog je kasnije javljeno da je u njemu bilo „samo mrtvih oko 50“.',
        notes: ['Dokle je voz stigao, knjiga ne kaže; nacrtan je pred Prvom četom.'],
        marks: [
          { t: 'train', at: [15.3626, 45.1180], label: 'voz iz Plaškog', lp: 'e', guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.3686, 45.0790], [15.3709, 45.0844], [15.3728, 45.0908], [15.3638, 45.0959], [15.3603, 45.1007], [15.3624, 45.1135], [15.3626, 45.1172]] },
          { t: 'move', side: 'own', kind: 'fire', path: [[15.3612, 45.1230], [15.3622, 45.1195]] },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.3646, 45.1160], [15.3640, 45.1060], [15.3660, 45.0960]], label: 'natrag', lp: 'e', at: 0.6 },
        ],
      },
      {
        date: '19. jula 1942.', when: 'za to vreme',
        view: [15.329, 45.123, 15.368, 45.153],
        text: 'Dok se Prva četa bori s vozom, od Vojnovca naiđe još pedesetak Italijana. Kad vide da voz uzmiče, i oni '
          + 'se, pucajući nasumce, povuku prema vaktarnici. Samo se grupa od dvanaest s poručnikom upusti u borbu s '
          + 'Drugom četom kordunaškog bataljona i bude potučena: pobegla su samo dvojica, ostali su zarobljeni.',
        notes: [
          'Mesto vaktarnice knjiga ne daje; nacrtana je kraj pruge prema Vojnovcu.',
          'Gde je stajala Druga četa kordunaškog bataljona, knjiga ne kaže; strelica polazi od zasede.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.3361, 45.1465], [15.3389, 45.1422], [15.3438, 45.1400]],
            label: 'pedesetak Ital.', lp: 'w', at: 0.3 },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.3428, 45.1412], [15.3402, 45.1432], [15.3386, 45.1452]] },
          { t: 'post', at: [15.3372, 45.1455], label: 'vaktarnica', lp: 'w', small: true, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.3505, 45.1380], [15.3478, 45.1393], [15.3452, 45.1402]], label: '2/III', lp: 'n', at: 0.4, guess: true },
        ],
      },
      {
        date: '19. jula 1942.', when: 'potom',
        text: 'Goneći Italijane prema vaktarnici, delovi Drugog i Trećeg bataljona nađu se između dve vatre: stižu dva '
          + 'oklopna voza, iz Ogulina i iz Plaškog. Pešadija se ne usuđuje da izađe, ali topovi i minobacači tuku sve '
          + 'oko pruge. Petnaest boraca Druge čete kordunaškog bataljona, s komesarom čete, uleti u tunel i jedva se '
          + 'probije napolje; tu pogine Marko Šimulija Zore.',
        notes: [
          'Gde su se oklopni vozovi zaustavili, knjiga ne kaže; nacrtani su na pruzi severno i južno od zasede.',
          'Knjiga ne imenuje tunel; ovo je jedini tunel između Vojnovca i zasede (i na karti JNA), kratak, pod raskršćem '
            + 'puteva južno od stanice Vojnovac, u pravcu kojim su Kordunaši gonili Italijane.',
        ],
        marks: [
          { t: 'train', at: [15.3381, 45.1441], label: 'oklopni voz iz Ogulina', lp: 'w', armoured: true, guess: true },
          { t: 'train', at: [15.3622, 45.1215], label: 'oklopni voz iz Plaškog', lp: 'e', armoured: true, guess: true },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.3400, 45.1430], [15.3480, 45.1370]] },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.3612, 45.1232], [15.3530, 45.1340]] },
          { t: 'spot', at: P.tunnel, label: 'tunel', lp: 'nw' },
        ],
      },
      {
        date: '19. jula 1942.', when: 'povlačenje',
        text: 'Pod baražnom vatrom snage se povlače, Kordunaši prema Velikom Humu. Dok naređuje postupno '
          + 'povlačenje, ranjen je komandant bataljona Momčilo Novković. Druga četa drži italijanski streljački stroj '
          + 'na odstojanju dok mu komandant brigade Stevan Opsenica džepnim nožićem vadi gelere iz noge. Popodne ga '
          + 'bolničarka Zora Kovačević odvozi u bolnicu u Korenici; bataljonom od tada komanduje inž. Mićo Jović.',
        notes: [
          'Veliki Hum je ovde Hum (861 m, i na karti JNA), istočno od zasede; knjiga ne kaže koji je.',
          'Kuda se povukao Drugi bataljon i odakle je išao streljački stroj, knjiga ne kaže.',
        ],
        marks: [
          { t: 'move', side: 'friend', kind: 'back', path: [[15.3525, 45.1360], [15.3700, 45.1366], [15.3870, 45.1360]],
            label: 'prema Velikom Humu', lp: 'n', at: 0.6, guess: true },
          { t: 'move', side: 'own', kind: 'back', path: [[15.3440, 45.1335], [15.3380, 45.1305], [15.3320, 45.1270]], guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.3580, 45.1262], [15.3530, 45.1295], [15.3478, 45.1328]],
            label: 'streljački stroj', lp: 'se', at: 0.2, guess: true },
        ],
      },
    ],
    enemy: [
      'Garnizon u Plaškom: oko 800 Italijana; u Vojnovcu oko 200',
      'Patrola iz Vojnovca: oficir i 15 vojnika, pa još pedesetak',
      'Voz s Italijanima iz Plaškog',
      'Dva oklopna voza, iz Ogulina i iz Plaškog, s topovima i minobacačima',
    ],
    friends: [
      'Treći, kordunaški bataljon (komandant Josip Kustrin): na pruzi',
      'Manji delovi Drugog kordunaškog partizanskog odreda',
    ],
    result: 'Patrola je razbijena: sedam Italijana je poginulo, oficir i osmorica su zarobljeni. Voz iz Plaškog vraćen '
      + 'je s mnogo mrtvih, a Kordunaši su potukli i grupu od dvanaest s poručnikom. Zaseda je ipak otkrivena pre nego '
      + 'što je naišao voz iz Ogulina, a bataljon je ostao bez svog komandanta.',
    wounded: [{ name: 'Novković Jovanov Momčilo', id: '0002005812', note: 'komandant bataljona' }],
    pages: [31, 33],
  },
  {
    key: 'potpolje',
    foe: 'cet',
    region: 'kapela',
    title: 'Napad na Potpolje',
    short: 'Potpolje',
    dates: '22. jula 1942.',
    start: '1942-07-22', end: '1942-07-22',
    about: 'Brigada napada četnike u selima istočno od pruge, duž ceste Blata–Vezmari–Begovac–Lička Jesenica. Od '
      + 'maja ih tu skupljaju kraljevski oficiri koje su Italijani doveli iz zarobljeništva. Bataljon prvi put vodi '
      + 'inž. Mićo Jović.',
    view: [15.392, 44.968, 15.488, 45.038],
    places: ['Lička Jesenica', 'Potpolje', 'Blata', 'Begovac', 'Vezmari', 'Vukelić Poljana', 'Saborsko'],
    base: [
      { t: 'area', side: 'enemy', at: P.blata, rx: 0.4, ry: 0.28, label: 'Blata: 60 četnika', lp: 'e' },
      { t: 'area', side: 'enemy', at: P.jesenicaSt, rx: 0.32, ry: 0.2, rot: -35, label: 'stanica: oko 80 Ital.', lp: 'w' },
      { t: 'area', side: 'enemy', at: P.saborsko, rx: 0.45, ry: 0.3, label: 'Saborsko: 60 oružnika, 90 domobrana', lp: 'n' },
      { t: 'area', side: 'enemy', at: P.jesenica, rx: 0.42, ry: 0.32, label: 'Jesenica: 70 četnika', lp: 'e', until: 1 },
    ],
    steps: [
      {
        date: '22. jula 1942.', when: 'pred napad',
        text: 'Brigada je razvučena: najsevernije, kod jezera kraj Blata, stoji Drugi bataljon, gotovo 8 km od '
          + 'najjužnijih četa Prvog, prema Saborskom. Četvrti bataljon zauzima položaje na jugozapadu, oko stanice '
          + 'Jesenica. Mićo Jović i operativni oficir Jovo Ljeskovac razradili su plan za svaku četu.',
        notes: [
          '„Jezero Blata“ je ovde jedino jezero kod Blata (Jezero Begovac, GeoNames); knjiga ne daje bliže mesto. Na '
            + 'topografskoj karti JNA 1:25.000 polje Blata između Grbe, Ogrizovića i Begovca je močvarno, a jezera na '
            + 'njemu nema.',
          'Prvi bataljon je nacrtan kod Vukelić-Poljane, koju je napao, na južnom kraju rasporeda prema Saborskom.',
          'Jovo Ljeskovac je nacrtao skice rasporeda obe strane, i one su sačuvane (knjiga, str. 36); po njima bi se '
            + 'ova karta mogla nacrtati tačno.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.4135, 45.0175], rx: 0.75, ry: 0.4, rot: -25, label: 'II bat.', lp: 'nw', guess: true },
          { t: 'area', side: 'friend', at: [15.4560, 44.9800], rx: 0.6, ry: 0.35, label: 'I bat.', lp: 'se', guess: true },
          { t: 'area', side: 'friend', at: [15.4255, 44.9720], rx: 0.6, ry: 0.32, rot: -30, label: 'IV bat.', lp: 'sw' },
        ],
      },
      {
        date: '22. jula 1942.', when: 'u svanuće',
        text: 'Jedna četa napada Potpolje i brzo istera četnike, koji se zatvore u crkvu i popov stan. Prvi bataljon, '
          + 'koji je položaje zauzeo tačno u 4 sata, napada s druge strane: jedna četa na Jesenicu, i dve čete drže '
          + 'vezu, a druga odmah zauzme Vukelić-Poljanu i krene prema Saborskom, na osiguranje.',
        notes: [
          'Koja je četa Drugog bataljona napala, knjiga ne kaže; tu je poginuo komandir Druge čete Jovo Bogdanović, '
            + 'pa je verovatno bila njegova.',
          'Crkva je pravoslavna crkva svetog Ilije u Ličkoj Jesenici (OpenStreetMap); popov stan je kraj nje.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'attack', path: [[15.4200, 45.0150], [15.4330, 45.0110], [15.4440, 45.0065], [15.4410, 45.0000]],
            label: 'četa II bat. (2/II?)', lp: 'n', at: 0.45 },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.4535, 44.9825], [15.4480, 44.9895], [15.4420, 44.9940]] },
          { t: 'post', at: P.jesenicaChurch, label: 'crkva i popov stan', lp: 'w' },
          { t: 'area', side: 'enemy', at: [15.4408, 44.9962], rx: 0.2, ry: 0.14, label: 'Jesenica: četnici', lp: 'e' },
        ],
      },
      {
        date: '22. jula 1942.', when: 'tokom borbe',
        text: 'Italijani sa stanice tuku čete mitraljezima s visine, s boka. Četnici se priberu i pojačaju vatru; '
          + 'partizani počnu da ginu. Jovo Ljeskovac pogine dok s ugla jedne kuće osmatra. Četnici iz Blata pokušaju '
          + 'da zađu napadačima za leđa, ali ih primeti i odbije Četvrti bataljon, koji je na osiguranju oko stanice. '
          + 'Ustaše krenule iz Saborskog u pomoć vraćene su „u neredu“.',
        notes: [
          'Kojim su putem išli četnici iz Blata, knjiga ne kaže; zna se samo da ih je odbio Četvrti bataljon.',
          'Ko je vratio ustaše iz Saborskog, knjiga ne kaže; na tu stranu je pošla četa Prvog bataljona posle Vukelić-Poljane.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.4310, 44.9790], [15.4370, 44.9890], [15.4405, 44.9955]], force: 'it' },
          { t: 'fight', at: [15.4425, 45.0005] },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.3995, 45.0290], [15.3985, 45.0180], [15.4030, 45.0010],
            [15.4130, 44.9860], [15.4200, 44.9786]], label: 'četnici iz Blata', lp: 'w', at: 0.45, guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.4760, 44.9840], [15.4680, 44.9860], [15.4600, 44.9880]],
            label: 'ustaše iz Saborskog', lp: 's', at: 0.4, guess: true },
        ],
      },
      {
        date: '22. jula 1942.', time: 'do 14.00',
        text: 'Juriš na crkvu tražio bi velike žrtve. Operativni štab odluči da se čete neprimetno izvuku na polazne '
          + 'položaje; borba je trajala do 14 sati. Bataljon se povlači u selo Letište, gde od rana umire Mile Basta.',
        marks: [
          { t: 'move', side: 'own', kind: 'back', path: [[15.4415, 45.0030], [15.4330, 45.0105], [15.4215, 45.0155]] },
          { t: 'move', side: 'friend', kind: 'back', path: [[15.4440, 44.9930], [15.4500, 44.9860], [15.4545, 44.9815]] },
        ],
      },
    ],
    enemy: [
      'Četnici u Ličkoj Jesenici (70), Blatima (60) i Plaškom (oko 60), od maja nešto više',
      'Italijani na stanici Jesenica: mitraljezi, minobacači i topovi',
      'U Saborskom oko 60 oružnika i 90 domobrana, i ustaše',
    ],
    friends: [
      'Prvi bataljon: napad na Jesenicu i Vukelić-Poljanu',
      'Četvrti, banijski bataljon: oko stanice, odbio četnike iz Blata',
      'Treći, kordunaški bataljon: osiguranje',
    ],
    result: 'Zarobljeno je 10 četnika, zaplenjeno 12 karabina; kasnije se saznalo da je poginulo 17 četnika i jedan '
      + 'ustaša. Selo nije zauzeto. Štab brigade javio je 5 mrtvih i 9 ranjenih; knjiga imenom navodi šest poginulih '
      + 'iz bataljona i jednog koji je umro od rana.',
    fallen: [
      { name: 'Ljeskovac Milin Jovan', id: '0002004172', note: 'operativni oficir bataljona' },
      { name: 'Bogdanović Jovo', id: '0002000526', note: 'komandir Druge čete' },
      { name: 'Basarić Nikola', id: '0002000302' },
      { name: 'Radaković Mane', id: '0002007035' },
      { name: 'Ćerić Milan' },
      { name: 'Potrebić Dušan', id: '0002006900' },
      { name: 'Basta Mile', id: '0002000312', note: 'umro od rana u Letištu' },
    ],
    pages: [33, 37],
  },
  {
    key: 'brinje',
    foe: 'it',
    region: 'kapela',
    title: 'Prema Brinju',
    short: 'Brinje',
    dates: '11–14. avgusta 1942.',
    start: '1942-08-11', end: '1942-08-14',
    about: 'Brigada napada žandarmerijske posade u Jezeranima i Krišpolju. Drugi bataljon postavljen je prema '
      + 'garnizonu u Brinju, oko 500 Italijana i stotinak ustaša, da ih ne pusti u pomoć.',
    view: [15.075, 44.975, 15.235, 45.062],
    places: ['Brinje', 'Križpolje', 'Jezerane', 'Holjevci', 'Radotići', 'Pernari', 'Letinac', 'Vodoteč', 'Pavlovići'],
    base: [
      { t: 'area', side: 'enemy', at: P.brinje, rx: 0.7, ry: 0.45, rot: -20, label: 'Brinje: 500 Ital., 100 ustaša', lp: 'sw' },
      { t: 'area', side: 'enemy', at: P.jezerane, rx: 0.4, ry: 0.28, label: 'Jezerane: 120 oružnika', lp: 'ne', until: 4 },
      { t: 'area', side: 'enemy', at: P.krispolje, rx: 0.35, ry: 0.24, label: 'Krišpolje: 43 oružnika', lp: 'ne', until: 3 },
      { t: 'area', side: 'enemy', at: P.letinac, rx: 0.35, ry: 0.24, label: 'Letinac: ustaše', lp: 'e' },
    ],
    steps: [
      {
        date: '11. avgusta 1942.', when: 'kasno popodne',
        text: 'Čete Duje Čubrila i Miloša Đakovića, koji prvi put komanduju četama, i Treća četa Mile Počuče '
          + 'zaposedaju kote 578 i 586 (Kip) kraj brinjske ceste. Cesta je prekopana i zatrpana stablima, a na stabla '
          + 'su vezane bombe da eksplodiraju ako ih neko dirne.',
        view: [15.105, 44.990, 15.195, 45.040],
        notes: [
          'Kip je na topografskoj karti JNA 1:25.000 vrh od 578 m kraj ceste Brinje–Krišpolje, kao kota 578 u knjizi. '
            + 'Kote 586 karta JNA nema; nacrtana je na uzvišici uz cestu kilometar severnije, kod Košara.',
          'Gde je cesta prekopana, knjiga ne kaže; nacrtano je ispod Kipa.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.1530, 45.0145], rx: 0.85, ry: 0.42, rot: -62, label: 'II bat.', lp: 'e' },
          { t: 'kota', at: P.kip, label: '578 Kip', lp: 'w' },
          { t: 'kota', at: P.k586, label: '586', lp: 'e', guess: true },
          { t: 'cut', path: [[15.1385, 45.0062], [15.1410, 45.0090], [15.1435, 45.0098]], label: 'prekopana cesta', lp: 'w', guess: true },
        ],
      },
      {
        date: '12. avgusta 1942.', time: '3.00',
        text: 'U 3 sata Kordunaši napadaju Jezerane, a u 3.15 Banijci Krišpolje. Prvi bataljon je u rezervi na '
          + 'raskršću pod Maljenom, a jedna njegova četa na čukama južno od Pernara, prema ustašama u Letincu.',
        notes: ['Odakle su Kordunaši i Banijci napadali sela, knjiga ne kaže.'],
        marks: [
          { t: 'area', side: 'own', at: [15.1530, 45.0145], rx: 0.85, ry: 0.42, rot: -62, label: 'II bat.', lp: 'w' },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.2170, 45.0640], [15.2120, 45.0580], [15.2075, 45.0535]], label: 'III bat.', lp: 'e', at: 0, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.1800, 45.0360], [15.1720, 45.0310], [15.1675, 45.0280]], label: 'IV bat.', lp: 'e', at: 0, guess: true },
          { t: 'area', side: 'friend', at: [15.1900, 45.0430], rx: 0.5, ry: 0.3, label: 'I bat., rezerva', lp: 'e' },
          { t: 'area', side: 'friend', at: [15.1980, 45.0080], rx: 0.35, ry: 0.22, label: 'četa I bat.', lp: 'e' },
          { t: 'kota', at: P.maljen, label: 'Maljen 684', lp: 'n' },
        ],
      },
      {
        date: '12. avgusta 1942.', when: 'istog dana',
        text: 'Italijani iz Brinja, po svom običaju, tuku položaje bataljona artiljerijom sa sigurne daljine. U rejonu '
          + 'Radotići–Holjevac poginu Milan Bjelobaba i Miladin Kotur; sahranjeni su u Vodoteču.',
        view: [15.105, 44.990, 15.195, 45.040],
        notes: ['Gde su stajali topovi, knjiga ne kaže; nacrtani su na ivici Brinja.'],
        marks: [
          { t: 'area', side: 'enemy', at: [15.1255, 44.9975], rx: 0.22, ry: 0.15, label: 'artiljerija', lp: 'w', guess: true },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.1270, 44.9990], [15.1390, 45.0070], [15.1480, 45.0120]] },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.1262, 44.9995], [15.1300, 45.0080], [15.1325, 45.0145]] },
        ],
      },
      {
        date: '12. avgusta 1942.', time: '19.00',
        text: 'Krišpolje pada u 19 sati: Banijci zapale školu, a branioci crkve se predaju; zarobljeno je 45 ustaša, '
          + 'oružnika i domobrana.',
        view: [15.105, 44.990, 15.195, 45.040],
        marks: [
          { t: 'post', at: P.krispolje, label: 'Krišpolje: 45 zarobljenih', lp: 'ne', taken: true, force: 'ndh' },
        ],
      },
      {
        date: '12. ili 13. avgusta 1942.', when: 'posle artiljerijske pripreme',
        text: 'Posle 18.30 predaju se i Jezerane: Kordunaši zapale crkvu, a branioci škole i žandarmerijske stanice se '
          + 'predaju; zarobljeno je 72. U to vreme Italijani iz Brinja posle višesatne artiljerijske pripreme krenu u '
          + 'gustom streljačkom stroju na položaje bataljona. Protivjurišima ih bataljon vraća prema Brinju. Teško je '
          + 'ranjen komandir Druge čete Miloš Đaković; četu preuzima Đurika Potkonjak, njen treći komandir za '
          + 'četrdesetak dana.',
        view: [15.105, 44.990, 15.195, 45.040],
        notes: [
          'Dan nije siguran: knjiga ovaj napad pripoveda posle pada Jezerana i pre 13. avgusta, a Jezerane su, po istoj '
            + 'knjizi, još bile u borbi i 13. avgusta.',
          'Strelice napada i protivnapada su nacrtane cestom iz Brinja; knjiga ne daje pravac.',
        ],
        marks: [
          { t: 'post', at: P.jezerane, label: 'Jezerane: 72 zarobljena', lp: 'ne', taken: true, force: 'ndh' },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.1345, 45.0025], [15.1400, 45.0060], [15.1450, 45.0095]],
            label: 'streljački stroj', lp: 'se', at: 0.3, guess: true },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.1490, 45.0125], [15.1440, 45.0085], [15.1395, 45.0050]], guess: true },
        ],
      },
      {
        date: '13. avgusta 1942.', time: 'oko 17.00',
        text: 'U Brinje stižu sveže italijanske snage iz Primorja i Brloga i napadaju „uz paklenu vatru mitraljeza, '
          + 'topova i minobacača“. Uz bataljon je Brinjski bataljon Pete operativne zone. Posle prvog sudara Italijani '
          + 'odstupe, ali „začudo“ odstupi i Brinjski bataljon; zatim Italijani krenu ponovo, širokim frontom. U pomoć '
          + 'trčeći stižu Banijci iz oslobođenog Krišpolja. Oko 17 sati brza paljba i juriš nateraju Italijane natrag u '
          + 'Brinje.',
        view: [15.105, 44.990, 15.195, 45.040],
        notes: ['Gde je stajao Brinjski bataljon, knjiga ne kaže, samo da je bio uz Drugi.'],
        marks: [
          { t: 'area', side: 'ally', at: [15.1395, 45.0175], rx: 0.4, ry: 0.25, label: 'Brinjski bat.', lp: 'nw', guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.1300, 45.0030], [15.1360, 45.0080], [15.1420, 45.0110]],
            label: 'Italijani iz Primorja', lp: 'sw', at: 0.1, guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.1650, 45.0262], [15.1610, 45.0215], [15.1570, 45.0180]], label: 'IV bat.', lp: 'e', at: 0.2 },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.1480, 45.0120], [15.1410, 45.0070], [15.1350, 45.0030]], guess: true },
        ],
      },
      {
        date: '14. avgusta 1942.', when: 'ujutro',
        text: 'Posle artiljerijske pripreme oko 900 Italijana, s tenkovima, krene prema Krišpolju. Na prekopanom delu '
          + 'ceste tenkovi se okrenu natrag, a za njima žurno i pešadija.',
        view: [15.105, 44.990, 15.195, 45.040],
        marks: [
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.1320, 45.0000], [15.1358, 45.0024], [15.1385, 45.0058]],
            label: 'oko 900 Ital. s tenkovima', lp: 'w', at: 0.2 },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.1370, 45.0060], [15.1335, 45.0025], [15.1300, 44.9995]] },
        ],
      },
    ],
    enemy: [
      'Brinje: oko 500 Italijana i stotinak ustaša, artiljerija; od 13. avgusta sveže snage iz Primorja i Brloga, '
        + '14. avgusta oko 900 vojnika s tenkovima',
      'Jezerane: 120 oružnika u crkvi, žandarmerijskoj stanici i kućama',
      'Krišpolje: 43 oružnika, 13 u crkvi i 30 u školi',
      'Ustaše iz Letinca',
    ],
    friends: [
      'Treći, kordunaški bataljon: napad na Jezerane',
      'Četvrti, banijski bataljon: napad na Krišpolje, pa u pomoć Drugom',
      'Prvi bataljon: rezerva pod Maljenom, četa južno od Pernara',
      'Brinjski bataljon Pete operativne zone (komandant Srđan Uzelac)',
    ],
    result: 'Krišpolje i Jezerane su oslobođeni: zarobljeno je 45 i 72 ustaša, oružnika i domobrana. Italijani nisu '
      + 'prošli. Na položajima jugozapadno od Krišpolja, gde su ih zaustavile čete Prvog i Drugog bataljona, '
      + 'poginula su tri borca, a ranjeno 30, većinom od artiljerije. Brigada je od 12. do 14. avgusta izgubila 17 '
      + 'boraca.',
    fallen: [
      { name: 'Bjelobaba Danin Milan', id: '0002000447' },
      { name: 'Kotur Miladin', id: '0002003675' },
    ],
    wounded: [{ name: 'Đaković Miloš', note: 'komandir Druge čete' }],
    pages: [50, 55],
  },
  {
    key: 'dabar',
    foe: 'ndh',
    region: 'kapela',
    title: 'Oslobođenje Dabra',
    short: 'Dabar',
    dates: '1–3. septembra 1942.',
    start: '1942-09-01', end: '1942-09-03',
    about: 'Dabar, na cesti Otočac–Lička Jesenica, bio je najisturenije ustaško uporište u Kapeli, ostavljeno „kao '
      + 'otok na slobodnom teritoriju“. U njemu je bilo oko 90 ustaša i oružnika, utvrđenih u popovom stanu i oružničkoj '
      + 'stanici na zapadnom ulazu, u bunkeru pod crkvom prema Glibodolu i u opštinskoj zgradi.',
    view: [15.290, 44.940, 15.352, 44.970],
    places: ['Dabar', 'Glibodol', 'Lička Jesenica'],
    base: [
      { t: 'area', side: 'enemy', at: P.dabar, rx: 0.45, ry: 0.28, label: 'Dabar: oko 90 ustaša i oružnika', lp: 's', until: 2 },
      // "bunker s malog uzvišenja ispod crkve": the church's own spot
      { t: 'post', at: P.dabarChurch, label: 'crkva, bunker pod njom', lp: 'n', small: true, until: 3 },
      { t: 'post', at: [15.3040, 44.9546], label: 'popov stan, oružnička stanica', lp: 'w', small: true, guess: true, until: 3 },
      { t: 'post', at: [15.3118, 44.9541], label: 'opštinska zgrada', lp: 'e', small: true, guess: true, until: 3 },
    ],
    steps: [
      {
        date: '1. septembra 1942.', time: '1.00',
        text: 'Bataljoni bez pucnja zaposedaju položaje: 300 boraca Prvog bataljona s jugozapada i zapada, 150 '
          + 'boraca „Pekiše Vuksana“ cestom s istoka, koji ujedno čuvaju pravac prema Jesenici, i 50 boraca otočkog '
          + 'bataljona „Božidar Adžija“ sa severa. Svaki bataljon drži jednu četu u rezervi.',
        notes: [
          'Crkva svetog Mihovila je na OpenStreetMap, a bunker je bio „s malog uzvišenja ispod crkve“; popov stan i '
            + 'oružnička stanica „na zapadnom ulazu“ nacrtani su po opisu, opštinska zgrada usred sela.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.3262, 44.9519], rx: 0.6, ry: 0.28, rot: 0, label: 'II bat., 150', lp: 'n' },
          { t: 'area', side: 'friend', at: [15.3005, 44.9480], rx: 0.6, ry: 0.35, rot: 40, label: 'I bat., 300', lp: 'sw' },
          { t: 'area', side: 'ally', at: [15.3090, 44.9625], rx: 0.45, ry: 0.22, label: '„Božidar Adžija“, 50', lp: 'n' },
          { t: 'move', side: 'own', kind: 'march', path: [[15.3360, 44.9535], [15.3422, 44.9557], [15.3500, 44.9557]], label: 'prema Jesenici', lp: 's', at: 0.7 },
        ],
      },
      {
        date: '1. septembra 1942.', when: 'zatim',
        text: 'Ustaše su usmeno i pismeno pozvane na predaju. Odgovor je bio: „Hrabro udrite, hrabrije ćemo '
          + 'odgovoriti!“',
        marks: [],
      },
      {
        date: '1–3. septembra 1942.', when: 'napad',
        text: 'Delovi „Marka Oreškovića“ napadnu s istočne i zapadne strane i izazovu pometnju. Koristeći je, Prva '
          + 'četa Duje Čubrila i komesara Steve Potkonjaka Mačka u jednom naletu pređe čistinu s južne strane, upadne u '
          + 'selo i preseče ga napola. Grupa „Božidara Adžije“ i krntijaša daskom namazanom blatom spusti do crkve minu '
          + 'od tridesetak kilograma; posle eksplozije ustaše beže iz crkve u bunker, pa u druge utvrđene zgrade.',
        notes: [
          'Knjiga ne kaže čija je bila Prva četa Duje Čubrila. Verovatno Drugog bataljona: Čubrilo je 11. avgusta s '
            + 'njegovim četama zaposeo kote kod Brinja, kasnije je komandovao Drugim bataljonom, a komesar Stevo '
            + 'Potkonjak Mačak i Mirko Čubrilo Žicar su u spisku borci Drugog bataljona.',
          'Dan napada knjiga ne daje: posle odbijene predaje 1. septembra, do kraja 3. septembra ujutro.',
          'Napad delova Prvog bataljona sa zapada je nacrtan kod zapadnog ulaza; napad s istoka knjiga pominje, ali ne kaže odakle, pa nije nacrtan.',
        ],
        marks: [
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.2985, 44.9545], [15.3015, 44.9547], [15.3035, 44.9547]] },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.3200, 44.9500], [15.3150, 44.9515], [15.3110, 44.9538]],
            label: '1/II (D. Čubrilo)', lp: 's', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.3085, 44.9615], [15.3078, 44.9588], [15.3071, 44.9558]], label: 'mina na crkvu', lp: 'w', at: 0.4 },
          { t: 'fight', at: P.dabarChurch },
        ],
      },
      {
        date: '3. septembra 1942.', time: 'oko 5.00',
        text: 'Najteža je borba za opštinsku zgradu. Bombe se vraćaju bombama; posle nekoliko odbijenih juriša Duja '
          + 'Čubrilo iz mrtvog ugla baca boce sa zapaljivom smešom na krov, a ustaše iskaču kroz prozore, ali ne '
          + 'uspevaju da pobegnu. Oko 5 sati otpor je slomljen u svim utvrđenim zgradama.',
        notes: ['Bombe su, po sećanju Duje Čubrila, vraćali on, Branko Pokrajac Jaban i Mirko Čubrilo Žicar.'],
        marks: [
          { t: 'post', at: P.dabar, label: 'Dabar: 32 zarobljena', lp: 's', taken: true },
        ],
      },
    ],
    enemy: [
      'Oko 90 ustaša i oružnika, s mesnom milicijom',
      'Utvrđeni popov stan i oružnička stanica na zapadnom ulazu, bunker pod crkvom prema Glibodolu, opštinska zgrada',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: 300 boraca',
      'Otočki partizanski bataljon „Božidar Adžija“: 50 boraca',
    ],
    result: 'Dabar je oslobođen: 10 ustaša i oružnika je poginulo, 32 su zarobljena, a petorica su se 4. i 5. '
      + 'septembra sama javila. Iz brigade je ranjeno 8 boraca. Slobodna teritorija spojila se od Jezerana i Letinca '
      + 'do pruge, a brigada je dobila bazu za akcije na pruzi u Kapeli.',
    pages: [65, 67],
  },
  {
    key: 'rusenje-pruge',
    foe: 'it',
    region: 'kapela',
    title: 'Generalno rušenje pruge',
    short: 'Rušenje pruge',
    dates: '6–7. septembra 1942.',
    start: '1942-09-06', end: '1942-09-07',
    about: 'Šest bataljona, tri kordunaška i Prvi, Drugi i Četvrti bataljon brigade, napadaju istog dana kapelsku '
      + 'prugu, da je ovog puta poruše „temeljito tako da se saobraćaj preko Kapele zbilja onemogući“. Drugi '
      + 'bataljon ne napada kao celina: dve njegove čete nastupaju s Kordunašima, kod stanica Jesenica i Javornik.',
    view: [15.400, 44.862, 15.512, 44.995],
    places: ['Lička Jesenica', 'Blata', 'Rudopolje', 'Dugi Dol'],
    base: [
      { t: 'area', side: 'enemy', at: P.jesenicaSt, rx: 0.32, ry: 0.2, rot: -35, label: 'stanica Jesenica: Italijani', lp: 'se' },
      { t: 'area', side: 'enemy', at: P.javornikSt, rx: 0.28, ry: 0.18, label: 'Javornik: bunkeri i žica', lp: 'e' },
      { t: 'area', side: 'enemy', at: P.rudopoljeSt, rx: 0.3, ry: 0.2, label: 'Rudopolje: Italijani', lp: 'e' },
      { t: 'area', side: 'enemy', at: P.blataSt, rx: 0.25, ry: 0.17, label: 'Blata: Italijani', lp: 'e' },
      { t: 'post', at: P.vakt33, label: 'vaktarnica 33', lp: 'e', small: true, guess: true, until: 2 },
    ],
    steps: [
      {
        date: '6. septembra 1942.', time: 'do 13.00',
        text: 'Do 13 sati svih šest bataljona zaposeda položaje za napad. Jedna četa Drugog bataljona pripojena je '
          + 'Udarnom bataljonu Drugog kordunaškog odreda, koji se neprimetno privlači stanici Jesenica, da napadne iz '
          + 'neposredne blizine. Još jedna četa je s tri čete Drugog udarnog kordunaškog bataljona pred malom stanicom '
          + 'Javornik. „Marko Orešković“ je južnije, prema Rudopolju.',
        notes: [
          'Koje su čete bile kod koje stanice, knjiga ne kaže, a ni gde su bili treća četa i štab bataljona.',
          'Knjiga na jednom mestu kaže da su dve čete „Pekiše Vuksana“ nastupale s Udarnim bataljonom i s Četvrtim '
            + 'bataljonom brigade, a na drugom da je četa kod Javornika bila s Drugim udarnim kordunaškim bataljonom. '
            + 'Gde je bio Četvrti bataljon, ne kaže, pa nije nacrtan.',
          'Položaji kod stanica nacrtani su na strani odakle je brigada dolazila, od Dabra. Vaktarnica br. 33 nacrtana '
            + 'je južno od Javornika, jer je na nju naišao oklopni voz od Rudopolja; tačno mesto knjiga ne daje.',
        ],
        marks: [
          { t: 'area', side: 'ally', at: [15.4222, 44.9802], rx: 0.5, ry: 0.28, rot: -30, label: 'Udarni bat. 2. kord. odreda', lp: 'w', guess: true },
          { t: 'area', side: 'own', id: 'jesenica', at: [15.4250, 44.9766], rx: 0.22, ry: 0.14, label: 'četa II bat.', lp: 's', guess: true },
          { t: 'area', side: 'ally', at: [15.4528, 44.9290], rx: 0.42, ry: 0.24, label: 'II udarni kord. bat.', lp: 'w', guess: true },
          { t: 'area', side: 'own', id: 'javornik', at: [15.4553, 44.9246], rx: 0.22, ry: 0.14, label: 'četa II bat.', lp: 'sw', guess: true },
          { t: 'area', side: 'friend', at: [15.4625, 44.9050], rx: 0.38, ry: 0.2, rot: -35, label: 'I bat.', lp: 'w', guess: true },
        ],
      },
      {
        date: '6. septembra 1942.', time: '15.00',
        view: [15.412, 44.966, 15.446, 44.990],
        text: 'Znak za opšti napad daje Udarni bataljon, kome je pripojena četa „Pekiše Vuksana“. Iznenađenje je '
          + 'postignuto: u prvom naletu zauzeti su jedna vaktarnica i dva bunkera sa 8 Italijana. Stanica ipak nije '
          + 'osvojena; ranjeno je 14 boraca i komandant Udarnog bataljona Nikola Basara. Kod Javornika napad u '
          + 'predviđeno vreme nije izveden: stanicu brane dvospratni bunkeri i ograda od žice, a šuma oko nje je posečena.',
        notes: ['Gde su bili vaktarnica i bunkeri, knjiga ne kaže; nacrtani su kraj stanice.'],
        marks: [
          { t: 'move', side: 'ally', kind: 'attack', path: [[15.4230, 44.9797], [15.4256, 44.9788], [15.4278, 44.9781]] },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.4255, 44.9764], [15.4272, 44.9768], [15.4286, 44.9773]] },
          { t: 'post', at: [15.4268, 44.9799], label: 'vaktarnica i 2 bunkera: 8 zarobljenih', lp: 'ne', taken: true, small: true, guess: true },
          { t: 'fight', at: [15.4295, 44.9778] },
        ],
      },
      {
        date: '6. septembra 1942.', when: 'istog dana',
        view: [15.455, 44.888, 15.489, 44.912],
        text: 'Južnije, „Marko Orešković“ silovitim naletom zauzme vaktarnicu br. 33 i zarobi 16 Italijana, pa se '
          + 'rasporedi u šumi na strmini nad prugom. Od Rudopolja naiđe oklopni voz, ali stane ispred zasede; Italijani '
          + 'iz njega krenu u streljačkom stroju prema vaktarnici, a voz lagano mili za njima. Kad uđu u usek, dočeka ih '
          + 'unakrsna vatra; ostali se daju u paničan beg.',
        notes: [
          'Ovo je borba Prvog bataljona; Drugi u njoj nije bio. Knjiga je pripoveda uz napad 6. septembra, bez sata.',
          'Mesto useka i mesto gde je voz stao nisu zapisani.',
        ],
        marks: [
          { t: 'post', at: P.vakt33, label: 'vaktarnica 33: 16 zarobljenih', lp: 'w', taken: true, small: true, guess: true },
          { t: 'area', side: 'friend', at: [15.4628, 44.9022], rx: 0.38, ry: 0.2, rot: -35, label: 'I bat.', lp: 'w', guess: true },
          { t: 'train', at: [15.4795, 44.8963], label: 'oklopni voz iz Rudopolja', lp: 'e', armoured: true, guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.4778, 44.8974], [15.4732, 44.8992], [15.4690, 44.9016]], label: 'streljački stroj', lp: 's', at: 0.3 },
          { t: 'move', side: 'friend', kind: 'fire', path: [[15.4648, 44.9002], [15.4683, 44.9010]] },
          { t: 'move', side: 'friend', kind: 'fire', path: [[15.4712, 44.9042], [15.4702, 44.9022]] },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.4712, 44.8994], [15.4752, 44.8975], [15.4805, 44.8952]], label: 'paničan beg', lp: 'se', at: 0.6 },
        ],
      },
      {
        date: '6. septembra 1942.', when: 'čim je pao mrak',
        view: [15.440, 44.914, 15.478, 44.938],
        text: 'Kod Javornika se napada čim padne mrak, ali se ne može napredovati: vatra je vrlo jaka, a Italijani su dan '
          + 'pre napada dobili četiri bacača mina, kojima neprestano gađaju. Bataljon se povuče malo dalje od stanice i '
          + 'blokira je, „ne dajući neprijatelju mogućnost da ometa rušenje pruge“.',
        notes: [
          'Knjiga kaže samo „bataljon“: Kordunaše, s kojima je bila četa „Pekiše Vuksana“.',
          'Koliko su se povukli od stanice, knjiga ne kaže.',
        ],
        marks: [
          { t: 'move', side: 'ally', kind: 'stopped', path: [[15.4532, 44.9288], [15.4560, 44.9276], [15.4580, 44.9267]] },
          { t: 'move', side: 'own', kind: 'stopped', path: [[15.4556, 44.9246], [15.4572, 44.9252], [15.4585, 44.9257]] },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.4602, 44.9262], [15.4566, 44.9275]] },
          { t: 'area', side: 'ally', at: [15.4500, 44.9302], rx: 0.42, ry: 0.24, label: 'II udarni kord. bat.', lp: 'w', guess: true },
          { t: 'area', side: 'own', id: 'javornik', at: [15.4528, 44.9238], rx: 0.22, ry: 0.14, label: 'četa II bat.', lp: 'sw', guess: true },
        ],
      },
      {
        date: '7. septembra 1942.', when: 'drugog dana uveče',
        text: 'Italijani tuku artiljerijom i bacačima od Blata i iz sela Jesenice, a drugog dana uveče prikupe veće snage '
          + 'i dovuku tri brdska topa; prikupljaju se i od Rudopolja. „Pekiša Vuksan“ je zarobio jednog Italijana, koji '
          + 'je s karabinom i opremom pobegao sa stanice Jesenica.',
        notes: [
          'Gde su se prikupljale veće snage, knjiga ne kaže; nacrtane su kod stanice Jesenica, gde je bila borba.',
          'Kad je zarobljen Italijan sa stanice, knjiga ne kaže.',
          'Koji je deo pruge porušen, knjiga ne kaže, pa nije nacrtan.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.4008, 45.0300], [15.4090, 45.0060], [15.4195, 44.9835]], label: 'od Blata', lp: 'w', at: 0.3 },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.4410, 44.9950], [15.4330, 44.9872], [15.4262, 44.9812]], label: 'iz Jesenice', lp: 'e', at: 0.3 },
          { t: 'area', side: 'enemy', at: [15.4385, 44.9712], rx: 0.45, ry: 0.25, label: 'veće snage, 3 brdska topa', lp: 'se', guess: true },
          { t: 'move', side: 'enemy', kind: 'march', path: [[15.4872, 44.8710], [15.4835, 44.8890], [15.4730, 44.8992]], label: 'od Rudopolja', lp: 'e', at: 0.4, guess: true },
        ],
      },
    ],
    enemy: [
      '74. pešadijski puk divizije „Lombardia“ i eskadron „Genova cavalleria“',
      'Stanica Javornik: dvospratni bunkeri, žica, posečena šuma; dan pre napada stigla su četiri bacača mina',
      'Oklopni voz iz Rudopolja',
      'Drugog dana veće snage i tri brdska topa',
    ],
    friends: [
      'Udarni bataljon Drugog kordunaškog odreda (komandant Nikola Basara): stanica Jesenica',
      'Drugi udarni kordunaški bataljon, tri čete: stanica Javornik',
      'Prvi bataljon „Marko Orešković“: vaktarnica br. 33',
      'Četvrti, banijski bataljon',
      'Odredski bataljon iz Kunić-Sela: radne grupe, pruga severno i južno od Plaškog',
    ],
    result: 'Stanice Jesenica i Javornik nisu osvojene, ali je pruga preko Kapele zadugo ostala van saobraćaja: po '
      + 'ustaškom izveštaju pisanom deset dana kasnije, „pruga se popravlja, ali će promet biti više dana obustavljen“. '
      + 'Zarobljeno je 25 Italijana: osam Kordunaši, šesnaest „Marko Orešković“ i jednog „Pekiša Vuksan“.',
    pages: [68, 70],
  },
  {
    key: 'kosinj',
    foe: 'ndh',
    region: 'kosinj',
    title: 'Kosinjski Bakovac',
    short: 'Kosinj',
    dates: '20–21. septembra 1942.',
    start: '1942-09-20', end: '1942-09-21',
    about: 'Prva i Druga lička brigada napadaju ustaše, domobrane i četnike u kosinjskim selima pod Velebitom. '
      + 'Drugi bataljon, kome od 15. septembra komanduje inž. Mićo Jović, ima najduži put: obilaznim maršem do '
      + 'polaznih položaja pred Kosinjskim Ribnikom i Bakovcem, desetak kilometara zapadno od Gornjeg Kosinja.',
    view: [15.185, 44.668, 15.335, 44.760],
    places: ['Bakovac Kosinjski', 'Antinovica', 'Gornji Kosinj', 'Podjelar', 'Krš', 'Lipovo Polje', 'Kruščica', 'Sušanj', 'Vukelići', 'Poljan', 'Donji Kosinj'],
    base: [
      { t: 'area', side: 'enemy', at: K.gornjiKosinj, rx: 0.55, ry: 0.35, label: 'Kosinj: ustaše, oružnici, milicija', lp: 'e', until: 3 },
      { t: 'area', side: 'enemy', at: K.bakovac, rx: 0.4, ry: 0.28, label: 'Bakovac: ustaše', lp: 'n', until: 2 },
      { t: 'area', side: 'enemy', at: K.lipovoPolje, rx: 0.4, ry: 0.28, label: 'Lipovo Polje: oko 50 četnika', lp: 'n' },
    ],
    steps: [
      {
        date: '20–21. septembra 1942.', when: 'noću',
        text: 'Od jedinica brigade prvi kreće „Pekiša Vuksan“: do polaznih položaja, koje treba zaposesti do 9 sati, ima '
          + 'dvadesetak kilometara po teško prohodnom terenu, i bataljon je u pokretu nešto duže od 13 sati. „Marko '
          + 'Orešković“ napada južno od Gornjeg Kosinja, Dulibu, Kruščicu, Poljanak i Sušanj; čete Četvrtog bataljona '
          + 'podeljene su između njega i Druge ličke, a jedna ostaje u Poljanu, u rezervi.',
        notes: [
          'Odakle je bataljon krenuo, knjiga ne kaže; brigada je pre akcije bila u rejonu Krša.',
          'Put je nacrtan približno, kao obilazak s juga, jer su čete izbile na južne i jugozapadne prilaze Bakovcu; '
            + 'knjiga ga ne opisuje.',
          'Kosinjski Ribnik je u GeoNames selo Ribnik, kraj Bakovca; OpenStreetMap ga nema.',
          'Duliba je na topografskoj karti JNA 1:25.000 krčevina zapadno od Kruščice (732 m); Poljanak je zaselak '
            + 'Poljanka kraj Sušnja, a Vukelić-Selo zaselak Vukelići između Gornjeg i Donjeg Kosinja.',
          'Puteve Prvog bataljona i jedinica Druge ličke knjiga ne daje; nacrtani su približno, kao i mesta četa '
            + 'Četvrtog bataljona, koje su išle s Prvim bataljonom i s Četvrtim bataljonom Druge ličke.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'march', path: [K.krs, [15.3100, 44.7150], [15.2950, 44.6990], [15.2780, 44.6850],
            [15.2600, 44.6850], [15.2450, 44.6880], K.antinovica, [15.2380, 44.6975], [15.2250, 44.7010], [15.2130, 44.7030]],
            label: 'II bat.', lp: 's', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.3150, 44.7260], [15.3030, 44.7080], [15.2900, 44.6900],
            [15.2750, 44.6720], [15.2580, 44.6680], K.duliba], label: 'I bat. s četama IV bat.', lp: 'e', at: 0.55, guess: true },
          { t: 'move', side: 'ally', kind: 'attack', path: [[15.2950, 44.7570], [15.2820, 44.7500], [15.2720, 44.7455]],
            label: '4. bat. 2. ličke i čete IV bat.', lp: 'w', at: 0.6, guess: true },
          { t: 'area', side: 'friend', at: K.poljan, rx: 0.3, ry: 0.2, label: 'četa IV bat., rezerva', lp: 'e' },
        ],
      },
      {
        date: '21. septembra 1942.', when: 'na maršu',
        view: [15.175, 44.660, 15.270, 44.745],
        text: 'Prvi okršaj bataljon ima u selu Antinovcu, gde zarobi neprijateljsku stražu. Na obilaznom maršu prema '
          + 'Kosinjskom Bakovcu savlada i stražu kod Velikog vrha.',
        notes: [
          'Antinovac je ovde zaselak Antinovica (OpenStreetMap i karta JNA), jedino tako nazvano mesto blizu Bakovca.',
          'Veliki vrh je vrh od 910 m između Antinovice i Kruščice (i na karti JNA). Put je nacrtan od Antinovice '
            + 'zapadnom stranom Velikog vrha prema Bakovcu, pa su okršaji redom kao u knjizi.',
          'Odakle je bataljon „Ognjen Prica“ obišao Bakovac, knjiga ne kaže; po planu je Druga lička išla „iz '
            + 'podvelebitskih vrleti“.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'march', path: [[15.2600, 44.6850], [15.2450, 44.6880], K.antinovica, [15.2380, 44.6975],
            [15.2250, 44.7010], [15.2130, 44.7030]], label: 'II bat.', lp: 's', at: 0.15, guess: true },
          { t: 'post', at: K.antinovica, label: 'straža u Antinovcu', lp: 's', taken: true, small: true, guess: true },
          { t: 'post', at: [15.2395, 44.6978], label: 'straža kod Velikog vrha', lp: 'e', taken: true, small: true, guess: true },
          { t: 'kota', at: K.velikiVrh, label: '910 Veliki vrh', lp: 'e' },
          { t: 'area', side: 'friend', at: K.duliba, rx: 0.4, ry: 0.25, label: 'I bat., polazni položaj', lp: 'w', guess: true, until: 3 },
          { t: 'move', side: 'ally', kind: 'march', path: [[15.1760, 44.7470], [15.1880, 44.7380], [15.2000, 44.7262]],
            label: 'bat. „Ognjen Prica“', lp: 'w', at: 0.3, guess: true },
        ],
      },
      {
        date: '21. septembra 1942.', time: '9.15',
        view: [15.180, 44.690, 15.262, 44.730],
        text: 'Petnaest minuta posle roka dve čete zaposednu položaje na južnim i jugozapadnim prilazima Bakovcu, a '
          + 'Treća četa izbija na severne prilaze, da sačeka bataljon „Ognjen Prica“ Druge ličke. Kad taj bataljon upadne '
          + 'u Bakovac, priključi mu se i Treća četa Mile Počuče. Neprijatelj se iz sela povuče na obližnja brda, kote 788 '
          + 'i 894, i odatle pruža jak otpor: bataljonu je sprečen brz prodor na istok, prema Kosinju.',
        notes: [
          'Mesta četa knjiga daje samo kao prilaze selu.',
          'Kote knjiga ne smešta. Na topografskoj karti JNA 1:25.000 kota 788 je Brneci vršak, severozapadno od sela, '
            + 'a kota 894 vis od 891 m severoistočno od njega, nad cestom prema Gornjem Kosinju.',
          'Odakle je naišao bataljon „Ognjen Prica“, knjiga ne kaže.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.2085, 44.7040], rx: 0.5, ry: 0.25, rot: -30, label: 'dve čete II bat.', lp: 'sw', guess: true },
          { t: 'area', side: 'own', at: [15.2125, 44.7172], rx: 0.3, ry: 0.18, label: '3/II (M. Počuča)', lp: 'n', guess: true },
          { t: 'move', side: 'ally', kind: 'attack', path: [[15.2000, 44.7262], [15.2060, 44.7190], [15.2110, 44.7130]],
            label: 'bat. „Ognjen Prica“', lp: 'w', at: 0.2, guess: true },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.2060, 44.7115], [15.1960, 44.7150], K.k788], guess: true },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.2140, 44.7110], [15.2200, 44.7140], K.k894], guess: true },
          { t: 'kota', at: K.k788, label: '788 Brneci vršak', lp: 'w' },
          { t: 'kota', at: K.k894, label: '894', lp: 'e' },
          { t: 'area', side: 'enemy', at: K.k788, rx: 0.35, ry: 0.22, label: 'ustaše', lp: 'n', id: 'k788' },
          { t: 'area', side: 'enemy', at: K.k894, rx: 0.35, ry: 0.22, label: 'ustaše', lp: 'n', id: 'k894' },
          { t: 'move', side: 'enemy', kind: 'fire', path: [K.k894, [15.2180, 44.7110], [15.2110, 44.7060]], guess: true },
        ],
      },
      {
        date: '21. septembra 1942.', time: 'do 18.30',
        text: 'Prvi bataljon je u 9 sati pred Kruščicom, gde Vujo Miljuš mitraljeskim rafalom pokosi četvoricu ustaša, '
          + 'pa čisti Podjelar. Uspaničen neprijatelj beži na sve strane, i Prvi bataljon u 18.30, bez većih okršaja, '
          + 'ulazi u Kosinj; na brdima oko njega uhvaćeno je šest velikih ustaških zastava. Neprijatelj iz Bakovca se '
          + 'izvukao bez većih gubitaka; komandant brigade za to je okrivio bataljon „Ognjen Prica“, „koji nije zaposjeo '
          + 'svoje određene položaje“.',
        marks: [
          { t: 'move', side: 'friend', kind: 'attack', path: [K.duliba, K.kruscica, K.poljanka, K.susanj, K.podjelar, [15.2740, 44.7152]],
            label: 'I bat.', lp: 'e', at: 0.25 },
          { t: 'fight', at: K.kruscica },
          { t: 'post', at: K.gornjiKosinj, label: 'Kosinj, 18.30', lp: 'e', taken: true },
        ],
      },
    ],
    enemy: [
      'Po velikom županu oko 600 naoružanih oružnika, ustaša i milicionera, s mitraljezima i minobacačima; štab je '
        + 'računao sa 100 ustaša i 270 domobrana',
      'Lička bojna ustaškog bojnika Ivana Devčića Pivca i delovi drugih bojni',
      'U Lipovom Polju oko 50 četnika',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: Duliba, Kruščica, Poljanak, Sušanj, Podjelar, Kosinj',
      'Četvrti, banijski bataljon: čete uz Prvi bataljon i Drugu ličku, jedna u rezervi u Poljanu',
      'Druga lička brigada: bataljon „Ognjen Prica“ na Bakovac, njen Četvrti bataljon na Vukelić-Selo',
      'Bataljon „Matija Gubec“ Četvrtog ličkog odreda: grupe od 10 do 12 boraca, kao vodiči',
    ],
    result: 'Kosinj je zauzet, ali je „skoro svim ustaškim i četničkim banditima“ uspelo da umaknu. Brigada je imala '
      + 'jednog poginulog i četiri lakše ranjena, Druga lička 7 poginulih i 25 ranjenih. Napad je uznemirio sve okolne '
      + 'garnizone: već sutradan su u Perušić stigla tri italijanska pešadijska puka.',
    pages: [84, 87],
  },
  {
    key: 'pazarista',
    foe: 'ndh',
    region: 'kosinj',
    title: 'Pazarišta',
    short: 'Pazarišta',
    dates: '26. septembra – 1. oktobra 1942.',
    start: '1942-09-26', end: '1942-10-01',
    about: 'Pazarišta su na pola puta od Kosinja do Gospića, razvučena u dolini Pazarišnice. Ustaški bojnik Rogoz '
      + 'rasporedio je ustaše i miliciju po visovima severno od doline, od Metlače nad Klancem prema zapadu. Brigada '
      + 'ih napada s tri bataljona koja su s njom: Prvim, Drugim i Četvrtim.',
    view: [15.240, 44.600, 15.335, 44.715],
    places: ['Klanac', 'Kaluđerovac', 'Vaganac', 'Oteš', 'Kruščica', 'Sušanj', 'Predvaganac', 'Klanačko Polje'],
    base: [
      { t: 'area', side: 'enemy', at: K.klanac, rx: 0.6, ry: 0.35, label: 'Klanac: 150 ustaša i oružnika, 300 milicionera', lp: 's', until: 3 },
      { t: 'area', side: 'enemy', at: K.kaludjerovac, rx: 0.35, ry: 0.22, label: 'Kaluđerovac: satnik Tatek', lp: 'e', until: 3 },
      { t: 'kota', at: K.metlaca, label: 'Metlača', lp: 'e' },
    ],
    steps: [
      {
        date: '26. septembra 1942.', when: 'prvi napad',
        text: 'Brigada pokušava da preko Kaluđerovca, koji drži mešovita jedinica satnika Tateka, prodre na Klanac, gde '
          + 'su ustaše bojnika Pivca. Napad je odbijen.',
        notes: [
          'Koji je bataljon napadao gde, knjiga ne kaže; strelica je cela brigada.',
          'Odakle je brigada krenula, knjiga ne kaže; strelica dolazi sa severa.',
        ],
        marks: [
          { t: 'move', side: 'friend', kind: 'stopped', path: [[15.2950, 44.6900], [15.3060, 44.6700], [15.3100, 44.6585]],
            label: 'brigada', lp: 'w', at: 0.3, guess: true },
        ],
      },
      {
        date: '27. septembra 1942.', when: 'sutradan',
        text: 'Napad se obnavlja, ali iz Gospića stiže pojačanje, i ustaše „su dali žestok otpor na položajima koji '
          + 'dominiraju Klancem“.',
        notes: ['Pojačanje je nacrtano s juga, od Gospića; put mu knjiga ne daje.'],
        marks: [
          { t: 'move', side: 'friend', kind: 'stopped', path: [[15.2950, 44.6900], [15.3060, 44.6700], [15.3092, 44.6598]], guess: true },
          { t: 'move', side: 'enemy', kind: 'march', path: [[15.3300, 44.6030], [15.3120, 44.6200], [15.3010, 44.6290]],
            label: 'pojačanje iz Gospića', lp: 'e', at: 0.3, guess: true },
        ],
      },
      {
        date: '30. septembra 1942.', when: 'noću, na 1. oktobar',
        text: 'Treći napad izvode obe brigade. Tri bataljona Prve kreću od Sušnja, Babinog brda i Kruščice i napadaju '
          + 'preko Vaganca i Oteša na Klanac; Druga lička, od Antinovca, Bakovca i Kruščice, napada takođe na Klanac, '
          + 'preko Kaluđerovca i mosta na Lici.',
        notes: [
          'Koji je bataljon krenuo odakle, knjiga ne kaže, pa nijedna strelica nije označena kao Drugi bataljon.',
          'Babino brdo nije pronađeno na kartama, ni na topografskoj karti JNA; nacrtan je put od Sušnja i od Kruščice.',
          'Putevi su približni: knjiga daje samo mesta kroz koja su išli.',
        ],
        marks: [
          { t: 'move', side: 'friend', kind: 'attack', path: [K.susanj, [15.2700, 44.6800], K.vaganac, [15.2700, 44.6300], K.otes,
            [15.2900, 44.6285]], label: 'I, II i IV bat.', lp: 'w', at: 0.45, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [K.kruscica, [15.2630, 44.6630], K.vaganac], guess: true },
          { t: 'move', side: 'ally', kind: 'attack', path: [[15.2950, 44.6800], K.kaludjerovac, [15.3050, 44.6420], [15.3005, 44.6350]],
            label: '2. lička br.', lp: 'e', at: 0.3, guess: true },
        ],
      },
      {
        date: '1. oktobra 1942.', when: 'do večeri',
        text: 'Borba traje do večeri; neprijatelj „davao je žestok otpor“, i „veliki broj bandita uspio je pobjeći“. '
          + 'Zarobljeno je 65, od kojih je 20 ustaša streljano, a ostali su pušteni; mrtvih je 33. Prva brigada ima dva '
          + 'teško ranjena; obojica, Vukašin Budimirović i prvi intendant Drugog bataljona Dušan Pavlica, umiru posle dva dana.',
        notes: ['U spisku boraca brigade Pavlica je poginuo 1. oktobra u Kruščici.'],
        marks: [
          { t: 'post', at: K.klanac, label: 'Pazarišta: 65 zarobljenih', lp: 's', taken: true },
          { t: 'fight', at: [15.2928, 44.6378] },
        ],
      },
    ],
    enemy: [
      'Bojnik Rogoz: 150 ustaša i oružnika i oko 300 ustaških milicionera',
      'Mešovita jedinica satnika Tateka na Kaluđerovcu, ustaše bojnika Pivca na Klancu',
      'Pojačanje iz Gospića, od 27. septembra',
    ],
    friends: [
      'Prvi, Drugi i Četvrti bataljon brigade; Treći je bio u otočkom kotaru',
      'Druga lička brigada: 3 poginula i 13 ranjenih',
    ],
    result: 'Pazarišta su oslobođena, ali od 500 neprijateljskih vojnika „nije se uspjelo pohvatati ili likvidirati '
      + 'niti jedna četvrtina“. Zaplenjena su 3 mitraljeza, protivoklopni mitraljez, 3 minobacača, 4 puškomitraljeza, '
      + 'automat i 100 pušaka. Okružni komitet je kasnije zapazio da se raspoloženje u hrvatskim selima zapadne Like '
      + '„poboljšalo u našu korist“.',
    fallen: [{ name: 'Pavlica Petra Dušan', id: '0002006192', note: 'prvi intendant bataljona, umro od rana' }],
    pages: [88, 90],
  },
  {
    key: 'glina',
    foe: 'ndh',
    region: 'glina',
    title: 'Napad na Glinu',
    short: 'Glina',
    dates: '21–23. oktobra 1942.',
    start: '1942-10-21', end: '1942-10-23',
    about: 'Četiri brigade, Prva, Sedma i Osma banijska i Peta kordunaška, pod Operativnim štabom Glavnog štaba '
      + 'Hrvatske, napadaju ustaško-domobranski garnizon u Glini. Glavni štab je verovao da domobrani samo čekaju '
      + 'priliku da se predaju, a garnizon je od svog obaveštajca znao kada će napad biti i s kakvim snagama.',
    view: [16.050, 45.220, 16.250, 45.360],
    places: ['Glina', 'Jukinac', 'Crni Lug', 'Majske Poljane', 'Prekopa', 'Drenovac Banski', 'Donji Klasnić', 'Rudići', 'Majski Trtnik', 'Ravno Rašće',
      'Roviška', 'Gređani', 'Hrastovica', 'Graberje', 'Trtnik Glinski'],
    base: [
      { t: 'area', side: 'enemy', at: G.glina, rx: 0.75, ry: 0.5, label: 'Glina: oko 650 ustaša i domobrana', lp: 'w', until: 2 },
      { t: 'post', at: G.kozarica, label: 'Kozarica', lp: 'w', small: true },
      { t: 'post', at: G.battery, label: 'baterija kod klaonice', lp: 'ne', small: true, guess: true },
    ],
    steps: [
      {
        date: '21. oktobra 1942.', when: 'dan pred napad',
        view: [15.950, 45.220, 16.300, 45.425],
        text: 'Brigada je u Klasniću, 18 km jugoistočno od Gline, kad Operativni štab izda zapovest: Treći bataljon da '
          + 'zauzme uporište na Kozarici i železničku stanicu, Prvi i Drugi da se od Majskih Poljana probiju preko potoka '
          + 'Maje, osvoje bateriju kod klaonice i prodru u centar grada. Četvrti, banijski bataljon, jedini čiji borci '
          + 'dobro znaju Glinu, ostaje na osiguranju ceste Petrinja–Glina. Deo Sedme banijske je kod Gređana, prema '
          + 'Topuskom, Osma zatvara prilaze od Gore, a Peta kordunaška je prema Hrastovici i Cepelištu.',
        notes: [
          'Gde su bile klaonica i baterija, knjiga ne kaže; nacrtane su na istočnoj strani grada, odakle je napadao '
            + 'Prvi bataljon.',
          'Kozarica je brdo od 184 m južno od grada (OpenStreetMap).',
        ],
        marks: [
          { t: 'area', side: 'own', at: G.klasnic, rx: 0.7, ry: 0.4, label: 'II bat., s brigadom', lp: 'e' },
          { t: 'area', side: 'ally', at: G.gredjani, rx: 0.5, ry: 0.3, label: 'deo 7. banijske br.', lp: 's', guess: true, until: 2 },
          { t: 'area', side: 'ally', at: [16.1950, 45.4120], rx: 0.6, ry: 0.3, label: '8. banijska br.', lp: 'e', guess: true, until: 2 },
          { t: 'area', side: 'ally', at: [16.2620, 45.3880], rx: 0.5, ry: 0.3, label: '5. kordunaška br.', lp: 's', guess: true, until: 2 },
          { t: 'area', side: 'enemy', at: G.hrastovica, rx: 0.35, ry: 0.22, label: 'Hrastovica', lp: 'n' },
        ],
      },
      {
        date: '22. oktobra 1942.', when: 'dvadesetak sati pred napad',
        view: [16.080, 45.225, 16.250, 45.350],
        text: 'Brigada se pomera desetak kilometara na sever, u Drenovac na Bručini, a odatle polazi na položaje preko '
          + 'Majskog Trtnika, Ravnog Rašća, Roviške, Crnog Luga i Maje. Popodne počne snažan pljusak; potok Maja postaje '
          + 'bujica, i nijedan bataljon nije na polaznim položajima u dogovoreno vreme, u 24 sata.',
        notes: ['Put je nacrtan kroz mesta koja knjiga navodi; Crni Lug je selo Crni Lug Glinski jugoistočno od Gline '
          + '(topografska karta JNA 1:25.000).'],
        marks: [
          { t: 'move', side: 'own', kind: 'march', path: [G.klasnic, [16.2050, 45.2700], G.drenovac], label: 'brigada', lp: 'e', at: 0.5, guess: true },
          { t: 'move', side: 'own', kind: 'march', path: [G.drenovac, [16.1900, 45.2965], G.majskiTrtnik, G.ravnoRasce, G.roviska,
            G.crniLug, [16.1160, 45.3385]], at: 0.55, guess: true },
          { t: 'area', side: 'own', at: [16.1160, 45.3395], rx: 0.4, ry: 0.22, label: 'II bat.', lp: 'e', guess: true },
        ],
      },
      {
        date: '23. oktobra 1942.', time: '1.45',
        view: [16.066, 45.316, 16.134, 45.370],
        text: 'Napad počinje u 1.45 umesto u ponoć. Bataljoni bez žrtava pređu Maju, mnogi borci preplivavajući je. '
          + '„Marko Orešković“ nastupa preko Jukinačkog mosta na bateriju, a „Pekiša Vuksan“, desno od njega, prema '
          + 'centru grada: od železničke stanice prema crkvi, desnim krilom povezan s delovima Sedme banijske. Treći '
          + 'bataljon napada Kozaricu i blokira stanicu; dva bataljona Sedme banijske prodiru od Jukinca u severni deo grada.',
        notes: [
          'Knjiga napad Drugog bataljona opisuje dvojako: desno od Prvog, koji je išao preko Jukinačkog mosta, i od '
            + 'železničke stanice prema crkvi. Strelica je nacrtana po drugom opisu.',
          'Crkva je ovde katolička crkva svetog Ivana Nepomuka (OpenStreetMap); knjiga ne kaže koja.',
          'Jukinac je severoistočni deo Gline (karta JNA 1:25.000); Jukinački most je nacrtan gde cesta iz Jukinca '
            + 'prelazi Maju. Po ustaškom izveštaju, krntijaši su napali istočni deo mesta.',
          'Raspored neprijatelja u gradu knjiga daje ukratko: oko 3 satnije u rovovima oko Gline, 2 satnije, oko 50 '
            + 'ustaša i 30 žandara u samom gradu, utvrđene zgrade oko Jukinačkog mosta, oružnička postaja i baterija na '
            + 'istoku. Mesta su procena; ulica kojom je išao Drugi bataljon ostavljena je prazna, jer u njoj „većinom '
            + 'neprijatelja nije ni bilo“.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'attack', path: [[16.1140, 45.3392], [16.1040, 45.3335], [16.0948, 45.3322], [16.0908, 45.3400]], guess: true },
          { t: 'area', side: 'own', at: [16.0928, 45.3352], rx: 0.17, ry: 0.11, label: 'II bat.', lp: 'e', guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[16.1170, 45.3478], G.jukinacMost, [16.1045, 45.3440], [16.1008, 45.3408]],
            label: 'I bat.', lp: 'e', at: 0.2, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[16.1000, 45.3212], [16.0900, 45.3222], [16.0838, 45.3244]],
            label: 'III bat.', lp: 's', at: 0.4, guess: true },
          { t: 'move', side: 'ally', kind: 'attack', path: [[16.1062, 45.3560], [16.0990, 45.3500], [16.0932, 45.3446]],
            label: '7. banijska br.', lp: 'e', at: 0.2, guess: true },
          { t: 'area', side: 'friend', at: [16.1150, 45.3618], rx: 0.5, ry: 0.25, label: 'IV bat., osiguranje', lp: 'w', guess: true, until: 4 },
          { t: 'spot', at: G.church, label: 'crkva', lp: 'nw', guess: true, until: 4 },
          { t: 'area', side: 'enemy', id: 'rov-jug', at: [16.0835, 45.3348], rx: 0.32, ry: 0.09, rot: -20, label: 'rovovi: oko 3 satnije', lp: 'sw', guess: true, until: 4 },
          { t: 'area', side: 'enemy', id: 'rov-zapad', at: [16.0795, 45.3405], rx: 0.09, ry: 0.28, guess: true, until: 4 },
          { t: 'area', side: 'enemy', id: 'rov-sever', at: [16.0880, 45.3465], rx: 0.3, ry: 0.09, rot: 8, guess: true, until: 4 },
          { t: 'area', side: 'enemy', id: 'most', at: [16.1072, 45.3468], rx: 0.17, ry: 0.11, label: 'satnija kod mosta', lp: 'n', guess: true, until: 4 },
          { t: 'area', side: 'enemy', id: 'centar', at: [16.0868, 45.3395], rx: 0.18, ry: 0.12, label: 'rezerve u gradu', lp: 'w', guess: true, until: 4 },
          { t: 'post', at: [16.0975, 45.3388], label: 'oružnička postaja', lp: 'ne', small: true, guess: true, until: 4 },
        ],
      },
      {
        date: '23. oktobra 1942.', when: 'do svitanja',
        view: [16.066, 45.316, 16.134, 45.370],
        text: 'Borba traje 6 sati. U Glinu prodire pet bataljona, bez veze i bez vodiča, i mnogi se gube u gradu; čete su '
          + 'rasute po udarnim grupama, prodor jenjava, a otpor raste. „Marko Orešković“ nije postavio osiguranje prema '
          + 'ciglani i tučen je odande ubitačnom vatrom; njegovi kuriri dvaput traže pomoć, a štab Četvrtog bataljona traži '
          + 'da i on uđe u borbu, ali Operativni štab to ne dozvoli. Za Drugi bataljon Operativni štab će reći da je „bio '
          + 'skoro potpuno pasivan“, da je „ušao u ulicu gdje većinom neprijatelja nije ni bilo i borbe skoro nije ni '
          + 'imao“. Neprijatelj rezerve, dve satnije, oko 50 ustaša i oko 30 žandara, baca tamo gde je najugroženiji.',
        notes: ['Ciglana je na karti JNA između centra i Jukinca, kod glinokopa; gde je bio Drugi bataljon u gradu, '
          + 'knjiga ne kaže.'],
        marks: [
          { t: 'spot', at: G.ciglana, label: 'ciglana', lp: 'nw' },
          { t: 'move', side: 'enemy', kind: 'fire', path: [G.ciglana, [16.1010, 45.3425]] },
          { t: 'area', side: 'own', at: [16.0918, 45.3368], rx: 0.17, ry: 0.11, label: 'II bat.', lp: 's', guess: true },
          { t: 'fight', at: [16.0992, 45.3402] },
          { t: 'move', side: 'enemy', kind: 'attack', path: [[16.0880, 45.3402], [16.0935, 45.3406], [16.0978, 45.3405]], guess: true },
        ],
      },
      {
        date: '23. oktobra 1942.', when: 'u osvit',
        view: [16.050, 45.220, 16.250, 45.430],
        text: 'Ostaje samo jedno rešenje: povlačenje. Brigada se povlači u Rudić, gde ostaje do 25. oktobra, a zatim u '
          + 'Klasnić. Iz Petrinje je preko Gore Glini u pomoć krenula čitava bojna, ali je stigla kad se brigada već povukla.',
        notes: [
          'Put povlačenja knjiga ne opisuje.',
          'Put bojne iz Petrinje nacrtan je od Gore, kroz koju je išla; ostatak nije zapisan.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'back', path: [[16.1000, 45.3380], [16.1200, 45.3200], [16.1450, 45.2900], [16.1600, 45.2450], G.rudici],
            label: 'u Rudić', lp: 'e', at: 0.6, guess: true },
          { t: 'area', side: 'own', at: G.rudici, rx: 0.4, ry: 0.25, label: 'II bat.', lp: 'e' },
          { t: 'move', side: 'enemy', kind: 'march', path: [[16.1922, 45.4192], [16.1500, 45.3900], [16.1100, 45.3550]],
            label: 'bojna iz Petrinje', lp: 'e', at: 0.3, guess: true },
          { t: 'area', side: 'enemy', at: G.glina, rx: 0.75, ry: 0.5, label: 'Glina', lp: 'w' },
        ],
      },
    ],
    enemy: [
      'Po zapovesti oko 650 vojnika, jedna satnija ustaša i domobrani, baterija od 4 topa kod klaonice, 4 teška i 8 lakih bacača',
      'U stvari i delovi bojne Ivana Mraka i 1. oružničke pukovnije, pod 5. gorskim zdrugom pukovnika Lalića: oko 3 '
        + 'satnije u rovovima oko grada; u rezervi 2 satnije, oko 50 ustaša i oko 30 žandara',
      'Bojna iz Petrinje, koja je stigla posle povlačenja',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: na bateriju, istočni deo grada',
      'Treći, kordunaški bataljon: Kozarica i stanica',
      'Četvrti, banijski bataljon: osiguranje ceste Petrinja–Glina, između Jukinca i Prekopa',
      'Sedma banijska: dva bataljona od Jukinca u severni deo grada',
      'Osma banijska i Peta kordunaška: na prilazima Glini',
    ],
    result: 'Glina nije zauzeta. Operativni štab je ipak ocenio da napad nije potpun neuspeh: partizani su došli u '
      + 'centar grada, „pomlatili najmanje 50 neprijateljskih vojnika“, zapalili sudsku zgradu i odneli puškomitraljeze. '
      + 'Zarobljeno je 9 domobrana, jedan ustaša i jedan oružnik. Grupa brigada imala je 20 mrtvih, 40 ranjenih i 2 '
      + 'nestala, Prva brigada 9 poginulih, od toga osam iz „Marka Oreškovića“, i 19 ranjenih. „Pekiša Vuksan“ i '
      + 'Četvrti bataljon nisu imali gubitaka.',
    pages: [101, 106],
  },
  {
    key: 'mala-melnica',
    foe: 'ndh',
    region: 'slunj',
    title: 'Prvi napad na Slunj',
    short: 'Mala Melnica',
    dates: '6–8. novembra 1942.',
    start: '1942-11-06', end: '1942-11-08',
    about: 'Posle marša od 160 km s Banije, brigada s Drugom ličkom napada Slunj, najveći i najutvrđeniji ustaški '
      + 'garnizon u dolini Korane. Planeri su računali s manje od 1000 branilaca u paničnom bekstvu, a bilo ih je više '
      + 'od 1500, odlučnih da se brane. Napad je zamišljen kao proslava 7. novembra. Drugim bataljonom sada komanduje '
      + 'Ilija Palija.',
    view: [15.535, 45.068, 15.625, 45.135],
    places: ['Slunj', 'Podmelnica', 'Slunjčica', 'Lumbardenik', 'Katići', 'Mala Melnica', 'Velika Melnica', 'Donji Lađevac',
      'Gornje Taborište', 'Donje Taborište'],
    base: [
      { t: 'area', side: 'enemy', at: S.slunj, rx: 0.7, ry: 0.5, label: 'Slunj: više od 1500 ustaša i domobrana', lp: 'n', until: 2 },
      { t: 'kota', at: S.k471, label: '471', lp: 'e' },
      { t: 'kota', at: S.k518, label: '518', lp: 'w' },
    ],
    steps: [
      {
        date: '6. novembra 1942.', time: '22.00',
        text: 'Napad je naređen za 22 sata. Drugi bataljon treba da zauzme Malu Melnicu (k. 471), da se desnim krilom '
          + 'spusti na cestu Slunj–Rakovica u selu Slušnica, gde će se povezati s Drugom ličkom, a levim krilom uhvati '
          + 'vezu s Prvim bataljonom na Velikoj Melnici (k. 518), pa da upadne u Slunj s jugozapada. Levo od njih '
          + 'napadaju Četvrti, preko Pliješa (k. 389), i Treći, na kotu 292 severozapadno od grada. Nevreme je strašno: '
          + 'jedinice lutaju, vodiči ne stižu, i neki bataljoni kasne i po 8 sati.',
        notes: [
          'Strelice ovog koraka su zadaci iz zapovesti štaba brigade, ne pokreti.',
          'Slušnica je reka i selo na cesti od Rakovice, na kartama Slunjčica.',
          'Na topografskoj karti JNA 1:25.000 Pliješ je Plješ, 387 m, zapadno od Podmelnice, kota 292 je kota 295 '
            + 'severozapadno od grada, a kota 471 Lalića vrh (473 m), vrh Male Melnice.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'march', path: [[15.5800, 45.0760], S.k471, [15.5835, 45.0990], [15.5815, 45.1085]],
            label: 'zadatak II bat.', lp: 'e', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.5640, 45.0880], S.k518, [15.5770, 45.1060]], label: 'I bat.', lp: 'w', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.5420, 45.1060], S.plijes, [15.5650, 45.1210]], label: 'IV bat.', lp: 'w', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.5550, 45.1320], [15.5700, 45.1250], S.k292], label: 'III bat.', lp: 'n', at: 0.2, guess: true },
          { t: 'move', side: 'ally', kind: 'march', path: [[15.6050, 45.0720], S.lumbardenik, [15.5920, 45.1090]], label: '2. lička br.', lp: 'e', at: 0.3, guess: true },
          { t: 'kota', at: S.plijes, label: '389 Pliješ', lp: 'w' },
          { t: 'kota', at: S.k292, label: '292', lp: 'n' },
        ],
      },
      {
        date: '7. novembra 1942.', time: '5.00',
        view: [15.562, 45.070, 15.605, 45.105],
        text: 'Prvi u dodir s neprijateljem dolazi „Pekiša Vuksan“, u kome je od starih partizana ostalo jedva 50. Ilija '
          + 'Palija ga u 5 sati uvodi u borbu, na desnom krilu brigade, uz cestu od Rakovice, i bataljon silovitim '
          + 'naletom zaposedne Malu Melnicu. Treću četu Palija šalje prema izvoru Slušnice, da se spoji s levim krilom '
          + 'Druge ličke, ali Druga lička ne dolazi. Veza s „Markom Oreškovićem“ brzo je uspostavljena.',
        notes: ['Odakle je bataljon krenuo na Malu Melnicu, knjiga ne kaže; strelica dolazi od ceste.'],
        marks: [
          { t: 'move', side: 'own', kind: 'attack', path: [[15.5810, 45.0790], [15.5840, 45.0835], [15.5857, 45.0868]] },
          { t: 'area', side: 'own', at: [15.5856, 45.0886], rx: 0.35, ry: 0.2, label: 'II bat.', lp: 'w' },
          { t: 'move', side: 'own', kind: 'march', path: [[15.5872, 45.0870], [15.5886, 45.0830], [15.5888, 45.0794]], label: '3/II', lp: 'e', at: 0.5 },
          { t: 'spot', at: S.izvor, label: 'izvor Slušnice', lp: 'e' },
          { t: 'area', side: 'friend', at: [15.5735, 45.0972], rx: 0.35, ry: 0.2, label: 'I bat.', lp: 'w', guess: true },
        ],
      },
      {
        date: '7. novembra 1942.', when: 'celog dana',
        view: [15.555, 45.078, 15.615, 45.125],
        text: 'Borbe traju celog dana. Neprijatelj je izbačen iz rovova i bunkera spoljne odbrane, većinom u ponovljenim '
          + 'jurišima i bombaškim akcijama, i do večeri sateran u utvrđene zgrade. Pred „Pekišom Vuksanom“ su '
          + 'cementirani bunkeri. Gine Jakov Petrlić, komandir Prvog voda Druge čete, posle predložen za narodnog '
          + 'heroja. Grupa boraca s komesarom Prve čete Stevom Potkonjakom Mačkom zarobi trojicu ustaških kurira, koji su '
          + 'nosili poštu iz Lađevca u Slunj.',
        notes: [
          'Gde su bili bunkeri pred bataljonom i dokle je bataljon stigao, knjiga ne kaže.',
          'Petrlić je u izveštajima i Peterlić; gde je pao, knjiga ne kaže.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.5832, 45.0995], rx: 0.4, ry: 0.2, label: 'II bat.', lp: 'w', guess: true },
          { t: 'post', at: [15.5840, 45.1042], label: 'cementirani bunkeri', lp: 'e', small: true, guess: true },
          { t: 'fight', at: [15.5836, 45.1020] },
          { t: 'area', side: 'friend', at: [15.5762, 45.1048], rx: 0.3, ry: 0.2, label: 'I bat.', lp: 'w', guess: true },
          { t: 'area', side: 'enemy', at: [15.5855, 45.1150], rx: 0.42, ry: 0.3, label: 'Slunj: utvrđene zgrade', lp: 'n' },
        ],
      },
      {
        date: '8. novembra 1942.', time: '7.00',
        view: [15.520, 45.068, 15.625, 45.135],
        text: 'Druga lička se „pod pritiskom neprijatelja iz Lađevaca“ povukla prema Rakovici, a od Operativnog štaba '
          + 'nema vesti. Štab brigade drži bataljone oko Slunja do 7 sati, a onda im naređuje da se povuku na polazne '
          + 'položaje, pa u Zbjeg.',
        notes: ['Zbjeg je ovde Zbjeg Močilski (GeoNames), zapadno od Slunja; put povlačenja knjiga ne opisuje.'],
        marks: [
          { t: 'move', side: 'own', kind: 'back', path: [[15.5822, 45.0990], [15.5650, 45.0962], [15.5480, 45.0990], [15.5365, 45.1000]],
            label: 'u Zbjeg', lp: 'n', at: 0.6, guess: true },
          { t: 'area', side: 'own', at: S.zbjeg, rx: 0.35, ry: 0.22, label: 'II bat.', lp: 's', guess: true },
        ],
      },
    ],
    enemy: [
      '10. ustaška satnija, oko 600 vojnika; slunjski sat 3. pešadijske pukovnije, oko 130; oko 200 oružnika i naoružanih',
      'Ustaše tučene u Ličkom Petrovom Selu, majari iz Vaganca, Drežnik-Grada i Rakovice, delovi 31. i 33. ustaške bojne',
      'Svaki odrasli muškarac u Slunju bio je naoružan',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: preko Velikih Melnica; komandant Mile Marčetić teško ranjen',
      'Četvrti, banijski bataljon: Pliješ, pa pred gimnaziju',
      'Treći, kordunaški bataljon: kota 292, dvaput preko Korane',
      'Druga lička brigada: nije stigla u borbu',
    ],
    result: 'Slunj nije zauzet: do noći su bataljoni „opasali samo mjesto i stjerali neprijatelja u kuće“. Brigada je '
      + 'imala 4 poginula; samo 10. ustaška bojna imala je 11 mrtvih i 40 ranjenih. Glavni štab Hrvatske pohvalio je '
      + 'brigadu kao celinu i prihvatio predlog da se vodnik Jakov Petrlić proglasi za narodnog heroja.',
    fallen: [{ name: 'Petrlić Jakov', id: '0002006468', note: 'komandir Prvog voda Druge čete' }],
    pages: [110, 116],
  },
  {
    key: 'slunj',
    foe: 'ndh',
    region: 'slunj',
    title: 'Lađevac i oslobođenje Slunja',
    short: 'Slunj',
    dates: '11–14. novembra 1942.',
    start: '1942-11-11', end: '1942-11-14',
    about: 'Drugi napad na Slunj spreman je s više opreza, u dve faze: ojačana brigada 11. novembra zauzima Lađevac, a '
      + 'tri dana kasnije, s Drugom ličkom i Osmom kordunaškom, i sam Slunj, opkoljen sa svih strana.',
    view: [15.555, 45.072, 15.705, 45.135],
    places: ['Slunj', 'Donji Lađevac', 'Gornji Lađevac', 'Podmelnica', 'Lumbardenik', 'Slunjčica', 'Mala Melnica', 'Gornje Taborište'],
    base: [
      { t: 'area', side: 'enemy', at: S.slunj, rx: 0.7, ry: 0.5, label: 'Slunj', lp: 'n', until: 3 },
      { t: 'area', side: 'enemy', at: S.ladjevac, rx: 0.45, ry: 0.3, label: 'Lađevac: ustaše', lp: 's', until: 1 },
    ],
    steps: [
      {
        date: '11. novembra 1942.', time: '6.00',
        text: 'Napad na Lađevac počinje u 6 sati; „Marko Orešković“ s bataljonom „Mićo Radaković“ Druge ličke prodire u '
          + 'selo. Kordunaški bataljon zaposeda položaje između Lađevca i Slunja, od kote 402 na zapadu do leve obale '
          + 'Korane na istoku, levim krilom povezan s „Pekišom Vuksanom“, koji zatvara izlaze iz Slunja na jug, prema '
          + 'Melnicama. Ustaše iz Slunja ovog puta ne interveniraju: uzbunio ih je lažni napad Četvrtog bataljona.',
        notes: [
          'Kota 402 je na karti JNA V. Pluznik (400 m), između Slunja i Lađevca, gde se desno krilo Drugog bataljona '
            + 'sastaje s Trećim; Korana teče severno od Lađevca na zapad, prema Slunju, pa je njena leva obala južna.',
          'Položaj Drugog bataljona knjiga daje samo kao zadatak: zatvoriti izlaze iz Slunja na jug.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [15.5985, 45.0985], rx: 1.0, ry: 0.28, rot: -12, label: 'II bat.', lp: 's', guess: true },
          { t: 'area', side: 'friend', at: [15.6560, 45.0975], rx: 3.3, ry: 0.28, rot: -4, label: 'III bat.', lp: 'n', guess: true },
          { t: 'kota', at: S.k402, label: '402', lp: 'w' },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.6120, 45.0800], [15.6220, 45.0850], [15.6290, 45.0880]],
            label: 'I bat. i „Mićo Radaković“', lp: 's', at: 0.2, guess: true },
        ],
      },
      {
        date: '11. novembra 1942.', when: 'tokom dana',
        text: 'Otpor u selu brzo je skršen, i veći deo posade povlači se na severoistok, jer bataljon „Mićo Radaković“ '
          + 'taj pravac nije na vreme zatvorio. Najžešća je borba za rovove na koti 402, odakle ih Treći bataljon '
          + '„brzim naletom“ natera u paničan beg prema Slunju. Na tim položajima i na položajima „Pekiše Vuksana“ ima '
          + 'tokom dana još nekoliko okršaja s dve-tri satnije, koje bez ozbiljnih namera pokušavaju da pomognu svojima u Lađevcu.',
        notes: ['Odakle su dolazile satnije iz Slunja, knjiga ne kaže; nacrtane su na putevima iz grada prema jugu.'],
        marks: [
          { t: 'post', at: S.ladjevac, label: 'Lađevac', lp: 's', taken: true },
          { t: 'move', side: 'enemy', kind: 'back', path: [[15.6335, 45.0902], [15.6450, 45.0980], [15.6560, 45.1045]], label: 'posada beži', lp: 'e', at: 0.5 },
          { t: 'fight', at: S.k402 },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.5880, 45.1100], [15.5910, 45.1052], [15.5945, 45.1012]],
            label: 'satnije iz Slunja', lp: 'e', at: 0.2, guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[15.6000, 45.1150], [15.6075, 45.1060], [15.6110, 45.0990]], guess: true },
        ],
      },
      {
        date: '14. novembra 1942.', time: '15.40',
        view: [15.560, 45.085, 15.610, 45.122],
        text: 'Znak za napad daju pucnji iz haubice. Bataljoni su se neopaženo privukli; brigada je srednja kolona, između '
          + 'kanjona Slušnice i ceste Mrzlo Polje–Slunj. „Marko Orešković“ projuri kroz Podmelnice i na juriš zauzme prve '
          + 'rovove na bezimenoj koti, a Treći se klinom probije prema parku. „Pekiša Vuksan“ posle kraće borbe očisti '
          + 'selo uzduž glavne ceste i istera neprijatelja iz rovova pred sobom: borci su, za komandantom Ilijom Palijom '
          + 'i svojim komandirima, „kao vukovi uskakali u rovove“ i na leđima ustaša ušli u centar Slunja.',
        notes: [
          'Koje je selo uz glavnu cestu očistio bataljon, knjiga ne kaže; strelica ide cestom od Rakovice.',
          'Bezimena kota i park nisu na kartama.',
        ],
        marks: [
          { t: 'move', side: 'own', kind: 'attack', path: [[15.5840, 45.0960], [15.5838, 45.1030], [15.5845, 45.1090], [15.5852, 45.1132]],
            label: 'II bat.', lp: 'e', at: 0.4, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.5700, 45.1040], [15.5763, 45.1075], [15.5800, 45.1110]], label: 'I bat.', lp: 'w', at: 0.2, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.5680, 45.1100], [15.5760, 45.1125], [15.5820, 45.1140]], label: 'III bat.', lp: 'n', at: 0.2, guess: true },
        ],
      },
      {
        date: '14. novembra 1942.', time: 'oko 18.00',
        view: [15.560, 45.095, 15.610, 45.135],
        text: 'Oko 18 sati tri bataljona brigade su u centru Slunja; desetak minuta kasnije borci Kordunaškog bataljona '
          + 'zvone crkvenim zvonima. Neprijatelj beži, uglavnom prema Karlovcu, a mnogo ustaša koji nisu mogli da pobegnu '
          + 'izvrši samoubistvo. Slunj je dotad najveće oslobođeno mesto u Hrvatskoj. U gradu uveče ostaje samo „Pekiša '
          + 'Vuksan“, da postavi straže kod svih važnijih državnih zgrada i trgovina, a glavnina brigade nastavlja gonjenje.',
        notes: ['Crkva je ovde katolička crkva Presvetog Trojstva (OpenStreetMap); knjiga ne kaže koja.'],
        marks: [
          { t: 'post', at: S.slunj, label: 'Slunj', lp: 'n', taken: true },
          { t: 'area', side: 'own', at: [15.5845, 45.1138], rx: 0.3, ry: 0.2, label: 'II bat.: straže u gradu', lp: 'w' },
          { t: 'spot', at: S.church, label: 'crkva', lp: 'e', guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [[15.5862, 45.1200], [15.5850, 45.1260], [15.5800, 45.1320]], label: 'gonjenje', lp: 'e', at: 0.5 },
        ],
      },
    ],
    enemy: [
      'Opkoljeni garnizon Slunja; u Lađevcu ustaše, pojačane uoči napada ustašama iz Furjana',
      'Dve-tri satnije iz Slunja, u pomoć Lađevcu',
    ],
    friends: [
      'Bataljon „Mićo Radaković“ Druge ličke: s Prvim bataljonom na Lađevac',
      'Četvrti, banijski bataljon: lažni napad na Slunj 11. novembra',
      'Druga lička i Osma kordunaška brigada: 14. novembra levo i desno od brigade',
      'Dve haubice',
    ],
    result: 'Lađevac i Slunj su oslobođeni. Kod Lađevca su poginula četiri borca brigade, a 15 je ranjeno; u borbi za '
      + 'Slunj 14. novembra brigada je imala dva poginula i 9 ranjenih. Neprijatelj se ipak izvukao iz Slunja, jer '
      + 'jedinice koje je trebalo da zatvore severne izlaze nisu na vreme stigle.',
    pages: [116, 119],
  },
  {
    key: 'dvor',
    foe: 'ndh',
    region: 'dvor',
    title: 'Zamlača i Krstovo brdo',
    short: 'Dvor na Uni',
    dates: '25–29. novembra 1942.',
    start: '1942-11-26', end: '1942-11-29',
    about: 'Brigada je sada u Šestoj diviziji. Dok Sedma banijska i Druga lička napadaju Dvor na Uni, a krajiške '
      + 'brigade susedni Bosanski Novi, brigada zatvara cestu i prugu od Kostajnice. Drugi bataljon treba da se uklini '
      + 'u neprijateljski raspored dva kilometra severno od Dvora, između Dvora i Zamlače, „u svrhu osiguranja naših '
      + 'snaga u Dvoru od Zamlače i sprečavanja bijega neprijatelja iz Dvora, te hvatanja istoga“.',
    view: [16.340, 45.055, 16.500, 45.205],
    places: ['Dvor', 'Zamlača', 'Hrtić', 'Unčani', 'Golubovac Divuški', 'Divuša', 'Kozibrod', 'Kuljani', 'Kirišnica', 'Volinja',
      'Šegestin', 'Zrin', 'Donja Oraovica', 'Novi Grad'],
    base: [
      { t: 'area', side: 'enemy', at: D.dvor, rx: 0.6, ry: 0.4, label: 'Dvor: 800 domobrana, 250 Nemaca, 66 ustaša, 47 žandara', lp: 'w' },
      { t: 'area', side: 'enemy', at: D.zamlaca, rx: 0.3, ry: 0.2, label: 'Zamlača: ustaška milicija', lp: 'e', until: 1 },
      { t: 'area', side: 'enemy', at: D.volinja, rx: 0.4, ry: 0.25, label: 'Volinja i most: domobrani', lp: 'e' },
      { t: 'area', side: 'enemy', at: D.zrin, rx: 0.35, ry: 0.22, label: 'Zrin', lp: 'w' },
    ],
    steps: [
      {
        date: '26. novembra 1942.', time: 'do 23.00',
        view: [16.330, 45.050, 16.510, 45.210],
        text: 'Bataljoni su iz Rujevca krenuli u podne 25. novembra i tridesetak sati, manje uočljivim stazama, prilaze '
          + 'svojim položajima. Treći i Četvrti bataljon treba da zaposednu položaje kod Volinje, između Kirišnice i '
          + 'Crlješnice (284 m), i da postave zasede između kota 284 i 219 prema cesti i pruzi; Prvi da se rasporedi oko '
          + 'Šegestina i blokira Zrin; Drugi da se uklini između Dvora i Zamlače.',
        notes: [
          'Kota 219 je ovde vrh te visine južno od Crlješnice, kod Kirišnice; knjiga je ne smešta bliže.',
          'Mesto Drugog bataljona knjiga daje kao zadatak: dva kilometra severno od Dvora, između Dvora i Zamlače.',
        ],
        marks: [
          { t: 'area', side: 'own', at: [16.3810, 45.0800], rx: 0.35, ry: 0.2, label: 'II bat.', lp: 'w', guess: true },
          { t: 'area', side: 'friend', at: [16.3892, 45.1530], rx: 0.45, ry: 0.28, label: 'I bat.', lp: 'w', guess: true },
          { t: 'area', side: 'friend', at: [16.4605, 45.1890], rx: 0.5, ry: 0.3, label: 'III i IV bat.', lp: 'w', guess: true },
          { t: 'kota', at: D.crljesnica, label: '284 Crlješnica', lp: 'e' },
          { t: 'kota', at: D.k219, label: '219', lp: 'e', guess: true },
        ],
      },
      {
        date: '26. novembra 1942.', time: '23.00',
        view: [16.355, 45.065, 16.440, 45.145],
        text: 'Napad počinje u 23 sata, kad i napad na Bosanski Novi i Dvor. „Pekiša Vuksan“ u jednom naletu zauzme '
          + 'Zamlaču i zarobi 23 ustaška milicionera; među njima je bilo više prisilno mobilisanih, i svi takvi su posle '
          + 'suđenja u Žirovcu pušteni kućama. Krntijaši napadaju Unčane i Golubovac; otpor je žestok i nepredviđeno dug.',
        notes: ['Odakle je bataljon napao Zamlaču, knjiga ne kaže.'],
        marks: [
          { t: 'move', side: 'own', kind: 'attack', path: [[16.3790, 45.0812], [16.3815, 45.0850], [16.3832, 45.0880]] },
          { t: 'post', at: D.zamlaca, label: 'Zamlača: 23 zarobljena', lp: 'e', taken: true },
          { t: 'area', side: 'own', at: [16.3846, 45.0905], rx: 0.25, ry: 0.15, label: 'II bat.', lp: 'w' },
          { t: 'move', side: 'friend', kind: 'attack', path: [[16.4000, 45.1400], [16.4100, 45.1330], [16.4150, 45.1296]], label: 'I bat.', lp: 'w', at: 0.2, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[16.4060, 45.1440], [16.4180, 45.1400], [16.4255, 45.1362]], guess: true },
        ],
      },
      {
        date: '27. novembra 1942.', when: 'ujutro i preko dana',
        view: [16.400, 45.120, 16.500, 45.210],
        text: 'Prvi bataljon posle kratkog i žestokog okršaja uđe u Divušu, najveće naselje između Kostajnice i Dvora. '
          + 'Treći i Četvrti zaposeli su položaje bez borbe; Četvrti se bori s posadama Volinje i mosta, a Kordunaši '
          + 'zasedom dočekuju Nemce između Volinje i Kuljana. Vozom iz Kukuruzara stiže 4. bojna 2. gorskog zdruga, s '
          + 'nekoliko nemačkih tenkova; domobrani i ustaše zaustavljeni su između Volinje i Kuljana, a kad sa severa '
          + 'naiđe oklopni voz, Milisav Dakić ga zaustavi protivtenkovskim mitraljezom i napadne s obe strane pruge.',
        notes: ['Gde su bile zaseda i borba s vozom, knjiga ne kaže; nacrtane su na cesti i pruzi južno od Volinje.'],
        marks: [
          { t: 'post', at: D.divusa, label: 'Divuša', lp: 'e', taken: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[16.4300, 45.1400], [16.4380, 45.1415], [16.4436, 45.1425]], label: 'I bat.', lp: 's', at: 0.2, guess: true },
          { t: 'ambush', at: [16.4755, 45.1718], face: [16.4790, 45.1780], label: 'zaseda III bat.', lp: 'w', guess: true },
          { t: 'train', at: [16.4802, 45.1800], label: 'oklopni voz', lp: 'e', armoured: true, guess: true },
          { t: 'move', side: 'enemy', kind: 'stopped', path: [[16.4860, 45.1990], [16.4805, 45.1900], [16.4775, 45.1805]],
            label: '4. bojna 2. gorskog zdruga', lp: 'e', at: 0.2 },
          { t: 'move', side: 'friend', kind: 'fire', path: [[16.4722, 45.1832], [16.4785, 45.1810]] },
        ],
      },
      {
        date: '28. novembra 1942.', time: 'od 10.20',
        view: [16.405, 45.120, 16.495, 45.205],
        text: 'Od Volinje prema Divuši, Zamlači i Dvoru krene pet do sedam nemačkih tenkova s topovima i pet oklopnih '
          + 'automobila. Protivtenkovski mitraljez Trećeg bataljona ne može da ih probije, i kolona se probije prema '
          + 'Dvoru; njena pešadijska pratnja je raspršena. Iz rejona Crlješnice u 10.20 krene oko 2000 vojnika, tri bojne '
          + 'i nemački bataljon, s baterijom topova. Do 16 sati pređu pola puta do Divuše, predveče otpor Trećeg i '
          + 'Četvrtog bataljona popusti, i u 19 sati izbiju u Divušu. Južno od nje njihov streljački stroj zaustavljen je '
          + 'na Golupskom brdu, a motorizacija na cesti pred Golubovcem, gde su krntijaši.',
        notes: [
          'Golupsko brdo je ovde vrh Golubovac kraj Divuše (228 m na OpenStreetMap; knjiga: 225 m).',
          'Put tenkova nacrtan je cestom; knjiga ne kaže kuda su prošli ni dokle su stigli.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'attack', path: [[16.4860, 45.2000], [16.4790, 45.1800], [16.4630, 45.1540], [16.4450, 45.1430], [16.4300, 45.1350]],
            label: 'pet do sedam nemačkih tenkova', lp: 'e', at: 0.35, force: 'de', guess: true },
          { t: 'move', side: 'enemy', kind: 'attack', path: [[16.4683, 45.1900], [16.4640, 45.1700], [16.4560, 45.1520], [16.4462, 45.1442]],
            label: 'oko 2000: tri bojne i nemački bataljon', lp: 'w', at: 0.3 },
          { t: 'post', at: D.divusa, label: 'Divuša, 19.00', lp: 'e', force: 'ndh' },
          { t: 'area', side: 'friend', at: [16.4560, 45.1655], rx: 0.45, ry: 0.25, label: 'III i IV bat.', lp: 'w', guess: true },
          { t: 'kota', at: D.golupsko, label: '225 Golupsko brdo', lp: 'n' },
          { t: 'area', side: 'friend', at: D.golubovac, rx: 0.35, ry: 0.2, label: 'I bat.', lp: 's', guess: true },
        ],
      },
      {
        date: '28. novembra 1942.', when: 'zatim',
        view: [16.400, 45.125, 16.440, 45.150],
        text: 'Ustaše i domobrani pukovnika Gregorića u „žestokom jurišu“ zauzmu Golupsko brdo i gone partizane sve do '
          + 'Krstova brda iznad Golubovca i Unčana, gde uđu u raspored „Pekiše Vuksana“. Tu se vodi izuzetno surova '
          + 'borba: čete bataljona više puta uzmiču, pa se silovitim protivnapadima vraćaju, i nekoliko puta bije se prsa '
          + 'u prsa. Ilija Palija i Duja Čubrilo lome kundake pušaka. Pogine puškomitraljezac Prve čete Ilija Krajnović, '
          + 'štiteći odstupnicu drugova, a ranjeni su braća Pjevači, vodnik Prve čete Stevo i desetar Treće čete Nikola, '
          + 'i njihov stričević Nikola, vodnik u Trećoj četi.',
        notes: [
          'Krstovo brdo nije na kartama; nacrtano je na visu od oko 215 m iznad Golubovca i Unčana.',
          'Kad je bataljon prešao od Zamlače na Krstovo brdo, knjiga ne kaže.',
          'Dan nije siguran: Gregorićevi su zauzeli Golupsko brdo posle 19 sati 28. novembra, a čete su se ovde sudarale '
            + '„u višednevnim sudarima“; u spisku boraca Krajnović je poginuo 27. novembra.',
        ],
        marks: [
          { t: 'area', side: 'own', at: D.krstovo, rx: 0.4, ry: 0.22, label: 'II bat.', lp: 'w', guess: true },
          { t: 'kota', at: D.krstovo, label: 'Krstovo brdo', lp: 'n', guess: true },
          { t: 'move', side: 'enemy', kind: 'attack', path: [[16.4345, 45.1450], [16.4250, 45.1412], [16.4172, 45.1376]],
            label: 'Gregorićevi ustaše i domobrani', lp: 'n', at: 0.3 },
          { t: 'move', side: 'own', kind: 'attack', path: [[16.4118, 45.1345], [16.4180, 45.1364], [16.4232, 45.1386]] },
          { t: 'fight', at: [16.4172, 45.1372] },
        ],
      },
      {
        date: '28. novembra 1942.', when: 'u najžešćem okršaju',
        view: [16.402, 45.127, 16.432, 45.146],
        text: 'Mina razori mitraljesko gnezdo vodnika Nikole Miščevića: vodnik pogine, a Jovo Potkonjak i Veljko Dimić su '
          + 'ranjeni. Dok ih izvlače, nagrne gust streljački stroj nemačke i domobranske pešadije; lakše ranjeni Potkonjak '
          + 'se povuče, a osamnaestogodišnji Dimić ostane nepokretan kraj mrtvog Miščevića. Komandir Prve čete Duja '
          + 'Čubrilo povede četu na streljački stroj; „Tuklo se vatrom i bajunetima, više kundaka je polomljeno“, zapisao '
          + 'je Dimić. Teško je ranjen komandir mitraljeskog voda Dragan Dejanović Muso, a pogine kurir Milan Potkonjak '
          + 'Bračko Kokin, dok komandantu Paliji nosi izveštaj komandira Treće čete.',
        notes: ['U spisku boraca kurir Milan Potkonjak poginuo je 27. novembra, „na Kirišnici“.'],
        marks: [
          { t: 'move', side: 'enemy', kind: 'attack', path: [[16.4242, 45.1404], [16.4196, 45.1386], [16.4160, 45.1371]],
            label: 'nemačka i domobranska pešadija', lp: 'n', at: 0.3 },
          { t: 'move', side: 'own', kind: 'attack', path: [[16.4112, 45.1349], [16.4150, 45.1361], [16.4186, 45.1375]],
            label: '1/II (D. Čubrilo)', lp: 's', at: 0.3 },
          { t: 'fight', at: [16.4170, 45.1373] },
        ],
      },
      {
        date: '29. novembra 1942.', time: '6.00',
        text: 'Štab Prvog hrvatskog korpusa u 6 sati naređuje povlačenje: posle spajanja kostajničke kolone s garnizonom '
          + 'Dvora svi dalji napadi bili bi „više nego ludi“. Od poslednjeg sata 26. do podneva 29. novembra brigada je '
          + 'imala 14 mrtvih i više od 30 ranjenih, a zarobila je 23 domobrana i 3 Nemca. Povlači se u rejon Slunja, na '
          + 'reorganizaciju; 2. decembra u Podzvizdu iz nje odlaze Kordunaški i Banijski bataljon.',
        notes: ['Put povlačenja knjiga ne opisuje.'],
        marks: [
          { t: 'move', side: 'own', kind: 'back', path: [[16.4118, 45.1360], [16.3900, 45.1385], [16.3600, 45.1410]], label: 'povlačenje', lp: 'n', at: 0.5, guess: true },
        ],
      },
    ],
    enemy: [
      'Dvor: oko 800 domobrana, 250 Nemaca, 66 ustaša i 47 žandara, dve haubice; kružna odbrana s bunkerima, žicom i minama',
      'Uz Unu između Kostajnice i Dvora oko 850 vojnika; u Kostajnici štab 2. domobranske divizije i četa 202. nemačkog oklopnog puka',
      '4. bojna 2. gorskog zdruga, vozom iz Kukuruzara, s nemačkim tenkovima',
      '28. novembra pet do sedam tenkova 3. čete 202. oklopnog puka i pet oklopnih automobila; oko 2000 vojnika, tri '
        + 'bojne i 3. bataljon 741. nemačkog puka, s baterijom topova',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“: Unčani, Golubovac, Divuša, Golupsko brdo',
      'Treći, kordunaški, i Četvrti, banijski bataljon: zasede kod Volinje',
      'Sedma banijska i Druga lička: napad na Dvor; Osma banijska južno od Dvora',
      'Krajiške brigade Prvog bosanskog korpusa: napad na Bosanski Novi',
    ],
    result: 'Dvor nije zauzet: nemačka kolona iz Kostajnice probila se do garnizona Dvora i Bosanskog Novog. To je bila '
      + 'poslednja zajednička borba bataljona prvog sastava brigade i prva s nemačkim tenkovima; štab divizije ocenio '
      + 'je da su se u njoj neki borci „naročito istakli“, a iz Drugog bataljona pohvaljeni su vodnik Nikica Mišćević, '
      + 'Ilija Potkonjak i Nikola Vojvodić.',
    fallen: [
      { name: 'Krajnović Mile Ilija', id: '0002003748', note: 'puškomitraljezac Prve čete' },
      { name: 'Miščević Nikola', note: 'vodnik' },
      { name: 'Potkonjak Janka Milan', id: '0002006883', note: 'kurir („Bračko Kokin“)' },
    ],
    wounded: [
      { name: 'Pjevač Đurin Stevo', id: '0002006714', note: 'vodnik u Prvoj četi' },
      { name: 'Pjevač Đurin Nikola', id: '0002006711', note: 'desetar u Trećoj četi' },
      { name: 'Pjevač Đukanov Nikola', id: '0002006709', note: 'vodnik u Trećoj četi; u spisku poginuo 27. 11.' },
      { name: 'Potkonjak Triše Jovo', id: '0002006881' },
      { name: 'Dimić Todora Veljko', id: '0002001494' },
      { name: 'Dejanović Markov Dragan', id: '0002001393', note: 'komandir mitraljeskog voda („Muso“)' },
    ],
    pages: [122, 128],
  },
  {
    key: 'komic',
    foe: 'ndh',
    region: 'lovinac',
    title: 'Udbinska kolona kod Komića',
    short: 'Komić',
    dates: '14. decembra 1942.',
    start: '1942-12-14', end: '1942-12-14',
    about: 'Početkom decembra brigada se vraća u Liku kao Prva udarna brigada Šeste divizije, s novim Trećim i Četvrtim '
      + 'bataljonom, „Božidarom Adžijom“ i „Matijom Gupcem“ iz Četvrtog ličkog odreda. Ustaška posada Udbine, koja je u '
      + 'septembru poklala Jošan, po dogovoru s Talijanima pokušava da se izvuče prema Lovincu i Raduču, gde je čekaju '
      + 'talijanske i ustaške jedinice. Prvi su na nju naišli „Pekiša Vuksan“ i „Matija Gubec“.',
    view: [15.660, 44.385, 15.860, 44.545],
    places: ['Udbina', 'Komić', 'Kurjak', 'Baste', 'Poljice', 'Lovinac', 'Mutilić', 'Gornja Klapavica'],
    base: [
      { t: 'post', at: L.lovinac, label: 'Lovinac: Talijani i ustaše', lp: 's', force: 'it' },
    ],
    steps: [
      {
        date: '14. decembra 1942.', time: '4.00–5.00',
        text: 'U maglovito predjutro ustaški satnik Josip Baljak Ventura izvede iz Udbine 416 ustaša i 940 delimično '
          + 'naoružanih civila i krene prema ustaško-talijanskim jedinicama koje ga po dogovoru čekaju na istočnim '
          + 'prilazima Lovincu i Raduču. Kad kolona od hiljadu i po ljudi izbije pred kurjački zaselak Baste, na nju su, '
          + 'piše štab divizije, zapucale razređene straže Udbinske čete Ličkog odreda. Četvrti bataljon, na maršu od '
          + 'Komića prema Poljicu, tri-četiri kilometra istočnije, između 4 i 5 sati nikakvu pucnjavu nije čuo.',
        notes: [
          'Je li iko pucao kod Basta, nije sigurno: tako piše štab divizije, a vodnik „Matije Gupca“ Stevo Kokotović '
            + 'tvrdi da seoske straže nisu ni pokušale.',
          'Baste su na topografskoj karti JNA 1:25.000 zaselak Kurjaka, na raskršću puteva prema Ploči i prema '
            + 'Komiću; Basta kod Jurinovca, bliže Udbini, na putu je kolone pre njega.',
          'Knjiga kaže da su na prve pucnje kod Komića u taj rejon upućeni Drugi i Četvrti bataljon, „zatečen u '
            + 'Paklariću“; Drugi je zato nacrtan u Paklariću, a njegova Druga četa, koja tek polazi, u Komiću.',
          'Paklarić je dolina istočno od Mirkače i Opačić vrha, sa zaseocima Pavlice, Račići, Šarići i Krtinići; '
            + 'nacrtan je po topografskoj karti JNA 1:25.000. Na putu je od Poljica prema Klapavici, kuda je Četvrti bataljon išao.',
          'Put kolone od Udbine do Basta nacrtan je približno.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'march', path: [L.udbina, [15.7560, 44.5120], [15.7390, 44.4905], [15.7341, 44.4861], L.baste],
            label: '416 ustaša i 940 civila', lp: 'e', at: 0.4, force: 'ndh', guess: true },
          { t: 'move', side: 'friend', kind: 'march', path: [L.komic, [15.7650, 44.4540], L.poljice], label: 'IV bat.', lp: 'n', at: 0.5, guess: true },
          { t: 'area', side: 'own', at: L.paklaric, rx: 0.4, ry: 0.25, label: 'II bat. (Paklarić)', lp: 'e', id: 'II', guess: true },
          // the company goes with the battalion when Palija takes all its companies to Mirkača (step 2)
          { t: 'area', side: 'own', at: L.komic, rx: 0.2, ry: 0.13, label: '2/II', lp: 'n', id: '2/II', until: 2 },
        ],
      },
      {
        date: '14. decembra 1942.', when: 'zatim',
        text: 'Bilo zbog pucnjave kod Basta, bilo zato što se ustaški komandanti boje da kolonu uvedu u uski klanac Tušice '
          + 'prema Ploči, kolona skrene na jug, prema Komiću, da se kroz usek Čatrnju, između Komače i Malog Romića, '
          + 'probije prema Lovincu. Prva s njom uđe u borbu Druga četa „Pekiše Vuksana“ (komandir Đurika Potkonjak, '
          + 'komesar Gojko Milekić), koja je upravo krenula iz Komića preko Poljica prema Klapavicama i Paklariću, za '
          + 'Četvrtim bataljonom.',
        notes: [
          'Na topografskoj karti JNA 1:25.000 Čatrnja je izvor (826 m) u useku između Komače (1177 m) i Malog Komića '
            + '(1026 m); „Mali Romić“ u knjizi je Mali Komić. Južno od useka je udolina Korita, pa Okrugla. Tušice nema ni na '
            + 'toj karti.',
          'Gde je četa dočekala kolonu, knjiga ne kaže; nacrtana je kod Komića, odakle je pošla.',
        ],
        marks: [
          { t: 'move', side: 'enemy', kind: 'march', path: [L.baste, [15.7175, 44.4835], [15.7250, 44.4700], L.komic, L.catrnja],
            label: 'udbinska kolona', lp: 'w', at: 0.3, force: 'ndh', guess: true },
          { t: 'move', side: 'own', kind: 'fire', path: [[15.7520, 44.4535], [15.7445, 44.4515]], label: '2/II', lp: 'e', at: 0, guess: true },
          { t: 'fight', at: L.komic },
          { t: 'spot', at: L.catrnja, label: 'Čatrnja', lp: 'w' },
        ],
      },
      {
        date: '14. decembra 1942.', when: 'u magli',
        text: 'Na prve pucnje kod Komića u taj rejon krenu Drugi i Četvrti bataljon. Ilija Palija je čete „Pekiše '
          + 'Vuksana“, „maglom zagrnute“, lukavo „privukao neprijatelju i stjerao neprijatelja s položaja Mirkače preko '
          + 'Poljane i Čatrnje“. Pružajući grčevit otpor, ustaše zaposednu Okruglu (969 m), nad južnim izlazom iz '
          + 'Čatrnje, i Kopjuv (1007 m), i bataljon se tu bori više sati. Istovremeno dva bataljona Druge brigade hitaju '
          + 'preko Mirkače (1130 m) u rejon Korita.',
        notes: [
          'Na karti JNA Okrugla ima 967 m (knjiga: 969), Mirkača 1131 m (knjiga: 1130), a Kopjuv je Kapljuv, 1003 m '
            + '(knjiga: 1007), jugoistočno od Okrugle. Korita su udolina između Malog Komića, Mirkače i Okrugle.',
          'Poljane nema ni na karti JNA.',
          'Odakle je bataljon napao Mirkaču i odakle su došla dva bataljona Druge brigade, knjiga ne kaže.',
        ],
        marks: [
          { t: 'kota', at: L.mirkaca, label: '1130 Mirkača', lp: 'e' },
          { t: 'kota', at: L.okrugla, label: '969 Okrugla', lp: 'w' },
          { t: 'kota', at: L.kopjuv, label: '1007 Kopjuv', lp: 'e' },
          { t: 'move', side: 'own', kind: 'attack', path: [L.paklaric, [15.7575, 44.4345], L.mirkaca, [15.7420, 44.4352], L.catrnja], guess: true },
          { t: 'move', side: 'enemy', kind: 'back', path: [L.mirkaca, L.korita, L.okrugla], force: 'ndh', guess: true },
          { t: 'area', side: 'enemy', at: L.okrugla, rx: 0.35, ry: 0.2, label: 'ustaše', lp: 'w', force: 'ndh' },
          { t: 'area', side: 'enemy', at: L.kopjuv, rx: 0.35, ry: 0.2, label: 'ustaše', lp: 'e', force: 'ndh' },
          { t: 'area', side: 'own', at: L.korita, rx: 0.4, ry: 0.22, label: 'II bat.', lp: 'n', id: 'II', guess: true },
          { t: 'move', side: 'ally', kind: 'march', path: [[15.7900, 44.4470], [15.7720, 44.4410], L.mirkaca, L.korita],
            label: 'dva bataljona 2. ličke br.', lp: 's', at: 0.3, guess: true },
        ],
      },
      {
        date: '14. decembra 1942.', time: 'oko 12.00',
        text: 'Oko podne na produženje desnog krila Drugog bataljona stigne Četvrti: „krenuo sjevernim padinama kote '
          + 'Mirkača i napao neprijateljsku komoru, koja je svojim zadnjim dijelom izlazila iz Komića“. Deo „Matije '
          + 'Gupca“ izbije na jugoistočni kraj sela, „braneći selo od paljevine i protjerivajući ustaške bande“.',
        notes: ['Desno krilo Drugog bataljona knjiga ne smešta; Četvrti je nacrtan kako ga opisuje, severnim padinama '
          + 'Mirkače od Paklarića prema Komiću.'],
        marks: [
          { t: 'move', side: 'friend', kind: 'attack', path: [L.paklaric, [15.7690, 44.4400], [15.7600, 44.4440], [15.7480, 44.4490], [15.7425, 44.4505]],
            label: 'IV bat.', lp: 'n', at: 0.45, guess: true },
          { t: 'move', side: 'enemy', kind: 'march', path: [L.komic, [15.7350, 44.4420], L.catrnja], label: 'komora', lp: 'w', at: 0.4, force: 'ndh', guess: true },
        ],
      },
      {
        date: '14. decembra 1942.', when: 'u rane popodnevne sate',
        text: 'Četvrtom bataljonu neočekivano „došao s leđa neprijatelj preko kota iz Lovinca“, i bataljon pređe u '
          + 'defanzivu. Uz sav napor dva bataljona Prve i dva Druge brigade ishod nije bio naročit: nije bilo jedinstvene '
          + 'komande ni veza među bataljonima, i ustaše umaknu prema Lovincu.',
        notes: ['Kuda je neprijatelj iz Lovinca došao, i kuda je kolona otišla, knjiga ne kaže; strele su nacrtane '
          + 'približno.'],
        marks: [
          { t: 'move', side: 'enemy', kind: 'attack', path: [L.lovinac, [15.7050, 44.4150], [15.7250, 44.4400], [15.7430, 44.4475]],
            label: 'iz Lovinca', lp: 'w', at: 0.3, guess: true },
          { t: 'move', side: 'friend', kind: 'back', path: [[15.7430, 44.4500], [15.7560, 44.4470]], label: 'IV bat.', lp: 'n', guess: true },
          { t: 'move', side: 'enemy', kind: 'march', path: [L.okrugla, [15.7100, 44.4050], L.lovinac], label: 'ustaše umiču', lp: 'e', at: 0.5, force: 'ndh', guess: true },
        ],
      },
    ],
    enemy: [
      'Udbinska ustaška posada satnika Josipa Baljka Venture: 416 ustaša i 940 delimično naoružanih civila '
        + '(„mobilizirano i naoružano sve stanovništvo sposobno za borbu“)',
      'Ustaško-talijanske jedinice na istočnim prilazima Lovincu i Raduču, koje su kolonu čekale',
    ],
    friends: [
      'Četvrti bataljon „Matija Gubec“: od Paklarića, severnim padinama Mirkače, na komoru kod Komića',
      'Dva bataljona Druge ličke brigade: preko Mirkače u rejon Korita',
      'Straže Udbinske čete Ličkog partizanskog odreda kod Basta',
    ],
    result: 'Udbinske ustaše umakle su ovoga puta „ne plativši dug“: po talijanskim dokumentima imale su 9 poginulih, '
      + 'među njima jednog satnika, 14 ranjenih i „nekoliko nestalih“; po štabu korpusa zarobljen je jedan vojnik. Prva '
      + 'brigada nije imala gubitaka; Druga je imala dva poginula i deset ranjenih.',
    pages: [142, 144],
  },
  {
    key: 'raduc',
    foe: 'it',
    region: 'lovinac',
    title: 'Na pruzi kod Raduča',
    short: 'Raduč',
    dates: '25–30. decembra 1942.',
    start: '1942-12-25', end: '1942-12-30',
    about: 'Talijani se spremaju da napuste Liku, a Šesta divizija treba da ovlada prugom od Medka do Gračaca. Na '
      + 'katolički Božić, 25. decembra u 17 sati, kad se računa da je pažnja branilaca posle božićnog ručka najslabija, '
      + 'brigade napadaju uporišta duž pruge. Prva napada utvrđenu železničku stanicu Raduč, a „Pekiša Vuksan“ treba da '
      + 'je zaštiti od Metka, odakle dolaze ustaše, domobrani i Talijani divizije „Re“.',
    view: [15.495, 44.385, 15.685, 44.475],
    places: ['Raduč', 'Kruškovac', 'Bagunica', 'Papuča', 'Drenovac Radučki', 'Gornja Ploča', 'Parčići', 'Mogorić', 'Medak', 'Lovinac', 'Miletić', 'Sveti Rok'],
    base: [
      { t: 'post', at: L.station, label: 'stanica Raduč: Talijani i četnici', lp: 's', force: 'it' },
    ],
    steps: [
      {
        date: '25. decembra 1942.', when: 'pred napad',
        text: 'Brigada se prikupi u Ploči, odakle je poljskim putem sedam kilometara do stanice Raduč, preko gole, '
          + 'spržene visoravni na 600 metara, s kamenom gromadom Žira (852 m) na pola puta. Naređenje je: s Gospićkim '
          + 'bataljonom Ličkog odreda, topom 75 mm i minerskim vodom napasti stanicu i bunker kod mosta zapadno od nje, '
          + 'porušiti cestu i prugu i postaviti osiguranje prema Metku. Napad na svim sektorima počinje u 17 sati.',
        notes: ['Ploča je ovde selo Gornja Ploča (OpenStreetMap); Žir je na OpenStreetMap Zir, 850 m (knjiga: 852).',
          'Put od Ploče do stanice nacrtan je približno.'],
        marks: [
          { t: 'area', side: 'friend', at: L.ploca, rx: 0.55, ry: 0.32, label: 'brigada, s II bat.', lp: 'e', until: 1 },
          { t: 'kota', at: L.zir, label: '852 Žir', lp: 'e' },
          { t: 'move', side: 'friend', kind: 'march', path: [L.ploca, L.zir, L.station], at: 0.5, guess: true },
        ],
      },
      {
        date: '25. decembra 1942.', time: '17.00',
        text: '„Pekiša Vuksan“ zaposedne položaje kod Kruškovca, par kilometara zapadno od stanice, rastera neprijatelja '
          + 's okolnih čuka i rasporedi se prema Metku tako da može, „ustreba li, a ustrebat će“, odbiti napade od Metka. '
          + 'Između njega i stanice „Božidar Adžija“ treba da posedne prugu i da napadne bunkere na njoj, a „Matija Gubec“ '
          + 'zaposeda kote 706, 592 i 601 da spreči odstupanje neprijatelja. Talijane i četnike u stanici napada „Marko '
          + 'Orešković“, s topom pratećeg voda divizije, ali uzalud: pred bunkerima pogine šest krntijaša. Radne grupe '
          + 'te večeri razore 1600 metara pruge i sruše most dug 12 metara.',
        notes: [
          '„Od Metka“ i „u Metku“ su padeži od Medak (kao redak, retka): do stanice Medak je od stanice Raduč osam '
            + 'kilometara, koliko knjiga i kaže. Napadi od Medka zato dolaze sa severozapada, uz prugu.',
          'Naređenje brigadi stavlja kote 706 i 592 kod Bogunice, a Četvrti bataljon drži kote 706, 592 i 601. Na '
            + 'topografskoj karti JNA 1:25.000 kota 706 je vis Bagunica južno od sela (703 m), nad Papučom, odakle su '
            + 'bataljon napali četnici, a kota 592 Visoko brdo severno od sela i pruge (592,0). Knjiga kaže da su kote '
            + '„jugozapadno od stanice“; Bogunica je zapadno od nje.',
          'Kote 601 nema na karti JNA, čije se visine od ratnih karata razlikuju za po nekoliko metara (706 i 703). '
            + 'Nacrtana je na koti 599,6 istočno od Uzelaca, kod izvora Popovac, između Bogunice i Kruškovca; mogla bi '
            + 'biti i kota 602 kod Potrebića, zapadno od Bagunice.',
          'Za Treći bataljon knjiga kaže samo: na pruzi, između stanice i Drugog bataljona. Gde su razorena pruga i '
            + 'most, ne kaže; naređenje je bilo da se pruga poruši „ispred sela Kruškovca“.',
        ],
        marks: [
          // the first positions stand until the battalions are redeployed on the 29th (step 6), which the book doesn't
          // tell battalion by battalion
          { t: 'area', side: 'own', at: L.kruskovac, rx: 0.5, ry: 0.28, rot: -30, label: 'II bat.', lp: 'n', until: 6 },
          { t: 'area', side: 'friend', at: [15.5860, 44.4260], rx: 0.45, ry: 0.2, rot: -35, label: 'III bat.', lp: 's', guess: true, until: 6 },
          // the battalion on its three kote, across Bogunica and the railway; a company on each is the map's guess
          { t: 'area', side: 'friend', at: L.k706, rx: 0.3, ry: 0.2, label: 'IV bat.', lp: 'w', guess: true, until: 6, id: 'IV-706' },
          { t: 'area', side: 'friend', at: L.k592, rx: 0.3, ry: 0.2, guess: true, until: 6, id: 'IV-592' },
          { t: 'area', side: 'friend', at: L.k601, rx: 0.3, ry: 0.2, guess: true, until: 6, id: 'IV-601' },
          { t: 'kota', at: L.k706, label: '706', lp: 'e' },
          { t: 'kota', at: L.k592, label: '592', lp: 'e' },
          { t: 'kota', at: L.k601, label: '601', lp: 'e', guess: true },
          { t: 'move', side: 'friend', kind: 'stopped', path: [[15.6170, 44.4250], [15.6090, 44.4200], [15.6045, 44.4170]],
            label: 'I bat.', lp: 'e', at: 0.2, guess: true },
          { t: 'cut', path: [[15.5960, 44.4205], [15.5880, 44.4250], [15.5790, 44.4300]], label: '1600 m pruge', lp: 's', guess: true },
        ],
      },
      {
        date: '26. decembra 1942.', when: 'ujutro',
        text: 'Od Metka od jutra nadiru ustaško-domobranske jedinice. General Pelligra, koji u Metku ima dva pešadijska '
          + 'bataljona i dve mitraljeske čete divizije „Re“, pošalje vozom 2. domobransku lovačku bojnu. Voz dočekaju '
          + 'delovi brigade nekoliko kilometara jugoistočno od Metka, kod Bogunice, gde pruga prelazi Vedošića potok: '
          + 'strojovođa je smrtno ranjen, ali vrati voz u Medak, a oko 800 ustaša i domobrana pređe u oštar napad.',
        notes: ['Koji su delovi brigade dočekali voz, knjiga ne kaže. Vedošića potok je na topografskoj karti JNA 1:25.000 '
          + 'Vedašica; voz je nacrtan gde ga pruga prelazi, kod Bogunice.'],
        marks: [
          { t: 'train', at: [15.5524, 44.4428], label: 'voz s 2. lovačkom bojnom', lp: 'n', force: 'ndh', guess: true },
          { t: 'move', side: 'enemy', kind: 'attack', path: [[15.5180, 44.4530], [15.5350, 44.4450], [15.5500, 44.4385]],
            label: 'oko 800 ustaša i domobrana', lp: 'n', at: 0.2, force: 'ndh', guess: true },
          { t: 'fight', at: [15.5524, 44.4428] },
        ],
      },
      {
        date: '26. decembra 1942.', when: 'zatim',
        text: 'Jedna ustaška kolona vešto se ubaci u pozadinu „Matije Gupca“. Prva četa Četvrtog bataljona na koti 706 '
          + 'ne odoli, jer je u taj mah s leđa napadnu četnici iz Papuče; opkoljena, krene u napad na ustaše i bije se '
          + 'prsa u prsa. Pogine vodnik Ivica Blažević iz Smiljana, a dok ga izvlače, sedamnaestogodišnji Mićo Lemić '
          + 'Tubonjin i njegov otac Petar. Tešku situaciju reši Treća četa, koju zamenik komandira Đuro Lemić povede u '
          + 'napad: ustaše se povuku s kote 706 prema Metku i odvedu dvojicu zarobljenih boraca, Danu Brujića i Niku '
          + 'Vuksana, koji su u Gospiću posle mučenja streljani.',
        notes: ['Odakle je ustaška kolona ušla u pozadinu Četvrtog bataljona i odakle je napala Treća četa, knjiga ne kaže.'],
        marks: [
          { t: 'move', side: 'enemy', kind: 'attack', path: [[15.5290, 44.4450], [15.5320, 44.4385], [15.5385, 44.4345]],
            label: 'ustaška kolona', lp: 'w', at: 0.3, force: 'ndh', guess: true },
          { t: 'move', side: 'enemy', kind: 'attack', path: [L.papuca, [15.5440, 44.4300], [15.5420, 44.4335]], label: 'četnici iz Papuče', lp: 's', at: 0, force: 'cet' },
          { t: 'fight', at: L.k706 },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.5500, 44.4300], [15.5455, 44.4330], [15.5410, 44.4365]],
            label: '3/IV (Đ. Lemić)', lp: 'ne', at: 0.1, guess: true },
          { t: 'move', side: 'enemy', kind: 'back', path: [L.k706, [15.5300, 44.4430], [15.5180, 44.4530]], force: 'ndh', guess: true },
        ],
      },
      {
        date: '26. decembra 1942.', when: 'pred mrak',
        text: 'Kod stanice Prva četa Prvog bataljona pođe za komesarom Ilijom Radakovićem („Komunisti i skojevci, za '
          + 'mnom!“) na bunkere uz vijadukt i, zasuta bombama, odbrana ne odoli. Pred mrak svi bunkeri oko stanice su '
          + 'zauzeti; uveče minerski vod digne u vazduh železni most na Jadovi. Stanica ostaje u talijanskim rukama.',
        notes: ['Gde su vijadukt i most na Jadovi, knjiga ne kaže; nisu nacrtani. Reku koju OpenStreetMap zove Jadova '
          + '(na karti JNA Glamočnica) pruga prelazi kod stanice Medak, pod italijanskim garnizonom.'],
        marks: [
          { t: 'post', at: [15.5995, 44.4185], label: 'bunkeri oko stanice', lp: 'e', taken: true, small: true, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.6100, 44.4230], [15.6040, 44.4200], [15.6000, 44.4188]], label: '1/I', lp: 'n', at: 0.2, guess: true },
        ],
      },
      {
        date: '27. decembra 1942.', when: 'preko dana',
        text: 'Kad su čete „Matije Gupca“ odbacile ustaše prema Metku, vršilac dužnosti komandanta Četvrtog bataljona '
          + 'Mane Pražić i komandant Drugog Ilija Palija povedu sve snage na četnike u rejonu Papuče. Trećeg dana borbe '
          + 'brigada ima protiv sebe Talijane, ustaše i četnike, i talijansku avijaciju; jedan avion oboren je između '
          + 'Raduča i Lovinca. Pešadija dobije tenkove i oklopni voz: dva tenka uništi protivtenkovskim topom komandir '
          + 'odeljenja Viktor Ostojić, a oklopni voz, zaustavljen gde je pruga razorena i zasut vatrom s obe strane, brzo '
          + 'se vrati u Medak. Tog dana brigada ima 6 mrtvih i 16 ranjenih.',
        notes: [
          'Odakle su Drugi i Četvrti bataljon napali Papuču, knjiga ne kaže.',
          'Gde su uništeni tenkovi, knjiga ne kaže; oklopni voz je nacrtan na pruzi kod Kruškovca, gde je bila razorena.',
        ],
        marks: [
          { t: 'area', side: 'enemy', at: L.papuca, rx: 0.3, ry: 0.18, label: 'četnici', lp: 's', force: 'cet', until: 6 },
          { t: 'move', side: 'own', kind: 'attack', path: [[15.5650, 44.4290], [15.5560, 44.4275], [15.5485, 44.4265]],
            label: 'II bat.', lp: 's', at: 0.2, guess: true },
          { t: 'move', side: 'friend', kind: 'attack', path: [[15.5440, 44.4385], [15.5450, 44.4320], [15.5455, 44.4285]],
            label: 'IV bat.', lp: 'w', at: 0.75, guess: true },
          { t: 'train', at: [15.5735, 44.4344], label: 'oklopni voz', lp: 'n', armoured: true, force: 'it', guess: true },
        ],
      },
      {
        date: '28–29. decembra 1942.',
        text: 'Borbe se vode i četvrtog dana, a zatim štab divizije oceni da je zadatak uglavnom izvršen i da brigade '
          + 'mogu postepeno da se izvlače. Naređenje 29. decembra: jedan bataljon u Kruškovac, da zadržava neprijatelja i '
          + 'pred njim se povlači prema Raduču i u Miletić Gaju ili Svetom Roku se poveže s Drugom brigadom; jedan u '
          + 'Parčiće, s patrolama prema stanici; dva u Ploču i Mogorić. Pre nego što jedinice napuste položaje, „od '
          + 'neprestane artiljerijske vatre iz Metka i velikih bacača iz Raduča“ poginu dva borca, a osam je ranjeno.',
        view: [15.495, 44.345, 15.705, 44.475],
        notes: [
          'Koji je bataljon gde ostao, knjiga ne kaže; Drugi zato nije posebno označen.',
          'Miletić Gaj je zaselak Miletić kod Svetog Roka (OpenStreetMap). Pravac povlačenja je iz naređenja; put preko '
            + 'Raduča do Miletića nacrtan je približno.',
        ],
        marks: [
          { t: 'area', side: 'friend', at: L.kruskovac, rx: 0.35, ry: 0.2, label: 'jedan bataljon u Kruškovcu', lp: 'sw', id: 'kruskovac' },
          { t: 'move', side: 'friend', kind: 'back', path: [L.kruskovac, [15.5790, 44.4110], L.raduc, [15.6150, 44.3800], L.miletic],
            label: 'zadržava, pa prema Miletić Gaju', lp: 'e', at: 0.62, guess: true },
          { t: 'area', side: 'friend', at: L.parcici, rx: 0.35, ry: 0.2, label: 'jedan bataljon u Parčićima', lp: 's', id: 'parcici' },
          { t: 'area', side: 'friend', at: L.ploca, rx: 0.35, ry: 0.2, label: 'dva bataljona, Ploča i Mogorić', lp: 'e' },
          { t: 'area', side: 'friend', at: L.mogoric, rx: 0.35, ry: 0.2 },
          { t: 'move', side: 'enemy', kind: 'fire', path: [[15.5250, 44.4520], [15.5600, 44.4335]], label: 'artiljerija iz Metka', lp: 'n', at: 0.3, guess: true },
          { t: 'move', side: 'enemy', kind: 'fire', path: [L.station, [15.5760, 44.4290]], label: 'bacači iz Raduča', lp: 's', at: 0.5 },
        ],
      },
      {
        date: '30. decembra 1942.', time: '8.00',
        text: 'U 8 sati neprijatelj krene iz Metka u tri kolone, koje su napadnute samo mestimično, s bokova. Šesta '
          + 'divizija više nema snage da se održi: borci su promrzli, šesti dan bez krova nad glavom, neredovno hranjeni '
          + 'i slabo odeveni, a vreme je vedro, s vrlo niskim temperaturama. Brigade se povuku prema Bruvnu i Udbini, a '
          + 'Talijani s ustašama i četnicima, uz gubitke od 30 mrtvih i još više ranjenih, probiju se preko Raduča u '
          + 'Lovinac i Ričice, gde se spoje s divizijom „Sassari“, koja s četnicima nastupa od Gračaca. Bataljoni Prve '
          + 'brigade razmeste se u Mogoriću, Vrepcu, Pavlovcu, Buljmizama i Zavalju.',
        notes: ['Putevi kolona i povlačenja nacrtani su približno; knjiga ih ne opisuje. Bruvno je izvan ovog lista.'],
        marks: [
          { t: 'move', side: 'enemy', kind: 'attack', path: [[15.5100, 44.4565], [15.5500, 44.4420], [15.5900, 44.4235], L.station, [15.6400, 44.3950], L.lovinac],
            label: 'tri kolone iz Metka', lp: 'n', at: 0.15, guess: true },
          { t: 'move', side: 'friend', kind: 'back', path: [L.kruskovac, [15.5750, 44.4600], L.mogoric], label: 'u Mogorić', lp: 'w', at: 0.5, guess: true },
          { t: 'move', side: 'friend', kind: 'back', path: [L.ploca, [15.6700, 44.4720]], label: 'prema Udbini', lp: 'e', at: 0.6, guess: true },
        ],
      },
    ],
    enemy: [
      'Uporište Raduč: železnička stanica s bunkerima, rovovima i žicom, „snabdjevena velikim brojem automatskih '
        + 'oruđa“; Talijani i četnici',
      'U Metku dva pešadijska bataljona i dve mitraljeske čete divizije „Re“ (general Raffaele Pelligra); 26. decembra '
        + '2. domobranska lovačka bojna, vozom, i oko 800 ustaša i domobrana',
      'Četnici u Papuči',
      '27. decembra talijanska avijacija, tenkovi i oklopni voz',
      '30. decembra tri kolone iz Metka; od Gračaca divizija „Sassari“ s četnicima',
    ],
    friends: [
      'Prvi bataljon „Marko Orešković“, s topom 75 mm pratećeg voda divizije: napad na stanicu Raduč',
      'Treći bataljon „Božidar Adžija“: pruga i bunkeri između stanice i Drugog bataljona',
      'Četvrti bataljon „Matija Gubec“: kote 706, 592 i 601',
      'Gospićki bataljon Ličkog odreda, minerski vod i četa za vezu',
      'Druga i Treća brigada Šeste divizije: napadi duž pruge prema Lovincu, Ričicama i Guduri',
    ],
    result: 'Pruga je bila prekinuta pet dana: razoreno je 1600 metara pruge, srušena su dva mosta i zauzeti bunkeri oko '
      + 'stanice Raduč. Stanicu brigada nije zauzela, i 30. decembra Talijani, ustaše i četnici probili su se do Lovinca. '
      + 'Od 25. do 30. decembra brigada je imala 17 poginulih i 45 ranjenih, a ustaše su zarobile dvojicu „Gupčevih“ '
      + 'boraca. Štab divizije javio je da borcima treba nekoliko dana odmora, „ne toliko zbog umorenosti, nego zbog '
      + 'uređivanja obuće, jer su borci zbog rđavog vremena obosili“.',
    wounded: [
      { name: 'Njegovan Nikola', id: '0002005831', note: 'vršilac dužnosti komandira' },
    ],
    pages: [148, 153],
  },
]
