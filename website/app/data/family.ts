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
    text: 'Znamo da je bio komesar i da je poginuo negde na Žumberku. Spasio je od streljanja svog sestrića Manojla Manu Kosanovića, koji je poginuo na Ilirskoj Bistrici goneći ustaše.',
    from: 'B. Batalo, praunuk',
    date: '2026-11',
  },
]

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
