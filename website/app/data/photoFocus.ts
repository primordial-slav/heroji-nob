// Where the soldiers are in each unit's photo, as the vertical object-position (percent): the unit page banner and
// the soldier popup's strip show only a band of the photo (a fifth of its height in the popup), and the default
// 45% often catches sky or ground. Set by eye from each photo, for the popup's 6.3:1 strip, so the faces sit in it.
const FOCUS: Record<string, number> = {
  'prva-licka-brigada': 47,
  'prva-proleterska-brigada': 59,
  'ljubljanska-brigada': 76,
  'druga-licka-brigada': 41,
  'treca-proleterska-brigada': 13,
  '13-proleterska-brigada': 63,
  '2-dalmatinska-brigada': 31,
  '4-splitska-brigada': 40,
  'prva-vojvodjanska-brigada': 19,
  '5-kozaracka-brigada': 53,
  '2-vojvodjanska-brigada': 44,
  '8-krajiska-brigada': 58,
  '6-krajiska-brigada': 50,
  '4-krajiska-brigada': 47,
  '3-krajiska-proleterska-brigada': 26,
  '17-slavonska-brigada': 54,
  '25-srpska-divizija': 53,
  '1-sumadijska-brigada': 50,
  '18-slavonska-brigada': 56,
  '4-banijska-brigada': 7,
  '4-srpska-brigada': 63,
  '7-vojvodjanska-brigada': 37,
  '19-bircanska-brigada': 23,
  '2-krajiska-brigada': 50,
  'tuzlanski-odred': 22,
  'uzicki-odred': 63,
  '14-srpska-brigada': 21,
  '7-crnogorska-brigada': 36,
  '17-majevicka-brigada': 54,
  '25-brodska-brigada': 37,
  '25-srpska-brigada': 47,
  '21-tuzlanska-brigada': 37,
  '53-srednjobosanska-divizija': 50,
  '21-slavonska-brigada': 79,
  '32-zagorska-divizija': 36,
  '1-dalmatinska-brigada': 50,
  '16-slavonska-omladinska-brigada': 30,
  '8-crnogorska-brigada': 58,
  'druga-proleterska-brigada': 66,
}

// The object-position for a unit's photo in a wide crop; undefined keeps the stylesheet's default
export function photoPosition(unitId: string): string | undefined {
  const y = FOCUS[unitId]
  return y == null ? undefined : `50% ${y}%`
}
