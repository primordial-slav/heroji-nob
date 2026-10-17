// Prva lička proleterska brigada „Marko Orešković“: its path and its command, for /jedinica/prva-licka-brigada
// (local only). Sources: the brigade's own book, Jovo Popović, Prva lička proleterska brigada „Marko Orešković“
// (Beograd 1988, the site's prva-licka-proleterska.pdf; `p` is the PDF page, the printed page is about 8 more), its
// list of fighters (the entries, `id`), and the NOVJ order of battle (Anić, Joksimović, Gutić, znaci 00003/523: the
// brigade's row 7 and the 6. division's). A post's time is given as the source prints it; none where it gives none.

export interface Person {
  name: string // surname first, as the list prints it
  id?: string // the soldier's record in the unit's list
  when?: string // as printed: "od 19. februara do 24. oktobra 1944"
  start?: string // for the order: YYYY, YYYY-MM or YYYY-MM-DD
  note?: string // what the source adds: wounded, fell, moved on
  hero?: boolean // narodni heroj
  p?: number // the book's PDF page that says so
}

export interface Span {
  name: string
  from: string // YYYY-MM-DD
  to: string
  note?: string
  href?: string
}

export interface Battalion {
  slug: string
  name: string
  short: string
  from: string
  to: string
  origin: string // what it was before the brigade
  after?: string // what became of it
  detail: string[] // the unit_detail values its fighters' entries give
  p?: number
}

export const BOOK = '/pdfs/prva-licka-proleterska.pdf'
export const UNIT_ID = 'prva-licka-brigada'
export const START = '1942-07-01'
export const END = '1945-05-15'

export const NAMES: { from: string; name: string; p?: number }[] = [
  { from: '1942-07-08', name: 'Prva NOU brigada Hrvatske (udarna brigada 1. operativne zone)', p: 9 },
  { from: '1942-11-22', name: '1. lička udarna brigada, u 6. ličkoj diviziji' },
  { from: '1944-03-19', name: '1. lička proleterska brigada „Marko Orešković“', p: 3 },
]

// Who the brigade was under, each a lane of the chart
export const COMMAND: { label: string; spans: Span[] }[] = [
  {
    label: 'Pod komandom',
    spans: [
      { name: '1. operativna zona Hrvatske', from: '1942-07-08', to: '1942-11-22' },
      {
        name: '6. lička divizija', from: '1942-11-22', to: '1945-05-15',
        note: 'od 19. 3. 1944. 6. lička proleterska divizija „Nikola Tesla“; s njom 2. i 3. lička brigada do kraja rata',
      },
    ],
  },
  {
    label: 'Korpus',
    spans: [
      { name: '1. hrvatski korpus', from: '1942-11-22', to: '1943-10-07' },
      { name: '4. korpus', from: '1943-10-07', to: '1943-11-09' },
      { name: '1. proleterski korpus', from: '1943-11-09', to: '1945-01-01' },
    ],
  },
  {
    label: 'Armija',
    spans: [{ name: '1. armija', from: '1945-01-01', to: '1945-05-15' }],
  },
]

export const BATTALIONS: Battalion[] = [
  {
    slug: '1-bataljon', name: '1. bataljon „Marko Orešković“', short: '1. „Marko Orešković“',
    from: '1942-07-08', to: '1945-05-15',
    origin: 'Lički bataljon „Marko Orešković Krntija“, osnovan 23. 11. 1941. Po njemu je brigada kasnije dobila ime.',
    detail: ['1. bataljon'], p: 91,
  },
  {
    slug: '2-bataljon', name: '2. bataljon „Pekiša Vuksan“', short: '2. „Pekiša Vuksan“',
    from: '1942-07-08', to: '1945-05-15',
    origin: 'Lički bataljon „Pekiša Vuksan“.',
    detail: ['2. bataljon'], p: 10,
  },
  {
    slug: '3-kordunaski', name: '3. (kordunaški) bataljon', short: '3. kordunaški',
    from: '1942-07-08', to: '1942-11-18',
    origin: '2. bataljon 1. kordunaškog NOP odreda.', after: 'Vratio se na Kordun 18. 11. 1942.',
    detail: ['3. kordunaški bataljon'], p: 10,
  },
  {
    slug: '4-banijski', name: '4. (banijski) bataljon', short: '4. banijski',
    from: '1942-07-08', to: '1942-11-18',
    origin: 'Udarni bataljon Banijskog NOP odreda.', after: 'Vratio se na Baniju 18. 11. 1942.',
    detail: ['4. banijski bataljon'], p: 10,
  },
  {
    slug: '3-bataljon', name: '3. bataljon „Božidar Adžija“', short: '3. „Božidar Adžija“',
    from: '1942-11-18', to: '1945-05-15',
    origin: 'Otočki bataljon „Božidar Adžija“ 4. ličkog NOP odreda.',
    detail: ['3. bataljon'], p: 55,
  },
  {
    slug: '4-bataljon', name: '4. bataljon „Matija Gubec“', short: '4. „Matija Gubec“',
    from: '1942-11-18', to: '1945-03-15',
    origin: 'Bataljon „Matija Gubec“ 4. ličkog NOP odreda.', after: 'Rasformiran sredinom marta 1945.',
    detail: ['4. bataljon'], p: 470,
  },
  {
    slug: '5-mitraljeski', name: '5. (mitraljeski) bataljon', short: '5. mitraljeski',
    from: '1942-12-15', to: '1943-05-15',
    origin: 'Osnovan 15. 12. 1942. u Klapavicama od mitraljeskih vodova bataljona.',
    after: 'Rasformiran sredinom maja 1943; umesto njega prateća četa.',
    detail: ['5. mitraljeski bataljon'], p: 137,
  },
  {
    slug: '5-ruski', name: '5. (ruski) bataljon', short: '5. ruski',
    from: '1944-04-06', to: '1944-05-17',
    origin: 'Osnovan 6. 4. 1944. od čete zarobljenih i prebeglih vojnika iz nemačke službe.',
    detail: ['5. ruski bataljon'], p: 359,
  },
  {
    slug: '5-makedonski', name: '5. (makedonski) bataljon „Jane Sandanski“', short: '5. „Jane Sandanski“',
    from: '1944-12-07', to: '1945-03-12',
    origin: 'Formirali su ga beogradski Makedonci; u brigadu je ušao 7. 12. 1944. kao njen 5. bataljon. Bio je deveti bataljon koji je brigada imala od osnivanja.',
    after: 'Rasformiran sredinom marta 1945.',
    detail: ['5. makedonski bataljon', 'makedonski bataljon'], p: 466,
  },
]

// The brigade's path, a dated line each
export const EVENTS: { date: string; text: string; p?: number }[] = [
  { date: '1942-06-13', text: 'Štab 1. operativne zone naređuje bataljonima „Marko Orešković Krntija“ i „Pekiša Vuksan“ i 2. bataljonu 1. kordunaškog odreda da se spreme za pokret.', p: 10 },
  { date: '1942-07-08', text: 'Brigada je osnovana kod vrela Mrežnice, kao Prva NOU brigada Hrvatske, od četiri bataljona: dva lička („Marko Orešković“ i „Pekiša Vuksan“), kordunaškog i banijskog.', p: 9 },
  { date: '1942-11-18', text: 'Kordunaški i banijski bataljon se vraćaju u svoje krajeve; u brigadu ulaze bataljoni 4. ličkog odreda, „Božidar Adžija“ kao 3. i „Matija Gubec“ kao 4.', p: 55 },
  { date: '1942-11-22', text: 'Brigada ulazi u novu 6. (ličku) diviziju, s 2. i 9. brigadom NOV Hrvatske; divizija je u 1. hrvatskom korpusu.' },
  { date: '1942-12-15', text: 'Od mitraljeskih vodova bataljona osnovan je 5. (mitraljeski) bataljon. Rasformiran je sredinom maja 1943.', p: 137 },
  { date: '1943-10-07', text: 'Divizija prelazi u 4. korpus, a 9. 11. 1943. u 1. proleterski korpus.' },
  { date: '1944-03-19', text: 'Brigada postaje proleterska, a divizija 6. lička proleterska divizija „Nikola Tesla“.' },
  { date: '1944-04-06', text: 'Od zarobljenih i prebeglih vojnika iz nemačke službe osnovan je 5. (ruski) bataljon; ostao je u brigadi do 17. 5. 1944.', p: 359 },
  { date: '1944-12-07', text: 'U brigadu ulazi makedonski bataljon „Jane Sandanski“, formiran u Beogradu.', p: 466 },
  { date: '1945-01-01', text: 'Divizija je u 1. armiji, do kraja rata.' },
  { date: '1945-03-15', text: 'Rasformirani su bataljoni „Matija Gubec“ i „Jane Sandanski“.', p: 470 },
]

// The brigade's staff. Each list in the order the posts were held; one held twice is listed twice.
export const STAFF: { post: string; people: Person[] }[] = [
  {
    post: 'Komandant',
    people: [
      { name: 'Opsenica Stevan', id: '0002005929', when: 'prvi komandant, do 2. 1. 1943', start: '1942-07-08', hero: true, p: 91 },
      { name: 'Radaković Lazo', id: '0002007032', when: 'od 2. 1. do 20. 9. 1943', start: '1943-01-02', hero: true },
      { name: 'Dimić Milan', id: '0002001484', when: '28. 9. 1943 – 19. 2. 1944', start: '1943-09-28' },
      { name: 'Antončić Milan Velebit', id: '0002000121', when: 'od 19. februara do 24. oktobra 1944', start: '1944-02-19', hero: true },
      { name: 'Čanković Miloš', id: '0002001070', when: 'od 24. oktobra do 27. novembra 1944', start: '1944-10-24', p: 464 },
      { name: 'Zaklan Dmitar', id: '0002009484', when: 'od kraja novembra 1944. do 9. 3. 1945', start: '1944-11-27', hero: true, note: 'Pre toga komandant bataljona i operativni oficir štaba brigade.', p: 464 },
      { name: 'Čanković Miloš', id: '0002001070', when: 'od 10. 3. 1945', start: '1945-03-10' },
    ],
  },
  {
    post: 'Politički komesar',
    people: [
      { name: 'Krunić Uroš', id: '0002003854', when: 'prvi komesar, 13. 6. – 2. 12. 1942', start: '1942-06-13', hero: true, p: 91 },
      { name: 'Brujić Srđan', id: '0002000782', when: 'od 2. 12. 1942. do 12. 2. 1943', start: '1942-12-02', note: 'Povučen u štab divizije.', p: 173 },
      { name: 'Desnica Branko', id: '0002001427', when: 'februar – jun 1943', start: '1943-02', note: 'Teško ranjen u Smiljanu 26. 6. 1943.' },
      { name: 'Pejnović Nikola Nikica', id: '0002006333', when: '1943', start: '1943-07', note: 'Od oktobra 1944. komesar 6. proleterske divizije.' },
      { name: 'Vujnović Bogdan Bogde', id: '0002009344', when: 'od 20. 9. 1943. do 27. 11. 1944', start: '1943-09-20', note: 'Pozvan u Vrhovni štab 23. 11. 1944.', p: 464 },
      { name: 'Grković Jovica', id: '0002009806', when: 'od 25. novembra 1944, poslednji ratni komesar', start: '1944-11-25', p: 464 },
    ],
  },
  {
    post: 'Zamenik komandanta',
    people: [
      { name: 'Karaš Milutin', id: '0002003451', when: 'septembar – oktobar 1942', start: '1942-09', note: 'Poginuo marta 1945. kao načelnik štaba 34. divizije.', p: 91 },
      { name: 'Hohštetner Vojko', id: '0002002522', when: 'od kraja oktobra do 2. 12. 1942', start: '1942-10-25', note: 'Poginuo 1944.' },
      { name: 'Bobić Milan', id: '0002000493', when: 'decembar 1942', start: '1942-12', note: 'Poginuo januara 1945. u Baranji kao komandant Osječke brigade.' },
      { name: 'Bubalo Rade', id: '0002000791', when: 'od 2. 1. do 16. 3. 1943', start: '1943-01-02', note: 'Poginuo 16. 3. 1943. u Svetom Roku.' },
      { name: 'Šijan Milan', id: '0002008480', when: 'od marta do juna 1943', start: '1943-03', hero: true },
      { name: 'Rakić Dragan', id: '0002007340', when: 'od juna 1943. do marta 1944', start: '1943-06', hero: true },
      { name: 'Čanković Miloš', id: '0002001070', when: 'od 14. do 24. oktobra 1944, i od kraja novembra 1944. do 9. 3. 1945', start: '1944-10-14', p: 464 },
    ],
  },
  {
    post: 'Zamenik komesara (od decembra 1944. pomoćnik komesara)',
    people: [
      { name: 'Uzelac Milan Brico', id: '0002009051', when: 'prvi zamenik, od 24. 8. 1942', start: '1942-08-24', note: 'Poginuo 1944. kao obaveštajni oficir Glavnog štaba Hrvatske.', p: 91 },
      { name: 'Čanković Marko', id: '0002001069', when: 'od 15. 11. 1942. do kraja januara 1943', start: '1942-11-15', note: 'Poginuo u Dalmaciji oktobra 1943.' },
      { name: 'Vujnović Bogdan Bogde', id: '0002009344', when: 'od sredine januara do kraja septembra 1943, kao partijski rukovodilac brigade', start: '1943-01-15', p: 464 },
      { name: 'Mrđa Simo', id: '0002005446', when: 'septembar 1943 – 8. januar 1944', start: '1943-09' },
      { name: 'Božović Časlav', id: '0002000703', when: 'od 15. 1. do 24. 10. 1944', start: '1944-01-15', p: 324 },
      { name: 'Grubić Milan', id: '0002002428', when: 'pomoćnik komesara, od 24. 10. 1944. do pobede', start: '1944-10-24', p: 463 },
    ],
  },
  {
    post: 'Načelnik štaba',
    people: [
      { name: 'Bursać Jovo', id: '0002000862', when: 'prvi načelnik štaba, od aprila do 1. novembra 1944', start: '1944-04', p: 454 },
      { name: 'Drobac Đuro', id: '0002001654', when: '1. 11. 1944. do 7. 1. 1945', start: '1944-11-01', p: 468 },
      { name: 'Medić Mirko Cukić', id: '0002004721', when: 'poslednji ratni načelnik štaba; došao iz Kosmajske brigade', start: '1945-01', p: 500 },
    ],
  },
]

// The staff's posts as spans for the chart on the Štab page: from the dates above; `guess` where an end or a start is
// only the next holder's start, or the months are worked out (Pejnović: "1943", between Desnica and Vujnović)
export const STAFF_CHART: { post: string; spans: { name: string; from: string; to: string; guess?: boolean }[] }[] = [
  {
    post: 'Komandant',
    spans: [
      { name: 'Opsenica', from: '1942-07-08', to: '1943-01-02' },
      { name: 'L. Radaković', from: '1943-01-02', to: '1943-09-20' },
      { name: 'Dimić', from: '1943-09-28', to: '1944-02-19' },
      { name: 'Antončić', from: '1944-02-19', to: '1944-10-24' },
      { name: 'Čanković', from: '1944-10-24', to: '1944-11-27' },
      { name: 'Zaklan', from: '1944-11-27', to: '1945-03-09' },
      { name: 'Čanković', from: '1945-03-10', to: '1945-05-15' },
    ],
  },
  {
    post: 'Politički komesar',
    spans: [
      { name: 'Krunić', from: '1942-07-08', to: '1942-12-02' },
      { name: 'Brujić', from: '1942-12-02', to: '1943-02-12' },
      { name: 'Desnica', from: '1943-02-12', to: '1943-06-26' },
      { name: 'Pejnović', from: '1943-06-26', to: '1943-09-20', guess: true },
      { name: 'Vujnović', from: '1943-09-20', to: '1944-11-25' },
      { name: 'Grković', from: '1944-11-25', to: '1945-05-15' },
    ],
  },
  {
    post: 'Zamenik komandanta',
    spans: [
      { name: 'Karaš', from: '1942-09-01', to: '1942-10-25' },
      { name: 'Hohštetner', from: '1942-10-25', to: '1942-12-02' },
      { name: 'Bobić', from: '1942-12-02', to: '1943-01-02', guess: true },
      { name: 'Bubalo', from: '1943-01-02', to: '1943-03-16' },
      { name: 'Šijan', from: '1943-03-16', to: '1943-06-15' },
      { name: 'Rakić', from: '1943-06-15', to: '1944-03-15' },
      { name: 'Čanković', from: '1944-10-14', to: '1944-10-24' },
      { name: 'Čanković', from: '1944-11-27', to: '1945-03-09' },
    ],
  },
  {
    post: 'Zamenik komesara',
    spans: [
      { name: 'Uzelac', from: '1942-08-24', to: '1942-11-15', guess: true },
      { name: 'M. Čanković', from: '1942-11-15', to: '1943-01-31' },
      { name: 'Vujnović', from: '1943-01-31', to: '1943-09-30' },
      { name: 'Mrđa', from: '1943-09-30', to: '1944-01-08' },
      { name: 'Božović', from: '1944-01-15', to: '1944-10-24' },
      { name: 'Grubić', from: '1944-10-24', to: '1945-05-15' },
    ],
  },
  {
    post: 'Načelnik štaba',
    spans: [
      { name: 'Bursać', from: '1944-04-01', to: '1944-11-01' },
      { name: 'Drobac', from: '1944-11-01', to: '1945-01-07' },
      { name: 'Medić', from: '1945-01-07', to: '1945-05-15', guess: true },
    ],
  },
]

// Each battalion's command, where the book and the entries give it (the rest of the posts come from the entries,
// _data/<id>.posts.json). 10. 10. 1942: footnote 278, the brigade's staffs on that day (p. 91).
export const BATTALION_STAFF: Record<string, { post: string; people: Person[] }[]> = {
  '1-bataljon': [
    {
      post: 'Komandant',
      people: [
        { name: 'Jovanić Đoko', id: '0002003148', when: 'u prvom sastavu', start: '1942-07', hero: true },
        { name: 'Damjanović Danilo Danić', id: '0002001311', when: '1942', start: '1942-08', hero: true, note: 'Poslat na školovanje u Lapac, oktobra 1942.', p: 92 },
        { name: 'Marčetić Mile', id: '0002004401', when: 'oktobar – novembar 1942, i mart – april 1943', start: '1942-10', note: '10. 10. 1942. zastupnik komandanta.', p: 91 },
        { name: 'Šijan Milan', id: '0002008480', when: 'januar – mart 1943', start: '1943-01', hero: true },
        { name: 'Tankosić Milan', id: '0002008648' },
        { name: 'Žunić Jandre', id: '0002009789', when: 'od 9. 8. 1944', start: '1944-08-09', note: 'Poginuo u Beogradu 20. 10. 1944.', p: 427 },
        { name: 'Vukelić Branko Bato', id: '0002009371', when: '1. 11. 1944 – 16. 3. 1945', start: '1944-11-01' },
        { name: 'Pavković Nikola', id: '0002006174', when: 'od 16. 3. 1945', start: '1945-03-16' },
      ],
    },
    {
      post: 'Politički komesar',
      people: [
        { name: 'Šijan Milan', id: '0002008480', when: 'u prvom sastavu', start: '1942-07', hero: true },
        { name: 'Radaković Ilija', id: '0002007028', when: '10. 10. 1942', start: '1942-10', hero: true, p: 91 },
        { name: 'Cvjetićanin Petar Perica', id: '0002001041', when: 'v. d. komesara, april 1943', start: '1943-04', note: 'Teško ranjen 26. 5. 1943. na Vratniku, umro u otočkoj bolnici.' },
        { name: 'Vujnović Miloš Lašo', id: '0002009338' },
        { name: 'Zorić Damjan', id: '0002009543' },
        { name: 'Milošević Ilija', id: '0002005139' },
        { name: 'Lasković Mirko', id: '0002003933', when: 'od 20. 4. 1945, poslednji ratni komesar', start: '1945-04-20' },
      ],
    },
  ],
  '2-bataljon': [
    {
      post: 'Komandant',
      people: [
        { name: 'Novković Momčilo', id: '0002005812', when: 'prvi komandant, do 15. 9. 1942', start: '1942-07', hero: true, note: 'Ranjen 19. 7. 1942; bataljon od tada vodi njegov zamenik Mićo Jović.' },
        { name: 'Jović Mićo', id: '0002003368', when: 'od 19. 7. 1942. kao zamenik, komandant septembar – oktobar 1942', start: '1942-07-19', note: '10. 10. 1942. komandant.', p: 91 },
        { name: 'Palija Ilija', id: '0002006018', when: 'novembar 1942 – februar 1943', start: '1942-11', note: 'Poginuo 7. 4. 1945. kao komandant Artiljerijske brigade 6. divizije.' },
        { name: 'Dukić Bogdan', id: '0002001723', start: '1943-02', note: 'Poginuo 18. marta 1943. u Miletić Gaju kod Svetog Roka.' },
        { name: 'Zorić Jovica', id: '0002009567', when: 'u proleće 1943', start: '1943-04' },
        { name: 'Radovanac Đuro', id: '0002007171', when: 'jun 1943 – januar 1944', start: '1943-06' },
        { name: 'Žunić Jandre', id: '0002009789', when: '19. 1. – kraj leta 1944', start: '1944-01-19', note: 'Potom komandant 1. bataljona.' },
        { name: 'Dubajić Mirko', id: '0002001692', start: '1944-08', note: 'Poginuo 4. 11. 1944. na Fruškoj gori.' },
        { name: 'Todorić Miloš', id: '0002008751', when: 'od 5. 11. 1944', start: '1944-11-05' },
      ],
    },
    {
      post: 'Politički komesar',
      people: [
        { name: 'Glumac Slavko', id: '0002002305', when: 'februar – jun 1942, pre brigade', start: '1942-02' },
        { name: 'Vujnović Damjan Deni', id: '0002009347', when: 'prvi komesar u brigadi', start: '1942-07' },
        { name: 'Radaković Simo Sem', id: '0002007043', when: 'oktobar 1942 – februar 1943', start: '1942-10', p: 92 },
        { name: 'Toplak Ferdo', id: '0002008876', when: '28. 6. – 25. 9. 1943', start: '1943-06-28' },
        { name: 'Dimić Janko Pop', id: '0002001480' },
        { name: 'Ćopić Jovo', id: '0002001224', start: '1944-10', note: 'Poginuo 21. 10. 1944. na Bežanijskoj kosi.' },
        { name: 'Štetić Bude', id: '0002008573', when: '21. 10. – 4. 11. 1944', start: '1944-10-21', note: 'Poginuo na Fruškoj gori 4. 11. 1944.' },
        { name: 'Baškot Simo', id: '0002000330', when: 'novembar 1944 – maj 1945', start: '1944-11' },
      ],
    },
  ],
  '3-kordunaski': [
    { post: 'Komandant', people: [{ name: 'Dakić Milisav', id: '0002001294', when: '10. 10. 1942', start: '1942-10', hero: true, note: 'Poginuo 21. 3. 1943. kod Vrhovina, kao komandant bataljona 3. kordunaške brigade.', p: 91 }] },
    {
      post: 'Politički komesar',
      people: [
        { name: 'Dejanović Milić', id: '0002001400', when: 'prvi komesar, do oktobra 1942', start: '1942-07', note: 'Vraćen na Kordun za komesara odreda.', p: 92 },
        { name: 'Ratković Milan', id: '0002007474', when: 'od oktobra 1942', start: '1942-10', note: 'Poginuo kod Slunja 7. 11. 1942.', p: 92 },
      ],
    },
  ],
  '4-banijski': [
    { post: 'Komandant', people: [{ name: 'Milojević Radomir', when: '10. 10. 1942', start: '1942-10', p: 91 }] },
    { post: 'Politički komesar', people: [{ name: 'Đukić Mile Grba', id: '0002001934', when: 'od septembra 1942', start: '1942-09', p: 92 }] },
    { post: 'Zamenik komandanta', people: [{ name: 'Karapandža Đuro', id: '0002003450', when: '10. 10. 1942', start: '1942-10', p: 91 }] },
  ],
  '3-bataljon': [
    {
      post: 'Komandant',
      people: [
        { name: 'Ciganović Vlado', id: '0002000952', when: 'maj – septembar 1943', start: '1943-05' },
        { name: 'Rađenović Branko Gešić', id: '0002007246', when: 'septembar 1943 – mart 1944', start: '1943-09' },
        { name: 'Jovanić Đoko Đuro Mali', id: '0002003146', when: 'od 14. 10. 1944', start: '1944-10-14', note: 'Ranjen 6. 4. 1945.' },
        { name: 'Starčević Mirko', id: '0002008106', when: 'od 12. 4. 1945, poslednji ratni komandant', start: '1945-04-12' },
      ],
    },
    {
      post: 'Politički komesar',
      people: [
        { name: 'Šnajder Boško Motorist', id: '0002008539', when: 'v. d. komesara, početkom 1943', start: '1943-01' },
        { name: 'Damjanović Branko', id: '0002001304' },
        { name: 'Milekić Gojko', id: '0002004881', when: 'april 1943 – mart 1944', start: '1943-04' },
        { name: 'Ljuština Đuro', id: '0002004210', when: 'mart 1944 – januar 1945', start: '1944-03' },
      ],
    },
  ],
  '4-bataljon': [
    {
      post: 'Komandant',
      people: [
        { name: 'Mlinarić Božo', id: '0002005420', note: 'Komandant bataljona „Matija Gubec“; umro 1943.' },
        { name: 'Zaklan Dmitar', id: '0002009484', when: '1942 – maj 1943', start: '1942-11', hero: true },
        { name: 'Počuča Mile', id: '0002006757', when: 'od 2. 1. do 20. 4. 1943', start: '1943-01-02' },
        { name: 'Marić Petar Perica', id: '0002004439', when: 'zamenik, pa komandant, februar – jul 1943', start: '1943-02' },
        { name: 'Čubrilo Dušan Duja', id: '0002001145', when: 'jun – septembar 1943', start: '1943-06' },
        { name: 'Drobac Đuro', id: '0002001654', when: 'od septembra 1943', start: '1943-09' },
        { name: 'Pavković Nikola', id: '0002006174', when: 'od 1. 11. 1944. do 16. 3. 1945', start: '1944-11-01' },
      ],
    },
    {
      post: 'Politički komesar',
      people: [
        { name: 'Balenović Dane', id: '0002000253', when: '1942', start: '1942-11' },
        { name: 'Popović Đuran', id: '0002006808', when: 'januar 1943', start: '1943-01' },
        { name: 'Grubišić Jovan', id: '0002002434', when: '28. 1. – 16. 4. 1943', start: '1943-01-28', note: 'Potom obaveštajni oficir brigade; poginuo 26. 6. 1943. kod Perušića.' },
        { name: 'Ljuština Đuro', id: '0002004210', when: '18. 12. 1943 – 5. 3. 1944', start: '1943-12-18' },
        { name: 'Jasenko Ivica', id: '0002002878' },
      ],
    },
  ],
  '5-mitraljeski': [
    {
      post: 'Komandant',
      people: [
        { name: 'Plećaš Stevo Biće', id: '0002006742', when: 'prvi komandant, desetak dana', start: '1942-12-15', p: 137 },
        { name: 'Bursać Jovo', id: '0002000862', start: '1943-01', p: 170 },
        { name: 'Vitas Branko', id: '0002009214', when: 'april – maj 1943', start: '1943-04' },
      ],
    },
    { post: 'Zamenik komesara', people: [{ name: 'Borić Antun Tuna', id: '0002000623', p: 147 }, { name: 'Ćopić Jovo', p: 168 }] },
  ],
  '5-ruski': [
    { post: 'Komandant', people: [{ name: 'Dubajić Mirko', id: '0002001692', when: 'od 6. 4. 1944', start: '1944-04-06', p: 359 }, { name: 'Pokrajac Branko Jaban', id: '0002006771', when: 'aprila 1944', start: '1944-04-07', note: 'Od 17. 5. 1944. zamenik komandanta 4. bataljona; poginuo 5. 9. 1944. kod Užičke Požege.' }] },
    { post: 'Politički komesar', people: [{ name: 'Rađenović Pero', id: '0002007288', when: 'od 6. 4. 1944', start: '1944-04-06', p: 359 }] },
  ],
  '5-makedonski': [],
}

// The companies' command where the book's accounts of the fights name it (read for the battalion page on the map,
// /mapa/bataljon, episodes.ts; the records matched there by name and what the book says of the man), before what the
// entries give. '?' is a company the book does not number.
export const COMPANY_STAFF: Record<string, Record<string, Person[]>> = {
  '2-bataljon': {
    '1': [
      { name: 'Čubrilo Dušan Duja', id: '0002001145', when: 'komandir, septembar 1942 (Dabar) i novembar 1942 (Slunj)', start: '1942-09', note: 'Kasnije komandant 4. bataljona.' },
      { name: 'Potkonjak Stevo Mačak', id: '0002006895', when: 'politički komesar, septembar 1942 (Dabar)', start: '1942-09' },
    ],
    '2': [
      { name: 'Bogdanović Jovo', id: '0002000526', when: 'komandir, jul 1942', start: '1942-07', note: 'Poginuo u napadu na Potpolje 22. 7. 1942, po opisu borbe; njegov zapis kaže 24. juna, kod Ličke Jasenice.' },
      { name: 'Đaković Miloš', when: 'komandir, avgust 1942', start: '1942-08', note: 'Ranjen kod Brinja.' },
      { name: 'Potkonjak Đurika', id: '0002006873', when: 'komandir, novembar 1942 (Slunj)', start: '1942-11' },
      { name: 'Petrlić Jakov', id: '0002006468', when: 'komandir 1. voda', start: '1942-11', note: 'Poginuo 7. 11. 1942, u napadu na Slunj.' },
    ],
    '3': [
      { name: 'Počuča Mile', when: 'komandir, 1942', start: '1942-09' },
    ],
    '?': [
      { name: 'Vlajković Bato', when: 'komandir čete, novembar 1942 (Slunj)', start: '1942-11' },
    ],
  },
}
