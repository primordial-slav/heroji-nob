import { NextResponse } from 'next/server'
import { getDb } from '../../lib/db'
import { loadAllSoldiers } from '../../lib/soldiers'

export async function GET() {
  const db = getDb()
  const { soldiers } = loadAllSoldiers()

  const counts = db.prepare(`
    SELECT
      COUNT(*) as total_reviewed,
      SUM(CASE WHEN status = 'issue' THEN 1 ELSE 0 END) as issues,
      SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) as correct,
      SUM(CASE WHEN status = 'dismissed' THEN 1 ELSE 0 END) as dismissed
    FROM reviews
  `).get() as { total_reviewed: number, issues: number, correct: number, dismissed: number }

  const issueTypes = db.prepare(`
    SELECT
      SUM(wrong_name) as wrong_name,
      SUM(merged_entries) as merged_entries,
      SUM(section_header) as section_header,
      SUM(wrong_birth_year) as wrong_birth_year,
      SUM(fathers_name_wrong) as fathers_name_wrong,
      SUM(duplicate_record) as duplicate_record,
      SUM(garbled_text) as garbled_text,
      SUM(other_issue) as other_issue
    FROM reviews WHERE status = 'issue'
  `).get()

  return NextResponse.json({
    total_soldiers: soldiers.length,
    total_reviewed: counts.total_reviewed || 0,
    issues: counts.issues || 0,
    correct: counts.correct || 0,
    dismissed: counts.dismissed || 0,
    by_issue_type: issueTypes,
  })
}
