/**
 * Loading progress shared by the light loader (scene 0) and the lazily loaded 3D chunk.
 * Kept dependency-free so it lives in the initial bundle.
 */
import { useSyncExternalStore } from 'react'

type State = { progress: number; ready: boolean }

let state: State = { progress: 0, ready: false }
const listeners = new Set<() => void>()

export const loadState = {
  get: () => state,
  set(patch: Partial<State>) {
    const next = { ...state, ...patch }
    // progress never goes backwards (the loader manager can report fewer items as new ones queue up)
    next.progress = Math.max(state.progress, Math.min(100, next.progress))
    if (next.progress === state.progress && next.ready === state.ready) return
    state = next
    listeners.forEach((l) => l())
  },
  subscribe(l: () => void) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
}

export function useLoadState() {
  return useSyncExternalStore(loadState.subscribe, loadState.get)
}
