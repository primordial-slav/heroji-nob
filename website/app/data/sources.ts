export interface PdfSource {
  id: string
  title: string
  author: string
  pdfPath: string
  thumbnail: string
  brigadeName: string
  description?: string
}

export const sources: PdfSource[] = [
  {
    id: 'prva-licka-proleterska',
    title: 'Prva lička proleterska brigada',
    author: 'Rajko Šarenac (ur.)',
    pdfPath: '/pdfs/prva-licka-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/prva-licka-proleterska.jpg',
    brigadeName: 'Prva lička proleterska brigada "Marko Orešković"',
    description: 'Monografija, Biblioteka Ratna prošlost naroda i narodnosti Jugoslavije, knj. 322'
  },
  {
    id: 'prva-proleterska-1',
    title: 'Prva proleterska brigada — tom 1',
    author: 'Veljko Miladinović (ur.)',
    pdfPath: '/pdfs/prva-proleterska-1.pdf',
    thumbnail: '/images/pdf-thumbs/prva-proleterska-1.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Spisak boraca — prvi tom (A–I)'
  },
  {
    id: 'prva-proleterska-2',
    title: 'Prva proleterska brigada — tom 2',
    author: 'Veljko Miladinović (ur.)',
    pdfPath: '/pdfs/prva-proleterska-2.pdf',
    thumbnail: '/images/pdf-thumbs/prva-proleterska-2.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Spisak boraca — drugi tom (I–O)'
  },
  {
    id: 'prva-proleterska-3',
    title: 'Prva proleterska brigada — tom 3',
    author: 'Veljko Miladinović (ur.)',
    pdfPath: '/pdfs/prva-proleterska-3.pdf',
    thumbnail: '/images/pdf-thumbs/prva-proleterska-3.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Spisak boraca — treći tom (O–Ž)'
  },
  {
    id: 'druga-licka-spisak',
    title: 'Druga lička proleterska brigada — spisak poginulih',
    author: 'Vojnoistorijski institut',
    pdfPath: '/pdfs/druga-licka-spisak.pdf',
    thumbnail: '/images/pdf-thumbs/druga-licka-spisak.jpg',
    brigadeName: 'Druga lička proleterska brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca i starešina brigade'
  },
  {
    id: 'druga-licka-sjecanja-prezivjeli',
    title: 'Druga lička proleterska brigada — spisak preživjelih',
    author: 'Đuro Mileusnić',
    pdfPath: '/pdfs/druga-licka-sjecanja-prezivjeli.pdf',
    thumbnail: '/images/pdf-thumbs/druga-licka-sjecanja-prezivjeli.jpg',
    brigadeName: 'Druga lička proleterska brigada',
    description: 'Spisak preživjelih boraca i starješina Druge ličke proleterske brigade (iz zbornika sjećanja)'
  },
  {
    id: 'druga-licka-sjecanja-poginuli',
    title: 'Druga lička proleterska brigada — spisak poginulih (zbornik sjećanja)',
    author: 'Đuro Mileusnić',
    pdfPath: '/pdfs/druga-licka-sjecanja-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/druga-licka-sjecanja-poginuli.jpg',
    brigadeName: 'Druga lička proleterska brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca Druge ličke proleterske brigade (iz zbornika sjećanja); većina je i na spisku Vojnoistorijskog instituta'
  },
  {
    id: 'treca-proleterska-brigada',
    title: 'Treća proleterska (sandžačka) brigada',
    author: 'Žarko Vidović',
    pdfPath: '/pdfs/treca-proleterska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/treca-proleterska-brigada.jpg',
    brigadeName: 'Treća proleterska (sandžačka) brigada',
    description: 'Monografija, Biblioteka Ratna prošlost naših naroda, knj. 144'
  },
  {
    id: 'treca-proleterska-poginuli-knj3',
    title: 'Treća proleterska (sandžačka) brigada — spisak poginulih i umrlih (zbornik sjećanja, knj. 3)',
    author: 'Šućro Hadžismajlović',
    pdfPath: '/pdfs/treca-proleterska-poginuli-knj3.pdf',
    thumbnail: '/images/pdf-thumbs/treca-proleterska-poginuli-knj3.jpg',
    brigadeName: 'Treća proleterska (sandžačka) brigada',
    description: 'Spisak poginulih i umrlih boraca i starješina po godinama, 1942-1945 (1.374 imena; u ovom primjerku nedostaju strane s početkom 1944. godine)'
  },
  {
    id: 'treca-proleterska-formiranje',
    title: 'Treća proleterska (sandžačka) brigada — spisak boraca i starešina na dan formiranja (zbornik sjećanja)',
    author: 'Čedomir Drulović i dr. (ur.)',
    pdfPath: '/pdfs/treca-proleterska-formiranje.pdf',
    thumbnail: '/images/pdf-thumbs/treca-proleterska-formiranje.jpg',
    brigadeName: 'Treća proleterska (sandžačka) brigada',
    description: 'Isti spisak kao u monografiji Žarka Vidovića, ćirilicom, kako ga je sredila redakcija zbornika sjećanja; po bataljonima i četama'
  },
  {
    id: 'ljubljanska-brigada',
    title: '10. slovenska NOV brigada „Ljubljanska"',
    author: 'Borivoj Lah – Boris',
    pdfPath: '/pdfs/ljubljanska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/ljubljanska-brigada.jpg',
    brigadeName: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    description: 'Monografija Ljubljanske brigade'
  },
  {
    id: '13-proleterska-spisak',
    title: 'Trinaesta proleterska brigada „Rade Končar"',
    author: 'Todor Radošević (ur.)',
    pdfPath: '/pdfs/13-proleterska-spisak.pdf',
    thumbnail: '/images/pdf-thumbs/13-proleterska-spisak.jpg',
    brigadeName: '13. proleterska udarna brigada "Rade Končar"',
    description: 'Spisak palih i preživjelih boraca (treći dio monografije)'
  },
  {
    id: '2-dalmatinska-proleterska',
    title: '2. dalmatinska proleterska udarna brigada',
    author: 'Nikola Anić',
    pdfPath: '/pdfs/2-dalmatinska-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/2-dalmatinska-proleterska.jpg',
    brigadeName: '2. dalmatinska proleterska udarna brigada',
    description: 'Popis boraca 2. dalmatinske proleterske brigade NOVJ'
  },
  {
    id: '4-splitska-brigada',
    title: '4. splitska udarna brigada',
    author: 'Vinko Uvodić (ur.)',
    pdfPath: '/pdfs/4-splitska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/4-splitska-brigada.jpg',
    brigadeName: '4. splitska udarna brigada',
    description: 'Popis poginulih i preživjelih boraca brigade'
  },
  {
    id: 'prva-vojvodjanska',
    title: 'Prva vojvođanska brigada',
    author: 'Vojnoistorijski institut',
    pdfPath: '/pdfs/prva-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/prva-vojvodjanska.jpg',
    brigadeName: 'Prva vojvođanska brigada',
    description: 'Spisak boraca Prve vojvođanske brigade'
  },
  {
    id: '5-kozaracka',
    title: 'Peta kozaračka brigada',
    author: 'Lj. Borojević, D. Samardžija, R. Bašić',
    pdfPath: '/pdfs/5-kozaracka.pdf',
    thumbnail: '/images/pdf-thumbs/5-kozaracka.jpg',
    brigadeName: '5. krajiška (kozaračka) udarna brigada',
    description: 'Spisak poginulih, nestalih i umrlih boraca i rukovodilaca brigade'
  },
  {
    id: '2-vojvodjanska',
    title: 'Druga vojvođanska NOU brigada',
    author: 'Žarko Atanacković',
    pdfPath: '/pdfs/2-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/2-vojvodjanska.jpg',
    brigadeName: '2. vojvođanska udarna brigada',
    description: 'Spisak boraca i starešina 2. vojvođanske brigade'
  },
  {
    id: '8-krajiska',
    title: 'Osma krajiška NOU brigada',
    author: 'Izudin Čaušević',
    pdfPath: '/pdfs/8-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/8-krajiska.jpg',
    brigadeName: '8. krajiška udarna brigada',
    description: 'Spisak poginulih i umrlih u toku NOR-a iz 8. krajiške brigade'
  },
  {
    id: '6-krajiska',
    title: 'Šesta krajiška NOU brigada',
    author: 'Branko Damjanović, Savo Popović',
    pdfPath: '/pdfs/6-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/6-krajiska.jpg',
    brigadeName: '6. krajiška udarna brigada',
    description: 'Spisak poginulih i umrlih boraca i starješina brigade, s dopunskim spiskom'
  },
  {
    id: '6-krajiska-prezivjeli',
    title: 'Šesta krajiška NOU brigada — spisak preživjelih (ratna sjećanja)',
    author: 'Grupa autora',
    pdfPath: '/pdfs/6-krajiska-prezivjeli.pdf',
    thumbnail: '/images/pdf-thumbs/6-krajiska-prezivjeli.jpg',
    brigadeName: '6. krajiška udarna brigada',
    description: 'Spisak boraca brigade koji su preživeli rat, samo imena, s naknadnim spiskom (str. 747–762 knjige)'
  },
  {
    id: '4-krajiska',
    title: 'Četvrta krajiška NOU brigada',
    author: 'Rade Zorić',
    pdfPath: '/pdfs/4-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/4-krajiska.jpg',
    brigadeName: '4. krajiška udarna brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca i starešina 4. krajiške brigade'
  },
  {
    id: '3-krajiska-proleterska',
    title: 'Treća krajiška proleterska brigada',
    author: 'Savo Trikić',
    pdfPath: '/pdfs/3-krajiska-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/3-krajiska-proleterska.jpg',
    brigadeName: '3. krajiška proleterska udarna brigada',
    description: 'Spisak palih boraca Treće proleterske krajiške brigade s osnovnim matičnim podacima'
  },
  {
    id: '3-krajiska-spisak-boraca',
    title: 'Treća krajiška brigada — spisak boraca (zbornik sjećanja, knj. 3)',
    author: 'Grupa autora',
    pdfPath: '/pdfs/3-krajiska-spisak-boraca.pdf',
    thumbnail: '/images/pdf-thumbs/3-krajiska-spisak-boraca.jpg',
    brigadeName: '3. krajiška proleterska udarna brigada',
    description: 'Spisak boraca brigade koji su se borili u njenom sastavu od 22. 8. 1942. do 9. 5. 1945, preživelih i poginulih: odakle su, zanimanje, kada su stupili u NOB i u brigadu, dužnost, sudbina; s dopunom i prilogom (str. 579 i dalje)'
  },
  {
    id: '17-slavonska-poginuli',
    title: 'Sedamnaesta slavonska brigada — poginuli',
    author: 'Zdravko B. Cvetković',
    pdfPath: '/pdfs/17-slavonska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/17-slavonska-poginuli.jpg',
    brigadeName: '17. slavonska udarna brigada',
    description: 'Spisak poginulih boraca 17. udarne brigade'
  },
  {
    id: '17-slavonska-prezivjeli',
    title: 'Sedamnaesta slavonska brigada — preživjeli',
    author: 'Zdravko B. Cvetković',
    pdfPath: '/pdfs/17-slavonska-prezivjeli.pdf',
    thumbnail: '/images/pdf-thumbs/17-slavonska-prezivjeli.jpg',
    brigadeName: '17. slavonska udarna brigada',
    description: 'Spisak preživjelih boraca 17. udarne brigade'
  },
  {
    id: '25-srpska-divizija',
    title: '25. srpska NOU divizija',
    author: 'Milojica Pantelić',
    pdfPath: '/pdfs/25-srpska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/25-srpska-divizija.jpg',
    brigadeName: '25. srpska udarna divizija',
    description: 'Spisak poginulih boraca i rukovodilaca 25. divizije'
  },
  {
    id: '1-sumadijska',
    title: 'Prva šumadijska brigada',
    author: 'Isidor Đuković',
    pdfPath: '/pdfs/1-sumadijska.pdf',
    thumbnail: '/images/pdf-thumbs/1-sumadijska.jpg',
    brigadeName: '1. šumadijska brigada',
    description: 'Spiskovi poginulih boraca i starešina i boraca koji su preživeli rat'
  },
  {
    id: '18-slavonska',
    title: '18. slavonska brigada',
    author: 'Rade Roksandić, Zdravko B. Cvetković',
    pdfPath: '/pdfs/18-slavonska.pdf',
    thumbnail: '/images/pdf-thumbs/18-slavonska.jpg',
    brigadeName: '18. slavonska udarna brigada',
    description: 'Spisak poginulih i umrlih boraca i rukovodilaca 18. udarne brigade i spisak preživelih boraca'
  },
  {
    id: '4-banijska',
    title: 'Četvrta banijska brigada — zbornik sjećanja',
    author: 'Zbornik sjećanja',
    pdfPath: '/pdfs/4-banijska.pdf',
    thumbnail: '/images/pdf-thumbs/4-banijska.jpg',
    brigadeName: '4. banijska brigada',
    description: 'Spisak boraca 4. banijske brigade'
  },
  {
    id: '4-srpska',
    title: 'Četvrta srpska udarna brigada',
    author: 'Milorad Gončin',
    pdfPath: '/pdfs/4-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/4-srpska.jpg',
    brigadeName: '4. srpska udarna brigada',
    description: 'Spisak boraca Četvrte srpske udarne brigade'
  },
  {
    id: '7-vojvodjanska',
    title: 'Sedma vojvođanska udarna brigada',
    author: 'Nikola Božić',
    pdfPath: '/pdfs/7-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/7-vojvodjanska.jpg',
    brigadeName: '7. vojvođanska udarna brigada',
    description: 'Spisak boraca 7. vojvođanske udarne brigade (preživeli, poginuli i umrli posle rata)'
  },
  {
    id: '19-bircanska',
    title: 'Devetnaesta birčanska NOU brigada',
    author: 'Zbornik',
    pdfPath: '/pdfs/19-bircanska.pdf',
    thumbnail: '/images/pdf-thumbs/19-bircanska.jpg',
    brigadeName: '19. birčanska brigada',
    description: 'Spisak boraca 19. birčanske brigade'
  },
  {
    id: '2-krajiska',
    title: 'Druga krajiška narodnooslobodilačka udarna brigada',
    author: 'Milorad Gončin',
    pdfPath: '/pdfs/2-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/2-krajiska.jpg',
    brigadeName: '2. krajiška udarna brigada',
    description: 'Spisak poginulih i umrlih boraca i rukovodilaca 2. krajiške brigade u toku NOR-a'
  },
  {
    id: 'tuzlanski-odred',
    title: 'Tuzlanski narodnooslobodilački partizanski odred',
    author: 'Grupa autora',
    pdfPath: '/pdfs/tuzlanski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/tuzlanski-odred.jpg',
    brigadeName: 'Tuzlanski NOP odred',
    description: 'Spisak boraca Tuzlanskog NOP odreda'
  },
  {
    id: 'uzicki-odred',
    title: 'Užički partizanski odred „Dimitrije Tucović“ — spisak poginulih boraca',
    author: 'Zbornik',
    pdfPath: '/pdfs/uzicki-odred.pdf',
    thumbnail: '/images/pdf-thumbs/uzicki-odred.jpg',
    brigadeName: 'Užički NOP odred',
    description: 'Spisak boraca Užičkog NOP odreda poginulih u narodnooslobodilačkom ratu 1941-1945.'
  },
  {
    id: '14-srpska',
    title: 'Četrnaesta srpska (niška) NO brigada — spisak poginulih',
    author: 'Zbornik',
    pdfPath: '/pdfs/14-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/14-srpska.jpg',
    brigadeName: '14. srpska udarna brigada',
    description: 'Spisak poginulih boraca i starešina odreda i 14. srpske brigade'
  },
  {
    id: '7-crnogorska-omladinska',
    title: 'Sedma crnogorska omladinska brigada „Budo Tomović“ — spisak poginulih',
    author: 'Mitar Đurišić',
    pdfPath: '/pdfs/7-crnogorska-omladinska.pdf',
    thumbnail: '/images/pdf-thumbs/7-crnogorska.jpg',
    brigadeName: '7. crnogorska omladinska brigada',
    description: 'Spisak poginulih boraca 7. crnogorske omladinske NOU brigade'
  },
  {
    id: '17-majevicka',
    title: 'Sedamnaesta majevička NOU brigada — spisak poginulih i umrlih',
    author: 'Grupa autora',
    pdfPath: '/pdfs/17-majevicka.pdf',
    thumbnail: '/images/pdf-thumbs/17-majevicka.jpg',
    brigadeName: '17. majevička brigada',
    description: 'Spisak boraca Trećeg majevičkog NOP odreda i 17. majevičke NOU brigade poginulih i umrlih u NOR'
  },
  {
    id: '25-brodska-poginuli',
    title: 'Brodska brigada — spisak poginulih boraca',
    author: 'Nail Redžić',
    pdfPath: '/pdfs/25-brodska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/25-brodska.jpg',
    brigadeName: '25. brodska brigada',
    description: 'Spisak poginulih boraca Brodske brigade 28. divizije'
  },
  {
    id: '25-brodska-sastav',
    title: 'Brodska brigada — sastav u oktobru 1943.',
    author: 'Nail Redžić',
    pdfPath: '/pdfs/25-brodska-sastav.pdf',
    thumbnail: '/images/pdf-thumbs/25-brodska-sastav.jpg',
    brigadeName: '25. brodska brigada',
    description: 'Spisak boraca i rukovodilaca koji su bili u Brodskoj brigadi u oktobru 1943. godine'
  },
  {
    id: '25-srpska-brigada',
    title: '25. srpska brigada — spiskovi poginulih i ranjenih',
    author: 'Milorad Madić, Dušan Jončić',
    pdfPath: '/pdfs/25-srpska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/25-srpska-brigada.jpg',
    brigadeName: '25. srpska brigada',
    description: 'Spisak poginulih i spisak ranjenih boraca i rukovodilaca 25. srpske brigade'
  },
  {
    id: '21-tuzlanska',
    title: '21. tuzlanska istočnobosanska NOU brigada — spisak poginulih',
    author: 'Grupa autora',
    pdfPath: '/pdfs/21-tuzlanska.pdf',
    thumbnail: '/images/pdf-thumbs/21-tuzlanska.jpg',
    brigadeName: '21. tuzlanska brigada',
    description: 'Spisak poginulih boraca i starješina 21. tuzlanske NOU brigade'
  },
  {
    id: '53-srednjobosanska-divizija',
    title: '53. srednjobosanska NOU divizija — spisak poginulih, zarobljenih i nestalih',
    author: 'Mladen Vukosavljević, Drago Karasijević',
    pdfPath: '/pdfs/53-srednjobosanska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/53-srednjobosanska-divizija.jpg',
    brigadeName: '53. srednjobosanska divizija',
    description: 'Spisak poginulih, zarobljenih i nestalih boraca Pedeset treće NOU srednjebosanske divizije'
  },
  {
    id: '21-slavonska',
    title: '21. slavonska NOU brigada — spisak poginulih, umrlih i nestalih',
    author: 'Bogdan Bosiočić',
    pdfPath: '/pdfs/21-slavonska.pdf',
    thumbnail: '/images/pdf-thumbs/21-slavonska.jpg',
    brigadeName: '21. slavonska brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca i starješina Dvadeset prve udarne slavonske brigade'
  },
  {
    id: '32-divizija',
    title: '32. divizija — spisak boraca',
    author: 'Grupa autora',
    pdfPath: '/pdfs/32-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/32-divizija.jpg',
    brigadeName: '32. zagorska divizija',
    description: 'Spisak boraca 32. divizije i Zapadne grupe odreda (poginuli označeni zvjezdicom, nestali crticom)'
  },
  {
    id: '32-divizija-borci',
    title: '32. divizija NOVJ — borci divizije po jedinicama',
    author: 'Grupa autora',
    pdfPath: '/pdfs/32-divizija-borci.pdf',
    thumbnail: '/images/pdf-thumbs/32-divizija-borci.jpg',
    brigadeName: '32. zagorska divizija',
    description: 'Borci štaba divizije, prištapskih jedinica, brigada Braća Radić, Matija Gubec, Mihovil Pavlek Miškina i I udarne zagorske, i borci s nepotpunim podacima: godina i mesto rođenja, narodnost, zanimanje, kada su stupili u NOV, sudbina; borac je naveden u svakoj jedinici u kojoj se borio (str. 431–662 knjige)'
  },
  {
    id: '1-dalmatinska',
    title: 'Prva dalmatinska proleterska brigada — spisak poginulih',
    author: 'Mirko Novović',
    pdfPath: 'https://znaci.org/00001/32_1.htm',
    thumbnail: '/images/pdf-thumbs/1-dalmatinska.jpg',
    brigadeName: '1. dalmatinska proleterska brigada',
    description: 'Spisak boraca Prve dalmatinske proleterske NOU brigade poginulih u toku narodnooslobodilačkog rata (tekst na znaci.org, bez skenirane knjige)'
  },
  {
    id: '16-slavonska-omladinska',
    title: '16. slavonska omladinska NOU brigada „Jože Vlahović“ — spiskovi poginulih i rukovodilaca',
    author: 'Stevo Pravdić, Nail Redžić',
    pdfPath: '/pdfs/16-slavonska-omladinska.pdf',
    thumbnail: '/images/pdf-thumbs/16-slavonska-omladinska.jpg',
    brigadeName: '16. slavonska omladinska brigada „Jože Vlahović“',
    description: 'Spisak poginulih boraca i rukovodilaca brigade; spisak poginulih u Pokuplju i na Žumberku; rukovodioci brigade od njenog formiranja do kraja rata (str. 389-428 knjige)'
  },
  {
    id: '8-crnogorska',
    title: 'Osma crnogorska NOU brigada — zbornik sjećanja',
    author: 'Boško Brajović i dr. (ur.)',
    pdfPath: '/pdfs/8-crnogorska.pdf',
    thumbnail: '/images/pdf-thumbs/8-crnogorska.jpg',
    brigadeName: '8. crnogorska brigada',
    description: 'Spisak palih drugova boraca i starješina brigade (str. 471-501 knjige) i dopunski spisak palih iz Uba (str. 509-510)'
  },
  {
    id: 'druga-proleterska',
    title: 'Druga proleterska brigada — ilustrovana monografija (1942—1992)',
    author: 'Miodrag Žiko Avramović',
    pdfPath: '/pdfs/druga-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/druga-proleterska.jpg',
    brigadeName: 'Druga proleterska brigada',
    description: 'Poginuli, umrli i nestali borci Brigade, po mestu i danu pogibije: Sutjeska, istočna Bosna, Pljevlja i Prijepolje, zapadna Srbija, Sremski front (str. 274-278 knjige)'
  },
  {
    id: 'borci-sutjeske-4-proleterska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-4-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-4-proleterska.jpg',
    brigadeName: '4. proleterska crnogorska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: '4-proleterska-poginuli',
    title: 'Četvrta proleterska crnogorska brigada — spisak poginulih',
    author: 'Blažo Janković',
    pdfPath: '/pdfs/4-proleterska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/4-proleterska-poginuli.jpg',
    brigadeName: '4. proleterska crnogorska brigada',
    description: 'Borci i starešine brigade poginuli od 1942. do 1945, po godinama: rođenje, zanimanje, dužnost, kada su i gde pali'
  },
  {
    id: 'borci-sutjeske-5-proleterska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-5-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-5-proleterska.jpg',
    brigadeName: '5. proleterska crnogorska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-6-istocnobosanska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-6-istocnobosanska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-6-istocnobosanska.jpg',
    brigadeName: '6. istočnobosanska proleterska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-10-hercegovacka',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-10-hercegovacka.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-10-hercegovacka.jpg',
    brigadeName: '10. hercegovačka brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-7-banijska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-7-banijska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-7-banijska.jpg',
    brigadeName: '7. banijska brigada „Vasilj Gaćeša“',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-8-banijska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-8-banijska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-8-banijska.jpg',
    brigadeName: '8. banijska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-3-dalmatinska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-3-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-3-dalmatinska.jpg',
    brigadeName: '3. dalmatinska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-16-banijska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-16-banijska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-16-banijska.jpg',
    brigadeName: '16. banijska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-7-krajiska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-7-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-7-krajiska.jpg',
    brigadeName: '7. krajiška brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: '7-krajiska-spisak',
    title: 'Sedma krajiška brigada — preživjeli i poginuli (zbornik, knj. 2)',
    author: 'Grupa autora',
    pdfPath: '/pdfs/7-krajiska-spisak.pdf',
    thumbnail: '/images/pdf-thumbs/7-krajiska-spisak.jpg',
    brigadeName: '7. krajiška brigada',
    description: 'Preživeli i poginuli borci i rukovodioci od formiranja brigade decembra 1942. do kraja rata: rođenje, narodnost, zanimanje, kada su stupili u NOB, dužnost, sudbina (str. 447 i dalje)'
  },
  {
    id: 'borci-sutjeske-15-majevicka',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-15-majevicka.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-15-majevicka.jpg',
    brigadeName: '15. majevička brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-prva-proleterska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-prva-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-prva-proleterska.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-druga-proleterska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-druga-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-druga-proleterska.jpg',
    brigadeName: 'Druga proleterska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-treca-proleterska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-treca-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-treca-proleterska.jpg',
    brigadeName: 'Treća proleterska (sandžačka) brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-3-krajiska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-3-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-3-krajiska.jpg',
    brigadeName: '3. krajiška proleterska udarna brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-1-dalmatinska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-1-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-1-dalmatinska.jpg',
    brigadeName: '1. dalmatinska proleterska brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-2-dalmatinska',
    title: 'Borci Sutjeske — borci brigade na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-2-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-2-dalmatinska.jpg',
    brigadeName: '2. dalmatinska proleterska udarna brigada',
    description: 'Prozivka boraca sa Sutjeske: svi borci brigade u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: '12-dalmatinska',
    title: 'Dvanaesta dalmatinska udarna brigada (Prva otočka) — spisak poginulih',
    author: 'Nikola Anić',
    pdfPath: '/pdfs/12-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/12-dalmatinska.jpg',
    brigadeName: '12. dalmatinska (1. otočka) brigada',
    description: 'Spisak poginulih boraca i rukovodilaca brigade, po borbama, od Sućurja, 22. septembra 1943, do Ilirske Bistrice, 6. maja 1945. (str. 353–366 knjige)'
  },
  {
    id: '3-makedonska',
    title: 'Treća makedonska brigada — spisak poginulih boraca',
    author: 'Kiril Mihailovski Grujica',
    pdfPath: '/pdfs/3-makedonska.pdf',
    thumbnail: '/images/pdf-thumbs/3-makedonska.jpg',
    brigadeName: '3. makedonska brigada',
    description: 'Spisak poginulih boraca brigade: odakle su, godina rođenja, gde su i kada pali (str. 359–368 knjige)'
  },
  {
    id: '18-hrvatska',
    title: 'Osamnaesta hrvatska istočnobosanska brigada — spisak boraca',
    author: 'Grupa autora',
    pdfPath: '/pdfs/18-hrvatska.pdf',
    thumbnail: '/images/pdf-thumbs/18-hrvatska.jpg',
    brigadeName: '18. hrvatska istočnobosanska brigada',
    description: 'Spisak boraca brigade, preživelih i poginulih: godina i mesto rođenja, narodnost, zanimanje, kada su stupili u brigadu, dužnost, sudbina (str. 582–696 knjige)'
  },
  {
    id: '11-dalmatinska',
    title: 'Jedanaesta dalmatinska udarna brigada — popis boraca',
    author: 'Milan Rako, Slavko Družijanić',
    pdfPath: '/pdfs/11-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/11-dalmatinska.jpg',
    brigadeName: '11. dalmatinska brigada',
    description: 'Popis boraca brigade: poginuli, nestali i preživeli (na dan 15. maja 1945): dužnost, rođenje, zanimanje, kada su stupili u NOB, sudbina (str. 479–600 knjige)'
  },
  {
    id: '12-krajiska-poginuli',
    title: 'Dvanaesta krajiška NOU brigada — spisak poginulih',
    author: 'Joco Marjanović, Mile Kukolj, Milutin Vujović, Boro Gaćeša, Rade Ranilović',
    pdfPath: '/pdfs/12-krajiska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/12-krajiska-poginuli.jpg',
    brigadeName: '12. krajiška brigada',
    description: 'Poginuli borci i rukovodioci brigade: dužnost, godina i mesto rođenja, gde su i kada pali'
  },
  {
    id: '12-krajiska-prezivjeli',
    title: 'Dvanaesta krajiška NOU brigada — spisak preživjelih',
    author: 'Joco Marjanović, Mile Kukolj, Milutin Vujović, Boro Gaćeša, Rade Ranilović',
    pdfPath: '/pdfs/12-krajiska-prezivjeli.pdf',
    thumbnail: '/images/pdf-thumbs/12-krajiska-prezivjeli.jpg',
    brigadeName: '12. krajiška brigada',
    description: 'Preživeli borci i rukovodioci brigade: godina i mesto rođenja'
  },
  {
    id: '17-srpska',
    title: 'Sedamnaesta srpska brigada — spisak boraca',
    author: 'Predrag Milenković',
    pdfPath: '/pdfs/17-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/17-srpska.jpg',
    brigadeName: '17. srpska brigada',
    description: 'Spisak boraca brigade koji su preživeli rat i spisak poginulih boraca: rođenje, kada su stupili u brigadu, dužnost, gde su i kada pali (str. 317–373 knjige)'
  },
  {
    id: '14-srednjobosanska',
    title: '14. srednjobosanska NOU brigada — spisak poginulih i preživjelih',
    author: 'Stevo Samardžija',
    pdfPath: '/pdfs/14-srednjobosanska.pdf',
    thumbnail: '/images/pdf-thumbs/14-srednjobosanska.jpg',
    brigadeName: '14. srednjobosanska brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca i rukovodilaca brigade, i spisak boraca koji su preživeli rat, po opštinama (str. 393–458 knjige)'
  },
  {
    id: '3-vojvodjanska',
    title: 'Treća vojvođanska NOU brigada — spiskovi boraca i starešina',
    author: 'Radovan Panić',
    pdfPath: '/pdfs/3-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/3-vojvodjanska.jpg',
    brigadeName: '3. vojvođanska brigada',
    description: 'Spiskovi boraca i starešina brigade: poginuli, oni čija je sudbina ostala neutvrđena, i preživeli (str. 479 i dalje)'
  },
  {
    id: 'kalnicki-odred',
    title: 'Kalnički partizanski odred — spisak boraca',
    author: 'Žarko Milićević',
    pdfPath: '/pdfs/kalnicki-odred.pdf',
    thumbnail: '/images/pdf-thumbs/kalnicki-odred.jpg',
    brigadeName: 'Kalnički partizanski odred',
    description: 'Spisak boraca Kalničkoga partizanskog odreda, poginulih i preživelih (str. 311 i dalje)'
  },
  {
    id: 'posavsko-trebavski-odred',
    title: 'Posavsko-trebavski odred — spisak boraca',
    author: 'Esad Tihić',
    pdfPath: '/pdfs/posavsko-trebavski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/posavsko-trebavski-odred.jpg',
    brigadeName: 'Posavsko-trebavski partizanski odred',
    description: 'Spisak boraca odreda po opštinama iz kojih su došli (str. 313 i dalje)'
  },
  {
    id: '8-kordunaska-divizija',
    title: 'Osma kordunaška udarna divizija — popis palih boraca',
    author: 'Historijski arhiv u Karlovcu (Zbornik, knj. 9)',
    pdfPath: '/pdfs/8-kordunaska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/8-kordunaska-divizija.jpg',
    brigadeName: '8. kordunaška divizija',
    description: 'Popis palih boraca Osme divizije, po prezimenu, s brigadom u kojoj su bili (str. 806 i dalje)'
  },
  {
    id: 'cankarjeva',
    title: 'Cankarjeva brigada — seznam cankarjevcev, padli',
    author: 'Lado Ambrožič-Novljan',
    pdfPath: '/pdfs/cankarjeva.pdf',
    thumbnail: '/images/pdf-thumbs/cankarjeva.jpg',
    brigadeName: 'Cankarjeva brigada',
    description: 'Spisak boraca brigade koji su preživeli rat (str. 815 i dalje) i spisak njenih poginulih (str. 847 i dalje)'
  },
  {
    id: 'gubceva',
    title: 'Gubčeva brigada — seznam gubčevcev, padli',
    author: 'Lado Ambrožič-Novljan',
    pdfPath: '/pdfs/gubceva.pdf',
    thumbnail: '/images/pdf-thumbs/gubceva.jpg',
    brigadeName: 'Gubčeva brigada',
    description: 'Spisak boraca brigade koji su preživeli rat (str. 979 i dalje) i spisak njenih poginulih (str. 1016 i dalje)'
  },
  {
    id: 'dvanajsta',
    title: 'Dvanajsta brigada — seznam padlih, seznam borcev XII. SNOUB',
    author: 'Lado Ambrožič-Novljan',
    pdfPath: '/pdfs/dvanajsta.pdf',
    thumbnail: '/images/pdf-thumbs/dvanajsta.jpg',
    brigadeName: '12. slovenačka brigada',
    description: 'Spisak poginulih boraca brigade i spisak onih koji su preživeli rat, na kraju knjige'
  },
  {
    id: 'gradnikova',
    title: 'Gradnikova brigada — pregled borcev',
    author: 'Stanko Petelin',
    pdfPath: '/pdfs/gradnikova.pdf',
    thumbnail: '/images/pdf-thumbs/gradnikova.jpg',
    brigadeName: 'Gradnikova brigada',
    description: 'Spisak boraca poginulih u brigadi i spisak ostalih: onih koji su preživeli rat ili nisu poginuli dok su bili u njoj (str. 840 i dalje)'
  },
  {
    id: 'zidanskova',
    title: 'Zidanškova brigada — seznam borcev',
    author: 'Mirko Fajdiga',
    pdfPath: '/pdfs/zidanskova.pdf',
    thumbnail: '/images/pdf-thumbs/zidanskova.jpg',
    brigadeName: 'Zidanškova brigada',
    description: 'Spisak boraca brigade; kod poginulih godina rođenja i pogibije (str. 731 i dalje)'
  },
  {
    id: 'skofjeloski-odred',
    title: 'Škofjeloški odred — seznam borcev',
    author: 'Tone Lotrič',
    pdfPath: '/pdfs/skofjeloski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/skofjeloski-odred.jpg',
    brigadeName: 'Škofjeloški odred',
    description: 'Spisak boraca odreda, samo imena, kako su upisani u sačuvanoj arhivi odreda (str. 314 i dalje)'
  },
  {
    id: 'istrski-odred',
    title: 'Istrski odred — seznam borcev, padli',
    author: 'Maks Zadnik',
    pdfPath: '/pdfs/istrski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/istrski-odred.jpg',
    brigadeName: 'Istarski odred',
    description: 'Spisak boraca odreda (str. 827 i dalje), bez poginulih, i spisak poginulih s kratkim podacima (str. 849 i dalje)'
  },
  {
    id: 'zapadnodolenjski-odred',
    title: 'Zapadnodolenjski odred — seznam odredovcev, padli',
    author: 'Velimir Kraševec',
    pdfPath: '/pdfs/zapadnodolenjski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/zapadnodolenjski-odred.jpg',
    brigadeName: 'Zapadnodolenjski odred',
    description: 'Spisak boraca odreda (str. 333 i dalje) i spisak njegovih poginulih (str. 340 i dalje)'
  },
  {
    id: 'braciceva',
    title: 'Bračičeva brigada, II. del — padli borci, borci, ki so vojno preživeli',
    author: 'Mirko Fajdiga',
    pdfPath: '/pdfs/braciceva.pdf',
    thumbnail: '/images/pdf-thumbs/braciceva.jpg',
    brigadeName: 'Bračičeva brigada',
    description: 'Spisak poginulih boraca brigade (str. 722 i dalje) i onih koji su preživeli rat (str. 746 i dalje)'
  },
  {
    id: 'tomsiceva-2',
    title: 'Tomšičeva brigada, 2. knjiga — seznam borcev 1942—1943',
    author: 'Franci Strle',
    pdfPath: '/pdfs/tomsiceva-2.pdf',
    thumbnail: '/images/pdf-thumbs/tomsiceva-2.jpg',
    brigadeName: 'Tomšičeva brigada',
    description: 'Spisak boraca brigade od 16. jula 1942. do 13. jula 1943. (2. knjiga, str. 847 i dalje)'
  },
  {
    id: 'tomsiceva-3',
    title: 'Tomšičeva brigada, 3. knjiga — borci 1942—1943, izpuščeni iz 2. knjige',
    author: 'Franci Strle',
    pdfPath: '/pdfs/tomsiceva-3.pdf',
    thumbnail: '/images/pdf-thumbs/tomsiceva-3.jpg',
    brigadeName: 'Tomšičeva brigada',
    description: 'Borci brigade od 16. jula 1942. do 13. jula 1943. koji su izostali iz spiska 2. knjige ili su se naknadno javili (3. knjiga, str. 647 i dalje)'
  },
  {
    id: 'tomsiceva-4',
    title: 'Tomšičeva brigada, 4. knjiga — seznama borcev 1943—1945',
    author: 'Franci Strle',
    pdfPath: '/pdfs/tomsiceva-4.pdf',
    thumbnail: '/images/pdf-thumbs/tomsiceva-4.jpg',
    brigadeName: 'Tomšičeva brigada',
    description: 'Spiskovi boraca brigade od 13. jula 1943. do 1. aprila 1944. i od 1. aprila 1944. do 15. maja 1945. (4. knjiga, str. 576 i dalje)'
  },
  {
    id: '1-slovenska-artilerijska',
    title: 'Prva slovenska artilerijska brigada',
    author: 'Borivoj Lah – Boris',
    pdfPath: '/pdfs/1-slovenska-artilerijska.pdf',
    thumbnail: '/images/pdf-thumbs/1-slovenska-artilerijska.jpg',
    brigadeName: '1. slovenačka artiljerijska brigada',
    description: 'Spisak starešina, spisak artiljeraca i spisak poginulih (str. 388 i dalje)'
  },
  {
    id: 'artilerija-9-korpusa',
    title: 'Artilerija 9. korpusa',
    author: 'Borivoj Lah – Boris',
    pdfPath: '/pdfs/artilerija-9-korpusa.pdf',
    thumbnail: '/images/pdf-thumbs/artilerija-9-korpusa.jpg',
    brigadeName: 'Artiljerija 9. korpusa',
    description: 'Spisak boraca artiljerije, spisak poginulih i spisak starešina (str. 316 i dalje)'
  },
  {
    id: '19-srpska',
    title: 'Devetnaesta srpska brigada — poginuli i preživeli',
    author: 'Predrag Pejčić',
    pdfPath: '/pdfs/19-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/19-srpska.jpg',
    brigadeName: '19. srpska brigada',
    description: 'Poginuli, nestali i umrli po jedinicama i borci koji su preživeli rat: rođenje, dužnost, kada i gde su pali (str. 411–612)'
  },
  {
    id: '22-srpska',
    title: '22. srpska kosmajska brigada — poginuli i preživeli borci',
    author: 'Milorad Gončin',
    pdfPath: '/pdfs/22-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/22-srpska.jpg',
    brigadeName: '22. srpska kosmajska brigada',
    description: 'Poginuli i preživeli borci i starešine brigade: rođenje, kada su stupili u brigadu, dužnost, gde su pali (str. 317–399)'
  },
  {
    id: '12-vojvodjanska',
    title: '12. vojvođanska udarna brigada — spisak boraca i poginulih',
    author: 'Branislav Popov Miša',
    pdfPath: '/pdfs/12-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/12-vojvodjanska.jpg',
    brigadeName: '12. vojvođanska brigada',
    description: 'Spisak boraca po mestima u kojima su živeli pre stupanja u brigadu i spisak poginulih: odakle su, godina rođenja, gde su pali (str. 207–258)'
  },
  {
    id: '4-vojvodjanska',
    title: 'Četvrta vojvođanska brigada — pripadnici i poginuli',
    author: 'Špiro Lagator',
    pdfPath: '/pdfs/4-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/4-vojvodjanska.jpg',
    brigadeName: '4. vojvođanska brigada',
    description: 'Spisak pripadnika brigade na dan 7. oktobra 1943. i spisak poginulih i umrlih do 1. 3. 1946: rođenje, zanimanje, dužnost, gde su pali (str. 281–334)'
  },
  {
    id: '1-kosovsko-metohijska',
    title: 'Prva kosovsko-metohijska brigada — spiskovi boraca',
    author: 'Milutin Milković',
    pdfPath: '/pdfs/1-kosovsko-metohijska.pdf',
    thumbnail: '/images/pdf-thumbs/1-kosovsko-metohijska.jpg',
    brigadeName: '1. kosovsko-metohijska brigada',
    description: 'Spiskovi boraca: kosovsko-metohijski bataljoni od kojih je brigada formirana, borci koji su stupili 1944. iz Porečja i Tetova i od Junika i Dečana, poginuli i ranjeni (str. 351–383)'
  },
  {
    id: '8-vojvodjanska',
    title: 'Rovovi i mostobrani: Osma vojvođanska brigada — poginuli i nestali',
    author: 'Nikola Božić',
    pdfPath: '/pdfs/8-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/8-vojvodjanska.jpg',
    brigadeName: '8. vojvođanska brigada',
    description: 'Spisak poginulih i nestalih boraca i rukovodilaca brigade: rođenje, gde su i kada pali ili nestali (str. 675–722)'
  },
  {
    id: '19-sjevernodalmatinska',
    title: 'Devetnaesta sjevernodalmatinska divizija — popis poginulih i umrlih',
    author: 'Dragutin Grgurević',
    pdfPath: '/pdfs/19-sjevernodalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/19-sjevernodalmatinska.jpg',
    brigadeName: '19. severnodalmatinska divizija',
    description: 'Popis poginulih i umrlih boraca divizije od formiranja do kraja rata: odakle su, gde su i kada pali (str. 253–299)'
  },
  {
    id: '21-srpska',
    title: 'Druga šumadijska - 21. srpska brigada — u koloni brigade',
    author: 'Isidor Đuković',
    pdfPath: '/pdfs/21-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/21-srpska.jpg',
    brigadeName: '21. srpska brigada',
    description: 'Poginuli, preživeli i drugi koji su se borili u brigadi (Druga šumadijska): roditelji, rođenje, dužnost, kada su stupili u brigadu i gde su pali (str. 387–472)'
  },
  {
    id: '14-hercegovacka',
    title: 'Četrnaesta hercegovačka omladinska NOU brigada — spisak boraca i poginulih',
    author: 'Grupa autora',
    pdfPath: '/pdfs/14-hercegovacka.pdf',
    thumbnail: '/images/pdf-thumbs/14-hercegovacka.jpg',
    brigadeName: '14. hercegovačka brigada',
    description: 'Spisak boraca koji su prošli kroz brigadu: godina i mesto rođenja; poginuli, s jedinicom i mestom pogibije (str. 243–287)'
  },
  {
    id: '5-vojvodjanska',
    title: 'Peta vojvođanska brigada — spisak boraca i starešina',
    author: 'Nikola Mraović',
    pdfPath: '/pdfs/5-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/5-vojvodjanska.jpg',
    brigadeName: '5. vojvođanska brigada',
    description: 'Spisak boraca i starešina brigade: godina i mesto rođenja, zanimanje, dužnost u brigadi, gde su pali ili nestali (str. 429–584)'
  },
  {
    id: '6-vojvodjanska',
    title: 'Šesta vojvođanska udarna brigada — spisak poginulih',
    author: 'Živan M. Ninković',
    pdfPath: '/pdfs/6-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/6-vojvodjanska.jpg',
    brigadeName: '6. vojvođanska brigada',
    description: 'Spisak poginulih boraca i rukovodilaca: godina i mesto rođenja, datum i mesto pogibije, gde su sahranjeni (str. 175–199)'
  },
  {
    id: '13-vojvodjanska',
    title: 'Kako do brigade — spisak pripadnika XIII vojvođanske brigade',
    author: 'Đorđe Momčilović',
    pdfPath: '/pdfs/13-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/13-vojvodjanska.jpg',
    brigadeName: '13. vojvođanska brigada',
    description: 'Spisak pripadnika brigade: imena, ponegde nadimak ili mesto; autor napominje da spisak nije potpun (str. 771–793)'
  },
  {
    id: '7-srpska',
    title: 'Sedma srpska brigada — spisak boraca i poginulih',
    author: 'Đura Zlatković, Miloš D. Bakić',
    pdfPath: '/pdfs/7-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/7-srpska.jpg',
    brigadeName: '7. srpska brigada',
    description: 'Spisak boraca početkom maja 1944. po selima i spisak poginulih, umrlih i nestalih: rođenje, kada su stupili u brigadu, gde su pali (str. 459–501)'
  },
  {
    id: '15-srpska',
    title: 'Petnaesta srpska NO brigada — spiskovi boraca, poginulih i ranjenih',
    author: 'Vojislav Nikčević',
    pdfPath: '/pdfs/15-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/15-srpska.jpg',
    brigadeName: '15. srpska brigada',
    description: 'Spisak boraca i rukovodilaca brigade, spisak poginulih i spisak ranjenih: rođenje, dužnost, kada i gde su pali ili ranjeni (str. 155–173)'
  },
  {
    id: '8-srpska',
    title: '8. srpska brigada — Nezaboravnik (spisak poginulih)',
    author: 'Petar Damjanov',
    pdfPath: '/pdfs/8-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/8-srpska.jpg',
    brigadeName: '8. srpska brigada',
    description: '„Nezaboravnik“, spisak poginulih boraca brigade: rođenje, datum i mesto pogibije (str. 265–297)'
  },
  {
    id: '10-srpska',
    title: 'Deseta srpska NOU brigada — spisak poginulih',
    author: 'Radovan Timotijević',
    pdfPath: '/pdfs/10-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/10-srpska.jpg',
    brigadeName: '10. srpska brigada',
    description: 'Spisak poginulih boraca i rukovodilaca: rođenje, kada su stupili u brigadu, dužnost, gde su pali i sahranjeni (str. 488–541)'
  },
  {
    id: '23-srpska',
    title: '23. srpska brigada — pregled poginulih i umrlih',
    author: 'Dragoljub Ž. Mirčetić Duško',
    pdfPath: '/pdfs/23-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/23-srpska.jpg',
    brigadeName: '23. srpska brigada',
    description: 'Pregled poginulih i umrlih boraca i rukovodilaca: godina i mesto rođenja, zanimanje, kada su stupili u NOVJ, jedinica, gde su pali i sahranjeni (str. 352–388)'
  },
  {
    id: '12-srpska',
    title: 'Dvanaesta srpska NOU brigada — pregled poginulih i umrlih',
    author: 'Dragoljub Ž. Mirčetić',
    pdfPath: '/pdfs/12-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/12-srpska.jpg',
    brigadeName: '12. srpska brigada',
    description: 'Pregled poginulih i umrlih boraca i rukovodilaca: godina i mesto rođenja, zanimanje, kada su stupili u NOVJ, jedinica, gde su pali i sahranjeni (str. 355–400)'
  }
]
