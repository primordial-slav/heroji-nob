export interface Unit {
  id: string
  name: string
  nameEn: string
  description: string
  image: string
  soldierCount: number
  dataFile: string
}

export const units: Unit[] = [
  {
    id: 'prva-licka-brigada',
    name: 'Prva lička proleterska brigada "Marko Orešković"',
    nameEn: '1st Lika Proletarian Brigade "Marko Orešković"',
    description: 'Formirana juna 1942. godine',
    image: '/images/prva-licka-brigada.jpg',
    soldierCount: 9368,
    dataFile: '/soldiers.json'
  }
  // Add more units here as you get more data
]
