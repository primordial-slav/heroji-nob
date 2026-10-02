"""
Find and install unit photos from the Biblioteka Znaci photo gallery (znaci.org).

A unit's photo must show that unit's soldiers (a group: standing, marching,
lined up) and znaci.org's own description must name the unit. Candidates are
every photo tagged with the unit's znaci.org entry (odrednica) plus every
photo whose description matches the unit's caption pattern.

Usage:
    python scripts/find_unit_photos.py --list                 # units, chosen photo, candidate counts
    python scripts/find_unit_photos.py --candidates KEY [...] # print candidates, write contact sheets
    python scripts/find_unit_photos.py --identify             # which znaci photo each current site image is
    python scripts/find_unit_photos.py --book KEY PDF [...]   # photos + printed captions in the unit's book(s)
    python scripts/find_unit_photos.py --apply [KEY ...]      # download chosen photos, write docs/UNIT_PHOTOS.md

Adding a unit: add an entry to UNITS with its tag slug(s) from
https://znaci.org/odrednice.php and a caption pattern, run --candidates,
look at the contact sheets (photos, and the museum caption cards of tagged
photos that have no typed description), set `photo` (plus `card`, `crop`,
`note` as needed), run --apply KEY, and point the unit's `image` in
website/app/data/units.ts at /images/<KEY>.jpg.

When the gallery has nothing, try the unit's own book on znaci.org: its
landing page (e.g. https://znaci.org/00001/267.htm) links the whole book or
its chapters as PDFs. `--book KEY 00001/267.pdf` lists every photo printed in
it with the caption under it and writes a contact sheet; check the caption on
the rendered page, then set `book=dict(pdf=..., page=..., xref=..., caption=...)`
instead of `photo`.

Everything fetched is cached in data-extraction/.cache/znaci_photos/.
All photos on znaci.org are marked Public Domain.
"""

import argparse
import io
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

BASE = "https://www.znaci.org"
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data-extraction" / ".cache" / "znaci_photos"
IMAGES = ROOT / "website" / "public" / "images"
SHEETS = CACHE / "sheets"
BOOKS = CACHE / "books"
DOC = ROOT / "docs" / "UNIT_PHOTOS.md"
MAX_SIDE = 1200  # longest side of an installed photo (the site serves images unoptimized)
JPEG_QUALITY = 82

# Ordinal forms used in captions: "13.", "XIII", "trinaeste" ...
_WORDS = {
    1: "prv", 2: "drug", 3: "tre[cć]", 4: "[cč]etvrt", 5: "pet", 6: "[sš]est", 7: "sedm",
    8: "osm", 9: "devet", 10: "deset", 11: "jedanaest", 12: "dvanaest", 13: "trinaest", 14: "[cč]etrnaest", 15: "petnaest",
    16: "[sš]esnaest", 17: "sedamnaest", 18: "osamnaest", 19: "devetnaest", 21: "dvadeset\\s*prv",
    25: "dvadeset\\s*pet", 32: "trideset\\s*drug", 53: "pedeset\\s*tre[cć]",
}
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI",
          12: "XII", 13: "XIII", 14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 21: "XXI",
          25: "XXV", 32: "XXXII", 53: "LIII"}


def nth(n, stem):
    """Caption pattern for 'N. <stem>' in any case ending: 13. proleterske, trinaeste proleterske."""
    forms = [r"(?<![\d.])%d\s*\.?" % n, r"\b%s\.?" % _ROMAN[n]]
    if n in _WORDS:
        forms.append(r"\b%s[a-zčćšž]*" % _WORDS[n])
    return r"(?:%s)\s+(?:\w+\s+)?%s" % ("|".join(forms), stem)


# key: image file name (without .jpg) under website/public/images/.
# tags: znaci.org odrednica slugs. caption: regex (case-insensitive) naming the unit.
# photo: chosen znaci.org photo id (None = no photo that qualifies yet).
# card: the museum caption card's text, for photos with no typed description on znaci.org.
# crop: (left, top, right, bottom) as fractions, to trim empty ground or sky.
# book: a photo printed in the unit's book on znaci.org: dict(pdf, page, xref, caption).
# descreen: blur radius that smooths a coarse halftone print (book photos).
# source: a photo from elsewhere (url, caption), kept as the file already on the site.
# note: anything the next person should know (shown in docs/UNIT_PHOTOS.md).
UNITS = {
    # --- on the site ---
    "prva-licka-brigada": dict(
        name="1. lička proleterska brigada", tags=["1-licka-proleterska-udarna-brigada"],
        caption=nth(1, r"li[cč]k") + "|mark[oa] ore[sš]kovi", photo=10298),
    "prva-proleterska-brigada": dict(
        name="1. proleterska brigada", tags=["1-proleterska-udarna-brigada"],
        caption=nth(1, r"proletersk[aeiou]\w*\s+(?:udarn\w+\s+)?brigad"), photo=None, source=dict(
            url="https://commons.wikimedia.org/wiki/File:Tito_predaje_zastavu_Prvoj_proleterskoj_brigadi.jpg",
            caption="Vrhovni komandant Tito predaje vojničku zastavu I proleterskoj brigadi u Bosanskom Petrovcu 7. novembra 1942. godine.")),
    "ljubljanska-brigada": dict(
        name="10. slovenska (Ljubljanska) brigada", tags=["10-slovenska-udarna--brigada--ljubljanska"],
        caption=r"ljubljansk\w+\s+brigad|\bljubljan[cč]ani|10\.?\s*SNOUB|" + nth(10, r"sloven"), photo=6014),
    "druga_licka": dict(
        name="2. lička proleterska brigada", tags=["2-licka-proleterska-udarna-brigada"],
        caption=nth(2, r"li[cč]k"), photo=8570, card="Jedinice II ličke brigade na položaju kod Vrlike u Dalmaciji u borbi sa Italijanima, 1943. godine."),
    "treca-proleterska-brigada": dict(
        name="3. proleterska (sandžačka) brigada", tags=["3-proleterska-sandzacka-udarna-brigada"],
        caption=nth(3, r"proletersk") + r"|sand[zž]a[cč]k\w+\s+(?:proletersk\w+\s+)?brigad", photo=6660, card="Borci III sandžačke brigade u Pljevljima 1943. na dan proslave 26-godišnjice Oktobarske revolucije."),
    "13-proleterska-brigada": dict(
        name="13. proleterska brigada \"Rade Končar\"", tags=["13-proleterska-udarna-brigada-rade-koncar"],
        caption=nth(13, r"proletersk") + r"|brigad\w+\s+\"?rade kon[cč]ar", photo=8152, card="Borci XIII proleterske brigade u Livnu, januara 1943. godine."),
    "2-dalmatinska-brigada": dict(
        name="2. dalmatinska proleterska brigada", tags=["2-dalmatinska-proleterska-udarna-brigada"],
        caption=nth(2, r"dalmatinsk"), photo=7549, card="Hercegovački i dalmatinski partizani ulaze u Dubrovnik - borci II dalmatinske brigade, oktobar 1944."),
    "4-splitska-brigada": dict(
        name="4. dalmatinska (splitska) brigada", tags=["4-dalmatinska-udarna-brigada"],
        caption=nth(4, r"dalmatinsk") + r"|splitsk\w+\s+brigad", photo=None,
        book=dict(pdf="00001/89_5.pdf", page=14, xref=63, caption="Postrojavanje 4. bataljona, Rujani, travanj 1944."),
        descreen=1.2,
        note="A battalion of the brigade, in its own book. The gallery's only photo naming the brigade is a studio portrait of four leaders (13383); "
             "the image here before was znaci 3966, Split volunteers in 1943, which doesn't name the brigade."),
    "prva-vojvodjanska-brigada": dict(
        name="1. vojvođanska brigada", tags=["1-vojvodjanska-udarna-brigada"],
        caption=nth(1, r"vojvo(?:đ|dj|d)ansk"), photo=14761, card="Borci 1. bataljona 1. vojvodjanske brigade prilikom oslobodjenja Loznice 24.09.1944."),
    "peta-kozaracka-brigada": dict(
        name="5. krajiška (kozaračka) brigada", tags=["5-krajiska-kozarska-udarna-brigada"],
        caption=nth(5, r"(?:krajisk\w+\s+)?\(?koza(?:ra[cč]k|rsk)") + r"|koza(?:ra[cč]k|rsk)\w+\s+brigad|" + nth(5, r"kraji[sš]k"),
        photo=13908, crop=(0.05, 0.12, 0.75, 0.68)),
    "druga-vojvodjanska-brigada": dict(
        name="2. vojvođanska brigada", tags=["2-vojvodjanska-udarna-brigada"],
        caption=nth(2, r"vojvo(?:đ|dj|d)ansk"), photo=None,
        book=dict(pdf="00001/72_4.pdf", page=4, xref=15, caption="Jun 1943. Borci 2. vojvođanske NOU brigade u Virču"),
        descreen=1.4,
        note="The image here before was znaci 3413, 'Pokret vojvođanskih jedinica kroz Bosnu', which doesn't name the brigade."),
    "osma-krajiska-brigada": dict(
        name="8. krajiška brigada", tags=["8-krajiska-brigada"],
        caption=nth(8, r"kraji[sš]k"), photo=5046, note="The brigade's artillery; the only photo naming the brigade."),
    "sesta-krajiska-brigada": dict(
        name="6. krajiška brigada", tags=["6-krajiska-udarna-brigada"],
        caption=nth(6, r"kraji[sš]k"), photo=16043),
    "cetvrta-krajiska-brigada": dict(
        name="4. krajiška brigada", tags=["4-krajiska-udarna-brigada"],
        caption=nth(4, r"kraji[sš]k"), photo=15181, crop=(0.0, 0.0, 1.0, 0.8)),
    "treca-krajiska-brigada": dict(
        name="3. krajiška proleterska brigada", tags=["3-krajiska-proleterska-udarna-brigada"],
        caption=nth(3, r"kraji[sš]k"), photo=15438),
    "17-slavonska-brigada": dict(
        name="17. slavonska brigada", tags=["17-slavonska-udarna-brigada"],
        caption=nth(17, r"slavonsk"), photo=15450),
    "25-srpska-divizija": dict(
        name="25. srpska divizija", tags=["25-srpska-divizija-novj"],
        caption=nth(25, r"(?:srpsk\w+\s+)?(?:nou\s+)?divizij"), photo=5732, card="Prve jedinice Druge jugoslovenske armije, borci XXV divizije prelaze savski most kod Zagreba, 8.V.1945 g. /3 sata po podne/."),
    "1-sumadijska-brigada": dict(
        name="1. šumadijska brigada", tags=["1-sumadijska-brigada"],
        caption=nth(1, r"[sš]umadijsk\w+\s+brigad"), photo=None,
        book=dict(pdf="00001/102_4.pdf", page=10, xref=39,
                  caption="Borci 1. šumadijske brigade na dan formiranja 5. oktobra 1943. godine na planini Rudnik"),
        descreen=1.6, crop=(0.0, 0.08, 1.0, 0.78),
        note="Nothing in the gallery; the book's only group photo of the brigade is a coarse halftone print."),
    "18-slavonska-brigada": dict(
        name="18. slavonska brigada", tags=["18-slavonska-udarna-brigada"],
        caption=nth(18, r"slavonsk"), photo=13731),
    "4-banijska-brigada": dict(
        name="4. banijska brigada", tags=["4-banijska-udarna-brigada"],
        caption=nth(4, r"banijsk"), photo=None,
        book=dict(pdf="00001/188_3.pdf", page=32, xref=139, caption="Mineri i bombaši 4. brigade, jesen 1944."),
        note="Nothing in the gallery; from the brigade's zbornik (chapter 3)."),
    "4-srpska-brigada": dict(
        name="4. srpska (2. južnomoravska) brigada", tags=["4-srpska-brigada-2-juznomoravska"],
        caption=nth(4, r"srpsk\w+\s+brigad") + "|" + nth(2, r"ju[zž]nomoravsk\w+\s+brigad"), photo=4961, note="Under the brigade's earlier name, 2. južnomoravska; "
        "the brigade's book prints the same photo as 'Treći bataljon (crnotravski) u selu Brestovcu, Pusta reka, 5. decembar 1943.' (00001/149.pdf, p. 391)."),
    "7-vojvodjanska-brigada": dict(
        name="7. vojvođanska brigada", tags=["7-vojvodjanska-udarna-brigada"],
        caption=nth(7, r"vojvo(?:đ|dj|d)ansk"), photo=8998, card="Ulazak boraca 7. vojvodjanske brigade u Novi Sad, 23. oktobra 1944.g."),
    "19-bircanska-brigada": dict(
        name="19. birčanska brigada", tags=["19-bircanska-udarna-brigada"],
        caption=nth(19, r"bir[cč]ansk") + r"|bir[cč]ansk\w+\s+brigad", photo=None,
        book=dict(pdf="00001/267.pdf", page=236, xref=1175,
                  caption="Grupa boraca brigade u oslobođenoj Tuzli, septembra 1944."),
        crop=(0.0, 0.0, 0.94, 0.9),
        note="The gallery has only the brigade's staff (11254). The photo in the book is a scan of a page; the crop drops its page number and gutter."),
    # --- lined up (PDF downloaded, not parsed yet) ---
    "14-srpska-brigada": dict(
        name="14. srpska brigada", tags=["14-srpska-udarna-brigada"],
        caption=nth(14, r"srpsk\w+\s+(?:nou\s+|udarn\w+\s+)?brigad"), photo=None,
        book=dict(pdf="00001/66_5.pdf", page=18, xref=83,
                  caption="Brigada na maršu kroz Kragujevac krajem oktobra 1944."),
        descreen=0.8),
    "17-majevicka-brigada": dict(
        name="17. majevička brigada", tags=["17-majevicka-udarna-brigada"],
        caption=nth(17, r"majevi[cč]k"), photo=4853),
    "2-krajiska-brigada": dict(
        name="2. krajiška brigada", tags=["2-krajiska-udarna-brigada"],
        caption=nth(2, r"kraji[sš]k"), photo=6238, card="Kolona boraca Druge krajiške brigade."),
    "21-slavonska-brigada": dict(
        name="21. slavonska brigada", tags=["21-slavonska-udarna-brigada"],
        caption=nth(21, r"slavonsk"), photo=15707),
    "21-tuzlanska-brigada": dict(
        name="21. tuzlanska brigada", tags=["21-tuzlanska-udarna-brigada"],
        caption=nth(21, r"\(?tuzlansk") + r"|tuzlansk\w+\s+brigad", photo=None,
        book=dict(pdf="00001/250_3.pdf", page=18, xref=175, caption="Borci Brigade na ulicama Sarajeva"),
        note="From the book's first photo section (Sarajevo, April 1945)."),
    "25-brodska-brigada": dict(
        name="25. slavonska (brodska) brigada", tags=["25-slavonska-udarna-brigada-brodska"],
        caption=nth(25, r"(?:slavonsk|brodsk)") + r"|brodsk\w+\s+brigad", photo=None,
        book=dict(pdf="00001/262_5.pdf", page=42, xref=179, caption="April 1944 — Prvi vod 1. čete 1. bataljona"),
        note="A platoon of the brigade, in its own book. The photos whose captions name the brigade (entering Šabac, crossing the Vrbas) show mostly crowd and a ferry."),
    "25-srpska-brigada": dict(
        name="25. srpska (1. pirotska) brigada", tags=["25-srpska-brigada-1-pirotska"],
        caption=nth(25, r"srpsk\w+\s+(?:nou\s+)?brigad") + "|" + nth(1, r"pirotsk"), photo=None,
        book=dict(pdf="00001/215_5.pdf", page=59, xref=363,
                  caption="Defile jedinica 25. brigade, u Orahovcu, na proslavi 27. marta (1945)"),
        descreen=1.4),
    "3-makedonska-brigada": dict(
        name="3. makedonska brigada", tags=["3-makedonska-udarna-brigada"],
        caption=nth(3, r"makedonsk"), photo=13204),
    "11-dalmatinska-brigada": dict(
        name="11. dalmatinska brigada", tags=["11-dalmatinska-udarna-brigada-biokovska"],
        caption=nth(11, r"dalmatinsk") + r"|biokovsk\w* brigad", photo=None,
        book=dict(pdf="00003/547.pdf", page=28, xref=165, caption="Brigadna kolona na maršu preko Biokova, jesen 1943. godine"),
        crop=(0.0, 0.3, 1.0, 1.0),
        note="Nothing in the gallery is tagged with the brigade; the photo is from its own book (the crop keeps the column)."),
    "12-krajiska-brigada": dict(
        name="12. krajiška brigada", tags=["12-krajiska-udarna-brgada"],
        caption=nth(12, r"kraji[sš]k"), photo=None,
        book=dict(pdf="00001/168_1.pdf", page=24, xref=151, caption="Grupa boraca 3. bataljona, maja 1944. u okol. Prnjavora"),
        note="Nothing in the gallery is tagged with the brigade (its tag is spelled 12-krajiska-udarna-brgada); the photo is from its own book."),
    "17-srpska-brigada": dict(
        name="17. srpska brigada", tags=["17-srpska-brigada"],
        caption=nth(17, r"srpsk\w+\s+(?:nou\s+|udarn\w+\s+)?brigad"), photo=4976),
    "14-srednjobosanska-brigada": dict(
        name="14. srednjobosanska brigada", tags=["14-srednjobosanska-udarna-brigada"],
        caption=nth(14, r"srednjobosansk"), photo=9455),
    "3-vojvodjanska-brigada": dict(
        name="3. vojvođanska brigada", tags=["3-vojvodjanska-udarna-brigada"],
        caption=nth(3, r"vojvo[dđ]j?ansk"), photo=4863),
    "kalnicki-odred": dict(
        name="Kalnički partizanski odred", tags=["kalnicki-partizanski-odred"],
        caption=r"kalni[cč]k\w*\s+(?:partizansk\w*\s+|nop\s+)?odred", photo=None,
        book=dict(pdf="00003/558.pdf", page=410, xref=1807,
                  caption="Prva četa 1. bataljona KPO u listopadu 1943. u oslobođenom Ludbregu"),
        note="Nothing in the gallery is tagged with the odred; the photo is from its own book."),
    "posavsko-trebavski-odred": dict(
        name="Posavsko-trebavski partizanski odred", tags=[],
        caption=r"posavsko[\s-]*trebavsk\w*\s+(?:partizansk\w*\s+|nop\s+)?odred", photo=None,
        note="Nothing in the znaci.org gallery names the odred, and its book (00001/302, re-typeset) prints no photos."),
    "8-kordunaska-divizija": dict(
        name="8. kordunaška divizija", tags=[],
        caption=r"(?:\b8\.|osm\w+)\s+(?:kordunašk\w+\s+)?(?:udarn\w+\s+)?divizij", photo=None,
        book=dict(pdf="00003/571.pdf", page=250, xref=1127, caption="Plaški, jesen 1944. Jurišni vod 1. brigade 8. divizije."),
        crop=(0.0, 0.07, 1.0, 1.0),
        note="Nothing in the gallery is a group of the division's soldiers; the photo is from its own zbornik (the crop drops the torn top edge)."),
    "cankarjeva-brigada": dict(
        name="Cankarjeva brigada", tags=[],
        caption=r"cankar\w*\s+brigad", photo=11247),
    "gubceva-brigada": dict(
        name="Gubčeva brigada", tags=[],
        caption=r"gub[cč]ev\w*\s+brigad", photo=None,
        book=dict(pdf="00003/782.pdf", page=221, xref=2012, caption="Skupina partizanov Gubčeve brigade. Fotografija je iz leta 1943"),
        crop=(0.0, 0.22, 1.0, 0.88),
        note="The gallery has no group of the brigade's soldiers; the photo is from its own book (the crop keeps the group)."),
    "dvanajsta-brigada": dict(
        name="Dvanajsta brigada (XII. SNOUB)", tags=[],
        caption=r"(?:XII\.?|dvanajst\w*)\s+(?:slovensk\w*\s+)?(?:snou\s+)?brigad", photo=None,
        book=dict(pdf="00003/814.pdf", page=150, xref=1273, caption="Skupina borcev in bork 1. bataljona Dvanajste brigade"),
        note="Nothing in the gallery names the brigade; the photo is from its own book."),
    "gradnikova-brigada": dict(
        name="Gradnikova brigada", tags=[],
        caption=r"(?:gradnikov|gori[sš]k)\w*\s+brigad", photo=None,
        book=dict(pdf="00003/825.pdf", page=84, xref=1237, caption="Prvi bataljon Gradnikove brigade na šentviški planoti konec maja 1943."),
        note="Nothing in the gallery names the brigade; the photo is from its own book."),
    "zidanskova-brigada": dict(
        name="Zidanškova brigada", tags=[],
        caption=r"zidan[sš]kov\w*\s+brigad", photo=None,
        book=dict(pdf="00003/776.pdf", page=706, xref=3719, caption="Borci 1. bataljona nad Ivnikom konec maja 1945"),
        crop=(0.0, 0.1, 1.0, 0.9),
        note="Nothing in the gallery names the brigade; the photo is from its own book (its 1st battalion)."),
    "skofjeloski-odred": dict(
        name="Škofjeloški odred", tags=[],
        caption=r"[sš]kofjelo[sš]k\w*\s+odred", photo=None,
        book=dict(pdf="00003/809.pdf", page=61, xref=585, caption="Borci škofjeloškega odreda v vasi Jesenica pri Bukovem na Cerkljanskem"),
        note="Nothing in the gallery names the odred; the photo is from its own book."),
    "18-hrvatska-brigada": dict(
        name="18. hrvatska istočnobosanska brigada", tags=["18-hrvatska-istocnobosanska-udarna-brigada"],
        caption=nth(18, r"hrvatsk"), photo=None,
        book=dict(pdf="00001/251_2.pdf", page=207, xref=1001,
                  caption="Defile boraca Brigade u oslobođenom Sarajevu, april 1945."),
        crop=(0.0, 0.06, 1.0, 1.0),
        note="Nothing in the gallery names the brigade; the photo is from its own book (the crop drops scan noise at the top)."),
    "32-zagorska-divizija": dict(
        name="32. zagorska divizija", tags=["32-zagorska-divizija-novj"],
        caption=nth(32, r"(?:zagorsk\w+\s+)?divizij") + r"|zagorsk\w+\s+divizij", photo=None,
        book=dict(pdf="00003/542.pdf", page=454, xref=2359,
                  caption="Kolona Brigade »Matija Gubec« ulazi u Zagreb 10. maja 1945. godine"),
        note="Matija Gubec was one of the division's brigades; in this book the caption sits above the photo."),
    "53-srednjobosanska-divizija": dict(
        name="53. srednjobosanska divizija", tags=["53-srednjobosanska-divizija-novj"],
        caption=nth(53, r"(?:srednjobosansk\w+\s+)?divizij"), photo=None,
        book=dict(pdf="00003/712.pdf", page=175, xref=1055,
                  caption="Bataljon pri štabu 53. divizije na željezničkoj stanici u Teslicu, pred polazak u akciju na ustaško uporište u selu Sivši, marta 1945. godine"),
        crop=(0.0, 0.0, 1.0, 0.74)),
    "7-crnogorska-omladinska-brigada": dict(
        name="7. crnogorska omladinska brigada \"Budo Tomović\"",
        tags=["7-crnogorska-omladinska-brigada-budo-tomovic"],
        caption=nth(7, r"crnogorsk\w+\s+omladinsk") + r"|budo tomovi", photo=7421, card="VII omladinska brigada \"Budo Tomović\" za vreme vežbe."),
    "tuzlanski-odred": dict(
        name="Tuzlanski partizanski odred", tags=[],
        caption=r"tuzlansk\w+\s+(?:partizansk\w+\s+|nop\s+)?odred", photo=None,
        book=dict(pdf="00003/469.pdf", page=68, xref=291, caption="Tuzlanski partizanski odred u Smolući juna 1944. godine"),
        descreen=0.6, crop=(0.0, 0.12, 1.0, 1.0),
        note="Nothing in the gallery. The other scan of the book (00002/403.pdf, p. 67) has the same photo at lower resolution; "
             "the faint lines at the top are the back of the page showing through."),
    "uzicki-odred": dict(
        name="Užički partizanski odred \"Dimitrije Tucović\"",
        tags=["uzicki-partizanski-odred-dimitrije-tucovic"],
        caption=r"u[zž]i[cč]k\w+\s+(?:partizansk\w+\s+)?odred|dimitrij\w+ tucovi", photo=None,
        book=dict(pdf="00001/196_7.pdf", page=8, xref=67,
                  caption="Jedinice Užičkog odreda, postrojene na užičkoj žitnoj pijaci, spremne za smotru pred komandantom Dušanom Jerkovićem"),
        note="From the book's photo chapter (1941)."),
    "1-dalmatinska-brigada": dict(
        name="1. dalmatinska proleterska brigada", tags=["1-dalmatinska-proleterska-udarna-brigada"],
        caption=nth(1, r"dalmatinsk"), photo=5070,
        note="znaci 9201 is the same photo, its caption card reading 'Prva dalmatinska brigada u maršu na oslobođenom Hvaru, septembra 1944.'"),
    "16-slavonska-omladinska-brigada": dict(
        name="16. slavonska omladinska brigada \"Jože Vlahović\"", tags=["16-omladinska-udarna-brigada-joza-vlahovic"],
        caption=nth(16, r"(?:slavonsk\w+\s+)?omladinsk") + r"|brigad\w+\s+\W?jo[zž][ea] vlahovi", photo=None,
        book=dict(pdf="00002/407.pdf", page=275, xref=1167, caption="Četa Omladinske brigade, Kordun, proljeće 1944."),
        note="The gallery has only a portrait of a boy soldier of the brigade (3956)."),
    "8-crnogorska-brigada": dict(
        name="8. crnogorska brigada", tags=["8-crnogorska-udarna-brigada"],
        caption=nth(8, r"crnogorsk"), photo=None,
        book=dict(pdf="00001/275.pdf", page=171, xref=715, caption="Borci 2 bataljona na maršu iz Beograda ka sremskom frontu"),
        note="The brigade's 2nd battalion, in its own book. The gallery has the crowd at the brigade's formation (6038), its staff "
             "(11155) and two combat photos captioned for the 5th, 7th and 8th Montenegrin brigades together."),
    "druga-proleterska-brigada": dict(
        name="2. proleterska brigada", tags=["2-proleterska-udarna-brigada"],
        caption=r"(?<![\d.])2\s*\.?\s+proletersk|\bdrug[aeiou]\w*\s+proletersk|\bII\.?\s+proletersk", photo=3451,
        note="The brigade on the march through eastern Bosnia toward Majevica, July 1943."),
    # The units Borci Sutjeske brings to the site
    "4-proleterska-brigada": dict(
        name="4. proleterska (crnogorska) brigada", tags=["4-proleterska-crnogorska-udarna-brigada"],
        caption=nth(4, r"(?:proletersk|crnogorsk)"), photo=13653),
    "5-proleterska-brigada": dict(
        name="5. proleterska (crnogorska) brigada", tags=["5-proterska-crnogorska-udarna-brigada"],
        caption=nth(5, r"(?:proletersk|crnogorsk)"), photo=8915),
    "6-istocnobosanska-brigada": dict(
        name="6. istočnobosanska proleterska brigada", tags=["6-istocnobosanska-proleterska-udarna-brigada"],
        caption=nth(6, r"(?:isto[cč]nobosansk|proletersk\w*\s+isto[cč]no)"), photo=15928),
    "10-hercegovacka-brigada": dict(
        name="10. hercegovačka brigada", tags=["10-hercegovacka-udarna-brigada"],
        caption=nth(10, r"hercegova[cč]k"), photo=10546),
    "7-banijska-brigada": dict(
        name="7. banijska brigada \"Vasilj Gaćeša\"", tags=["7-banijska-udarna-brigada-vasilj-gacesa"],
        caption=nth(7, r"banijsk") + r"|va[sz]il\w*\s+ga[cćč]e[sš]", photo=None,
        book=dict(pdf="00001/63_3.pdf", page=4, xref=15,
                  caption="Deo kolone grupe bataljona Banijskog NOP odreda, odnosno 7. banijske brigade »Vasilj Gaćeša«, u Moslavini 1942."),
        note="The gallery has only a column of the 7th Banija Division (10585); this is the brigade's own column, in its book."),
    "8-banijska-brigada": dict(
        name="8. banijska brigada", tags=["8-banijska-udarna-brigada"],
        caption=nth(8, r"banijsk"), photo=None,
        book=dict(pdf="00003/383.pdf", page=150, xref=1103, caption="Stroj 2. brigade na Sv. Duhu kod sela Vrpolje 5. novembra 1943."),
        note="The brigade lined up, as the 2nd brigade of the 7th Division (renumbered in September 1943), in its own book; "
             "the caption is printed above the photo. Nothing in the gallery."),
    "3-dalmatinska-brigada": dict(
        name="3. dalmatinska brigada", tags=["3-dalmatinska-udarna-brigada"],
        caption=nth(3, r"dalmatinsk"), photo=8504,
        note="At the brigade's formation; the date in the caption (17. 11.) differs from the odrednica's 12. 11. 1942."),
    "16-banijska-brigada": dict(
        name="16. banijska brigada", tags=["16-banijska-udarna-brigada"],
        caption=nth(16, r"banijsk"), photo=None),
    "7-krajiska-brigada": dict(
        name="7. krajiška brigada", tags=["7-krajiska-udarna-brigada"],
        caption=nth(7, r"kraji[sš]k"), photo=15178, crop=(0, 0.27, 1, 0.72),
        note="At the Sutjeska; the only photo of the brigade's fighters in the gallery."),
    "12-dalmatinska-brigada": dict(
        name="12. dalmatinska (1. otočka) brigada", tags=["12-dalmatinska-udarna-brigada-prva-otocka"],
        caption=nth(12, r"dalmatinsk") + r"|\b(?:1\.|prv\w+)\s+oto[cč]k", photo=5084),
    "15-majevicka-brigada": dict(
        name="15. majevička brigada", tags=["15-majevicka-udarna-brigada"],
        caption=nth(15, r"majevi[cč]k") + "|" + nth(1, r"majevi[cč]k"), photo=13981,
        note='At the Sutjeska, on Milinklade, 9 June 1943.'),
}

# Words that suggest a group of soldiers; words that suggest something else.
GROUP_WORDS = r"borc|bork|partizan|kolon|stroj|smotr|mar[sš]|pokret|bataljon|[cč]et[ae]\b|[cč]eti\b|vod\b|voda\b|jedinic|brigad[ae] u|odmor|prelaz|ulaz|defil|polaga|zakletv|mitraljez|grup"
OTHER_WORDS = r"komandant|komesar|na[cč]elnik|[sš]tab\b|[sš]taba\b|poginul|umrl|ubijen|streljan|sahran|grob|spomenik|le[sš]ev|portret|zastav|orden|priznanj|pismo|letak|dokument"


# ---------------------------------------------------------------- fetching

# znaci.org's certificate expired in 2026 and http redirects to https; these are
# read-only fetches of public-domain pages, so don't verify it.
_SSL = ssl._create_unverified_context()


def _get(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (knjiga-boraca photo finder)"})
            with urllib.request.urlopen(req, timeout=60, context=_SSL) as resp:
                return resp.read()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def _cached_json(name, build):
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    data = build()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def gallery():
    """{id: caption} for every photo in the gallery (one request)."""
    def build():
        html = _get(BASE + "/fotogalerija.php?slika_po_strani=100000").decode("utf-8", "replace")
        items = re.findall(r"fotografija\.php\?br=(\d+)'><img class='galerija-slika'[^>]*title='([^']*)'", html)
        return {i: unescape(t).strip() for i, t in items}
    return _cached_json("gallery.json", build)


def tag_photos(slug):
    """Photo ids tagged with a znaci.org entry, in the order the entry page lists them."""
    def build():
        html = _get(BASE + "/odrednica.php?slug=" + urllib.parse.quote(slug)).decode("utf-8", "replace")
        tag_id = re.search(r'id="odrednica_id" value="(\d+)"', html).group(1)
        total = int(re.search(r'id="broj_fotografija" value="(\d+)"', html).group(1))
        ids = re.findall(r"fotografija\.php\?br=(\d+)", html)
        if total > len(ids):
            more = _get("%s/api/ajax-fotografije.php?br=%s&ucitaj_od=%d&ucitaj_do=%d"
                        % (BASE, tag_id, len(ids), total + 10)).decode("utf-8", "replace")
            ids += re.findall(r"fotografija\.php\?br=(\d+)", more)
        seen = []
        for i in ids:
            if i not in seen:
                seen.append(i)
        return seen
    return _cached_json("tag_%s.json" % slug, build)


def photo_details(pid):
    """Description, date, region and tags from the photo's page."""
    def build():
        html = _get("%s/fotografija.php?br=%s" % (BASE, pid)).decode("utf-8", "replace")
        def field(pat):
            m = re.search(pat, html, re.S)
            return unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
        return {
            "id": pid,
            "caption": re.sub(r"^Nije unet$", "", field(r"<span id='opis'>(.*?)</span>")),
            "original_caption": bool(re.search(r"o_slikama/%s\.jpg" % pid, html)),
            "date": field(r"<b>Datum: </b><span>(.*?)</span>").rstrip("."),
            "region": field(r"<b>Oblast:</b>(.*?)<br>"),
            "source": field(r"<b>Izvor:</b>(.*?)<br>"),
            "tags": re.findall(r"odrednica\.php\?slug=([^'\"]+)", html.split("Oznake:")[-1]),
        }
    return _cached_json("photo/%s.json" % pid, build)


def caption_card(pid):
    """The scanned museum caption card (znaci.org shows it as 'Izvorni opis')."""
    path = CACHE / "cards" / ("%s.jpg" % pid)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get("%s/o_slikama/%s.jpg" % (BASE, pid)))
    return path


def thumbnail(pid):
    path = CACHE / "thumbs" / ("%s.jpg" % pid)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get("%s/images/thumbnails/%s.jpg" % (BASE, pid)))
    return path


def book_pdf(path):
    """A znaci.org book or chapter PDF, e.g. '00001/267.pdf', cached locally."""
    local = BOOKS / path.replace("/", "_")
    if not local.exists():
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(_get("%s/%s" % (BASE, path)))
    return local


def book_photos(path):
    """Every photo printed in a book PDF with the caption under it (or above, if none below)."""
    import fitz
    sys.path.insert(0, str(ROOT / "data-extraction"))
    from _parser_scaffold import cyrillic_to_latin
    photos = []
    for pno, page in enumerate(fitz.open(book_pdf(path)), 1):
        area = page.rect.width * page.rect.height
        blocks = page.get_text("blocks")
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            if not info["xref"] or (x1 - x0) * (y1 - y0) < 0.06 * area:
                continue
            below = sorted((b for b in blocks if 0 <= b[1] - y1 + 2 < 90 and b[2] > x0 and b[0] < x1), key=lambda b: b[1])
            above = sorted((b for b in blocks if 0 <= y0 - b[3] + 2 < 60 and b[2] > x0 and b[0] < x1), key=lambda b: -b[3])
            near = below[:1] or above[:1]
            caption = " ".join(cyrillic_to_latin(near[0][4]).split()) if near else ""
            photos.append({"pdf": path, "page": pno, "xref": info["xref"], "caption": caption})
    return photos


def book_image(path, xref):
    """A photo from a book PDF at the resolution it's embedded in."""
    import fitz
    from PIL import Image
    pix = fitz.Pixmap(fitz.open(book_pdf(path)), xref)
    if pix.n - pix.alpha >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def book_sheet(key, photos, per_sheet=18):
    """Numbered grids of a book's photos, labelled page/xref."""
    from PIL import Image, ImageDraw
    SHEETS.mkdir(parents=True, exist_ok=True)
    font = _font(18)
    cell_w, cell_h, cols = 440, 340, 6
    paths = []
    for s in range(0, len(photos), per_sheet):
        chunk = photos[s:s + per_sheet]
        sheet = Image.new("RGB", (cols * cell_w, ((len(chunk) + cols - 1) // cols) * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for n, ph in enumerate(chunk):
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            im = book_image(ph["pdf"], ph["xref"])
            im.thumbnail((cell_w - 10, cell_h - 34))
            sheet.paste(im, (x + 5, y + 30))
            draw.text((x + 5, y + 5), "p. %d / xref %d" % (ph["page"], ph["xref"]), fill="black", font=font)
        path = SHEETS / ("%s_book_%d.jpg" % (key, s // per_sheet + 1))
        sheet.save(path, quality=80)
        paths.append(path)
    return paths


# ---------------------------------------------------------------- candidates

def candidates(key):
    """Candidate photos for a unit: tagged first (znaci's order), then caption matches."""
    unit = UNITS[key]
    pat = re.compile(unit["caption"], re.I)
    ids = []
    for slug in unit["tags"]:
        ids += [i for i in tag_photos(slug) if i not in ids]
    ids += [i for i, cap in gallery().items() if pat.search(cap) and i not in ids]
    with ThreadPoolExecutor(max_workers=4) as ex:
        details = list(ex.map(photo_details, ids))
    out = []
    for d in details:
        cap = d["caption"]
        d["names_unit"] = bool(pat.search(cap))
        d["tagged"] = any(t in d["tags"] for t in unit["tags"])
        d["group"] = bool(re.search(GROUP_WORDS, cap, re.I))
        d["other"] = bool(re.search(OTHER_WORDS, cap, re.I))
        out.append(d)
    return out


def contact_sheet(key, cands, per_sheet=24):
    """Numbered thumbnail grids for looking at the candidates."""
    from PIL import Image, ImageDraw
    SHEETS.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(thumbnail, [c["id"] for c in cands]))
    font = _font(18)
    cell_w, cell_h, cols = 330, 270, 6
    paths = []
    for s in range(0, len(cands), per_sheet):
        chunk = cands[s:s + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for n, c in enumerate(chunk):
            x, y = (n % cols) * cell_w, (n // cols) * cell_h
            try:
                im = Image.open(thumbnail(c["id"])).convert("RGB")
                im.thumbnail((cell_w - 10, cell_h - 34))
                sheet.paste(im, (x + 5, y + 30))
            except Exception:
                pass
            mark = ("U" if c["names_unit"] else "-") + ("T" if c["tagged"] else "-")
            draw.text((x + 5, y + 5), "%s  %s" % (c["id"], mark), fill="black", font=font)
        path = SHEETS / ("%s_%d.jpg" % (key, s // per_sheet + 1))
        sheet.save(path, quality=80)
        paths.append(path)
    return paths


def card_sheet(key, cands):
    """Caption cards of tagged photos that have no typed description, stacked for reading."""
    from PIL import Image, ImageDraw
    font = _font(22)
    tiles = []
    for c in cands:
        try:
            im = Image.open(caption_card(c["id"])).convert("RGB")
        except Exception:
            continue
        im.thumbnail((900, 300))
        tile = Image.new("RGB", (900, im.size[1] + 30), "white")
        tile.paste(im, (0, 30))
        ImageDraw.Draw(tile).text((5, 3), c["id"], fill="red", font=font)
        tiles.append(tile)
    paths = []
    for s in range(0, len(tiles), 8):
        chunk = tiles[s:s + 8]
        sheet = Image.new("RGB", (900, sum(t.size[1] for t in chunk)), "white")
        y = 0
        for t in chunk:
            sheet.paste(t, (0, y))
            y += t.size[1]
        path = SHEETS / ("%s_cards_%d.jpg" % (key, s // 8 + 1))
        sheet.save(path, quality=85)
        paths.append(path)
    return paths


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------- identify current images

def _dhash(img, size=16):
    from PIL import Image
    g = img.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (px[r * (size + 1) + c] > px[r * (size + 1) + c + 1])
    return bits


def identify():
    """Match every image under website/public/images/ against the whole znaci.org gallery."""
    from PIL import Image
    gal = gallery()
    ids = list(gal)
    print("Fetching %d gallery thumbnails (cached after the first run)..." % len(ids))
    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(lambda i: _safe(thumbnail, i), ids))
    hashes = _cached_json("thumb_hashes.json", lambda: {})
    for i in ids:
        if i not in hashes:
            try:
                hashes[i] = _dhash(Image.open(thumbnail(i)))
            except Exception:
                hashes[i] = None
    (CACHE / "thumb_hashes.json").write_text(json.dumps(hashes), encoding="utf-8")
    result = {}
    for f in sorted(IMAGES.glob("*.jpg")):
        h = _dhash(Image.open(f))
        best = sorted((bin(h ^ v).count("1"), i) for i, v in hashes.items() if v is not None)[:2]
        dist, pid = best[0]
        result[f.name] = {"id": pid if dist <= 40 else None, "distance": dist, "runner_up": best[1][0]}
        cap = gal.get(pid, "") if dist <= 40 else ""
        print("%-40s %s" % (f.name, ("znaci %s (d=%d): %s" % (pid, dist, cap)) if dist <= 40
                            else "no match (closest %s, d=%d)" % (pid, dist)))
    return result


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception:
        return None


# ---------------------------------------------------------------- install

def install(key):
    """Download the unit's chosen photo into website/public/images/<key>.jpg (unless it's already there)."""
    from PIL import Image, ImageFilter, ImageOps
    unit = UNITS[key]
    out = IMAGES / ("%s.jpg" % key)
    if unit.get("book"):
        book = unit["book"]
        im = book_image(book["pdf"], book["xref"])
        label = "book %s p. %d" % (book["pdf"], book["page"])
    else:
        im = Image.open(io.BytesIO(_get("%s/images/%s.jpg" % (BASE, unit["photo"])))).convert("RGB")
        label = "znaci %s" % unit["photo"]
    edited = "crop" in unit or "descreen" in unit
    if out.exists() and not edited and bin(_dhash(Image.open(out)) ^ _dhash(im)).count("1") <= 12:
        print("%-34s already %s" % (out.name, label))
        return
    if "descreen" in unit:
        im = ImageOps.autocontrast(im.filter(ImageFilter.GaussianBlur(unit["descreen"])), cutoff=1)
    if "crop" in unit:
        left, top, right, bottom = unit["crop"]
        w, h = im.size
        im = im.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    im.save(out, quality=JPEG_QUALITY, optimize=True, progressive=True)
    print("%-34s <- %s (%dx%d, %d KB)" % (out.name, label, im.size[0], im.size[1], out.stat().st_size // 1024))


def write_doc():
    lines = [
        "# Unit photos",
        "",
        "Each unit's card photo comes from the [Biblioteka Znaci photo gallery](https://znaci.org/fotogalerija.php) "
        "(public domain). Rule: a group of the unit's own soldiers (standing, marching, lined up), and the photo's "
        "description names the unit. Where znaci.org has no typed description, the museum's caption card "
        "(\"Izvorni opis\" on the photo page) is quoted instead. Units with nothing in the gallery can use a photo "
        "printed in the unit's own book on znaci.org, with the book's caption.",
        "",
        "Generated by `python scripts/find_unit_photos.py --apply`; to change a photo, edit `UNITS` in that script "
        "(its docstring explains how candidates are found).",
    ]
    units_ts = (ROOT / "website" / "app" / "data" / "units.ts").read_text(encoding="utf-8")
    on_site, ready, missing = [], [], []
    for key, unit in UNITS.items():
        note = (" — " + unit["note"]) if unit.get("note") else ""
        if unit["photo"]:
            d = photo_details(str(unit["photo"]))
            desc = d["caption"] or ("%s *(caption card)*" % unit["card"])
            if d["date"] and d["date"][:4] not in desc:
                desc += " (%s)" % d["date"]
            row = "| %s | `%s.jpg` | [znaci %s](%s/fotografija.php?br=%s) | %s%s |" % (
                unit["name"], key, unit["photo"], BASE, unit["photo"], " ".join(desc.split()), note)
        elif unit.get("book"):
            book = unit["book"]
            row = "| %s | `%s.jpg` | [book, p. %d](%s/%s#page=%d) | %s *(caption in the unit's book)*%s |" % (
                unit["name"], key, book["page"], BASE, book["pdf"], book["page"], book["caption"], note)
        elif unit.get("source"):
            row = "| %s | `%s.jpg` | [Wikimedia Commons](%s) | %s%s |" % (
                unit["name"], key, unit["source"]["url"], unit["source"]["caption"], note)
        else:
            missing.append("| %s | %s |" % (unit["name"], unit.get("note") or "Nothing in the znaci.org gallery names the unit; its book hasn't been checked (`--book`)."))
            continue
        (on_site if "/images/%s.jpg" % key in units_ts else ready).append(row)
    header = ["| Unit | Image | Photo | Description |", "|---|---|---|---|"]
    lines += ["", "## On the site", ""] + header + on_site
    if ready:
        lines += ["", "## Ready for units not on the site yet",
                  "", "Point the unit's `image` in `units.ts` at `/images/<Image>` when it's added.", ""] + header + ready
    if missing:
        lines += ["", "## No qualifying photo", "",
                  "These units keep their current image (the book's first page, or a photo flagged below).", "",
                  "| Unit | Why |", "|---|---|"] + missing
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", DOC.relative_to(ROOT))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--candidates", nargs="+", metavar="KEY")
    ap.add_argument("--identify", action="store_true")
    ap.add_argument("--book", nargs="+", metavar=("KEY", "PDF"))
    ap.add_argument("--apply", nargs="*", metavar="KEY")
    ap.add_argument("--all", action="store_true", help="with --candidates: include photos whose caption doesn't name the unit")
    args = ap.parse_args()

    if args.list:
        for key, unit in UNITS.items():
            c = candidates(key)
            named = sum(1 for d in c if d["names_unit"])
            photo = unit["photo"] or ("book" if unit.get("book") else "commons" if unit.get("source") else "-")
            print("%-34s photo=%-7s candidates=%3d named=%3d  %s" % (key, photo, len(c), named, unit["name"]))
    if args.candidates:
        keys = list(UNITS) if args.candidates == ["all"] else args.candidates
        for key in keys:
            c = candidates(key)
            card_only = [d for d in c if d["tagged"] and not d["caption"] and d["original_caption"]]
            shown = c if args.all else [d for d in c if d["names_unit"] or d in card_only]
            print("\n## %s — %s (%d candidates, %d name the unit, %d captioned only on the card)"
                  % (key, UNITS[key]["name"], len(c), sum(d["names_unit"] for d in c), len(card_only)))
            print("  flags: U caption names the unit, T tagged with it, g group words, x portrait/death/other words")
            for d in shown:
                flags = ("U" if d["names_unit"] else "-") + ("T" if d["tagged"] else "-") + \
                        ("g" if d["group"] else "-") + ("x" if d["other"] else "-")
                print("  %6s %s %-10s %s" % (d["id"], flags, d["date"], d["caption"][:150] or "(see caption card)"))
            if shown:
                for p in contact_sheet(key, shown):
                    print("  sheet:", p)
            if card_only:
                for p in card_sheet(key, card_only):
                    print("  cards:", p)
    if args.identify:
        identify()
    if args.book:
        key, pdfs = args.book[0], args.book[1:]
        photos = [ph for pdf in pdfs for ph in book_photos(pdf)]
        print("\n## %s — %d photos in %s" % (key, len(photos), ", ".join(pdfs)))
        for ph in photos:
            print("  %-16s p. %-4d xref %-6d %s" % (ph["pdf"], ph["page"], ph["xref"], ph["caption"][:150]))
        for path in book_sheet(key, photos):
            print("  sheet:", path)
    if args.apply is not None:
        keys = args.apply or [k for k, u in UNITS.items() if u["photo"] or u.get("book")]
        for key in keys:
            if UNITS[key]["photo"] or UNITS[key].get("book"):
                install(key)
        write_doc()


if __name__ == "__main__":
    main()
