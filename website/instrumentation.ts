// Runs once when a server starts. Under `next dev`, it keeps the data the pages load up to date with the data files,
// and restarts the server when it holds too much memory (app/lib/devData.ts); a built site has its data from the
// build (package.json, "build").
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs' && process.env.NODE_ENV === 'development') {
    const { watchData, watchMemory } = await import('./app/lib/devData')
    watchData()
    watchMemory()
  }
}
