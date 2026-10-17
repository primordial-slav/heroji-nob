# znaci.org — books with soldier lists

Survey of the whole Biblioteka Znaci library for **lists of soldiers** we can extract: rosters, the fallen, survivors, a unit's leaders. Surveyed 2026-10-01; it replaces the survey of 2026-09-27, which read only the 211 book titles that name a unit and missed the viewer-format books and the books the index doesn't link.

## Method

- **Index**: the home page lists 894 books outside the periodicals: 577 with a landing page (`/0000N/K.htm` or `.php`) and 317 in the newer page viewer (`/00003/7xx.php?bk=N`, the whole book as `/00003/N.pdf`). Probing the gaps in the numbering found 116 more books the index doesn't link (Vojkova brigada, the Karlovac archive's kotar volumes, a second copy of Treća vojvođanska with its lists as web pages).
- **Contents**: every landing page's table of contents was read (three layouts: chapter links, a table of headings with book pages, the `?broj=` viewer with PDF pages) and each heading matched against list words in Latin, Cyrillic and Slovene (`spisak`, `popis`, `imenik`, `pregled`, `seznam`, `poginuli`, `pali`, `padli`, `preživjeli`, `starješine`, `kader` …).
- **Viewer books without contents on the page**: the contents pages (first 12 and last 15 pages) were read straight from the PDF with HTTP range requests, about 1 MB a book instead of the whole file. A few books make the reader scan the whole file; they are marked "not checked".
- **Chapter PDFs** of the lists were opened the same way for their page count and a text-layer check (all those listed below have one unless noted).
- Cache: `data-extraction/.cache/znaci_library/` (landing pages, PDF blocks). Pages below are the book's own page numbers unless marked "PDF p.".

## Totals

| | books |
|---|---:|
| Books read (indexed + unlisted) | 982 |
| With a list heading in the contents | 233 + 12 found by reading PDFs |
| Already used on the site | 30 |
| **New units with a soldier list** | **~75** (52 Serbo-Croatian, 23 Slovene) |
| More books for units already on the site | ~15 |
| Lists across units (battles, offensives) | 10 |
| Lists by place (municipality, kotar) | ~30 |

## 1. Top find: *Borci Sutjeske*

Viktor Kučan: **BORCI SUTJESKE** ([00001/129](https://znaci.org/00001/129.htm)). "Prozivka boraca sa Sutjeske": every fighter of the units in the battle, brigade by brigade, one PDF each, about 1,150 pages of two-column bios in one format: "SURNAME Father GIVEN, duty, rođen 1922, village, municipality, occupation, nationality, u NOB od 1942, član KPJ …, poginuo na Sutjesci … / krajem rata …". Roughly 20,000 soldiers.

| PDF | Unit | Pages | On the site? |
|---|---|---:|---|
| [129_5](https://znaci.org/00001/129_5.pdf) | Vrhovni štab NOV i POJ | 34 | — |
| [129_6](https://znaci.org/00001/129_6.pdf)–[129_9](https://znaci.org/00001/129_9.pdf) | Staffs of the 1. and 2. proleterska, 3. udarna, 7. banijska divisions | 14, 9, 10, 9 | — |
| [129_10](https://znaci.org/00001/129_10.pdf) | Prva proleterska | 110 | yes (1) |
| [129_11](https://znaci.org/00001/129_11.pdf) | Druga proleterska | 73 | yes (39) |
| [129_12](https://znaci.org/00001/129_12.pdf) | Treća proleterska (sandžačka) | 64 | yes (5) |
| [129_13](https://znaci.org/00001/129_13.pdf) | Četvrta proleterska (crnogorska) | 98 | **new** |
| [129_14](https://znaci.org/00001/129_14.pdf) | Peta proleterska (crnogorska) | 82 | **new** |
| [129_15](https://znaci.org/00001/129_15.pdf) | Šesta istočnobosanska | 43 | **new** |
| [129_16](https://znaci.org/00001/129_16.pdf) | Deseta hercegovačka | 77 | **new** |
| [129_17](https://znaci.org/00001/129_17.pdf) | Treća krajiška | 88 | yes (10) |
| [129_18](https://znaci.org/00001/129_18.pdf) | Sedma banijska | 41 | **new** |
| [129_19](https://znaci.org/00001/129_19.pdf) | Prva dalmatinska | 67 | yes (36) |
| [129_20](https://znaci.org/00001/129_20.pdf) | Osma banijska | 40 | **new** |
| [129_21](https://znaci.org/00001/129_21.pdf) | Druga dalmatinska | 84 | yes (7) |
| [129_22](https://znaci.org/00001/129_22.pdf) | Treća dalmatinska | 73 | **new** |
| [129_23](https://znaci.org/00001/129_23.pdf) | Šesnaesta banijska | 29 | **new** |
| [129_24](https://znaci.org/00001/129_24.pdf) | Sedma krajiška | 57 | **new** |
| [129_25](https://znaci.org/00001/129_25.pdf) | Prva majevička | 26 | **new** |
| [129_26](https://znaci.org/00001/129_26.pdf) | Centralna bolnica | 40 | — |

For units on the site its entries are a second book (merge with `find_source_duplicates.py`); for the others it is the first.

## 2. New units — brigades

| Unit | Book | Lists (page) | Link |
|---|---|---|---|
| 4. proleterska (crnogorska) | Blažo Janković | at formation 10. VI 1942; fallen 1942–45; officers by battalion and duty (pp. 109–126) and narodni heroji (pp. 129–131) ([148_13.pdf](https://znaci.org/00001/148_13.pdf), 131 pp. with the chapter; **all done**) | [00001/148](https://znaci.org/00001/148.htm) |
| 4. proleterska | Zbornik sjećanja, knj. 2 | at formation (p. 491, ~82 pp.) | [00001/287](https://znaci.org/00001/287.htm) |
| 6. crnogorska | Zbornik sjećanja | fallen (p. 871) | [00003/537](https://znaci.org/00003/537.htm) |
| 1. bokeljska | Dušan Živković | fallen and died (p. 315, 10 pp.) | [00003/384](https://znaci.org/00003/384.htm) |
| 4. sandžačka | | fallen (p. 460, 10 pp.), wounded (p. 470, 16 pp.), spomenica holders | [00001/271](https://znaci.org/00001/271.htm) |
| 7. krajiška | Jovan Kljajić | fallen (p. 350) | [00003/396](https://znaci.org/00003/396.htm) |
| 7. krajiška | Sjećanja i spisak boraca, knj. 2 | survivors and fallen ([186_2.pdf](https://znaci.org/00001/186_2.pdf), 229 pp.) | [00001/186](https://znaci.org/00001/186.htm) |
| 11. krajiška (kozaračka) | Milinović, Karasijević | women (p. 425), fallen (p. 439) | [00001/167](https://znaci.org/00001/167.htm) |
| 12. krajiška | Marjanović et al. | fallen ([168_7.pdf](https://znaci.org/00001/168_7.pdf), 39 pp.), survivors ([168_8.pdf](https://znaci.org/00001/168_8.pdf), 72 pp.) | [00001/168](https://znaci.org/00001/168.htm) |
| 3. banijska | Jovo Borojević, *Sinovi Šamarice* | members (p. 195, 10 pp.) | [00003/447](https://znaci.org/00003/447.htm) |
| 7. banijska | Ljuban Đurić | fallen | [00001/63](https://znaci.org/00001/63.htm) |
| 8. banijska | Ljuban Đurić | fallen and died (p. 247, 66 pp.) | [00003/383](https://znaci.org/00003/383.htm) |
| 12. proleterska slavonska | Jovan Kokot | women (survived or fell), fallen: as web pages ([46_225](https://znaci.org/00001/46_225.htm), [46_226](https://znaci.org/00001/46_226.htm)) | [00001/46](https://znaci.org/00001/46.htm) |
| 4. brigada Slavonije (2. brodska) | Obradović, Miletić | fallen and wounded (p. 164) | [00001/190](https://znaci.org/00001/190.htm) |
| Osječka udarna | Zdravko B. Cvetković | leaders (p. 203; **done**, `osjecka-rukovodioci.pdf`), fallen (p. 207, 12 pp.), survivors (p. 219) | [00003/450](https://znaci.org/00003/450.htm) |
| Karlovačka udarna | Lulik, Zatezalo | at formation 5. III 1944 (p. 379, 22 pp.), fallen (p. 401, 14 pp.) | [00003/546](https://znaci.org/00003/546.htm) |
| 1. zagorska | Vladimir Hlaić, *Grebeni Ivančice* | fallen (p. 191) | [00003/625](https://znaci.org/00003/625.htm) |
| 3. primorsko-goranska | Bogdan Mamula | staffs (p. 227; **done**, `3-primorsko-goranska-stabovi.pdf`), officers and medics (p. 234), fallen (p. 241, 19 pp.) | [00001/122](https://znaci.org/00001/122.htm) |
| 14. primorsko-goranska | Vladimir-Dušan Matetić | fallen (p. 227, 38 pp.) | [00003/544](https://znaci.org/00003/544.htm) |
| 6. dalmatinska | Danilo Damjanović | command (p. 257; **done**, `6-dalmatinska-kadar.pdf`), fallen (p. 259) | [00001/105](https://znaci.org/00001/105.htm) |
| 1. dalmatinska | Mirko Novović, Stevan Petković | officers at formation (108_3, pp. 55-58; **done**, `1-dalmatinska-formiranje.pdf`), changes in the command of the brigade and its battalions (108_20, pp. 435-443; **done**, `1-dalmatinska-komandni-sastav.pdf`), company commanders and commissars, narodni heroji, fallen (108_21; **done**, `1-dalmatinska-monografija.pdf`) | [00001/108](https://znaci.org/00001/108.htm) |
| Druga lička | Đorđe J. Orlović | the officers of the brigade staff and its battalions' staffs, in prose (160_20, pp. 349-360; **done**, `druga-licka-staresine.pdf`) | [00001/160](https://znaci.org/00001/160.htm) |
| 13. hercegovačka | Mensur Seferović | the officers, "Starješinski sastav" (270_7, pp. 305-315; **done**, `13-hercegovacka-starjesine.pdf`) | [00001/270](https://znaci.org/00001/270.htm) |
| 2. dalmatinska | Nikola Anić | the staffs and commands, "Pregled štabova i komandi" (33_21, pp. 473-486; **done**, `2-dalmatinska-stabovi.pdf`) | [00001/33](https://znaci.org/00001/33.htm) |
| 14. hercegovačka (omladinska) | Grupa autora | the command, Prilog 4 (268_5, pp. 234-242; **done**, `14-hercegovacka-komandni-sastav.pdf`) | [00001/268](https://znaci.org/00001/268.htm) |
| 11. dalmatinska | Rako, Družijanić | fallen (p. 479, 26 pp.), missing (p. 505), survivors (p. 507, 94 pp.), the staffs and commands (PDF pp. 599-612, book pp. 611-624; **done**, `11-dalmatinska-stabovi.pdf`) | [00003/547](https://znaci.org/00003/547.htm) |
| 12. dalmatinska (Prva otočka) | Nikola Anić | notes and fallen (already downloaded: `website/public/pdfs/12-dalmatinska.pdf`, 58 pp.); the staffs (PDF pp. 22-25, book pp. 339-342; **done**, `parse_12_dalmatinska_kadrovi.py`) | [00001/80](https://znaci.org/00001/80.htm) |
| 12. hercegovačka | Osman Đikić | fallen (p. 207, 15 pp.) | [00001/243](https://znaci.org/00001/243.htm) |
| 13. hercegovačka | Mensur Seferović | fallen (p. 316, 14 pp.) | [00001/270](https://znaci.org/00001/270.htm) |
| 14. hercegovačka (omladinska) | | everyone who served (p. 243, 32 pp.), fallen (p. 275) | [00001/268](https://znaci.org/00001/268.htm) |
| 14. srednjobosanska | Stevo Samardžija | fallen (p. 393, 30 pp.), survivors (p. 423, 36 pp.) | [00003/579](https://znaci.org/00003/579.htm) |
| 15. majevička | Sjećanja i članci | roster (p. 485), narodni heroji | [00002/408](https://znaci.org/00002/408.htm) |
| 18. hrvatska istočnobosanska | | officers (p. 573, 9 pp.; **done**, `18-hrvatska-starjesine.pdf`), roster (p. 582, 115 pp.; [251_4.pdf](https://znaci.org/00001/251_4.pdf), 142 pp.) | [00001/251](https://znaci.org/00001/251.htm) |
| 1. kosovsko-metohijska | Milutin Milković | rosters ([185_15.pdf](https://znaci.org/00001/185_15.pdf), 40 pp.) | [00001/185](https://znaci.org/00001/185.htm) |
| 3. makedonska | Kiril Mihailovski Grujica | decorations, narodni heroji, fallen (already downloaded: `3-makedonska.pdf`, Cyrillic) | [00001/71](https://znaci.org/00001/71.htm) |
| 5. srpska | Jovanović, Mirčetić | fallen and died (p. 450) | [00001/86](https://znaci.org/00001/86.htm) |
| 7. srpska (5. južnomoravska) | Zlatković, Bakić | roster May 1944 (p. 459, 11 pp.), fallen, died and missing | [00001/277](https://znaci.org/00001/277.htm) |
| 8. srpska | Petar Damjanov | *Nezaboravnik*, the fallen (p. 265, 34 pp.) | [00003/398](https://znaci.org/00003/398.htm) |
| 9. srpska | *U stroju i s narodom*, spomen-knjiga | imenik boraca with a short bio of each (p. 47, ~326 pp.) | [00001/121](https://znaci.org/00001/121.htm) |
| 10. srpska | Radovan Timotijević | fallen (p. 488) | [00003/381](https://znaci.org/00003/381.htm) |
| 12. srpska | Dragoljub Mirčetić | fallen and died (Prilog 3, PDF p. 357 of 421) | [bk=841](https://znaci.org/00003/7xx.php?bk=841) |
| 15. srpska | Vojislav Nikčević | roster (p. 155, 12 pp.), fallen (p. 167), wounded (p. 171) | [00003/477](https://znaci.org/00003/477.htm) |
| 17. srpska | Predrag Milenković | survivors (p. 317, 53 pp.), fallen (p. 370) | [00001/274](https://znaci.org/00001/274.htm) |
| 19. srpska | Predrag Pejčić | *Pali za slobodu*, *Preživeli rat* (p. 473), staffs (p. 613; **done**) | [00001/87](https://znaci.org/00001/87.htm) |
| 20. srpska | Dragoljub Mirčetić | fallen and died (Prilog 2, PDF p. 339 of 408) | [bk=840](https://znaci.org/00003/7xx.php?bk=840) |
| 21. srpska (2. šumadijska) | Isidor Đuković | *Preživeli su rat* (p. 413) | [00001/197](https://znaci.org/00001/197.htm) |
| 22. srpska kosmajska | Milorad Gončin | fallen (p. 295, 24 pp.), survivors (p. 319) | [00003/445](https://znaci.org/00003/445.htm) |
| 23. srpska | Dragoljub Mirčetić | fallen and died (p. 352, 37 pp.) | [00001/214](https://znaci.org/00001/214.htm) |
| 31. srpska | Isidor Đuković | (the appendix, 231_6.pdf, is missing on znaci.org: 404 on 2026-10-16) fallen, missing, died (p. 290, 64 pp.); fallen of incomplete identity (p. 354); survivors (p. 364) | [00001/231](https://znaci.org/00001/231.htm) |
| 3. vojvođanska | Radovan Panić | fallen (p. 479), fate unknown (p. 521), survivors (p. 544). The unlisted copy [00001/57](https://znaci.org/00001/57.htm) has all three as web pages (57_49–51.htm) | [00001/70](https://znaci.org/00001/70.htm) |
| 4. vojvođanska | Špiro Lagator | members 7. X 1943 (p. 281, 31 pp.), fallen and died (p. 312) | [00001/230](https://znaci.org/00001/230.htm) |
| 5. vojvođanska | Nikola Mraović | soldiers and officers (p. 429) | [00001/81](https://znaci.org/00001/81.htm) |
| 6. vojvođanska | Živan M. Ninković | staffs and company commands (p. 171; **done**, `6-vojvodjanska-stabovi.pdf`), fallen (p. 175, 25 pp.), thanked for the liberation (p. 200, 7 pp.) | [00001/252](https://znaci.org/00001/252.htm) |
| 8. vojvođanska | Nikola Božić, *Rovovi i mostobrani* | fallen and missing (p. 675, 48 pp.) | [00001/184](https://znaci.org/00001/184.htm) |
| 12. vojvođanska | Branislav Popov Miša | roster (p. 206, 33 pp.), fallen (p. 239, 19 pp.) | [00003/443](https://znaci.org/00003/443.htm) |
| 13. vojvođanska | Đorđe Momčilović, *Kako do brigade* | roster (p. 771) | [00003/431](https://znaci.org/00003/431.htm) |
| 1. konjička | Milorad Gončin | fallen (p. 317), wartime roster (p. 321) | [00001/278](https://znaci.org/00001/278.htm) |

## 3. New units — divisions, battalions, odredi

| Unit | Book | Lists (page) | Link |
|---|---|---|---|
| 8. kordunaška divizija | Zbornik HAK, knj. 9 | fallen by unit (p. 806, 109 pp.), command (p. 762; **done**, `8-kordunaska-divizija-kadar.pdf`), Primišlje's fallen in other units (p. 746, 27) | [00003/571](https://znaci.org/00003/571.htm) |
| 9. dalmatinska divizija | Obrad Egić | fallen of the division (p. 121, 5 pp.) and of the 3. dalmatinska (p. 126) | [00001/187](https://znaci.org/00001/187.htm) |
| 19. sjevernodalmatinska divizija | Dragutin Grgurević | fallen and died (p. 253, 48 pp.), leaders (p. 233; the command table, Politodjel and heroes pp. 240-252 **done**, `19-sjevernodalmatinska-kadar.pdf`) | [00003/575](https://znaci.org/00003/575.htm) |
| 22. divizija | Živojin Nikolić Brka | fallen (p. 445, 32 pp.) | [00001/235](https://znaci.org/00001/235.htm) |
| 34. divizija | Vladimir Hlaić | fallen (p. 401, 32 pp.; [641_1.pdf](https://znaci.org/00003/641_1.pdf)), command (PDF pp. 407-417, book pp. 389-399; **done**, `34-divizija-kadar.pdf`) | [00003/641](https://znaci.org/00003/641.htm) |
| 51. vojvođanska divizija | Sreta Savić | fallen, by brigade ([152_8.pdf](https://znaci.org/00001/152_8.pdf)) | [00001/152](https://znaci.org/00001/152.htm) |
| 42. vazduhoplovna divizija | Predrag Pejčić | fallen (p. 279), personnel by regiment | [00001/238](https://znaci.org/00001/238.htm) |
| 1. i 2. eskadrila NOVJ | Predrag Pejčić | personnel (p. 331), fallen (p. 311) | [00001/115](https://znaci.org/00001/115.htm) |
| Prvi proleterski bataljon Hrvatske | Mamula et al. | roster (p. 262, 17 pp.) | [00003/590](https://znaci.org/00003/590.htm) |
| Proleterski bataljon Bosanske krajine | Trikić, Repajić | roster with photos (p. 263) | [00003/490](https://znaci.org/00003/490.htm) |
| Mostarski bataljon | Enver Ćemalović | Konjički bataljon IX 1941–VI 1942 (p. 331), Mostarski bataljon VI 1942–VI 1943 (p. 364) | [00001/182](https://znaci.org/00001/182.htm) |
| Prvi tenkovski bataljon | Vujo Vidaković | members (p. 337) | [00003/543](https://znaci.org/00003/543.htm) |
| Treći diverzantski odred | Vukašin Karanović | fighters and officers (p. 587), fallen (p. 591) | [00003/541](https://znaci.org/00003/541.htm) |
| Mačvanski (Podrinski) odred | Dragoslav Parmaković | roster | [00001/48](https://znaci.org/00001/48.htm) |
| Posavski odred | Milosav Bojić | roster (p. 565) | [00001/279](https://znaci.org/00001/279.htm) |
| Čačanski odred | Pantelić et al. | the fallen, narodni heroji | [00001/51](https://znaci.org/00001/51.htm) |
| Toplički odred | Dragoljub Dinić | at formation (p. 302), fallen and died (p. 305, 28 pp.) | [00001/280](https://znaci.org/00001/280.htm) |
| Posavsko-trebavski odred | Esad Tihić | roster (p. 311, 91 pp.) | [00001/302](https://znaci.org/00001/302.htm) |
| Kalnički odred | Žarko Milićević | roster (p. 311, 90 pp.) | [00003/558](https://znaci.org/00003/558.htm) |
| Zagrebački odred | Zbornik | roster (p. 407), wounded, fallen, missing of the 1. bataljon | [00003/607](https://znaci.org/00003/607.htm) |
| Turopoljsko-posavski odred | Višnja Huzjak | fallen (PDF p. 19 of 32) | [bk=835](https://znaci.org/00003/7xx.php?bk=835) |
| Mosorski odred | Velić, Petrić, Vuletić | odred 1942–44 (PDF p. 357), komande mjesta and field workers (PDF p. 575), leaders (PDF p. 565, **done**, `mosorski-odred-kader.pdf`) | [bk=794](https://znaci.org/00003/7xx.php?bk=794) |
| Novosadski odred | Vanja Sanader (2026) | members 1941 and 1944 (pp. 85–86; Cyrillic) | [bk=2851](https://znaci.org/00003/7xx.php?bk=2851) |

## 4. New units — Slovene brigades and odredi

Most of the Knjižnica NOV in POS monographs end with a roster ("Seznam borcev") and the fallen ("Padli"). PDF pages are the viewer's.

| Unit | Book | Lists (PDF page of total) | Link |
|---|---|---|---|
| Cankarjeva | Lado Ambrožič-Novljan 1975 | commanders 810 (**done**, `cankarjeva-kader.pdf`), **Seznam cankarjevcev 815**, Padli 847 (of 910) | [767](https://znaci.org/00003/767.php) |
| Gubčeva | Ambrožič-Novljan 1972 | commanders (976, **done**, `gubceva-kader.pdf`), **Seznam gubčevcev**, Padli | [bk=782](https://znaci.org/00003/7xx.php?bk=782) |
| Tomšičeva I–IV | Franci Strle 1980–89 | I: udarna grupa, 1. proletarski bataljon (535–539 of 615; **done**, `tomsiceva-1.pdf`); II: **roster VII 1942–VII 1943** (840 of 941); III: names left out of II (646 of 715); IV: **rosters VII 1943–IV 1944 (573) and IV 1944–V 1945 (621)** (of 746) | [790](https://znaci.org/00003/7xx.php?bk=790), [787](https://znaci.org/00003/7xx.php?bk=787), [792](https://znaci.org/00003/7xx.php?bk=792), [788](https://znaci.org/00003/7xx.php?bk=788) |
| Šercerjeva | Milan Guček 1973 | Padli (518 of 550), volunteers | [bk=813](https://znaci.org/00003/7xx.php?bk=813) |
| XII. SNOUB (Dvanajsta) | Ambrožič-Novljan 1976 | Padli (609), **Seznam borcev (613 of 648)**, commanders (573, **done**, `dvanajsta-kader.pdf`) | [bk=814](https://znaci.org/00003/7xx.php?bk=814) |
| Kosovelova | Radosav Isaković 1973 | Padli (802), commanders (819 of 854) | [bk=773](https://znaci.org/00003/7xx.php?bk=773) |
| Gradnikova | Stanko Petelin 1983 | Padli (840), **Pregled borcev** (849 of 888) | [bk=825](https://znaci.org/00003/7xx.php?bk=825) |
| Bračičeva II | Mirko Fajdiga 1994 | Padli (304), **survivors (328 of 446)** | [bk=775](https://znaci.org/00003/7xx.php?bk=775) |
| Zidanšekova II | Mirko Fajdiga 1975 | commanders (730, **done**, `zidanskova-kader.pdf`), **Seznam borcev (732 of 793)** | [bk=776](https://znaci.org/00003/7xx.php?bk=776) |
| 1. in 2. prekomorska | Vilhar, Klun 1967 | Padli (346), leaders (358 of 399) | [769](https://znaci.org/00003/769.php) |
| 4. prekomorska | Pervanje, Hočevar 1969 | Padli in umrli (327), leaders (329 of 365) | [bk=783](https://znaci.org/00003/7xx.php?bk=783) |
| 5. prekomorska | Šmit, Bordon, Klun 1969 | Padli (279), leaders (297 of 342) | [bk=816](https://znaci.org/00003/7xx.php?bk=816) |
| Artileristi prekomorci | Karel Levičnik 1968 | Padli (218), leaders (222 of 253): **done**, a book across units, `parse_artileristi_prekomorci.py` | [bk=778](https://znaci.org/00003/7xx.php?bk=778) |
| Letalci prekomorci | Rafael Perhauc 1968 | the squadrons’ and the Algerian detachment’s leaders (319 of 354; no list of the fallen): **done**, a book across units, `parse_letalci_prekomorci.py`, their posts added to unit 139’s records | [bk=786](https://znaci.org/00003/7xx.php?bk=786) |
| 1. slovenska artilerijska | Borivoj Lah 1975 | **Seznam topničarjev**, officers (389, **done**), Padli (404 of 427) | [bk=826](https://znaci.org/00003/7xx.php?bk=826) |
| Artilerija 9. korpusa | Borivoj Lah 1985 | **Seznam borcev (316)**, Padli (324 of 353) | [bk=824](https://znaci.org/00003/7xx.php?bk=824) |
| Deveta (Kočevska) | Velimir Kraševec 1991, 2 vols | fallen and wounded (vol. 1, ch. 24), a roster mentioned in the preface; vol. 2: commanders (p. 401, **done**, `deveta-kader.pdf`) | [2849](https://znaci.org/00003/7xx.php?bk=2849), [2850](https://znaci.org/00003/7xx.php?bk=2850) |
| Istrski odred | Maks Zadnik 1975 | commanders (821, **done**, `istrski-odred-kader.pdf`), **Seznam borcev (827 of 901)**, padli odredovci | [bk=811](https://znaci.org/00003/7xx.php?bk=811) |
| Škofjeloški odred | Tone Lotrič 1971 | **Seznam borcev odreda (314 of 335)** | [bk=809](https://znaci.org/00003/7xx.php?bk=809) |
| Zapadnodolenjski odred | Velimir Kraševec 1985 | **Seznam odredovcev**, Padli | [bk=808](https://znaci.org/00003/7xx.php?bk=808) |
| Dolomitski odred | Rudolf Hribernik, *Dolomiti v NOB* 3 | heroes, spomenica holders and padli prvoborci (pp. 126-130 of 163; on the site as `dolomiti-v-nob-3.pdf`, a book across units: **done**, `parse_dolomiti_v_nob.py`) | [bk=1079](https://znaci.org/00003/7xx.php?bk=1079) |
| Mira Mihevc, *Na nevarnih poteh* | | members of the protection unit of the VPV (p. 291), Padli borci (303), heroes (305), spomenica holders (307 of 328): **done**, unit 150, `parse_zascitna_enota.py` | [757](https://znaci.org/00003/757.php) |

Commanders only (small): 31. divizija (Petelin, [823](https://znaci.org/00003/7xx.php?bk=823); the XXXI. divizija's list again, not read), 15. divizija ([770](https://znaci.org/00003/770.php); **done**, `15-divizija-stabi.pdf`), Petnajsta brigada ([815](https://znaci.org/00003/7xx.php?bk=815); **done**, `15-brigada-stabi.pdf`), Vojkova brigada (unlisted, [573](https://znaci.org/00003/573.htm), p. 517; the same, not read), Jeseniško-bohinjski odred ([771](https://znaci.org/00003/771.php); **done**, `jb-odred-stabi.pdf`). The XXXI. divizija's staffs are on the site from *Med Triglavom in Trstom* 2 (`xxxi-divizija-stabi.pdf`), books across units.

Not checked (the PDF makes the reader scan the whole file, or has no text layer): Kozjanski odred 1–2 (Teropšič, [2085](https://znaci.org/00003/7xx.php?bk=2085), [2086](https://znaci.org/00003/7xx.php?bk=2086); a leaflet says its roster holds 1,182 names), Kokrški odred I–III (Ivan Jan), Druga grupa odredov (Ferlež), *Med Triglavom in Trstom* (XXXI. divizija), *Cankarjev bataljon* (Ivan Jan), *Najboljši so padli* I–III, *Iskra in plamen* 1–3, Lovćenski odred ([2425](https://znaci.org/00003/7xx.php?bk=2425)), Nikšićki odred ([1024](https://znaci.org/00003/7xx.php?bk=1024)), *Teslić u NOB* ([1026](https://znaci.org/00003/7xx.php?bk=1026)).

## 5. More books for units already on the site

| Unit (code) | Book | Lists | Link |
|---|---|---|---|
| Prva proleterska (1) | *Borci Sutjeske* | see §1 | [129_10](https://znaci.org/00001/129_10.pdf) |
| Prva proleterska (1) | *Dalmatinci u Prvoj proleterskoj* | fighters from Dalmatia (p. 467, ~288 pp., bios) | [00001/207](https://znaci.org/00001/207.htm) |
| Prva proleterska (1) | *Prvi crnogorski bataljon* | by year joined, 1942–45, incomplete (pp. 713–788) | [00003/493](https://znaci.org/00003/493.htm) |
| Prva proleterska (1) | *Beogradski bataljon* | roster 1941–45 | [00003/499](https://znaci.org/00003/499.htm) |
| Prva proleterska (1) | Branislav Božović, *Rudarska četa* | roster (PDF p. 426, 7 pp.) | [00003/748](https://znaci.org/00003/748.php) |
| Prva proleterska (1) | Miloš Vuksanović | at formation, Rudo (p. 433) | [00003/382](https://znaci.org/00003/382.htm) |
| Prva proleterska (1) | *Prva proleterska brigada*, knj. 4, Spisak boraca | the roster A–Ž (97_1–3, on the site), the supplement (97_4, **done**), the battalion Garibaldi (97_5, **done**), the brigade on the day of formation, Cyrillic (97_6, pp. 10–33; the Rudo line-up again, not read), narodni heroji (97_6, images) | [00001/97](https://znaci.org/00001/97.htm) |
| Treća krajiška (10) | Zbornik sjećanja knj. 1–2; knj. 3 | roster XI 1942 ([31_263.htm](https://znaci.org/00001/31_263.htm); **done**, `parse_3_krajiska_sastav_1942.py`); **everyone who served in the war** (knj. 3, p. 579) | [00001/31](https://znaci.org/00001/31.htm), [00003/394](https://znaci.org/00003/394.htm) |
| Šesta krajiška (13) | *Ratna sjećanja* | wartime cadre 1942–43 (p. 739; **done**, `6-krajiska-kadar.pdf`), **survivors** (p. 747) | [00001/147](https://znaci.org/00001/147.htm) |
| Osma krajiška (14) | *Sjećanja boraca* | fallen and died (p. 689; on the site as `8-krajiska-sjecanja-poginuli.pdf`, a second book: **done**, `parse_8_krajiska_sjecanja.py`), corrections to the monograph (p. 743) | [00001/68](https://znaci.org/00001/68.htm) |
| Prva vojvođanska (9) | *Mladost slobodi darovana* | roster ([132_7.pdf](https://znaci.org/00001/132_7.pdf), 33 pp.) | [00001/132](https://znaci.org/00001/132.htm) |
| 7. crnogorska omladinska (28) | Zbornik sjećanja | fallen (p. 709, 26 pp.; a second book: **done**, `parse_7_crnogorska_zbornik.py`) | [00003/471](https://znaci.org/00003/471.htm) |
| 32. divizija (35) | *32. divizija NOVJ* | **Borci 32. divizije** (p. 431, ~220 pp.), incomplete (p. 653), the command (PDF pp. 373-382, book pp. 286-295; **done**, `32-divizija-kadar.pdf`) | [00003/542](https://znaci.org/00003/542.htm) |
| Tuzlanski odred (25) | companion volume | roster (p. 325, 114 pp.; the same list as the site’s, not added) | [00003/469](https://znaci.org/00003/469.htm) |
| 17. slavonska (16) | *28. slavonska divizija* | fallen at Ludbreg 6. VII 1944 (p. 287), and 3. X 1943 with the Braća Radić at Šemovec (pp. 84-85) (on the site as `ludbreg-poginuli.pdf`, a book across units: **done**, `parse_ludbreg_poginuli.py`) | [00001/189](https://znaci.org/00001/189.htm) |
| Druga proleterska, Treća sandžačka, Treća krajiška, Prva i Druga dalmatinska | *Borci Sutjeske* | see §1 | |

## 6. Lists across units

| Book | Lists | Link |
|---|---|---|
| Mišo Leković, *Ofanziva proleterskih brigada u leto 1942.* | fallen and missing 24. VI–30. IX 1942, by brigade and battalion ([183_15.pdf](https://znaci.org/00001/183_15.pdf), 14 pp.; on the site as `ofanziva-1942-poginuli.pdf`, a book across units: **done**, `parse_ofanziva_1942.py`) | [00001/183](https://znaci.org/00001/183.htm) |
| Dragoljub Tmušić, *Sremski front* | fallen, by unit (PDF pp. 55-160; **done**: `sremski-front-poginuli.pdf`, a book across units, 11,972 names; the Red Army's lists after them not read) | [00003/724](https://znaci.org/00003/724.htm) |
| Milorad Gončin, *U rovovima Srema* | fallen ([211_1.pdf](https://znaci.org/00001/211_1.pdf), 39 pp.; **done**: `u-rovovima-srema-poginuli.pdf`, a book across units) | [00001/211](https://znaci.org/00001/211.htm) |
| Nikola Božić, *Batinska bitka* | 51. divizija fallen (p. 469, 22 pp.) and missing (p. 491, 11 pp.); Soviet fallen (p. 502, 59 pp.) | [00002/427](https://znaci.org/00002/427.htm) |
| *Oslobođenje Kruševca 1944.* | fallen ([292_32.pdf](https://znaci.org/00001/292_32.pdf), 11 pp.; **done**: `krusevac-1944-poginuli.pdf`, a book across units) | [00001/292](https://znaci.org/00001/292.htm) |
| Milan Brunović, Tomo Sović, *Bitka kod Oborova* | the fallen (p. 158, 3 pp.; **done**: `bitka-kod-oborova-poginuli.pdf`, a book across units) | [00003/660](https://znaci.org/00003/660.htm) |
| *Istočna Bosna u NOR-u* 2 | fallen of the 6. istočnobosanska (PDF p. 478, 7 pp.) | [00003/751](https://znaci.org/00003/751.php) |
| *Žene Hrvatske u NOB* | women of the VI. korpus who fell (p. 301, 12 pp.), women of the 1. bataljon of the Osječka (p. 282) | [00003/585](https://znaci.org/00003/585.htm) |
| Kažimir Pribilović, *Četvrti pomorski obalni sektor* | fallen and died (p. 473, 6 pp.), the staff (Prilog X, 652_1 p. 70, book p. 485; **done**, `4-pomorski-sektor-stab.pdf`) | [00003/652](https://znaci.org/00003/652.htm) |
| Jaša Romano, *Jevreji Jugoslavije 1941–1945* | Jewish participants in the NOR ([191_4.pdf](https://znaci.org/00001/191_4.pdf), 205 pp.), spomenica holders, narodni heroji | [00001/191](https://znaci.org/00001/191.htm) |
| *Sanitetska služba u NOR-u*, knj. IV | doctors who lost their lives in the war, a bio each ([199_15.htm](https://znaci.org/00001/199_15.htm), a web page; on the site as a book across units, those in the army only: **done**, `parse_sanitetska_lekari.py`) | [00001/199](https://znaci.org/00001/199.htm) |
| *Vojnotehnička radionica Vrhovnog štaba NOV i POJ u Grmeču* | the workshop’s workers, guards and the Drvar foundry’s workers (PDF pp. 359-362): **done**, a second book of unit 112, `parse_vtr_grmec.py` | [00003/766](https://znaci.org/00003/766.php) |
| Ikovic, Linasi, *Koroško partizansko zdravstvo* | the Carinthian wounded and sick, the partisan hospitals’ patients and staff, a bio each (PDF pp. 282-355): **done**, a book across units, `parse_korosko_zdravstvo.py` | [bk=756](https://znaci.org/00003/7xx.php?bk=756) |
| Stanko Petelin-Vojko, *Med Triglavom in Trstom* (2) | the staffs of the XXXI. divizija and the Gradnikova, Prešernova and Vojkova (PDF pp. 268-273): **done**, a book across units, `parse_xxxi_divizija_stabi.py`; vol. 1 (1082) has no lists | [bk=1083](https://znaci.org/00003/7xx.php?bk=1083) |
| Checked, no fighter lists | Moškrič, *Iskra in plamen* 1 (1094, pre-war history) and 2 (1095: only Mala Zelena jama's 41 dead, fallen fighters and civilians not told apart); Semič-Daki, *Najboljši so padli* I (1098, memoirs) | |

## 7. Lists by place (not by unit)

The fallen of a municipality or kotar, often with their unit. The site has no place for these yet; they could link to unit records, or become a list of their own.

The Karlovac archive's kotar volumes each print four lists, village by village under each općina: **pali borci** (fighters who fell, with unit, date and place), **žrtve fašističkog terora i rata** (civilians and others killed), **umrli od tifusa**, and **nosioci Partizanske spomenice 1941** (survivors too: the only list here of people who lived), plus a name index of the articles. Located so far (PDF pages of the whole-book PDF; downloaded to `mile-bakic/` and `mile-bakic/izvori/`, not in git):

| Volume | Pali borci | Žrtve | Tifus | Spomenica | Name index |
|---|---|---|---|---|---|
| knj. 20 Gospić i Perušić ([642](https://znaci.org/00003/642.htm); lists also as chapter [642_2.pdf](https://znaci.org/00003/642_2.pdf), pp. 1, 61, 203, 209; **done**: fallen and spomenica on the site as `hak-20-gospic-perusic.pdf`, a book across units) | 642_2 p. 1 | p. 1043 | 642_2 p. 203 | 642_2 p. 209 | p. 1211 (book) |
| knj. 10 Korenica i Udbina ([489](https://znaci.org/00003/489.htm); **done**: fallen on the site as `hak-10-korenica-udbina.pdf`, whole-book PDF pp. 986-1035) | p. 963 | p. 969 | p. 982 | | p. 1150 |
| knj. 14 Donji Lapac ([458](https://znaci.org/00003/458.htm); **done**: fallen as `hak-14-donji-lapac.pdf`) | p. 1039 | p. 1091 | p. 1136 | | p. 1194 |
| knj. 13 Gračac ([638](https://znaci.org/00003/638.htm); **done**: fallen as `hak-13-gracac.pdf`) | p. 914 | p. 888 | p. 1012 | | p. 1030 |
| knj. 7 Plaščanska dolina ([487](https://znaci.org/00003/487.htm); **done**: fallen as `hak-7-plascanska-dolina.pdf`) | p. 720 | p. 733 | p. 758 | | |

Entry format (knj. 20): "79. ŠAŠIĆ Milana DMITAR, 1905, seljak, Srbin. Strijeljale ga ustaše u Širokoj Kuli juna 1941." — surname, father, given name, year, occupation, nationality, fate.

- **Zbornik Historijskog arhiva u Karlovcu** (most unlisted): Donji Lapac ([458](https://znaci.org/00003/458.htm), p. 1041, 54 pp.), Plaščanska dolina ([487](https://znaci.org/00003/487.htm), p. 689, 13 pp.), Korenica and Udbina ([489](https://znaci.org/00003/489.htm), p. 990, 50 pp.), Slunj and Veljun ([497](https://znaci.org/00003/497.htm), p. 919, 59 pp.), Gračac ([638](https://znaci.org/00003/638.htm), p. 917, 48 pp.), Gospić and Perušić ([642](https://znaci.org/00003/642.htm)), Vojnić ([644](https://znaci.org/00003/644.htm)), Duga Resa ([616](https://znaci.org/00003/616.htm)), Drežnica ([678](https://znaci.org/00003/678.htm)), Gornje Dubrave ([681](https://znaci.org/00003/681.htm)); Mile Mrkalj, *Sjeničak* ([640](https://znaci.org/00003/640.htm), p. 330)
- **Bosnia**: *Spomen-knjiga poginulih tuzlanskih boraca* ([144](https://znaci.org/00001/144.htm), p. 13, ~288 pp.), *Jajačko područje* I–II (fallen 1941, 1942: [722_1](https://znaci.org/00003/722_1.pdf), [721_1](https://znaci.org/00003/721_1.pdf)), *Srez Sanski Most u NOB* III ([bk=796](https://znaci.org/00003/7xx.php?bk=796)), Derventa ([bk=827](https://znaci.org/00003/7xx.php?bk=827)), Cazinska krajina ([587](https://znaci.org/00003/587.htm), p. 430), Dragoje Lukić, *Rat i djeca Kozare* (children who fell as fighters, [106_8.htm](https://znaci.org/00001/106_8.htm))
- **Serbia, Montenegro**: *Čačanski kraj u NOB — pali borci i žrtve* ([698](https://znaci.org/00003/698.htm)), *Požega u NOR* ([696_1](https://znaci.org/00003/696_1.pdf), 131 pp.; also rosters of the Požega companies 1941, p. 611), *Prilog u krvi (Pljevlja)* ([109_4](https://znaci.org/00001/109_4.pdf), 79 pp.)
- **Croatia, Dalmatia**: *Hrvatsko zagorje u revoluciji* (1981: [647_1](https://znaci.org/00003/647_1.pdf), 109 pp.; 1959: [648_1](https://znaci.org/00003/648_1.pdf), 89 pp.), Imotska krajina ([bk=803](https://znaci.org/00003/7xx.php?bk=803)), Vinodolska Selca ([bk=793](https://znaci.org/00003/7xx.php?bk=793)), Sušak i Rijeka ([bk=799](https://znaci.org/00003/7xx.php?bk=799)), Vis (fighters from the island in NOVJ units, [bk=804](https://znaci.org/00003/7xx.php?bk=804); **done**: the memorial plaques' fallen and died of wounds, pregled g, `vis-zrtve-nob.pdf`; its lists of the KPJ members and of the Komiža volunteers of August 1941 are no fighter lists)
- **Slovenia, Italy**: *Križani v boju za svobodo* ([720](https://znaci.org/00003/720.htm)), *Zbornik Ljubljana Moste-Polje* (spomenica holders, [bk=1103](https://znaci.org/00003/7xx.php?bk=1103))

## 8. References, not rosters

- *Narodni heroji Jugoslavije* ([00001/10](https://znaci.org/00001/10.htm); Petar Kačavenda's 1982–83 edition, [bk=977](https://znaci.org/00003/7xx.php?bk=977), [978](https://znaci.org/00003/7xx.php?bk=978)): every narodni heroj with a bio, for checking the medals.
- Holders of the Partizanska spomenica 1941, in several regional books (Moslavački odred, Virovitica, Gospić, Sušak). Virovitica ([653](https://znaci.org/00003/653.pdf), part IV, 14 bios), Gospić (in the Karlovac volume knj. 20) and Sušak are on the site; the Moslavački odred's list gives names only.

## 9. Skipped: not soldier lists

Camp inmates (the Jasenovac document volumes), civilians killed (Čačak, Bojnik, Dudik, Cazin), war criminals (Državna komisija), round-table participants, ZAVNOBiH/ZAVNOH members, people who gave goods to the partisans.

## Already used on the site

znaci.org books behind units 1–39: 00001/32, 33, 55, 64, 66, 69, 72, 73, 89, 94, 97, 101, 102, 110, 123, 131, 133, 137, 146, 149, 160, 163, 164, 188, 196, 205, 206, 215, 224, 250, 254, 262, 267, 275; 00002/403, 407; 00003/375, 567, 613, 711, 712. Ljubljanska is Borivoj Lah's *Ljubljanska brigada* ([768](https://znaci.org/00003/768.php), roster at PDF p. 394).
