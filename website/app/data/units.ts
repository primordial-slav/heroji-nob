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
    description: 'Formirana u junu 1942.',
    image: '/images/prva-licka-brigada.jpg',
    soldierCount: 9814,
    dataFile: '/soldiers.json',
    pdfFiles: ['/pdfs/prva-licka-proleterska.pdf']
  },
  {
    id: 'prva-proleterska-brigada',
    name: 'Prva proleterska narodnooslobodilačka udarna brigada',
    nameEn: '1st Proletarian People\'s Liberation Assault Brigade',
    description: 'Formirana 21. decembra 1941.',
    image: '/images/prva-proleterska-brigada.jpg',
    soldierCount: 14060,
    dataFile: '/prva-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/prva-proleterska-1.pdf', '/pdfs/prva-proleterska-2.pdf', '/pdfs/prva-proleterska-3.pdf']
  },
  {
    id: 'ljubljanska-brigada',
    name: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    nameEn: '10th Slovenian People\'s Liberation Assault Brigade "Ljubljana"',
    description: 'Formirana 11. septembra 1943.',
    image: '/images/ljubljanska-brigada.jpg',
    soldierCount: 3175,
    dataFile: '/ljubljanska-soldiers.json',
    pdfFiles: ['/pdfs/ljubljanska-brigada.pdf']
  },
  {
    id: 'druga-licka-brigada',
    name: 'Druga lička proleterska brigada',
    nameEn: '2nd Lika Proletarian Brigade',
    description: 'Formirana 1942. Poginuli, umrli i nestali borci, i oni koji su preživeli rat.',
    image: '/images/druga_licka.jpg',
    soldierCount: 7592,
    dataFile: '/druga-licka-soldiers.json',
    pdfFiles: ['/pdfs/druga-licka-spisak.pdf', '/pdfs/druga-licka-sjecanja-prezivjeli.pdf', '/pdfs/druga-licka-sjecanja-poginuli.pdf']
  },
  {
    id: 'treca-proleterska-brigada',
    name: 'Treća proleterska (sandžačka) brigada',
    nameEn: '3rd Proletarian (Sandžak) Brigade',
    description: 'Formirana 5. juna 1942. Spisak je sa dana kad je brigada formirana.',
    image: '/images/treca-proleterska-brigada.jpg',
    soldierCount: 897,
    dataFile: '/treca-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/treca-proleterska-brigada.pdf']
  },
  {
    id: '13-proleterska-brigada',
    name: '13. proleterska udarna brigada "Rade Končar"',
    nameEn: '13th Proletarian Assault Brigade "Rade Končar"',
    description: 'Formirana 7. novembra 1942. Poginuli i preživeli borci.',
    image: '/images/13-proleterska-brigada.jpg',
    soldierCount: 8261,
    dataFile: '/13-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/13-proleterska-spisak.pdf']
  },
  {
    id: '2-dalmatinska-brigada',
    name: '2. dalmatinska proleterska udarna brigada',
    nameEn: '2nd Dalmatian Proletarian Assault Brigade',
    description: 'Formirana 3. oktobra 1942. Borci brigade.',
    image: '/images/2-dalmatinska-brigada.jpg',
    soldierCount: 5546,
    dataFile: '/2-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/2-dalmatinska-proleterska.pdf']
  },
  {
    id: '4-splitska-brigada',
    name: '4. splitska udarna brigada',
    nameEn: '4th Split Assault Brigade',
    description: 'Formirana u septembru 1943. Poginuli i preživeli borci.',
    image: '/images/4-splitska-brigada.jpg',
    soldierCount: 3097,
    dataFile: '/4-splitska-soldiers.json',
    pdfFiles: ['/pdfs/4-splitska-brigada.pdf']
  },
  {
    id: 'prva-vojvodjanska-brigada',
    name: 'Prva vojvođanska brigada',
    nameEn: '1st Vojvodina Brigade',
    description: 'Formirana 1944. Borci brigade.',
    image: '/images/prva-vojvodjanska-brigada.jpg',
    soldierCount: 1592,
    dataFile: '/prva-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/prva-vojvodjanska.pdf']
  },
  {
    id: '5-kozaracka-brigada',
    name: '5. krajiška (kozaračka) udarna brigada',
    nameEn: '5th Krajina (Kozara) Assault Brigade',
    description: 'Formirana 23. septembra 1942. na Kozari. Poginuli, nestali i umrli borci i starešine.',
    image: '/images/peta-kozaracka-brigada.jpg',
    soldierCount: 1007,
    dataFile: '/5-kozaracka-soldiers.json',
    pdfFiles: ['/pdfs/5-kozaracka.pdf']
  },
  {
    id: '2-vojvodjanska-brigada',
    name: '2. vojvođanska udarna brigada',
    nameEn: '2nd Vojvodina Assault Brigade',
    description: 'Formirana 20. aprila 1943. na Majevici. Borci i starešine od formiranja do kraja rata.',
    image: '/images/druga-vojvodjanska-brigada.jpg',
    soldierCount: 2143,
    dataFile: '/2-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/2-vojvodjanska.pdf']
  },
  {
    id: '8-krajiska-brigada',
    name: '8. krajiška udarna brigada',
    nameEn: '8th Krajina Assault Brigade',
    description: 'Formirana 28. decembra 1942. u Cazinu. Borci koji su poginuli ili umrli u ratu.',
    image: '/images/osma-krajiska-brigada.jpg',
    soldierCount: 1171,
    dataFile: '/8-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/8-krajiska.pdf']
  },
  {
    id: '6-krajiska-brigada',
    name: '6. krajiška udarna brigada',
    nameEn: '6th Krajina Assault Brigade',
    description: 'Formirana 14. oktobra 1942. od jedinica Prvog krajiškog odreda. Poginuli i umrli borci i starešine.',
    image: '/images/sesta-krajiska-brigada.jpg',
    soldierCount: 1825,
    dataFile: '/6-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/6-krajiska.pdf']
  },
  {
    id: '4-krajiska-brigada',
    name: '4. krajiška udarna brigada',
    nameEn: '4th Krajina Assault Brigade',
    description: 'Formirana 9. septembra 1942. u Tičevu kod Bosanskog Grahova. Poginuli, umrli i nestali borci i starešine.',
    image: '/images/cetvrta-krajiska-brigada.jpg',
    soldierCount: 1663,
    dataFile: '/4-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/4-krajiska.pdf']
  },
  {
    id: '3-krajiska-proleterska-brigada',
    name: '3. krajiška proleterska udarna brigada',
    nameEn: '3rd Krajina Proletarian Assault Brigade',
    description: 'Formirana 22. avgusta 1942. u Kamenici kod Drvara. Poginuli borci.',
    image: '/images/treca-krajiska-brigada.jpg',
    soldierCount: 2268,
    dataFile: '/3-krajiska-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/3-krajiska-proleterska.pdf']
  },
  {
    id: '17-slavonska-brigada',
    name: '17. slavonska udarna brigada',
    nameEn: '17th Slavonia Assault Brigade',
    description: 'Formirana 30. decembra 1942. kod Voćina. Poginuli i preživeli borci, po opštinama.',
    image: '/images/17-slavonska-brigada.jpg',
    soldierCount: 3613,
    dataFile: '/17-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/17-slavonska-poginuli.pdf', '/pdfs/17-slavonska-prezivjeli.pdf']
  },
  {
    id: '25-srpska-divizija',
    name: '25. srpska udarna divizija',
    nameEn: '25th Serbian Assault Division',
    description: 'Formirana 21. juna 1944. kod Jošanice u Pustoj reci. Poginuli borci i starešine 16, 18. i 19. srpske brigade.',
    image: '/images/25-srpska-divizija.jpg',
    soldierCount: 882,
    dataFile: '/25-srpska-divizija-soldiers.json',
    pdfFiles: ['/pdfs/25-srpska-divizija.pdf']
  },
  {
    id: '1-sumadijska-brigada',
    name: '1. šumadijska brigada',
    nameEn: '1st Šumadija Brigade',
    description: 'Formirana 5. oktobra 1943. Poginuli borci i starešine, i borci koji su preživeli rat.',
    image: '/images/1-sumadijska-brigada.jpg',
    soldierCount: 320,
    dataFile: '/1-sumadijska-soldiers.json',
    pdfFiles: ['/pdfs/1-sumadijska.pdf']
  },
  {
    id: '18-slavonska-brigada',
    name: '18. slavonska udarna brigada',
    nameEn: '18th Slavonia Assault Brigade',
    description: 'Formirana 11. februara 1943. u Mijači kod Pakraca. Poginuli, umrli i preživeli borci.',
    image: '/images/18-slavonska-brigada.jpg',
    soldierCount: 1548,
    dataFile: '/18-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/18-slavonska.pdf']
  },
  {
    id: '4-banijska-brigada',
    name: '4. banijska brigada',
    nameEn: '4th Banija Brigade',
    description: 'Brigada 7. divizije. Borci brigade.',
    image: '/images/4-banijska-brigada.jpg',
    soldierCount: 2147,
    dataFile: '/4-banijska-soldiers.json',
    pdfFiles: ['/pdfs/4-banijska.pdf']
  },
  {
    id: '4-srpska-brigada',
    name: '4. srpska udarna brigada',
    nameEn: '4th Serbian Assault Brigade',
    description: 'Borci brigade, među njima i stranci i borci čije ime nije utvrđeno.',
    image: '/images/4-srpska-brigada.jpg',
    soldierCount: 6323,
    dataFile: '/4-srpska-soldiers.json',
    pdfFiles: ['/pdfs/4-srpska.pdf']
  },
  {
    id: '7-vojvodjanska-brigada',
    name: '7. vojvođanska udarna brigada',
    nameEn: '7th Vojvodina Assault Brigade',
    description: 'Preživeli, poginuli i borci umrli posle rata, i borci 4. (ruskog) bataljona.',
    image: '/images/7-vojvodjanska-brigada.jpg',
    soldierCount: 3577,
    dataFile: '/7-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/7-vojvodjanska.pdf']
  },
  {
    id: '19-bircanska-brigada',
    name: '19. birčanska brigada',
    nameEn: '19th Birač Brigade',
    description: 'Borci brigade.',
    image: '/images/19-bircanska-brigada.jpg',
    soldierCount: 1987,
    dataFile: '/19-bircanska-soldiers.json',
    pdfFiles: ['/pdfs/19-bircanska.pdf']
  },
  {
    id: '2-krajiska-brigada',
    name: '2. krajiška udarna brigada',
    nameEn: '2nd Krajina Assault Brigade',
    description: 'Formirana 2. avgusta 1942. Poginuli i umrli borci i starešine.',
    image: '/images/2-krajiska-brigada.jpg',
    soldierCount: 1566,
    dataFile: '/2-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/2-krajiska.pdf']
  },
  {
    id: 'tuzlanski-odred',
    name: 'Tuzlanski NOP odred',
    nameEn: 'Tuzla Partisan Detachment',
    description: 'Borci odreda, mnogi i sa fotografijom.',
    image: '/images/tuzlanski-odred.jpg',
    soldierCount: 1110,
    dataFile: '/tuzlanski-odred-soldiers.json',
    pdfFiles: ['/pdfs/tuzlanski-odred.pdf']
  },
  {
    id: 'uzicki-odred',
    name: 'Užički NOP odred „Dimitrije Tucović“',
    nameEn: 'Užice Partisan Detachment',
    description: 'Borci odreda poginuli u ratu 1941–1945.',
    image: '/images/uzicki-odred.jpg',
    soldierCount: 1282,
    dataFile: '/uzicki-odred-soldiers.json',
    pdfFiles: ['/pdfs/uzicki-odred.pdf']
  },
  {
    id: '14-srpska-brigada',
    name: '14. srpska udarna brigada',
    nameEn: '14th Serbian Assault Brigade',
    description: 'Poginuli borci i starešine Niškog odreda i 14. srpske brigade.',
    image: '/images/14-srpska-brigada.jpg',
    soldierCount: 1006,
    dataFile: '/14-srpska-soldiers.json',
    pdfFiles: ['/pdfs/14-srpska.pdf']
  },
  {
    id: '7-crnogorska-brigada',
    name: '7. crnogorska omladinska brigada „Budo Tomović“',
    nameEn: '7th Montenegrin Youth Brigade',
    description: 'Poginuli borci brigade.',
    image: '/images/7-crnogorska-omladinska-brigada.jpg',
    soldierCount: 439,
    dataFile: '/7-crnogorska-soldiers.json',
    pdfFiles: ['/pdfs/7-crnogorska-omladinska.pdf']
  },
  {
    id: '17-majevicka-brigada',
    name: '17. majevička brigada',
    nameEn: '17th Majevica Brigade',
    description: 'Poginuli i umrli borci Trećeg majevičkog odreda i 17. majevičke brigade.',
    image: '/images/17-majevicka-brigada.jpg',
    soldierCount: 900,
    dataFile: '/17-majevicka-soldiers.json',
    pdfFiles: ['/pdfs/17-majevicka.pdf']
  },
  {
    id: '25-brodska-brigada',
    name: '25. brodska brigada',
    nameEn: '25th Brod Brigade',
    description: 'Poginuli borci, i svi borci i starešine brigade u oktobru 1943.',
    image: '/images/25-brodska-brigada.jpg',
    soldierCount: 825,
    dataFile: '/25-brodska-soldiers.json',
    pdfFiles: ['/pdfs/25-brodska-poginuli.pdf', '/pdfs/25-brodska-sastav.pdf']
  },
  {
    id: '25-srpska-brigada',
    name: '25. srpska brigada',
    nameEn: '25th Serbian Brigade',
    description: 'Poginuli i ranjeni borci i starešine, po ratnim spiskovima brigade.',
    image: '/images/25-srpska-brigada.jpg',
    soldierCount: 368,
    dataFile: '/25-srpska-brigada-soldiers.json',
    pdfFiles: ['/pdfs/25-srpska-brigada.pdf']
  },
  {
    id: '21-tuzlanska-brigada',
    name: '21. tuzlanska brigada',
    nameEn: '21st Tuzla Brigade',
    description: 'Poginuli borci i starešine.',
    image: '/images/21-tuzlanska-brigada.jpg',
    soldierCount: 211,
    dataFile: '/21-tuzlanska-soldiers.json',
    pdfFiles: ['/pdfs/21-tuzlanska.pdf']
  },
  {
    id: '53-srednjobosanska-divizija',
    name: '53. srednjobosanska divizija',
    nameEn: '53rd Central Bosnian Division',
    description: 'Poginuli, zarobljeni i nestali borci 14, 18. i 19. brigade i Prnjavorskog i Motajičkog odreda.',
    image: '/images/53-srednjobosanska-divizija.jpg',
    soldierCount: 800,
    dataFile: '/53-srednjobosanska-soldiers.json',
    pdfFiles: ['/pdfs/53-srednjobosanska-divizija.pdf']
  },
  {
    id: '21-slavonska-brigada',
    name: '21. slavonska brigada',
    nameEn: '21st Slavonian Brigade',
    description: 'Poginuli, umrli i nestali borci i starešine.',
    image: '/images/21-slavonska-brigada.jpg',
    soldierCount: 1117,
    dataFile: '/21-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/21-slavonska.pdf']
  },
  {
    id: '32-zagorska-divizija',
    name: '32. zagorska divizija',
    nameEn: '32nd Zagorje Division',
    description: 'Borci divizije i Zapadne grupe odreda. U knjizi su samo imena; zvezdica znači da je borac poginuo, crtica da je nestao.',
    image: '/images/32-zagorska-divizija.jpg',
    soldierCount: 10041,
    dataFile: '/32-divizija-soldiers.json',
    pdfFiles: ['/pdfs/32-divizija.pdf']
  },
  {
    id: '1-dalmatinska-brigada',
    name: '1. dalmatinska proleterska brigada',
    nameEn: '1st Dalmatian Proletarian Brigade',
    description: 'Borci poginuli u ratu. Spisak postoji samo kao tekst na znaci.org, bez skenirane knjige.',
    image: '/images/1-dalmatinska-brigada.jpg',
    soldierCount: 2165,
    dataFile: '/1-dalmatinska-soldiers.json',
    pdfFiles: []
  },
  {
    id: '16-slavonska-omladinska-brigada',
    name: '16. slavonska omladinska brigada „Jože Vlahović“',
    nameEn: '16th Slavonian Youth Brigade "Jože Vlahović"',
    description: 'Poginuli borci i starešine, poginuli u Pokuplju i na Žumberku, i rukovodioci brigade od formiranja do kraja rata.',
    image: '/images/16-slavonska-omladinska-brigada.jpg',
    soldierCount: 1121,
    dataFile: '/16-slavonska-omladinska-soldiers.json',
    pdfFiles: ['/pdfs/16-slavonska-omladinska.pdf']
  },
  {
    id: '8-crnogorska-brigada',
    name: '8. crnogorska brigada',
    nameEn: '8th Montenegrin Brigade',
    description: 'Poginuli borci i starešine, i dopunski spisak poginulih iz Uba.',
    image: '/images/8-crnogorska-brigada.jpg',
    soldierCount: 730,
    dataFile: '/8-crnogorska-soldiers.json',
    pdfFiles: ['/pdfs/8-crnogorska.pdf']
  }
  // Add more units here as you get more data
]
