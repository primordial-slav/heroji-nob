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
    soldierId: '0122917644', // Kovačević Pajov Dušan of Osječenica (Nikšić), Borci drugih jedinica
    text: 'Rođen 1923. u Osječenici kod Nikšića, a poginuo pri proboju Sremskog fronta, početkom aprila 1945. godine.',
    from: 'iz porodične arhive', // the sender did not allow a name: no name, no relation (the user's rule, 2026-11-23)
    date: '2026-11',
  },
  {
    soldierId: '0122907839', // Sekulić Mane Miloš of Zbjeg (Slunj), Borci drugih jedinica
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
    soldierId: '0122959608', // Ćulibrk Svetko of Risovac (Porodična arhiva 9990000004); the granddaughter's form of 2026-11-20 15:51
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
    // photos (a portrait from the 1950 Australian immigration file, the standing photo cut from Jože Petek's photograph
    // of the escape, that whole photograph) were lost by the form's /api/prilog on Vercel and never arrived
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
    // (2026-11-22); the portrait is from after the war, so in his album
    pieces: [{ kind: 'photo', file: '0122961366-1.jpg', caption: 'Posle rata' }],
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
    soldierId: '0122961370', // Dvorski Mije Martin of Herešin, 21. slavonska, not in any book: his grandson's missing-fighter
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
]

export function contributionsFor(soldierId: string, otherIds: (string | undefined)[] = []): FamilyContribution[] {
  const ids = new Set([soldierId, ...otherIds.filter(Boolean)])
  return familyContributions.filter((c) => ids.has(c.soldierId))
}
