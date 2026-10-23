import { useI18n } from '../i18n/I18nProvider'
import { projects } from '../data/projects'
import { About } from '../about/About'
import './lite.css'

const pad = (n: number) => String(n).padStart(2, '0')

/** Little shard glyph for the cards (solid for projects, dashed outline for "coming soon"). */
function ShardIcon({ soon }: { soon: boolean }) {
  return (
    <svg className="shard-icon" viewBox="0 0 24 24" aria-hidden="true" data-soon={soon}>
      <path d="M5 7 L14 3 L20 9 L17 19 L7 20 Z" />
    </svg>
  )
}

/**
 * Simplified page (spec §10, design system pp. 13–15): same story and content without 3D, for "reduce
 * motion", no WebGL or weak GPUs. Static scene image, project cards, About and contacts — all real HTML.
 */
export function LitePage() {
  const { t, lang } = useI18n()
  const l = t.lite
  return (
    <main id="conteudo" className="lite">
      <section className="lite-hero" aria-labelledby="lite-title">
        <div className="lite-hero-head">
          <h1 id="lite-title" className="lite-title">
            {l.titleA} <em>{l.titleB}</em>
          </h1>
          <p className="lite-tagline">{l.tagline}</p>
        </div>
        <figure className="lite-scene">
          <picture>
            <source type="image/webp" srcSet="/images/scene-800.webp 800w, /images/scene-1600.webp 1600w" sizes="(max-width: 900px) 100vw, 1100px" />
            <img src="/images/scene-1600.jpg" width={1600} height={900} alt={l.sceneAlt} fetchPriority="high" />
          </picture>
          <figcaption className="label">
            <span className="moon" aria-hidden="true" />
            {l.note}
          </figcaption>
        </figure>
      </section>

      <section id="projetos" className="lite-projects" aria-labelledby="lite-projects-title">
        <div className="lite-section-head">
          <h2 id="lite-projects-title" className="lite-h2">
            {l.shardsTitleA} <em>{l.shardsTitleB}</em>
          </h2>
          <p className="label">{l.shardsMeta}</p>
        </div>
        <ul className="lite-cards">
          {projects.map((pr, i) => {
            const soon = 'comingSoon' in pr && !!pr.comingSoon
            return (
              <li key={pr.id} className="lite-card" data-soon={soon}>
                <ShardIcon soon={soon} />
                <p className="label lite-card-kicker">
                  {t.shard} {pad(i + 1)}
                </p>
                {soon ? (
                  <>
                    <h3>
                      <em>{t.comingSoon}</em>
                    </h3>
                    <p className="lite-card-body">{t.comingSoonBody}</p>
                  </>
                ) : (
                  <>
                    <h3>{'name' in pr ? pr.name : ''}</h3>
                    <p className="lite-card-body">{'description' in pr ? pr.description[lang] : ''}</p>
                    <a className="lite-card-link label" href={'url' in pr ? pr.url : '#'} target="_blank" rel="noopener noreferrer">
                      {t.openOnGithub}
                      <span className="sr-only"> — {'name' in pr ? pr.name : ''}</span>
                    </a>
                  </>
                )}
              </li>
            )
          })}
        </ul>
      </section>

      <About key={lang} lite />
    </main>
  )
}
