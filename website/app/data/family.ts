// Photos, documents and stories that families sent through "Znam ovog borca" and that were checked and approved
// for publishing (the sender gave permission). How to add one: docs/FAMILY_CONTRIBUTIONS.md

/** A photograph or a document a family sent, beside the one `photo` (components/FamilyStory.tsx shows them as an album) */
export interface FamilyPiece {
  kind: 'photo' | 'document'
  file: string           // file in website/public/porodica/: the photo, or a document's first page
  pages?: string[]       // a document's other pages, in order
  caption?: string       // what it is, in the sender's words: 'Vojna knjižica', 'Sa saborcima, 1944.'
  transcripts?: string[] // what each page says, page by page, where it is written by hand or hard to read
}

export interface FamilyContribution {
  soldierId: string     // the record it belongs to
  photo?: string        // file in website/public/porodica/, e.g. '0002000003-1.jpg'
  photoCaption?: string // what the photo shows and when, in the sender's words
  text?: string         // the story, as sent (lightly edited for spelling only)
  pieces?: FamilyPiece[] // more photos and documents from the same sender
  from: string          // credit line, e.g. 'Ana Petrović, unuka'
  date: string          // when it was sent, 'YYYY-MM'
  origin?: 'facebook'   // not from the family but from a public Facebook page: the heading says so, `from` names the page
}

export const familyContributions: FamilyContribution[] = [
  {
    soldierId: '0002000242', // Bakić Maksimov Mile, Prva lička
    photo: '0002000242-1.jpg',
    // the user's family archive (their MyHeritage tree, 2026-11-19): photos of him alone and the papers of his decoration;
    // the family photos with other people wait for the user's word on which may be shown
    pieces: [
      { kind: 'photo', file: '0002000242-2.jpg', caption: 'U uniformi' },
      { kind: 'photo', file: '0002000242-3.jpg', caption: 'U oficirskoj uniformi' },
      { kind: 'photo', file: '0002000242-4.jpg' },
      { kind: 'photo', file: '0002000242-5.jpg' },
      { kind: 'photo', file: '0002000242-6.jpg', caption: 'U kasnijim godinama' },
      {
        kind: 'document',
        file: '0002000242-7.jpg',
        caption: 'Povelja o odlikovanju Ordenom republike sa srebrnim vencem, 1984.',
        transcripts: ['Ukazom Predsedništva Socijalističke Federativne Republike Jugoslavije broj 90 od 17. oktobra 1984. godine, za naročite zasluge na polju javne delatnosti kojom se doprinosi opštem napretku zemlje, odlikovan je Mile M. Bakić Ordenom republike sa srebrnim vencem, o čemu se izdaje ova povelja. Kancelarija ordena, u Beogradu 17. oktobra 1984. godine. Šef Kancelarije ordena, [potpis]'],
      },
      {
        kind: 'document',
        file: '0002000242-8.jpg',
        caption: 'Iz novina: odlikovani Ordenom republike sa srebrnim vijencem',
        transcripts: ['Ordenom republike sa srebrnim vijencem: Bakić Maksima Mile, Popov Branka Dejan, Prijić Milana Radivoj; za osobite zasluge i uspjehe postignute u radu značajnom za socijalističku izgradnju zemlje'],
      },
    ],
    from: 'iz porodične arhive',
    date: '2026-10',
  },
  {
    soldierId: '0122959019', // Bajić Stevan Todor "Soko", Beška (Porodična arhiva)
    photo: '0122959019-1.jpg',
    photoCaption: 'Fotografija iz vojne knjižice',
    from: 'iz porodične arhive',
    date: '2026-10',
  },
  {
    soldierId: '0126000703', // Novaković Vuka Radomir, Čačanski NOP odred
    photo: '0126000703-1.jpg',
    text: 'Njegova slika nalazi se u Spomen-muzeju prve partizanske bolnice u rodnom selu u Donjoj Gorevnici kod Čačka. Njegovo ime upisano je na spomen-ploči na Zadružnom domu u Donjoj Gorevnici.',
    from: 'F. Adžić, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0136006734', // Todosijević Dragić Jelica (Borci drugih jedinica – Srbija)
    text: 'Ne znamo gde je sahranjena. Ne znamo za sigurno ni gde je poginula. Neki kažu da su je ubili četnici 1942.',
    from: 'J. Todosijević, bratanica',
    date: '2026-11',
  },
  {
    soldierId: '0136021032', // Đoković Miodrag Dragan (Borci drugih jedinica – Srbija)
    photo: '0136021032-1.jpg',
    photoCaption: 'Spomen-bista ispred škole u Lađevcima',
    text: 'Pre rata, radio je kao učitelj (pre toga i izuzetan učenik) u rodnom mestu nakon čega je dobio nadimak „Uča” (negde napisano i kao „Učo”). Posle rata, njegovo ime sve do danas nosi Osnovna škola u Lađevcima kod Kraljeva. Tokom rata, bio je borac Kraljevačkog NOP odreda. Ispred škole, od 1976. godine nalazi se spomen-bista Dragana Đokovića, rad autora Ace Mitrovića. Bistu su podigli braća i majka Dragana Đokovića.',
    from: 'F. Adžić',
    date: '2026-11',
  },
  {
    soldierId: '0036100540', // Karamatić Joze Ivo "Čović" of Plina Istočna (Ploče), 1. dalmatinska; the user sent the photos
    photo: '0036100540-1.jpg', // a boy in a partisan cap with a rifle, cut from a group photo, tinted
    pieces: [{ kind: 'photo', file: '0036100540-2.jpg', caption: 'U kasnijim godinama' }], // in a partisan cap, with his decorations
    // the photos' source, as the user gave it; under the heading "Sa Facebook stranice" (the user, 2026-11-19)
    from: '„Bitka na Sutjesci”',
    origin: 'facebook',
    date: '2026-11',
  },
  {
    soldierId: '0135000797', // Piperov Nikola Vlado (Borci drugih jedinica – Makedonija)
    text: 'Ispravka godine rođenja: na njegovoj spomen-bisti u selu Stojakovo uklesana je 1919. Popis iz 1964. navodi 1920.',
    from: 'Ispravka po prijavi',
    date: '2026-11',
  },
  {
    soldierId: '0122917644', // Kovačević Pajov Dušan of Osječenica (Nikšić), Borci drugih jedinica
    text: 'Rođen 1923. u Osječenici kod Nikšića, a poginuo pri proboju Sremskog fronta, početkom aprila 1945. godine.',
    from: 'nećak',
    date: '2026-11',
  },
  {
    soldierId: '0122907839', // Sekulić Mane Miloš of Zbjeg (Slunj), Borci drugih jedinica
    photo: '0122907839-1.jpg',
    text: 'Ime mu se u izvorima razlikuje: knjige ga upisuju i kao Miloša, sina Manina, i kao Manu, sina Milošev. Znamo da je bio komesar i da je poginuo negde na Žumberku. Spasio je od streljanja svog sestrića Manojla Manu Kosanovića, koji je poginuo na Ilirskoj Bistrici goneći ustaše.',
    from: 'B. Batalo, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0060000921', // Kosanović Milovana Mane (Manojlo), Zbjeg: the nephew Miloš Sekulić saved from a firing squad
    text: 'Porodica ga navodi kao Manojla Manu Kosanovića. Njegov ujak Miloš Sekulić, komesar bataljona, spasio ga je od streljanja. Poginuo je kod Ilirske Bistrice, goneći ustaše.',
    from: 'B. Batalo, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0042000145', // Gaković Gojka Milorad, Banjani; the same man as Gaković Milorad 0013020151 of the 6. krajiška (linked)
    photo: '0042000145-1.jpg',
    text: 'Rođen u Banjanima kod Bosanskog Broda. Pre rata trgovac, povezan sa KPJ, ali nije bio aktivan član. Učesnik NOB-a od 1941. Prebacio je brojnu porodicu u Vojvodinu pre pokolja, pa se vratio u selo. Tifusar na Neretvi, ranjen na Sutjesci. U sastavu Šeste krajiške, a zatim 7. istočnobosanske muslimanske divizije. U memoarima saboraca pominje se pod nadimkom „Crni”. Predvodio je akciju zauzimanja i uništenja rudnika Ljubija 1943.',
    from: 'B. Obradović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122959607', // Krnić Ive Blaž of Konjevrate (Šibenik), survived; his photo in uniform is his portrait (the user's choice, 2026-11-19)
    photo: '9990000003-1.jpg',
    photoCaption: 'U uniformi',
    text: 'Prošao je bitke na Neretvi i Sutjesci, a učestvovao je i u borbama za oslobođenje Knina i Šibenika.',
    from: '', // the grandson's later form (14:21) did not allow his name
    date: '2026-11',
  },
  {
    soldierId: '0122957805', // Kupres Marka Miloš of Kožuhe (Doboj), narodni heroj, Borci drugih jedinica
    text: 'U čast ovog narodnog heroja Kulturno-umjetničko društvo u Kožuhama nosi ime po njemu.',
    from: 'N. Kaišarević',
    date: '2026-11',
  },
  {
    soldierId: '0122959606', // Eftimovski Gjore of Sušica (Gostivar), brother of Kiro (Porodična arhiva)
    text: 'Роден е 1925 година во село Сушица. Потекнува од многучлено сиромашно семејство. Уште како дете оди на печалба во Белград како општ работник, каде што се запознава со идеите на напредното работничко движење. За време на окупацијата на земјата во Белград е примен за член на СКОЈ, а нешто подоцна и за член на КПЈ. Кон крајот на 1941 година е уапсен од страна на Недиќевата полиција, но заради немање докази набрзо е пуштен на слобода. Особена активност и бестрашност покажува во вршењето на многу одговорни курирски задачи. Во единиците на Народноослободителната војска стапил доброволно во јуни 1943 година, како борец во составот на Космајскиот народноослободителен одред. Во една акција во 1944 година во Белград е заробен од германскиот фашистички окупатор и нешто подоцна стрелан во Бањица. За него постои спомен-обележје на гробиштата на ослободителите на Белград.',
    from: 'nećak',
    date: '2026-11',
  },
  {
    soldierId: '0135001012', // Eftimovski Božo Kiro of Sušica (Gostivar), census part Makedonija
    text: 'Роден е 1923 година во село Сушица. Потекнува од многучлено сиромашно семејство. Уште како дете останал сирак без татко, па бил присилен да оди на печалба во Белград, каде што работи како општ работник. Во слободните мигови постојано е во друштво со напредни работници и младинци, што му дава можност да се запознае со идеите на напредното работничко движење. Во Белград останал до капитулацијата на стара Југославија. Веднаш по капитулацијата се враќа во своето родно место, се приклучува во напредното движење и станал член на Месниот народноослободителен одбор. Бил член и на партискиот актив на селото. Во единиците на Народноослободителната војска стапил доброволно во мај 1944 година, како борец во составот на Првата македонско-косовска бригада. Со својата единица учествувал во сите борби и акции. Загинал на 28 август 1944 година во борбите за ослободување на Кичево. Неговиот брат Ѓоре (роден 1925 година, исто така од Сушица) во јуни 1943 година стапил во Космајскиот народноослободителен одред. Во една акција во 1944 година во Белград е заробен од германскиот окупатор и подоцна стрелан во Бањица. За него постои спомен-обележје на гробиштата на ослободителите на Белград.',
    from: 'nećak',
    date: '2026-11',
  },
]

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
