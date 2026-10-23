import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import pt from './pt.json'
import en from './en.json'

export type Lang = 'pt' | 'en'
export type Dict = typeof pt

const DICTS: Record<Lang, Dict> = { pt, en }
const STORAGE_KEY = 'gio-portfolio-lang'

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'pt' || saved === 'en') return saved
  } catch {
    /* storage blocked: fall through to the browser language */
  }
  return navigator.language?.toLowerCase().startsWith('pt') ? 'pt' : 'en'
}

type Ctx = { lang: Lang; t: Dict; setLang: (l: Lang) => void }
const I18nContext = createContext<Ctx | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang)

  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    try {
      localStorage.setItem(STORAGE_KEY, l)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    const t = DICTS[lang]
    document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en'
    document.title = t.documentTitle
    document.querySelector('meta[name="description"]')?.setAttribute('content', t.metaDescription)
  }, [lang])

  const value = useMemo(() => ({ lang, t: DICTS[lang], setLang }), [lang, setLang])
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside <I18nProvider>')
  return ctx
}
