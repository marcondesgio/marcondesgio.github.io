import { band } from '../scroll/progress'

/**
 * What every character does at story progress p (spec §4). Pure function so it is easy to tune and
 * reversible by construction: scrolling back just evaluates an earlier p.
 *
 * mode 'scrub' = clip time is a function of p; mode 'loop' = ambient loop on wall-clock time.
 */
export type ClipState = { clip: string; mode: 'scrub'; t: number } | { clip: string; mode: 'loop' }

export type StoryState = {
  gio: ClipState
  tutu: ClipState
  /** where Tutu's root is: her desk spot, flying along the jump arc, or Gio's cat anchor (floor → arms → lap) */
  tutuOn: 'desk' | 'jump' | 'anchor'
  jump: number // 0..1 along the arc from the desk to the floor
  cupBroken: boolean
  fracture: number // 0..1 of cup_fall_break
  chairTurn: number // 0..1 → 0..180°
}

const scrub = (clip: string, t: number): ClipState => ({ clip, mode: 'scrub', t })
const loop = (clip: string): ClipState => ({ clip, mode: 'loop' })

// cup_fall_break: impact is frame 36 of 200 (60 fps) → 0.18 of the clip
const IMPACT = 0.18
// tutu_slap (24 frames) touches the mug at frame 13; the mug is pushed from that exact p
const SLAP = [0.24, 0.31] as const
const CONTACT = SLAP[0] + (SLAP[1] - SLAP[0]) * (12 / 23)
// tutu_jump_down (36 frames): she leaves the desk at frame 12 and lands at frame 26
const JUMP_AIR = [11 / 35, 25 / 35] as const

export function storyAt(p: number): StoryState {
  const s: StoryState = {
    gio: loop('gio_typing_loop'),
    tutu: loop('tutu_sit_bored_loop'),
    tutuOn: 'desk',
    jump: 0,
    cupBroken: false,
    fracture: 0,
    chairTurn: 0,
  }

  // Scenes 0 → 1 — leaning over the mug (her eyes in the coffee), then she sits up beside it
  if (p < 0.09) s.tutu = scrub('tutu_lean_cup', 1 - band(p, 0.04, 0.09))

  // Scene 2 — the slap: look at Gio, look back at the mug, wind up and swat it (then watch it go over the edge)
  if (p >= 0.15) {
    if (p < 0.2) s.tutu = scrub('tutu_look_gio', band(p, 0.15, 0.2))
    else if (p < SLAP[0]) s.tutu = scrub('tutu_look_cup', band(p, 0.2, SLAP[0]))
    else s.tutu = scrub('tutu_slap', band(p, SLAP[0], SLAP[1]))
  }

  // Scenes 3–4 — the paw touches the mug and it starts sliding right then; fall until just after impact,
  // then the shards settle and stay put
  if (p >= CONTACT) {
    s.cupBroken = true
    s.fracture =
      p < 0.45 ? band(p, CONTACT, 0.45) * (IMPACT + 0.04) : IMPACT + 0.04 + band(p, 0.45, 0.49) * (1 - IMPACT - 0.04)
  }

  // Scene 5 — she jumps down next to the shards and puts on her "não fui eu" face as the broom arrives
  if (p >= 0.63) {
    const t = band(p, 0.63, 0.69)
    s.tutu = scrub('tutu_jump_down', t)
    s.tutuOn = 'jump'
    s.jump = band(t, JUMP_AIR[0], JUMP_AIR[1])
  }
  if (p >= 0.65) s.gio = scrub('gio_broom_enter', band(p, 0.65, 0.8))
  if (p >= 0.69) {
    s.tutu = loop('tutu_sit_floor_innocent')
    s.tutuOn = 'anchor'
  }

  // Scene 6 — Gio crouches and picks her up (lift starts ~0.6 into the clip), walks back, sits facing us
  if (p >= 0.8) {
    s.gio = p < 0.86 ? scrub('gio_crouch_pick_cat', band(p, 0.8, 0.86)) : scrub('gio_sit_with_cat', band(p, 0.86, 0.92))
    s.chairTurn = band(p, 0.88, 0.91)
  }
  if (p >= 0.83) s.tutu = scrub('tutu_picked_up', band(p, 0.83, 0.86))
  if (p >= 0.9) s.tutu = loop('tutu_lap_loop')

  // Scene 7 — about me: idle with Tutu on the lap
  if (p >= 0.92) s.gio = loop('gio_idle_lap_loop')

  return s
}
