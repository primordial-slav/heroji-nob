import type { Lang } from './config'
import type { PdfSource } from '@/app/data/sources'
import { toCyrillic } from './cyrillic'

// The Izvori page in Slovene, Macedonian and English. A book's title stays as the book prints it (it is a
// citation); what the site says about the book is translated: its description, the part of the title the
// site added after " — " (it names the list in the record's book switch), and author lines that are not
// names ("Grupa autora", "(ur.)"). Every source added to data/sources.ts needs a description here.
// In Cyrillic Serbo-Croatian (sr-cyrl) the description and the site's part of the title are the Latin ones in
// Cyrillic; the title and the author stay as the book prints them.

type Texts = Record<string, string>

const DESCRIPTION: Partial<Record<Lang, Texts>> = {
  sl: {
    'prva-licka-proleterska': 'Monografija, zbirka Ratna prošlost naroda i narodnosti Jugoslavije, knj. 322',
    'prva-proleterska-1': 'Seznam borcev, prvi zvezek (A–I)',
    'prva-proleterska-2': 'Seznam borcev, drugi zvezek (I–O)',
    'prva-proleterska-3': 'Seznam borcev, tretji zvezek (O–Ž)',
    'druga-licka-spisak': 'Seznam padlih, umrlih in pogrešanih borcev in poveljnikov brigade',
    'druga-licka-sjecanja-prezivjeli': 'Seznam preživelih borcev in poveljnikov Druge liške proletarske brigade (iz zbornika spominov)',
    'druga-licka-sjecanja-poginuli':
      'Seznam padlih, umrlih in pogrešanih borcev Druge liške proletarske brigade (iz zbornika spominov); večina je tudi na seznamu Vojnozgodovinskega inštituta',
    'treca-proleterska-brigada': 'Monografija, zbirka Ratna prošlost naših naroda, knj. 144',
    'treca-proleterska-poginuli-knj3':
      'Seznam padlih in umrlih borcev in poveljnikov po letih, 1942–1945 (1.374 imen; v tem izvodu manjkajo strani z začetkom leta 1944)',
    'treca-proleterska-formiranje':
      'Isti seznam kot v monografiji Žarka Vidovića, v cirilici, kot ga je uredilo uredništvo zbornika spominov; po bataljonih in četah',
    'ljubljanska-brigada': 'Monografija Ljubljanske brigade',
    '13-proleterska-spisak': 'Seznam padlih in preživelih borcev (tretji del monografije)',
    '2-dalmatinska-proleterska': 'Seznam borcev 2. dalmatinske proletarske brigade NOVJ',
    '4-splitska-brigada': 'Seznam padlih in preživelih borcev brigade',
    'prva-vojvodjanska': 'Seznam borcev Prve vojvodinske brigade',
    '5-kozaracka': 'Seznam padlih, pogrešanih in umrlih borcev in poveljnikov brigade',
    '2-vojvodjanska': 'Seznam borcev in poveljnikov 2. vojvodinske brigade',
    '8-krajiska': 'Seznam padlih in umrlih v NOB iz 8. krajiške brigade',
    '6-krajiska': 'Seznam padlih in umrlih borcev in poveljnikov brigade, z dopolnilnim seznamom',
    '4-krajiska': 'Seznam padlih, umrlih in pogrešanih borcev in poveljnikov 4. krajiške brigade',
    '3-krajiska-proleterska': 'Seznam padlih borcev Tretje proletarske krajiške brigade z osnovnimi osebnimi podatki',
    '17-slavonska-poginuli': 'Seznam padlih borcev 17. udarne brigade',
    '17-slavonska-prezivjeli': 'Seznam preživelih borcev 17. udarne brigade',
    '25-srpska-divizija': 'Seznam padlih borcev in poveljnikov 25. divizije',
    '1-sumadijska': 'Seznama padlih borcev in poveljnikov ter borcev, ki so vojno preživeli',
    '18-slavonska': 'Seznam padlih in umrlih borcev in poveljnikov 18. udarne brigade ter seznam preživelih borcev',
    '4-banijska': 'Seznam borcev 4. banijske brigade',
    '4-srpska': 'Seznam borcev Četrte srbske udarne brigade',
    '7-vojvodjanska': 'Seznam borcev 7. vojvodinske udarne brigade (preživeli, padli in po vojni umrli)',
    '19-bircanska': 'Seznam borcev 19. birčanske brigade',
    '2-krajiska': 'Seznam padlih in umrlih borcev in poveljnikov 2. krajiške brigade v NOB',
    'tuzlanski-odred': 'Seznam borcev Tuzelskega partizanskega odreda',
    'uzicki-odred': 'Seznam borcev Užiškega partizanskega odreda, ki so padli v narodnoosvobodilni vojni 1941–1945',
    '14-srpska': 'Seznam padlih borcev in poveljnikov odreda in 14. srbske brigade',
    '7-crnogorska-omladinska': 'Seznam padlih borcev 7. črnogorske mladinske brigade',
    '17-majevicka': 'Seznam borcev Tretjega majeviškega partizanskega odreda in 17. majeviške brigade, ki so padli ali umrli v NOB',
    '25-brodska-poginuli': 'Seznam padlih borcev Brodske brigade 28. divizije',
    '25-brodska-sastav': 'Seznam borcev in poveljnikov, ki so bili oktobra 1943 v Brodski brigadi',
    '25-srpska-brigada': 'Seznam padlih in seznam ranjenih borcev in poveljnikov 25. srbske brigade',
    '21-tuzlanska': 'Seznam padlih borcev in poveljnikov 21. tuzelske brigade',
    '53-srednjobosanska-divizija': 'Seznam padlih, ujetih in pogrešanih borcev 53. srednjebosanske divizije',
    '21-slavonska': 'Seznam padlih, umrlih in pogrešanih borcev in poveljnikov 21. slavonske udarne brigade',
    '32-divizija': 'Seznam borcev 32. divizije in Zahodne skupine odredov (padli so označeni z zvezdico, pogrešani s pomišljajem)',
    '1-dalmatinska':
      'Seznam borcev Prve dalmatinske proletarske brigade, ki so padli v narodnoosvobodilni vojni (besedilo na znaci.org, brez skenirane knjige)',
    '16-slavonska-omladinska':
      'Seznam padlih borcev in poveljnikov brigade; seznam padlih v Pokuplju in na Žumberku; vodstvo brigade od ustanovitve do konca vojne (str. 389–428 knjige)',
    '8-crnogorska': 'Seznam padlih tovarišev, borcev in poveljnikov brigade (str. 471–501 knjige) in dopolnilni seznam padlih iz Uba (str. 509–510)',
    'druga-proleterska':
      'Padli, umrli in pogrešani borci brigade, po kraju in dnevu smrti: Sutjeska, vzhodna Bosna, Pljevlja in Prijepolje, zahodna Srbija, sremska fronta (str. 274–278 knjige)',
    'borci-sutjeske-4-proleterska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-5-proleterska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-6-istocnobosanska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-10-hercegovacka':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-7-banijska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-8-banijska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-3-dalmatinska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-16-banijska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-7-krajiska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-15-majevicka':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-prva-proleterska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-druga-proleterska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-treca-proleterska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-3-krajiska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-1-dalmatinska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-2-dalmatinska':
      'Imenski seznam borcev s Sutjeske: vsi borci brigade v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    '12-dalmatinska':
      'Seznam padlih borcev in poveljnikov brigade, po bojih, od Sućurja 22. septembra 1943 do Ilirske Bistrice 6. maja 1945 (str. 353–366 knjige)',
    '3-makedonska':
      'Seznam padlih borcev brigade: od kod so bili, leto rojstva, kje in kdaj so padli (str. 359–368 knjige)',
    '3-krajiska-spisak-boraca':
      'Seznam borcev, ki so se v brigadi borili od 22. 8. 1942 do 9. 5. 1945, preživelih in padlih: od kod so bili, poklic, kdaj so vstopili v NOB in v brigado, dolžnost, usoda; z dopolnilom in prilogo (str. 579 in naprej)',
    '6-krajiska-prezivjeli':
      'Seznam borcev brigade, ki so vojno preživeli, samo imena, z naknadnim seznamom (str. 747–762 knjige)',
    '32-divizija-borci':
      'Borci štaba divizije, spremljevalnih enot, brigad Braća Radić, Matija Gubec, Mihovil Pavlek Miškina in I. udarne zagorske ter borci z nepopolnimi podatki: leto in kraj rojstva, narodnost, poklic, vstop v NOV, usoda; borec je naveden v vsaki enoti, v kateri se je boril (str. 431–662 knjige)',
    '18-hrvatska':
      'Seznam borcev brigade, preživelih in padlih: leto in kraj rojstva, narodnost, poklic, vstop v brigado, dolžnost, usoda (str. 582–696 knjige)',
    '11-dalmatinska':
      'Seznam borcev brigade: padli, pogrešani in preživeli (na dan 15. maja 1945): dolžnost, rojstvo, poklic, vstop v NOB, usoda (str. 479–600 knjige)',
    '7-krajiska-spisak':
      'Preživeli in padli borci in poveljniki od ustanovitve brigade decembra 1942 do konca vojne: rojstvo, narodnost, poklic, vstop v NOB, dolžnost, usoda (str. 447 in naprej)',
    '12-krajiska-poginuli':
      'Padli borci in poveljniki brigade: dolžnost, leto in kraj rojstva, kje in kdaj so padli',
    '12-krajiska-prezivjeli':
      'Preživeli borci in poveljniki brigade: leto in kraj rojstva',
    '17-srpska':
      'Seznam borcev brigade, ki so vojno preživeli, in seznam padlih: rojstvo, vstop v brigado, dolžnost, kje in kdaj so padli (str. 317–373 knjige)',
    '14-srednjobosanska':
      'Seznam padlih, umrlih in pogrešanih borcev in poveljnikov brigade ter seznam borcev, ki so vojno preživeli, po občinah (str. 393–458 knjige)',
    '4-proleterska-poginuli':
      'Borci in poveljniki brigade, padli od 1942 do 1945, po letih: rojstvo, poklic, dolžnost, kdaj in kje so padli',
    '3-vojvodjanska':
      'Seznami borcev in poveljnikov brigade: padli, tisti, katerih usoda ni znana, in preživeli (str. 479 in naprej)',
    'kalnicki-odred':
      'Seznam borcev Kalniškega partizanskega odreda, padlih in preživelih (str. 311 in naprej)',
    'posavsko-trebavski-odred':
      'Seznam borcev odreda po občinah, iz katerih so prišli (str. 313 in naprej)',
    '8-kordunaska-divizija':
      'Seznam padlih borcev Osme divizije po priimkih, z brigado, v kateri so bili (str. 806 in naprej)',
    'cankarjeva':
      'Seznam cankarjevcev, ki so preživeli vojno (str. 815 in naprej), in seznam padlih (str. 847 in naprej)',
    'gubceva':
      'Seznam gubčevcev, ki so preživeli vojno (str. 979 in naprej), in seznam padlih (str. 1016 in naprej)',
    'dvanajsta':
      'Seznam padlih borcev brigade in seznam borcev, ki so preživeli vojno, na koncu knjige',
    'gradnikova':
      'Seznam v brigadi padlih borcev in seznam drugih borcev brigade, ki so preživeli vojno ali niso padli v njej (str. 840 in naprej)',
    'zidanskova':
      'Seznam borcev brigade; padli so označeni z letnicama rojstva in padca (str. 731 in naprej)',
    'skofjeloski-odred':
      'Seznam borcev odreda, samo imena, kot so vpisani v ohranjenem arhivu odreda (str. 314 in naprej)',
    'istrski-odred':
      'Seznam borcev odreda (str. 827 in naprej), brez padlih, in seznam padlih s kratkimi podatki (str. 849 in naprej)',
    'zapadnodolenjski-odred':
      'Seznam odredovcev (str. 333 in naprej) in seznam padlih (str. 340 in naprej)',
    'braciceva':
      'Seznam padlih borcev brigade (str. 722 in naprej) in tistih, ki so vojno preživeli (str. 746 in naprej)',
    'tomsiceva-2':
      'Seznam borcev brigade od 16. julija 1942 do 13. julija 1943 (2. knjiga, str. 847 in naprej)',
    'tomsiceva-3':
      'Borci brigade od 16. julija 1942 do 13. julija 1943, ki so bili izpuščeni iz seznama 2. knjige ali so se dodatno prijavili (3. knjiga, str. 647 in naprej)',
    'tomsiceva-4':
      'Seznama borcev brigade od 13. julija 1943 do 1. aprila 1944 in od 1. aprila 1944 do 15. maja 1945 (4. knjiga, str. 576 in naprej)',
    '1-slovenska-artilerijska':
      'Seznam starešin, seznam topničarjev in seznam padlih (str. 388 in naprej)',
    'artilerija-9-korpusa':
      'Seznam borcev artilerije, seznam padlih in poveljniški kader (str. 316 in naprej)',
    '19-srpska':
      'Padli, pogrešani in umrli po enotah ter borci, ki so vojno preživeli: rojstvo, dolžnost, kdaj in kje so padli (str. 411–612)',
    '22-srpska':
      'Padli in preživeli borci in starešine brigade: rojstvo, vstop v brigado, dolžnost, kje so padli (str. 317–399)',
    '12-vojvodjanska':
      'Seznam borcev po krajih, kjer so živeli pred vstopom v brigado, in seznam padlih: od kod so bili, leto rojstva, kje so padli (str. 207–258)',
    '4-vojvodjanska':
      'Seznam pripadnikov brigade na dan 7. oktobra 1943 in seznam padlih in umrlih do 1. 3. 1946: rojstvo, poklic, dolžnost, kje so padli (str. 281–334)',
    '1-kosovsko-metohijska':
      'Seznami borcev: kosovsko-metohijska bataljona, iz katerih je bila brigada ustanovljena, borci, ki so se pridružili leta 1944 iz Porečja in Tetova ter od Junika in Dečanov, padli in ranjeni (str. 351–383)',
    '8-vojvodjanska':
      'Seznam padlih in pogrešanih borcev in voditeljev brigade: rojstvo, kje in kdaj so padli ali izginili (str. 675–722)',
    '19-sjevernodalmatinska':
      'Seznam padlih in umrlih borcev divizije od ustanovitve do konca vojne: od kod so bili, kje in kdaj so padli (str. 253–299)',
    '21-srpska':
      'Padli, preživeli in drugi, ki so se borili v brigadi (Druga šumadijska): starši, rojstvo, dolžnost, vstop v brigado in kje so padli (str. 387–472)',
    '14-hercegovacka':
      'Seznam borcev, ki so šli skozi brigado: leto in kraj rojstva; padli, z enoto in krajem smrti (str. 243–287)',
    '5-vojvodjanska':
      'Seznam borcev in starešin brigade: leto in kraj rojstva, poklic, dolžnost v brigadi, kje so padli ali izginili (str. 429–584)',
    '6-vojvodjanska':
      'Seznam padlih borcev in starešin: leto in kraj rojstva, datum in kraj smrti, kje so pokopani (str. 175–199)',
    '13-vojvodjanska':
      'Seznam pripadnikov brigade: imena, ponekod vzdevek ali kraj; avtor opozarja, da seznam ni popoln (str. 771–793)',
    '7-srpska':
      'Seznam borcev v začetku maja 1944 po vaseh in seznam padlih, umrlih in pogrešanih: rojstvo, vstop v brigado, kje so padli (str. 459–501)',
    '15-srpska':
      'Seznam borcev in starešin brigade, seznam padlih in seznam ranjenih: rojstvo, dolžnost, kdaj in kje so padli ali bili ranjeni (str. 155–173)',
  },
  mk: {
    'prva-licka-proleterska': 'Монографија, библиотека „Ratna prošlost naroda i narodnosti Jugoslavije“, кн. 322',
    'prva-proleterska-1': 'Список на борците, прв том (A–I)',
    'prva-proleterska-2': 'Список на борците, втор том (I–O)',
    'prva-proleterska-3': 'Список на борците, трет том (O–Ž)',
    'druga-licka-spisak': 'Список на загинатите, починатите и исчезнатите борци и старешини на бригадата',
    'druga-licka-sjecanja-prezivjeli': 'Список на преживеаните борци и старешини на Втората личка пролетерска бригада (од зборникот спомени)',
    'druga-licka-sjecanja-poginuli':
      'Список на загинатите, починатите и исчезнатите борци на Втората личка пролетерска бригада (од зборникот спомени); повеќето ги има и на списокот на Воено-историскиот институт',
    'treca-proleterska-brigada': 'Монографија, библиотека „Ratna prošlost naših naroda“, кн. 144',
    'treca-proleterska-poginuli-knj3':
      'Список на загинатите и починатите борци и старешини по години, 1942–1945 (1.374 имиња; во овој примерок недостасуваат страниците со почетокот на 1944 година)',
    'treca-proleterska-formiranje':
      'Истиот список како во монографијата на Жарко Видовиќ, на кирилица, како што го средила редакцијата на зборникот спомени; по баталјони и чети',
    'ljubljanska-brigada': 'Монографија на Љубљанската бригада',
    '13-proleterska-spisak': 'Список на загинатите и преживеаните борци (трет дел од монографијата)',
    '2-dalmatinska-proleterska': 'Список на борците на 2-ра далматинска пролетерска бригада на НОВЈ',
    '4-splitska-brigada': 'Список на загинатите и преживеаните борци на бригадата',
    'prva-vojvodjanska': 'Список на борците на Првата војводинска бригада',
    '5-kozaracka': 'Список на загинатите, исчезнатите и починатите борци и старешини на бригадата',
    '2-vojvodjanska': 'Список на борците и старешините на 2-ра војводинска бригада',
    '8-krajiska': 'Список на загинатите и починатите во НОБ од 8-ма краишка бригада',
    '6-krajiska': 'Список на загинатите и починатите борци и старешини на бригадата, со дополнителен список',
    '4-krajiska': 'Список на загинатите, починатите и исчезнатите борци и старешини на 4-та краишка бригада',
    '3-krajiska-proleterska': 'Список на загинатите борци на Третата пролетерска краишка бригада, со основните лични податоци',
    '17-slavonska-poginuli': 'Список на загинатите борци на 17-та ударна бригада',
    '17-slavonska-prezivjeli': 'Список на преживеаните борци на 17-та ударна бригада',
    '25-srpska-divizija': 'Список на загинатите борци и старешини на 25-та дивизија',
    '1-sumadijska': 'Списоци на загинатите борци и старешини и на борците што ја преживеаја војната',
    '18-slavonska': 'Список на загинатите и починатите борци и старешини на 18-та ударна бригада и список на преживеаните борци',
    '4-banijska': 'Список на борците на 4-та банијска бригада',
    '4-srpska': 'Список на борците на Четвртата српска ударна бригада',
    '7-vojvodjanska': 'Список на борците на 7-ма војводинска ударна бригада (преживеани, загинати и починати по војната)',
    '19-bircanska': 'Список на борците на 19-та бирчанска бригада',
    '2-krajiska': 'Список на загинатите и починатите борци и старешини на 2-ра краишка бригада во НОБ',
    'tuzlanski-odred': 'Список на борците на Тузланскиот партизански одред',
    'uzicki-odred': 'Список на борците на Ужичкиот партизански одред загинати во народноослободителната војна 1941–1945',
    '14-srpska': 'Список на загинатите борци и старешини на одредот и на 14-та српска бригада',
    '7-crnogorska-omladinska': 'Список на загинатите борци на 7-ма црногорска младинска бригада',
    '17-majevicka': 'Список на борците на Третиот мајевички партизански одред и на 17-та мајевичка бригада загинати или починати во НОБ',
    '25-brodska-poginuli': 'Список на загинатите борци на Бродската бригада од 28-ма дивизија',
    '25-brodska-sastav': 'Список на борците и старешините што биле во Бродската бригада во октомври 1943',
    '25-srpska-brigada': 'Список на загинатите и список на ранетите борци и старешини на 25-та српска бригада',
    '21-tuzlanska': 'Список на загинатите борци и старешини на 21-ва тузланска бригада',
    '53-srednjobosanska-divizija': 'Список на загинатите, заробените и исчезнатите борци на 53-та среднобосанска дивизија',
    '21-slavonska': 'Список на загинатите, починатите и исчезнатите борци и старешини на 21-ва славонска ударна бригада',
    '32-divizija': 'Список на борците на 32-ра дивизија и на Западната група одреди (загинатите се означени со ѕвездичка, исчезнатите со цртичка)',
    '1-dalmatinska':
      'Список на борците на Првата далматинска пролетерска бригада загинати во народноослободителната војна (текст на znaci.org, без скенирана книга)',
    '16-slavonska-omladinska':
      'Список на загинатите борци и старешини на бригадата; список на загинатите во Покупје и на Жумберак; раководството на бригадата од формирањето до крајот на војната (стр. 389–428 од книгата)',
    '8-crnogorska': 'Список на паднатите другари, борци и старешини на бригадата (стр. 471–501 од книгата) и дополнителен список на паднатите од Уб (стр. 509–510)',
    'druga-proleterska':
      'Загинати, починати и исчезнати борци на бригадата, по место и ден на загинувањето: Сутјеска, источна Босна, Пљевља и Пријеполе, западна Србија, Сремскиот фронт (стр. 274–278 од книгата)',
    'borci-sutjeske-4-proleterska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-5-proleterska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-6-istocnobosanska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-10-hercegovacka':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-7-banijska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-8-banijska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-3-dalmatinska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-16-banijska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-7-krajiska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-15-majevicka':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-prva-proleterska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-druga-proleterska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-treca-proleterska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-3-krajiska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-1-dalmatinska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-2-dalmatinska':
      'Поименичен список на борците од Сутјеска: сите борци на бригадата во битката, со податоци за секого и што било со него до крајот на војната.',
    '12-dalmatinska':
      'Список на загинатите борци и старешини на бригадата, по борбите, од Суќурај на 22 септември 1943 до Илирска Бистрица на 6 мај 1945 (стр. 353–366 од книгата)',
    '3-makedonska':
      'Список на загинатите борци на бригадата: од каде се, година на раѓање, каде и кога загинале (стр. 359–368 од книгата)',
    '3-krajiska-spisak-boraca':
      'Список на борците што се бореле во бригадата од 22. 8. 1942 до 9. 5. 1945, преживеани и загинати: од каде се, занимање, кога стапиле во НОБ и во бригадата, должност, судбина; со дополнување и прилог (стр. 579 и натаму)',
    '6-krajiska-prezivjeli':
      'Список на борците на бригадата што ја преживеаја војната, само имиња, со дополнителен список (стр. 747–762 од книгата)',
    '32-divizija-borci':
      'Борци на штабот на дивизијата, придружните единици, бригадите „Браќа Радиќ“, „Матија Губец“, „Миховил Павлек Мишкина“ и I ударна загорска, и борци со нецелосни податоци: година и место на раѓање, народност, занимање, кога стапиле во НОВ, судбина; борецот е наведен во секоја единица во која се борел (стр. 431–662 од книгата)',
    '18-hrvatska':
      'Список на борците на бригадата, преживеани и загинати: година и место на раѓање, народност, занимање, кога стапиле во бригадата, должност, судбина (стр. 582–696 од книгата)',
    '11-dalmatinska':
      'Список на борците на бригадата: загинати, исчезнати и преживеани (на 15 мај 1945): должност, раѓање, занимање, кога стапиле во НОБ, судбина (стр. 479–600 од книгата)',
    '7-krajiska-spisak':
      'Преживеани и загинати борци и раководители од формирањето на бригадата декември 1942 до крајот на војната: раѓање, народност, занимање, кога стапиле во НОБ, должност, судбина (стр. 447 и натаму)',
    '12-krajiska-poginuli':
      'Загинатите борци и раководители на бригадата: должност, година и место на раѓање, каде и кога загинале',
    '12-krajiska-prezivjeli':
      'Преживеаните борци и раководители на бригадата: година и место на раѓање',
    '17-srpska':
      'Список на борците на бригадата што ја преживеаја војната и список на загинатите: раѓање, кога стапиле во бригадата, должност, каде и кога загинале (стр. 317–373 од книгата)',
    '14-srednjobosanska':
      'Список на загинатите, починатите и исчезнатите борци и раководители на бригадата, и список на борците што ја преживеаја војната, по општини (стр. 393–458 од книгата)',
    '4-proleterska-poginuli':
      'Борци и старешини на бригадата загинати од 1942 до 1945, по години: раѓање, занимање, должност, кога и каде загинале',
    '3-vojvodjanska':
      'Списоци на борците и старешините на бригадата: загинати, оние чија судбина остана неутврдена, и преживеани (стр. 479 и натаму)',
    'kalnicki-odred':
      'Список на борците на Калничкиот партизански одред, загинати и преживеани (стр. 311 и натаму)',
    'posavsko-trebavski-odred':
      'Список на борците на одредот по општините од кои дошле (стр. 313 и натаму)',
    '8-kordunaska-divizija':
      'Список на загинатите борци на Осмата дивизија, по презиме, со бригадата во која биле (стр. 806 и натаму)',
    'cankarjeva':
      'Список на борците на бригадата што ја преживеале војната (стр. 815 и натаму) и список на нејзините загинати (стр. 847 и натаму)',
    'gubceva':
      'Список на борците на бригадата што ја преживеале војната (стр. 979 и натаму) и список на нејзините загинати (стр. 1016 и натаму)',
    'dvanajsta':
      'Список на загинатите борци на бригадата и список на оние што ја преживеале војната, на крајот на книгата',
    'gradnikova':
      'Список на борците загинати во бригадата и список на другите: оние што ја преживеале војната или не загинале додека биле во неа (стр. 840 и натаму)',
    'zidanskova':
      'Список на борците на бригадата; кај загинатите годината на раѓање и на загинување (стр. 731 и натаму)',
    'skofjeloski-odred':
      'Список на борците на одредот, само имиња, како што се запишани во зачуваната архива на одредот (стр. 314 и натаму)',
    'istrski-odred':
      'Список на борците на одредот (стр. 827 и натаму), без загинатите, и список на загинатите со кратки податоци (стр. 849 и натаму)',
    'zapadnodolenjski-odred':
      'Список на борците на одредот (стр. 333 и натаму) и список на неговите загинати (стр. 340 и натаму)',
    'braciceva':
      'Список на загинатите борци на бригадата (стр. 722 и натаму) и на оние што ја преживеале војната (стр. 746 и натаму)',
    'tomsiceva-2':
      'Список на борците на бригадата од 16 јули 1942 до 13 јули 1943 (2. книга, стр. 847 и натаму)',
    'tomsiceva-3':
      'Борци на бригадата од 16 јули 1942 до 13 јули 1943 што беа изоставени од списокот во 2. книга или се пријавија дополнително (3. книга, стр. 647 и натаму)',
    'tomsiceva-4':
      'Списоци на борците на бригадата од 13 јули 1943 до 1 април 1944 и од 1 април 1944 до 15 мај 1945 (4. книга, стр. 576 и натаму)',
    '1-slovenska-artilerijska':
      'Список на старешините, на артилерците и на загинатите (стр. 388 и натаму)',
    'artilerija-9-korpusa':
      'Список на борците на артилеријата, на загинатите и на старешините (стр. 316 и натаму)',
    '19-srpska':
      'Загинати, исчезнати и починати по единици и борците што ја преживеаја војната: раѓање, должност, кога и каде загинале (стр. 411–612)',
    '22-srpska':
      'Загинати и преживеани борци и старешини на бригадата: раѓање, кога стапиле во бригадата, должност, каде загинале (стр. 317–399)',
    '12-vojvodjanska':
      'Список на борците по местата каде што живееле пред да стапат во бригадата и список на загинатите: од каде се, година на раѓање, каде загинале (стр. 207–258)',
    '4-vojvodjanska':
      'Список на припадниците на бригадата на 7 октомври 1943 и список на загинатите и починатите до 1. 3. 1946: раѓање, занимање, должност, каде загинале (стр. 281–334)',
    '1-kosovsko-metohijska':
      'Списоци на борците: косовско-метохиските баталјони од кои е формирана бригадата, борците што се приклучија во 1944 од Поречието и Тетово и од Јуник и Дечани, загинатите и ранетите (стр. 351–383)',
    '8-vojvodjanska':
      'Список на загинатите и исчезнатите борци и раководители на бригадата: раѓање, каде и кога загинале или исчезнале (стр. 675–722)',
    '19-sjevernodalmatinska':
      'Список на загинатите и починатите борци на дивизијата од формирањето до крајот на војната: од каде се, каде и кога загинале (стр. 253–299)',
    '21-srpska':
      'Загинати, преживеани и други што се бореа во бригадата (Втора шумадиска): родители, раѓање, должност, кога стапиле во бригадата и каде загинале (стр. 387–472)',
    '14-hercegovacka':
      'Список на борците што поминале низ бригадата: година и место на раѓање; загинатите, со единицата и местото на загинување (стр. 243–287)',
    '5-vojvodjanska':
      'Список на борците и старешините на бригадата: година и место на раѓање, занимање, должност во бригадата, каде загинале или исчезнале (стр. 429–584)',
    '6-vojvodjanska':
      'Список на загинатите борци и раководители: година и место на раѓање, датум и место на загинување, каде се погребани (стр. 175–199)',
    '13-vojvodjanska':
      'Список на припадниците на бригадата: имиња, понекаде прекар или место; авторот напоменува дека списокот не е целосен (стр. 771–793)',
    '7-srpska':
      'Список на борците на почетокот на мај 1944 по села и список на загинатите, умрените и исчезнатите: раѓање, стапување во бригадата, каде загинале (стр. 459–501)',
    '15-srpska':
      'Список на борците и раководителите на бригадата, список на загинатите и список на ранетите: раѓање, должност, кога и каде загинале или биле ранети (стр. 155–173)',
  },
  en: {
    'prva-licka-proleterska': 'Brigade history, in the series Ratna prošlost naroda i narodnosti Jugoslavije, vol. 322',
    'prva-proleterska-1': 'Roll of the brigade, volume one (A–I)',
    'prva-proleterska-2': 'Roll of the brigade, volume two (I–O)',
    'prva-proleterska-3': 'Roll of the brigade, volume three (O–Ž)',
    'druga-licka-spisak': 'The brigade’s Partisans and officers who were killed, died or went missing',
    'druga-licka-sjecanja-prezivjeli': 'Surviving Partisans and officers of the 2nd Lika Proletarian Brigade (from a collection of memoirs)',
    'druga-licka-sjecanja-poginuli':
      'Partisans of the 2nd Lika Proletarian Brigade who were killed, died or went missing (from a collection of memoirs); most are also on the Military History Institute’s list',
    'treca-proleterska-brigada': 'Brigade history, in the series Ratna prošlost naših naroda, vol. 144',
    'treca-proleterska-poginuli-knj3':
      'Partisans and officers who were killed or died, year by year, 1942–1945 (1,374 names; this copy lacks the pages for early 1944)',
    'treca-proleterska-formiranje':
      'The same roll as in Žarko Vidović’s brigade history, in Cyrillic, as the editors of the memoir collection arranged it, by battalion and company',
    'ljubljanska-brigada': 'History of the Ljubljana Brigade',
    '13-proleterska-spisak': 'The fallen and the survivors (part three of the brigade history)',
    '2-dalmatinska-proleterska': 'Roll of the 2nd Dalmatian Proletarian Brigade',
    '4-splitska-brigada': 'The brigade’s fallen and survivors',
    'prva-vojvodjanska': 'Roll of the 1st Vojvodina Brigade',
    '5-kozaracka': 'The brigade’s Partisans and officers who were killed, went missing or died',
    '2-vojvodjanska': 'Partisans and officers of the 2nd Vojvodina Brigade',
    '8-krajiska': 'Members of the 8th Krajina Brigade who were killed or died in the war',
    '6-krajiska': 'The brigade’s Partisans and officers who were killed or died, with a supplementary list',
    '4-krajiska': 'Partisans and officers of the 4th Krajina Brigade who were killed, died or went missing',
    '3-krajiska-proleterska': 'Fallen Partisans of the 3rd Krajina Proletarian Brigade, with their basic personal details',
    '17-slavonska-poginuli': 'Fallen Partisans of the 17th Assault Brigade',
    '17-slavonska-prezivjeli': 'Surviving Partisans of the 17th Assault Brigade',
    '25-srpska-divizija': 'Fallen Partisans and officers of the 25th Division',
    '1-sumadijska': 'Lists of fallen Partisans and officers, and of Partisans who survived the war',
    '18-slavonska': 'Partisans and officers of the 18th Assault Brigade who were killed or died, and a list of survivors',
    '4-banijska': 'Roll of the 4th Banija Brigade',
    '4-srpska': 'Roll of the 4th Serbian Assault Brigade',
    '7-vojvodjanska': 'Roll of the 7th Vojvodina Assault Brigade (survivors, the fallen, and those who died after the war)',
    '19-bircanska': 'Roll of the 19th Birač Brigade',
    '2-krajiska': 'Partisans and officers of the 2nd Krajina Brigade who were killed or died in the war',
    'tuzlanski-odred': 'Roll of the Tuzla Partisan Detachment',
    'uzicki-odred': 'Members of the Užice Partisan Detachment killed in the war of 1941–1945',
    '14-srpska': 'Fallen Partisans and officers of the detachment and of the 14th Serbian Brigade',
    '7-crnogorska-omladinska': 'Fallen Partisans of the 7th Montenegrin Youth Brigade',
    '17-majevicka': 'Members of the 3rd Majevica Partisan Detachment and the 17th Majevica Brigade who were killed or died in the war',
    '25-brodska-poginuli': 'Fallen Partisans of the Brod Brigade, 28th Division',
    '25-brodska-sastav': 'Partisans and officers who served in the Brod Brigade in October 1943',
    '25-srpska-brigada': 'Lists of the killed and of the wounded among the Partisans and officers of the 25th Serbian Brigade',
    '21-tuzlanska': 'Fallen Partisans and officers of the 21st Tuzla Brigade',
    '53-srednjobosanska-divizija': 'Partisans of the 53rd Central Bosnian Division who were killed, captured or went missing',
    '21-slavonska': 'Partisans and officers of the 21st Slavonian Assault Brigade who were killed, died or went missing',
    '32-divizija': 'Roll of the 32nd Division and the Western Group of Detachments (an asterisk marks the killed, a dash the missing)',
    '1-dalmatinska': 'Members of the 1st Dalmatian Proletarian Brigade killed in the war (text on znaci.org, with no scanned book)',
    '16-slavonska-omladinska':
      'The brigade’s fallen Partisans and officers; those killed in Pokuplje and on Žumberak; the brigade’s leaders from its formation to the end of the war (pp. 389–428 of the book)',
    '8-crnogorska': 'The brigade’s fallen comrades, Partisans and officers (pp. 471–501 of the book), and a further list of the fallen from Ub (pp. 509–510)',
    'druga-proleterska':
      'The brigade’s Partisans who were killed, died or went missing, by place and day: the Sutjeska, eastern Bosnia, Pljevlja and Prijepolje, western Serbia, the Syrmian Front (pp. 274–278 of the book)',
    'borci-sutjeske-4-proleterska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-5-proleterska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-6-istocnobosanska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-10-hercegovacka':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-7-banijska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-8-banijska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-3-dalmatinska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-16-banijska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-7-krajiska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-15-majevicka':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-prva-proleterska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-druga-proleterska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-treca-proleterska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-3-krajiska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-1-dalmatinska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-2-dalmatinska':
      'The roll of the Sutjeska: every Partisan of the brigade in the battle, with details of each and what became of them by the end of the war.',
    '12-dalmatinska':
      'The brigade’s Partisans and officers who were killed, battle by battle, from Sućuraj on 22 September 1943 to Ilirska Bistrica on 6 May 1945 (pp. 353–366 of the book)',
    '3-makedonska':
      'The brigade’s Partisans who were killed: where they came from, the year of birth, where and when they fell (pp. 359–368 of the book)',
    '3-krajiska-spisak-boraca':
      'Every Partisan who fought in the brigade from 22 August 1942 to 9 May 1945, survivors and the fallen: where they came from, occupation, when they joined the struggle and the brigade, duty and fate; with a supplement and an addendum (pp. 579 ff.)',
    '6-krajiska-prezivjeli':
      'The brigade’s Partisans who survived the war, names only, with a later list (pp. 747–762 of the book)',
    '32-divizija-borci':
      'Partisans of the division’s staff, its attached units, the Braća Radić, Matija Gubec, Mihovil Pavlek Miškina and 1st Zagorje Assault brigades, and some with incomplete details: year and place of birth, nationality, occupation, when they joined the army, fate; each is listed under every unit he fought in (pp. 431–662 of the book)',
    '18-hrvatska':
      'The brigade’s Partisans, survivors and the fallen: year and place of birth, nationality, occupation, when they joined the brigade, duty and fate (pp. 582–696 of the book)',
    '11-dalmatinska':
      'The brigade’s Partisans: those killed, the missing, and the survivors (as of 15 May 1945): duty, birth, occupation, when they joined the struggle, fate (pp. 479–600 of the book)',
    '7-krajiska-spisak':
      'Partisans and officers who survived or were killed, from the brigade’s formation in December 1942 to the end of the war: birth, nationality, occupation, when they joined the struggle, duty, fate (pp. 447 ff.)',
    '12-krajiska-poginuli':
      'The brigade’s Partisans and officers who were killed: duty, year and place of birth, where and when they fell',
    '12-krajiska-prezivjeli':
      'The brigade’s Partisans and officers who survived: year and place of birth',
    '17-srpska':
      'The brigade’s Partisans who survived the war, and those who were killed: birth, when they joined, duty, where and when they fell (pp. 317–373 of the book)',
    '14-srednjobosanska':
      'The brigade’s Partisans and officers who were killed, died or went missing, and those who survived the war, by municipality (pp. 393–458 of the book)',
    '4-proleterska-poginuli':
      'The brigade’s Partisans and officers killed from 1942 to 1945, year by year: birth, occupation, duty, when and where they fell',
    '3-vojvodjanska':
      'Lists of the brigade’s Partisans and officers: those killed, those whose fate remains unknown, and the survivors (pp. 479 ff.)',
    'kalnicki-odred':
      'List of the members of the Kalnik Partisan Detachment, killed and surviving (pp. 311 ff.)',
    'posavsko-trebavski-odred':
      'List of the detachment’s members by the municipality they came from (pp. 313 ff.)',
    '8-kordunaska-divizija':
      'List of the Eighth Division’s fallen, by surname, with the brigade each served in (pp. 806 ff.)',
    'cankarjeva':
      'List of the brigade’s members who survived the war (pp. 815 ff.) and of its fallen (pp. 847 ff.)',
    'gubceva':
      'List of the brigade’s members who survived the war (pp. 979 ff.) and of its fallen (pp. 1016 ff.)',
    'dvanajsta':
      'Lists of the brigade’s fallen and of those who survived the war, at the end of the book',
    'gradnikova':
      'Lists of the Partisans killed in the brigade and of its other members, who survived the war or did not fall while in it (pp. 840 ff.)',
    'zidanskova':
      'List of the brigade’s members; for those killed, the years of birth and death (pp. 731 ff.)',
    'skofjeloski-odred':
      'List of the detachment’s members, names only, as the surviving files of the detachment record them (pp. 314 ff.)',
    'istrski-odred':
      'List of the detachment’s members (pp. 827 ff.), without the fallen, and of the fallen with a short account of each (pp. 849 ff.)',
    'zapadnodolenjski-odred':
      'List of the detachment’s members (pp. 333 ff.) and of its fallen (pp. 340 ff.)',
    'braciceva':
      'Lists of the brigade’s fallen (pp. 722 ff.) and of those who survived the war (pp. 746 ff.)',
    'tomsiceva-2':
      'List of the brigade’s members from 16 July 1942 to 13 July 1943 (book 2, pp. 847 ff.)',
    'tomsiceva-3':
      'The brigade’s members from 16 July 1942 to 13 July 1943 left out of book 2’s list or reported later (book 3, pp. 647 ff.)',
    'tomsiceva-4':
      'Lists of the brigade’s members from 13 July 1943 to 1 April 1944 and from 1 April 1944 to 15 May 1945 (book 4, pp. 576 ff.)',
    '1-slovenska-artilerijska':
      'Lists of the officers, the gunners and the fallen (pp. 388 ff.)',
    'artilerija-9-korpusa':
      'Lists of the artillery’s members, its fallen and its officers (pp. 316 ff.)',
    '19-srpska':
      'The killed, missing and dead by unit, and the Partisans who survived the war: birth, duty, when and where they fell (pp. 411–612)',
    '22-srpska':
      'The brigade’s Partisans and officers who were killed or survived: birth, when they joined, duty, where they fell (pp. 317–399)',
    '12-vojvodjanska':
      'The brigade’s members by the place they lived in before joining, and its fallen: where they came from, year of birth, where they fell (pp. 207–258)',
    '4-vojvodjanska':
      'The brigade’s members on 7 October 1943, and those killed or dead up to 1 March 1946: birth, occupation, duty, where they fell (pp. 281–334)',
    '1-kosovsko-metohijska':
      'Lists of the brigade’s members: the Kosovo-Metohija battalions it was formed from, those who joined in 1944 from Poreče and Tetovo and from Junik and Dečani, its fallen and wounded (pp. 351–383)',
    '8-vojvodjanska':
      'The brigade’s killed and missing Partisans and leaders: birth, where and when they fell or went missing (pp. 675–722)',
    '19-sjevernodalmatinska':
      'The division’s Partisans killed or dead from its formation to the end of the war: where they came from, where and when they fell (pp. 253–299)',
    '21-srpska':
      'The brigade’s (2nd Šumadija) Partisans who were killed or survived, and others who fought in it: parents, birth, duty, when they joined and where they fell (pp. 387–472)',
    '14-hercegovacka':
      'Everyone who served in the brigade: year and place of birth; the fallen, with their unit and where they fell (pp. 243–287)',
    '5-vojvodjanska':
      'The brigade’s soldiers and officers: year and place of birth, trade, duty in the brigade, where they fell or went missing (pp. 429–584)',
    '6-vojvodjanska':
      'The fallen soldiers and officers: year and place of birth, date and place of death, where they were buried (pp. 175–199)',
    '13-vojvodjanska':
      'The brigade’s members: names, here and there a nickname or a place; the author notes the list is incomplete (pp. 771–793)',
    '7-srpska':
      'The soldiers in early May 1944 by village, and those killed, dead or missing: birth, when they joined, where they fell (pp. 459–501)',
    '15-srpska':
      'The brigade’s soldiers and officers, its fallen and its wounded: birth, duty, when and where they fell or were wounded (pp. 155–173)',
  },
}

// The part of a title the site added after " — ", as the record's book switch shows it
const PART: Partial<Record<Lang, Texts>> = {
  sl: {
    'tom 1': '1. zvezek',
    'tom 2': '2. zvezek',
    'tom 3': '3. zvezek',
    'spisak poginulih': 'seznam padlih',
    'spisak preživjelih': 'seznam preživelih',
    'spisak preživjelih (ratna sjećanja)': 'seznam preživelih (vojni spomini)',
    'spisak poginulih (zbornik sjećanja)': 'seznam padlih (zbornik spominov)',
    'spisak poginulih i umrlih (zbornik sjećanja, knj. 3)': 'seznam padlih in umrlih (zbornik spominov, 3. knjiga)',
    'spisak boraca i starešina na dan formiranja (zbornik sjećanja)': 'seznam na dan ustanovitve (zbornik spominov)',
    'poginuli': 'padli',
    'preživjeli': 'preživeli',
    'zbornik sjećanja': 'zbornik spominov',
    'spisak poginulih boraca': 'seznam padlih',
    'spisak poginulih i umrlih': 'seznam padlih in umrlih',
    'sastav u oktobru 1943.': 'sestava oktobra 1943',
    'spiskovi poginulih i ranjenih': 'seznama padlih in ranjenih',
    'spisak poginulih, zarobljenih i nestalih': 'seznam padlih, ujetih in pogrešanih',
    'spisak poginulih, umrlih i nestalih': 'seznam padlih, umrlih in pogrešanih',
    'spisak boraca': 'seznam borcev',
    'spiskovi boraca i starešina': 'seznami borcev in poveljnikov',
    'spisak poginulih i preživjelih': 'seznam padlih in preživelih',
    'preživjeli i poginuli (zbornik, knj. 2)': 'preživeli in padli (zbornik, 2. knjiga)',
    'popis boraca': 'seznam borcev',
    'borci divizije po jedinicama': 'borci divizije po enotah',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'seznam borcev (zbornik spominov, 3. knjiga)',
    'spiskovi poginulih i rukovodilaca': 'seznama padlih in vodstva',
    'ilustrovana monografija (1942—1992)': 'ilustrirana monografija (1942–1992)',
    'borci brigade na Sutjesci': 'borci brigade na Sutjeski',
  },
  mk: {
    'tom 1': 'том 1',
    'tom 2': 'том 2',
    'tom 3': 'том 3',
    'spisak poginulih': 'список на загинатите',
    'spisak preživjelih': 'список на преживеаните',
    'spisak preživjelih (ratna sjećanja)': 'список на преживеаните (воени сеќавања)',
    'spisak poginulih (zbornik sjećanja)': 'список на загинатите (зборник спомени)',
    'spisak poginulih i umrlih (zbornik sjećanja, knj. 3)': 'список на загинатите и починатите (зборник спомени, кн. 3)',
    'spisak boraca i starešina na dan formiranja (zbornik sjećanja)': 'список на денот на формирањето (зборник спомени)',
    'poginuli': 'загинати',
    'preživjeli': 'преживеани',
    'zbornik sjećanja': 'зборник спомени',
    'spisak poginulih boraca': 'список на загинатите',
    'spisak poginulih i umrlih': 'список на загинатите и починатите',
    'sastav u oktobru 1943.': 'составот во октомври 1943',
    'spiskovi poginulih i ranjenih': 'списоци на загинатите и ранетите',
    'spisak poginulih, zarobljenih i nestalih': 'список на загинатите, заробените и исчезнатите',
    'spisak poginulih, umrlih i nestalih': 'список на загинатите, починатите и исчезнатите',
    'spisak boraca': 'список на борците',
    'spiskovi boraca i starešina': 'списоци на борците и старешините',
    'spisak poginulih i preživjelih': 'список на загинатите и преживеаните',
    'preživjeli i poginuli (zbornik, knj. 2)': 'преживеани и загинати (зборник, кн. 2)',
    'popis boraca': 'список на борците',
    'borci divizije po jedinicama': 'борци на дивизијата по единици',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'список на борците (зборник спомени, кн. 3)',
    'spiskovi poginulih i rukovodilaca': 'списоци на загинатите и на раководството',
    'ilustrovana monografija (1942—1992)': 'илустрирана монографија (1942–1992)',
    'borci brigade na Sutjesci': 'борците на бригадата на Сутјеска',
  },
  en: {
    'tom 1': 'volume 1',
    'tom 2': 'volume 2',
    'tom 3': 'volume 3',
    'spisak poginulih': 'the fallen',
    'spisak preživjelih': 'the survivors',
    'spisak preživjelih (ratna sjećanja)': 'the survivors (war memoirs)',
    'spisak poginulih (zbornik sjećanja)': 'the fallen (memoirs)',
    'spisak poginulih i umrlih (zbornik sjećanja, knj. 3)': 'the fallen and the dead (memoirs, vol. 3)',
    'spisak boraca i starešina na dan formiranja (zbornik sjećanja)': 'roll on the day of formation (memoirs)',
    'poginuli': 'the fallen',
    'preživjeli': 'the survivors',
    'zbornik sjećanja': 'memoirs',
    'spisak poginulih boraca': 'the fallen',
    'spisak poginulih i umrlih': 'the fallen and the dead',
    'sastav u oktobru 1943.': 'roll of October 1943',
    'spiskovi poginulih i ranjenih': 'the killed and the wounded',
    'spisak poginulih, zarobljenih i nestalih': 'the killed, captured and missing',
    'spisak poginulih, umrlih i nestalih': 'the killed, dead and missing',
    'spisak boraca': 'roll',
    'spiskovi boraca i starešina': 'Partisans and officers',
    'spisak poginulih i preživjelih': 'the fallen and the survivors',
    'preživjeli i poginuli (zbornik, knj. 2)': 'survivors and the fallen (memoirs, vol. 2)',
    'popis boraca': 'roll',
    'borci divizije po jedinicama': 'the division’s Partisans, by unit',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'roll (memoirs, vol. 3)',
    'spiskovi poginulih i rukovodilaca': 'the fallen and the leaders',
    'ilustrovana monografija (1942—1992)': 'illustrated history (1942–1992)',
    'borci brigade na Sutjesci': 'the brigade at the Sutjeska',
  },
}

// Author lines that are not a person's name
const AUTHOR: Partial<Record<Lang, [RegExp, string][]>> = {
  sl: [[/^Grupa autora$/, 'Skupina avtorjev'], [/^Zbornik sjećanja$/, 'Zbornik spominov'], [/^Zbornik$/, 'Zbornik'],
    [/^Vojnoistorijski institut$/, 'Vojnozgodovinski inštitut'], [/ i dr\./, ' idr.']],
  mk: [[/^Grupa autora$/, 'Група автори'], [/^Zbornik sjećanja$/, 'Зборник спомени'], [/^Zbornik$/, 'Зборник'],
    [/^Vojnoistorijski institut$/, 'Воено-историски институт'], [/ i dr\./, ' и др.'], [/\(ur\.\)/, '(ур.)']],
  en: [[/^Grupa autora$/, 'Various authors'], [/^Zbornik sjećanja$/, 'Memoir collection'], [/^Zbornik$/, 'Collection'],
    [/^Vojnoistorijski institut$/, 'Military History Institute'], [/ i dr\./, ' et al.'], [/\(ur\.\)/, '(ed.)']],
}

export function sourceDescription(source: PdfSource, lang: Lang): string | undefined {
  if (lang === 'sr-cyrl') return source.description && toCyrillic(source.description)
  return DESCRIPTION[lang]?.[source.id] ?? source.description
}

export function sourceAuthor(source: PdfSource, lang: Lang): string {
  return (AUTHOR[lang] ?? []).reduce((text, [from, to]) => text.replace(from, to), source.author)
}

/** The list a title names after " — ", in the language: "Brodska brigada — spisak poginulih boraca" -> "the fallen" */
export function titlePart(title: string, lang: Lang): string {
  const part = title.includes(' — ') ? title.split(' — ').pop()! : title
  if (lang === 'sr-cyrl') return title.includes(' — ') ? toCyrillic(part) : part
  return PART[lang]?.[part] ?? part
}

export function missingSourceTexts(ids: string[]): string[] {
  return (Object.entries(DESCRIPTION) as [Lang, Texts][]).flatMap(([lang, texts]) =>
    ids.filter((id) => !texts[id]).map((id) => `${lang}:${id}`))
}
