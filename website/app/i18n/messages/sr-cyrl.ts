import { cyrillicMessages } from '../cyrillic'
import { sr, type Messages } from './sr'

// Српскохрватски: the Serbo-Croatian text of sr.ts in Cyrillic, letter for letter (i18n/cyrillic.ts), so a change
// to sr.ts shows in both scripts. Only what letter-for-letter can't do is written here.

export const srCyrl: Messages = cyrillicMessages(sr, {
  record: {
    // The credit is data ("znaci.org, br. 13283", "znaci.org, knjiga o jedinici"); the site's own words in it change
    photoCredit: (credit: string) => credit.replace(', br. ', ', бр. ').replace(', knjiga o jedinici', ', књига о јединици'),
  },
  sources: {
    heroLicense: 'https://creativecommons.org/licenses/by-sa/4.0/deed.sr',
  },
})
