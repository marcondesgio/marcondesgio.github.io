import './loadingHooks'
import { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree, type ThreeEvent } from '@react-three/fiber'
import { useGLTF } from '@react-three/drei'
import { Color, Group, Mesh, MeshBasicMaterial, MeshStandardMaterial, Object3D, Quaternion, RepeatWrapping, type Texture, Vector3 } from 'three'
import { progress } from '../scroll/progress'
import { ClipPlayer } from './ClipPlayer'
import { storyAt, type ClipState } from './timeline'
import { b2t, deg } from './coords'
import { debug, debugEnabled, type DebugModel } from './debug'
import { loadState } from '../loader/loadState'
import { ShardFx } from '../shards/ShardFx'
import { isTouchDevice, shardStore } from '../shards/shardStore'
import { projects } from '../data/projects'
import { cupFocus } from './focus'

const DRACO = '/draco/'
export const MODEL_URLS = {
  desk: '/models/desk_scene.glb',
  cup: '/models/cup.glb',
  fracture: '/models/cup_fracture.glb',
  tutu: '/models/tutu.glb',
  gio: '/models/gio.glb',
}
Object.values(MODEL_URLS).forEach((url) => useGLTF.preload(url, DRACO))

function marker(root: Object3D, name: string) {
  const o = root.getObjectByName(name)
  if (!o) throw new Error(`marker ${name} missing in desk_scene.glb`)
  return o.position.clone()
}

// where Tutu lands next to the shards: Gio's cat anchor at the start of gio_broom_enter (CAT_FLOOR in
// blender/scripts/gio_anim.py), facing +X (90°) so the hand-off to the anchor is seamless
const TUTU_LANDING = b2t(0.6, -0.5, 0)
const TUTU_LANDING_Q = new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), deg(90))
const JUMP_HEIGHT = 0.12

// per-group brightness on top of the lightmaps (the floor scenes need a little lift; no re-bake needed)
// per-lightmap gain, or an [r, g, b] tint: the floor bakes red (R:G:B ≈ 1:0.42:0.4) under the warm lamp and
// lilac fill, so its green is lifted back toward honey wood (≈ 1:0.65:0.45)
const BAKED_GAIN: Record<string, number | [number, number, number]> = { baked_floor: [0.82, 1.25, 0.95], baked_room: 1.2, baked_props: 1.05, baked_desk: 0.7, baked_chair: 0.8 }

/** Opens a project in a new tab; "coming soon" shards have no link. */
export function openProject(index: number) {
  const pr = projects[index]
  if (!pr || ('comingSoon' in pr && pr.comingSoon)) return
  window.open(pr.url, '_blank', 'noopener,noreferrer')
}

function setCursor(index: number | null) {
  const pr = index === null ? null : projects[index]
  document.body.style.cursor = pr && !('comingSoon' in pr && pr.comingSoon) ? 'pointer' : ''
}

function apply(player: ClipPlayer, state: ClipState, elapsed: number) {
  if (state.mode === 'loop') player.loop(state.clip, elapsed)
  else player.showAt(state.clip, state.t)
}

/** Everything in the story, positioned from the desk scene's spot_* markers and driven by p. */
export function Story() {
  const desk = useGLTF(MODEL_URLS.desk, DRACO)
  const cup = useGLTF(MODEL_URLS.cup, DRACO)
  const fracture = useGLTF(MODEL_URLS.fracture, DRACO)
  const tutu = useGLTF(MODEL_URLS.tutu, DRACO)
  const gio = useGLTF(MODEL_URLS.gio, DRACO)

  const cupRef = useRef<Group>(null)
  const tutuRef = useRef<Group>(null)
  const gioRef = useRef<Group>(null)

  const players = useMemo(
    () => ({
      gio: new ClipPlayer(gio.scene, gio.animations),
      tutu: new ClipPlayer(tutu.scene, tutu.animations),
      fracture: new ClipPlayer(fracture.scene, fracture.animations),
    }),
    [gio, tutu, fracture],
  )

  const spots = useMemo(
    () => ({
      cup: marker(desk.scene, 'spot_cup'),
      tutu: marker(desk.scene, 'spot_tutu_desk'),
      gio: marker(desk.scene, 'spot_gio_seat'),
    }),
    [desk],
  )
  const chair = useMemo(() => desk.scene.getObjectByName('chair'), [desk])
  const chairRestY = useMemo(() => chair?.rotation.y ?? 0, [chair])
  const anchor = useMemo(() => gio.scene.getObjectByName('gio_cat_anchor'), [gio])
  const shardFx = useMemo(() => new ShardFx(fracture.scene), [fracture])

  // the spilled coffee was near-black on the night floor: a warmer, lighter brown that still reads as liquid
  useEffect(() => {
    fracture.scene.traverse((o) => {
      const mat = (o as Mesh).material as MeshStandardMaterial | undefined
      if (mat?.name === 'coffee_spill') {
        mat.color.set('#7A4A2E')
        mat.roughness = 0.22
        mat.emissive.set('#2A140C')
      }
    })
  }, [fracture])

  // Baked environment (blender/scripts/bake_desk.py): lighting + AO live in the textures, so those meshes are
  // drawn unlit. Only the lamp and the monitor are real-time lights (Lights.tsx), for the moving characters.
  const screenMap = useMemo(() => {
    let screen: Texture | null = null
    desk.scene.traverse((o) => {
      const mesh = o as Mesh
      if (!mesh.isMesh) return
      const mat = mesh.material as MeshStandardMaterial
      if (mat.name.startsWith('baked_')) {
        const gain = BAKED_GAIN[mat.name] ?? 1
        const [r, g, b] = typeof gain === 'number' ? [gain, gain, gain] : gain
        mesh.material = new MeshBasicMaterial({ map: mat.map, name: mat.name, color: new Color(r, g, b) })
      } else if (mesh.name === 'monitor_screen') {
        screen = mat.emissiveMap ?? mat.map
        if (screen) {
          screen.wrapT = RepeatWrapping
          screen.needsUpdate = true
        }
        mesh.material = new MeshBasicMaterial({ map: screen, name: 'monitor_screen' })
      }
    })
    return screen as Texture | null
  }, [desk])

  useEffect(() => {
    // skinned meshes keep their rest-pose bounds; Gio walks metres away from it, so never cull them
    for (const root of [gio.scene, tutu.scene]) {
      root.traverse((o) => {
        if ((o as Mesh).isMesh) o.frustumCulled = false
      })
    }
  }, [gio, tutu])

  useEffect(() => {
    // models are in (Suspense resolved); give the GPU two frames to compile before calling it ready
    let id = requestAnimationFrame(() => {
      id = requestAnimationFrame(() => loadState.set({ progress: 100, ready: true }))
    })
    return () => cancelAnimationFrame(id)
  }, [])

  // counts rendered frames so the reversal check can wait for the scene to actually redraw
  const renderedFrames = useRef(0)
  useFrame(() => void (renderedFrames.current += 1))

  // ?debug: snapshot of what is on screen, used by the reversal check (forward vs backward must match)
  const getThree = useThree((s) => s.get)
  useEffect(() => {
    if (!debugEnabled) return
    const v = new Vector3()
    const round = (x: Vector3) => x.toArray().map((n) => +n.toFixed(4))
    window.__probe = () => ({
      p: +progress.p.toFixed(4),
      frame: renderedFrames.current,
      camera: round(getThree().camera.position),
      tutu: round(tutuRef.current!.getWorldPosition(v)),
      gioHips: round(gio.scene.getObjectByName('hips')!.getWorldPosition(v)),
      shard1: round(shardFx.shards[0].root.getWorldPosition(v)),
      chairY: +(chair?.rotation.y ?? 0).toFixed(4),
      focus: round(cupFocus),
      cupVisible: cupRef.current?.visible,
      // the swatting paw (three.js drops the '.' from "front_paw.L")
      tutuPaw: round(tutu.scene.getObjectByName('front_pawL')?.getWorldPosition(v) ?? v.set(0, 0, 0)),
    })
  }, [getThree, gio, tutu, shardFx, chair])

  useEffect(() => {
    debug.registerClips('gio', players.gio.names)
    debug.registerClips('tutu', players.tutu.names)
    debug.registerClips('cup', players.fracture.names)
  }, [players])

  // scratch objects for attaching Tutu to Gio's cat anchor
  const tmp = useMemo(() => ({ p: new Vector3(), q: new Quaternion(), s: new Vector3(), up: new Vector3(0, 1, 0) }), [])

  useFrame(({ clock, camera, size }, delta) => {
    const elapsed = clock.elapsedTime
    const s = storyAt(progress.p)
    const o = debug.state.overrides
    const pick = (model: DebugModel, fallback: ClipState): ClipState =>
      o[model] ? { clip: o[model]!, mode: 'loop' } : fallback

    apply(players.gio, pick('gio', s.gio), elapsed)
    apply(players.tutu, pick('tutu', s.tutu), elapsed)

    const broken = s.cupBroken || !!o.cup
    if (cupRef.current) cupRef.current.visible = !broken
    fracture.scene.visible = broken
    if (o.cup) players.fracture.loop(o.cup, elapsed)
    else players.fracture.showAt('cup_fall_break', s.fracture)
    shardFx.update(progress.p, elapsed, delta, camera, size.width, size.height)

    // what the camera follows in scene 3: the mug, or the centre of its five main shards once it breaks
    if (broken) {
      cupFocus.set(0, 0, 0)
      for (const sh of shardFx.shards) cupFocus.add(sh.root.getWorldPosition(tmp.p))
      cupFocus.divideScalar(Math.max(1, shardFx.shards.length))
    } else if (cupRef.current) {
      cupRef.current.getWorldPosition(cupFocus)
    }

    // code slowly scrolling on the monitor (ambient loop)
    if (screenMap) screenMap.offset.y = -((elapsed * 0.012) % 1)

    if (chair) chair.rotation.y = chairRestY + Math.PI * s.chairTurn

    // Tutu sits on the desk, leaps along an arc to the floor, or follows the anchor Gio carries
    const t = tutuRef.current
    if (t) {
      if (s.tutuOn === 'jump') {
        const a = s.jump
        t.position.lerpVectors(spots.tutu, TUTU_LANDING, a)
        t.position.y += JUMP_HEIGHT * Math.sin(Math.PI * a)
        tmp.q.setFromAxisAngle(tmp.up, deg(20))
        t.quaternion.slerpQuaternions(tmp.q, TUTU_LANDING_Q, a)
      } else if (s.tutuOn === 'anchor' && anchor) {
        gioRef.current?.updateMatrixWorld(true)
        anchor.matrixWorld.decompose(tmp.p, tmp.q, tmp.s)
        t.position.copy(tmp.p)
        t.quaternion.copy(tmp.q)
      } else {
        t.position.copy(spots.tutu)
        t.quaternion.setFromAxisAngle(tmp.up, deg(20))
      }
    }
  })

  // scene 4: desktop hover shows the label and click opens; touch: first tap shows, second tap opens
  const onShardHover = (e: ThreeEvent<PointerEvent>) => {
    if (e.pointerType === 'touch' || !shardStore.get().interactive) return
    const index = ShardFx.indexOf(e.object)
    if (index === null) return
    e.stopPropagation()
    shardStore.set({ active: index, source: 'pointer' })
    setCursor(index)
  }
  const onShardOut = (e: ThreeEvent<PointerEvent>) => {
    if (e.pointerType === 'touch' || shardStore.get().source !== 'pointer') return
    shardStore.set({ active: null, source: null })
    setCursor(null)
  }
  const onShardClick = (e: ThreeEvent<MouseEvent>) => {
    const { interactive, active, source } = shardStore.get()
    const index = ShardFx.indexOf(e.object)
    if (!interactive || index === null) return
    e.stopPropagation()
    const touch = isTouchDevice || (e.nativeEvent as PointerEvent).pointerType === 'touch'
    if (!touch || (active === index && source === 'touch')) openProject(index)
    else shardStore.set({ active: index, source: 'touch' })
  }

  return (
    <>
      <primitive object={desk.scene} />
      <group ref={cupRef} position={spots.cup} rotation={[0, deg(20), 0]}>
        <primitive object={cup.scene} />
      </group>
      <group onPointerMove={onShardHover} onPointerOut={onShardOut} onClick={onShardClick}>
        <primitive object={fracture.scene} />
      </group>
      <group ref={tutuRef}>
        <primitive object={tutu.scene} />
      </group>
      <group ref={gioRef} position={spots.gio} rotation={[0, Math.PI, 0]}>
        <primitive object={gio.scene} />
      </group>
    </>
  )
}
