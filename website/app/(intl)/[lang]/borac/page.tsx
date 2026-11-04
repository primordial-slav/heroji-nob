import RecordPage from '../../../views/RecordPage'
import { RECORD_SHELL_METADATA } from '../../../i18n/metadata'

// The one page behind every record's own address in a language (borac/[id]/route.ts, lib/recordAnswer.ts)
export const metadata = RECORD_SHELL_METADATA

export default function BoracPage() {
  return <RecordPage />
}
