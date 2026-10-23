import { storyToScroll } from '../scroll/progress'

type Probe = Record<string, unknown> & { p: number }
declare global {
  interface Window {
    __probe?: () => Probe
  }
}

const POINTS = [0.02, 0.12, 0.2, 0.28, 0.36, 0.42, 0.5, 0.6, 0.66, 0.72, 0.84, 0.88, 0.95]
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

/**
 * Scroll to p, wait until the (scrubbed, smoothed) story has settled there, then until the 3D scene has
 * really drawn a few new frames: browsers pause requestAnimationFrame in a hidden tab while GSAP keeps
 * updating p on timers, which would compare a new p against an old picture.
 */
async function go(p: number): Promise<Probe> {
  const track = document.querySelector<HTMLElement>('.scroll-track')!
  window.scrollTo({ top: storyToScroll(p) * (track.offsetHeight - window.innerHeight) })
  let last = -1
  for (let i = 0; i < 80; i++) {
    await sleep(100)
    const s = window.__probe!()
    if (Math.abs(s.p - p) < 0.0006 && s.p === last) break
    last = s.p
  }
  const start = window.__probe!().frame as number
  for (let i = 0; i < 60; i++) {
    await sleep(50)
    const s = window.__probe!()
    if ((s.frame as number) >= start + 4) return s
  }
  throw new Error('the 3D scene is not rendering — keep the tab visible while the test runs')
}

/**
 * Reversal check (spec §4 "Reversão"): visit key points forward, go to the end, visit them again
 * backward and compare what is on screen (camera, Tutu, Gio, a shard, chair, mug). Ambient loops
 * driven by the clock (typing, breathing on the lap) may differ by a few millimetres.
 */
export async function runReversalTest() {
  if (!window.__probe) throw new Error('open the site with ?debug')
  const forward = new Map<number, Probe>()
  for (const p of POINTS) forward.set(p, await go(p))
  await go(1)
  const diffs: string[] = []
  for (const p of [...POINTS].reverse()) {
    const back = await go(p)
    const fwd = forward.get(p)!
    for (const key of Object.keys(fwd)) {
      if (key === 'p' || key === 'frame') continue
      const a = JSON.stringify(fwd[key])
      const b = JSON.stringify(back[key])
      if (a !== b) diffs.push(`p=${p} ${key}: ${a} → ${b}`)
    }
  }
  return { checked: POINTS.length, diffs }
}
