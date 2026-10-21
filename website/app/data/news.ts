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
    date: '2026-10-21',
    text: {
      sr: 'Sedam knjiga o selima i krajevima iz Digitalne biblioteke Porekla: Han Pijesak, Skakavac kod Petrovca, Žitorađe, Brod kod Crne Trave, Grahovo kod Nikšića, Kolašin i Božiće, oko 1.450 boraca i aktivista; 288 zapisa iz njih dodato je zapisima koji već postoje.',
      sl: 'Sedem knjig o vaseh in krajih iz digitalne knjižnice Poreklo: Han Pijesak, Skakavac pri Petrovcu, Žitorađe, Brod pri Crni Travi, Grahovo pri Nikšiću, Kolašin in Božiće, okoli 1.450 borcev in aktivistov; 288 zapisov iz njih je dodanih zapisom, ki že obstajajo.',
      mk: 'Седум книги за селата и краиштата од дигиталната библиотека на Порекло: Хан Пијесак, Скакавац кај Петровац, Житорађе, Брод кај Црна Трава, Грахово кај Никшиќ, Колашин и Божиќе, околу 1.450 борци и активисти; 288 записи од нив се додадени на записите што веќе постојат.',
      en: 'Seven books on villages and districts from the Poreklo digital library: Han Pijesak, Skakavac near Petrovac, Žitorađe, Brod near Crna Trava, Grahovo near Nikšić, Kolašin and Božiće, some 1,450 fighters and activists; 288 of their entries have been added to records already on the site.',
    },
  },
  {
    date: '2026-10-20',
    text: {
      sr: 'Stari Majdan: uneti su pali borci ostalih sela i spiskovi boraca i učesnika rata iz 1983. godine i nosilaca Partizanske spomenice 1941, oko 1.200 imena; borci i učesnici iz spiskova označeni su kao učesnici. Iz tri druga spiska uneti su i aktivisti NOP-a koji su stradali van vojske, njih 82.',
      sl: 'Stari Majdan: vneseni so padli borci ostalih vasi ter seznami borcev in udeležencev vojne iz leta 1983 in nosilcev Partizanske spomenice 1941, okoli 1.200 imen; borci in udeleženci s seznamov so označeni kot udeleženci. Iz treh drugih seznamov so vneseni tudi aktivisti NOG, ki so umrli zunaj vojske, 82 jih je.',
      mk: 'Стари Мајдан: внесени се загинатите борци од другите села и списоците на борците и учесниците во војната од 1983 година и на носителите на Партизанската споменица 1941, околу 1.200 имиња; борците и учесниците од списоците се означени како учесници. Од три други списоци внесени се и активистите на НОД што загинале надвор од војската, 82.',
      en: 'Stari Majdan: the fallen of its other villages are in, with the 1983 lists of the war’s fighters and participants and of the holders of the 1941 Partisan Commemorative Medal, some 1,200 names; those of the lists are marked as participants. Three other lists now include the movement’s activists who died outside the army, 82 of them.',
    },
  },
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
      sr: 'Iz jedanaest spiskova koji zajedno navode borce i ostale učesnike pokreta uneti su i aktivisti NOP-a, oko 7.200 članova KPJ i SKOJ-a, odbornika i terenskih radnika, označeni kao aktivisti.',
      sl: 'Iz enajstih seznamov, ki skupaj navajajo borce in druge udeležence gibanja, so vneseni tudi aktivisti NOG, okoli 7.200 članov KPJ in SKOJ, odbornikov in terenskih delavcev, označeni kot aktivisti.',
      mk: 'Од единаесет списоци што заедно ги наведуваат борците и другите учесници во движењето внесени се и активистите на НОД, околу 7.200 членови на КПЈ и СКОЈ, одборници и теренски работници, означени како активисти.',
      en: 'From eleven lists that name fighters together with others in the movement, its activists are now in too, some 7,200 party and youth league members, committee members and field workers, marked as activists.',
    },
  },
  {
    date: '2026-10-19',
    text: {
      sr: 'Osam knjiga o selima Like, Otočca i Brinja, Bosanskog Grahova i Starog Majdana: oko 5.800 palih i preživelih boraca i aktivista, 710 pridruženo zapisima koji već postoje.',
      sl: 'Osem knjig o vaseh Like, Otočca in Brinja, Bosanskega Grahova in Starega Majdana: okoli 5.800 padlih in preživelih borcev ter aktivistov, 710 pridruženih zapisom, ki že obstajajo.',
      mk: 'Осум книги за селата во Лика, Оточац и Бриње, Босанско Грахово и Стари Мајдан: околу 5.800 загинати и преживеани борци и активисти, 710 приклучени кон записите што веќе постојат.',
      en: 'Eight books on the villages of Lika, Otočac and Brinje, Bosansko Grahovo and Stari Majdan: some 5,800 fallen and surviving fighters and activists, 710 of them added to records already on the site.',
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
