import { formatNumber, plural } from '../format'

// The site's own text in Serbo-Croatian (ekavica, Latin script). VOICE.md says how it is written.
// Text in [brackets] becomes a link or a button where the page puts one.

const n = (x: number) => formatNumber('sr', x)

const MONTHS_GENITIVE = [
  'januara', 'februara', 'marta', 'aprila', 'maja', 'juna',
  'jula', 'avgusta', 'septembra', 'oktobra', 'novembra', 'decembra',
]
const MONTHS = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']

const borci = (x: number) => `${n(x)} ${plural('sr', x, { one: 'borac', few: 'borca', other: 'boraca' })}`
const godine = (x: number) => plural('sr', x, { one: 'godina', few: 'godine', other: 'godina' })

export const sr = {
  site: {
    name: 'Knjiga boraca',
    description: 'Spiskovi boraca partizanskih jedinica, pretraživi po imenu, sa stranom iz knjige uz svaki zapis.',
  },
  nav: { label: 'Glavna navigacija', home: 'Početna', gallery: 'Galerija', sources: 'Izvori' },
  theme: { label: 'Tema', light: 'Svetla tema', dark: 'Tamna tema', system: 'Sistemska tema' },
  language: { label: 'Jezik' },

  /** "15 boraca" */
  borci,
  /** "Pronađeno 15 boraca" */
  found: (x: number) => `${plural('sr', x, { one: 'Pronađen', few: 'Pronađena', other: 'Pronađeno' })} ${borci(x)}`,

  home: {
    title: 'Pretraga boraca',
    fieldLabel: 'Prezime, ime ili mesto',
    /** "110.430 imena": under the search field */
    total: (x: number) => `${n(x)} ${plural('sr', x, { one: 'ime', other: 'imena' })}`,
    loading: 'Učitavanje spiskova…',
    loadFailedTitle: 'Spiskovi se nisu učitali',
    loadFailedText: 'Proverite internet vezu i osvežite stranu.',
    noneTitle: (q: string) => `Nema boraca za „${q}“`,
    noneText:
      'Pokušajte samo prezime, ili ime i prezime bez očevog imena. Knjige često beleže očevo ime u genitivu, na primer „Milorada“ umesto „Milorad“.',
    unitsTitle: 'Jedinice',
    otherUnits: 'Ostale jedinice',
    /** The wartime portraits in the home page's margins */
    rails: 'Borci na fotografijama iz rata',
    bandCredit: 'Na fotografiji:',
  },

  filters: {
    toggle: 'Filteri',
    active: (x: number) => `(${x} uključeno)`,
    birthYear: 'Godina rođenja',
    range: 'Odstupanje od godine rođenja',
    exact: 'tačno',
    place: 'Mesto',
    placeHint: 'selo ili grad',
    unit: 'Jedinica',
    allUnits: 'Sve jedinice',
    fate: 'Sudbina',
    allFates: 'Svi',
    fates: { poginuli: 'Poginuli', umrli: 'Umrli', nestali: 'Nestali' },
    wholeWords: 'Samo cele reči',
    clear: 'Ukloni filtere',
    noneTitle: (q: string) => (q ? `Nema boraca za „${q}“ s ovim filterima` : 'Nema boraca s ovim filterima'),
    noneText: 'Proverite filtere ili ih [uklonite].',
  },

  share: { search: 'Podeli pretragu', copied: 'Link je kopiran', failed: 'Kopirajte adresu stranice' },

  results: {
    pageOf: (page: number, total: number) => `strana ${page} od ${total}`,
    /** While a search runs */
    searching: 'Pretraga…',
    perPage: 'Po strani',
    pages: 'Strane rezultata',
    previous: 'Prethodna',
    next: 'Sledeća',
  },

  onThisDay: {
    title: 'Na današnji dan',
    note: (day: number, month: number) => `Borci koji su ${day}. ${MONTHS_GENITIVE[month - 1]} poginuli, umrli ili nestali u ratu`,
    loading: 'Učitavanje',
    deathTitle: 'Godina i mesto smrti',
    missingTitle: 'Godina i mesto nestanka',
    death: 'Smrt:',
    missing: (female: boolean): string => (female ? 'Nestala' : 'Nestao'),
    /** "23 godine", "22/23 godine" */
    age: (from: number, to: number) => (from === to ? `${to} ${godine(to)}` : `${from}/${to} ${godine(to)}`),
    showLess: 'Prikaži manje',
    showAll: (x: number) => `Prikaži sve za ovaj dan (${x})`,
  },

  medals: { heroj: 'Narodni heroj', spomenica: 'Nosilac Partizanske spomenice 1941' },

  // The record's facts and its line of dated steps (scripts/extract_life_events.py). A step's own words (a duty, a
  // transfer, an illness) are the book's; printedLabels: the step shows them alone, without a label of its own.
  life: {
    title: 'Životni put',
    show: 'Pokaži u knjizi',
    /** "Iz zapisa na str. 57": where the steps of a soldier with one entry come from */
    source: (page: number | string) => `Iz zapisa na str. ${page}`,
    printedLabels: true,
    born: (woman: boolean): string => (woman ? 'Rođena' : 'Rođen'),
    skoj: 'Član SKOJ-a',
    kpj: 'Član KPJ',
    nob: 'U NOB',
    /** came to the unit: a brigade, division, detachment (odred) or another unit */
    unit: (kind: string): string => ({ brigade: 'U brigadi', division: 'U diviziji', detachment: 'U odredu' } as Record<string, string>)[kind] ?? 'U jedinici',
    duty: 'Dužnost',
    moved: 'Prekomandovan',
    ill: 'Oboleo',
    left: 'Otpušten',
    wounded: (woman: boolean): string => (woman ? 'Ranjena' : 'Ranjen'),
    captured: (woman: boolean): string => (woman ? 'Zarobljena' : 'Zarobljen'),
    exchanged: (woman: boolean): string => (woman ? 'Razmenjena' : 'Razmenjen'),
    /** the death as the record has it (death_type): poginuo, umro, nestao, streljan, ubijen */
    fate: (type: string | undefined, woman: boolean): string => {
      const words: Record<string, [string, string]> = {
        poginuo: ['Poginuo', 'Poginula'], umro: ['Umro', 'Umrla'], nestao: ['Nestao', 'Nestala'],
        streljan: ['Streljan', 'Streljana'], ubijen: ['Ubijen', 'Ubijena'],
      }
      return (words[type ?? ''] ?? ['Smrt', 'Smrt'])[woman ? 1 : 0]
    },
    /** a step's day or month under its year: "11. 7.", "decembar" */
    day: (d: number, m: number) => `${d}. ${m}.`,
    month: (m: number) => MONTHS[m - 1],
    /** where a fact leads, with its count */
    neighbours: (x: number) => `još ${n(x)} iz tog mesta`,
    comrades: (x: number) => borci(x),
    sameDay: (x: number) => `istog dana još ${n(x)}`,
    sameDayShort: 'istog dana',
    /** a death the record gives without a date or a place */
    undated: 'datum nije naveden',
  },

  record: {
    close: 'Zatvori',
    photo: 'Fotografija:',
    openPhoto: 'Otvori fotografiju',
    closePhoto: 'Zatvori fotografiju',
    /** Where a photograph comes from: "znaci.org, br. 13283", "znaci.org, knjiga o jedinici" */
    photoCredit: (credit: string) => credit,
    photoUnknown: 'Fotografija ovog borca nije poznata',
    entries: 'Zapisi u knjigama',
    page: (p: number | string) => `str. ${p}`,
    nameInBook: 'Ime u knjizi:',
    references: 'Reference',
    book: 'Knjiga',
    loadingPage: 'Učitavanje strane…',
    source: 'Izvor',
    noScan: 'Za ovaj spisak nema skenirane knjige: objavljen je kao tekst na [znaci.org].',
    steps: 'Susedni zapisi u spisku',
    previous: 'Prethodni',
    next: 'Sledeći',
    fields: {
      fathersName: 'Ime oca',
      birthYear: 'Godina rođenja',
      birthPlace: 'Mesto rođenja',
      ethnicity: 'Narodnost',
      occupation: 'Zanimanje',
      rank: 'Dužnost',
      unitDetail: 'Podjedinica',
      deathDate: 'Datum smrti',
      deathPlace: 'Mesto smrti',
      killedDate: 'Datum pogibije',
      killedPlace: 'Mesto pogibije',
    },
    /** "Petrović Milan. Prva lička proleterska brigada, Rajko Šarenac (ur.), str. 42. Knjiga boraca, zapis 0002000042." */
    citation: (name: string, where: string, page: number | null, id: string) =>
      `${name}. ${where}${page != null ? `, str. ${page}` : ''}. Knjiga boraca, zapis ${id}.`,
  },

  actions: {
    share: 'Podeli zapis',
    card: 'Spomen-kartica',
    cite: 'Citiraj',
    linkCopied: 'Link je kopiran.',
    link: 'Link do zapisa',
    copy: 'Kopiraj',
    copied: 'Kopirano',
  },

  report: {
    open: 'Vidite grešku u ovom zapisu? Prijavite je',
    label: 'Šta nije tačno?',
    hint: 'Na primer: prezime je u knjizi Adžić, a ovde piše Adzić.',
    send: 'Pošalji prijavu',
    cancel: 'Otkaži',
    sending: 'Slanje…',
    sent: 'Hvala, prijava je poslata. Proverićemo zapis u knjizi.',
    failed: 'Prijava nije poslata. Proverite internet vezu i [pokušajte ponovo].',
  },

  know: {
    prompt: 'Imate fotografiju ili znate nešto o ovom borcu?',
    open: 'Znam ovog borca',
    title: 'Znam ovog borca',
    relation: 'Ko ste vi ovom borcu?',
    relationHint: 'Na primer: unuka, sin, rođak, komšija',
    story: 'Šta znate o ovom borcu',
    storyHint: 'Šta porodica pamti, gde je grob, šta je bilo posle rata, ili šta u zapisu nije tačno.',
    photo: 'Fotografija',
    optional: '(nije obavezno)',
    choosePhoto: 'Izaberite fotografiju',
    chooseOther: 'Izaberite drugu',
    remove: 'Ukloni',
    notImage: 'Izaberite fotografiju (JPG ili PNG).',
    tooLarge: 'Fotografija je prevelika. Pošaljite manju (do 9 MB).',
    name: 'Vaše ime i prezime',
    email: 'Email',
    emailHint: 'Email nam služi samo da vam se javimo. Ne objavljujemo ga.',
    consent: 'Dozvoljavam da se fotografija i tekst objave uz ovaj zapis, sa mojim imenom.',
    error: 'Nije poslato. Proverite vezu sa internetom i pokušajte ponovo.',
    send: 'Pošalji',
    sending: 'Šalje se…',
    cancel: 'Otkaži',
    thanks: 'Hvala vam. Pogledaćemo ono što ste poslali.',
    willReply: 'Ako nešto ne bude jasno, javićemo vam se.',
    photoLost: 'Fotografija nije stigla zbog prekida veze; pošaljite je, molimo, još jednom.',
  },

  family: {
    title: 'Od porodice',
    sent: (year: number, month?: number) => (month ? `${MONTHS[month - 1]} ${year}.` : `${year}.`),
  },

  kin: {
    label: 'Saborci i zemljaci',
    comrades: 'Saborci',
    neighbours: 'Zemljaci',
    unit: 'Jedinica',
    birthplace: 'Mesto rođenja',
    sameDay: 'Stradali istog dana',
    samePlaceTag: 'isto mesto',
    sameDayTag: 'isti dan',
    thisRecord: 'ovaj zapis',
    more: (x: number) => `još ${n(x)}`,
    count: (x: number) => n(x),
    day: (d: number, m: number, y: number) => `${d}. ${m}. ${y}.`,
    // Sub-units, as the books name them
    battalion: (x: number) => `${x}. bataljon`,
    company: (x: number) => `${x}. četa`,
    platoon: (x: number) => `${x}. vod`,
    squad: (x: number) => `${x}. desetina`,
    staff: 'prištapske jedinice',
    noBattalion: 'bataljon nije naveden',
  },

  viewer: {
    failed: 'Strana iz knjige trenutno ne može da se prikaže.',
    previous: 'Prethodna strana',
    next: 'Sledeća strana',
    page: (p: number, total: number | null) => `str. ${p}${total ? ` / ${total}` : ''}`,
    back: 'Nazad na zapis',
    zoomOut: 'Umanji',
    zoomIn: 'Uvećaj',
    wholeBook: 'Cela knjiga na strani Izvori',
  },

  crop: {
    failed: 'Isečak iz knjige ne može da se prikaže.',
    loading: 'Učitavanje isečka iz knjige',
    alt: 'Zapis kako je odštampan u knjizi',
  },

  card: {
    title: 'Spomen-kartica',
    description: 'Zapis borca iz knjige boraca, za štampu.',
    loading: 'Učitava se zapis…',
    missingTitle: 'Ovaj zapis ne postoji',
    missingText: 'Link je možda nepotpun. Potražite borca na početnoj stranici.',
    failedTitle: 'Zapis se nije učitao',
    failedText: 'Proverite vezu sa internetom i osvežite stranicu.',
    back: 'Nazad na zapis',
    print: 'Odštampaj ili sačuvaj kao PDF',
    preparing: 'Priprema se isečak iz knjige…',
    entry: 'Zapis u knjizi',
    webText: 'tekst objavljen na znaci.org',
  },

  unit: {
    notFound: 'Jedinica nije pronađena',
    backHome: 'Nazad na početnu',
    allUnits: 'Sve jedinice',
    search: 'Pretraga u ovoj jedinici',
    placeholder: 'Prezime, ime ili mesto',
    loading: 'Učitavanje spiska',
    loadFailedTitle: 'Spisak se nije učitao',
    loadFailedText: 'Proverite internet vezu i osvežite stranu.',
    noneTitle: (q: string) => `Nema boraca za „${q}“ u ovoj jedinici`,
    noneText: 'Pokušajte samo prezime, ili potražite na [početnoj strani] u svim jedinicama.',
  },

  gallery: {
    title: 'Galerija',
    description: 'Fotografije boraca: lica iz knjiga jedinica i iz fotogalerije znaci.org.',
    label: (x: number) => `Fotografije boraca (${n(x)})`,
  },

  sources: {
    metaTitle: 'Izvori',
    metaDescription: 'Izvorni dokumenti korišćeni za bazu podataka boraca NOB-a.',
    title: 'Izvorni dokumenti',
    intro:
      'Podaci o borcima prikupljeni su iz monografija brigada i spiskova boraca objavljenih u izdanjima Vojnoistorijskog instituta. Ovde možete pregledati i preuzeti originalne PDF dokumente.',
    openPdf: 'Otvori PDF',
    download: 'Preuzmi',
    openList: 'Otvori spisak',
    medalsTitle: 'Slike odlikovanja',
    hero:
      'Orden narodnog heroja: fotografija [Pinki, Wikimedia Commons], licenca [CC BY-SA 4.0]. Isečak i crtež ordena na ovom sajtu napravljeni su od te fotografije i objavljeni pod istom licencom.',
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.sr-latn',
    spomenica:
      'Partizanska spomenica 1941: slika iz registra državnih znakova Svetske organizacije za intelektualnu svojinu (WIPO), [javno dobro].',
  },

  /** The month by name in running text: "8. jula 1942.", "u septembru 1943." */
  date: (day: number | undefined, month: number, year: number) =>
    day ? `${day}. ${MONTHS_GENITIVE[month - 1]} ${year}.` : `${MONTHS[month - 1]} ${year}.`,
}

export type Messages = typeof sr
