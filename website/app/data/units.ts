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
    description: 'Formirana 8. jula 1942. kod vrela Mrežnice.',
    image: '/images/prva-licka-brigada.jpg',
    soldierCount: 9863,
    dataFile: '/soldiers.json',
    pdfFiles: ['/pdfs/prva-licka-proleterska.pdf']
  },
  {
    id: 'prva-proleterska-brigada',
    name: 'Prva proleterska narodnooslobodilačka udarna brigada',
    nameEn: '1st Proletarian People\'s Liberation Assault Brigade',
    description: 'Formirana 21. decembra 1941.',
    image: '/images/prva-proleterska-brigada.jpg',
    soldierCount: 14501,
    dataFile: '/prva-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/prva-proleterska-1.pdf', '/pdfs/prva-proleterska-2.pdf', '/pdfs/prva-proleterska-3.pdf', '/pdfs/borci-sutjeske-prva-proleterska.pdf']
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
    description: 'Formirana 18. avgusta 1942. u Laudonovom gaju. Poginuli, umrli i nestali borci, i oni koji su preživeli rat.',
    image: '/images/druga_licka.jpg',
    soldierCount: 7591,
    dataFile: '/druga-licka-soldiers.json',
    pdfFiles: ['/pdfs/druga-licka-spisak.pdf', '/pdfs/druga-licka-sjecanja-prezivjeli.pdf', '/pdfs/druga-licka-sjecanja-poginuli.pdf']
  },
  {
    id: 'treca-proleterska-brigada',
    name: 'Treća proleterska (sandžačka) brigada',
    nameEn: '3rd Proletarian (Sandžak) Brigade',
    description: 'Formirana 5. juna 1942. Spisak je sa dana kad je brigada formirana.',
    image: '/images/treca-proleterska-brigada.jpg',
    soldierCount: 2666,
    dataFile: '/treca-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/treca-proleterska-brigada.pdf', '/pdfs/treca-proleterska-poginuli-knj3.pdf', '/pdfs/treca-proleterska-formiranje.pdf', '/pdfs/borci-sutjeske-treca-proleterska.pdf']
  },
  {
    id: '13-proleterska-brigada',
    name: '13. proleterska udarna brigada "Rade Končar"',
    nameEn: '13th Proletarian Assault Brigade "Rade Končar"',
    description: 'Formirana 7. novembra 1942. Poginuli i preživeli borci.',
    image: '/images/13-proleterska-brigada.jpg',
    soldierCount: 8275,
    dataFile: '/13-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/13-proleterska-spisak.pdf']
  },
  {
    id: '2-dalmatinska-brigada',
    name: '2. dalmatinska proleterska udarna brigada',
    nameEn: '2nd Dalmatian Proletarian Assault Brigade',
    description: 'Formirana 3. oktobra 1942. Borci brigade.',
    image: '/images/2-dalmatinska-brigada.jpg',
    soldierCount: 6057,
    dataFile: '/2-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/2-dalmatinska-proleterska.pdf', '/pdfs/borci-sutjeske-2-dalmatinska.pdf']
  },
  {
    id: '4-splitska-brigada',
    name: '4. splitska udarna brigada',
    nameEn: '4th Split Assault Brigade',
    description: 'Formirana u septembru 1943. Poginuli i preživeli borci.',
    image: '/images/4-splitska-brigada.jpg',
    soldierCount: 3078,
    dataFile: '/4-splitska-soldiers.json',
    pdfFiles: ['/pdfs/4-splitska-brigada.pdf']
  },
  {
    id: 'prva-vojvodjanska-brigada',
    name: 'Prva vojvođanska brigada',
    nameEn: '1st Vojvodina Brigade',
    description: 'Formirana 11. aprila 1943. u Brđanima na Majevici. Borci brigade.',
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
    soldierCount: 1020,
    dataFile: '/5-kozaracka-soldiers.json',
    pdfFiles: ['/pdfs/5-kozaracka.pdf']
  },
  {
    id: '2-vojvodjanska-brigada',
    name: '2. vojvođanska udarna brigada',
    nameEn: '2nd Vojvodina Assault Brigade',
    description: 'Formirana 20. aprila 1943. na Majevici. Borci i starešine od formiranja do kraja rata.',
    image: '/images/druga-vojvodjanska-brigada.jpg',
    soldierCount: 2149,
    dataFile: '/2-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/2-vojvodjanska.pdf']
  },
  {
    id: '8-krajiska-brigada',
    name: '8. krajiška udarna brigada',
    nameEn: '8th Krajina Assault Brigade',
    description: 'Formirana 28. decembra 1942. u Cazinu. Borci koji su poginuli ili umrli u ratu.',
    image: '/images/osma-krajiska-brigada.jpg',
    soldierCount: 1172,
    dataFile: '/8-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/8-krajiska.pdf']
  },
  {
    id: '6-krajiska-brigada',
    name: '6. krajiška udarna brigada',
    nameEn: '6th Krajina Assault Brigade',
    description: 'Formirana 14. oktobra 1942. od jedinica Prvog krajiškog odreda. Poginuli i umrli borci i starešine, i borci koji su preživeli rat.',
    image: '/images/sesta-krajiska-brigada.jpg',
    soldierCount: 3656,
    dataFile: '/6-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/6-krajiska.pdf', '/pdfs/6-krajiska-prezivjeli.pdf']
  },
  {
    id: '4-krajiska-brigada',
    name: '4. krajiška udarna brigada',
    nameEn: '4th Krajina Assault Brigade',
    description: 'Formirana 9. septembra 1942. u Tičevu kod Bosanskog Grahova. Poginuli, umrli i nestali borci i starešine.',
    image: '/images/cetvrta-krajiska-brigada.jpg',
    soldierCount: 1670,
    dataFile: '/4-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/4-krajiska.pdf']
  },
  {
    id: '3-krajiska-proleterska-brigada',
    name: '3. krajiška proleterska udarna brigada',
    nameEn: '3rd Krajina Proletarian Assault Brigade',
    description: 'Formirana 22. avgusta 1942. u Kamenici kod Drvara. Borci brigade od formiranja do kraja rata.',
    image: '/images/treca-krajiska-brigada.jpg',
    soldierCount: 7297,
    dataFile: '/3-krajiska-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/3-krajiska-proleterska.pdf', '/pdfs/borci-sutjeske-3-krajiska.pdf', '/pdfs/3-krajiska-spisak-boraca.pdf']
  },
  {
    id: '17-slavonska-brigada',
    name: '17. slavonska udarna brigada',
    nameEn: '17th Slavonia Assault Brigade',
    description: 'Formirana 30. decembra 1942. kod Voćina. Poginuli i preživeli borci, po opštinama.',
    image: '/images/17-slavonska-brigada.jpg',
    soldierCount: 3648,
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
    soldierCount: 324,
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
    description: 'Formirana 30. juna 1943. u Obijaju na Baniji. Brigada 7. divizije. Borci brigade.',
    image: '/images/4-banijska-brigada.jpg',
    soldierCount: 2147,
    dataFile: '/4-banijska-soldiers.json',
    pdfFiles: ['/pdfs/4-banijska.pdf']
  },
  {
    id: '4-srpska-brigada',
    name: '4. srpska udarna brigada',
    nameEn: '4th Serbian Assault Brigade',
    description: 'Formirana 20. novembra 1943. u Bucima kod Kruševca. Borci brigade, među njima i stranci i borci čije ime nije utvrđeno.',
    image: '/images/4-srpska-brigada.jpg',
    soldierCount: 6332,
    dataFile: '/4-srpska-soldiers.json',
    pdfFiles: ['/pdfs/4-srpska.pdf']
  },
  {
    id: '7-vojvodjanska-brigada',
    name: '7. vojvođanska udarna brigada',
    nameEn: '7th Vojvodina Assault Brigade',
    description: 'Formirana 2. jula 1944. na salašu Mušickog kod Batrovaca. Preživeli, poginuli i borci umrli posle rata, i borci 4. (ruskog) bataljona.',
    image: '/images/7-vojvodjanska-brigada.jpg',
    soldierCount: 3578,
    dataFile: '/7-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/7-vojvodjanska.pdf']
  },
  {
    id: '19-bircanska-brigada',
    name: '19. birčanska brigada',
    nameEn: '19th Birač Brigade',
    description: 'Formirana 24. oktobra 1943. u Vlasenici. Borci brigade.',
    image: '/images/19-bircanska-brigada.jpg',
    soldierCount: 1989,
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
    description: 'Formiran 24. oktobra 1943. u Tuzli. Borci odreda, mnogi i sa fotografijom.',
    image: '/images/tuzlanski-odred.jpg',
    soldierCount: 1110,
    dataFile: '/tuzlanski-odred-soldiers.json',
    pdfFiles: ['/pdfs/tuzlanski-odred.pdf']
  },
  {
    id: 'uzicki-odred',
    name: 'Užički NOP odred „Dimitrije Tucović“',
    nameEn: 'Užice Partisan Detachment',
    description: 'Formiran 7. jula 1941. u Užicu. Borci odreda poginuli u ratu 1941–1945.',
    image: '/images/uzicki-odred.jpg',
    soldierCount: 1283,
    dataFile: '/uzicki-odred-soldiers.json',
    pdfFiles: ['/pdfs/uzicki-odred.pdf']
  },
  {
    id: '14-srpska-brigada',
    name: '14. srpska udarna brigada',
    nameEn: '14th Serbian Assault Brigade',
    description: 'Formirana 17. juna 1944. u Ribarima kod Đunisa. Poginuli borci i starešine Niškog odreda i 14. srpske brigade.',
    image: '/images/14-srpska-brigada.jpg',
    soldierCount: 1006,
    dataFile: '/14-srpska-soldiers.json',
    pdfFiles: ['/pdfs/14-srpska.pdf']
  },
  {
    id: '7-crnogorska-brigada',
    name: '7. crnogorska omladinska brigada „Budo Tomović“',
    nameEn: '7th Montenegrin Youth Brigade',
    description: 'Formirana 30. decembra 1943. u Kolašinu. Poginuli borci brigade.',
    image: '/images/7-crnogorska-omladinska-brigada.jpg',
    soldierCount: 439,
    dataFile: '/7-crnogorska-soldiers.json',
    pdfFiles: ['/pdfs/7-crnogorska-omladinska.pdf']
  },
  {
    id: '17-majevicka-brigada',
    name: '17. majevička brigada',
    nameEn: '17th Majevica Brigade',
    description: 'Formirana 10. oktobra 1943. u okolini Tuzle. Poginuli i umrli borci Trećeg majevičkog odreda i 17. majevičke brigade.',
    image: '/images/17-majevicka-brigada.jpg',
    soldierCount: 902,
    dataFile: '/17-majevicka-soldiers.json',
    pdfFiles: ['/pdfs/17-majevicka.pdf']
  },
  {
    id: '25-brodska-brigada',
    name: '25. brodska brigada',
    nameEn: '25th Brod Brigade',
    description: 'Formirana 1. oktobra 1943. kod Slavonske Orahovice. Poginuli borci, i svi borci i starešine brigade u oktobru 1943.',
    image: '/images/25-brodska-brigada.jpg',
    soldierCount: 825,
    dataFile: '/25-brodska-soldiers.json',
    pdfFiles: ['/pdfs/25-brodska-poginuli.pdf', '/pdfs/25-brodska-sastav.pdf']
  },
  {
    id: '25-srpska-brigada',
    name: '25. srpska brigada',
    nameEn: '25th Serbian Brigade',
    description: 'Formirana 1. septembra 1944. u Strelcu kod Pirota. Poginuli i ranjeni borci i starešine, po ratnim spiskovima brigade.',
    image: '/images/25-srpska-brigada.jpg',
    soldierCount: 368,
    dataFile: '/25-srpska-brigada-soldiers.json',
    pdfFiles: ['/pdfs/25-srpska-brigada.pdf']
  },
  {
    id: '21-tuzlanska-brigada',
    name: '21. tuzlanska brigada',
    nameEn: '21st Tuzla Brigade',
    description: 'Formirana 19. septembra 1944. u Pašabunaru kod Tuzle. Poginuli borci i starešine.',
    image: '/images/21-tuzlanska-brigada.jpg',
    soldierCount: 211,
    dataFile: '/21-tuzlanska-soldiers.json',
    pdfFiles: ['/pdfs/21-tuzlanska.pdf']
  },
  {
    id: '53-srednjobosanska-divizija',
    name: '53. srednjobosanska divizija',
    nameEn: '53rd Central Bosnian Division',
    description: 'Formirana 23. jula 1944. u srednjoj Bosni. Poginuli, zarobljeni i nestali borci 14, 18. i 19. brigade i Prnjavorskog i Motajičkog odreda.',
    image: '/images/53-srednjobosanska-divizija.jpg',
    soldierCount: 800,
    dataFile: '/53-srednjobosanska-soldiers.json',
    pdfFiles: ['/pdfs/53-srednjobosanska-divizija.pdf']
  },
  {
    id: '21-slavonska-brigada',
    name: '21. slavonska brigada',
    nameEn: '21st Slavonian Brigade',
    description: 'Formirana 17. maja 1943. u Orljavcu kod Slavonske Požege. Poginuli, umrli i nestali borci i starešine.',
    image: '/images/21-slavonska-brigada.jpg',
    soldierCount: 1117,
    dataFile: '/21-slavonska-soldiers.json',
    pdfFiles: ['/pdfs/21-slavonska.pdf']
  },
  {
    id: '32-zagorska-divizija',
    name: '32. zagorska divizija',
    nameEn: '32nd Zagorje Division',
    description: 'Formirana 12. decembra 1943. na Kalniku. Borci divizije i Zapadne grupe odreda, i borci štaba i brigada divizije, s podacima o svakom.',
    image: '/images/32-zagorska-divizija.jpg',
    soldierCount: 17659,
    dataFile: '/32-divizija-soldiers.json',
    pdfFiles: ['/pdfs/32-divizija.pdf', '/pdfs/32-divizija-borci.pdf']
  },
  {
    id: '1-dalmatinska-brigada',
    name: '1. dalmatinska proleterska brigada',
    nameEn: '1st Dalmatian Proletarian Brigade',
    description: 'Formirana 6. septembra 1942. u selu Dobro kod Livna. Borci poginuli u ratu. Spisak postoji samo kao tekst na znaci.org, bez skenirane knjige.',
    image: '/images/1-dalmatinska-brigada.jpg',
    soldierCount: 2980,
    dataFile: '/1-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-1-dalmatinska.pdf']
  },
  {
    id: '16-slavonska-omladinska-brigada',
    name: '16. slavonska omladinska brigada „Jože Vlahović“',
    nameEn: '16th Slavonian Youth Brigade "Jože Vlahović"',
    description: 'Formirana 29. decembra 1942. u Gornjim Borkima kod Daruvara. Poginuli borci i starešine, poginuli u Pokuplju i na Žumberku, i rukovodioci brigade od formiranja do kraja rata.',
    image: '/images/16-slavonska-omladinska-brigada.jpg',
    soldierCount: 1122,
    dataFile: '/16-slavonska-omladinska-soldiers.json',
    pdfFiles: ['/pdfs/16-slavonska-omladinska.pdf']
  },
  {
    id: '8-crnogorska-brigada',
    name: '8. crnogorska brigada',
    nameEn: '8th Montenegrin Brigade',
    description: 'Formirana 25. februara 1944. u Beranama. Poginuli borci i starešine, i dopunski spisak poginulih iz Uba.',
    image: '/images/8-crnogorska-brigada.jpg',
    soldierCount: 747,
    dataFile: '/8-crnogorska-soldiers.json',
    pdfFiles: ['/pdfs/8-crnogorska.pdf']
  },
  {
    id: 'druga-proleterska-brigada',
    name: 'Druga proleterska brigada',
    nameEn: '2nd Proletarian Brigade',
    description: 'Formirana 1. marta 1942. u Čajniču. Poginuli, umrli i nestali borci, po mestu i danu pogibije, od Sutjeske do Sremskog fronta.',
    image: '/images/druga-proleterska-brigada.jpg',
    soldierCount: 2216,
    dataFile: '/druga-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/druga-proleterska.pdf', '/pdfs/borci-sutjeske-druga-proleterska.pdf']
  },
  {
    id: '4-proleterska-brigada',
    name: '4. proleterska crnogorska brigada',
    nameEn: '4th Proletarian Montenegrin Brigade',
    description: 'Formirana 10. juna 1942. Borci brigade u bici na Sutjesci, i borci i starešine poginuli od 1942. do 1945.',
    image: '/images/4-proleterska-brigada.jpg',
    soldierCount: 3496,
    dataFile: '/4-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-4-proleterska.pdf', '/pdfs/4-proleterska-poginuli.pdf']
  },
  {
    id: '5-proleterska-brigada',
    name: '5. proleterska crnogorska brigada',
    nameEn: '5th Proletarian Montenegrin Brigade',
    description: 'Formirana 12. juna 1942. u Smriječnu kod Šavnika. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/5-proleterska-brigada.jpg',
    soldierCount: 1574,
    dataFile: '/5-proleterska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-5-proleterska.pdf']
  },
  {
    id: '6-istocnobosanska-brigada',
    name: '6. istočnobosanska proleterska brigada',
    nameEn: '6th East Bosnian Proletarian Brigade',
    description: 'Formirana 2. avgusta 1942. u Šekovićima kod Vlasenice. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/6-istocnobosanska-brigada.jpg',
    soldierCount: 807,
    dataFile: '/6-istocnobosanska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-6-istocnobosanska.pdf']
  },
  {
    id: '10-hercegovacka-brigada',
    name: '10. hercegovačka brigada',
    nameEn: '10th Herzegovina Brigade',
    description: 'Formirana 10. avgusta 1942. kod Kupresa. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/10-hercegovacka-brigada.jpg',
    soldierCount: 1478,
    dataFile: '/10-hercegovacka-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-10-hercegovacka.pdf']
  },
  {
    id: '7-banijska-brigada',
    name: '7. banijska brigada „Vasilj Gaćeša“',
    nameEn: '7th Banija Brigade "Vasilj Gaćeša"',
    description: 'Formirana 2. septembra 1942. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/7-banijska-brigada.jpg',
    soldierCount: 890,
    dataFile: '/7-banijska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-7-banijska.pdf']
  },
  {
    id: '8-banijska-brigada',
    name: '8. banijska brigada',
    nameEn: '8th Banija Brigade',
    description: 'Formirana 7. septembra 1942. u Obljaju kod Gline. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/8-banijska-brigada.jpg',
    soldierCount: 834,
    dataFile: '/8-banijska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-8-banijska.pdf']
  },
  {
    id: '3-dalmatinska-brigada',
    name: '3. dalmatinska brigada',
    nameEn: '3rd Dalmatian Brigade',
    description: 'Formirana 12. novembra 1942. u Vrbi kod Sinja. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/3-dalmatinska-brigada.jpg',
    soldierCount: 1322,
    dataFile: '/3-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-3-dalmatinska.pdf']
  },
  {
    id: '16-banijska-brigada',
    name: '16. banijska brigada',
    nameEn: '16th Banija Brigade',
    description: 'Formirana 26. decembra 1942. u Klasniću. Borci brigade u bici na Sutjesci, maja i juna 1943.',
    image: '/images/pdf-thumbs/borci-sutjeske-16-banijska.jpg',
    soldierCount: 591,
    dataFile: '/16-banijska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-16-banijska.pdf']
  },
  {
    id: '7-krajiska-brigada',
    name: '7. krajiška brigada',
    nameEn: '7th Krajina Brigade',
    description: 'Formirana 27. decembra 1942. u Orahovljanima kod Ključa. Preživeli i poginuli borci i starešine, od formiranja do kraja rata.',
    image: '/images/7-krajiska-brigada.jpg',
    soldierCount: 4336,
    dataFile: '/7-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-7-krajiska.pdf', '/pdfs/7-krajiska-spisak.pdf']
  },
  {
    id: '15-majevicka-brigada',
    name: '15. majevička brigada',
    nameEn: '15th Majevica Brigade',
    description: 'Formirana 11. aprila 1943. Borci brigade, tada 1. majevičke, u bici na Sutjesci, maja i juna 1943.',
    image: '/images/15-majevicka-brigada.jpg',
    soldierCount: 510,
    dataFile: '/15-majevicka-soldiers.json',
    pdfFiles: ['/pdfs/borci-sutjeske-15-majevicka.pdf']
  },
  {
    id: '12-dalmatinska-brigada',
    name: '12. dalmatinska (1. otočka) brigada',
    nameEn: '12th Dalmatian (1st Island) Brigade',
    description: 'Formirana 15. septembra 1943. na ostrvima Braču, Hvaru, Visu i Šolti. Poginuli borci i starešine, po borbama u kojima su pali.',
    image: '/images/12-dalmatinska-brigada.jpg',
    soldierCount: 361,
    dataFile: '/12-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/12-dalmatinska.pdf']
  },
  {
    id: '3-makedonska-brigada',
    name: '3. makedonska brigada',
    nameEn: '3rd Macedonian Brigade',
    description: 'Formirana 26. februara 1944. u selu Žegljane kod Kumanova. Poginuli borci.',
    image: '/images/3-makedonska-brigada.jpg',
    soldierCount: 232,
    dataFile: '/3-makedonska-soldiers.json',
    pdfFiles: ['/pdfs/3-makedonska.pdf']
  },
  {
    id: '18-hrvatska-brigada',
    name: '18. hrvatska istočnobosanska brigada',
    nameEn: '18th Croatian East Bosnian Brigade',
    description: 'Formirana 10. oktobra 1943. kod Tuzle, a proglašena 17. oktobra u Husinu. Borci brigade.',
    image: '/images/18-hrvatska-brigada.jpg',
    soldierCount: 1738,
    dataFile: '/18-hrvatska-soldiers.json',
    pdfFiles: ['/pdfs/18-hrvatska.pdf']
  },
  {
    id: '11-dalmatinska-brigada',
    name: '11. dalmatinska brigada',
    nameEn: '11th Dalmatian Brigade',
    description: 'Formirana 2. oktobra 1943. na Biokovu. Poginuli, nestali i preživeli borci.',
    image: '/images/11-dalmatinska-brigada.jpg',
    soldierCount: 3444,
    dataFile: '/11-dalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/11-dalmatinska.pdf']
  },
  {
    id: '12-krajiska-brigada',
    name: '12. krajiška brigada',
    nameEn: '12th Krajina Brigade',
    description: 'Formirana 19. februara 1943. u Driniću. Poginuli i preživeli borci i starešine.',
    image: '/images/12-krajiska-brigada.jpg',
    soldierCount: 3855,
    dataFile: '/12-krajiska-soldiers.json',
    pdfFiles: ['/pdfs/12-krajiska-poginuli.pdf', '/pdfs/12-krajiska-prezivjeli.pdf']
  },
  {
    id: '17-srpska-brigada',
    name: '17. srpska brigada',
    nameEn: '17th Serbian Brigade',
    description: 'Formirana 2. juna 1944. u Mehanama kod Kuršumlije. Preživeli i poginuli borci.',
    image: '/images/17-srpska-brigada.jpg',
    soldierCount: 989,
    dataFile: '/17-srpska-soldiers.json',
    pdfFiles: ['/pdfs/17-srpska.pdf']
  },
  {
    id: '14-srednjobosanska-brigada',
    name: '14. srednjobosanska brigada',
    nameEn: '14th Central Bosnian Brigade',
    description: 'Formirana 17. oktobra 1943. na Ceru kod Prnjavora. Poginuli, umrli i nestali borci, i borci koji su preživeli rat.',
    image: '/images/14-srednjobosanska-brigada.jpg',
    soldierCount: 2559,
    dataFile: '/14-srednjobosanska-soldiers.json',
    pdfFiles: ['/pdfs/14-srednjobosanska.pdf']
  },
  {
    id: '3-vojvodjanska-brigada',
    name: '3. vojvođanska brigada',
    nameEn: '3rd Vojvodina Brigade',
    description: 'Formirana 15. maja 1943. u Sremu. Poginuli borci i starešine, oni čija je sudbina ostala neutvrđena, i preživeli.',
    image: '/images/3-vojvodjanska-brigada.jpg',
    soldierCount: 4092,
    dataFile: '/3-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/3-vojvodjanska.pdf']
  },
  {
    id: 'kalnicki-odred',
    name: 'Kalnički partizanski odred',
    nameEn: 'Kalnik Partisan Detachment',
    description: 'Formiran 10. oktobra 1942. u Bijeloj kod Daruvara. Borci odreda, poginuli i preživeli.',
    image: '/images/kalnicki-odred.jpg',
    soldierCount: 3273,
    dataFile: '/kalnicki-odred-soldiers.json',
    pdfFiles: ['/pdfs/kalnicki-odred.pdf']
  },
  {
    id: 'posavsko-trebavski-odred',
    name: 'Posavsko-trebavski partizanski odred',
    nameEn: 'Posavina-Trebava Partisan Detachment',
    description: 'Formiran 4. februara 1944. kod Gradačca, od Posavskog i Trebavskog odreda. Borci odreda.',
    image: '/images/pdf-thumbs/posavsko-trebavski-odred.jpg',
    soldierCount: 1969,
    dataFile: '/posavsko-trebavski-odred-soldiers.json',
    pdfFiles: ['/pdfs/posavsko-trebavski-odred.pdf']
  },
  {
    id: '8-kordunaska-divizija',
    name: '8. kordunaška divizija',
    nameEn: '8th Kordun Division',
    description: 'Formirana 22. novembra 1942. u Crevarskoj Strani na Petrovoj gori. Poginuli borci divizije.',
    image: '/images/8-kordunaska-divizija.jpg',
    soldierCount: 2674,
    dataFile: '/8-kordunaska-divizija-soldiers.json',
    pdfFiles: ['/pdfs/8-kordunaska-divizija.pdf']
  },
  {
    id: 'cankarjeva-brigada',
    name: 'Cankarjeva brigada',
    nameEn: 'Cankar Brigade',
    description: 'Formirana 28. septembra 1942. kod Lapinja na Kočevskom. Poginuli i preživeli borci.',
    image: '/images/cankarjeva-brigada.jpg',
    soldierCount: 2896,
    dataFile: '/cankarjeva-soldiers.json',
    pdfFiles: ['/pdfs/cankarjeva.pdf']
  },
  {
    id: 'gubceva-brigada',
    name: 'Gubčeva brigada',
    nameEn: 'Gubec Brigade',
    description: 'Formirana 4. septembra 1942. kod Trebelnog iznad Mokronoga. Poginuli i preživeli borci.',
    image: '/images/gubceva-brigada.jpg',
    soldierCount: 2995,
    dataFile: '/gubceva-soldiers.json',
    pdfFiles: ['/pdfs/gubceva.pdf']
  },
  {
    id: 'dvanajsta-brigada',
    name: '12. slovenačka brigada',
    nameEn: '12th Slovene Brigade',
    description: 'Formirana 24. septembra 1943. u Mokronogu. Poginuli i preživeli borci.',
    image: '/images/dvanajsta-brigada.jpg',
    soldierCount: 1662,
    dataFile: '/dvanajsta-soldiers.json',
    pdfFiles: ['/pdfs/dvanajsta.pdf']
  },
  {
    id: 'gradnikova-brigada',
    name: 'Gradnikova brigada',
    nameEn: 'Gradnik Brigade',
    description: 'Formirana u aprilu 1943. na Golobaru kod Bovca. Poginuli borci i ostali borci brigade.',
    image: '/images/gradnikova-brigada.jpg',
    soldierCount: 3661,
    dataFile: '/gradnikova-soldiers.json',
    pdfFiles: ['/pdfs/gradnikova.pdf']
  },
  {
    id: 'zidanskova-brigada',
    name: 'Zidanškova brigada',
    nameEn: 'Zidanšek Brigade',
    description: 'Formirana 8. januara 1944. kod Svetog Primoža na Pohorju. Borci brigade, poginuli i preživeli.',
    image: '/images/zidanskova-brigada.jpg',
    soldierCount: 1151,
    dataFile: '/zidanskova-soldiers.json',
    pdfFiles: ['/pdfs/zidanskova.pdf']
  },
  {
    id: 'skofjeloski-odred',
    name: 'Škofjeloški odred',
    nameEn: 'Škofja Loka Detachment',
    description: 'Formiran po naredbi od 30. jula 1944, u brdima oko Škofje Loke. Imena boraca odreda.',
    image: '/images/skofjeloski-odred.jpg',
    soldierCount: 517,
    dataFile: '/skofjeloski-odred-soldiers.json',
    pdfFiles: ['/pdfs/skofjeloski-odred.pdf']
  },
  {
    id: 'istrski-odred',
    name: 'Istarski odred',
    nameEn: 'Istrian Detachment',
    description: 'Formiran 7. oktobra 1943. u Brkinima. Poginuli i ostali borci odreda.',
    image: '/images/istrski-odred.jpg',
    soldierCount: 1280,
    dataFile: '/istrski-odred-soldiers.json',
    pdfFiles: ['/pdfs/istrski-odred.pdf']
  },
  {
    id: 'zapadnodolenjski-odred',
    name: 'Zapadnodolenjski odred',
    nameEn: 'West Lower Carniola Detachment',
    description: 'Formiran krajem juna 1942. na Dolenjskom. Poginuli i ostali borci odreda.',
    image: '/images/zapadnodolenjski-odred.jpg',
    soldierCount: 831,
    dataFile: '/zapadnodolenjski-odred-soldiers.json',
    pdfFiles: ['/pdfs/zapadnodolenjski-odred.pdf']
  },
  {
    id: 'braciceva-brigada',
    name: 'Bračičeva brigada',
    nameEn: 'Bračič Brigade',
    description: 'Formirana 23. septembra 1943. u Kneževoj Njivi u Loškoj dolini. Poginuli i preživeli borci.',
    image: '/images/braciceva-brigada.jpg',
    soldierCount: 2216,
    dataFile: '/braciceva-soldiers.json',
    pdfFiles: ['/pdfs/braciceva.pdf']
  },
  {
    id: 'tomsiceva-brigada',
    name: 'Tomšičeva brigada',
    nameEn: 'Tomšič Brigade',
    description: 'Formirana 16. jula 1942. na Cesti na Kočevskom. Borci brigade od formiranja do kraja rata.',
    image: '/images/tomsiceva-brigada.jpg',
    soldierCount: 5921,
    dataFile: '/tomsiceva-soldiers.json',
    pdfFiles: ['/pdfs/tomsiceva-2.pdf', '/pdfs/tomsiceva-3.pdf', '/pdfs/tomsiceva-4.pdf']
  },
  {
    id: '1-slovenska-artilerijska-brigada',
    name: '1. slovenačka artiljerijska brigada',
    nameEn: '1st Slovene Artillery Brigade',
    description: 'Formirana 6. maja 1944. u Laščama kod Dvora. Artiljerci brigade i poginuli borci.',
    image: '/images/1-slovenska-artilerijska-brigada.jpg',
    soldierCount: 763,
    dataFile: '/1-slovenska-artilerijska-soldiers.json',
    pdfFiles: ['/pdfs/1-slovenska-artilerijska.pdf']
  },
  {
    id: 'artilerija-9-korpusa',
    name: 'Artiljerija 9. korpusa',
    nameEn: '9th Corps Artillery',
    description: 'Formirana 14. juna 1944. u Gornjem Lokovcu. Borci artiljerije i poginuli.',
    image: '/images/artilerija-9-korpusa.jpg',
    soldierCount: 414,
    dataFile: '/artilerija-9-korpusa-soldiers.json',
    pdfFiles: ['/pdfs/artilerija-9-korpusa.pdf']
  },
  {
    id: '19-srpska-brigada',
    name: '19. srpska brigada',
    nameEn: '19th Serbian Brigade',
    description: 'Formirana 12. juna 1944. u Gornjoj Jošanici. Poginuli, nestali i umrli borci i oni koji su preživeli rat.',
    image: '/images/19-srpska-brigada.jpg',
    soldierCount: 3557,
    dataFile: '/19-srpska-soldiers.json',
    pdfFiles: ['/pdfs/19-srpska.pdf']
  },
  {
    id: '22-srpska-brigada',
    name: '22. srpska kosmajska brigada',
    nameEn: '22nd Serbian (Kosmaj) Brigade',
    description: 'Formirana 12. septembra 1944. na Brdnjaku kod Drugovca. Poginuli i preživeli borci i starešine.',
    image: '/images/22-srpska-brigada.jpg',
    soldierCount: 1300,
    dataFile: '/22-srpska-soldiers.json',
    pdfFiles: ['/pdfs/22-srpska.pdf']
  },
  {
    id: '12-vojvodjanska-brigada',
    name: '12. vojvođanska brigada',
    nameEn: '12th Vojvodina Brigade',
    description: 'Formirana 8. oktobra 1944. u Vojlovici kod Pančeva. Borci brigade, po mestima u kojima su živeli, i poginuli.',
    image: '/images/12-vojvodjanska-brigada.jpg',
    soldierCount: 2540,
    dataFile: '/12-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/12-vojvodjanska.pdf']
  },
  {
    id: '4-vojvodjanska-brigada',
    name: '4. vojvođanska brigada',
    nameEn: '4th Vojvodina Brigade',
    description: 'Formirana 7. oktobra 1943. u šumi Varadin kod Višnjićeva. Borci prvog sastava brigade i poginuli.',
    image: '/images/4-vojvodjanska-brigada.jpg',
    soldierCount: 1241,
    dataFile: '/4-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/4-vojvodjanska.pdf']
  },
  {
    id: '1-kosovsko-metohijska-brigada',
    name: '1. kosovsko-metohijska brigada',
    nameEn: '1st Kosovo-Metohija Brigade',
    description: 'Formirana 24. juna 1944. u selu Zbaždi u zapadnoj Makedoniji. Borci brigade, poginuli i ranjeni.',
    image: '/images/1-kosovsko-metohijska-brigada.jpg',
    soldierCount: 1074,
    dataFile: '/1-kosovsko-metohijska-soldiers.json',
    pdfFiles: ['/pdfs/1-kosovsko-metohijska.pdf']
  },
  {
    id: '8-vojvodjanska-brigada',
    name: '8. vojvođanska brigada',
    nameEn: '8th Vojvodina Brigade',
    description: 'Formirana 12. septembra 1944. na proplanku Jabuka na Fruškoj gori. Poginuli i nestali borci i starešine.',
    image: '/images/8-vojvodjanska-brigada.jpg',
    soldierCount: 1113,
    dataFile: '/8-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/8-vojvodjanska.pdf']
  },
  {
    id: '19-sjevernodalmatinska-divizija',
    name: '19. severnodalmatinska divizija',
    nameEn: '19th North Dalmatian Division',
    description: 'Formirana 11. oktobra 1943. u Biovičinom Selu u Bukovici. Poginuli i umrli borci divizije.',
    image: '/images/19-sjevernodalmatinska-divizija.jpg',
    soldierCount: 1418,
    dataFile: '/19-sjevernodalmatinska-soldiers.json',
    pdfFiles: ['/pdfs/19-sjevernodalmatinska.pdf']
  },
  {
    id: '21-srpska-brigada',
    name: '21. srpska brigada',
    nameEn: '21st Serbian Brigade',
    description: 'Formirana 10. maja 1944. u Trebežu kod Darosave. Poginuli i preživeli borci i drugi koji su se borili u brigadi.',
    image: '/images/21-srpska-brigada.jpg',
    soldierCount: 1422,
    dataFile: '/21-srpska-soldiers.json',
    pdfFiles: ['/pdfs/21-srpska.pdf']
  },
  {
    id: '14-hercegovacka-brigada',
    name: '14. hercegovačka brigada',
    nameEn: '14th Herzegovina Brigade',
    description: 'Formirana 4. septembra 1944. kod Ljubinja, kao omladinska brigada. Svi borci koji su prošli kroz brigadu i poginuli.',
    image: '/images/14-hercegovacka-brigada.jpg',
    soldierCount: 1296,
    dataFile: '/14-hercegovacka-soldiers.json',
    pdfFiles: ['/pdfs/14-hercegovacka.pdf']
  },
  {
    id: '5-vojvodjanska-brigada',
    name: '5. vojvođanska brigada',
    nameEn: '5th Vojvodina Brigade',
    description: 'Formirana 15. novembra 1943. u Obršinama na Majevici. Borci i starešine brigade.',
    image: '/images/5-vojvodjanska-brigada.jpg',
    soldierCount: 4262,
    dataFile: '/5-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/5-vojvodjanska.pdf']
  },
  {
    id: '6-vojvodjanska-brigada',
    name: '6. vojvođanska brigada',
    nameEn: '6th Vojvodina Brigade',
    description: 'Formirana 17. januara 1944. na Jabučju kod Sremske Rače. Poginuli borci i rukovodioci brigade.',
    image: '/images/6-vojvodjanska-brigada.jpg',
    soldierCount: 347,
    dataFile: '/6-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/6-vojvodjanska.pdf']
  },
  {
    id: '13-vojvodjanska-brigada',
    name: '13. vojvođanska brigada',
    nameEn: '13th Vojvodina Brigade',
    description: 'Formirana 14. oktobra 1944. u Kikindi. Borci brigade, poimence.',
    image: '/images/13-vojvodjanska-brigada.jpg',
    soldierCount: 2750,
    dataFile: '/13-vojvodjanska-soldiers.json',
    pdfFiles: ['/pdfs/13-vojvodjanska.pdf']
  },
  {
    id: '7-srpska-brigada',
    name: '7. srpska brigada',
    nameEn: '7th Serbian Brigade',
    description: 'Formirana 4. februara 1944. u Jabukoviku kod Crne Trave, kao 5. južnomoravska. Borci u maju 1944. i poginuli, umrli i nestali.',
    image: '/images/7-srpska-brigada.jpg',
    soldierCount: 1188,
    dataFile: '/7-srpska-soldiers.json',
    pdfFiles: ['/pdfs/7-srpska.pdf']
  },
  {
    id: '15-srpska-brigada',
    name: '15. srpska brigada',
    nameEn: '15th Serbian Brigade',
    description: 'Formirana 2. juna 1944. u Retkoceru, u Gornjoj Jablanici. Borci i rukovodioci brigade, poginuli i ranjeni.',
    image: '/images/15-srpska-brigada.jpg',
    soldierCount: 902,
    dataFile: '/15-srpska-soldiers.json',
    pdfFiles: ['/pdfs/15-srpska.pdf']
  },
  {
    id: '8-srpska-brigada',
    name: '8. srpska brigada',
    nameEn: '8th Serbian Brigade',
    description: 'Formirana 8. marta 1944. u Trgovištu, kao 6. južnomoravska. Poginuli borci brigade.',
    image: '/images/8-srpska-brigada.jpg',
    soldierCount: 563,
    dataFile: '/8-srpska-soldiers.json',
    pdfFiles: ['/pdfs/8-srpska.pdf']
  },
  {
    id: '10-srpska-brigada',
    name: '10. srpska brigada',
    nameEn: '10th Serbian Brigade',
    description: 'Formirana 8. maja 1944. u Jabukoviku kod Crne Trave. Poginuli, umrli i nestali borci i rukovodioci brigade.',
    image: '/images/10-srpska-brigada.jpg',
    soldierCount: 376,
    dataFile: '/10-srpska-soldiers.json',
    pdfFiles: ['/pdfs/10-srpska.pdf']
  },
  {
    id: '23-srpska-brigada',
    name: '23. srpska brigada',
    nameEn: '23rd Serbian Brigade',
    description: 'Formirana 2. septembra 1944. u Šuman Topli kod Knjaževca. Poginuli i umrli borci i rukovodioci brigade.',
    image: '/images/23-srpska-brigada.jpg',
    soldierCount: 467,
    dataFile: '/23-srpska-soldiers.json',
    pdfFiles: ['/pdfs/23-srpska.pdf']
  },
  {
    id: '12-srpska-brigada',
    name: '12. srpska brigada',
    nameEn: '12th Serbian Brigade',
    description: 'Formirana 22. maja 1944. na Ostrozubu, južno od Bistrice. Poginuli i umrli borci i rukovodioci brigade.',
    image: '/images/12-srpska-brigada.jpg',
    soldierCount: 425,
    dataFile: '/12-srpska-soldiers.json',
    pdfFiles: ['/pdfs/12-srpska.pdf']
  },
  {
    id: '20-srpska-brigada',
    name: '20. srpska brigada',
    nameEn: '20th Serbian Brigade',
    description: 'Formirana 19. avgusta 1944. iznad sela Bučja kod Knjaževca. Poginuli i umrli borci i rukovodioci brigade.',
    image: '/images/20-srpska-brigada.jpg',
    soldierCount: 600,
    dataFile: '/20-srpska-soldiers.json',
    pdfFiles: ['/pdfs/20-srpska.pdf']
  },
  {
    id: '1-konjicka-brigada',
    name: '1. konjička brigada',
    nameEn: '1st Cavalry Brigade',
    description: 'Formirana 15. septembra 1944. u Slavkovici kod Ljiga. Ratni spisak starešina i boraca brigade i poginuli.',
    image: '/images/1-konjicka-brigada.jpg',
    soldierCount: 531,
    dataFile: '/1-konjicka-soldiers.json',
    pdfFiles: ['/pdfs/1-konjicka.pdf']
  },
  {
    id: 'toplicki-odred',
    name: 'Toplički NOP odred',
    nameEn: 'Toplica Partisan Detachment',
    description: 'Formiran 3. avgusta 1941. u Ajdanovcu kod Prokuplja. Borci na dan formiranja, poginuli i umrli, narodni heroji odreda.',
    image: '/images/toplicki-odred.jpg',
    soldierCount: 277,
    dataFile: '/toplicki-odred-soldiers.json',
    pdfFiles: ['/pdfs/toplicki-odred.pdf']
  },
  {
    id: 'karlovacka-brigada',
    name: 'Karlovačka udarna brigada',
    nameEn: 'Karlovac Assault Brigade',
    description: 'Formirana 5. marta 1944. u Hrašću kod Ozlja. Borci brigade na dan formiranja i poginuli.',
    image: '/images/karlovacka-brigada.jpg',
    soldierCount: 842,
    dataFile: '/karlovacka-soldiers.json',
    pdfFiles: ['/pdfs/karlovacka.pdf']
  },
  {
    id: '14-primorsko-goranska',
    name: '14. primorsko-goranska brigada',
    nameEn: '14th Primorje–Gorski Kotar Brigade',
    description: 'Formirana 26. novembra 1942. u Drežnici. Poginuli borci brigade.',
    image: '/images/14-primorsko-goranska.jpg',
    soldierCount: 679,
    dataFile: '/14-primorsko-goranska-soldiers.json',
    pdfFiles: ['/pdfs/14-primorsko-goranska.pdf']
  },
  {
    id: '22-divizija',
    name: '22. divizija',
    nameEn: '22nd Division',
    description: 'Formirana maja 1944. na desnoj obali Južne Morave. Poginuli borci 8., 10. i 12. srpske brigade.',
    image: '/images/22-divizija.jpg',
    soldierCount: 1005,
    dataFile: '/22-divizija-soldiers.json',
    pdfFiles: ['/pdfs/22-divizija.pdf']
  },
  {
    id: '34-divizija',
    name: '34. divizija',
    nameEn: '34th Division',
    description: 'Formirana 30. januara 1944. na Žumberku i u Pokuplju. Poginuli borci i rukovodioci divizije i njenih brigada.',
    image: '/images/34-divizija.jpg',
    soldierCount: 1415,
    dataFile: '/34-divizija-soldiers.json',
    pdfFiles: ['/pdfs/34-divizija.pdf']
  },
  {
    id: '4-sandzacka-brigada',
    name: '4. sandžačka brigada',
    nameEn: '4th Sandžak Brigade',
    description: 'Formirana 1. decembra 1943. u Pljevljima. Poginuli i ranjeni borci brigade.',
    image: '/images/4-sandzacka-brigada.jpg',
    soldierCount: 785,
    dataFile: '/4-sandzacka-soldiers.json',
    pdfFiles: ['/pdfs/4-sandzacka.pdf']
  },
  {
    id: '3-primorsko-goranska',
    name: '3. primorsko-goranska brigada',
    nameEn: '3rd Primorje–Gorski Kotar Brigade',
    description: 'Formirana 15. septembra 1943. u Škrljevu u Hrvatskom primorju. Starešine i četni bolničari brigade i poginuli.',
    image: '/images/pdf-thumbs/3-primorsko-goranska.jpg',
    soldierCount: 804,
    dataFile: '/3-primorsko-goranska-soldiers.json',
    pdfFiles: ['/pdfs/3-primorsko-goranska.pdf']
  },
  {
    id: '13-hercegovacka-brigada',
    name: '13. hercegovačka brigada',
    nameEn: '13th Herzegovina Brigade',
    description: 'Formirana 14. maja 1944. u Hercegovini. Poginuli borci i starešine brigade i svi koji su se borili u njoj.',
    image: '/images/13-hercegovacka-brigada.jpg',
    soldierCount: 2043,
    dataFile: '/13-hercegovacka-soldiers.json',
    pdfFiles: ['/pdfs/13-hercegovacka.pdf']
  },
  {
    id: '12-hercegovacka-brigada',
    name: '12. hercegovačka brigada',
    nameEn: '12th Herzegovina Brigade',
    description: 'Formirana 16. novembra 1943. u Hercegovini, od grupa bataljona 10. hercegovačke. Poginuli borci i starešine brigade.',
    image: '/images/12-hercegovacka-brigada.jpg',
    soldierCount: 278,
    dataFile: '/12-hercegovacka-soldiers.json',
    pdfFiles: ['/pdfs/12-hercegovacka.pdf']
  },
  {
    id: '1-bokeljska-brigada',
    name: '1. bokeljska brigada',
    nameEn: '1st Boka Brigade',
    description: 'Formirana 5. oktobra 1944. u Konjskom kod Trebinja. Poginuli, umrli i nestali borci brigade.',
    image: '/images/1-bokeljska-brigada.jpg',
    soldierCount: 201,
    dataFile: '/1-bokeljska-soldiers.json',
    pdfFiles: ['/pdfs/1-bokeljska.pdf']
  }
  // Add more units here as you get more data
]
