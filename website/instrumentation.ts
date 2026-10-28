// Runs once when a server starts. Under `next dev`, it keeps the data the pages load up to date with the data files
// (app/lib/devData.ts); a built site has it from the build (package.json, "build").
export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs' && process.env.NODE_ENV === 'development') {
    const { watchData } = await import('./app/lib/devData')
    watchData()
  }
}
