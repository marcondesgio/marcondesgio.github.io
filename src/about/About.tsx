import { Fragment, useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n/I18nProvider'
import { contact } from '../data/contact'
import { aboutRefs } from './aboutRefs'
import { Photo } from './Photo'
import './about.css'

const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

/** Fades + rises children in as they enter the viewport; `data-delay` staggers siblings. */
function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  useEffect(() => {
    const root = ref.current
    if (!root) return
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          ;(e.target as HTMLElement).dataset.in = e.isIntersecting ? 'true' : 'false'
        }
      },
      { threshold: 0.15 },
    )
    root.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, []) // App remounts <About key={lang}> so new text gets observed
  return ref
}

function CopyEmail() {
  const { t } = useI18n()
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(contact.email)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2200)
    } catch {
      /* clipboard blocked: the mailto link still works */
    }
  }
  return (
    <>
      <button type="button" className="icon-button" onClick={copy} aria-label={t.about.copy}>
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <rect x="5" y="5" width="8" height="8" rx="2" />
          <path d="M3 10V4a1 1 0 0 1 1-1h6" />
        </svg>
      </button>
      <span className="copied label" role="status" data-show={copied}>
        {copied ? t.about.copied : ''}
      </span>
    </>
  )
}

/**
 * Scene 7 — "Sobre mim" (design system page 10/11). Lives in the normal document flow right after the
 * story track; its first screen overlaps the end of the track so that at p = 1 it sits exactly at the
 * top. The photo itself is the fixed PhotoDissolve overlay: this section only reserves its slot.
 */
export function About({ lite = false }: { lite?: boolean }) {
  const { t } = useI18n()
  const a = t.about
  const ref = useReveal<HTMLElement>()
  const words = a.lead.split(' ')

  return (
    <section
      id="sobre"
      className="about"
      aria-labelledby="about-title"
      data-lite={lite || undefined}
      ref={(el) => {
        ;(ref as React.MutableRefObject<HTMLElement | null>).current = el
        aboutRefs.section = el
      }}
    >
      <div className="about-photo-col">
        <div className="about-photo-slot" ref={(el) => void (aboutRefs.slot = el)}>
          {/* in the 3D story the photo is the fixed PhotoDissolve overlay; the simplified page shows it here */}
          {lite && <Photo />}
        </div>
        <p className="about-caption label">{a.caption}</p>
      </div>

      <div className="about-content" ref={(el) => void (aboutRefs.content = el)}>
        <p className="label about-kicker" data-reveal>
          {a.kicker}
        </p>
        <h2 id="about-title" className="about-title" data-reveal>
          {a.titleA} <em>{a.titleB}</em>
        </h2>
        <p className="about-lead">
          {words.map((w, i) => (
            <Fragment key={i}>
              {/* the space stays outside the inline-block span, or it collapses */}
              <span data-reveal style={{ transitionDelay: `${Math.min(i * 22, 900)}ms` }}>
                {w}
              </span>{' '}
            </Fragment>
          ))}
        </p>

        <div className="about-block">
          <p className="label about-label" data-reveal>
            {a.timelineLabel}
          </p>
          <ol className="timeline">
            {a.timeline.map((job, i) => (
              <li key={job.company} className="timeline-item" data-reveal style={{ transitionDelay: `${i * 90}ms` }}>
                <span className="timeline-dot" aria-hidden="true" />
                <p className="label timeline-period">{job.period}</p>
                <h3>
                  {job.role} <span className="timeline-company">· {job.company}</span>
                </h3>
                <p className="timeline-place">{job.place}</p>
                {'promo' in job && job.promo && <p className="timeline-promo">↑ {job.promo}</p>}
                <ul className="tags">
                  {job.tags.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
                <details className="timeline-details" open={i === 0}>
                  <summary>{a.timelineMore}</summary>
                  <ul>
                    {job.bullets.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </details>
              </li>
            ))}
          </ol>
        </div>

        <div className="about-block" data-reveal>
          <p className="label about-label">{a.skillsLabel}</p>
          <dl className="skills">
            {a.skills.map((g) => (
              <div key={g.title}>
                <dt className="label">{g.title}</dt>
                <dd>
                  <ul className="chips">
                    {g.items.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="about-block" data-reveal>
          <p className="label about-label">{a.builtLabel}</p>
          <ul className="about-cards built">
            {a.built.map((b) => (
              <li key={b.title} className="about-card">
                <h3>{b.title}</h3>
                <ul className="tags">
                  {b.items.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>

        <div className="about-split">
          <div className="about-block" data-reveal>
            <p className="label about-label">{a.educationLabel}</p>
            <ol className="education">
              {a.education.map((e) => (
                <li key={e.title}>
                  <span className="label education-years">{e.years}</span>
                  <div>
                    <h3>{e.title}</h3>
                    <p>{e.school}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
          <div className="about-block" data-reveal>
            <p className="label about-label">{a.languagesLabel}</p>
            <div className="language-card">
              <div className="language-head">
                <h3>{a.language}</h3>
                <span className="label">B2</span>
              </div>
              <p>{a.languageLevel}</p>
              <div className="language-scale" aria-hidden="true">
                {LEVELS.map((l, i) => (
                  <span key={l} data-on={i <= 3} />
                ))}
              </div>
              <div className="language-levels label" aria-hidden="true">
                {LEVELS.map((l) => (
                  <span key={l}>{l}</span>
                ))}
              </div>
              <p className="sr-only">{a.languageNote}</p>
            </div>
          </div>
        </div>

        <div id="contato" className="contact-card" data-reveal>
          <p className="label about-label">{a.contactLabel}</p>
          <div className="contact-email">
            <a href={`mailto:${contact.email}`}>{contact.email}</a>
            <CopyEmail />
          </div>
          <div className="contact-links">
            <a className="button secondary" href={contact.linkedin} target="_blank" rel="noopener noreferrer">
              LinkedIn ↗
            </a>
            <a className="button primary" href={contact.github} target="_blank" rel="noopener noreferrer">
              GitHub ↗
            </a>
          </div>
        </div>

        <p className="about-footer label">{a.footer}</p>
      </div>
    </section>
  )
}
