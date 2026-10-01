import type { Lang } from './config'
import { sr, type Messages } from './messages/sr'
import { srCyrl } from './messages/sr-cyrl'
import { sl } from './messages/sl'
import { mk } from './messages/mk'
import { en } from './messages/en'

export type { Lang } from './config'
export type { Messages } from './messages/sr'

export const MESSAGES: Record<Lang, Messages> = { sr, 'sr-cyrl': srCyrl, sl, mk, en }

export function messagesFor(lang: Lang): Messages {
  return MESSAGES[lang]
}
