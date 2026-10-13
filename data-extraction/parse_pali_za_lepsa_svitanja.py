"""
Pali za lepša svitanja (Majke heroja pričaju...), Al. Tadić, 1967 (biblioteka.poreklo.rs): a book across units, its
entries added to the records of the heroes it portrays (see scripts/match_references.py), as the hero books are.

Each chapter is a hero's mother (or a comrade) telling his or her story, under the hero's name, a portrait and a short
biography: birth, trade, KPJ, the NOB, death and the day proclaimed a narodni heroj. That biography is the entry kept;
the stories stay in the book. 32 heroes in 30 chapters ("Umrli su zagrljeni" and "Dvojica iz ilegalne štamparije" are
two each; Dara Pavlović of "Dve sestre" was not proclaimed and has no biography).

The OCR of the biographies is garbled past reading in several chapters ("К3'3М.·1НЈОСПФОВСКИ" for Кузман Јосифовски),
so each was typed from the page image (cut out by its OCR boxes), in Latin, as printed: Marija Bursać born 1924,
Ramiz "Sadik", Bora Vukmirović born "u Bregnovu". Two misprints are read as meant: Kuzman Josifovski proclaimed in 1945
(the scan's "1915"), Elpida Karamandi "stupila" (printed "ступили"), and "U NOB" where Đuro Strugar's has "У НОМ".

Output: data-extraction/poreklo/pali-za-lepsa-svitanja-entries.json (IDs 9004xxxxxx), with the fields the matcher reads.

Usage: python data-extraction/parse_pali_za_lepsa_svitanja.py
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
OUT = HERE / 'poreklo' / 'pali-za-lepsa-svitanja-entries.json'
DOC = '6b106046-9636-495b-a1d2-ee797e7c60e3/00000001/00000001/00008604'
VIEWER_URL = 'https://biblioteka.poreklo.rs/ResCarta/jsp/RcWebImageViewer.jsp?doc_id={id}&pg_seq={page}'
PREFIX = '9004'
OFFSET = 4                       # scan page minus the book's page (the scan's p. 23 is the book's 19)

# (scan page, surname, given name, nickname, the biography as printed)
BIOS = [
    (9, 'Jovanović', 'Živorad', 'Žikica Španac', 'Rođen 1914. godine u Valjevu, Srbija. Student. Član KPJ od 1935. U NOB stupio 1941. godine. Poginuo 13. III 1942 u selu Radanovcu. Za narodnog heroja proglašen 6. VII 1945. godine.'),
    (23, 'Kluz', 'Franjo', '', 'Rođen 1913. godine u selu Jošik, Bosanska Dubica, Bosna i Hercegovina. Pilot. Član KPJ od 1942. U NOB stupio maja 1942. godine. Poginuo 14. IX 1944. kod Omiša. Za narodnog heroja proglašen 18. V 1948. godine.'),
    (35, 'Orešković', 'Marko', 'Krntija', 'Rođen 1895. godine u selu Široka Kula, Gospić, Hrvatska. Radnik. Član KPJ od 1925. U NOB stupio 1941. godine. Ubijen 20. X 1941. u selu Očijevu. Za narodnog heroja proglašen 26. VII 1945 godine.'),
    (48, 'Ćetković', 'Jelena', '', 'Rođena 1916. godine na Cetinju, Crna Gora. Radnica. Član KPJ od 1936. U NOB stupila 1941. godine. Streljana 15. V 1943. u Beogradu. Za narodnog heroja proglašena 5. VII 1952. godine.'),
    (58, 'Josifovski', 'Kuzman', 'Pitu', 'Rođen 1915. godine u Prilepu, Makedonija. Student. Član KPJ od 1938. U NOB stupio 1941. godine. Poginuo 25. II 1944. u Skoplju. Za narodnog heroja proglašen 3. VIII 1945. godine.'),
    (69, 'Destovnik', 'Karel', 'Kajuh', 'Rođen 1922. godine u Šoštanju, Celje, Slovenija. Đak. Član KPJ od 1940. U NOB stupio 1941. godine. Poginuo 22. II 1944. u selu Zavodnje. Za narodnog heroja proglašen 21. VII 1953. godine.'),
    (78, 'Pavlović', 'Drinka', '', 'Rođena 1919. godine u selu Belanovica, Lazarevac, Srbija. Učiteljica. Član KPJ od 1940. U NOB stupila 1941. godine. Streljana 14. V 1943. na Banjici. Za narodnog heroja proglašena 6. VII 1953. godine.'),
    (90, 'Mitrov', 'Danko', '', 'Rođen 1919. godine u selu Đurđevcu, Koprivnica, Hrvatska. Đak. Član KPJ od pre rata. U NOB stupio 1941. godine. Poginuo 1942. ispod Motajice. Za narodnog heroja proglašen 26. VII 1945. godine.'),
    (102, 'Sadik', 'Ramiz', '', 'Rođen 1915. godine u Peći, Kosmet, Srbija. Student prava. Član KPJ od 1936. U NOB stupio 1941. godine. Streljan 20. IV 1943. kod Landovice, blizu Prizrena. Za narodnog heroja proglašen 6. III 1945. godine.'),
    (102, 'Vukmirović', 'Bora', '', 'Rođen 1912. godine u Bregnovu, u Bugarskoj. Radnik. Član KPJ od 1933. U NOB stupio 1941. godine. Streljan 20. IV 1943 kod Landovice, blizu Prizrena. Za narodnog heroja proglašen 6. III 1945. godine.'),
    (114, 'Demonja', 'Nikola', '', 'Rođen 1919. godine u selu Vlahović, Glina, Hrvatska. Radnik. Član KPJ od 1941. U NOB stupio 1941. godine. Poginuo 6. IX 1944. u Slavonskoj Požegi. Za narodnog heroja proglašen 19. VI 1945. godine.'),
    (122, 'Zrenjanin', 'Žarko', '', 'Rođen 1902. godine u selu Izbištu, Vršac, Srbija. Učitelj. Član KPJ od 1927. U NOB stupio 1941. godine. Poginuo 5. XI 1942. u selu Pavlišu. Za narodnog heroja proglašen 25. XII 1944. godine.'),
    (132, 'Lukić', 'Veljko', 'Kurjak', 'Rođen 1917. godine u selu Donja Bukovica, Bijeljina, Bosna i Hercegovina. Zemljoradnik. Član KPJ. U NOB stupio 1941. godine. Poginuo aprila 1944. u Drinskom polju. Za narodnog heroja proglašen 12. I 1945. godine.'),
    (142, 'Bursać', 'Marija', '', 'Rođena 1924. godine u Kamenici, Drvar, Bosna i Hercegovina. Domaćica. Član KPJ od 1942. U NOB stupila 1941. godine. Podlegla ranama novembra 1943. Za narodnog heroja proglašena 15. X 1943. godine.'),
    (148, 'Čajavec', 'Rudi', '', 'Rođen 1911. godine u Zgošću, Kakanj, Bosna i Hercegovina. Pravnik. Član KPJ od pre rata. U NOB stupio 1941. godine. Poginuo 2. VII 1942. kod sela Klašnice blizu Banjaluke. Za narodnog heroja proglašen 20. XII 1951. godine.'),
    (161, 'Pavlović', 'Ratko', 'Ćićko', 'Rođen 1913. godine u selu Berilju, Prokuplje, Srbija. Pravnik. Član KPJ od pre rata. U NOB stupio 1941. godine. Poginuo 26. IV 1943. kod Strezimirovaca. Za narodnog heroja proglašen je 9. V 1945. godine.'),
    (170, 'Strugar', 'Đuro', '', 'Rođen 1912. godine u Gornjem Ceklinu, Rijeka Crnojevića, Crna Gora. Pravnik. Član KPJ od 1933. U NOB stupio 1941. godine. Ubijen 1941. u Beogradu. Za narodnog heroja proglašen 9. V 1945. godine.'),
    (178, 'Matijević', 'Miloš', 'Mrša', 'Rođen 1902. godine u selu Kestenovcu, Karlovac, Hrvatska. Radnik. Član KPJ od 1926. U NOB stupio 1941. godine. Ubijen 17. XII 1941. u Beogradu. Za narodnog heroja proglašen 16. VII 1951. godine.'),
    (190, 'Pravica', 'Dragica', '', 'Rođena 1919. godine u Mostaćima, Trebinje, Bosna i Hercegovina. Student. Član KPJ od pre rata. U NOB stupila 1941. godine. Streljana u leto 1942. u okolini Trebinja. Za narodnog heroja proglašena 8. VI 1945. godine.'),
    (197, 'Jović', 'Slobodan', '', 'Rođen 1918. godine u Kučevu, Požarevac, Srbija. Slovoslagač. Član KPJ od pre rata. U NOB stupio 1941. godine. Poginuo 29. VII 1944. u Beogradu. Za narodnog heroja proglašen 30. X 1946. godine.'),
    (197, 'Đonović', 'Branko', '', 'Rođen 1916. godine u selu Tomići, Bar, Crna Gora. Grafički radnik. Član KPJ od pre rata. U NOB stupio 1941. godine. Poginuo 29. VII 1944. u Beogradu. Za narodnog heroja proglašen 30. IV 1946. godine.'),
    (208, 'Petrov', 'Olga', '', 'Rođena 1921. godine u Barandi, Pančevo, Srbija. Učiteljica. Član KPJ od 1940. U NOB stupila 1941. godine. Streljana 9. V 1942. Za narodnog heroja proglašena 27. XI 1953. godine.'),
    (228, 'Dovadžija', 'Mustafa', '', 'Rođen 1921. godine u Sarajevu, Bosna i Hercegovina. Bravarski radnik. Član KPJ od 1941. U NOB stupio 1941. godine. Ubijen maja 1942. kod Stublina. Za narodnog heroja proglašen 5. VII 1951. godine.'),
    (235, 'Karamandi', 'Elpida', '', 'Rođena 1920. godine u Lerinu, Jegejska Makedonija. Student. Član KPJ od 1941. U NOB stupila 1941. godine. Ubijena 1942. kod sela Salci Bitoljsko. Za narodnog heroja proglašena 6. X 1951. godine.'),
    (242, 'Jovičić', 'Olga', 'Rita', 'Rođena 1920. godine u Kraljevu, Srbija. Student. Član KPJ od 1940. U NOB stupila 1941. godine. Poginula 1943. u selu Duge kod Prozora. Za narodnog heroja proglašena 20. XII 1951. godine.'),
    (251, 'Milovanović', 'Miodrag', 'Lune', 'Rođen 1921. godine u Dobrodolu, Titovo Užice, Srbija. Đak. Član KPJ od 1941. U NOB stupio 1941. godine. Poginuo aprila 1944. nedaleko od svog sela. Za narodnog heroja proglašen 20. V 1944. godine.'),
    (262, 'Srnić', 'Dragoslav', 'Padobranac', 'Rođen 1914. godine u selu Draginje, Šabac, Srbija. Grafički radnik. Član KPJ od 1939. U NOB stupio 1941. godine. Poginuo septembra 1941. u okolini Šapca. Za narodnog heroja proglašen 7. VII 1953. godine.'),
    (270, 'Stamenković', 'Trajko', '', 'Rođen 1909. godine u Leskovcu, Srbija. Student. Član KPJ od 1928. U NOB stupio 1941. godine. Streljan krajem 1942. na Banjici. Za narodnog heroja proglašen 14. XII 1949. godine.'),
    (277, 'Dimić', 'Nada', '', 'Rođena 1923. godine u Divoselu, Gospić, Hrvatska. Tekstilna radnica. Član KPJ od 1940. U NOB stupila 1941. godine. Ubijena marta 1942. u ustaškom logoru Stara Gradiška. Za narodnog heroja proglašena 5. VII 1951. godine.'),
    (286, 'Naumov', 'Stefan', 'Stiv', 'Rođen 1920. godine u Lepenskom, Jegejska Makedonija. Student. Član KPJ od 1939. U NOB stupio 1941. godine. Poginuo septembra 1942. kod sela Bolno. Za narodnog heroja proglašen 29. VII 1945. godine.'),
    (294, 'Tomović', 'Budimir', 'Budo', 'Rođen 1914. godine na Cetinju, Crna Gora. Student. Član KPJ od 1935. U NOB stupio 1941. godine. Poginuo 1942. kod Crkvina blizu Kolašina. Za narodnog heroja proglašen 11. VII 1945. godine.'),
    (300, 'Nešić', 'Ljubomir', '', 'Rođen 1918. godine u Zaječaru, Srbija. Student. Član KPJ od 1939. U NOB stupio 1941. godine. Poginuo septembra 1941. kod Salaša. Za narodnog heroja proglašen 14. XII 1949. godine.'),
]


def main():
    entries = []
    for n, (page, last, first, nick, bio) in enumerate(BIOS, 1):
        born = re.match(r'Rođena?\s+(1[89]\d\d)\.\s*godine\s+(?:u|na)\s+(?:selu\s+)?([^.]+)\.', bio)
        death = re.search(r'(?:Poginu(?:o|la)|Ubijen[a]?|Streljan[a]?|Podlegla ranama)[^.]*?(?:\.\s*[IVX]+\s*)?[^.]*?\b(19[34]\d)\b', bio)
        if not death:
            death = re.search(r'(?:Poginu(?:o|la)|Ubijen[a]?|Streljan[a]?|Podlegla)\D*?(?:\d{1,2}\.\s*[IVX]+\s*)?(19[34]\d)', bio)
        entries.append({'soldier_id': f'{PREFIX}{n:06d}', 'name': f'{last} {first}' + (f' – {nick}' if nick else ''),
                        'last_name': last, 'first_name': first, 'nick': nick, 'fathers_name': '',
                        'birth_year': born.group(1) if born else '', 'born_in': born.group(2) if born else '',
                        'death_year': death.group(1) if death else '', 'survived': False, 'additional_info': bio,
                        'source_url': VIEWER_URL.format(id=DOC, page=page), 'source_page': page - OFFSET})
    OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(entries)} heroes; birth year {sum(1 for e in entries if e["birth_year"])}, '
          f'death year {sum(1 for e in entries if e["death_year"])}')
    for e in entries:
        print(f"  {e['soldier_id']} {e['name']:40} b. {e['birth_year']} {e['born_in'][:35]:35} d. {e['death_year']}")


if __name__ == '__main__':
    main()
