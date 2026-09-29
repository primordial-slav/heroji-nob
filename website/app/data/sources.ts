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
    id: 'treca-proleterska-brigada',
    title: 'Treća proleterska (sandžačka) brigada',
    author: 'Žarko Vidović',
    pdfPath: '/pdfs/treca-proleterska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/treca-proleterska-brigada.jpg',
    brigadeName: 'Treća proleterska (sandžačka) brigada',
    description: 'Monografija, Biblioteka Ratna prošlost naših naroda, knj. 144'
  },
  {
    id: 'ljubljanska-brigada',
    title: '10. slovenska NOV brigada „Ljubljanska"',
    author: 'Boris Vojlah',
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
  }
]
