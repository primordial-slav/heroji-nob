// Photos, documents and stories that families sent through "Znam ovog borca" and that were checked and approved
// for publishing (the sender gave permission). How to add one: docs/FAMILY_CONTRIBUTIONS.md

/** A photograph or a document a family sent, beside the one `photo` (components/FamilyStory.tsx shows them as an album) */
export interface FamilyPiece {
  kind: 'photo' | 'document'
  file: string           // file in website/public/porodica/: the photo, or a document's first page
  pages?: string[]       // a document's other pages, in order
  caption?: string       // what it is, in the sender's words: 'Vojna knjižica', 'Sa saborcima, 1944.'
  transcripts?: string[] // what each page says, page by page, where it is written by hand or hard to read
}

export interface FamilyContribution {
  soldierId: string     // the record it belongs to
  photo?: string        // file in website/public/porodica/, e.g. '0002000003-1.jpg'
  photoCaption?: string // what the photo shows and when, in the sender's words
  photoFrom?: string    // where the portrait comes from when not from the sender: 'Vikipedija' (credited under it)
  text?: string         // the story, as sent (lightly edited for spelling only)
  pieces?: FamilyPiece[] // more photos and documents from the same sender
  from: string          // credit line, e.g. 'Ana Petrović, unuka'; 'iz porodične arhive' when the sender did not allow a name (no
                        // initial, no relation either: the user's rule, 2026-11-23)
  date: string          // when it was sent, 'YYYY-MM'
  origin?: 'facebook'   // not from the family but from a public Facebook page: the heading says so, `from` names the page
    | 'visitor'         // or from a visitor who is not of the family (a researcher, an anonymous report): "Od posetilaca"
  wikipedia?: string    // his article on Wikipedia, linked under the note ("Članak na Vikipediji"; the user, 2026-11-20)
}

export const familyContributions: FamilyContribution[] = [
  {
    soldierId: '0002000242', // Bakić Maksimov Mile, Prva lička
    photo: '0002000242-1.jpg',
    // the user's family archive (their MyHeritage tree, 2026-11-19): photos of him alone and the papers of his decoration;
    // the family photos with other people wait for the user's word on which may be shown
    pieces: [
      { kind: 'photo', file: '0002000242-2.jpg', caption: 'U uniformi' },
      { kind: 'photo', file: '0002000242-3.jpg', caption: 'U oficirskoj uniformi' },
      { kind: 'photo', file: '0002000242-4.jpg' },
      { kind: 'photo', file: '0002000242-5.jpg' },
      { kind: 'photo', file: '0002000242-6.jpg', caption: 'U kasnijim godinama' },
      {
        kind: 'document',
        file: '0002000242-7.jpg',
        caption: 'Povelja o odlikovanju Ordenom republike sa srebrnim vencem, 1984.',
        transcripts: ['Ukazom Predsedništva Socijalističke Federativne Republike Jugoslavije broj 90 od 17. oktobra 1984. godine, za naročite zasluge na polju javne delatnosti kojom se doprinosi opštem napretku zemlje, odlikovan je Mile M. Bakić Ordenom republike sa srebrnim vencem, o čemu se izdaje ova povelja. Kancelarija ordena, u Beogradu 17. oktobra 1984. godine. Šef Kancelarije ordena, [potpis]'],
      },
      {
        kind: 'document',
        file: '0002000242-8.jpg',
        caption: 'Iz novina: odlikovani Ordenom republike sa srebrnim vijencem',
        transcripts: ['Ordenom republike sa srebrnim vijencem: Bakić Maksima Mile, Popov Branka Dejan, Prijić Milana Radivoj; za osobite zasluge i uspjehe postignute u radu značajnom za socijalističku izgradnju zemlje'],
      },
    ],
    from: 'iz porodične arhive',
    date: '2026-10',
  },
  {
    soldierId: '0122959019', // Bajić Stevan Todor "Soko", Beška (Porodična arhiva)
    photo: '0122959019-1.jpg',
    photoCaption: 'Fotografija iz vojne knjižice',
    from: 'iz porodične arhive',
    date: '2026-10',
  },
  {
    soldierId: '0126000703', // Novaković Vuka Radomir, Čačanski NOP odred
    photo: '0126000703-1.jpg',
    text: 'Njegova slika nalazi se u Spomen-muzeju prve partizanske bolnice u rodnom selu u Donjoj Gorevnici kod Čačka. Njegovo ime upisano je na spomen-ploči na Zadružnom domu u Donjoj Gorevnici.',
    from: 'F. Adžić, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0136006734', // Todosijević Dragić Jelica (Borci drugih jedinica – Srbija)
    text: 'Ne znamo gde je sahranjena. Ne znamo za sigurno ni gde je poginula. Neki kažu da su je ubili četnici 1942.',
    from: 'J. Todosijević, bratanica',
    date: '2026-11',
  },
  {
    soldierId: '0136021032', // Đoković Miodrag Dragan (Borci drugih jedinica – Srbija)
    photo: '0136021032-1.jpg',
    photoCaption: 'Spomen-bista ispred škole u Lađevcima',
    text: 'Pre rata, radio je kao učitelj (pre toga i izuzetan učenik) u rodnom mestu nakon čega je dobio nadimak „Uča” (negde napisano i kao „Učo”). Posle rata, njegovo ime sve do danas nosi Osnovna škola u Lađevcima kod Kraljeva. Tokom rata, bio je borac Kraljevačkog NOP odreda. Ispred škole, od 1976. godine nalazi se spomen-bista Dragana Đokovića, rad autora Ace Mitrovića. Bistu su podigli braća i majka Dragana Đokovića.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Драган_Ђоковић_Учо',
  },
  {
    soldierId: '0001010635', // Ristović Milije Dobrica "Staća" of Kovanluk (Kraljevo), Prva proleterska; a visitor's message of 2026-11-19
    photo: '0001010635-1.jpg', // from his Wikipedia article; postwar, his portrait all the same (the user, 2026-11-20)
    photoFrom: 'Vikipedija',
    photoCaption: 'Posle rata',
    text: 'Nosilac Partizanske spomenice 1941. Posle rata bio je visoki funkcioner u Kraljevu, između ostalog predsednik Sreskog odbora. Umro je 1971. i sahranjen u Aleji nosilaca Partizanske spomenice 1941. u Kraljevu.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Добрица_Ристовић',
  },
  {
    soldierId: '0136040042', // Jasnić Antonije Danica "Koka" of Kraljevo (census part Srbija); a visitor's message of 2026-11-20
    photo: '0136040042-1.jpg', // from her Wikipedia article (public domain)
    photoFrom: 'Vikipedija',
    photoCaption: 'U Studenici, 1940.',
    pieces: [{ kind: 'photo', file: '0136040042-2.jpg', caption: 'Spomen-ploča u selu Lisi kod Ivanjice, sa imenima streljanih boraca' }], // her Wikipedia article (CC0)
    text: 'Profesorka francuskog jezika u Gimnaziji u Kraljevu. Uhapšena je u junu 1941, pobegla iz zatvora sa Olgom Jovičić Ritom i stupila u Kraljevački NOP odred „Jovo Kursula”. U decembru 1941. ostala je uz ranjenike u selu Kaoni; zarobili su je četnici i streljali u selu Lisi kod Ivanjice. Posmrtno je odlikovana Partizanskom spomenicom 1941.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Даница_Кока_Јаснић',
  },
  {
    soldierId: '0136014651', // Kolarević Miloš Tihomir "Tika" of Grdica (Kraljevo), census part Srbija; a visitor's message of 2026-11-20
    photo: '0136014651-1.jpg',
    photoCaption: '1930-ih',
    text: 'Tihomir Tika Kolarević i njegov rođeni brat Milomir iz Grdice kod Kraljeva stupili su na početku rata u različite vojske: Tika u partizane, Milomir u četnike. Tokom rata su se suočili, kada je Tika razoružao brata i njegovu jedinicu. Tika je poginuo u ratu, a Milomir je otišao u izbeglištvo u London, gde je umro od starosti nekoliko decenija kasnije. Od posleratnih godina u Grdici postoji Ulica Tike Kolarevića, a od 2000-ih jedna ulica nosi i Milomirovo ime, pored ulice brata protiv kojeg je ratovao. Izmišljena verzija dvojice braće, po njihovoj priči, pojavljuje se u filmu „Crvena zemlja” iz 1970-ih, smeštenom u Kraljevo 1941.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0036100540', // Karamatić Joze Ivo "Čović" of Plina Istočna (Ploče), 1. dalmatinska; the user sent the photos
    photo: '0036100540-1.jpg', // a boy in a partisan cap with a rifle, cut from a group photo, tinted
    pieces: [{ kind: 'photo', file: '0036100540-2.jpg', caption: 'U kasnijim godinama' }], // in a partisan cap, with his decorations
    // the photos' source, as the user gave it; under the heading "Sa Facebook stranice" (the user, 2026-11-19)
    from: '„Bitka na Sutjesci”',
    origin: 'facebook',
    date: '2026-11',
  },
  {
    soldierId: '0135000797', // Piperov Nikola Vlado (Borci drugih jedinica – Makedonija)
    text: 'Ispravka godine rođenja: na njegovoj spomen-bisti u selu Stojakovo uklesana je 1919. Popis iz 1964. navodi 1920.',
    from: 'Ispravka po prijavi',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0041900005', // Kovačević Pajov Dušan of Osječenica (Nikšić), Borci drugih jedinica
    text: 'Rođen 1923. u Osječenici kod Nikšića, a poginuo pri proboju Sremskog fronta, početkom aprila 1945. godine.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0097900021', // Sekulić Mane Miloš of Zbjeg (Slunj), Borci drugih jedinica
    photo: '0122907839-1.jpg',
    text: 'Ime mu se u izvorima razlikuje: knjige ga upisuju i kao Miloša, sina Manina, i kao Manu, sina Milošev. Znamo da je bio komesar i da je poginuo negde na Žumberku. Spasio je od streljanja svog sestrića Manojla Manu Kosanovića, koji je poginuo na Ilirskoj Bistrici goneći ustaše.',
    from: 'B. Batalo, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0060000921', // Kosanović Milovana Mane (Manojlo), Zbjeg: the nephew Miloš Sekulić saved from a firing squad
    text: 'Porodica ga navodi kao Manojla Manu Kosanovića. Njegov ujak Miloš Sekulić, komesar bataljona, spasio ga je od streljanja. Poginuo je kod Ilirske Bistrice, goneći ustaše.',
    from: 'B. Batalo, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0042000145', // Gaković Gojka Milorad, Banjani; the same man as Gaković Milorad 0013020151 of the 6. krajiška (linked)
    photo: '0042000145-1.jpg',
    text: 'Rođen u Banjanima kod Bosanskog Broda. Pre rata trgovac, povezan sa KPJ, ali nije bio aktivan član. Učesnik NOB-a od 1941. Prebacio je brojnu porodicu u Vojvodinu pre pokolja, pa se vratio u selo. Tifusar na Neretvi, ranjen na Sutjesci. U sastavu Šeste krajiške, a zatim 7. istočnobosanske muslimanske divizije. U memoarima saboraca pominje se pod nadimkom „Crni”. Predvodio je akciju zauzimanja i uništenja rudnika Ljubija 1943.',
    from: 'B. Obradović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122959607', // Krnić Ive Blaž of Konjevrate (Šibenik), survived; his photo in uniform is his portrait (the user's choice, 2026-11-19)
    photo: '9990000003-1.jpg',
    photoCaption: 'U uniformi',
    // the grandson's form of 16:23 (the wound and Bari), lightly edited for spelling
    text: 'Tijekom NOB-a teško je ranjen i prebačen u Bari (Italija), u savezničku bolnicu. Kasnije se vratio u borbu.', // the 16:23 form alone: the battles are his Porodična arhiva entry's (the user, 2026-11-23)
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0001003949', // Ivanović Radosava Špiro of Dragovoljići (Nikšić), Prva proleterska; the form of 2026-11-19 18:15
    text: 'Umro je 1976. godine. Penzionisan je kao pukovnik JNA.',
    from: 'S. Polić, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0010900056', // Ćulibrk Svetko of Risovac (Porodična arhiva 9990000004); the granddaughter's form of 2026-11-20 15:51
    photo: '0122959608-1.jpg',
    // she sent his two war memoirs as a typed PDF (the first was printed as "U Trećoj krajiškoj brigadi" in Bosanski
    // Petrovac u NOB, zbornik sjećanja, knj. V, 1974, pp. 235-239, which she sent whole) and allowed text and photos,
    // not her name
    pieces: [{
      kind: 'document',
      file: '0122959608-2.jpg',
      pages: ['0122959608-3.jpg', '0122959608-4.jpg', '0122959608-5.jpg', '0122959608-6.jpg'],
      caption: 'Njegova ratna sećanja: „Postao sam proleterski borac” (u zborniku Bosanski Petrovac u NOB, knj. V, 1974) i „Na pragu Srbije”',
    }],
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0122908393', // Lukić Luke Petar of Gejkovac (Krstinja), killed at Jadovno 1941 (hak-19-vojnic); the great-granddaughter's form of 2026-11-20 17:28
    photo: '0122908393-1.jpg', // cut from the photo with his sons, shown whole in the album
    pieces: [{ kind: 'photo', file: '0122908393-2.jpg', caption: 'Sa sinovima Ilijom i Bogdanom' }],
    text: 'Prema porodičnom sjećanju, ljudi su odvedeni iz Mehina Stanja, a neki su završili u crkvi u Kladuši, odakle su odvedeni u Jadovno. Nakon rata djeca su ostala siročad, a djed je bio udomljen u Ljubljani. Ipak, nakon par dana vratio se na Kordun.',
    from: 'A. Petrušić, praunuka',
    date: '2026-11',
  },
  {
    soldierId: '0067000827', // Palčič Dino, b. 1925, Istarski odred; the great-grandson's form of 2026-11-20 17:48 (sent four times, its photo never arrived)
    // translated from Slovene by the sender
    text: 'Učestvovao je u borbama i radio kao stražar u tajnoj partizanskoj bolnici. Na kraju je izgubio nogu usled rane od gelera koja se inficirala. Posle rata živeo je u Ljubljani, gde je radio kao mehaničar na železničkoj stanici. Preminuo je 2007. godine u Ljubljani, gde je i sahranjen.',
    from: 'M. Palčič, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0021004079', // Radenković Milorada Živan of Počekovina (Trstenik), 4. srpska; the nephew's two forms of 2026-11-20 20:48 and 20:50
    // his own handwritten autobiography (after 1946) gives his path: Keserović's četnici from November 1943, over to the
    // partisans 19 March 1944 (2. južnomoravska), 16. brigada, 7. brigada of the 23rd division, 10. krajiška, 4. srpska;
    // the same book's "Radenković Živojin, vodnik, Medalja za hrabrost" (0021004080) is he: merged (316883, the user's word)
    photo: '0021004079-1.jpg', // cut from his military ID (Vojni otsek Novi Sad), shown whole in the album
    photoCaption: 'Fotografija iz vojne knjižice',
    text: 'Sa 15 godina učestvovao je u borbama na Kraljevu, a kada je video da je došlo do sukoba između četnika i partizana, vratio se kući u selo. Keserovićevi četnici mobilisali su ga 1943. i poslali u Toplicu. Kada je video da četnici vode borbe jedino protiv partizana, a da im Nemci dostavljaju municiju, prebegao je jastrebačkim partizanima. Kući ništa nije javljao, kako porodica ne bi trpela eventualne represalije, a u međuvremenu je Keserović poslao roditeljima saučešće i izveštaj da je poginuo u borbi sa partizanima. U oktobru 1944, na putu od Kruševca ka Kraljevu, svratio je kući, a majka je, kada ga je ugledala, pala u nesvest. Priča moje babe: „15. oktobar 1944. Čuje se da u naš sokak (koji je slepa ulica) dolazi neka mašinerija, bruji, klopara... Izađem na kapiju i vidim čelična grdosija ide prema našoj kući. Ta mašina dolazi do naše kapije i staje, a sa nje skače neki mladić u uniformi i prilazi mi. Pogledam bolje i padnem u nesvest!” Posle rata bio je pripadnik milicije u Čačku i Novom Sadu. Godine 1952. došao je kući na odmor i otišao sa društvom na Moravu da love ribu; pala mu je iz ruke bomba koja mu je raznela nogu, i na putu do bolnice umro je od krvarenja.',
    pieces: [
      {
        kind: 'document',
        file: '0021004079-2.jpg',
        pages: ['0021004079-3.jpg'],
        caption: 'Vojna knjižica',
        transcripts: [
          'Lični opis: stas visok, kosa smeđa, lice duguljasto, oči smeđe, nos pravilan, usta pravilna. Ime: Radenković M. Živan. Svojeručni potpis: Radenković Živan.',
          'Čin pri ispisu iz kadra: vodnik. Ocena: kažnjavan u jedinici nije bio, [nečitko] disciplinovan. Overa: Vojni otsek Novi Sad 1, br. 18, 21. II [194]7. Učestvovao u ratu 1941–1945. Ranjen 11. IV 1944. g. u levi kuk, drugi put 22. IV 1945. u levo rame [nečitko]. Odlikovan Medaljom za hrabrost.',
        ],
      },
      { kind: 'photo', file: '0021004079-4.jpg', caption: 'Sa saborcima; on stoji drugi sleva, u beloj uniformi. Na poleđini je njegova posveta bratu' },
      { kind: 'photo', file: '0021004079-5.jpg', caption: 'Sedi desno, sa automatom' },
      { kind: 'photo', file: '0021004079-6.jpg', caption: 'Sombor, 26. VII 1945; sedi u sredini' },
      {
        kind: 'document',
        file: '0021004079-7.jpg',
        pages: ['0021004079-8.jpg', '0021004079-9.jpg', '0021004079-10.jpg'],
        caption: 'Njegova autobiografija, pisana rukom',
        transcripts: [
          'Autobiografija. Radenković Živan, rođen 26. VII 1926. god. u selu Počekovina, srez Trstenik, Srbija, od oca + Milorada i majke Simone, rođene Crnoglavac. Od rođenja pa do 1941. živeo sam kod svoje kuće baveći se zemljoradnjom. Završio sam 4 razreda osnovne škole, a zanimanje mi je zemljoradnik. 6-tog aprila 1941. godine, kada je stara jugoslovenska vojska odstupala, tada sam i ja sa njima pošao kao izbeglica [?] od kuće od okupatora, i to u pravcu Čačka. Nakon toga, kada je neprijatelj zauzeo Čačak i kada je počeo da zarobljava vojsku, ja sam se tada vratio svojoj kući, gde sam nastavio sa svojim radom. U jesen 1941. godine, kada je bila berba kukuruza, naišli su četnici u moje selo, te su mi naredili da im nosim municiju u pravcu Kraljeva. Kada smo stigli do Čukojevca, tu se počela voditi borba između četnika i Nemaca; kod napada na Kraljevo video sam da i Partizani učestvuju u borbi zajedno sa četnicima protiv Nemaca. Kada smo ušli u [nečitko] Kraljevo, video sam četnike da izdaju [?] protiv Partizana, pošto su počeli voditi borbu protiv Partizana; ja sam se tada priključio Partizanima, i to Šumadijskom odredu. Videvši da se dve strane bore između Partizana i četnika, ja sam rešio da odem svojoj kući, a bio sam i mlad za borbu, pošto sam tada imao svega 15 godina. Oktobra meseca 1941-ve godine sam iz Čukojevca pošao u pravcu svoje kuće; pošto sam prešao reku Ibar, uputio sam se preko [nečitko] Goč planine, te preko [nečitko] planine sreza trsteničkog, i tako stigao svojoj kući.',
          'Kada sam stigao svojoj kući, nastavio sam i dalje svojim radom kod kuće. Polovinom decembra su naišli Partizani u moje selo, i pošto su našli mene sa još nekoliko drugova u kafani [nečitko] Markovića, pozvali su nas da srušimo most koji je ležao na reci [nečitko]. Taj poziv Partizana mi smo zadatak izvršili, pošto smo most i srušili u zajednici sa Partizanima. Pošto smo srušili most, naišle su nemačke trupe, i Partizani su nam savetovali da idemo svaki svojoj kući, a oni su takođe otišli svojim putem. Od kraja decembra 1941. godine pa do jula 1943. godine sam živeo kod svoje kuće radeći svoj zemljoradnički posao. Za sve to vreme nisam bio nikakav pripadnik nikakve političke organizacije. Januara 6-tog 1943. godine ubijen je od strane četnika moj komšija Miodrag [nečitko] i njegov [nečitko] Aleksić; nakon tri meseca doznao sam od četnika da mi preti opasnost, pošto sam učestvovao kod rušenja mosta sa Partizanima na reci [nečitko], i budući da sam se plašio četnika, bio sam primoran da se krijem. Dosadilo mi je to neprestano skrivanje, otac je moj tada rešio da me da u Poljsku stražu, pošto je poznavao kapetana [nečitko], glavnog komandanta Poljske straže. U Poljskoj straži sam bio stražar pred kasarnom, a posle u Trsteniku, a posle sam bio [nečitko] za čuvanje drva u Novo Selo. Za sve vreme provedeno u Poljskoj straži nisam primao platu niti ikakve prinadležnosti osim odeće. U Poljskoj straži sam proveo od jula 1943. do 28-og novembra 1943-će godine. 28-og novembra izdajom komandira straže [Vasić?], narednika i podnarednika [nečitko], bili smo predati četnicima, koji su nas odveli u šumu. Kako narednik tako isto i podnarednik su se izvukli, dok smo mi ostali sa četnicima. Decembra meseca sam bio raspoređen u četničku brigadu Nikole Gordića, kapetana, u kojoj sam ostao do 19. marta 1944. god. Za sve vreme provedeno u četnicima nisam u borbama učestvovao do napada na moje selo. Kod napada na selo Počekovinu učestvovao sam u borbi protiv [Ljotićeve?] vojske i milicije koja je bila pod komandom [nečitko].',
          'U pomenutoj borbi nikoga nisam ubio. U mojem mestu sam ostao samo jednu noć, i odatle sam dalje otišao sa četnicima u pravcu Goč planine. Na Goč planini smo se zadržali duže vreme, bez ikakvih borbi. Februara 28-og krenuli smo sa pomenute planine prema Toplici, ali sa kakvim ciljem, meni nije bilo poznato. U tom pokretu prema Toplici imali smo prvu borbu sa Partizanima kod Plane, a da li je to Velika Plana ili Mala Plana, to tačno ne znam; i tek tada sam ja video da se borba vodi protiv Partizana. Pošto se borba kod pomenutog mesta Plane završila, krenuli smo se prema Pustoj reci. Na [nečitko] Visu je takođe počela borba između Partizana i četnika. Kada je borba počela, ja sam se odvojio sa još šest drugova i prešao Partizanima na dan 19. marta posle podne, i stupio u II-gu Južnomoravsku brigadu, u kojoj sam dobio raspored i raspoređen u prvi bataljon, treću četu. U istoj jedinici sam ostao od 19. marta do juna 1944. god. Juna meseca sam raspoređen u četu [Zapadne Morave?] i zadatak nam je bio da imamo stvoriti šesnaestu brigadu. U Rasini smo osnovali šesnaestu brigadu, u kojoj sam ostao sve dok se nismo sastali sa Prvom divizijom [?]. U šesnaestoj brigadi sam bio vodnik I. voda Rasinskog [nečitko] omladinskog bataljona. Kada smo došli u [Borski?] rudnik, tada sam prekomandovan u 23-ću diviziju, 7-mu brigadu, III. bataljon, II. četu, gde sam ostao do napada na Beograd. Kod napada na Beograd budem ponovo prekomandovan u petu diviziju, X-tu Krajišku brigadu, II. bataljon, III. četu, i budem postavljen za vodnika prvog voda. U istoj jedinici sam ostao do 15-tog marta 1945. god. U istoj jedinici sam proizveden u čin vodnika. Pošto je 15-tog marta rasformirana X-ta Krajiška brigada, prekomandovan sam u 21-vu Srpsku diviziju, IV. brigadu, I-vi bataljon, III-ću četu, gde sam vršio dužnost vodnika prvog voda pomenute čete. U istoj jedinici sam odlikovan Medaljom za hrabrost,',
          'iz koje sam demobilisan 5-tog marta 1946. godine, pošto sam odslužio svoj rok. Po demobilizaciji iz J. A. vratio sam se svojoj kući, gde sam se prijavio kako Narodnim vlastima tako i vojnom delegatu sreza trsteničkog. Budući da sam kod kuće siromašnog stanja, stalo mi je bilo da potražim državnu službu, te sam napravio molbu na Odeljak železničko-saobraćajne milicije Novi Sad, što mi je i uspelo, te sam bio primljen u N. miliciju. U N. miliciju sam stupio 30-tog aprila 1946-te godine. Od 30-tog aprila 1946-te godine pa do 2-gog oktobra nalazio sam se na dužnosti u Železničko-saobraćajnoj miliciji u Novom Sadu, i to do dana današnjeg. Za tačnost gore navedenog tvrdim svojeručnim potpisom. Radenković Živan',
        ],
      },
      {
        kind: 'document',
        file: '0021004079-11.jpg',
        caption: 'Saučešće koje je komanda Keserovićevog Rasinskog korpusa poslala njegovim roditeljima, javljajući da je poginuo u borbi protiv partizana; on je tada već bio partizan',
        transcripts: ['Saučešće komandanta Rasinskog korpusa p. pukovnika Dragutina Keserovića i komandanta II Trsteničke brigade kapetana Nikole Gordića. U Toplici, 20. ov. meseca, u borbi protiv komunističke nemani, vršeći svoju najsvetiju dužnost, časno je položio svoj život na oltar slavne Otadžbine, a za svoj narod i za Njegovo Veličanstvo Kralja Petra II, vojnik-dobrovoljac II Trsteničke brigade Živan Radenković. Živan Radenković, dostojno vršeći svoju uzvišenu dužnost, predložen je za viteza Karađorđeve zvezde. Neka mu je slava i večita zahvalnost srpskog naroda, jer položi svoj život za našu slobodu i veličinu naše Otadžbine. Zastupa komandanta II Trsteničke brigade p. poručnik [potpis]'],
      },
    ],
    from: 'H. Radenković, bratanac',
    date: '2026-11',
  },
  {
    soldierId: '0122959615', // Radenković Milorada Živka of Počekovina (Porodična arhiva 9990000005), Živan's sister; the nephew's missing-fighter form of 2026-11-20 21:33
    photo: '0122959615-1.jpg', // cut from her military ID, shown whole in the album
    photoCaption: 'Fotografija iz vojne knjižice',
    text: 'Posle rata radila je u Tanjugu, Direkciji za informacije Vlade FNRJ, Radio Jugoslaviji, Saveznom zavodu za statistiku, Prijemnom centru FNRJ i Jugoslovenskoj foto agenciji, a od 1958. do penzionisanja radila je kao sekretar kabineta predsednika Savezne skupštine SFRJ. Nosilac je Ordena rada sa srebrnim vencem.',
    pieces: [
      {
        kind: 'document',
        file: '0122959615-2.jpg',
        pages: ['0122959615-3.jpg'],
        caption: 'Vojna knjižica',
        transcripts: [
          'Lični opis: stas srednji, kosa kestenjasta, lice okruglo, oči kestenjaste, nos pravilan, usta pravilna, osobeni znaci nema. Prezime, očevo ime i ime: Radenković Milorada Živka. Svojeručni potpis: Radenković Živka.',
          'Datum i mesto rođenja: 27. III 1929, Počekovina. Mesto stalnog boravka: Beograd. Vojni otsek sreza (grada): Beograd. Nacionalnost: srpkinja. Škole u građanstvu i pismenost: gimnazija [?]. Zanimanje i soc. poreklo: službenica, službeničko. Znanje jezika: srpsko-hrvatski. Datum stupanja u JNA: [nečitko] XII 1943. Osposobljen u JNA: VES 182. Otpušten iz JNA: [nečitko] 1945. Čin pri otpustu iz JNA: [nečitko].',
        ],
      },
      { kind: 'photo', file: '0122959615-4.jpg', caption: 'Stoji u sredini' },
      { kind: 'document', file: '0122959615-5.jpg', caption: 'Njena biografija (prva strana): uhapšena 1943. kao partizanski saradnik, pobegla iz zatvora i stupila u XVI jastrebački odred, u kome je već bio njen brat Živan' },
      { kind: 'document', file: '0122959615-6.jpg', caption: 'Rešenje o priznanju radnog staža, 1954: u NOB-u od 15. 12. 1943. do 15. 5. 1945.' },
      { kind: 'document', file: '0122959615-7.jpg', caption: 'Povelja o odlikovanju Ordenom rada sa srebrnim vencem' },
    ],
    from: 'H. Radenković, bratanac',
    date: '2026-11',
  },
  {
    soldierId: '0122959616', // Radenković Milorada Petar of Počekovina (Porodična arhiva 9990000006), Živan's and Živka's elder brother; the nephew's missing-fighter form of 2026-11-20 21:50
    photo: '0122959616-1.jpg', // the photo the family set on his medal's certificate
    photoCaption: 'U kasnijim godinama',
    text: 'Godine 1941. uključio se u prikupljanje oružja za borbu protiv okupatora. Učestvovao je u pripremi bitke na Popini kao deo grupe koja je, pod rukovodstvom kapetana Milenkovića, porušila most u selu Gornji Ribnik na putu Kruševac–Kraljevo. Tih dana bio je kurir na liniji Trstenik–Kruševac tokom priprema za pružanje otpora na Popini kod Trstenika. Kada su započele borbe između četnika i partizana, povukao se i gledao kako da spase glavu od četnika u dolini Zapadne Morave, koji su proganjali porodicu zbog sestre i brata koji su bili u partizanima. Partizanima se priključio 1944. godine, što je upisano u Monografiju o učesnicima NOR-a opštine Trstenik (str. 305).',
    pieces: [
      { kind: 'document', file: '0122959616-2.jpg', caption: 'Monografija o učesnicima NOR-a 1941–1945. opštine Trstenik (1996), str. 305: „Radenković (Milorada) Petar, rođen 1923. g., učesnik NOR-a od 1944. godine”' },
      { kind: 'document', file: '0122959616-3.jpg', caption: 'Uverenje o odlikovanju Medaljom rada, 1972.' },
    ],
    from: 'H. Radenković, bratanac',
    date: '2026-11',
  },
  {
    soldierId: '0029000349', // Lukić Risto Veljko "Kurjak", narodni heroj, first commander of the 17. majevička; a visitor's form of 2026-11-20 22:00
    // two wartime photos as printed in a book (photographed from its pages), with the book's captions; no text, and no
    // relation given, so a visitor's; his portrait stays the one the site had
    pieces: [
      { kind: 'photo', file: '0029000349-1.jpg', caption: 'Na konju levo, kao komandant Majevičkog odreda, sa Rodoljubom Čolakovićem, u selu Vršani' },
      { kind: 'photo', file: '0029000349-2.jpg', caption: 'Slijeva nadesno: Haso Burić, Veljko Lukić Kurjak, Rodoljub Čolaković, Cviko Radovanović i Nikola Simić (april 1943, selo Vršani)' },
    ],
    from: 'N. Zarić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122959609', // Milutinović Olga "Debela" of Gledić (Kraljevo), activist (Poruke posetilaca 9992000001); F. Adžić's message
    text: 'Njeno ime nosi Osnovna škola u Godačici kod Kraljeva, a ispred škole je od 1972. njena bista.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122959610', // Vilotijević Dragomir "Crni" of Kraljevo, activist (Vikipedija 9991000001)
    text: 'Osnovna škola „Braća Vilotijević” u Kraljevu nosi ime njega i njegovog brata, narodnog heroja Rada Vilotijevića Viće.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Драгомир_Вилотијевић_Црни',
  },
  {
    soldierId: '0122959611', // Kuzmanović Tihomir of Donja Gorevnica, activist (Vikipedija 9991000002)
    photo: '9990000007-1.jpg', // the relief of his plaque, as his portrait (the user, 2026-11-20)
    photoFrom: 'Vikipedija',
    photoCaption: 'Reljef sa spomen-ploče u Žiči',
    pieces: [{ kind: 'photo', file: '9990000007-2.jpg', caption: 'Spomen-ploča na Zadružnom domu u Žiči' }],
    text: 'Zadrugari i meštani Žiče postavili su mu spomen-ploču nad ulazom u Zadružni dom, koji je podignut 1935. na njegovu inicijativu.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Тихомир_Кузмановић',
  },
  {
    soldierId: '0122912114', // Bogavac Vukašina Dragoslav, narodni heroj, of Veliđe (Berane), Vikipedija 9991000004; a visitor's message of 2026-11-20 (F. Adžić, who didn't write the article)
    photo: '0122912114-1.jpg', // F. Adžić's own, clearer than his Wikipedia article's, which it replaced (his message of 2026-11-20)
    text: 'U Kraljevu je radio u Fabrici vagona i bio među organizatorima protesta i štrajkova. Godine 1941. bio je sekretar Okružnog komiteta KPJ za Kraljevo i od pristiglih boraca sastavio je tri odreda; u Bosni je postao komesar Fočansko-čelebićkog odreda. Poginuo je u proleće 1942. na Vrbnici na Zelengori, kada su se 5. proleterska brigada, Vrhovni štab i ranjenici probijali iz četničkog obruča.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
    wikipedia: 'https://sr.wikipedia.org/wiki/Драгослав_Богавац',
  },
  {
    soldierId: '0136014584', // Pirić Velimir Đorđe of Čibukovac (Kraljevo), census part Srbija; one of the five Pirić brothers
    text: 'Bio je jedan od petorice braće Pirić iz Kraljeva, koji su svi bili partizani: Dragomir, Đorđije Đorđe, Milivoje, Jovan i Života. Rat je preživeo samo Života.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0136014585', // Pirić Velimir Milivoje of Čibukovac (Kraljevo), census part Srbija; one of the five Pirić brothers
    text: 'Bio je jedan od petorice braće Pirić iz Kraljeva, koji su svi bili partizani: Dragomir, Đorđije Đorđe, Milivoje, Jovan i Života. Rat je preživeo samo Života.',
    from: 'F. Adžić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122957805', // Kupres Marka Miloš of Kožuhe (Doboj), narodni heroj, Borci drugih jedinica
    text: 'U čast ovog narodnog heroja Kulturno-umjetničko društvo u Kožuhama nosi ime po njemu.',
    from: 'N. Kaišarević',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0069002027', // Čolnik Karel of Rošpoh (Maribor), Bračičeva brigada; a historian's form of 2026-11-21 08:23
    // (author of "Anzac Guerrillas", co-author of "The Greatest Escape"), sent in English, translated here; his three
    // photos (lost by the form's /api/prilog on Vercel) came again by mail on 2026-11-23: a portrait from the 1950 Australian
    // immigration file, the standing photo cut from Jože Petek's photograph of the escape, that whole photograph
    photo: '0069002027-1.jpg',
    photoCaption: 'Iz australijskog useljeničkog dosijea, 1950',
    pieces: [
      { kind: 'photo', file: '0069002027-2.jpg', caption: 'Isečak sa fotografije Jože Peteka, septembar 1944' },
      {
        kind: 'photo',
        file: '0069002027-3.jpg',
        caption: 'Kolona odbeglih ratnih zarobljenika i partizanske pratnje, boraca pohorske čete Lackovog odreda, na putu kroz Savinjsku dolinu. Fotografija: Jože Petek',
      },
    ],
    text: 'Bio je u pratnji pod komandom Franca Grudna koja je od 1. do 7. septembra 1944. sprovela 105 odbeglih ratnih zarobljenika iz zemalja Komonvelta i Francuske sa Pohorja do Save. Sa suprugom Anicom iselio se 1950. u Melburn, u Australiji. Godine 1985. pojavio se u dokumentarnom filmu Televizije Ljubljana i australijskog SBS-a „Pot k svobodi” („March to Freedom”).',
    from: 'E. Goldrick, istoričar',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122959617', // Muhadinović Jovana Radovan of Kranji Do (Cetinje), not in any book on the site: his grandson's
    // missing-fighter form of 2026-11-21 18:05 (Porodična arhiva 9990000007); his own words, as sent
    text: 'Ratni vojni invalid. Ranjen na brdu Bukovica, Cetinjski srez, pri napadu na bunkersko gnijezdo neprijatelja. Odlikovan nekoliko puta; 1948. dodijeljena mu je Medalja za hrabrost.',
    from: 'J. Muhadinović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0082000602', // Dimitrić (Dimitrijević) Branko "Jaša" of Jazak, 5. vojvođanska; his grandson's two forms of
    // 2026-11-21 20:16 and 20:36; the names of his wife, children and siblings left out (living people among them)
    photo: '0082000602-1.jpg', // in uniform with a titovka
    text: 'Nadimak iz rata: Jaša. Ranjen je u nogu tokom rata; operisan je nekoliko puta bez uspeha, a rana nikada nije potpuno zarasla. Posle rata doslužio je vojni rok u Gardijskoj brigadi. Živeo je povučeno u Jasku, oženio se 1947. i bavio se poljoprivredom; društveno-politički angažman nakon rata ga nije zanimao. Amaterski je svirao bas na igrankama. Preminuo je 2002. i sahranjen na seoskom groblju u Jasku.',
    pieces: [
      { kind: 'photo', file: '0082000602-2.jpg', caption: 'Posle rata, za vreme dosluženja vojnog roka u Gardijskoj brigadi; vidi se pečat' },
    ],
    from: 'D. Dimitrijević, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0060010080', // Macut Pavao, 8. kordunaška, načelnik štaba of its 2. brigada; a form of 2026-11-21 20:42 by a
    // distant relative. A public office of someone alive is dated, never "sada" (the user, 2026-11-21: "as of november
    // 2026 ... so we dont have to change it later")
    text: 'Posle rata služio je u Jugoslovenskoj narodnoj armiji i penzionisan je u činu pukovnika. Otac je Đura Macuta, predsednika Vlade Srbije u novembru 2026. Rođen je 1915, a umro 2008. ili 2009.',
    from: 'D. Dimitrijević, dalji rođak',
    date: '2026-11',
  },
  {
    soldierId: '0060001137', // Macut Nikole Đuro of Pješćanica, 8. kordunaška, fell 17.06.1943 at Cetingrad; the same
    // sender's form of 2026-11-21 20:39 (the office dated, as above)
    text: 'Rođeni stric Đura Macuta, predsednika Vlade Srbije u novembru 2026, koji je po njemu dobio ime.',
    from: 'D. Dimitrijević, dalji rođak',
    date: '2026-11',
  },
  {
    soldierId: '0122961304', // Macut Miloša Petar "Pero" of Pješčanica, not in any book: the same sender's missing-fighter
    // form of 2026-11-21 20:53 (Porodična arhiva 9990000009); of his death only "unclear circumstances" (the user,
    // 2026-11-21), not the investigation the family heard of
    text: 'Porodica njegove sestričine pamti da je od oslobođenja Rume, 27. oktobra 1944, bio u OZN-i. Borio se na Sremskom frontu i ranjavan je više puta. Poginuo je verovatno 1945. ili 1946, pod nerazjašnjenim okolnostima.',
    from: 'D. Dimitrijević, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0122959606', // Eftimovski Gjore of Sušica (Gostivar), brother of Kiro (Porodična arhiva)
    text: 'Роден е 1925 година во село Сушица. Потекнува од многучлено сиромашно семејство. Уште како дете оди на печалба во Белград како општ работник, каде што се запознава со идеите на напредното работничко движење. За време на окупацијата на земјата во Белград е примен за член на СКОЈ, а нешто подоцна и за член на КПЈ. Кон крајот на 1941 година е уапсен од страна на Недиќевата полиција, но заради немање докази набрзо е пуштен на слобода. Особена активност и бестрашност покажува во вршењето на многу одговорни курирски задачи. Во единиците на Народноослободителната војска стапил доброволно во јуни 1943 година, како борец во составот на Космајскиот народноослободителен одред. Во една акција во 1944 година во Белград е заробен од германскиот фашистички окупатор и нешто подоцна стрелан во Бањица. За него постои спомен-обележје на гробиштата на ослободителите на Белград.',
    from: 'nećak',
    date: '2026-11',
  },
  {
    soldierId: '0135001012', // Eftimovski Božo Kiro of Sušica (Gostivar), census part Makedonija
    text: 'Роден е 1923 година во село Сушица. Потекнува од многучлено сиромашно семејство. Уште како дете останал сирак без татко, па бил присилен да оди на печалба во Белград, каде што работи како општ работник. Во слободните мигови постојано е во друштво со напредни работници и младинци, што му дава можност да се запознае со идеите на напредното работничко движење. Во Белград останал до капитулацијата на стара Југославија. Веднаш по капитулацијата се враќа во своето родно место, се приклучува во напредното движење и станал член на Месниот народноослободителен одбор. Бил член и на партискиот актив на селото. Во единиците на Народноослободителната војска стапил доброволно во мај 1944 година, како борец во составот на Првата македонско-косовска бригада. Со својата единица учествувал во сите борби и акции. Загинал на 28 август 1944 година во борбите за ослободување на Кичево. Неговиот брат Ѓоре (роден 1925 година, исто така од Сушица) во јуни 1943 година стапил во Космајскиот народноослободителен одред. Во една акција во 1944 година во Белград е заробен од германскиот окупатор и подоцна стрелан во Бањица. За него постои спомен-обележје на гробиштата на ослободителите на Белград.',
    from: 'nećak',
    date: '2026-11',
  },
  {
    soldierId: '0021004669', // Spasojević Miloša Milovan of Rušanj, 4. srpska: his grandson's form of 2026-11-22 12:43
    text: 'Preminuo je 24. decembra 1998. u Rušnju, gde je i sahranjen. Iza sebe je ostavio dve ćerke, četvoro unučadi i osmoro praunučadi.',
    from: 'B. Nikolić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0018001538', // Sekulić Mane Sava, 2. vojvođanska (the book prints his name alone): a cousin's form of
    // 2026-11-22 17:36; the census's Sekulić Mane Savo of Žarkovac is the same man
    text: 'Sava Sekulić je rođen u Dobrincima, srez Ruma, 1922. godine, od oca Mane Sekulića iz sela Tobolić, kotar Slunj, i majke Milije Trbojević iz sela Bugar, kotar Bihać. Od sredine 1920. do početka Drugog svetskog rata Sekulići su živeli u selu Žarkovac kod Rume. Sava se u NOB uključio zajedno sa mlađim bratom Milanom početkom 1943. i poginuo je, prema nekim podacima, 6. maja 1945. kod sela Drljanovci blizu Bjelovara, u završnim operacijama za oslobođenje zemlje. Sused Rade Devrnja se sećao da su u izbeglištvu u Bogatiću, prilikom konačnog oslobođenja 1944, on i otac videli Savu kao člana neke vojvođanske partizanske jedinice i da je Sava viknuo Radinom ocu: „Čika Milane, sloboda, vratićemo se mi u naš Žarkovac!“',
    from: 'J. Eror, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0136028645', // Kojić Ilije Miodrag of Brusnik, census part Srbija: his grandson's form of 2026-11-22 12:35,
    // in English (translated); his father's emigration, his brother's death and who may have killed him left out
    // (about others, a guess); the wedding photo is colourised; his face cut from it is his portrait (the user, 2026-11-23)
    photo: '0136028645-2.jpg',
    photoCaption: 'Na dan venčanja',
    pieces: [{ kind: 'photo', file: '0136028645-1.jpg', caption: 'Miodrag i Ružica na dan venčanja' }],
    text: 'Otac mu je bio Ilija, majka Milka, rođena Stojanović, a supruga Ružica, rođena Milošević, svi iz Brusnika. Ćerke Miroslava i Slobodanka bile su premale da ga zapamte. Ružica je išla kod Moše Pijade da traži pomoć da se pronađu Miodragovi posmrtni ostaci u istočnoj Bosni. Primio ju je na tri minuta i obećao da će pomoći, ali do toga nikad nije došlo.',
    from: 'M. Kojadinović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0138008216', // Ćosić Ilije Bogdan of Bingula, census part Vojvodina: his brother's grandson's form of
    // 2026-11-22 18:54 with a wartime portrait, in his words; the error report of 18:50 (no sender) is the visitors' note
    // below (the user, 2026-11-23: the family's apart from the rest)
    photo: '0138008216-1.jpg',
    text: 'Bio je komesar i ađutant Peka Dapčevića na rejonu sremskog fronta kod Bingule. Ranjavan je tri puta: prvi put kod Aranđelovca, zatim kod Šarengrada i treći put kod Sesveta kod Zagreba.',
    from: 'B. Kanja, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0138008216', // the same man: the error report of 2026-11-22 18:50, no sender; its words
    text: 'Nije rođen u Kuzminu nego u Binguli. Bio je poručnik, politički komesar. Preminuo je 1947. godine. Bio je u pokretu otpora u Zemunu, otišao je u Posavski odred, iz Posavskog odreda u 2. šumadijsku brigadu, koja je posle preformirana u 21. srpsku brigadu, a zatim je prešao u 31. srpsku brigadu 21. divizije.',
    from: 'Ispravka po prijavi',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0138006914', // Bućko J Milan of Bingula, census part Vojvodina: the error report of 2026-11-22 18:58, no sender
    // (fell by Grgurevci, a vodnik: rows by patch_record); the book it names, at the user's word (/pregled, 2026-11-23)
    text: 'U knjizi „Mladost slobodi darovana” o njemu je priča „Miner Vanja”.',
    from: 'Ispravka po prijavi',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122961366', // Mijanović Nikole Milutin "Mošo" of Cetinje, Lovćenski odred, not in any book: his nephew's
    // missing-fighter form of 2026-11-22 23:01 (Porodična arhiva 9990000014); his career after the war at the user's word
    // (2026-11-22); the portrait is from after the war: his card's portrait at the user's word (2026-11-23, "Milutin add
    // photo as profile"), not among the home page's wartime portraits (wartimePortraits.ts)
    photo: '0122961366-1.jpg',
    photoCaption: 'Posle rata',
    text: 'Nosilac je Partizanske spomenice. Teško je ranjen u borbama protiv četnika u blizini Čeva u ljeto 1944. godine i zarobljen. Pobjegao je iz cetinjske bolnice, gdje je liječen da bi mu se sudilo. Poslije rata završio je studije srpskog jezika i jugoslovenske književnosti na beogradskom Filozofskom fakultetu. Bio je direktor Izdavačkog preduzeća „Narodna knjiga“ na Cetinju, sekretar Opštinskog komiteta SK Cetinje i direktor Narodnog muzeja SR Crne Gore. Umro je u Beogradu 1989. godine, gdje je i sahranjen.',
    from: 'I. Mijanović, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0122961367', // Mijanović Nikole Vladimir of Cetinje, Lovćenski odred, Milutin's brother, not in any book:
    // the same nephew's form of 2026-11-22 23:14 (Porodična arhiva 9990000015); his photo in uniform is his portrait
    photo: '0122961367-1.jpg',
    photoCaption: 'U uniformi',
    text: 'Rođen je 1924. godine na Cetinju, gdje je završio gimnaziju. Bio je predratni član SKOJ-a i nosilac Partizanske spomenice 1941, borac Lovćenskog partizanskog odreda. Zarobljen je 1942. godine od strane nacionalista Krsta Popovića i interniran u Italiju, odakle je pobjegao u septembru 1943, vratio se u Crnu Goru i ponovo se priključio NOP-u. Kraj rata dočekao je kao obavještajni oficir. Poslije rata završio je Ekonomski fakultet. Bio je sekretar Okružnog komiteta KPJ za Cetinje, direktor ATP „Tara“ i generalni direktor EI „Obod“. Umro je u Beogradu 2013. godine i sahranjen na Cetinju.',
    from: 'I. Mijanović, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0054003542', // Zrnić Simo of Turjak, 12. krajiška: his great-grandson's form of 2026-11-22 21:02 (no name for the card); the
    // prison death after the war shown at the user's word (2026-11-22)
    text: 'Bio je prvoborac. Posle rata umro je u zatvoru u Zenici; grobno mesto nije poznato.', // the user's own wording (/pregled, 2026-11-23)
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0038000017', // Aničić Ivana Dragoljub of Nepričava, 8. crnogorska: his niece's account through a man of
    // the next village (form of 2026-11-22 18:30, no name for the card); the user, 2026-11-22: the family's father and
    // fate on the card, the books' "poginuo kod Račinovaca" in their references
    text: 'Porodica pamti da mu je otac bio Ivan i da nije poginuo u ratu. Dugo se borio sa administracijom da dokaže da je greškom zaveden kao poginuli borac.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0001007129', // Mihić Gojka Maksim of Čavaš (Ravno), Prva proleterska, linked with his records in the 53.
    // srednjobosanska divizija and the 14. srednjobosanska (0033000402, 0056001266): his nephew's four forms of 2026-11-21/22 (permission for text, photos and
    // the name as initial, surname and relation); the photo the forms announced never came through, the user found it on
    // the family's site (mihici.com, which the nephew's form links) and gave it, 2026-11-23
    photo: '0001007129-1.jpg',
    text: 'Rođen je 1926. u hercegovačkom selu Čavaš, danas u opštini Ravno. Porodica se 1934. preselila u Miškovce kod Dervente.',
    from: 'V. Mihić, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0122961365', // Nišić Džafera Rizah of Živinice, 16. muslimanska, not in any book: his grandson's
    // missing-fighter form of 2026-11-22 20:24 (Porodična arhiva 9990000011); the column under the banner is in his album
    pieces: [{ kind: 'photo', file: '0122961365-1.jpg', caption: 'U stroju u Tuzli, oktobra 1943. Rizah Nišić je zamjenik komandira 2. čete drugog bataljona 16. muslimanske NOU brigade.' }],
    text: 'Poslije demobilizacije 1953. nastanio se u Gračanici, gdje je i preminuo 2004. godine.',
    from: 'S. Nišić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0132046220', // Krstulović Ivana Zdravko of Split, census part Hrvatska (fell 1943 at Kalinovik): the form of
    // 2026-11-23 02:53 by his brother's grandson (the brother is Krstulović Ante "Tonko", Porodična arhiva 9990000016); the
    // census's year stands, the grave's 1944 is in the note; the photo of the grave in his album
    pieces: [{ kind: 'photo', file: '0132046220-1.jpg', caption: 'Grob na splitskom Lovrincu' }],
    text: 'Po obiteljskim pričama poginuo je za vrijeme Pete ofanzive, ali na njegovom grobu u Splitu piše 1944. Poslije rata braća su otišla po njegove posmrtne ostatke i pokopala ga na splitskom Lovrincu, pored majke Mile.',
    from: 'A. Krstulović, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0036100433', // Ivanišević-Andrijić Jerka Vjera "Vesna" of Split, 1. dalmatinska: a photo alone, form of
    // 2026-11-23 08:28 (no name for the card); her wartime portrait
    photo: '0036100433-1.jpg',
    photoCaption: 'U uniformi',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0018000298', // Divljak Milorada Živko of Novi Karlovci, 2. vojvođanska: his grandson's form of 2026-11-23 08:45
    // (Porodična arhiva 9990000019 referenced, for the wound and the death in his rows)
    text: 'Učesnik je bitke na Sutjesci, gde je ranjen na dva mesta. Posle rata bio je upravnik sirotišta u Savinom Selu. Zatim se s porodicom preselio u Zrenjanin, gde je radio kao sekretar u „Luxolu“. Posle teškog infarkta penzionisan je. Umro je u Zrenjaninu 1990. godine.',
    from: 'S. Tuba, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0033000126', // Dvorski Josip of Herešin, 53. srednjobosanska divizija: his brother's grandson's form of 2026-11-23
    // 10:20 (the father Mijo by correction 317147); the brother is Dvorski Mije Martin (Porodična arhiva 9990000018)
    text: 'Brat je Martina Dvorskog iz Herešina, borca 21. slavonske udarne brigade.',
    from: 'D. Švalek, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0122961368', // Krstulović Ivana Ante "Tonko" of Split, not in any book: his grandson's missing-fighter form of
    // 2026-11-23 03:11 (Porodična arhiva 9990000016); Zdravko (0132046220) is his brother
    text: 'Bio je prvoborac 1941. godine, pripadnik splitskih udarnih grupa koje su 1941. bacile bombe na talijansku vojnu glazbu u Splitu. Talijani su ga uhapsili i poslali na robiju u Italiju. Poslije kapitulacije Italije uspio se pridružiti slovenskim partizanima. Umro je u Splitu 1996. godine.',
    from: 'A. Krstulović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122961369', // Ivančić Paško of Split, not in any book: the same sender's missing-fighter form of 2026-11-23 08:24
    // (Porodična arhiva 9990000017)
    text: 'Od 1944. bio je borac, puškomitraljezac 20. dalmatinske divizije. Sudjelovao je u borbama za oslobođenje Knina, Gospića, Rijeke i Trsta. Po završetku rata, 1946. godine, izgubio je nogu pri čišćenju minskih polja u Sloveniji. Umro je u Splitu 1998. godine.',
    from: 'A. Krstulović, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0034900003', // Dvorski Mije Martin of Herešin, 21. slavonska (in the unit since 2026-11-23: the family names it; was 0122961370), not in any book: his grandson's missing-fighter
    // form of 2026-11-23 10:17 (Porodična arhiva 9990000018); the photo in uniform, from a document, is his portrait;
    // Josip (0033000126) is his brother
    photo: '0122961370-1.jpg',
    photoCaption: 'U uniformi',
    text: 'U 21. slavonsku udarnu brigadu stupio je dragovoljno 18. novembra 1943. Dva puta je ranjen 1944. godine u okolici Slavonske Požege. Nakon liječenja bio je u Glavnom štabu Hrvatske, a zatim u 1. bataljonu 2. autopuka 2. jugoslavenske armije.',
    from: 'D. Švalek, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122940691', // Čelebić Ilije Jovan of Štitari (Cetinje), fell 1. 12. 1941 at Pljevlja: his nephew's form of
    // 2026-11-23 13:21 (on the Spomenica's record 0122926735, joined to this one the same day)
    text: 'Sahranjen je u spomen-kosturnici spomenika palima u Pljevaljskoj bici, na Stražici u Pljevljima.',
    from: 'Ž. Čelebić, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0132008320', // Kontić Ivan Joso of Trbounje (Drniš), census part Hrvatska: his niece's form of 2026-11-23 13:02
    // (text yes, no name for the card); the party by override
    text: 'Kao mlad bio je član KPJ i 1941. otišao je u partizane. Poginuo je u oslobađanju Rijeke, ali se ne zna gdje se sve borio.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0007900037', // (was 0122926745 in Borci drugih jedinica; in the 2. dalmatinska since 2026-11-23) Čelebić Ilije Novak of Štitari (Cetinje), Jovan's brother: their nephew's form of 2026-11-23
    // 13:30 (Porodična arhiva 9990000022 joined to his record: the wound and the death of 1946 in his rows)
    text: 'Ranjen je prilikom oslobađanja Cresa 1945, a umro je 1946. u bolnici u Zagrebu od zadobijenih rana. Grob mu je na Cetinju, gdje je prenesen iz Zagreba.',
    from: 'Ž. Čelebić, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0122905539', // Đukić Borivoja Vidoje of Mirosaljci (Arilje), 38. divizija: his nephew's form of 2026-11-23 13:38
    // (the place of death Odžak by override, as the census has it)
    text: 'Poginuo je u Bosni, u Posavini, u bici kod Odžaka, u borbi protiv dobro utvrđenih ustaških formacija. Sahranjen je zajedno sa više palih drugova kod Kule u Zvorniku.',
    from: 'M. Đukić, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0045000441', // Nevajda Luke Vasilj of Vlahović (Glina), 8. banijska: his grandson's form of 2026-11-23 13:46 (no
    // name for the card)
    text: 'Pobjegao je sa strijeljanja u Banskom Grabovcu; jedan je od nekolicine preživjelih.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0043000203', // Buturović Ahmeta Fadil of Prozor, 10. hercegovačka (linked with the Mostarski bataljon's
    // 0125000128, 317155): a post of the Facebook page "Bitka na Sutjesci" the user sent, 2026-11-23; the portrait cut from
    // it (tinted); the death by correction 317156
    photo: '0043000203-1.jpg',
    photoCaption: 'U uniformi',
    text: 'Komunist, borac 10. hercegovačke brigade na Neretvi i Sutjesci. Ubijen je 1993. godine u Sarajevu, za vreme opsade grada.',
    from: '„Bitka na Sutjesci”',
    origin: 'facebook',
    date: '2026-11',
  },
  {
    soldierId: '0040011900', // Čelebić Ilijin Joko of Štitari, 4. proleterska ("poginuo decembra 1942" in its two lists): his
    // nephew's missing-fighter form of 2026-11-23 13:36 for "Čelebić Đoko" is he, the family wins (the user, 2026-11-23);
    // Porodična arhiva 9990000023 referenced, the rows by correction 317154
    text: 'Za vrijeme rata bio je komesar u X crnogorskoj udarnoj brigadi. Nestao je 1949. godine kao pilot JRV, u padu aviona u Dunav.',
    from: 'Ž. Čelebić, sinovac',
    date: '2026-11',
  },
  {
    soldierId: '0122961373', // Siriščević Josip of Split, an illegal shot in Šibenik 22.5.1942 (a man of the movement, Porodična arhiva
    // 9990000026): his grandson's missing-fighter form of 2026-11-23 14:54 with three photos (after his comment the user passed on)
    photo: '0122961373-1.jpg',
    pieces: [
      { kind: 'photo', file: '0122961373-2.jpg', caption: 'Spomen-kamen u Splitu streljanim splitskim komunistima, 22. svibnja 1942.' },
      { kind: 'photo', file: '0122961373-3.jpg', caption: 'Spomen-ploča u Spomen-kosturnici na Lovrincu' },
    ],
    text: 'Nije bio pripadnik nijedne jedinice. Zbog ilegalnog rada u Splitu uhapsili su ga talijanski okupatori i strijeljali 22. 5. 1942. u Šibeniku, zajedno sa cijelom grupom koju je predvodio Rade Končar. Pokopan je u Spomen-kosturnici na splitskom groblju Lovrinac; ime mu je navedeno i u kosturnici i na spomeniku u Spomen-parku Šubićevac u Šibeniku. Njegov slučaj zabilježen je u dokumentima na stranici Znaci (znaci.org).',
    from: 'I. Profaca, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0013010439', // Heganović Salih, 6. krajiška (the survivors' list, name alone): his grandson's form of 2026-11-23 14:09
    text: 'Kao dijete pomagao sam mu pri kupanju, i objašnjavao mi je da su ožiljci na leđima od rane koju je zadobio od ustaša pri napadu partizana na Karlovac. Bio je u 6. krajiškoj brigadi. Poslije rata radio je kao rudar u Kaknju.',
    from: 'A. Velispahić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0001013150', // Vihtner (the book: Vihner) Rudolfa Gordana, Prva proleterska: her son's forms of 2026-11-23 15:00 and
    // 15:41 with four photos (the surname, nationality and day of birth by correction 317157); the school photo her portrait
    photo: '0001013150-1.jpg',
    photoCaption: 'Đačka fotografija',
    pieces: [
      { kind: 'photo', file: '0001013150-2.jpg', caption: 'Sa suprugom Bojanom Belingarom' },
      { kind: 'photo', file: '0001013150-3.jpg', caption: 'Posle rata' },
      { kind: 'photo', file: '0001013150-4.jpg', caption: 'Sa sinom' },
    ],
    text: 'Rođena je 30. marta 1927. u Beogradu, od oca Rudolfa Vihtnera i majke Miroslave, rođene Predojević. Posle rata udala se za Slovenca Bojana Belingara, takođe partizana. Do penzionisanja radila je u Nuklearnom institutu u Vinči.',
    from: 'B. Belingar, sin',
    date: '2026-11',
  },
  {
    soldierId: '0001005586', // Krnić Lovre Mirko of Konjevrate, Prva proleterska: his grandson's form of 2026-11-23 15:07 (from the book
    // Dalmatinci u Prvoj proleterskoj brigadi); the death by correction 317158
    photo: '0001005586-1.jpg',
    text: 'Za NOP radi od druge polovine 1941, član SKOJ-a od proljeća 1942. Početkom listopada 1942. odlazi u partizane i u Ključu stupa u 6. beogradski bataljon 1. proleterske brigade, prvo kao borac, zatim puškomitraljezac. U srpnju 1943. dolazi u Sinjski partizanski odred, gdje je komandir čete, a početkom 1945. radi pri Komandi mjesta Šibenik u KNOJ-u. Umro je 1990. godine.',
    from: 'L. Krnić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0085000297', // Janković M Živko, 7. srpska: his granddaughter's photo of 2026-11-23 15:13 (no text); his face cut
    // from the family photo is his portrait, the whole photo in his album (the user, 2026-11-23: "crop photo")
    photo: '0085000297-2.jpg',
    pieces: [{ kind: 'photo', file: '0085000297-1.jpg', caption: 'Porodična fotografija' }],
    from: 'R. Janković, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0021005315', // Tinkić Miodraga Svetozar, 4. srpska: a relative's form of 2026-11-23 15:24 (in Cyrillic); the photo from
    // Gončin's book, him with comrades in a trench on the Srem front, cut to him: his portrait (the user, 2026-11-23: "photo not
    // added")
    photo: '0021005315-1.jpg',
    photoCaption: 'U rovu na Sremskom frontu (iz knjige M. Gončina „22. srpska kosmajska brigada”)',
    text: 'Poreklom je iz Ćuprije; ime je dobio po dedi Svetozaru, trgovcu i kafedžiji. Otac Miodrag bio je savetnik Ministarstva finansija. Imao je sestre Veru i Leposavu. Bio je kapetan JA. Sahranjen je sa sestrom Verom na Novom groblju u Beogradu.',
    from: 'A. Milosavljević Tinkić, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0118900042', // Petković Dane Dragica of Ostrvica, 3. lička: her granddaughter's form of 2026-11-23 15:32 with her wartime
    // photo (Porodična arhiva 9990000032 referenced, the death by correction 317160)
    photo: '0118900042-1.jpg',
    photoCaption: 'U uniformi, sa automatom',
    text: 'Udala se za Đuru Drobca (Jove). Živela je u Zemunu i Novom Sadu. Nosilac je Partizanske spomenice 1941; u NOV je stupila 1941, a ne marta 1944. Preminula je 13. februara 1991. u Novom Sadu, gde je i sahranjena pored supruga.',
    from: 'M. Drobac, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0054002338', // Petić Nenad of Mala Žuljevica, 12. krajiška: his nephew's form of 2026-11-23 15:34 (rank by 317161)
    text: 'Bio je poručnik. Ranjen je kod Srpca, kroz noge. Preživio je rat.',
    from: 'O. Petić, nećak',
    date: '2026-11',
  },
  {
    soldierId: '0132011863', // Sarapa (the census: Savap) Ilije Ljuban of Donji Klasnić, census part Hrvatska, fell 1943 at the
    // Sutjeska: his grandmother's brother, the form of 2026-11-23 15:35 (the surname by override); his father is 0132011862
    text: 'Sin je Ilije Sarape, također partizana. Groba nema; tijelo nikada nije nađeno.',
    from: 'D. Dvanajščak, pranećakinja',
    date: '2026-11',
  },
  {
    soldierId: '0002001654', // Drobac Jove Đuro of Gračac, Prva lička: his granddaughter's form of 2026-11-23 15:36 with his photos
    // (Porodična arhiva 9990000033 referenced: the Spomenica); his wife is Petković Dragica (0118900042)
    photo: '0002001654-1.jpg',
    photoCaption: 'U oficirskoj uniformi',
    text: 'Nosilac mnogih odlikovanja i Partizanske spomenice 1941. Supruga mu je bila Dragica, rođena Petković, takođe nosilac Partizanske spomenice.',
    from: 'M. Drobac, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0132011862', // Sarapa Rade Ilija of Donji Klasnić, census part Hrvatska: his great-granddaughter's form of 2026-11-23
    // 15:41 with his wartime photo (the death by override); Ljuban (0132011863) is his son
    photo: '0132011862-1.jpg',
    photoCaption: 'U partizanskoj uniformi',
    text: 'Iz NOB-a se vratio. S obitelji se preselio s Banije u Šidske Banovce, gdje je ubrzo umro od posljedica ranjavanja. Iza sebe je ostavio ženu Evicu, sina Milana i kćeri Anku i Jelenu.',
    from: 'D. Dvanajščak, praunuka',
    date: '2026-11',
  },
  {
    soldierId: '0091000267', // Milosavljević Ilija of Ćuprija, 20. srpska: a relative's form of 2026-11-23 15:42 (in Cyrillic; father,
    // day of birth, party, birthplace by correction 317163); the photo from the chronicle "Na Moravi Ćuprija", marked unknown fighter
    photo: '0091000267-1.jpg',
    photoCaption: 'Iz hronike „Na Moravi Ćuprija” (D. Đulić, M. Milačić), gde je obeležen kao nepoznati borac',
    text: 'Rođen je 22. maja 1922. od oca Bogomira I. Milosavljevića Tinkića i majke Stane. U SKOJ je primljen 1940, a u KPJ 1941. U njegovoj kući, kao i u kućama brata Živojina Žikice i sestre Seke, tokom rata su održavani kursevi prve pomoći; oni su izvezli i veliku partijsku zastavu koju su predali Okružnom komitetu SKOJ-a. Poginuo je 28. novembra 1944. Telo mu je vraćeno u Ćupriju i ovde je sahranjen, a ne na mestu pogibije kako piše u knjizi; njegova sahrana bila je navodno najveća u to vreme.',
    from: 'A. Milosavljević Tinkić, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0002005456', // Mrkonjić Jankov Sava of Gaćeša Selo, Prva lička: his grandson's form of 2026-11-23 15:45 with his photo
    // (Porodična arhiva 9990000034 referenced for the line; the death by 317165)
    photo: '0002005456-1.jpg',
    text: 'U NOB-u od 1941, borac partizanskog odreda „Gaćeša Selo”; od februara 1942. u 3. četi 2. bataljona 1. kordunaškog partizanskog odreda. Kasnije borac 3. bataljona 1. ličke proleterske brigade i 1. bataljona 15. kordunaške brigade. U toku rata jednom je ranjen u nogu, kod Generalskog Stola. Posle rata demobilisan je i nastavio da radi u rudniku kao poslovođa smene. Umro je 1986. u Gaćeša Selu, gde je i sahranjen.',
    from: 'M. Mrkonjić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0005900079', // (was 0122961375; in the Treća proleterska since 2026-11-23) Cvijetić Leke Milorad of Kordovina (Pljevlja), 3. proleterska sandžačka: his son's missing-fighter form of
    // 2026-11-23 15:11 (Porodična arhiva 9990000028; no name for the card)
    text: 'Posle rata bio je oficir JNA.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0122961376', // Jasenovčanin Vase Petar of Jasenovčani (Sisak), 7. banijska divizija: his granddaughter's missing-fighter
    // form of 2026-11-23 15:18 (Porodična arhiva 9990000029)
    text: 'U rat je stupio sa 18 godina i cijeli rat bio borac 7. banijske udarne divizije. Ranjen je kod Prozora. Poslije rata bio je komandir milicijske stanice.',
    from: 'T. Kovačević, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0122961377', // Radin-Mačukat Ante Ive-Vinko of Vodice: his grandson's missing-fighter form of 2026-11-23 15:24, the text
    // a page of a book of Vodice he photographed (Porodična arhiva 9990000030; no name for the card)
    pieces: [{ kind: 'document', file: '0122961377-1.jpg', caption: 'Stranica knjige o Vodicama, njegova natuknica (1045)' }],
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0122961378', // Kovačević Marko of Slovinci (Sisak), 7. banijska divizija: his granddaughter's missing-fighter form of
    // 2026-11-23 15:24 (Porodična arhiva 9990000031)
    text: 'Tokom rata bio je politički komesar u svojoj jedinici. Posle rata radio je kao matičar u Šašu i Sunji. Umro je 1968. godine.',
    from: 'T. Kovačević, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0004000147', // Belingar Bojan of Ljubljana, Ljubljanska brigada: his son's form of 2026-11-23 16:02 with three files
    // (Porodična arhiva 9990000043 referenced; rows by 317169); his wife is Vihtner Gordana (0001013150)
    photo: '0004000147-1.jpg',
    photoCaption: 'U uniformi',
    pieces: [
      {
        kind: 'document',
        file: '0004000147-2.jpg',
        caption: 'Uprava SVPB-B, 7. 3. 1945: čin poručnika',
        transcripts: ['Uprava S V P B - B. Položaj 7.3.1945. Ekonomatu S V P B - B. Glavni štab NOV in POJ Slovenije, Personalni odsek je z aktom štev 510. z dne 20.2.1945. odobril rang poročnika politkomisarju Belingarju Bojanu! Iskreno čestitamo! Smrt fašizmu - svoboda narodu! Politkomisar: [potpis]. Upravnik poročnik: dr. [potpis]'],
      },
      { kind: 'photo', file: '0004000147-3.jpg', caption: 'Na susretu boraca, u kasnijim godinama' },
    ],
    text: 'Rođen je 30. jula 1927. u Ljubljani, od oca Petera i majke Zinke, rođene Kolar. Ceo radni vek, do penzionisanja 1976, proveo je u Saveznom sekretarijatu za unutrašnje poslove u Beogradu. Supruga mu je bila Gordana, rođena Vihtner, takođe partizanka. Umro je 5. avgusta 2011.',
    from: 'B. Belingar, sin',
    date: '2026-11',
  },
  {
    soldierId: '0070101809', // Kolar Stane, dr., Tomšičeva brigada: his grandmother's brother, the form of 2026-11-23 16:30 with his
    // officer's portrait and a newspaper obituary (the day of birth and of death by 317170: the obituary's 1944, the form's 1945)
    photo: '0070101809-1.jpg',
    photoCaption: 'U oficirskoj uniformi, pre rata',
    pieces: [{ kind: 'document', file: '0070101809-2.jpg', caption: 'Iz novina: dr. Stane Kolar' }],
    text: 'Rođen je 14. februara 1903. u Gornjoj Radgoni, od oca Ivana Kolara i majke Marije, rođene Kovač. Sa 23 godine završio je medicinu, a zatim radio kao vojni lekar u Bihaću i Ljubljani. Godine 1937. oženio se Banjalučankom Mirom Stojanović, profesorkom nemačkog. Poginuo je 23. marta sa još 22 partizana u mestu Češnjice iznad Blagovice kod Domžala. Posle rata njegovi posmrtni ostaci preneti su u porodičnu grobnicu Kolarovih na groblju Žale u Ljubljani.',
    from: 'B. Belingar, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0132038452', // Španja Ante Sime of Vodice, census part Hrvatska: his great-grandson's form of 2026-11-23 16:22
    text: 'Okružen talijansko-četničkim formacijama, bacio je bombu pod sebe.',
    from: 'L. Španja, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0132038451', // Španja Ante Luce of Vodice, census part Hrvatska: the same great-grandson's missing-fighter form of
    // 2026-11-23 16:28 ("Španja Lujo", the verbs feminine: she); the death by override
    text: 'Bila je borac Prve primorske čete. Izdali su je domaći izdajnici iz takozvane AKM (antikomunističke milicije, četnici); strijeljana je na Srimskoj lokvi zajedno s ostalim drugovima.',
    from: 'L. Španja, praunuk',
    date: '2026-11',
  },
  {
    soldierId: '0053000943', // Gradac Mate Ante of Zapadna Plina, 11. dalmatinska: a photo, form of 2026-11-23 16:27
    photo: '0053000943-1.jpg',
    photoCaption: 'Sa harmonikom',
    from: 'D. Gradac',
    date: '2026-11',
  },
  {
    soldierId: '0005000052', // Musić Seid "Sejdo" of Nova Varoš, Treća proleterska: his grandson's form of 2026-11-23 16:53 (no name)
    text: 'Po saznanju porodice, umro je u Sarajevu.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0162000182', // Studen Miloš, 1. tenkovski bataljon: his grandson's form of 2026-11-23 17:03 (Porodična arhiva 9990000041
    // referenced; rows by 317172)
    text: 'Rođen je 1921. U partizanima je od 1942, borac Prvog tenkovskog bataljona 8. kordunaške udarne divizije. Učestvovao je u borbama za Trst. Posle rata, na osnovu sporazuma Tita i Envera Hodže, bio je instruktor tenkovskih jedinica u Valoni. Kasnije je radio u šumskom gospodarstvu kao vozač kamiona. Preminuo je 2007. godine.',
    from: 'Č. Studen, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0036001847', // Srzić I Marica of Makarska, 1. dalmatinska: her grandmother's sister's great-nephew, form of 2026-11-23
    // 17:21 (no name; Porodična arhiva 9990000042, the death by 317174)
    text: 'Poginula je na Krekovima, na Sutjesci. Kad su svi oko nje poginuli, uzela je mitraljez i nastavila pucati dok nije poginula; navodno je bila vrlo uspješna s mitraljezom. Ranije, kad su joj rekli da joj je poginuo brat, rekla je: „Svi koji su poginuli su moja braća.” Vrtić u Makarskoj nosio je njeno ime.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0036001845', // Srzić S Frane of Makarska, 1. dalmatinska: the same sender, form of 2026-11-23 17:25 (no name; 317175)
    text: 'Ranjen je u borbama za Jajce i sakriven s ostalim ranjenicima u jednoj štali. Ustaše su uhvatile nekoga tko im je odao gdje se ranjenici nalaze, pa su ih žive zapalili zajedno sa štalom.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0131011230', // Fijačko Franc Andrej of Brezovec (Ptuj), census part Slovenija: his nephew's form of 2026-11-23 17:32
    text: 'Obitelj je protjerana sa svog ognjišta u logore Jasenovac i Stara Gradiška, a zatim internirana u Srijem (Irig, Ruma, Futog). Sudjelovao je u proboju Srijemskog fronta, ranjen je u glavu, izgubio oko i od posljedica umro.',
    from: 'J. Sušić Jurić, nećak',
    date: '2026-11',
  },
  {
    soldierId: '0025000514', // Kreco Dimitrijin Krsto of Tuzla, Tuzlanski odred: his granddaughter's form of 2026-11-23 17:44
    text: 'Njegov grob nikada nije pronađen.',
    from: 'A. Savić, unuka',
    date: '2026-11',
  },
  {
    soldierId: '0035104016', // Iveković Albina Svetozar of Klanjec, 32. divizija: his grandson's form of 2026-11-23 17:47 (317176)
    text: 'Umro je 2003. u Varaždinu.',
    from: 'B. Iveković, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122961379', // Kovač Arsena Mirko of Donje Žešče, 4. armija: his grandson's missing-fighter form of 2026-11-23 15:58
    // (Porodična arhiva 9990000036); his face cut from the family photo is the portrait, the whole photo in the album
    photo: '0122961379-1.jpg',
    photoCaption: 'U kasnijim godinama',
    pieces: [{ kind: 'photo', file: '0122961379-2.jpg', caption: 'S porodicom' }],
    text: 'U partizane je stupio 1943, kao vrlo mlad. Učestvovao je u oslobađanju Dalmacije i Trsta. Posle rata upućen je u školu za milicionere, ali je izbačen zbog nediscipline. Iz Bosne se preselio u Vojvodinu, u selo Orlovat, sa ženom, njenim sestrama i prvim detetom.',
    from: 'D. Kovač, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0008002961', // (his family's record 0122961381 joined to this one, the user's word of 2026-11-23: both units) Vučković Frane Nikola of Brnaze, 4. splitska and 16. slavonska omladinska: his grandson's missing-fighter form of
    // 2026-11-23 16:28 with his wartime photo (Porodična arhiva 9990000038; no name for the card)
    photo: '0122961381-1.jpg',
    photoCaption: 'U partizanskoj uniformi',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0028019015', // Vučeraković Petrov Jovan of Krnjice (Bar), 7. crnogorska: a man of his village sent a painted portrait,
    // form of 2026-11-23 16:53; on the card at the user's word (2026-11-23: "yeah put the drawing on")
    photo: '0028019015-1.jpg',
    photoCaption: 'Crtež',
    from: 'M. Pekić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122961384', // Zadnik Jože of Pregarje, intendant of the 3. prekomorska brigada: his grandson's message the user passed on,
    // 2026-11-23 (Porodična arhiva 9990000044; a new record, the user's answer: not the Tomšičeva's Jože of 1904); his wartime photo
    photo: '0122961384-1.jpg',
    photoCaption: 'U uniformi prekomorskih brigada',
    text: 'Rođen je 1901. u Pregarju. Bio je intendant 3. prekomorske brigade. Preživio je rat, a umro je 1964.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0133029946', // Samardžić (Vlado) Ives, census part BiH: Ivanka "Ives" Samardžić, a post of the Facebook page „Bitka na
    // Sutjesci” the user sent (2026-11-23); the rows by override; her portrait cut from the post
    photo: '0133029946-1.jpg',
    photoFrom: '„Bitka na Sutjesci”',
    text: 'Ivanka Ives Samardžić rođena je u Mostaru 25. januara 1925. Završila je osmi razred gimnazije u Sarajevu. Članica SKOJ-a bila je od 1943. Ustaše su je uhapsile 24. marta 1945. i posle nekoliko dana obesile tokom masovnog pogubljenja na Marijin Dvoru u Sarajevu. Prema izvorima, na suđenju se ponašala dostojanstveno.',
    from: '„Bitka na Sutjesci”',
    origin: 'facebook',
    date: '2026-11',
  },
  {
    soldierId: '0109000032', // Antolović Josip "Joka Hrvat", narodni heroj, Mačvanski odred: his grandson's mail of 2026-11-24 01:01
    // (no name given; Porodična arhiva 9990000050 referenced; rows by 317182); his photo on Psunj, never online
    photo: '0109000032-1.jpg',
    photoCaption: 'Na obroncima Psunja, kao komandant 12. slavonske brigade',
    pieces: [{ kind: 'photo', file: '0109000032-2.jpg', caption: 'Na obroncima Psunja' }],
    text: 'Od 10. veljače 1943. do 1. veljače 1944. bio je zapovjednik 12. slavonske proleterske udarne brigade, a od siječnja 1944. zapovjednik 33. divizije X. zagrebačkog korpusa. Njemu osobno najviše je značila upravo 12. slavonska, jer je u nju dao najviše. Umro je 28. siječnja 1999. u Zagrebu.',
    from: 'iz porodične arhive', // no name in the mail: no name, no relation
    date: '2026-11',
  },
  {
    soldierId: '0132037115', // Perkov Filicije Ante of Primošten Burnji, census part Hrvatska: his nephew's son's mail of 2026-11-24
    // (the site's mail fallback, no permission lines: no name); a book's entry and his portrait; rows by override
    photo: '0132037115-1.jpg',
    pieces: [
      {
        kind: 'document',
        file: '0132037115-2.jpg',
        caption: 'Iz knjige',
        transcripts: ['PERKOV ANTE Filicija — rođen 1918. u Dragi — Burnji Primošten, zemljoradnik, Hrvat. U Skoj primljen 1942, član KP 1943. Odlaskom u NOV 1943. stupio u sastav 8. šibenske brigade 20. divizije. Te godine poginuo kao borac iste brigade u borbama kod Livna.'],
      },
    ],
    text: 'Prema obiteljskoj predaji, do kraja 1942. radio je u Njemačkoj, u tvornici Mercedesa. Kad je čuo za pokolj na području Primoštena, u kojem mu je strijeljan otac Filicijo, vratio se i s bratom Mladinom otišao u partizane. Obojica su poginula 1943.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0133021194', // Bandov (census: Bondov) Mato Srećko of Grgurići (Livno), census part BiH: a reader's mail of 2026-11-23
    // 21:46 with the entry of Brčić and Bogovac's book (no "Bondov" family in that region); surname, unit and death by override
    pieces: [
      {
        kind: 'document',
        file: '0133021194-1.jpg',
        caption: 'Rafael Brčić, Mile Bogovac, „Livanjski kraj u revolucionarnom radničkom pokretu i NOB”, Sarajevo 1979, spisak poginulih boraca',
        transcripts: ['BANDOV, Matin, SREĆKO, iz Grgurića, rođen 1923, zemljoradnik, Hrvat, u NOB stupio jula 1942, puškomitraljezac, poginuo u sastavu 10. hercegovačke brigade aprila 1943. kod Stoca.'],
      },
    ],
    text: 'Prezime mu je Bandov, a ne Bondov, kako piše u popisu žrtava rata iz 1964; Bondova u tom kraju nema. Tako ga navodi i knjiga „Livanjski kraj u revolucionarnom radničkom pokretu i NOB”.',
    from: 'S. Brešić',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0140001000', // Valtrović Đ Relja, 42. vazduhoplovna divizija: his son's mail of 2026-11-24 00:39 (the site's mail fallback,
    // no permission lines: no name); father, birth and occupation by 317183
    text: 'Bio je divan suprug i otac, i profesor kog su voljele generacije đaka.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961385', // Ujević Ante Zdravko of Krivodol, Biokovski odred: his grandson's mail of 2026-11-24 08:21 (the site's mail
    // fallback, no permission lines: no name; Porodična arhiva 9990000045); his photo with his brother Mate, his face the portrait
    photo: '0122961385-1.jpg',
    photoCaption: 'Sa bratom Matom',
    pieces: [{ kind: 'photo', file: '0122961385-2.jpg', caption: 'Sa bratom Matom Ujevićem, narodnim herojem' }],
    text: 'Godine 1943. s majkom Mareškom odlazi u Biokovo, zbog opasnosti od kazne po okružnici 3C, jer su ostali u obitelji, brat Mate i sestre Nediljka (kasnije udana Radivčić) i Antica (kasnije udana Kujundžić, supruga Nedjeljka Kujundžića, autora knjige „Imotska krajina u NOB”), već bili u partizanima; sve troje sudjelovali su u bitkama na Neretvi i Sutjesci. Pridružuje se kao kurir partizanskom odredu na području Kozice. Sudjeluje u borbama i teško je ranjen u borbi s Nijemcima na Korčuli 1944, kod Blata. Odatle je prebačen na Vis, a kasnije u savezničku bolnicu u Italiji. Završava srednju školu za djecu borce na Hvaru, a zatim u Zagrebu Pravni fakultet.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961386', // Arslanagić Hasana Mustafa of Arslanagića Most (Trebinje): his nephew's mail of 2026-11-24 (the site's mail
    // fallback, no permission lines: no name; Porodična arhiva 9990000046)
    text: 'Kao gimnazijalac u Trebinju bio je član SKOJ-a. Obitelj se preselila u Dubrovnik, gdje je radio ilegalno. Talijani su ga uhapsili i zatvorili na Mamuli, a zatim prebacili u Bari ili Brindisi. Nakon kapitulacije Italije talijanski komunisti su ga vratili, prema obiteljskom sjećanju u Istru, gdje je bio politički komesar. Nosilac je Partizanske spomenice 1941. Poslije rata bio je inspektor Jugoslavenskih željeznica i završio višu prometnu školu. Partijsku knjižicu oduzeli su mu 1945, a vratili 1948; sam ju je vratio 1983. Živio je i umro u Dubrovniku, devedesetih godina.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961387', // Kolundžija (Zdujić) Petka Dušanka of Prizren: her daughter's mail of 2026-11-24 (the site's mail fallback, no
    // permission lines: no name; Porodična arhiva 9990000047; born "8.11.2025" in the mail, read as 1925)
    text: 'Rođena je kao Dušanka Zdujić. Sa porodicom je radila ilegalno u okupiranom Prizrenu, a početkom 1943. otišla je u partizansku jedinicu u Drenici. Posle rata radila je u CK SKOJ-a, a zatim u socijalnoj i zdravstvenoj zaštiti.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0010900051', // Kolundžija Petra Mile of Krnjeuša (Bosanski Petrovac): the same daughter's mail of 2026-11-24 (no permission
    // lines: no name; Porodična arhiva 9990000048; born "12.07.2024" in the mail, read as 1924)
    text: 'U partizanima je bio od prvog dana ustanka, borac 3. krajiške brigade. Bio je vijećnik Prvog i Drugog zasjedanja ZAVNOBiH-a. Posle rata radio je u SKOJ-u, a kasnije u Beogradu.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961389', // Krišto Ante Ivo "Ivić" of Dobro (Livno): his missing-fighter form of 2026-11-23 22:14, sent as a screenshot
    // by mail (FormSubmit refused it); a comrade's son and neighbour, text and name allowed (Porodična arhiva 9990000049)
    text: 'U NOB-u je bio od 1941. i nosilac je Partizanske spomenice 1941.',
    from: 'S. Brešić, sin očevog druga i komšija',
    origin: 'visitor',
    date: '2026-11',
  },
  {
    soldierId: '0122961390', // Sučić Stjepana Ivan of Plaški: his daughter's missing-fighter form of 2026-11-24 09:02 by the site's mail
    // fallback (no permission lines: no name; Porodična arhiva 9990000051; "7. kordunaška divizija" as she writes it)
    text: 'U rat je otišao 1943, kao kurir 7. kordunaške divizije. Poslije rata sudjelovao je na omladinskim radnim akcijama Brčko–Banovići i Šamac–Sarajevo, a kasnije radio na željeznici, gdje je i umirovljen. Bio je korisnik boračke mirovine. Umro je 2018. i sahranjen u Plaškom.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0007005370', // Ujević Ante Mate, narodni heroj, 2. dalmatinska: his brother Zdravko's grandson's mail of 2026-11-24 08:21
    // (no name; Porodična arhiva 9990000054 referenced, the Neretva and the Sutjeska); the user's note on /pregled 67b0185984;
    // the family's photo of him with his brother is his portrait (cut to him), the whole photo in his album
    photo: '0007005370-1.jpg',
    photoCaption: 'Sa bratom Zdravkom',
    pieces: [{ kind: 'photo', file: '0007005370-2.jpg', caption: 'Sa bratom Zdravkom Ujevićem' }],
    text: 'Po obiteljskom sjećanju, sudjelovao je u bitkama na Neretvi i Sutjesci, kao i sestre Nediljka i Antica. Mlađi brat Zdravko bio je kurir Biokovskog odreda.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0007005371', // Ujević-Radovčić Ante Nediljka, 2. dalmatinska: her brother Zdravko's grandson's mail of 2026-11-24 08:21
    // (no name; Porodična arhiva 9990000055 referenced); the user's note on /pregled 67b0185984
    text: 'Po obiteljskom sjećanju, sudjelovala je u bitkama na Neretvi i Sutjesci, kao i brat Mate i sestra Antica.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961392', // Ujević Ante Antica of Krivodol, later Kujundžić: her brother Zdravko's grandson's mail of 2026-11-24 08:21
    // (no name; Porodična arhiva 9990000053); the user's note on /pregled 67b0185984
    text: 'Bila je u partizanima prije 1943. i sudjelovala u bitkama na Neretvi i Sutjesci, kao i brat Mate i sestra Nediljka. Kasnije se udala za Nedjeljka Kujundžića, autora knjige „Imotska krajina u NOB”.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961391', // Perkov Filicije Mladin of Primošten Burnji: his brother Ante's nephew's son's mail of 2026-11-24 (no name;
    // Porodična arhiva 9990000052); the user's note on /pregled 3fb351d5a4
    text: 'U partizane je otišao prije brata Ante, koji mu se pridružio kad se krajem 1942. vratio iz Njemačke, nakon što im je otac Filicijo strijeljan u pokolju na području Primoštena. Obojica su poginula 1943.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961393', // Race Franca Boris "Žarko" of Hrpelje: his great-nephew's missing-fighter form of 2026-11-24 10:05 with his photo
    // (text and name allowed; Porodična arhiva 9990000056, role activist: an illegal worker, no unit); the dates from the lexicon
    // Obrazi slovenskih pokrajin the sender gave
    photo: '0122961393-1.jpg',
    photoCaption: 'U kasnijim godinama',
    text: 'Vodio je ilegalnu štampariju i bio nosilac Partizanske spomenice 1941. Prema leksikonu „Obrazi slovenskih pokrajin”: od decembra 1941. bio je u tehnici (ilegalnoj štampariji) CK KP Slovenije, od avgusta 1942. do aprila 1943. vodio je tehniku Petrač; uhapšen je i u junu 1943. osuđen na 30 godina, a iz zatvora u Parmi pušten je u decembru 1943. Od januara 1944. bio je partizanski učitelj u Hrpeljama, zatim je vodio tehniku Slavnik u Brkinima. Posle rata bio je građevinski preduzetnik u Trstu i od 1964. do 1987. predsednik Slovenske kulturno-gospodarske zveze. Umro je u Trstu 26. aprila 1995.',
    from: 'A. Race, pranećak',
    date: '2026-11',
  },
  {
    soldierId: '0122961394', // Kruc Dragutin of Zagreb, Kalnička brigada: his grandson's missing-fighter form of 2026-11-24 10:39 (text yes,
    // name no; Porodična arhiva 9990000057)
    text: 'Kao skojevac u Zagrebu nosio je oružje i materijal na vezu na Medvednicu. U partizane je otišao sa 19 godina; bio je borac Kalničke brigade 10. zagrebačkog korpusa, a zatim u sanitetu. Preživio je rat.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation
    date: '2026-11',
  },
  {
    soldierId: '0108000481', // Lapčević Stevo of Bišćanovo (Glina), 3. banijska brigada: his grandson's plain mail of 2026-11-24 10:18
    // (the form wouldn't send; no permission lines: no name) with four photos (Porodična arhiva 9990000058; rows by 317188)
    photo: '0108000481-1.jpg',
    photoCaption: 'U partizanskoj uniformi',
    pieces: [
      // the whole print cut to his figure, cap to boots, without its torn edge (the user's note on /pregled, 2026-11-24: "better crop")
      { kind: 'photo', file: '0108000481-6.jpg', caption: 'U partizanskoj uniformi, cela figura' },
      { kind: 'photo', file: '0108000481-2.jpg', caption: 'Kao oficir, posle rata' },
      { kind: 'photo', file: '0108000481-3.jpg', caption: 'Sa odlikovanjima' },
      { kind: 'photo', file: '0108000481-4.jpg', caption: 'U oficirskoj uniformi' },
    ],
    text: 'Rođen je 1925. u Bišćanovu kod Gline. Posle rata završio je školu KOV i KNOJ u Kragujevcu i službovao po Srbiji; penzionisan je krajem pedesetih kao kapetan. Umro je 2008. u Sremskoj Mitrovici, gde je i sahranjen.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0057900008', // Petrenj Stevan Mara of Bosut, 3. vojvođanska (from the census, joined to her family's entry 9990000060): form of 2026-11-24 10:04 (text and name allowed;
    // "unuk" on all three Petrenj forms)
    text: 'Bila je u Trećoj vojvođanskoj brigadi. Grob joj je u Maloj Moštanici, gde ima i spomenik.',
    from: 'V. Petrenj, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0138007908', // Petrenj Stevan Adam of Bosut, census part Vojvodina: form of 2026-11-24 10:06; the death by override
    text: 'Pobegao je iz Jasenovca. Nije poginuo: umro je od tifusa u Birču.',
    from: 'V. Petrenj, rođak',
    date: '2026-11',
  },
  {
    soldierId: '0138007910', // Petrenj Stevan Stevan of Bosut, census part Vojvodina: form of 2026-11-24 10:07; the death by override
    text: 'Poginuo je na Sremskom frontu.',
    from: 'V. Petrenj, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0010101525', // Žujić-Torbica Milana Zora of Brekinja, 3. krajiška proleterska: her grandson's form of 2026-11-24 10:51
    // with her photo (text and name allowed; Porodična arhiva 9990000059 referenced)
    photo: '0010101525-1.jpg',
    photoCaption: 'U partizanskoj uniformi',
    text: 'Učestvovala je u bici na Neretvi i u borbama za oslobođenje Beograda. Krajem rata bila je politički komesar čete za vezu (Savo O. Trikić, „Treća krajiška proleterska brigada”, str. 352). O njoj je pisao i Yugopapir, u članku „Zora Žujić, 19-godišnja Kozarčanka”.',
    from: 'A. Torbica, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0041900178', // Lekić Muratov Mahmut of Tuzi (the Spomenica's, Podgorica): his relative's form of 2026-11-24 11:36 (text and
    // name allowed; Porodična arhiva 9990000061 joined, ONE_MAN); the photo the form announced never arrived
    text: 'Bio je pekarski radnik iz Tuzi. Bio je jedan od organizatora SKOJ-a u Skadru i istaknuti partizan u rejonu Skadra, Tirane, Drača i Tuzi; blisko je sarađivao s Blažom Jovanovićem tokom njegove misije u Albaniji. Poginuo je u proljeće 1944. na Crkvinama kod Kolašina, kao komandir izviđačkog voda Pete proleterske crnogorske brigade. Grob mu nije poznat.',
    from: 'M. A., rođak',
    date: '2026-11',
  },
  {
    soldierId: '0122961396', // Šuran Bortola Marčelo: his grandson's missing-fighter form of 2026-11-24 11:51 (sent twice; Porodična arhiva 9990000062)
    text: 'Poginuo je negde na Gomancima, blizu Ilirske Bistrice, 1944. ili 1945. godine.',
    from: 'A. Šuran, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122961397', // Miljenović Božo of Trupinjak (Krnjak): his granddaughter's missing-fighter form of 2026-11-24 12:07 (text yes,
    // name no; Porodična arhiva 9990000063); her brothers unnamed, as she wrote (the user, 2026-11-24)
    text: 'Bio je prvoborac, u odredu Trupinjska kosa. Iz rata je izašao kao kapetan, a kasnije postao major. Tri njegova brata poginula su u partizanima.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961398', // Brajdić Antun of Zagreb: his grandson's missing-fighter form of 2026-11-24 12:00 (text yes, name no; Porodična
    // arhiva 9990000064); his brothers Rafael (0122961399) and Tomo (0122961400) at the user's word
    text: 'Bio je ilegalac u Zagrebu, a zatim otišao u partizane, s trojicom ili četvoricom braće; poznata su imena dvojice, Rafaela i Tome. Jedan od braće ranjen je tako da je izgubio vid, pa su ga ostali sve vreme vodili sa sobom. Svi su preživeli rat.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961399', // Brajdić Rafael, Antun's brother (9990000065): the same form; the user: "rafael and tomo for antun brajdic too"
    text: 'Brat Antuna Brajdića. Iz Zagreba je s braćom otišao u partizane; svi su preživeli rat.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0122961400', // Brajdić Tomo, Antun's brother (9990000066): the same form
    text: 'Brat Antuna Brajdića. Iz Zagreba je s braćom otišao u partizane; svi su preživeli rat.',
    from: 'iz porodične arhive',
    date: '2026-11',
  },
  {
    soldierId: '0010000573', // Jeličić Mile Jovo of Vodenica, 3. krajiška: his grandson's form of 2026-11-24 12:55 (Porodična arhiva
    // 9990000067 referenced; the death by 317191: the family wins over the books' Sutjeska and Jasenovac)
    text: 'Ranjen je u bici za Drvar, kao borac Titovog bataljona. Avionom RAF-a evakuisan je u Italiju, u Bari, gde je podlegao ranama.',
    from: 'B. Jeličić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0053003096', // Zaknić Franka Marko "Kutlić" of Blato, 11. dalmatinska: his grandson's form of 2026-11-24 12:45 (317192)
    text: 'Bio je kamenoklesar. Umro je 11. studenog 2010; grob mu je u Blatu na Korčuli.',
    from: 'D. Žaknić, unuk',
    date: '2026-11',
  },
  {
    soldierId: '0122961402', // Ćirković Sava of Kozare (Vlasotince): his grandson's missing-fighter form of 2026-11-24 13:21 (text and name
    // allowed; Porodična arhiva 9990000070); forced into the chetniks, then a partisan to the war's end: a record (the rules)
    text: 'Rat ga je zatekao na odsluženju vojnog roka u Zagrebu. Krenuo je pešice kući, u selo Kozare kod Vlasotinca; na putu je uhapšen i neko vreme proveo u zatvoru u Višegradu. Na putu ka kući ponovo je uhvaćen i odveden u logor u Rumuniji, iz kojeg je pušten jer je Kozare tada bilo pod bugarskom kontrolom. Kod kuće su ga četnici prisilno mobilisali; po raspadu te jedinice priključio se partizanima i u njima ostao do kraja rata. Učestvovao je u oslobađanju Beograda. Umro je početkom devedesetih.',
    from: 'Z. Ćirković, unuk',
    date: '2026-11',
  },
]

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
