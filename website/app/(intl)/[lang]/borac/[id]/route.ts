import type { NextRequest } from 'next/server'
import { isLang } from '@/app/i18n/config'
import { recordAnswer } from '@/app/lib/recordAnswer'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'
export const maxDuration = 15

export async function GET(request: NextRequest, { params }: { params: Promise<{ lang: string; id: string }> }) {
  const { lang, id } = await params
  if (!isLang(lang)) return new Response('Not found', { status: 404 })
  return recordAnswer(request, lang, id)
}
