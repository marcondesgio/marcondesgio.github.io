import { useI18n } from '../i18n/I18nProvider'
import { projects } from '../data/projects'
import { progress, storyToScroll } from '../scroll/progress'
import { INTERACTIVE_FROM, INTERACTIVE_TO, shardStore } from './shardStore'

const SHARDS_P = 0.56 // middle of the pause zone

/**
 * The same links as the shards, as real HTML: indexable, keyboard and screen-reader friendly (spec §4).
 * Hidden until it receives keyboard focus; focusing an item jumps the story to scene 4 and lights up the
 * matching shard with its floating label.
 */
export function ProjectList() {
  const { t, lang } = useI18n()

  const focus = (index: number) => {
    shardStore.set({ active: index, source: 'focus' })
    const p = progress.p
    if (p < INTERACTIVE_FROM || p >= INTERACTIVE_TO) {
      const max = document.documentElement.scrollHeight - window.innerHeight
      window.scrollTo({ top: storyToScroll(SHARDS_P) * max, behavior: 'instant' })
    }
  }
  const blur = () => {
    if (shardStore.get().source === 'focus') shardStore.set({ active: null, source: null })
  }

  return (
    <section id="projetos" aria-labelledby="projects-title">
      <h2 id="projects-title" className="sr-only">
        {t.projectsTitle}
      </h2>
      <ul className="project-list">
        {projects.map((pr, i) => (
          <li key={pr.id}>
            {'comingSoon' in pr && pr.comingSoon ? (
              <span tabIndex={0} aria-disabled="true" onFocus={() => focus(i)} onBlur={blur}>
                {t.shard} {i + 1}: {t.comingSoon}
              </span>
            ) : (
              <a
                href={pr.url}
                target="_blank"
                rel="noopener noreferrer"
                onFocus={() => focus(i)}
                onBlur={blur}
                aria-description={pr.description[lang]}
              >
                {pr.name}
                <span className="sr-only"> — {pr.description[lang]} ({t.openOnGithub})</span>
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
