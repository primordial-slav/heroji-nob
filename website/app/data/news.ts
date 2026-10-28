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
    date: '2026-10-28',
    text: {
      sr: 'Uneto je šesnaest novih knjiga, uglavnom o selima i opštinama: oko 4.200 boraca, aktivista i nosilaca Partizanske spomenice 1941. Oko 600 boraca koji su već bili na sajtu sada ima još jednu knjigu koja piše o njima, a ostali su novi, među Ostalim borcima.',
      sl: 'Vnesenih je šestnajst novih knjig, večinoma o vaseh in občinah: okoli 4.200 borcev, aktivistov in nosilcev Partizanske spomenice 1941. Okoli 600 borcev, ki so že bili na strani, ima zdaj še eno knjigo, ki piše o njih, ostali so novi, med Drugimi borci.',
      mk: 'Внесени се шеснаесет нови книги, главно за селата и општините: околу 4.200 борци, активисти и носители на Партизанската споменица 1941. Околу 600 борци што веќе беа на сајтот сега имаат уште една книга што пишува за нив, а останатите се нови, меѓу Другите борци.',
      en: 'Sixteen new books are in, most of them on villages and municipalities: some 4,200 fighters, activists and holders of the 1941 Partisan Commemorative Medal. About 600 fighters already on the site now have one more book that writes about them; the rest are new, among the Other fighters.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Ime oca je sada u nominativu i kod oko 7.900 boraca kod kojih je ostalo onako kako je štampano u knjizi, najviše iz Mosorskog odreda, IV pomorskog obalnog sektora, 1. krajiške, Čačanskog odreda, 15. majevičke i 1. bokeljske: „Miloša“ je Miloš, „Jove“ Jovo. Gde popis iz 1964. daje oca istog čoveka, uzeto je njegovo ime. Po imenu oca sada ih nalazi i pretraga.',
      sl: 'Ime očeta je zdaj v imenovalniku tudi pri okoli 7.900 borcih, pri katerih je ostalo tako, kot je natisnjeno v knjigi, največ iz Mosorskega odreda, IV. pomorskega obalnega sektorja, 1. krajiške, Čačanskega odreda, 15. majeviške in 1. bokeljske: »Miloša« je Miloš, »Jove« Jovo. Kjer popis iz leta 1964 daje očeta istega človeka, je vzeto njegovo ime. Po imenu očeta jih zdaj najde tudi iskanje.',
      mk: 'Името на таткото сега е во основна форма и кај околу 7.900 борци кај кои остана онака како што е отпечатено во книгата, најмногу од Мосорскиот одред, IV поморски крајбрежен сектор, 1-ва краишка, Чачанскиот одред, 15-та мајевичка и 1-ва бокељска: „Miloša“ е Miloš, „Jove“ Jovo. Каде што пописот од 1964 година го дава таткото на истиот човек, земено е неговото име. Според името на таткото сега ги наоѓа и пребарувањето.',
      en: 'The father’s name is now in its base form for some 7,900 more fighters, where it had stayed as the book prints it, most of them of the Mosor detachment, the IV naval coastal sector, the 1st Krajina, the Čačak detachment, the 15th Majevica and the 1st Boka: “Miloša” is Miloš, “Jove” Jovo. Where the 1964 census gives the same man’s father, his name was taken. Search now finds them by the father’s name too.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Mesta rođenja i pogibije prepoznata su po bazi geografskih imena GeoNames: oko 8.400 mesta koja su bila u padežu sada stoje u nominativu („Užicu“ je Užice), a u stablu „Saborci i zemljaci“ borci iz istog sela su zajedno kako god ga knjige pisale, dok dva sela istog imena više nisu jedno. Tako je sa svojim zemljacima povezano još oko 15.000 boraca.',
      sl: 'Kraji rojstva in smrti so prepoznani po zbirki zemljepisnih imen GeoNames: okoli 8.400 krajev, ki so bili v sklonu, je zdaj v imenovalniku (»Užicu« je Užice), v drevesu »Soborci in rojaki« pa so borci iz iste vasi skupaj, kakor koli jo pišejo knjige, dve vasi z istim imenom pa nista več ena. Tako je s svojimi rojaki povezanih še okoli 15.000 borcev.',
      mk: 'Местата на раѓање и загинување се препознаени според базата на географски имиња GeoNames: околу 8.400 места што беа во падеж сега стојат во основна форма („Užicu“ е Užice), а во стеблото „Соборци и земјаци“ борците од исто село се заедно, како и да го пишуваат книгите, додека две села со исто име веќе не се едно. Така со своите земјаци се поврзани уште околу 15.000 борци.',
      en: 'Places of birth and death are now identified with the GeoNames geographical database: some 8,400 places printed in a grammatical case are given in their base form (“Užicu” is Užice), and the “Comrades and neighbours” tree keeps the fighters of one village together however the books spell it, while two villages of one name are no longer one. Some 15,000 more fighters are now linked with their neighbours.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Ispravljeno je oko 8.000 mesta rođenja u koja je ušlo nešto drugo: dužnost, jedinica ili republika („Borac brigade“, „Krasica, Bakar, SR Hrvatska“); poginuli iz Beograda u popisu iz 1964. sada su rođeni u Beogradu, a ne u njegovim opštinama.',
      sl: 'Popravljenih je okoli 8.000 krajev rojstva, v katere je zašlo kaj drugega: dolžnost, enota ali republika („Borac brigade“, „Krasica, Bakar, SR Hrvatska“); padli iz Beograda v popisu iz leta 1964 so zdaj rojeni v Beogradu, ne v njegovih občinah.',
      mk: 'Поправени се околу 8.000 места на раѓање во кои влегло нешто друго: должност, единица или република („Borac brigade“, „Krasica, Bakar, SR Hrvatska“); загинатите од Белград во пописот од 1964 година сега се родени во Белград, а не во неговите општини.',
      en: 'About 8,000 birthplaces that held something else, a duty, a unit or a republic (“Borac brigade”, “Krasica, Bakar, SR Hrvatska”), have been put right; the 1964 census’s fallen from Belgrade are now born in Belgrade, not in its municipalities.',
    },
  },
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
