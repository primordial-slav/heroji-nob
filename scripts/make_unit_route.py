"""A unit's way through the war, for the map page (/mapa): its route, and where its fighters fell.

- The route: dated waypoints written out below from the unit's own history (for Prva proleterska: Miloš
  Vuksanović's monograph, 1981), checked month by month against where the unit's fallen died. Each waypoint is
  placed by GeoNames, the place of that name nearest the rough position given here.
- The fallen: every record of one killed (death_type poginuo) with a place and a date, placed by GeoNames too. A
  village's name is common, so the candidate is the one nearest the municipality the entry names ("Šarengrad, Vukovar"), or else nearest
  where the route has the unit that month; names in the locative or genitive ("u Vitovlju", "kod Turbeta") are
  read back to the nominative.

GeoNames (CC BY 4.0) country files are cached in data-extraction/.cache/map1941/geonames/.
Writes website/app/(sr)/mapa/units/<unit>.ts, in the map's units (the projection in map1941.ts).

Usage: python scripts/make_unit_route.py [--samples]
"""
import collections
import json
import math
import re
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_map_1941 import Projection  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GEONAMES = ROOT / 'data-extraction' / '.cache' / 'map1941' / 'geonames'
MAPA = ROOT / 'website' / 'app' / '(sr)' / 'mapa'
COUNTRIES = ['BA', 'HR', 'RS', 'ME', 'XK', 'MK', 'SI']

# date, place (as GeoNames knows it), rough lon/lat, the event as the map's legend gives it (the map numbers
# it), kind. From the brigade's monograph (Miloš Vuksanović, Prva proleterska brigada, 1981; znaci.org 00003/382):
# the dates and places its chapters give, checked against where the brigade's fallen died, month by month
PRVA_PROLETERSKA = [
    ('1941-12-21', 'Rudo', 19.37, 43.62, 'Rudo, 21. XII 1941: osnovana', 'formed'),
    ('1942-01-21', 'Pjenovac', 18.84, 44.08, 'Pjenovac, 21. I 1942: nemačka ofanziva u istočnoj Bosni', 'battle'),
    ('1942-01-28', 'Igman', 18.25, 43.75, 'Igman, 28. I 1942: Igmanski marš', 'stop'),
    ('1942-02-05', 'Trnovo', 18.45, 43.67, None, 'stop'),
    ('1942-02-20', 'Foča', 18.78, 43.51, None, 'stop'),
    ('1942-03-15', 'Vlasenica', 18.94, 44.18, 'Vlasenica, III 1942: razbijanje četnika u istočnoj Bosni', 'battle'),
    ('1942-04-05', 'Rogatica', 19.00, 43.80, None, 'battle'),
    ('1942-04-20', 'Foča', 18.78, 43.51, None, 'stop'),
    ('1942-05-17', 'Mratinje', 18.80, 43.27, None, 'stop'),
    ('1942-05-28', 'Nevesinje', 18.11, 43.26, None, 'battle'),
    ('1942-06-12', 'Gat', 18.60, 43.07, 'Gat, 12. VI 1942: napad na četnike', 'battle'),
    ('1942-06-16', 'Čemerno', 18.60, 43.24, None, 'stop'),
    ('1942-06-24', 'Zelengora', 18.58, 43.33, 'Zelengora, 24. VI 1942: pohod u Bosansku krajinu', 'stop'),
    ('1942-07-04', 'Bradina', 18.03, 43.72, None, 'battle'),
    ('1942-07-08', 'Konjic', 17.96, 43.65, 'Konjic, 8. VII 1942: oslobođenje Konjica', 'battle'),
    ('1942-07-14', 'Prozor', 17.61, 43.82, None, 'stop'),
    ('1942-07-25', 'Duvno', 17.23, 43.72, None, 'battle'),
    ('1942-08-01', 'Šujica', 17.17, 43.83, None, 'battle'),
    ('1942-08-07', 'Livno', 17.01, 43.83, 'Livno, 7. VIII 1942: oslobođenje Livna', 'battle'),
    ('1942-08-16', 'Posušje', 17.33, 43.47, 'Posušje, 16. VIII 1942: prodor u Dalmaciju', 'battle'),
    ('1942-08-20', 'Aržano', 17.00, 43.58, None, 'battle'),
    ('1942-09-04', 'Kupres', 17.28, 43.99, None, 'stop'),
    ('1942-09-17', 'Bosansko Grahovo', 16.36, 44.18, None, 'stop'),
    ('1942-10-07', 'Ključ', 16.78, 44.53, 'Ključ, 7. X 1942: oslobođenje Ključa', 'battle'),
    ('1942-10-27', 'Bosansko Grahovo', 16.36, 44.18, None, 'battle'),
    ('1942-11-07', 'Bosanski Petrovac', 16.37, 44.55, 'Bosanski Petrovac, 7. XI 1942: ratna zastava', 'stop'),
    ('1942-11-20', 'Sitnica', 16.95, 44.45, None, 'battle'),
    ('1942-11-26', 'Jajce', 17.27, 44.34, 'Jajce, XI 1942: oslobođenje Jajca', 'battle'),
    ('1942-12-15', 'Kotor Varoš', 17.37, 44.62, None, 'stop'),
    ('1943-01-10', 'Teslić', 17.86, 44.61, None, 'stop'),
    ('1943-01-16', 'Prnjavor', 17.66, 44.87, 'Prnjavor, I 1943: oslobođenje Prnjavora', 'battle'),
    ('1943-02-02', 'Šiprage', 17.56, 44.47, None, 'stop'),
    ('1943-02-07', 'Gračanica', 17.49, 44.00, None, 'stop'),
    ('1943-02-17', 'Repovci', 17.97, 43.76, None, 'stop'),
    ('1943-02-18', 'Ivan Sedlo', 18.03, 43.76, 'Ivan-sedlo, 17–28. II 1943: borbe na pruzi Sarajevo–Konjic', 'battle'),
    ('1943-03-04', 'Gornji Vakuf', 17.59, 43.94, 'Gornji Vakuf, 3–5. III 1943: protivudar', 'battle'),
    ('1943-03-08', 'Jablanica', 17.76, 43.66, 'Jablanica, 8. III 1943: prelaz Neretve', 'stop'),
    ('1943-03-16', 'Glavatičevo', 18.07, 43.50, None, 'battle'),
    ('1943-03-21', 'Ulog', 18.31, 43.42, None, 'battle'),
    ('1943-03-23', 'Kalinovik', 18.45, 43.50, None, 'stop'),
    ('1943-04-09', 'Ustikolina', 18.79, 43.58, 'Ustikolina, IV 1943: prelaz Drine', 'battle'),
    ('1943-04-25', 'Goražde', 18.98, 43.67, None, 'battle'),
    ('1943-05-10', 'Bijelo Polje', 19.75, 43.04, 'Bijelo Polje, V 1943: uništenje italijanske kolone', 'battle'),
    ('1943-05-15', 'Šahovići', 19.64, 43.06, None, 'stop'),
    ('1943-05-22', 'Čelebići', 18.92, 43.38, None, 'battle'),
    ('1943-06-05', 'Tjentište', 18.69, 43.35, 'Sutjeska, V–VI 1943: bitka na Sutjesci', 'battle'),
    ('1943-06-10', 'Balinovac', 18.55, 43.37, 'Balinovac, 9–10. VI 1943: proboj na Zelengori', 'battle'),
    ('1943-06-13', 'Miljevina', 18.65, 43.52, None, 'battle'),
    ('1943-06-25', 'Vlasenica', 18.94, 44.18, None, 'battle'),
    ('1943-06-28', 'Drinjača', 19.15, 44.29, None, 'battle'),
    ('1943-07-05', 'Zvornik', 19.10, 44.39, 'Zvornik, 4–5. VII 1943: oslobođenje Zvornika', 'battle'),
    ('1943-07-19', 'Žepa', 19.13, 43.95, None, 'stop'),
    ('1943-07-31', 'Nemila', 17.92, 44.33, None, 'stop'),
    ('1943-08-04', 'Petrovo Polje', 17.56, 44.40, None, 'stop'),
    ('1943-08-21', 'Šiprage', 17.56, 44.47, None, 'stop'),
    ('1943-09-01', 'Turbe', 17.57, 44.24, None, 'battle'),
    ('1943-09-14', 'Duvno', 17.23, 43.72, None, 'stop'),
    ('1943-09-18', 'Omiš', 16.69, 43.44, None, 'battle'),
    ('1943-09-22', 'Trilj', 16.72, 43.62, 'Dalmacija, IX 1943: posle kapitulacije Italije', 'battle'),
    ('1943-09-25', 'Aržano', 17.00, 43.58, None, 'battle'),
    ('1943-10-20', 'Travnik', 17.67, 44.23, 'Travnik, X 1943 – IV 1944: borbe u centralnoj Bosni', 'battle'),
    ('1943-12-15', 'Šujica', 17.17, 43.83, None, 'battle'),
    ('1944-01-10', 'Travnik', 17.67, 44.23, None, 'battle'),
    ('1944-04-11', 'Jajce', 17.27, 44.34, None, 'battle'),
    ('1944-04-20', 'Mrkonjić Grad', 17.08, 44.42, None, 'battle'),
    ('1944-05-28', 'Mlinište', 16.88, 44.20, 'Mlinište, 27/28. V 1944: Drvarska operacija', 'battle'),
    ('1944-06-01', 'Glamoč', 16.85, 44.05, None, 'stop'),
    ('1944-06-04', 'Kupres', 17.28, 43.99, None, 'stop'),
    ('1944-06-15', 'Vranica', 17.75, 43.95, None, 'battle'),
    ('1944-06-28', 'Hranisava', 18.14, 43.73, None, 'stop'),
    ('1944-07-04', 'Foča', 18.78, 43.51, None, 'stop'),
    ('1944-07-06', 'Boljanići', 19.21, 43.45, None, 'stop'),
    ('1944-07-25', 'Pljevlja', 19.36, 43.36, None, 'stop'),
    ('1944-08-25', 'Palisad', 19.70, 43.72, 'Palisad, VIII 1944: prodor u Srbiju', 'battle'),
    ('1944-09-08', 'Bajina Bašta', 19.57, 43.97, None, 'battle'),
    ('1944-09-15', 'Valjevo', 19.89, 44.27, 'Valjevo, 14–17. IX 1944: oslobođenje Valjeva', 'battle'),
    ('1944-09-25', 'Ub', 20.07, 44.46, None, 'battle'),
    ('1944-10-08', 'Lazarevac', 20.26, 44.38, None, 'stop'),
    ('1944-10-11', 'Kosmaj', 20.56, 44.47, None, 'stop'),
    ('1944-10-16', 'Beograd', 20.46, 44.82, 'Beograd, 15–20. X 1944: oslobođenje Beograda', 'battle'),
    ('1944-11-26', 'Stara Pazova', 20.16, 44.99, None, 'stop'),
    ('1944-12-15', 'Šid', 19.23, 45.13, 'Šid, XII 1944 – IV 1945: Sremski front', 'battle'),
    ('1945-04-12', 'Šarengrad', 19.30, 45.23, 'Šarengrad, 12. IV 1945: proboj Sremskog fronta', 'battle'),
    ('1945-04-14', 'Đakovo', 18.41, 45.31, None, 'stop'),
    ('1945-04-19', 'Pleternica', 17.81, 45.29, None, 'battle'),
    ('1945-04-24', 'Nova Gradiška', 17.38, 45.26, None, 'stop'),
    ('1945-04-27', 'Novi Grabovac', 17.00, 45.40, 'Novi Grabovac, 27. IV 1945: borba kod Novske', 'battle'),
    ('1945-04-29', 'Lipik', 17.15, 45.41, None, 'stop'),
    ('1945-05-02', 'Pavlovac', 17.05, 45.72, None, 'stop'),
    ('1945-05-03', 'Čazma', 16.62, 45.75, None, 'stop'),
    ('1945-05-04', 'Dubrava', 16.54, 45.84, None, 'battle'),
    ('1945-05-06', 'Vrbovec', 16.42, 45.88, 'Vrbovec, 5–6. V 1945: borba za Vrbovec', 'battle'),
    ('1945-05-09', 'Zagreb', 15.98, 45.81, 'Zagreb, 9. V 1945: ulazak u Zagreb', 'end'),
]

# What happened at each numbered event, for the card the map opens on it: a few plain sentences from the monograph,
# by the waypoint's date
PRVA_PROLETERSKA_ABOUT = {
    '1941-12-21': 'Brigada je osnovana u Rudom od četiri bataljona iz Srbije i dva iz Crne Gore. Na dan osnivanja '
                  'imala je 1.196 boraca, od toga 71 ženu. Komandant je bio Koča Popović, politički komesar Filip '
                  'Kljajić Fića.',
    '1942-01-21': 'U januarskoj ofanzivi Nemaca u istočnoj Bosni brigada se borila na Romaniji. Na Pjenovcu su '
                  '21. januara nemački skijaši i konjica iznenadili Peti bataljon i delove Romanijskog odreda.',
    '1942-01-28': 'Brigada je prešla Igman 28. januara 1942, po snegu i na temperaturi od oko −30 °C. Mnogi borci su '
                  'promrzli i lečeni su posle u Foči, gde je bio Vrhovni štab.',
    '1942-03-15': 'U martu 1942. tri bataljona brigade vratila su se u istočnu Bosnu. Sa Birčanskim i Majevičkim '
                  'odredom razbili su četnike i oslobodili Miliće, Vlasenicu, Drinjaču, Srebrenicu i Bratunac.',
    '1942-06-12': 'Iz Mratinja na Pivi glavnina brigade krenula je 18. maja u severnu Hercegovinu, gde je razbijala '
                  'četnike. Napad na četnike u Gatu, 12. juna, nije uspeo, pa se brigada povukla preko Čemerna i '
                  'Lebršnika na Zelengoru.',
    '1942-06-24': 'Pokret sa Zelengore počeo je 24. juna 1942. Sa grupom proleterskih brigada i Vrhovnim štabom '
                  'brigada je krenula na zapad, ka Bosanskoj krajini.',
    '1942-07-08': 'Početkom jula brigade su rušile prugu i cestu Sarajevo–Konjic. Prva proleterska napala je Konjic '
                  '8. jula u dva časa i oslobodila ga.',
    '1942-08-07': 'Posle Prozora, Šćita i Duvna brigada je sa Trećom sandžačkom napala Livno. Grad je oslobođen '
                  '7. avgusta oko 9 časova; zarobljeno je oko 400 domobrana, 250 ustaša i 7 Nemaca.',
    '1942-08-16': 'Drugi, Četvrti i Šesti bataljon prodrli su prema Dalmaciji. Posušje je oslobođeno 16. avgusta, a '
                  '17. avgusta Drugi bataljon je ušao u Lovreć. Od 20. avgusta odbijali su napade italijanske divizije '
                  '„Bergamo“.',
    '1942-10-07': 'Napad na Ključ počeo je noću 3. oktobra. Posle dva neuspela napada brigada je varkom zauzela grad, u '
                  'zoru 7. oktobra. Krajem oktobra napadala je Bosansko Grahovo.',
    '1942-11-07': 'Brigada se početkom novembra okupila kod Bosanskog Petrovca i na praznik 7. novembra primila ratnu '
                  'zastavu. Od 1. novembra bila je u sastavu Prve proleterske divizije, sa Trećom sandžačkom i Trećom '
                  'krajiškom brigadom.',
    '1942-11-26': 'Brigada je 16. novembra krenula iz Petrovca i napala Sitnicu, a noću 23/24. novembra krenula je ka '
                  'Jajcu i učestvovala u njegovom oslobođenju. U decembru je razbijala četnike u centralnoj Bosni.',
    '1943-01-16': 'U decembru 1942. brigada je presekla cestu Banja Luka–Prnjavor. U januaru 1943. ponovo se borila oko '
                  'Teslića, a zatim oslobodila Prnjavor i prodrla ka Savi.',
    '1943-02-18': 'U Četvrtoj ofanzivi brigada je krenula iz centralne Bosne 30. januara, preko Ugra i planina Vranice, '
                  'Zeca i Bitovnje. Pred zoru 17. februara izbila je u Repovce, a do 28. februara vodila teške borbe '
                  'na Ivan-sedlu, kod Bradine i Tarčina.',
    '1943-03-04': 'Brigada je učestvovala u protivudaru kod Gornjeg Vakufa, od 3. do 5. marta 1943.',
    '1943-03-08': 'Brigada je krenula 7. marta preko Prozora ka Jablanici i prešla Neretvu 8. marta pre podne. Zatim se '
                  'uz Prenj probijala kroz četnike, preko Glavatičeva i Uloga, do Kalinovika, u koji je njen Četvrti '
                  'bataljon ušao 23. marta.',
    '1943-04-09': 'Brigada je 28. marta izbila na Drinu kod Ustikoline. Prvi pokušaj prelaska bio je 7. aprila. Na '
                  'drugoj obali zauzela je Kapak 10. aprila i borila se za Krčino brdo i Ifsar protiv italijanske '
                  'divizije „Taurinense“.',
    '1943-05-10': 'Brigada je 7. maja izbila pred Bijelo Polje i na putu Prijepolje–Bijelo Polje uništila italijansku '
                  'kolonu.',
    '1943-06-05': 'Kod Bijelog Polja brigada se prva sudarila sa nemačkom Prvom brdskom divizijom. Zatim se borila kod '
                  'Trovrha i Zlatnog bora, kod Foče, a do 6. juna u dolini Sutjeske.',
    '1943-06-10': 'Brigada je 6. juna krenula ispod Dragoš-sedla, preko Katuništa i Lučkih koliba. Ujutro 9. juna izbila '
                  'je na Balinovac i 10. juna probila nemački obruč. Zatim je probila i drugi obruč, kod Miljevine.',
    '1943-07-05': 'Posle oslobođenja Han Pijeska i Vlasenice brigada je napala Zvornik 4. jula u 21 čas i oslobodila ga. '
                  'Vrhovni štab je 11. jula naredio diviziji da se izvuče iz daljih borbi oko Zvornika.',
    '1943-09-22': 'Posle kapitulacije Italije Vrhovni štab je 15. septembra uputio Prvu diviziju u Dalmaciju, prema '
                  'Splitu, da pomogne u razoružavanju Italijana. Brigada se borila kod Omiša, Trilja i Aržana. '
                  'Početkom oktobra u nju je ušao bataljon „Garibaldi“, od 350 Italijana.',
    '1943-10-20': 'U jesen 1943. i zimu 1944. brigada je vodila borbe oko Travnika, Šujice, Jajca i Mrkonjić Grada.',
    '1944-05-28': 'U Drvarskoj operaciji brigada je noću 27/28. maja napala Nemce kod Mliništa. Zatim je obezbeđivala '
                  'prolaz kolone Vrhovnog štaba preko puta Mlinište–Glamoč, 31. maja i 1. juna.',
    '1944-08-25': 'U avgustu je brigada prešla Uvac u Srbiju. Na Palisadu, na Zlatiboru, namamila je u klopku bugarski '
                  '61. puk.',
    '1944-09-15': 'Prva i Šesta divizija napale su Valjevo noću 14/15. septembra 1944. Nemci su se povukli 17. septembra '
                  'i naleteli na položaje brigade kod Divaca.',
    '1944-10-16': 'Brigada je 7. oktobra krenula preko Lajkovca i Lazarevca ka Kosmaju i pred zoru 15. oktobra izbila '
                  'blizu Slavije. Posle oslobođenja Beograda bila je prva posadna jedinica u gradu.',
    '1944-12-15': 'Brigada je iz Beograda krenula na Sremski front 24. novembra 1944. Tu je, do aprila 1945, učestvovala '
                  'u dva neuspela pokušaja proboja i u odbrani.',
    '1945-04-12': 'Brigada je učestvovala u proboju Sremskog fronta 12. aprila 1945. Do 15. aprila izbila je na istočni '
                  'kraj Požeške kotline, a Pleternicu je napadala 19. aprila.',
    '1945-04-27': 'Na liniji Novska–Ilova Nemci su organizovali odbranu. Brigada je 26. aprila izbila u Brezovac, a '
                  '27. aprila napadala Novi Grabovac, uz dva bataljona Italijanske brigade. Imala je 37 poginulih i '
                  '102 ranjena.',
    '1945-05-06': 'U gonjenju neprijatelja ka Zagrebu brigada je preko Čazme i Dubrave stigla pred Vrbovec, jako '
                  'uporište na putu za Zagreb. Napad je počeo 5. maja u 20 časova i nastavljen je 6. maja.',
    '1945-05-09': 'U 14 časova 9. maja brigada je, sa crvenom zastavom na čelu, prošla kroz oslobođeni Zagreb.',
}

# Prva lička proleterska "Marko Orešković", from its monograph (Jovo Popović, Beograd 1988; the site's own PDF of
# it, prva-licka-proleterska.pdf): the chapters' dates and places, checked against where the brigade's fallen died.
# A place written '=Name' is not looked up: its coordinates are the ones given (Ilići by the Mrežnica's spring, between
# Slunj and Plaški, is not the Ilići GeoNames knows)
PRVA_LICKA = [
    # before the brigade first stood together: its battalions on their way to the Korana, under its staff
    ('1942-06-28', 'Smoljanac', 15.66, 44.94, None, 'battle'),
    ('1942-06-30', 'Sadilovac', 15.72, 44.94, 'Sadilovac, 28–30. VI 1942: bataljoni na okupljanju', 'battle'),
    ('1942-07-03', 'Lađevac', 15.64, 45.09, 'Lađevac, 3. VII 1942: prvi napad brigade', 'battle'),
    ('1942-07-08', '=Ilići', 15.47, 45.06, 'Ilići, 8. VII 1942: osnovana, prvi put postrojena', 'formed'),
    ('1942-07-15', 'Lička Jesenica', 15.29, 45.03, None, 'battle'),
    ('1942-07-24', 'Plaški', 15.37, 45.08, 'Plaški, VII 1942: na Kapeli i u plašćanskoj dolini', 'battle'),
    ('1942-08-08', 'Jezerane', 15.21, 45.05, 'Jezerane, VIII 1942: borbe za Prokike, Jezerane i Krišpolje', 'battle'),
    ('1942-08-14', 'Križpolje', 15.17, 45.02, None, 'battle'),
    ('1942-08-24', 'Škare', 15.31, 44.89, None, 'stop'),
    ('1942-08-31', 'Dabar', 15.31, 44.96, 'Dabar, VIII 1942: oslobođenje Dabra', 'battle'),
    ('1942-09-20', 'Perušić', 15.38, 44.65, None, 'battle'),
    ('1942-09-27', 'Pazarište', 15.22, 44.64, 'Pazarište, IX 1942: ofanziva Prve zone', 'battle'),
    ('1942-10-05', 'Krbavica', 15.63, 44.71, None, 'stop'),
    ('1942-10-23', 'Glina', 16.09, 45.34, 'Glina, 22/23. X 1942: napad na Glinu', 'battle'),
    ('1942-11-03', 'Ličko Petrovo Selo', 15.71, 44.88, None, 'battle'),
    ('1942-11-14', 'Slunj', 15.59, 45.12, 'Slunj, 14. XI 1942: oslobođenje Slunja', 'battle'),
    ('1942-11-27', 'Divuša', 16.44, 45.14, 'Dvor na Uni, 26–28. XI 1942: borbe kod Dvora', 'battle'),
    ('1942-12-20', 'Raduč', 15.58, 44.39, 'Raduč, XII 1942: borbe na komunikacijama Gospić–Gračac', 'battle'),
    ('1943-01-17', 'Gračac', 15.85, 44.30, 'Gračac, 16–19. I 1943: borba za Gračac', 'battle'),
    ('1943-02-05', 'Mazin', 15.97, 44.45, 'Mazin, II 1943: operacija „Weiss“', 'battle'),
    ('1943-02-13', 'Gornji Lapac', 15.99, 44.52, None, 'battle'),
    ('1943-02-20', 'Srb', 16.13, 44.36, None, 'battle'),
    ('1943-03-14', 'Sveti Rok', 15.65, 44.36, 'Sveti Rok, 14. III 1943: proletna ofanziva korpusa', 'battle'),
    ('1943-04-04', 'Žegar', 15.87, 44.15, 'Žegar, IV 1943: borbe u severnoj Dalmaciji', 'battle'),
    ('1943-04-10', 'Pađene', 16.10, 44.09, None, 'battle'),
    ('1943-04-28', 'Gospić', 15.37, 44.55, 'Gospić, 28–30. IV 1943: napad na Gospić', 'battle'),
    ('1943-05-20', 'Otočac', 15.24, 44.87, None, 'stop'),
    ('1943-06-28', 'Smiljan', 15.32, 44.56, None, 'battle'),
    ('1943-08-18', 'Perušić', 15.38, 44.65, 'Perušić, VIII 1943: obrana slobodne teritorije', 'battle'),
    ('1943-10-05', 'Brušane', 15.27, 44.50, 'Gospić, IX–X 1943: druga opsada Gospića', 'battle'),
    ('1943-10-20', 'Bruvno', 15.90, 44.40, None, 'battle'),
    ('1943-11-11', 'Srb', 16.13, 44.36, 'Srb, 11. XI 1943: polazak u Bosnu', 'stop'),
    ('1943-11-19', 'Bugojno', 17.45, 44.06, None, 'stop'),
    ('1943-11-29', 'Han-Bila', 17.76, 44.24, None, 'battle'),
    ('1943-12-15', 'Travnik', 17.67, 44.23, 'Travnik, XII 1943: travnički decembar', 'battle'),
    ('1944-01-08', 'Mrkonjić Grad', 17.08, 44.42, None, 'battle'),
    ('1944-01-18', 'Mlinište', 16.88, 44.20, 'Mlinište, I 1944: pohvala Vrhovnog komandanta', 'battle'),
    ('1944-02-20', 'Drvar', 16.38, 44.37, None, 'stop'),
    ('1944-03-19', 'Resanovci', 16.30, 44.30, 'Resanovci, 19. III 1944: proletersko zvanje', 'stop'),
    ('1944-04-17', 'Donji Lapac', 15.96, 44.55, 'Donji Lapac, IV 1944: borbe u dolini Une', 'battle'),
    ('1944-04-25', 'Martin Brod', 16.14, 44.49, None, 'battle'),
    ('1944-05-26', 'Drvar', 16.38, 44.37, 'Drvar, 25–28. V 1944: desant na Drvar', 'battle'),
    ('1944-06-11', 'Glamoč', 16.85, 44.05, None, 'stop'),
    ('1944-07-02', 'Livno', 17.01, 43.83, None, 'battle'),
    ('1944-07-18', 'Mlinište', 16.88, 44.20, None, 'stop'),
    ('1944-07-20', 'Kupres', 17.28, 43.99, None, 'stop'),
    ('1944-07-29', 'Vareš', 18.33, 44.16, None, 'battle'),
    ('1944-08-12', 'Zelengora', 18.55, 43.35, 'Zelengora, VIII 1944: marš za Srbiju', 'battle'),
    ('1944-08-20', 'Planina Pivska', 18.88, 43.28, None, 'stop'),
    ('1944-08-25', 'Žabljak', 19.12, 43.15, None, 'stop'),
    ('1944-09-02', 'Zlatibor', 19.71, 43.73, None, 'stop'),
    ('1944-09-05', 'Arilje', 20.10, 43.75, None, 'battle'),
    ('1944-09-08', 'Požega', 20.04, 43.85, None, 'battle'),
    ('1944-09-16', 'Valjevo', 19.89, 44.27, 'Valjevo, 16. IX 1944: ulazak u Valjevo', 'battle'),
    ('1944-09-23', 'Koceljeva', 19.81, 44.47, None, 'stop'),
    ('1944-10-06', 'Kosmaj', 20.56, 44.47, None, 'stop'),
    ('1944-10-14', 'Beograd', 20.46, 44.82, None, 'battle'),
    ('1944-10-20', 'Bežanijska Kosa', 20.35, 44.80, 'Zemun, 20. X 1944: prelaz Save', 'battle'),
    # Into Srem by the roads the book names (pp. 457-461): Dobanovci 23 X, Stara Pazova, Ruma 25 X, the Radinci
    # 28 X, then on 3 XI north-west by Manđelos and Ležimir to the line Vizić - Erdevik, held to the end of November
    ('1944-10-23', 'Dobanovci', 20.23, 44.83, None, 'stop'),
    ('1944-10-24', 'Stara Pazova', 20.16, 44.99, None, 'stop'),
    ('1944-10-25', 'Ruma', 19.84, 45.01, None, 'stop'),
    ('1944-10-28', 'Veliki Radinci', 19.67, 45.04, None, 'stop'),
    ('1944-11-03', 'Ležimir', 19.55, 45.12, None, 'stop'),
    ('1944-11-05', 'Erdevik', 19.40, 45.12, 'Erdevik, 4–28. XI 1944: Fruška gora', 'battle'),
    # 'transfer': the way into this place was a move away from the fighting, drawn thin and without arrows: back to
    # Beograd to rest (1-31 XII, p. 473), and by goods train from Zemun to Ruma on 1 I 1945 (p. 491)
    ('1944-12-01', 'Beograd', 20.46, 44.82, 'Beograd, XII 1944: odmor i popuna', 'transfer'),
    ('1944-12-31', 'Zemun', 20.40, 44.85, None, 'stop'),
    ('1945-01-01', 'Stara Pazova', 20.16, 44.99, None, 'transfer'),    # the railway to Ruma runs through it
    ('1945-01-01', 'Ruma', 19.84, 45.01, None, 'transfer'),
    ('1945-01-02', 'Sremska Mitrovica', 19.61, 44.98, None, 'stop'),
    ('1945-01-02', 'Kuzmin', 19.41, 45.03, None, 'stop'),
    ('1945-01-03', 'Šid', 19.23, 45.13, 'Šid, I–IV 1945: Sremski front', 'battle'),
    ('1945-02-15', 'Ilinci', 19.12, 45.11, None, 'battle'),
    ('1945-04-04', 'Adaševci', 19.22, 45.08, None, 'stop'),
    ('1945-04-06', 'Batrovci', 19.13, 45.05, 'Batrovci, 4–7. IV 1945: napad na Lipovac i Batrovce', 'battle'),
    ('1945-04-11', 'Vrbanja', 18.93, 44.98, None, 'battle'),
    ('1945-04-20', 'Slavonski Brod', 18.02, 45.16, 'Slavonski Brod, 20. IV 1945', 'battle'),
    ('1945-04-25', 'Uljanik', 17.02, 45.53, None, 'stop'),
    ('1945-04-29', 'Kreštelovac', 17.05, 45.58, None, 'battle'),
    ('1945-05-05', '=Miloševac', 16.70, 45.76, 'Čazma, 4–5. V 1945: borba za Čazmu', 'battle'),
    ('1945-05-07', 'Donja Zelina', 16.23, 45.91, None, 'stop'),
    ('1945-05-09', 'Gračani', 15.97, 45.85, None, 'battle'),
    ('1945-05-13', 'Šestine', 15.93, 45.85, 'Zagreb, 9–13. V 1945: Medvednica i parada', 'end'),
]

PRVA_LICKA_ABOUT = {
    '1942-06-30': 'Brigadu je naredbama štaba Prve operativne zone Hrvatske od 13. juna 1942. trebalo sastaviti od '
                  'četiri najbolja bataljona ličkih, kordunaških i banijskih odreda. Naređenja bataljonima poslata su do '
                  '18. juna, a štab brigade, sa komandantom Stevanom Opsenicom, radio je od druge polovine juna. Na putu '
                  'do mesta okupljanja, na Korani, ustaše su pred zoru 28. juna napale bataljon „Marko Orešković '
                  'Krntija“ u Smoljancu, a 30. juna bataljon „Pekiša Vuksan“ u Sadilovcu. „Krntijaši“ će biti 1. bataljon '
                  'brigade, koja je kasnije od njega preuzela ime Marka Oreškovića.',
    '1942-07-03': 'Posle borbi u Smoljancu i Sadilovcu komandanti zone i brigade odlučili su da ne čekaju banijski '
                  'bataljon i da najkasnije 3. jula napadnu Lađevac, selo kod Slunja, a po mogućnosti i sam Slunj. '
                  'Bataljon „Marko Orešković“ upao je u Lađevac i rasterao ustaše i njihovu miliciju, ali kad su Kordunaši '
                  'izgubili Melnicu, a ustaše prodorom ugrozile njegovo levo krilo, ostavio je zaplenjene magacine i '
                  'povukao se.',
    '1942-07-08': 'Brigada je prvi put postrojena u punom sastavu 8. jula 1942, na livadi kod vrela Mrežnice, u selu '
                  'Ilići između Slunja i Plaškog: nešto više od 1.100 boraca iz četiri bataljona ličkih, kordunaških i '
                  'banijskih odreda. Tada se zvala Udarna brigada Prve operativne zone Hrvatske. Okupljanje bataljona '
                  'završeno je tom smotrom, pa se 8. jul uzima kao dan formiranja brigade.',
    '1942-07-24': 'Posle formiranja brigada je krenula na zapad, na Kapelu. Napadala je prugu kod Blata i Rudopolja i '
                  'vodila tri borbe oko Plaškog.',
    '1942-08-08': 'U prvoj polovini avgusta brigada se borila za Prokike, Jezerane i Krišpolje i razbila neprijateljski '
                  'koridor Brinje–Ogulin, od Drežnice na jug do Škara.',
    '1942-08-31': 'Iz Krišpolja i Jezerana brigada je 19. avgusta krenula u četiri kolone, sa oko 800 boraca. Posle '
                  'napada na Letinac oslobodila je Dabar, a 6. septembra učestvovala u rušenju kapelske pruge.',
    '1942-09-27': 'U ofanzivi združenih snaga Prve zone, od 14. septembra do 2. oktobra, brigada je napadala '
                  'garnizone u perušićkom kotaru i zauzela Pazarište. Od 18. septembra zvala se Prva narodnooslobodilačka '
                  'udarna brigada Hrvatske.',
    '1942-10-23': 'Brigada je 11. oktobra krenula na Baniju. U noći 22/23. oktobra, po jakom pljusku, napadala je Glinu.',
    '1942-11-14': 'U bihaćkoj operaciji brigada je od 2. novembra napadala Ličko Petrovo Selo i gonila neprijatelja '
                  'prema Slunju. U Slunj je ušla uveče 14. novembra.',
    '1942-11-27': 'Od 20. novembra brigada je bila Prva brigada 6. divizije. Napad na uporišta između Volinje i Zamlače, '
                  'kod Dvora na Uni, počeo je 26. novembra u 23 časa; 27. novembra brigada je ušla u Divušu.',
    '1942-12-20': 'U decembru 1942. brigada je napadala neprijateljska uporišta na cesti i pruzi Gospić–Gračac, između '
                  'Medaka i Lovinca.',
    '1943-01-17': 'Od 16. do 19. januara 1943. brigada je učestvovala u borbi za Gračac.',
    '1943-02-05': 'U operaciji „Weiss“, od 20. januara do 23. februara, brigada je sa celom 6. divizijom vodila '
                  'neprekidne borbe protiv Italijana i četnika koji su se probijali od Gračaca preko Mazina i Gornjeg '
                  'Lapca i od Zrmanje prema Srbu.',
    '1943-03-14': 'U proletnoj ofanzivi Prvog hrvatskog korpusa bataljoni brigade razbili su oko 21 čas 14. marta ustaške '
                  'položaje između Ričica i Svetog Roka.',
    '1943-04-04': 'Početkom aprila brigada se borila u severnoj Dalmaciji, kod Žegara i Pađena.',
    '1943-04-28': 'Gospić je bio poslednje ustaško uporište u Lici. Četiri partizanske brigade napale su ga krajem aprila; '
                  'Prva je 28. aprila zauzela položaje prema zapadnim izlazima grada. Napad nije uspeo.',
    '1943-08-18': 'U avgustu 1943. brigada je branila slobodnu teritoriju perušićkog kotara; ustaše su 18. avgusta izbile '
                  'u Lički Osik.',
    '1943-10-05': 'Posle kapitulacije Italije brigada je u septembru i oktobru 1943. ponovo opsedala Gospić; 5. oktobra '
                  'ušla je u Brušane.',
    '1943-11-11': 'Tačno u 13 sati 11. novembra 1943. brigada je, sa 1.147 boraca, krenula iz Srba u Bosnu, u sastav '
                  'Prvog proleterskog korpusa. Do Bugojna je putovala osam dana.',
    '1943-12-15': 'Krajem novembra brigada je stigla na područje Travnika; 29. novembra bataljon „Marko Orešković“ napao '
                  'je most na Lašvi kod Han Bile. Ceo decembar proveo je u borbama oko Travnika.',
    '1944-01-18': 'Brigada je 8. januara 1944. izbila u Mrkonjić Grad. Kod Mliništa i Protića napadala je 18. i 19. '
                  'januara nemačke motorizovane kolone. Za januarske borbe pohvalio ju je Vrhovni komandant.',
    '1944-03-19': 'Vrhovni komandant je 6. ličkoj diviziji dao naziv proleterska divizija „Nikola Tesla“. Od 19. marta '
                  '1944. brigada je Prva lička proleterska.',
    '1944-04-17': 'U aprilu 1944. brigada je imala 15 borbi u dolini Une. Uveče 17. aprila tri bataljona napala su Nemce '
                  'u Mamcu, kod Donjeg Lapca.',
    '1944-05-26': 'Uoči desanta na Drvar bataljoni brigade bili su na liniji Mali i Veliki Cvjetnić. Brigada je razbijala '
                  'nemačke desantne snage u Drvaru, a 28. maja predveče udarila je na začelje nemačkih kolona na cesti '
                  'prema Drvaru i uništila pet blindiranih kola.',
    '1944-08-12': 'Brigada je krenula prema Srbiji 18. jula 1944, sa 933 borca. Bosnu je prešla 27. jula, između dva '
                  'blindirana voza, borila se na Zelengori, a na Pivskoj planini 20. avgusta imala je 797 boraca. Taru je '
                  'prešla 25. avgusta.',
    '1944-09-16': 'Sa Zlatibora brigada je nastupala prema Arilju i Užičkoj Požegi, a predveče 16. septembra ušla je u '
                  'Valjevo.',
    '1944-10-20': 'Poslednjeg dana bitke za Beograd, 20. oktobra, brigada je prva prešla Savu, preko zemunskog mosta, da '
                  'bi se stvorio mostobran ispred Bežanije i Zemuna.',
    '1944-11-05': 'Iz rajona Radinaca brigada je 3. novembra krenula na severozapad, preko Manđelosa i Ležimira, a 4. '
                  'novembra ušla je u borbu sa zadatkom da nastupa prema Erdeviku i Binguli. Na liniji Vizić–Erdevik '
                  'držala je položaje do kraja novembra; za stare borce frontalne borbe u Sremu bile su novo i skupo '
                  'plaćeno iskustvo.',
    '1944-12-01': 'Sa Fruške gore brigada je 1. decembra, po susnežici, stigla u Beograd i ostala u njemu do kraja meseca: '
                  'obuka, reorganizacija i popuna. Do 7. decembra primljeno je 2.293 novomobilisanih, a 7. decembra u '
                  'njen sastav ušao je u Beogradu formirani makedonski bataljon „Jane Sandanski“.',
    '1945-01-03': 'Naređenje za pokret iz Beograda stiglo je 31. decembra. Brigada je prenoćila u Zemunu, 1. januara '
                  'otišla teretnim vagonima u Rumu, a odatle uglavnom pešice, preko Sremske Mitrovice, Martinaca i '
                  'Kuzmina, do Šida, pred koji je stigla 3. januara. U rovovima Srema provela je devedeset dana.',
    '1945-04-06': 'U završnoj ofanzivi brigada je posle smotre u Adaševcima 4. aprila napala Lipovac i Batrovce. Juriši su '
                  'trajali danima, uz velike gubitke.',
    '1945-04-20': 'Posle napada na železničku stanicu Vrbanja, 11. aprila, brigada je 20. aprila ušla u Slavonski Brod, '
                  'pošto ga je neprijatelj napustio.',
    '1945-05-05': 'Brigada je ujutro 5. maja sa Drugom brigadom zauzela Čazmu. U dvodnevnim borbama, više kod Miloševca '
                  'nego u samoj Čazmi, imala je velike gubitke.',
    '1945-05-13': 'Brigada je 9. i 10. maja razbijala nemačke i ustaške jedinice na Medvednici, kod Remeta i Gračana. '
                  'Prikupila se 12. maja u severnim delovima Zagreba, a njen bataljon učestvovao je 13. maja u paradi.',
}

# Treća krajiška proleterska brigada: from Savo Trikić's monograph (Vojnoizdavački i novinski centar, znaci.org
# 00001/224), its chapters' dates and places, checked against where the brigade's fallen died, month by month (the
# book's pages on January 1945 are blank in the scan; that month follows its chapter title and the fallen)
TRECA_KRAJISKA = [
    ('1942-08-22', 'Kamenica', 16.35, 44.40, 'Kamenica kod Drvara, 22. VIII 1942: osnovana', 'formed'),
    ('1942-08-25', 'Krnjeuša', 16.20, 44.68, None, 'stop'),
    ('1942-09-02', 'Cazin', 15.94, 44.97, 'Cazin, 2. IX 1942: prvo oslobođenje Cazina', 'battle'),
    ('1942-09-12', 'Lušci Palanka', 16.47, 44.73, None, 'stop'),
    ('1942-09-16', 'Ribnik', 16.81, 44.42, None, 'stop'),
    ('1942-09-20', 'Manjača', 17.05, 44.62, 'Manjača, 19–29. IX 1942: borbe na Manjači', 'battle'),
    ('1942-09-29', 'Sitnica', 17.03, 44.50, None, 'battle'),
    ('1942-10-06', 'Krasulje', 16.75, 44.57, 'Krasulje i Ključ, X 1942: borbe u dolini Sane', 'battle'),
    ('1942-10-07', 'Ključ', 16.78, 44.53, None, 'battle'),
    ('1942-10-27', 'Sanica', 16.62, 44.59, None, 'stop'),
    ('1942-11-03', 'Bihać', 15.87, 44.82, 'Bihać, 2–5. XI 1942: oslobođenje Bihaća', 'battle'),
    ('1942-11-13', 'Bosanski Petrovac', 16.37, 44.55, None, 'stop'),
    ('1942-11-20', 'Čađavica', 16.95, 44.48, None, 'battle'),
    ('1942-11-26', 'Jajce', 17.27, 44.34, 'Jajce, XI 1942: oslobođenje Jajca', 'battle'),
    ('1942-12-04', 'Kotor Varoš', 17.37, 44.62, 'Kotor Varoš, XII 1942: borbe u srednjoj Bosni', 'battle'),
    ('1942-12-09', 'Šnjegotina', 17.45, 44.60, None, 'battle'),
    ('1942-12-21', 'Pribinić', 17.68, 44.58, None, 'stop'),
    ('1942-12-31', 'Teslić', 17.86, 44.61, 'Teslić, XII 1942 – I 1943: borbe za Teslić', 'battle'),
    ('1943-01-21', 'Teslić', 17.86, 44.61, None, 'battle'),
    ('1943-02-04', 'Komar', 17.48, 44.22, None, 'stop'),
    ('1943-02-08', 'Gornji Vakuf', 17.59, 43.94, None, 'stop'),
    ('1943-02-17', 'Prozor', 17.61, 43.82, 'Prozor, 16–17. II 1943: oslobođenje Prozora', 'battle'),
    ('1943-02-21', 'Gornji Vakuf', 17.59, 43.94, 'Gornji Vakuf, II–III 1943: odbrana Vrbasa i protivudar', 'battle'),
    ('1943-03-01', 'Raduša', 17.48, 43.93, None, 'battle'),
    ('1943-03-11', 'Gračanica', 17.63, 43.87, None, 'battle'),
    ('1943-03-15', 'Jablanica', 17.76, 43.66, 'Jablanica, 15. III 1943: prelaz Neretve', 'battle'),
    ('1943-03-21', 'Bijela', 17.93, 43.62, None, 'battle'),
    ('1943-04-07', 'Kalinovik', 18.45, 43.50, None, 'stop'),
    ('1943-04-09', 'Ustikolina', 18.79, 43.58, 'Ustikolina, 7–9. IV 1943: prelaz Drine', 'battle'),
    ('1943-04-12', 'Čajniče', 19.07, 43.56, None, 'battle'),
    ('1943-04-23', 'Pljevlja', 19.36, 43.36, 'Pljevlja, IV–V 1943: borbe s Italijanima i četnicima', 'battle'),
    ('1943-05-15', 'Bijelo Polje', 19.75, 43.04, 'Bijelo Polje, 15–18. V 1943: početak Pete ofanzive', 'battle'),
    ('1943-05-25', 'Čelebići', 18.83, 43.33, 'Čelebići, 24–27. V 1943: borbe kod Foče', 'battle'),
    ('1943-05-30', 'Šćepan Polje', 18.85, 43.34, None, 'stop'),
    ('1943-06-02', 'Mratinje', 18.80, 43.27, None, 'stop'),
    ('1943-06-08', 'Tjentište', 18.69, 43.35, 'Sutjeska, 5–10. VI 1943: proboj preko Sutjeske', 'battle'),
    ('1943-06-10', 'Balinovac', 18.62, 43.40, None, 'battle'),
    ('1943-06-13', 'Miljevina', 18.65, 43.53, 'Vis i Šiljevac, 11–14. VI 1943: proboj obruča', 'battle'),
    ('1943-06-18', 'Renovica', 18.79, 43.73, None, 'battle'),
    ('1943-06-25', 'Srebrenica', 19.30, 44.10, 'Srebrenica, 25–26. VI 1943: oslobođenje Srebrenice i Bratunca', 'battle'),
    ('1943-06-26', 'Bratunac', 19.33, 44.19, None, 'stop'),
    ('1943-06-28', 'Milići', 19.08, 44.17, None, 'stop'),
    ('1943-07-04', 'Sokolac', 18.80, 43.94, 'Sokolac, VII 1943: napad na Sokolac', 'battle'),
    ('1943-07-18', 'Prača', 18.77, 43.77, 'Prača, VII 1943: napadi u dolini Prače', 'battle'),
    ('1943-07-28', 'Jahorina', 18.56, 43.73, None, 'stop'),
    ('1943-07-31', 'Trnovo', 18.45, 43.67, None, 'battle'),
    ('1943-08-04', 'Ivan Sedlo', 18.03, 43.75, None, 'battle'),
    ('1943-08-16', 'Donji Vakuf', 17.43, 44.14, 'Donji Vakuf, 16. VIII 1943: oslobođenje Donjeg Vakufa', 'battle'),
    ('1943-08-19', 'Turbe', 17.58, 44.25, None, 'battle'),
    ('1943-08-23', 'Bugojno', 17.45, 44.06, 'Bugojno, 22–25. VIII 1943: oslobođenje Bugojna', 'battle'),
    ('1943-09-14', 'Duvno', 17.23, 43.72, None, 'stop'),
    ('1943-09-22', 'Sinj', 16.64, 43.70, 'Sinj, 19–26. IX 1943: napad na Sinj', 'battle'),
    ('1943-10-03', 'Livno', 17.01, 43.83, 'Livno, 3. X 1943: ulazak u Livno', 'battle'),
    ('1943-10-07', 'Kupres', 17.28, 43.99, None, 'stop'),
    ('1943-10-10', 'Zenica', 17.91, 44.20, 'Zenica, 10/11. X 1943: napad na Zenicu', 'battle'),
    ('1943-10-15', 'Travnik', 17.67, 44.23, 'Travnik, X–XI 1943: napadi na Travnik', 'battle'),
    ('1943-11-03', 'Han Bila', 17.76, 44.22, None, 'battle'),
    ('1943-11-29', 'Travnik', 17.67, 44.23, None, 'battle'),
    ('1943-12-08', 'Šujica', 17.17, 43.83, 'Borova glava i Šujica, XII 1943: borbe kod Livna', 'battle'),
    ('1943-12-24', 'Turbe', 17.58, 44.25, None, 'stop'),
    ('1943-12-31', 'Banja Luka', 17.19, 44.77, 'Banja Luka, 31. XII 1943 – 3. I 1944: napad na Banju Luku', 'battle'),
    ('1944-01-08', 'Mrkonjić Grad', 17.08, 44.42, None, 'battle'),
    ('1944-01-18', 'Ubovići', 16.90, 44.10, None, 'battle'),
    ('1944-02-09', 'Mlinište', 16.85, 44.25, None, 'stop'),
    ('1944-03-10', 'Jajce', 17.27, 44.34, None, 'battle'),
    ('1944-03-18', 'Glamoč', 16.85, 44.05, None, 'stop'),
    ('1944-04-14', 'Ljubunčić', 16.98, 43.90, None, 'battle'),
    ('1944-05-27', 'Priluka', 16.97, 43.89, 'Livno–Glamoč, 25–28. V 1944: borbe za vreme desanta na Drvar', 'battle'),
    ('1944-06-01', 'Mlinište', 16.85, 44.25, 'Mliništa i Čardak, 1–3. VI 1944: prethodnica kolone Vrhovnog štaba', 'battle'),
    ('1944-06-04', 'Kupres', 17.28, 43.99, None, 'stop'),
    ('1944-06-08', 'Donje Vukovsko', 17.40, 43.96, None, 'stop'),
    ('1944-06-19', 'Zec', 17.85, 43.95, 'Zec i Crni vrh, VI 1944: borbe s divizijom „Prinz Eugen“', 'battle'),
    ('1944-06-23', 'Rostovo', 17.66, 44.07, None, 'battle'),
    ('1944-06-25', 'Vranica', 17.75, 43.95, None, 'stop'),
    ('1944-06-28', 'Brđani', 18.07, 43.70, 'Brđani, 27/28. VI 1944: prelaz pruge Konjic–Sarajevo', 'battle'),
    ('1944-07-02', 'Miljevina', 18.65, 43.53, None, 'stop'),
    ('1944-07-04', 'Foča', 18.78, 43.51, None, 'stop'),
    ('1944-07-12', 'Čajniče', 19.07, 43.56, None, 'battle'),
    ('1944-07-20', 'Pljevlja', 19.36, 43.36, 'Pljevlja, VII–VIII 1944: u strateškoj rezervi Vrhovnog štaba', 'battle'),
    ('1944-08-21', 'Priboj', 19.53, 43.58, None, 'stop'),
    ('1944-08-23', 'Čajetina', 19.72, 43.75, None, 'battle'),
    ('1944-08-25', 'Palisad', 19.70, 43.72, 'Zlatibor, 22–25. VIII 1944: prelaz Uvca i napad na Palisad', 'battle'),
    ('1944-08-28', 'Sirogojno', 19.88, 43.68, None, 'stop'),
    ('1944-09-03', 'Arilje', 20.10, 43.75, 'Arilje, 3. IX 1944: oslobođenje Arilja', 'battle'),
    ('1944-09-05', 'Kosjerić', 19.91, 44.00, 'Kosjerić i Jelova gora, 5–9. IX 1944: borbe s četnicima', 'battle'),
    ('1944-09-08', 'Jelova Gora', 19.83, 43.95, None, 'battle'),
    ('1944-09-11', 'Divci', 20.03, 44.30, None, 'stop'),
    ('1944-09-15', 'Valjevo', 19.89, 44.27, 'Valjevo, 14–18. IX 1944: oslobođenje Valjeva', 'battle'),
    ('1944-09-21', 'Bogovađa', 20.18, 44.32, None, 'stop'),
    ('1944-10-02', 'Ub', 20.08, 44.46, 'Ub, 2. X 1944: oslobođenje Uba', 'battle'),
    ('1944-10-11', 'Mladenovac', 20.70, 44.44, 'Mladenovac, 10–12. X 1944: susret sa Crvenom armijom', 'battle'),
    ('1944-10-14', 'Ralja', 20.55, 44.56, None, 'stop'),
    ('1944-10-17', 'Beograd', 20.46, 44.81, 'Beograd, 15–20. X 1944: od Čubure do Kalemegdana', 'battle'),
    ('1944-11-23', 'Beograd', 20.46, 44.81, None, 'stop'),
    ('1944-11-25', 'Sremski Karlovci', 19.93, 45.20, None, 'stop'),
    ('1944-11-26', 'Susek', 19.53, 45.21, None, 'stop'),
    ('1944-12-03', 'Tovarnik', 19.15, 45.17, 'Tovarnik, 3–9. XII 1944: proboj kod Tovarnika', 'battle'),
    ('1944-12-10', 'Berak', 18.95, 45.25, None, 'battle'),
    ('1945-01-05', 'Đeletovci', 19.07, 45.20, None, 'battle'),
    ('1945-01-18', 'Šid', 19.23, 45.13, 'Šid, 18–19. I 1945: nemačka protivofanziva', 'battle'),
    ('1945-02-15', 'Erdevik', 19.40, 45.12, None, 'stop'),
    ('1945-04-05', 'Bapska', 19.27, 45.21, 'Novak-Bapska, 5. IV 1945: nasilno izviđanje', 'battle'),
    ('1945-04-12', 'Bapska', 19.27, 45.21, 'Novak-Bapska, 12. IV 1945: proboj Sremskog fronta', 'battle'),
    ('1945-04-13', 'Opatovac', 19.20, 45.25, None, 'stop'),
    ('1945-04-14', 'Markušica', 18.73, 45.37, None, 'stop'),
    ('1945-04-16', 'Ruševo', 18.00, 45.28, None, 'battle'),
    ('1945-04-20', 'Pleternica', 17.81, 45.29, 'Pleternica, 17–20. IV 1945: oslobođenje Pleternice', 'battle'),
    ('1945-04-23', 'Cernik', 17.38, 45.29, None, 'stop'),
    ('1945-04-27', 'Bujavica', 17.12, 45.43, 'Bujavica, kraj IV 1945: borbe na Ilovi', 'battle'),
    ('1945-05-07', 'Vrbovec', 16.42, 45.88, 'Vrbovec, 7–8. V 1945: borbe kod Vrbovca', 'battle'),
    ('1945-05-08', 'Sveti Ivan Zelina', 16.24, 45.96, None, 'stop'),
    ('1945-05-10', 'Šestine', 15.95, 45.85, 'Šestine, 9–10. V 1945: poslednje borbe na Zagrebačkoj gori', 'battle'),
]

# What the monograph tells of each numbered event, in a few sentences (the card under the map)
TRECA_KRAJISKA_ABOUT = {
    '1942-08-22': 'Brigada je formirana 22. avgusta 1942. u selu Kamenici kod Drvara, od jedinica 5. krajiškog odreda. '
                  'Toga dana brojala je 704 borca, među njima mnogo radnika drvarskih i petrovačkih pilana, fabrika i '
                  'rudnika. Prvi komandant bio je Nikola Karanović.',
    '1942-09-02': 'Na prvi borbeni zadatak brigada je krenula 24. avgusta, preko Bosanskog Petrovca i Krnjeuše u '
                  'Cazinsku krajinu. Napad je počeo 2. septembra u tri časa; zajedno sa 1. krajiškim odredom brigada je '
                  'razbila posade u Pounju, a Cazin je istog jutra prvi put oslobođen. Sutradan je neprijatelj, sa '
                  'tenkovima, artiljerijom i avijacijom, napao od Bosanske Krupe.',
    '1942-09-20': 'Preko Lušci Palanke, Bravskog i Ribnika brigada je posle četiri dana marša 19. septembra posela '
                  'položaje na severnim padinama Manjače, kod Kadine Vode. Do kraja meseca odbijala je svakodnevne '
                  'napade pešadije sa tenkovima i avijacijom, dok su druge brigade 25. septembra oslobodile Jajce.',
    '1942-10-06': 'Početkom oktobra brigada je prešla Sanu i sa 1. proleterskom brigadom vodila borbe jugozapadno od '
                  'Ključa. Noću 5/6. oktobra zauzela je uporišta na Gvozdacu i Ramićkom kamenu i napala utvrđeno selo '
                  'Krasulje; Ključ je 7. oktobra ponovo oslobođen. Na položajima kod Krasulja ostala je do kraja oktobra.',
    '1942-11-03': 'Krajem oktobra brigada je usiljenim maršem preko Lušci Palanke stigla pred Bihać. Napad je počeo 2. '
                  'novembra uveče; brigada je napadala Žegar i Borik, a poslednje ustaše predale su se u tvrđavi Sokolac '
                  '5. novembra. Posle oslobođenja preuzela je garnizonsku službu u gradu, a 11. novembra Tito je izvršio '
                  'smotru njenog 4. bataljona.',
    '1942-11-26': 'U sastavu novoformirane 1. proleterske divizije brigada je 16. novembra krenula iz Bosanskog Petrovca '
                  'prema srednjoj Bosni. Posle borbi kod Sitnice i Čađavice učestvovala je u napadu na Jajce, koji je '
                  'počeo 25. novembra uveče, i grad je oslobođen.',
    '1942-12-04': 'U decembru brigada je sa 1. proleterskom i 3. sandžačkom vodila borbe u srednjoj Bosni, oko Kotor '
                  'Varoši, Maslovara i Šnjegotine, protiv domobrana, ustaša i četničkih odreda. Kotor Varoš je oslobođen '
                  'noću 3/4. decembra.',
    '1942-12-31': 'Napad na Teslić počeo je 31. decembra uveče i grad je oslobođen. Neprijatelj ga je ponovo zauzeo 6. '
                  'januara 1943. Brigada je Teslić napadala još 14, 15. i 17. januara, a od 20. do 23. januara odbijala '
                  'napade nemačkih i ustaških snaga od grada.',
    '1943-02-17': 'Na početku nemačke operacije „Weiss“ brigada je prešla Borje i Usoru, a 4. februara, kod tunela na '
                  'Komaru, i put Turbe–Donji Vakuf, pa je stigla u gornji tok Vrbasa. Njen 4. bataljon učestvovao je u '
                  'napadu na Prozor, koji je oslobođen 17. februara.',
    '1943-02-21': 'Brigada je zatvarala pravac od Bugojna prema Gornjem Vakufu. Od 21. februara odbijala je napade '
                  'nemačkih snaga sa tenkovima, a od 28. februara do 2. marta vodila teške borbe na Raduši i Kobili. U '
                  'protivudaru Glavne operativne grupe, od 3. do 5. marta, Nemci su odbačeni preko Gornjeg Vakufa.',
    '1943-03-15': 'Od 8. do 14. marta brigada je u dolini Rame, kod Gračanice, zadržavala nemačku kolonu sa tenkovima '
                  'koja je od Prozora nastupala prema Neretvi. Neretvu je prešla kod Jablanice 15. marta, preko '
                  'improvizovanog mosta, a zatim je kod Bijele, prema Konjicu, štitila Centralnu bolnicu sa ranjenicima.',
    '1943-04-09': 'Preko Glavatičeva brigada je 7. aprila stigla u rejon Kalinovika i na Drinu. Posle prvog neuspelog '
                  'pokušaja jedinice 1. proleterske divizije zauzele su 8. aprila Krčino brdo i Kapak na desnoj obali; '
                  'brigada se prebacila 9. aprila, a 12. aprila ušla je u Čajniče.',
    '1943-04-23': 'Goneći četnike, brigada je izbila pred Pljevlja i do 8. maja držala položaje prema gradu, odbijajući '
                  'napade Italijana i četnika.',
    '1943-05-15': 'Kod Bijelog Polja, na Limu, brigadu je 15. maja zatekao početak nemačke operacije „Schwarz“: opšti '
                  'napad nemačke 1. brdske divizije. U četvorodnevnim borbama kod Šahovića i Mojkovca imala je 14 '
                  'poginulih i 41 ranjenog.',
    '1943-05-25': 'Usiljenim maršem preko Kosanice i Mekog Dola brigada je stigla u fočanski sektor i 24. maja '
                  'učestvovala u napadu na Trovrh. Do 27. maja kod Popovog Dola i Čelebića zadržavala je nemačku 369. '
                  'diviziju, a zatim je na levoj obali Tare, od Uzlupa do Šćepan Polja, branila prelaze.',
    '1943-06-08': 'Brigada je 2. juna prenoćila u Mratinju, a od 5. juna, sa 1. proleterskom divizijom, probijala se '
                  'preko Sutjeske. Na početku bitke, 15. maja, imala je 1.207 boraca, od kojih 161 ženu, a 20. juna '
                  '1.084, od kojih 100 žena.',
    '1943-06-13': 'Posle proboja kod Balinovca, 10. juna, brigada je noću 12/13. juna vodila borbe za Vis i Šiljevac, '
                  'jedne od svojih najuspešnijih u ofanzivi, i probila obruč kod Miljevine. Noću 17/18. juna prešla je '
                  'put Goražde–Renovica i prugu Višegrad–Sarajevo i zarobila 40 domobrana i 5 Nemaca.',
    '1943-06-25': 'U protivofanzivi u istočnoj Bosni brigada je preko Devetaka i planine Javor 25. juna upala u '
                  'Srebrenicu, koju su ustaše i milicija napustile pred njenim dolaskom. Sutradan su njeni bataljoni ušli '
                  'u Bratunac i izbili na Drinu.',
    '1943-07-04': 'Početkom jula brigada je prešla put Sokolac–Han Pijesak i 4. jula, sa 6. istočnobosanskom brigadom, '
                  'napala garnizon u Sokolcu. Od 12. do 16. jula odbijala je napade dveju neprijateljskih pukovnija sa '
                  'tenkovima, koje su nastojale da oslobode put Sokolac–Vlasenica.',
    '1943-07-18': 'Brigada je 17. jula izbila na komunikaciju Sarajevo–Višegrad u dolini Prače i napadala uporišta na '
                  'pruzi. U tim borbama imala je teške gubitke, naročito 2. bataljon.',
    '1943-08-16': 'Preko Jahorine i Trnova, koje je zauzela 31. jula, brigada je noću 3/4. avgusta kod Ivan-sedla prešla '
                  'prugu Sarajevo–Mostar i vratila se u srednju Bosnu. Njeni 3. i 4. bataljon oslobodili su 16. avgusta '
                  'Donji Vakuf.',
    '1943-08-23': 'Napad na Bugojno počeo je 22. avgusta u 23 časa; posle dvodnevnih borbi grad je oslobođen, a slobodna '
                  'teritorija proširena od izvora Bosne do Bosanske krajine. Brigada je do 12. septembra ostala kod '
                  'Bugojna, a tog dana je proglašena proleterskom.',
    '1943-09-22': 'Posle kapitulacije Italije brigada je preko Duvna i Buškog blata krenula u Dalmaciju i noću 17/18. '
                  'septembra prešla Cetinu. Napad na nemačko-ustaški garnizon u Sinju, od 19. do 22. septembra, nije '
                  'uspeo; Nemci su se 24. septembra probili iz Sinja i 27. septembra ušli u Split.',
    '1943-10-03': 'Na povratku iz Dalmacije, u napadu na Livno, njen 3. bataljon sa tenkovskom grupom ušao je u grad 3. '
                  'oktobra ujutro; posada ga je napustila bez borbe.',
    '1943-10-10': 'U dolini Lašve brigada je noću 10/11. oktobra upala u Zenicu, onesposobila objekte i oslobodila '
                  'zatvorenike, a zatim se povukla.',
    '1943-10-15': 'Napad 1. proleterske divizije na Travnik, 15. oktobra, nije uspeo. Do kraja novembra brigada je bila '
                  'između Travnika, Kupresa i Gornjeg Vakufa, napadala uporišta u dolini Lašve i 29. novembra, u vreme '
                  'Drugog zasedanja AVNOJ-a, ponovo napala Travnik.',
    '1943-12-08': 'Na početku nemačke zimske ofanzive brigada je 6. decembra kod Borove glave dočekala motorizovanu '
                  'grupu „Berger“. Noću 9/10. decembra napadala je Livno, a do 18. decembra vodila svakodnevne borbe oko '
                  'Šujice.',
    '1943-12-31': 'U napadu 5. korpusa na Banju Luku brigada je 31. decembra uveče prodrla u grad. Posle uličnih borbi, '
                  'kada su 2. januara u grad stigli nemački tenkovi od Bosanske Gradiške, jedinice su se 3. januara u '
                  'četiri časa povukle.',
    '1944-05-27': 'Na dan desanta na Drvar, 25. maja, brigada je bila na pravcu Livno–Glamoč. Njen 3. bataljon je 27. maja '
                  'kod Korične zaustavio nemačku motorizovanu kolonu i vratio je u Livno, a brigada je do 28. maja '
                  'odbijala napade sa ovog pravca.',
    '1944-06-01': 'Posle povlačenja iz okoline Drvara brigada je bila prethodnica kolone Vrhovnog štaba, koja je 1. juna '
                  'krenula preko Mliništa i Čardaka. Vrhovni štab je noću 3/4. juna stigao na Kupreško polje, odakle je '
                  'deo štaba prebačen avionom.',
    '1944-06-19': 'Kod Zeca i Vranice divizija „Prinz Eugen“ pokušala je da okruži 1. proletersku diviziju. Brigada je '
                  '18. juna zauzela Vitreušu, Smiljevu kosu i Štit i držala položaje na Zecu dok se ostale brigade nisu '
                  'izvukle; na začelju kolone, kod Crnog vrha i Rostova, štitila je pokret pod borbom.',
    '1944-06-28': 'Noću 27/28. juna 1. proleterska divizija prešla je prugu i put Konjic–Sarajevo na širokom frontu. '
                  'Borba brigade za železničke stanice Brđani i Kanina trajala je do tri časa 28. juna.',
    '1944-07-20': 'Brigada je 4. i 5. jula obezbedila prelaz 1. i 13. proleterske brigade i bolnice preko Drine kod '
                  'Foče. Kao deo strateške rezerve Vrhovnog štaba ostala je u Sandžaku do 22. avgusta: branila je put '
                  'Čajniče–Goražde i položaje na Ćehotini kod Pljevalja. Ordenom narodnog oslobođenja odlikovana je 1. '
                  'jula 1944.',
    '1944-08-25': 'Brigada je kod Priboja prešla Lim, a 23. avgusta u četiri časa nasilno je prešla Uvac i do večeri '
                  'ovladala grebenom Čigote, na Zlatiboru. Napad 1. proleterske divizije na utvrđeni rejon na Palisadu, '
                  'koji su branili Bugari i četnici, 24. i 25. avgusta, nije uspeo.',
    '1944-09-03': 'Njen 1. bataljon izveo je 1. septembra demonstrativni napad na Užice, a 3. bataljon je 3. septembra na '
                  'juriš oslobodio Arilje.',
    '1944-09-05': 'Goneći četnike, brigada je 5. septembra oslobodila Kosjerić. Od 7. do 9. septembra, na frontu od '
                  'Kosjerića do Karana, odbijala je napade glavnine četničkih korpusa, koji su nastupali prema Jelovoj '
                  'gori.',
    '1944-09-15': 'Napad na Valjevo počeo je 14. septembra u 18 časova; bataljoni brigade savladali su spoljnu odbranu i '
                  'vodili ulične borbe. Nemci su napustili grad 18. septembra.',
    '1944-10-02': 'Posle desetodnevnog odmora kod Lajkovca brigada je 2. oktobra napala Ub i oslobodila ga; imala je 11 '
                  'poginulih i 45 ranjenih.',
    '1944-10-11': 'Rušeći prugu Niš–Beograd, brigada je od 9. do 12. oktobra vršila pritisak na garnizon u Mladenovcu. '
                  'Njeni bataljoni su 12. oktobra oko podne susreli jedinice Crvene armije.',
    '1944-10-17': 'Iz Ralje, preko Avale, brigada je 15. oktobra ušla u grad i sa linije Čubura–Svetosavska crkva–'
                  'Karađorđev park nastupala prema centru. Njeni bombaši i posada sovjetskog protivtenkovskog topa '
                  'uništili su 18. oktobra nemački tenk „tigar“, a noću 19/20. oktobra 2. i 5. bataljon prodrli su do '
                  'Nebojšine kule i ušća Save. U oslobođenom Beogradu brigada je ostala do 24. novembra.',
    '1944-12-03': 'Krajem novembra brigada je preko Pazove i Sremskih Karlovaca stigla na Frušku goru. U napadu 1. '
                  'proleterskog korpusa, 3. decembra, probila je nemačku odbranu i do 9. decembra vodila borbe za '
                  'Tovarnik, Ilaču i Šidske Banovce, a zatim napadala utvrđenu liniju kod Beraka.',
    '1945-01-18': 'U januaru 1945. brigada je držala front kod Šida i Tovarnika. Nemačka protivofanziva 18. i 19. januara '
                  'zahvatila je i ovaj deo Sremskog fronta; najviše njenih boraca poginulo je kod Šida i na Kozjakovom '
                  'salašu.',
    '1945-04-05': 'Uoči proboja Sremskog fronta brigada je izvela nasilno izviđanje nemačke utvrđene zone kod '
                  'Novak-Bapske i pretrpela velike žrtve; po spisku palih, samo 5. aprila poginulo je 79 njenih boraca. '
                  '„Poučeni gorkim iskustvom“, piše Trikić, njeni starešine i borci spremali su proboj tako da se greške '
                  'ne ponove.',
    '1945-04-12': 'Brigada je 8. aprila posela položaje kod Babinog Dola, sa štabom u Novak-Bapskoj, a 12. aprila do 14 '
                  'časova probila Sremski front. Po njenoj bojnoj relaciji, od 12. do 14. aprila ubila je 2.137 i '
                  'zarobila 684 neprijateljska vojnika.',
    '1945-04-20': 'Preko Nuštra, Jarmine i Markušice brigada je izbila u Požešku kotlinu. Pleternicu, koju su branile '
                  'ustaše, napadala je od 17. aprila sa 13. proleterskom brigadom i tenkovima; grad je oslobođen 20. '
                  'aprila u četiri časa.',
    '1945-04-27': 'Na liniji Una–Novska–Ilova–Bilogora Nemci su pokušali da zaustave Jugoslovensku armiju. Brigada je '
                  '27. aprila naišla na jak otpor na položajima Bujavica–Novi Grabovac, kod Lipika.',
    '1945-05-07': 'U napadu na Zagreb brigada je 7. maja uvedena u borbu kod Vrbovca, gde je neprijatelj bio opkoljen; '
                  'samo mali deo njegovih snaga probio se iz obruča.',
    '1945-05-10': 'Iz Novog Mesta kod Svetog Ivana Zeline brigada je 8. maja krenula usiljenim maršem padinama Zagrebačke '
                  'gore prema Šestinama. Posle žestokih borbi 9. i 10. maja razbila je neprijatelja kod Šestina; ujutro '
                  '10. maja, na južnim padinama Zagrebačke gore, završila je ratni put.',
}


UNITS = {
    'prva-proleterska': {'data': 'prva-proleterska-soldiers.json', 'route': PRVA_PROLETERSKA, 'name': 'Prva proleterska',
                         'about': PRVA_PROLETERSKA_ABOUT,
                         'source': 'Miloš Vuksanović, Prva proleterska brigada, Beograd 1981'},
    'prva-licka': {'data': 'soldiers.json', 'route': PRVA_LICKA, 'name': 'Prva lička proleterska',
                   'about': PRVA_LICKA_ABOUT,
                   'source': 'Jovo Popović, Prva lička proleterska NOU brigada „Marko Orešković“, Beograd 1988'},
    'treca-krajiska': {'data': '3-krajiska-proleterska-soldiers.json', 'route': TRECA_KRAJISKA,
                       'name': 'Treća krajiška proleterska', 'about': TRECA_KRAJISKA_ABOUT,
                       'source': 'Savo Trikić, Treća krajiška proleterska brigada, Vojnoizdavački i novinski centar, Beograd'},
}

# Names in the records that GeoNames knows otherwise, and regions that are no single place
ALIASES = {'uzicka pozega': 'Požega', 'sutjeska': 'Tjentište', 'sutjesci': 'Tjentište', 'dolina sutjeske': 'Tjentište', 'zlatni bor': 'Čelebići',
           'berka': 'Berkasovo', 'sid banovci': 'Šidski Banovci', 'sremski front': None,
           'srem': None, 'istocna bosna': None, 'sandzak': None, 'bosna': None, 'neretva': None, 'drina': None,
           'crna gora': None, 'hercegovina': None, 'dalmacija': None, 'slavonija': None, 'krajina': None,
           'srbija': None, 'lika': None,
           # Treća krajiška's records: hamlets and salaši the gazetteer lacks, given the place they belong to
           'novak bapske': 'Bapska', 'novak bapska': 'Bapska', 'novak babske': 'Bapska', 'novak babska': 'Bapska',
           'kozjakovom salasu': 'Šid', 'kozjakov salas': 'Šid', 'grcica salas': 'Šid',
           'govze na zelengori': 'Zelengora', 'govze': 'Zelengora', 'luckih koliba': 'Zelengora',
           'luckih koliba na zelengori': 'Zelengora', 'zecjem brdu': 'Zečje Brdo', 'popova mosta na sutjesci': 'Tjentište',
           'popovog mosta na sutjesci': 'Tjentište', 'scepan polja na sutjesci': 'Šćepan-Polje', 'ubovica dolini': 'Ubovići',
           'turbet': 'Turbe', 'vizica na fruskoj gori': 'Vizić', 'berka u sremu': 'Berak', 'lovasa u sremu': 'Lovas',
           'ruseva u slavoniji': 'Ruševo', 'han kolima': 'Han Kola'}
PREFIX = re.compile(r'^(?:kod|na|u|s\.|sel[oa]|kraj|pod|iznad|blizu|pored|okolin[ai]|rejon|podrucje|bolnica u|u bolnici u|'
                    r'na putu|izmedu|na planini|planina|planini|grad)\s+', re.I)
CYR = dict(zip('абвгдђежзијклљмнњопрстћуфхцчџш', ['a', 'b', 'v', 'g', 'd', 'đ', 'e', 'ž', 'z', 'i', 'j', 'k', 'l', 'lj', 'm',
                                                  'n', 'nj', 'o', 'p', 'r', 's', 't', 'ć', 'u', 'f', 'h', 'c', 'č', 'dž', 'š']))


def fold(s: str) -> str:
    s = ''.join(CYR.get(c, c) for c in s.lower())
    s = s.replace('đ', 'd').replace('dj', 'd')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9 ]+', ' ', s).strip()


def gazetteer():
    index = collections.defaultdict(list)
    for cc in COUNTRIES:
        with zipfile.ZipFile(GEONAMES / f'{cc}.zip') as z:
            for line in z.read(f'{cc}.txt').decode('utf-8').splitlines():
                f = line.split('\t')
                if f[6] not in ('P', 'T', 'H', 'L', 'S'):
                    continue
                entry = (float(f[5]), float(f[4]), f[6], int(f[14] or 0), f[1])
                keys = {fold(f[1]), fold(f[2])} | {fold(a) for a in f[3].split(',') if a}
                for k in keys:
                    if k:
                        index[k].append(entry)
    return index


def km(a, b):
    return math.hypot((a[0] - b[0]) * 111.32 * math.cos(math.radians((a[1] + b[1]) / 2)), (a[1] - b[1]) * 110.57)


# endings of the locative or genitive, and the nominative endings they may come from
CASE_RULES = [('lju', 'lje'), ('nju', 'nje'), ('ku', 'ak'), ('cu', 'ce'), ('cu', 'ac'), ('ca', 'ac'), ('aca', 'ci'),
              ('ima', 'i'), ('ama', 'e'), ('ama', 'a'), ('im', 'e'), ('u', 'a'), ('u', 'o'), ('u', 'e'), ('u', ''),
              ('eta', 'e'), ('alja', 'lja'), ('ova', 'ovo'), ('a', ''), ('a', 'o'), ('e', 'a'), ('i', 'a'),
              ('i', ''), ('og', 'o'), ('og', 'i'), ('oj', 'a'), ('om', 'o')]
# the books' abbreviations before a place's name ("Sl. Brod", "G. Slatnik"); OCR reads Sl. as "SI." or "Si."
ABBREV = {'sl': 'slavonski', 'si': 'slavonski', 'g': 'gornji', 'gor': 'gornji', 'd': 'donji', 'v': 'veliki',
          'vel': 'veliki', 'm': 'mali', 'b': 'bosanski', 'bos': 'bosanski', 'st': 'stari', 'n': 'novi'}


def variants(name: str) -> list[str]:
    """The name as printed, and the nominatives a locative or genitive could come from: each word may take its own
    ending ("Bežanijskoj kosi" is Bežanijska Kosa, "Baškim Oštarijama" Baške Oštarije), and an abbreviation before
    it is written out"""
    n = fold(name)
    words = [ABBREV.get(w, w) for w in n.split()]
    if not words:
        return [n]
    def forms(w):
        f = [w]
        for old, new in CASE_RULES:
            if w.endswith(old) and len(w) > len(old) + 2:
                f.append(w[: -len(old)] + new)
        return list(dict.fromkeys(f))
    combos = ['']
    for w in words[:4]:
        combos = [f'{c} {f}'.strip() for c in combos for f in forms(w)][:400]
    return list(dict.fromkeys([n, ' '.join(words)] + combos))


def lookup(index, name, anchor, radius, classes=('P', 'T', 'H', 'L', 'S'), towns=False):
    """The place of that name nearest `anchor` within `radius` km, a settlement preferred to a mountain or a
    locality a few km nearer, and those to a river. With `towns`, a town of 5,000 or more of that name anywhere
    when nothing lies within reach (the wounded died in hospitals far from the front)"""
    penalty = {'P': 0, 'T': 8, 'S': 8, 'L': 8, 'H': 25}
    best, town = None, None
    for v in variants(name):
        for lon, lat, fc, pop, gname in index.get(v, []):
            if fc not in classes:
                continue
            d = km((lon, lat), anchor)
            # a place's own name before one GeoNames only lists among its other names (Vrbovec, not Vrbovec Samoborski)
            # and, between two of the same name about as near, the bigger
            score = (d + penalty[fc] + (5 if v != fold(name) else 0) + (25 if fold(gname) != v else 0)
                     - min(10.0, 3 * math.log10(pop + 1)))
            if d <= radius and (best is None or score < best[0]):
                best = (score, (lon, lat), gname)
            if fc == 'P' and pop >= 5000 and v == fold(name) and (town is None or d < town[0]):
                town = (d, (lon, lat), gname)
    if best:
        return best[1], best[2]
    if towns and town:
        return town[1], town[2]
    return None, None


MONTH_WORDS = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'august', 'septemb', 'oktob', 'novemb',
               'decemb']


def month_of(text: str):
    """The year and month of a date of death, as numbers ("12. 5. 1943") or in words ("krajem maja 1943")"""
    m = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', text) or re.search(r'(\d{1,2})\.\s*(\d{4})', text)
    if not m:
        w = re.search(r'([a-zčćšžđ]+)\s+(\d{4})', text.lower().replace('avgust', 'august'))
        if not w:
            return None
        mo = next((i + 1 for i, s in enumerate(MONTH_WORDS) if w.group(1).startswith(s)), None)
        if mo is None or (MONTH_WORDS[mo - 1] in ('jun', 'jul') and not w.group(1).startswith(('juna', 'jula', 'jun ', 'jul '))
                          and w.group(1) not in ('jun', 'jul', 'juna', 'jula')):
            return None
        yr = int(w.group(2))
        if not 1941 <= yr <= 1945:
            return None
        return f'{yr}-{mo:02d}'
    mo, yr = (int(m.group(2)), int(m.group(3))) if m.lastindex == 3 else (int(m.group(1)), int(m.group(2)))
    if not (1941 <= yr <= 1945 and 1 <= mo <= 12):
        return None
    return f'{yr}-{mo:02d}'


def main():
    samples = '--samples' in sys.argv
    map_ts = (MAPA / 'map1941.ts').read_text(encoding='utf-8')
    proj_meta = json.loads(re.search(r'export const PROJ = (\{.*\})', map_ts).group(1))
    proj = Projection(proj_meta)
    proj.k, proj.x0, proj.y0 = proj_meta['k'], proj_meta['x0'], proj_meta['y0']
    index = gazetteer()

    for key, unit in UNITS.items():
        route = []
        for d, name, lon, lat, label, kind in unit['route']:
            if name.startswith('='):                # placed by hand: GeoNames has another place of that name
                name, pos = name[1:], (lon, lat)
                route.append({'date': d, 'place': name, 'lon': lon, 'lat': lat, 'label': label, 'kind': kind})
                continue
            pos, gname = lookup(index, name, (lon, lat), 30)
            if pos is None:
                print(f'  route: {name} not in GeoNames near {lon}, {lat}; kept as given')
                pos = (lon, lat)
            route.append({'date': d, 'place': name, 'lon': pos[0], 'lat': pos[1], 'label': label, 'kind': kind})

        def where(month: str):
            """The route's position in the middle of a month"""
            t = date.fromisoformat(f'{month}-15').toordinal()
            pts = [(date.fromisoformat(r['date'] if len(r['date']) == 10 else r['date'] + '-15').toordinal(), (r['lon'], r['lat'])) for r in route]
            if t <= pts[0][0]:
                return pts[0][1]
            for (t1, p1), (t2, p2) in zip(pts, pts[1:]):
                if t1 <= t <= t2:
                    f = (t - t1) / ((t2 - t1) or 1)
                    return (p1[0] + (p2[0] - p1[0]) * f, p1[1] + (p2[1] - p1[1]) * f)
            return pts[-1][1]

        records = json.loads((ROOT / 'website' / 'public' / unit['data']).read_text(encoding='utf-8'))
        fallen = collections.defaultdict(lambda: {'n': 0, 'months': collections.Counter(), 'ids': collections.defaultdict(list)})
        totals = collections.Counter()
        killed = collections.defaultdict(list)          # month -> the killed, placed on the map or not
        unplaced = collections.Counter()
        placed = 0
        for r in records:
            place, when = r.get('death_place'), r.get('death_date')
            if not place or not when or r.get('death_type') != 'poginuo':   # killed: not died, missing or captured
                continue
            month = month_of(when)
            if not month:
                continue
            totals[month] += 1
            killed[month].append(r['soldier_id'])
            parts = [p.strip() for p in place.split(',') if p.strip()]
            head = PREFIX.sub('', parts[0]).strip()
            head = PREFIX.sub('', head).strip()
            head = re.split(r'\s+kod\s+', head)[0].strip()       # "Gračanima kod Zagreba": the place, not the town
            alias = ALIASES.get(fold(head), head)
            if alias is None:
                unplaced[head] += 1
                continue
            route_at = where(month)
            pos = None
            if len(parts) > 1:                      # the municipality (or mountain) the entry names
                hint_name = PREFIX.sub('', parts[1]).strip()
                hint_name = ALIASES.get(fold(hint_name), hint_name)
                hint = lookup(index, hint_name, route_at, 150)[0] if hint_name else None
                if hint:
                    pos, gname = lookup(index, alias, hint, 35)
            if pos is None:
                pos, gname = lookup(index, alias, route_at, 90, towns=True)
            if pos is None:
                unplaced[head] += 1
                continue
            placed += 1
            spot = fallen[(round(pos[0], 3), round(pos[1], 3))]
            spot['n'] += 1
            spot['months'][month] += 1
            spot['ids'][month].append(r['soldier_id'])
            spot.setdefault('names', collections.Counter())[head] += 1      # as the book writes it: Sutjeska, not Tjentište
        total = sum(totals.values())
        print(f'{unit["name"]}: {placed} of {total} fallen placed at {len(fallen)} places '
              f'({100 * placed / total:.0f}%)')
        if samples:
            print('  not placed:', ', '.join(f'{p} {n}' for p, n in unplaced.most_common(40)))

        def xy(lon, lat):
            x, y = proj(lon, lat)
            return round(x, 1), round(y, 1)

        route_out = []
        for r in route:
            x, y = xy(r['lon'], r['lat'])
            route_out.append({'date': r['date'], 'place': r['place'], 'x': x, 'y': y, 'label': r['label'], 'kind': r['kind'],
                              'about': unit['about'].get(r['date']) if r['label'] else None})
        missing = [r['date'] for r in route if r['label'] and r['date'] not in unit['about']]
        if missing:
            print('  events without a description:', ', '.join(missing))
        fallen_out, killed_at = [], []
        for (lon, lat), spot in sorted(fallen.items(), key=lambda kv: -kv[1]['n']):
            x, y = xy(lon, lat)
            fallen_out.append({'place': spot['names'].most_common(1)[0][0], 'x': x, 'y': y, 'n': spot['n'],
                               'months': dict(sorted(spot['months'].items()))})
            killed_at.append(dict(sorted(spot['ids'].items())))

        out = MAPA / 'units' / f'{key}.ts'
        out.parent.mkdir(exist_ok=True)
        lines = [
            f'// Generated by scripts/make_unit_route.py: {unit["name"]}\'s way through the war. Do not edit by hand.',
            '// Places from GeoNames (CC BY 4.0); the fallen from the unit\'s records (death_place, death_date).',
            '',
            "export type Waypoint = { date: string; place: string; x: number; y: number; label: string | null;",
            "  kind: 'formed' | 'battle' | 'stop' | 'end' | 'transfer'; about: string | null }",
            f'export const SOURCE = {json.dumps(unit["source"], ensure_ascii=False)}',
            f'export const ROUTE: Waypoint[] = {json.dumps(route_out, ensure_ascii=False)}',
            '',
            '// where its fighters were killed (poginuli): one spot per place, with how many in each month',
            'export type FallenSpot = { place: string; x: number; y: number; n: number; months: Record<string, number> }',
            f'export const FALLEN: FallenSpot[] = {json.dumps(fallen_out, ensure_ascii=False)}',
            '',
            '// all killed in each month, placed on the map or not',
            f'export const FALLEN_BY_MONTH: Record<string, number> = {json.dumps(dict(sorted(totals.items())))}',
            '',
        ]
        out.write_text('\n'.join(lines), encoding='utf-8')
        print(f'  wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)')

        # Who they are, for the list a count on the map opens (mapa/spisak): a module of its own, so the map's
        # pages don't carry thousands of ids
        ids_out = MAPA / 'units' / f'{key}-killed.ts'
        ids_out.write_text('\n'.join([
            f'// Generated by scripts/make_unit_route.py: who of {unit["name"]} was killed, as the map counts them.',
            '// Do not edit by hand.',
            '',
            f'export const DATA_FILE = {json.dumps("/" + unit["data"])}',
            '// soldier ids by month: every count in FALLEN_BY_MONTH',
            f'export const KILLED_BY_MONTH: Record<string, string[]> = {json.dumps(dict(sorted(killed.items())))}',
            '// soldier ids by spot (in the order of FALLEN) and month',
            f'export const KILLED_AT: Record<string, string[]>[] = {json.dumps(killed_at)}',
            '',
        ]), encoding='utf-8')
        print(f'  wrote {ids_out.relative_to(ROOT)} ({ids_out.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
