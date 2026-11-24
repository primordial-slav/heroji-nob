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
  nav: { label: 'Glavna navigacija', home: 'Domov', units: 'Enote', gallery: 'Fotografije borcev', sources: 'Viri' },
  theme: { label: 'Videz', light: 'Svetla tema', dark: 'Temna tema', system: 'Kot v sistemu' },
  language: { label: 'Jezik' },
  footer: {
    contact: 'Kontakt',
    records: 'Napako ali kar veste o borcu nam lahko sporočite tudi neposredno iz njegovega zapisa.',
    missingAsk: 'Če borca ni na strani,',
    missingLink: 'nam pošljite, kar veste o njem ali njej',
    support: 'Podpora',
    supportText: 'Stran je brezplačna in brez oglasov. Če želite pomagati, da tako ostane,',
    supportLink: 'jo podprite na platformi Ko-fi',
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
      unitsText: 'Brigade, divizije in odredi po letu ustanovitve in seznami njihovih borcev.',
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
      title: 'Dopolnitve',
      date: (d: number, m: number, y: number) => `${d}. ${m}. ${y}`,
    },
    otherUnits: 'Druge enote',
    noUnit: 'Brez enote',
    census: 'Popis žrtev vojne iz leta 1964',
    censusLead: 'Padli in umrli borci, katerih enote še ni na strani, po republikah in pokrajinah.',
    /** The wartime portraits in the home page's margins */
    rails: 'Borci na fotografijah iz vojne',
    /** The switch at the top of the right margin: it stops the drifting portraits, then starts them again */
    railsStop: 'Ustavi portrete',
    railsStart: 'Zaženi portrete',
    bandCredit: 'Na fotografiji:',
  },

  filters: {
    toggle: 'Filtri',
    active: (x: number) => `(izbranih: ${x})`,
    birthYear: 'Leto rojstva',
    range: 'Odstopanje od leta rojstva',
    exact: 'točno',
    /** In the empty year field: the year is optional */
    yearHint: 'če ga veste',
    /** The switch under a typed year: the year alone, or also the records whose entries print none */
    yearOnly: (from: number, to: number) => (from === to ? `Samo rojeni ${from}` : `Samo rojeni ${from}–${to}`),
    yearAny: 'Tudi brez letnice rojstva',
    undatedLabel: 'Zapisi brez letnice rojstva',
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
    /** With a birth year set: the records whose entries print none, which the year leaves out */
    undated: (x: number) => `še ${n(x)} brez letnice rojstva`,
    undatedIn: (x: number) => `od tega ${n(x)} brez letnice rojstva`,
    undatedHide: 'skrij jih',
    undatedShow: (x: number) => `Pokaži ${n(x)} brez letnice rojstva`,
  },

  onThisDay: {
    title: (day: number, month: number) => `Padli, umrli ali pogrešani ${day}. ${MONTHS_GENITIVE[month - 1]}`,
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
    skoj: 'Član SKOJ-a',
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
    kozara: 'Bitka na Kozari',
    neretva: 'Bitka na Neretvi',
    drvar: 'Desant na Drvar',
    beograd: 'Osvoboditev Beograda',
    srem: 'Sremska fronta',
    trst: 'Boji za Trst',
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
    steps: 'Sosednji zapisi na seznamu',
    stepsFound: 'Sosednji rezultati iskanja',
    wholePage: 'Celotna stran vira',
    wholeEntry: 'Celoten zapis',
    stepOf: (at: number, total: number) => `${n(at)} od ${n(total)}`,
    previous: 'Prejšnji',
    next: 'Naslednji',
    fields: {
      father: 'Oče',
      mother: 'Mati',
      ethnicity: 'Narodnost',
      duty: 'Dolžnost',
      units: 'Enote',
      occupation: 'Poklic',
      party: 'Partija',
    },
    or: 'ali',
    fromFamily: 'Popravljeno po podatkih družine',
    /** The card's dot after the name, a family having added to it (the user's choice of 2026-11-23): its tooltip */
    familyDot: 'Dopolnjeno s podatki družine',
    /** The Igman march: "Kot pripadnik 2. čete 1. bataljona se je udeležil igmanskega marša 27. in 28. januarja 1942." */
    igman: (e: WarEvent, woman: boolean) => {
      const where = e.c && e.b ? `${e.c}. čete ${e.b}. bataljona`
        : e.s === 'bstab' ? `štaba ${e.b}. bataljona` : e.s === 'bsanitet' ? `sanitete ${e.b}. bataljona`
        : e.s === 'posavska' ? 'Posavske čete 6. bataljona' : e.s === 'stab' ? 'štaba brigade'
        : e.s === 'sanitet' ? 'sanitete brigade' : e.s === 'odeljenje' ? 'sanitetnega oddelka brigade'
        : e.s === 'hirurska' ? 'kirurške ekipe brigade' : ''
      const did = `se je ${e.sure ? '' : 'najverjetneje '}${woman ? 'udeležila' : 'udeležil'} igmanskega marša 27. in 28. januarja 1942.`
      return where ? `Kot ${woman ? 'pripadnica' : 'pripadnik'} ${where} ${did}` : `${woman ? 'Udeležila' : 'Udeležil'} se je igmanskega marša 27. in 28. januarja 1942.`
    },
    /** The battle of the Sutjeska: everyone Borci Sutjeske lists */
    neretva: (woman: boolean) => `${woman ? 'Sodelovala' : 'Sodeloval'} je v bitki na Neretvi februarja in marca 1943.`,
    kozara: (woman: boolean) => `${woman ? 'Sodelovala' : 'Sodeloval'} je v bitki na Kozari junija in julija 1942.`,
    drvar: (woman: boolean) => `Med nemškim desantom 25. maja 1944 je ${woman ? 'bila' : 'bil'} v Drvarju.`,
    beograd: (woman: boolean) => `${woman ? 'Sodelovala' : 'Sodeloval'} je pri osvoboditvi Beograda oktobra 1944.`,
    srem: (woman: boolean) => `${woman ? 'Borila' : 'Boril'} se je na sremski fronti 1944–1945.`,
    trst: (woman: boolean) => `${woman ? 'Sodelovala' : 'Sodeloval'} je v bojih za Trst aprila in maja 1945.`,
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
    email: 'Vaš e-naslov',
    optional: '(ni obvezno)',
    emailHint: 'Naslov potrebujemo samo zato, da se vam lahko zahvalimo in odgovorimo. Ne bomo ga objavili ali dali nikomur in ne bomo vam pošiljali nezaželene pošte.',
    mayReply: 'Na ta naslov mi lahko odgovorite',
    willReply: 'Oglasili se vam bomo na naslov, ki ste ga pustili.',
  },

  know: {

    /** the form says what is missing when sent incomplete, and gives the address when it can't reach us (2026-11-23) */

    required: '(obvezno)',

    needName: 'Vpišite svoje ime in priimek.',

    needStory: 'Napišite, kaj veste o borcu, ali dodajte fotografijo.',

    fallback: (address: string) => `Če še vedno ne gre, pošljite isto po e-pošti na ${address}.`,

    openMail: 'Odpri e-pošto s tem besedilom',
    prompt: 'Imate fotografijo ali veste kaj o tem borcu?',
    open: 'Vem kaj o tem borcu',
    title: 'Vem kaj o tem borcu',
    relation: 'Kako ste povezani s tem borcem?',
    relationHint: 'Na primer: vnukinja, sin, sorodnik, sosed',
    story: 'Kaj veste o tem borcu',
    storyHint: 'Kaj se o njem pripoveduje v družini, kje je pokopan, kaj je bilo po vojni ali kaj v zapisu ni pravilno.',
    photo: 'Fotografija',
    optional: '(ni obvezno)',
    choosePhoto: 'Izberite fotografijo',
    chooseOther: 'Izberite drugo',
    remove: 'Odstrani',
    notImage: 'Pošljete lahko samo fotografije (JPG ali PNG) in dokumente (PDF).',
    files: 'Fotografije in dokumenti',
    filesHint: (n: number) => `Fotografije borca in njegovih dokumentov (vojaška knjižica, odločbe, pisma), posnete s telefonom ali skenirane; lahko tudi PDF. Do ${n} datotek.`,
    chooseFiles: 'Izberite datoteke',
    addMore: 'Dodajte še',
    tooMany: (n: number) => `Največ ${n} datotek.`,
    fileTooLarge: (name: string) => `Datoteka ${name} je prevelika. Pošljite manjšo (do 9 MB).`,
    filesLost: (names: string) => `Te datoteke niso prispele: ${names}.`,
    sendAgain: 'Pošlji jih znova',
    sendingFile: (n: number, of: number) => `Pošiljanje datoteke ${n} od ${of}${dots}`,
    name: 'Vaše ime in priimek',
    email: 'E-pošta',
    emailHint: 'E-naslov potrebujemo samo zato, da se vam lahko oglasimo: če ga vpišete, vam sporočimo, ko bo kartica borca dopolnjena. Ne bomo ga objavili ali dali nikomur in ne bomo vam pošiljali nezaželene pošte.',
    consentTitle: 'Kaj smemo objaviti',
    consentHint: 'Sprašujemo ločeno za dvoje: za vsebino in za vaše ime. Brez prvega dovoljenja ne objavimo ničesar od poslanega; popravimo lahko le podatke na kartici (letnico, kraj). Brez drugega objavimo brez podpisa.',
    consent: 'Objava vsebine: besedilo in fotografije, ki jih pošiljam, se smejo objaviti na kartici tega borca.',
    consentName: 'Objava imena: ob objavi sme pisati, kdo je to poslal, z začetnico imena, priimkom in sorodstvom (npr. »M. Novak, vnukinja«).',
    error: 'Sporočilo ni bilo poslano. Preverite internetno povezavo in poskusite znova.',
    send: 'Pošlji',
    sending: `Pošiljanje${dots}`,
    cancel: 'Prekliči',
    thanks: 'Hvala. Pregledali bomo, kar ste poslali.',
    willReply: 'Če kaj ne bo jasno, se vam bomo oglasili.',
    photoLost: 'Fotografija zaradi prekinjene povezave ni prispela; prosimo, pošljite jo še enkrat.',
  },

  /** A fighter not on the site: the form under an empty search and under the results (MissingSoldierForm) */
  missing: {
    /** the form says what is missing when sent incomplete, and gives the address when it can't reach us (2026-11-23) */
    required: '(obvezno)',
    needName: 'Vpišite svoje ime in priimek.',
    needSoldier: 'Vpišite ime in priimek borca.',
    needSomething: 'Dodajte vsaj nekaj o borcu: kaj veste, enoto, kraj rojstva ali fotografijo.',
    fallback: (address: string) => `Če še vedno ne gre, pošljite isto po e-pošti na ${address}.`,
    openMail: 'Odpri e-pošto s tem besedilom',
    prompt: 'Borca ni v knjigah na strani? Pošljite nam, kar veste o njem ali njej.',
    ask: 'Ne najdete svojega borca?',
    askLink: 'Pošljite nam, kar veste o njem ali njej',
    open: 'Pošljite podatke o borcu',
    title: 'Borec, ki ga ni na strani',
    intro: 'Napišite, kar veste, in dodajte fotografije in posnetke dokumentov. Nič se ne objavi samodejno: borca dodamo sami, ko preverimo, kar ste poslali.',
    soldier: 'Ime in priimek borca',
    father: 'Očetovo ime',
    born: 'Leto rojstva',
    bornHint: 'npr. 1921',
    birthplace: 'Kraj rojstva',
    unit: 'Enota',
    unitHint: 'brigada, odred ali bataljon, če veste',
    fate: 'Usoda',
    fates: { unknown: 'Ne vem', fell: 'Padel ali padla', died: 'Umrl ali umrla med vojno', missing: 'Pogrešan ali pogrešana', survived: 'Preživel ali preživela vojno' },
    story: 'Kaj veste o njem ali njej',
    storyHint: 'Kar se pripoveduje v družini: enota in soborci, kraj smrti ali življenje po vojni.',
    files: 'Fotografije in dokumenti',
    filesHint: (n: number) => `Fotografije in dokumenti (vojaška knjižica, odločbe, pisma), posneti s telefonom ali skenirani. Do ${n} datotek.`,
    chooseFiles: 'Izberite datoteke',
    addMore: 'Dodajte še',
    remove: 'Odstrani',
    notImage: 'Pošljete lahko samo fotografije in posnetke dokumentov (JPG ali PNG).',
    tooMany: (n: number) => `Največ ${n} datotek.`,
    tooLarge: (name: string) => `Datoteka ${name} je prevelika. Pošljite manjšo (do 9 MB).`,
    name: 'Vaše ime in priimek',
    relation: 'V kakšnem sorodstvu ste?',
    relationHint: 'npr. vnukinja, sin, sorodnik',
    email: 'E-pošta',
    optional: '(ni obvezno)',
    emailHint: 'E-naslov potrebujemo samo zato, da se vam lahko oglasimo: če ga vpišete, vam sporočimo, ko bo kartica borca dopolnjena. Ne bomo ga objavili ali dali nikomur in ne bomo vam pošiljali nezaželene pošte.',
    consentTitle: 'Kaj smemo objaviti',
    consentHint: 'Sprašujemo ločeno za dvoje: za vsebino in za vaše ime. Brez prvega dovoljenja ne objavimo ne fotografij ne vaše zgodbe, borca pa dodamo le s podatki o njem (rojstvo, enote, usoda). Brez drugega objavimo brez podpisa.',
    consent: 'Objava vsebine: to, kar pišem, in fotografije, ki jih pošiljam, se smejo objaviti na strani.',
    consentName: 'Objava imena: ob objavi sme pisati, kdo je to poslal, z začetnico imena, priimkom in sorodstvom (npr. »M. Novak, vnukinja«).',
    error: 'Sporočilo ni bilo poslano. Preverite internetno povezavo in poskusite znova.',
    send: 'Pošlji',
    sending: `Pošiljanje${dots}`,
    cancel: 'Prekliči',
    thanks: 'Hvala. Pregledali bomo, kar ste poslali.',
    willReply: 'Če kaj ne bo jasno, se vam bomo oglasili.',
    filesLost: (names: string) => `Te datoteke niso prispele: ${names}.`,
    sendAgain: 'Pošlji jih znova',
    sendingFile: (n: number, of: number) => `Pošiljanje datoteke ${n} od ${of}${dots}`,
  },

  family: {
    title: 'Iz družine',
    titleFacebook: 'S Facebook strani',
    titleVisitor: 'Od obiskovalcev',
    titleMixed: 'Iz družine in od obiskovalcev',
    wikipedia: 'Članek na Wikipediji',
    sent: (year: number, month?: number) => (month ? `${MONTHS[month - 1]} ${year}` : `${year}`),
    /** A family's photos and documents (components/FamilyStory.tsx) */
    kind: { photo: 'fotografija', document: 'dokument' },
    pages: (n: number) => `${n} str.`,
    page: (page: number, of: number) => `stran ${page} od ${of}`,
    transcript: 'Prepis',
    previous: 'Prejšnja',
    next: 'Naslednja',
    close: 'Zapri',
    open: (what: string) => `Odpri: ${what}`,
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
    title: 'Fotografije borcev',
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
    fullDescription: 'Celoten opis',
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
