import { useEffect, useMemo } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Vector3 } from 'three'
import { band, progress } from '../scroll/progress'
import { b2t, smoothstep } from './coords'
import { cameraTarget, cupFocus } from './focus'

type Key = { p: number; pos: [number, number, number]; target: [number, number, number]; fit?: boolean }

/**
 * Camera keyframes along p, in Blender coordinates (match the preview renders). Between keys the path is
 * a Catmull-Rom spline, so the camera glides through the story instead of stopping at every key;
 * repeating a key makes a hold. `fit` keys frame a wide subject (the shards): on portrait screens the
 * camera backs off along its view line.
 */
const KEYS: Key[] = [
  // scene 0 hand-off: straight down into the mug, same size as the loader mug, held while it fades
  { p: 0.0, pos: [0.47, 0.299, 1.02], target: [0.47, 0.3, 0.8] },
  { p: 0.05, pos: [0.47, 0.299, 1.02], target: [0.47, 0.3, 0.8] },
  // scene 1: lift off the mug and swing out to reveal Gio, Tutu and the mug
  { p: 0.09, pos: [0.86, 0.02, 1.28], target: [0.42, 0.3, 0.84] },
  { p: 0.14, pos: [1.15, -1.55, 1.45], target: [0.0, 0.35, 0.92] },
  // scene 2: ease in on Tutu and the mug
  { p: 0.2, pos: [1.05, -0.95, 1.25], target: [0.36, 0.38, 0.88] },
  { p: 0.27, pos: [0.98, -0.42, 1.02], target: [0.45, 0.36, 0.84] }, // close on the swat
  { p: 0.3, pos: [0.98, -0.42, 1.02], target: [0.47, 0.3, 0.82] },
  // scene 3 (0.30–0.45) orbits the falling mug, blended in by the code below
  { p: 0.38, pos: [1.1, -0.9, 0.72], target: [0.5, -0.12, 0.55] },
  // scene 4: all five shards, steady while people hover them
  { p: 0.48, pos: [0.54, -0.86, 0.46], target: [0.53, -0.2, 0.04], fit: true },
  { p: 0.63, pos: [0.54, -0.86, 0.46], target: [0.53, -0.2, 0.04], fit: true },
  // scene 5: down to the floor — legs, broom and Tutu only
  { p: 0.7, pos: [0.38, -1.5, 0.22], target: [0.8, -0.45, 0.24] },
  { p: 0.78, pos: [0.35, -1.55, 0.2], target: [0.8, -0.45, 0.25] },
  // scene 6: the crouch, then rise with her to the torso + Tutu framing of the eu_e_tutu photo
  { p: 0.84, pos: [0.25, -1.5, 0.5], target: [0.8, -0.45, 0.3] },
  { p: 0.88, pos: [0.15, -1.55, 0.85], target: [0.4, -0.35, 0.7] },
  { p: 0.93, pos: [-0.22, -1.55, 1.1], target: [-0.22, -0.22, 0.95] },
  { p: 1.0, pos: [-0.22, -1.35, 1.1], target: [-0.22, -0.22, 0.97] },
]

const RIM_Z = 0.845 // top of the mug on the desk (Blender z)

/** Loader mug is min(56vh, 72vw) wide (loader.css); intro keys are tuned for 56vh. */
function introScale(width: number, height: number) {
  return Math.min(0.56 * height, 0.72 * width, 560) / (0.56 * height)
}

function catmullRom(out: Vector3, p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: number) {
  const t2 = t * t
  const t3 = t2 * t
  for (const axis of ['x', 'y', 'z'] as const) {
    out[axis] =
      0.5 *
      (2 * p1[axis] +
        (-p0[axis] + p2[axis]) * t +
        (2 * p0[axis] - 5 * p1[axis] + 4 * p2[axis] - p3[axis]) * t2 +
        (-p0[axis] + 3 * p1[axis] - 3 * p2[axis] + p3[axis]) * t3)
  }
  return out
}

const reducedMotion =
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

export function CameraRig() {
  const camera = useThree((s) => s.camera)
  const size = useThree((s) => s.size)

  const keys = useMemo(() => {
    const k = introScale(size.width, size.height)
    const back = Math.max(1, Math.pow(1.3 / (size.width / size.height), 0.75))
    return KEYS.map((key) => {
      const pos: [number, number, number] =
        key.p <= 0.05 ? [key.pos[0], key.pos[1], RIM_Z + (key.pos[2] - RIM_Z) / k] : key.pos
      const target = b2t(...key.target)
      const p = b2t(...pos)
      if (key.fit) p.sub(target).multiplyScalar(back).add(target)
      return { p: key.p, pos: p, target }
    })
  }, [size.width, size.height])

  const v = useMemo(
    () => ({
      pos: new Vector3(),
      target: new Vector3(),
      orbit: new Vector3(),
      right: new Vector3(),
      up: new Vector3(),
      pointer: { x: 0, y: 0, tx: 0, ty: 0 },
    }),
    [],
  )

  // a touch of pointer parallax on desktop
  useEffect(() => {
    if (reducedMotion || window.matchMedia('(hover: none)').matches) return
    const onMove = (e: PointerEvent) => {
      v.pointer.tx = (e.clientX / window.innerWidth) * 2 - 1
      v.pointer.ty = (e.clientY / window.innerHeight) * 2 - 1
    }
    window.addEventListener('pointermove', onMove)
    return () => window.removeEventListener('pointermove', onMove)
  }, [v])

  useFrame((_, delta) => {
    const p = progress.p
    let i = keys.findIndex((k) => k.p > p) - 1
    if (i < 0) i = p < keys[0].p ? 0 : keys.length - 2
    i = Math.min(i, keys.length - 2)
    const k0 = keys[Math.max(0, i - 1)]
    const k1 = keys[i]
    const k2 = keys[i + 1]
    const k3 = keys[Math.min(keys.length - 1, i + 2)]
    const t = Math.min(1, Math.max(0, (p - k1.p) / (k2.p - k1.p)))
    // holds (identical keys) stay perfectly still; elsewhere the spline keeps velocity continuous
    if (k1.pos.equals(k2.pos) && k1.target.equals(k2.target)) {
      v.pos.copy(k1.pos)
      v.target.copy(k1.target)
    } else {
      catmullRom(v.pos, k0.pos, k1.pos, k2.pos, k3.pos, t)
      catmullRom(v.target, k0.target, k1.target, k2.target, k3.target, t)
    }

    // scene 3: orbit the falling mug and follow it to the floor (spec: "pode girar em volta da xícara")
    const w = smoothstep(band(p, 0.29, 0.32)) * (1 - smoothstep(band(p, 0.44, 0.47)))
    if (w > 0) {
      const a = (-25 + 110 * band(p, 0.3, 0.45)) * (Math.PI / 180)
      const r = 0.62
      // three.js space (y up): circle around the mug in the floor plane, a little above it
      v.orbit.set(cupFocus.x + Math.sin(a) * r, cupFocus.y + 0.22, cupFocus.z + Math.cos(a) * r)
      v.pos.lerp(v.orbit, w)
      v.target.lerp(cupFocus, w)
    }

    // eased pointer parallax; off while the loader mug has to line up exactly
    const pp = v.pointer
    const ease = Math.min(1, delta * 3)
    pp.x += (pp.tx - pp.x) * ease
    pp.y += (pp.ty - pp.y) * ease
    camera.position.copy(v.pos)
    camera.lookAt(v.target)
    camera.updateMatrix()
    cameraTarget.copy(v.target)
    const amount = 0.035 * band(p, 0.05, 0.1)
    if (amount > 0) {
      v.right.setFromMatrixColumn(camera.matrix, 0)
      v.up.setFromMatrixColumn(camera.matrix, 1)
      camera.position.addScaledVector(v.right, pp.x * amount).addScaledVector(v.up, -pp.y * amount * 0.6)
      camera.lookAt(v.target)
    }
  })
  return null
}
