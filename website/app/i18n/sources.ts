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
    'druga-licka-staresine':
      'Komandanti, komisarji, njihovi namestniki, operativni in obveščevalni častniki ter intendanti štaba brigade in štabov bataljonov od ustanovitve do konca vojne, pri večini s kratkim življenjepisom (str. 349–360)',
    'treca-proleterska-brigada': 'Monografija, zbirka Ratna prošlost naših naroda, knj. 144',
    'treca-proleterska-poginuli-knj3':
      'Seznam padlih in umrlih borcev in poveljnikov po letih, 1942–1945 (1.374 imen; v tem izvodu manjkajo strani z začetkom leta 1944)',
    'treca-proleterska-formiranje':
      'Isti seznam kot v monografiji Žarka Vidovića, v cirilici, kot ga je uredilo uredništvo zbornika spominov; po bataljonih in četah',
    'ljubljanska-brigada': 'Monografija Ljubljanske brigade',
    '13-proleterska-spisak': 'Seznam padlih in preživelih borcev (tretji del monografije)',
    '2-dalmatinska-proleterska': 'Seznam borcev 2. dalmatinske proletarske brigade NOVJ',
    '2-dalmatinska-stabovi':
      'Starešine štaba brigade s časom, ko je kdo opravljal dolžnost, čet pri štabu, brigadne bolnišnice, štabov bataljonov in poveljstev čet, po dolžnostih (str. 473–486)',
    '4-splitska-brigada': 'Seznam padlih in preživelih borcev brigade',
    'prva-vojvodjanska': 'Seznam borcev Prve vojvodinske brigade',
    '5-kozaracka': 'Seznam padlih, pogrešanih in umrlih borcev in poveljnikov brigade',
    '2-vojvodjanska': 'Seznam borcev in poveljnikov 2. vojvodinske brigade',
    '8-krajiska': 'Seznam padlih in umrlih v NOB iz 8. krajiške brigade',
    '8-krajiska-sjecanja-poginuli':
      'Seznam padlih in umrlih borcev brigade iz zbornika spominov: oče, leto in kraj rojstva, kdaj in kje je padel, dolžnost.',
    '6-krajiska': 'Seznam padlih in umrlih borcev in poveljnikov brigade, z dopolnilnim seznamom',
    '4-krajiska': 'Seznam padlih, umrlih in pogrešanih borcev in poveljnikov 4. krajiške brigade',
    '3-krajiska-proleterska': 'Seznam padlih borcev Tretje proletarske krajiške brigade z osnovnimi osebnimi podatki',
    '17-slavonska-poginuli': 'Seznam padlih borcev 17. udarne brigade',
    '17-slavonska-prezivjeli': 'Seznam preživelih borcev 17. udarne brigade',
    '25-srpska-divizija': 'Seznam padlih borcev in poveljnikov 25. divizije',
    '1-sumadijska': 'Seznama padlih borcev in poveljnikov ter borcev, ki so vojno preživeli',
    '18-slavonska': 'Seznam padlih in umrlih borcev in poveljnikov 18. udarne brigade ter seznam preživelih borcev',
    '4-banijska': 'Seznam borcev 4. banijske brigade',
    '4-banijska-starjesine': 'Komandanti, politični komisarji, njihovi namestniki, načelniki štaba in drugi starešine štaba brigade in štabov bataljonov, po dolžnostih, samo imena (str. 52–53)',
    '4-srpska': 'Seznam borcev Četrte srbske udarne brigade',
    '7-vojvodjanska': 'Seznam borcev 7. vojvodinske udarne brigade (preživeli, padli in po vojni umrli)',
    '19-bircanska': 'Seznam borcev 19. birčanske brigade',
    '2-krajiska': 'Seznam padlih in umrlih borcev in poveljnikov 2. krajiške brigade v NOB',
    'tuzlanski-odred': 'Seznam borcev Tuzelskega partizanskega odreda',
    'uzicki-odred': 'Seznam borcev Užiškega partizanskega odreda, ki so padli v narodnoosvobodilni vojni 1941–1945',
    'pozega-cete':
      'Seznami borcev 1. in 2. požeške čete Užiškega odreda 1941—1942, Pilatovačke čete na dan ustanovitve, borcev, ki so varovali objekte v Požegi, udeležencev NOB iz vasi okoli Požege v drugih enotah leta 1941, 1. čete 5. bataljona Užiškega odreda leta 1944 ter padlih in umrlih borcev Požeške čete 2. proletarske brigade, po vaseh; po vojni so jih sestavili preživeli borci čet. Seznami delavcev partizanskih delavnic, simpatizerjev in beguncev niso vneseni.',
    '14-srpska': 'Seznam padlih borcev in poveljnikov odreda in 14. srbske brigade',
    '7-crnogorska-omladinska': 'Seznam padlih borcev 7. črnogorske mladinske brigade',
    '7-crnogorska-zbornik-poginuli':
      'Padli borci in starešine brigade iz zbornika spominov: rojstvo, četa in bataljon, kdaj in kje je padel.',
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
    'prva-proleterska-stroj-u-rudom':
      'Borci, ki so 21. decembra 1941 stali v zboru v Rudem, po štabih, bataljonih in četah: rojstvo, poklic, dolžnost in kaj se je s kom zgodilo v vojni (str. 433–492). Zvezdica ob imenu označuje borca, ki je padel v vojni.',
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
      'Seznam padlih borcev in poveljnikov brigade, po bojih, od Sućurja 22. septembra 1943 do Ilirske Bistrice 6. maja 1945 (str. 353–366 knjige), in pregled vodilnega kadra štaba brigade in štabov bataljonov, s časom, ko je kdo opravljal dolžnost (str. 339–342)',
    '3-makedonska':
      'Seznam padlih borcev brigade: od kod so bili, leto rojstva, kje in kdaj so padli (str. 359–368 knjige)',
    '3-krajiska-spisak-boraca':
      'Seznam borcev, ki so se v brigadi borili od 22. 8. 1942 do 9. 5. 1945, preživelih in padlih: od kod so bili, poklic, kdaj so vstopili v NOB in v brigado, dolžnost, usoda; z dopolnilom in prilogo (str. 579 in naprej)',
    '3-krajiska-sastav-1942':
      'Vsi borci in starešine brigade sredi novembra 1942, po štabu, politodjelu, intendanturi, bataljonih, četah in vodih: dolžnost, leto in kraj rojstva, narodnost, poklic, pri mnogih tudi poznejša usoda (besedilo na znaci.org, brez skenirane knjige)',
    '6-krajiska-prezivjeli':
      'Seznam borcev brigade, ki so vojno preživeli, samo imena, z naknadnim seznamom (str. 747–762 knjige)',
    '6-krajiska-kadar':
      'Starešine brigade 1942–1943 po dolžnostih, od komandantov brigade do četnih bolničark, samo imena (str. 739–745 knjige)',
    '32-divizija-borci':
      'Borci štaba divizije, spremljevalnih enot, brigad Braća Radić, Matija Gubec, Mihovil Pavlek Miškina in I. udarne zagorske ter borci z nepopolnimi podatki: leto in kraj rojstva, narodnost, poklic, vstop v NOV, usoda; borec je naveden v vsaki enoti, v kateri se je boril (str. 431–662 knjige)',
    '32-divizija-kadar':
      'Starešine štaba divizije in enot pri štabu, brigad »Braća Radić«, »Matija Gubec«, »Mihovil Pavlek Miškina« in 1. zagorske, njihovih bataljonov in spremljevalnih čet, po dolžnostih (str. 286–295)',
    '18-hrvatska':
      'Seznam borcev brigade, preživelih in padlih: leto in kraj rojstva, narodnost, poklic, vstop v brigado, dolžnost, usoda (str. 582–696 knjige)',
    '18-hrvatska-starjesine':
      'Poveljniki štaba brigade, bataljonov in čet ter enot pri štabu, po dolžnostih, samo imena (str. 573–581 knjige)',
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
    '4-proleterska-formiranje':
      'Seznam borcev in starešin na dan ustanovitve brigade, 17. junija 1942, po štabih, bataljonih in četah: dolžnost, kraj in leto rojstva, poklic, članstvo v KPJ in SKOJ in kaj je bilo z njim.',
    '3-vojvodjanska':
      'Seznami borcev in poveljnikov brigade: padli, tisti, katerih usoda ni znana, in preživeli (str. 479 in naprej)',
    'kalnicki-odred':
      'Seznam borcev Kalniškega partizanskega odreda, padlih in preživelih (str. 311 in naprej)',
    'kalnicki-odred-kadar':
      'Voditelji prvih oboroženih skupin in formacij na Kalniku 1941–1942, štaba odreda, njegovih bataljonov, čet in vodov, s časom, ko je kdo opravljal dolžnost (str. 282–303, 305)',
    'posavsko-trebavski-odred':
      'Seznam borcev odreda po občinah, iz katerih so prišli (str. 313 in naprej)',
    '8-kordunaska-divizija':
      'Seznam padlih borcev Osme divizije po priimkih, z brigado, v kateri so bili (str. 806 in naprej)',
    '8-kordunaska-divizija-kadar':
      'Komandanti, politični komisarji in načelniki štaba divizije, njenih brigad in bataljonov, s časom na dolžnosti in usodo vsakega (str. 762–775)',
    'cankarjeva':
      'Seznam cankarjevcev, ki so preživeli vojno (str. 815 in naprej), in seznam padlih (str. 847 in naprej)',
    'cankarjeva-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba brigade ter komandanti in komisarji bataljonov, s časom na dolžnosti (str. 810–814)',
    'gubceva':
      'Seznam gubčevcev, ki so preživeli vojno (str. 979 in naprej), in seznam padlih (str. 1016 in naprej)',
    'gubceva-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba brigade ter komandanti in komisarji bataljonov, s časom na dolžnosti (str. 975–978)',
    'dvanajsta':
      'Seznam padlih borcev brigade in seznam borcev, ki so preživeli vojno, na koncu knjige',
    'dvanajsta-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba brigade in bataljonov, s časom na dolžnosti; šefi obveščevalnega centra, intendanti, sanitetni referenti in sekretarji SKOJ, samo imena (str. 571–574)',
    'gradnikova':
      'Seznam v brigadi padlih borcev in seznam drugih borcev brigade, ki so preživeli vojno ali niso padli v njej (str. 840 in naprej)',
    'gradnikova-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba brigade s časom, ko je kdo opravljal dolžnost, ter kratki življenjepisi narodnih herojev brigade (str. 791–799)',
    'zidanskova':
      'Seznam borcev brigade; padli so označeni z letnicama rojstva in padca (str. 731 in naprej)',
    'zidanskova-kader':
      'Komandanti, politični komisarji, njihovi namestniki, načelniki štaba in sekretarji SKOJ brigade, s časom na dolžnosti (str. 729–730)',
    'skofjeloski-odred':
      'Seznam borcev odreda, samo imena, kot so vpisani v ohranjenem arhivu odreda (str. 314 in naprej)',
    'istrski-odred':
      'Seznam borcev odreda (str. 827 in naprej), brez padlih, in seznam padlih s kratkimi podatki (str. 849 in naprej)',
    'istrski-odred-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba odreda, njegovih bataljonov in čet, s časom na dolžnosti (str. 821–826)',
    'zapadnodolenjski-odred':
      'Seznam odredovcev (str. 333 in naprej) in seznam padlih (str. 340 in naprej)',
    'braciceva':
      'Seznam padlih borcev brigade (str. 722 in naprej) in tistih, ki so vojno preživeli (str. 746 in naprej)',
    'tomsiceva-1':
      'Seznama borcev enot, iz katerih je nastala brigada: udarne grupe 3. bataljona Ljuba Šercerja, Dakijeve leteče udarne patrulje, Proletarske udarne patrulje in čete ter 1. slovenskega proletarskega udarnega bataljona Toneta Tomšiča (1. knjiga, str. 535 in naprej)',
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
    '19-sjevernodalmatinska-kadar':
      'Komandanti in politični komisarji divizije in njenih brigad, s časom na dolžnosti, člani politodela 1943–1945 in narodni heroji divizije, s kratkim življenjepisom (str. 240–252)',
    '21-srpska':
      'Padli, preživeli in drugi, ki so se borili v brigadi (Druga šumadijska): starši, rojstvo, dolžnost, vstop v brigado in kje so padli (str. 387–472)',
    '14-hercegovacka':
      'Seznam borcev, ki so šli skozi brigado: leto in kraj rojstva; padli, z enoto in krajem smrti (str. 243–287)',
    '14-hercegovacka-komandni-sastav':
      'Štab brigade, štabi bataljonov, poveljstva čet, spremljevalni vodi, komandirji in politični delegati vodov ter enote pri štabu, po dolžnostih, s časom, ko je kdo opravljal dolžnost (str. 234–242)',
    '5-vojvodjanska':
      'Seznam borcev in starešin brigade: leto in kraj rojstva, poklic, dolžnost v brigadi, kje so padli ali izginili (str. 429–584)',
    '6-vojvodjanska':
      'Seznam padlih borcev in starešin: leto in kraj rojstva, datum in kraj smrti, kje so pokopani (str. 175–199)',
    '6-vojvodjanska-stabovi':
      'Člani štaba brigade, štabov njenih bataljonov in poveljstev čet, po dolžnostih, samo imena (str. 171–174)',
    '13-vojvodjanska':
      'Seznam pripadnikov brigade: imena, ponekod vzdevek ali kraj; avtor opozarja, da seznam ni popoln (str. 771–793)',
    '7-srpska':
      'Seznam borcev v začetku maja 1944 po vaseh in seznam padlih, umrlih in pogrešanih: rojstvo, vstop v brigado, kje so padli (str. 459–501)',
    '15-srpska':
      'Seznam borcev in starešin brigade, seznam padlih in seznam ranjenih: rojstvo, dolžnost, kdaj in kje so padli ali bili ranjeni (str. 155–173)',
    '8-srpska':
      '„Nezaboravnik“, seznam padlih borcev brigade: rojstvo, datum in kraj smrti (str. 265–297)',
    '10-srpska':
      'Seznam padlih borcev in starešin: rojstvo, vstop v brigado, dolžnost, kje so padli in pokopani (str. 488–541)',
    '23-srpska':
      'Pregled padlih in umrlih borcev in starešin: leto in kraj rojstva, poklic, vstop v NOVJ, enota, kje so padli in pokopani (str. 352–388)',
    '12-srpska':
      'Pregled padlih in umrlih borcev in starešin: leto in kraj rojstva, poklic, vstop v NOVJ, enota, kje so padli in pokopani (str. 355–400)',
    '20-srpska':
      'Pregled padlih in umrlih borcev in starešin: leto in kraj rojstva, poklic, vstop v NOVJ, enota, kje so padli in pokopani (str. 321–385)',
    '1-konjicka':
      'Seznam padlih borcev in starešin (rojstvo, kje so padli) in vojni seznam starešin in borcev brigade, samo imena (str. 317–327)',
    'toplicki-odred':
      'Borci odreda na dan ustanovitve, seznam padlih in umrlih borcev in starešin ter narodni heroji, ki so se borili v odredu, s fotografijami (str. 302–344)',
    'karlovacka':
      'Seznam borcev in starešin brigade na dan ustanovitve v Hrašću 5. marca 1944 in seznam padlih borcev in starešin (str. 379–414)',
    'karlovacka-kadar':
      'Štab brigade in štabi štirih bataljonov s časom, ko je kdo opravljal dolžnost, in kaj je bilo z njim, komandirji, komisarji in delegati čet in vodov, čete in vodi pri štabu, zaledje (str. 371–378)',
    '14-primorsko-goranska':
      'Seznam padlih borcev brigade z rojstvom, dolžnostjo in krajem smrti (str. 227–264)',
    '22-divizija':
      'Seznam padlih borcev in starešin divizije po brigadah: kraj rojstva, dan in kraj smrti (str. 445–476)',
    '34-divizija':
      'Pregled padlih borcev in starešin divizije: čin, brigada, rojstvo, vstop v NOB, kraj in dan smrti (str. 401–432)',
    '34-divizija-kadar':
      'Starešine štaba divizije, divizijskega komiteja KPJ, političnega oddelka, intendanture in saniteta, brigad »Franjo Ogulinac Seljo«, 16. mladinske »Joža Vlahović«, karlovške in žumberške, partizanskih odredov in samostojnih enot divizije, po dolžnostih (str. 389–399)',
    '4-sandzacka':
      'Seznam padlih borcev in starešin (rojstvo, kje so padli) in seznam ranjenih s krajem in dnem ranitve (str. 460–485)',
    '3-primorsko-goranska':
      'Seznam starešin brigade in četnih bolničarjev z dolžnostjo ter seznam padlih pripadnikov brigade z rojstvom in krajem smrti (str. 234–259)',
    '3-primorsko-goranska-stabovi':
      'Člani štaba brigade, štabov bataljonov in poveljniki samostojnih enot, po dolžnostih, s časom na dolžnosti in kako se je končal (str. 227–233)',
    '13-hercegovacka':
      'Padli borci in starešine brigade (rojstvo, dan in kraj smrti) in seznam borcev, ki so se borili v brigadi, samo imena (str. 316–347)',
    '13-hercegovacka-starjesine':
      'Štab brigade in enote pri štabu, štabi bataljonov in poveljstva čet, po dolžnostih, s časom, ko je kdo opravljal dolžnost (str. 305–315)',
    '12-hercegovacka':
      'Seznam padlih borcev in starešin brigade po občinah: rojstvo, dolžnost, kje in kdaj so padli (str. 207–220)',
    '1-bokeljska':
      'Seznam padlih in umrlih borcev brigade ter pogrešanih v boju: bataljon, rojstvo, kje in kdaj so padli (str. 315–321)',
    '1-bokeljska-spisak':
      'Seznam brigade od ustanovitve 5. oktobra 1944 do konca vojne, po enotah: štab, bataljoni in enote pri štabu, dolžnost in ime vsakega borca in starešine (str. 291–314). Borec, premeščen v drugo enoto, je vpisan tudi vanjo, zato se nekateri pojavijo dvakrat. Strani na znaci.org nimajo besedila, le slike: imena so prebrana s slik.',
    '6-dalmatinska':
      'Seznam padlih borcev brigade: od kod so bili, kje in kdaj so padli (str. 259–271)',
    '6-dalmatinska-kadar':
      'Komandanti, komisarji, njihovi namestniki, načelniki in drugi starešine štaba brigade in štabov bataljonov, po dolžnostih, samo imena (str. 257–258)',
    'osjecka':
      'Seznam padlih in umrlih borcev brigade in seznam preživelih borcev, po občinah rojstva (str. 207–254)',
    'osjecka-rukovodioci':
      'Komandanti, komisarji in načelniki štaba brigade, komandanti in komisarji bataljonov, komandirji in komisarji čet, samo imena (str. 203–206)',
    '1-zagorska':
      'Seznam padlih borcev in starešin brigade od 8. maja 1944 do 15. maja 1945: leto in kraj rojstva, kdaj in kje so padli (str. 191–205)',
    '6-crnogorska':
      'Seznam padlih borcev in poveljnikov brigade, z umrlimi zaradi ran in bolezni: rojstvo, dolžnost, kje in kdaj so padli (str. 871 in dalje)',
    '11-krajiska-poginuli':
      'Seznam padlih borcev brigade po občinah: rojstvo, narodnost, poklic, kdaj so vstopili v NOV, dolžnost, kje in kdaj so padli (str. 439–463)',
    '11-krajiska-zene':
      'Seznam bork, ki so bile v brigadi, samo imena (str. 425)',
    '3-banijska':
      'Seznam poveljnikov in borcev brigade, samo imena (str. 195–205)',
    '8-banijska-poginuli':
      'Padli in umrli borci brigade od 7. septembra 1942 do 6. decembra 1944: rojstvo, poklic, kdaj so prišli v brigado, dolžnost, kje in kdaj so padli (str. 247–312)',
    '8-banijska-kadar':
      'Štab brigade, politodel in štabi petih bataljonov, po dolžnostih (str. 244–246)',
    'macvanski-odred':
      'Seznam borcev Mačvanskega (Podrinjskega) partizanskega odreda, prvi del (julij 1941 – marec 1942): po krajih, iz katerih so vstopili v odred, s podatki o vsakem (besedilo na znaci.org, brez skenirane knjige; drugi del ni objavljen)',
    'posavski-odred':
      'Seznam borcev Posavskega partizanskega odreda leta 1941: poveljstvo, bolnišnica in bataljoni, s podatki o vsakem (str. 565–742)',
    '51-divizija':
      'Borci 51. vojvodinske divizije, padli in pogrešani v bitki pri Batini novembra 1944: rojstvo, dolžnost, kje in kdaj so padli (str. 469–501)',
    '51-divizija-savic':
      'Seznam padlih borcev in starešin divizije od ustanovitve, 1. novembra 1944, do konca vojne, 15. maja 1945, po brigadah: 7., 8., 12. in 14. (slovaška), artilerijska, enote pri štabu; rojstvo, dolžnost, kje in kdaj so padli (str. 219–288)',
    'borci-sutjeske-vrhovni-stab':
      'Imenski seznam borcev s Sutjeske: vsi pripadniki Vrhovnega štaba, njegovih služb, Spremljevalnega bataljona in britanske vojaške misije v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'vtr-grmec':
      'Delavci vojaškotehnične delavnice Vrhovnega štaba v Grmeču 1942–1943, z obrtjo in krajem, od koder so bili, tisti, ki so padli ali umrli med vojno in po njej, straža delavnice in delavci drvarske livarne (str. 361–364).',
    'borci-sutjeske-1-proleterska-divizija':
      'Imenski seznam borcev s Sutjeske: štab divizije z njegovimi službami in spremljevalnimi enotami v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-2-proleterska-divizija':
      'Imenski seznam borcev s Sutjeske: štab divizije z njegovimi službami in spremljevalnimi enotami v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-3-udarna-divizija':
      'Imenski seznam borcev s Sutjeske: štab divizije z njegovimi službami in spremljevalnimi enotami v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-7-banijska-divizija':
      'Imenski seznam borcev s Sutjeske: štab divizije z njegovimi službami in spremljevalnimi enotami v bitki, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    'borci-sutjeske-centralna-bolnica':
      'Imenski seznam borcev s Sutjeske: osebje Centralne bolnišnice in ranjenci, katerih enote ni bilo mogoče ugotoviti, s podatki o vsakem in o tem, kaj se je z njim zgodilo do konca vojne.',
    '3-licka':
      'Seznam padlih, umrlih in pogrešanih borcev brigade ter njeni narodni heroji (str. 361–413).',
    '5-proleterska-partizanke':
      'Življenjepisi partizank brigade: rojstvo, pot v NOB, dolžnosti v brigadi, rane in odlikovanja, življenje po vojni (str. 43–278).',
    '16-banijska-poginuli':
      'Seznam padlih borcev in poveljnikov brigade od 26. decembra 1942 do 30. junija 1943, z letom in krajem rojstva ter krajem smrti (str. 201–247).',
    'pozarevacki-odred':
      'Seznam borcev odreda od 1941 do oktobra 1944, s podatki o vsakem (str. 238–307; uredil Miodrag Stojanović Kole).',
    '1-proleterski-bataljon':
      'Seznam borcev bataljona, z letnico in krajem rojstva ter usodo (str. 262–277).',
    '4-pomorski-sektor':
      'Seznam borcev IV. POS 1943–1945, ki so ga sestavili Sekcija borcev sektorja in avtor (4.702 imeni, s krajem, od koder je kdo), ter padli in umrli borci sektorja z dolžnostjo in okoliščinami smrti (str. 418–478).',
    '4-pomorski-sektor-stab':
      'Komandanti, politični komisarji, njihovi pomočniki in načelniki štaba sektorja, s časom, ko je kdo opravljal dolžnost (priloga X, str. 485)',
    'viski-bataljon':
      'Seznam borcev Viškega prostovoljnega bataljona na Visu konec januarja 1944: poveljstvo, čete, vodi in desetini Biševa in Oključne (str. 538–539).',
    'kokrski-odred-1':
      'Seznam borcev Kokrškega odreda prve sestave, junij 1942 - januar 1943, po štabu, bataljonih in četah: od kod je kdo, dolžnosti in kaj se je s kom zgodilo (str. 509–525).',
    'kokrski-odred':
      'Spisek borcev Drugega kokrškega odreda, avtorjeva rekonstrukcija po spiskih in dokumentih odreda: štabi, obveščevalni center in točke, kurirske postaje, sanitetne ustanove, delavnice in bataljoni po četah in obdobjih, z letnico rojstva in kdo je padel (str. 453–478).',
    'cankarjev-bataljon':
      'Formacija bataljona v Dražgošah, španski borci in narodni heroji, padli cankarjevci po bojih 1941–1942, preživeli nosilci spomenice 1941 in ostali preživeli udeleženci dražgoške bitke (str. 338–346).',
    'novosadski-odred':
      'Seznam pripadnikov Novosadskega partizanskega odreda v letih 1941 in 1944: ime, dolžnost, od kod je kdo in od kdaj (str. 85–92).',
    'deveta':
      'Seznam borcev IX. SNOB Kočevske: ime, leto in kraj rojstva, pri padlih leto in kraj smrti (str. 425–446).',
    'deveta-kader':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba brigade ter komandanti in komisarji bataljonov, s časom na dolžnosti in kdo je padel na dolžnosti (str. 401–404)',
    '4-prekomorska':
      'Seznam padlih in umrlih borcev in vodilni kader brigade: štab, komanda stana, bataljoni, samostojna četa in komande čet (str. 327–333).',
    '9-srpska':
      'Stroj v Rečici: 377 borcev na dan ustanovitve, 11. marca 1944; poveljniški kader brigade, bataljonov in čet z datumi dolžnosti; bolničarke in borke. Imenika borcev s kratkimi življenjepisi (str. 47–372) znaci.org nima.',
    'kozjanski-odred':
      'Seznam borcev in bork Kozjanskega odreda: 3.495 oseb od ustanovitve do ukinitve, z datumom in krajem rojstva, vstopom v NOV in POS, poklicem in opombo (kje je kdo bil, kdo je padel); strani so tu črno-bele, besedilo kot v knjigi.',
    'proleterski-bataljon-bk':
      'Seznam borcev bataljona: življenjepis vsakega ob njegovi fotografiji, od rojstva in prihoda v Kozaraško, Grmečko ali Drvarsko proletarsko četo do smrti ali konca vojne (str. 256–362).',
    '1-tenkovski-bataljon':
      'Seznam pripadnikov Tankovskega voda Skupine partizanskih odredov za Liko, Tankovske čete 1. korpusa in Tankovskega bataljona Glavnega štaba NOV in PO Hrvaške (251 imen, str. 337–340).',
    '3-diverzantski-odred':
      'Pregled borcev in starešin 3. diverzantske skupine, čete, bataljona in odreda (imena, z oznako padlih in po vojni umrlih) in pregled padlih diverzantov z dolžnostjo in letom (priloga IV, str. 587–591).',
    '1-2-prekomorska':
      'Seznam padlih borcev in bork obeh brigad (rojstvo, kdaj in kje je kdo padel) in vodilni kader v taboriščih Carbonara in Gravina, na Korčuli, Hvaru in Visu ter komande čet (str. 357–372).',
    '5-prekomorska':
      'Seznam padlih borcev in bork (256: rojstvo, kdaj in kje je kdo padel) in vodilni kader brigade, bataljonov in čet (str. 283–301).',
    'sercerjeva':
      'Seznam partizanov prostovoljcev Šercerjeve brigade od ustanovitve 6. oktobra 1942 do konca februarja 1943 (ime, partizansko ime in kraj) in seznam padlih do konca leta 1943, po kraju in dnevu smrti (str. 509–523).',
    'kosovelova':
      'Seznam padlih, pogrešanih in za posledicami ran umrlih borcev (504 imena: rojstvo, kraj, kdaj in kje je kdo padel) in poveljniški kader brigade in njenih bataljonov z datumi dolžnosti (str. 803–824).',
    'eskadrile-novj':
      'Seznama moštva prve in druge eskadrilje NOVJ (352. in 351. eskadrilja RAF): številka, čin, dolžnost, rojstvo in kako je kdo prišel v eskadrilji, z Bližnjega vzhoda, iz italijanskega ujetništva ali iz domovine; na koncu imena, katerih eskadrilja ni ugotovljena (str. 331–354).',
    '42-vazduhoplovna':
      'Seznam moštva divizije po polkih (421., 422. in 423. letalski polk), štabu, samostojni četi in letalskih delavnicah: čin in dolžnost (str. 291–321).',
    '18-srpska':
      '„Borili so se v 18. srbski brigadi“: 5.047 borcev in starešin brigade po avtorjevem štetju, od tega 780 padlih, 787 ranjenih, 47 pogrešanih in 49 umrlih zaradi bolezni, z letom in krajem rojstva, dolžnostjo in tem, kje je kdo padel ali bil ranjen (str. 313–426).',
    '5-srpska':
      'Seznam padlih in umrlih borcev in starešin brigade (priloga št. 2): leto in kraj rojstva, poklic, kdaj je kdo stopil v NOVJ, bataljon in dolžnost, kdaj in kje je padel in kje je pokopan (str. 450–510).',
    'cacanski-odred':
      'Padli borci odreda, po pokrajinah (Dragačevo, Ljubić, Trnava, Takovo, Čačak) in vaseh: oče, poklic, rojstvo, bataljon, v katerem se je boril, in kako in kje je padel.',
    'mostarski-bataljon':
      'Borci Konjiškega bataljona (september 1941 — junij 1942), Mostarskega bataljona (junij 1942 — junij 1943) in Mostarskega bataljona v Mostarskem partizanskem odredu (junij 1943 — maj 1944), vsak s kratkim življenjepisom: rojstvo, poklic, SKOJ in KPJ, prihod v bataljon, dolžnost in usoda (str. 329–392).',
    '13-krajiska':
      'Dva seznama: borci in starešine, ki so bili v brigadi avgusta in septembra 1943, s krajem, dolžnostjo in za padle, kdaj in kje so padli in kje so pokopani; člani partijske organizacije KPJ brigade maja 1945, z dnem sprejema v Partijo in dolžnostjo (str. 365–404).',
    'pozega-pali':
      'Priloga Dragoljuba Munjića: seznam padlih borcev NOB, žrtev fašističnega terorja in civilnih žrtev vojne v okraju Požega, po vaseh, z rojstvom, enoto in tem, kako je kdo padel. Vneseni so borci in, označeni kot aktivisti, sodelavci NOP, odborniki in delavci partizanskih delavnic; civilne žrtve in vojaki nekdanje jugoslovanske vojske niso. Knjiga ne pripada eni enoti: njen zapis je dodan zapisu vsakega borca, ki je na strani in za katerega se zanesljivo ve, da je on.',
    'cacanski-kraj-pali':
      'Padli in umrli iz čačanskega okraja 1941–1945, po pokrajinah (Dragačevo, Ljubić, Takovo, Trnava, Čačak) in vaseh: oče, poklic, rojstvo, enota in kako je kdo padel. Vneseni so borci in, označeni kot aktivisti, člani KPJ in SKOJ, odborniki, sodelavci NOP in delavci partizanskih delavnic leta 1941; civilne žrtve in četniki niso. Knjiga ne pripada eni enoti: njen zapis je dodan zapisu vsakega borca, ki je na strani in za katerega se zanesljivo ve, da je on.',
    '1-krajiska':
      'Seznam padlih, umrlih in pogrešanih borcev brigade, 2.127 imen: rojstvo, kdaj so stopili v NOB in v brigado, četa in bataljon, dolžnost, kdaj in kje so padli in kje so pokopani (str. 331–442). Podatke je zbral in uredil Slobodan Spegar Spego.',
    'pionirska-ceta':
      'Seznam borcev čete, ki jo je avtor vodil kot komandir: rojstvo, kdaj je kdo postal borec, dolžnost v četi in življenje po vojni (str. 125–132).',
    'zbornik-heroja-1957':
      'Portreti narodnih herojev, razglašenih do leta 1957: rojstvo, pot v NOB, smrt ali življenje po vojni in dan razglasitve. Knjiga ne pripada eni enoti: portret je dodan zapisu vsakega heroja, ki je na strani in za katerega je zanesljivo, da je to on.',
    'narodni-heroji-1982-1':
      'Življenjepisi vseh narodnih herojev, druga izdaja (1982), 1. zvezek (A–M): rojstvo, življenje pred vojno, pot v NOB, smrt ali življenje po vojni in dan razglasitve. Knjiga ne pripada eni enoti: življenjepis je dodan zapisu vsakega heroja, ki je na strani in za katerega je zanesljivo, da je to on.',
    'narodni-heroji-1982-2':
      'Življenjepisi vseh narodnih herojev, druga izdaja (1982), 2. zvezek (N–Ž): rojstvo, življenje pred vojno, pot v NOB, smrt ali življenje po vojni in dan razglasitve. Knjiga ne pripada eni enoti: življenjepis je dodan zapisu vsakega heroja, ki je na strani in za katerega je zanesljivo, da je to on.',
    'trebinjci-pali':
      'Spominska knjiga Zveze borcev Trebinje (1974): borci z območja občine, ki so padli v vojni (str. 13–96), in borci iz vse Jugoslavije, padli pri Trebinju (str. 159–174), z rojstvom, enotami in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznama žrtev fašističnega terorja iz iste knjige nismo vnesli.',
    'pali-za-lepsa-svitanja':
      'Pripovedujejo matere narodnih herojev o svojih sinovih in hčerah (1967); nad vsako zgodbo je kratek življenjepis heroja: rojstvo, poklic, KPJ, NOB, smrt in dan razglasitve. Knjiga ne pripada eni enoti: življenjepis je dodan zapisu vsakega heroja, ki je na strani in za katerega je zanesljivo, da je to on.',
    'ofanziva-1942-poginuli':
      'Seznam borcev 1., 2., 3. in 4. proleterske brigade, ki so padli ali izginili na pohodu v zahodno Bosno od 24. junija do 30. septembra 1942 (str. 698–711), po brigadah in bataljonih, z rojstvom, poklicem in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hak-20-gospic-perusic':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 20): padli borci z območja okrajev Gospić in Perušić 1941–1945 (str. 986–1045) in nosilci Partizanske spomenice 1941 (str. 1194–1209), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-10-korenica-udbina':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 10): padli borci z območja okrajev Korenica in Udbina 1941–1945 (str. 990–1039), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hronika-prigrevica':
      'Monografija vasi Prigrevica pri Apatinu (1997), kamor so se po vojni naselile družine borcev iz Like in Banije: padli, umrli in pogrešani borci NOB iz teh družin (str. 307–331) in nosilci Partizanske spomenice 1941 (str. 339–353), z rojstvom, enoto in smrtjo ali življenjem po vojni. Seznamov borcev, ki so v vojno stopili pozneje, samo z imeni, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-medak':
      'Monografija vasi nekdanje občine Medak pri Gospiću (2004): borci NOB iz teh vasi, ki so padli v boju s sovražnikom, po vaseh (str. 434–465), in nosilci Partizanske spomenice 1941 (str. 506–513), z rojstvom, enoto in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-hasani':
      'Monografija vasi Hašani pri Bosanski Krupi (1991): padli, umrli in pogrešani borci NOB iz vasi (str. 135–138), nosilci Partizanske spomenice 1941 (str. 138) in drugi preživeli udeleženci NOB, samo z imeni (str. 139). Preživelih, ki jim je bil borčevski staž priznan za delo za NOG, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-podgocka-naselja':
      'Monografija vasi pod Gočem pri Trsteniku (2008): borci iz Gornjega Ribnika, padli na sremski fronti (str. 194–195), in udeleženci NOB iz Odžakov, ki so padli ali izginili v vojni (str. 344–345). Seznamov tistih, ki so jih ubili četniki, in žrtev fašističnega terorja nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-prekopcelica':
      'Monografija vasi Prekopčelica pri Lebanu (2012): borci iz vasi po brigadah in odredih NOVJ, v katerih so bili (str. 121–124), in padli v partizanih (str. 126). Pripadnikov zalednih enot in udeležencev, ki so jih navedli le sorodniki, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-brezovica-stublica':
      'Monografija vasi Brezovica in Stublica pri Trsteniku (2015): udeleženci NOB iz Brezovice, mobilizirani oktobra 1944, ter padli in pogrešani v vojni (str. 113–115), in udeleženci NOB iz Stublice (str. 478–479). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-makce':
      'Monografija vasi Makce pri Velikem Gradištu (2000): vaščani, ki so v vojni padli, umrli ali izginili, večinoma borci 25. divizije (str. 62–64), in udeleženci NOB, ki so vojno preživeli, z letom rojstva in odlikovanjem (str. 64–66). Žrtev fašističnega terorja z istega seznama nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-donje-vidovo':
      'Monografija vasi Donje Vidovo pri Paraćinu (1997): s seznama padlih vaščanov smo vnesli le tiste, ki jih knjiga beleži kot udeležence NOB (str. 127), ne pa žrtev fašističnega terorja in drugih padlih. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-petrlas':
      'Monografija vasi Petrlaš pri Dimitrovgradu (2001): borci iz Petrlaša v Prvi caribrodski, 8., 10. in 12. srbski brigadi, 13. dopolnilnem bataljonu in drugih enotah NOVJ (str. 348). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-labukovo':
      'Monografija vasi Labukovo pri Svrljigu (2007): vaščani, padli v NOB od 1941 do 1945 (str. 44); tistih, ki jih knjiga navaja kot talce, žrtve terorja in taboriščnike, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-beli-breg':
      'Monografija vasi Beli Breg pri Aleksincu (2009): vaščani, udeleženci NOB, z letom rojstva, dnem vstopa v enoto in enoto, ter padli in umrli takoj po vojni (str. 113–114). Ujetnikov, interniranih in vojakov jugoslovanske vojske iz iste tabele nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hronika-donja-gorevnica':
      'Monografija vasi Donja Gorevnica pri Čačku (1996): s seznama padlih borcev in žrtev iz vasi smo vnesli le borce (str. 233–238), ne pa žrtev terorja in vojakov jugoslovanske vojske. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'ostrvica':
      'Monografija vasi Ostrvica pri Gospiću (2003): popis gospodinjstev v vasi s spremembami med vojno (str. 617–663), vsak član družine in kaj se je z njim zgodilo. Vnesli smo le borce, tiste, za katere zapis pravi, da so bili borci, ali navaja vojaško dolžnost ali enoto; civilistov, žrtev terorja in pripadnikov vojske NDH nismo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'divoselo':
      'Monografija vasi Divoselo, Čitluk in Ornice pri Gospiću: padli borci in oficirji teh vasi 1941–1945, vsak s kratkim življenjepisom (str. 425–435). Dveh vojakov jugoslovanske vojske, padlih v aprilski vojni, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'mogoric':
      'Monografija vasi Mogorić v Liki: 110 padlih borcev vasi s spominske plošče na Domu spominov, vsak s kratkim življenjepisom (str. 191–199), in nosilci Partizanske spomenice 1941 iz vasi (str. 201). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'vrebac':
      'Monografija vasi Vrebac, Zavođe in Pavlovac pri Gospiću: padli borci NOB teh vasi od 1941 do 1945, po vaseh, vsak s kratkim življenjepisom (str. 298–311). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'licko-petrovo-selo':
      'Vojna kronika nekdanje občine Ličko Petrovo Selo (1985): padli borci po vaseh (Ličko Petrovo Selo, Novo Selo, Željava, Arapov Do, Rešetar, Zaklopača in Lisina, Donji Vaganac), v tabeli z letom rojstva, vstopa v NOV in smrti, krajem smrti, enoto in dolžnostjo (str. 207–214). Umrlih za tifusom, od lakote in min nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'bosansko-grahovo':
      'Padli borci narodnoosvobodilne vojne z območja Bosanskega Grahova, po vaseh, vsak s kratkim življenjepisom (str. 642–697). Seznama žrtev fašističnega terorja, ki sledi, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'staromajdansko':
      'Padli borci in žrtve fašističnega terorja z območja Starega Majdana pri Sanskem Mostu, po vaseh, vsak s kratkim življenjepisom (str. 177–246), ter seznami umrlih in živih borcev in udeležencev vojne leta 1983 in nosilcev Partizanske spomenice 1941, le imena (str. 247–266). Vnesli smo padle borce in nosilce spomenice; borci in udeleženci vojne s seznamov imen so označeni kot udeleženci, ker seznam ne pove, kdo je bil borec in kdo aktivist; žrtev terorja nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'han-pijesak':
      'Borci občine Han Pijesak in tisti, ki so padli na njenem območju: padli v Pjenovcu 21. januarja 1942 in v drugi sovražni ofenzivi, večinoma borci Prve proletarske brigade (str. 106–109), narodni heroji in vidni udeleženci NOB (str. 147–150) ter padli borci 1941–1945, vsak s kratkim življenjepisom (str. 151–161). Vneseni so tudi, označeni kot aktivisti, partijski in terenski delavci, ki jih seznam šteje med padle. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'skakavac':
      'Borci in udeleženci NOB iz vasi Skakavac pri Bosanskem Petrovcu: prvoborci, nosilci Partizanske spomenice 1941 (str. 163–165), udeleženci NOV, ki so preživeli vojno (str. 166–173), in padli borci (str. 173–177), vsak s kratkim življenjepisom, ter člani narodnoosvobodilnih odborov, odborov AFŽ, mladinske organizacije in KPJ, le imena (str. 181–191), vneseni kot aktivisti. Preživeli, za katere življenjepis pove le, da so bili udeleženci NOV, so označeni kot udeleženci. Žrtve terorja in eden, ki je leta 1943 prestopil k četnikom, niso vneseni. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'zitoradje':
      'Udeleženci NOV iz Žitorađa pri Vladičinem Hanu, le imena (str. 86), ranjeni in padli borci iz vasi (str. 86–88) ter borci srbskih brigad, padli ob osvoboditvi vasi septembra in oktobra 1944, vsak s kratkim življenjepisom (str. 89–91). Žrtve fašističnega terorja niso vnesene. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'brod-crna-trava':
      'Priloga III, padli 1941–1945 iz vasi Brod pri Crni Travi, preglednica z mahalo, datumom in krajem smrti ter enoto (str. 808–809). Vneseni so le tisti, za katere preglednica navaja enoto, saj so med drugimi tudi civilne žrtve. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'revolucionarno-grahovo':
      'Borci iz Grahova pri Nikšiću, padli v NOV in revoluciji 1941–1945, vsak s kratkim življenjepisom (str. 93–128), in padli narodni heroji (str. 81–91). Vneseni so tudi, označeni kot aktivisti, pripadniki gibanja, ki so umrli v zaporih in taboriščih, od žrtev fašističnega terorja (str. 129–133) pa le aktivisti in borci. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'kolasin':
      'Padli v NOV in revoluciji z območja Kolašina, vsak s kratkim življenjepisom (str. 683–724), in nosilci Partizanske spomenice 1941 z dolžnostjo, ki so jo imeli ob koncu vojne (str. 732–743). Aktivisti gibanja so označeni kot aktivisti, padli, za katere življenjepis pove le, da so bili v NOG, pa kot udeleženci; od žrtev fašizma in vojne (str. 726–731) so vneseni le borci. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'bozice':
      'Borci iz Božića pri Andrijevici po bratstvih, le imena, kot jih avtor šteje po Konvenciji o borcu (str. 316–317), nosilci Partizanske spomenice 1941 (str. 317) in padli kot borci ali sodelavci NOGJ (str. 318–319). Padli pripadniki četniškega gibanja niso vneseni. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'otocac-brinje':
      'Seznam padlih borcev, žrtev fašističnega terorja ter preživelih borcev in dejavnih udeležencev NOB nekdanje občine Otočac, po vaseh: padli borci (str. 411–433) ter preživeli borci in dejavni udeleženci NOB (str. 461–531), z rojstvom, vstopom v NOB in dolžnostjo. Vnesli smo tudi dejavne udeležence, politične delavce, odbornike ter člane SKOJ in AFŽ, označene kot aktivisti; žrtev terorja nismo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'hak-14-donji-lapac':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 14): padli borci z območja okraja Donji Lapac 1941–1945 (str. 1041–1094), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-13-gracac':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 13): padli borci z območja okraja Gračac 1941–1945 (str. 917–965), po občinah, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-7-plascanska-dolina':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 7): padli borci iz Plaščanske doline in okolice 1941–1945 (str. 689–701), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'krusevac-1944-poginuli':
      'Seznam borcev, padlih v bojih za osvoboditev Kruševca septembra in oktobra 1944, po enotah: 4. proleterska črnogorska, 3., 6. in 17. srbska brigada ter Poveljstvo kruševačkega vojnega področja (str. 273–283), z rojstvom in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'u-rovovima-srema-poginuli':
      'Seznam borcev, padlih na sremski fronti (str. 230–267), po brigadah in krajih, kjer so padli, samo imena, včasih z dolžnostjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on, po imenu, brigadi in kraju smrti.',
    'sremski-front-poginuli':
      'Seznami borcev, padlih na sremski fronti od oktobra 1944 do aprila 1945, po divizijah in brigadah, vsak za kratko zgodovino enote: samo imena, včasih z očetovo začetnico. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on, po imenu, brigadi in času smrti. Seznamov padlih rdečearmejcev s konca knjige nismo vnesli.',
    'bitka-kod-oborova-poginuli':
      'Imena 128 borcev 2. moslavaške brigade in Posavskega partizanskega odreda, padlih pri Oborovem 29. marca 1944 (str. 158–160). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'zrtve-rata-1964-slo':
      'Popis žrtev vojne iz leta 1964 z območja Slovenije, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-hrv':
      'Popis žrtev vojne iz leta 1964 z območja Hrvaške, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-bih':
      'Popis žrtev vojne iz leta 1964 z območja Bosne in Hercegovine, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-crg':
      'Popis žrtev vojne iz leta 1964 z območja Črne gore, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-mak':
      'Popis žrtev vojne iz leta 1964 z območja Makedonije, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-srb':
      'Popis žrtev vojne iz leta 1964 z območja ožje Srbije, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-kos':
      'Popis žrtev vojne iz leta 1964 z območja Kosova in Metohije, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    'zrtve-rata-1964-voj':
      'Popis žrtev vojne iz leta 1964 z območja Vojvodine, po občinah in vaseh: vneseni so le borci NOB, ki so padli ali umrli v vojni, ne žrtve terorja. Popis ne pripada eni enoti: zapis iz njega je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci. Popis je objavil Muzej žrtev genocida.',
    '6-istocnobosanska-dopuna':
      'Borci brigade, katerih podatki niso bili objavljeni v knjigi „Borbeni put Šeste proleterske brigade“ (1977), zbrani do leta 1981: rojstvo, vstop v NOB, dolžnost, usoda; in borci, za katere kraj in čas smrti nista ugotovljena (str. 676 in naprej)',
    '7-banijska-poginuli':
      'Nepopoln seznam v vojni padlih in umrlih pripadnikov brigade: rojstvo, narodnost, poklic, vstop v NOVJ, bataljon, kje in kdaj so padli (str. 394–462)',
    '15-majevicka-spisak':
      'Narodni heroji brigade in seznam vseh njenih borcev: leto in kraj rojstva, narodnost, poklic, vstop v NOB in prihod v brigado, usoda (str. 484–557)',
    'beogradski-bataljon':
      'Vsi borci Beograjskega bataljona od prvih dni vstaje do 1. marca 1945, ko je postal 3. bataljon Prve proletarske, po času prihoda v bataljon: poklic, rojstvo, članstvo v KPJ in SKOJ, kaj se je komu zgodilo v vojni',
    '1-dalmatinska-monografija':
      'Komandirji in politični komisarji čet po bataljonih, življenjepisi narodnih herojev brigade in seznam v vojni padlih borcev, isti kot na znaci.org, tukaj s skenirano knjigo',
    '4-brigada-slavonije':
      'Seznam padlih borcev in starešin brigade (četa in dolžnost, datum in kraj rojstva, datum in kraj smrti) ter seznam ranjenih (enota in dolžnost, kdaj so bili ranjeni), prilogi 2 in 3 knjige (str. 164 in naprej)',
    '4-brigada-slavonije-rukovodioci':
      'Voditelji štaba brigade in enot pri štabu ter štirih bataljonov, od komandanta do vodnika, po dolžnostih, s tem, od kod so bili in kdaj so opravljali dolžnost, ter tovariši na raznih dolžnostih v brigadi, priloga 1 knjige (str. 177–182)',
    '9-dalmatinska-divizija':
      'Borci in starešine divizije, ki so padli ali izginili v bojih od 11. februarja do 15. aprila 1943, imena z očetovim imenom (str. 121–126)',
    '3-dalmatinska-poginuli':
      'Padli in pogrešani borci in starešine 3. samostojne dalmatinske brigade od 14. aprila do 6. junija 1943, imena z očetovim imenom (str. 126–128)',
    '12-slavonska-zene':
      'Seznam bork 12. proletarske slavonske brigade, padlih, umrlih in preživelih, s kratkimi življenjepisi (besedilo na znaci.org, brez skenirane knjige; seznama vseh borcev brigade, ki ga knjiga napoveduje, ni bilo)',
    'zagrebacki-odred':
      'Seznam borcev odreda iz zbornika dokumentov in spominov (str. 407–418): večinoma preživeli, ki so se po vojni prijavili pri SUBNOR v Zelini, in padli, ki jih omenjajo vojni dokumenti in spomini; vas, občina in usoda. Bataljonov, ki so v celoti odšli v brigado „Matija Gubec“ in v Zagorsko brigado, v njem ni.',
    'mosorski-odred':
      'Seznam borcev Mosorskega partizanskega odreda 1942–1944 (prvi del seznama, str. 355–562): I. mosorski odred, Mosorski bataljon, Leteča mosorska četa in odred od oktobra 1943 do novembra 1944, z rojstvom, poklicem, prihodom v odred in usodo. Drugi del seznama, borci komand mest in terenski delavci, ni vnesen.',
    'mosorski-odred-2':
      'Drugi del seznama iz iste knjige (str. 573–648): borci komand mest ter partijsko-politični in terenski delavci s področja Mosorja. V seznamu odreda so borci, tisti, za katere zapis pravi, da so bili borci, ali navaja vojaško dolžnost ali enoto vojske, in pripadniki delovnih bataljonov. Terenski in politični delavci, odborniki in članice AFŽ so vneseni kot aktivisti, vsak k zapisu borca, ki je na strani, če je to on, drugi med Drugimi borci.',
    'mosorski-odred-kader':
      'Vodstvo odreda 1942–1944, po dolžnostih, od komandantov odreda do komandirjev vodov, vodnih delegatov in četnih bolničark, samo imena (str. 563–568)',
    'turopoljsko-posavski-odred':
      'Seznam padlih borcev odreda (99, s krajem rojstva, datumom in krajem smrti) ter ustreljeni in umrli borci odreda med vojno (16), str. 17–20 (Muzej Turopolja, Velika Gorica 1983)',
    'zascitna-enota-vpv':
      'Pripadniki zaščitne enote vojaško-političnega vodstva NOB Slovenije, ki so preživeli vojno, z datumom in krajem rojstva in bazami, v katerih so služili, nato padli borci, narodni heroji in nosilci Partizanske spomenice 1941 (str. 293–310).',
    'hak-19-vojnic':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 19): padli borci z območja okraja Vojnić 1941–1945 (str. 1123–1177), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-18-slunj-veljun':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 18): padli borci z območja okrajev Slunj in Veljun 1941–1945 (str. 921–977), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-15-duga-resa':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 15): padli borci z območja sedanje občine Duga Resa 1941–1945 (str. 1060–1090), po občinah in vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom iz iste knjige nismo vnesli.',
    'hak-12-dreznica':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 12): padli borci z območja občine Drežnica 1941–1945 (str. 865–876), po vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznama žrtev fašističnega terorja in vojne iz iste knjige nismo vnesli.',
    'hak-16-gornje-dubrave':
      'Iz zbornika Zgodovinskega arhiva v Karlovcu (knj. 16): padli borci z območja občine Gornje Dubrave 1941–1945 (str. 889–899), po vaseh, z rojstvom, potjo v NOB in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznama žrtev fašističnega terorja in vojne iz iste knjige nismo vnesli.',
    'sjenicak':
      'Kronika kordunske vasi, ki jo je izdal Zgodovinski arhiv v Karlovcu, z dvema njenima seznamoma: padli in umrli borci 1941–1945 iz Donjega, Gornjega in Lasinjskega Sjeničaka (str. 330–338), po vaseh, z rojstvom, potjo v NOB in smrtjo, ter nosilci Partizanske spomenice 1941 (str. 385–389). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Seznamov žrtev fašističnega terorja in umrlih za tifusom in prehladom iz iste knjige nismo vnesli.',
    'tuzla-spomen-knjiga':
      'Spominska knjiga občine Tuzla: življenjepisi njenih udeležencev NOB, ki so padli v letih 1941–1945 (str. 13–300), rojenih, živečih ali zaposlenih v Tuzli ali takih, ki so od tam odšli v partizane, pogosto s fotografijo, z enoto, rojstvom in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on. Drugega dela knjige, žrtev fašističnega terorja, nismo vnesli.',
    'jajce-1941-poginuli':
      'Iz zbornika spominov o jajškem območju (knj. I): seznam borcev z jajškega območja, padlih leta 1941, z rojstvom, enoto in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'jajce-1942-poginuli':
      'Iz zbornika spominov o jajškem območju (knj. II): seznam borcev in aktivistov NOG z jajškega območja, padlih leta 1942, z rojstvom, enoto in smrtjo. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'spomenica-crnogorskim-antifasistima':
      'Seznam črnogorskih antifašistov, padlih in umrlih v letih 1941–1945, po občinah, v tabeli: ime, očetovo ime, leto in kraj rojstva, leto smrti in kraj smrti. Vsi, ki jih knjiga navaja, so šteti za partizane: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on, drugi so med drugimi borci.',
    'moste-polje-spomenica-1941':
      'Nosilci partizanske spomenice 1941 z območja današnje občine Moste-Polje v Ljubljani, iz arhiva CK ZKS (str. 257–260): ime, letnica rojstva in poklic, za tiste, ki so umrli po vojni, tudi letnica smrti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'vis-spomenica-1941':
      'Nosilci partizanske spomenice 1941 z viškega otočja (str. 521), samo imena, in stavek knjige o narodnem heroju Andriji Božaniću. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca z otoka, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'prilog-u-krvi-pali-borci':
      'Padli borci NOB iz pljevaljskega okraja od aprila 1941 do 15. maja 1945 (str. 141–216), z življenjepisom vsakega. Knjiga med padle borce šteje tudi partijske in politične delavce, odbornike in sodelavce NOG: vneseni so tudi ti, označeni kot aktivisti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'jevreji-jugoslavije-ucesnici-nor':
      'Seznam judovskih udeležencev narodnoosvobodilne vojne, z življenjepisom vsakega (str. 307 in dalje). Seznam šteje vse, ki so bili v NOG: vneseni so vsi, politični in zaledni delavci ter tisti, ki so jih ujeli na poti k partizanom, pa so označeni kot aktivisti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'hrvatsko-zagorje-1981':
      'Seznam padlih udeležencev NOB 1941–1945 z območja občin Donja Stubica, Ivanec, Klanjec, Krapina, Pregrada, Zabok, Zaprešić in Zlatar-Bistrica, z rojstvom, enoto in smrtjo. Seznam skupaj navaja borce in žrtve fašističnega terorja; vneseni so borci in, označeni kot aktivisti, člani KPJ, SKOJ in NOO, politični delavci in kurirji, žrtve terorja pa ne. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'imotska-krajina-pali-borci':
      'Padli borci in žrtve fašističnega terorja po vaseh Imotske krajine (str. 163–472), z rojstvom, potjo v NOV in smrtjo. Vneseni so padli borci iz dela, ki ga knjiga za vsako vas naslovi »Poginuli borci«, skojevci, komunisti in politični delavci, ki jih knjiga tam šteje, pa so označeni kot aktivisti; žrtev terorja nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'knjazevac-pomenik':
      'Vsi, ki so umrli v drugi svetovni vojni z območja občine Knjaževac, po vaseh (str. 37–327), z rojstvom in smrtjo: partizani, četniki, ustreljeni in civilisti skupaj. Vneseni so partizanski borci in, označeni kot aktivisti, komunisti, skojevci, odborniki in sodelavci partizanov; četniki, civilisti in tisti, ki jih je obsodila nova oblast, niso. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'iskra-in-plamen-padli':
      'Iz zbornika o NOB v vaseh nekdanje občine Polje pri Ljubljani: „Svoja življenja so dali za svobodo”, umrli iz teh vasi po vaseh, z letnicama rojstva in smrti ter krajem smrti. Vneseni so le padli v NOV; umrli v internaciji in zaporih, talci in ostale žrtve niso. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'cazinska-krajina-pali-borci':
      'Seznam padlih borcev Cazinske krajine, po občinah (Bihać, Bosanska Krupa, Cazin, Velika Kladuša) in vaseh, z očetovim imenom ter letnicama rojstva in smrti. Seznam srbskih civilnih žrtev iz iste knjige ni vnesen. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'derventa-pali-borci':
      'Seznam padlih borcev narodnoosvobodilne vojne z območja občine Derventa, z rojstvom, enoto in krajem smrti. Seznam žrtev fašističnega terorja iz iste knjige ni vnesen. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'sanski-most-borci':
      'Seznami borcev sreza Sanski Most po naseljih: padli v NOB, nosilci Partizanske spomenice 1941 in borci NOB, živi 15. maja 1945, z rojstvom, poklicem, vstopom v NOB in dolžnostjo. Iz tretjega seznama so vneseni borci (borec, vojaška dolžnost ali čin, enota) in, označeni kot aktivisti, odborniki ter člani SKOJ in AFŽ brez vojaške dolžnosti; žrtve fašističnega terorja niso. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'rat-i-djeca-kozare':
      'Iz knjige o otrocih Kozare v vojni, poglavje „Pali kao borci narodnooslobodilačkog rata”: 370 kozarskih dečkov in deklic, mlajših od 15 let, ki so padli kot borci, po občinah, s krajem in letnicama rojstva in smrti (besedilo na znaci.org, brez skenirane knjige). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'krizani-v-boju-za-svobodo':
      'Knjiga o ljudeh vasi Križ pri Trstu v vojni: življenjepisi padlih (vneseni so tisti, ki so bili v partizanih ali v vojski, in, označeni kot aktivisti, aktivisti Osvobodilne fronte in terenci), in tabeli Križanov v NOVJ in borcev NOV, ki so živeli v Križu, z očetom, rojstvom, vstopom v NOV, činom in enoto. Prostovoljci v Španiji, Križani v italijanskih enotah in deportiranci niso vneseni. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'vinodolska-selca':
      'Iz prilog knjige o Selcah pri Crikvenici v vojni: seznam borcev iz Selc, padlih v NOB, z dolžnostjo, enoto, rojstvom in smrtjo, ter prvoborci in nosilci Partizanske spomenice 1941. Vneseni so tudi, označeni kot aktivisti, sodelavci NOG, pogubljeni v taboriščih. Seznam organiziranih udeležencev NOB (le imena, s članicami AFŽ in odborniki) in seznami žrtev niso vneseni. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'susak-rijeka-spomenica':
      'Iz prilog knjige o Sušaku in Reki v NOB: nosilci Partizanske spomenice 1941 z območja občine Reka, ime in kraj, kot jih je sestavil občinski odbor ZZB. Seznama članov KPJ in SKOJ iz leta 1941, padlih v NOB, nista vnesena, ker ne povesta, kdo je bil borec. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'zene-vi-korpus-poginule':
      'Iz zbornika dokumentov o ženah Hrvaške v NOB (dokument 427): seznam padlih tovarišic borcev in voditeljic v enotah VI. korpusa NOVJ, ki ga je štab korpusa sestavil 23. decembra 1944, z dolžnostjo in enoto, letom in krajem rojstva ter tem, kdaj in v katerem boju je padla. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'ludbreg-poginuli':
      'Seznami borcev, padlih v dveh bojih za Ludbreg: 17. slavonske brigade v Ludbregu in Šemovcu 3. oktobra 1943, brigade »Braća Radić« pri Šemovcu istega dne in 17. slavonske v Ludbregu 6. julija 1944 (str. 84–85, 287–289), z letom in krajem rojstva. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'dolomiti-v-nob-3':
      'Narodni heroji Dolomitov, hribovja zahodno od Ljubljane, nosilci spominskega znaka 1941 in padli prvoborci, z datumom in krajem rojstva (str. 667–671). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'sanitetska-sluzba-lekari':
      'Zdravniki, ki so izgubili življenje v vojni, s kratkim življenjepisom: od kod so bili, kdaj so vstopili v NOVJ, dolžnost in enota, smrt (besedilo na znaci.org, brez skenirane knjige). Vpisani so tisti, ki so bili v vojski, zdravniki, ki so jih kot sodelavce gibanja ubili v zaledju (organizirali so vstajo, skrivali in zdravili partizane), pa so označeni kot aktivisti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'korosko-zdravstvo':
      'Ranjeni in bolni borci in aktivisti na Koroškem do februarja 1944, pacienti koroških partizanskih bolnišnic, koroški borci, ki so se zdravili izven bolnišnic, in sanitetno osebje, s kratkim življenjepisom (str. 282–355). Vpisani so borci in osebje partizanskih bolnišnic, politični delavci na terenu ter zdravniki in medicinske sestre, ki so partizanom pošiljali zdravila, pa so označeni kot aktivisti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'artileristi-prekomorci':
      'Seznam padlih artileristov prekomorcev, Slovencev in Istranov, ki so iz Italije in Afrike prišli v artilerijske enote, ustanovljene na Visu in v Italiji, in seznam vodilnega kadra teh enot (str. 227–234). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'virovitica-spomenica-1941':
      'Nosilci partizanske spomenice 1941 iz občine Virovitica, štirinajst življenjepisov s fotografijami (str. 221–239). Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'vis-zrtve-nob':
      'Žrtve NOB s spominskih plošč viškega otočja (str. 516–520): padli v bojih in umrli zaradi ran in bolezni iz Visa, Komiže, Biševa, Oključne in vasi pod Humom, samo ime in očetovo ime. Talci, ki so jih Italijani ustrelili leta 1943, in umrli v ustaških zaporih niso vpisani. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca z otoka, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'xxxi-divizija-stabi':
      'Štabi XXXI. divizije ter Gradnikove, Prešernove in Vojkove brigade (str. 557–562): komandanti, komisarji, njihovi namestniki in načelniki štaba, vsak s časom, ko je bil na dolžnosti, in kdo od njih je padel. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    '15-brigada-stabi':
      'Komandanti, politični komisarji, njihovi namestniki in načelniki štaba 15. brigade ter komandanti in komisarji njenih bataljonov (str. 447–450), vsak s časom, ko je bil na dolžnosti, in kjer se je dolžnost tako končala, da je bil ranjen, je zbolel ali padel. Brigade ni na strani: zapis iz knjige je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    '15-divizija-stabi':
      'Poveljniška sestava 15. divizije NOV in POS (str. 583–584): komandanti, politični komisarji, njihovi namestniki in pomočniki ter načelniki štaba, vsak s časom, ko je bil na dolžnosti. Divizije ni na strani: zapis iz knjige je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'jb-odred-stabi':
      'Štabi Jeseniško-bohinjskega odreda, njegovih treh bataljonov in šolskega taborišča, avgust 1944 – maj 1945 (str. 354–356): komandanti, politični komisarji, njihovi pomočniki in namestniki ter načelnik štaba, vsak s časom, ko je bil na dolžnosti. Odreda ni na strani: zapis iz knjige je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'banijski-odredi-kadar':
      'Starešine banijskih partizanskih odredov 1941–1945 (str. 372–378): malih odredov in vaških skupin borcev 1941, Banijskega partizanskega odreda in njegovih bataljonov, udarnih bataljonov, partizanskih čet in dveh odredov Banije 1944, po dolžnostih. Odredov ni na strani: zapis iz knjige je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'letalci-prekomorci-kader':
      'Vodilni kader 1. in 2. lovske eskadrilje NOVJ, letalskega detašmana NOVJ v Alžiriji in 1. letalskega polka (str. 322–325): čin in dolžnost vsakega, s časom, ko jo je opravljal. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'niksicki-odred-pali-borci':
      'Imena padlih borcev z območja nekdanjega nikšiškega okraja in občine Herceg Novi (str. 393–420): kraj in leto rojstva, kraj in leto smrti; ter narodni heroji Nikšića in Herceg Novega, z življenjepisom vsakega (str. 423–427). Skoraj vsi so šli skozi Nikšićki odred, padli pa so v brigadah, v odredu in na drugih dolžnostih. Strani na znaci.org nimajo besedila, le slike: imena so prebrana s slik. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'teslic-u-nob-borci':
      'Seznam borcev narodnoosvobodilne vojne občine Teslić (str. 234–267) in seznam padlih in umrlih borcev (str. 269–279), z življenjepisom vsakega. Seznama ob borcih štejeta tudi odbornike in sodelavce NOG: vneseni so le tisti, za katere zapis pravi, da so bili borci ali v NOVJ, ali navaja vojaško dolžnost ali enoto vojske. Strani na znaci.org nimajo besedila, le slike: imena so prebrana s slik. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'lovcenski-odred-pali-borci':
      'Padli, ustreljeni in umrli borci NOB 1941–1945 z ozemlja Lovćenskega partizanskega odreda, po okrajih (cetinjski, barski, kotorski) in vaseh, z življenjepisom vsakega (str. 611–713). Avtor med padle borce šteje vse iz gibanja, ki so izgubili življenje, tudi aktiviste, žrtev terorja pa ne; vneseni so vsi. Strani na znaci.org nimajo besedila, le slike: imena so prebrana s slik. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on; drugi so med Drugimi borci.',
    'zene-1-dalmatinska':
      'Seznam bork brigade iz let 1944–1945 (dokument 368): dolžnost in čin, datum in kraj rojstva, kdaj so vstopile v NOV, odlikovanja in mnenje štaba o vsaki',
    '1-dalmatinska-komandni-sastav':
      'Komandanti, komisarji, njihovi namestniki, načelniki štaba, intendanti, referenti saniteta, mladinski voditelji in obveščevalni častniki štaba brigade in vsakega bataljona od 6. septembra 1942 do konca vojne, s časom, ko je kdo opravljal dolžnost (str. 435–443)',
    '1-dalmatinska-formiranje':
      'Starešine štaba brigade, političnega oddelka, bataljonov in čet 6. septembra 1942 v vasi Dobro pri Livnu: dolžnost, leto rojstva, narodnost, poklic (str. 55–58)',
    'zene-11-dalmatinska':
      'Seznam bork brigade iz let 1944–1945 (dokument 376): datum in kraj rojstva, dolžnost in čin, kdaj so vstopile v NOV, odlikovanja in mnenje štaba o vsaki',
    '11-dalmatinska-stabovi':
      'Starešine štaba brigade s časom, ko je kdo opravljal dolžnost, čet pri štabu, previjališč in podčastniškega tečaja, štabov bataljonov in poveljstev čet, po dolžnostih (str. 611–624)',
    'osjecka-zene':
      'Borke Osiješke brigade po bataljonih, kot jih je štab brigade popisal za I. kongres AFŽ Hrvaške (dokument 420): datum in kraj rojstva, od kdaj so v partizanih',
    'dalmatinci-prva-proleterska':
      'Borci Prve proletarske brigade iz Dalmacije, z življenjepisom vsakega: rojstvo, poklic, pot v NOB in v brigado, boji, usoda; in dodatni seznam tistih, za katere avtorja nista zbrala podatkov (str. 467–754)',
    'crnogorski-bataljon':
      'Borci, ki so v Prvi črnogorski bataljon Prve proletarske vstopili v letih 1942, 1943, 1944 in 1945, ter borci brez popolnih podatkov: rojstvo, poklic, vstop v NOB, usoda; v cirilici (str. 713–795)',
    'rudarska-ceta':
      'Borci Rudarske čete (rudarji Trepče in Kopaonika), ko je 21. decembra 1941 v Rudem vstopila v Prvo proletarsko, z življenjepisom vsakega (str. 426–430)',
    'prva-proleterska-dopunski':
      'Pripadniki brigade, ki jih je uredništvo našlo po seznamu v prvih treh knjigah, s podatki o vsakem (str. 1065–1071)',
    'prva-proleterska-garibaldi':
      'Italijanski vojaki, ki so se po kapitulaciji Italije pridružili partizanom, s štabom bataljona, samo imena in dolžnosti (str. 1072–1082)',
    'kotor-varos':
      'Seznama padlih, umrlih in pogrešanih udeležencev NOB občin Kotor-Varoš in Skender-Vakuf po krajevnih organizacijah SUBNOR (str. 333–354), z rojstvom, enoto in smrtjo, ter nosilci Partizanske spomenice 1941 obeh občin (str. 357). Vneseni so tudi udeleženci, ki niso bili borci, označeni kot aktivisti ali udeleženci. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'sokolac':
      'Seznam padlih borcev Sokolca v drugi svetovni vojni 1941–1945 (str. 524–571), 503 kratke biografije: rojstvo, vstop v NOV, enota in smrt. Seznama padlih četnikov iz iste knjige nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'popovo-polje':
      'Priloga »Borci iz Popovega polja, padli v NOB« (str. 419–430): rojstvo, dolžnost, kraj in dan smrti. Seznama žrtev fašističnega terorja iz iste knjige nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'bijelo-polje':
      'Priloge monografije: nosilci Partizanske spomenice 1941 (str. 733–753) in padli borci NOB okraja Bijelo Polje (str. 778–886), z rojstvom, enotami in smrtjo. Seznama borcev v stroju Tretje sandžaške brigade na dan ustanovitve (str. 754–774) še nismo vnesli, ker so imena v skenu težko berljiva; ne padlih v aprilski vojni in žrtev terorja. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'lezimir':
      'Članek »Žrtve vasi Ležimir 1941–1945« (str. 95–120): vsi umrli iz Ležimira v Sremu. Vneseni so le borci, tisti, za katere seznam pravi, da so padli v NOB; žrtve terorja in tisti, ki so jih ubili partizani, niso. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'prva-niska-gimnazija':
      'Pregled gimnazijcev raznih generacij, padlih v NOB, in žrtev fašističnega terorja (str. 221–232): padli kot borci partizanskih odredov in NOVJ ter med ubitimi in ustreljenimi tisti, ki so bili v gibanju. Dijakov, ki so umrli v internaciji in v bombardiranju, nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'binovce':
      'Udeleženci NOB iz Binovca in Kalabovca pri Surdulici (str. 24–25), le imena, vneseni kot udeleženci, in pet padlih borcev (str. 26). Internirancev, žrtev terorja in civilnih žrtev nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'kremna':
      'Padli partizanski borci iz Kremne pri Prnjavorju in s spominske plošče v Podvučjaku (str. 134–147), le imena, nosilci Partizanske spomenice 1941 in komandanti partizanskih enot s prnjavorskega območja (str. 171–172). Seznamov četnikov in žrtev iz iste knjige nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'komani':
      'Padli v NOB iz Bandićev, s spominske plošče v Zagaraču (str. 223–224), in vrstice seznamov bratstev o istih borcih. Ustreljenih in žrtev z iste plošče ter padlih v prejšnjih vojnah nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'gornja-jablanica':
      'Narodni heroji in drugi padli borci leta 1941 iz Gornje Jablanice, po vaseh (str. 663–669), in nosilci Partizanske spomenice 1941 (str. 669–673), le imena. Nosilcev Albanske spomenice in Karađorđeve zvezde nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    '2-korpus-stabovi':
      'Seznam poveljniškega sestava štabov divizij in štaba 2. udarnega korpusa (str. 463–465): komandanti, politični komisarji, namestniki in načelniki štabov korpusa, 2. proletarske, 3. udarne, 29. in 37. udarne divizije, Primorske operativne skupine, italijanske divizije »Garibaldi« in topniške brigade korpusa, z meseci na dolžnosti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'moslavina-spomenica-1941':
      'Pregled nosilcev Partizanske spomenice 1941 z območja Moslavine (str. 629–632), le imena in vzdevki: rojeni v Moslavini ali so tam dlje živeli, med njimi tudi voditelji KP, SKOJ, AFŽ in NOO. Odreda ni na strani; ostali so med Drugimi borci.',
    'knezica':
      'Priloge knjige o vaseh Knežice pod Kozaro: padli borci NOB, po vaseh (str. 451–463), z letom rojstva in smrti ter krajem smrti, nosilci Partizanske spomenice 1941 (str. 501–502) in preživeli borci NOB krajevnega območja Knežica (str. 503–508), le imena. Seznama žrtev fašističnega terorja iz iste knjige nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'kordunski-rekvijem':
      'Seznam padlih borcev nekdanje občine Primišlje 1941–1945, ki ga je sestavil general Dušan Livada (str. 176–191), po vaseh, s kratkim življenjepisom; člani Partije in SKOJ, odborniki in članice AFŽ, ki jih seznam šteje, so vneseni kot aktivisti. Vnesenih je tudi prvih 49 nosilcev Partizanske spomenice 1941, ki so se iz Slunja preselili v Vojvodino (str. 338–342). Seznamov žrtev terorja in umrlih za tifusom nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'sencur-padli-borci':
      'Seznam padlih borcev, aktivistov in drugih žrtev fašističnega nasilja z območja občine Šenčur pri Kranju, po vaseh, z življenjepisom (str. 359–368), in seznam borcev Kokrške čete, december 1941 – pomlad 1942, z zadnjim bivališčem in dnem prihoda v četo (str. 381–384). Vneseni so borci in, označeni kot aktivisti, ljudje OF in Partije; talcev, izseljenih in drugih ubitih brez deleža v gibanju nismo vnesli. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
    'klanjscek-komandni-sastav':
      'Priloga 1, »Seznam poveljniškega sestava višjih enot NOV in PO Slovenije« (str. 393–400): komandanti, politični komisarji, njihovi namestniki in načelniki štabov Glavnega štaba, pokrajinskih štabov, skupin odredov, operativnih con, korpusov in divizij, z dnevi na dolžnosti in krajem smrti. Knjiga ne pripada eni enoti: zapis iz nje je dodan zapisu vsakega borca, ki je na strani in za katerega je zanesljivo, da je to on.',
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
    'druga-licka-staresine':
      'Командантите, комесарите, нивните заменици, оперативните и разузнавачките офицери и интендантите на штабот на бригадата и на штабовите на баталјоните од формирањето до крајот на војната, за повеќето со кратка биографија (стр. 349–360)',
    'treca-proleterska-brigada': 'Монографија, библиотека „Ratna prošlost naših naroda“, кн. 144',
    'treca-proleterska-poginuli-knj3':
      'Список на загинатите и починатите борци и старешини по години, 1942–1945 (1.374 имиња; во овој примерок недостасуваат страниците со почетокот на 1944 година)',
    'treca-proleterska-formiranje':
      'Истиот список како во монографијата на Жарко Видовиќ, на кирилица, како што го средила редакцијата на зборникот спомени; по баталјони и чети',
    'ljubljanska-brigada': 'Монографија на Љубљанската бригада',
    '13-proleterska-spisak': 'Список на загинатите и преживеаните борци (трет дел од монографијата)',
    '2-dalmatinska-proleterska': 'Список на борците на 2-ра далматинска пролетерска бригада на НОВЈ',
    '2-dalmatinska-stabovi':
      'Старешините на штабот на бригадата со времето кога кој ја вршел должноста, на четите при штабот, на бригадната болница, на штабовите на баталјоните и на командите на четите, по должности (стр. 473–486)',
    '4-splitska-brigada': 'Список на загинатите и преживеаните борци на бригадата',
    'prva-vojvodjanska': 'Список на борците на Првата војводинска бригада',
    '5-kozaracka': 'Список на загинатите, исчезнатите и починатите борци и старешини на бригадата',
    '2-vojvodjanska': 'Список на борците и старешините на 2-ра војводинска бригада',
    '8-krajiska': 'Список на загинатите и починатите во НОБ од 8-ма краишка бригада',
    '8-krajiska-sjecanja-poginuli':
      'Списокот на загинатите и умрените борци на бригадата од зборникот спомени: татко, година и место на раѓање, кога и каде загинал, должност.',
    '6-krajiska': 'Список на загинатите и починатите борци и старешини на бригадата, со дополнителен список',
    '4-krajiska': 'Список на загинатите, починатите и исчезнатите борци и старешини на 4-та краишка бригада',
    '3-krajiska-proleterska': 'Список на загинатите борци на Третата пролетерска краишка бригада, со основните лични податоци',
    '17-slavonska-poginuli': 'Список на загинатите борци на 17-та ударна бригада',
    '17-slavonska-prezivjeli': 'Список на преживеаните борци на 17-та ударна бригада',
    '25-srpska-divizija': 'Список на загинатите борци и старешини на 25-та дивизија',
    '1-sumadijska': 'Списоци на загинатите борци и старешини и на борците што ја преживеаја војната',
    '18-slavonska': 'Список на загинатите и починатите борци и старешини на 18-та ударна бригада и список на преживеаните борци',
    '4-banijska': 'Список на борците на 4-та банијска бригада',
    '4-banijska-starjesine': 'Командантите, политичките комесари, нивните заменици, началниците на штабот и другите старешини на штабот на бригадата и на штабовите на баталјоните, по должности, само имиња (стр. 52–53)',
    '4-srpska': 'Список на борците на Четвртата српска ударна бригада',
    '7-vojvodjanska': 'Список на борците на 7-ма војводинска ударна бригада (преживеани, загинати и починати по војната)',
    '19-bircanska': 'Список на борците на 19-та бирчанска бригада',
    '2-krajiska': 'Список на загинатите и починатите борци и старешини на 2-ра краишка бригада во НОБ',
    'tuzlanski-odred': 'Список на борците на Тузланскиот партизански одред',
    'uzicki-odred': 'Список на борците на Ужичкиот партизански одред загинати во народноослободителната војна 1941–1945',
    'pozega-cete':
      'Списоците на борците од 1. и 2. пожешка чета на Ужичкиот одред 1941—1942, Пилатовачката чета на денот на формирањето, борците што ги чувале објектите во Пожега, учесниците во НОБ од селата околу Пожега во други единици во 1941, 1. чета на 5. баталјон на Ужичкиот одред во 1944 и загинатите и умрените борци од Пожешката чета на 2. пролетерска бригада, по села; по војната ги составиле преживеаните борци од четите. Списоците на работниците во партизанските работилници, симпатизерите и бегалците не се внесени.',
    '14-srpska': 'Список на загинатите борци и старешини на одредот и на 14-та српска бригада',
    '7-crnogorska-omladinska': 'Список на загинатите борци на 7-ма црногорска младинска бригада',
    '7-crnogorska-zbornik-poginuli':
      'Загинатите борци и старешини на бригадата од зборникот спомени: раѓање, чета и баталјон, кога и каде загинал.',
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
    'prva-proleterska-stroj-u-rudom':
      'Борците што на 21 декември 1941 стоеја во строј во Рудо, по штабови, баталјони и чети: раѓање, занимање, должност и што било со секого во војната (стр. 433–492). Ѕвездичката до името го означува борецот што загинал во војната.',
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
      'Список на загинатите борци и старешини на бригадата, по борбите, од Суќурај на 22 септември 1943 до Илирска Бистрица на 6 мај 1945 (стр. 353–366 од книгата), и прегледот на раководниот кадар на штабот на бригадата и на штабовите на баталјоните, со времето кога кој ја вршел должноста (стр. 339–342)',
    '3-makedonska':
      'Список на загинатите борци на бригадата: од каде се, година на раѓање, каде и кога загинале (стр. 359–368 од книгата)',
    '3-krajiska-spisak-boraca':
      'Список на борците што се бореле во бригадата од 22. 8. 1942 до 9. 5. 1945, преживеани и загинати: од каде се, занимање, кога стапиле во НОБ и во бригадата, должност, судбина; со дополнување и прилог (стр. 579 и натаму)',
    '3-krajiska-sastav-1942':
      'Сите борци и старешини на бригадата во средината на ноември 1942, по штабот, политодделот, интендантурата, баталјоните, четите и водовите: должност, година и место на раѓање, народност, занимање, кај многумина и подоцнежната судбина (текст на znaci.org, без скенирана книга)',
    '6-krajiska-prezivjeli':
      'Список на борците на бригадата што ја преживеаја војната, само имиња, со дополнителен список (стр. 747–762 од книгата)',
    '6-krajiska-kadar':
      'Старешините на бригадата 1942–1943 по должности, од командантите на бригадата до четните болничарки, само имиња (стр. 739–745 од книгата)',
    '32-divizija-borci':
      'Борци на штабот на дивизијата, придружните единици, бригадите „Браќа Радиќ“, „Матија Губец“, „Миховил Павлек Мишкина“ и I ударна загорска, и борци со нецелосни податоци: година и место на раѓање, народност, занимање, кога стапиле во НОВ, судбина; борецот е наведен во секоја единица во која се борел (стр. 431–662 од книгата)',
    '32-divizija-kadar':
      'Старешините на штабот на дивизијата и единиците при штабот, на нејзините четири бригади, нивните баталјони и придружни чети, по должности (стр. 286–295)',
    '18-hrvatska':
      'Список на борците на бригадата, преживеани и загинати: година и место на раѓање, народност, занимање, кога стапиле во бригадата, должност, судбина (стр. 582–696 од книгата)',
    '18-hrvatska-starjesine':
      'Старешините на штабот на бригадата, на баталјоните и четите и на единиците при штабот, по должности, само имиња (стр. 573–581 од книгата)',
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
    '4-proleterska-formiranje':
      'Списокот на борците и старешините на денот на формирањето на бригадата, 17 јуни 1942, по штабови, баталјони и чети: должност, место и година на раѓање, занимање, членство во КПЈ и СКОЈ и што се случило со него.',
    '3-vojvodjanska':
      'Списоци на борците и старешините на бригадата: загинати, оние чија судбина остана неутврдена, и преживеани (стр. 479 и натаму)',
    'kalnicki-odred':
      'Список на борците на Калничкиот партизански одред, загинати и преживеани (стр. 311 и натаму)',
    'kalnicki-odred-kadar':
      'Раководителите на првите вооружени групи и формации на Калник 1941–1942, на штабот на одредот, неговите баталјони, чети и водови, со времето кога кој ја вршел должноста (стр. 282–303, 305)',
    'posavsko-trebavski-odred':
      'Список на борците на одредот по општините од кои дошле (стр. 313 и натаму)',
    '8-kordunaska-divizija':
      'Список на загинатите борци на Осмата дивизија, по презиме, со бригадата во која биле (стр. 806 и натаму)',
    '8-kordunaska-divizija-kadar':
      'Командантите, политичките комесари и началниците на штабот на дивизијата, нејзините бригади и баталјони, со времето на должноста и што станало со секој (стр. 762–775)',
    'cankarjeva':
      'Список на борците на бригадата што ја преживеале војната (стр. 815 и натаму) и список на нејзините загинати (стр. 847 и натаму)',
    'cankarjeva-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на бригадата и командантите и комесарите на баталјоните, со времето на должноста (стр. 810–814)',
    'gubceva':
      'Список на борците на бригадата што ја преживеале војната (стр. 979 и натаму) и список на нејзините загинати (стр. 1016 и натаму)',
    'gubceva-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на бригадата и командантите и комесарите на баталјоните, со времето на должноста (стр. 975–978)',
    'dvanajsta':
      'Список на загинатите борци на бригадата и список на оние што ја преживеале војната, на крајот на книгата',
    'dvanajsta-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на бригадата и баталјоните, со времето на должноста; шефовите на разузнавачкиот центар, интендантите, санитетските референти и секретарите на СКОЈ, само имиња (стр. 571–574)',
    'gradnikova':
      'Список на борците загинати во бригадата и список на другите: оние што ја преживеале војната или не загинале додека биле во неа (стр. 840 и натаму)',
    'gradnikova-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на бригадата, со времето кога кој ја вршел должноста, и кратки биографии на народните херои на бригадата (стр. 791–799)',
    'zidanskova':
      'Список на борците на бригадата; кај загинатите годината на раѓање и на загинување (стр. 731 и натаму)',
    'zidanskova-kader':
      'Командантите, политичките комесари, нивните заменици, началниците на штабот и секретарите на СКОЈ на бригадата, со времето на должноста (стр. 729–730)',
    'skofjeloski-odred':
      'Список на борците на одредот, само имиња, како што се запишани во зачуваната архива на одредот (стр. 314 и натаму)',
    'istrski-odred':
      'Список на борците на одредот (стр. 827 и натаму), без загинатите, и список на загинатите со кратки податоци (стр. 849 и натаму)',
    'istrski-odred-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на одредот, неговите баталјони и чети, со времето на должноста (стр. 821–826)',
    'zapadnodolenjski-odred':
      'Список на борците на одредот (стр. 333 и натаму) и список на неговите загинати (стр. 340 и натаму)',
    'braciceva':
      'Список на загинатите борци на бригадата (стр. 722 и натаму) и на оние што ја преживеале војната (стр. 746 и натаму)',
    'tomsiceva-1':
      'Списоци на борците на единиците од кои настанала бригадата: ударната група на 3. баталјон Љубо Шерцер, Дакиевата летечка ударна патрола, Пролетерската ударна патрола и чета и 1. словенечки пролетерски ударен баталјон Тоне Томшич (1. книга, стр. 535 и натаму)',
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
    '19-sjevernodalmatinska-kadar':
      'Командантите и политичките комесари на дивизијата и нејзините бригади, со времето на должноста, членовите на политодделот 1943–1945 и народните херои на дивизијата, со кратка биографија (стр. 240–252)',
    '21-srpska':
      'Загинати, преживеани и други што се бореа во бригадата (Втора шумадиска): родители, раѓање, должност, кога стапиле во бригадата и каде загинале (стр. 387–472)',
    '14-hercegovacka':
      'Список на борците што поминале низ бригадата: година и место на раѓање; загинатите, со единицата и местото на загинување (стр. 243–287)',
    '14-hercegovacka-komandni-sastav':
      'Штабот на бригадата, штабовите на баталјоните, командите на четите, придружните водови, командирите и политичките делегати на водовите и единиците при штабот, по должности, со времето кога кој ја вршел должноста (стр. 234–242)',
    '5-vojvodjanska':
      'Список на борците и старешините на бригадата: година и место на раѓање, занимање, должност во бригадата, каде загинале или исчезнале (стр. 429–584)',
    '6-vojvodjanska':
      'Список на загинатите борци и раководители: година и место на раѓање, датум и место на загинување, каде се погребани (стр. 175–199)',
    '6-vojvodjanska-stabovi':
      'Членовите на штабот на бригадата, на штабовите на нејзините баталјони и на командите на четите, по должности, само имиња (стр. 171–174)',
    '13-vojvodjanska':
      'Список на припадниците на бригадата: имиња, понекаде прекар или место; авторот напоменува дека списокот не е целосен (стр. 771–793)',
    '7-srpska':
      'Список на борците на почетокот на мај 1944 по села и список на загинатите, умрените и исчезнатите: раѓање, стапување во бригадата, каде загинале (стр. 459–501)',
    '15-srpska':
      'Список на борците и раководителите на бригадата, список на загинатите и список на ранетите: раѓање, должност, кога и каде загинале или биле ранети (стр. 155–173)',
    '8-srpska':
      '„Незаборавник“, список на загинатите борци на бригадата: раѓање, датум и место на загинување (стр. 265–297)',
    '10-srpska':
      'Список на загинатите борци и раководители: раѓање, стапување во бригадата, должност, каде загинале и се погребани (стр. 488–541)',
    '23-srpska':
      'Преглед на загинатите и умрените борци и раководители: година и место на раѓање, занимање, стапување во НОВЈ, единица, каде загинале и се погребани (стр. 352–388)',
    '12-srpska':
      'Преглед на загинатите и умрените борци и раководители: година и место на раѓање, занимање, стапување во НОВЈ, единица, каде загинале и се погребани (стр. 355–400)',
    '20-srpska':
      'Преглед на загинатите и умрените борци и раководители: година и место на раѓање, занимање, стапување во НОВЈ, единица, каде загинале и се погребани (стр. 321–385)',
    '1-konjicka':
      'Список на загинатите борци и раководители (раѓање, каде загинале) и воениот список на старешините и борците на бригадата, само имиња (стр. 317–327)',
    'toplicki-odred':
      'Борците на одредот на денот на формирањето, списокот на загинатите и умрените борци и раководители и народните херои што се бореле во одредот, со фотографии (стр. 302–344)',
    'karlovacka':
      'Список на борците и раководителите на бригадата на денот на формирањето во Храшќе на 5 март 1944 и список на загинатите борци и раководители (стр. 379–414)',
    'karlovacka-kadar':
      'Штабот на бригадата и штабовите на четирите баталјони со времето кога кој ја вршел должноста и што станало со него, командирите, комесарите и делегатите на четите и водовите, четите и водовите при штабот, позадината (стр. 371–378)',
    '14-primorsko-goranska':
      'Список на загинатите борци на бригадата, со раѓањето, должноста и местото на загинувањето (стр. 227–264)',
    '22-divizija':
      'Список на загинатите борци и раководители на дивизијата по бригади: место на раѓање, ден и место на загинувањето (стр. 445–476)',
    '34-divizija':
      'Преглед на загинатите борци и раководители на дивизијата: чин, бригада, раѓање, стапување во НОБ, место и ден на загинувањето (стр. 401–432)',
    '34-divizija-kadar':
      'Старешините на штабот на дивизијата, нејзиниот комитет на КПЈ, политичкиот оддел, интендантурата и санитетот, на нејзините четири бригади, партизанските одреди и самостојните единици, по должности (стр. 389–399)',
    '4-sandzacka':
      'Список на загинатите борци и раководители (раѓање, каде загинале) и список на ранетите, со местото и денот на ранувањето (стр. 460–485)',
    '3-primorsko-goranska':
      'Список на старешините на бригадата и четните болничари, со должноста, и список на загинатите припадници на бригадата, со раѓањето и местото на загинувањето (стр. 234–259)',
    '3-primorsko-goranska-stabovi':
      'Членовите на штабот на бригадата, на штабовите на баталјоните и старешините на самостојните единици, по должности, со времето на должноста и како завршило (стр. 227–233)',
    '13-hercegovacka':
      'Загинатите борци и старешини на бригадата (раѓање, ден и место на загинувањето) и список на борците што се бореле во бригадата, само имиња (стр. 316–347)',
    '13-hercegovacka-starjesine':
      'Штабот на бригадата и единиците при штабот, штабовите на баталјоните и командите на четите, по должности, со времето кога кој ја вршел должноста (стр. 305–315)',
    '12-hercegovacka':
      'Список на загинатите борци и старешини на бригадата, по општини: раѓање, должност, каде и кога загинале (стр. 207–220)',
    '1-bokeljska':
      'Список на загинатите и умрените борци на бригадата и на исчезнатите во борба: баталјон, раѓање, каде и кога загинале (стр. 315–321)',
    '1-bokeljska-spisak':
      'Списокот на бригадата од формирањето на 5 октомври 1944 до крајот на војната, по единици: штабот, баталјоните и единиците при штабот, должноста и името на секој борец и старешина (стр. 291–314). Борец преместен во друга единица е запишан и во неа, па некои се појавуваат двапати. Страниците на znaci.org немаат текст, само слики: имињата се прочитани од сликите.',
    '6-dalmatinska':
      'Список на загинатите борци на бригадата: од каде се, каде и кога загинале (стр. 259–271)',
    '6-dalmatinska-kadar':
      'Командантите, комесарите, нивните заменици, началниците и другите старешини на штабот на бригадата и на штабовите на баталјоните, по должности, само имиња (стр. 257–258)',
    'osjecka':
      'Список на загинатите и умрените борци на бригадата и список на преживеаните борци, по општини на раѓање (стр. 207–254)',
    'osjecka-rukovodioci':
      'Командантите, комесарите и началниците на штабот на бригадата, командантите и комесарите на баталјоните, командирите и комесарите на четите, само имиња (стр. 203–206)',
    '1-zagorska':
      'Список на загинатите борци и раководители на бригадата од 8 мај 1944 до 15 мај 1945: година и место на раѓање, кога и каде загинале (стр. 191–205)',
    '6-crnogorska':
      'Список на загинатите борци и старешини на бригадата, со умрените од рани и болести: раѓање, должност, каде и кога загинале (стр. 871 и натаму)',
    '11-krajiska-poginuli':
      'Список на загинатите борци на бригадата, по општини: раѓање, националност, занимање, кога стапиле во НОВ, должност, каде и кога загинале (стр. 439–463)',
    '11-krajiska-zene':
      'Список на борките што биле во бригадата, само имиња (стр. 425)',
    '3-banijska':
      'Список на раководителите и борците на бригадата, само имиња (стр. 195–205)',
    '8-banijska-poginuli':
      'Загинатите и умрените борци на бригадата од 7 септември 1942 до 6 декември 1944: раѓање, занимање, кога стапиле во бригадата, должност, каде и кога загинале (стр. 247–312)',
    '8-banijska-kadar':
      'Штабот на бригадата, политоделот и штабовите на петте баталјони, по должности (стр. 244–246)',
    'macvanski-odred':
      'Список на борците на Мачванскиот (Подринскиот) партизански одред, прв дел (јули 1941 – март 1942): по местата од кои стапиле во одредот, со податоци за секого (текст на znaci.org, без скенирана книга; вториот дел не е објавен)',
    'posavski-odred':
      'Список на борците на Посавскиот партизански одред во 1941: команда, болница и баталјони, со податоци за секого (стр. 565–742)',
    '51-divizija':
      'Борците на 51. војводинска дивизија загинати и исчезнати во Батинската битка, ноември 1944: раѓање, должност, каде и кога загинале (стр. 469–501)',
    '51-divizija-savic':
      'Список на загинатите борци и старешини на дивизијата од формирањето, 1 ноември 1944, до крајот на војната, 15 мај 1945, по бригади: 7., 8., 12. и 14. (словачка), артилериска, единиците при штабот; раѓање, должност, каде и кога загинале (стр. 219–288)',
    'borci-sutjeske-vrhovni-stab':
      'Поименичен список на борците од Сутјеска: сите припадници на Врховниот штаб, неговите служби, Придружниот баталјон и британската воена мисија во битката, со податоци за секого и што било со него до крајот на војната.',
    'vtr-grmec':
      'Работниците на воено-техничката работилница на Врховниот штаб во Грмеч 1942–1943, со занаетот и местото од каде што биле, оние што загинале или умреле во војната и по неа, обезбедувањето на работилницата и работниците на дрварската леарница (стр. 361–364).',
    'borci-sutjeske-1-proleterska-divizija':
      'Поименичен список на борците од Сутјеска: штабот на дивизијата, неговите служби и придружни единици во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-2-proleterska-divizija':
      'Поименичен список на борците од Сутјеска: штабот на дивизијата, неговите служби и придружни единици во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-3-udarna-divizija':
      'Поименичен список на борците од Сутјеска: штабот на дивизијата, неговите служби и придружни единици во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-7-banijska-divizija':
      'Поименичен список на борците од Сутјеска: штабот на дивизијата, неговите служби и придружни единици во битката, со податоци за секого и што било со него до крајот на војната.',
    'borci-sutjeske-centralna-bolnica':
      'Поименичен список на борците од Сутјеска: персоналот на Централната болница и ранетите чија единица не можела да се утврди, со податоци за секого и што било со него до крајот на војната.',
    '3-licka':
      'Список на загинатите, умрените и исчезнатите борци на бригадата и нејзините народни херои (стр. 361–413).',
    '5-proleterska-partizanke':
      'Биографии на партизанките на бригадата: раѓање, пат во НОБ, должности во бригадата, рани и одликувања, живот по војната (стр. 43–278).',
    '16-banijska-poginuli':
      'Список на загинатите борци и старешини на бригадата од 26 декември 1942 до 30 јуни 1943, со година и место на раѓање и место на загинување (стр. 201–247).',
    'pozarevacki-odred':
      'Список на борците на одредот од 1941 до октомври 1944, со податоци за секого (стр. 238–307; приредил Миодраг Стојановиќ Коле).',
    '1-proleterski-bataljon':
      'Список на борците на баталјонот, со година и место на раѓање и судбина (стр. 262–277).',
    '4-pomorski-sektor':
      'Попис на борците на IV ПОС 1943–1945, што го составија Секцијата на борците на секторот и авторот (4.702 имиња, со местото од каде е кој), и загинатите и умрените борци на секторот, со должноста и како загинале (стр. 418–478).',
    '4-pomorski-sektor-stab':
      'Командантите, политичките комесари, нивните помошници и началниците на штабот на секторот, со времето кога кој ја вршел должноста (прилог X, стр. 485)',
    'viski-bataljon':
      'Списокот на борците на Вишкиот доброволен баталјон на Вис кон крајот на јануари 1944: командата, четите, водовите и десетините од Бишево и Оклучна (стр. 538–539).',
    'kokrski-odred-1':
      'Списокот на борците на Кокршкиот одред од првиот состав, јуни 1942 - јануари 1943, по штабот, баталјоните и четите: од каде е кој, должностите и што се случило со секого (стр. 509–525).',
    'kokrski-odred':
      'Списокот на борците на Вториот кокршки одред, авторова реконструкција според списоците и документите на одредот: штабовите, разузнавачкиот центар и точки, куририските станици, санитетот, работилниците и баталјоните по чети и периоди, со годината на раѓање и кој загинал (стр. 453–478).',
    'cankarjev-bataljon':
      'Формацијата на баталјонот во Драгоше, шпанските борци и народните херои, загинатите борци по битките 1941–1942, преживеаните носители на Споменицата 1941 и другите преживеани учесници во битката за Драгоше (стр. 338–346).',
    'novosadski-odred':
      'Попис на припадниците на Новосадскиот партизански одред во 1941 и 1944 година: име, должност, од каде е кој и од кога (стр. 85–92).',
    'deveta':
      'Список на борците на IX. СНОБ Кочевска: име, година и место на раѓање, а за загинатите година и место на смртта (стр. 425–446).',
    'deveta-kader':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на бригадата и командантите и комесарите на баталјоните, со времето на должноста и кој паднал на должноста (стр. 401–404)',
    '4-prekomorska':
      'Список на загинатите и умрените борци и командниот кадар на бригадата: штаб, команда на место, баталјони, самостојна чета и команди на четите (стр. 327–333).',
    '9-srpska':
      'Строј во Речица: 377 борци на денот на формирањето, 11 март 1944; командниот кадар на бригадата, баталјоните и четите со датумите на должностите; болничарките и борките. Именикот на борците со кратки биографии (стр. 47–372) znaci.org го нема.',
    'kozjanski-odred':
      'Список на борците и борките на Козјанскиот одред: 3.495 лица од формирањето до расформирањето, со датум и место на раѓање, влез во НОВ, занимање и забелешка (каде кој бил, кој паднал); страниците се тука црно-бели, текстот како во книгата.',
    'proleterski-bataljon-bk':
      'Список на борците на баталјонот: биографија на секој, со неговата фотографија, од раѓањето и доаѓањето во Козарачката, Грмечката или Дрварската пролетерска чета до загинувањето или крајот на војната (стр. 256–362).',
    '1-tenkovski-bataljon':
      'Попис на припадниците на Тенковскиот вод на Групата партизански одреди за Лика, Тенковската чета на 1-от корпус и Тенковскиот баталјон на Главниот штаб на НОВ и ПО на Хрватска (251 име, стр. 337–340).',
    '3-diverzantski-odred':
      'Преглед на борците и старешините на 3-та диверзантска група, чета, баталјон и одред (имиња, со ознака за загинатите и умрените по војната) и преглед на загинатите диверзанти со должност и година (прилог IV, стр. 587–591).',
    '1-2-prekomorska':
      'Список на загинатите борци и борки на двете бригади (раѓање, кога и каде паднал) и командниот кадар во логорите Карбонара и Гравина, на Корчула, Хвар и Вис и командите на четите (стр. 357–372).',
    '5-prekomorska':
      'Список на загинатите борци и борки (256: раѓање, кога и каде паднал) и командниот кадар на бригадата, баталјоните и четите (стр. 283–301).',
    'sercerjeva':
      'Список на доброволците на Шерцерјевата бригада од формирањето на 6 октомври 1942 до крајот на февруари 1943 (име, партизанско име и место) и список на загинатите до крајот на 1943, по местото и денот на загинувањето (стр. 509–523).',
    'kosovelova':
      'Список на загинатите, исчезнатите и умрените од рани (504 имиња: раѓање, место, кога и каде паднал) и командниот кадар на бригадата и нејзините баталјони со датумите на должностите (стр. 803–824).',
    'eskadrile-novj':
      'Списоци на составот на првата и втората ескадрила на НОВЈ (352-ри и 351-ви сквадрон на РАФ): број, чин, должност, раѓање и како кој дошол во ескадрилите, од Блискиот Исток, од италијанско заробеништво или од земјата; на крајот имиња чија ескадрила не е утврдена (стр. 331–354).',
    '42-vazduhoplovna':
      'Список на составот на дивизијата по полкови (421-ви, 422-ри и 423-ти воздухопловен полк), штаб, самостојна чета и авиоработилници: чин и должност (стр. 291–321).',
    '18-srpska':
      '„Тие се бореа во 18-та српска бригада“: 5.047 борци и раководители на бригадата според пресметката на авторот, од кои 780 загинати, 787 ранети, 47 исчезнати и 49 умрени од болест, со година и место на раѓање, должност и каде кој загинал или бил ранет (стр. 313–426).',
    '5-srpska':
      'Список на загинатите и умрените борци и раководители на бригадата (прилог бр. 2): година и место на раѓање, занимање, кога кој стапил во НОВЈ, баталјон и должност, кога и каде загинал и каде е погребан (стр. 450–510).',
    'cacanski-odred':
      'Загинатите борци на одредот, по краеви (Драгачево, Љубиќ, Трнава, Таково, Чачак) и села: татко, занимање, раѓање, баталјонот во кој се борел и како и каде загинал.',
    'mostarski-bataljon':
      'Борците на Коњичкиот баталјон (септември 1941 — јуни 1942), на Мостарскиот баталјон (јуни 1942 — јуни 1943) и на Мостарскиот баталјон во Мостарскиот партизански одред (јуни 1943 — мај 1944), секој со кратка биографија: раѓање, занимање, СКОЈ и КПЈ, доаѓање во баталјонот, должност и судбина (стр. 329–392).',
    '13-krajiska':
      'Два списока: борците и раководителите што биле во бригадата во август и септември 1943, со место, должност и, за загинатите, кога и каде загинале и каде се погребани; членовите на партиската организација на КПЈ во бригадата во мај 1945, со денот на приемот во Партијата и должноста (стр. 365–404).',
    'pozega-pali':
      'Прилогот на Драгољуб Муњиќ: список на загинатите борци од НОБ, жртвите на фашистичкиот терор и цивилните жртви на војната во срезот Пожега, по села, со раѓање, единица и како загинал секој. Внесени се борците и, означени како активисти, соработниците на НОП, одборниците и работниците во партизанските работилници; цивилните жртви и војниците на поранешната југословенска војска не се. Книгата не припаѓа на една единица: записот од неа е додаден кон записот на секој борец што е на сајтот и за кого сигурно се знае дека е тој.',
    'cacanski-kraj-pali':
      'Загинатите и настраданите од чачанскиот крај 1941–1945, по краеви (Драгачево, Љубиќ, Таково, Трнава, Чачак) и села: татко, занимање, раѓање, единица и како загинал секој. Внесени се борците и, означени како активисти, членовите на КПЈ и СКОЈ, одборниците, соработниците на НОП и работниците во партизанските работилници во 1941; цивилните жртви и четниците не се. Книгата не припаѓа на една единица: записот од неа е додаден кон записот на секој борец што е на сајтот и за кого сигурно се знае дека е тој.',
    '1-krajiska':
      'Список на загинатите, умрените и исчезнатите борци на бригадата, 2.127 имиња: раѓање, кога стапиле во НОБ и во бригадата, чета и баталјон, должност, кога и каде загинале и каде се погребани (стр. 331–442). Податоците ги истражил и обработил Слободан Спегар Спего.',
    'pionirska-ceta':
      'Список на борците на четата што авторот ја водел како командир: раѓање, кога кој станал борец, должност во четата и живот по војната (стр. 125–132).',
    'zbornik-heroja-1957':
      'Портрети на народните херои прогласени до 1957: раѓање, пат во НОБ, смрт или живот по војната и денот на прогласувањето. Книгата не припаѓа на една единица: портретот е додаден на записот на секој херој што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'narodni-heroji-1982-1':
      'Биографии на сите народни херои, второ издание (1982), том 1 (A–M): раѓање, живот пред војната, пат во НОБ, смрт или живот по војната и денот на прогласувањето. Книгата не припаѓа на една единица: биографијата е додадена на записот на секој херој што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'narodni-heroji-1982-2':
      'Биографии на сите народни херои, второ издание (1982), том 2 (N–Ž): раѓање, живот пред војната, пат во НОБ, смрт или живот по војната и денот на прогласувањето. Книгата не припаѓа на една единица: биографијата е додадена на записот на секој херој што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'trebinjci-pali':
      'Споменица на Сојузот на борците од Требиње (1974): борците од општината што паднале во војната (стр. 13–96) и борците од цела Југославија што загинале кај Требиње (стр. 159–174), со раѓање, единици и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списокот на жртвите на фашистичкиот терор од истата книга не е внесен.',
    'pali-za-lepsa-svitanja':
      'Мајките на народните херои раскажуваат за своите синови и ќерки (1967); над секоја приказна е кратка биографија на херојот: раѓање, занимање, КПЈ, НОБ, смрт и денот на прогласувањето. Книгата не припаѓа на една единица: биографијата е додадена на записот на секој херој што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'ofanziva-1942-poginuli':
      'Список на борците од 1., 2., 3. и 4. пролетерска бригада што загинале или исчезнале во походот кон западна Босна, од 24 јуни до 30 септември 1942 (стр. 698–711), по бригади и баталјони, со раѓање, занимање и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hak-20-gospic-perusic':
      'Од зборникот на Историскиот архив во Карловац (кн. 20): паднатите борци од околиите Госпиќ и Перушиќ 1941–1945 (стр. 986–1045) и носителите на Партизанската споменица 1941 (стр. 1194–1209), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-10-korenica-udbina':
      'Од зборникот на Историскиот архив во Карловац (кн. 10): паднатите борци од околиите Кореница и Удбина 1941–1945 (стр. 990–1039), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hronika-prigrevica':
      'Монографија на селото Пригревица кај Апатин (1997), во кое по војната се населиле семејства на борци од Лика и Банија: загинатите, починатите и исчезнатите борци од НОБ од тие семејства (стр. 307–331) и носителите на Партизанската споменица 1941 (стр. 339–353), со раѓање, единица и смрт или живот по војната. Списоците на борците што влегле во војната подоцна, само со име, не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-medak':
      'Монографија на селата од некогашната општина Медак кај Госпиќ (2004): борците од НОБ од тие села што загинале во борба со непријателот, по села (стр. 434–465), и носителите на Партизанската споменица 1941 (стр. 506–513), со раѓање, единица и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-hasani':
      'Монографија на селото Хашани кај Босанска Крупа (1991): загинатите, починатите и исчезнатите борци од НОБ од селото (стр. 135–138), носителите на Партизанската споменица 1941 (стр. 138) и другите преживеани учесници во НОБ, само со име (стр. 139). Преживеаните на кои боречкиот стаж им е признат за работа за НОД не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-podgocka-naselja':
      'Монографија на селата под Гоч кај Трстеник (2008): борците од Горњи Рибник што загинале на Сремскиот фронт (стр. 194–195) и учесниците во НОБ од Оџаци што загинале или исчезнале во војната (стр. 344–345). Списоците на убиените од четниците и на жртвите на фашистичкиот терор не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-prekopcelica':
      'Монографија на селото Прекопчелица кај Лебане (2012): борците од селото по бригадите и одредите на НОВЈ во кои биле (стр. 121–124) и загинатите во партизаните (стр. 126). Припадниците на позадинските единици и учесниците што ги навеле само роднините не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-brezovica-stublica':
      'Монографија на селата Брезовица и Стублица кај Трстеник (2015): учесниците во НОБ од Брезовица мобилизирани во октомври 1944 и загинатите и исчезнатите во војната (стр. 113–115) и учесниците во НОБ од Стублица (стр. 478–479). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-makce':
      'Монографија на селото Макце кај Велико Градиште (2000): жителите што загинале, починале или исчезнале во војната, повеќето борци од 25. дивизија (стр. 62–64), и учесниците во НОБ што ја преживеале војната, со година на раѓање и одликување (стр. 64–66). Жртвите на фашистичкиот терор од истиот список не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-donje-vidovo':
      'Монографија на селото Доње Видово кај Параќин (1997): од списокот на загинатите жители се внесени само оние што книгата ги бележи како учесници во НОБ (стр. 127), а не и жртвите на фашистичкиот терор и другите загинати. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-petrlas':
      'Монографија на селото Петрлаш кај Димитровград (2001): борците од Петрлаш во Првата царибродска, 8., 10. и 12. српска бригада, 13. дополнителен баталјон и другите единици на НОВЈ (стр. 348). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-labukovo':
      'Монографија на селото Лабуково кај Сврљиг (2007): жителите загинати во НОБ од 1941 до 1945 (стр. 44); оние што книгата ги наведува како заложници, жртви на теророт и логораши не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-beli-breg':
      'Монографија на селото Бели Брег кај Алексинац (2009): жителите учесници во НОБ, со година на раѓање, денот кога влегле во единицата и единицата, и загинатите и починатите веднаш по војната (стр. 113–114). Заробениците, интернираните и војниците на Југословенската војска од истата табела не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hronika-donja-gorevnica':
      'Монографија на селото Доња Горевница кај Чачак (1996): од списокот на паднатите борци и жртви од селото се внесени само борците (стр. 233–238), а не и жртвите на теророт и војниците на Југословенската војска. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'ostrvica':
      'Монографија на селото Острвица кај Госпиќ (2003): попис на домаќинствата во селото со промените за време на војната (стр. 617–663), секој член на семејството и што се случило со него. Внесени се само борците, оние за кои записот вели дека биле борци, наведува воена должност или единица; цивилите, жртвите на теророт и припадниците на војската на НДХ не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'divoselo':
      'Монографија на селата Дивосело, Читлук и Орнице кај Госпиќ: загинатите борци и офицери од тие села 1941–1945, секој со кратка биографија (стр. 425–435). Двајцата војници на Југословенската војска загинати во априлската војна не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'mogoric':
      'Монографија на селото Могориќ во Лика: 110 загинати борци од селото од спомен-плочата на Спомен-домот, секој со кратка биографија (стр. 191–199), и носителите на Партизанската споменица 1941 од селото (стр. 201). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'vrebac':
      'Монографија на селата Вребац, Завоѓе и Павловац кај Госпиќ: загинатите борци од НОВ од тие села од 1941 до 1945, по села, секој со кратка биографија (стр. 298–311). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'licko-petrovo-selo':
      'Воена хроника на некогашната општина Личко Петрово Село (1985): загинатите борци по села (Личко Петрово Село, Ново Село, Жељава, Арапов До, Решетар, Заклопача и Лисина, Доњи Ваганац), во табела со годините на раѓање, стапување во НОВ и загинување, местото на загинување, единицата и должноста (стр. 207–214). Починатите од тифус, глад и мини не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'bosansko-grahovo':
      'Загинатите борци од народноослободителната војна од подрачјето на Босанско Грахово, по села, секој со кратка биографија (стр. 642–697). Списокот на жртвите на фашистичкиот терор што следи не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'staromajdansko':
      'Загинатите борци и жртвите на фашистичкиот терор од подрачјето на Стари Мајдан кај Сански Мост, по села, секој со кратка биографија (стр. 177–246), и списоците на починатите и живите борци и учесници во војната во 1983 и на носителите на Партизанската споменица 1941, само имиња (стр. 247–266). Внесени се загинатите борци и носителите на споменицата; борците и учесниците во војната од списоците на имиња се означени како учесници, бидејќи списокот не кажува кој бил борец, а кој активист; жртвите на теророт не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'han-pijesak':
      'Борците од општината Хан Пијесак и оние што паднале на нејзиното подрачје: загинатите во Пјеновац на 21 јануари 1942 и во втората непријателска офанзива, главно борци на Првата пролетерска бригада (стр. 106–109), народните херои и истакнатите учесници во НОБ (стр. 147–150) и загинатите борци 1941–1945, секој со кратка биографија (стр. 151–161). Внесени се и, означени како активисти, партиските и теренските работници што списокот ги брои меѓу загинатите. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'skakavac':
      'Борците и учесниците во НОБ од селото Скакавац кај Босански Петровац: првоборците, носители на Партизанската споменица 1941 (стр. 163–165), учесниците во НОВ што ја преживеале војната (стр. 166–173) и загинатите борци (стр. 173–177), секој со кратка биографија, и членовите на народноослободителните одбори, одборите на АФЖ, младинската организација и КПЈ, само имиња (стр. 181–191), внесени како активисти. Преживеаните за кои биографијата кажува само дека биле учесници во НОВ се означени како учесници. Жртвите на теророт и еден што во 1943 преминал кај четниците не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'zitoradje':
      'Учесниците во НОВ од Житорађе кај Владичин Хан, само имиња (стр. 86), ранетите и загинатите борци од селото (стр. 86–88) и борците на српските бригади загинати при ослободувањето на селото во септември и октомври 1944, секој со кратка биографија (стр. 89–91). Жртвите на фашистичкиот терор не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'brod-crna-trava':
      'Прилог III, загинатите 1941–1945 од селото Брод кај Црна Трава, табела со маалото, датумот и местото на загинувањето и единицата (стр. 808–809). Внесени се само оние за кои табелата ја наведува единицата, бидејќи меѓу другите има и цивилни жртви. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'revolucionarno-grahovo':
      'Борците од Грахово кај Никшиќ паднати во НОВ и револуцијата 1941–1945, секој со кратка биографија (стр. 93–128), и загинатите народни херои (стр. 81–91). Внесени се и, означени како активисти, припадниците на движењето што загинале во затворите и логорите, а од жртвите на фашистичкиот терор (стр. 129–133) само активистите и борците. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'kolasin':
      'Загинатите во НОВ и револуцијата од подрачјето на Колашин, секој со кратка биографија (стр. 683–724), и носителите на Партизанската споменица 1941 со должноста што ја имале на крајот на војната (стр. 732–743). Активистите на движењето се означени како активисти, а загинатите за кои биографијата кажува само дека биле во НОД како учесници; од жртвите на фашизмот и војната (стр. 726–731) внесени се само борците. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'bozice':
      'Борците од Божиќе кај Андријевица по братства, само имиња, како што ги брои авторот според Конвенцијата за борецот (стр. 316–317), носителите на Партизанската споменица 1941 (стр. 317) и загинатите како борци или соработници на НОДЈ (стр. 318–319). Загинатите припадници на четничкото движење не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'otocac-brinje':
      'Список на загинатите борци, жртвите на фашистичкиот терор и преживеаните борци и активни учесници во НОБ од некогашната општина Оточац, по села: загинатите борци (стр. 411–433) и преживеаните борци и активни учесници во НОБ (стр. 461–531), со раѓање, стапување во НОБ и должност. Внесени се и активните учесници, политичките работници, одборниците и членовите на СКОЈ и АФЖ, означени како активисти; жртвите на теророт не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'hak-14-donji-lapac':
      'Од зборникот на Историскиот архив во Карловац (кн. 14): паднатите борци од околијата Доњи Лапац 1941–1945 (стр. 1041–1094), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-13-gracac':
      'Од зборникот на Историскиот архив во Карловац (кн. 13): паднатите борци од околијата Грачац 1941–1945 (стр. 917–965), по општини, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-7-plascanska-dolina':
      'Од зборникот на Историскиот архив во Карловац (кн. 7): паднатите борци од Плашчанската долина и околината 1941–1945 (стр. 689–701), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'krusevac-1944-poginuli':
      'Список на борците загинати во борбите за ослободувањето на Крушевац во септември и октомври 1944, по единици: 4. пролетерска црногорска, 3., 6. и 17. српска бригада и Командата на крушевачкото воено подрачје (стр. 273–283), со раѓање и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'u-rovovima-srema-poginuli':
      'Список на борците загинати на Сремскиот фронт (стр. 230–267), по бригади и по местото каде што паднале, само имиња, понекогаш со должноста. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој, по име, бригада и место на загинувањето.',
    'sremski-front-poginuli':
      'Списоци на борците загинати на Сремскиот фронт од октомври 1944 до април 1945, по дивизии и бригади, секој по кратката историја на единицата: само имиња, понекогаш со иницијалот на таткото. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој, по име, бригада и време на загинувањето. Списоците на паднатите црвеноармејци од крајот на книгата не се внесени.',
    'bitka-kod-oborova-poginuli':
      'Имињата на 128 борци од 2. мославачка бригада и Посавскиот партизански одред загинати кај Оборово на 29 март 1944 (стр. 158–160). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'zrtve-rata-1964-slo':
      'Пописот на жртвите на војната од 1964, од подрачјето на Словенија, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-hrv':
      'Пописот на жртвите на војната од 1964, од подрачјето на Хрватска, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-bih':
      'Пописот на жртвите на војната од 1964, од подрачјето на Босна и Херцеговина, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-crg':
      'Пописот на жртвите на војната од 1964, од подрачјето на Црна Гора, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-mak':
      'Пописот на жртвите на војната од 1964, од подрачјето на Македонија, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-srb':
      'Пописот на жртвите на војната од 1964, од подрачјето на Србија без покраините, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-kos':
      'Пописот на жртвите на војната од 1964, од подрачјето на Косово и Метохија, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    'zrtve-rata-1964-voj':
      'Пописот на жртвите на војната од 1964, од подрачјето на Војводина, по општини и села: внесени се само борците на НОБ што загинале или умреле во војната, не и жртвите на теророт. Пописот не припаѓа на една единица: записот од него е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци. Пописот го објави Музејот на жртвите на геноцидот.',
    '6-istocnobosanska-dopuna':
      'Борци на бригадата чии податоци не се објавени во книгата „Borbeni put Šeste proleterske brigade“ (1977), собрани до 1981: раѓање, кога стапиле во НОБ, должност, судбина; и борци за кои не се утврдени местото и времето на загинувањето (стр. 676 и натаму)',
    '7-banijska-poginuli':
      'Нецелосен список на загинатите во војната и починатите припадници на бригадата: раѓање, народност, занимање, кога стапиле во НОВЈ, баталјон, каде и кога загинале (стр. 394–462)',
    '15-majevicka-spisak':
      'Народните херои на бригадата и список на сите нејзини борци: година и место на раѓање, народност, занимање, кога стапиле во НОБ и дошле во бригадата, судбина (стр. 484–557)',
    'beogradski-bataljon':
      'Сите борци на Белградскиот баталјон од првите денови на востанието до 1 март 1945, кога стана 3. баталјон на Првата пролетерска, според тоа кога дошле во баталјонот: занимање, раѓање, членство во КПЈ и СКОЈ, што се случило со секого во војната',
    '1-dalmatinska-monografija':
      'Командирите и политичките комесари на четите по баталјони, биографиите на народните херои на бригадата и списокот на борците загинати во војната, истиот како на znaci.org, тука со скенираната книга',
    '4-brigada-slavonije':
      'Список на загинатите борци и старешини на бригадата (чета и должност, датум и место на раѓање, датум и место на загинувањето) и список на ранетите (единица и должност, кога биле ранети), прилозите 2 и 3 од книгата (стр. 164 и натаму)',
    '4-brigada-slavonije-rukovodioci':
      'Раководителите на штабот на бригадата и на единиците при штабот и на четирите баталјони, од командантот до водникот, по должности, со тоа од каде биле и кога ја вршеле должноста, и другарите на разни должности во бригадата, прилогот 1 од книгата (стр. 177–182)',
    '9-dalmatinska-divizija':
      'Борците и старешините на дивизијата што загинале или исчезнале во борбите од 11 февруари до 15 април 1943, имиња со татковото име (стр. 121–126)',
    '3-dalmatinska-poginuli':
      'Загинатите и исчезнатите борци и старешини на 3. самостојна далматинска бригада од 14 април до 6 јуни 1943, имиња со татковото име (стр. 126–128)',
    '12-slavonska-zene':
      'Список на жените борци на 12. пролетерска славонска бригада, загинати, починати и преживеани, со кратки биографии (текст на znaci.org, без скенирана книга; списокот на сите борци на бригадата што го најави книгата не е објавен)',
    'zagrebacki-odred':
      'Список на борците на одредот од зборникот документи и спомени (стр. 407–418): главно преживеани што по војната се пријавиле во СУБНОР во Зелина и загинати што ги спомнуваат воените документи и спомените; село, општина и судбина. Баталјоните што цели заминале во бригадата „Матија Губец“ и во Загорската бригада не се во него.',
    'mosorski-odred':
      'Список на борците на Мосорскиот партизански одред 1942–1944 (првиот дел од списокот, стр. 355–562): I мосорски одред, Мосорскиот баталјон, Летечката мосорска чета и одредот од октомври 1943 до ноември 1944, со раѓање, занимање, доаѓање во одредот и судбина. Вториот дел од списокот, борците на командите на места и теренските работници, не е внесен.',
    'mosorski-odred-2':
      'Вториот дел од пописот од истата книга (стр. 573–648): борците на командите на места, партиско-политичките и теренските работници од подрачјето на Мосор. Во списокот на одредот се борците, оние за кои записот вели дека биле борци или наведува воена должност или единица на војската, и припадниците на работните баталјони. Теренските и политичките работници, одборниците и членките на АФЖ се внесени како активисти, секој кон записот на борецот што е на сајтот ако е тоа тој, другите меѓу Другите борци.',
    'mosorski-odred-kader':
      'Раководниот кадар на одредот 1942–1944, по должности, од командантите на одредот до командирите на водови, водните делегати и четните болничарки, само имиња (стр. 563–568)',
    'turopoljsko-posavski-odred':
      'Список на загинатите борци на одредот (99, со место на раѓање, датум и место на загинувањето) и стрелани и починати борци на одредот во војната (16), стр. 17–20 (Музеј на Туропоље, Велика Горица 1983)',
    'zascitna-enota-vpv':
      'Припадниците на заштитната единица на воено-политичкото раководство на НОБ на Словенија што ја преживеаја војната, со датум и место на раѓање и базите во кои служеле, потоа загинатите борци, народните херои и носителите на Партизанската споменица 1941 (стр. 293–310).',
    'hak-19-vojnic':
      'Од зборникот на Историскиот архив во Карловац (кн. 19): паднатите борци од околијата Војниќ 1941–1945 (стр. 1123–1177), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-18-slunj-veljun':
      'Од зборникот на Историскиот архив во Карловац (кн. 18): паднатите борци од околиите Слуњ и Велјун 1941–1945 (стр. 921–977), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-15-duga-resa':
      'Од зборникот на Историскиот архив во Карловац (кн. 15): паднатите борци од денешната општина Дуга Реса 1941–1945 (стр. 1060–1090), по општини и села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус од истата книга не се внесени.',
    'hak-12-dreznica':
      'Од зборникот на Историскиот архив во Карловац (кн. 12): паднатите борци од општината Дрежница 1941–1945 (стр. 865–876), по села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списокот на жртвите на фашистичкиот терор и на војната од истата книга не е внесен.',
    'hak-16-gornje-dubrave':
      'Од зборникот на Историскиот архив во Карловац (кн. 16): паднатите борци од општината Горње Дубраве 1941–1945 (стр. 889–899), по села, со раѓање, пат во НОБ и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списокот на жртвите на фашистичкиот терор и на војната од истата книга не е внесен.',
    'sjenicak':
      'Хроника на едно кордунско село, издадена од Историскиот архив во Карловац, со два нејзини списока: паднатите и умрените борци 1941–1945 од Долни, Горни и Ласињски Сјеничак (стр. 330–338), по села, со раѓање, пат во НОБ и смрт, и носителите на Партизанската споменица 1941 (стр. 385–389). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Списоците на жртвите на фашистичкиот терор и на умрените од тифус и настинка од истата книга не се внесени.',
    'tuzla-spomen-knjiga':
      'Спомен-книга на општина Тузла: биографии на нејзините учесници во НОБ што загинале во 1941–1945 (стр. 13–300), родени, живееле или работеле во Тузла или од неа тргнале во партизаните, често со фотографија, со единицата, раѓањето и смртта. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој. Вториот дел на книгата, жртвите на фашистичкиот терор, не е внесен.',
    'jajce-1941-poginuli':
      'Од зборникот спомени за јајачкиот крај (кн. I): списокот на борците од јајачкото подрачје загинати во 1941 година, со раѓање, единица и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'jajce-1942-poginuli':
      'Од зборникот спомени за јајачкиот крај (кн. II): списокот на борците и активистите на НОД од јајачкото подрачје загинати во 1942 година, со раѓање, единица и смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'spomenica-crnogorskim-antifasistima':
      'Список на црногорските антифашисти загинати и умрени во 1941–1945, по општини, во табела: име, татково име, година и место на раѓање, година на смрт и место на загинување. Сите што книгата ги наведува се водат како партизани: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој, а другите се меѓу другите борци.',
    'moste-polje-spomenica-1941':
      'Носителите на Партизанската споменица 1941 од подрачјето на денешната општина Мосте-Поље во Љубљана, од архивот на ЦК ЗКС (стр. 257–260): име, година на раѓање и занимање, а за оние што умреле по војната и година на смрт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'vis-spomenica-1941':
      'Носителите на Партизанската споменица 1941 од вишкото островје (стр. 521), само имиња, и реченицата на книгата за народниот херој Андрија Божаниќ. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец од островот што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'prilog-u-krvi-pali-borci':
      'Паднатите борци на НОБ од пљеваљската околија од април 1941 до 15 мај 1945 (стр. 141–216), со биографија на секој. Книгата меѓу паднатите борци ги вбројува и партиските и политичките работници, одборниците и соработниците на НОД: и тие се внесени, означени како активисти. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'jevreji-jugoslavije-ucesnici-nor':
      'Списокот на еврејските учесници во народноослободителната војна, со биографија на секој (стр. 307 и понатаму). Списокот ги брои сите што биле во НОД: внесени се сите, а политичките и позадинските работници и оние што биле фатени на патот кон партизаните се означени како активисти. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'hrvatsko-zagorje-1981':
      'Попис на загинатите учесници во НОБ 1941–1945 од подрачјето на општините Доња Стубица, Иванец, Клањец, Крапина, Прерада, Забок, Запрешиќ и Златар-Бистрица, со раѓање, единица и смрт. Пописот заедно ги наведува борците и жртвите на фашистичкиот терор; внесени се борците и, означени како активисти, членовите на КПЈ, СКОЈ и НОО, политичките работници и куририте, а жртвите на теророт не. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'imotska-krajina-pali-borci':
      'Паднатите борци и жртвите на фашистичкиот терор по селата на Имотската крајина (стр. 163–472), со раѓање, пат во НОВ и смрт. Внесени се паднатите борци од делот што книгата за секое село го насловува »Poginuli borci«, а скоевците, комунистите и политичките работници што книгата таму ги вбројува се означени како активисти; жртвите на теророт не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'knjazevac-pomenik':
      'Сите настрадани во Втората светска војна од подрачјето на општина Књажевац, по села (стр. 37–327), со раѓање и смрт: партизани, четници, стрелани и цивили заедно. Внесени се партизанските борци и, означени како активисти, комунистите, скоевците, одборниците и соработниците на партизаните; четниците, цивилите и оние што ги осудила новата власт не се. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'iskra-in-plamen-padli':
      'Од зборникот за НОБ во селата на некогашната општина Поље кај Љубљана: „Svoja življenja so dali za svobodo”, умрените од тие села по села, со годините на раѓање и смрт и местото на загинувањето. Внесени се само загинатите во НОВ; умрените во интернација и затвори, заложниците и другите жртви не се. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'cazinska-krajina-pali-borci':
      'Списокот на загинатите борци од Цазинска Крајина, по општини (Бихаќ, Босанска Крупа, Цазин, Велика Кладуша) и села, со името на таткото и годините на раѓање и загинување. Списокот на српските цивилни жртви од истата книга не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'derventa-pali-borci':
      'Списокот на загинатите борци од народноослободителната војна од подрачјето на општина Дервента, со раѓање, единица и место на загинувањето. Списокот на жртвите на фашистичкиот терор од истата книга не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'sanski-most-borci':
      'Списоците на борците од Санскиот срез по населби: загинатите во НОБ, носителите на Партизанската споменица 1941 и борците на НОБ живи на 15 мај 1945, со раѓање, занимање, стапување во НОБ и должност. Од третиот список внесени се борците (борец, воена должност или чин, единица) и, означени како активисти, одборниците и членовите на СКОЈ и АФЖ без воена должност; жртвите на фашистичкиот терор не се. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'rat-i-djeca-kozare':
      'Од книгата за децата на Козара во војната, поглавјето „Pali kao borci narodnooslobodilačkog rata”: 370 козарски момчиња и девојчиња помлади од 15 години кои загинале како борци, по општини, со местото и годините на раѓање и загинување (текст на znaci.org, без скенирана книга). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'krizani-v-boju-za-svobodo':
      'Книга за луѓето од селото Криж кај Трст во војната: животописите на загинатите (внесени се оние што биле во партизаните или во војската и, означени како активисти, активистите на Ослободителниот фронт и теренците), и табелите на Крижаните во НОВЈ и на борците на НОВ што живееле во Криж, со таткото, раѓањето, стапувањето во НОВ, чинот и единицата. Доброволците во Шпанија, Крижаните во италијански единици и депортираните не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'vinodolska-selca':
      'Од прилозите на книгата за Селце кај Цриквеница во војната: списокот на борците од Селце загинати во НОБ, со должноста, единицата, раѓањето и загинувањето, и првоборците и носителите на Партизанската споменица 1941. Внесени се и, означени како активисти, соработниците на НОД погубени во логорите. Списокот на организираните учесници во НОБ (само имиња, со членките на АФЖ и одборниците) и списоците на жртвите не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'susak-rijeka-spomenica':
      'Од прилозите на книгата за Сушак и Риека во НОБ: носителите на Партизанската споменица 1941 од подрачјето на општина Риека, име и место, како ги составил општинскиот одбор на СУБНОР. Списоците на членовите на КПЈ и СКОЈ од 1941 загинати во НОБ не се внесени, бидејќи не кажуваат кој бил борец. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'zene-vi-korpus-poginule':
      'Од зборникот документи за жените на Хрватска во НОБ (документ 427): пописот на загинатите другарки борци и раководителки во единиците на VI корпус на НОВЈ, што штабот на корпусот го составил на 23 декември 1944, со должноста и единицата, годината и местото на раѓање и кога и во која борба загинала. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'ludbreg-poginuli':
      'Списоци на борците загинати во двете борби за Лудбрег: од 17. славонска бригада во Лудбрег и Шемовец на 3 октомври 1943, од бригадата „Браќа Радиќ“ кај Шемовец истиот ден и од 17. славонска во Лудбрег на 6 јули 1944 (стр. 84–85, 287–289), со година и место на раѓање. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'dolomiti-v-nob-3':
      'Народните херои од Доломитите, ридовите западно од Љубљана, носителите на Споменицата 1941 и првоборците што загинаа, со датум и место на раѓање (стр. 667–671). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'sanitetska-sluzba-lekari':
      'Лекарите што го загубија животот во војната, со кратка биографија: од каде биле, кога влегле во НОВЈ, должност и единица, смрт (текст на znaci.org, без скенирана книга). Внесени се оние што биле во војската, а лекарите што како соработници на движењето биле убиени во позадината (го организирале востанието, ги криеле и лекувале партизаните) се означени како активисти. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'korosko-zdravstvo':
      'Ранетите и болните борци и активисти во Корушка до февруари 1944, пациентите на корушките партизански болници, корушките борци лекувани надвор од болниците и санитетскиот персонал, со кратка биографија (стр. 282–355). Внесени се борците и персоналот на партизанските болници, а политичките работници на теренот и лекарите и медицинските сестри што им праќале лекови на партизаните се означени како активисти. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'artileristi-prekomorci':
      'Списокот на загинатите артилерци прекуморци, Словенци и Истрани што од Италија и Африка дошле во артилериските единици формирани на Вис и во Италија, и списокот на командантите и комесарите на тие единици (стр. 227–234). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'virovitica-spomenica-1941':
      'Носителите на Партизанската споменица 1941 од општина Вировитица, четиринаесет биографии со фотографии (стр. 221–239). Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'vis-zrtve-nob':
      'Жртвите во НОБ од спомен-плочите на вишкото островје (стр. 516–520): загинатите во борбите и умрените од рани и болести од Вис, Комижа, Бишево, Окључна и селата под Хум, само име и татково име. Заложниците што Италијанците ги стрелаа во 1943 и умрените во усташките затвори не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец од островот што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'xxxi-divizija-stabi':
      'Штабовите на XXXI дивизија и на нејзините бригади, Градникова, Прешернова и Војкова (стр. 557–562): командантите, комесарите, нивните заменици и началниците на штабот, секој со времето кога бил на должноста, и кој од нив загинал. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    '15-brigada-stabi':
      'Командантите, политичките комесари, нивните заменици и началниците на штабот на 15. словенечка бригада и командантите и комесарите на нејзините баталјони (стр. 447–450), секој со времето кога бил на должноста и, каде што должноста така завршила, дека бил ранет, се разболел или загинал. Бригадата не е на сајтот: записот од книгата е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    '15-divizija-stabi':
      'Командниот состав на 15. дивизија на НОВ и ПО на Словенија (стр. 583–584): командантите, политичките комесари, нивните заменици и помошници и началниците на штабот, секој со времето кога бил на должноста. Дивизијата не е на сајтот: записот од книгата е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'jb-odred-stabi':
      'Штабовите на Јесеничко-бохињскиот одред, на неговите три баталјони и на школскиот логор, август 1944 – мај 1945 (стр. 354–356): командантите, политичките комесари, нивните помошници и заменици и началникот на штабот, секој со времето кога бил на должноста. Одредот не е на сајтот: записот од книгата е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'banijski-odredi-kadar':
      'Старешините на банискиот партизански одреди 1941–1945 (стр. 372–378): на малите одреди и селските групи борци од 1941, на Банискиот партизански одред и неговите баталјони, ударните баталјони, партизанските чети и двата одреди на Банија од 1944, по должности. Одредите не се на сајтот: записот од книгата е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'letalci-prekomorci-kader':
      'Раководниот кадар на 1. и 2. ловечка ескадрила на НОВЈ, на воздухопловниот одред на НОВЈ во Алжир и на 1. воздухопловен полк (стр. 322–325): чинот и должноста на секој, со времето кога ја вршел. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'niksicki-odred-pali-borci':
      'Имињата на паднатите борци од подрачјето на поранешната никшиќка околија и општината Херцег Нови (стр. 393–420): место и година на раѓање, место и година на загинување; и народните херои на Никшиќ и Херцег Нови, со биографија на секој (стр. 423–427). Речиси сите поминале низ Никшиќкиот одред, а загинале во бригадите, во одредот и на други должности. Страниците на znaci.org немаат текст, само слики: имињата се прочитани од сликите. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'teslic-u-nob-borci':
      'Списокот на борците од народноослободителната војна од општината Теслиќ (стр. 234–267) и списокот на загинатите и умрените борци (стр. 269–279), со биографија на секој. Списоците покрај борците ги бројат и одборниците и соработниците на НОД: внесени се само оние за кои записот вели дека биле борци или во НОВЈ, или наведува воена должност или единица на војската. Страниците на znaci.org немаат текст, само слики: имињата се прочитани од сликите. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'lovcenski-odred-pali-borci':
      'Загинатите, стрелани и умрени борци од НОВ 1941–1945 од територијата на Ловќенскиот партизански одред, по околии (цетињска, барска, которска) и села, со биографија на секој (стр. 611–713). Авторот меѓу паднатите борци ги брои сите од движењето што го загубиле животот, и активистите, а жртвите на теророт не; внесени се сите. Страниците на znaci.org немаат текст, само слики: имињата се прочитани од сликите. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој; другите се меѓу Другите борци.',
    'zene-1-dalmatinska':
      'Список на жените борци на бригадата од 1944–1945 (документ 368): должност и чин, датум и место на раѓање, кога стапиле во НОВ, одликувања и мислењето на штабот за секоја',
    '1-dalmatinska-komandni-sastav':
      'Командантите, комесарите, нивните заменици, началниците на штабот, интендантите, референтите за санитет, младинските раководители и разузнавачките офицери на штабот на бригадата и на секој баталјон од 6 септември 1942 до крајот на војната, со времето кога кој ја вршел должноста (стр. 435–443)',
    '1-dalmatinska-formiranje':
      'Старешините на штабот на бригадата, на политичкиот оддел, на баталјоните и четите на 6 септември 1942 во селото Добро кај Ливно: должност, година на раѓање, народност, занимање (стр. 55–58)',
    'zene-11-dalmatinska':
      'Список на жените борци на бригадата од 1944–1945 (документ 376): датум и место на раѓање, должност и чин, кога стапиле во НОВ, одликувања и мислењето на штабот за секоја',
    '11-dalmatinska-stabovi':
      'Старешините на штабот на бригадата со времето кога кој ја вршел должноста, на четите при штабот, превивалиштата и подофицерскиот курс, на штабовите на баталјоните и командите на четите, по должности (стр. 611–624)',
    'osjecka-zene':
      'Жените борци на Осиечката бригада по баталјони, како што ги попишал штабот на бригадата за I конгрес на АФЖ на Хрватска (документ 420): датум и место на раѓање, од кога се во партизани',
    'dalmatinci-prva-proleterska':
      'Борците на Првата пролетерска бригада од Далмација, со биографија за секого: раѓање, занимање, пат во НОБ и во бригадата, борби, судбина; и дополнителен список на оние за кои авторите не собрале податоци (стр. 467–754)',
    'crnogorski-bataljon':
      'Борците што стапиле во Првиот црногорски баталјон на Првата пролетерска во 1942, 1943, 1944 и 1945 и борците без целосни податоци: раѓање, занимање, кога стапиле во НОБ, судбина; на кирилица (стр. 713–795)',
    'rudarska-ceta':
      'Борците на Рударската чета (рудари од Трепча и Копаоник) кога влезе во Првата пролетерска во Рудо на 21 декември 1941, со биографија за секого (стр. 426–430)',
    'prva-proleterska-dopunski':
      'Припадниците на бригадата што редакцијата ги најде по списокот во првите три книги, со податоци за секого (стр. 1065–1071)',
    'prva-proleterska-garibaldi':
      'Италијанските војници што по капитулацијата на Италија им се приклучија на партизаните, со штабот на баталјонот, само имиња и должности (стр. 1072–1082)',
    'kotor-varos':
      'Списоците на загинатите, умрените и исчезнатите учесници во НОБ од општините Котор-Варош и Скендер-Вакуф по месните организации на СУБНОР (стр. 333–354), со раѓање, единица и смрт, и носителите на Партизанската споменица 1941 од двете општини (стр. 357). Внесени се и учесниците што не биле борци, означени како активисти или учесници. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'sokolac':
      'Списокот на загинатите борци од Соколац во Втората светска војна 1941–1945 (стр. 524–571), 503 кратки биографии: раѓање, стапување во НОВ, единица и загинување. Списокот на загинатите четници од истата книга не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'popovo-polje':
      'Прилогот „Борци од Попово поле загинати во НОБ” (стр. 419–430): раѓање, должност, место и ден на загинувањето. Списокот на жртвите на фашистичкиот терор од истата книга не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'bijelo-polje':
      'Прилозите на монографијата: носителите на Партизанската споменица 1941 (стр. 733–753) и загинатите борци во НОБ од бјелополската околија (стр. 778–886), со раѓање, единици и смрт. Списокот на борците во строј на Третата санџачка бригада на денот на формирањето (стр. 754–774) сè уште не е внесен, бидејќи имињата во скенот тешко се читаат; не се внесени ни загинатите во Априлската војна и жртвите на теророт. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'lezimir':
      'Статијата „Жртвите на селото Лежимир 1941–1945” (стр. 95–120): сите настрадани од Лежимир во Срем. Внесени се само борците, оние за кои списокот вели дека загинале во НОБ; жртвите на теророт и оние што ги убиле партизаните не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'prva-niska-gimnazija':
      'Прегледот на гимназијалците од разни генерации загинати во НОБ и жртвите на фашистичкиот терор (стр. 221–232): загинатите како борци на партизанските одреди и НОВЈ, а од убиените и стреланите оние што биле во движењето. Учениците што настрадале во интернација и при бомбардирањата не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'binovce':
      'Учесниците во НОБ од Биновце и Калабовце кај Сурдулица (стр. 24–25), само имиња, внесени како учесници, и петте загинати борци (стр. 26). Интернираните, жртвите на теророт и цивилните жртви не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'kremna':
      'Загинатите партизански борци од Кремна кај Прњавор и од спомен-плочата во Подвучјак (стр. 134–147), само имиња, носителите на Партизанската споменица 1941 и командантите на партизанските единици од прњаворското подрачје (стр. 171–172). Списоците на четниците и жртвите од истата книга не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'komani':
      'Бандиќите загинати во НОБ, од спомен-плочата во Загарач (стр. 223–224), и редовите од списоците на братствата за истите борци. Стреланите и жртвите од истата плоча и загинатите во поранешните војни не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'gornja-jablanica':
      'Народните херои и другите загинати првоборци од Горња Јабланица, по села (стр. 663–669), и носителите на Партизанската споменица 1941 (стр. 669–673), само имиња. Носителите на Албанската споменица и на Караѓорѓевата ѕвезда не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    '2-korpus-stabovi':
      'Списокот на командниот состав на штабовите на дивизиите и на штабот на 2. ударен корпус (стр. 463–465): командантите, политичките комесари, заменици и началниците на штабовите на корпусот, 2. пролетерска, 3. ударна, 29. и 37. ударна дивизија, Приморската оперативна група, италијанската дивизија »Гарибалди« и артилериската бригада на корпусот, со месеците на должноста. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'moslavina-spomenica-1941':
      'Прегледот на носителите на Партизанската споменица 1941 од подрачјето на Мославина (стр. 629–632), само имиња и прекари: родени во Мославина или подолго живееле таму, меѓу нив и раководителите на КП, СКОЈ, АФЖ и НОО. Одредот не е на сајтот; останатите се меѓу Другите борци.',
    'knezica':
      'Прилозите на книгата за селата на Кнежица под Козара: загинатите борци во НОБ, по села (стр. 451–463), со годината на раѓање и загинување и местото на смртта, носителите на Партизанската споменица 1941 (стр. 501–502) и преживеаните борци во НОБ од месното подрачје Кнежица (стр. 503–508), само имиња. Списокот на жртвите на фашистичкиот терор од истата книга не е внесен. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'kordunski-rekvijem':
      'Списокот на загинатите борци од поранешната општина Примишље 1941–1945 што го составил генералот Душан Ливада (стр. 176–191), по села, со кратка биографија; членовите на Партијата и СКОЈ, одборниците и членките на АФЖ што ги брои списокот се внесени како активисти. Внесени се и првите 49 носители на Партизанската споменица 1941 што од Слуњ се преселиле во Војводина (стр. 338–342). Списоците на жртвите на теророт и на умрените од тифус не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'sencur-padli-borci':
      'Списокот на загинатите борци, активисти и другите жртви на фашистичкото насилство од подрачјето на општината Шенчур кај Крањ, по села, со биографија (стр. 359–368), и списокот на борците на Кокршката чета, декември 1941 – пролет 1942, со последното живеалиште и денот на доаѓањето во четата (стр. 381–384). Внесени се борците и, означени како активисти, луѓето на ОФ и на Партијата; заложниците, иселените и другите убиени без удел во движењето не се внесени. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
    'klanjscek-komandni-sastav':
      'Прилог 1, „Список на командниот состав на повисоките единици на НОВ и ПО Словенија” (стр. 393–400): командантите, политичките комесари, нивните заменици и началниците на штабовите на Главниот штаб, покраинските штабови, групите одреди, оперативните зони, корпусите и дивизиите, со деновите на должноста и местото на загинувањето. Книгата не припаѓа на една единица: записот од неа е додаден на записот на секој борец што е на сајтот и за кого сигурно се знае дека е тоа тој.',
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
    'druga-licka-staresine':
      'The commanders, commissars, their deputies, operations and intelligence officers and quartermasters of the brigade staff and the battalion staffs from its formation to the end of the war, most with a short biography (pp. 349–360)',
    'treca-proleterska-brigada': 'Brigade history, in the series Ratna prošlost naših naroda, vol. 144',
    'treca-proleterska-poginuli-knj3':
      'Partisans and officers who were killed or died, year by year, 1942–1945 (1,374 names; this copy lacks the pages for early 1944)',
    'treca-proleterska-formiranje':
      'The same roll as in Žarko Vidović’s brigade history, in Cyrillic, as the editors of the memoir collection arranged it, by battalion and company',
    'ljubljanska-brigada': 'History of the Ljubljana Brigade',
    '13-proleterska-spisak': 'The fallen and the survivors (part three of the brigade history)',
    '2-dalmatinska-proleterska': 'Roll of the 2nd Dalmatian Proletarian Brigade',
    '2-dalmatinska-stabovi':
      'The officers of the brigade staff with the time each held the post, of the companies at the staff, the brigade hospital, the battalion staffs and company commands, by duty (pp. 473–486)',
    '4-splitska-brigada': 'The brigade’s fallen and survivors',
    'prva-vojvodjanska': 'Roll of the 1st Vojvodina Brigade',
    '5-kozaracka': 'The brigade’s Partisans and officers who were killed, went missing or died',
    '2-vojvodjanska': 'Partisans and officers of the 2nd Vojvodina Brigade',
    '8-krajiska': 'Members of the 8th Krajina Brigade who were killed or died in the war',
    '8-krajiska-sjecanja-poginuli':
      'The brigade’s fighters who fell or died in the war, from its collection of memoirs: father, year and place of birth, when and where each fell, duty.',
    '6-krajiska': 'The brigade’s Partisans and officers who were killed or died, with a supplementary list',
    '4-krajiska': 'Partisans and officers of the 4th Krajina Brigade who were killed, died or went missing',
    '3-krajiska-proleterska': 'Fallen Partisans of the 3rd Krajina Proletarian Brigade, with their basic personal details',
    '17-slavonska-poginuli': 'Fallen Partisans of the 17th Assault Brigade',
    '17-slavonska-prezivjeli': 'Surviving Partisans of the 17th Assault Brigade',
    '25-srpska-divizija': 'Fallen Partisans and officers of the 25th Division',
    '1-sumadijska': 'Lists of fallen Partisans and officers, and of Partisans who survived the war',
    '18-slavonska': 'Partisans and officers of the 18th Assault Brigade who were killed or died, and a list of survivors',
    '4-banijska': 'Roll of the 4th Banija Brigade',
    '4-banijska-starjesine': 'The commanders, political commissars, their deputies, chiefs of staff and other officers of the brigade staff and the battalion staffs, by duty, names only (pp. 52–53)',
    '4-srpska': 'Roll of the 4th Serbian Assault Brigade',
    '7-vojvodjanska': 'Roll of the 7th Vojvodina Assault Brigade (survivors, the fallen, and those who died after the war)',
    '19-bircanska': 'Roll of the 19th Birač Brigade',
    '2-krajiska': 'Partisans and officers of the 2nd Krajina Brigade who were killed or died in the war',
    'tuzlanski-odred': 'Roll of the Tuzla Partisan Detachment',
    'uzicki-odred': 'Members of the Užice Partisan Detachment killed in the war of 1941–1945',
    'pozega-cete':
      'The rolls of the 1st and 2nd Požega companies of the Užice Detachment, 1941–1942, the Pilatovići company on the day it was formed, the fighters guarding the town, the villagers who fought in other units in 1941, the 1st company of the detachment’s 5th battalion in 1944, and the fallen of the Požega company of the 2nd Proletarian Brigade, by village, as the companies’ survivors reconstructed them after the war. The lists of the partisan workshops’ workers, sympathizers and refugees were not entered.',
    '14-srpska': 'Fallen Partisans and officers of the detachment and of the 14th Serbian Brigade',
    '7-crnogorska-omladinska': 'Fallen Partisans of the 7th Montenegrin Youth Brigade',
    '7-crnogorska-zbornik-poginuli':
      'The brigade’s fallen fighters and officers from its collection of memoirs: birth, company and battalion, when and where each fell.',
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
    'prva-proleterska-stroj-u-rudom':
      'The men and women in the line-up at Rudo on 21 December 1941, when the brigade was formed, by staff, battalion and company: birth, trade, duty and what became of each in the war (pp. 433–492). An asterisk by a name marks one who fell in the war.',
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
      'The brigade’s Partisans and officers who were killed, battle by battle, from Sućuraj on 22 September 1943 to Ilirska Bistrica on 6 May 1945 (pp. 353–366 of the book), and the officers of the brigade staff and the battalion staffs, with the time each held the post (pp. 339–342)',
    '3-makedonska':
      'The brigade’s Partisans who were killed: where they came from, the year of birth, where and when they fell (pp. 359–368 of the book)',
    '3-krajiska-spisak-boraca':
      'Every Partisan who fought in the brigade from 22 August 1942 to 9 May 1945, survivors and the fallen: where they came from, occupation, when they joined the struggle and the brigade, duty and fate; with a supplement and an addendum (pp. 579 ff.)',
    '3-krajiska-sastav-1942':
      'Every Partisan and officer of the brigade in mid-November 1942, by staff, political department, quartermaster service, battalion, company and platoon: duty, year and place of birth, nationality, occupation, and for many what became of them later (text on znaci.org, with no scanned book)',
    '6-krajiska-prezivjeli':
      'The brigade’s Partisans who survived the war, names only, with a later list (pp. 747–762 of the book)',
    '6-krajiska-kadar':
      'The brigade’s officers and cadre of 1942–1943 by duty, from its commanders to the company nurses, names only (pp. 739–745 of the book)',
    '32-divizija-borci':
      'Partisans of the division’s staff, its attached units, the Braća Radić, Matija Gubec, Mihovil Pavlek Miškina and 1st Zagorje Assault brigades, and some with incomplete details: year and place of birth, nationality, occupation, when they joined the army, fate; each is listed under every unit he fought in (pp. 431–662 of the book)',
    '32-divizija-kadar':
      'The officers of the division staff and the units at it, of its four brigades, their battalions and escort companies, by duty (pp. 286–295)',
    '18-hrvatska':
      'The brigade’s Partisans, survivors and the fallen: year and place of birth, nationality, occupation, when they joined the brigade, duty and fate (pp. 582–696 of the book)',
    '18-hrvatska-starjesine':
      'The officers of the brigade’s staff, its battalions and companies and the units attached to the staff, by duty, names only (pp. 573–581 of the book)',
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
    '4-proleterska-formiranje':
      'The brigade’s fighters and officers on the day it was formed, 17 June 1942, by staff, battalion and company: duty, place and year of birth, trade, membership of the KPJ and SKOJ, and what became of each.',
    '3-vojvodjanska':
      'Lists of the brigade’s Partisans and officers: those killed, those whose fate remains unknown, and the survivors (pp. 479 ff.)',
    'kalnicki-odred':
      'List of the members of the Kalnik Partisan Detachment, killed and surviving (pp. 311 ff.)',
    'kalnicki-odred-kadar':
      'The leaders of the first armed groups and formations on Kalnik in 1941–1942, of the detachment’s staff, its battalions, companies and platoons, with the time each held the post (pp. 282–303, 305)',
    'posavsko-trebavski-odred':
      'List of the detachment’s members by the municipality they came from (pp. 313 ff.)',
    '8-kordunaska-divizija':
      'List of the Eighth Division’s fallen, by surname, with the brigade each served in (pp. 806 ff.)',
    '8-kordunaska-divizija-kadar':
      'The commanders, political commissars and chiefs of staff of the division, its brigades and battalions, with how long each held the post and what became of him (pp. 762–775)',
    'cankarjeva':
      'List of the brigade’s members who survived the war (pp. 815 ff.) and of its fallen (pp. 847 ff.)',
    'cankarjeva-kader':
      'The brigade’s commanders, political commissars, their deputies and chiefs of staff, and its battalions’ commanders and commissars, with how long each held the post (pp. 810–814)',
    'gubceva':
      'List of the brigade’s members who survived the war (pp. 979 ff.) and of its fallen (pp. 1016 ff.)',
    'gubceva-kader':
      'The brigade’s commanders, political commissars, their deputies and chiefs of staff, and its battalions’ commanders and commissars, with how long each held the post (pp. 975–978)',
    'dvanajsta':
      'Lists of the brigade’s fallen and of those who survived the war, at the end of the book',
    'dvanajsta-kader':
      'The commanders, political commissars, their deputies and chiefs of staff of the brigade and its battalions, with how long each held the post; the heads of its intelligence centre, its quartermasters, medical officers and SKOJ secretaries, names only (pp. 571–574)',
    'gradnikova':
      'Lists of the Partisans killed in the brigade and of its other members, who survived the war or did not fall while in it (pp. 840 ff.)',
    'gradnikova-kader':
      'The brigade’s commanders, political commissars, their deputies and chiefs of staff, with the time each held the post, and short biographies of the brigade’s People’s Heroes (pp. 791–799)',
    'zidanskova':
      'List of the brigade’s members; for those killed, the years of birth and death (pp. 731 ff.)',
    'zidanskova-kader':
      'The brigade’s commanders, political commissars, their deputies, chiefs of staff and SKOJ secretaries, with how long each held the post (pp. 729–730)',
    'skofjeloski-odred':
      'List of the detachment’s members, names only, as the surviving files of the detachment record them (pp. 314 ff.)',
    'istrski-odred':
      'List of the detachment’s members (pp. 827 ff.), without the fallen, and of the fallen with a short account of each (pp. 849 ff.)',
    'istrski-odred-kader':
      'The commanders, political commissars, their deputies and chiefs of staff of the detachment, its battalions and companies, with how long each held the post (pp. 821–826)',
    'zapadnodolenjski-odred':
      'List of the detachment’s members (pp. 333 ff.) and of its fallen (pp. 340 ff.)',
    'braciceva':
      'Lists of the brigade’s fallen (pp. 722 ff.) and of those who survived the war (pp. 746 ff.)',
    'tomsiceva-1':
      'Lists of the fighters of the units the brigade grew from: the strike group of the 3rd Ljubo Šercer Battalion, Daki’s flying strike patrol, the Proletarian strike patrol and company, and the 1st Slovene Proletarian Strike Battalion Tone Tomšič (book 1, pp. 535 ff.)',
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
    '19-sjevernodalmatinska-kadar':
      'The commanders and political commissars of the division and its brigades, with how long each held the post, the members of its political department 1943–1945, and its People’s Heroes, with a short biography (pp. 240–252)',
    '21-srpska':
      'The brigade’s (2nd Šumadija) Partisans who were killed or survived, and others who fought in it: parents, birth, duty, when they joined and where they fell (pp. 387–472)',
    '14-hercegovacka':
      'Everyone who served in the brigade: year and place of birth; the fallen, with their unit and where they fell (pp. 243–287)',
    '14-hercegovacka-komandni-sastav':
      'The brigade staff, the battalion staffs, company commands, escort platoons, platoon commanders and political delegates and the units at the staff, by duty, with the time each held the post (pp. 234–242)',
    '5-vojvodjanska':
      'The brigade’s soldiers and officers: year and place of birth, trade, duty in the brigade, where they fell or went missing (pp. 429–584)',
    '6-vojvodjanska':
      'The fallen soldiers and officers: year and place of birth, date and place of death, where they were buried (pp. 175–199)',
    '6-vojvodjanska-stabovi':
      'The members of the brigade staff, of its battalions’ staffs and of the company commands, by duty, names only (pp. 171–174)',
    '13-vojvodjanska':
      'The brigade’s members: names, here and there a nickname or a place; the author notes the list is incomplete (pp. 771–793)',
    '7-srpska':
      'The soldiers in early May 1944 by village, and those killed, dead or missing: birth, when they joined, where they fell (pp. 459–501)',
    '15-srpska':
      'The brigade’s soldiers and officers, its fallen and its wounded: birth, duty, when and where they fell or were wounded (pp. 155–173)',
    '8-srpska':
      '“Nezaboravnik”, the brigade’s fallen: birth, date and place of death (pp. 265–297)',
    '10-srpska':
      'The fallen soldiers and officers: birth, when they joined, duty, where they fell and were buried (pp. 488–541)',
    '23-srpska':
      'The soldiers and officers who were killed or died: year and place of birth, trade, when they joined, their unit, where they fell and were buried (pp. 352–388)',
    '12-srpska':
      'The soldiers and officers who were killed or died: year and place of birth, trade, when they joined, their unit, where they fell and were buried (pp. 355–400)',
    '20-srpska':
      'The soldiers and officers who were killed or died: year and place of birth, trade, when they joined, their unit, where they fell and were buried (pp. 321–385)',
    '1-konjicka':
      'The fallen soldiers and officers (birth, where they fell) and the brigade’s wartime list of officers and men, names only (pp. 317–327)',
    'toplicki-odred':
      'The detachment’s men on the day it was formed, its fallen and dead soldiers and officers, and the People’s Heroes who fought in it, with their photographs (pp. 302–344)',
    'karlovacka':
      'The brigade’s soldiers and officers on the day it was formed at Hrašće, 5 March 1944, and its fallen soldiers and officers (pp. 379–414)',
    'karlovacka-kadar':
      'The brigade staff and the staffs of its four battalions with the time each held the post and what became of him, the company and platoon commanders, commissars and delegates, the companies and platoons at the staff, the rear (pp. 371–378)',
    '14-primorsko-goranska':
      'The brigade’s fallen, with their birth, duty and where they fell (pp. 227–264)',
    '22-divizija':
      'The division’s fallen soldiers and officers, by brigade: birthplace, and the day and place they fell (pp. 445–476)',
    '34-divizija':
      'The division’s fallen soldiers and officers: rank, brigade, birth, when they joined, and where and when they fell (pp. 401–432)',
    '34-divizija-kadar':
      'The officers of the division staff, its party committee, political department, intendance and medical service, of its four brigades, the partisan detachments and the units at the division staff, by duty (pp. 389–399)',
    '4-sandzacka':
      'The fallen soldiers and officers (birth, where they fell) and the wounded, with where and when they were wounded (pp. 460–485)',
    '3-primorsko-goranska':
      'The brigade’s officers and company medics, with their duties, and its fallen, with their birth and where they fell (pp. 234–259)',
    '3-primorsko-goranska-stabovi':
      'The members of the brigade staff and the battalion staffs and the officers of its independent units, by duty, with how long each held it and how it ended (pp. 227–233)',
    '13-hercegovacka':
      'The brigade’s fallen soldiers and officers (birth, day and place of death) and everyone who fought in it, names only (pp. 316–347)',
    '13-hercegovacka-starjesine':
      'The brigade staff and the units at the staff, the battalion staffs and company commands, by duty, with the time each held the post (pp. 305–315)',
    '12-hercegovacka':
      'The brigade’s fallen soldiers and officers, by municipality: birth, duty, where and when they fell (pp. 207–220)',
    '1-bokeljska':
      'The brigade’s fallen and dead, and those missing in battle: battalion, birth, where and when they fell (pp. 315–321)',
    '1-bokeljska-spisak':
      'The brigade’s roll from its formation on 5 October 1944 to the end of the war, by unit: the staff, the battalions and the units at the staff, each fighter’s and officer’s duty and name (pp. 291–314). A man transferred to another unit was entered there too, so some stand twice. The pages on znaci.org have no text, only images: the names were read from the images.',
    '6-dalmatinska':
      'The brigade’s fallen: where they came from, where and when they fell (pp. 259–271)',
    '6-dalmatinska-kadar':
      'The commanders, commissars, their deputies, chiefs and other officers of the brigade staff and the battalion staffs, by duty, names only (pp. 257–258)',
    'osjecka':
      'The brigade’s fallen and dead, and its survivors, by the municipality they were born in (pp. 207–254)',
    'osjecka-rukovodioci':
      'The brigade’s commanders, commissars and chiefs of staff, its battalions’ commanders and commissars, and its company commanders and commissars, names only (pp. 203–206)',
    '1-zagorska':
      'The brigade’s fallen fighters and officers, 8 May 1944 to 15 May 1945: year and place of birth, when and where they fell (pp. 191–205)',
    '6-crnogorska':
      'The brigade’s fallen Partisans and officers, with those who died of wounds or illness: birth, duty, where and when they fell (p. 871 on)',
    '11-krajiska-poginuli':
      'The brigade’s fallen, by municipality: birth, nationality, occupation, when they joined the army, duty, where and when they fell (pp. 439–463)',
    '11-krajiska-zene':
      'The women who fought in the brigade, names only (p. 425)',
    '3-banijska':
      'The brigade’s officers and fighters, names only (pp. 195–205)',
    '8-banijska-poginuli':
      'The brigade’s fallen and dead, 7 September 1942 to 6 December 1944: birth, occupation, when they joined, duty, where and when they fell (pp. 247–312)',
    '8-banijska-kadar':
      'The brigade staff, its political department and the staffs of its five battalions, by duty (pp. 244–246)',
    'macvanski-odred':
      'The fighters of the Mačva (Podrinje) Partisan Detachment, part one (July 1941 – March 1942), by the place they joined from, with details of each (a text on znaci.org, no scan of the book; part two is not published)',
    'posavski-odred':
      'The fighters of the Posavina Partisan Detachment in 1941: command, hospital and battalions, with details of each (pp. 565–742)',
    '51-divizija':
      'The 51st Vojvodina Division’s fallen and missing in the Battle of Batina, November 1944: birth, duty, where and when they fell (pp. 469–501)',
    '51-divizija-savic':
      'The fighters and officers of the division who fell from its formation, 1 November 1944, to the end of the war, 15 May 1945, by brigade: the 7th, 8th, 12th and 14th (Slovak), the artillery brigade and the staff units; birth, duty, where and when they fell (pp. 219–288)',
    'borci-sutjeske-vrhovni-stab':
      'The roll of the Sutjeska: every member of the Supreme Headquarters, its services, the Escort Battalion and the British military mission in the battle, with details of each and what became of them by the end of the war.',
    'vtr-grmec':
      'The workers of the Supreme Headquarters’ military workshop in Grmeč, 1942–1943, with their trade and home town, those who fell or died during the war and after it, the workshop’s guards and the workers of the Drvar foundry (pp. 361–364).',
    'borci-sutjeske-1-proleterska-divizija':
      'The roll of the Sutjeska: the division staff, its services and escort units in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-2-proleterska-divizija':
      'The roll of the Sutjeska: the division staff, its services and escort units in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-3-udarna-divizija':
      'The roll of the Sutjeska: the division staff, its services and escort units in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-7-banijska-divizija':
      'The roll of the Sutjeska: the division staff, its services and escort units in the battle, with details of each and what became of them by the end of the war.',
    'borci-sutjeske-centralna-bolnica':
      'The roll of the Sutjeska: the Central Hospital’s staff, and wounded whose own unit could not be established, with details of each and what became of them by the end of the war.',
    '3-licka':
      'The roll of the brigade’s fallen, dead and missing, and its People’s Heroes (pp. 361–413).',
    '5-proleterska-partizanke':
      'Life stories of the brigade’s women Partisans: birth, the way into the war, duties in the brigade, wounds and decorations, life after the war (pp. 43–278).',
    '16-banijska-poginuli':
      'The roll of the brigade’s Partisans and officers killed from 26 December 1942 to 30 June 1943, with year and place of birth and where each fell (pp. 201–247).',
    'pozarevacki-odred':
      'The roll of the detachment’s fighters from 1941 to October 1944, with details of each (pp. 238–307; compiled by Miodrag Stojanović Kole).',
    '1-proleterski-bataljon':
      'The roll of the battalion’s fighters, with year and place of birth and what became of each (pp. 262–277).',
    '4-pomorski-sektor':
      'The roll of the 4th Naval Coastal Sector, 1943–1945, drawn up by the sector’s veterans’ section and the author (4,702 names, with where each came from), and the sector’s fallen and dead, with their duty and how they died (pp. 418–478).',
    '4-pomorski-sektor-stab':
      'The sector’s commanders, political commissars, their assistants and chiefs of staff, with the time each held the post (Appendix X, p. 485)',
    'viski-bataljon':
      'The roll of the Vis Volunteer Battalion at the end of January 1944: its command, companies, platoons and the Biševo and Oključna sections (pp. 538–539).',
    'kokrski-odred-1':
      'The roll of the first Kokra Detachment, June 1942 - January 1943, by staff, battalion and company: where each came from, their duties and what became of them (pp. 509–525).',
    'kokrski-odred':
      'The roll of the second Kokra Detachment, the author’s reconstruction from the detachment’s own lists and papers: the staffs, intelligence centre and posts, courier stations, medical staff, workshops and the battalions by company and period, with years of birth and who fell (pp. 453–478).',
    'cankarjev-bataljon':
      'The battalion’s order of battle at Dražgoše, its Spanish Civil War veterans and narodni heroji, its fallen battle by battle, 1941–1942, the surviving holders of the Partisan Commemorative Medal 1941 and the other survivors of Dražgoše (pp. 338–346).',
    'novosadski-odred':
      'The members of the Novi Sad Partisan Detachment in 1941 and in 1944: name, duty, where each came from and since when (pp. 85–92).',
    'deveta':
      'The roll of the 9th Slovene Brigade “Kočevska”: name, year and place of birth, and for the fallen the year and place of death (pp. 425–446).',
    'deveta-kader':
      'The brigade’s commanders, political commissars, their deputies and chiefs of staff, and its battalions’ commanders and commissars, with how long each held the post and who fell in it (pp. 401–404)',
    '4-prekomorska':
      'The brigade’s fallen and dead, and its officers: the staff, the base command, the battalions, the independent company and the companies (pp. 327–333).',
    '9-srpska':
      'The line at Rečica: 377 fighters on the day the brigade was formed, 11 March 1944; the officers of the brigade, its battalions and companies with the dates of their duties; the nurses and women fighters. The book’s roll of every fighter with a short biography (pp. 47–372) is not on znaci.org.',
    'kozjanski-odred':
      'Every man and woman of the Kozjansko Detachment, 3,495 people from its founding to its disbanding, with date and place of birth, joining the partisans, trade and a note (where each served, who fell); the pages are black and white here, the text as in the book.',
    'proleterski-bataljon-bk':
      'The battalion’s fighters: each one’s biography beside his photograph, from his birth and coming to the Kozara, Grmeč or Drvar proletarian company to his death or the end of the war (pp. 256–362).',
    '1-tenkovski-bataljon':
      'The roll of the tank platoon of the Lika partisan detachments, the 1st Corps’ tank company and the tank battalion of the Croatian General Staff (251 names, pp. 337–340).',
    '3-diverzantski-odred':
      'Every fighter and officer of the 3rd sabotage group, company, battalion and detachment (names, marking the fallen and those who died after the war), and the fallen saboteurs with their duty and year (appendix IV, pp. 587–591).',
    '1-2-prekomorska':
      'The fallen of both brigades (birth, when and where each fell), and the officers in the Carbonara and Gravina camps, on Korčula, Hvar and Vis, and the companies’ officers (pp. 357–372).',
    '5-prekomorska':
      'The brigade’s fallen (256: birth, when and where each fell), and the officers of the brigade, its battalions and companies (pp. 283–301).',
    'sercerjeva':
      'The volunteers of the Šercer Brigade from its founding on 6 October 1942 to the end of February 1943 (name, partisan name and place), and its fallen to the end of 1943, by the place and day they fell (pp. 509–523).',
    'kosovelova':
      'The fallen, the missing and those who died of wounds (504 names: birth, home, when and where each fell), and the officers of the brigade and its battalions with the dates of their duties (pp. 803–824).',
    'eskadrile-novj':
      'The rolls of the Yugoslav Army’s first and second squadrons (RAF 352 and 351 Squadrons): service number, rank, duty, birth and how each came to the squadrons, from the Middle East, from Italian captivity or from home; at the end, names whose squadron was not established (pp. 331–354).',
    '42-vazduhoplovna':
      'The division’s men by regiment (the 421st, 422nd and 423rd Air Regiments), staff, independent company and aircraft workshops: rank and duty (pp. 291–321).',
    '18-srpska':
      '“They fought in the 18th Serbian Brigade”: 5,047 fighters and officers by the author’s count, of them 780 fallen, 787 wounded, 47 missing and 49 dead of illness, with year and place of birth, duty and where each fell or was wounded (pp. 313–426).',
    '5-srpska':
      'The brigade’s fallen and dead fighters and officers (appendix 2): year and place of birth, trade, when each joined the army, battalion and duty, when and where they fell and where they are buried (pp. 450–510).',
    'cacanski-odred':
      'The detachment’s fallen, by district (Dragačevo, Ljubić, Trnava, Takovo, Čačak) and village: father, trade, birth, the battalion each fought in, and how and where they died.',
    'mostarski-bataljon':
      'The fighters of the Konjic Battalion (September 1941 — June 1942), the Mostar Battalion (June 1942 — June 1943) and the Mostar Battalion in the Mostar Partisan Detachment (June 1943 — May 1944), each with a short biography: birth, trade, SKOJ and Party membership, when they joined, duty and fate (pp. 329–392).',
    '13-krajiska':
      'Two lists: the fighters and officers in the brigade in August and September 1943, with village, duty and, for the fallen, when and where they fell and where they are buried; the members of the brigade’s Communist Party organisation in May 1945, with the day each joined the Party and duty (pp. 365–404).',
    'pozega-pali':
      'Dragoljub Munjić’s appendix: the fallen fighters, the victims of the fascist terror and the civilian dead of the Požega district, by village, with birth, unit and how each died. The fighters are included and, marked as activists, the movement’s helpers, committee members and the workers of the partisan workshops; civilians and soldiers of the old Yugoslav army are not. The book belongs to no single unit: its entry is added to the record of every fighter on the site who is surely the same man.',
    'cacanski-kraj-pali':
      'The dead of the Čačak region, 1941–1945, by district (Dragačevo, Ljubić, Takovo, Trnava, Čačak) and village: father, trade, birth, unit and how each died. The fighters are included and, marked as activists, the members of the party and SKOJ, committee members, helpers of the movement and the workers of the partisan workshops of 1941; civilian victims and Chetniks are not. The book belongs to no single unit: its entry is added to the record of every fighter on the site who is surely the same man.',
    '1-krajiska':
      'The brigade’s fallen, dead and missing, 2,127 names: birth, when each joined the struggle and the brigade, company and battalion, duty, when and where they fell and where they are buried (pp. 331–442). Researched and compiled by Slobodan Spegar Spego.',
    'pionirska-ceta':
      'The roll of the company the author led as its commander: birth, when each became a fighter, duty in the company and life after the war (pp. 125–132).',
    'zbornik-heroja-1957':
      'Portraits of the People’s Heroes proclaimed up to 1957: birth, the way into the war, death or life after it, and the day each was proclaimed. The book belongs to no single unit: a portrait is added to the record of each hero on the site where the match is certain.',
    'narodni-heroji-1982-1':
      'The lives of all the People’s Heroes, second edition (1982), volume 1 (A–M): birth, life before the war, the way into it, death or life after it, and the day each was proclaimed. The book belongs to no single unit: a life is added to the record of each hero on the site where the match is certain.',
    'narodni-heroji-1982-2':
      'The lives of all the People’s Heroes, second edition (1982), volume 2 (N–Ž): birth, life before the war, the way into it, death or life after it, and the day each was proclaimed. The book belongs to no single unit: a life is added to the record of each hero on the site where the match is certain.',
    'trebinjci-pali':
      'The memorial book of the Trebinje veterans’ association (1974): the fighters of the municipality who fell in the war (pp. 13–96) and fighters from all over Yugoslavia who were killed near Trebinje (pp. 159–174), with birth, units and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s list of civilian victims of fascist terror was left out.',
    'pali-za-lepsa-svitanja':
      'Mothers of People’s Heroes tell of their sons and daughters (1967); above each story stands a short life of the hero: birth, trade, the Party, the war, death and the day proclaimed. The book belongs to no single unit: a life is added to the record of each hero on the site where the match is certain.',
    'ofanziva-1942-poginuli':
      'The fighters of the 1st, 2nd, 3rd and 4th Proletarian Brigades killed or missing on the march into western Bosnia, 24 June to 30 September 1942 (pp. 698–711), by brigade and battalion, with birth, trade and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hak-20-gospic-perusic':
      'From the Karlovac Historical Archive’s collection (vol. 20): the fighters from the districts of Gospić and Perušić who fell in 1941–1945 (pp. 986–1045) and the holders of the Partisan Commemorative Medal 1941 (pp. 1194–1209), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-10-korenica-udbina':
      'From the Karlovac Historical Archive’s collection (vol. 10): the fighters from the districts of Korenica and Udbina who fell in 1941–1945 (pp. 990–1039), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hronika-prigrevica':
      'A history of the village of Prigrevica near Apatin (1997), settled after the war by fighters’ families from Lika and Banija: the Partisans of those families who were killed, died or went missing (pp. 307–331) and the holders of the Partisan Commemorative Medal 1941 (pp. 339–353), with birth, unit and death or life after the war. The lists of fighters who joined later, names only, were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-medak':
      'A history of the villages of the former Medak municipality near Gospić (2004): the Partisans of those villages who were killed fighting the enemy, village by village (pp. 434–465), and the holders of the Partisan Commemorative Medal 1941 (pp. 506–513), with birth, unit and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-hasani':
      'A history of the village of Hašani near Bosanska Krupa (1991): the village’s Partisans who were killed, died or went missing (pp. 135–138), the holders of the Partisan Commemorative Medal 1941 (p. 138) and the other surviving veterans, names only (p. 139). Survivors credited with service for work for the movement were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-podgocka-naselja':
      'A history of the villages below Mount Goč near Trstenik (2008): the fighters from Gornji Ribnik killed on the Syrmian Front (pp. 194–195) and the Partisans from Odžaci who were killed or went missing in the war (pp. 344–345). The lists of those killed by the Chetniks and of civilian victims of fascist terror were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-prekopcelica':
      'A history of the village of Prekopčelica near Lebane (2012): the village’s fighters by the brigades and detachments they served in (pp. 121–124) and those killed with the Partisans (p. 126). Members of rear units and veterans named only by their relatives were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-brezovica-stublica':
      'A history of the villages of Brezovica and Stublica near Trstenik (2015): the veterans from Brezovica called up in October 1944 and those killed or missing in the war (pp. 113–115), and the veterans from Stublica (pp. 478–479). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-makce':
      'A history of the village of Makce near Veliko Gradište (2000): the villagers killed, dead or missing in the war, most of them fighters of the 25th Division (pp. 62–64), and the veterans who survived the war, with year of birth and decoration (pp. 64–66). The civilian victims of fascist terror on the same list were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-donje-vidovo':
      'A history of the village of Donje Vidovo near Paraćin (1997): of its list of villagers killed in the war, only those the book marks as fighters were entered (p. 127), not the victims of fascist terror and the others killed. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-petrlas':
      'A history of the village of Petrlaš near Dimitrovgrad (2001): the fighters from Petrlaš in the 1st Caribrod, the 8th, 10th and 12th Serbian Brigades, the 13th Replacement Battalion and other units of the army (p. 348). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-labukovo':
      'A history of the village of Labukovo near Svrljig (2007): the villagers killed in the war, 1941–1945 (p. 44); those the book lists as hostages, victims of terror and camp inmates were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-beli-breg':
      'A history of the village of Beli Breg near Aleksinac (2009): the villagers who fought in the war, with year of birth, the day they joined their unit and the unit, and those killed or who died soon after the war (pp. 113–114). The prisoners, internees and soldiers of the Yugoslav army in the same table were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hronika-donja-gorevnica':
      'A history of the village of Donja Gorevnica near Čačak (1996): of its list of the village’s fallen fighters and victims, only the fighters were entered (pp. 233–238), not the victims of terror and the soldiers of the Yugoslav army. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'ostrvica':
      'A history of the village of Ostrvica near Gospić (2003): its census of households with what changed in the war (pp. 617–663), each member of the family and what became of them. Only the fighters were entered, those whose entry calls them a fighter or gives a military duty or unit; civilians, victims of terror and men of the NDH army were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'divoselo':
      'A history of the villages of Divoselo, Čitluk and Ornice near Gospić: their fighters and officers killed in 1941–1945, each with a short biography (pp. 425–435). Two soldiers of the Yugoslav army killed in the April war were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'mogoric':
      'A history of the village of Mogorić in Lika: the 110 fallen fighters of the village from the plaque at its memorial hall, each with a short biography (pp. 191–199), and the village’s holders of the Partisan Commemorative Medal 1941 (p. 201). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'vrebac':
      'A history of the villages of Vrebac, Zavođe and Pavlovac near Gospić: their Partisans killed from 1941 to 1945, village by village, each with a short biography (pp. 298–311). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'licko-petrovo-selo':
      'A war chronicle of the former municipality of Ličko Petrovo Selo (1985): its fallen fighters by village (Ličko Petrovo Selo, Novo Selo, Željava, Arapov Do, Rešetar, Zaklopača and Lisina, Donji Vaganac), in a table with the years of birth, of joining the army and of death, the place of death, the unit and the duty (pp. 207–214). Those who died of typhus, hunger and mines were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'bosansko-grahovo':
      'The fallen fighters of the war of liberation from the Bosansko Grahovo area, village by village, each with a short biography (pp. 642–697). The list of the victims of fascist terror that follows was left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'staromajdansko':
      'The fallen fighters and the victims of fascist terror of the Stari Majdan area near Sanski Most, village by village, each with a short biography (pp. 177–246), and lists of the fighters and participants of the war who had died or were living in 1983 and of the holders of the Partisan Commemorative Medal of 1941, names only (pp. 247–266). The fallen fighters and the medal holders were entered; the fighters and participants of the name lists are marked as participants, since the list doesn’t say who fought and who was an activist; the victims of terror were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'han-pijesak':
      'The fighters of the Han Pijesak municipality and those who fell on its ground: the dead of Pjenovac, 21 January 1942, and of the second enemy offensive, most of them of the 1st Proletarian Brigade (pp. 106–109), the people’s heroes and notable fighters (pp. 147–150), and the fallen of 1941–1945, each with a short biography (pp. 151–161). The party and field workers the list counts among its dead are in too, marked as activists. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'skakavac':
      'The fighters and participants of the war of liberation from the village of Skakavac near Bosanski Petrovac: the first fighters, holders of the 1941 Partisan Commemorative Medal (pp. 163–165), the participants who survived the war (pp. 166–173) and the fallen (pp. 173–177), each with a short biography, and the members of the people’s liberation committees, the AFŽ committees, the youth organization and the party, names only (pp. 181–191), entered as activists. Survivors whose biography says only that they took part are marked as participants. The victims of terror and one man who went over to the Chetniks in 1943 were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'zitoradje':
      'The participants of the war of liberation from Žitorađe near Vladičin Han, names only (p. 86), the village’s wounded and fallen fighters (pp. 86–88), and the fighters of Serbian brigades who fell freeing the village in September and October 1944, each with a short biography (pp. 89–91). The victims of fascist terror were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'brod-crna-trava':
      'Appendix III, the dead of 1941–1945 from the village of Brod near Crna Trava, a table of the hamlet, the day and place of death and the unit (pp. 808–809). Only those the table gives a unit were entered, since the others include civilian victims. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'revolucionarno-grahovo':
      'The fighters from Grahovo near Nikšić who fell in the war and the revolution of 1941–1945, each with a short biography (pp. 93–128), and the fallen people’s heroes (pp. 81–91). The movement’s people who died in prisons and camps are in too, marked as activists, and of the victims of fascist terror (pp. 129–133) only the activists and fighters. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'kolasin':
      'The dead of the Kolašin area in the war and the revolution, each with a short biography (pp. 683–724), and the holders of the 1941 Partisan Commemorative Medal with the duty they held at the war’s end (pp. 732–743). The movement’s activists are marked as activists, and the dead whose biography says only that they were in the movement as participants; of the victims of fascism and the war (pp. 726–731) only the fighters were entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'bozice':
      'The fighters of Božiće near Andrijevica by brotherhood, names only, as the author counts them under the Convention on combatants (pp. 316–317), the holders of the 1941 Partisan Commemorative Medal (p. 317), and those who fell as fighters or helpers of the movement (pp. 318–319). The Chetniks’ dead were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'otocac-brinje':
      'A list of the fallen fighters, the victims of fascist terror and the surviving fighters and active members of the movement of the former municipality of Otočac, village by village: the fallen (pp. 411–433) and the surviving fighters and active members (pp. 461–531), with birth, joining and duty. The active members were entered too, political workers, committee members and members of the youth league and the women’s front, marked as activists; the victims of terror were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'hak-14-donji-lapac':
      'From the Karlovac Historical Archive’s collection (vol. 14): the fighters from the district of Donji Lapac who fell in 1941–1945 (pp. 1041–1094), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-13-gracac':
      'From the Karlovac Historical Archive’s collection (vol. 13): the fighters from the district of Gračac who fell in 1941–1945 (pp. 917–965), by municipality, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-7-plascanska-dolina':
      'From the Karlovac Historical Archive’s collection (vol. 7): the fighters from the Plaški valley and its surroundings who fell in 1941–1945 (pp. 689–701), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'krusevac-1944-poginuli':
      'The fighters killed in the battles for the liberation of Kruševac in September and October 1944, by unit: the 4th Montenegrin Proletarian, the 3rd, 6th and 17th Serbian Brigades and the Kruševac military area command (pp. 273–283), with birth and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'u-rovovima-srema-poginuli':
      'The fighters killed on the Srem front (pp. 230–267), by brigade and by the place where they fell, names only, sometimes with a duty. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain, by name, brigade and place of death.',
    'sremski-front-poginuli':
      'The fighters killed on the Srem front from October 1944 to April 1945, by division and brigade, each list after a short history of the unit: names only, sometimes with the father’s initial. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain, by name, brigade and time of death. The lists of fallen Red Army soldiers at the end of the book were left out.',
    'bitka-kod-oborova-poginuli':
      'The names of the 128 fighters of the 2nd Moslavina Brigade and the Posavina Partisan Detachment killed at Oborovo on 29 March 1944 (pp. 158–160). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'zrtve-rata-1964-slo':
      'The 1964 census of the war’s victims in Slovenia, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-hrv':
      'The 1964 census of the war’s victims in Croatia, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-bih':
      'The 1964 census of the war’s victims in Bosnia and Herzegovina, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-crg':
      'The 1964 census of the war’s victims in Montenegro, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-mak':
      'The 1964 census of the war’s victims in Macedonia, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-srb':
      'The 1964 census of the war’s victims in Serbia without its provinces, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-kos':
      'The 1964 census of the war’s victims in Kosovo and Metohija, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    'zrtve-rata-1964-voj':
      'The 1964 census of the war’s victims in Vojvodina, by municipality and village: only the fighters of the Liberation War who were killed or died in it are included, not the victims of terror. The census belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters. Published by the Museum of Genocide Victims.',
    '6-istocnobosanska-dopuna':
      'Partisans of the brigade whose details were not published in “Borbeni put Šeste proleterske brigade” (1977), gathered by 1981: birth, when they joined the struggle, duty, fate; and those whose place and time of death were never established (pp. 676 ff.)',
    '7-banijska-poginuli':
      'An incomplete list of the brigade’s members killed in the war or who died: birth, nationality, occupation, when they joined the army, battalion, where and when they fell (pp. 394–462)',
    '15-majevicka-spisak':
      'The brigade’s People’s Heroes and a roll of all its Partisans: year and place of birth, nationality, occupation, when they joined the struggle and came to the brigade, fate (pp. 484–557)',
    'beogradski-bataljon':
      'Every Partisan of the Belgrade Battalion from the first days of the uprising to 1 March 1945, when it became the 3rd Battalion of the 1st Proletarian, grouped by when they joined: occupation, birth, Party and youth league membership, what became of each in the war',
    '1-dalmatinska-monografija':
      'Company commanders and political commissars by battalion, the lives of the brigade’s People’s Heroes and the list of its Partisans killed in the war, the same as on znaci.org, here with the scanned book',
    '4-brigada-slavonije':
      'The brigade’s Partisans and officers who were killed (company and duty, date and place of birth, date and place of death) and those who were wounded (unit and duty, when they were wounded), appendices 2 and 3 of the book (pp. 164 ff.)',
    '4-brigada-slavonije-rukovodioci':
      'The leaders of the brigade staff and its units and of its four battalions, from the commander to the platoon sergeants, by duty, with where they came from and when they held the post, and the comrades in other duties in the brigade, appendix 1 of the book (pp. 177–182)',
    '9-dalmatinska-divizija':
      'The division’s Partisans and officers killed or missing in the fighting from 11 February to 15 April 1943, names with the father’s name (pp. 121–126)',
    '3-dalmatinska-poginuli':
      'The killed and missing of the 3rd Independent Dalmatian Brigade, 14 April to 6 June 1943, names with the father’s name (pp. 126–128)',
    '12-slavonska-zene':
      'The women fighters of the 12th Proletarian Slavonian Brigade, killed, dead since or surviving, with short lives (text on znaci.org, no scanned book; the roll of all the brigade’s fighters the book announced was never published)',
    'zagrebacki-odred':
      'The roll of the detachment’s fighters from its collection of documents and memoirs (pp. 407–418): mostly survivors who registered with the veterans’ association in Zelina after the war, and the fallen named in wartime papers and memoirs; village, municipality and fate. The battalions that went whole to the “Matija Gubec” and Zagorje brigades are not in it.',
    'mosorski-odred':
      'The roll of the Mosor Partisan Detachment, 1942–1944 (the list’s first part, pp. 355–562): the 1st Mosor Detachment, the Mosor Battalion, the Flying Mosor Company and the detachment of October 1943 to November 1944, with birth, occupation, joining and fate. The list’s second part, the town commands’ men and the field workers, is not included.',
    'mosorski-odred-2':
      'The second part of the same book’s roll (pp. 573–648): the fighters of the town commands and the party, political and field workers of the Mosor area. The odred’s roll holds the fighters, those whose entry says they fought or names a military duty or an army unit, and the labour battalions’ men. The field and political workers, council members and AFŽ members were entered as activists, each added to the record of a fighter on the site where it is the same person, the others among the Other fighters.',
    'mosorski-odred-kader':
      'The detachment’s leaders, 1942–1944, by duty, from its commanders to its platoon commanders, platoon delegates and company nurses, names only (pp. 563–568)',
    'turopoljsko-posavski-odred':
      'The detachment’s fighters killed in action (99, with birthplace, date and place of death) and those shot or who died during the war (16), pp. 17–20 (Turopolje Museum, Velika Gorica 1983)',
    'zascitna-enota-vpv':
      'The members of the protection unit of the Slovene partisan leadership who survived the war, with date and place of birth and the bases they served at, then its fallen, its national heroes and the holders of the Partisan Commemorative Medal 1941 (pp. 293–310).',
    'hak-19-vojnic':
      'From the Karlovac Historical Archive’s collection (vol. 19): the fighters from the district of Vojnić who fell in 1941–1945 (pp. 1123–1177), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-18-slunj-veljun':
      'From the Karlovac Historical Archive’s collection (vol. 18): the fighters from the districts of Slunj and Veljun who fell in 1941–1945 (pp. 921–977), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-15-duga-resa':
      'From the Karlovac Historical Archive’s collection (vol. 15): the fighters from today’s municipality of Duga Resa who fell in 1941–1945 (pp. 1060–1090), by municipality and village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus were left out.',
    'hak-12-dreznica':
      'From the Karlovac Historical Archive’s collection (vol. 12): the fighters from the municipality of Drežnica who fell in 1941–1945 (pp. 865–876), by village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s list of victims of fascist terror and of the war was left out.',
    'hak-16-gornje-dubrave':
      'From the Karlovac Historical Archive’s collection (vol. 16): the fighters from the municipality of Gornje Dubrave who fell in 1941–1945 (pp. 889–899), by village, with birth, the way into the war and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s list of victims of fascist terror and of the war was left out.',
    'sjenicak':
      'The chronicle of a Kordun village, published by the Karlovac Historical Archive, with two of its lists: the fighters from Donji, Gornji and Lasinjski Sjeničak who fell or died in 1941–1945 (pp. 330–338), by village, with birth, the way into the war and death, and the holders of the Partisan Commemorative Medal 1941 (pp. 385–389). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The same book’s lists of victims of fascist terror and of those who died of typhus and cold were left out.',
    'tuzla-spomen-knjiga':
      'The memorial book of the municipality of Tuzla: biographies of its partisans who fell in 1941–1945 (pp. 13–300), born, living or working in Tuzla or joining the army from there, often with a photograph, with unit, birth and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain. The book’s second part, the victims of fascist terror, was left out.',
    'jajce-1941-poginuli':
      'From the collection of memoirs on the Jajce area (vol. I): the fighters from the Jajce area who fell in 1941, with birth, unit and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'jajce-1942-poginuli':
      'From the collection of memoirs on the Jajce area (vol. II): the fighters and activists of the liberation movement from the Jajce area who fell in 1942, with birth, unit and death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'spomenica-crnogorskim-antifasistima':
      'Montenegro’s antifascists who were killed or died in 1941–1945, by municipality, in a table: name, father’s name, year and place of birth, year and place of death. Everyone the book names is counted as a partisan: an entry is added to the record of each fighter on the site where the match is certain, and the others are among the other fighters.',
    'moste-polje-spomenica-1941':
      'The holders of the Partisan Commemorative Medal of 1941 from the area of today\'s Moste-Polje district of Ljubljana, from the archive of the Slovene party\'s central committee (pp. 257–260): name, year of birth and trade, and for those who died after the war the year of death. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'vis-spomenica-1941':
      'The holders of the Partisan Commemorative Medal of 1941 from the Vis islands (p. 521), names only, with the book\'s sentence on the national hero Andrija Božanić. The book belongs to no single unit: an entry is added to the record of each fighter from the island on the site where the match is certain; the others are among the Other fighters.',
    'prilog-u-krvi-pali-borci':
      'The fallen fighters of the Pljevlja district, April 1941 to 15 May 1945 (pp. 141–216), each with a biography. The book counts party and political workers, committee members and helpers of the movement among its fallen fighters too: they were entered too, marked as activists. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'jevreji-jugoslavije-ucesnici-nor':
      'The list of the Jewish participants in the war of liberation, each with a biography (p. 307 on). The list counts everyone in the movement: everyone was entered, and the political workers, the rear and those caught on their way to the partisans are marked as activists. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'hrvatsko-zagorje-1981':
      'The roll of the participants of the war who fell in 1941–1945 from the municipalities of Donja Stubica, Ivanec, Klanjec, Krapina, Pregrada, Zabok, Zaprešić and Zlatar-Bistrica, with birth, unit and death. The roll lists fighters and victims of fascist terror together; the fighters were entered and, marked as activists, the members of the party, SKOJ and the committees, political workers and couriers; the victims of terror were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'imotska-krajina-pali-borci':
      'The fallen fighters and the victims of fascist terror of the villages of the Imotski region (pp. 163–472), with birth, the way into the army and death. The fallen fighters were entered, from the part the book heads “Poginuli borci” in each village, and the SKOJ members, communists and political workers it counts there are marked as activists; the victims of terror were left out. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'knjazevac-pomenik':
      'Everyone from the municipality of Knjaževac who died in the Second World War, by village (pp. 37–327), with birth and death: partisans, Chetniks, the executed and civilians together. The partisan fighters were entered and, marked as activists, the communists, SKOJ members, committee members and helpers of the partisans; the Chetniks, the civilians and those the new authorities sentenced were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'iskra-in-plamen-padli':
      'From a collection on the liberation war in the villages of the former municipality of Polje near Ljubljana: “Svoja življenja so dali za svobodo”, the dead of those villages by village, with the years of birth and death and the place of death. Only those who fell in the army were entered; those who died in internment and prisons, hostages and other victims were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'cazinska-krajina-pali-borci':
      'The fallen fighters of the Cazin region, by municipality (Bihać, Bosanska Krupa, Cazin, Velika Kladuša) and village, with the father’s name and the years of birth and death. The book’s list of Serb civilian victims was not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'derventa-pali-borci':
      'The fighters from the municipality of Derventa who fell in the liberation war, with birth, unit and place of death. The book’s list of the victims of fascist terror was not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'sanski-most-borci':
      'The fighters of the Sanski Most district by village: those who fell, the holders of the Partisan Commemorative Medal of 1941, and the fighters alive on 15 May 1945, with birth, trade, the year they joined and their duty. From the third list the fighters were entered (a fighter, a military duty or rank, a unit) and, marked as activists, the committee members and the SKOJ and AFŽ members without a military duty; the victims of fascist terror were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'rat-i-djeca-kozare':
      'From the book on the children of Kozara in the war, the chapter “Pali kao borci narodnooslobodilačkog rata”: the 370 boys and girls of Kozara under fifteen who fell as fighters, by municipality, with place and years of birth and death (text on znaci.org, no scan of the book). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'krizani-v-boju-za-svobodo':
      'A book on the people of Križ (Santa Croce) by Trieste in the war: the biographies of the fallen (those who were partisans or in the army were entered and, marked as activists, the activists of the Liberation Front and its field workers), and the tables of the men and women of Križ in the Yugoslav army and of the fighters who lived there, with father, birth, joining, rank and unit. The volunteers in Spain, those in Italian units and the deportees were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'vinodolska-selca':
      'From the appendices of a book on Selce near Crikvenica in the war: the fighters of Selce who fell, with duty, unit, birth and death, and the first fighters and holders of the Partisan Commemorative Medal of 1941. The helpers of the movement executed in camps were entered too, marked as activists. The list of organized participants (names only, with the AFŽ women and committee members) and the lists of victims were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'susak-rijeka-spomenica':
      'From the appendices of a book on Sušak and Rijeka in the war: the holders of the Partisan Commemorative Medal of 1941 from the Rijeka municipality, name and place, as the veterans’ board compiled them. The lists of the KPJ and SKOJ members of 1941 who fell were not entered, since they do not say who was a fighter. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'zene-vi-korpus-poginule':
      'From a collection of documents on the women of Croatia in the war (document 427): the VI Corps staff’s list of its women fighters and officers who fell, drawn up on 23 December 1944, with duty and unit, year and place of birth, and when and in which fight each fell. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'ludbreg-poginuli':
      'The fighters killed in the two battles for Ludbreg: the 17th Slavonian Brigade’s in Ludbreg and Šemovec on 3 October 1943, the »Braća Radić« Brigade’s at Šemovec the same day, and the 17th Slavonian’s in Ludbreg on 6 July 1944 (pp. 84–85, 287–289), with year and place of birth. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'dolomiti-v-nob-3':
      'The national heroes of the Dolomiti, the hills west of Ljubljana, the holders of the 1941 Commemorative Medal and the first fighters who fell, with date and place of birth (pp. 667–671). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'sanitetska-sluzba-lekari':
      'The doctors who lost their lives in the war, each with a short biography: where they came from, when they joined the army, their duty and unit, their death (a text on znaci.org, no scan of the book). Those who served in the army are entered, and the doctors killed behind the lines as helpers of the movement (who organized the uprising, hid and treated partisans) are marked as activists. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'korosko-zdravstvo':
      'The wounded and sick fighters and activists in Carinthia to February 1944, the patients of the Carinthian partisan hospitals, the Carinthian fighters treated outside them and the medical staff, each with a short biography (pp. 282–355). Entered are the fighters and the staff of the partisan hospitals and, marked as activists, the political workers in the field and the doctors and nurses who sent medicines to the partisans. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'artileristi-prekomorci':
      'The fallen gunners among the "prekomorci", the Slovenes and Istrians who came from Italy and Africa to the artillery units formed on Vis and in Italy, and the commanders and commissars of those units (pp. 227–234). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'virovitica-spomenica-1941':
      'The holders of the Partisan Commemorative Medal of 1941 from the Virovitica municipality, fourteen biographies with photographs (pp. 221–239). The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'vis-zrtve-nob':
      'The war\'s dead from the memorial plaques of the Vis islands (pp. 516–520): those who fell in battle and those who died of wounds and illness, from Vis, Komiža, Biševo, Oključna and the villages under Hum, the name and the father\'s name only. The hostages the Italians shot in 1943 and those who died in Ustaša prisons are left out. The book belongs to no single unit: an entry is added to the record of each fighter from the island on the site where the match is certain; the others are among the Other fighters.',
    'xxxi-divizija-stabi':
      'The staffs of the XXXI Division and its brigades, the Gradnik, Prešeren and Vojko brigades (pp. 557–562): commanders, commissars, their deputies and the chiefs of staff, each with the dates he held the post, and which of them fell. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    '15-brigada-stabi':
      'The commanders, political commissars, their deputies and the chiefs of staff of the Slovene 15th Brigade, and the commanders and commissars of its battalions (pp. 447–450), each with the dates he held the post and, where it ended so, that he was wounded, fell ill or fell. The brigade is not on the site: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    '15-divizija-stabi':
      'The command of the 15th Division of the Slovene partisan army (pp. 583–584): commanders, political commissars, their deputies and assistants, and the chiefs of staff, each with the dates he held the post. The division is not on the site: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'jb-odred-stabi':
      'The staffs of the Jesenice-Bohinj Detachment, its three battalions and its school camp, August 1944 – May 1945 (pp. 354–356): commanders, political commissars, their assistants and deputies, and the chief of staff, each with the dates he held the post. The detachment is not on the site: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'banijski-odredi-kadar':
      'The officers of the Banija partisan detachments, 1941–1945 (pp. 372–378): of the small detachments and village groups of 1941, the Banija Partisan Detachment and its battalions, the shock battalions, the partisan companies and the two Banija detachments of 1944, by duty. The detachments are not on the site: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'letalci-prekomorci-kader':
      'The leading officers of the 1st and 2nd fighter squadrons of the NOVJ, of the NOVJ air detachment in Algeria and of the 1st air regiment (pp. 322–325): each man’s rank and duty, with the dates he held it. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain; the others are among the Other fighters.',
    'niksicki-odred-pali-borci':
      'The names of the fallen of the former Nikšić district and the Herceg Novi municipality (pp. 393–420): place and year of birth, place and year of death; and the national heroes of Nikšić and Herceg Novi, with a biography of each (pp. 423–427). Nearly all of them passed through the Nikšić Detachment, and they fell in the brigades, in the detachment and in other duties. The pages on znaci.org have no text, only images: the names were read from the images. The book belongs to no single unit: its entry has been added to the record of every fighter on the site who is known for certain to be the one it describes; the others are among the Other fighters.',
    'teslic-u-nob-borci':
      'The roll of the fighters of the war of liberation from the Teslić municipality (pp. 234–267) and the list of its fighters who fell or died (pp. 269–279), with a biography of each. Besides the fighters the lists count members of the liberation committees and helpers of the movement: only those whose entry says they were fighters or in the army, or names a military duty or an army unit, were taken in. The pages on znaci.org have no text, only images: the names were read from the images. The book belongs to no single unit: its entry has been added to the record of every fighter on the site who is known for certain to be the one it describes; the others are among the Other fighters.',
    'lovcenski-odred-pali-borci':
      'The fighters of the war of liberation from the territory of the Lovćen Partisan Detachment who fell, were shot or died in 1941–1945, by district (Cetinje, Bar, Kotor) and village, with a biography of each (pp. 611–713). The author counts among the fallen everyone in the movement who lost his life, activists too, but no victims of terror; all of them were taken in. The pages on znaci.org have no text, only images: the names were read from the images. The book belongs to no single unit: its entry has been added to the record of every fighter on the site who is known for certain to be the one it describes; the others are among the Other fighters.',
    'zene-1-dalmatinska':
      'The brigade’s women fighters, 1944–1945 (document 368): duty and rank, date and place of birth, when they joined the army, decorations, and the staff’s opinion of each',
    '1-dalmatinska-komandni-sastav':
      'The commanders, commissars, their deputies, chiefs of staff, quartermasters, medical officers, youth leaders and intelligence officers of the brigade staff and of each battalion from 6 September 1942 to the end of the war, with the time each held the post (pp. 435–443)',
    '1-dalmatinska-formiranje':
      'The officers of the brigade staff, the political department, the battalions and companies on 6 September 1942 in the village of Dobro near Livno: duty, year of birth, nationality, occupation (pp. 55–58)',
    'zene-11-dalmatinska':
      'The brigade’s women fighters, 1944–1945 (document 376): date and place of birth, duty and rank, when they joined the army, decorations, and the staff’s opinion of each',
    '11-dalmatinska-stabovi':
      'The officers of the brigade staff with the time each held the post, of the companies at the staff, the dressing stations and the NCO course, the battalion staffs and company commands, by duty (pp. 611–624)',
    'osjecka-zene':
      'The women of the Osijek Brigade by battalion, as the brigade’s staff listed them for the 1st Congress of the AFŽ of Croatia (document 420): date and place of birth, when they joined the Partisans',
    'dalmatinci-prva-proleterska':
      'The 1st Proletarian Brigade’s fighters from Dalmatia, each with a short life: birth, occupation, the way into the war and the brigade, battles, fate; and a supplementary list of those the authors could not gather details on (pp. 467–754)',
    'crnogorski-bataljon':
      'The fighters who joined the 1st Montenegrin Battalion of the 1st Proletarian in 1942, 1943, 1944 and 1945, and those with incomplete details: birth, occupation, when they joined the struggle, fate; in Cyrillic (pp. 713–795)',
    'rudarska-ceta':
      'The Miners’ Company (miners of Trepča and Kopaonik) as it joined the 1st Proletarian at Rudo on 21 December 1941, each with a short life (pp. 426–430)',
    'prva-proleterska-dopunski':
      'Members of the brigade the editors found after the roster of the first three books was set, each with a short life (pp. 1065–1071)',
    'prva-proleterska-garibaldi':
      'The Italian soldiers who joined the Partisans after Italy’s capitulation, with the battalion staff, names and duties only (pp. 1072–1082)',
    'kotor-varos':
      'The lists of the participants of the war from the Kotor-Varoš and Skender-Vakuf municipalities who fell, died or went missing, by local veterans’ branch (pp. 333–354), with birth, unit and death, and the two municipalities’ holders of the 1941 Partisan Commemorative Medal (p. 357). Participants who were not fighters were entered too, marked as activists or participants. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'sokolac':
      'The list of Sokolac’s fighters who fell in the Second World War, 1941–1945 (pp. 524–571), 503 short biographies: birth, joining the army, unit and death. The same book’s list of the Chetniks’ dead was not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'popovo-polje':
      'The appendix of the fighters from Popovo polje who fell in the war (pp. 419–430): birth, duty, and the place and day of death. The same book’s list of the victims of fascist terror was not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'bijelo-polje':
      'The monograph’s appendices: the holders of the 1941 Partisan Commemorative Medal (pp. 733–753) and the fighters of the Bijelo Polje district who fell in the war (pp. 778–886), with birth, units and death. The list of the men in the ranks of the Third Sandžak Brigade on the day it was formed (pp. 754–774) is not entered yet, as the names in the scan are hard to read; nor are the dead of the April war and the victims of terror. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'lezimir':
      'The article on the dead of the village of Ležimir in Srem, 1941–1945 (pp. 95–120). Only the fighters were entered, those the list says fell in the war of liberation; the victims of terror and those the partisans killed were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'prva-niska-gimnazija':
      'The school’s list of its pupils of every generation who fell in the war and of the victims of fascist terror (pp. 221–232): those who fell as fighters of the partisan detachments and the army, and of those killed or shot, the members of the movement. Pupils who died in internment or in bombing raids were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'binovce':
      'The participants of the war from Binovce and Kalabovce near Surdulica (pp. 24–25), names only, entered as participants, and the five fighters who fell (p. 26). The internees, the victims of terror and the civilian dead were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'kremna':
      'The partisan fighters from Kremna near Prnjavor who fell, and those on the memorial plaque at Podvučjak (pp. 134–147), names only, the holders of the 1941 Partisan Commemorative Medal and the commanders of partisan units from the Prnjavor area (pp. 171–172). The same book’s lists of Chetniks and of victims were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'komani':
      'The Bandići who fell in the war of liberation, from the memorial plaque at Zagarač (pp. 223–224), with the lines of the brotherhoods’ lists on the same fighters. The plaque’s shot and its victims and the dead of earlier wars were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'gornja-jablanica':
      'The People’s Heroes and the other first fighters of 1941 from Gornja Jablanica who fell, by village (pp. 663–669), and the holders of the 1941 Partisan Commemorative Medal (pp. 669–673), names only. The holders of the Albanian Commemorative Medal and the Karađorđe Star were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    '2-korpus-stabovi':
      'The list of the command staff of the divisions and of the 2nd Assault Corps (pp. 463–465): the commanders, political commissars, deputies and chiefs of staff of the corps, the 2nd Proletarian, 3rd Assault, 29th and 37th Assault Divisions, the Coastal Operational Group, the Italian division Garibaldi and the corps’ artillery brigade, with the months each held the post. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'moslavina-spomenica-1941':
      'The holders of the 1941 Partisan Commemorative Medal from the Moslavina area (pp. 629–632), names and nicknames only: born in Moslavina or long resident there, the leaders of the party, the youth league, the women’s front and the liberation committees among them. The detachment is not on the site; the rest are among the Other fighters.',
    'knezica':
      'The appendices of a book on the villages of Knežica under Kozara: the fighters who fell in the war, by village (pp. 451–463), with the years of birth and death and the place of death, the holders of the 1941 Partisan Commemorative Medal (pp. 501–502) and the surviving fighters of the Knežica area (pp. 503–508), names only. The same book’s list of the victims of fascist terror was not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'kordunski-rekvijem':
      'General Dušan Livada’s list of the fighters of the former Primišlje municipality who fell, 1941–1945 (pp. 176–191), by village, with a short biography; the party and youth league members, committee members and women’s front members the list counts were entered as activists. The first 49 holders of the 1941 Partisan Commemorative Medal who moved from Slunj to Vojvodina (pp. 338–342) were entered too. The lists of the victims of terror and of those who died of typhus were not entered. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'sencur-padli-borci':
      'The list of the fighters, activists and other victims of fascist violence from the Šenčur municipality near Kranj, by village, with a biography each (pp. 359–368), and the roster of the Kokra company, December 1941 to spring 1942, with each fighter’s last home and the day he joined (pp. 381–384). The fighters were entered and, marked as activists, the people of the Liberation Front and the party; hostages, deportees and others killed with no part in the movement were not. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
    'klanjscek-komandni-sastav':
      'Appendix 1, the list of the command staff of the higher units of the Slovene partisan army (pp. 393–400): the commanders, political commissars, their deputies and the chiefs of staff of the General Staff, the provincial staffs, the groups of detachments, the operational zones, the corps and the divisions, with the days each held the post and where those who fell were killed. The book belongs to no single unit: an entry is added to the record of each fighter on the site where the match is certain.',
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
    'jedinični spisak brigade': 'seznam brigade po enotah',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'seznam borcev (zbornik spominov, 3. knjiga)',
    'spiskovi poginulih i rukovodilaca': 'seznama padlih in vodstva',
    'ilustrovana monografija (1942—1992)': 'ilustrirana monografija (1942–1992)',
    'borci brigade na Sutjesci': 'borci brigade na Sutjeski',
    'borci brigade na dan njenog osnivanja (stroj u Rudom)': 'borci brigade na dan ustanovitve (zbor v Rudem)',
    'dopuna spiska boraca': 'dopolnitev seznama borcev',
    'komandiri i komesari četa, narodni heroji, poginuli': 'komandirji in komisarji čet, narodni heroji, padli',
    'spisak poginulih i nestalih': 'seznam padlih in pogrešanih',
    'spisak žena boraca': 'seznam bork',
    'žene borci I. dalmatinske proleterske brigade': 'borke I. dalmatinske proletarske brigade',
    'žene borci XI. dalmatinske brigade': 'borke XI. dalmatinske brigade',
    'žene borci Osječke brigade': 'borke Osiješke brigade',
    'spiskovi boraca koji su stupili u bataljon 1942–1945': 'seznami borcev, ki so vstopili v bataljon 1942–1945',
    'spisak boraca u Rudom 21. XII 1941.': 'seznam borcev v Rudem 21. 12. 1941',
    'spisak komandnog kadra': 'seznam poveljniškega kadra',
    'pregled komandnog kadra i narodni heroji': 'pregled poveljniškega kadra in narodni heroji',
    'pregled komandnog kadra': 'pregled poveljniškega kadra',
    'poveljniški kader': 'poveljniški kader',
    'starešine štabova': 'starešine štabov',
    'pregled rukovodećeg kadra': 'pregled vodilnega kadra',
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
    'jedinični spisak brigade': 'список на бригадата по единици',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'список на борците (зборник спомени, кн. 3)',
    'spiskovi poginulih i rukovodilaca': 'списоци на загинатите и на раководството',
    'ilustrovana monografija (1942—1992)': 'илустрирана монографија (1942–1992)',
    'borci brigade na Sutjesci': 'борците на бригадата на Сутјеска',
    'borci brigade na dan njenog osnivanja (stroj u Rudom)': 'борците на бригадата на денот на формирањето (строј во Рудо)',
    'dopuna spiska boraca': 'дополнување на списокот на борците',
    'komandiri i komesari četa, narodni heroji, poginuli': 'командири и комесари на чети, народни херои, загинати',
    'spisak poginulih i nestalih': 'список на загинатите и исчезнатите',
    'spisak žena boraca': 'список на жените борци',
    'žene borci I. dalmatinske proleterske brigade': 'жените борци на I далматинска пролетерска бригада',
    'žene borci XI. dalmatinske brigade': 'жените борци на XI далматинска бригада',
    'žene borci Osječke brigade': 'жените борци на Осиечката бригада',
    'spiskovi boraca koji su stupili u bataljon 1942–1945': 'списоци на борците што стапиле во баталјонот 1942–1945',
    'spisak boraca u Rudom 21. XII 1941.': 'список на борците во Рудо, 21. XII 1941',
    'spisak komandnog kadra': 'список на командниот кадар',
    'pregled komandnog kadra i narodni heroji': 'преглед на командниот кадар и народните херои',
    'pregled komandnog kadra': 'преглед на командниот кадар',
    'poveljniški kader': 'командниот кадар',
    'starešine štabova': 'старешините на штабовите',
    'pregled rukovodećeg kadra': 'преглед на раководниот кадар',
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
    'jedinični spisak brigade': 'the brigade’s roll, by unit',
    'spisak boraca (zbornik sjećanja, knj. 3)': 'roll (memoirs, vol. 3)',
    'spiskovi poginulih i rukovodilaca': 'the fallen and the leaders',
    'ilustrovana monografija (1942—1992)': 'illustrated history (1942–1992)',
    'borci brigade na Sutjesci': 'the brigade at the Sutjeska',
    'borci brigade na dan njenog osnivanja (stroj u Rudom)': 'the brigade on the day it was formed (the line-up at Rudo)',
    'dopuna spiska boraca': 'addendum to the roll',
    'komandiri i komesari četa, narodni heroji, poginuli': 'company commanders and commissars, People’s Heroes, the fallen',
    'spisak poginulih i nestalih': 'the killed and missing',
    'spisak žena boraca': 'the women fighters',
    'žene borci I. dalmatinske proleterske brigade': 'the women fighters of the 1st Dalmatian Proletarian Brigade',
    'žene borci XI. dalmatinske brigade': 'the women fighters of the 11th Dalmatian Brigade',
    'žene borci Osječke brigade': 'the women fighters of the Osijek Brigade',
    'spiskovi boraca koji su stupili u bataljon 1942–1945': 'the fighters who joined the battalion, 1942–1945',
    'spisak boraca u Rudom 21. XII 1941.': 'the company at Rudo, 21 December 1941',
    'spisak komandnog kadra': 'the command roll',
    'pregled komandnog kadra i narodni heroji': 'the commanders and the People’s Heroes',
    'pregled komandnog kadra': 'the commanders',
    'poveljniški kader': 'the commanders',
    'starešine štabova': 'the officers of the staffs',
    'pregled rukovodećeg kadra': 'the leaders',
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
