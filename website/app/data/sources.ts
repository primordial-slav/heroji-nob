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
    thumbnail: '/images/pdf-thumbs/placeholder.jpg',
    brigadeName: '2. dalmatinska proleterska udarna brigada',
    description: 'Popis boraca 2. dalmatinske proleterske brigade NOVJ'
  },
  {
    id: '4-splitska-brigada',
    title: '4. splitska udarna brigada',
    author: 'Vinko Uvodić (ur.)',
    pdfPath: '/pdfs/4-splitska-brigada.pdf',
    thumbnail: '/images/pdf-thumbs/placeholder.jpg',
    brigadeName: '4. splitska udarna brigada',
    description: 'Popis poginulih i preživjelih boraca brigade'
  },
  {
    id: 'prva-vojvodjanska',
    title: 'Prva vojvođanska brigada',
    author: 'Vojnoistorijski institut',
    pdfPath: '/pdfs/prva-vojvodjanska.pdf',
    thumbnail: '/images/pdf-thumbs/placeholder.jpg',
    brigadeName: 'Prva vojvođanska brigada',
    description: 'Spisak boraca Prve vojvođanske brigade'
  }
]
