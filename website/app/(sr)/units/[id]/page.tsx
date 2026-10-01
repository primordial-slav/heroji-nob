import UnitPage, { unitMetadata, unitParams } from '../../../views/unitPage'

export const dynamicParams = false

export function generateStaticParams() {
  return unitParams()
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  return unitMetadata('sr', (await params).id)
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  return <UnitPage lang="sr" id={(await params).id} />
}
