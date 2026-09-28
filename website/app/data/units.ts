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
    soldierCount: 9757,
    dataFile: '/soldiers.json',
    pdfFiles: ['/pdfs/prva-licka-proleterska.pdf']
  },
  {
    id: 'prva-proleterska-brigada',
    name: 'Prva proleterska narodnooslobodilačka udarna brigada',
    nameEn: '1st Proletarian People\'s Liberation Assault Brigade',
    description: 'Formirana 21. decembra 1941. godine',
    image: '/images/prva-proleterska-brigada.jpg',
    soldierCount: 14090,
    dataFile: '/prva-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/prva-proleterska-1.pdf', '/pdfs/prva-proleterska-2.pdf', '/pdfs/prva-proleterska-3.pdf']
  },
  {
    id: 'ljubljanska-brigada',
    name: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    nameEn: '10th Slovenian People\'s Liberation Assault Brigade "Ljubljana"',
    description: 'Formirana 11. septembra 1943. godine',
    image: '/images/ljubljanska-brigada.jpg',
    soldierCount: 3133,
    dataFile: '/ljubljanska-soldiers.json',
    pdfFiles: ['/pdfs/ljubljanska-brigada.pdf']
  },
  {
    id: 'druga-licka-brigada',
    name: 'Druga lička proleterska brigada',
    nameEn: '2nd Lika Proletarian Brigade',
    description: 'Formirana 1942. godine. Spisak poginulih, umrlih i nestalih boraca.',
    image: '/images/druga_licka.jpg',
    soldierCount: 1487,
    dataFile: '/druga-licka-soldiers.json',
    pdfFiles: ['/pdfs/druga-licka-spisak.pdf']
  },
  {
    id: 'treca-proleterska-brigada',
    name: 'Treća proleterska (sandžačka) brigada',
    nameEn: '3rd Proletarian (Sandžak) Brigade',
    description: 'Formirana 5. juna 1942. godine. Spisak boraca i starešina na dan formiranja brigade.',
    image: '/images/treca-proleterska-brigada.jpg',
    soldierCount: 894,
    dataFile: '/treca-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/treca-proleterska-brigada.pdf']
  },
  {
    id: '13-proleterska-brigada',
    name: '13. proleterska udarna brigada "Rade Končar"',
    nameEn: '13th Proletarian Assault Brigade "Rade Končar"',
    description: 'Formirana 7. novembra 1942. godine. Spisak palih i preživjelih boraca.',
    image: '/images/13-proleterska-brigada.jpg',
    soldierCount: 8255,
    dataFile: '/13-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/13-proleterska-spisak.pdf']
  },
  {
    id: '2-dalmatinska-brigada',
    name: '2. dalmatinska proleterska udarna brigada',
    nameEn: '2nd Dalmatian Proletarian Assault Brigade',
    description: 'Formirana 3. oktobra 1942. godine. Popis boraca brigade.',
    image: '/images/2-dalmatinska-brigada.jpg',
    soldierCount: 5542,
    dataFile: '/2-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/2-dalmatinska-proleterska.pdf']
  },
  {
    id: '4-splitska-brigada',
    name: '4. splitska udarna brigada',
    nameEn: '4th Split Assault Brigade',
    description: 'Formirana septembra 1943. godine. Popis poginulih i preživjelih boraca.',
    image: '/images/4-splitska-brigada.jpg',
    soldierCount: 3093,
    dataFile: '/4-splitska-soldiers.json',
    pdfFiles: ['/pdfs/4-splitska-brigada.pdf']
  },
  {
    id: 'prva-vojvodjanska-brigada',
    name: 'Prva vojvođanska brigada',
    nameEn: '1st Vojvodina Brigade',
    description: 'Formirana 1944. godine. Spisak boraca brigade.',
    image: '/images/prva-vojvodjanska-brigada.jpg',
    soldierCount: 1592,
    dataFile: '/prva-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/prva-vojvodjanska.pdf']
  },
  {
    id: '5-kozaracka-brigada',
    name: '5. krajiška (kozaračka) udarna brigada',
    nameEn: '5th Krajina (Kozara) Assault Brigade',
    description: 'Formirana 23. septembra 1942. godine na Kozari. Spisak poginulih, nestalih i umrlih boraca i rukovodilaca.',
    image: '/images/peta-kozaracka-brigada.jpg',
    soldierCount: 1007,
    dataFile: '/5-kozaracka-soldiers.json',
    pdfFiles: ['/pdfs/5-kozaracka.pdf']
  },
  {
    id: '2-vojvodjanska-brigada',
    name: '2. vojvođanska udarna brigada',
    nameEn: '2nd Vojvodina Assault Brigade',
    description: 'Formirana 20. aprila 1943. godine na Majevici. Spisak boraca i starešina brigade od formiranja do kraja rata.',
    image: '/images/druga-vojvodjanska-brigada.jpg',
    soldierCount: 2143,
    dataFile: '/2-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/2-vojvodjanska.pdf']
  },
  {
    id: '8-krajiska-brigada',
    name: '8. krajiška udarna brigada',
    nameEn: '8th Krajina Assault Brigade',
    description: 'Formirana 28. decembra 1942. godine u Cazinu. Spisak poginulih i umrlih boraca brigade u toku NOR-a.',
    image: '/images/osma-krajiska-brigada.jpg',
    soldierCount: 1171,
    dataFile: '/8-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/8-krajiska.pdf']
  },
  {
    id: '6-krajiska-brigada',
    name: '6. krajiška udarna brigada',
    nameEn: '6th Krajina Assault Brigade',
    description: 'Formirana 14. oktobra 1942. godine od jedinica Prvog krajiškog NOP odreda. Spisak poginulih i umrlih boraca i starješina brigade.',
    image: '/images/sesta-krajiska-brigada.jpg',
    soldierCount: 1825,
    dataFile: '/6-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/6-krajiska.pdf']
  },
  {
    id: '4-krajiska-brigada',
    name: '4. krajiška udarna brigada',
    nameEn: '4th Krajina Assault Brigade',
    description: 'Formirana 9. septembra 1942. godine u Tičevu kod Bosanskog Grahova. Spisak poginulih, umrlih i nestalih boraca i starešina brigade.',
    image: '/images/cetvrta-krajiska-brigada.jpg',
    soldierCount: 1663,
    dataFile: '/4-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/4-krajiska.pdf']
  },
  {
    id: '3-krajiska-proleterska-brigada',
    name: '3. krajiška proleterska udarna brigada',
    nameEn: '3rd Krajina Proletarian Assault Brigade',
    description: 'Formirana 22. avgusta 1942. godine u selu Kamenici kod Drvara. Spisak palih boraca brigade s osnovnim matičnim podacima.',
    image: '/images/treca-krajiska-brigada.jpg',
    soldierCount: 2268,
    dataFile: '/3-krajiska-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/3-krajiska-proleterska.pdf']
  },
  {
    id: '17-slavonska-brigada',
    name: '17. slavonska udarna brigada',
    nameEn: '17th Slavonia Assault Brigade',
    description: 'Formirana 30. decembra 1942. godine u rejonu Voćina. Spiskovi poginulih i preživjelih boraca brigade, po općinama.',
    image: '/images/17-slavonska-brigada.jpg',
    soldierCount: 3613,
    dataFile: '/17-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/17-slavonska-poginuli.pdf', '/pdfs/17-slavonska-prezivjeli.pdf']
  },
  {
    id: '25-srpska-divizija',
    name: '25. srpska udarna divizija',
    nameEn: '25th Serbian Assault Division',
    description: 'Formirana 21. juna 1944. godine kod sela Jošanice u Pustoj reci. Spisak poginulih boraca i rukovodilaca divizije (16, 18. i 19. srpska brigada).',
    image: '/images/pdf-thumbs/25-srpska-divizija.jpg',
    soldierCount: 881,
    dataFile: '/25-srpska-divizija-soldiers.json',
    pdfFiles: ['/pdfs/25-srpska-divizija.pdf']
  },
  {
    id: '1-sumadijska-brigada',
    name: '1. šumadijska brigada',
    nameEn: '1st Šumadija Brigade',
    description: 'Formirana 5. oktobra 1943. godine. Spiskovi poginulih boraca i starešina i boraca koji su preživeli rat.',
    image: '/images/pdf-thumbs/1-sumadijska.jpg',
    soldierCount: 319,
    dataFile: '/1-sumadijska-soldiers.json',
    pdfFiles: ['/pdfs/1-sumadijska.pdf']
  },
  {
    id: '18-slavonska-brigada',
    name: '18. slavonska udarna brigada',
    nameEn: '18th Slavonia Assault Brigade',
    description: 'Formirana 11. februara 1943. godine u selu Mijači kod Pakraca. Spiskovi poginulih i umrlih te preživelih boraca brigade.',
    image: '/images/18-slavonska-brigada.jpg',
    soldierCount: 1548,
    dataFile: '/18-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/18-slavonska.pdf']
  }
  // Add more units here as you get more data
]
