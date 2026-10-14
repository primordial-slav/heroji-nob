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
    title: '10. slovenska NOV brigada „Ljubljanska“',
    author: 'Borivoj Lah – Boris',
    pdfPath: '/pdfs/ljubljanska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/ljubljanska-brigada.jpg',
    brigadeName: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    description: 'Monografija Ljubljanske brigade'
  },
  {
    id: '13-proleterska-spisak',
    title: 'Trinaesta proleterska brigada „Rade Končar“',
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
    id: '1-dalmatinska-monografija',
    title: 'Prva dalmatinska proleterska brigada — komandiri i komesari četa, narodni heroji, poginuli',
    author: 'Mirko Novović, Stevan Petković',
    pdfPath: '/pdfs/1-dalmatinska-monografija.pdf',
    thumbnail: '/images/pdf-thumbs/1-dalmatinska-monografija.jpg',
    brigadeName: '1. dalmatinska proleterska brigada',
    description: 'Komandiri i politički komesari četa po bataljonima, biografije narodnih heroja brigade i spisak boraca poginulih u ratu, isti kao na znaci.org, ovde sa skeniranom knjigom'
  },
  {
    id: 'zene-1-dalmatinska',
    title: 'Žene Hrvatske u narodnooslobodilačkoj borbi — žene borci I. dalmatinske proleterske brigade',
    author: 'Zbornik',
    pdfPath: '/pdfs/zene-1-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/zene-1-dalmatinska.jpg',
    brigadeName: '1. dalmatinska proleterska brigada',
    description: 'Spisak žena boraca brigade iz 1944–1945 (dokument 368): dužnost i čin, datum i mesto rođenja, kada su stupile u NOV, odlikovanja i mišljenje štaba o svakoj'
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
    id: '5-proleterska-partizanke',
    title: 'Partizanke Pete proleterske crnogorske brigade',
    author: 'Grupa autora',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00005897',
    thumbnail: '/images/pdf-thumbs/5-proleterska-partizanke.jpg',
    brigadeName: '5. proleterska crnogorska brigada',
    description: 'Biografije partizanki brigade: rođenje, put u NOB, dužnosti u brigadi, rane i odlikovanja, život posle rata (str. 43–278). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
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
    id: '6-istocnobosanska-dopuna',
    title: 'Šesta proleterska istočnobosanska brigada — dopuna spiska boraca',
    author: 'Rudi Petovar, Savo Trikić',
    pdfPath: '/pdfs/6-istocnobosanska-dopuna.pdf',
    thumbnail: '/images/pdf-thumbs/6-istocnobosanska-dopuna.jpg',
    brigadeName: '6. istočnobosanska proleterska brigada',
    description: 'Borci brigade čiji podaci nisu objavljeni u knjizi „Borbeni put Šeste proleterske brigade“ (1977), prikupljeni do 1981: rođenje, kada su stupili u NOB, dužnost, sudbina; i borci kojima nije utvrđeno mesto i vreme pogibije (str. 676 i dalje)'
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
    id: '7-banijska-poginuli',
    title: 'Sedma banijska brigada — spisak poginulih i umrlih',
    author: 'Ljuban Đurić',
    pdfPath: '/pdfs/7-banijska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/7-banijska-poginuli.jpg',
    brigadeName: '7. banijska brigada „Vasilj Gaćeša“',
    description: 'Nepotpun spisak poginulih u ratu i umrlih pripadnika brigade: rođenje, narodnost, zanimanje, kada su stupili u NOVJ, bataljon, gde i kada su pali (str. 394–462)'
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
    id: '8-banijska-poginuli',
    title: 'Osma banijska NOU brigada — pregled palih i umrlih boraca',
    author: 'Ljuban Đurić',
    pdfPath: '/pdfs/8-banijska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/8-banijska-poginuli.jpg',
    brigadeName: '8. banijska brigada',
    description: 'Pali i umrli borci brigade od 7. septembra 1942. do 6. decembra 1944: rođenje, zanimanje, kada su stupili u brigadu, dužnost, gde i kada su pali (str. 247–312)'
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
    id: '9-dalmatinska-divizija',
    title: 'Dva rođenja Devete dalmatinske divizije — spisak poginulih i nestalih',
    author: 'Obrad Egić',
    pdfPath: '/pdfs/9-dalmatinska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/9-dalmatinska-divizija.jpg',
    brigadeName: '9. dalmatinska divizija',
    description: 'Borci i rukovodioci divizije koji su poginuli i nestali u borbama od 11. februara do 15. aprila 1943, imena sa očevim imenom (str. 121–126)'
  },
  {
    id: '3-dalmatinska-poginuli',
    title: 'Dva rođenja Devete dalmatinske divizije — spisak poginulih i nestalih',
    author: 'Obrad Egić',
    pdfPath: '/pdfs/3-dalmatinska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/3-dalmatinska-poginuli.jpg',
    brigadeName: '3. dalmatinska brigada',
    description: 'Poginuli i nestali borci i rukovodioci 3. samostalne dalmatinske brigade od 14. aprila do 6. juna 1943, imena sa očevim imenom (str. 126–128)'
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
    id: '16-banijska-poginuli',
    title: 'Šesnaesta banijska narodnooslobodilačka udarna brigada',
    author: 'Ljuban P. Đurić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=b6ed63f4-83a8-458b-80d7-1d3dff4a056f/00000001/00000001/00003006',
    thumbnail: '/images/pdf-thumbs/16-banijska-poginuli.jpg',
    brigadeName: '16. banijska brigada',
    description: 'Spisak poginulih boraca i starešina brigade od 26. decembra 1942. do 30. juna 1943, s godinom i mestom rođenja i mestom pogibije (str. 201–247). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
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
    id: '15-majevicka-spisak',
    title: 'Petnaesta majevička brigada — spisak boraca',
    author: 'Grupa autora',
    pdfPath: '/pdfs/15-majevicka-spisak.pdf',
    thumbnail: '/images/pdf-thumbs/15-majevicka-spisak.jpg',
    brigadeName: '15. majevička brigada',
    description: 'Narodni heroji brigade i spisak svih njenih boraca: godina i mesto rođenja, narodnost, zanimanje, kada su stupili u NOB i došli u brigadu, sudbina (str. 484–557)'
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
    id: 'prva-proleterska-stroj-u-rudom',
    title: 'Prva proleterska brigada — borci brigade na dan njenog osnivanja (stroj u Rudom)',
    author: 'Miloš Vuksanović',
    pdfPath: '/pdfs/prva-proleterska-stroj-u-rudom.pdf',
    thumbnail: '/images/pdf-thumbs/prva-proleterska-stroj-u-rudom.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Borci koji su 21. decembra 1941. stajali u stroju u Rudom, po štabovima, bataljonima i četama: rođenje, zanimanje, dužnost i šta je s kim bilo u ratu (str. 433–492). Zvezdica uz ime označava borca koji je poginuo u ratu.'
  },
  {
    id: 'beogradski-bataljon',
    title: 'Beogradski bataljon Prve proleterske brigade 1941–1945. — spisak boraca',
    author: 'Grupa autora',
    pdfPath: '/pdfs/beogradski-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/beogradski-bataljon.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Svi borci Beogradskog bataljona od prvih dana ustanka do 1. marta 1945, kada je postao 3. bataljon Prve proleterske, po tome kada su došli u bataljon: zanimanje, rođenje, članstvo u KPJ i SKOJ-u, šta je s kim bilo u ratu'
  },
  {
    id: 'dalmatinci-prva-proleterska',
    title: 'Dalmatinci u Prvoj proleterskoj — popis boraca',
    author: 'Tomislav Jelić, Vitomir Pirak',
    pdfPath: '/pdfs/dalmatinci-prva-proleterska.pdf',
    thumbnail: '/images/pdf-thumbs/dalmatinci-prva-proleterska.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Borci Prve proleterske brigade iz Dalmacije, s biografijom svakog: rođenje, zanimanje, put u NOB i u brigadu, borbe, sudbina; i dodatni spisak onih za koje autori nisu prikupili podatke (str. 467–754)'
  },
  {
    id: 'crnogorski-bataljon',
    title: 'Prvi crnogorski bataljon Prve proleterske NOU brigade — spiskovi boraca koji su stupili u bataljon 1942–1945',
    author: 'Zbornik sjećanja',
    pdfPath: '/pdfs/crnogorski-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/crnogorski-bataljon.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Borci koji su u Prvi crnogorski bataljon Prve proleterske stupili 1942, 1943, 1944. i 1945. i borci bez potpunih podataka: rođenje, zanimanje, kada su stupili u NOB, sudbina; ćirilica (str. 713–795)'
  },
  {
    id: 'rudarska-ceta',
    title: 'Rudarska četa — spisak boraca u Rudom 21. XII 1941.',
    author: 'Branislav Božović',
    pdfPath: '/pdfs/rudarska-ceta.pdf',
    thumbnail: '/images/pdf-thumbs/rudarska-ceta.jpg',
    brigadeName: 'Prva proleterska narodnooslobodilačka udarna brigada',
    description: 'Borci Rudarske čete (rudari Trepče i Kopaonika) kada je ušla u Prvu proletersku u Rudom 21. decembra 1941, s biografijom svakog (str. 426–430)'
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
    id: 'zene-11-dalmatinska',
    title: 'Žene Hrvatske u narodnooslobodilačkoj borbi — žene borci XI. dalmatinske brigade',
    author: 'Zbornik',
    pdfPath: '/pdfs/zene-11-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/zene-11-dalmatinska.jpg',
    brigadeName: '11. dalmatinska brigada',
    description: 'Spisak žena boraca brigade iz 1944–1945 (dokument 376): datum i mesto rođenja, dužnost i čin, kada su stupile u NOV, odlikovanja i mišljenje štaba o svakoj'
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
  },
  {
    id: '20-srpska',
    title: 'Dvadeseta srpska brigada — pregled poginulih i umrlih',
    author: 'Dragoljub Mirčetić Duško',
    pdfPath: '/pdfs/20-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/20-srpska.jpg',
    brigadeName: '20. srpska brigada',
    description: 'Pregled poginulih i umrlih boraca i rukovodilaca: godina i mesto rođenja, zanimanje, kada su stupili u NOVJ, jedinica, gde su pali i sahranjeni (str. 321–385)'
  },
  {
    id: '1-konjicka',
    title: '1. konjička brigada — pali borci i ratni spisak',
    author: 'Milorad Gončin',
    pdfPath: '/pdfs/1-konjicka.pdf',
    thumbnail: '/images/pdf-thumbs/1-konjicka.jpg',
    brigadeName: '1. konjička brigada',
    description: 'Spisak palih boraca i rukovodilaca (rođenje, gde su pali) i ratni spisak starešina i boraca brigade, samo imena (str. 317–327)'
  },
  {
    id: 'toplicki-odred',
    title: 'Toplički NOP odred — borci na dan formiranja, poginuli i umrli, narodni heroji',
    author: 'Dragoljub Dinić Mića',
    pdfPath: '/pdfs/toplicki-odred.pdf',
    thumbnail: '/images/pdf-thumbs/toplicki-odred.jpg',
    brigadeName: 'Toplički NOP odred',
    description: 'Borci odreda na dan formiranja, spisak poginulih i umrlih boraca i rukovodilaca i narodni heroji koji su se borili u odredu, sa fotografijama (str. 302–344)'
  },
  {
    id: 'karlovacka',
    title: 'Karlovačka udarna brigada — borci na dan formiranja i poginuli',
    author: 'Josip Lulik Pepo, Đuro Zatezalo',
    pdfPath: '/pdfs/karlovacka.pdf',
    thumbnail: '/images/pdf-thumbs/karlovacka.jpg',
    brigadeName: 'Karlovačka udarna brigada',
    description: 'Popis boraca i rukovodilaca brigade na dan formiranja u Hrašću 5. marta 1944. i popis poginulih boraca i rukovodilaca (str. 379–414)'
  },
  {
    id: '14-primorsko-goranska',
    title: '14. primorsko-goranska brigada — spisak poginulih boraca',
    author: 'Vladimir-Dušan Matetić',
    pdfPath: '/pdfs/14-primorsko-goranska.pdf',
    thumbnail: '/images/pdf-thumbs/14-primorsko-goranska.jpg',
    brigadeName: '14. primorsko-goranska brigada',
    description: 'Spisak poginulih boraca brigade, s rođenjem, dužnošću i mestom pogibije (str. 227–264)'
  },
  {
    id: '22-divizija',
    title: '22. divizija — spisak poginulih boraca i rukovodilaca',
    author: 'Živojin Nikolić Brka',
    pdfPath: '/pdfs/22-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/22-divizija.jpg',
    brigadeName: '22. divizija',
    description: 'Spisak poginulih boraca i rukovodilaca divizije, po brigadama: mesto rođenja, dan i mesto pogibije (str. 445–476)'
  },
  {
    id: '34-divizija',
    title: '34. udarna divizija — pregled poginulih boraca i rukovodilaca',
    author: 'Vladimir Hlaić',
    pdfPath: '/pdfs/34-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/34-divizija.jpg',
    brigadeName: '34. divizija',
    description: 'Pregled poginulih boraca i rukovodilaca divizije: čin, brigada, rođenje, stupanje u NOB, mesto i dan pogibije (str. 401–432)'
  },
  {
    id: '4-sandzacka',
    title: '4. sandžačka brigada — poginuli i ranjeni borci',
    author: 'Čedo Drulović',
    pdfPath: '/pdfs/4-sandzacka.pdf',
    thumbnail: '/images/pdf-thumbs/4-sandzacka.jpg',
    brigadeName: '4. sandžačka brigada',
    description: 'Spisak poginulih boraca i rukovodilaca (rođenje, gde su pali) i spisak ranjenih, s mestom i danom ranjavanja (str. 460–485)'
  },
  {
    id: '3-primorsko-goranska',
    title: '3. primorsko-goranska brigada — starešine, bolničari i poginuli',
    author: 'Bogdan Mamula',
    pdfPath: '/pdfs/3-primorsko-goranska.pdf',
    thumbnail: '/images/pdf-thumbs/3-primorsko-goranska.jpg',
    brigadeName: '3. primorsko-goranska brigada',
    description: 'Spisak starešina brigade i četnih bolničara, s dužnošću, i spisak poginulih pripadnika brigade, s rođenjem i mestom pogibije (str. 234–259)'
  },
  {
    id: '13-hercegovacka',
    title: '13. hercegovačka brigada — poginuli i borci brigade',
    author: 'Mensur Seferović',
    pdfPath: '/pdfs/13-hercegovacka.pdf',
    thumbnail: '/images/pdf-thumbs/13-hercegovacka.jpg',
    brigadeName: '13. hercegovačka brigada',
    description: 'Poginuli borci i starešine brigade (rođenje, dan i mesto pogibije) i spisak boraca koji su se borili u brigadi, samo imena (str. 316–347)'
  },
  {
    id: '12-hercegovacka',
    title: '12. hercegovačka brigada — spisak poginulih boraca i starešina',
    author: 'Osman Đikić',
    pdfPath: '/pdfs/12-hercegovacka.pdf',
    thumbnail: '/images/pdf-thumbs/12-hercegovacka.jpg',
    brigadeName: '12. hercegovačka brigada',
    description: 'Spisak poginulih boraca i starešina brigade, po opštinama: rođenje, dužnost, gde i kada su pali (str. 207–220)'
  },
  {
    id: '1-bokeljska',
    title: '1. bokeljska brigada — spisak poginulih i umrlih boraca',
    author: 'Dušan Živković',
    pdfPath: '/pdfs/1-bokeljska.pdf',
    thumbnail: '/images/pdf-thumbs/1-bokeljska.jpg',
    brigadeName: '1. bokeljska brigada',
    description: 'Spisak poginulih i umrlih boraca brigade i nestalih u borbi: bataljon, rođenje, gde i kada su pali (str. 315–321)'
  },
  {
    id: '6-dalmatinska',
    title: '6. dalmatinska brigada — spisak poginulih boraca',
    author: 'Danilo Damjanović',
    pdfPath: '/pdfs/6-dalmatinska.pdf',
    thumbnail: '/images/pdf-thumbs/6-dalmatinska.jpg',
    brigadeName: '6. dalmatinska brigada',
    description: 'Spisak poginulih boraca brigade: odakle su, gde i kada su pali (str. 259–271)'
  },
  {
    id: 'osjecka',
    title: 'Osječka udarna brigada — poginuli, umrli i preživeli borci',
    author: 'Zdravko B. Cvetković',
    pdfPath: '/pdfs/osjecka.pdf',
    thumbnail: '/images/pdf-thumbs/osjecka.jpg',
    brigadeName: 'Osječka udarna brigada',
    description: 'Spisak poginulih i umrlih boraca brigade i spisak preživelih boraca, po opštinama rođenja (str. 207–254)'
  },
  {
    id: 'osjecka-zene',
    title: 'Žene Hrvatske u narodnooslobodilačkoj borbi — žene borci Osječke brigade',
    author: 'Zbornik',
    pdfPath: '/pdfs/osjecka-zene.pdf',
    thumbnail: '/images/pdf-thumbs/osjecka-zene.jpg',
    brigadeName: 'Osječka udarna brigada',
    description: 'Drugarice Osječke brigade po bataljonima, kako ih je štab brigade popisao za I. kongres AFŽ Hrvatske (dokument 420): datum i mesto rođenja, od kada su u partizanima'
  },
  {
    id: '4-brigada-slavonije',
    title: '4. NOU brigada Slavonije (Druga brodska brigada) — spiskovi poginulih i ranjenih',
    author: 'Stanko Obradović, Antun Miletić',
    pdfPath: '/pdfs/4-brigada-slavonije.pdf',
    thumbnail: '/images/pdf-thumbs/4-brigada-slavonije.jpg',
    brigadeName: '4. brigada Slavonije',
    description: 'Spisak poginulih boraca i rukovodilaca brigade (četa i dužnost, datum i mesto rođenja, datum i mesto pogibije) i spisak ranjenih (jedinica i dužnost, kada su ranjeni), prilozi 2 i 3 knjige (str. 164 i dalje)'
  },
  {
    id: '12-slavonska-zene',
    title: 'Dvanaesta slavonska — spisak žena boraca',
    author: 'Jovan Kokot',
    pdfPath: 'https://znaci.org/00001/46_225.htm',
    thumbnail: '/images/pdf-thumbs/12-slavonska-zene.jpg',
    brigadeName: '12. proleterska slavonska brigada',
    description: 'Spisak žena boraca 12. proleterske slavonske brigade, poginulih, umrlih i preživelih, s kratkim životopisima (tekst na znaci.org, bez skenirane knjige; spisak svih boraca brigade knjiga je najavila, ali nije objavljen)'
  },
  {
    id: 'zagrebacki-odred',
    title: 'Zagrebački partizanski odred — popis boraca',
    author: 'Zbornik',
    pdfPath: '/pdfs/zagrebacki-odred.pdf',
    thumbnail: '/images/pdf-thumbs/zagrebacki-odred.jpg',
    brigadeName: 'Zagrebački partizanski odred',
    description: 'Popis boraca odreda iz zbornika dokumenata i sećanja (str. 407–418): uglavnom preživeli koji su se posle rata prijavili SUBNOR-u u Zelini i poginuli koje pominju ratni dokumenti i sećanja; selo, opština i sudbina. Bataljoni koji su celi otišli u brigadu „Matija Gubec“ i u Zagorsku brigadu nisu u njemu.'
  },
  {
    id: 'mosorski-odred',
    title: 'Mosorski partizanski odred — popis boraca',
    author: 'Miroslav Velić, Ante V. Petrić',
    pdfPath: '/pdfs/mosorski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/mosorski-odred.jpg',
    brigadeName: 'Mosorski partizanski odred',
    description: 'Popis boraca Mosorskog partizanskog odreda 1942–1944 (prvi deo popisa, str. 355–562): I mosorski odred, Mosorski bataljon, Leteća mosorska četa i odred od oktobra 1943. do novembra 1944, s rođenjem, zanimanjem, dolaskom u odred i sudbinom. Drugi deo popisa, borci komandi mesta i terenski radnici, nije unet.'
  },
  {
    id: 'turopoljsko-posavski-odred',
    title: 'Turopoljsko-posavski partizanski odred — spisak poginulih i umrlih',
    author: 'Višnja Huzjak',
    pdfPath: '/pdfs/turopoljsko-posavski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/turopoljsko-posavski-odred.jpg',
    brigadeName: 'Turopoljsko-posavski partizanski odred',
    description: 'Popis poginulih boraca odreda (99, s mestom rođenja, datumom i mestom pogibije) i streljani i umrli borci odreda u ratu (16), str. 17–20 (Muzej Turopolja, Velika Gorica 1983)'
  },
  {
    id: '1-zagorska',
    title: '1. zagorska brigada — spisak poginulih boraca i rukovodilaca',
    author: 'Vladimir Hlaić',
    pdfPath: '/pdfs/1-zagorska.pdf',
    thumbnail: '/images/pdf-thumbs/1-zagorska.jpg',
    brigadeName: '1. zagorska brigada',
    description: 'Spisak poginulih boraca i rukovodilaca brigade, od 8. maja 1944. do 15. maja 1945: godina i mesto rođenja, kada i gde su pali (str. 191–205)'
  },
  {
    id: '6-crnogorska',
    title: 'Šesta crnogorska udarna brigada — poginuli borci i starešine',
    author: 'Zbornik',
    pdfPath: '/pdfs/6-crnogorska.pdf',
    thumbnail: '/images/pdf-thumbs/6-crnogorska.jpg',
    brigadeName: '6. crnogorska brigada',
    description: 'Spisak poginulih boraca i starešina brigade, s onima koji su umrli od rana i bolesti: rođenje, dužnost, gde i kada su pali (str. 871 i dalje)'
  },
  {
    id: '11-krajiska-poginuli',
    title: 'Jedanaesta krajiška NOU brigada — spisak poginulih boraca',
    author: 'Đuro Milinović, Drago Karasijević',
    pdfPath: '/pdfs/11-krajiska-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/11-krajiska-poginuli.jpg',
    brigadeName: '11. krajiška (kozaračka) brigada',
    description: 'Spisak poginulih boraca brigade, po opštinama: rođenje, narodnost, zanimanje, kada su stupili u NOV, dužnost, gde i kada su pali (str. 439–463)'
  },
  {
    id: '11-krajiska-zene',
    title: 'Jedanaesta krajiška NOU brigada — spisak žena boraca',
    author: 'Đuro Milinović, Drago Karasijević',
    pdfPath: '/pdfs/11-krajiska-zene.pdf',
    thumbnail: '/images/pdf-thumbs/11-krajiska-zene.jpg',
    brigadeName: '11. krajiška (kozaračka) brigada',
    description: 'Spisak žena boraca koje su bile u brigadi, samo imena (str. 425)'
  },
  {
    id: '3-banijska',
    title: 'Sinovi Šamarice — spisak rukovodilaca i boraca Treće banijske brigade',
    author: 'Jovo Borojević',
    pdfPath: '/pdfs/3-banijska.pdf',
    thumbnail: '/images/pdf-thumbs/3-banijska.jpg',
    brigadeName: '3. banijska brigada',
    description: 'Spisak rukovodilaca i boraca brigade, samo imena (str. 195–205)'
  },
  {
    id: 'macvanski-odred',
    title: 'Mačvanski partizanski odred — spisak boraca',
    author: 'Dragoslav Parmaković',
    pdfPath: 'https://znaci.org/00001/48_102.htm',
    thumbnail: '/images/pdf-thumbs/macvanski-odred.jpg',
    brigadeName: 'Mačvanski (Podrinski) NOP odred',
    description: 'Spisak boraca Mačvanskog (Podrinskog) NOP odreda, prvi deo (jul 1941 – mart 1942): po mestima iz kojih su stupili u odred, s podacima o svakom (tekst na znaci.org, bez skenirane knjige; drugi deo nije objavljen)'
  },
  {
    id: 'posavski-odred',
    title: 'Posavski partizanski odred — borci odreda',
    author: 'Milosav Bojić',
    pdfPath: '/pdfs/posavski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/posavski-odred.jpg',
    brigadeName: 'Posavski partizanski odred',
    description: 'Spisak boraca Posavskog partizanskog odreda 1941: komanda, bolnica i bataljoni, s podacima o svakom (str. 565–742)'
  },
  {
    id: '51-divizija',
    title: 'Batinska bitka — borci 51. vojvođanske divizije poginuli i nestali',
    author: 'Nikola Božić',
    pdfPath: '/pdfs/51-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/51-divizija.jpg',
    brigadeName: '51. vojvođanska divizija',
    description: 'Borci 51. vojvođanske divizije poginuli i nestali u Batinskoj bici, novembra 1944: rođenje, dužnost, gde i kada su pali (str. 469–501)'
  },
  {
    id: '51-divizija-savic',
    title: '51. vojvođanska divizija',
    author: 'Sreta Savić',
    pdfPath: '/pdfs/51-divizija-savic.pdf',
    thumbnail: '/images/pdf-thumbs/51-divizija-savic.jpg',
    brigadeName: '51. vojvođanska divizija',
    description: 'Spisak poginulih boraca i rukovodilaca divizije od formiranja, 1. novembra 1944, do kraja rata, 15. maja 1945, po brigadama: 7, 8, 12. i 14. (slovačka), artiljerijska, prištapske jedinice; rođenje, dužnost, gde i kada su pali (str. 219–288)'
  },
  {
    id: 'borci-sutjeske-vrhovni-stab',
    title: 'Borci Sutjeske — pripadnici na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-vrhovni-stab.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-vrhovni-stab.jpg',
    brigadeName: 'Vrhovni štab NOV i POJ',
    description: 'Prozivka boraca sa Sutjeske: svi pripadnici Vrhovnog štaba, njegovih službi, Pratećeg bataljona i britanske vojne misije u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-1-proleterska-divizija',
    title: 'Borci Sutjeske — štab divizije na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-1-proleterska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-1-proleterska-divizija.jpg',
    brigadeName: '1. proleterska divizija',
    description: 'Prozivka boraca sa Sutjeske: štab divizije, njegove službe i prateće jedinice u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-2-proleterska-divizija',
    title: 'Borci Sutjeske — štab divizije na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-2-proleterska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-2-proleterska-divizija.jpg',
    brigadeName: '2. proleterska divizija',
    description: 'Prozivka boraca sa Sutjeske: štab divizije, njegove službe i prateće jedinice u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-3-udarna-divizija',
    title: 'Borci Sutjeske — štab divizije na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-3-udarna-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-3-udarna-divizija.jpg',
    brigadeName: '3. udarna divizija',
    description: 'Prozivka boraca sa Sutjeske: štab divizije, njegove službe i prateće jedinice u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-7-banijska-divizija',
    title: 'Borci Sutjeske — štab divizije na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-7-banijska-divizija.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-7-banijska-divizija.jpg',
    brigadeName: '7. banijska divizija',
    description: 'Prozivka boraca sa Sutjeske: štab divizije, njegove službe i prateće jedinice u bici, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: 'borci-sutjeske-centralna-bolnica',
    title: 'Borci Sutjeske — pripadnici na Sutjesci',
    author: 'Viktor Kučan',
    pdfPath: '/pdfs/borci-sutjeske-centralna-bolnica.pdf',
    thumbnail: '/images/pdf-thumbs/borci-sutjeske-centralna-bolnica.jpg',
    brigadeName: 'Centralna bolnica',
    description: 'Prozivka boraca sa Sutjeske: osoblje Centralne bolnice i ranjenici čija se jedinica nije mogla utvrditi, s podacima o svakom i šta je s njim bilo do kraja rata.'
  },
  {
    id: '3-licka',
    title: 'Treća lička brigada',
    author: 'Milan Šijan',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=b6ed63f4-83a8-458b-80d7-1d3dff4a056f/00000001/00000001/00009287',
    thumbnail: '/images/pdf-thumbs/3-licka.jpg',
    brigadeName: '3. lička proleterska brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca brigade i njeni narodni heroji (str. 361–413). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'pozarevacki-odred',
    title: 'Požarevački narodnooslobodilački partizanski odred',
    author: 'Strahinja Popović',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=b6ed63f4-83a8-458b-80d7-1d3dff4a056f/00000001/00000001/00006203',
    thumbnail: '/images/pdf-thumbs/pozarevacki-odred.jpg',
    brigadeName: 'Požarevački NOP odred',
    description: 'Popis boraca odreda od 1941. do oktobra 1944, s podacima o svakom (str. 238–307; priredio Miodrag Stojanović Kole). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: '1-proleterski-bataljon',
    title: 'Prvi proleterski bataljon Hrvatske',
    author: 'Bogdan Mamula, Rudi Bašić, Branko Vurdelja, Dušan Pekić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=b6ed63f4-83a8-458b-80d7-1d3dff4a056f/00000001/00000001/00009291',
    thumbnail: '/images/pdf-thumbs/1-proleterski-bataljon.jpg',
    brigadeName: '1. proleterski bataljon Hrvatske',
    description: 'Spisak boraca bataljona, s godinom i mestom rođenja i sudbinom (str. 262–277). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'pionirska-ceta',
    title: 'Ratnici od puške manji',
    author: 'Gojko Matić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=b6ed63f4-83a8-458b-80d7-1d3dff4a056f/00000001/00000001/00009857',
    thumbnail: '/images/pdf-thumbs/pionirska-ceta.jpg',
    brigadeName: 'Prva naoružana pionirska partizanska četa',
    description: 'Popis boraca čete koju je autor vodio kao komandir: rođenje, kad je ko postao borac, dužnost u četi i život posle rata (str. 125–132). Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'zbornik-heroja-1957',
    title: 'Zbornik narodnih heroja Jugoslavije',
    author: 'Grupa autora',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00001279',
    thumbnail: '/images/pdf-thumbs/zbornik-heroja.jpg',
    brigadeName: '',
    description: 'Portreti narodnih heroja proglašenih do 1957: rođenje, put u NOB, smrt ili život posle rata i dan kad je ko proglašen. Knjiga ne pripada jednoj jedinici: portret je dodat zapisu svakog heroja koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'narodni-heroji-1982-1',
    title: 'Narodni heroji Jugoslavije — tom 1',
    author: 'Grupa autora',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00007644',
    thumbnail: '/images/pdf-thumbs/narodni-heroji-1982-1.jpg',
    brigadeName: '',
    description: 'Biografije svih narodnih heroja, drugo izdanje (1982), prvi tom (A–M): rođenje, život pre rata, put u NOB, smrt ili život posle rata i dan kad je ko proglašen. Knjiga ne pripada jednoj jedinici: biografija je dodata zapisu svakog heroja koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'narodni-heroji-1982-2',
    title: 'Narodni heroji Jugoslavije — tom 2',
    author: 'Grupa autora',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00007645',
    thumbnail: '/images/pdf-thumbs/narodni-heroji-1982-2.jpg',
    brigadeName: '',
    description: 'Biografije svih narodnih heroja, drugo izdanje (1982), drugi tom (N–Ž): rođenje, život pre rata, put u NOB, smrt ili život posle rata i dan kad je ko proglašen. Knjiga ne pripada jednoj jedinici: biografija je dodata zapisu svakog heroja koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'trebinjci-pali',
    title: 'Trebinjci pali u borbi za slobodu 1941–1945',
    author: 'Grupa autora',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=a6202620-b210-4465-8bdc-5bcf4cbe8c24/00000001/00000001/00009701',
    thumbnail: '/images/pdf-thumbs/trebinjci-pali.jpg',
    brigadeName: '',
    description: 'Spomenica SUBNOR-a Trebinje (1974): borci sa područja opštine koji su pali u ratu (str. 13–96) i borci iz cele Jugoslavije koji su poginuli kod Trebinja (str. 159–174), s rođenjem, jedinicama i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spisak žrtava fašističkog terora iz iste knjige nije unet. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'pali-za-lepsa-svitanja',
    title: 'Pali za lepša svitanja',
    author: 'Al. Tadić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00008604',
    thumbnail: '/images/pdf-thumbs/pali-za-lepsa-svitanja.jpg',
    brigadeName: '',
    description: 'Majke narodnih heroja pričaju o svojim sinovima i kćerima (1967); nad svakom pričom je kratka biografija heroja: rođenje, zanimanje, KPJ, NOB, smrt i dan kad je proglašen. Knjiga ne pripada jednoj jedinici: biografija je dodata zapisu svakog heroja koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'ofanziva-1942-poginuli',
    title: 'Ofanziva proleterskih brigada u leto 1942.',
    author: 'Mišo Leković',
    pdfPath: '/pdfs/ofanziva-1942-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/ofanziva-1942-poginuli.jpg',
    brigadeName: '',
    description: 'Spisak boraca 1, 2, 3. i 4. proleterske brigade poginulih i nestalih u pohodu u zapadnu Bosnu, od 24. juna do 30. septembra 1942 (str. 698–711), po brigadama i bataljonima, s rođenjem, zanimanjem i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on.'
  },
  {
    id: 'hak-20-gospic-perusic',
    title: 'Kotar Gospić i kotar Perušić u narodnooslobodilačkom ratu 1941–1945.',
    author: 'Zdenka Krivokuća',
    pdfPath: '/pdfs/hak-20-gospic-perusic.pdf',
    thumbnail: '/images/pdf-thumbs/hak-20-gospic-perusic.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 20): pali borci s područja kotara Gospić i kotara Perušić 1941–1945 (str. 986–1045) i nosioci Partizanske spomenice 1941 (str. 1194–1209), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-10-korenica-udbina',
    title: 'Kotar Korenica i kotar Udbina u NOR-u i socijalističkoj izgradnji',
    author: 'Gojko Vezmar',
    pdfPath: '/pdfs/hak-10-korenica-udbina.pdf',
    thumbnail: '/images/pdf-thumbs/hak-10-korenica-udbina.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 10): pali borci s područja kotara Korenica i kotara Udbina 1941–1945 (str. 990–1039), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  // Village chronicles of the Poreklo library ("Hronike sela" and others): the fighters' lists, a book across units each
  {
    id: 'hronika-prigrevica',
    title: 'Prigrevica',
    author: 'Zorica Korica-Aćimović',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000397',
    thumbnail: '/images/pdf-thumbs/hronika-prigrevica.jpg',
    brigadeName: '',
    description: 'Monografija sela Prigrevica kod Apatina (1997), u koje su posle rata naseljene porodice boraca iz Like i Banije: poginuli, umrli i nestali borci NOR-a iz tih porodica (str. 307–331) i nosioci Partizanske spomenice 1941. (str. 339–353), s rođenjem, jedinicom i smrću ili životom posle rata. Spiskovi boraca koji su u rat stupili kasnije, samo s imenom, nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-medak',
    title: 'Lika i Srbi Medačke opštine',
    author: 'Dušan Uzelac',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000261',
    thumbnail: '/images/pdf-thumbs/hronika-medak.jpg',
    brigadeName: '',
    description: 'Monografija sela nekadašnje opštine Medak kod Gospića (2004): borci NOR-a iz tih sela koji su poginuli u borbi s neprijateljem, po selima (str. 434–465), i nosioci Partizanske spomenice 1941. (str. 506–513), s rođenjem, jedinicom i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-hasani',
    title: 'Hašani',
    author: 'Jovan Jakšić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000050',
    thumbnail: '/images/pdf-thumbs/hronika-hasani.jpg',
    brigadeName: '',
    description: 'Monografija sela Hašani kod Bosanske Krupe (1991): poginuli, umrli i nestali borci NOR-a iz sela (str. 135–138), nosioci Partizanske spomenice 1941. (str. 138) i ostali preživeli učesnici NOR-a, samo s imenom (str. 139). Preživeli kojima je borački staž priznat za rad za NOP nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-podgocka-naselja',
    title: 'Podgočka naselja trsteničkog kraja',
    author: 'Momčilo R. Todosijević',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000784',
    thumbnail: '/images/pdf-thumbs/hronika-podgocka-naselja.jpg',
    brigadeName: '',
    description: 'Monografija sela pod Gočem kod Trstenika (2008): borci iz Gornjeg Ribnika poginuli na Sremskom frontu (str. 194–195) i učesnici NOR-a iz Odžaka koji su poginuli ili nestali u ratu (str. 344–345). Spiskovi poginulih od četnika i žrtava fašističkog terora nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-prekopcelica',
    title: 'Prekopčelica, predgrađe Caričinog Grada',
    author: 'Nikola C. Stanković',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000722',
    thumbnail: '/images/pdf-thumbs/hronika-prekopcelica.jpg',
    brigadeName: '',
    description: 'Monografija sela Prekopčelica kod Lebana (2012): borci iz sela po brigadama i odredima NOVJ u kojima su bili (str. 121–124) i poginuli u partizanima (str. 126). Pripadnici pozadinskih jedinica i učesnici koje su naveli samo rođaci nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-brezovica-stublica',
    title: 'Brezovica i Stublica',
    author: 'Milan Bogićević, Milan Panić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000849',
    thumbnail: '/images/pdf-thumbs/hronika-brezovica-stublica.jpg',
    brigadeName: '',
    description: 'Monografija sela Brezovica i Stublica kod Trstenika (2015): učesnici NOR-a iz Brezovice mobilisani oktobra 1944. i poginuli i nestali u ratu (str. 113–115) i učesnici NOR-a iz Stublice (str. 478–479). Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-makce',
    title: 'Makce',
    author: 'Zorica Korica-Aćimović',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000430',
    thumbnail: '/images/pdf-thumbs/hronika-makce.jpg',
    brigadeName: '',
    description: 'Monografija sela Makce kod Velikog Gradišta (2000): Makčani poginuli, umrli i nestali u ratu, većinom borci 25. divizije (str. 62–64), i učesnici NOR-a koji su preživeli rat, s godinom rođenja i odlikovanjem (str. 64–66). Žrtve fašističkog terora iz istog spiska nisu unete. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-donje-vidovo',
    title: 'Donje Vidovo',
    author: 'Miroslav Dimitrijević',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000130',
    thumbnail: '/images/pdf-thumbs/hronika-donje-vidovo.jpg',
    brigadeName: '',
    description: 'Monografija sela Donje Vidovo kod Paraćina (1997): iz spiska poginulih meštana uneti su samo oni koje knjiga beleži kao učesnike NOB-a (str. 127), ne i žrtve fašističkog terora i ostali poginuli. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-petrlas',
    title: 'Petrlaš: selo koje nestaje',
    author: 'Stanimir Stavrov',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000196',
    thumbnail: '/images/pdf-thumbs/hronika-petrlas.jpg',
    brigadeName: '',
    description: 'Monografija sela Petrlaš kod Dimitrovgrada (2001): borci iz Petrlaša u Prvoj caribrodskoj, 8, 10. i 12. srpskoj brigadi, 13. dopunskom bataljonu i drugim jedinicama NOVJ (str. 348). Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-labukovo',
    title: 'Labukovo: zapisi obojeni lirikom',
    author: 'Srbislav Jocić',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000721',
    thumbnail: '/images/pdf-thumbs/hronika-labukovo.jpg',
    brigadeName: '',
    description: 'Monografija sela Labukovo kod Svrljiga (2007): meštani poginuli u NOB-u od 1941. do 1945. (str. 44); oni koje knjiga navodi kao taoce, žrtve terora i logoraše nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-beli-breg',
    title: 'Beli Breg (Aleksinac)',
    author: 'Slobodan V. Stanojević',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000464',
    thumbnail: '/images/pdf-thumbs/hronika-beli-breg.jpg',
    brigadeName: '',
    description: 'Monografija sela Beli Breg kod Aleksinca (2009): meštani učesnici NOR-a, s godinom rođenja, danom kad su stupili u jedinicu i jedinicom, i poginuli i umrli neposredno posle rata (str. 113–114). Zarobljenici, internirani i vojnici Jugoslovenske vojske iz iste tabele nisu uneti. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hronika-donja-gorevnica',
    title: 'Donja Gorevnica (zemlja i ljudi)',
    author: 'Radul Marković, Miloljub S. Pantović',
    pdfPath: 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id=0fa57049-5775-4da5-a8e6-fb3d1a4ecdad/00000001/00000001/00000094',
    thumbnail: '/images/pdf-thumbs/hronika-donja-gorevnica.jpg',
    brigadeName: '',
    description: 'Monografija sela Donja Gorevnica kod Čačka (1996): iz spiska palih boraca i žrtava iz sela uneti su samo borci (str. 233–238), ne i žrtve terora i vojnici Jugoslovenske vojske. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Knjiga je skenirana u Digitalnoj biblioteci Porekla, koju otvaraju samo članovi Porekla.'
  },
  {
    id: 'hak-14-donji-lapac',
    title: 'Kotar Donji Lapac u narodnooslobodilačkom ratu 1941–1945.',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-14-donji-lapac.pdf',
    thumbnail: '/images/pdf-thumbs/hak-14-donji-lapac.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 14): pali borci s područja kotara Donji Lapac 1941–1945 (str. 1041–1094), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-13-gracac',
    title: 'Kotar Gračac u narodnooslobodilačkom ratu 1941–1945.',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-13-gracac.pdf',
    thumbnail: '/images/pdf-thumbs/hak-13-gracac.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 13): pali borci s područja kotara Gračac 1941–1945 (str. 917–965), po opštinama, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-7-plascanska-dolina',
    title: 'Plaščanska dolina i okolica u NOR-u 1941–1945.',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-7-plascanska-dolina.pdf',
    thumbnail: '/images/pdf-thumbs/hak-7-plascanska-dolina.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 7): pali borci s područja Plaščanske doline i okoline 1941–1945 (str. 689–701), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-19-vojnic',
    title: 'Kotar Vojnić u narodnooslobodilačkoj borbi i socijalističkoj revoluciji',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-19-vojnic.pdf',
    thumbnail: '/images/pdf-thumbs/hak-19-vojnic.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 19): pali borci s područja kotara Vojnić 1941–1945 (str. 1123–1177), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-18-slunj-veljun',
    title: 'Kotar Slunj i kotar Veljun u NOR i socijalističkoj izgradnji, 2. dio',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-18-slunj-veljun.pdf',
    thumbnail: '/images/pdf-thumbs/hak-18-slunj-veljun.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 18): pali borci s područja kotara Slunj i kotara Veljun 1941–1945 (str. 921–977), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-15-duga-resa',
    title: 'Duga Resa: radovi iz dalje prošlosti, NOB-e i socijalističke izgradnje',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-15-duga-resa.pdf',
    thumbnail: '/images/pdf-thumbs/hak-15-duga-resa.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 15): pali borci s područja sadašnje opštine Duga Resa 1941–1945 (str. 1060–1090), po opštinama i selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa iz iste knjige nisu uneti.'
  },
  {
    id: 'hak-12-dreznica',
    title: 'Partizanska Drežnica',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-12-dreznica.pdf',
    thumbnail: '/images/pdf-thumbs/hak-12-dreznica.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 12): pali borci s područja opštine Drežnica 1941–1945 (str. 865–876), po selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spisak žrtava fašističkog terora i rata iz iste knjige nije unet.'
  },
  {
    id: 'hak-16-gornje-dubrave',
    title: 'Općina Gornje Dubrave',
    author: 'Grupa autora',
    pdfPath: '/pdfs/hak-16-gornje-dubrave.pdf',
    thumbnail: '/images/pdf-thumbs/hak-16-gornje-dubrave.jpg',
    brigadeName: '',
    description: 'Iz zbornika Historijskog arhiva u Karlovcu (knj. 16): pali borci s područja opštine Gornje Dubrave 1941–1945 (str. 889–899), po selima, s rođenjem, putem u NOB i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spisak žrtava fašističkog terora i rata iz iste knjige nije unet.'
  },
  {
    id: 'sjenicak',
    title: 'Sjeničak: kronika kordunaškog sela',
    author: 'Mile Mrkalj',
    pdfPath: '/pdfs/sjenicak.pdf',
    thumbnail: '/images/pdf-thumbs/sjenicak.jpg',
    brigadeName: '',
    description: 'Hronika kordunaškog sela iz izdanja Historijskog arhiva u Karlovcu, s dva njena spiska: pali i umrli borci 1941–1945 iz Donjeg, Gornjeg i Lasinjskog Sjeničaka (str. 330–338), po selima, s rođenjem, putem u NOB i smrću, i nosioci Partizanske spomenice 1941 (str. 385–389). Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Spiskovi žrtava fašističkog terora i umrlih od tifusa i prehlade iz iste knjige nisu uneti.'
  },
  {
    id: 'tuzla-spomen-knjiga',
    title: 'Spomen-knjiga poginulih tuzlanskih boraca NOR-a i žrtava fašističkog terora 1941–1945.',
    author: 'Grupa autora',
    pdfPath: '/pdfs/tuzla-spomen-knjiga.pdf',
    thumbnail: '/images/pdf-thumbs/tuzla-spomen-knjiga.jpg',
    brigadeName: '',
    description: 'Spomen-knjiga opštine Tuzla: biografije njenih učesnika NOR-a koji su poginuli 1941–1945 (str. 13–300), rođenih, nastanjenih ili zaposlenih u Tuzli ili onih koji su iz nje otišli u partizane, često s fotografijom, s jedinicom, rođenjem i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on. Drugi deo knjige, žrtve fašističkog terora, nije unet.'
  },
  {
    id: 'krusevac-1944-poginuli',
    title: 'Oslobođenje Kruševca 1944. godine',
    author: 'Grupa autora',
    pdfPath: '/pdfs/krusevac-1944-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/krusevac-1944-poginuli.jpg',
    brigadeName: '',
    description: 'Spisak boraca poginulih u borbama za oslobođenje Kruševca septembra i oktobra 1944, po jedinicama: 4. proleterska crnogorska, 3, 6. i 17. srpska brigada i Komanda kruševačkog vojnog područja (str. 273–283), s rođenjem i smrću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on.'
  },
  {
    id: 'u-rovovima-srema-poginuli',
    title: 'U rovovima Srema',
    author: 'Milorad Gončin',
    pdfPath: '/pdfs/u-rovovima-srema-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/u-rovovima-srema-poginuli.jpg',
    brigadeName: '',
    description: 'Spisak boraca poginulih na Sremskom frontu (str. 230–267), po brigadama i po mestu gde su pali, samo imena, ponekad s dužnošću. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on, po imenu, brigadi i mestu pogibije.'
  },
  {
    id: 'sremski-front-poginuli',
    title: 'Sremski front',
    author: 'Dragoljub Tmušić',
    pdfPath: '/pdfs/sremski-front-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/sremski-front-poginuli.jpg',
    brigadeName: '',
    description: 'Spiskovi boraca poginulih na Sremskom frontu od oktobra 1944. do aprila 1945, po divizijama i brigadama, svaki posle kratke istorije jedinice: samo imena, ponekad s očevim inicijalom. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on, po imenu, brigadi i vremenu pogibije. Spiskovi palih crvenoarmejaca s kraja knjige nisu uneti.'
  },
  {
    id: '1-krajiska',
    title: 'Prva krajiška udarna proleterska brigada',
    author: 'Milorad Gončin, Stevo Rauš',
    pdfPath: '/pdfs/1-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/1-krajiska.jpg',
    brigadeName: '1. krajiška proleterska udarna brigada',
    description: 'Spisak poginulih, umrlih i nestalih boraca brigade, 2.127 imena: rođenje, kada su stupili u NOB i u brigadu, četa i bataljon, dužnost, kada i gde su pali i gde su sahranjeni (str. 331–442). Podatke je istražio i obradio Slobodan Spegar Spego.'
  },
  {
    id: '13-krajiska',
    title: 'Trinaesta krajiška brigada',
    author: 'Milan N. Zorić',
    pdfPath: '/pdfs/13-krajiska.pdf',
    thumbnail: '/images/pdf-thumbs/13-krajiska.jpg',
    brigadeName: '13. krajiška brigada',
    description: 'Dva spiska: borci i rukovodioci koji su bili u brigadi u avgustu i septembru 1943, s mestom, dužnošću i, za poginule, kada su pali i gde su sahranjeni; članovi KPJ partijske organizacije brigade u maju 1945, s danom prijema u Partiju i dužnošću (str. 365–404).'
  },
  {
    id: 'mostarski-bataljon',
    title: 'Mostarski bataljon',
    author: 'Enver Ćemalović',
    pdfPath: '/pdfs/mostarski-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/mostarski-bataljon.jpg',
    brigadeName: 'Mostarski bataljon',
    description: 'Borci Konjičkog bataljona (septembar 1941 — jun 1942), Mostarskog bataljona (jun 1942 — jun 1943) i Mostarskog bataljona u Mostarskom partizanskom odredu (jun 1943 — maj 1944), svaki s kratkim životopisom: rođenje, zanimanje, SKOJ i KPJ, dolazak u bataljon, dužnost i sudbina (str. 329–392).'
  },
  {
    id: 'cacanski-odred',
    title: 'Čačanski narodnooslobodilački partizanski odred „Dr Dragiša Mišović“',
    author: 'Milojica Pantelić, Radovan M. Marinković, Vladimir Nikšić',
    pdfPath: '/pdfs/cacanski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/cacanski-odred.jpg',
    brigadeName: 'Čačanski NOP odred „Dr Dragiša Mišović“',
    description: 'Pali borci odreda, po krajevima (Dragačevo, Ljubić, Trnava, Takovo, Čačak) i selima: otac, zanimanje, rođenje, bataljon u kome je borac bio i kako je i gde poginuo.'
  },
  {
    id: '5-srpska',
    title: 'Peta srpska NOU brigada',
    author: 'Stanimir Jovanović, Dragoljub Mirčetić',
    pdfPath: '/pdfs/5-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/5-srpska.jpg',
    brigadeName: '5. srpska brigada',
    description: 'Spisak poginulih i umrlih boraca i rukovodilaca brigade (prilog br. 2): godina i mesto rođenja, zanimanje, kada je ko stupio u NOVJ, bataljon i dužnost, kada i gde je pao i gde je sahranjen (str. 450–510).'
  },
  {
    id: '18-srpska',
    title: 'Osamnaesta srpska brigada',
    author: 'Krstivoje Milosavljević',
    pdfPath: '/pdfs/18-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/18-srpska.jpg',
    brigadeName: '18. srpska brigada',
    description: '„Oni su se borili u 18. srpskoj brigadi“: 5.047 boraca i rukovodilaca brigade po autorovom računu, od toga 780 poginulih, 787 ranjenih, 47 nestalih i 49 umrlih od bolesti, s godinom i mestom rođenja, dužnošću i time gde je ko pao ili bio ranjen (str. 313–426). Spisak je sastavljen iz evidencije SUBNOR-a, ratne sanitetske dokumentacije 25. divizije i sačuvanih dokumenata brigade.'
  },
  {
    id: 'cacanski-kraj-pali',
    title: 'Čačanski kraj u NOB — pali borci i žrtve',
    author: 'Grupa autora',
    pdfPath: '/pdfs/cacanski-kraj-pali.pdf',
    thumbnail: '/images/pdf-thumbs/cacanski-kraj-pali.jpg',
    brigadeName: '',
    description: 'Poginuli i stradali iz čačanskog kraja 1941–1945, po krajevima (Dragačevo, Ljubić, Takovo, Trnava, Čačak) i selima: otac, zanimanje, rođenje, jedinica i kako je ko poginuo. Uneti su samo borci; civilne žrtve i četnici nisu. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on.'
  },
  {
    id: 'pozega-pali',
    title: 'Požega u NOR i revoluciji 1941—1945',
    author: 'Jovan R. Radovanović',
    pdfPath: '/pdfs/pozega-pali.pdf',
    thumbnail: '/images/pdf-thumbs/pozega-pali.jpg',
    brigadeName: '',
    description: 'Prilog Dragoljuba Munjića: spisak palih boraca NOR-a, žrtava fašističkog terora i civilnih žrtava rata u srezu požeškom, po selima, s rođenjem, jedinicom i time kako je ko poginuo. Uneti su samo borci; civilne žrtve, saradnici NOP-a i vojnici bivše jugoslovenske vojske nisu. Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on.'
  },
  {
    id: '4-pomorski-sektor',
    title: 'Četvrti pomorski obalni sektor Mornarice NOVJ',
    author: 'Kažimir Pribilović',
    pdfPath: '/pdfs/4-pomorski-sektor.pdf',
    thumbnail: '/images/4-pomorski-sektor.jpg',
    brigadeName: 'IV pomorski obalni sektor',
    description: 'Popis boraca IV POS-a 1943–1945, koji su sastavili Sekcija boraca sektora i autor (4.702 imena, sa mestom odakle je ko), i poginuli i umrli borci sektora, sa dužnošću i kako su pali (str. 418–478).'
  },
  {
    id: 'viski-bataljon',
    title: 'Vis 1941-1945',
    author: 'Veseljko Huljić',
    pdfPath: '/pdfs/viski-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/viski-bataljon.jpg',
    brigadeName: 'Viški dobrovoljački bataljon',
    description: 'Spisak boraca Viškog dobrovoljačkog bataljona na Visu krajem januara 1944: komanda, čete, vodovi i desetine Biševa i Oključne (str. 538–539).'
  },
  {
    id: 'kokrski-odred-1',
    title: 'Kokrški odred - narodnoosvobodilni boj pod Karavankami I',
    author: 'Ivan Jan',
    pdfPath: '/pdfs/kokrski-odred-1.pdf',
    thumbnail: '/images/pdf-thumbs/kokrski-odred.jpg',
    brigadeName: 'Kokrški odred',
    description: 'Spisak boraca Kokrškog odreda prvog sastava, jun 1942 - januar 1943, po štabu, bataljonima i četama: odakle je ko, dužnosti i šta je s kim bilo (str. 509–525).'
  },
  {
    id: 'kokrski-odred',
    title: 'Kokrški odred - narodnoosvobodilni boj pod Karavankami III',
    author: 'Ivan Jan',
    pdfPath: '/pdfs/kokrski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/kokrski-odred.jpg',
    brigadeName: 'Kokrški odred',
    description: 'Spisak boraca Drugog kokrškog odreda, autorova rekonstrukcija po spiskovima i dokumentima odreda: štabovi, obaveštajni centar i tačke, kurirske stanice, sanitet, radionice i bataljoni po četama i periodima, s godinom rođenja i ko je pao (str. 453–478).'
  },
  {
    id: 'cankarjev-bataljon',
    title: 'Cankarjev bataljon in dražgoška bitka',
    author: 'Ivan Jan',
    pdfPath: '/pdfs/cankarjev-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/cankarjev-bataljon.jpg',
    brigadeName: 'Cankarjev bataljon',
    description: 'Formacija bataljona u Dražgošama, španski borci i narodni heroji, poginuli cankarjevci po bitkama 1941–1942, preživeli nosioci Spomenice 1941. i ostali preživeli učesnici dražgoške bitke (str. 338–346).'
  },
  {
    id: 'novosadski-odred',
    title: 'Novosadski partizanski odred - dva puta rođen',
    author: 'Vanja Sanader',
    pdfPath: '/pdfs/novosadski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/novosadski-odred.jpg',
    brigadeName: 'Novosadski partizanski odred',
    description: 'Popis pripadnika Novosadskog partizanskog odreda 1941. i 1944. godine: ime, dužnost, odakle je ko i od kada (str. 85–92).'
  },
  {
    id: 'deveta',
    title: 'Deveta brigada II',
    author: 'Velimir Kraševec-Igor',
    pdfPath: '/pdfs/deveta.pdf',
    thumbnail: '/images/pdf-thumbs/deveta.jpg',
    brigadeName: 'Deveta brigada (Kočevska)',
    description: 'Seznam borcev IX. SNOB Kočevske: ime, godina i mesto rođenja, a za poginule godina i mesto pogibije (str. 425–446).'
  },
  {
    id: '4-prekomorska',
    title: 'Četrta prekomorska brigada',
    author: 'Edvin Pervanje, Jože A. Hočevar',
    pdfPath: '/pdfs/4-prekomorska.pdf',
    thumbnail: '/images/pdf-thumbs/4-prekomorska.jpg',
    brigadeName: '4. prekomorska brigada',
    description: 'Spisak poginulih i umrlih boraca i komandni kadar brigade: štab, komanda mesta, bataljoni, samostalna četa i komande četa (str. 327–333).'
  },
  {
    id: '9-srpska',
    title: 'Deveta srpska udarna brigada u stroju i s narodom',
    author: 'spomen-knjiga',
    pdfPath: '/pdfs/9-srpska.pdf',
    thumbnail: '/images/pdf-thumbs/9-srpska.jpg',
    brigadeName: '9. srpska brigada',
    description: 'Stroj u Rečici: 377 boraca na dan formiranja, 11. marta 1944; komandni sastav brigade, bataljona i četa sa datumima dužnosti; bolničarke i borci, stroj žena. Imenik boraca s kratkim životopisom (str. 47–372) znaci.org nema.'
  },
  {
    id: 'kozjanski-odred',
    title: 'Kozjanski odred II',
    author: 'Tomaž Teropšič',
    pdfPath: '/pdfs/kozjanski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/kozjanski-odred.jpg',
    brigadeName: 'Kozjanski odred',
    description: 'Seznam borcev in bork Kozjanskega odreda: 3.495 osoba od osnivanja do rasformiranja, s datumom i mestom rođenja, dolaskom u NOV, zanimanjem i napomenom (gde je ko bio, ko je pao); stranice su ovde crno-bele, tekst kao u knjizi.'
  },
  {
    id: 'proleterski-bataljon-bk',
    title: 'Proleterski bataljon Bosanske krajine',
    author: 'Savo Trikić, Dušan Repajić',
    pdfPath: '/pdfs/proleterski-bataljon-bk.pdf',
    thumbnail: '/images/pdf-thumbs/proleterski-bataljon-bk.jpg',
    brigadeName: 'Proleterski bataljon Bosanske krajine',
    description: 'Spisak boraca bataljona: biografija svakog, uz njegovu fotografiju, od rođenja i dolaska u Kozaračku, Grmečku ili Drvarsku proletersku četu do pogibije ili kraja rata (str. 256–362).'
  },
  {
    id: '1-tenkovski-bataljon',
    title: 'Prvi tenkovski bataljon',
    author: 'Vujo Vidaković',
    pdfPath: '/pdfs/1-tenkovski-bataljon.pdf',
    thumbnail: '/images/pdf-thumbs/1-tenkovski-bataljon.jpg',
    brigadeName: 'Prvi tenkovski bataljon',
    description: 'Popis pripadnika Tenkovskog voda Grupe partizanskih odreda za Liku, Tenkovske čete 1. korpusa i Tenkovskog bataljona Glavnog štaba NOV i PO Hrvatske (251 ime, str. 337–340).'
  },
  {
    id: '3-diverzantski-odred',
    title: 'Treći diverzantski odred',
    author: 'Vukašin Karanović',
    pdfPath: '/pdfs/3-diverzantski-odred.pdf',
    thumbnail: '/images/pdf-thumbs/3-diverzantski-odred.jpg',
    brigadeName: 'Treći diverzantski odred',
    description: 'Pregled boraca i starešina 3. diverzantske grupe, čete, bataljona i odreda (imena, sa oznakom poginulih i umrlih posle rata) i pregled poginulih diverzanata sa dužnošću i godinom (prilog IV, str. 587–591).'
  },
  {
    id: '1-2-prekomorska',
    title: 'Prva in druga prekomorska brigada',
    author: 'Srečko Vilhar, Albert Klun',
    pdfPath: '/pdfs/1-2-prekomorska.pdf',
    thumbnail: '/images/pdf-thumbs/1-2-prekomorska.jpg',
    brigadeName: '1. i 2. prekomorska brigada',
    description: 'Spisak poginulih boraca i borkinja obe brigade (rođenje, kada i gde je ko pao) i komandni kadar u logorima Carbonara i Gravina, na Korčuli, Hvaru i Visu, i komande četa (str. 357–372).'
  },
  {
    id: '5-prekomorska',
    title: 'Peta prekomorska brigada',
    author: 'Albert Klun, Rado Bordon i dr.',
    pdfPath: '/pdfs/5-prekomorska.pdf',
    thumbnail: '/images/pdf-thumbs/5-prekomorska.jpg',
    brigadeName: '5. prekomorska brigada',
    description: 'Spisak poginulih boraca i borkinja (256: rođenje, kada i gde je ko pao) i komandni kadar brigade, bataljona i četa (str. 283–301).'
  },
  {
    id: 'sercerjeva',
    title: 'Šercerjeva brigada I',
    author: 'Lado Ambrožič-Novljan',
    pdfPath: '/pdfs/sercerjeva.pdf',
    thumbnail: '/images/pdf-thumbs/sercerjeva.jpg',
    brigadeName: 'Šercerjeva brigada',
    description: 'Spisak dobrovoljaca Šercerjeve brigade od osnivanja 6. oktobra 1942. do kraja februara 1943. (ime, partizansko ime i mesto) i spisak poginulih do kraja 1943, po mestu i danu pogibije (str. 509–523).'
  },
  {
    id: 'kosovelova',
    title: 'Kosovelova brigada',
    author: 'Stanko Petelin',
    pdfPath: '/pdfs/kosovelova.pdf',
    thumbnail: '/images/pdf-thumbs/kosovelova.jpg',
    brigadeName: 'Kosovelova brigada',
    description: 'Spisak poginulih, nestalih i umrlih od rana (504 imena: rođenje, mesto, kada i gde je ko pao) i komandni kadar brigade i njenih bataljona sa datumima dužnosti (str. 803–824).'
  },
  {
    id: 'eskadrile-novj',
    title: 'Prva i druga eskadrila NOVJ',
    author: 'Predrag Pejčić',
    pdfPath: '/pdfs/eskadrile-novj.pdf',
    thumbnail: '/images/pdf-thumbs/eskadrile-novj.jpg',
    brigadeName: '1. i 2. eskadrila NOVJ',
    description: 'Spiskovi ljudstva prve i druge eskadrile NOVJ (352. i 351. skvadron RAF-a): broj, čin, dužnost, rođenje i kako je ko došao u eskadrile, sa Bliskog istoka, iz italijanskog zarobljeništva ili iz zemlje; na kraju imena čija eskadrila nije utvrđena (str. 331–354).'
  },
  {
    id: '42-vazduhoplovna',
    title: '42. vazduhoplovna divizija',
    author: 'Predrag Pejčić',
    pdfPath: '/pdfs/42-vazduhoplovna.pdf',
    thumbnail: '/images/pdf-thumbs/42-vazduhoplovna.jpg',
    brigadeName: '42. vazduhoplovna divizija',
    description: 'Spisak ljudstva divizije po pukovima (421, 422. i 423. vazduhoplovni puk), štabu, samostalnoj četi i aeroplanskim radionicama: čin i dužnost (str. 291–321).'
  },
  {
    id: 'bitka-kod-oborova-poginuli',
    title: 'Bitka kod Oborova',
    author: 'Milan Brunović, Tomo Sović',
    pdfPath: '/pdfs/bitka-kod-oborova-poginuli.pdf',
    thumbnail: '/images/pdf-thumbs/bitka-kod-oborova-poginuli.jpg',
    brigadeName: '',
    description: 'Imena 128 boraca 2. moslavačke brigade i Posavskog partizanskog odreda poginulih kod Oborova 29. marta 1944 (str. 158–160). Knjiga ne pripada jednoj jedinici: zapis iz nje dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on.'
  },
  {
    id: 'zrtve-rata-1964-slo',
    title: 'Žrtve rata 1941–1945: SR Slovenija',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Slo.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-slo.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Slovenije, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-hrv',
    title: 'Žrtve rata 1941–1945: SR Hrvatska',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Hrv.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-hrv.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Hrvatske, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-bih',
    title: 'Žrtve rata 1941–1945: SR Bosna i Hercegovina',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/BiH.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-bih.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Bosne i Hercegovine, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-crg',
    title: 'Žrtve rata 1941–1945: SR Crna Gora',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Crg.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-crg.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Crne Gore, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-mak',
    title: 'Žrtve rata 1941–1945: SR Makedonija',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Mak.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-mak.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Makedonije, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-srb',
    title: 'Žrtve rata 1941–1945: SR Srbija (bez pokrajina)',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Srb.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-srb.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja uže Srbije, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-kos',
    title: 'Žrtve rata 1941–1945: Kosovo i Metohija',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Kos.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-kos.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Kosova i Metohije, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  },
  {
    id: 'zrtve-rata-1964-voj',
    title: 'Žrtve rata 1941–1945: Vojvodina',
    author: 'Savezni zavod za statistiku (popis 1964); Muzej žrtava genocida',
    pdfPath: 'https://www.muzejgenocida.rs/wp-content/uploads/2024/03/Voj.pdf',
    thumbnail: '/images/pdf-thumbs/zrtve-rata-1964-voj.jpg',
    brigadeName: '',
    description: 'Popis žrtava rata iz 1964, sa područja Vojvodine, po opštinama i selima: uneti su samo borci NOB-a koji su poginuli ili umrli u ratu, ne i žrtve terora. Popis ne pripada jednoj jedinici: zapis iz njega dodat je zapisu svakog borca koji je na sajtu i za koga se pouzdano zna da je to on; ostali su među Ostalim borcima. Popis je objavio Muzej žrtava genocida.'
  }
]
