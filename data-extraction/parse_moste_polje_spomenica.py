"""
*Zbornik občine Ljubljana Moste-Polje* (znaci.org 00003/1103, the whole book's PDF pp. 51-54 →
website/public/pdfs/moste-polje-spomenica-1941.pdf): "Nosilci Partizanske spomenice 1941" (book pp. 257-260), the 209
holders of the spomenica from the area of today's Moste-Polje (Ljubljana), from the archive of the CK ZKS. A book across
units: its entries are added to the records of the soldiers it describes (scripts/match_references.py), the rest go to
Ostali borci.

Two columns, numbered, each entry hanging: "1. Aleš-Ščurk Frančiška, 1912 — uradnica — umrla l. 1957". The book's
note: the surname (for some women the maiden name too), the given name, the year of birth and the trade, and the year of
death of those who died since. The text layer is too garbled to read ("Ba1rešič-Moj,škerc", "Oeirar"), so the entries
are typed from the page images (ENTRIES); the layer gives each entry's place by its number. A holder of the spomenica
lived through the war, so every entry is `survived` (the year of a later death is `died_after`).

Output: data-extraction/znaci/moste-polje-spomenica-1941-entries.json (IDs 9044xxxxxx, by the book's number).
Usage: python data-extraction/parse_moste_polje_spomenica.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry_boxes  # noqa: E402

PDF = 'moste-polje-spomenica-1941.pdf'
OUT = HERE / 'znaci' / 'moste-polje-spomenica-1941-entries.json'
PREFIX = '9044'
TITLE = 'Nosilci Partizanske spomenice 1941, Moste-Polje'

# as printed; "—" parts: the year of birth, the trade, a later death
ENTRIES = """
1. Aleš-Ščurk Frančiška, 1912 — uradnica — umrla l. 1957
2. Alič Franc, 1906 — strojnik — umrl l. 1965
3. Alič Milan, 1922 — mizar
4. Anžur Anton, 1913 — zidar
5. Arnejšek Boris, 1921 — ključavničar
6. Arnejšek Dušan, 1925 — soboslikar
7. Babnik Anton, 1892 — delavec
8. Babnik Anton, 1911 — kovač
9. Babnik Stane, 1921 — monter
10. Barešič-Mojškerc Marija, 1923 — kmečka delavka
11. Becele Janez, 1912 — mizar
12. Belšak Maks, 1922 — pleskar
13. Benedik Ivan, 1923 — kolar
14. Berčič Miha, 1911 — delavec
15. Bergant-Polak Juga, 1918 — študentka medicine
16. Bergman Marija, 1922 — uradnica
17. Bežan Ivica, 1923 — delavka
18. Bežan Miroslav, 1921 — železniški uslužbenec
19. Bobnar Ana, 1926 — dijakinja
20. Bobnar Stane, 1912 — delavec
21. Bradaškja Rastko, 1917 — novinar
22. Bratko Ivan, 1914 — publicist
23. Breznik Jože, 1914 — delavec
24. Cerar Anton, 1914 — mizar
25. Cerar Franc, 1909 — kmet
26. Cibic Leon, 1923 — študent
27. Cimerman Vinko, 1921 — trgovski pomočnik
28. Čepeljnik Franc, 1883 — strojevodja drž. žel. — umrl l. 1963
29. Čermelj Peter, 1900 — delavec
30. Černe Franc, 1898 — delavec — umrl l. 1955
31. Černe Karel, 1904 — čevljar
32. Černivec Marija, 1919 — delavka — umrla l. 1962
33. Dežman Anton, 1904 — delavec
34. Dežman Lucija, 1904 — gospodinja
35. Dimnik Anton, 1921 — trgovski pomočnik
36. Dimnik Frančiška, 1904 — gospodinja
37. Dimnik Karel, 1924 — brivski vajenec
38. Dobrovoljc Elidija, 1924 — dijakinja
39. Dolčič Emil, 1920 — delavec
40. Dolinšek Tone, 1910 — železostrugar
41. Drglin Anton, 1919 — zidar
42. Farčnik Avgust, 1911 — trgovski pomočnik
43. Ferfila Ignac, 1909 — kovač — umrl l. 1952
44. Ferlež Ivan, 1920 — delavec
45. Gašperšič Gabrijel, 1923 — delavec
46. Gomzi Sonja, 1922 — študentka
47. Gornik Gojko, 1925 — dijak
48. Grčar Edvard, 1902 — delavec
49. Gregorčič dr. Rihard, 1904 — zdravnik
50. Grum Anton, 1923 — tesar
51. Grum Karel, 1920 — tesar
52. Habič Ana, 1921 — kmečka del.
53. Habič Jože, 1915 — kmet
54. Harmel Milan, 1905 — uradnik
55. Hočevar Anton, 1912 — delavec
56. Hribar Janez, 1918 — vodovodni instalater
57. Ivanuš Branko, 1919 — gradbeni tehnik — umrl l. 1955
58. Ivanuš Heda, 1923 — študentka
59. Jager Jože, 1918 — zidar
60. Jakhel Jože, 1923 — delavec
61. Jereb Karel, 1903 — kurjač
62. Jeriha Pavel, 1922 — dijak
63. Jernejc Franc, 1915 — mesarski pomočnik
64. Jernejc Franc, 1922 — strojni ključavničar
65. Kačar Jože, 1897 — mizar
66. Kanoni dr. Janez, 1904 — zdravnik
67. Kardelj-Maček Pepca, 1914 — delavka
68. Kasum Tomo, 1913 — brivski pomočnik
69. Kašper Jože, 1922 — ključavničar
70. Keber Stane, 1918 — delavec
71. Klavs inž. Vladimir, 1919 — študent
72. Klešnik Kazimir, 1921 — delavec
73. Klešnik Roman, 1910 — železničar
74. Kocjančič Anton, 1922 — delavec
75. Kocjančič Janez, 1925 — ključavničar
76. Kocjančič Jože, 1917 — zidar
77. Kogej Marija, 1924 — dijakinja
78. Kogej Vasja, 1924 — študent
79. Kogoj Ivica, 1926 — študentka
80. Kogoj Marija, 1903 — gospodinja
81. Kogoj Vladimir, 1923 — ključavničar
82. Kokalj Stane, 1897 — šofer
83. Kokalj Stanko, 1923 — električar
84. Komel-Škrk Nada, 1922 — fotografska vajenka
85. Kompare Ferdinand, 1908 — delavec
86. Kompare Jože, 1916 — delavec — umrl l. 1963
87. Kopač Jože, 1920 — strojni ključ.
88. Kopač-Šerbak Zora, 1913 — učiteljica
89. Kotar Alojz, 1906 — delavec
90. Kovačič inž. Božo, 1920 — študent
91. Kralj Franc, 1908 — delavec
92. Kregar Avgust, 1889 — sadjar, perutninar
93. Krmec Metod, 1909 — zidar
94. Kukavica Ludvik, 1908 — zidar
95. Kumše Franc, 1903 — čevljar
96. Kušar Miha, 1920 — mizar
97. Kušljan Marička, 1914 — delavka — umrla l. 1957
98. Leskošek Franc, 1897 — strugar
99. Leskošek Marija, 1899 — gospodinja — umrla l. 1965
100. Lovše Andrej, 1910 — delavec
101. Lovše Terezija, 1913 — gospodinja
102. Lozej Zdravko, 1919 — delavec
103. Maček Ivan, 1908 — delavec
104. Maček Leopold, 1901 — delavec
105. Maček Leopold, 1928 — dijak
106. Maček Roza, 1905 — gospodinja
107. Maček Tilka, 1909 — delavka
108. Mahnič Mirko, 1913 — mizar
109. Majerič Martin, 1921 — krojaški pomočnik
110. Majeršič Albin, 1918 — stavbeni ključavničar
111. Majeršič Maks, 1901 — železničar — umrl l. 1959
112. Makuc-Tavčar Marija, 1924 — modistka
113. Marinko Valentin, 1912 — mehanik mojster
114. Martinčič Jože, 1912 — delavec
115. Matul Janez, 1907 — električar
116. Mazovec Franc, 1910 — mesar
117. Mazovec Lado, 1925 — delavec
118. Mekinda Jože, 1922 — študent — umrl l. 1963
119. Menard Maks, 1922 — dijak — umrl l. 1956
120. Meze Davorina, 1926 — dijakinja
121. Mojškerc Franc, 1920 — pleskar — umrl l. 1948
122. Mojškerc Jakob, 1918 — zidar
123. Mojškerc Vinko, 1921 — monter
124. Novak Stane, 1922 — delavec
125. Nusdorfer Alojz, 1910 — delavec — umrl l. 1952
126. Ocepek-Dovč Angela, 1912 — delavka — umrla leta 1959
127. Okretič-Kampos Zorka, 1924 — uradnica
128. Omahen Ivan, 1924 — tapetniški vajenec — umrl l. 1962
129. Omahen Jože, 1900 — železničar
130. Omahen Lovro, 1898 — delavec
131. Omejc Terezija, 1914 — delavka
132. Osenjak Francka, 1901 — delavka
133. Pangeršič Janez, 1898 — železniški prometnik
134. Pavličič Jože, 1916 — pravnik
135. Pavšič Štefan, 1910 — trgovski pomočnik
136. Pečnikar Jože, 1925 — delavec
137. Peršič Bogomir, 1914 — profesor
138. Peršič Zorka, 1914 — profesorica
139. Pogačnik Vili, 1909 — delavec
140. Pokovec Franc, 1921 — kovinobrusač
141. Polk Albin, 1918 — mizar
142. Porenta Valentin, 1909 — ključavničar
143. Prešeren-Maček Cilka, 1918 — delavka
144. Prošek Leopold, 1920 — instalater
145. Prusnik Anton, 1921 — delavec
146. Puhar Rudi, 1921 — uslužbenec
147. Rakušček Zdravko, 1921 — klepar
148. Rode Venceslav, 1921 — mesarski vajenec
149. Rojc Ana, 1914 — delavka
150. Rojšek Franc, 1914 — kmečki del.
151. Rojšek Ivan, 1908 — tesar
152. Rozman Pavel, 1922 — steklobrusač
153. Rozman Viktor, 1905 — strojni ključavničar
154. Sajevic-Baš Mara, 1916 — šivilja
155. Sigulin Anton, 1917 — študent
156. Simčič Marjan, 1909 — pravnik
157. Simonič Štefan, 1915 — delavec
158. Smrekar Fani, 1917 — delavka
159. Smrekar Ludvik, 1918 — električar
160. Snoj Ivan, 1924 — ključavničar
161. Snoj Rudolf, 1924 — soboslikarski vajenec
162. Sotlar Franc, 1919 — delavec
163. Srakar Marjan, 1921 — trgovski pomočnik
164. Stare Ivan, 1913 — želez. zavirač
165. Stibrič Zdravko, 1924 — delavec
166. Stopar Viktor, 1913 — strojni ključavničar
167. Stopar Vlado, 1919 — mehanik, delavec
168. Stražar Ivo, 1921 — mehanik, šofer
169. Strle Franc, 1907 — čevljarski mojster
170. Strle Marija, 1909 — gospodinja
171. Svetek Ivan, 1921 — krojaški pomočnik
172. Šavelj dr. Marta, 1917 — študentka medicine
173. Šegvič-Lukec Anica, 1921 — delavka, šivilja
174. Šircelj Ivan, 1921 — delavec
175. Šlambergar Vili, 1910 — delavec
176. Štrumelj Karel, 1909 — ključavničar
177. Tabernik Karel, 1911 — delavec
178. Taufer Karel, 1919 — študent
179. Taurer Franc, 1910 — galvanizer
180. Taurer Henrik, 1913 — brivski mojster
181. Tavčar Ančka, 1922 — kmečka delavka
182. Tavčar Franc, 1920 — študent
183. Tratnik Jovan, 1921 — elektromehanik
184. Trošt Rado, 1922 — dijak
185. Trtnik Alojz, 1922 — delavec
186. Trtnik Alojz, 1917 — soboslikar
187. Trtnik Anton, 1923 — delavec
188. Trtnik Bogomir, 1925 — delavec
189. Učakar Marjan, 1921 — steklarski pomočnik
190. Valič-Klanjšek Dana, 1922 — dijakinja učiteljišča
191. Verbič Alojz, 1912 — brivski mojster
192. Vidergar Anton, 1919 — soboslikar
193. Vidergar Avgust, 1914 — mehanik
194. Vidergar Franc, 1908 — delavec
195. Vidergar Rudolf, 1923 — mehanik
196. Vodnik Jože, 1913 — železniški uslužbenec
197. Vovk-Lampič Minka, 1925 — šiviljska vajenka
198. Zabukovec Milan, 1923 — strojni ključavničar
199. Zadravec Dušan, 1912 — šofer
200. Zajc Slavko, 1923 — mizar
201. Zajec Ivan, 1922 — kmečki del.
202. Zajic Milica, 1913 — gospodinja
203. Završnik Miroslav, 1921 — železničar
204. Zdešar Franc, 1911 — zidar — umrl l. 1953
205. Zgonc-Hajek Nada, 1920 — knjigoveška delavka
206. Zupančič Anton, 1910 — klepar
207. Zupančič Stane, 1912 — kmet
208. Židan Stane, 1915 — zidar
209. Žugelj Franc, 1919 — študent
"""


def typed() -> list[dict]:
    out = []
    for ln in ENTRIES.strip().splitlines():
        m = re.match(r'^(\d+)\.\s+(.+?),\s+(\d{4})\s+—\s+(.+)$', ln)
        assert m, ln
        no, name, year, rest = int(m.group(1)), m.group(2), m.group(3), m.group(4)
        died = re.search(r'\s+—\s+umrla?\s+(?:l\.|leta)\s+(\d{4})$', rest)
        trade = rest[:died.start()] if died else rest
        out.append({'no': no, 'printed': ln.split('. ', 1)[1], 'name': name, 'year': year, 'trade': trade.strip(),
                    'died': died.group(1) if died else ''})
    assert [e['no'] for e in out] == list(range(1, 210))
    return out


def places() -> dict[int, tuple]:
    """each number's place on the page: the text layer's "12." at a line's start (its "l." is 1, "2GO" a page number)"""
    found = {}
    with pdfplumber.open(HERE.parent / 'website' / 'public' / 'pdfs' / PDF) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            for col in entry_boxes.read_page(page, 2, False, entry_boxes.GUTTER.get((PDF, pno)))['columns']:
                for ln in col:
                    m = re.match(r'^([0-9lI]{1,3})\s*[.,]?\s+[A-ZČŠŽ]', ln['text'].strip())
                    if not m:
                        continue
                    no = int(m.group(1).replace('l', '1').replace('I', '1'))
                    if 1 <= no <= 209 and no not in found:
                        found[no] = (pno, round(ln['x0'], 1), round(ln['top'], 1))
    return found


def split_name(name: str) -> tuple[str, str, list[str], str]:
    """(surname as printed, given name, other surnames to try, title): "Barešič-Mojškerc Marija", "Klavs inž. Vladimir" """
    title = ''
    m = re.search(r'\s(dr\.|inž\.)\s', f' {name} ')
    if m:
        title, name = m.group(1), re.sub(r'\s(?:dr\.|inž\.)\s', ' ', f' {name} ').strip()
    last, given = name.split(' ', 1)
    also = last.split('-') if '-' in last else []
    return last, given, also, title


def main():
    ents, found = typed(), places()
    missing = [e['no'] for e in ents if e['no'] not in found]
    recs = []
    for e in ents:
        last, given, also, title = split_name(e['name'])
        if e['no'] in found:
            pno, x, y = found[e['no']]
        else:                                   # between its neighbours in the same column
            prev = max((n for n in found if n < e['no']), default=None)
            pno, x, y = found[prev][0], found[prev][1], found[prev][2] + 10.5 * (e['no'] - prev)
        died = f", umrl{'a' if e['printed'].split(' — ')[-1].startswith('umrla') else ''} {e['died']}" if e['died'] else ''
        recs.append({
            'soldier_id': f"{PREFIX}{e['no']:06d}", 'name': f'{last} {given}', 'last_name': last, 'first_name': given,
            'also': also, 'nick': '', 'fathers_name': '', 'birth_year': e['year'], 'born_in': '', 'death_year': '',
            'death_date': '', 'survived': True, 'died_after': e['died'], 'units': [], 'no': e['no'],
            'list': TITLE,
            'additional_info': f"{TITLE}: {e['no']}. {e['printed']}.",
            'pdf_file': PDF, 'pdf_page': pno, 'pdf_x': x, 'pdf_y': y})
    stats = entry_boxes.fill_boxes(recs)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(recs)} entries -> {OUT.relative_to(HERE.parent)}; placed by the text layer: {len(recs) - len(missing)}, '
          f'estimated: {missing}')
    print(f"boxes: {entry_boxes.describe(stats, stats['boxed'])}")


if __name__ == '__main__':
    main()
