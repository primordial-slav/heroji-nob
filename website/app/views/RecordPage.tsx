'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { units, type Unit } from '@/app/data/units'
import { useLang, useT } from '@/app/i18n/LangContext'
import { localePath } from '@/app/i18n/config'
import { locateRecord } from '@/app/lib/recordAddress'
import { recordPath } from '@/app/lib/records'
import { fullRecord, loadKin } from '@/app/lib/searchIndex'
import type { Soldier } from '@/app/lib/types'
import SoldierModal from '@/app/components/LazySoldierModal'

// One object for every render: React writes a new one into the element, which would wipe the record's text
const LEFT_AS_IT_IS = { __html: '' }

// A record's own address, /borac/<id>. The route that answers it (lib/recordAnswer.ts) serves this one prerendered page
// with the record's text in the slot below, and here it opens as a record opens from a list. Closing it goes to his unit.
export default function RecordPage() {
  const lang = useLang()
  const t = useT()
  const router = useRouter()
  const [soldier, setSoldier] = useState<Soldier | null>(null)
  const [trouble, setTrouble] = useState<'missing' | 'failed' | null>(null)
  const unit = useRef<Unit | null>(null)
  const asked = useRef('')

  const show = async (id: string) => {
    asked.current = id
    const place = await locateRecord(id)
    const owner = place && units.find((u) => u.id === place.unit)
    const kin = owner && place ? await loadKin(owner, place.id) : null
    if (!owner || !kin) {
      if (asked.current === id) setTrouble('missing')
      return
    }
    const record = await fullRecord({ ...kin.self, unit: owner.name })
    if (asked.current !== id) return
    unit.current = owner
    setSoldier(record)
    // the head's title is the page's own once it has loaded; the address follows the records stepped through
    document.title = `${record.full_name} · ${t.site.name}`
    window.history.replaceState(window.history.state, '', recordPath(record.soldier_id, lang))
  }

  useEffect(() => {
    const id = decodeURIComponent(window.location.pathname.split('/').filter(Boolean).pop() ?? '')
    show(id).catch(() => setTrouble('failed'))
    // the address is read once, when the page opens
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <>
      {/* Filled by the route as it answers; the page must not empty it, so the text stays under the dialog */}
      <div id="record-plain" dangerouslySetInnerHTML={LEFT_AS_IT_IS} suppressHydrationWarning />
      {trouble && (
        <div className="container card-page">
          <div className="empty">
            <h2>{trouble === 'missing' ? t.card.missingTitle : t.card.failedTitle}</h2>
            <p>{trouble === 'missing' ? t.card.missingText : t.card.failedText}</p>
          </div>
        </div>
      )}
      {soldier && (
        <SoldierModal
          key={soldier.soldier_id}
          soldier={soldier}
          onOpen={(to) => { show(to.soldier_id).catch(() => undefined) }}
          onClose={() => {
            setSoldier(null)
            router.replace(unit.current ? localePath(lang, `/units/${unit.current.id}`) : localePath(lang, '/'))
          }}
        />
      )}
    </>
  )
}
