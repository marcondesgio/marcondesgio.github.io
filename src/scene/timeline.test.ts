/**
 * Reversibility (spec §1, §3): everything on screen is a pure function of p, so scrolling back must give
 * exactly the same state as scrolling forward. These tests pin that down and check the timeline only
 * references clips that really exist in the exported GLBs.
 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { storyAt, type ClipState } from './timeline'
import { scrollToStory, storyToScroll } from '../scroll/progress'

function glbAnimations(file: string): string[] {
  const buf = readFileSync(new URL(`../../public/models/${file}`, import.meta.url))
  const len = buf.readUInt32LE(12)
  const json = JSON.parse(buf.subarray(20, 20 + len).toString('utf8'))
  return (json.animations ?? []).map((a: { name: string }) => a.name)
}

const STEP = 0.0005
const ps = Array.from({ length: Math.round(1 / STEP) + 1 }, (_, i) => Math.min(1, i * STEP))

describe('scroll ↔ story mapping (pause zone)', () => {
  it('round-trips and is monotonic', () => {
    let prev = -1
    for (const p of ps) {
      expect(scrollToStory(storyToScroll(p))).toBeCloseTo(p, 9)
      const s = storyToScroll(p)
      expect(s).toBeGreaterThanOrEqual(prev)
      prev = s
    }
    expect(storyToScroll(0)).toBe(0)
    expect(storyToScroll(1)).toBeCloseTo(1, 12)
  })
})

describe('storyAt', () => {
  it('gives the same state scrolling forward and backward', () => {
    const forward = ps.map((p) => JSON.stringify(storyAt(p)))
    const backward = [...ps].reverse().map((p) => JSON.stringify(storyAt(p))).reverse()
    expect(backward).toEqual(forward)
  })

  it('keeps every scrubbed time, the jump and the chair inside [0, 1]', () => {
    for (const p of ps) {
      const s = storyAt(p)
      for (const c of [s.gio, s.tutu]) if (c.mode === 'scrub') expect(c.t).toBeGreaterThanOrEqual(0), expect(c.t).toBeLessThanOrEqual(1)
      for (const v of [s.jump, s.fracture, s.chairTurn]) expect(v).toBeGreaterThanOrEqual(0), expect(v).toBeLessThanOrEqual(1)
    }
  })

  it('only uses clips that exist in the GLBs', () => {
    const gio = new Set(glbAnimations('gio.glb'))
    const tutu = new Set(glbAnimations('tutu.glb'))
    expect(glbAnimations('cup_fracture.glb')).toContain('cup_fall_break')
    for (const p of ps) {
      const s = storyAt(p)
      expect(gio, `gio clip at p=${p}`).toContain(s.gio.clip)
      expect(tutu, `tutu clip at p=${p}`).toContain(s.tutu.clip)
    }
  })

  it('moves scrubbed clips smoothly (no jumps while the same clip plays)', () => {
    const jumps: string[] = []
    const check = (who: string, a: ClipState, b: ClipState, p: number) => {
      if (a.mode === 'scrub' && b.mode === 'scrub' && a.clip === b.clip && Math.abs(a.t - b.t) > 0.05) {
        jumps.push(`${who} ${a.clip} @ p=${p.toFixed(4)}: ${a.t.toFixed(3)} → ${b.t.toFixed(3)}`)
      }
    }
    for (let i = 1; i < ps.length; i++) {
      const a = storyAt(ps[i - 1])
      const b = storyAt(ps[i])
      check('gio', a.gio, b.gio, ps[i])
      check('tutu', a.tutu, b.tutu, ps[i])
      expect(Math.abs(a.fracture - b.fracture), `fracture @ p=${ps[i]}`).toBeLessThan(0.05)
    }
    expect(jumps).toEqual([])
  })
})
