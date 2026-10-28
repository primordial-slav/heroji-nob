// The files scripts/prepare-data.ts writes from the unit files to public/data/ (in .gitignore), before the site is
// built and, under `next dev`, whenever a data file changes (lib/devData.ts); the pages load them as they are. Here
// for the script and the pages alike.

/** In public/ */
export const DATA_DIR = 'data'

/** A unit's full records, RECORDS_PER_PART at a time, in the order of its data file, with their life's steps */
export const RECORDS_PER_PART = 250
export const recordsPath = (unitId: string, part: number) => `/${DATA_DIR}/records/${unitId}/${part}.json`

/** "Na današnji dan": those who fell, died or went missing on a day of the war, "10-28" */
export const onThisDayPath = (day: string) => `/${DATA_DIR}/on-this-day/${day}.json`

/** The soldiers of the portraits in the home page's margins */
export const PORTRAIT_PEOPLE_PATH = `/${DATA_DIR}/portrait-people.json`

/** The places index in small files (lib/placeFiles.ts): where a shard of ids' places are, and a chunk of places */
export const placesOfPath = (shard: string) => `/${DATA_DIR}/places/of/${shard}.json`
export const placesChunkPath = (n: number) => `/${DATA_DIR}/places/chunk/${n}.json`
