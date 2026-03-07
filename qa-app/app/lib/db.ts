import Database from 'better-sqlite3'
import path from 'path'

let db: Database.Database | null = null

export function getDb(): Database.Database {
  if (db) return db

  const dbPath = path.join(process.cwd(), 'qa.db')
  db = new Database(dbPath)
  db.pragma('journal_mode = WAL')

  db.exec(`
    CREATE TABLE IF NOT EXISTS reviews (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      soldier_id    TEXT NOT NULL UNIQUE,
      brigade_code  INTEGER NOT NULL,
      status        TEXT NOT NULL DEFAULT 'pending',
      wrong_name         INTEGER DEFAULT 0,
      merged_entries     INTEGER DEFAULT 0,
      section_header     INTEGER DEFAULT 0,
      wrong_birth_year   INTEGER DEFAULT 0,
      fathers_name_wrong INTEGER DEFAULT 0,
      duplicate_record   INTEGER DEFAULT 0,
      garbled_text       INTEGER DEFAULT 0,
      other_issue        INTEGER DEFAULT 0,
      description   TEXT DEFAULT '',
      detection     TEXT DEFAULT 'random',
      flags_detail  TEXT DEFAULT '',
      soldier_data  TEXT NOT NULL,
      created_at    TEXT DEFAULT (datetime('now'))
    )
  `)

  return db
}
