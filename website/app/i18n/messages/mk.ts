import { formatNumber, plural } from '../format'
import type { Messages } from './sr'

// Македонски. Written for Macedonian readers, not translated word for word: the Macedonian words for the
// war (загинати, починати, исчезнати, соборци, земјаци), the definite article and the doubled object
// ("проверете ја врската"), ordinals as Macedonian writes them ("13-та бригада", "1-ви баталјон") and dates
// without a full stop after the day ("8 јули 1942"). Names from the books stay as the books print them.
// VOICE.md, section "Македонски".

const n = (x: number) => formatNumber('mk', x)

const MONTHS = ['јануари', 'февруари', 'март', 'април', 'мај', 'јуни', 'јули', 'август', 'септември', 'октомври', 'ноември', 'декември']

/** "1-ви", "2-ри", "7-ми", "13-ти"; feminine "1-ва", "2-ра", "13-та" */
export function mkOrdinal(x: number, feminine = false): string {
  const mod100 = x % 100
  const mod10 = x % 10
  let ending = 'ти'
  if (mod100 < 11 || mod100 > 19) {
    if (mod10 === 1) ending = 'ви'
    else if (mod10 === 2) ending = 'ри'
    else if (mod10 === 7 || mod10 === 8) ending = 'ми'
  }
  return `${x}-${feminine ? ending.replace(/и$/, 'а') : ending}`
}

const borci = (x: number) => `${n(x)} ${plural('mk', x, { one: 'борец', other: 'борци' })}`
const godini = (x: number) => plural('mk', x, { one: 'година', other: 'години' })

export const mk: Messages = {
  site: {
    name: 'Книга на борците',
    description: 'Списоци на борците од партизанските единици. Може да се пребарува по име, а покрај секој запис стои страницата од книгата.',
  },
  nav: { label: 'Главна навигација', home: 'Почетна', gallery: 'Галерија', sources: 'Извори' },
  theme: { label: 'Изглед', light: 'Светла тема', dark: 'Темна тема', system: 'Според системот' },
  language: { label: 'Јазик' },

  borci,
  found: (x: number) => `${plural('mk', x, { one: 'Најден', other: 'Најдени' })} ${borci(x)}`,

  home: {
    title: 'Пребарување борци',
    fieldLabel: 'Презиме, име или место',
    total: (x: number) => `${n(x)} ${plural('mk', x, { one: 'име', other: 'имиња' })}`,
    loading: 'Се вчитуваат списоците…',
    loadFailedTitle: 'Списоците не се вчитаа',
    loadFailedText: 'Проверете ја интернет-врската и освежете ја страницата.',
    noneTitle: (q: string) => `Нема резултати за „${q}“`,
    noneText:
      'Обидете се само со презимето, или со име и презиме без татковото име. Книгите често го пишуваат татковото име со падежна наставка, на пример „Milorada“ наместо „Milorad“.',
    unitsTitle: 'Единици',
    otherUnits: 'Други единици',
    /** The wartime portraits in the home page's margins */
    rails: 'Борци на фотографии од војната',
    bandCredit: 'На фотографијата:',
  },

  filters: {
    toggle: 'Филтри',
    active: (x: number) => `(вклучени: ${x})`,
    birthYear: 'Година на раѓање',
    range: 'Отстапување од годината на раѓање',
    exact: 'точно',
    place: 'Место',
    placeHint: 'село или град',
    unit: 'Единица',
    allUnits: 'Сите единици',
    fate: 'Судбина',
    allFates: 'Сите',
    fates: { poginuli: 'Загинати', umrli: 'Починати', nestali: 'Исчезнати' },
    wholeWords: 'Само цели зборови',
    clear: 'Отстрани ги филтрите',
    noneTitle: (q: string) => (q ? `Нема резултати за „${q}“ со овие филтри` : 'Нема резултати со овие филтри'),
    noneText: 'Проверете ги филтрите или [отстранете ги].',
  },

  share: { search: 'Сподели го пребарувањето', copied: 'Врската е копирана', failed: 'Копирајте ја адресата на страницата' },

  results: {
    pageOf: (page: number, total: number) => `страница ${page} од ${total}`,
    searching: 'Се пребарува…',
    perPage: 'По страница',
    pages: 'Страници со резултати',
    previous: 'Претходна',
    next: 'Следна',
  },

  onThisDay: {
    title: 'На денешен ден',
    note: (day: number, month: number) => `Борци што загинале, починале или исчезнале во војната на ${day} ${MONTHS[month - 1]}`,
    loading: 'Се вчитува',
    deathTitle: 'Година и место на смртта',
    missingTitle: 'Година и место на исчезнувањето',
    death: 'Смрт:',
    missing: (female: boolean) => (female ? 'Исчезната' : 'Исчезнат'),
    age: (from: number, to: number) => (from === to ? `${to} ${godini(to)}` : `${from}/${to} ${godini(to)}`),
    showLess: 'Прикажи помалку',
    showAll: (x: number) => `Прикажи ги сите за овој ден (${x})`,
  },

  medals: { heroj: 'Народен херој', spomenica: 'Носител на Партизанска споменица 1941' },

  life: {
    title: 'Животен пат',
    show: 'Покажи во книгата',
    source: (page: number | string) => `Од записот на стр. ${page}`,
    printedLabels: false,
    born: (woman: boolean) => (woman ? 'Родена' : 'Роден'),
    skoj: 'Член на СКОЈ',
    kpj: 'Член на КПЈ',
    nob: 'Во НОБ',
    unit: (kind: string) => ({ brigade: 'Во бригадата', division: 'Во дивизијата', detachment: 'Во одредот' } as Record<string, string>)[kind] ?? 'Во единицата',
    duty: 'Должност',
    moved: 'Преместен',
    ill: 'Заболел',
    left: 'Отпуштен',
    wounded: (woman: boolean) => (woman ? 'Ранета' : 'Ранет'),
    captured: (woman: boolean) => (woman ? 'Заробена' : 'Заробен'),
    exchanged: (woman: boolean) => (woman ? 'Разменета' : 'Разменет'),
    fate: (type: string | undefined, woman: boolean) => {
      const words: Record<string, [string, string]> = {
        poginuo: ['Загинал', 'Загинала'], umro: ['Починал', 'Починала'], nestao: ['Исчезнат', 'Исчезната'],
        streljan: ['Стрелан', 'Стрелана'], ubijen: ['Убиен', 'Убиена'],
      }
      return (words[type ?? ''] ?? ['Смрт', 'Смрт'])[woman ? 1 : 0]
    },
    day: (d: number, m: number) => `${d}.${m}`,
    month: (m: number) => MONTHS[m - 1],
    neighbours: (x: number) => `уште ${n(x)} од истото место`,
    comrades: (x: number) => borci(x),
    sameDay: (x: number) => `истиот ден уште ${n(x)}`,
    sameDayShort: 'истиот ден',
  },

  record: {
    close: 'Затвори',
    photo: 'Фотографија:',
    openPhoto: 'Отвори ја фотографијата',
    closePhoto: 'Затвори ја фотографијата',
    /** Where a photograph comes from: "znaci.org, br. 13283", "znaci.org, knjiga o jedinici" */
    photoCredit: (credit: string) => credit.replace(', br. ', ', бр. ').replace(', knjiga o jedinici', ', книга за единицата'),
    photoUnknown: 'Фотографијата на овој борец не е позната',
    entries: 'Записи во книгите',
    page: (p: number | string) => `стр. ${p}`,
    nameInBook: 'Името во книгата:',
    references: 'Референци',
    book: 'Книга',
    loadingPage: 'Се вчитува страницата…',
    source: 'Извор',
    noScan: 'За овој список нема скенирана книга: објавен е како текст на [znaci.org].',
    steps: 'Соседни записи во списокот',
    previous: 'Претходен',
    next: 'Следен',
    fields: {
      fathersName: 'Татково име',
      birthYear: 'Година на раѓање',
      birthPlace: 'Место на раѓање',
      ethnicity: 'Националност',
      occupation: 'Занимање',
      rank: 'Должност',
      unitDetail: 'Потединица',
      deathDate: 'Датум на смртта',
      deathPlace: 'Место на смртта',
      killedDate: 'Датум на загинувањето',
      killedPlace: 'Место на загинувањето',
    },
    citation: (name: string, where: string, page: number | null, id: string) =>
      `${name}. ${where}${page != null ? `, стр. ${page}` : ''}. Книга на борците, запис ${id}.`,
  },

  actions: {
    share: 'Сподели го записот',
    card: 'Спомен-картичка',
    cite: 'Цитирај',
    linkCopied: 'Врската е копирана.',
    link: 'Врска до записот',
    copy: 'Копирај',
    copied: 'Копирано',
  },

  report: {
    open: 'Забележавте грешка во овој запис? Пријавете ја',
    label: 'Што не е точно?',
    hint: 'На пример: во книгата презимето е Adžić, а тука пишува Adzić.',
    send: 'Испрати пријава',
    cancel: 'Откажи',
    sending: 'Се испраќа…',
    sent: 'Ви благодариме, пријавата е испратена. Ќе го провериме записот во книгата.',
    failed: 'Пријавата не е испратена. Проверете ја интернет-врската и [обидете се повторно].',
  },

  know: {
    prompt: 'Имате фотографија или знаете нешто за овој борец?',
    open: 'Знам за овој борец',
    title: 'Знам за овој борец',
    relation: 'Која е вашата врска со борецот?',
    relationHint: 'На пример: внука, син, роднина, сосед',
    story: 'Што знаете за овој борец',
    storyHint: 'Што се памети во семејството, каде е гробот, што било по војната или што не е точно во записот.',
    photo: 'Фотографија',
    optional: '(не е задолжително)',
    choosePhoto: 'Изберете фотографија',
    chooseOther: 'Изберете друга',
    remove: 'Отстрани',
    notImage: 'Изберете фотографија (JPG или PNG).',
    tooLarge: 'Фотографијата е преголема. Испратете помала (до 9 MB).',
    name: 'Вашето име и презиме',
    email: 'Е-пошта',
    emailHint: 'Е-поштата ни треба само за да ви одговориме. Не ја објавуваме.',
    consent: 'Дозволувам фотографијата и текстот да се објават покрај овој запис, со моето име.',
    error: 'Не е испратено. Проверете ја интернет-врската и обидете се повторно.',
    send: 'Испрати',
    sending: 'Се испраќа…',
    cancel: 'Откажи',
    thanks: 'Ви благодариме. Ќе го прегледаме она што го испративте.',
    willReply: 'Ако нешто не е јасно, ќе ви се јавиме.',
    photoLost: 'Фотографијата не пристигна поради прекин на врската; ве молиме, испратете ја уште еднаш.',
  },

  family: {
    title: 'Од семејството',
    sent: (year: number, month?: number) => (month ? `${MONTHS[month - 1]} ${year}` : `${year}`),
  },

  kin: {
    label: 'Соборци и земјаци',
    comrades: 'Соборци',
    neighbours: 'Земјаци',
    unit: 'Единица',
    birthplace: 'Место на раѓање',
    sameDay: 'Загинати истиот ден',
    samePlaceTag: 'исто место',
    sameDayTag: 'ист ден',
    thisRecord: 'овој запис',
    more: (x: number) => `уште ${n(x)}`,
    count: (x: number) => n(x),
    day: (d: number, m: number, y: number) => `${d}.${m}.${y}`,
    battalion: (x: number) => `${mkOrdinal(x)} баталјон`,
    company: (x: number) => `${mkOrdinal(x, true)} чета`,
    platoon: (x: number) => `${mkOrdinal(x)} вод`,
    squad: (x: number) => `${mkOrdinal(x, true)} десетина`,
    staff: 'единици при штабот',
    noBattalion: 'баталјонот не е наведен',
  },

  viewer: {
    failed: 'Страницата од книгата моментално не може да се прикаже.',
    previous: 'Претходна страница',
    next: 'Следна страница',
    page: (p: number, total: number | null) => `стр. ${p}${total ? ` / ${total}` : ''}`,
    back: 'Назад кон записот',
    zoomOut: 'Намали',
    zoomIn: 'Зголеми',
    wholeBook: 'Целата книга е меѓу изворите',
  },

  crop: {
    failed: 'Исечокот од книгата не може да се прикаже.',
    loading: 'Се вчитува исечокот од книгата',
    alt: 'Записот како што е отпечатен во книгата',
  },

  card: {
    title: 'Спомен-картичка',
    description: 'Запис за борец од книгата, подготвен за печатење.',
    loading: 'Се вчитува записот…',
    missingTitle: 'Овој запис не постои',
    missingText: 'Врската можеби е нецелосна. Побарајте го борецот на почетната страница.',
    failedTitle: 'Записот не се вчита',
    failedText: 'Проверете ја интернет-врската и освежете ја страницата.',
    back: 'Назад кон записот',
    print: 'Отпечати или зачувај како PDF',
    preparing: 'Се подготвува исечокот од книгата…',
    entry: 'Запис во книгата',
    webText: 'текст објавен на znaci.org',
  },

  unit: {
    notFound: 'Единицата не е пронајдена',
    backHome: 'Назад на почетната страница',
    allUnits: 'Сите единици',
    search: 'Пребарување во оваа единица',
    placeholder: 'Презиме, име или место',
    loading: 'Се вчитува списокот',
    loadFailedTitle: 'Списокот не се вчита',
    loadFailedText: 'Проверете ја интернет-врската и освежете ја страницата.',
    noneTitle: (q: string) => `Нема резултати за „${q}“ во оваа единица`,
    noneText: 'Обидете се само со презимето или пребарајте ги сите единици на [почетната страница].',
  },

  gallery: {
    title: 'Галерија',
    description: 'Фотографии на борците: лица од книгите на единиците и од фотогалеријата на znaci.org.',
    label: (x: number) => `Фотографии на борците (${n(x)})`,
  },

  sources: {
    metaTitle: 'Извори',
    metaDescription: 'Книгите од кои се земени списоците на борците, со скен од секоја книга.',
    title: 'Изворни документи',
    intro:
      'Податоците за борците се собрани од монографиите на бригадите и од списоците на борци што ги објавил Воено-историскиот институт во Белград. Тука можете да ги прегледате и да ги преземете оригиналните документи во PDF.',
    openPdf: 'Отвори PDF',
    download: 'Преземи',
    openList: 'Отвори го списокот',
    medalsTitle: 'Слики од одликувањата',
    hero:
      'Орден на народен херој: фотографија [Pinki, Wikimedia Commons], лиценца [CC BY-SA 4.0]. Исечокот и цртежот на орденот на оваа страница се направени од таа фотографија и се објавени под истата лиценца.',
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.mk',
    spomenica:
      'Партизанска споменица 1941: слика од регистарот на државни знаци на Светската организација за интелектуална сопственост (WIPO), [јавен домен].',
  },

  date: (day: number | undefined, month: number, year: number) =>
    day ? `${day} ${MONTHS[month - 1]} ${year}` : `${MONTHS[month - 1]} ${year}`,
}
