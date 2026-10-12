"""
Parser: Požarevački NOP odred (brigade code 119).

Source: "Požarevački narodnooslobodilački partizanski odred" (Požarevac, 1991; 346 scan pages), in the Digital library
        of Poreklo (biblioteka.poreklo.rs, collection "Drugi svetski rat"; for members only). The library's OCR text of
        the list pages is kept in data-extraction/poreklo/pozarevacki-odred.json (poreklo_text.py). The appendix
        "Popis boraca u jedinicama Požarevačkog narodnooslobodilačkog partizanskog odreda od 1941-1944 godine"
        (scan pages 250-319, book pp. 238-307; compiled by Miodrag Stojanović Kole, October 1991): 1,340 fighters
        who fought in the odred's units from 1941 until October 1944, when it joined the NOVJ; not the members of
        the strike groups, the party, the councils, the front or the youth. Cyrillic, by letter, one entry a paragraph
        with its first line indented:
            АВРАМОВИЋ ЗДРАВКО, земљорадник, из Дољашнице, рођен 1921 г. у Дољашници. У одреду од августа 1941. г.
            до 17. фебруара 1942. г.
        A capitalised word after the name is a nickname ("АДАМОВИЋ РАДИВОЈЕ, Ћота, земљорадник"). It ends with
        "Borci ... kojima nisu utvrđena imena i ostali podaci": men known by a nickname or a first name only.

The OCR reads the bold capitals of the names badly: about one surname in eleven comes out in Latin letters
("BACI/fh МИЛАН" = ВАСИЋ МИЛАН), Ћ and Ђ as 'ћ, 'Б, 'в or junk ("АВРАМОВИ'ћ", "ћОР'БЕВИ'ћ" = ЂОРЂЕВИЋ), Љ and Њ in
lowercase, and words split after a letter ("Г РУБИЋ", "СТОЈ АН"). decode() undoes only what is certain; a name
the corpus still doesn't know, in surname or given name, was read from the page scan (SCAN, by scan page and the
entry's place among the page's entries). There is no scan on the site: records carry `source_url` (the page in the
library's viewer) and `source_page` (the book's page).
"""
import json
import re
from collections import Counter
from pathlib import Path

from _parser_scaffold import _record, cyrillic_to_latin, run_parser
from poreklo_text import load, page_lines, printed_page, viewer_url

BOOK = load('pozarevacki-odred.json')
PAGES = range(250, 320)
MARK = 'ꙮ '                                          # starts an entry (a letter: the scaffold strips leading marks)
UC = 'А-ЯЂЈЉЊЋЏ'

# Names read from the page scans: (scan page, the OCR's text of the name) -> name, or (name, the start of the
# line's rest as read, as it is printed) where the rest needs setting right too, or None for a line that is not
# an entry ("ине.", the end of the line before)
SCAN = {
    (255, 'БУЂЕЛАН ДРАГОЊУБ'): 'БУЂЕЛАН ДРАГОЉУБ',
    (267, 'ЖУЈРША РАДИВОЈ Е'): 'ЖУЈИЦА РАДИВОЈЕ',
    (250, 'АДАМОВИБ Др Милосав'): 'АДАМОВИЋ Др МИЛОСАВ',
    (250, "АЛБУНОВИ'ћ ЖИВОЈИН"): 'АЛБУНОВИЋ ЖИВОЈИН',
    (250, 'АНТЈЕЛКОВИБ БОРА'): 'АНЂЕЛКОВИЋ БОРА',
    (250, 'АНТЈЕЛКОВИЂ ВЕЛЕ'): 'АНЂЕЛКОВИЋ ВЕЛЕ',
    (250, "AHTI/I'h МИОДРАГ"): 'АНТИЋ МИОДРАГ',
    (251, "АРСЕНИЈЕВИ'ћ НШСОЛА"): 'АРСЕНИЈЕВИЋ НИКОЛА',
    (251, 'АРСИТ: ДРАГИША'): 'АРСИЋ ДРАГИША',
    (251, "АТАНСКОВИ'ћ ПАВЛЕ"): 'АТАНСКОВИЋ ПАВЛЕ',
    (252, "БОГИЧИ'ћ ДРАГУТИН"): 'БОГИЧИЋ ДРАГУТИН',
    (252, 'БАЈАГИТ: МИЛОШ'): 'БАЈАГИЋ МИЛОШ',
    (252, 'БАљУКОВ ИВАН'): 'БАЉУКОВ ИВАН',
    (252, 'БАЈ–БЛОВ'): 'БАЊЛОВ',
    (252, 'BAKI/fh СТЕВАН'): 'БАКИЋ СТЕВАН',
    (252, 'БИЛАВ ДРАГ АН'): 'БИЛАВ ДРАГАН',
    (252, "БИРОВЕСКОВИ'В ЈОВИЦА"): 'БИРОВЕСКОВИЋ ЈОВИЦА',
    (253, 'БИЦАНОВИЂ МИЛАН'): 'БИЦАНОВИЋ МИЛАН',
    (253, 'БЛАГОЈЕВИТ: ДУШАН'): 'БЛАГОЈЕВИЋ ДУШАН',
    (253, 'БОВАН "F)OPTJE'): 'БОВАН ЂОРЂЕ',
    (253, 'БОГАДНОВИЂ ЖИВКО'): 'БОГАДНОВИЋ ЖИВКО',
    (253, "БОГ ДАНОВИ'ћ МИЛУТИН"): 'БОГДАНОВИЋ МИЛУТИН',
    (253, 'БОГДАНОВИТ: МИОДРАГ'): 'БОГДАНОВИЋ МИОДРАГ',
    (254, "БОГОЈЕВИ'ћ БОРИСЛАВА"): 'БОГОЈЕВИЋ БОРИСЛАВА',
    (254, "БРЕЈИ'ћ МИЛОРАД"): 'БРЕЈИЋ МИЛОРАД',
    (255, 'БУБУЈЕСКО ДУШАН'): 'БУБУЈЕСКО ДУШАН',
    (255, "БУЗЕЈИ'ћ ВУЈША"): 'БУЗЕЈИЋ ВУЈИЦА',
    (255, 'БУљУБАША ВЛАДА'): 'БУЉУБАША ВЛАДА',
    (255, 'БУљУБАША "БОРБЕ'): 'БУЉУБАША ЂОРЂЕ',
    (255, 'БУљУБАША ПАВЛЕ'): 'БУЉУБАША ПАВЛЕ',
    (255, 'БУНУШЕВАЦ ТОМА'): 'БУНУШЕВАЦ ТОМА',
    (255, 'BACITE ДРАГОЊУБ'): 'ВАСИЋ ДРАГОЉУБ',
    (255, 'BACI/fh МИЛАН'): 'ВАСИЋ МИЛАН',
    (256, 'BACI/{T\\ МИЛОЈКА'): 'ВАСИЋ МИЛОЈКА',
    (256, 'BACI/[Tx МИЛУТИН'): 'ВАСИЋ МИЛУТИН',
    (256, 'BACI/TF: МИЛУТИН'): 'ВАСИЋ МИЛУТИН',
    (256, 'BACH?) МИОДРАГ'): 'ВАСИЋ МИОДРАГ',
    (256, 'ВАСИТз MI/IXAJHO'): 'ВАСИЋ МИХАЈЛО',
    (256, 'ВЕЈБКОВРГБ ВИТОМИР'): 'ВЕЉКОВИЋ ВИТОМИР',
    (257, "ВЕРНИКИ'ћ ДРАГИША"): 'ВЕРНИКИЋ ДРАГИША',
    (257, 'ВИТЕЖЕВАЦ ЖИВОТА'): 'ВИТЕЖЕВАЦ ЖИВОТА',
    (257, "ВЛАДИ'ћ ТРАИЛО"): 'ВЛАДИЋ ТРАИЛО',
    (257, 'ВЛКУ ПЕТАР'): 'ВЛКУ ПЕТАР',
    (257, 'ВРЕБАЛОВ Др БОШКО'): 'ВРЕБАЛОВ Др БОШКО',
    (257, 'ВРЕБАЛОВ ГУЦУЊА'): ('ВРЕБАЛОВ-ГУЦУЊА ВЕРА', 'ВЕРА, љубица, ', 'Љубица, '),
    (258, "ВУЈУ'ћ БОРИСЛАВ"): 'ВУЈУЋ БОРИСЛАВ',
    (258, 'ВУЛЕТИТ: РАДИСАВ'): 'ВУЛЕТИЋ РАДИСАВ',
    (258, 'ВУРДЕЈБА МЛАДЕН'): 'ВУРДЕЉА МЛАДЕН',
    (259, 'ВУЧКОВУГћ ЖИВОЈИН'): 'ВУЧКОВИЋ ЖИВОЈИН',
    (259, 'FAN/FF: ВОЈИСЛАВ'): 'ГАЈИЋ ВОЈИСЛАВ',
    (260, 'ГОСТОВИ\'ћ "ћОР\'ћЕ'): 'ГОСТОВИЋ ЂОРЂЕ',
    (260, "ГОЧИ'ћ ЈОВАН"): 'ГОЧИЋ ЈОВАН',
    (260, "ГОЧИ'ћ СИМА"): 'ГОЧИЋ СИМА',
    (260, 'ГРЕЧКА НРПСОЛАЈ'): 'ГРЕЧКА НИКОЛАЈ',
    (260, 'ДАБРПН АНА'): 'ДАБИЋ АНА',
    (261, 'ДЕПИЈ А ИЛИ] А'): 'ДЕЛИЈА ИЛИЈА',
    (261, "ДИЧИ'ћ РАДОМИР"): 'ДИЧИЋ РАДОМИР',
    (262, 'nom/na СТОЈ АН'): 'ДОНИЋ СТОЈАН',
    (262, 'ДРАГУЛОВИТ: љУБИША'): 'ДРАГУЛОВИЋ ЉУБИША',
    (262, 'ДРАШКОЦИ ЛАЗАР'): 'ДРАШКОЦИ ЛАЗАР',
    (262, 'ДРАШКОЦИ РАТКО'): 'ДРАШКОЦИ РАТКО',
    (262, "ДУГОШЕВИ'ћ ВЕЊКО"): 'ДУГОШЕВИЋ ВЕЉКО',
    (262, "ДУГОШЕВИ'ћ НАТАЛИЈА"): 'ДУГОШЕВИЋ НАТАЛИЈА',
    (262, "ДРЕШЕВИ'ћ МАРКО"): 'ДРЕШЕВИЋ МАРКО',
    (263, 'BI/[HAG НИКОЛА'): 'ЂИЛАС НИКОЛА',
    (263, "ћОКИ'ћ Ј ЕЛЕНКО"): 'ЂОКИЋ ЈЕЛЕНКО',
    (263, "ћОРТЈЕВИ'ћ БОЖИДАР"): 'ЂОРЂЕВИЋ БОЖИДАР',
    (263, "БОРЂЕВИ'ћ БОГОЈ Е"): 'ЂОРЂЕВИЋ БОГОЈЕ',
    (263, "БОРТЈЕВИ'ћ ДРАГИ"): 'ЂОРЂЕВИЋ ДРАГИ',
    (263, "ЂОРТЈЕВИ'ћ МИЛОВАН"): 'ЂОРЂЕВИЋ МИЛОВАН',
    (264, 'БУРЂЕВ МИЛИВОЈЕ'): 'ЂУРЂЕВ МИЛИВОЈЕ',
    (264, "БУРИЧИ'ћ ТРИФУН"): 'ЂУРИЧИЋ ТРИФУН',
    (264, 'БУРИЂ АЛЕКСАНДАР'): 'ЂУРИЋ АЛЕКСАНДАР',
    (264, 'ЂУРИТгЈОВАН'): 'ЂУРИЋ ЈОВАН',
    (264, "БУРИ'ћ љУБИСАВ"): 'ЂУРИЋ ЉУБИСАВ',
    (264, "ЂУРИ'ћ 'BOP'BE"): 'ЂУРИЋ ЂОРЂЕ',
    (264, "ЕЛГЕРАШЕВИ'ћ ЂУРО"): 'ЕЛГЕРАШЕВИЋ ЂУРО',
    (265, 'ЖИВАНОВИТ: ДУШАН'): 'ЖИВАНОВИЋ ДУШАН',
    (265, 'ЖИВАНОВИЂ ШЛОРАД'): 'ЖИВАНОВИЋ МИЛОРАД',
    (265, 'ЖИВИТ: БРАНКО'): 'ЖИВИЋ БРАНКО',
    (266, "ЖИВКОВИ'ћ ШИСАВ"): 'ЖИВКОВИЋ МИЛИСАВ',
    (266, "КИВОЈИНОВИ'В СТОЈ АН"): 'ЖИВОЈИНОВИЋ СТОЈАН',
    (266, "КИВОТИ'ћ ЖИВОЈИН"): 'ЖИВОТИЋ ЖИВОЈИН',
    (267, "ЖУРЖИ'ћ ЧЕДОМИР"): 'ЖУРЖИЋ ЧЕДОМИР',
    (267, "ЗДРАВКОВИ'ћ KOCTAHTHHH"): 'ЗДРАВКОВИЋ КОСТАНТНИН',
    (267, "ЗЛАћАНОВИ'ћ ЂОРЂЕ"): 'ЗЛАЂАНОВИЋ ЂОРЂЕ',
    (268, 'ИВАНОВИћ ШАН'): 'ИВАНОВИЋ МИЛАН',
    (268, "ИВКОВИ'ћ љУБШПА"): 'ИВКОВИЋ ЉУБИША',
    (269, 'ИВКОВРЊ УРОШ'): 'ИВКОВИЋ УРОШ',
    (269, "ШЊАТОВИ'ћ БОРИВОЈЕ"): 'ИГЊАТОВИЋ БОРИВОЈЕ',
    (269, "ШЊАТОВИ'ћ РОКСАНДА"): 'ИГЊАТОВИЋ РОКСАНДА',
    (269, "ИВОШВИ'ћ НИКОЛА"): 'ИВОШВИЋ НИКОЛА',
    (269, 'NJU/FF: ДРАГОЊУБ'): 'ИЛИЋ ДРАГОЉУБ',
    (269, 'WII/fh ДРАГОШ'): 'ИЛИЋ ДРАГОШ',
    (269, 'WII/[Tm "БОРБЕ'): 'ИЛИЋ ЂОРЂЕ',
    (269, 'WII/fh Ј ЕВРЕМ'): 'ИЛИЋ ЈЕВРЕМ',
    (269, 'PUM/Th JOBAH'): 'ИЛИЋ ЈОВАН',
    (270, 'HDI/IT] МИЛИВОЈЕ'): 'ИЛИЋ МИЛИВОЈЕ',
    (270, 'JTI/fh МИЛУТИН'): 'ИЛИЋ МИЛУТИН',
    (270, 'HDI/IT) МОМЧИЛО'): 'ИЛИЋ МОМЧИЛО',
    (270, 'PUB/fh HETAP'): 'ИЛИЋ ПЕТАР',
    (270, 'YU“/TB РАДОСЛАВ'): 'ИЛИЋ РАДОСЛАВ',
    (270, 'JTI/[Tx САВА'): 'ИЛИЋ САВА',
    (270, 'PBH/[Tx СВЕТОМИР'): 'ИЛИЋ СВЕТОМИР',
    (270, 'HDI/IB СТАНОЈКО'): 'ИЛИЋ СТАНОЈКО',
    (270, 'HDI/[Tx ХРИСТИВОЈ Е'): 'ИЛИЋ ХРИСТИВОЈЕ',
    (270, 'ИМБРИБ МИЛУТИН'): 'ИМБРИЋ МИЛУТИН',
    (270, 'HI/IT; ДАНИЛО'): 'ИЛИЋ ДАНИЛО',
    (271, 'ЈАНКОВИТ: МОМЧИЛО'): 'ЈАНКОВИЋ МОМЧИЛО',
    (272, "Ј АЊИ'ћ љУБРПЦА"): 'ЈАЊИЋ ЉУБИЦА',
    (272, "Ј АЊИ'ћ ТОМА"): 'ЈАЊИЋ ТОМА',
    (272, "ЈЕВ'ГИ'ћ ВОЈИСЛАВ"): 'ЈЕВТИЋ ВОЈИСЛАВ',
    (272, "Ј ЕВТИ'ћ ЂОРТЈЕ"): 'ЈЕВТИЋ ЂОРЂЕ',
    (273, "ЈШЕНКОВИ'ћ ВЕЛИМИР"): 'ЈЕЛЕНКОВИЋ ВЕЛИМИР',
    (273, 'ЈОВАНОВИТ: ВИТОМИР'): 'ЈОВАНОВИЋ ВИТОМИР',
    (273, 'JOBAHOBVITx ДРАГОЊУБ'): 'ЈОВАНОВИЋ ДРАГОЉУБ',
    (274, 'ЈОВАНОВИТт ЖНКА'): 'ЈОВАНОВИЋ ЖИКА',
    (274, "JOBAHOBH'B љУБИША"): 'ЈОВАНОВИЋ ЉУБИША',
    (275, "JOBAHOBH'Fx МОМЧИЛО"): 'ЈОВАНОВИЋ МОМЧИЛО',
    (275, "JOBAHOBI/I'Fn ПАВЛЕ"): 'ЈОВАНОВИЋ ПАВЛЕ',
    (275, 'ЈОВАНОВУГБ СВЕТОМИР'): 'ЈОВАНОВИЋ СВЕТОМИР',
    (276, "Ј ОЊЕВИ'ћ МИОДРАГ"): 'ЈОЊЕВИЋ МИОДРАГ',
    (276, "ЈОСИПОВИ'ћ ТАЈХЕРТ"): 'ЈОСИПОВИЋ ТАЈХЕРТ',
    (277, "ЈОЛИ'ћ - БУДИМИРОВИЂ РАДМРША"): 'ЈОЛИЋ-БУДИМИРОВИЋ РАДМИЛА',
    (277, 'КАРАЏРГБ МИЛАН'): 'КАРАЏИЋ МИЛАН',
    (277, 'КАРАЏИТ: РАДИСАВ'): 'КАРАЏИЋ РАДИСАВ',
    (277, 'КАРИО ИСАК'): 'КАРИО ИСАК',
    (277, "КАШ'ћЕПАН ЂУРО"): 'КАШЋЕЛАН ЂУРО',
    (277, "КОЖОМАНОВИ'ћ љУБИСАВ"): 'КОЖОМАНОВИЋ ЉУБИСАВ',
    (278, 'KOJI/fh ИВАН'): 'КОЈИЋ ИВАН',
    (278, 'KOJI/IT: ИЛИЈА'): 'КОЈИЋ ИЛИЈА',
    (278, "KOJ И'ћ МИЛАН"): 'КОЈИЋ МИЛАН',
    (278, "KOJ И'ћ ЧЕДОМИР"): 'КОЈИЋ ЧЕДОМИР',
    (278, 'KOI-IHT: CBETO3AP'): 'КОНИЋ СВЕТОЗАР',
    (278, "КОСТИ'ћ – CTEBPI'B ДРАГОЊУБ"): 'КОСТИЋ-СТЕВИЋ ДРАГОЉУБ',
    (278, "КОЦИ'ћ ШОДРАГ"): 'КОЦИЋ МИОДРАГ',
    (278, 'КОЏИС КАТАРИНА'): 'КОЦИС КАТАРИНА',
    (278, 'КРИЛЕНКО ИВАН'): 'КРИЛЕНКО ИВАН',
    (278, 'КРИСАНОВИЂ JOBAH'): 'КРИСАНОВИЋ ЈОВАН',
    (279, 'КРШЊАНИН МИОМИР'): 'КРШЉАНИН МИОМИР',
    (279, 'КУПРЕШАК МИЈО'): 'КУПРЕШАК МИЈО',
    (279, 'ЛАЗАРЕВИТ: МИЛАН'): 'ЛАЗАРЕВИЋ МИЛАН',
    (280, "ЛЕМАЈИ'ћ МРШЕВА"): 'ЛЕМАЈИЋ МИЛЕВА',
    (280, 'ЛОР БОРА'): 'ЛОР БОРА',
    (280, 'ЛУКИТ: СВЕТОМИР'): 'ЛУКИЋ СВЕТОМИР',
    (280, 'ЛУПШАН ЂОРТЈЕ'): 'ЛУПШАН ЂОРЂЕ',
    (281, "МАРРШКОВИ'ћ ДИМИТ РИЈ Е"): 'МАРИНКОВИЋ ДИМИТРИЈЕ',
    (281, "МАРШ–!КОВИ'ћ КРСТА"): 'МАРИНКОВИЋ КРСТА',
    (281, "МАРШ-!КОВИ'Н СВЕТОЗАР"): 'МАРИНКОВИЋ СВЕТОЗАР',
    (281, 'МАРШ–!КОВИТт ТРИФУН'): 'МАРИНКОВИЋ ТРИФУН',
    (281, "МРАЈАНОВИ'ћ ДРАГОМИР"): 'МРАЈАНОВИЋ ДРАГОМИР',
    (282, 'МАРИЈУТИТ: ЖИВОЈИН'): 'МАРИЈУТИЋ ЖИВОЈИН',
    (282, 'МАРИЛО МОЈСИЈЕ'): 'МАРИЛО МОЈСИЈЕ',
    (282, 'МАРКОВИТ: МИЛИЦА'): 'МАРКОВИЋ МИЛИЦА',
    (282, "МАРКОВИ'ћ нвдвљко"): 'МАРКОВИЋ НЕДЕЉКО',
    (283, "МАРКОВИ'ћ РУСИДОР"): 'МАРКОВИЋ РУСИДОР',
    (283, 'MATE/fh МИРОСЛАВ'): 'МАТИЋ МИРОСЛАВ',
    (283, 'МЕЂАНИН ЗДРАВКО'): 'МЕЂАНИН ЗДРАВКО',
    (284, 'МИЛАДИНОВИТ: СТОЈАН'): 'МИЛАДИНОВИЋ СТОЈАН',
    (284, 'ШЕТИЂ АЛЕКСАНДАР'): 'МИЛЕТИЋ АЛЕКСАНДАР',
    (284, 'МИЛЕТИТ: БРАНИСЛАВА'): 'МИЛЕТИЋ БРАНИСЛАВА',
    (284, "ШЕТИ'ћ ЖИВОТА"): 'МИЛЕТИЋ ЖИВОТА',
    (285, "МИЛЕТИ'ћ CBETOMI/IP"): 'МИЛЕТИЋ СВЕТОМИР',
    (285, 'ШЛИЂ МАРКО'): 'МИЛИЋ МАРКО',
    (285, "МИЛИБЕВИ'В MMI/BOJE"): 'МИЛИЋЕВИЋ МИЛИВОЈЕ',
    (286, 'ШОЈЕВИТ: ЖИВОМИР'): 'МИЛОЈЕВИЋ ЖИВОМИР',
    (286, 'МИЛОЈЕВИЂ ВУЛ/ША'): 'МИЛОЈЕВИЋ ВУЈИЦА',
    (286, "ШОЈЕВИ'ћ ТАНАСИЈ Е"): 'МИЛОЈЕВИЋ ТАНАСИЈЕ',
    (286, "МИЛОЈКОВИ'ћ ДРАГУ'П/Ш"): 'МИЛОЈКОВИЋ ДРАГУТИН',
    (287, 'МИЛОЈКОВИТ: ЈОВАН'): 'МИЛОЈКОВИЋ ЈОВАН',
    (287, 'МИЛОРАДОВИТЊ СЛОБОДАН'): 'МИЛОРАДОВИЋ СЛОБОДАН',
    (287, 'МИЛОРАДИВИЂ СТОЈАН'): 'МИЛОРАДИВИЋ СТОЈАН',
    (287, 'МИЛОСАВЊЕВИТ: ЖИВОЈИН'): 'МИЛОСАВЉЕВИЋ ЖИВОЈИН',
    (288, "МИЛОСАВЊЕВИЂ – l'IYPPI'h љУБРППА"): 'МИЛОСАВЉЕВИЋ-ПУРИЋ ЉУБИША',
    (288, 'МИЛОСАВЊЕВИЂ љУБРШЈА'): 'МИЛОСАВЉЕВИЋ ЉУБИША',
    (288, "МРШОСАВЊЕВИ'В Д. ЖИВОЈРШ"): 'МИЛОСАВЉЕВИЋ Д. ЖИВОЈИН',
    (288, 'МИЛОСАВЊАВИБ ТИХОМИР'): 'МИЛОСАВЉАВИЋ ТИХОМИР',
    (289, "МИЛОШЕВИТ: – МИЛОРАДОВИ'ћ ДОБРИВОЈЕ"): 'МИЛОШЕВИЋ-МИЛОРАДОВИЋ ДОБРИВОЈЕ',
    (289, "МИЛОШЕВИ'ћ љувомив"): 'МИЛОШЕВИЋ ЉУБОМИР',
    (289, 'МИЛОШЕВИТ) МИЛАН'): 'МИЛОШЕВИЋ МИЛАН',
    (289, 'МИЛОШЕВИТ: СВЕТИСЛАВ'): 'МИЛОШЕВИЋ СВЕТИСЛАВ',
    (289, 'MPUIYTI/[HOBWB МАКСИМ'): 'МИЛУТИНОВИЋ МАКСИМ',
    (290, 'МИРКОВИТ: ЖИВАН'): 'МИРКОВИЋ ЖИВАН',
    (291, 'МИП/ГР! БОГ ДАН'): 'МИТИЋ БОГДАН',
    (291, 'МИП/ГР! ВЛАСТИМИР'): 'МИТИЋ ВЛАСТИМИР',
    (291, "МИ'П/Гћ МИРОСЛАВ"): 'МИТИЋ МИРОСЛАВ',
    (291, 'МИТ РОВИТ: ТРАЈКО'): 'МИТРОВИЋ ТРАЈКО',
    (291, 'MUMI]/FF) АЛЕКСАНДАР'): 'МИШИЋ АЛЕКСАНДАР',
    (291, 'МОНТИЈ АС САДИКА'): 'МОНТИЈАС САДИКА',
    (291, 'МОРИСАвљЕВИТт МИОДРАГ'): 'МОРИСАВЉЕВИЋ МИОДРАГ',
    (291, 'МОСКЛОВЛИЂ ДРАГАН'): 'МОСКЛОВЛИЋ ДРАГАН',
    (291, "МОСКОВЛИ'ћ МАРКО"): 'МОСКОВЛИЋ МАРКО',
    (291, 'МОСКОВЛИТ: РАДОМИР'): 'МОСКОВЛИЋ РАДОМИР',
    (291, 'МОМАКОВИћ ЧЕДОМИР'): 'МОМАКОВИЋ ЧЕДОМИР',
    (292, "НАЈЧЕВИ'ћ ДРАГОЊУБ"): 'НАЈЧЕВИЋ ДРАГОЉУБ',
    (292, "НАЦКОВИ'ћ СВЕТОМИР"): 'НАЦКОВИЋ СВЕТОМИР',
    (292, 'НЕДЕЈБКОВИЂ ДОБРИВОЈ Е'): 'НЕДЕЉКОВИЋ ДОБРИВОЈЕ',
    (292, "НЕДЕЈБКОВИ'ћ ДРАГОСЛАВ"): 'НЕДЕЉКОВИЋ ДРАГОСЛАВ',
    (292, 'НЕћАК "B)/PO'): 'НЕЋАК ЂУРО',
    (292, "НРЖОЛИ'ћ BOJI/lMI/IP"): 'НИКОЛИЋ ВОЈИМИР',
    (293, 'НШСОЛИТ: ЖИВОЈИН'): 'НИКОЛИЋ ЖИВОЈИН',
    (293, 'НШСОЛИТ: ПЕТРОНИЈЕ'): 'НИКОЛИЋ ПЕТРОНИЈЕ',
    (293, 'НИЦУЊЕВИЂ ДУШАН'): 'НИЦУЉЕВИЋ ДУШАН',
    (293, 'НОВАКОВИТ: ДИМИТРИЈЕ'): 'НОВАКОВИЋ ДИМИТРИЈЕ',
    (294, 'НОВАКОВИТ: ПАВЛЕ'): 'НОВАКОВИЋ ПАВЛЕ',
    (294, "OBPAHOBI/I'Fx АЛЕКСАНДАР"): 'ОБРАДОВИЋ АЛЕКСАНДАР',
    (294, 'ОБРАДОВИТ: ВЛАДА'): 'ОБРАДОВИЋ ВЛАДА',
    (295, "HAVHOBH'B ДРАГОЊУБ"): 'ПАУНОВИЋ ДРАГОЉУБ',
    (296, "ПАУНОВИ'Р: НЕМАЊА"): 'ПАУНОВИЋ НЕМАЊА',
    (296, "ПЕРИ'ћ КАТАРШ–1А"): 'ПЕРИЋ КАТАРИНА',
    (297, "ПЕ'ГКОВИ'ћ МИЛУТИН"): 'ПЕТКОВИЋ МИЛУТИН',
    (297, 'ПЕТРОВИТ: БОРИВОЈЕ'): 'ПЕТРОВИЋ БОРИВОЈЕ',
    (298, "ПЕТРОВИ'ћ ДУШАН. Боња"): ('ПЕТРОВИЋ ДУШАН', '', 'Боња, '),
    (298, 'ПЕТРОВИТ: ЛУКА'): 'ПЕТРОВИЋ ЛУКА',
    (298, 'ПЕТРОВИТ: љУБИША'): 'ПЕТРОВИЋ ЉУБИША',
    (298, 'ПЕТРОВИТ! ПЕТАР'): 'ПЕТРОВИЋ ПЕТАР',
    (298, "ПЕТРОВИћ – АКЕСНТ'ИЈЕВИЂ ПЕТАР"): 'ПЕТРОВИЋ-АКЕСНТИЈЕВИЋ ПЕТАР',
    (299, 'EU“/[T\\ JOBAH'): 'ПЕШИЋ ЈОВАН',
    (299, "ПОПОВИ'ћ JOCHH"): 'ПОПОВИЋ ЈОСИП',
    (299, 'ПОПОВИТ: СЛАВКО'): 'ПОПОВИЋ СЛАВКО',
    (299, 'ПРОТИВ МИОДРАГ'): 'ПРОТИЋ МИОДРАГ',
    (299, 'ПОСАВЕТ Ј. ТОМА'): 'ПОСАВЕТ Ј. ТОМА',
    (300, 'ПРЛУЛОВИТ: ОЛГ А'): 'ПРЛУЛОВИЋ ОЛГА',
    (300, "ПРВУЛОВИ'ћ ДИМИТ РИЈ Е"): 'ПРВУЛОВИЋ ДИМИТРИЈЕ',
    (300, 'РАДИТ: MPUIAH'): 'РАДИЋ МИЛАН',
    (301, "РАДОСАВЊЕВИ'ћ НРПСОЛА"): 'РАДОСАВЉЕВИЋ НИКОЛА',
    (301, 'РАДОСАВЊЕВИ\'ћ "ГИХОМИР'): 'РАДОСАВЉЕВИЋ ТИХОМИР',
    (302, "РАКИ'ћ НРЖОЛА"): 'РАКИЋ НИКОЛА',
    (303, 'ине.'): None,
    (303, 'РЕМЕЊАК ВУЈША'): 'РЕМЕЊАК ВУЈИЦА',
    (303, 'РЕФИК САДШС'): 'РЕФИК САДИК',
    (303, 'РИСТИТ! МИЛАН'): 'РИСТИЋ МИЛАН',
    (303, 'РУЖИћ ДАРРП–[КА'): 'РУЖИЋ ДАРИНКА',
    (304, "РУКИ'ћ БОГДАН"): 'РУКИЋ БОГДАН',
    (304, 'САВИТ: АВРАМ'): 'САВИЋ АВРАМ',
    (304, 'САМАРШ/Гћ СЛОБОДАН'): 'САМАРЏИЋ СЛОБОДАН',
    (305, 'СИЛВЕСТЕР ХАЈНЦ'): 'СИЛВЕСТЕР ХАЈНЦ',
    (305, 'СИНАЈКО ДУШАН'): 'СИНАЈКО ДУШАН',
    (305, "СПАСИ'ћ BOJI/IH"): 'СПАСИЋ ВОЈИН',
    (306, "СТАНКОВИТ: МИЛУ'ГРШ"): 'СТАНКОВИЋ МИЛУТИН',
    (306, "СТАНОЈЕВИ'ћ ДИМИТ РИЈ Е"): 'СТАНОЈЕВИЋ ДИМИТРИЈЕ',
    (307, "СТ АНОЈ ЕВИ'ћ љУБОМИР"): 'СТАНОЈЕВИЋ ЉУБОМИР',
    (307, 'СТАМЕНКОВИТ: ЖИВОРАД'): 'СТАМЕНКОВИЋ ЖИВОРАД',
    (307, 'СТАНИСАВЈБЕВИЂ МИРОСЛАВ'): 'СТАНИСАВЉЕВИЋ МИРОСЛАВ',
    (307, "СТАНОЈЛОВИ'ћ ВЛАДИћШР"): 'СТАНОЈЛОВИЋ ВЛАДИМИР',
    (307, "СТАНОИЧИ'В РАДОМИР"): 'СТАНОИЧИЋ РАДОМИР',
    (307, "СТЕВИ'ћ ДРАГШПА"): 'СТЕВИЋ ДРАГИША',
    (308, 'СТЕВИТ: ИВАН'): 'СТЕВИЋ ИВАН',
    (308, 'СТЕВИТ: СВЕТОМИР'): 'СТЕВИЋ СВЕТОМИР',
    (308, "С'ГЕПАНОВИТ: НИКОЛА"): 'СТЕПАНОВИЋ НИКОЛА',
    (308, "СТЕФАНОВИ'ћ ←БОР'ЊЕ"): 'СТЕФАНОВИЋ ЂОРЂЕ',
    (310, "СТОЈАНОВИ'ћ љувомив"): 'СТОЈАНОВИЋ ЉУБОМИР',
    (310, "СТОЈАНОВИ'ћ МИЛЕ. Жицар"): ('СТОЈАНОВИЋ МИЛЕ', '', 'Жицар, '),
    (310, "СТОЈАНОВИ'ћ С'ГЕВАН"): 'СТОЈАНОВИЋ СТЕВАН',
    (310, 'СТОЈМИРОВИЂ СВЕТИСЛАВ'): 'СТОЈМИРОВИЋ СВЕТИСЛАВ',
    (310, 'СТОЈИЛОВИТ: ДРАГИША'): 'СТОЈИЛОВИЋ ДРАГИША',
    (311, 'СТОЈИЧЕВИТ: ДУШАН'): 'СТОЈИЧЕВИЋ ДУШАН',
    (312, "СТРАЈШ–[ОВИ'ћ СЕЛИМИР"): 'СТРАЈИНОВИЋ СЕЛИМИР',
    (312, "СТРАИНОВИ'В ТРАИЛО"): 'СТРАИНОВИЋ ТРАИЛО',
    (312, "СТРАЈИ'ћ ФИЛИП"): 'СТРАЈИЋ ФИЛИП',
    (313, "СУБОТИ'ћ инг ПЕТАР"): 'СУБОТИЋ инг ПЕТАР',
    (314, 'ТРАИЛОВИЂ ЂОРћЕ'): 'ТРАИЛОВИЋ ЂОРЂЕ',
    (315, 'ТРИФУНОВИТ: љУБОМИР'): 'ТРИФУНОВИЋ ЉУБОМИР',
    (315, 'УРОШЕВИТ: "БОРТЈЕ'): 'УРОШЕВИЋ ЂОРЂЕ',
    (315, 'ФИЛИМОН ИЛИЈ А'): 'ФИЛИМОН ИЛИЈА',
    (315, "ФИЛРШОВИ'В АЛЕКСАНДАР"): 'ФИЛИПОВИЋ АЛЕКСАНДАР',
    (316, "ФИЛРШОВИ'В ДУШАН"): 'ФИЛИПОВИЋ ДУШАН',
    (316, 'ФИРУЛЕСКО МИЛАН'): 'ФИРУЛЕСКО МИЛАН',
    (316, "ФОТИ'ћ АЛИЈА"): 'ФОТИЋ АЛИЈА',
    (316, "ФУЈКИ'ћ МИЛАН"): 'ФУЈКИЋ МИЛАН',
    (316, 'ЦВЕТКОВИТ: ДУШАН'): 'ЦВЕТКОВИЋ ДУШАН',
    (317, 'ЧИКАРЕВИЂ МИЛУТШ-Ц'): 'ЧИКАРЕВИЋ МИЛУТИН',
    (317, "ЧОБАТАРЕВИ'ћ ДРАГИША"): 'ЧОБАТАРЕВИЋ ДРАГИША',
    (317, "ЧОГУРОВИ'ћ ВЕПИЗАР"): 'ЧОГУРОВИЋ ВЕЛИЗАР',
    (317, "l·IOJIOBl/I'Fn HETAP"): 'ЧОЛОВИЋ ПЕТАР',
    (317, 'HDMI/IT: МИЛАН'): 'ЧОМИЋ МИЛАН',
    (317, "ћИРИ'ћ АЛЕКСАНДАР"): 'ЋИРИЋ АЛЕКСАНДАР',
    (317, 'Til/[PHP: дОБРИВОЈЕ'): 'ЋИРИЋ ДОБРИВОЈЕ',
    (317, "ћУКОВИ'ћ MI/UIAH"): 'ЋУКОВИЋ МИЛАН',
    (317, 'ШАРИТ: ДУШАН'): 'ШАРИЋ ДУШАН',
    (317, "ШЕРБАНОВИ'ћ ЈОВАН"): 'ШЕРБАНОВИЋ ЈОВАН',
    (318, 'ШЕРБАНОВИЂ ПАУН'): 'ШЕРБАНОВИЋ ПАУН',
    (318, 'ШТРИБАНОВИБ ВЛАДНМИР'): 'ШТРИБАНОВИЋ ВЛАДИМИР',
    (318, 'ШУКАЛОВИТт "БОРЂЕ'): 'ШУКАЛОВИЋ ЂОРЂЕ',
    (318, 'ШУТтУР МНТтО'): 'ШУЋУР МИЋО',
}

# Latin capitals the OCR gives for the Cyrillic ones they look like
LOOKALIKE = str.maketrans({'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К', 'M': 'М', 'O': 'О', 'P': 'Р',
                           'T': 'Т', 'X': 'Х', 'J': 'Ј', 'Y': 'У', ']': 'Ј'})

_names: Counter = Counter()


def corpus() -> None:
    """Every other unit's names, in Latin as spelled, for checking a decoded name and joining split ones"""
    for f in Path('website/public').glob('*soldiers.json'):
        if f.name != 'pozarevacki-odred-soldiers.json':
            for s in json.loads(f.read_text(encoding='utf-8')):
                for k in ('last_name', 'first_name'):
                    _names[(s.get(k) or '').upper()] += 1


def known(cyr: str) -> bool:
    return all(_names[cyrillic_to_latin(w)] > 0 for w in re.split(r'[\s-]+', cyr) if w)


def garbled(head: str) -> bool:
    """A name the OCR read in Latin letters or with junk in its first word"""
    first = head.split()[0] if head.split() else ''
    return bool(re.search(r'[A-Za-z/\\\[\]{}()|?!"“”;:]', first))


# The OCR's usual confusions in these capitals, tried one at a time and two together
CONFUSIONS = [('Њ', 'Љ'), ('П', 'Л'), ('Б', 'Ђ'), ('В', 'Б'), ('РШ', 'ИН'), ('РП', 'ИН'), ('РПЗ', 'ИЋ'), ('РГЋ', 'ИЋ'), ("'", ''),
              ('’', '')]


def fix_word(w: str) -> str:
    """A word of a name the corpus doesn't know: the spelling the corpus knows best among the OCR's usual
    confusions (МИЛОСАВЊЕВИЋ -> МИЛОСАВЉЕВИЋ, АНЂЕПКО -> АНЂЕЛКО, ЖИВОЈРШ -> ЖИВОЈИН); else as read"""
    if not re.fullmatch(f"[{UC}'’]+", w) or _names[cyrillic_to_latin(w)]:
        return w

    def variants(s: str) -> set[str]:
        out = set()
        for a, b in CONFUSIONS:
            for m in re.finditer(re.escape(a), s):
                out.add(s[:m.start()] + b + s[m.end():])
        return out
    one = variants(w)
    cands = one | {v2 for v in one for v2 in variants(v)}
    best = max(cands, key=lambda c: _names[cyrillic_to_latin(c)], default=w)
    return best if _names[cyrillic_to_latin(best)] >= 2 else w


def split_head(text: str) -> tuple[str, str]:
    """The name in capitals at the start of an entry's first line, and the rest; the comma after the name is
    sometimes read as a full stop or „"""
    text = re.sub(r'^[^\w]+', '', text)
    m = re.match(rf'^(?P<head>(?:[^\s,„]+\s+)*?[^\s,„]+?)\s*(?:,|„|\.\s+(?=[а-яђјљњћџ]|У\s)|\s+(?=из\s))\s*(?P<rest>.*)$', text)
    if not m:
        return text, ''
    return m.group('head'), m.group('rest')


def decode(head: str) -> str:
    """The certain repairs of a name in capitals"""
    head = re.sub(r'["“”„]', '', head)
    head = head.replace("'Б", 'Ђ').replace("'ћ", 'Ћ').replace('’ћ', 'Ћ')
    words = []
    for w in re.split(r'(\s+|\s*[-–]\s*)', head):
        if not w.strip() or re.fullmatch(r'\s*[-–]\s*', w):
            words.append('-' if '-' in w or '–' in w else ' ')
            continue
        if re.search(f'[{UC}]', w):
            w = w.translate(LOOKALIKE)
        w = re.sub(r'^ћ(?=[' + UC + '])', 'Ђ', w)                            # ЂОКИЋ: a lowercase ћ starts it
        w = re.sub(r'(?<=И)(?:[\'’][ВБЂНћ]|Т[^' + UC + r'\s]{1,3}|[^' + UC + r'\s]{1,4})$', 'Ћ', w)   # -ИЋ: И'в, ИТт, ИТ1
        w = re.sub(r'(?<=И)[БЂ]$', 'Ћ', w)
        w = re.sub(r'(?<=[' + UC + '])ћ', 'Ћ', w)
        if not re.fullmatch(r'Д[рР]\.?', w):
            w = w.upper()                                                    # "ДРАГољУБ", "дРАГОСЛАВ", "љувомир"
        words.append(fix_word(w))
    head = ''.join(words).strip()
    head = re.sub(rf'(?<![{UC}])([{UC}]) (?=[{UC}]{{2,}})', r'\1', head)    # "Г РУБИЋ", "Ј ОВАН"

    def join(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        return a + b if len(b) <= 2 or _names[cyrillic_to_latin(a + b)] > _names[cyrillic_to_latin(b)] else m.group(0)
    return re.sub(rf'([{UC}]*Ј) ([{UC}]+)', join, head)                       # "СТОЈ АН", "ВАСИЛИЈ Е"


def entries() -> list[dict]:
    """Each entry's first line: page, place on the page, the name (decoded or read from the scan) and the rest"""
    out, unnamed = [], False
    for page in PAGES:
        lines = page_lines(BOOK, page)[0]
        xs = sorted(l.x0 for l in lines)
        body = xs[len(xs) // 4] if xs else 0                                 # where the continuation lines start
        n = 0
        for line in lines:
            text = line.text.strip().replace("'Б", 'Ђ')
            if not text or re.fullmatch(r'[\d\s]+', text) or re.fullmatch(rf'[{UC}A-Z]\.?', text):
                continue                                                     # page numbers, the letter headings
            start = 700 < line.x0 - body < 1500                              # the first line is indented
            ws = line.words
            for k in (1, 2):
                # a scrap of the line before set on this one ("y БУ'БЕЛАН ДРАГОЊУБ, ..."): it goes back there
                if (not start and len(ws) > k and out and all(len(w.text) <= 3 for w in ws[:k])
                        and 700 < ws[k].x0 - body < 1500 and re.match(rf"^[{UC}'ћ]{{3,}}", ws[k].text)):
                    out[-1]['text'] += ' ' + ' '.join(w.text for w in ws[:k])
                    text, start = ' '.join(w.text for w in ws[k:]).replace("'Б", 'Ђ'), True
                    break
            item = {'page': page, 'line': line, 'start': start, 'text': text}
            if start and text.startswith('Борци Пожаревачког'):
                unnamed = True                                               # "... kojima nisu utvrđena imena"
                item['skip'] = True
            elif start and text.startswith('3 црвеноармејаца'):
                item['skip'] = True                                          # "3 red army men ... names not remembered"
            elif start and unnamed:
                item['unnamed'] = True
            elif start:
                head, rest = split_head(text)
                item['key'] = key = (page, head)
                n += 1
                read = SCAN.get(key, '')
                if read is None:
                    item['start'] = False                                    # not an entry: "ине.", a line of the one before
                else:
                    if isinstance(read, tuple):                              # the rest of the line set right too
                        read, drop, lead = read
                        assert rest.startswith(drop), (key, rest[:30])
                        rest = lead + rest[len(drop):]
                    item.update(n=n - 1, ocr=head, head=read or decode(head), rest=rest)
            out.append(item)
    return out


# Latin letters the OCR gives for the Cyrillic ones they look like, in the entries' text
LATIN_IN_CYRILLIC = str.maketrans({'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'x': 'х', 'y': 'у', 'A': 'А',
                                   'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н', 'O': 'О', 'P': 'Р', 'C': 'С',
                                   'T': 'Т', 'X': 'Х', 'Y': 'У'})


def cyrillic_text(text: str) -> str:
    """A word of Cyrillic and Latin look-alikes ("Кучевy"), or the Latin "y" for the preposition у, in Cyrillic"""
    def word(m: re.Match) -> str:
        w = m.group(0)
        if (re.search('[а-яђјљњћџА-ЯЂЈЉЊЋЏ]', w) or w in ('y', 'Y')) and re.fullmatch('[а-яђјљњћџА-ЯЂЈЉЊЋЏaeopcxyABEKMHOPCTXY]+', w):
            return w.translate(LATIN_IN_CYRILLIC)
        return w
    return re.sub(r'[^\W\d_]+', word, text)


def read_lines(_path: str, _start: int, _end) -> list[dict]:
    out, used = [], set()
    for e in entries():
        if 'key' in e:
            used.add(e['key'])
        if e.get('skip'):
            text = '§skip ' + e['text']
        elif e.get('unnamed'):
            text = '¤' + e['text']
        elif 'head' in e:
            text = e['head'] + ', ' + e['rest']
        else:
            text = e['text']
        text = cyrillic_text(text)
        out.append({'text': (MARK if e['start'] else '') + text, 'x': e['line'].x0, 'y': e['line'].top, 'page': e['page']})
    assert used >= set(SCAN), f'readings for entries that are not there: {sorted(set(SCAN) - used)}'
    return out


def parse_entry(text: str) -> dict:
    text = text.replace(MARK, '').strip()
    if text.startswith('§skip'):
        return {}
    text = re.sub(r'(?<=[a-zčćžšđ])[—–-]\s+(?=[a-zčćžšđ])', '', text)      # "u odre– du": broken at the line's end
    if text.startswith('¤'):
        # the closing section: a nickname or a first name only ("„Buda“", "Sredoje. „Lovac“", "Velikojac Vlastimir")
        text = text[1:]
        m = re.match(r'^(?P<name>„[^“"]+[“"]|[A-ZČĆŽŠĐ][a-zčćžšđ]+(?: [A-ZČĆŽŠĐ][a-zčćžšđ]+)?)[.,]?\s*(?P<rest>.*)$', text)
        if not m:
            return {}
        name, parts = m.group('name'), m.group('name').split()
        if len(parts) == 2 and not name.startswith('„'):
            return _record(parts[0], parts[1], '', m.group('rest'))          # "Velikojac Vlastimir, puškomitraljezac"
        rec = _record(name, '', '', m.group('rest'))
        rec['_alone'] = True                                                 # a first name or a nickname only: see post
        return rec
    head, _, rest = text.partition(', ')
    words = head.split()
    title, initial = None, ''
    if len(words) > 2 and re.fullmatch(r'(?:D[rR]|ing)\.?', words[1]):
        title, words = words[1].lower().rstrip('.'), [words[0]] + words[2:]  # "ADAMOVIĆ Dr Milosav", "SUBOTIĆ ing PETAR"
    if len(words) > 2 and re.fullmatch(r'[A-ZČĆŽŠĐ][a-zA-Zž]?\.', words[1]):
        initial, words = words[1].rstrip('.').title(), [words[0]] + words[2:]  # "MILOSAVLJEVIĆ D. ŽIVOJIN"
    last, given = words[0], ' '.join(words[1:])
    rest = re.sub(r"^['’]?ć(?=[a-zčćžšđ])", 'Ć', rest)                       # "ćota": a capital Ћ read in lowercase
    info = rest
    nick = re.match(r'^(?P<nick>[A-ZČĆŽŠĐ][a-zčćžšđ]+(?: [A-ZČĆŽŠĐ][a-zčćžšđ]+)?)\s*[,.]\s*(?P<rest>.*)$', rest)
    if nick and not re.match(r'^(?:Rođen|Rodj|U|Poginuo|Iz)$', nick.group('nick')):
        info = f"zvani {nick.group('nick')}; {nick.group('rest')}"           # "Ćota, zemljoradnik, ..."
    if title:
        info = f'{title}; ' + info
    return _record(last, given, initial, info)


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s.pop('_alone', False):
            # the closing section's men known by one name ("Ivan", "Kuzman", "„Buda“"): it is no surname
            s['first_name'], s['last_name'] = s['last_name'], ''
        page = s.pop('pdf_page')
        for k in ('pdf_y', 'pdf_x', 'pdf_y_end', 'pdf_file'):
            s.pop(k, None)
        s['source_url'] = viewer_url(BOOK, page)
        s['source_page'] = printed_page(BOOK, page)
        s['full_name'] = ' '.join(p for p in (s['last_name'], s['middle_name'], s['first_name']) if p)
    return soldiers


def unread() -> list[dict]:
    """Entries whose name, decoded, the corpus doesn't know and the scan readings don't give"""
    return [e for e in entries() if 'head' in e and e['key'] not in SCAN and not known(e['head'])]


if __name__ == '__main__':
    corpus()
    run_parser(
        pdf_path='poreklo/pozarevacki-odred.json',
        brigade_code=119,
        output_path='website/public/pozarevacki-odred-soldiers.json',
        script='cyrillic',
        extract_fn=read_lines,
        entry_start_re=re.compile('^' + MARK),
        parse_entry_fn=parse_entry,
        post_fn=post,
    )
    print(f'  {len(unread())} names neither the corpus knows nor the scan readings give')
