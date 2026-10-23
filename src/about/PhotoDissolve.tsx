import { useEffect, useRef } from 'react'
import { band, progress } from '../scroll/progress'
import { PHOTO } from '../data/contact'
import { Photo } from './Photo'
import { aboutRefs } from './aboutRefs'

const smooth = (t: number) => t * t * (3 - 2 * t)
const lerp = (a: number, b: number, t: number) => a + (b - a) * t
const reducedMotion =
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Scene 7 (spec §4): the 3D Gio + Tutu dissolve, with a soft glow, into the real eu_e_tutu photo in the
 * same framing (the camera's last key centres them like the photo), then the photo glides into the About
 * section's slot while a night veil covers the 3D. Everything is a function of p and the slot's layout,
 * so scrolling back runs it in reverse. After the story ends the photo simply tracks its slot.
 */
export function PhotoDissolve() {
  const wrap = useRef<HTMLDivElement>(null)
  const img = useRef<HTMLImageElement>(null)
  const veil = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let raf = 0
    const frame = () => {
      raf = requestAnimationFrame(frame)
      const el = wrap.current
      const slot = aboutRefs.slot
      const section = aboutRefs.section
      if (!el || !slot || !section) return
      const p = progress.p
      const vw = window.innerWidth
      const vh = window.innerHeight

      // 1) dissolve in place (p 0.915 → 0.95), framed like the 3D torso shot
      const d = smooth(band(p, 0.915, 0.95))
      // 2) glide to the About slot (p 0.955 → 0.995) while the night veil comes in
      const m = smooth(band(p, 0.955, 0.995))

      const h0 = vh * 0.86
      const start = { w: h0 * PHOTO.aspect, h: h0, x: (vw - h0 * PHOTO.aspect) / 2, y: vh * 0.07 }
      const sr = slot.getBoundingClientRect()
      const top = section.getBoundingClientRect().top
      // where the slot will be once the section reaches the top (= live slot once it has)
      const rest = { w: sr.width, h: sr.height, x: sr.left, y: top > 0 ? sr.top - top : sr.top }
      const r =
        top > 0
          ? { w: lerp(start.w, rest.w, m), h: lerp(start.h, rest.h, m), x: lerp(start.x, rest.x, m), y: lerp(start.y, rest.y, m) }
          : rest

      const visible = d > 0.001
      el.style.visibility = visible ? 'visible' : 'hidden'
      el.style.transform = `translate(${r.x}px, ${r.y}px)`
      el.style.width = `${r.w}px`
      el.style.height = `${r.h}px`
      el.style.borderRadius = `${lerp(8, 28, m)}px`

      // the dissolve: a growing soft radial mask + a glow that peaks halfway
      const glow = reducedMotion ? 0 : Math.sin(Math.PI * d)
      const radius = reducedMotion ? (d > 0.5 ? 200 : 0) : d * 135
      const mask = `radial-gradient(circle at 50% 42%, #000 ${radius - 22}%, transparent ${radius}%)`
      el.style.maskImage = mask
      el.style.webkitMaskImage = mask
      if (img.current) img.current.style.filter = `brightness(${1 + 0.55 * glow}) saturate(${1 - 0.25 * glow})`
      el.style.boxShadow = `0 0 ${60 + 60 * glow}px rgb(255 143 192 / ${0.35 * glow}), var(--shadow-3)`

      if (veil.current) veil.current.style.opacity = String(smooth(band(p, 0.95, 0.99)))
      if (aboutRefs.content) aboutRefs.content.style.opacity = String(smooth(band(p, 0.96, 1)))
    }
    raf = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(raf)
  }, [])

  return (
    <>
      <div ref={veil} className="night-veil" aria-hidden="true" />
      <div ref={wrap} className="photo-dissolve">
        <Photo ref={img} />
      </div>
    </>
  )
}
