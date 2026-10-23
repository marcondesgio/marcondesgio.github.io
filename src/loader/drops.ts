/**
 * A drop falling into the loader's coffee (click / tap on it). Position is in coffee space: -1..1 on both
 * axes, y up, centre of the cup at 0,0. The shader draws the ripple rings and the eyes' reflection wobbles.
 */
export type Drop = { x: number; y: number; at: number }

type Listener = (d: Drop) => void
const listeners = new Set<Listener>()

export function emitDrop(x: number, y: number) {
  const d = { x, y, at: performance.now() }
  listeners.forEach((l) => l(d))
}

export function onDrop(l: Listener) {
  listeners.add(l)
  return () => void listeners.delete(l)
}
