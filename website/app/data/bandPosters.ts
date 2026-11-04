// The Partisans' wartime posters pasted in the home band's margins (components/BandPosters.tsx): each once, none on both
// sides, the languages and the women spread out. `o` is how far out from the column a poster stands, `y` from the band's
// top, `h` and `w` its size in px, `turn` its tilt in degrees. scripts/make_band_posters.py makes the prints.
export type BandPoster = { id: string; o: number; y: number; h: number; w: number; turn: number; title: string; author: string; year: string }

export const BAND_POSTERS: { left: BandPoster[]; right: BandPoster[] } = {
  left: [
    { id: 'zena-u-borbi', o: 26, y: 22, h: 174, w: 134, turn: -3, title: 'Žena u borbi', author: '', year: '1943' },
    { id: 'miting-zena', o: 40, y: 186, h: 162, w: 115, turn: -1, title: 'Први антифашистички митинг жена Србије', author: 'Đorđe Andrejević-Kun', year: '1945' },
    { id: 'ni-zrno', o: 160, y: -14, h: 186, w: 153, turn: 1, title: 'Ni zrno žita okupatoru', author: 'Franjo Mraz', year: '1943' },
    { id: 'narod', o: 150, y: 160, h: 174, w: 135, turn: 3, title: 'Narod si bo pisal svobodo sam', author: 'France Mihelič', year: '1943' },
    { id: 'zima', o: 286, y: 26, h: 158, w: 117, turn: -2, title: 'Zima! Vsi vse za naše borce', author: 'Ivan Seljak', year: '1944' },
    { id: 'bratstvom', o: 272, y: 176, h: 162, w: 135, turn: 0, title: 'Bratstvom i jedinstvom', author: 'Vlado Kristl', year: '1944' },
    { id: 'u-borbu', o: 404, y: -8, h: 197, w: 152, turn: 2, title: 'У борбу против окупатора', author: 'Dragoljub Vuksanović', year: '1941' },
    { id: 'slovenske-zene', o: 412, y: 176, h: 174, w: 122, turn: -3, title: 'Slovenske žene nadomestimo', author: 'Vito Globočnik', year: '1945' },
    { id: 'zgrabimo', o: 540, y: 18, h: 174, w: 140, turn: -1, title: 'Zgrabimo za orožje vsi', author: 'Nikolaj Pirnat', year: '1941-45' },
    { id: 'svi-u-borbu', o: 530, y: 180, h: 162, w: 110, turn: 1, title: 'Svi u borbu protiv NDH', author: 'Edo Murtić', year: '1944' },
    { id: 'srbija', o: 660, y: 36, h: 111, w: 167, turn: 3, title: 'Србија се умирит не може', author: '', year: '1941' },
    { id: 'proletarca', o: 668, y: 150, h: 186, w: 152, turn: -2, title: 'Proletarca na jurišu', author: 'Nikolaj Pirnat', year: '1944' },
  ],
  right: [
    { id: 'svi-na-front', o: 40, y: 2, h: 186, w: 128, turn: -3, title: 'Svi na front, sve za front!', author: 'Vasilij Petrović-Antipov', year: '1944' },
    { id: 'osmi-mart', o: 22, y: 176, h: 169, w: 118, turn: -1, title: 'Живео 8. март', author: 'Ismet Mujezinović', year: '1945' },
    { id: 'za-zadnji-udar', o: 156, y: 28, h: 162, w: 128, turn: 1, title: 'Za zadnji udar vsi - vse!', author: 'Nikolaj Pirnat', year: '1945' },
    { id: 'gradi-zemunice', o: 150, y: 182, h: 139, w: 123, turn: 3, title: 'Gradi zemunice', author: 'Franjo Mraz', year: '1943' },
    { id: 'dalmatinka', o: 278, y: -12, h: 186, w: 146, turn: -2, title: 'Dalmatinka u borbi', author: '', year: '1944' },
    { id: 'partizanka', o: 288, y: 160, h: 186, w: 153, turn: 0, title: 'Partizanka', author: 'Nikolaj Pirnat', year: '1944' },
    { id: 'ja-se-borim', o: 410, y: 20, h: 174, w: 129, turn: 2, title: 'Ја се борим, а ти?', author: 'Dragoljub Vuksanović', year: '1941' },
    { id: 'pazi', o: 404, y: 184, h: 162, w: 125, turn: -3, title: 'Пази, петоколонаш вреба', author: 'Pivo Karamatijević, Bora Baruh', year: '1941' },
    { id: 'muslimanska', o: 532, y: -6, h: 193, w: 142, turn: -1, title: 'Godišnjica XVI muslimanske brigade', author: 'Ismet Mujezinović', year: '1944' },
    { id: 'zena-kroz-borbu', o: 540, y: 172, h: 174, w: 156, turn: 1, title: 'Žena kroz borbu', author: '', year: '1941-45' },
    { id: 'zene-steber', o: 664, y: 16, h: 174, w: 121, turn: 3, title: 'Žene steber našega zaledja', author: '', year: '1945' },
    { id: 'dosla-je', o: 660, y: 176, h: 174, w: 129, turn: -2, title: 'Došla je bratska Crvena armija', author: 'Zlatko Prica', year: '1944' },
  ],
}
