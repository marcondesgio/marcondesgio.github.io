import {
  AdditiveBlending,
  Camera,
  CanvasTexture,
  Color,
  Material,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  MeshBasicMaterial,
  PlaneGeometry,
  Vector3,
} from 'three'
import { projects } from '../data/projects'
import { INTERACTIVE_FROM, INTERACTIVE_TO, shardStore } from './shardStore'

const LAMP = new Color('#FFC98F') // warm rim glow, like the desk lamp
const SHARD_NAME = /^shard_(\d\d)$/

type RimUniforms = { uRim: { value: number }; uRimColor: { value: Color }; uLift: { value: number } }

/** Clone the shard's materials and add a fresnel rim glow ("leve brilho na borda", spec §4) and a float. */
function addRim(material: Material): { material: MeshStandardMaterial; uniforms: RimUniforms } {
  const m = (material as MeshStandardMaterial).clone()
  const uniforms: RimUniforms = { uRim: { value: 0 }, uRimColor: { value: LAMP.clone() }, uLift: { value: 0 } }
  m.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms)
    // the float is a world-space lift in the vertex shader: the animation mixer only re-writes node
    // transforms when the clip value changes, so nudging position.y would accumulate frame after frame
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nuniform float uLift;')
      .replace(
        '#include <project_vertex>',
        `#include <project_vertex>
        mvPosition.xyz += (viewMatrix * vec4(0.0, uLift, 0.0, 0.0)).xyz;
        gl_Position = projectionMatrix * mvPosition;`,
      )
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uRim;\nuniform vec3 uRimColor;')
      .replace(
        '#include <emissivemap_fragment>',
        `#include <emissivemap_fragment>
        float rimF = 1.0 - abs(dot(normalize(normal), normalize(vViewPosition)));
        totalEmissiveRadiance += uRimColor * uRim * (0.25 + 1.6 * pow(rimF, 2.2));`,
      )
  }
  m.customProgramCacheKey = () => 'shard-rim'
  return { material: m, uniforms }
}

export type ShardEntry = { index: number; root: Object3D; uniforms: RimUniforms[]; glow: number; lift: number; halo: Mesh<PlaneGeometry, MeshBasicMaterial> }

// soft round glow texture for the halos under the project shards (drawn once, shared)
function haloTexture() {
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const g = c.getContext('2d')!
  const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64)
  grad.addColorStop(0, 'rgba(255,255,255,1)')
  grad.addColorStop(0.35, 'rgba(255,255,255,0.45)')
  grad.addColorStop(1, 'rgba(255,255,255,0)')
  g.fillStyle = grad
  g.fillRect(0, 0, 128, 128)
  return new CanvasTexture(c)
}
// warm candle tones (feedback round 3: no neon in the room)
const HALO_COLORS = ['#FFD39A', '#FFC48A', '#F5DDB8', '#FFCFA8', '#F0D9B5']

/**
 * The five project shards inside cup_fracture.glb: rim glow, a small float while scene 4 is on, and the
 * per-frame screen position of the active shard for the floating label.
 */
export class ShardFx {
  readonly shards: ShardEntry[] = []
  private tmp = new Vector3()
  private haloMap = haloTexture()
  private haloGeo = new PlaneGeometry(1, 1)

  constructor(root: Object3D) {
    root.traverse((o) => {
      const match = o.name.match(SHARD_NAME)
      if (!match) return
      const index = Number(match[1]) - 1
      if (index >= projects.length) return
      // a flat pool of coloured light on the floor (a billboard would be cut in half by the floor)
      const halo = new Mesh(
        this.haloGeo,
        new MeshBasicMaterial({ map: this.haloMap, color: HALO_COLORS[index % HALO_COLORS.length], transparent: true,
          depthWrite: false, blending: AdditiveBlending, opacity: 0, toneMapped: false }),
      )
      halo.rotation.x = -Math.PI / 2
      halo.scale.setScalar(0.16)
      halo.renderOrder = 2
      root.add(halo)
      const entry: ShardEntry = { index, root: o, uniforms: [], glow: 0, lift: 0, halo }
      o.traverse((c) => {
        const mesh = c as Mesh
        if (!mesh.isMesh) return
        const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
        const patched = mats.map((mat) => addRim(mat))
        entry.uniforms.push(...patched.map((p) => p.uniforms))
        mesh.material = Array.isArray(mesh.material) ? patched.map((p) => p.material) : patched[0].material
        mesh.userData.shardIndex = index
      })
      this.shards.push(entry)
    })
    this.shards.sort((a, b) => a.index - b.index)
  }

  /** Shard index for a raycast hit (walks up to the shard_XX node), or null for fragments/other meshes. */
  static indexOf(obj: Object3D | null): number | null {
    for (let o = obj; o; o = o.parent) {
      const m = o.name.match(SHARD_NAME)
      if (m) return Number(m[1]) - 1
    }
    return null
  }

  /** Run after the fracture clip has posed the shards this frame. */
  update(p: number, elapsed: number, delta: number, camera: Camera, width: number, height: number) {
    const live = p >= INTERACTIVE_FROM && p < INTERACTIVE_TO
    const fadeIn = Math.min(1, Math.max(0, (p - INTERACTIVE_FROM) / 0.015))
    const { active } = shardStore.get()
    shardStore.set({ interactive: live })
    // keyboard focus survives the jump to scene 4; pointer/touch selections end with the scene
    if (!live && active !== null && shardStore.get().source !== 'focus') shardStore.set({ active: null, source: null })

    for (const s of this.shards) {
      const comingSoon = 'comingSoon' in projects[s.index] && projects[s.index].comingSoon
      // projects glow and breathe to invite a hover; "coming soon" shards stay quieter
      const pulse = 0.5 + 0.5 * Math.sin(elapsed * 2.2 + s.index * 1.7)
      const target = !live ? 0 : s.index === active ? 1.5 : comingSoon ? 0.2 : 0.55 + 0.35 * pulse
      s.glow += (target - s.glow) * Math.min(1, delta * 8)
      s.lift = live ? fadeIn * (0.006 + 0.004 * Math.sin(elapsed * 1.6 + s.index * 1.3)) : 0
      for (const u of s.uniforms) {
        u.uRim.value = s.glow
        u.uLift.value = s.lift
      }
      // halo: a soft coloured light pool on the floor right under the shard
      s.root.getWorldPosition(s.halo.position)
      s.halo.position.y = 0.006
      const haloTarget = !live ? 0 : (s.index === active ? 1 : comingSoon ? 0.25 : 0.65 + 0.35 * pulse) * fadeIn
      const m = s.halo.material
      m.opacity += (haloTarget - m.opacity) * Math.min(1, delta * 6)
      s.halo.visible = m.opacity > 0.01
      s.halo.scale.setScalar(0.2 + 0.05 * (s.index === active ? 1 : pulse))
    }

    const a = active === null ? undefined : this.shards.find((s) => s.index === active)
    if (a && live) {
      a.root.getWorldPosition(this.tmp)
      this.tmp.y += a.lift
      this.tmp.project(camera)
      shardStore.pushPosition(((this.tmp.x + 1) / 2) * width, ((1 - this.tmp.y) / 2) * height, true)
    } else {
      shardStore.pushPosition(0, 0, false)
    }
  }
}
