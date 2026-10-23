import { useI18n, type Lang } from '../i18n/I18nProvider'
import { SCENES, sceneAt, useProgressValue } from '../scroll/progress'
import './overlay.css'

export function Header({ nav = false }: { nav?: boolean }) {
  const { t, lang, setLang } = useI18n()
  // keyboard users land on the project links first (in the 3D story that also jumps to scene 4)
  const skip = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const first = document.querySelector<HTMLElement>('.project-list a, .project-list [tabindex], .lite-card a')
    if (first) {
      e.preventDefault()
      first.focus()
    }
  }
  return (
    <header className="hud-header">
      <a className="skip-link" href="#projetos" onClick={skip}>
        {t.skip}
      </a>
      <p className="site-name">
        {t.siteName} <em>{t.siteNameAccent}</em>
      </p>
      <div className="hud-header-end">
        {nav && (
          <nav className="site-nav" aria-label={t.nav.label}>
            <a href="#projetos">{t.nav.projects}</a>
            <a href="#sobre">{t.nav.about}</a>
            <a href="#contato">{t.nav.contact}</a>
          </nav>
        )}
        <div className="lang-switch" role="group" aria-label={t.langSwitch}>
          {(['pt', 'en'] as Lang[]).map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={lang === l}
              aria-label={l === 'pt' ? 'Português' : 'English'}
              lang={l === 'pt' ? 'pt-BR' : 'en'}
              onClick={() => setLang(l)}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}

export function ProgressDots() {
  const { t } = useI18n()
  const p = useProgressValue()
  const current = SCENES.indexOf(sceneAt(p))
  return (
    <nav className="progress-dots" aria-label={t.progress} data-intro={p < 0.05} data-done={p > 0.985}>
      <ol>
        {SCENES.map((s, i) => (
          <li key={s.id} data-state={i < current ? 'done' : i === current ? 'active' : 'todo'}>
            <span className="sr-only">{t.scenes[s.id]}</span>
          </li>
        ))}
      </ol>
      <span className="label progress-count" aria-hidden="true">
        {String(current + 1).padStart(2, '0')}/{String(SCENES.length).padStart(2, '0')}
      </span>
    </nav>
  )
}

