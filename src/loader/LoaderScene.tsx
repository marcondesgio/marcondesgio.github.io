import { useEffect, useRef } from 'react'
import { useI18n } from '../i18n/I18nProvider'
import { band, useProgressValue } from '../scroll/progress'
import { useLoadState } from './loadState'
import { CoffeeSurface } from './CoffeeSurface'
import { EYE_CYCLE_MS, TutuEyes } from './TutuEyes'
import { emitDrop } from './drops'
import './loader.css'

const reducedMotion =
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
const isTouch = typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches

/**
 * Scene 0 (spec §4): the mug seen from above, Tutu's eyes reflected in the coffee, steam. Paints from the
 * initial bundle while the 3D chunk and GLBs load. When everything is ready it waits for the current
 * eye cycle to end, then calls onRelease (scroll unlocks) and shows the hint. As the story starts it
 * fades out over the 3D mug, which the camera frames the same way at p = 0; scrolling back fades it in.
 */
export function LoaderScene({ released, onRelease }: { released: boolean; onRelease: () => void }) {
  const { t } = useI18n()
  const { progress, ready } = useLoadState()
  const p = useProgressValue(0.002)
  const cycleStart = useRef(performance.now())

  useEffect(() => {
    if (!ready || released) return
    if (reducedMotion) {
      onRelease()
      return
    }
    const intoCycle = (performance.now() - cycleStart.current) % EYE_CYCLE_MS
    const id = window.setTimeout(onRelease, EYE_CYCLE_MS - intoCycle)
    return () => window.clearTimeout(id)
  }, [ready, released, onRelease])

  // click / tap the coffee: a drop falls there (ripples + eyes wobble) and the mug sways as if about to spill
  const mug = useRef<HTMLDivElement>(null)
  const drop = (e: React.PointerEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - r.left) / r.width) * 2 - 1
    const y = -(((e.clientY - r.top) / r.height) * 2 - 1)
    if (x * x + y * y > 1) return
    emitDrop(x, y)
    const el = mug.current
    if (!el) return
    const len = Math.hypot(x, y) || 1
    // the cup tips away from where the drop hit (screen y is down)
    el.style.setProperty('--sway-x', String(len < 0.15 ? 0 : -x / len))
    el.style.setProperty('--sway-y', String(len < 0.15 ? 1 : y / len))
    el.dataset.sway = 'false'
    void el.offsetWidth // restart the animation on rapid clicks
    el.dataset.sway = 'true'
  }

  const opacity = released ? 1 - band(p, 0.004, 0.05) : 1
  const visible = opacity > 0

  return (
    <div
      className="loader-scene"
      data-motion={reducedMotion ? 'reduced' : 'full'}
      style={{ opacity, visibility: visible ? 'visible' : 'hidden' }}
    >
      <div className="mug" aria-hidden="true" ref={mug}>
        <div className="mug-handle" />
        <div className="mug-rim" />
        <div className="mug-coffee" onPointerDown={reducedMotion ? undefined : drop}>
          <CoffeeSurface reducedMotion={reducedMotion || !visible} />
          <TutuEyes />
        </div>
        <div className="steam">
          <span />
          <span />
          <span />
        </div>
      </div>

      <div className="loader-status" role="status" aria-live="polite">
        {!released ? (
          <>
            <p className="loader-value">
              {Math.round(progress)}
              <span>%</span>
            </p>
            <div className="loader-bar" aria-hidden="true">
              <span style={{ transform: `scaleX(${progress / 100})` }} />
            </div>
            <p className="label">{t.loading}</p>
          </>
        ) : (
          <>
            <p className="label loader-done">100%</p>
            <p className="scroll-hint label">
              <span className={isTouch ? 'hint-arrow' : 'hint-mouse'} aria-hidden="true" />
              {isTouch ? t.scrollHintTouch : t.scrollHint}
            </p>
          </>
        )}
      </div>
    </div>
  )
}
