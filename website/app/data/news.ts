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
      sr: 'Očevo ime sada stoji u osnovnom obliku i kod još oko 7.900 boraca: „Miloša“ je Miloš.',
      sl: 'Očetovo ime je zdaj v osnovni obliki še pri okoli 7.900 borcih: »Miloša« je Miloš.',
      mk: 'Името на таткото сега е во основна форма и кај уште околу 7.900 борци: „Miloša“ е Miloš.',
      en: 'The father’s name is now in its plain form for about 7,900 more fighters: “Miloša” (Miloš’s) is Miloš.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Mesta rođenja i pogibije: „Užicu“ je sada Užice, a u „Saborci i zemljaci“ borci iz istog sela su zajedno i kad knjige različito pišu selo.',
      sl: 'Kraji rojstva in smrti: »Užicu« je zdaj Užice, v »Soborci in rojaki« pa so borci iz iste vasi skupaj, tudi ko knjige vas pišejo različno.',
      mk: 'Места на раѓање и загинување: „Užicu“ сега е Užice, а во „Соборци и земјаци“ борците од исто село се заедно и кога книгите различно го пишуваат селото.',
      en: 'Places of birth and death: “Užicu” is now Užice, and in “Comrades and neighbours” fighters from one village stay together however the books spell it.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Ispravljeno je oko 8.000 mesta rođenja u kojima je pisalo nešto drugo, na primer dužnost ili jedinica.',
      sl: 'Popravljenih je okoli 8.000 krajev rojstva, kjer je pisalo kaj drugega, na primer dolžnost ali enota.',
      mk: 'Поправени се околу 8.000 места на раѓање каде што пишувало нешто друго, на пример должност или единица.',
      en: 'About 8,000 birthplaces that held something else, such as a duty or a unit, have been corrected.',
    },
  },
  {
    date: '2026-10-21',
    text: {
      sr: 'Borci iz sedam knjiga o selima: Han Pijesak, Skakavac, Žitorađe, Brod kod Crne Trave, Grahovo kod Nikšića, Kolašin i Božiće.',
      sl: 'Borci iz sedmih knjig o vaseh: Han Pijesak, Skakavac, Žitorađe, Brod pri Crni Travi, Grahovo pri Nikšiću, Kolašin in Božiće.',
      mk: 'Борците од седум книги за селата: Хан Пијесак, Скакавац, Житорађе, Брод кај Црна Трава, Грахово кај Никшиќ, Колашин и Божиќе.',
      en: 'Fighters from seven books on villages: Han Pijesak, Skakavac, Žitorađe, Brod near Crna Trava, Grahovo near Nikšić, Kolašin and Božiće.',
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
      sr: 'Četiri spiska bila su samo skenirane slike, bez teksta. Sada su pročitani: ceo spisak 1. bokeljske brigade, pali borci Nikšićkog i Lovćenskog odreda i borci iz opštine Teslić.',
      sl: 'Štirje seznami so bili le skenirane slike brez besedila. Zdaj so prebrani: celoten seznam 1. bokeljske brigade, padli borci Nikšićkega in Lovćenskega odreda ter borci iz občine Teslić.',
      mk: 'Четири списоци беа само скенирани слики, без текст. Сега се прочитани: целиот список на 1-ва бокељска бригада, загинатите борци на Никшиќкиот и Ловќенскиот одред и борците од општината Теслиќ.',
      en: 'Four lists were only scanned images, with no text. They have now been read: the 1st Boka Brigade’s whole roll, the fallen of the Nikšić and Lovćen detachments, and the fighters from the Teslić municipality.',
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
      sr: 'Borac koga jedinica ima u dve ili tri knjige sada ima jedan zapis, a u njemu sve te knjige. Ako je bio u dve jedinice, zapisi su povezani.',
      sl: 'Borec, ki ga enota navaja v dveh ali treh knjigah, ima zdaj en zapis z vsemi temi knjigami. Če je bil v dveh enotah, sta zapisa povezana.',
      mk: 'Борец што единицата го има во две или три книги сега има еден запис, со сите тие книги. Ако бил во две единици, записите се поврзани.',
      en: 'A fighter whose unit lists him in two or three books now has one record, with all those books in it. If he served in two units, the records are linked.',
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
      sr: 'Komandanti, komesari i druge starešine dvadesetak jedinica, iz knjiga tih jedinica, sa datumima kad su bili na dužnosti.',
      sl: 'Komandanti, komisarji in druge starešine dvajsetih enot, iz knjig teh enot, z datumi, ko so bili na dolžnosti.',
      mk: 'Командантите, комесарите и другите старешини на дваесетина единици, од книгите на тие единици, со датумите кога биле на должност.',
      en: 'The commanders, commissars and other officers of some twenty units, from the units’ own books, with the dates they held each post.',
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
