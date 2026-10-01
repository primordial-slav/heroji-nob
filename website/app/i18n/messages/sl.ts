import { formatNumber, plural } from '../format'
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
  nav: { label: 'Glavna navigacija', home: 'Domov', gallery: 'Galerija', sources: 'Viri' },
  theme: { label: 'Videz', light: 'Svetla tema', dark: 'Temna tema', system: 'Kot v sistemu' },
  language: { label: 'Jezik' },

  borci,
  found: (x: number) => `${plural('sl', x, { one: 'Najden', two: 'Najdena', few: 'Najdeni', other: 'Najdenih' })} ${borci(x)}`,

  home: {
    title: 'Iskanje borcev',
    fieldLabel: 'Priimek, ime ali kraj',
    placeholder: (x: number) => `Iščite med ${n(x)} ${plural('sl', x, { one: 'imenom', two: 'imenoma', other: 'imeni' })}`,
    examplesLead: 'Na primer:',
    examples: [
      { label: 'Novak', query: 'Novak' },
      { label: 'Anton Novak', query: 'Anton Novak' },
      { label: 'Trbovlje', query: 'Trbovlje' },
      { label: 'Novak iz Ljubljane', query: 'Novak', place: 'Ljubljana' },
    ],
    loading: `Nalaganje seznamov${dots}`,
    loadFailedTitle: 'Seznami se niso naložili',
    loadFailedText: 'Preverite internetno povezavo in osvežite stran.',
    noneTitle: (q: string) => `Za »${q}« ni zadetkov`,
    noneText:
      'Poskusite samo s priimkom ali z imenom in priimkom brez očetovega imena. Knjige očetovo ime pogosto zapišejo v rodilniku, na primer »Milorada« namesto »Milorad«. Črki ć in đ lahko vpišete kot c in d.',
    unitsTitle: 'Enote',
    otherUnits: 'Druge enote',
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
  },

  onThisDay: {
    title: 'Na današnji dan',
    note: (day: number, month: number) => `Borci, ki so ${day}. ${MONTHS_GENITIVE[month - 1]} med vojno padli, umrli ali izginili`,
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
    references: 'V knjigi',
    book: 'Knjiga',
    loadingPage: `Nalaganje strani${dots}`,
    source: 'Vir',
    noScan: 'Za ta seznam ni skenirane knjige: objavljen je kot besedilo na [znaci.org].',
    steps: 'Sosednji zapisi na seznamu',
    previous: 'Prejšnji',
    next: 'Naslednji',
    fields: {
      fathersName: 'Očetovo ime',
      birthYear: 'Leto rojstva',
      birthPlace: 'Kraj rojstva',
      ethnicity: 'Narodnost',
      occupation: 'Poklic',
      rank: 'Funkcija',
      unitDetail: 'Podenota',
      deathDate: 'Datum smrti',
      deathPlace: 'Kraj smrti',
      killedDate: 'Datum smrti',
      killedPlace: 'Kraj smrti',
    },
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
    day: (d: number, m: number, y: number) => `${d}. ${m}. ${y}`,
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
  },

  unit: {
    notFound: 'Te enote ni',
    backHome: 'Nazaj na začetno stran',
    allUnits: 'Vse enote',
    search: 'Iskanje v tej enoti',
    placeholder: 'Priimek, ime ali kraj',
    loading: 'Nalaganje seznama',
    loadFailedTitle: 'Seznam se ni naložil',
    loadFailedText: 'Preverite internetno povezavo in osvežite stran.',
    noneTitle: (q: string) => `Za »${q}« v tej enoti ni zadetkov`,
    noneText: 'Poskusite samo s priimkom ali pa iščite po vseh enotah na [začetni strani].',
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
      'Podatki o borcih so zbrani iz monografij brigad in seznamov borcev, ki jih je izdal Vojnozgodovinski inštitut v Beogradu. Tu si lahko izvirne dokumente PDF ogledate in jih prenesete.',
    openPdf: 'Odpri PDF',
    download: 'Prenesi',
    openList: 'Odpri seznam',
    medalsTitle: 'Slike odlikovanj',
    hero:
      'Red narodnega heroja: fotografija [Pinki, Wikimedia Commons], licenca [CC BY-SA 4.0]. Izrez in risba reda na tej strani sta narejena iz te fotografije in objavljena pod isto licenco.',
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.sl',
    spomenica:
      'Partizanska spomenica 1941: slika iz registra državnih simbolov Svetovne organizacije za intelektualno lastnino (WIPO), [javna domena].',
  },

  date: (day: number | undefined, month: number, year: number) =>
    day ? `${day}. ${MONTHS_GENITIVE[month - 1]} ${year}` : `${MONTHS_GENITIVE[month - 1]} ${year}`,
}
