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
    description: 'Ustanovljena 18. avgusta 1942 v Laudonovem gaju. Padli, umrli in pogrešani borci ter tisti, ki so vojno preživeli.',
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
    description: 'Ustanovljena 3. oktobra 1942. Borci brigade.',
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
    description: 'Ustanovljena 14. oktobra 1942 iz enot Prvega krajiškega odreda. Padli in umrli borci in poveljniki.',
  },
  '4-krajiska-brigada': {
    name: '4. krajiška udarna brigada',
    description: 'Ustanovljena 9. septembra 1942 v Tičevu pri Bosanskem Grahovu. Padli, umrli in pogrešani borci in poveljniki.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3. krajiška proletarska udarna brigada',
    description: 'Ustanovljena 22. avgusta 1942 v Kamenici pri Drvarju. Padli borci.',
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
    description: 'Ustanovljena 30. junija 1943 v Obijaju na Baniji. Brigada 7. divizije. Borci brigade.',
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
      'Ustanovljena 12. decembra 1943 na Kalniku. Borci divizije in Zahodne skupine odredov. V knjigi so samo imena; zvezdica pomeni, da je borec padel, pomišljaj, da je pogrešan.',
  },
  '1-dalmatinska-brigada': {
    name: '1. dalmatinska proletarska brigada',
    description:
      'Ustanovljena 6. septembra 1942 v vasi Dobro pri Livnu. Borci, ki so padli v vojni. Seznam obstaja samo kot besedilo na znaci.org, brez skenirane knjige.',
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
      'Ustanovljena 10. junija 1942. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '5-proleterska-brigada': {
    name: '5. proletarska črnogorska brigada',
    description:
      'Ustanovljena 12. junija 1942 v Smriječnu pri Šavniku. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
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
      'Ustanovljena 7. septembra 1942 v Obljaju pri Glini. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '3-dalmatinska-brigada': {
    name: '3. dalmatinska brigada',
    description:
      'Ustanovljena 12. novembra 1942 v Vrbi pri Sinju. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '16-banijska-brigada': {
    name: '16. banijska brigada',
    description:
      'Ustanovljena 26. decembra 1942 v Klasniću. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '7-krajiska-brigada': {
    name: '7. krajiška brigada',
    description:
      'Ustanovljena 27. decembra 1942 v Orahovljanih pri Ključu. Borci brigade v bitki na Sutjeski, maja in junija 1943.',
  },
  '15-majevicka-brigada': {
    name: '15. majeviška brigada',
    description:
      'Ustanovljena 11. aprila 1943. Borci brigade, tedaj 1. majeviške, v bitki na Sutjeski, maja in junija 1943.',
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
    description: 'Формирана на 18 август 1942 во Лаудонов Гај. Загинати, починати и исчезнати борци, и оние што ја преживеаја војната.',
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
    description: 'Формирана на 3 октомври 1942. Борци на бригадата.',
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
    description: 'Формирана на 14 октомври 1942 од единиците на Првиот краишки одред. Загинати и починати борци и старешини.',
  },
  '4-krajiska-brigada': {
    name: '4-та краишка ударна бригада',
    description: 'Формирана на 9 септември 1942 во Тичево кај Босанско Грахово. Загинати, починати и исчезнати борци и старешини.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3-та краишка пролетерска ударна бригада',
    description: 'Формирана на 22 август 1942 во Каменица кај Дрвар. Загинати борци.',
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
    description: 'Формирана на 30 јуни 1943 во Обијај на Банија. Бригада на 7-та дивизија. Борци на бригадата.',
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
      'Формирана на 12 декември 1943 на Калник. Борци на дивизијата и на Западната група одреди. Во книгата има само имиња; ѕвездичка значи дека борецот загинал, а цртичка дека исчезнал.',
  },
  '1-dalmatinska-brigada': {
    name: '1-ва далматинска пролетерска бригада',
    description:
      'Формирана на 6 септември 1942 во селото Добро кај Ливно. Борци загинати во војната. Списокот постои само како текст на znaci.org, без скенирана книга.',
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
      'Формирана на 10 јуни 1942. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '5-proleterska-brigada': {
    name: '5-та пролетерска црногорска бригада',
    description:
      'Формирана на 12 јуни 1942 во Смријечно кај Шавник. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
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
      'Формирана на 7 септември 1942 во Обљај кај Глина. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '3-dalmatinska-brigada': {
    name: '3-та далматинска бригада',
    description:
      'Формирана на 12 ноември 1942 во Врба кај Сињ. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '16-banijska-brigada': {
    name: '16-та банијска бригада',
    description:
      'Формирана на 26 декември 1942 во Класниќ. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '7-krajiska-brigada': {
    name: '7-ма краишка бригада',
    description:
      'Формирана на 27 декември 1942 во Ораховљани кај Кључ. Борците на бригадата во битката на Сутјеска, мај и јуни 1943.',
  },
  '15-majevicka-brigada': {
    name: '15-та мајевичка бригада',
    description:
      'Формирана на 11 април 1943. Борците на бригадата, тогаш 1-ва мајевичка, во битката на Сутјеска, мај и јуни 1943.',
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
    description: 'Formed on 18 August 1942 in Laudonov Gaj. Partisans who were killed, died or went missing, and those who survived the war.',
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
    description: 'Formed on 3 October 1942. Members of the brigade.',
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
    description: 'Formed on 14 October 1942 from units of the 1st Krajina Detachment. Partisans and officers who were killed or died.',
  },
  '4-krajiska-brigada': {
    name: '4th Krajina Assault Brigade',
    description:
      'Formed on 9 September 1942 in Tičevo near Bosansko Grahovo. Partisans and officers who were killed, died or went missing.',
  },
  '3-krajiska-proleterska-brigada': {
    name: '3rd Krajina Proletarian Assault Brigade',
    description: 'Formed on 22 August 1942 in Kamenica near Drvar. The fallen.',
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
    description: 'Formed on 30 June 1943 in Obijaj, Banija. A brigade of the 7th Division. Members of the brigade.',
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
      'Formed on 12 December 1943 on Kalnik. Members of the division and of the Western Group of Detachments. The book gives names only: an asterisk marks those killed, a dash those missing.',
  },
  '1-dalmatinska-brigada': {
    name: '1st Dalmatian Proletarian Brigade',
    description:
      'Formed on 6 September 1942 in the village of Dobro near Livno. Partisans killed in the war. The roll exists only as text on znaci.org, with no scanned book.',
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
      'Formed on 10 June 1942. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '5-proleterska-brigada': {
    name: '5th Proletarian Montenegrin Brigade',
    description:
      'Formed on 12 June 1942 in Smriječno near Šavnik. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
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
      'Formed on 7 September 1942 in Obljaj near Glina. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '3-dalmatinska-brigada': {
    name: '3rd Dalmatian Brigade',
    description:
      'Formed on 12 November 1942 in Vrba near Sinj. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '16-banijska-brigada': {
    name: '16th Banija Brigade',
    description:
      'Formed on 26 December 1942 in Klasnić. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '7-krajiska-brigada': {
    name: '7th Krajina Brigade',
    description:
      'Formed on 27 December 1942 in Orahovljani near Ključ. Partisans of the brigade in the Battle of the Sutjeska, May and June 1943.',
  },
  '15-majevicka-brigada': {
    name: '15th Majevica Brigade',
    description:
      'Formed on 11 April 1943. Partisans of the brigade, then the 1st Majevica, in the Battle of the Sutjeska, May and June 1943.',
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
