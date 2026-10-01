import { createSoldierIndex, searchSoldiers, type SearchFields, type SearchHits, type SoldierIndex } from './soldierSearch'

// Searches one slice of the soldiers off the page's thread (see useFuseSearch). The slice comes in pieces;
// the index is built when the last one is in, and a search posted after the data waits for it.

export type ToSearchWorker =
  | { type: 'data'; soldiers: SearchFields[]; last: boolean }
  | { type: 'search'; query: string; wholeWords: boolean }

export type FromSearchWorker = SearchHits

const scope = self as unknown as Worker
let received: SearchFields[] = []
let index: SoldierIndex | null = null

scope.onmessage = (event: MessageEvent<ToSearchWorker>) => {
  const message = event.data
  if (message.type === 'data') {
    received = received.concat(message.soldiers)
    if (message.last) {
      index = createSoldierIndex(received)
      received = []
    }
    return
  }
  const hits: FromSearchWorker = searchSoldiers(index!, message.query, message.wholeWords)
  scope.postMessage(hits, [hits.idx.buffer, hits.rank.buffer, hits.score.buffer])
}
