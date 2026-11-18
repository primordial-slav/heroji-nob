// Photos and stories that families sent through "Znam ovog borca" and that were checked and approved
// for publishing (the sender gave permission). How to add one: docs/FAMILY_CONTRIBUTIONS.md

export interface FamilyContribution {
  soldierId: string     // the record it belongs to
  photo?: string        // file in website/public/porodica/, e.g. '0002000003-1.jpg'
  photoCaption?: string // what the photo shows and when, in the sender's words
  text?: string         // the story, as sent (lightly edited for spelling only)
  from: string          // credit line, e.g. 'Ana Petrović, unuka'
  date: string          // when it was sent, 'YYYY-MM'
}

export const familyContributions: FamilyContribution[] = [
  {
    soldierId: '0002000242', // Bakić Maksimov Mile, Prva lička
    photo: '0002000242-1.jpg',
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
    text: 'Pre rata radio je kao učitelj (pre toga i izuzetan učenik) u rodnom mestu, nakon čega je dobio nadimak „Uča” (negde napisano i kao „Učo”). Posle rata njegovo ime sve do danas nosi Osnovna škola u Lađevcima kod Kraljeva. Tokom rata bio je borac Kraljevačkog NOP odreda. Ispred škole, od 1976. godine, nalazi se spomen-bista Dragana Đokovića, rad autora Ace Mitrovića. Bistu su podigli braća i majka Dragana Đokovića.',
    from: 'F. Adžić',
    date: '2026-11',
  },
]

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
