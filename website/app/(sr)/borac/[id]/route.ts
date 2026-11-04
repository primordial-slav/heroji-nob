import type { NextRequest } from 'next/server'
import { recordAnswer } from '@/app/lib/recordAnswer'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 15

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  return recordAnswer(request, 'sr', (await params).id)
}
