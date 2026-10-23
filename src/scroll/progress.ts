/**
 * The single story progress value p ∈ [0, 1] (spec §3). Written by ScrollDriver, read every frame by the
 * 3D scene without React re-renders. UI that needs to re-render subscribes with useProgressValue().
 */
import { useSyncExternalStore } from 'react'

type Listener = (p: number) => void

const state = { p: 0 }
const listeners = new Set<Listener>()

export const progress = {
  get p() {
    return state.p
  },
  set(p: number) {
    const next = Math.min(1, Math.max(0, p))
    if (next === state.p) return
    state.p = next
    listeners.forEach((l) => l(next))
  },
  subscribe(l: Listener) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
}

/** React hook for UI; quantized so overlays don't re-render on every pixel of scroll. */
export function useProgressValue(step = 0.005) {
  return useSyncExternalStore(
    (cb) => progress.subscribe(cb),
    () => Math.round(progress.p / step) * step,
  )
}

/** Story bands (spec §4). Ranges are starting points; tweak here only. */
export const SCENES = [
  { id: 'desk', from: 0.0, to: 0.15 },
  { id: 'slap', from: 0.15, to: 0.3 },
  { id: 'fall', from: 0.3, to: 0.45 },
  { id: 'shards', from: 0.45, to: 0.65 },
  { id: 'broom', from: 0.65, to: 0.8 },
  { id: 'lap', from: 0.8, to: 0.92 },
  { id: 'about', from: 0.92, to: 1.0 },
] as const

export type SceneId = (typeof SCENES)[number]['id']

export function sceneAt(p: number) {
  return SCENES.find((s) => p < s.to) ?? SCENES[SCENES.length - 1]
}

/** Local 0..1 progress of p inside [a, b], clamped. */
export function band(p: number, a: number, b: number) {
  return Math.min(1, Math.max(0, (p - a) / (b - a)))
}

/**
 * Pause zone (spec §4, scene 4): the shards band takes SLOW.weight times more scroll than its share of
 * p, so the story lingers while people hover the projects. Scroll fraction s ∈ [0, 1] ↔ story p.
 */
const SLOW = { from: 0.45, to: 0.65, weight: 2.4 }
const SLOW_EXTRA = (SLOW.to - SLOW.from) * (SLOW.weight - 1)
const TOTAL = 1 + SLOW_EXTRA

export function scrollToStory(s: number) {
  const u = s * TOTAL
  if (u <= SLOW.from) return u
  const slowEnd = SLOW.from + (SLOW.to - SLOW.from) * SLOW.weight
  if (u <= slowEnd) return SLOW.from + (u - SLOW.from) / SLOW.weight
  return u - SLOW_EXTRA
}

export function storyToScroll(p: number) {
  let u = p
  if (p > SLOW.from) u = SLOW.from + (Math.min(p, SLOW.to) - SLOW.from) * SLOW.weight + Math.max(0, p - SLOW.to)
  return u / TOTAL
}
