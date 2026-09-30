// Straight double quotes in unit names become Serbo-Croatian „…“
export function sqQuotes(text: string) {
  return text.replace(/"([^"]*)"/g, '„$1“')
}
