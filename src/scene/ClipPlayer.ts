import { AnimationAction, AnimationClip, AnimationMixer, Object3D } from 'three'

/**
 * Plays baked Blender clips with the time set by hand (spec §3: action.time = f(p), never play()).
 * Exactly one clip has weight 1 at a time; the others sit at weight 0, so nodes the active clip does
 * not touch fall back to their rest transform.
 */
export class ClipPlayer {
  readonly mixer: AnimationMixer
  private actions = new Map<string, AnimationAction>()

  constructor(root: Object3D, clips: AnimationClip[]) {
    this.mixer = new AnimationMixer(root)
    for (const clip of clips) {
      const action = this.mixer.clipAction(clip)
      action.play()
      action.paused = true
      action.setEffectiveWeight(0)
      this.actions.set(clip.name, action)
    }
  }

  get names() {
    return [...this.actions.keys()]
  }

  duration(name: string) {
    return this.actions.get(name)?.getClip().duration ?? 0
  }

  /** Show `name` at `time` seconds (clamped to the clip). */
  show(name: string, time: number) {
    const target = this.actions.get(name)
    if (!target) return
    for (const [n, action] of this.actions) {
      action.setEffectiveWeight(n === name ? 1 : 0)
    }
    target.time = Math.min(Math.max(time, 0), target.getClip().duration)
    this.mixer.update(0)
  }

  /** Show `name` at a normalized position 0..1 of the clip. */
  showAt(name: string, t: number) {
    this.show(name, t * this.duration(name))
  }

  /** Ambient loop driven by wall-clock time (allowed by the spec for idle loops). */
  loop(name: string, elapsed: number) {
    const d = this.duration(name)
    if (d > 0) this.show(name, elapsed % d)
  }
}
