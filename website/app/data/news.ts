import type { Lang } from '@/app/i18n/config'
import { toCyrillic } from '@/app/i18n/cyrillic'

// "Šta je novo" on the home page: the site's recent changes, newest first. A big one has a title and a sentence or
// two; a small one is one line. Changes of a few days may stand as one. Each text in Serbo-Croatian (Latin; the
// Cyrillic is made from it), Slovene, Macedonian and English, written as VOICE.md says: plain, short, no pathos.

type Text = Record<'sr' | 'sl' | 'mk' | 'en', string>

export interface NewsItem {
  date: string // YYYY-MM-DD
  title?: Text // the big ones
  text: Text
}

export const NEWS: NewsItem[] = [
  {
    date: '2026-10-19',
    title: {
      sr: 'Spiskovi koji su bili samo slike',
      sl: 'Seznami, ki so bili le slike',
      mk: 'Списоци што беа само слики',
      en: 'Lists that were only images',
    },
    text: {
      sr: 'Četiri spiska sa znaci.org koji su bili samo skenirane slike sada su pročitani: ceo spisak 1. bokeljske brigade po jedinicama (oko 3.100 boraca), pali borci Nikšićkog i Lovćenskog odreda i borci opštine Teslić. Oko 640 zapisa iz njih dodato je zapisima koji već postoje, a oko 2.200 drugih je među Ostalim borcima.',
      sl: 'Štirje seznami z znaci.org, ki so bili le skenirane slike, so zdaj prebrani: celoten seznam 1. bokeljske brigade po enotah (okoli 3.100 borcev), padli borci Nikšićkega in Lovćenskega odreda ter borci občine Teslić. Okoli 640 zapisov iz njih je dodanih zapisom, ki že obstajajo, okoli 2.200 drugih je med Drugimi borci.',
      mk: 'Четири списоци од znaci.org што беа само скенирани слики сега се прочитани: целиот список на 1-ва бокељска бригада по единици (околу 3.100 борци), паднатите борци на Никшиќкиот и Ловќенскиот одред и борците од општината Теслиќ. Околу 640 записи од нив се приклучени кон записите што веќе постојат, а околу 2.200 други се меѓу Другите борци.',
      en: 'Four lists on znaci.org that were only scanned images have now been read: the 1st Boka Brigade’s whole roll by unit (some 3,100 fighters), the fallen of the Nikšić and Lovćen detachments, and the fighters of the Teslić municipality. About 640 of their entries have been added to records already on the site; some 2,200 others are among the Other fighters.',
    },
  },
  {
    date: '2026-10-19',
    text: {
      sr: 'Šest knjiga o selima Like i Bosanskog Grahova: oko 1.500 palih i drugih boraca, 400 pridruženo zapisima koji već postoje.',
      sl: 'Šest knjig o vaseh Like in Bosanskega Grahova: okoli 1.500 padlih in drugih borcev, 400 pridruženih zapisom, ki že obstajajo.',
      mk: 'Шест книги за селата во Лика и Босанско Грахово: околу 1.500 загинати и други борци, 400 приклучени кон записите што веќе постојат.',
      en: 'Six books on the villages of Lika and Bosansko Grahovo: some 1,500 fallen and other fighters, 400 of them added to records already on the site.',
    },
  },
  {
    date: '2026-10-17',
    text: {
      sr: 'Druga lička brigada: 15 zapisa dobilo je nazad drugi red iz knjige, koji je izostao pri čitanju.',
      sl: 'Druga liška brigada: 15 zapisov je dobilo nazaj drugo vrstico iz knjige, ki se je pri branju izgubila.',
      mk: 'Втора личка бригада: на 15 записи им е вратен вториот ред од книгата, кој беше испуштен при читањето.',
      en: '2nd Lika Brigade: 15 entries have their second line from the book back, lost when the book was read.',
    },
  },
  {
    date: '2026-10-16',
    title: {
      sr: 'Jedan borac, jedan zapis',
      sl: 'En borec, en zapis',
      mk: 'Еден борец, еден запис',
      en: 'One fighter, one record',
    },
    text: {
      sr: 'Kad isti borac stoji u više knjiga jedne jedinice, to je sada jedan zapis, sa svim knjigama na jednom mestu. Spojeno je oko 1.700 takvih zapisa, a zapisi istog borca u dve jedinice povezani su.',
      sl: 'Če isti borec stoji v več knjigah ene enote, je zdaj to en zapis, z vsemi knjigami na enem mestu. Združenih je okoli 1.700 takih zapisov, zapisi istega borca v dveh enotah pa so povezani.',
      mk: 'Кога ист борец стои во повеќе книги на една единица, тоа сега е еден запис, со сите книги на едно место. Споени се околу 1.700 такви записи, а записите на ист борец во две единици се поврзани.',
      en: 'When one fighter appears in several books of a unit, he is now one record, with every book in one place. About 1,700 such records have been joined, and a fighter’s records in two units are linked.',
    },
  },
  {
    date: '2026-10-16',
    title: {
      sr: 'Starešine jedinica',
      sl: 'Starešine enot',
      mk: 'Старешини на единиците',
      en: 'The units’ officers',
    },
    text: {
      sr: 'Spiskovi komandanata, komesara i drugih starešina dvadesetak jedinica, sa vremenom kad su bili na dužnosti, iz knjiga tih jedinica. Većina je pridružena zapisima koji već postoje.',
      sl: 'Seznami komandantov, komisarjev in drugih starešin dvajsetih enot, s časom, ko so bili na dolžnosti, iz knjig teh enot. Večina je pridružena zapisom, ki že obstajajo.',
      mk: 'Списоци на команданти, комесари и други старешини на дваесетина единици, со времето кога биле на должност, од книгите на тие единици. Повеќето се приклучени кон записите што веќе постојат.',
      en: 'Lists of the commanders, commissars and other officers of some twenty units, with the time each held his post, from the units’ own books. Most have been added to records already on the site.',
    },
  },
  {
    date: '2026-10-16',
    text: {
      sr: 'Prva proleterska brigada: dopunski spisak i bataljon „Garibaldi“ iz četvrte knjige. 3. krajiška brigada: spisak boraca iz novembra 1942.',
      sl: 'Prva proletarska brigada: dopolnilni seznam in bataljon »Garibaldi« iz četrte knjige. 3. krajiška brigada: seznam borcev iz novembra 1942.',
      mk: 'Прва пролетерска бригада: дополнителниот список и баталјонот „Гарибалди“ од четвртата книга. 3. краишка бригада: список на борците од ноември 1942.',
      en: '1st Proletarian Brigade: the supplementary list and the Garibaldi battalion from the fourth book. 3rd Krajina Brigade: its list of fighters of November 1942.',
    },
  },
  {
    date: '2026-10-16',
    text: {
      sr: 'Oko 300 imena koja je skeniranje iseklo ili spojilo pročitano je ponovo sa strana knjiga.',
      sl: 'Okoli 300 imen, ki jih je skeniranje razsekalo ali zlepilo, je prebranih znova s strani knjig.',
      mk: 'Околу 300 имиња што скенирањето ги исекло или споило се прочитани повторно од страниците на книгите.',
      en: 'About 300 names the scanning had cut up or run together were read again from the books’ pages.',
    },
  },
  {
    date: '2026-10-15',
    text: {
      sr: 'Mesta rođenja i pogibije bez reči koje su im se pridružile pri čitanju, u oko 1.200 zapisa.',
      sl: 'Kraji rojstva in smrti brez besed, ki so se jim pridružile pri branju, v okoli 1.200 zapisih.',
      mk: 'Местата на раѓање и загинување без зборовите што им се придружиле при читањето, во околу 1.200 записи.',
      en: 'Places of birth and death cleared of words that had stuck to them in reading, in about 1,200 records.',
    },
  },
  {
    date: '2026-10-14',
    title: {
      sr: 'Trideset novih jedinica',
      sl: 'Trideset novih enot',
      mk: 'Триесет нови единици',
      en: 'Thirty new units',
    },
    text: {
      sr: 'Među njima 18. srpska brigada, prekomorske brigade, eskadrile NOVJ, Kokrški odred i Cankarjev bataljon iz Dražgoša. Uz njih oko 900 novih fotografija boraca.',
      sl: 'Med njimi 18. srbska brigada, prekomorske brigade, eskadrilji NOVJ, Kokrški odred in Cankarjev bataljon iz Dražgoš. Z njimi okoli 900 novih fotografij borcev.',
      mk: 'Меѓу нив 18. српска бригада, прекуморските бригади, ескадрилите на НОВЈ, Кокршкиот одред и Канкаревиот баталјон од Дражгоше. Со нив и околу 900 нови фотографии на борци.',
      en: 'Among them the 18th Serbian Brigade, the overseas brigades, the NOVJ squadrons, the Kokra Detachment and the Cankar Battalion of Dražgoše. With them about 900 new photographs of fighters.',
    },
  },
]

/** An item's text in the page's language (the Cyrillic made from the Latin) */
export function newsText(text: Text, lang: Lang): string {
  return lang === 'sr-cyrl' ? toCyrillic(text.sr) : text[lang]
}
