import { Vector3 } from 'three'

/** Blender (Z up) -> three.js (Y up), same conversion the glTF exporter applies. */
export function b2t(x: number, y: number, z: number) {
  return new Vector3(x, z, -y)
}

export const deg = (d: number) => (d * Math.PI) / 180

export function smoothstep(t: number) {
  const c = Math.min(1, Math.max(0, t))
  return c * c * (3 - 2 * c)
}
