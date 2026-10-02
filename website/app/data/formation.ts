// When each unit was formed: the home page groups the units under the year and orders them by this date.
// date is 'YYYY-MM-DD', or 'YYYY-MM' / 'YYYY' when the source gives no more. Every new unit needs an entry;
// until it has one it is listed after the dated units. Where sources disagree, the unit's own book wins.

export interface Formation {
  date: string
  place?: string
  source: string // where the date comes from
  note?: string
}

// The card text, taken from the unit's book when the unit was added
const FROM_CARD = 'knjiga jedinice (opis na kartici)'

export const formation: Record<string, Formation> = {
  'uzicki-odred': {
    date: '1941-07-07', place: 'Užice (Abacija)', source: 'https://znaci.org/00001/196_2.pdf',
    note: 'Odluka OK KPJ o formiranju odreda i štab; prve čete 28. jula 1941. Isto: znaci.org odrednica.',
  },
  'prva-proleterska-brigada': { date: '1941-12-21', source: FROM_CARD },
  'druga-proleterska-brigada': {
    date: '1942-03-01', place: 'Čajniče', source: 'https://znaci.org/00001/55_6.pdf',
    note: 'Monografija: dan osnivanja Brigade 1. mart 1942, obeležavan pred hotelskom zgradom u Čajniču.',
  },
  'treca-proleterska-brigada': { date: '1942-06-05', source: FROM_CARD },
  'prva-licka-brigada': {
    date: '1942-07-08', place: 'Ilići kod vrela Mrežnice', source: 'https://znaci.org/00001/137_2.pdf',
    note: 'Knjiga: štab radi od druge polovine juna; brigada prvi put postrojena 8. jula 1942.',
  },
  '2-krajiska-brigada': { date: '1942-08-02', source: FROM_CARD },
  'druga-licka-brigada': {
    date: '1942-08-18', place: 'Laudonov gaj (Krbavsko polje)', source: 'https://znaci.org/00001/110_1.pdf',
    note: 'Neki dokumenti navode 14. ili 20. avgust; hr.wikipedia 19. avgust.',
  },
  '3-krajiska-proleterska-brigada': { date: '1942-08-22', place: 'Kamenica kod Drvara', source: FROM_CARD },
  '1-dalmatinska-brigada': {
    date: '1942-09-06', place: 'Dobro kod Livna', source: 'https://znaci.org/00001/108_3.pdf',
    note: 'znaci.org odrednica: 5. 9. 1942.',
  },
  '4-krajiska-brigada': { date: '1942-09-09', place: 'Tičevo kod Bosanskog Grahova', source: FROM_CARD },
  '5-kozaracka-brigada': { date: '1942-09-23', place: 'Kozara', source: FROM_CARD },
  '2-dalmatinska-brigada': { date: '1942-10-03', source: FROM_CARD },
  '6-krajiska-brigada': { date: '1942-10-14', source: FROM_CARD },
  '13-proleterska-brigada': { date: '1942-11-07', source: FROM_CARD },
  '8-krajiska-brigada': { date: '1942-12-28', place: 'Cazin', source: FROM_CARD },
  '16-slavonska-omladinska-brigada': {
    date: '1942-12-29', place: 'Gornji Borki kod Daruvara', source: 'https://znaci.org/00002/407.pdf',
    note: 'Bataljoni se okupili 30–31. decembra; znaci.org odrednica: 30. 12. 1942.',
  },
  '17-slavonska-brigada': { date: '1942-12-30', place: 'kod Voćina', source: FROM_CARD },
  '18-slavonska-brigada': { date: '1943-02-11', place: 'Mijača kod Pakraca', source: FROM_CARD },
  'prva-vojvodjanska-brigada': {
    date: '1943-04-11', place: 'Brđani na Majevici', source: 'https://znaci.org/00001/132_1.pdf',
    note: 'Isto: znaci.org odrednica. Kartica je ranije navodila 1944.',
  },
  '2-vojvodjanska-brigada': { date: '1943-04-20', place: 'Majevica', source: FROM_CARD },
  '21-slavonska-brigada': {
    date: '1943-05-17', place: 'Orljavac kod Slavonske Požege', source: 'https://znaci.org/00001/254_1.pdf',
    note: 'znaci.org odrednica: s. Slatinski Drenovac.',
  },
  '4-banijska-brigada': {
    date: '1943-06-30', place: 'Obijaj (Banija)', source: 'https://znaci.org/00001/188_1.pdf',
    note: 'Formirana kao 2. brigada Unske operativne grupe; datum 1. 5. 1943. u odrednici odnosi se na drugu brigadu.',
  },
  'ljubljanska-brigada': { date: '1943-09-11', source: FROM_CARD },
  '4-splitska-brigada': { date: '1943-09', source: FROM_CARD },
  '25-brodska-brigada': {
    date: '1943-10-01', place: 'kod Slavonske Orahovice', source: 'https://znaci.org/00001/262_2.pdf',
    note: 'Knjiga pokazuje da je raniji datum 29. 9. 1943. pogrešan.',
  },
  '1-sumadijska-brigada': { date: '1943-10-05', source: FROM_CARD },
  '17-majevicka-brigada': {
    date: '1943-10-10', place: 'okolina Tuzle', source: 'https://znaci.org/odrednica.php?slug=17-majevicka-udarna-brigada',
    note: 'bs.wikipedia: 16. 10. 1943, Tuzla (svečana smotra). Knjiga brigade nije proverena.',
  },
  '19-bircanska-brigada': {
    date: '1943-10-24', place: 'Vlasenica', source: 'https://znaci.org/00001/267_2.pdf',
    note: 'bs.wikipedia: 23. 10. 1943.',
  },
  'tuzlanski-odred': {
    date: '1943-10-24', place: 'Tuzla', source: 'https://znaci.org/odrednica.php?slug=tuzla',
    note: 'sr.wikipedia (Vojna enciklopedija): 29. 10. 1943. Knjiga odreda nije proverena.',
  },
  '4-srpska-brigada': {
    date: '1943-11-20', place: 'Buci kod Kruševca', source: 'https://znaci.org/00001/149_2.pdf',
    note: 'Svečano postrojavanje 21. novembra; znaci.org odrednica: 21. 11. 1943.',
  },
  '32-zagorska-divizija': {
    date: '1943-12-12', place: 'Kalnik', source: 'https://znaci.org/odrednica.php?slug=32-zagorska-divizija-novj',
    note: 'Mesto prema hr.wikipedia; monografija nije proverena.',
  },
  '7-crnogorska-brigada': {
    date: '1943-12-30', place: 'Kolašin', source: 'https://znaci.org/00001/64_2.pdf',
    note: 'znaci.org odrednica: s. Vlahovići kod Kolašina.',
  },
  '8-crnogorska-brigada': { date: '1944-02-25', place: 'Berane', source: 'https://znaci.org/00001/275_1.pdf' },
  '14-srpska-brigada': {
    date: '1944-06-17', place: 'Ribare kod Đunisa', source: 'https://znaci.org/00001/66_3.pdf',
    note: 'Naredba pročitana 14. juna; smotra 17. juna usvojena kao dan formiranja.',
  },
  '25-srpska-divizija': { date: '1944-06-21', place: 'kod Jošanice u Pustoj reci', source: FROM_CARD },
  '7-vojvodjanska-brigada': { date: '1944-07-02', place: 'salaš Mušickog kod Batrovaca', source: 'https://znaci.org/00001/73_2.pdf' },
  '53-srednjobosanska-divizija': {
    date: '1944-07-23', place: 'srednja Bosna', source: 'https://znaci.org/00003/712.pdf',
    note: 'Štab počeo s radom 23. jula 1944; ime 53. od 15. decembra 1944.',
  },
  '25-srpska-brigada': {
    date: '1944-09-01', place: 'Strelac kod Pirota', source: 'https://znaci.org/00001/215_4.pdf',
    note: 'Naredba 22. divizije 6. 9. 1944; znaci.org i bs.wikipedia: 6. 9. 1944.',
  },
  '21-tuzlanska-brigada': { date: '1944-09-19', place: 'Pašabunar kod Tuzle', source: 'https://znaci.org/00001/250_2.pdf' },
  '4-proleterska-brigada': {
    date: '1942-06-10', source: 'https://znaci.org/00001/148.htm',
    note: 'Knjiga brigade (Janković): spisak boraca „na dan formiranja, 10. jun 1942.“ znaci.org odrednica: 17. 6. 1942, s. Ljubina na Zelengori.',
  },
  '5-proleterska-brigada': {
    date: '1942-06-12', place: 'Smriječno kod Šavnika', source: 'https://znaci.org/odrednica.php?slug=5-proterska-crnogorska-udarna-brigada',
    note: 'Odluka VŠ o formiranju 4. i 5. proleterske 10. 6. 1942. Knjiga brigade nije proverena.',
  },
  '6-istocnobosanska-brigada': {
    date: '1942-08-02', place: 'Šekovići kod Vlasenice', source: 'https://znaci.org/odrednica.php?slug=6-istocnobosanska-proleterska-udarna-brigada',
    note: 'Od Grupe udarnih istočnobosanskih bataljona. Knjiga brigade nije proverena.',
  },
  '10-hercegovacka-brigada': {
    date: '1942-08-10', place: 'kod Donjeg Malovana, blizu Kupresa', source: 'https://znaci.org/odrednica.php?slug=10-hercegovacka-udarna-brigada',
    note: 'Od Hercegovačkog NOP odreda i Mostarskog partizanskog bataljona. Knjiga brigade nije proverena.',
  },
  '7-banijska-brigada': {
    date: '1942-09-02', source: 'https://znaci.org/00001/63_1.pdf',
    note: 'Knjiga brigade (Đurić): Glavni štab Hrvatske naredio formiranje 2. 9. 1942, dok su bataljoni Banijskog odreda bili na putu za Moslavinu; kao brigada postrojeni nešto kasnije. sr.wikipedia: 2. 9. 1942, u Moslavini.',
  },
  '8-banijska-brigada': {
    date: '1942-09-07', place: 'Obljaj kod Gline', source: 'https://znaci.org/odrednica.php?slug=8-banijska-udarna-brigada',
    note: 'Formirana kao 8. hrvatska NO brigada, od 1, 2. i 4. bataljona Banijskog NOP odreda. Knjiga brigade nije proverena.',
  },
  '3-dalmatinska-brigada': {
    date: '1942-11-12', place: 'Vrba kod Sinja', source: 'https://znaci.org/odrednica.php?slug=3-dalmatinska-udarna-brigada',
    note: 'Od Mosećkog i Mosorskog partizanskog bataljona i Rogozničke čete. Rasformirana 6. 6. 1943. na Sutjesci, kasnije ponovo formirana.',
  },
  '16-banijska-brigada': {
    date: '1942-12-26', place: 'Klasnić', source: 'https://znaci.org/odrednica.php?slug=16-banijska-udarna-brigada',
    note: 'Formirana kao 16. hrvatska NO brigada, od po jednog bataljona 7, 8. i 15. hrvatske brigade; odrednica: „s. Klasnić (kod Ogulina)“. Rasformirana 30. 6. 1943.',
  },
  '7-krajiska-brigada': {
    date: '1942-12-27', place: 'Orahovljani kod Ključa', source: 'https://znaci.org/odrednica.php?slug=7-krajiska-udarna-brigada',
    note: 'Od krajiške polubrigade i delova 3. krajiškog NOP odreda. Knjiga brigade nije proverena.',
  },
  '15-majevicka-brigada': {
    date: '1943-04-11', source: 'https://znaci.org/odrednica.php?slug=15-majevicka-udarna-brigada',
    note: 'Majevička grupa udarnih bataljona preimenovana u Majevičku NOU brigadu, kasnije 1. pa 15. majevička. sr.wikipedia: 23. 3. 1943. Knjiga brigade nije proverena.',
  },
  '12-dalmatinska-brigada': {
    date: '1943-09-15', place: 'Brač, Hvar, Vis i Šolta', source: 'https://znaci.org/00001/80_7.pdf',
    note: 'Knjiga brigade (Anić) računa brigadu od 15. rujna 1943. znaci.org odrednica: 21. 9. 1943, na Braču, Hvaru, Visu i Šolti.',
  },
  '3-makedonska-brigada': {
    date: '1944-02-26', place: 'Žegljane kod Kumanova', source: 'https://znaci.org/00001/71_2.pdf',
    note: 'Knjiga brigade (Mihailovski), str. 24: formirana u školskom dvorištu sela Žegnjana (Žegljane), 26. februara 1944.',
  },
  '18-hrvatska-brigada': {
    date: '1943-10-10', place: 'kod Tuzle (proglašena u Husinu 17. 10.)', source: 'https://znaci.org/00001/251_2.pdf',
    note: 'Knjiga brigade, str. 25-26: zvanično formirana 10. oktobra 1943; svečano proglašenje i smotra 17. oktobra u Husinu.',
  },
  '11-dalmatinska-brigada': {
    date: '1943-10-02', place: 'Biokovo', source: 'https://znaci.org/00003/547.pdf',
    note: 'Knjiga brigade (Rako, Družijanić), str. 24: prvi put se postrojila 2. oktobra 1943, na Biokovu (Kozica).',
  },
  '12-krajiska-brigada': {
    date: '1943-02-19', place: 'Drinić', source: 'https://znaci.org/00001/168_2.pdf',
    note: 'Knjiga brigade, str. 36-37: formirana između 12. i 24. februara 1943. u Driniću; 19. februara formirani Štab, dva bataljona i Prateći vod (kao 12. krajiška polubrigada).',
  },
  '17-srpska-brigada': {
    date: '1944-06-02', place: 'Mehane kod Kuršumlije', source: 'https://znaci.org/odrednica.php?slug=17-srpska-brigada',
    note: 'Hronologija na znaci.org: 2. 6. 1944. kod s. Mejane (blizu Kuršumlije) GŠ za Srbiju formirao 17. srpsku NO brigadu; knjiga brigade beleži proslavu godišnjice u s. Mehane 2. 6. 1947.',
  },
  '14-srednjobosanska-brigada': {
    date: '1943-10-17', place: 'Cer kod Prnjavora', source: 'https://znaci.org/00003/579.pdf',
    note: 'Knjiga brigade (Samardžija), str. 7-8: svečani čin formiranja određen za nedjelju 17. oktobra 1943. na Ceru kod Prnjavora (naredba štaba 11. divizije od 15. oktobra).',
  },
  '3-vojvodjanska-brigada': {
    date: '1943-05-15', place: 'Srem', source: 'https://znaci.org/00001/70_2.pdf',
    note: 'Knjiga brigade (Panić): autor uzima 15. maj 1943, kada je odluka o formiranju 3. grupe vojvođanskih udarnih bataljona saopštena komandantu; drugi autori uzimaju 2. jun 1943.',
  },
  'kalnicki-odred': {
    date: '1942-10-10', place: 'Bijela kod Daruvara', source: 'https://znaci.org/00003/558.pdf',
    note: 'Knjiga odreda (Milićević, str. 75): formirao ga je štab III. operativne zone u selu Bijela, istočno od Daruvara.',
  },
  'posavsko-trebavski-odred': {
    date: '1944-02-04', place: 'kod Gradačca', source: 'https://znaci.org/00001/302.pdf',
    note: 'Knjiga odreda (Tihić): spajanjem bataljona Posavskog (formiran 17. septembra 1943. u Obudovcu) i Trebavskog NOP odreda (20. septembra 1943. u Skugriću).',
  },
  '8-kordunaska-divizija': {
    date: '1942-11-22', place: 'Crevarska Strana na Petrovoj gori', source: 'https://znaci.org/00003/571.pdf',
    note: 'Zbornik HAK knj. 9: Naredba br. 95 Vrhovnog štaba od 22. novembra 1942; štab konstituisan u Suvoj Perni, divizija postrojena u Crevarskoj Strani.',
  },
  'cankarjeva-brigada': {
    date: '1942-09-28', place: 'Lapinje na Kočevskom', source: 'https://znaci.org/00003/767.pdf',
    note: 'Knjiga brigade (Ambrožič-Novljan, str. 26): ustanovni miting 28. septembra 1942. kod Lapinja, po dnevniku Glavnog štaba; često se navode 23. i 24. septembar.',
  },
  'gubceva-brigada': {
    date: '1942-09-04', place: 'Trebelno nad Mokronogom', source: 'https://znaci.org/00003/782.pdf',
    note: 'Knjiga brigade (Ambrožič-Novljan, str. 9): ustanovni miting u šumi južno od sela Trebelno.',
  },
  'dvanajsta-brigada': {
    date: '1943-09-24', place: 'Mokronog', source: 'https://znaci.org/00003/814.pdf',
    note: 'Knjiga brigade (Ambrožič-Novljan): ustanovni miting u Mokronogu; brigada nastala od jezgra Šlandrove brigade i 4. bataljona Gubčeve.',
  },
  'gradnikova-brigada': {
    date: '1943-04', place: 'Golobar kod Bovca', source: 'https://znaci.org/00003/825.pdf',
    note: 'Knjiga brigade (Petelin): od Severnoprimorskog odreda; ustanovni zbor na Golobaru na uskrsni ponedeljak, 26. aprila 1943, razbio je napad Italijana.',
  },
  'zidanskova-brigada': {
    date: '1944-01-08', place: 'Sv. Primož na Pohorju', source: 'https://znaci.org/00003/776.pdf',
    note: 'Knjiga brigade (Fajdiga): od Pohorskog odreda.',
  },
  'skofjeloski-odred': {
    date: '1944-07-30', place: 'Škofjeloški hribi', source: 'https://znaci.org/00003/809.pdf',
    note: 'Knjiga odreda (Lotrič): ukaz Glavnog štaba NOV i PO Slovenije od 30. jula 1944. o osnivanju Škofjeloškog i Kokrškog odreda.',
  },
  'istrski-odred': {
    date: '1943-10-07', place: 'Brkini', source: 'https://znaci.org/00003/811.pdf',
    note: 'Knjiga odreda (Zadnik, str. 86): štab 14. divizije dao je novoj jedinici ime pri osnivanju 7. oktobra 1943.',
  },
  'zapadnodolenjski-odred': {
    date: '1942-06', place: 'Dolenjska', source: 'https://znaci.org/00003/808.pdf',
    note: 'Knjiga odreda (Kraševec, str. 18): osnovan 24. ili 25. juna 1942, pri preuređenju 3. i stvaranju 5. grupe odreda, uglavnom od boraca rasformiranog Dolenjskog odreda.',
  },
  'braciceva-brigada': {
    date: '1943-09-23', place: 'Knežja Njiva, Loška dolina', source: 'https://znaci.org/00003/775.pdf',
    note: 'Knjiga brigade, II. deo (Fajdiga, str. 701): 13. SNOUB Mirko Bračič; do 3. oktobra 1943. SNOB-Loška.',
  },
  'tomsiceva-brigada': {
    date: '1942-07-16', place: 'Cesta na Kočevskem', source: 'https://znaci.org/00003/787.pdf',
    note: 'Strle, Tomšičeva brigada, 2. knjiga (str. 20-24): toga dana je na Cesti osnovan 2. proleterski udarni bataljon, i taj dan je proglašen danom osnivanja 1. SPUB Toneta Tomšiča.',
  },
  '1-slovenska-artilerijska-brigada': {
    date: '1944-05-06', place: 'Lašče', source: 'https://znaci.org/00003/826.pdf',
    note: 'Lah, Prva slovenska artilerijska brigada (str. 149-151): odluka Glavnog štaba NOV i PO Slovenije br. 320 od 6. maja 1944; 7. maja pročitana je artiljercima XV. i XVIII. divizije okupljenim u Laščama.',
  },
  'artilerija-9-korpusa': {
    date: '1944-06-14', place: 'Gornji Lokovec', source: 'https://znaci.org/00003/824.pdf',
    note: 'Lah, Artilerija 9. korpusa (str. 101-102): toga dana je imenovan štab artiljerije 9. korpusa i potčinjen mu divizion 31. divizije; spomenik na Gornjem Lokovcu.',
  },
  '19-srpska-brigada': {
    date: '1944-06-12', place: 'Gornja Jošanica', source: 'https://znaci.org/00001/87_1.pdf',
    note: 'Pejčić, Devetnaesta srpska brigada, gl. I (str. 17): formirana u selu Gornja Jošanica 12. juna 1944; jezgro je bio 1. bataljon iz 16. srpske brigade.',
  },
  '22-srpska-brigada': {
    date: '1944-09-12', place: 'Brdnjak kod Drugovca', source: 'https://znaci.org/00003/445.pdf',
    note: 'Gončin, 22. srpska kosmajska brigada (pogl. Svečanost na Brdnjaku): brigada je proglašena na Brdnjaku, između Drugovca i Selevca; spiskovi beleže svakog borca prvog sastava sa 12. 9. 1944.',
  },
  '12-vojvodjanska-brigada': {
    date: '1944-10-08', place: 'Vojlovica kod Pančeva', source: 'https://znaci.org/00003/443.pdf',
    note: 'Popov, 12. vojvođanska udarna brigada (pogl. Vojlovica, 8. oktobra): naredba Glavnog štaba NOV i PO Vojvodine o formiranju pročitana je na trgu u Vojlovici pred više od 2.000 boraca.',
  },
}

/** Sort key: a missing month goes to the end of its year, a missing day to the middle of its month */
export function formationKey(date: string): number {
  const [y, m, d] = date.split('-').map(Number)
  return y * 10000 + (m || 13) * 100 + (d || 15)
}
