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
      sr: 'Dodali smo šesnaest novih knjiga, uglavnom o selima i opštinama, sa oko 4.200 boraca, aktivista i nosilaca Partizanske spomenice 1941. Oko 600 njih već je bilo na sajtu, pa sada u njihovom zapisu stoji još jedna knjiga. Ostali su novi i nalaze se među Ostalim borcima.',
      sl: 'Dodali smo šestnajst novih knjig, večinoma o vaseh in občinah, z okoli 4.200 borci, aktivisti in nosilci Partizanske spomenice 1941. Okoli 600 jih je že bilo na strani, zato je zdaj v njihovem zapisu še ena knjiga. Drugi so novi in so med Drugimi borci.',
      mk: 'Додадовме шеснаесет нови книги, главно за селата и општините, со околу 4.200 борци, активисти и носители на Партизанската споменица 1941. Околу 600 од нив веќе беа на сајтот, па сега во нивниот запис стои уште една книга. Другите се нови и се наоѓаат меѓу Другите борци.',
      en: 'We have added sixteen new books, most of them on villages and municipalities, with some 4,200 fighters, activists and holders of the 1941 Partisan Commemorative Medal. About 600 of them were already on the site, so their records now show one more book. The rest are new and are listed under Other fighters.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Kod još oko 7.900 boraca ime oca više nije u padežu: umesto „Miloša“ sada piše Miloš.',
      sl: 'Pri še okoli 7.900 borcih očetovo ime ni več v sklonu: namesto »Miloša« zdaj piše Miloš.',
      mk: 'Кај уште околу 7.900 борци името на таткото веќе не е во падеж: наместо „Miloša“ сега пишува Miloš.',
      en: 'For about 7,900 more fighters the father’s name is no longer in a grammatical case: instead of “Miloša” (Miloš’s) it now says Miloš.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Mesta rođenja i pogibije više nisu u padežu: umesto „Užicu“ sada piše Užice. U „Saborci i zemljaci“ borci iz istog sela sada su zajedno, i kad knjige različito pišu ime sela.',
      sl: 'Kraji rojstva in smrti niso več v sklonu: namesto »Užicu« zdaj piše Užice. V »Soborci in rojaki« so borci iz iste vasi zdaj skupaj, tudi ko knjige ime vasi pišejo različno.',
      mk: 'Местата на раѓање и загинување веќе не се во падеж: наместо „Užicu“ сега пишува Užice. Во „Соборци и земјаци“ борците од исто село сега се заедно, и кога книгите различно го пишуваат името на селото.',
      en: 'Places of birth and death are no longer in a grammatical case: “Užicu” now reads Užice. In “Comrades and neighbours” fighters from one village are now together, even where the books spell the village differently.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Kod oko 8.000 boraca u mestu rođenja pisalo je nešto drugo, na primer dužnost ili jedinica. To je sada ispravljeno.',
      sl: 'Pri okoli 8.000 borcih je v kraju rojstva pisalo kaj drugega, na primer dolžnost ali enota. To je zdaj popravljeno.',
      mk: 'Кај околу 8.000 борци во местото на раѓање пишуваше нешто друго, на пример должност или единица. Тоа сега е поправено.',
      en: 'For about 8,000 fighters the place of birth held something else, such as a duty or a unit. That is now corrected.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Dodali smo borce iz sedam knjiga o selima i krajevima: Han Pijesak, Skakavac, Žitorađe, Brod kod Crne Trave, Grahovo kod Nikšića, Kolašin i Božiće.',
      sl: 'Dodali smo borce iz sedmih knjig o vaseh in krajih: Han Pijesak, Skakavac, Žitorađe, Brod pri Crni Travi, Grahovo pri Nikšiću, Kolašin in Božiće.',
      mk: 'Додадовме борци од седум книги за села и краишта: Хан Пијесак, Скакавац, Житорађе, Брод кај Црна Трава, Грахово кај Никшиќ, Колашин и Божиќе.',
      en: 'We have added the fighters from seven books on villages and districts: Han Pijesak, Skakavac, Žitorađe, Brod near Crna Trava, Grahovo near Nikšić, Kolašin and Božiće.',
    },
  },
  {
    date: '2026-10-20',
    text: {
      sr: 'Stari Majdan: dodali smo pale borce iz ostalih sela, nosioce Partizanske spomenice 1941 i spiskove boraca i učesnika rata iz 1983. godine, ukupno oko 1.200 imena. Spiskovi iz 1983. ne kažu ko je bio borac, a ko je pomagao pokretu, pa su ti ljudi označeni kao učesnici. Iz tri druga spiska dodali smo i 82 aktivista NOP-a koji su izgubili život van vojske.',
      sl: 'Stari Majdan: dodali smo padle borce iz drugih vasi, nosilce Partizanske spomenice 1941 ter sezname borcev in udeležencev vojne iz leta 1983, skupaj okoli 1.200 imen. Seznami iz leta 1983 ne povedo, kdo je bil borec in kdo je pomagal gibanju, zato so ti ljudje označeni kot udeleženci. Iz treh drugih seznamov smo dodali še 82 aktivistov NOG, ki so izgubili življenje zunaj vojske.',
      mk: 'Стари Мајдан: ги додадовме загинатите борци од другите села, носителите на Партизанската споменица 1941 и списоците на борците и учесниците во војната од 1983 година, вкупно околу 1.200 имиња. Списоците од 1983 година не кажуваат кој бил борец, а кој му помагал на движењето, па овие луѓе се означени како учесници. Од три други списоци ги додадовме и 82 активисти на НОД што го загубиле животот надвор од војската.',
      en: 'Stari Majdan: we have added the fallen of its other villages, the holders of the 1941 Partisan Commemorative Medal and the 1983 lists of the war’s fighters and participants, some 1,200 names in all. The 1983 lists don’t say who fought and who helped the movement, so those people are marked as participants. From three other lists we have also added 82 of the movement’s activists who lost their lives outside the army.',
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
      sr: 'Četiri spiska imali smo samo kao skenirane slike, bez teksta. Sada smo ih pročitali: ceo spisak 1. bokeljske brigade, pale borce Nikšićkog i Lovćenskog odreda i borce iz opštine Teslić.',
      sl: 'Štiri sezname smo imeli le kot skenirane slike, brez besedila. Zdaj smo jih prebrali: celoten seznam 1. bokeljske brigade, padle borce Nikšićkega in Lovćenskega odreda ter borce iz občine Teslić.',
      mk: 'Четири списоци ги имавме само како скенирани слики, без текст. Сега ги прочитавме: целиот список на 1-ва бокељска бригада, загинатите борци на Никшиќкиот и Ловќенскиот одред и борците од општината Теслиќ.',
      en: 'We had four lists only as scanned images, with no text. Now we have read them: the 1st Boka Brigade’s whole roll, the fallen of the Nikšić and Lovćen detachments, and the fighters from the Teslić municipality.',
    },
  },
  {
    date: '2026-10-19',
    text: {
      sr: 'Neki spiskovi uz borce navode i ljude koji su pomagali pokretu van vojske. Iz jedanaest takvih spiskova dodali smo i njih, oko 7.200 članova KPJ i SKOJ-a, odbornika i terenskih radnika. Na sajtu su označeni kao aktivisti.',
      sl: 'Nekateri seznami poleg borcev navajajo tudi ljudi, ki so gibanju pomagali zunaj vojske. Iz enajstih takih seznamov smo dodali tudi njih, okoli 7.200 članov KPJ in SKOJ, odbornikov in terenskih delavcev. Na strani so označeni kot aktivisti.',
      mk: 'Некои списоци покрај борците ги наведуваат и луѓето што му помагале на движењето надвор од војската. Од единаесет такви списоци ги додадовме и нив, околу 7.200 членови на КПЈ и СКОЈ, одборници и теренски работници. На сајтот се означени како активисти.',
      en: 'Some lists name, besides the fighters, the people who helped the movement outside the army. From eleven such lists we have added them too, some 7,200 party and youth league members, committee members and field workers. On the site they are marked as activists.',
    },
  },
  {
    date: '2026-10-19',
    text: {
      sr: 'Dodali smo borce i aktiviste iz osam knjiga o selima Like, Otočca i Brinja, Bosanskog Grahova i Starog Majdana, oko 5.800 palih i preživelih. Njih 710 već je bilo na sajtu, pa sada u njihovom zapisu stoji još jedna knjiga.',
      sl: 'Dodali smo borce in aktiviste iz osmih knjig o vaseh Like, Otočca in Brinja, Bosanskega Grahova in Starega Majdana, okoli 5.800 padlih in preživelih. 710 jih je že bilo na strani, zato je zdaj v njihovem zapisu še ena knjiga.',
      mk: 'Додадовме борци и активисти од осум книги за селата во Лика, Оточац и Бриње, Босанско Грахово и Стари Мајдан, околу 5.800 загинати и преживеани. 710 од нив веќе беа на сајтот, па сега во нивниот запис стои уште една книга.',
      en: 'We have added the fighters and activists from eight books on the villages of Lika, Otočac and Brinje, Bosansko Grahovo and Stari Majdan, some 5,800 fallen and surviving. 710 of them were already on the site, so their records now show one more book.',
    },
  },
  {
    date: '2026-10-17',
    text: {
      sr: 'Druga lička brigada: u 15 zapisa nedostajao je drugi red iz knjige. Sada je vraćen.',
      sl: 'Druga liška brigada: v 15 zapisih je manjkala druga vrstica iz knjige. Zdaj je vrnjena.',
      mk: 'Втора личка бригада: во 15 записи недостасуваше вториот ред од книгата. Сега е вратен.',
      en: '2nd Lika Brigade: 15 entries were missing their second line from the book. It is back now.',
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
      sr: 'Ako se isti borac pominje u više knjiga iste jedinice, sada ima jedan zapis, a u njemu su sve te knjige. Ako je bio u dve jedinice, njegovi zapisi su povezani.',
      sl: 'Če se isti borec omenja v več knjigah iste enote, ima zdaj en zapis, v njem pa so vse te knjige. Če je bil v dveh enotah, sta njegova zapisa povezana.',
      mk: 'Ако истиот борец се спомнува во повеќе книги на иста единица, сега има еден запис, а во него се сите тие книги. Ако бил во две единици, неговите записи се поврзани.',
      en: 'If the same fighter appears in several books of one unit, he now has a single record with all those books in it. If he served in two units, his records are linked.',
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
      sr: 'Iz knjiga dvadesetak jedinica dodali smo njihove komandante, komesare i druge starešine, sa datumima kada su bili na dužnosti.',
      sl: 'Iz knjig kakih dvajsetih enot smo dodali njihove komandante, komisarje in druge starešine, z datumi, ko so bili na dolžnosti.',
      mk: 'Од книгите на дваесетина единици ги додадовме нивните команданти, комесари и други старешини, со датумите кога биле на должност.',
      en: 'From the books of some twenty units we have added their commanders, commissars and other officers, with the dates they held each post.',
    },
  },
  {
    date: '2026-10-16',
    text: {
      sr: 'Prva proleterska brigada dobila je dopunski spisak i spisak bataljona „Garibaldi“ iz četvrte knjige, a 3. krajiška brigada spisak svojih boraca iz novembra 1942.',
      sl: 'Prva proletarska brigada je dobila dopolnilni seznam in seznam bataljona »Garibaldi« iz četrte knjige, 3. krajiška brigada pa seznam svojih borcev iz novembra 1942.',
      mk: 'Прва пролетерска бригада го доби дополнителниот список и списокот на баталјонот „Гарибалди“ од четвртата книга, а 3. краишка бригада списокот на своите борци од ноември 1942.',
      en: 'The 1st Proletarian Brigade now has its supplementary list and the list of the Garibaldi battalion from the fourth book, and the 3rd Krajina Brigade its list of fighters of November 1942.',
    },
  },
  {
    date: '2026-10-16',
    text: {
      sr: 'Oko 300 imena se pri čitanju skenova raspalo na delove ili spojilo sa susednim rečima. Ponovo smo ih pročitali sa strana knjiga.',
      sl: 'Okoli 300 imen je pri branju skenov razpadlo na dele ali se zlepilo s sosednjimi besedami. Znova smo jih prebrali s strani knjig.',
      mk: 'Околу 300 имиња при читањето на скеновите се распаднаа на делови или се споија со соседните зборови. Повторно ги прочитавме од страниците на книгите.',
      en: 'About 300 names had fallen apart or run into the words next to them when the scans were read. We have read them again from the books’ pages.',
    },
  },
  {
    date: '2026-10-15',
    text: {
      sr: 'U oko 1.200 zapisa uz mesto rođenja ili pogibije pri čitanju su ostale reči koje tu ne spadaju. Sada su uklonjene.',
      sl: 'V okoli 1.200 zapisih so ob kraju rojstva ali smrti pri branju ostale besede, ki tja ne spadajo. Zdaj so odstranjene.',
      mk: 'Во околу 1.200 записи покрај местото на раѓање или загинување при читањето останале зборови што не спаѓаат таму. Сега се отстранети.',
      en: 'In about 1,200 records, words that don’t belong there had stuck to the place of birth or death in reading. They are gone now.',
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
