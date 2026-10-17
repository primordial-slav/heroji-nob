// The war's great battles and operations. On the timeline each is drawn while it lasts (the months from `from` to
// `to`), for the units that fought in them (each unit's list is `battles` in units/index.ts, from its own book): crossed
// sabres in a ring at the place the battle is named for, though the unit may have fought some way off. A click opens
// `about`, a short account of the battle as a whole; the unit's own part is in its numbered events.
export type Battle = {
  key: string
  name: string
  dates: string
  from: string      // the first and the last month it is shown in
  to: string
  start: string     // its first and last day: the brigade's numbered events between them are its part in the battle
  end: string
  lon: number
  lat: number
  about: string
}

export const BATTLES: Battle[] = [
  {
    // the crossing at Jablanica
    key: 'neretva', name: 'Bitka na Neretvi', dates: 'januar – mart 1943.', from: '1943-01', to: '1943-03', start: '1943-01-20', end: '1943-03-31', lon: 17.757, lat: 43.659,
    about: 'Nemačka operacija „Weiss“ počela je 20. januara 1943. Nemačke, italijanske, ustaško-domobranske i četničke '
      + 'snage trebalo je da unište Glavnu operativnu grupu Vrhovnog štaba i slobodnu teritoriju u zapadnoj Bosni. '
      + 'Partizani su se, noseći oko četiri hiljade ranjenika i bolesnika, probijali ka jugoistoku. Posle protivudara '
      + 'kod Gornjeg Vakufa, početkom marta, prešli su Neretvu kod Jablanice preko porušenog mosta i razbili četnike '
      + 'na njenoj levoj obali.',
  },
  {
    // Tjentište
    key: 'sutjeska', name: 'Bitka na Sutjesci', dates: '15. V – 16. VI 1943.', from: '1943-05', to: '1943-06', start: '1943-05-15', end: '1943-06-16', lon: 18.689, lat: 43.349,
    about: 'U nemačkoj operaciji „Schwarz“ oko 120.000 nemačkih, italijanskih, bugarskih i ustaško-domobranskih vojnika '
      + 'opkolilo je Glavnu operativnu grupu, oko 22.000 boraca, u planinama između Pive, Tare i Sutjeske. Proboj na '
      + 'Balinovcu i preko Zelengore uspeo je posle teških borbi, sredinom juna. Poginulo je više od 7.000 boraca, među '
      + 'njima i komandant Treće divizije Sava Kovačević.',
  },
  {
    key: 'drvar', name: 'Desant na Drvar', dates: '25. V 1944.', from: '1944-05', to: '1944-05', start: '1944-05-25', end: '1944-06-06', lon: 16.380, lat: 44.374,
    about: 'Ujutro 25. maja 1944. nemački padobranci i jedrilice spustili su se na Drvar, gde su bili Vrhovni štab i '
      + 'savezničke vojne misije, a kopnene kolone krenule su na njega sa svih strana. Tito se sa štabom izvukao iz '
      + 'pećine iznad grada; branili su ih Prateći bataljon, pitomci Oficirske škole i brigade koje su pristizale. '
      + 'Vrhovni štab je početkom juna prešao na Vis.',
  },
  {
    key: 'beograd', name: 'Bitka za Beograd', dates: '14–20. X 1944.', from: '1944-10', to: '1944-10', start: '1944-10-14', end: '1944-10-20', lon: 20.460, lat: 44.820,
    about: 'Jedinice Prve armijske grupe NOVJ i sovjetski Četvrti gardijski mehanizovani korpus probijali su se od 14. '
      + 'oktobra 1944. ulicu po ulicu ka središtu grada. Beograd je oslobođen 20. oktobra; istog dana prve partizanske '
      + 'jedinice prešle su Savu i stvorile mostobran pred Zemunom.',
  },
  {
    // Šid, where the front stood longest
    key: 'srem', name: 'Sremski front', dates: '24. X 1944 – 12. IV 1945.', from: '1944-10', to: '1945-04', start: '1944-10-24', end: '1945-04-12', lon: 19.226, lat: 45.128,
    about: 'Između Dunava i Save nemačke snage držale su utvrđene linije, da zaštite povlačenje svojih trupa s Balkana. '
      + 'Na frontu su se, uz stare partizanske borce, borili deseci hiljada tek mobilisanih mladića, i gubici su bili '
      + 'veliki. Front je probijen 12. aprila 1945, posle čega je Prva armija nastupala kroz Slavoniju ka Zagrebu.',
  },
]
