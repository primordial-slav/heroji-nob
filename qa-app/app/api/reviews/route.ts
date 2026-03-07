import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../lib/db'

export async function POST(request: NextRequest) {
  const body = await request.json()

  const db = getDb()
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO reviews (
      soldier_id, brigade_code, status,
      wrong_name, merged_entries, section_header, wrong_birth_year,
      fathers_name_wrong, duplicate_record, garbled_text, other_issue,
      description, detection, flags_detail, soldier_data, created_at
    ) VALUES (
      @soldier_id, @brigade_code, @status,
      @wrong_name, @merged_entries, @section_header, @wrong_birth_year,
      @fathers_name_wrong, @duplicate_record, @garbled_text, @other_issue,
      @description, @detection, @flags_detail, @soldier_data, datetime('now')
    )
  `)

  const result = stmt.run({
    soldier_id: body.soldier_id,
    brigade_code: body.brigade_code,
    status: body.status,
    wrong_name: body.wrong_name ? 1 : 0,
    merged_entries: body.merged_entries ? 1 : 0,
    section_header: body.section_header ? 1 : 0,
    wrong_birth_year: body.wrong_birth_year ? 1 : 0,
    fathers_name_wrong: body.fathers_name_wrong ? 1 : 0,
    duplicate_record: body.duplicate_record ? 1 : 0,
    garbled_text: body.garbled_text ? 1 : 0,
    other_issue: body.other_issue ? 1 : 0,
    description: body.description || '',
    detection: body.detection || 'random',
    flags_detail: body.flags_detail || '',
    soldier_data: body.soldier_data || '{}',
  })

  return NextResponse.json({ success: true, id: result.lastInsertRowid })
}

export async function GET() {
  const db = getDb()
  const reviews = db.prepare(
    'SELECT * FROM reviews WHERE status = ? ORDER BY created_at DESC'
  ).all('issue')

  return NextResponse.json({ reviews })
}
