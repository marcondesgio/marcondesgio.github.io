/**
 * Dev-only clip preview (open the site with ?debug). When a clip is picked here it loops on wall-clock
 * time and overrides the scroll timeline for that model.
 */
import { useSyncExternalStore } from 'react'

export type DebugModel = 'gio' | 'tutu' | 'cup'
type State = { overrides: Partial<Record<DebugModel, string>>; clips: Partial<Record<DebugModel, string[]>> }

let state: State = { overrides: {}, clips: {} }
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((l) => l())

export const debugEnabled = typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('debug')

export const debug = {
  get state() {
    return state
  },
  setOverride(model: DebugModel, clip: string | undefined) {
    state = { ...state, overrides: { ...state.overrides, [model]: clip } }
    emit()
  },
  registerClips(model: DebugModel, clips: string[]) {
    state = { ...state, clips: { ...state.clips, [model]: clips } }
    emit()
  },
  subscribe(l: () => void) {
    listeners.add(l)
    return () => listeners.delete(l)
  },
}

export function useDebug() {
  return useSyncExternalStore(debug.subscribe, () => state)
}
