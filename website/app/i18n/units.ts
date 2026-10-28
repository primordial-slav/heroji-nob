import type { Lang } from './config'
import type { Unit } from '@/app/data/units'
import { quoteMarks } from './format'
import { toCyrillic } from './cyrillic'

// Each unit's name and card text in Slovene, Macedonian and English; the Serbo-Croatian ones are in
// data/units.ts. Names follow each language's own usage (liška, sandžaška, kozaraška; 13-та, Втора; 1st
// Lika), honorary names in straight quotes (each language's quotation marks are put in by unitName).
// Card texts follow VOICE.md's formula: when and where the unit was formed, then who is on its list.
// Every unit added to data/units.ts needs an entry here.

interface UnitText {
  name: string
  description: string
}

const sl: Record<string, UnitText> = {
  'prva-licka-brigada': {
    name: 'Prva liška proletarska brigada "Marko Orešković"',
    description: 'Ustanovljena 8. julija 1942 pri izviru Mrežnice.',
  },
  'prva-proleterska-brigada': {
    name: 'Prva proletarska narodnoosvobodilna udarna brigada',
    description: 'Ustanovljena 21. decembra 1941.',
  },
  'ljubljanska-brigada': {
    name: '10. slovenska narodnoosvobodilna udarna brigada "Ljubljanska"',
    description: 'Ustanovljena 11. septembra 1943.',
  },
  'druga-licka-brigada': {
    name: 'Druga liška proletarska brigada',
    description: 'Ustanovljena 18. avgusta 1942 v Laudonovem gaju. Padli, umrli in pogrešani borci, tisti, ki so vojno preživeli, ter starešine štaba brigade in bataljonov.',
  },
  'treca-proleterska-brigada': {
    name: 'Tretja proletarska (sandžaška) brigada',
    description: 'Ustanovljena 5. junija 1942. Seznam je z dneva, ko je bila brigada ustanovljena.',
  },
  '13-proleterska-brigada': {
    name: '13. proletarska udarna brigada "Rade Končar"',
    description: 'Ustanovljena 7. novembra 1942. Padli in preživeli borci.',
  },
  '2-dalmatinska-brigada': {
    name: '2. dalmatinska proletarska udarna brigada',
    description: 'Ustanovljena 3. oktobra 1942. Borci brigade ter štabi in poveljstva brigade, bataljonov in čet.',
  },
  '4-splitska-brigada': {
    name: '4. splitska udarna brigada',
    description: 'Ustanovljena septembra 1943. Padli in preživeli borci.',
  },
  'prva-vojvodjanska-brigada': {
    name: 'Prva vojvodinska brigada',
    description: 'Ustanovljena 11. aprila 1943 v Brđanih na Majevici. Borci brigade.',
  },
  '5-kozaracka-brigada': {
    name: '5. krajiška (kozaraška) udarna brigada',
    description: 'Ustanovljena 23. septembra 1942 na Kozari. Padli, pogrešani in umrli borci in poveljniki.',
  },
  '2-vojvodjanska-brigada': {
    name: '2. vojvodinska udarna brigada',
    description: 'Ustanovljena 20. aprila 1943 na Majevici. Borci in poveljniki od ustanovitve do konca vojne.',
  },
  '8-krajiska-brigada': {
    name: '8. krajiška udarna brigada',
    description: 'Ustanovljena 28. decembra 1942 v Cazinu. Borci, ki so v vojni padli ali umrli.',
  },
  '6-krajiska-brigada': {
    name: '6. krajiška udarna brigada',
    description: 'Ustanovljena 14. oktobra 1942 iz enot Prvega krajiškega odreda. Padli in umrli borci in poveljniki, poveljniki brigade 1942–1943 ter borci, ki so vojno preživeli.',
  },
  '4-krajiska-brigada': {
    name: '4. krajiška udarna brigada',
    description: 'Ustanovljena 9. septembra 1942 v Tičevu pri Bosanskem Grahovu. Padli, umrli in pogrešani borci in poveljniki.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3. krajiška proletarska udarna brigada',
    description: 'Ustanovljena 22. avgusta 1942 v Kamenici pri Drvarju. Borci brigade od ustanovitve do konca vojne.',
  },
  '17-slavonska-brigada': {
    name: '17. slavonska udarna brigada',
    description: 'Ustanovljena 30. decembra 1942 pri Voćinu. Padli in preživeli borci, po občinah.',
  },
  '25-srpska-divizija': {
    name: '25. srbska udarna divizija',
    description: 'Ustanovljena 21. junija 1944 pri Jošanici v Pusti reki. Padli borci in poveljniki 16., 18. in 19. srbske brigade.',
  },
  '1-sumadijska-brigada': {
    name: '1. šumadijska brigada',
    description: 'Ustanovljena 5. oktobra 1943. Padli borci in poveljniki ter borci, ki so vojno preživeli.',
  },
  '18-slavonska-brigada': {
    name: '18. slavonska udarna brigada',
    description: 'Ustanovljena 11. februarja 1943 v Mijači pri Pakracu. Padli, umrli in preživeli borci.',
  },
  '4-banijska-brigada': {
    name: '4. banijska brigada',
    description: 'Ustanovljena 30. junija 1943 v Obijaju na Baniji. Brigada 7. divizije. Starešine štabov in borci brigade.',
  },
  '4-srpska-brigada': {
    name: '4. srbska udarna brigada',
    description:
      'Ustanovljena 20. novembra 1943 v Bucih pri Kruševcu. Borci brigade, med njimi tudi tujci in borci, katerih imena niso znana.',
  },
  '7-vojvodjanska-brigada': {
    name: '7. vojvodinska udarna brigada',
    description:
      'Ustanovljena 2. julija 1944 na Mušickijevi kmetiji pri Batrovcih. Preživeli, padli in po vojni umrli borci ter borci 4. (ruskega) bataljona.',
  },
  '19-bircanska-brigada': {
    name: '19. birčanska brigada',
    description: 'Ustanovljena 24. oktobra 1943 v Vlasenici. Borci brigade.',
  },
  '2-krajiska-brigada': {
    name: '2. krajiška udarna brigada',
    description: 'Ustanovljena 2. avgusta 1942. Padli in umrli borci in poveljniki.',
  },
  'tuzlanski-odred': {
    name: 'Tuzelski partizanski odred',
    description: 'Ustanovljen 24. oktobra 1943 v Tuzli. Borci odreda, mnogi tudi s fotografijo.',
  },
  'uzicki-odred': {
    name: 'Užiški partizanski odred "Dimitrije Tucović"',
    description: 'Ustanovljen 7. julija 1941 v Užicah. Borci odreda, ki so padli v vojni 1941–1945.',
  },
  '14-srpska-brigada': {
    name: '14. srbska udarna brigada',
    description: 'Ustanovljena 17. junija 1944 v Ribarah pri Đunisu. Padli borci in poveljniki Niškega odreda in 14. srbske brigade.',
  },
  '7-crnogorska-brigada': {
    name: '7. črnogorska mladinska brigada "Budo Tomović"',
    description: 'Ustanovljena 30. decembra 1943 v Kolašinu. Padli borci brigade.',
  },
  '17-majevicka-brigada': {
    name: '17. majeviška brigada',
    description:
      'Ustanovljena 10. oktobra 1943 v okolici Tuzle. Padli in umrli borci Tretjega majeviškega odreda in 17. majeviške brigade.',
  },
  '25-brodska-brigada': {
    name: '25. brodska brigada',
    description: 'Ustanovljena 1. oktobra 1943 pri Slavonski Orahovici. Padli borci ter vsi borci in poveljniki brigade oktobra 1943.',
  },
  '25-srpska-brigada': {
    name: '25. srbska brigada',
    description: 'Ustanovljena 1. septembra 1944 v Strelcu pri Pirotu. Padli in ranjeni borci in poveljniki, po vojnih seznamih brigade.',
  },
  '21-tuzlanska-brigada': {
    name: '21. tuzelska brigada',
    description: 'Ustanovljena 19. septembra 1944 v Pašabunarju pri Tuzli. Padli borci in poveljniki.',
  },
  '53-srednjobosanska-divizija': {
    name: '53. srednjebosanska divizija',
    description:
      'Ustanovljena 23. julija 1944 v srednji Bosni. Padli, ujeti in pogrešani borci 14., 18. in 19. brigade ter Prnjavorskega in Motajiškega odreda.',
  },
  '21-slavonska-brigada': {
    name: '21. slavonska brigada',
    description: 'Ustanovljena 17. maja 1943 v Orljavcu pri Slavonski Požegi. Padli, umrli in pogrešani borci in poveljniki.',
  },
  '32-zagorska-divizija': {
    name: '32. zagorska divizija',
    description:
      'Ustanovljena 12. decembra 1943 na Kalniku. Borci divizije in Zahodne skupine odredov ter borci štaba in brigad divizije, s podatki o vsakem, in poveljniški sestav.',
  },
  '1-dalmatinska-brigada': {
    name: '1. dalmatinska proletarska brigada',
    description:
      'Ustanovljena 6. septembra 1942 v vasi Dobro pri Livnu. Borci, ki so padli v vojni, borci na Sutjeski, borke 1944–1945, komandirji in komisarji čet ter poveljstvo brigade in bataljonov.',
  },
  '16-slavonska-omladinska-brigada': {
    name: '16. slavonska mladinska brigada "Jože Vlahović"',
    description:
      'Ustanovljena 29. decembra 1942 v Gornjih Borkih pri Daruvarju. Padli borci in poveljniki, padli v Pokuplju in na Žumberku ter vodstvo brigade od ustanovitve do konca vojne.',
  },
  '8-crnogorska-brigada': {
    name: '8. črnogorska brigada',
    description: 'Ustanovljena 25. februarja 1944 v Beranah. Padli borci in poveljniki ter dopolnilni seznam padlih iz Uba.',
  },
  'druga-proleterska-brigada': {
    name: 'Druga proletarska brigada',
    description:
      'Ustanovljena 1. marca 1942 v Čajniču. Padli, umrli in pogrešani borci, po kraju in dnevu smrti, od Sutjeske do sremske fronte.',
  },
  '4-proleterska-brigada': {
    name: '4. proletarska črnogorska brigada',
    description:
      'Ustanovljena 10. junija 1942. Borci na dan ustanovitve in v bitki na Sutjeski, poveljniki brigade in narodni heroji ter borci in poveljniki, padli od 1942 do 1945.',
  },
  '5-proleterska-brigada': {
    name: '5. proletarska črnogorska brigada',
    description:
      'Ustanovljena 12. junija 1942 v Smriječnu pri Šavniku. Borci brigade v bitki na Sutjeski, maja in junija 1943, ter partizanke brigade.',
  },
  '6-istocnobosanska-brigada': {
    name: '6. vzhodnobosanska proletarska brigada',
    description:
      'Ustanovljena 2. avgusta 1942 v Šekovićih pri Vlasenici. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '10-hercegovacka-brigada': {
    name: '10. hercegovska brigada',
    description:
      'Ustanovljena 10. avgusta 1942 pri Kupresu. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '7-banijska-brigada': {
    name: '7. banijska brigada "Vasilj Gaćeša"',
    description:
      'Ustanovljena 2. septembra 1942. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '8-banijska-brigada': {
    name: '8. banijska brigada',
    description:
      'Ustanovljena 7. septembra 1942 v Obljaju pri Glini. Borci brigade v bitki na Sutjeski, maja in junija 1943, padli in umrli borci brigade ter poveljniški sestav.',
  },
  '3-dalmatinska-brigada': {
    name: '3. dalmatinska brigada',
    description:
      'Ustanovljena 12. novembra 1942 v Vrbi pri Sinju. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '9-dalmatinska-divizija': {
    name: '9. dalmatinska divizija',
    description:
      'Ustanovljena 11. februarja 1943 iz 3., 4. in 5. dalmatinske brigade, razpuščena aprila istega leta. Padli in pogrešani borci divizije od februarja do aprila 1943.',
  },
  '16-banijska-brigada': {
    name: '16. banijska brigada',
    description:
      'Ustanovljena 26. decembra 1942 v Klasniću. Borci brigade v bitki na Sutjeski, maja in junija 1943, ter borci in poveljniki, padli do konca junija 1943.',
  },
  '7-krajiska-brigada': {
    name: '7. krajiška brigada',
    description:
      'Ustanovljena 27. decembra 1942 v Orahovljanih pri Ključu. Preživeli in padli borci in poveljniki, od ustanovitve do konca vojne.',
  },
  '15-majevicka-brigada': {
    name: '15. majeviška brigada',
    description:
      'Ustanovljena 11. aprila 1943. Borci brigade, tedaj 1. majeviške, v bitki na Sutjeski, maja in junija 1943.',
  },
  '12-dalmatinska-brigada': {
    name: '12. dalmatinska (1. otoška) brigada',
    description:
      'Ustanovljena 15. septembra 1943 na otokih Brač, Hvar, Vis in Šolta. Padli borci in poveljniki, po bojih, v katerih so padli, ter vodilni kader štaba brigade in bataljonov.',
  },
  '3-makedonska-brigada': {
    name: '3. makedonska brigada',
    description:
      'Ustanovljena 26. februarja 1944 v vasi Žegljane pri Kumanovu. Padli borci.',
  },
  '18-hrvatska-brigada': {
    name: '18. hrvaška vzhodnobosanska brigada',
    description:
      'Ustanovljena 10. oktobra 1943 pri Tuzli, razglašena 17. oktobra v Husinu. Borci in poveljniki brigade.',
  },
  '11-dalmatinska-brigada': {
    name: '11. dalmatinska brigada',
    description:
      'Ustanovljena 2. oktobra 1943 na Biokovu. Padli, pogrešani in preživeli borci ter starešine štabov in poveljstev.',
  },
  '12-krajiska-brigada': {
    name: '12. krajiška brigada',
    description:
      'Ustanovljena 19. februarja 1943 v Driniću. Padli in preživeli borci in poveljniki.',
  },
  '17-srpska-brigada': {
    name: '17. srbska brigada',
    description:
      'Ustanovljena 2. junija 1944 v Mehanah pri Kuršumliji. Preživeli in padli borci.',
  },
  '14-srednjobosanska-brigada': {
    name: '14. srednjebosanska brigada',
    description:
      'Ustanovljena 17. oktobra 1943 na Ceru pri Prnjavorju. Padli, umrli in pogrešani borci ter borci, ki so vojno preživeli.',
  },
  '3-vojvodjanska-brigada': {
    name: '3. vojvodinska brigada',
    description:
      'Ustanovljena 15. maja 1943 v Sremu. Padli borci in poveljniki, tisti, katerih usoda ni znana, in preživeli.',
  },
  'kalnicki-odred': {
    name: 'Kalniški partizanski odred',
    description:
      'Ustanovljen 10. oktobra 1942 v Bijeli pri Daruvarju. Borci odreda, padli in preživeli, ter voditelji odreda in njegovih enot.',
  },
  'posavsko-trebavski-odred': {
    name: 'Posavsko-trebavski partizanski odred',
    description:
      'Ustanovljen 4. februarja 1944 pri Gradačcu iz Posavskega in Trebavskega odreda. Borci odreda.',
  },
  '8-kordunaska-divizija': {
    name: '8. kordunska divizija',
    description:
      'Ustanovljena 22. novembra 1942 v Crevarski Strani na Petrovi gori. Štabi divizije, brigad in bataljonov ter padli borci divizije.',
  },
  'cankarjeva-brigada': {
    name: 'Cankarjeva brigada',
    description:
      'Ustanovljena 28. septembra 1942 pri Lapinjah na Kočevskem. Štabi brigade in bataljonov, padli in preživeli borci.',
  },
  'gubceva-brigada': {
    name: 'Gubčeva brigada',
    description:
      'Ustanovljena 4. septembra 1942 pri Trebelnem nad Mokronogom. Štabi brigade in bataljonov, padli in preživeli borci.',
  },
  'dvanajsta-brigada': {
    name: 'Dvanajsta brigada',
    description:
      'Ustanovljena 24. septembra 1943 v Mokronogu. Štabi brigade in bataljonov, padli in preživeli borci.',
  },
  'gradnikova-brigada': {
    name: 'Gradnikova brigada',
    description:
      'Ustanovljena aprila 1943 na Golobarju pri Bovcu. Padli borci in drugi borci brigade, njen štab in narodni heroji.',
  },
  'zidanskova-brigada': {
    name: 'Zidanškova brigada',
    description:
      'Ustanovljena 8. januarja 1944 pri Sv. Primožu na Pohorju. Štab brigade, borci brigade, padli in preživeli.',
  },
  'skofjeloski-odred': {
    name: 'Škofjeloški odred',
    description:
      'Ustanovljen po ukazu z dne 30. julija 1944 v škofjeloških hribih. Imena borcev odreda.',
  },
  'istrski-odred': {
    name: 'Istrski odred',
    description:
      'Ustanovljen 7. oktobra 1943 v Brkinih. Štabi odreda, bataljonov in čet, padli in drugi borci odreda.',
  },
  'zapadnodolenjski-odred': {
    name: 'Zapadnodolenjski odred',
    description:
      'Ustanovljen konec junija 1942 na Dolenjskem. Padli in drugi borci odreda.',
  },
  'braciceva-brigada': {
    name: 'Bračičeva brigada',
    description:
      'Ustanovljena 23. septembra 1943 v Knežji Njivi v Loški dolini. Padli in preživeli borci.',
  },
  'tomsiceva-brigada': {
    name: 'Tomšičeva brigada',
    description:
      'Ustanovljena 16. julija 1942 na Cesti na Kočevskem. Borci enot, iz katerih je nastala, in borci brigade do konca vojne.',
  },
  '1-slovenska-artilerijska-brigada': {
    name: '1. slovenska artilerijska brigada',
    description:
      'Ustanovljena 6. maja 1944 v Laščah pri Dvoru. Starešine in topničarji brigade ter padli.',
  },
  'artilerija-9-korpusa': {
    name: 'Artilerija 9. korpusa',
    description:
      'Ustanovljena 14. junija 1944 na Gornjem Lokovcu. Borci artilerije in padli.',
  },
  '19-srpska-brigada': {
    name: '19. srbska brigada',
    description:
      'Ustanovljena 12. junija 1944 v Gornji Jošanici. Padli, pogrešani in umrli borci, tisti, ki so vojno preživeli, ter štabi brigade in bataljonov.',
  },
  '22-srpska-brigada': {
    name: '22. srbska kosmajska brigada',
    description:
      'Ustanovljena 12. septembra 1944 na Brdnjaku pri Drugovcu. Padli in preživeli borci in starešine.',
  },
  '12-vojvodjanska-brigada': {
    name: '12. vojvodinska brigada',
    description:
      'Ustanovljena 8. oktobra 1944 v Vojlovici pri Pančevu. Borci brigade po krajih, kjer so živeli, in padli.',
  },
  '4-vojvodjanska-brigada': {
    name: '4. vojvodinska brigada',
    description:
      'Ustanovljena 7. oktobra 1943 v gozdu Varadin pri Višnjićevu. Borci prve sestave brigade in padli.',
  },
  '1-kosovsko-metohijska-brigada': {
    name: '1. kosovsko-metohijska brigada',
    description:
      'Ustanovljena 24. junija 1944 v vasi Zbaždi v zahodni Makedoniji. Borci brigade, padli in ranjeni.',
  },
  '8-vojvodjanska-brigada': {
    name: '8. vojvodinska brigada',
    description:
      'Ustanovljena 12. septembra 1944 na jasi Jabuka na Fruški gori. Padli in pogrešani borci in starešine.',
  },
  '19-sjevernodalmatinska-divizija': {
    name: '19. severnodalmatinska divizija',
    description:
      'Ustanovljena 11. oktobra 1943 v Biovičinem Selu v Bukovici. Komandanti in komisarji divizije in brigad, narodni heroji ter padli in umrli borci divizije.',
  },
  '21-srpska-brigada': {
    name: '21. srbska brigada',
    description:
      'Ustanovljena 10. maja 1944 v Trebežu pri Darosavi. Padli in preživeli borci ter drugi, ki so se borili v brigadi.',
  },
  '14-hercegovacka-brigada': {
    name: '14. hercegovska brigada',
    description:
      'Ustanovljena 4. septembra 1944 pri Ljubinju kot mladinska brigada. Vsi borci, ki so šli skozi brigado, padli in poveljstvo.',
  },
  '5-vojvodjanska-brigada': {
    name: '5. vojvodinska brigada',
    description:
      'Ustanovljena 15. novembra 1943 v Obršinah na Majevici. Borci in starešine brigade.',
  },
  '6-vojvodjanska-brigada': {
    name: '6. vojvodinska brigada',
    description:
      'Ustanovljena 17. januarja 1944 na Jabučju pri Sremski Rači. Padli borci in starešine brigade ter člani štabov in poveljstev čet.',
  },
  '13-vojvodjanska-brigada': {
    name: '13. vojvodinska brigada',
    description:
      'Ustanovljena 14. oktobra 1944 v Kikindi. Borci brigade, po imenih.',
  },
  '7-srpska-brigada': {
    name: '7. srbska brigada',
    description:
      'Ustanovljena 4. februarja 1944 v Jabukoviku pri Crni Travi kot 5. južnomoravska. Borci maja 1944 ter padli, umrli in pogrešani.',
  },
  '15-srpska-brigada': {
    name: '15. srbska brigada',
    description:
      'Ustanovljena 2. junija 1944 v Retkocerju v Gornji Jablanici. Borci in starešine brigade, padli in ranjeni.',
  },
  '8-srpska-brigada': {
    name: '8. srbska brigada',
    description:
      'Ustanovljena 8. marca 1944 v Trgovištu kot 6. južnomoravska. Padli borci brigade.',
  },
  '10-srpska-brigada': {
    name: '10. srbska brigada',
    description:
      'Ustanovljena 8. maja 1944 v Jabukoviku pri Crni Travi. Padli, umrli in pogrešani borci in starešine brigade.',
  },
  '23-srpska-brigada': {
    name: '23. srbska brigada',
    description:
      'Ustanovljena 2. septembra 1944 v Šuman Topli pri Knjaževcu. Padli in umrli borci in starešine brigade.',
  },
  '12-srpska-brigada': {
    name: '12. srbska brigada',
    description:
      'Ustanovljena 22. maja 1944 na Ostrozubu južno od Bistrice. Padli in umrli borci in starešine brigade.',
  },
  '20-srpska-brigada': {
    name: '20. srbska brigada',
    description:
      'Ustanovljena 19. avgusta 1944 nad vasjo Bučje pri Knjaževcu. Padli in umrli borci in starešine brigade.',
  },
  '1-konjicka-brigada': {
    name: '1. konjeniška brigada',
    description:
      'Ustanovljena 15. septembra 1944 v Slavkovici pri Ljigu. Vojni seznam starešin in borcev brigade ter padli.',
  },
  'toplicki-odred': {
    name: 'Toplički partizanski odred',
    description:
      'Ustanovljen 3. avgusta 1941 v Ajdanovcu pri Prokuplju. Borci na dan ustanovitve, padli in umrli, narodni heroji odreda.',
  },
  'karlovacka-brigada': {
    name: 'Karlovška udarna brigada',
    description:
      'Ustanovljena 5. marca 1944 v Hrašću pri Ozlju. Borci brigade na dan ustanovitve, padli in poveljniški sestav.',
  },
  '14-primorsko-goranska': {
    name: '14. primorsko-goranska brigada',
    description:
      'Ustanovljena 26. novembra 1942 v Drežnici. Padli borci brigade.',
  },
  '22-divizija': {
    name: '22. divizija',
    description:
      'Ustanovljena maja 1944 na desnem bregu Južne Morave. Padli borci 8., 10. in 12. srbske brigade.',
  },
  '34-divizija': {
    name: '34. divizija',
    description:
      'Ustanovljena 30. januarja 1944 na Žumberku in v Pokuplju. Padli borci in starešine divizije in njenih brigad ter poveljniški sestav.',
  },
  '4-sandzacka-brigada': {
    name: '4. sandžaška brigada',
    description:
      'Ustanovljena 1. decembra 1943 v Pljevljah. Padli in ranjeni borci brigade.',
  },
  '3-primorsko-goranska': {
    name: '3. primorsko-goranska brigada',
    description:
      'Ustanovljena 15. septembra 1943 v Škrljevem v Hrvaškem primorju. Štabi brigade in bataljonov, starešine in četni bolničarji brigade ter padli.',
  },
  '13-hercegovacka-brigada': {
    name: '13. hercegovska brigada',
    description:
      'Ustanovljena 14. maja 1944 v Hercegovini. Padli borci in starešine brigade, vsi, ki so se borili v njej, in starešinski sestav.',
  },
  '12-hercegovacka-brigada': {
    name: '12. hercegovska brigada',
    description:
      'Ustanovljena 16. novembra 1943 v Hercegovini iz skupin bataljonov 10. hercegovske. Padli borci in starešine brigade.',
  },
  '1-bokeljska-brigada': {
    name: '1. bokeljska brigada',
    description:
      'Ustanovljena 5. oktobra 1944 v Konjskem pri Trebinju. Vsi borci in starešine brigade po enotah ter padli, umrli in pogrešani.',
  },
  '6-dalmatinska-brigada': {
    name: '6. dalmatinska brigada',
    description:
      'Ustanovljena 8. oktobra 1943 v Erveniku kot 2. brigada 19. divizije. Štabi brigade in bataljonov ter padli borci brigade.',
  },
  'osjecka-brigada': {
    name: 'Osiješka udarna brigada',
    description:
      'Ustanovljena 1. marca 1944 pri Slobodni Vlasti blizu Đakova. Padli in umrli borci brigade ter preživeli, po občinah, in njeni poveljniki.',
  },
  '4-brigada-slavonije': {
    name: '4. brigada Slavonije',
    description:
      'Ustanovljena 28. septembra 1944 v Podravski Slatini kot 4. brigada 12. divizije, imenovana Druga brodska. Padli in ranjeni borci brigade ter njeni voditelji.',
  },
  '12-slavonska-brigada': {
    name: '12. proletarska slavonska brigada',
    description:
      'Ustanovljena 11. oktobra 1942 v Budićih pri Pakracu kot 1. slavonska brigada, proletarska od 26. oktobra 1944. Borke brigade, padle, umrle in preživele.',
  },
  'zagrebacki-odred': {
    name: 'Zagrebški partizanski odred',
    description:
      'Ustanovljen 13. septembra 1943 na Zagrebški gori. Seznam borcev odreda: vas, občina in usoda.',
  },
  'mosorski-odred': {
    name: 'Mosorski partizanski odred',
    description:
      'Ustanovljen 21. februarja 1942 na Mosorju, znova 11. oktobra 1943, razpuščen 10. novembra 1944. Vsi borci odreda 1942–1944, s kratkimi življenjepisi, in vodstvo odreda.',
  },
  'turopoljsko-posavski-odred': {
    name: 'Turopoljsko-posavski partizanski odred',
    description:
      'Ustanovljen 8. avgusta 1943 pri Čički Poljani. Padli borci odreda ter tisti, ki so jih sovražniki ustrelili ali so umrli med vojno.',
  },
  'zascitni-bataljon-vpv': {
    name: 'Zaščitni bataljon IOOF in CK KPS',
    description:
      'Ustanovljen aprila 1944 iz čet, ki so od leta 1942 varovale baze in člane političnega vodstva Slovenije. Preživeli in padli pripadniki.',
  },
  '1-zagorska-brigada': {
    name: '1. zagorska brigada',
    description:
      'Ustanovljena 8. maja 1944 v Selnici pod Ivančico. Padli borci in starešine brigade.',
  },
  '6-crnogorska-brigada': {
    name: '6. črnogorska brigada',
    description:
      'Ustanovljena 14. novembra 1943 v Drijenku pri Kolašinu. Padli in umrli borci in poveljniki brigade.',
  },
  '11-krajiska-brigada': {
    name: '11. krajiška (kozaraška) brigada',
    description:
      'Ustanovljena 23. avgusta 1943 na Kozari iz Kozarskega NOP odreda. Padli borci brigade po občinah in seznam bork.',
  },
  '3-banijska-brigada': {
    name: '3. banijska brigada',
    description:
      'Ustanovljena 1. maja 1943 v Komogovini kot 4. banijska brigada; od septembra 1943 3. brigada 7. banijske divizije. Poveljniki in borci brigade.',
  },
  'macvanski-odred': {
    name: 'Mačvanski (Podrinjski) partizanski odred',
    description:
      'Ustanovljen 16. julija 1941 na Bubanji pri Glušcih v Mačvi; od avgusta Podrinjski partizanski odred. Borci odreda od julija 1941 do marca 1942, po krajih, iz katerih so prišli.',
  },
  'posavski-odred': {
    name: 'Posavski partizanski odred',
    description:
      'Ustanovljen 31. julija 1941 z odločitvijo Glavnega štaba za Srbijo, iz dveh posavskih čet in Tamnavske čete. Borci odreda leta 1941, po bataljonih.',
  },
  '51-divizija': {
    name: '51. vojvodinska divizija',
    description:
      'Ustanovljena 31. oktobra 1944 v Novem Sadu iz 7., 8. in 12. vojvodinske brigade. Borci divizije, padli od ustanovitve do konca vojne, maja 1945, in pogrešani v bitki pri Batini.',
  },
  'vrhovni-stab': {
    name: 'Vrhovni štab NOV in POJ',
    description:
      'Ustanovljen 27. junija 1941 v Beogradu kot Glavni štab partizanskih odredov Jugoslavije. Pripadniki Vrhovnega štaba, njegovih služb, Spremljevalnega bataljona in britanske vojaške misije v bitki na Sutjeski, maja in junija 1943, in delavci njegove vojaškotehnične delavnice v Grmeču 1942–1943.',
  },
  '1-proleterska-divizija': {
    name: '1. proletarska divizija',
    description:
      'Ustanovljena 1. novembra 1942 v Bosanskem Petrovcu. Štab divizije z njegovimi službami in spremljevalnimi enotami v bitki na Sutjeski, maja in junija 1943.',
  },
  '2-proleterska-divizija': {
    name: '2. proletarska divizija',
    description:
      'Ustanovljena 1. novembra 1942 v Tičevem. Štab divizije z njegovimi službami in spremljevalnimi enotami v bitki na Sutjeski, maja in junija 1943.',
  },
  '3-udarna-divizija': {
    name: '3. udarna divizija',
    description:
      'Ustanovljena 1. novembra 1942 v Tičevem. Štab divizije z njegovimi službami in spremljevalnimi enotami v bitki na Sutjeski, maja in junija 1943.',
  },
  '7-banijska-divizija': {
    name: '7. banijska divizija',
    description:
      'Ustanovljena 22. novembra 1942. Štab divizije z njegovimi službami in spremljevalnimi enotami v bitki na Sutjeski, maja in junija 1943.',
  },
  'centralna-bolnica': {
    name: 'Centralna bolnišnica',
    description:
      'Ustanovljena novembra 1941 v zahodni Srbiji. Osebje bolnišnice in ranjenci, katerih enote ni bilo mogoče ugotoviti, v bitki na Sutjeski, maja in junija 1943.',
  },
  '3-licka-brigada': {
    name: '3. liška proletarska brigada',
    description:
      'Ustanovljena 9. septembra 1942 v Mogoriću pri Gospiću kot 9. hrvaška brigada. Padli, umrli in pogrešani borci brigade ter njeni narodni heroji.',
  },
  'pozarevacki-odred': {
    name: 'Požarevški partizanski odred',
    description:
      'Ustanovljen avgusta 1941 v požarevškem okrožju. Vsi borci odreda od 1941 do oktobra 1944, ko je prešel v NOVJ.',
  },
  '1-proleterski-bataljon-hrvatske': {
    name: '1. proletarski bataljon Hrvaške',
    description:
      'Ustanovljen 7. maja 1942 v Korenici. Borci bataljona, do njegovega vstopa v 13. proletarsko brigado »Rade Končar«.',
  },
  'pionirska-ceta-divoselo': {
    name: 'Prva oborožena pionirska partizanska četa',
    description:
      'Ustanovljena 7. novembra 1942 v Divoselu pri Gospiću. Borci čete, otroci iz Divosela in okoliških vasi.',
  },
  '4-pomorski-sektor': {
    name: 'IV. pomorski obalni sektor',
    description: 'Ustanovljen 30. oktobra 1943 na Hvaru, sektor mornarice NOVJ za srednjo Dalmacijo in otoke. Vsi borci sektorja in od kod je kdo, pri padlih in umrlih tudi kje so padli, ter štab sektorja.',
  },
  'viski-bataljon': {
    name: 'Viški prostovoljni bataljon',
    description: 'Ustanovljen januarja 1944 na Visu za obrambo otoka, razpuščen konec aprila 1944. Borci bataljona po četah in vodih, konec januarja 1944.',
  },
  'kokrski-odred': {
    name: 'Kokrški odred',
    description: 'Ustanovljen 18. junija 1942 na Kališču pod Storžičem, drugič 27. avgusta 1944 v Dragi pri Begunjah. Borci prvega odreda z življenjepisi in spisek drugega po štabih, službah in četah.',
  },
  'cankarjev-bataljon': {
    name: 'Cankarjev bataljon',
    description: 'Ustanovljen 5. avgusta 1941 na Vodiški planini na Jelovici; januarja 1942 dražgoška bitka. Padli cankarjevci in preživeli udeleženci dražgoške bitke.',
  },
  'novosadski-odred': {
    name: 'Novosadski partizanski odred',
    description: 'Ustanovljen leta 1941, znova 28. avgusta 1944 na Palenkaševem salašu pri Bačkem Petrovcu. Pripadniki odreda v letih 1941 in 1944.',
  },
  'deveta-brigada': {
    name: 'Deveta brigada (Kočevska)',
    description: 'Ustanovljena 14. septembra 1943 iz bataljonov Zapadnodolenjskega odreda, v sestavu 18. divizije. Štabi brigade in bataljonov; borci brigade: leto in kraj rojstva, pri padlih tudi kje so padli.',
  },
  '4-prekomorska-brigada': {
    name: '4. prekomorska brigada',
    description: 'Ustanovljena 7. septembra 1944 v Italiji pri bazi NOVJ v Bariju: nakladanje in prevoz zavezniške pomoči. Padli in umrli ter vodilni kader.',
  },
  '9-srpska-brigada': {
    name: '9. srbska brigada',
    description: 'Ustanovljena 11. marca 1944 v Rečici. Borci v stroju na dan ustanovitve, poveljniški kader brigade, bataljonov in čet ter bolničarke in borke.',
  },
  'kozjanski-odred': {
    name: 'Kozjanski odred',
    description: 'Ustanovljen 27. aprila 1944 na Kozjanskem iz Kozjanskega bataljona. Vsi borci in borke odreda do njegove ukinitve: rojstvo, vstop v NOV, poklic in usoda.',
  },
  'proleterski-bataljon-bk': {
    name: 'Proletarski bataljon Bosanske krajine',
    description: 'Ustanovljen 25. marca 1942 v Čelincu iz Kozaraške in Grmečke proletarske čete ter Drvarskega proletarskega voda. Življenjepisi borcev, ob fotografiji vsakega.',
  },
  '1-tenkovski-bataljon': {
    name: 'Prvi tankovski bataljon',
    description: 'Ustanovljen 21. septembra 1943 v Liki iz Tankovske čete 1. korpusa. Pripadniki tankovskega voda, čete in bataljona Glavnega štaba Hrvaške.',
  },
  '3-diverzantski-odred': {
    name: 'Tretji diverzantski odred',
    description: 'Ustanovljen 7. septembra 1944 v Pobjeniku pri Čazmi iz 3. diverzantskega bataljona. Vsi borci in starešine diverzantske skupine, čete, bataljona in odreda.',
  },
  '1-2-prekomorska-brigada': {
    name: '1. in 2. prekomorska brigada',
    description: 'Ustanovljeni oktobra 1943 v Italiji, v taboriščih Carbonara in Gravina, iz Primorcev in Istranov iz italijanske vojske, zaporov in internacije. Padli in vodilni kader.',
  },
  '5-prekomorska-brigada': {
    name: '5. prekomorska brigada',
    description: 'Ustanovljena 23. decembra 1944 v Splitu iz Slovencev, ki so prešli iz zavezniških armad in ujetništva. Padli in poveljniški kader.',
  },
  'sercerjeva-brigada': {
    name: 'Šercerjeva brigada',
    description: 'Ustanovljena 6. oktobra 1942 na Mokrcu. Prostovoljci do konca februarja 1943 in padli do konca leta 1943, po kraju in dnevu smrti.',
  },
  'kosovelova-brigada': {
    name: 'Kosovelova brigada',
    description: 'Ustanovljena 23. septembra 1943 na Krasu. Padli, pogrešani in za posledicami ran umrli ter poveljniški kader brigade in bataljonov.',
  },
  'eskadrile-novj': {
    name: '1. in 2. eskadrilja NOVJ',
    description: 'Prva ustanovljena 22. aprila 1944 na letališču Benina v Libiji, druga 1. julija 1944. Piloti, mehaniki in drugo moštvo obeh eskadrilj.',
  },
  '42-vazduhoplovna-divizija': {
    name: '42. letalska divizija',
    description: 'Ustanovljena 29. decembra 1944 v Zemunu. Moštvo divizije po polkih in delavnicah: čin in dolžnost.',
  },
  '18-srpska-brigada': {
    name: '18. srbska brigada',
    description: 'Ustanovljena junija 1944 pod Velikim Jastrebcem. Vsi borci in starešine brigade, z letom in krajem rojstva ter tem, kako so padli ali bili ranjeni.',
  },
  '5-srpska-brigada': {
    name: '5. srbska brigada',
    description: 'Ustanovljena 14. januarja 1944 v Veliki Plani pri Prokuplju kot 3. južnomoravska brigada. Padli in umrli borci in starešine brigade.',
  },
  'cacanski-odred': {
    name: 'Čačanski partizanski odred "Dr. Dragiša Mišović"',
    description: 'Ustanovljen 6. julija 1941 v Kulinovcih pri Čačku. Padli borci odreda, po pokrajinah in vaseh.',
  },
  'mostarski-bataljon': {
    name: 'Mostarski bataljon',
    description: 'Ustanovljen septembra 1941 kot Konjiški bataljon, od 21. junija 1942 Mostarski. Borci bataljona do maja 1944, s kratkimi življenjepisi.',
  },
  '13-krajiska-brigada': {
    name: '13. krajiška brigada',
    description: 'Ustanovljena 23. avgusta 1943 iz Ribniškega partizanskega odreda. Borci brigade avgusta in septembra 1943 in njeni člani KPJ maja 1945.',
  },
  '1-krajiska-brigada': {
    name: '1. krajiška proletarska udarna brigada',
    description: 'Ustanovljena 21. maja 1942 v Lamoviti pri Prijedoru. Padli, umrli in pogrešani borci brigade.',
  },
  'ostali-borci': {
    name: 'Borci drugih enot',
    description:
      'Borci iz spominskih knjig, vaških kronik in zbornikov narodnih herojev, katerih enote še ni na strani.',
  },
  'ostali-borci-slovenija': {
    name: 'Borci drugih enot – Slovenija',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Slovenije, katerih enote še ni na strani.',
  },
  'ostali-borci-hrvatska': {
    name: 'Borci drugih enot – Hrvaška',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Hrvaške, katerih enote še ni na strani.',
  },
  'ostali-borci-bih': {
    name: 'Borci drugih enot – Bosna in Hercegovina',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Bosne in Hercegovine, katerih enote še ni na strani.',
  },
  'ostali-borci-crna-gora': {
    name: 'Borci drugih enot – Črna gora',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Črne gore, katerih enote še ni na strani.',
  },
  'ostali-borci-makedonija': {
    name: 'Borci drugih enot – Makedonija',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Makedonije, katerih enote še ni na strani.',
  },
  'ostali-borci-srbija': {
    name: 'Borci drugih enot – Srbija',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja ožje Srbije, katerih enote še ni na strani.',
  },
  'ostali-borci-kosovo': {
    name: 'Borci drugih enot – Kosovo in Metohija',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Kosova in Metohije, katerih enote še ni na strani.',
  },
  'ostali-borci-vojvodina': {
    name: 'Borci drugih enot – Vojvodina',
    description:
      'Padli in umrli borci iz popisa žrtev vojne iz leta 1964 z območja Vojvodine, katerih enote še ni na strani.',
  },
}

const mk: Record<string, UnitText> = {
  'prva-licka-brigada': {
    name: 'Прва личка пролетерска бригада "Марко Орешковиќ"',
    description: 'Формирана на 8 јули 1942 кај изворот на Мрежница.',
  },
  'prva-proleterska-brigada': {
    name: 'Прва пролетерска народноослободителна ударна бригада',
    description: 'Формирана на 21 декември 1941.',
  },
  'ljubljanska-brigada': {
    name: '10-та словенечка народноослободителна ударна бригада "Љубљанска"',
    description: 'Формирана на 11 септември 1943.',
  },
  'druga-licka-brigada': {
    name: 'Втора личка пролетерска бригада',
    description: 'Формирана на 18 август 1942 во Лаудонов Гај. Загинати, починати и исчезнати борци, оние што ја преживеаја војната, и старешините на штабот на бригадата и на баталјоните.',
  },
  'treca-proleterska-brigada': {
    name: 'Трета пролетерска (санџачка) бригада',
    description: 'Формирана на 5 јуни 1942. Списокот е од денот кога е формирана бригадата.',
  },
  '13-proleterska-brigada': {
    name: '13-та пролетерска ударна бригада "Раде Кончар"',
    description: 'Формирана на 7 ноември 1942. Загинати и преживеани борци.',
  },
  '2-dalmatinska-brigada': {
    name: '2-ра далматинска пролетерска ударна бригада',
    description: 'Формирана на 3 октомври 1942. Борци на бригадата и штабовите и командите на бригадата, баталјоните и четите.',
  },
  '4-splitska-brigada': {
    name: '4-та сплитска ударна бригада',
    description: 'Формирана во септември 1943. Загинати и преживеани борци.',
  },
  'prva-vojvodjanska-brigada': {
    name: 'Прва војводинска бригада',
    description: 'Формирана на 11 април 1943 во Брѓани на Мајевица. Борци на бригадата.',
  },
  '5-kozaracka-brigada': {
    name: '5-та краишка (козарачка) ударна бригада',
    description: 'Формирана на 23 септември 1942 на Козара. Загинати, исчезнати и починати борци и старешини.',
  },
  '2-vojvodjanska-brigada': {
    name: '2-ра војводинска ударна бригада',
    description: 'Формирана на 20 април 1943 на Мајевица. Борци и старешини од формирањето до крајот на војната.',
  },
  '8-krajiska-brigada': {
    name: '8-ма краишка ударна бригада',
    description: 'Формирана на 28 декември 1942 во Цазин. Борци што загинале или починале во војната.',
  },
  '6-krajiska-brigada': {
    name: '6-та краишка ударна бригада',
    description: 'Формирана на 14 октомври 1942 од единиците на Првиот краишки одред. Загинати и починати борци и старешини, старешините на бригадата 1942–1943 и борци што ја преживеаја војната.',
  },
  '4-krajiska-brigada': {
    name: '4-та краишка ударна бригада',
    description: 'Формирана на 9 септември 1942 во Тичево кај Босанско Грахово. Загинати, починати и исчезнати борци и старешини.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3-та краишка пролетерска ударна бригада',
    description: 'Формирана на 22 август 1942 во Каменица кај Дрвар. Борците на бригадата од формирањето до крајот на војната.',
  },
  '17-slavonska-brigada': {
    name: '17-та славонска ударна бригада',
    description: 'Формирана на 30 декември 1942 кај Воќин. Загинати и преживеани борци, по општини.',
  },
  '25-srpska-divizija': {
    name: '25-та српска ударна дивизија',
    description:
      'Формирана на 21 јуни 1944 кај Јошаница во Пуста Река. Загинати борци и старешини од 16-та, 18-та и 19-та српска бригада.',
  },
  '1-sumadijska-brigada': {
    name: '1-ва шумадиска бригада',
    description: 'Формирана на 5 октомври 1943. Загинати борци и старешини, и борци што ја преживеаја војната.',
  },
  '18-slavonska-brigada': {
    name: '18-та славонска ударна бригада',
    description: 'Формирана на 11 февруари 1943 во Мијача кај Пакрац. Загинати, починати и преживеани борци.',
  },
  '4-banijska-brigada': {
    name: '4-та банијска бригада',
    description: 'Формирана на 30 јуни 1943 во Обијај на Банија. Бригада на 7-та дивизија. Старешините на штабовите и борците на бригадата.',
  },
  '4-srpska-brigada': {
    name: '4-та српска ударна бригада',
    description:
      'Формирана на 20 ноември 1943 во Буци кај Крушевац. Борци на бригадата, меѓу нив и странци и борци чие име не е утврдено.',
  },
  '7-vojvodjanska-brigada': {
    name: '7-ма војводинска ударна бригада',
    description:
      'Формирана на 2 јули 1944 на фармата на Мушицки кај Батровци. Преживеани, загинати и борци починати по војната, и борци од 4-тиот (рускиот) баталјон.',
  },
  '19-bircanska-brigada': {
    name: '19-та бирчанска бригада',
    description: 'Формирана на 24 октомври 1943 во Власеница. Борци на бригадата.',
  },
  '2-krajiska-brigada': {
    name: '2-ра краишка ударна бригада',
    description: 'Формирана на 2 август 1942. Загинати и починати борци и старешини.',
  },
  'tuzlanski-odred': {
    name: 'Тузлански партизански одред',
    description: 'Формиран на 24 октомври 1943 во Тузла. Борци на одредот, многумина и со фотографија.',
  },
  'uzicki-odred': {
    name: 'Ужички партизански одред "Димитрије Туцовиќ"',
    description: 'Формиран на 7 јули 1941 во Ужице. Борци на одредот загинати во војната 1941–1945.',
  },
  '14-srpska-brigada': {
    name: '14-та српска ударна бригада',
    description:
      'Формирана на 17 јуни 1944 во Рибаре кај Ѓунис. Загинати борци и старешини од Нишкиот одред и од 14-та српска бригада.',
  },
  '7-crnogorska-brigada': {
    name: '7-ма црногорска младинска бригада "Будо Томовиќ"',
    description: 'Формирана на 30 декември 1943 во Колашин. Загинати борци на бригадата.',
  },
  '17-majevicka-brigada': {
    name: '17-та мајевичка бригада',
    description:
      'Формирана на 10 октомври 1943 во околината на Тузла. Загинати и починати борци од Третиот мајевички одред и од 17-та мајевичка бригада.',
  },
  '25-brodska-brigada': {
    name: '25-та бродска бригада',
    description:
      'Формирана на 1 октомври 1943 кај Славонска Ораховица. Загинати борци, и сите борци и старешини на бригадата во октомври 1943.',
  },
  '25-srpska-brigada': {
    name: '25-та српска бригада',
    description:
      'Формирана на 1 септември 1944 во Стрелац кај Пирот. Загинати и ранети борци и старешини, според воените списоци на бригадата.',
  },
  '21-tuzlanska-brigada': {
    name: '21-ва тузланска бригада',
    description: 'Формирана на 19 септември 1944 во Пашабунар кај Тузла. Загинати борци и старешини.',
  },
  '53-srednjobosanska-divizija': {
    name: '53-та среднобосанска дивизија',
    description:
      'Формирана на 23 јули 1944 во средна Босна. Загинати, заробени и исчезнати борци од 14-та, 18-та и 19-та бригада и од Прњаворскиот и Мотајичкиот одред.',
  },
  '21-slavonska-brigada': {
    name: '21-ва славонска бригада',
    description: 'Формирана на 17 мај 1943 во Орљавац кај Славонска Пожега. Загинати, починати и исчезнати борци и старешини.',
  },
  '32-zagorska-divizija': {
    name: '32-ра загорска дивизија',
    description:
      'Формирана на 12 декември 1943 на Калник. Борци на дивизијата и на Западната група одреди, и борци на штабот и бригадите на дивизијата, со податоци за секого, и командниот состав.',
  },
  '1-dalmatinska-brigada': {
    name: '1-ва далматинска пролетерска бригада',
    description:
      'Формирана на 6 септември 1942 во селото Добро кај Ливно. Борци загинати во војната, борци на Сутјеска, жени борци 1944–1945, командири и комесари на четите и командниот состав на бригадата и баталјоните.',
  },
  '16-slavonska-omladinska-brigada': {
    name: '16-та славонска младинска бригада "Јоже Влаховиќ"',
    description:
      'Формирана на 29 декември 1942 во Горни Борки кај Дарувар. Загинати борци и старешини, загинатите во Покупје и на Жумберак, и раководството на бригадата од формирањето до крајот на војната.',
  },
  '8-crnogorska-brigada': {
    name: '8-ма црногорска бригада',
    description: 'Формирана на 25 февруари 1944 во Беране. Загинати борци и старешини, и дополнителен список на загинатите од Уб.',
  },
  'druga-proleterska-brigada': {
    name: 'Втора пролетерска бригада',
    description:
      'Формирана на 1 март 1942 во Чајниче. Загинати, починати и исчезнати борци, по место и ден на загинувањето, од Сутјеска до Сремскиот фронт.',
  },
  '4-proleterska-brigada': {
    name: '4-та пролетерска црногорска бригада',
    description:
      'Формирана на 10 јуни 1942. Борците на денот на формирањето и во битката на Сутјеска, старешините на бригадата и народните херои, и борци и старешини загинати од 1942 до 1945.',
  },
  '5-proleterska-brigada': {
    name: '5-та пролетерска црногорска бригада',
    description:
      'Формирана на 12 јуни 1942 во Смријечно кај Шавник. Борците на бригадата во битката на Сутјеска, мај и јуни 1943, и партизанките на бригадата.',
  },
  '6-istocnobosanska-brigada': {
    name: '6-та источнобосанска пролетерска бригада',
    description:
      'Формирана на 2 август 1942 во Шековиќи кај Власеница. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '10-hercegovacka-brigada': {
    name: '10-та херцеговска бригада',
    description:
      'Формирана на 10 август 1942 кај Купрес. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '7-banijska-brigada': {
    name: '7-ма банијска бригада "Васиљ Гаќеша"',
    description:
      'Формирана на 2 септември 1942. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '8-banijska-brigada': {
    name: '8-ма банијска бригада',
    description:
      'Формирана на 7 септември 1942 во Обљај кај Глина. Борците на бригадата во битката на Сутјеска, мај и јуни 1943, загинатите и починатите борци на бригадата и командниот состав.',
  },
  '3-dalmatinska-brigada': {
    name: '3-та далматинска бригада',
    description:
      'Формирана на 12 ноември 1942 во Врба кај Сињ. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '9-dalmatinska-divizija': {
    name: '9-та далматинска дивизија',
    description:
      'Формирана на 11 февруари 1943 од 3-та, 4-та и 5-та далматинска бригада, расформирана во април истата година. Загинатите и исчезнатите борци на дивизијата од февруари до април 1943.',
  },
  '16-banijska-brigada': {
    name: '16-та банијска бригада',
    description:
      'Формирана на 26 декември 1942 во Класниќ. Борците на бригадата во битката на Сутјеска, мај и јуни 1943, и борци и старешини загинати до крајот на јуни 1943.',
  },
  '7-krajiska-brigada': {
    name: '7-ма краишка бригада',
    description:
      'Формирана на 27 декември 1942 во Ораховљани кај Кључ. Преживеани и загинати борци и старешини, од формирањето до крајот на војната.',
  },
  '15-majevicka-brigada': {
    name: '15-та мајевичка бригада',
    description:
      'Формирана на 11 април 1943. Борците на бригадата, тогаш 1-ва мајевичка, во битката на Сутјеска, мај и јуни 1943.',
  },
  '12-dalmatinska-brigada': {
    name: '12-та далматинска (1-ва островска) бригада',
    description:
      'Формирана на 15 септември 1943 на островите Брач, Хвар, Вис и Шолта. Загинати борци и старешини, по борбите во кои загинале, и раководниот кадар на штабот на бригадата и на баталјоните.',
  },
  '3-makedonska-brigada': {
    name: '3-та македонска бригада',
    description:
      'Формирана на 26 февруари 1944 во селото Жеглане кај Куманово. Загинати борци.',
  },
  '18-hrvatska-brigada': {
    name: '18-та хрватска источнобосанска бригада',
    description:
      'Формирана на 10 октомври 1943 кај Тузла, а прогласена на 17 октомври во Хусино. Борци и старешини на бригадата.',
  },
  '11-dalmatinska-brigada': {
    name: '11-та далматинска бригада',
    description:
      'Формирана на 2 октомври 1943 на Биоково. Загинати, исчезнати и преживеани борци и старешините на штабовите и командите.',
  },
  '12-krajiska-brigada': {
    name: '12-та краишка бригада',
    description:
      'Формирана на 19 февруари 1943 во Дриниќ. Загинати и преживеани борци и старешини.',
  },
  '17-srpska-brigada': {
    name: '17-та српска бригада',
    description:
      'Формирана на 2 јуни 1944 во Механе кај Куршумлија. Преживеани и загинати борци.',
  },
  '14-srednjobosanska-brigada': {
    name: '14-та среднобосанска бригада',
    description:
      'Формирана на 17 октомври 1943 на Цер кај Прњавор. Загинати, починати и исчезнати борци, и борци што ја преживеаја војната.',
  },
  '3-vojvodjanska-brigada': {
    name: '3-та војводинска бригада',
    description:
      'Формирана на 15 мај 1943 во Срем. Загинати борци и старешини, оние чија судбина остана неутврдена, и преживеаните.',
  },
  'kalnicki-odred': {
    name: 'Калнички партизански одред',
    description:
      'Формиран на 10 октомври 1942 во Бијела кај Дарувар. Борци на одредот, загинати и преживеани, и раководителите на одредот и неговите единици.',
  },
  'posavsko-trebavski-odred': {
    name: 'Посавско-требавски партизански одред',
    description:
      'Формиран на 4 февруари 1944 кај Градачац од Посавскиот и Требавскиот одред. Борци на одредот.',
  },
  '8-kordunaska-divizija': {
    name: '8-ма кордунска дивизија',
    description:
      'Формирана на 22 ноември 1942 во Цреварска Страна на Петрова гора. Штабовите на дивизијата, бригадите и баталјоните и загинатите борци на дивизијата.',
  },
  'cankarjeva-brigada': {
    name: 'Цанкарјева бригада',
    description:
      'Формирана на 28 септември 1942 кај Лапиње во Кочевско. Штабовите на бригадата и баталјоните, загинати и преживеани борци.',
  },
  'gubceva-brigada': {
    name: 'Губчева бригада',
    description:
      'Формирана на 4 септември 1942 кај Требелно над Мокроног. Штабовите на бригадата и баталјоните, загинати и преживеани борци.',
  },
  'dvanajsta-brigada': {
    name: '12-та словенечка бригада',
    description:
      'Формирана на 24 септември 1943 во Мокроног. Штабовите на бригадата и баталјоните, загинати и преживеани борци.',
  },
  'gradnikova-brigada': {
    name: 'Градникова бригада',
    description:
      'Формирана во април 1943 на Голобар кај Бовец. Загинати борци и другите борци на бригадата, нејзиниот штаб и народните херои.',
  },
  'zidanskova-brigada': {
    name: 'Зиданшкова бригада',
    description:
      'Формирана на 8 јануари 1944 кај Свети Примож на Похорје. Штабот на бригадата, борци на бригадата, загинати и преживеани.',
  },
  'skofjeloski-odred': {
    name: 'Шкофјелошки одред',
    description:
      'Формиран по наредба од 30 јули 1944, во ридовите околу Шкофја Лока. Имиња на борците на одредот.',
  },
  'istrski-odred': {
    name: 'Истарски одред',
    description:
      'Формиран на 7 октомври 1943 во Бркини. Штабовите на одредот, баталјоните и четите, загинати и другите борци на одредот.',
  },
  'zapadnodolenjski-odred': {
    name: 'Западнодолењски одред',
    description:
      'Формиран кон крајот на јуни 1942 во Долењско. Загинати и другите борци на одредот.',
  },
  'braciceva-brigada': {
    name: 'Брачичева бригада',
    description:
      'Формирана на 23 септември 1943 во Кнежја Њива во Лошка долина. Загинати и преживеани борци.',
  },
  'tomsiceva-brigada': {
    name: 'Томшичева бригада',
    description:
      'Формирана на 16 јули 1942 во Цеста во Кочевско. Борци на единиците од кои настана и борци на бригадата до крајот на војната.',
  },
  '1-slovenska-artilerijska-brigada': {
    name: '1-ва словенечка артилериска бригада',
    description:
      'Формирана на 6 мај 1944 во Лашче кај Двор. Старешините и артилерците на бригадата и загинатите.',
  },
  'artilerija-9-korpusa': {
    name: 'Артилерија на 9-ти корпус',
    description:
      'Формирана на 14 јуни 1944 во Горњи Локовец. Борците на артилеријата и загинатите.',
  },
  '19-srpska-brigada': {
    name: '19-та српска бригада',
    description:
      'Формирана на 12 јуни 1944 во Горња Јошаница. Загинати, исчезнати и починати борци, оние што ја преживеаја војната и штабовите на бригадата и баталјоните.',
  },
  '22-srpska-brigada': {
    name: '22-ра српска космајска бригада',
    description:
      'Формирана на 12 септември 1944 на Брдњак кај Друговац. Загинати и преживеани борци и старешини.',
  },
  '12-vojvodjanska-brigada': {
    name: '12-та војводинска бригада',
    description:
      'Формирана на 8 октомври 1944 во Војловица кај Панчево. Борците на бригадата по местата каде што живееле и загинатите.',
  },
  '4-vojvodjanska-brigada': {
    name: '4-та војводинска бригада',
    description:
      'Формирана на 7 октомври 1943 во шумата Варадин кај Вишњићево. Борците од првиот состав на бригадата и загинатите.',
  },
  '1-kosovsko-metohijska-brigada': {
    name: '1-ва косовско-метохиска бригада',
    description:
      'Формирана на 24 јуни 1944 во селото Збажди во западна Македонија. Борците на бригадата, загинатите и ранетите.',
  },
  '8-vojvodjanska-brigada': {
    name: '8-ма војводинска бригада',
    description:
      'Формирана на 12 септември 1944 на чистината Јабука на Фрушка Гора. Загинати и исчезнати борци и старешини.',
  },
  '19-sjevernodalmatinska-divizija': {
    name: '19-та севернодалматинска дивизија',
    description:
      'Формирана на 11 октомври 1943 во Биовичино Село во Буковица. Командантите и комесарите на дивизијата и бригадите, народните херои и загинатите и починатите борци на дивизијата.',
  },
  '21-srpska-brigada': {
    name: '21-ва српска бригада',
    description:
      'Формирана на 10 мај 1944 во Требеж кај Даросава. Загинати и преживеани борци и други што се бореа во бригадата.',
  },
  '14-hercegovacka-brigada': {
    name: '14-та херцеговска бригада',
    description:
      'Формирана на 4 септември 1944 кај Љубиње, како младинска бригада. Сите борци што поминале низ бригадата, загинатите и командниот состав.',
  },
  '5-vojvodjanska-brigada': {
    name: '5-та војводинска бригада',
    description:
      'Формирана на 15 ноември 1943 во Обршини на Мајевица. Борците и старешините на бригадата.',
  },
  '6-vojvodjanska-brigada': {
    name: '6-та војводинска бригада',
    description:
      'Формирана на 17 јануари 1944 на Јабучје кај Сремска Рача. Загинатите борци и раководители на бригадата и членовите на штабовите и командите на четите.',
  },
  '13-vojvodjanska-brigada': {
    name: '13-та војводинска бригада',
    description:
      'Формирана на 14 октомври 1944 во Кикинда. Борците на бригадата, поименично.',
  },
  '7-srpska-brigada': {
    name: '7-ма српска бригада',
    description:
      'Формирана на 4 февруари 1944 во Јабуковик кај Црна Трава, како 5-та јужноморавска. Борците во мај 1944 и загинатите, починатите и исчезнатите.',
  },
  '15-srpska-brigada': {
    name: '15-та српска бригада',
    description:
      'Формирана на 2 јуни 1944 во Реткоцер, во Горна Јабланица. Борците и раководителите на бригадата, загинатите и ранетите.',
  },
  '8-srpska-brigada': {
    name: '8-ма српска бригада',
    description:
      'Формирана на 8 март 1944 во Трговиште, како 6-та јужноморавска. Загинатите борци на бригадата.',
  },
  '10-srpska-brigada': {
    name: '10-та српска бригада',
    description:
      'Формирана на 8 мај 1944 во Јабуковик кај Црна Трава. Загинатите, починатите и исчезнатите борци и раководители на бригадата.',
  },
  '23-srpska-brigada': {
    name: '23-та српска бригада',
    description:
      'Формирана на 2 септември 1944 во Шуман Топла кај Књажевац. Загинатите и починатите борци и раководители на бригадата.',
  },
  '12-srpska-brigada': {
    name: '12-та српска бригада',
    description:
      'Формирана на 22 мај 1944 на Острозуб, јужно од Бистрица. Загинатите и починатите борци и раководители на бригадата.',
  },
  '20-srpska-brigada': {
    name: '20-та српска бригада',
    description:
      'Формирана на 19 август 1944 над селото Бучје кај Књажевац. Загинатите и починатите борци и раководители на бригадата.',
  },
  '1-konjicka-brigada': {
    name: '1-ва коњаничка бригада',
    description:
      'Формирана на 15 септември 1944 во Славковица кај Љиг. Воениот список на старешините и борците на бригадата и загинатите.',
  },
  'toplicki-odred': {
    name: 'Топлички партизански одред',
    description:
      'Формиран на 3 август 1941 во Ајдановац кај Прокупље. Борците на денот на формирањето, загинатите и починатите, народните херои на одредот.',
  },
  'karlovacka-brigada': {
    name: 'Карловачка ударна бригада',
    description:
      'Формирана на 5 март 1944 во Храшќе кај Озаљ. Борците на бригадата на денот на формирањето, загинатите и командниот состав.',
  },
  '14-primorsko-goranska': {
    name: '14-та приморско-горанска бригада',
    description:
      'Формирана на 26 ноември 1942 во Дрежница. Загинатите борци на бригадата.',
  },
  '22-divizija': {
    name: '22-ра дивизија',
    description:
      'Формирана во мај 1944 на десниот брег на Јужна Морава. Загинатите борци на 8-ма, 10-та и 12-та српска бригада.',
  },
  '34-divizija': {
    name: '34-та дивизија',
    description:
      'Формирана на 30 јануари 1944 на Жумберак и во Покупље. Загинатите борци и раководители на дивизијата и нејзините бригади и командниот состав.',
  },
  '4-sandzacka-brigada': {
    name: '4-та санџачка бригада',
    description:
      'Формирана на 1 декември 1943 во Пљевља. Загинатите и ранетите борци на бригадата.',
  },
  '3-primorsko-goranska': {
    name: '3-та приморско-горанска бригада',
    description:
      'Формирана на 15 септември 1943 во Шкрљево во Хрватското приморје. Штабовите на бригадата и баталјоните, старешините и четните болничари на бригадата и загинатите.',
  },
  '13-hercegovacka-brigada': {
    name: '13-та херцеговска бригада',
    description:
      'Формирана на 14 мај 1944 во Херцеговина. Загинатите борци и старешини на бригадата, сите што се бореле во неа и старешинскиот состав.',
  },
  '12-hercegovacka-brigada': {
    name: '12-та херцеговска бригада',
    description:
      'Формирана на 16 ноември 1943 во Херцеговина, од групите баталјони на 10-та херцеговска. Загинатите борци и старешини на бригадата.',
  },
  '1-bokeljska-brigada': {
    name: '1-ва бокељска бригада',
    description:
      'Формирана на 5 октомври 1944 во Коњско кај Требиње. Сите борци и старешини на бригадата по единици, и загинатите, починатите и исчезнатите.',
  },
  '6-dalmatinska-brigada': {
    name: '6-та далматинска бригада',
    description:
      'Формирана на 8 октомври 1943 во Ервеник, како 2-ра бригада на 19-та дивизија. Штабовите на бригадата и баталјоните и загинатите борци на бригадата.',
  },
  'osjecka-brigada': {
    name: 'Осиечка ударна бригада',
    description:
      'Формирана на 1 март 1944 кај Слободна Власт близу Ѓаково. Загинатите и починатите борци на бригадата и преживеаните, по општини, и нејзините старешини.',
  },
  '4-brigada-slavonije': {
    name: '4-та бригада на Славонија',
    description:
      'Формирана на 28 септември 1944 во Подравска Слатина, како 4-та бригада на 12-та дивизија, наречена Втора бродска. Загинатите и ранетите борци на бригадата и нејзините раководители.',
  },
  '12-slavonska-brigada': {
    name: '12-та пролетерска славонска бригада',
    description:
      'Формирана на 11 октомври 1942 во Будиќи кај Пакрац, како 1-ва славонска бригада, пролетерска од 26 октомври 1944. Жените борци на бригадата, загинати, починати и преживеани.',
  },
  'zagrebacki-odred': {
    name: 'Загрепски партизански одред',
    description:
      'Формиран на 13 септември 1943 на Загрепска Гора. Список на борците на одредот: село, општина и судбина.',
  },
  'mosorski-odred': {
    name: 'Мосорски партизански одред',
    description:
      'Формиран на 21 февруари 1942 на Мосор, повторно на 11 октомври 1943, расформиран на 10 ноември 1944. Сите борци на одредот 1942–1944, со кратки биографии, и раководниот кадар на одредот.',
  },
  'turopoljsko-posavski-odred': {
    name: 'Туропољско-посавски партизански одред',
    description:
      'Формиран на 8 август 1943 кај Чичка Пољана. Загинатите борци на одредот и оние што непријателите ги стрелаа или умреа во војната.',
  },
  'zascitni-bataljon-vpv': {
    name: 'Заштитен баталјон на ИООФ и ЦК КПС',
    description:
      'Формиран во април 1944 од четите што од 1942 ги чуваа базите и членовите на политичкото раководство на Словенија. Преживеаните и загинатите припадници.',
  },
  '1-zagorska-brigada': {
    name: '1-ва загорска бригада',
    description:
      'Формирана на 8 мај 1944 во Селница под Иванчица. Загинатите борци и раководители на бригадата.',
  },
  '6-crnogorska-brigada': {
    name: '6-та црногорска бригада',
    description:
      'Формирана на 14 ноември 1943 во Дријенак кај Колашин. Загинатите и починатите борци и старешини на бригадата.',
  },
  '11-krajiska-brigada': {
    name: '11-та краишка (козарачка) бригада',
    description:
      'Формирана на 23 август 1943 на Козара, од Козарскиот НОП одред. Загинатите борци на бригадата, по општини, и список на борките.',
  },
  '3-banijska-brigada': {
    name: '3-та банијска бригада',
    description:
      'Формирана на 1 мај 1943 во Комоговина како 4-та банијска бригада; од септември 1943 3-та бригада на 7-ма банијска дивизија. Раководителите и борците на бригадата.',
  },
  'macvanski-odred': {
    name: 'Мачвански (Подрински) партизански одред',
    description:
      'Формиран на 16 јули 1941 на Бубања кај Глушци во Мачва; од август Подрински партизански одред. Борците на одредот од јули 1941 до март 1942, по местата од кои дошле.',
  },
  'posavski-odred': {
    name: 'Посавски партизански одред',
    description:
      'Формиран на 31 јули 1941 со одлука на Главниот штаб за Србија, од две посавски чети и Тамнавската чета. Борците на одредот во 1941, по баталјони.',
  },
  '51-divizija': {
    name: '51-ва војводинска дивизија',
    description:
      'Формирана на 31 октомври 1944 во Нови Сад, од 7-ма, 8-ма и 12-та војводинска бригада. Борците на дивизијата загинати од формирањето до крајот на војната, мај 1945, и исчезнати во Батинската битка.',
  },
  'vrhovni-stab': {
    name: 'Врховен штаб на НОВ и ПОЈ',
    description:
      'Формиран на 27 јуни 1941 во Белград, како Главен штаб на партизанските одреди на Југославија. Припадниците на Врховниот штаб, неговите служби, Придружниот баталјон и британската воена мисија во битката на Сутјеска, мај и јуни 1943, и работниците на неговата воено-техничка работилница во Грмеч 1942–1943.',
  },
  '1-proleterska-divizija': {
    name: '1-ва пролетерска дивизија',
    description:
      'Формирана на 1 ноември 1942 во Босански Петровац. Штабот на дивизијата, неговите служби и придружни единици во битката на Сутјеска, мај и јуни 1943.',
  },
  '2-proleterska-divizija': {
    name: '2-ра пролетерска дивизија',
    description:
      'Формирана на 1 ноември 1942 во Тичево. Штабот на дивизијата, неговите служби и придружни единици во битката на Сутјеска, мај и јуни 1943.',
  },
  '3-udarna-divizija': {
    name: '3-та ударна дивизија',
    description:
      'Формирана на 1 ноември 1942 во Тичево. Штабот на дивизијата, неговите служби и придружни единици во битката на Сутјеска, мај и јуни 1943.',
  },
  '7-banijska-divizija': {
    name: '7-ма банијска дивизија',
    description:
      'Формирана на 22 ноември 1942. Штабот на дивизијата, неговите служби и придружни единици во битката на Сутјеска, мај и јуни 1943.',
  },
  'centralna-bolnica': {
    name: 'Централна болница',
    description:
      'Формирана во ноември 1941 во западна Србија. Персоналот на болницата и ранетите чија единица не можела да се утврди, во битката на Сутјеска, мај и јуни 1943.',
  },
  '3-licka-brigada': {
    name: '3-та личка пролетерска бригада',
    description:
      'Формирана на 9 септември 1942 во Могориќ кај Госпиќ како 9-та хрватска бригада. Загинатите, починатите и исчезнатите борци на бригадата и нејзините народни херои.',
  },
  'pozarevacki-odred': {
    name: 'Пожаревачки партизански одред',
    description:
      'Формиран во август 1941 во Пожаревачкиот округ. Сите борци на одредот од 1941 до октомври 1944, кога влезе во НОВЈ.',
  },
  '1-proleterski-bataljon-hrvatske': {
    name: '1-ви пролетерски баталјон на Хрватска',
    description:
      'Формиран на 7 мај 1942 во Кореница. Борците на баталјонот, до неговото влегување во 13-та пролетерска бригада „Раде Кончар“.',
  },
  'pionirska-ceta-divoselo': {
    name: 'Прва вооружена пионерска партизанска чета',
    description:
      'Формирана на 7 ноември 1942 во Дивосело кај Госпиќ. Борците на четата, деца од Дивосело и околните села.',
  },
  '4-pomorski-sektor': {
    name: 'IV поморски крајбрежен сектор',
    description: 'Формиран на 30 октомври 1943 во Хвар, сектор на морнарицата на НОВЈ за средна Далмација и островите. Сите борци на секторот и од каде е кој, а за загинатите и починатите и каде паднале, и штабот на секторот.',
  },
  'viski-bataljon': {
    name: 'Вишки доброволен баталјон',
    description: 'Формиран во јануари 1944 на Вис за одбрана на островот, расформиран кон крајот на април 1944. Борците на баталјонот по чети и водови, кон крајот на јануари 1944.',
  },
  'kokrski-odred': {
    name: 'Кокршки одред',
    description: 'Формиран на 18 јуни 1942 на Калишче под Сторжич, а втор пат на 27 август 1944 во Драга кај Бегуње. Борците на првиот одред со биографии и списокот на вториот по штабови, служби и чети.',
  },
  'cankarjev-bataljon': {
    name: 'Цанкаров баталјон',
    description: 'Формиран на 5 август 1941 на Водишката планина на Јеловица; во јануари 1942 битката за Драгоше. Загинатите борци на баталјонот и преживеаните учесници во битката за Драгоше.',
  },
  'novosadski-odred': {
    name: 'Новосадски партизански одред',
    description: 'Формиран во 1941, а повторно на 28 август 1944 на Паленкашевиот салаш кај Бачки Петровац. Припадниците на одредот во 1941 и 1944 година.',
  },
  'deveta-brigada': {
    name: 'Деветта бригада (Кочевска)',
    description: 'Формирана на 14 септември 1943 од баталјоните на Западнодолењскиот одред, во составот на 18-та дивизија. Штабовите на бригадата и баталјоните; борците на бригадата: година и место на раѓање, а за загинатите и каде паднале.',
  },
  '4-prekomorska-brigada': {
    name: '4-та прекуморска бригада',
    description: 'Формирана на 7 септември 1944 во Италија, при базата на НОВЈ во Бари: товарење и превоз на сојузничката помош. Загинатите и починатите и командниот кадар.',
  },
  '9-srpska-brigada': {
    name: '9-та српска бригада',
    description: 'Формирана на 11 март 1944 во Речица. Борците во строј на денот на формирањето, командниот кадар на бригадата, баталјоните и четите и болничарките и борките.',
  },
  'kozjanski-odred': {
    name: 'Козјански одред',
    description: 'Формиран на 27 април 1944 на Козјанско, од Козјанскиот баталјон. Сите борци и борки на одредот до неговото расформирање: раѓање, влез во НОВ, занимање и судбина.',
  },
  'proleterski-bataljon-bk': {
    name: 'Пролетерски баталјон на Босанска Краина',
    description: 'Формиран на 25 март 1942 во Челинац, од Козарачката и Грмечката пролетерска чета и Дрварскиот пролетерски вод. Биографии на борците, со фотографија на секој.',
  },
  '1-tenkovski-bataljon': {
    name: 'Прв тенковски баталјон',
    description: 'Формиран на 21 септември 1943 во Лика, од Тенковската чета на 1-от корпус. Припадниците на тенковскиот вод, чета и баталјон на Главниот штаб на Хрватска.',
  },
  '3-diverzantski-odred': {
    name: 'Трет диверзантски одред',
    description: 'Формиран на 7 септември 1944 во Побјеник кај Чазма, од 3-от диверзантски баталјон. Сите борци и старешини на диверзантската група, чета, баталјон и одред.',
  },
  '1-2-prekomorska-brigada': {
    name: '1-ва и 2-ра прекуморска бригада',
    description: 'Формирани во октомври 1943 во Италија, во логорите Карбонара и Гравина, од Приморци и Истрани од италијанската војска, затворите и интернацијата. Загинатите и командниот кадар.',
  },
  '5-prekomorska-brigada': {
    name: '5-та прекуморска бригада',
    description: 'Формирана на 23 декември 1944 во Сплит, од Словенци што преминале од сојузничките армии и заробеништво. Загинатите и командниот кадар.',
  },
  'sercerjeva-brigada': {
    name: 'Шерцерјева бригада',
    description: 'Формирана на 6 октомври 1942 на Мокрц. Доброволците до крајот на февруари 1943 и загинатите до крајот на 1943, по местото и денот на загинувањето.',
  },
  'kosovelova-brigada': {
    name: 'Косовелова бригада',
    description: 'Формирана на 23 септември 1943 на Крас. Загинатите, исчезнатите и починатите од рани и командниот кадар на бригадата и баталјоните.',
  },
  'eskadrile-novj': {
    name: '1-ва и 2-ра ескадрила НОВЈ',
    description: 'Првата формирана на 22 април 1944 на аеродромот Бенина во Либија, втората на 1 јули 1944. Пилотите, механичарите и другиот состав на двете ескадрили.',
  },
  '42-vazduhoplovna-divizija': {
    name: '42-ра воздухопловна дивизија',
    description: 'Формирана на 29 декември 1944 во Земун. Составот на дивизијата по полкови и работилници: чин и должност.',
  },
  '18-srpska-brigada': {
    name: '18-та српска бригада',
    description: 'Формирана во јуни 1944 под Велики Јастребац. Сите борци и раководители на бригадата, со година и место на раѓање и како загинале или биле ранети.',
  },
  '5-srpska-brigada': {
    name: '5-та српска бригада',
    description: 'Формирана на 14 јануари 1944 во Велика Плана кај Прокупље како 3-та јужноморавска бригада. Загинатите и починатите борци и раководители на бригадата.',
  },
  'cacanski-odred': {
    name: 'Чачански партизански одред „Д-р Драгиша Мишовиќ“',
    description: 'Формиран на 6 јули 1941 во Кулиновци кај Чачак. Загинатите борци на одредот, по краеви и села.',
  },
  'mostarski-bataljon': {
    name: 'Мостарски баталјон',
    description: 'Формиран во септември 1941 како Коњички баталјон, Мостарски од 21 јуни 1942. Борците на баталјонот до мај 1944, со кратки биографии.',
  },
  '13-krajiska-brigada': {
    name: '13-та краишка бригада',
    description: 'Формирана на 23 август 1943 од Рибничкиот партизански одред. Борците на бригадата во август и септември 1943 и нејзините членови на КПЈ во мај 1945.',
  },
  '1-krajiska-brigada': {
    name: '1-ва краишка пролетерска ударна бригада',
    description: 'Формирана на 21 мај 1942 во Ламовита кај Приједор. Загинатите, починатите и исчезнатите борци на бригадата.',
  },
  'ostali-borci': {
    name: 'Борци од други единици',
    description:
      'Борци од споменици, хроники на селата и зборници на народни херои чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-slovenija': {
    name: 'Борци од други единици – Словенија',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Словенија, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-hrvatska': {
    name: 'Борци од други единици – Хрватска',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Хрватска, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-bih': {
    name: 'Борци од други единици – Босна и Херцеговина',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Босна и Херцеговина, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-crna-gora': {
    name: 'Борци од други единици – Црна Гора',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Црна Гора, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-makedonija': {
    name: 'Борци од други единици – Македонија',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Македонија, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-srbija': {
    name: 'Борци од други единици – Србија',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Србија без покраините, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-kosovo': {
    name: 'Борци од други единици – Косово и Метохија',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Косово и Метохија, чија единица сè уште не е на сајтот.',
  },
  'ostali-borci-vojvodina': {
    name: 'Борци од други единици – Војводина',
    description:
      'Загинати и починати борци од пописот на жртвите на војната од 1964, од подрачјето на Војводина, чија единица сè уште не е на сајтот.',
  },
}

const en: Record<string, UnitText> = {
  'prva-licka-brigada': {
    name: '1st Lika Proletarian Brigade "Marko Orešković"',
    description: 'Formed on 8 July 1942 at the source of the Mrežnica.',
  },
  'prva-proleterska-brigada': {
    name: '1st Proletarian People’s Liberation Assault Brigade',
    description: 'Formed on 21 December 1941.',
  },
  'ljubljanska-brigada': {
    name: '10th Slovene People’s Liberation Assault Brigade "Ljubljanska"',
    description: 'Formed on 11 September 1943.',
  },
  'druga-licka-brigada': {
    name: '2nd Lika Proletarian Brigade',
    description: 'Formed on 18 August 1942 in Laudonov Gaj. Partisans who were killed, died or went missing, those who survived the war, and the officers of the brigade and battalion staffs.',
  },
  'treca-proleterska-brigada': {
    name: '3rd Proletarian (Sandžak) Brigade',
    description: 'Formed on 5 June 1942. The roll is from the day the brigade was formed.',
  },
  '13-proleterska-brigada': {
    name: '13th Proletarian Assault Brigade "Rade Končar"',
    description: 'Formed on 7 November 1942. The fallen and the survivors.',
  },
  '2-dalmatinska-brigada': {
    name: '2nd Dalmatian Proletarian Assault Brigade',
    description: 'Formed on 3 October 1942. Members of the brigade, and the staffs and commands of the brigade, its battalions and companies.',
  },
  '4-splitska-brigada': {
    name: '4th Split Assault Brigade',
    description: 'Formed in September 1943. The fallen and the survivors.',
  },
  'prva-vojvodjanska-brigada': {
    name: '1st Vojvodina Brigade',
    description: 'Formed on 11 April 1943 in Brđani on Mount Majevica. Members of the brigade.',
  },
  '5-kozaracka-brigada': {
    name: '5th Krajina (Kozara) Assault Brigade',
    description: 'Formed on 23 September 1942 on Mount Kozara. Partisans and officers who were killed, went missing or died.',
  },
  '2-vojvodjanska-brigada': {
    name: '2nd Vojvodina Assault Brigade',
    description: 'Formed on 20 April 1943 on Mount Majevica. Partisans and officers from its formation to the end of the war.',
  },
  '8-krajiska-brigada': {
    name: '8th Krajina Assault Brigade',
    description: 'Formed on 28 December 1942 in Cazin. Partisans who were killed or died in the war.',
  },
  '6-krajiska-brigada': {
    name: '6th Krajina Assault Brigade',
    description: 'Formed on 14 October 1942 from units of the 1st Krajina Detachment. Partisans and officers who were killed or died, the brigade’s officers of 1942–1943, and Partisans who survived the war.',
  },
  '4-krajiska-brigada': {
    name: '4th Krajina Assault Brigade',
    description:
      'Formed on 9 September 1942 in Tičevo near Bosansko Grahovo. Partisans and officers who were killed, died or went missing.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3rd Krajina Proletarian Assault Brigade',
    description: 'Formed on 22 August 1942 in Kamenica near Drvar. Partisans of the brigade from its formation to the end of the war.',
  },
  '17-slavonska-brigada': {
    name: '17th Slavonian Assault Brigade',
    description: 'Formed on 30 December 1942 near Voćin. The fallen and the survivors, by municipality.',
  },
  '25-srpska-divizija': {
    name: '25th Serbian Assault Division',
    description:
      'Formed on 21 June 1944 near Jošanica in Pusta Reka. Fallen Partisans and officers of the 16th, 18th and 19th Serbian Brigades.',
  },
  '1-sumadijska-brigada': {
    name: '1st Šumadija Brigade',
    description: 'Formed on 5 October 1943. Fallen Partisans and officers, and Partisans who survived the war.',
  },
  '18-slavonska-brigada': {
    name: '18th Slavonian Assault Brigade',
    description: 'Formed on 11 February 1943 in Mijača near Pakrac. Partisans who were killed, who died and who survived.',
  },
  '4-banijska-brigada': {
    name: '4th Banija Brigade',
    description: 'Formed on 30 June 1943 in Obijaj, Banija. A brigade of the 7th Division. The officers of its staffs, and the members of the brigade.',
  },
  '4-srpska-brigada': {
    name: '4th Serbian Assault Brigade',
    description:
      'Formed on 20 November 1943 in Buci near Kruševac. Members of the brigade, among them foreigners and Partisans whose names were never established.',
  },
  '7-vojvodjanska-brigada': {
    name: '7th Vojvodina Assault Brigade',
    description:
      'Formed on 2 July 1944 at the Mušicki farmstead near Batrovci. Survivors, the fallen and Partisans who died after the war, and members of the 4th (Russian) Battalion.',
  },
  '19-bircanska-brigada': {
    name: '19th Birač Brigade',
    description: 'Formed on 24 October 1943 in Vlasenica. Members of the brigade.',
  },
  '2-krajiska-brigada': {
    name: '2nd Krajina Assault Brigade',
    description: 'Formed on 2 August 1942. Partisans and officers who were killed or died.',
  },
  'tuzlanski-odred': {
    name: 'Tuzla Partisan Detachment',
    description: 'Formed on 24 October 1943 in Tuzla. Members of the detachment, many with a photograph.',
  },
  'uzicki-odred': {
    name: 'Užice Partisan Detachment "Dimitrije Tucović"',
    description: 'Formed on 7 July 1941 in Užice. Members of the detachment killed in the war of 1941–1945.',
  },
  '14-srpska-brigada': {
    name: '14th Serbian Assault Brigade',
    description:
      'Formed on 17 June 1944 in Ribare near Đunis. Fallen Partisans and officers of the Niš Detachment and the 14th Serbian Brigade.',
  },
  '7-crnogorska-brigada': {
    name: '7th Montenegrin Youth Brigade "Budo Tomović"',
    description: 'Formed on 30 December 1943 in Kolašin. The brigade’s fallen.',
  },
  '17-majevicka-brigada': {
    name: '17th Majevica Brigade',
    description:
      'Formed on 10 October 1943 near Tuzla. Partisans of the 3rd Majevica Detachment and the 17th Majevica Brigade who were killed or died.',
  },
  '25-brodska-brigada': {
    name: '25th Brod Brigade',
    description:
      'Formed on 1 October 1943 near Slavonska Orahovica. The fallen, and every Partisan and officer in the brigade in October 1943.',
  },
  '25-srpska-brigada': {
    name: '25th Serbian Brigade',
    description:
      'Formed on 1 September 1944 in Strelac near Pirot. Partisans and officers who were killed or wounded, from the brigade’s wartime rolls.',
  },
  '21-tuzlanska-brigada': {
    name: '21st Tuzla Brigade',
    description: 'Formed on 19 September 1944 in Pašabunar near Tuzla. Fallen Partisans and officers.',
  },
  '53-srednjobosanska-divizija': {
    name: '53rd Central Bosnian Division',
    description:
      'Formed on 23 July 1944 in central Bosnia. Partisans of the 14th, 18th and 19th Brigades and of the Prnjavor and Motajica Detachments who were killed, captured or went missing.',
  },
  '21-slavonska-brigada': {
    name: '21st Slavonian Brigade',
    description:
      'Formed on 17 May 1943 in Orljavac near Slavonska Požega. Partisans and officers who were killed, died or went missing.',
  },
  '32-zagorska-divizija': {
    name: '32nd Zagorje Division',
    description:
      'Formed on 12 December 1943 on Kalnik. Members of the division and of the Western Group of Detachments, and of the division’s staff and brigades, with details of each, and its command.',
  },
  '1-dalmatinska-brigada': {
    name: '1st Dalmatian Proletarian Brigade',
    description:
      'Formed on 6 September 1942 in the village of Dobro near Livno. Partisans killed in the war, Partisans at the Sutjeska, women fighters of 1944–1945, company commanders and commissars, and the command of the brigade and its battalions.',
  },
  '16-slavonska-omladinska-brigada': {
    name: '16th Slavonian Youth Brigade "Jože Vlahović"',
    description:
      'Formed on 29 December 1942 in Gornji Borki near Daruvar. Fallen Partisans and officers, those killed in Pokuplje and on Žumberak, and the brigade’s leaders from its formation to the end of the war.',
  },
  '8-crnogorska-brigada': {
    name: '8th Montenegrin Brigade',
    description: 'Formed on 25 February 1944 in Berane. Fallen Partisans and officers, and a further list of the fallen from Ub.',
  },
  'druga-proleterska-brigada': {
    name: '2nd Proletarian Brigade',
    description:
      'Formed on 1 March 1942 in Čajniče. Partisans who were killed, died or went missing, by place and day of death, from the Sutjeska to the Syrmian Front.',
  },
  '4-proleterska-brigada': {
    name: '4th Proletarian Montenegrin Brigade',
    description:
      'Formed on 10 June 1942. Partisans on the day it was formed and in the Battle of the Sutjeska, the brigade’s officers and People’s Heroes, and Partisans and officers killed from 1942 to 1945.',
  },
  '5-proleterska-brigada': {
    name: '5th Proletarian Montenegrin Brigade',
    description:
      'Formed on 12 June 1942 in Smriječno near Šavnik. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943, and the brigade’s women Partisans.',
  },
  '6-istocnobosanska-brigada': {
    name: '6th East Bosnian Proletarian Brigade',
    description:
      'Formed on 2 August 1942 in Šekovići near Vlasenica. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '10-hercegovacka-brigada': {
    name: '10th Herzegovina Brigade',
    description:
      'Formed on 10 August 1942 near Kupres. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '7-banijska-brigada': {
    name: '7th Banija Brigade "Vasilj Gaćeša"',
    description:
      'Formed on 2 September 1942. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '8-banijska-brigada': {
    name: '8th Banija Brigade',
    description:
      'Formed on 7 September 1942 in Obljaj near Glina. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943, the brigade’s fallen and dead, and its command.',
  },
  '3-dalmatinska-brigada': {
    name: '3rd Dalmatian Brigade',
    description:
      'Formed on 12 November 1942 in Vrba near Sinj. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '9-dalmatinska-divizija': {
    name: '9th Dalmatian Division',
    description:
      'Formed on 11 February 1943 from the 3rd, 4th and 5th Dalmatian Brigades, disbanded that April. The division’s killed and missing, February to April 1943.',
  },
  '16-banijska-brigada': {
    name: '16th Banija Brigade',
    description:
      'Formed on 26 December 1942 in Klasnić. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943, and Partisans and officers killed up to the end of June 1943.',
  },
  '7-krajiska-brigada': {
    name: '7th Krajina Brigade',
    description:
      'Formed on 27 December 1942 in Orahovljani near Ključ. Partisans and officers who survived or were killed, from its formation to the end of the war.',
  },
  '15-majevicka-brigada': {
    name: '15th Majevica Brigade',
    description:
      'Formed on 11 April 1943. Partisans of the brigade, then the 1st Majevica, in the Battle of the Sutjeska, May and June 1943.',
  },
  '12-dalmatinska-brigada': {
    name: '12th Dalmatian (1st Island) Brigade',
    description:
      'Formed on 15 September 1943 on the islands of Brač, Hvar, Vis and Šolta. Partisans and officers who were killed, by the battle in which they fell, and the officers of the brigade and battalion staffs.',
  },
  '3-makedonska-brigada': {
    name: '3rd Macedonian Brigade',
    description:
      'Formed on 26 February 1944 in the village of Žegljane near Kumanovo. The fallen.',
  },
  '18-hrvatska-brigada': {
    name: '18th Croatian East Bosnian Brigade',
    description:
      'Formed on 10 October 1943 near Tuzla and proclaimed on 17 October in Husino. Members and officers of the brigade.',
  },
  '11-dalmatinska-brigada': {
    name: '11th Dalmatian Brigade',
    description:
      'Formed on 2 October 1943 on Biokovo. Partisans who were killed, went missing or survived, and the officers of its staffs and companies.',
  },
  '12-krajiska-brigada': {
    name: '12th Krajina Brigade',
    description:
      'Formed on 19 February 1943 in Drinić. Partisans and officers who were killed or survived.',
  },
  '17-srpska-brigada': {
    name: '17th Serbian Brigade',
    description:
      'Formed on 2 June 1944 at Mehane near Kuršumlija. Partisans who survived or were killed.',
  },
  '14-srednjobosanska-brigada': {
    name: '14th Central Bosnian Brigade',
    description:
      'Formed on 17 October 1943 on Cer near Prnjavor. Partisans who were killed, died or went missing, and those who survived the war.',
  },
  '3-vojvodjanska-brigada': {
    name: '3rd Vojvodina Brigade',
    description:
      'Formed on 15 May 1943 in Srem. Partisans and officers who were killed, those whose fate remains unknown, and the survivors.',
  },
  'kalnicki-odred': {
    name: 'Kalnik Partisan Detachment',
    description:
      'Formed on 10 October 1942 at Bijela near Daruvar. Members of the detachment, those killed and the survivors, and the leaders of the detachment and its units.',
  },
  'posavsko-trebavski-odred': {
    name: 'Posavina-Trebava Partisan Detachment',
    description:
      'Formed on 4 February 1944 near Gradačac from the Posavina and Trebava detachments. Members of the detachment.',
  },
  '8-kordunaska-divizija': {
    name: '8th Kordun Division',
    description:
      'Formed on 22 November 1942 at Crevarska Strana on Petrova Gora. The staffs of the division, its brigades and battalions, and its Partisans who were killed.',
  },
  'cankarjeva-brigada': {
    name: 'Cankar Brigade',
    description:
      'Formed on 28 September 1942 near Lapinje in the Kočevje region. The staffs of the brigade and its battalions, and its Partisans who were killed and those who survived.',
  },
  'gubceva-brigada': {
    name: 'Gubec Brigade',
    description:
      'Formed on 4 September 1942 near Trebelno above Mokronog. The staffs of the brigade and its battalions, and its Partisans who were killed and those who survived.',
  },
  'dvanajsta-brigada': {
    name: '12th Slovene Brigade',
    description:
      'Formed on 24 September 1943 in Mokronog. The staffs of the brigade and its battalions, and its Partisans who were killed and those who survived.',
  },
  'gradnikova-brigada': {
    name: 'Gradnik Brigade',
    description:
      'Formed in April 1943 on Golobar near Bovec. Partisans who were killed, the brigade’s other members, its staff and its People’s Heroes.',
  },
  'zidanskova-brigada': {
    name: 'Zidanšek Brigade',
    description:
      'Formed on 8 January 1944 near Sveti Primož on Pohorje. The brigade staff, and the members of the brigade, those killed and the survivors.',
  },
  'skofjeloski-odred': {
    name: 'Škofja Loka Detachment',
    description:
      'Formed under an order of 30 July 1944, in the hills around Škofja Loka. The names of the detachment’s members.',
  },
  'istrski-odred': {
    name: 'Istrian Detachment',
    description:
      'Formed on 7 October 1943 in the Brkini hills. The staffs of the detachment, its battalions and companies, its Partisans who were killed, and its other members.',
  },
  'zapadnodolenjski-odred': {
    name: 'West Lower Carniola Detachment',
    description:
      'Formed at the end of June 1942 in Lower Carniola. Partisans who were killed, and the detachment’s other members.',
  },
  'braciceva-brigada': {
    name: 'Bračič Brigade',
    description:
      'Formed on 23 September 1943 at Knežja Njiva in the Loška dolina. Partisans who were killed and those who survived.',
  },
  'tomsiceva-brigada': {
    name: 'Tomšič Brigade',
    description:
      'Formed on 16 July 1942 at Cesta in the Kočevje region. Partisans of the units it grew from, and the brigade’s members to the end of the war.',
  },
  '1-slovenska-artilerijska-brigada': {
    name: '1st Slovene Artillery Brigade',
    description:
      'Formed on 6 May 1944 at Lašče near Dvor. The brigade’s officers and gunners, and its fallen.',
  },
  'artilerija-9-korpusa': {
    name: '9th Corps Artillery',
    description:
      'Formed on 14 June 1944 at Gornji Lokovec. The artillery’s members and its fallen.',
  },
  '19-srpska-brigada': {
    name: '19th Serbian Brigade',
    description:
      'Formed on 12 June 1944 in Gornja Jošanica. Partisans who were killed, went missing or died, those who survived the war, and the staffs of the brigade and its battalions.',
  },
  '22-srpska-brigada': {
    name: '22nd Serbian (Kosmaj) Brigade',
    description:
      'Formed on 12 September 1944 at Brdnjak near Drugovac. Partisans and officers who were killed or survived.',
  },
  '12-vojvodjanska-brigada': {
    name: '12th Vojvodina Brigade',
    description:
      'Formed on 8 October 1944 at Vojlovica near Pančevo. The brigade’s members, by the place they lived in, and its fallen.',
  },
  '4-vojvodjanska-brigada': {
    name: '4th Vojvodina Brigade',
    description:
      'Formed on 7 October 1943 in the Varadin forest near Višnjićevo. The brigade’s first members and its fallen.',
  },
  '1-kosovsko-metohijska-brigada': {
    name: '1st Kosovo-Metohija Brigade',
    description:
      'Formed on 24 June 1944 in the village of Zbaždi in western Macedonia. The brigade’s members, its fallen and wounded.',
  },
  '8-vojvodjanska-brigada': {
    name: '8th Vojvodina Brigade',
    description:
      'Formed on 12 September 1944 at the Jabuka clearing on Fruška Gora. Partisans and officers who were killed or went missing.',
  },
  '19-sjevernodalmatinska-divizija': {
    name: '19th North Dalmatian Division',
    description:
      'Formed on 11 October 1943 at Biovičino Selo in Bukovica. The commanders and commissars of the division and its brigades, its People’s Heroes, and its Partisans who were killed or died.',
  },
  '21-srpska-brigada': {
    name: '21st Serbian Brigade',
    description:
      'Formed on 10 May 1944 at Trebež near Darosava. Partisans who were killed or survived, and others who fought in the brigade.',
  },
  '14-hercegovacka-brigada': {
    name: '14th Herzegovina Brigade',
    description:
      'Formed on 4 September 1944 near Ljubinje as a youth brigade. Everyone who served in it, its fallen, and its command.',
  },
  '5-vojvodjanska-brigada': {
    name: '5th Vojvodina Brigade',
    description:
      'Formed on 15 November 1943 at Obršine on Mount Majevica. The brigade’s soldiers and officers.',
  },
  '6-vojvodjanska-brigada': {
    name: '6th Vojvodina Brigade',
    description:
      'Formed on 17 January 1944 at Jabučje near Sremska Rača. The brigade’s fallen soldiers and officers, and the members of its staffs and company commands.',
  },
  '13-vojvodjanska-brigada': {
    name: '13th Vojvodina Brigade',
    description:
      'Formed on 14 October 1944 at Kikinda. The brigade’s soldiers, by name.',
  },
  '7-srpska-brigada': {
    name: '7th Serbian Brigade',
    description:
      'Formed on 4 February 1944 at Jabukovik near Crna Trava, as the 5th South Morava Brigade. Its soldiers in May 1944, and those killed, dead or missing.',
  },
  '15-srpska-brigada': {
    name: '15th Serbian Brigade',
    description:
      'Formed on 2 June 1944 at Retkocer, Upper Jablanica. The brigade’s soldiers and officers, its fallen and its wounded.',
  },
  '8-srpska-brigada': {
    name: '8th Serbian Brigade',
    description:
      'Formed on 8 March 1944 at Trgovište, as the 6th South Morava Brigade. The brigade’s fallen.',
  },
  '10-srpska-brigada': {
    name: '10th Serbian Brigade',
    description:
      'Formed on 8 May 1944 at Jabukovik near Crna Trava. The brigade’s soldiers and officers who were killed, died or went missing.',
  },
  '23-srpska-brigada': {
    name: '23rd Serbian Brigade',
    description:
      'Formed on 2 September 1944 at Šuman Topla near Knjaževac. The brigade’s soldiers and officers who were killed or died.',
  },
  '12-srpska-brigada': {
    name: '12th Serbian Brigade',
    description:
      'Formed on 22 May 1944 on Mount Ostrozub, south of Bistrica. The brigade’s soldiers and officers who were killed or died.',
  },
  '20-srpska-brigada': {
    name: '20th Serbian Brigade',
    description:
      'Formed on 19 August 1944 above the village of Bučje near Knjaževac. The brigade’s soldiers and officers who were killed or died.',
  },
  '1-konjicka-brigada': {
    name: '1st Cavalry Brigade',
    description:
      'Formed on 15 September 1944 at Slavkovica near Ljig. The brigade’s wartime list of officers and men, and its fallen.',
  },
  'toplicki-odred': {
    name: 'Toplica Partisan Detachment',
    description:
      'Formed on 3 August 1941 at Ajdanovac near Prokuplje. Its men on the day it was formed, its dead, and its People’s Heroes.',
  },
  'karlovacka-brigada': {
    name: 'Karlovac Assault Brigade',
    description:
      'Formed on 5 March 1944 at Hrašće near Ozalj. Its men on the day it was formed, its fallen, and its command.',
  },
  '14-primorsko-goranska': {
    name: '14th Primorje–Gorski Kotar Brigade',
    description:
      'Formed on 26 November 1942 at Drežnica. The brigade’s fallen.',
  },
  '22-divizija': {
    name: '22nd Division',
    description:
      'Formed in May 1944 on the right bank of the South Morava. The fallen of its 8th, 10th and 12th Serbian Brigades.',
  },
  '34-divizija': {
    name: '34th Division',
    description:
      'Formed on 30 January 1944 in Žumberak and Pokuplje. The fallen soldiers and officers of the division and its brigades, and its command.',
  },
  '4-sandzacka-brigada': {
    name: '4th Sandžak Brigade',
    description:
      'Formed on 1 December 1943 in Pljevlja. The brigade’s fallen and wounded.',
  },
  '3-primorsko-goranska': {
    name: '3rd Primorje–Gorski Kotar Brigade',
    description:
      'Formed on 15 September 1943 at Škrljevo in the Croatian Littoral. The staffs of the brigade and its battalions, its officers and company medics, and its fallen.',
  },
  '13-hercegovacka-brigada': {
    name: '13th Herzegovina Brigade',
    description:
      'Formed on 14 May 1944 in Herzegovina. Its fallen soldiers and officers, all who fought in it, and the officers of its staffs and companies.',
  },
  '12-hercegovacka-brigada': {
    name: '12th Herzegovina Brigade',
    description:
      'Formed on 16 November 1943 in Herzegovina, from battalion groups of the 10th Herzegovina. The brigade’s fallen soldiers and officers.',
  },
  '1-bokeljska-brigada': {
    name: '1st Boka Brigade',
    description:
      'Formed on 5 October 1944 at Konjsko near Trebinje. Every fighter and officer of the brigade by unit, and its fallen, dead and missing.',
  },
  '6-dalmatinska-brigada': {
    name: '6th Dalmatian Brigade',
    description:
      'Formed on 8 October 1943 at Ervenik, as the 2nd Brigade of the 19th Division. The staffs of the brigade and its battalions, and the brigade’s fallen.',
  },
  'osjecka-brigada': {
    name: 'Osijek Assault Brigade',
    description:
      'Formed on 1 March 1944 near Slobodna Vlast, close to Đakovo. The brigade’s fallen and dead, and its survivors, by municipality, and its officers.',
  },
  '4-brigada-slavonije': {
    name: '4th Slavonia Brigade',
    description:
      'Formed on 28 September 1944 at Podravska Slatina, as the 4th Brigade of the 12th Division, called the 2nd Brod Brigade. The brigade’s fallen and wounded, and its leaders.',
  },
  '12-slavonska-brigada': {
    name: '12th Proletarian Slavonian Brigade',
    description:
      'Formed on 11 October 1942 at Budići near Pakrac as the 1st Slavonian Brigade, Proletarian from 26 October 1944. The brigade’s women fighters: the fallen, those who died later, and the survivors.',
  },
  'zagrebacki-odred': {
    name: 'Zagreb Partisan Detachment',
    description:
      'Formed on 13 September 1943 on Zagrebačka Gora. The roll of its fighters: village, municipality and fate.',
  },
  'mosorski-odred': {
    name: 'Mosor Partisan Detachment',
    description:
      'Formed on 21 February 1942 on Mosor, again on 11 October 1943, disbanded on 10 November 1944. All its fighters, 1942–1944, with short lives, and its leaders.',
  },
  'turopoljsko-posavski-odred': {
    name: 'Turopolje-Posavina Partisan Detachment',
    description:
      'Formed on 8 August 1943 near Čička Poljana. Its fighters killed in action, and those shot by the enemy or who died during the war.',
  },
  'zascitni-bataljon-vpv': {
    name: 'Protection Battalion of the Slovene Partisan Leadership',
    description:
      'Formed in April 1944 from the companies that had guarded the bases and members of the Slovene political leadership since 1942. Its members who survived and those who fell.',
  },
  '1-zagorska-brigada': {
    name: '1st Zagorje Brigade',
    description:
      'Formed on 8 May 1944 at Selnica, below Ivančica. The brigade’s fallen fighters and officers.',
  },
  '6-crnogorska-brigada': {
    name: '6th Montenegrin Brigade',
    description:
      'Formed on 14 November 1943 at Drijenak near Kolašin. The brigade’s fallen and dead, Partisans and officers.',
  },
  '11-krajiska-brigada': {
    name: '11th Krajina (Kozara) Brigade',
    description:
      'Formed on 23 August 1943 on Kozara, from the Kozara Partisan Detachment. The brigade’s fallen, by municipality, and a list of its women fighters.',
  },
  '3-banijska-brigada': {
    name: '3rd Banija Brigade',
    description:
      'Formed on 1 May 1943 at Komogovina as the 4th Banija Brigade; from September 1943 the 3rd brigade of the 7th Banija Division. The brigade’s officers and fighters.',
  },
  'macvanski-odred': {
    name: 'Mačva (Podrinje) Partisan Detachment',
    description:
      'Formed on 16 July 1941 at Bubanja near Glušci in Mačva; from August the Podrinje Partisan Detachment. Its fighters from July 1941 to March 1942, by the place they came from.',
  },
  'posavski-odred': {
    name: 'Posavina Partisan Detachment',
    description:
      'Formed on 31 July 1941 by order of the Serbian Main Staff, from two Posavina companies and the Tamnava company. Its fighters of 1941, by battalion.',
  },
  '51-divizija': {
    name: '51st Vojvodina Division',
    description:
      'Formed on 31 October 1944 in Novi Sad, from the 7th, 8th and 12th Vojvodina Brigades. The division’s fallen from its formation to the end of the war, May 1945, and its missing in the Battle of Batina.',
  },
  'vrhovni-stab': {
    name: 'Supreme Headquarters of the NOV and POJ',
    description:
      'Formed on 27 June 1941 in Belgrade, as the General Staff of the Partisan Detachments of Yugoslavia. Members of the Supreme Headquarters, its services, the Escort Battalion and the British military mission in the Battle of the Sutjeska, May and June 1943, and the workers of its military workshop in Grmeč, 1942–1943.',
  },
  '1-proleterska-divizija': {
    name: '1st Proletarian Division',
    description:
      'Formed on 1 November 1942 in Bosanski Petrovac. The division staff, its services and escort units in the Battle of the Sutjeska, May and June 1943.',
  },
  '2-proleterska-divizija': {
    name: '2nd Proletarian Division',
    description:
      'Formed on 1 November 1942 at Tičevo. The division staff, its services and escort units in the Battle of the Sutjeska, May and June 1943.',
  },
  '3-udarna-divizija': {
    name: '3rd Assault Division',
    description:
      'Formed on 1 November 1942 at Tičevo. The division staff, its services and escort units in the Battle of the Sutjeska, May and June 1943.',
  },
  '7-banijska-divizija': {
    name: '7th Banija Division',
    description:
      'Formed on 22 November 1942. The division staff, its services and escort units in the Battle of the Sutjeska, May and June 1943.',
  },
  'centralna-bolnica': {
    name: 'Central Hospital',
    description:
      'Formed in November 1941 in western Serbia. The hospital’s staff, and wounded whose own unit could not be established, in the Battle of the Sutjeska, May and June 1943.',
  },
  '3-licka-brigada': {
    name: '3rd Lika Proletarian Brigade',
    description:
      'Formed on 9 September 1942 at Mogorić near Gospić as the 9th Croatian Brigade. Its fallen, dead and missing fighters, and its People’s Heroes.',
  },
  'pozarevacki-odred': {
    name: 'Požarevac Partisan Detachment',
    description:
      'Formed in August 1941 in the Požarevac district. All its fighters from 1941 to October 1944, when it joined the Yugoslav Army.',
  },
  '1-proleterski-bataljon-hrvatske': {
    name: '1st Proletarian Battalion of Croatia',
    description:
      'Formed on 7 May 1942 in Korenica. Its fighters, until it joined the 13th Proletarian Brigade “Rade Končar”.',
  },
  'pionirska-ceta-divoselo': {
    name: 'First Armed Pioneer Partisan Company',
    description:
      'Formed on 7 November 1942 in Divoselo near Gospić. Its fighters, children from Divoselo and the villages around it.',
  },
  '4-pomorski-sektor': {
    name: '4th Naval Coastal Sector',
    description: 'Formed on 30 October 1943 at Hvar, the Partisan Navy’s sector for central Dalmatia and its islands. Every fighter of the sector and where each came from, and for the fallen and dead where they fell, and the sector’s staff.',
  },
  'viski-bataljon': {
    name: 'Vis Volunteer Battalion',
    description: 'Formed in January 1944 on Vis to defend the island and disbanded at the end of April 1944. Its men by company and platoon at the end of January 1944.',
  },
  'kokrski-odred': {
    name: 'Kokra Detachment',
    description: 'Formed on 18 June 1942 at Kališče under Storžič, and again on 27 August 1944 at Draga near Begunje. The first detachment’s fighters with their stories, and the second’s roll by staff, service and company.',
  },
  'cankarjev-bataljon': {
    name: 'Cankar Battalion',
    description: 'Formed on 5 August 1941 on Vodiška planina in the Jelovica hills; in January 1942 the battle of Dražgoše. The battalion’s fallen and the survivors of Dražgoše.',
  },
  'novosadski-odred': {
    name: 'Novi Sad Partisan Detachment',
    description: 'Formed in 1941 and again on 28 August 1944 at Palenkaš farm near Bački Petrovac. Its members in 1941 and in 1944.',
  },
  'deveta-brigada': {
    name: 'Ninth (Kočevje) Brigade',
    description: 'Formed on 14 September 1943 from the battalions of the Western Dolenjska Detachment, in the 18th Division. The staffs of the brigade and its battalions; the brigade’s fighters: year and place of birth, and for the fallen where they fell.',
  },
  '4-prekomorska-brigada': {
    name: '4th Overseas Brigade',
    description: 'Formed on 7 September 1944 in Italy, at the Yugoslav army’s base in Bari: loading and shipping Allied aid. The fallen and dead, and the officers.',
  },
  '9-srpska-brigada': {
    name: '9th Serbian Brigade',
    description: 'Formed on 11 March 1944 at Rečica. The fighters in its line on the day it was formed, the officers of the brigade, its battalions and companies, and its nurses and women fighters.',
  },
  'kozjanski-odred': {
    name: 'Kozjansko Detachment',
    description: 'Formed on 27 April 1944 in Kozjansko, from the Kozjansko Battalion. Every man and woman of the detachment until it was disbanded: birth, joining the partisans, trade and fate.',
  },
  'proleterski-bataljon-bk': {
    name: 'Proletarian Battalion of the Bosnian Krajina',
    description: 'Formed on 25 March 1942 at Čelinac, from the Kozara and Grmeč proletarian companies and the Drvar proletarian platoon. Each fighter’s biography, beside his photograph.',
  },
  '1-tenkovski-bataljon': {
    name: '1st Tank Battalion',
    description: 'Formed on 21 September 1943 in Lika, from the 1st Corps’ tank company. The men of the tank platoon, company and battalion of the Croatian General Staff.',
  },
  '3-diverzantski-odred': {
    name: '3rd Sabotage Detachment',
    description: 'Formed on 7 September 1944 at Pobjenik near Čazma, from the 3rd Sabotage Battalion. Every fighter and officer of the sabotage group, company, battalion and detachment.',
  },
  '1-2-prekomorska-brigada': {
    name: '1st and 2nd Overseas Brigades',
    description: 'Formed in October 1943 in Italy, in the Carbonara and Gravina camps, from Slovenes and Istrians out of the Italian army, prisons and internment. The fallen and the officers.',
  },
  '5-prekomorska-brigada': {
    name: '5th Overseas Brigade',
    description: 'Formed on 23 December 1944 in Split, from Slovenes who came over from the Allied armies and from captivity. The fallen and the officers.',
  },
  'sercerjeva-brigada': {
    name: 'Šercer Brigade',
    description: 'Formed on 6 October 1942 on Mokrc. The volunteers to the end of February 1943, and the fallen to the end of 1943 by the place and day they fell.',
  },
  'kosovelova-brigada': {
    name: 'Kosovel Brigade',
    description: 'Formed on 23 September 1943 on the Karst. The fallen, the missing and those who died of wounds, and the officers of the brigade and its battalions.',
  },
  'eskadrile-novj': {
    name: '1st and 2nd Squadrons of the Yugoslav Army (RAF 352 and 351)',
    description: 'The first formed on 22 April 1944 at Benina airfield in Libya, the second on 1 July 1944. The pilots, mechanics and other men of both squadrons.',
  },
  '42-vazduhoplovna-divizija': {
    name: '42nd Air Division',
    description: 'Formed on 29 December 1944 in Zemun. The division’s men by regiment and workshop: rank and duty.',
  },
  '18-srpska-brigada': {
    name: '18th Serbian Brigade',
    description: 'Formed in June 1944 below Mount Veliki Jastrebac. Every fighter and officer of the brigade, with year and place of birth and how they fell or were wounded.',
  },
  '5-srpska-brigada': {
    name: '5th Serbian Brigade',
    description: 'Formed on 14 January 1944 at Velika Plana near Prokuplje as the 3rd South Morava Brigade. The brigade’s fallen and dead fighters and officers.',
  },
  'cacanski-odred': {
    name: 'Čačak Partisan Detachment “Dr Dragiša Mišović”',
    description: 'Formed on 6 July 1941 at Kulinovci near Čačak. The detachment’s fallen, by district and village.',
  },
  'mostarski-bataljon': {
    name: 'Mostar Battalion',
    description: 'Formed in September 1941 as the Konjic Battalion, named the Mostar Battalion on 21 June 1942. Its fighters up to May 1944, each with a short biography.',
  },
  '13-krajiska-brigada': {
    name: '13th Krajina Brigade',
    description: 'Formed on 23 August 1943 from the Ribnik Partisan Detachment. The brigade’s fighters in August and September 1943, and its Communist Party members in May 1945.',
  },
  '1-krajiska-brigada': {
    name: '1st Krajina Proletarian Assault Brigade',
    description: 'Formed on 21 May 1942 at Lamovita near Prijedor. The brigade’s fallen, dead and missing fighters.',
  },
  'ostali-borci': {
    name: 'Fighters of other units',
    description:
      'Fighters from memorial books, village histories and the collections of People’s Heroes whose unit is not on the site yet.',
  },
  'ostali-borci-slovenija': {
    name: 'Fighters of other units – Slovenia',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Slovenia, whose unit is not on the site yet.',
  },
  'ostali-borci-hrvatska': {
    name: 'Fighters of other units – Croatia',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Croatia, whose unit is not on the site yet.',
  },
  'ostali-borci-bih': {
    name: 'Fighters of other units – Bosnia and Herzegovina',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Bosnia and Herzegovina, whose unit is not on the site yet.',
  },
  'ostali-borci-crna-gora': {
    name: 'Fighters of other units – Montenegro',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Montenegro, whose unit is not on the site yet.',
  },
  'ostali-borci-makedonija': {
    name: 'Fighters of other units – Macedonia',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Macedonia, whose unit is not on the site yet.',
  },
  'ostali-borci-srbija': {
    name: 'Fighters of other units – Serbia',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Serbia without its provinces, whose unit is not on the site yet.',
  },
  'ostali-borci-kosovo': {
    name: 'Fighters of other units – Kosovo and Metohija',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Kosovo and Metohija, whose unit is not on the site yet.',
  },
  'ostali-borci-vojvodina': {
    name: 'Fighters of other units – Vojvodina',
    description:
      'Fighters killed or dead in the war, from the 1964 census of war victims in Vojvodina, whose unit is not on the site yet.',
  },
}

const TEXT: Partial<Record<Lang, Record<string, UnitText>>> = { sl, mk, en }

// Serbo-Croatian in Cyrillic is the Latin text of data/units.ts, letter for letter
function inScript(lang: Lang, text: string): string {
  return lang === 'sr-cyrl' ? toCyrillic(text) : text
}

/** The unit's name in the language, with its quotation marks: Prva liška proletarska brigada »Marko Orešković« */
export function unitName(unit: Unit, lang: Lang): string {
  return inScript(lang, quoteMarks(lang, TEXT[lang]?.[unit.id]?.name ?? unit.name))
}

/** The unit's name without its honorary name: "Prva liška proletarska brigada" */
export function unitShortName(unit: Unit, lang: Lang): string {
  return inScript(lang, (TEXT[lang]?.[unit.id]?.name ?? unit.name).split(/\s+["„]/)[0])
}

export function unitDescription(unit: Unit, lang: Lang): string {
  return inScript(lang, TEXT[lang]?.[unit.id]?.description ?? unit.description)
}

/** Unit ids that lack a text in some language, for a check at build time */
export function missingUnitTexts(ids: string[]): string[] {
  return (Object.entries(TEXT) as [Lang, Record<string, UnitText>][]).flatMap(([lang, texts]) =>
    ids.filter((id) => !texts[id]).map((id) => `${lang}:${id}`))
}
