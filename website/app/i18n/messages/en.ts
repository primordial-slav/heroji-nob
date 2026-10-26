import { dateNumbers, formatNumber, plural } from '../format'
import type { Messages } from './sr'

// English (British spelling). Written for English readers, many of them descendants abroad, not translated
// word for word: "Partisans" (capitalised, as English-language histories write it) for the people on the
// lists, "roll" for a unit's list, "record" for a person's page and "entry" for the printed text,
// day-month-year dates ("8 July 1942") and ‘single’ quotes. VOICE.md, section "English".

const n = (x: number) => formatNumber('en', x)

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** "1st", "2nd", "3rd", "11th", "21st" */
export function enOrdinal(x: number): string {
  const mod100 = x % 100
  const mod10 = x % 10
  if (mod100 >= 11 && mod100 <= 13) return `${x}th`
  return `${x}${mod10 === 1 ? 'st' : mod10 === 2 ? 'nd' : mod10 === 3 ? 'rd' : 'th'}`
}

const partisans = (x: number) => `${n(x)} ${plural('en', x, { one: 'Partisan', other: 'Partisans' })}`

export const en: Messages = {
  site: {
    name: 'Knjiga boraca',
    description: 'The rolls of Yugoslav Partisan units, searchable by name, with the page from the book beside every record.',
  },
  nav: { label: 'Main navigation', home: 'Home', units: 'Units', gallery: 'Gallery', sources: 'Sources' },
  theme: { label: 'Theme', light: 'Light theme', dark: 'Dark theme', system: 'Same as system' },
  language: { label: 'Language' },
  notFound: {
    title: 'This page doesn’t exist',
    text: 'The address may be old or mistyped. Look for a Partisan by name on the home page.',
  },

  borci: partisans,
  found: (x: number) => `${partisans(x)} found`,

  home: {
    title: 'Find a Partisan',
    fieldLabel: 'Surname, name or place',
    total: (x: number) => `${n(x)} ${plural('en', x, { one: 'name', other: 'names' })}`,
    loading: 'Loading the rolls…',
    loadFailedTitle: 'The rolls did not load',
    loadFailedText: 'Check your internet connection and reload the page.',
    noneTitle: (q: string) => `No one found for ‘${q}’`,
    noneText:
      'Try the surname alone, or the first name and surname without the father’s name. The books often give the father’s name in the possessive form, such as ‘Milorada’ (Milorad’s) rather than ‘Milorad’. Letters such as č and ć can be typed as c.',
    doors: {
      title: 'Explore',
      units: 'Units',
      unitsText: 'Brigades, divisions and detachments by the year they were formed, each with its list of fighters.',
      unitsCount: (x: number) => `${n(x)} ${x === 1 ? 'unit' : 'units'}`,
      photos: 'Photographs',
      photosText: 'Faces of fighters from their units’ books, from znaci.org and from family albums.',
      photosCount: (x: number) => `${n(x)} ${x === 1 ? 'photograph' : 'photographs'}`,
      books: 'Books',
      booksText: 'The books and lists the names come from, with their scanned pages.',
      booksCount: (x: number) => `${n(x)} ${x === 1 ? 'source' : 'sources'}`,
    },
    news: {
      title: 'What’s new',
      date: (d: number, m: number, y: number) =>
        `${d} ${['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
          'November', 'December'][m - 1]} ${y}`,
      more: 'Show older',
    },
    otherUnits: 'Other units',
    noUnit: 'Without a unit',
    census: 'The 1964 census of war victims',
    censusLead: 'Fighters killed or dead in the war whose unit is not on the site yet, by republic and province.',
    /** The wartime portraits in the home page's margins */
    rails: 'Partisans in wartime photographs',
    bandCredit: 'In the photograph:',
  },

  filters: {
    toggle: 'Filters',
    active: (x: number) => `(${x} on)`,
    birthYear: 'Year of birth',
    range: 'Years either side',
    exact: 'exact',
    place: 'Place',
    placeHint: 'village or town',
    unit: 'Unit',
    allUnits: 'All units',
    fate: 'Fate',
    allFates: 'All',
    fates: { poginuli: 'Killed', umrli: 'Died', nestali: 'Missing' },
    wholeWords: 'Whole words only',
    clear: 'Clear filters',
    noneTitle: (q: string) => (q ? `No one found for ‘${q}’ with these filters` : 'No one matches these filters'),
    noneText: 'Check the filters or [clear them].',
  },

  share: { search: 'Share this search', copied: 'Link copied', failed: 'Copy the page address' },

  results: {
    pageOf: (page: number, total: number) => `page ${page} of ${total}`,
    searching: 'Searching…',
    perPage: 'Per page',
    pages: 'Result pages',
    previous: 'Previous',
    next: 'Next',
    noExact: 'No exact match',
    similar: (x: number, more: boolean) =>
      `${n(x)} ${more ? 'more ' : ''}similar ${plural('en', x, { one: 'record', other: 'records' })}`,
    similarTitle: 'Similar records',
    similarNote: 'A name or place spelled a little differently, or missing one of the words searched for.',
  },

  onThisDay: {
    title: 'On this day',
    note: (day: number, month: number) => `Partisans who were killed, died or went missing on ${day} ${MONTHS[month - 1]} during the war`,
    loading: 'Loading',
    deathTitle: 'Year and place of death',
    missingTitle: 'Year and place last seen',
    death: 'Died:',
    missing: () => 'Missing',
    age: (from: number, to: number) => (from === to ? `aged ${to}` : `aged ${from} or ${to}`),
    showLess: 'Show fewer',
    showAll: (x: number) => `Show everyone for this day (${x})`,
  },

  medals: { heroj: 'People’s Hero', spomenica: 'Holder of the Partisan Commemorative Medal 1941' },

  life: {
    title: 'Timeline',
    show: 'Show in the book',
    source: (page: number | string) => `From the entry on p. ${page}`,
    printedLabels: false,
    born: () => 'Born',
    skoj: 'Joined the Young Communists (SKOJ)',
    kpj: 'Joined the Communist Party',
    member: () => 'Member',
    party: (items: [string, string][]) =>
      items.map(([org, year]) => (({
        SKOJ: 'the Young Communists (SKOJ)', KPJ: 'the Communist Party (KPJ)',
        KPH: 'the Communist Party of Croatia (KPH)', KPS: 'the Communist Party of Slovenia (KPS)',
      } as Record<string, string>)[org] ?? org) + (year ? ` from ${year}` : '')).join(', '),
    nob: 'Joined the Partisans',
    unit: (kind: string) => ({ brigade: 'Joined the brigade', division: 'Joined the division', detachment: 'Joined the detachment' } as Record<string, string>)[kind] ?? 'Joined the unit',
    duty: 'Duty',
    moved: 'Transferred',
    ill: 'Fell ill',
    left: 'Discharged',
    wounded: () => 'Wounded',
    captured: () => 'Captured',
    exchanged: () => 'Exchanged',
    fate: (type: string | undefined) =>
      ({ poginuo: 'Killed in action', umro: 'Died', nestao: 'Missing', streljan: 'Shot', ubijen: 'Killed', zarobljen: 'Captured' } as Record<string, string>)[type ?? ''] ?? 'Died',
    day: (d: number, m: number) => dateNumbers(d, m),
    month: (m: number) => MONTHS[m - 1],
    neighbours: (x: number) => `${n(x)} more from the same place`,
    comrades: (x: number) => partisans(x),
    sameDay: (x: number) => `${n(x)} more the same day`,
    sameDayShort: 'the same day',
    undated: 'date not given',
    afterWar: 'after the war',
  },

  record: {
    close: 'Close',
    photo: 'Photograph:',
    openPhoto: 'Open the photograph',
    closePhoto: 'Close the photograph',
    /** Where a photograph comes from: "znaci.org, br. 13283", "znaci.org, knjiga o jedinici" */
    photoCredit: (credit: string) => credit.replace(', br. ', ', no. ').replace(', knjiga o jedinici', ', the unit’s book'),
    photoUnknown: 'No photograph of this Partisan is known',
    entries: 'Entries in the books',
    page: (p: number | string) => `p. ${p}`,
    nameInBook: 'Name in the book:',
    moreEntries: (count: number) =>
      count === 1 ? 'One more entry in another book' : `${n(count)} more entries in other books`,
    showPage: 'Show the page in the book',
    references: 'References',
    book: 'Book',
    loadingPage: 'Loading the page…',
    source: 'Source',
    noScan: 'There is no scanned book for this roll: it was published as text on [znaci.org].',
    noScanPoreklo: (title: string, page: number | null) =>
      `${title}${page != null ? `, page ${page}` : ''}. The book is scanned in the Poreklo digital library, which only its members can open.`,
    steps: 'Neighbouring records on the roll',
    previous: 'Previous',
    next: 'Next',
    fields: {
      fathersName: 'Father’s name',
      birthYear: 'Year of birth',
      birthPlace: 'Place of birth',
      ethnicity: 'Ethnicity',
      occupation: 'Occupation',
      rank: 'Role',
      unitDetail: 'Sub-unit',
      deathDate: 'Date of death',
      deathPlace: 'Place of death',
      killedDate: 'Killed',
      killedPlace: 'Place killed',
    },
    citation: (name: string, where: string, page: number | null, id: string) =>
      `${name}. ${where}${page != null ? `, p. ${page}` : ''}. Knjiga boraca, record ${id}.`,
  },

  actions: {
    share: 'Share this record',
    card: 'Memorial card',
    cite: 'Cite',
    linkCopied: 'Link copied.',
    link: 'Link to this record',
    copy: 'Copy',
    copied: 'Copied',
  },

  report: {
    open: 'Spotted a mistake in this record? Let us know',
    label: 'What is wrong?',
    hint: 'For example: the book has the surname Adžić, but here it says Adzić.',
    send: 'Send',
    cancel: 'Cancel',
    sending: 'Sending…',
    sent: 'Thank you, your note has been sent. We will check the record against the book.',
    failed: 'Your note was not sent. Check your internet connection and [try again].',
  },

  know: {
    prompt: 'Do you have a photograph of this Partisan, or know something about them?',
    open: 'I know about this Partisan',
    title: 'I know about this Partisan',
    relation: 'How are you connected to this Partisan?',
    relationHint: 'For example: granddaughter, son, cousin, neighbour',
    story: 'What you know about this Partisan',
    storyHint: 'What the family remembers, where the grave is, what happened after the war, or what is wrong in the record.',
    photo: 'Photograph',
    optional: '(optional)',
    choosePhoto: 'Choose a photograph',
    chooseOther: 'Choose another',
    remove: 'Remove',
    notImage: 'Please choose a photograph (JPG or PNG).',
    tooLarge: 'The photograph is too large. Please send a smaller one (up to 9 MB).',
    name: 'Your full name',
    email: 'Email',
    emailHint: 'We use your email only to get back to you. We never publish it.',
    consent: 'I agree that the photograph and text may be published with this record, under my name.',
    error: 'Not sent. Check your internet connection and try again.',
    send: 'Send',
    sending: 'Sending…',
    cancel: 'Cancel',
    thanks: 'Thank you. We will look at what you sent.',
    willReply: 'If anything is unclear, we will get in touch.',
    photoLost: 'The photograph did not arrive because the connection dropped; please send it again.',
  },

  family: {
    title: 'From the family',
    sent: (year: number, month?: number) => (month ? `${MONTHS[month - 1]} ${year}` : `${year}`),
  },

  kin: {
    label: 'Comrades and neighbours',
    comrades: 'Comrades',
    neighbours: 'Neighbours',
    unit: 'Unit',
    birthplace: 'Place of birth',
    sameDay: 'Killed the same day',
    samePlaceTag: 'same place',
    sameDayTag: 'same day',
    thisRecord: 'this record',
    more: (x: number) => `${n(x)} more`,
    count: (x: number) => n(x),
    day: (d: number, m: number, y: number) => dateNumbers(d, m, y),
    battalion: (x: number) => `${enOrdinal(x)} Battalion`,
    company: (x: number) => `${enOrdinal(x)} Company`,
    platoon: (x: number) => `${enOrdinal(x)} Platoon`,
    squad: (x: number) => `${enOrdinal(x)} Squad`,
    staff: 'staff units',
    noBattalion: 'battalion not given',
  },

  viewer: {
    failed: 'This page of the book cannot be shown at the moment.',
    previous: 'Previous page',
    next: 'Next page',
    page: (p: number, total: number | null) => `p. ${p}${total ? ` / ${total}` : ''}`,
    back: 'Back to the record',
    zoomOut: 'Zoom out',
    zoomIn: 'Zoom in',
    wholeBook: 'The whole book is under Sources',
  },

  crop: {
    failed: 'The entry from the book cannot be shown.',
    loading: 'Loading the entry from the book',
    alt: 'The entry as printed in the book',
  },

  card: {
    title: 'Memorial card',
    description: 'A Partisan’s record from the rolls, ready to print.',
    loading: 'Loading the record…',
    missingTitle: 'This record does not exist',
    missingText: 'The link may be incomplete. Search for the Partisan on the home page.',
    failedTitle: 'The record did not load',
    failedText: 'Check your internet connection and reload the page.',
    back: 'Back to the record',
    print: 'Print or save as PDF',
    preparing: 'Preparing the entry from the book…',
    entry: 'The entry in the book',
    webText: 'text published on znaci.org',
  },

  unit: {
    notFound: 'Unit not found',
    backHome: 'Back to the home page',
    allUnits: 'All units',
    search: 'Search this unit',
    placeholder: 'Surname, name or place',
    loading: 'Loading the roll',
    loadFailedTitle: 'The roll did not load',
    loadFailedText: 'Check your internet connection and reload the page.',
    noneTitle: (q: string) => `No one found for ‘${q}’ in this unit`,
    noneText: 'Try the surname alone, or search every unit from the [home page].',
  },

  unitsPage: {
    title: 'Units',
    description: 'Every unit on the site by the year it was formed: brigades, divisions and detachments, each with its list of fighters.',
    lead: (x: number) => `${n(x)} ${x === 1 ? 'unit' : 'units'} by the year they were formed, each with its list of fighters.`,
    years: 'Year formed',
    allYears: 'All',
    find: 'Unit name',
    partOf: 'Part of',
    none: (q: string) => `No unit matches “${q}”`,
    noneText: 'Try part of the name: a number, a place or a name, such as “Lika” or “13th”.',
    kinds: 'Kind of unit',
    kind: { brigada: 'Brigades', divizija: 'Divisions', odred: 'Detachments', ostalo: 'Other' },
    lands: 'Republic',
    land: {
      bih: 'Bosnia and Herzegovina', 'crna-gora': 'Montenegro', hrvatska: 'Croatia', makedonija: 'Macedonia',
      slovenija: 'Slovenia', srbija: 'Serbia',
    },
    noneChosen: 'No unit matches this choice',
    noneChosenText: 'Remove a filter or choose another year.',
  },
  gallery: {
    title: 'Gallery',
    description: 'Photographs of the Partisans: faces from the units’ books and from the znaci.org photo archive.',
    label: (x: number) => `Photographs of the Partisans (${n(x)})`,
  },

  sources: {
    metaTitle: 'Sources',
    metaDescription: 'The books the rolls of Partisans come from, each with its scan.',
    title: 'Original documents',
    intro:
      'The details of each Partisan come from brigade histories and from rolls published by the Military History Institute in Belgrade. You can read and download the original PDFs here.',
    openPdf: 'Open PDF',
    download: 'Download',
    openList: 'Open the roll',
    inPoreklo: 'In the Poreklo digital library, for its members only',
    medalsTitle: 'Images of the decorations',
    hero:
      'Order of the People’s Hero: photograph by [Pinki, Wikimedia Commons], licence [CC BY-SA 4.0]. The cut-out and the drawing of the order on this site were made from that photograph and are published under the same licence.',
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.en',
    spomenica:
      'Partisan Commemorative Medal 1941: image from the register of state emblems of the World Intellectual Property Organization (WIPO), [public domain].',
    placesTitle: 'Places',
    places:
      'Places of birth and death are identified with the [GeoNames] geographical database, licence [CC BY 4.0]. With it, the “Comrades and neighbours” tree keeps together the fighters of one village however the books spell it, and a place a book prints in a grammatical case (“u Užicu”) is given here in its base form.',
    placesLicense: 'https://creativecommons.org/licenses/by/4.0/deed.en',
  },

  date: (day: number | undefined, month: number, year: number) =>
    day ? `${day} ${MONTHS[month - 1]} ${year}` : `${MONTHS[month - 1]} ${year}`,
}
