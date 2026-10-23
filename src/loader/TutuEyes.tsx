import { useEffect, useRef } from 'react'
import { onDrop } from './drops'

/**
 * Tutu's eyes reflected in the coffee (she is leaning over the mug). Same almond shape and blue
 * (#9FD3F0) as the 3D model. The loop — blink → look right → look left → back — is pure CSS
 * (`EYE_CYCLE_MS`), so the loader can release the scroll exactly at the end of a cycle.
 * When the pointer moves, the pupils follow it instead (blinking keeps going); after a short idle
 * moment they drift back and the look-around loop resumes. A drop in the coffee (drops.ts) breaks the
 * reflection up for a moment, like a pebble in a puddle, then it settles back.
 */
export const EYE_CYCLE_MS = 4200
const IDLE_MS = 2200
const MAX_X = 15 // svg units the pupils may travel
const MAX_Y = 6
const CALM = 3.5 // resting displacement of the reflection

const ALMOND = 'M -36 0 Q 0 -36 36 0 Q 0 36 -36 0 Z'

function Eye({ x, id }: { x: number; id: string }) {
  return (
    <g transform={`translate(${x} 50)`}>
      <clipPath id={`clip-${id}`}>
        <path d={ALMOND} />
      </clipPath>
      <g className="eye-lid">
        <path d={ALMOND} fill="url(#iris)" />
        <g clipPath={`url(#clip-${id})`}>
          <g className="eye-track">
            <g className="eye-pupil">
              <ellipse rx="5.5" ry="24" fill="#0E0B0C" />
              <circle cx="8" cy="-7" r="3.6" fill="#FFFFFF" opacity="0.9" />
            </g>
          </g>
        </g>
      </g>
    </g>
  )
}

export function TutuEyes() {
  const svg = useRef<SVGSVGElement>(null)
  const disp = useRef<SVGFEDisplacementMapElement>(null)
  const wobble = useRef<SVGGElement>(null)

  useEffect(() => {
    const el = svg.current
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let idle = 0
    const set = (dx: number, dy: number) => {
      el.querySelectorAll<SVGGElement>('.eye-track').forEach((g) => g.setAttribute('transform', `translate(${dx} ${dy})`))
    }
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      const cx = r.left + r.width / 2
      const cy = r.top + r.height / 2
      // normalised against the screen so the eyes keep following far from the mug
      const nx = Math.max(-1, Math.min(1, (e.clientX - cx) / (window.innerWidth / 2)))
      const ny = Math.max(-1, Math.min(1, (e.clientY - cy) / (window.innerHeight / 2)))
      el.dataset.tracking = 'true'
      set(nx * MAX_X, ny * MAX_Y)
      window.clearTimeout(idle)
      idle = window.setTimeout(() => {
        el.dataset.tracking = 'false'
        set(0, 0)
      }, IDLE_MS)
    }
    window.addEventListener('pointermove', onMove)

    // drop: the displacement jumps and rings down; the eyes bob and squash with the passing waves
    let raf = 0
    let dropAt = 0
    const ring = (now: number) => {
      const age = (now - dropAt) / 1000
      const k = Math.exp(-age * 2.2)
      disp.current?.setAttribute('scale', String(CALM + 26 * k * Math.abs(Math.cos(age * 7))))
      const sy = 1 + 0.08 * k * Math.sin(age * 11)
      const bob = 3 * k * Math.sin(age * 9)
      wobble.current?.setAttribute('transform', `translate(100 ${50 + bob}) scale(${2 - sy} ${sy}) translate(-100 -50)`)
      if (age < 2.5) raf = requestAnimationFrame(ring)
      else {
        disp.current?.setAttribute('scale', String(CALM))
        wobble.current?.removeAttribute('transform')
      }
    }
    const offDrop = onDrop((d) => {
      dropAt = d.at
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(ring)
    })
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.clearTimeout(idle)
      cancelAnimationFrame(raf)
      offDrop()
    }
  }, [])

  return (
    <svg ref={svg} className="tutu-eyes" viewBox="0 0 200 100" aria-hidden="true" data-tracking="false">
      <defs>
        <radialGradient id="iris" cx="50%" cy="35%" r="70%">
          <stop offset="0%" stopColor="#CBE8F8" />
          <stop offset="60%" stopColor="#9FD3F0" />
          <stop offset="100%" stopColor="#6FA9CC" />
        </radialGradient>
        {/* a slow wobble so it reads as a reflection on liquid */}
        <filter id="ripple" x="-10%" y="-30%" width="120%" height="160%">
          <feTurbulence type="fractalNoise" baseFrequency="0.018 0.05" numOctaves="1" seed="3">
            <animate attributeName="baseFrequency" dur="7s" values="0.018 0.05;0.022 0.06;0.018 0.05" repeatCount="indefinite" />
          </feTurbulence>
          <feDisplacementMap ref={disp} in="SourceGraphic" scale={CALM} />
        </filter>
      </defs>
      <g filter="url(#ripple)">
        <g ref={wobble}>
          <Eye x={60} id="l" />
          <Eye x={140} id="r" />
        </g>
      </g>
    </svg>
  )
}
