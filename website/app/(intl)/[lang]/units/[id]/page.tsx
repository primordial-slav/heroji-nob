import UnitPage, { unitMetadata, unitParams } from '../../../../views/unitPage'
import type { Lang } from '../../../../i18n/config'

export const dynamicParams = false

export function generateStaticParams() {
  return unitParams()
}

export async function generateMetadata({ params }: { params: Promise<{ lang: string; id: string }> }) {
  const { lang, id } = await params
  return unitMetadata(lang as Lang, id)
}

export default async function Page({ params }: { params: Promise<{ lang: string; id: string }> }) {
  const { lang, id } = await params
  return <UnitPage lang={lang as Lang} id={id} />
}
