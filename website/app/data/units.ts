export interface Unit {
  id: string
  name: string
  nameEn: string
  description: string
  image: string
  soldierCount: number
  dataFile: string
  pdfFiles: string[]
}

export const units: Unit[] = [
  {
    id: 'prva-licka-brigada',
    name: 'Prva lička proleterska brigada "Marko Orešković"',
    nameEn: '1st Lika Proletarian Brigade "Marko Orešković"',
    description: 'Formirana juna 1942. godine',
    image: '/images/prva-licka-brigada.jpg',
    soldierCount: 9797,
    dataFile: '/soldiers.json',
    pdfFiles: ['/pdfs/prva-licka-proleterska.pdf']
  },
  {
    id: 'prva-proleterska-brigada',
    name: 'Prva proleterska narodnooslobodilačka udarna brigada',
    nameEn: '1st Proletarian People\'s Liberation Assault Brigade',
    description: 'Formirana 21. decembra 1941. godine',
    image: '/images/prva-proleterska-brigada.jpg',
    soldierCount: 14068,
    dataFile: '/prva-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/prva-proleterska-1.pdf', '/pdfs/prva-proleterska-2.pdf', '/pdfs/prva-proleterska-3.pdf']
  },
  {
    id: 'ljubljanska-brigada',
    name: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    nameEn: '10th Slovenian People\'s Liberation Assault Brigade "Ljubljana"',
    description: 'Formirana 11. septembra 1943. godine',
    image: '/images/ljubljanska-brigada.jpg',
    soldierCount: 3172,
    dataFile: '/ljubljanska-soldiers.json',
    pdfFiles: ['/pdfs/ljubljanska-brigada.pdf']
  },
  {
    id: 'druga-licka-brigada',
    name: 'Druga lička proleterska brigada',
    nameEn: '2nd Lika Proletarian Brigade',
    description: 'Formirana 1942. godine. Spisak poginulih, umrlih i nestalih boraca.',
    image: '/images/druga_licka.jpg',
    soldierCount: 1509,
    dataFile: '/druga-licka-soldiers.json',
    pdfFiles: ['/pdfs/druga-licka-spisak.pdf']
  },
  {
    id: 'treca-proleterska-brigada',
    name: 'Treća proleterska (sandžačka) brigada',
    nameEn: '3rd Proletarian (Sandžak) Brigade',
    description: 'Formirana 5. juna 1942. godine. Spisak boraca i starešina na dan formiranja brigade.',
    image: '/images/treca-proleterska-brigada.jpg',
    soldierCount: 859,
    dataFile: '/treca-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/treca-proleterska-brigada.pdf']
  },
  {
    id: '13-proleterska-brigada',
    name: '13. proleterska udarna brigada "Rade Končar"',
    nameEn: '13th Proletarian Assault Brigade "Rade Končar"',
    description: 'Formirana 7. novembra 1942. godine. Spisak palih i preživjelih boraca.',
    image: '/images/13-proleterska-brigada.jpg',
    soldierCount: 7936,
    dataFile: '/13-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/13-proleterska-spisak.pdf']
  }
  // Add more units here as you get more data
]
