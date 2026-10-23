import { Component, Suspense, lazy, useCallback, useState, type ReactNode } from 'react'
import { I18nProvider, useI18n } from './i18n/I18nProvider'
import { Header, ProgressDots } from './ui/Overlay'
import { DebugPanel } from './ui/DebugPanel'
import { debugEnabled } from './scene/debug'
import { LoaderScene } from './loader/LoaderScene'
import { ProjectList } from './shards/ProjectList'
import { ShardLabel } from './shards/ShardLabel'
import { About } from './about/About'
import { PhotoDissolve } from './about/PhotoDissolve'
import { LitePage } from './lite/LitePage'
import { chooseMode, type Mode } from './lite/mode'

// three.js, R3F, GSAP, Lenis and the GLBs: loaded after scene 0 is on screen
const Heavy = lazy(() => import('./scene/Heavy'))

/** If anything in the 3D story throws (lost WebGL context, failed GLB…), fall back to the simplified page. */
class StoryBoundary extends Component<{ onFail: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  componentDidCatch(error: unknown) {
    console.error('3D story failed, switching to the simplified page', error)
    this.props.onFail()
  }
  render() {
    return this.state.failed ? null : this.props.children
  }
}

function StorySite({ onFail }: { onFail: () => void }) {
  const { t, lang } = useI18n()
  const [released, setReleased] = useState(false)
  const onRelease = useCallback(() => setReleased(true), [])
  return (
    <>
      <StoryBoundary onFail={onFail}>
        <Suspense fallback={null}>
          <Heavy locked={!released} />
        </Suspense>
      </StoryBoundary>
      <LoaderScene released={released} onRelease={onRelease} />
      <Header />
      {released && <ProgressDots />}
      <ShardLabel />
      <PhotoDissolve />
      <main id="conteudo">
        <h1 className="sr-only">
          {t.documentTitle} — {t.about.titleA} {t.about.titleB}
        </h1>
        <ProjectList />
        <About key={lang} />
      </main>
      {debugEnabled && <DebugPanel />}
    </>
  )
}

function Site() {
  const [mode, setMode] = useState<Mode>(chooseMode)
  const toLite = useCallback(() => {
    // the story may have stopped scrolling (loader): undo what Lenis put on <html>
    document.documentElement.classList.remove('lenis', 'lenis-stopped', 'lenis-smooth')
    setMode('lite')
  }, [])
  if (mode === 'lite') {
    return (
      <>
        <Header nav />
        <LitePage />
      </>
    )
  }
  return <StorySite onFail={toLite} />
}

export function App() {
  return (
    <I18nProvider>
      <Site />
    </I18nProvider>
  )
}
