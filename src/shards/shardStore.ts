/**
 * Which project shard is active and where it is on screen. Shared by the 3D scene (hover/tap), the
 * floating label and the accessible project list (keyboard focus), so all three stay in sync.
 * Screen position updates every frame and is pushed straight to the label's DOM, not through React.
 */
import { useSyncExternalStore } from 'react'

export type ShardSource = 'pointer' | 'touch' | 'focus'
type State = { active: number | null; source: ShardSource | null; interactive: boolean }

let state: State = { active: null, source: null, interactive: false }
const listeners = new Set<() => void>()
type PosListener = (x: number, y: number, visible: boolean) => void
let posListener: PosListener | null = null

export const INTERACTIVE_FROM = 0.49 // shards have settled
export const INTERACTIVE_TO = 0.65 // the broom arrives: shards become scenery

export const shardStore = {
  get: () => state,
  set(patch: Partial<State>) {
    const next = { ...state, ...patch }
    if (next.active === state.active && next.source === state.source && next.interactive === state.interactive) return
    state = next
    listeners.forEach((l) => l())
  },
  subscribe(l: () => void) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
  onPosition(l: PosListener | null) {
    posListener = l
  },
  pushPosition(x: number, y: number, visible: boolean) {
    posListener?.(x, y, visible)
  },
}

export function useShardState() {
  return useSyncExternalStore(shardStore.subscribe, shardStore.get)
}

export const isTouchDevice =
  typeof window !== 'undefined' && window.matchMedia('(hover: none), (pointer: coarse)').matches
