export interface BrigadeConfig {
  name: string
  dataFile: string
  pdfFiles: string[]
}

export const BRIGADE_MAP: Record<number, BrigadeConfig> = {
  1: {
    name: 'Prva Proleterska',
    dataFile: 'prva-proleterska-soldiers.json',
    pdfFiles: ['prva-proleterska-1.pdf', 'prva-proleterska-2.pdf', 'prva-proleterska-3.pdf'],
  },
  2: {
    name: 'Prva Lička Proleterska',
    dataFile: 'soldiers.json',
    pdfFiles: ['prva-licka-proleterska.pdf'],
  },
  3: {
    name: 'Druga Lička Proleterska',
    dataFile: 'druga-licka-soldiers.json',
    pdfFiles: ['druga-licka-spisak.pdf'],
  },
  4: {
    name: 'Ljubljanska (10. SNOUB)',
    dataFile: 'ljubljanska-soldiers.json',
    pdfFiles: ['ljubljanska-brigada.pdf'],
  },
  5: {
    name: 'Treća Proleterska (Sandžačka)',
    dataFile: 'treca-proleterska-soldiers.json',
    pdfFiles: ['treca-proleterska-brigada.pdf'],
  },
  6: {
    name: '13. Proleterska "Rade Končar"',
    dataFile: '13-proleterska-soldiers.json',
    pdfFiles: ['13-proleterska-spisak.pdf'],
  },
}

export function getBrigadeCode(soldierId: string): number {
  return parseInt(soldierId.substring(0, 4), 10)
}

export function getBrigadeName(code: number): string {
  return BRIGADE_MAP[code]?.name ?? 'Unknown'
}
