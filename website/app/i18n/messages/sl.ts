import { dateNumbers, formatNumber, plural } from '../format'
import type { WarEvent } from '../../lib/types'
import type { Messages } from './sr'

// Slovenščina. Written for Slovene readers, not translated word for word: the Slovene words for the
// partisan war (padli, pogrešani, soborci, rojaki), the dual (2 borca, 2 leti), »…« quotes and dates
// without a full stop after the year ("8. julija 1942"). VOICE.md, section "Slovenščina".

const n = (x: number) => formatNumber('sl', x)

const MONTHS_GENITIVE = [
  'januarja', 'februarja', 'marca', 'aprila', 'maja', 'junija',
  'julija', 'avgusta', 'septembra', 'oktobra', 'novembra', 'decembra',
]
const MONTHS = ['januar', 'februar', 'marec', 'april', 'maj', 'junij', 'julij', 'avgust', 'september', 'oktober', 'november', 'december']

const borci = (x: number) => `${n(x)} ${plural('sl', x, { one: 'borec', two: 'borca', few: 'borci', other: 'borcev' })}`
const let_ = (x: number) => plural('sl', x, { one: 'leto', two: 'leti', few: 'leta', other: 'let' })
// Slovene sets the three dots apart from a whole word: "Nalaganje …"
const dots = ' …'

export const sl: Messages = {
  site: {
    name: 'Knjiga borcev',
    description: 'Seznami borcev partizanskih enot. Iščete lahko po imenu, ob vsakem zapisu je stran iz knjige.',
  },
  nav: { label: 'Glavna navigacija', home: 'Domov', units: 'Enote', gallery: 'Galerija', sources: 'Viri' },
  theme: { label: 'Videz', light: 'Svetla tema', dark: 'Temna tema', system: 'Kot v sistemu' },
  language: { label: 'Jezik' },
  footer: {
    contact: 'Kontakt',
    records: 'Napako v zapisu ali kaj, kar veste o borcu, lahko pošljete tudi iz samega zapisa.',
  },
  notFound: {
    title: 'Te strani ni',
    text: 'Naslov je morda star ali napačno vpisan. Borca poiščite po imenu na začetni strani.',
  },

  borci,
  found: (x: number) => `${plural('sl', x, { one: 'Najden', two: 'Najdena', few: 'Najdeni', other: 'Najdenih' })} ${borci(x)}`,

  home: {
    title: 'Iskanje borcev',
    fieldLabel: 'Priimek, ime ali kraj',
    total: (x: number) => `${n(x)} ${plural('sl', x, { one: 'ime', two: 'imeni', few: 'imena', other: 'imen' })}`,
    loadFailedTitle: 'Seznami se niso naložili',
    loadFailedText: 'Preverite internetno povezavo in osvežite stran.',
    noneTitle: (q: string) => `Za »${q}« ni zadetkov`,
    noneText:
      'Poskusite samo s priimkom ali z imenom in priimkom brez očetovega imena. Knjige očetovo ime pogosto zapišejo v rodilniku, na primer »Milorada« namesto »Milorad«. Črki ć in đ lahko vpišete kot c in d.',
    doors: {
      title: 'Raziščite',
      units: 'Enote',
      unitsText: 'Brigade, divizije in odredi po letu ustanovitve, vsaka s seznamom svojih borcev.',
      unitsCount: (x: number) => `${n(x)} ${plural('sl', x, { one: 'enota', two: 'enoti', few: 'enote', other: 'enot' })}`,
      photos: 'Fotografije',
      photosText: 'Obrazi borcev iz knjig njihovih enot, z znaci.org in iz družinskih albumov.',
      photosCount: (x: number) =>
        `${n(x)} ${plural('sl', x, { one: 'fotografija', two: 'fotografiji', few: 'fotografije', other: 'fotografij' })}`,
      books: 'Knjige',
      booksText: 'Knjige in seznami, iz katerih so imena, s skeniranimi stranmi.',
      booksCount: (x: number) => `${n(x)} ${plural('sl', x, { one: 'vir', two: 'vira', few: 'viri', other: 'virov' })}`,
    },
    news: {
      title: 'Kaj je novega',
      date: (d: number, m: number, y: number) => `${d}. ${m}. ${y}`,
    },
    otherUnits: 'Druge enote',
    noUnit: 'Brez enote',
    census: 'Popis žrtev vojne iz leta 1964',
    censusLead: 'Padli in umrli borci, katerih enote še ni na strani, po republikah in pokrajinah.',
    /** The wartime portraits in the home page's margins */
    rails: 'Borci na fotografijah iz vojne',
    bandCredit: 'Na fotografiji:',
  },

  filters: {
    toggle: 'Filtri',
    active: (x: number) => `(izbranih: ${x})`,
    birthYear: 'Leto rojstva',
    range: 'Odstopanje od leta rojstva',
    exact: 'točno',
    place: 'Kraj',
    placeHint: 'vas ali mesto',
    unit: 'Enota',
    allUnits: 'Vse enote',
    fate: 'Usoda',
    allFates: 'Vsi',
    fates: { poginuli: 'Padli', umrli: 'Umrli', nestali: 'Pogrešani' },
    wholeWords: 'Samo cele besede',
    clear: 'Počisti filtre',
    noneTitle: (q: string) => (q ? `Za »${q}« s temi filtri ni zadetkov` : 'S temi filtri ni zadetkov'),
    noneText: 'Preverite filtre ali jih [odstranite].',
  },

  share: { search: 'Deli iskanje', copied: 'Povezava je kopirana', failed: 'Kopirajte naslov strani' },

  results: {
    pageOf: (page: number, total: number) => `stran ${page} od ${total}`,
    searching: `Iskanje${dots}`,
    perPage: 'Na stran',
    pages: 'Strani z zadetki',
    previous: 'Prejšnja',
    next: 'Naslednja',
    noExact: 'Ni natančnega zadetka',
    similar: (x: number, more: boolean) =>
      `${more ? 'še ' : ''}${n(x)} ${plural('sl', x, { one: 'podoben zapis', two: 'podobna zapisa', few: 'podobni zapisi', other: 'podobnih zapisov' })}`,
    similarTitle: 'Podobni zapisi',
  },

  onThisDay: {
    title: (day: number, month: number) => `Padli, umrli ali pogrešani dne ${day}. ${MONTHS_GENITIVE[month - 1]}`,
    loading: 'Nalaganje',
    deathTitle: 'Leto in kraj smrti',
    missingTitle: 'Leto in kraj izginotja',
    death: 'Smrt:',
    missing: (female: boolean) => (female ? 'Pogrešana' : 'Pogrešan'),
    age: (from: number, to: number) => (from === to ? `${to} ${let_(to)}` : `${from} ali ${to} ${let_(to)}`),
    showLess: 'Prikaži manj',
    showAll: (x: number) => `Prikaži vse za ta dan (${x})`,
  },

  medals: { heroj: 'Narodni heroj', spomenica: 'Nosilec Partizanske spomenice 1941' },

  life: {
    title: 'Življenjska pot',
    show: 'Pokaži v knjigi',
    source: (page: number | string) => `Iz zapisa na str. ${page}`,
    printedLabels: false,
    born: (woman: boolean) => (woman ? 'Rojena' : 'Rojen'),
    skoj: 'Član SKOJ',
    kpj: 'Član KPJ',
    party: (items: [string, string][]) => items.map(([org, year]) => org + (year ? ` od ${year}` : '')).join(', '),
    nob: 'V NOB',
    unit: (kind: string) => ({ brigade: 'V brigadi', division: 'V diviziji', detachment: 'V odredu', battalion: 'V bataljonu', company: 'V četi' } as Record<string, string>)[kind] ?? 'V enoti',
    duty: 'Dolžnost',
    moved: 'Premeščen',
    ill: 'Zbolel',
    left: 'Odpuščen',
    wounded: (woman: boolean) => (woman ? 'Ranjena' : 'Ranjen'),
    captured: (woman: boolean) => (woman ? 'Ujeta' : 'Ujet'),
    exchanged: (woman: boolean) => (woman ? 'Zamenjana' : 'Zamenjan'),
    /** the steps of the war's events his unit was part of (lib/warEvents.ts) */
    igman: 'Igmanski marš',
    sutjeska: 'Bitka na Sutjeski',
    fate: (type: string | undefined, woman: boolean) => {
      const words: Record<string, [string, string]> = {
        poginuo: ['Padel', 'Padla'], umro: ['Umrl', 'Umrla'], nestao: ['Pogrešan', 'Pogrešana'],
        streljan: ['Ustreljen', 'Ustreljena'], ubijen: ['Ubit', 'Ubita'], zarobljen: ['Ujet', 'Ujeta'],
      }
      return (words[type ?? ''] ?? ['Smrt', 'Smrt'])[woman ? 1 : 0]
    },
    day: (d: number, m: number) => dateNumbers(d, m),
    month: (m: number) => MONTHS[m - 1],
    neighbours: (x: number) => `še ${n(x)} iz istega kraja`,
    comrades: (x: number) => borci(x),
    sameDay: (x: number) => `isti dan še ${n(x)}`,
    sameDayShort: 'isti dan',
    undated: 'datum ni naveden',
    afterWar: 'po vojni',
  },

  record: {
    close: 'Zapri',
    photo: 'Fotografija:',
    openPhoto: 'Odpri fotografijo',
    closePhoto: 'Zapri fotografijo',
    /** Where a photograph comes from: "znaci.org, br. 13283", "znaci.org, knjiga o jedinici" */
    photoCredit: (credit: string) => credit.replace(', br. ', ', št. ').replace(', knjiga o jedinici', ', knjiga o enoti'),
    photoUnknown: 'Fotografija tega borca ni znana',
    entries: 'Zapisi v knjigah',
    page: (p: number | string) => `str. ${p}`,
    nameInBook: 'Ime v knjigi:',
    moreEntries: (count: number) =>
      count === 1 ? 'Še en zapis v drugi knjigi' : `Še ${n(count)} ${plural('sl', count, { one: 'zapis', two: 'zapisa', few: 'zapisi', other: 'zapisov' })} v drugih knjigah`,
    showPage: 'Pokaži stran v knjigi',
    references: 'Reference',
    book: 'Knjiga',
    loadingPage: `Nalaganje strani${dots}`,
    source: 'Vir',
    noScan: 'Za ta seznam ni skenirane knjige: objavljen je kot besedilo na [znaci.org].',
    noScanMuseum: (title: string) => `${title}. Popis je objavljen kot PDF na spletni strani [Muzeja žrtev genocida].`,
    noScanBook: (title: string, page: number | null) => `${title}${page != null ? `, stran ${page}` : ''}.`,
    steps: 'Sosednji zapisi na seznamu',
    previous: 'Prejšnji',
    next: 'Naslednji',
    fields: {
      father: 'Oče',
      mother: 'Mati',
      ethnicity: 'Narodnost',
      occupation: 'Poklic',
      party: 'Partija',
    },
    or: 'ali',
    /** The Igman march: "Kot pripadnik 2. čete 1. bataljona je sodeloval v igmanskem maršu 27.–28. januarja 1942." */
    igman: (e: WarEvent, woman: boolean) => {
      const where = e.c && e.b ? `${e.c}. čete ${e.b}. bataljona`
        : e.s === 'bstab' ? `štaba ${e.b}. bataljona` : e.s === 'bsanitet' ? `sanitetne službe ${e.b}. bataljona`
        : e.s === 'posavska' ? 'Posavske čete 6. bataljona' : e.s === 'stab' ? 'štaba brigade'
        : e.s === 'sanitet' ? 'sanitetne službe brigade' : e.s === 'odeljenje' ? 'sanitetnega oddelka brigade'
        : e.s === 'hirurska' ? 'kirurške ekipe brigade' : ''
      const did = `je ${e.sure ? '' : 'najverjetneje '}${woman ? 'sodelovala' : 'sodeloval'} v igmanskem maršu 27.–28. januarja 1942.`
      return where ? `Kot ${woman ? 'pripadnica' : 'pripadnik'} ${where} ${did}` : `${woman ? 'Sodelovala' : 'Sodeloval'} je v igmanskem maršu 27.–28. januarja 1942.`
    },
    /** The battle of the Sutjeska: everyone Borci Sutjeske lists */
    sutjeska: (woman: boolean) => `${woman ? 'Sodelovala' : 'Sodeloval'} je v bitki na Sutjeski maja in junija 1943.`,
    citation: (name: string, where: string, page: number | null, id: string) =>
      `${name}. ${where}${page != null ? `, str. ${page}` : ''}. Knjiga borcev, zapis ${id}.`,
  },

  actions: {
    share: 'Deli zapis',
    card: 'Spominska kartica',
    cite: 'Citiraj',
    linkCopied: 'Povezava je kopirana.',
    link: 'Povezava do zapisa',
    copy: 'Kopiraj',
    copied: 'Kopirano',
  },

  report: {
    open: 'Ste v tem zapisu opazili napako? Sporočite nam jo',
    label: 'Kaj ni pravilno?',
    hint: 'Na primer: v knjigi piše priimek Adžić, tukaj pa Adzić.',
    send: 'Pošlji',
    cancel: 'Prekliči',
    sending: `Pošiljanje${dots}`,
    sent: 'Hvala, sporočilo je poslano. Zapis bomo preverili v knjigi.',
    failed: 'Sporočilo ni bilo poslano. Preverite internetno povezavo in [poskusite znova].',
  },

  know: {
    prompt: 'Imate fotografijo ali veste kaj o tem borcu?',
    open: 'Vem kaj o tem borcu',
    title: 'Vem kaj o tem borcu',
    relation: 'Kaj ste temu borcu?',
    relationHint: 'Na primer: vnukinja, sin, sorodnik, sosed',
    story: 'Kaj veste o tem borcu',
    storyHint: 'Kaj se pripoveduje v družini, kje je grob, kaj je bilo po vojni ali kaj v zapisu ni pravilno.',
    photo: 'Fotografija',
    optional: '(ni obvezno)',
    choosePhoto: 'Izberite fotografijo',
    chooseOther: 'Izberite drugo',
    remove: 'Odstrani',
    notImage: 'Izberite fotografijo (JPG ali PNG).',
    tooLarge: 'Fotografija je prevelika. Pošljite manjšo (do 9 MB).',
    name: 'Vaše ime in priimek',
    email: 'E-pošta',
    emailHint: 'E-naslov potrebujemo samo zato, da se vam lahko oglasimo. Objavili ga ne bomo.',
    consent: 'Dovoljujem, da se fotografija in besedilo z mojim imenom objavita ob tem zapisu.',
    error: 'Ni bilo poslano. Preverite internetno povezavo in poskusite znova.',
    send: 'Pošlji',
    sending: `Pošiljanje${dots}`,
    cancel: 'Prekliči',
    thanks: 'Hvala. Pregledali bomo, kar ste poslali.',
    willReply: 'Če kaj ne bo jasno, se vam bomo oglasili.',
    photoLost: 'Fotografija zaradi prekinjene povezave ni prispela; prosimo, pošljite jo še enkrat.',
  },

  family: {
    title: 'Iz družine',
    sent: (year: number, month?: number) => (month ? `${MONTHS[month - 1]} ${year}` : `${year}`),
  },

  kin: {
    label: 'Soborci in rojaki',
    comrades: 'Soborci',
    neighbours: 'Rojaki',
    unit: 'Enota',
    birthplace: 'Kraj rojstva',
    sameDay: 'Padli istega dne',
    samePlaceTag: 'isti kraj',
    sameDayTag: 'isti dan',
    thisRecord: 'ta zapis',
    more: (x: number) => `še ${n(x)}`,
    count: (x: number) => n(x),
    day: (d: number, m: number, y: number) => dateNumbers(d, m, y),
    battalion: (x: number) => `${x}. bataljon`,
    company: (x: number) => `${x}. četa`,
    platoon: (x: number) => `${x}. vod`,
    squad: (x: number) => `${x}. desetina`,
    staff: 'enote pri štabu',
    noBattalion: 'bataljon ni naveden',
  },

  viewer: {
    failed: 'Strani iz knjige trenutno ni mogoče prikazati.',
    previous: 'Prejšnja stran',
    next: 'Naslednja stran',
    page: (p: number, total: number | null) => `str. ${p}${total ? ` / ${total}` : ''}`,
    back: 'Nazaj na zapis',
    zoomOut: 'Pomanjšaj',
    zoomIn: 'Povečaj',
    wholeBook: 'Celotna knjiga je med viri',
  },

  crop: {
    failed: 'Izreza iz knjige ni mogoče prikazati.',
    loading: 'Nalaganje izreza iz knjige',
    alt: 'Zapis, kot je natisnjen v knjigi',
  },

  card: {
    title: 'Spominska kartica',
    description: 'Zapis borca iz knjige, pripravljen za tisk.',
    loading: `Nalaganje zapisa${dots}`,
    missingTitle: 'Tega zapisa ni',
    missingText: 'Povezava je morda nepopolna. Borca poiščite na začetni strani.',
    failedTitle: 'Zapis se ni naložil',
    failedText: 'Preverite internetno povezavo in osvežite stran.',
    back: 'Nazaj na zapis',
    print: 'Natisni ali shrani kot PDF',
    preparing: `Pripravljanje izreza iz knjige${dots}`,
    entry: 'Zapis v knjigi',
    webText: 'besedilo, objavljeno na znaci.org',
    museumText: 'popis na spletni strani Muzeja žrtev genocida',
  },

  unit: {
    notFound: 'Te enote ni',
    backHome: 'Nazaj na začetno stran',
    allUnits: 'Vse enote',
    search: 'Iskanje v tej enoti',
    placeholder: 'Priimek, ime ali kraj',
    loadFailedTitle: 'Seznam se ni naložil',
    loadFailedText: 'Preverite internetno povezavo in osvežite stran.',
    noneTitle: (q: string) => `Za »${q}« v tej enoti ni zadetkov`,
    noneText: 'Poskusite samo s priimkom ali pa iščite po vseh enotah na [začetni strani].',
  },

  unitsPage: {
    title: 'Enote',
    description: 'Vse enote na strani po letu ustanovitve: brigade, divizije in odredi, vsaka s seznamom svojih borcev.',
    lead: (x: number) =>
      `${n(x)} ${plural('sl', x, { one: 'enota', two: 'enoti', few: 'enote', other: 'enot' })} po letu ustanovitve, vsaka s seznamom svojih borcev.`,
    years: 'Leto ustanovitve',
    allYears: 'Vsa',
    find: 'Ime enote',
    partOf: 'V sestavi',
    none: (q: string) => `Nobena enota ne ustreza iskanju »${q}«`,
    noneText: 'Poskusite z delom imena: številko, krajem ali imenom, na primer »liška« ali »13.«.',
    kinds: 'Vrsta enote',
    kind: { brigada: 'Brigade', divizija: 'Divizije', odred: 'Odredi', ostalo: 'Druge' },
    lands: 'Republika',
    land: {
      bih: 'Bosna in Hercegovina', 'crna-gora': 'Črna gora', hrvatska: 'Hrvaška', makedonija: 'Makedonija',
      slovenija: 'Slovenija', srbija: 'Srbija',
    },
    noneChosen: 'Nobena enota ne ustreza temu izboru',
    noneChosenText: 'Odstranite kakšen filter ali izberite drugo leto.',
  },
  gallery: {
    title: 'Galerija',
    description: 'Fotografije borcev: obrazi iz knjig enot in iz fotogalerije znaci.org.',
    label: (x: number) => `Fotografije borcev (${n(x)})`,
  },

  sources: {
    metaTitle: 'Viri',
    metaDescription: 'Knjige, iz katerih so seznami borcev, s skenom vsake knjige.',
    title: 'Izvirni dokumenti',
    intro:
      'Podatki o borcih so zbrani iz monografij brigad in seznamov borcev, ki jih je izdal Vojnozgodovinski inštitut v Beogradu. Tu si lahko ogledate in prenesete izvirne dokumente PDF.',
    openPdf: 'Odpri PDF',
    fullDescription: 'Cel opis',
    download: 'Prenesi',
    openList: 'Odpri seznam',
    medalsTitle: 'Slike odlikovanj',
    hero:
      'Red narodnega heroja: fotografija [Pinki, Wikimedia Commons], licenca [CC BY-SA 4.0]. Izrez in risba reda na tej strani sta narejena iz te fotografije in objavljena pod isto licenco.',
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.sl',
    spomenica:
      'Partizanska spomenica 1941: slika iz registra državnih simbolov Svetovne organizacije za intelektualno lastnino (WIPO), [javna domena].',
    placesTitle: 'Kraji',
    places:
      'Kraje rojstva in smrti smo prepoznali s pomočjo zbirke zemljepisnih imen [GeoNames], licenca [CC BY 4.0]. Zato so v drevesu »Soborci in rojaki« borci iz iste vasi skupaj, tudi če knjige vas pišejo različno, kraj, ki ga knjiga navaja v sklonu (»u Užicu«), pa je tu zapisan v imenovalniku.',
    placesLicense: 'https://creativecommons.org/licenses/by/4.0/deed.sl',
  },

  date: (day: number | undefined, month: number, year: number) =>
    day ? `${day}. ${MONTHS_GENITIVE[month - 1]} ${year}` : `${MONTHS_GENITIVE[month - 1]} ${year}`,
}
