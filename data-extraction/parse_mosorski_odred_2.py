"""
Parser: Mosorski partizanski odred (brigade code 148), the book's part II: the fighters among "Popis boraca komandnih
mjesta, partijsko-političkih i terenskih radnika na području Mosora".

Source: Velić, Petrić, *Mosorski partizanski odred* (znaci.org 00003/794, the whole book's PDF pp. 575-650: "II dio")
→ website/public/pdfs/mosorski-odred-2.pdf. The same entries as part I (parse_mosorski_odred.py reads them):
    ALFIREVIĆ Ante ANTE, rođen 1926. u Ostrvici, Omiš, zemljoradnik, Hrvat. Bio je borac pri Komandi mjesta Omiš i u
    kotarskoj Miliciji od kolovoza 1944.
but the list mixes the komande mjesta's fighters with the party and field workers, AFŽ and NOO members of the Mosor
villages. Only the fighters go in (the user's decision of 2026-10-14, the Čačak reader's rule made stricter): an entry
that says borac, names a military duty, or puts him in a unit of the army ("u NOV od", "pripadnik radnog bataljona",
"stupio u 1. dalmatinsku brigadu"); a field worker who "collected food for the NOV", an odbornik, an AFŽ member stay
out, and a man of a komanda mjesta counts only with a military duty there. These get 0148010001 on (part I: 0148000001-),
and the same man in part I is merged (scripts/find_source_duplicates.py --brigade 148).
Usage: python data-extraction/parse_mosorski_odred_2.py [--dropped N]
"""
import random
import re
import sys
from pathlib import Path

import fitz

import parse_8_kordunaska_divizija as k8
import parse_mosorski_odred as m1
from _parser_scaffold import run_parser

HERE = Path(__file__).resolve().parent
PDF = HERE.parent / 'website' / 'public' / 'pdfs' / 'mosorski-odred-2.pdf'
DUTY = (r'komandir\w*|komandant\w*|komesar\w*|zamjenik\w*\s+(?:komandir|komandant|komesar|političk)\w*|desetar\w*|vodnik\w*|'
        r'delegat\w*\s+vod\w*|intendant\w*|(?:pušk\w*)?mitraljez(?:ac|ca|cem|ci)\b|bombaš\w*|bolničar\w*|oficir\w*|'
        r'starješin\w*|izviđač\w*|minobacač\w*|artiljer\w*|tenkist\w*')     # not "referent" (an NOO's office), nor
#                                       "vojnik", "mornar" (the old army, a trade), nor "iz mitraljeza" (shot with one)
UNIT = r'(?:brigad|odred|bataljon|bataljun|čet[aeiu]\b|vod[ua]?\b|divizij|korpus|NOVJ?\b|partizan|mornaric|KNOJ|eskadril)'
FIGHTER = re.compile(
    rf'\bbor(?:ac|kinja)\b'                              # he is one: not "tri borca ... uspjela su" (others)
    rf'|\b(?:{DUTY})\b'
    rf'|\b(?:kurir|stražar)\w*\s+(?:\S+\s+){{0,2}}(?:komand|štab|bataljon|čet|odred|brigad|partizansk)'
    rf'|\b(?:stupi[ol]\w*|otiša?[ol]\w*|uš[ao]\w*|pristupi[ol]\w*|mobiliziran\w*|mobilisan\w*|pripadnik\w*|primljen\w*)\s+'
    rf'(?:u\s+)?(?:\S+\s+){{0,4}}{UNIT}'
    rf'|\bu\s+(?:redove\s+|sastav\s+)?(?:NOVJ?|partizan\w*)\s+(?:od|je|se)\b'
    rf'|\b(?:odlask\w*|dolask\w*|prelask\w*)\s+u\s+(?:\S+\s+){{0,3}}{UNIT}', re.I)      # "do odlaska u NOVJ"
# a word that names the duty or the unit of a civilian body, not the army ("kurir NOO", "komandir seoske straže"
# stays: the partisan guards were the army's)
CHETNIK = re.compile(r'četničk\w* (?:odred|brigad|korpus|bataljon|čet\w*|komand)|ustašk\w* (?:bojn|postroj|vojsk)|domobran', re.I)


# units of the rear that are no fighting units: a komanda mjesta's rear unit, the children's pioneer companies; the
# labour battalions (radni bataljon, mostly older men, from the autumn of 1944) count, by the user's decision of
# 2026-10-14
REAR = re.compile(r'\b(?:\w+\s+)?(?:pozadinsk\w*\s+jedinic\w*|pionirsk\w*\s+čet\w*)', re.I)   # and the word before it:
#                                                                                           "komandir pionirske čete"


def fighter(rec: dict) -> bool:
    info = REAR.sub('', rec.get('additional_info') or '')
    return bool(FIGHTER.search(info)) and not CHETNIK.search(info)


# The books across units read three more rules beside FIGHTER (found on 2026-10-19 in Otočac's list and the other
# mixed lists, when the user asked to check them): an officer whom the entry gives only his rank, a man it puts in a
# unit without a verb of joining or calls a partisan, and the activists, who go in too, marked. The units' parsers
# don't read them, since an added record moves the IDs a unit's corrections are keyed to.

# the old army and the other side, beyond CHETNIK: a royal officer, a gendarme, the gorska straža, the April war, and
# a man the new authorities tried and shot ("streljan po presudi vojnog suda")
OTHER_ARMY = re.compile(r'\bbivš\w*\s+(?:\S+\s+){0,2}vojsk\w*|\bkraljev\w*\s+(?:\S+\s+)?vojsk\w*|'
                        r'\bjugosl[ao]v\w*\s+(?:kraljev\w*\s+)?vojsk\w*|\bvojsk\w*\s+(?:(?-i:KJ)|kraljevin\w*)|'
                        r'(?-i:\bVKJ\b|\bBJV\b|\bK[VJ]\b)|aprilsk\w*\s+rat\w*|\baprila?\s+1941|'
                        r'(?:pomorsk\w*|pom\.)\s*kapetan|kapetan\w*\s+(?:duge|obaln\w*|bojnog|brod\w*)|'
                        r'trgovačk\w*\s+mornar\w*|'
                        # a gendarme, a man of the gorska straža, himself ("žandarm, rođen 1908", "kapetan gorske
                        # straže"), not those who caught him ("uhvatili ga žandarmi", "u borbi protiv žandarma")
                        r'(?:^|[,;:.]\s*|\bkao\s+|\bbio\s+(?:je\s+)?)žandar\w*|\bžandarmerijsk\w*\s+(?:pod)?narednik\w*|'
                        r'\b(?:kapetan|komandant|komandir|pripadni[kc]|član|vođa|starešin)\w*\s+(?:\S+\s+)?gorsk\w*\s+straž\w*|'
                        r'\bnov\w*\s+vlast\w*', re.I)                  # one the new authorities tried and shot
# a fighter's or communist's kin, killed for him ("zbog odlaska sina i muža u partizane", "majka ubijenog partizana",
# "majka Vukašina Dragutinovića Raše, komuniste"): his words are not hers
KIN = re.compile(r'\b(?:sin|sina|sinom|sinov\w*|muž\w*|brat\w*|kć\w*|ćerk\w*|kćerk\w*|oca|otac|majk\w*|supru\w*|'
                 r'žen[aeu]|udovic\w*|roditelj\w*)\s+(?:\S+\s+){0,4}?(?:u\s+partizan\w*|partizan\w*|bor(?:ca|aca|cem)\b|'
                 r'komunist\w*|komandant\w*|komandir\w*|komesar\w*|narodn\w*\s+heroj\w*)', re.I)

# his own rank: in the nominative ("poginuo 1944. kao kapetan", "zastavnik u NOV", "kao politkomesar"), "bio je
# kapetanom", or after "u činu"; not another man's ("žena kapetana", "pod komandom ... podoficira KV")
RANK_WORD = (r'(?:pot?poručnik|poručnik|pod?poročnik|poročnik|kapetan|major|potpukovnik|pukovnik|pod?polkovnik|'
             r'polkovnik|(?-i:general)(?:-?major|-?pukovnik|-?lajtnant)?|zastavnik|podoficir|politkomesar|'
             r'vojni\s+referent)')                                   # (not the "General hospital 43" in Italy)
RANK = re.compile(rf'\b{RANK_WORD}(?:om)?\b|\bčin\w*\s+(?:\S+\s+)?{RANK_WORD}\w*', re.I)


def officer(rec: dict) -> bool:
    info = KIN.sub('', rec.get('additional_info') or '')
    return bool(RANK.search(info)) and not OTHER_ARMY.search(info) and not CHETNIK.search(info)


# where a list of the dead puts him in an army unit without a verb of joining ("poginuo u Vojvođanskoj brigadi", "kao
# referent saniteta Zagorske brigade"), within a sentence ("u Zagrebu. Radio je za Zagorski odred" is not; an
# ordinal's dot is, "u XIII. proleterskoj"); not one killed by a unit ("od pripadnika ... brigade")
ARMY_UNIT = r'(?:brigad\w*|odred\w*|bataljon\w*|bataljun\w*|divizij\w*|korpus\w*|eskadril\w*|čet[aeiu]\b)'
# the army by its name only right after "u" ("u NOV od 1943", "u sastav NOV"), not "kao i odeću i obuću za NOV"
IN_ARMY = re.compile(rf'\b(?:u|kao)\s+(?:(?:\d+|[IVXL]+)\.\s*|[^\s.;]+\s+){{0,5}}?{ARMY_UNIT}|'
                     r'\bu\s+(?:sastav\w*\s+|redove\s+)?(?-i:NOVJ?\b|NOV\s+i\s+POJ|KNOJ\w*|OZN\w*)|'
                     r'\bkao\s+(?:\S+\s+)?(?-i:KNOJ\w*|OZN\w*)|'
                     r'\bpripadni\w*\s+(?:\S+\s+){0,2}jedinic\w*', re.I)
# not one killed by a unit ("od pripadnika ... brigade"), nor a forced-labour company of the Hungarian army
# ("kažnjenička radna četa"), nor one who gathered help for the army ("prikupljala hranu za NOV")
NOT_IN_ARMY = re.compile(r'\bod\s+(?:strane\s+)?(?:\S+\s+){0,4}?(?:brigad|odred|bataljon|divizij|korpus|partizan|'
                         r'(?-i:NOV))|\bkažnjeničk\w*|\bradn\w*\s+čet\w*|\bza\s+(?-i:NOVJ?)\b|'
                         r'\b(?:hran\w*|pomo[ćc]\w*|odjeć\w*|odeć\w*|obuć\w*)\s+(?:\S+\s+)?(?:borc\w*|partizan\w*)',
                         re.I)                                  # "pripremala hranu borcima 2. čete"
HELPER = re.compile(r'\b(?:suradni|saradni|simpatizer|jatak|jatac)\w*', re.I)       # "suradnik Zagorskog odreda"


def in_army(rec: dict) -> bool:
    info = KIN.sub('', REAR.sub('', rec.get('additional_info') or ''))
    return (bool(IN_ARMY.search(info)) and not NOT_IN_ARMY.search(info) and not CHETNIK.search(info)
            and not HELPER.search(info) and not OTHER_ARMY.search(info))


# a partisan by that word ("poginuo kao biokovski partizan", "pobjegao u partizane"), or a man of the NOB who fell in
# battle ("Sudionikom je NOB-a od listopada 1944. Poginuo ... u borbama za oslobođenje Istre"); not one who fought
# against them
PARTISAN = re.compile(r'\bkao\s+(?:\S+\s+){0,2}partizan(?:ka)?\b|\bu\s+partizan(?:e|ima)\b|'
                      r'\b(?:u|kao|pripadni\w*)\s+(?:\S+\s+){0,2}partizansk\w*\s+jedinic\w*|'
                      r'\b(?:povuk\w*|otiš\w*|pošl?[ao]|krenu\w*)\s+(?:se\s+)?sa?\s+partizanima\b', re.I)
# (not "povukao se sa partizanima u Bosnu 1941" for "održavala vezu sa partizanima", nor one who only set out to join
# them: "krenula u partizane, ali je na putu uhvaćena", "pokušao pobeći 1944. u partizane")
ATTEMPT = re.compile(r'\b(?:kren\w*|pokuša\w*|namer\w*|nameravao|htio|hteo|htela|htjela|spremao|spremala|pošao|pošla|'
                     r'polazeć\w*|u\s+cilju|radi\s+uključ\w*)\b(?:\s+\S+){0,6}?\s+(?:u\s+)?partizan\w*', re.I)
BATTLE = re.compile(r'\b(?:poginu\w*|pa[lo]a?|ubijen\w*)\s+(?:\S+\s+){0,8}?u\s+borb\w*', re.I)
MOVEMENT = re.compile(r'(?-i:\b(?:NOB|NOP|NOV|NOR|NOVJ)\b)|\bpartizan\w*|\b(?:su|sa)dioni\w*|\bučesni\w*', re.I)
# a partisan unit or the movement, what an entry naming the old army must also name ("podoficir BJV; vodnik Treće čete
# Ljubićkog bataljona"; not "pilot BJV ... oborila njegov avion protivavionska artiljerija")
THEIRS = re.compile(r'\b(?:bataljon|bataljun|odred|brigad|divizij|korpus)\w*|\bčet[aeiu]\b|' + MOVEMENT.pattern, re.I)
AGAINST_THEM = re.compile(r'\b(?:protiv|pritiv|od)\s+(?:\S+\s+)?partizan\w*|\bborb\w*\s+(?:\S+\s+)?sa?\s+partizan\w*',
                          re.I)
# a domobran or a man of the other side who went over to them: "Iz domobrana je pobjegao i stupio u slavonske
# partizanske jedinice" (the rule above leaves out every entry that names the domobrani); to them, not from them
WENT_OVER = re.compile(r'\b(?:pob(?:i?j)?e[gć]\w*|preb(?:i?j)?e[gć]\w*|preš[ao]\w*|prelaz\w*|priključ\w*|b(?:i?j)?eg\w*|bekstv\w*|dezertir\w*)\s+'
                       r'(?:\S+\s+){0,8}?(?:(?:u|k|kod)\s+(?:\S+\s+){0,3}?(?:partizan\w*|(?-i:NOVJ?)\b|jedinic\w*)|'
                       r'partizanima)', re.I)
# the old army's ranks and duties, read away with its name ("oficir BJV", "pilot BJV", "kapetan — izviđač BJV")
OLD_DUTY = re.compile(r'\b(?:oficir|podoficir|pilot|vojnik|narednik|podnarednik|kapetan|major|poručnik|potporučnik|'
                      r'pukovnik|potpukovnik|general|izviđač|pitomac)\w*', re.I)


def fighter_or_officer(rec: dict) -> bool:
    raw = REAR.sub('', rec.get('additional_info') or '')
    other = CHETNIK.search(raw) or OTHER_ARMY.search(raw)
    if not other and (fighter(rec) or officer(rec) or in_army(rec)):
        return True
    info = KIN.sub('', raw)
    went = WENT_OVER.search(info)
    if went:
        info = info[went.start():]          # what he did once he went over to them ("pobegao u partizane; poginuo")
    if other:
        # one of the other side counts only if he went over to them; a man of the old army, a gendarme, or one who
        # fought gendarmes, by what he did in this war ("podoficir BJV; vodnik Treće čete Ljubićkog bataljona"), not
        # by his old rank ("oficir BJV, poginuo u borbi protiv Nemaca u Ćićevcu 10. aprila 1941")
        if CHETNIK.search(raw) and not went:
            return False
        info = OLD_DUTY.sub('', OTHER_ARMY.sub('', CHETNIK.sub('', info)))
        if not THEIRS.search(info):
            return False
        if fighter({'additional_info': info}) or officer({'additional_info': info}) or in_army({'additional_info': info}):
            return True
    if HELPER.search(info) or AGAINST_THEM.search(info) or NOT_IN_ARMY.search(info):
        return False
    info = ATTEMPT.sub('', info)
    return bool(PARTISAN.search(info) or (BATTLE.search(info) and MOVEMENT.search(info)))




# a man or woman of the movement who was no fighter: the party's, SKOJ's, the AFŽ's and USAOJ's people, the
# liberation committees' (NOO, odbornik), field and political workers, couriers, illegal workers and helpers of the
# NOP ("saradnik NOP-a"), the Slovene OF's activists. The user decided on 2026-10-19 that the mixed lists' activists go
# in too, marked `role: 'activist'` on the entry so the site can tell them apart; a list whose title counts every man
# in it as one of the movement (Otočac's "aktivni učesnici NOP", Sanski Most's "Borci NOB 15. maja 1945") takes all
# its non-fighters, a list of all the war's dead only those this names. Not a sympathizer alone, nor a victim of terror.
ORGAN = (r'(?:(?-i:KP\w*|SKOJ\w*|NOO\w*|NOF\w*|AF[ŽZ]\w*|USAO\w*|OF\b)|komitet\w*|partij\w*|ćelij\w*|aktiv\w*|'
         r'organiz\w*|odbor\w*)')
ACTIVIST = re.compile(
    r'\baktivist\w*|\bilegal\w*|\bodborni\w*|\b(?:vijećni|većni)\w*|narodnooslobodilačk\w*\s+odbor\w*|'
    r'\bnarodn\w*\s+odbor\w*|\bodbor\w*\s+(?-i:AF[ŽZ]|NOF|JNOF|USAO\w*|NOP\w*|NOB\w*|OF)\b|'
    r'(?-i:\b[MSKOG]?NOO\w*|\bKP\s*-?\s*[JHSM]\b|\bSKOJ\w*|\bAF[ŽZ]\b|\bUSAO\w*|\bOF\b|\bVOS\b|\bJ?NOF\w*)|'
    r'\bskojev\w*|\bpartij\w*|\bkomunist\w*|\bkomitet\w*|\bćelij\w*|'
    r'\bteren(?:ac|ka|ci|ski\s+radni\w*|sk\w*\s+rad\w*|sk\w*\s+odbor\w*|sk\w*\s+organiz\w*)|'
    r'\bpoliti\w*\s+radni\w*|\bpol\.\s*radni\w*|'
    rf'\b(?:sekretar|tajni[kc]|predsjedni[kc]|predsedni[kc])\w*\s+(?:\S+\s+){{0,3}}?{ORGAN}|'
    r'\borganizator\w*|\b(?:sa|su)radni(?:k|ka|ca|ci|ce|kom|com)?\b|\b(?:sa|su)ra[dđ]iva\w*\s+sa?\s+partizan\w*|'
    r'\bsodelav\w*|\bkurir\w*|\bdiverzant\w*|\budarn\w*\s+grup\w*|'
    r'osvobodiln\w*\s+front\w*|\bučesni\w*\s+(?:u\s+)?(?:NOB|NOP|NOR|narodnooslobodil)\w*|'
    r'\bpripadni\w*\s+(?-i:NOP)\w*|\bčlan\w*\s+(?-i:NOP)\w*|\bobveščeval\w*|\bobaveštajn\w*|\bobavještajn\w*|'
    r'\b(?:član|čl\.|sekretar|tajni[kc])\w*\s+(?-i:[MOKCPG]K|OK|KK|MK|PK|CK)\b|\bomladinsk\w*\s+rukovodi\w*|'
    r'\bpartizansk\w*\s+vez\w*|\bkao\s+veza\b|\bvodič\w*|\borganizir\w*\s+(?:radni\w*|član\w*|pristaš\w*)|'
    # the partisans' rear in the liberated towns of 1941: "radio u partizanskoj radionici", "na održavanju
    # partizanskog voza", "radila u partizanskoj bolnici"; "pozadinski radnik NOP-a"
    r'\brad(?:i[olaei]|il)\w*\s+(?:\S+\s+){0,4}?partizansk\w*|\bpozadinsk\w*\s+radni\w*|'
    r'\bu\s+(?:\S+\s+)?partizansk\w*\s+(?:radionic|bolnic|kuhinj|komand|štampar|tehnic)\w*|\bu\s+pozadini\s+za\b|'
    r'\bradni(?:k|ca|ci|ce)\s+(?:\S+\s+){0,2}?partizansk\w*|'           # "radnica partizanske fabrike oružja"
    # the illegal printing shops ("u ilegalnoj partijskoj tehnici", the Slovene "delala v tehniki Netopir"), and the
    # Slovene political and field workers ("politični delavec pri Ob KOM KPS")
    r'\b(?:ilegaln\w*|partijsk\w*|partizansk\w*)\s+tehni[kc]\w*|\bv\s+tehniki\b|\b(?:politi|terensk)\w*\s+delav\w*|'
    r'\brad(?:i[olaei]|il)\w*\s+(?:\S+\s+){0,2}?za\s+(?:(?-i:NOP|NOB)|partizan\w*)', re.I)    # "Aktivno radio za NOP"
# the book's mark of a victim of terror ("kao ŽFT", the OCR's ZFT, a slip's ŽTF), never a man of the movement
VICTIM = re.compile(r'(?-i:\b[ŽZ]FT\b|\bŽTF\b)|\bžrtv\w*\s+fašist\w*', re.I)


# what the entry says he was only suspected of or sympathized with ("Pod sumnjom da je partizanski kurir", "Kao
# simpatizer komunista")
SUSPECTED = re.compile(r'\b(?:simpatizer\w*|pod\s+sumnjom|osumnjič\w*|optužb\w*|optužen\w*)\s+(?:\S+\s+){0,5}\S+', re.I)


def activist(rec: dict) -> bool:
    """Of the movement and no fighter, by the words of the entry (for a list of all the war's dead)"""
    info = rec.get('additional_info') or ''
    own = SUSPECTED.sub('', KIN.sub('', info))
    return (not fighter_or_officer(rec) and bool(ACTIVIST.search(own)) and not CHETNIK.search(info)
            and not VICTIM.search(info) and not OTHER_ARMY.search(info))


def keep(ln: dict) -> bool:
    t = ln['text'].strip()
    if re.match(r'^(?:II\s+DIO|P\s*O\s*P\s*I\s*S\b|BORACA KOMANDNIH|I TERENSKIH RADNIKA|MOSORA$)', t):
        return False                                     # the part's title
    if re.match(r'^(?:PK|OK|KK|MK|CK|SK)\s', t):
        m1._state['open'] = False                        # "PK SKOJ-a za Dalmaciju" carries on a bio (Krstulović's)
        ln['text'] = t
        return True
    wife = re.match(r'^([A-ZČĆŽŠĐ][A-ZČĆŽŠĐ\-]{2,})\s+(?:ž\.|žena)\s+(?=[A-ZČĆŽŠĐ][a-zčćžšđ]+\s+[A-ZČĆŽŠĐ]{2})', t)
    if wife:                                             # "JAMAN žena Mate RUŽA": a wife, under her husband's name
        ln['text'] = '§x§ ' + wife.group(1) + ' ' + t[wife.end():]
        m1._state['open'] = False
        return True
    return m1.keep(ln)


DROPPED: list = []


FIX_GIVEN = {'Jahiel-Matić Luka': ('Jahiel', 'zvani Matić Luka'), 'MARIN »Đeno-': ('Marin', 'zvani Đeno')}


def post(soldiers: list[dict]) -> list[dict]:
    for s in soldiers:
        if s['first_name'] in FIX_GIVEN:
            s['first_name'], note = FIX_GIVEN[s['first_name']]
            s['additional_info'] = f"{note}; {s['additional_info']}"
    soldiers = m1.post(soldiers)
    kept = [s for s in soldiers if fighter(s)]
    DROPPED[:] = [s for s in soldiers if not fighter(s)]
    print(f'{len(soldiers)} entries in part II, {len(kept)} fighters kept, {len(DROPPED)} left out')
    return kept


if __name__ == '__main__':
    if not PDF.exists():
        src, out = fitz.open(HERE / '.cache' / 'znaci_library' / 'chapters' / '00003_794.pdf'), fitz.open()
        out.insert_pdf(src, from_page=574, to_page=649)
        out.save(PDF, garbage=4, deflate=True)
    k8.corpus()
    run_parser(
        pdf_path=str(PDF.relative_to(HERE.parent)).replace('\\', '/'),
        brigade_code=148,
        output_path='website/public/mosorski-odred-soldiers.json',
        start_page=1,
        end_page=None,
        layout='single',
        script='latin',
        entry_start_re=re.compile(r'^§x§'),
        parse_entry_fn=m1.parse,
        line_filter=keep,
        post_fn=post,
        id_start=10001,
        keep_other_sources=True,
    )
    if '--dropped' in sys.argv:
        random.seed(3)
        for s in random.sample(DROPPED, min(len(DROPPED), int(sys.argv[sys.argv.index('--dropped') + 1]))):
            print(f"  OUT {s['last_name']} {s['first_name']}: {s['additional_info'][:150]}")
