import HomePage from '../views/HomePage'
import { homePictures } from '@/app/lib/homePictures'
import { pageMetadata } from '../i18n/metadata'

export const metadata = pageMetadata('sr', '/')

export default function Page() {
  return <HomePage pictures={homePictures()} />
}
