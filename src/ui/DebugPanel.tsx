import { useState } from 'react'
import { sceneAt, storyToScroll, useProgressValue } from '../scroll/progress'
import { debug, useDebug, type DebugModel } from '../scene/debug'
import { runReversalTest } from './reversalTest'

const MODELS: { id: DebugModel; label: string }[] = [
  { id: 'gio', label: 'Gio' },
  { id: 'tutu', label: 'Tutu' },
  { id: 'cup', label: 'Caneca' },
]

/** ?debug — shows p, loops any baked clip, and runs the forward/backward reversal check. */
export function DebugPanel() {
  const p = useProgressValue(0.001)
  const { clips, overrides } = useDebug()
  const [reversal, setReversal] = useState('')

  const testReversal = async () => {
    setReversal('testing…')
    try {
      const r = await runReversalTest()
      setReversal(r.diffs.length ? `${r.diffs.length} diff(s): ${r.diffs.join('; ')}` : `ok — ${r.checked} points match`)
    } catch (e) {
      setReversal(String(e instanceof Error ? e.message : e))
    }
  }

  return (
    <aside className="debug-panel" aria-label="Debug">
      <div>
        p = {p.toFixed(3)} · {sceneAt(p).id}
      </div>
      <label>
        jump to p
        <input
          type="range"
          min={0}
          max={1}
          step={0.001}
          value={p}
          onChange={(e) => {
            // the story track, not the whole page (the About section follows it)
            const track = document.querySelector<HTMLElement>('.scroll-track')
            if (!track) return
            window.scrollTo({ top: storyToScroll(Number(e.target.value)) * (track.offsetHeight - window.innerHeight) })
          }}
        />
      </label>
      {MODELS.map((m) => (
        <label key={m.id}>
          {m.label}
          <select
            value={overrides[m.id] ?? ''}
            onChange={(e) => debug.setOverride(m.id, e.target.value || undefined)}
          >
            <option value="">timeline (scroll)</option>
            {(clips[m.id] ?? []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      ))}
      <button type="button" onClick={testReversal}>
        reversal test
      </button>
      {reversal && <output>{reversal}</output>}
    </aside>
  )
}
