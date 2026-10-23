import { useEffect, useRef } from 'react'
import { useI18n } from '../i18n/I18nProvider'
import { projects } from '../data/projects'
import { isTouchDevice, shardStore, useShardState } from './shardStore'
import './shards.css'

const pad = (n: number) => String(n).padStart(2, '0')

/**
 * Floating project label (design system "Rótulo flutuante"): sits above the active shard with a guide
 * line pointing down to it. Its position is written straight to the DOM every frame by ShardFx.
 */
export function ShardLabel() {
  const { t, lang } = useI18n()
  const { active, source, interactive } = useShardState()
  const wrap = useRef<HTMLDivElement>(null)

  useEffect(() => {
    shardStore.onPosition((x, y, visible) => {
      const el = wrap.current
      if (!el) return
      el.style.visibility = visible ? 'visible' : 'hidden'
      if (!visible) return
      // keep the card on screen: clamp x, flip below the shard when there is no room above
      const w = el.offsetWidth
      const cx = Math.min(Math.max(x, w / 2 + 16), window.innerWidth - w / 2 - 16)
      const below = y - el.offsetHeight - 70 < 70
      el.dataset.side = below ? 'below' : 'above'
      el.style.transform = `translate(${cx - w / 2}px, ${below ? y + 24 : y - el.offsetHeight - 24}px)`
      el.style.setProperty('--guide-x', `${x - (cx - w / 2)}px`)
    })
    return () => shardStore.onPosition(null)
  }, [])

  const pr = active === null ? null : projects[active]
  const soon = !!pr && 'comingSoon' in pr && !!pr.comingSoon
  const show = interactive && pr !== null

  return (
    <>
      <div ref={wrap} className="shard-label-wrap" aria-hidden="true">
        {show && (
          <div key={active} className="shard-label" data-soon={soon}>
            <p className="label shard-label-kicker">
              {t.shard} {pad(active! + 1)} / {pad(projects.length)}
            </p>
            {soon ? (
              <>
                <p className="shard-label-title">
                  <em>{t.comingSoon}</em>
                </p>
                <p className="shard-label-body">{t.comingSoonBody}</p>
                <p className="label shard-label-link shard-label-nolink">
                  <span className="clock" aria-hidden="true" />
                  {t.noLink}
                </p>
              </>
            ) : (
              <>
                <p className="shard-label-title">{'name' in pr! ? pr.name : ''}</p>
                <p className="shard-label-body">{'description' in pr! ? pr.description[lang] : ''}</p>
                <p className="label shard-label-link">{source === 'touch' ? `${t.tapAgain} ↗` : t.openOnGithub}</p>
              </>
            )}
          </div>
        )}
      </div>
      {interactive && active === null && (
        <p className="shards-hint label">{isTouchDevice ? t.shardsHintTouch : t.shardsHint}</p>
      )}
    </>
  )
}
