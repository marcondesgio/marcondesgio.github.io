import { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { NeutralToneMapping } from 'three'
import { Story } from './Story'
import { CameraRig } from './CameraRig'
import { Lights } from './Lights'
import { Effects } from './Effects'
import { shardStore } from '../shards/shardStore'

const isMobile = typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches

export function Experience() {
  return (
    <div className="canvas-layer">
      <Canvas
        dpr={[1, isMobile ? 1.5 : 2]}
        camera={{ fov: 45, near: 0.02, far: 30 }}
        gl={{ antialias: true, toneMapping: NeutralToneMapping, toneMappingExposure: 0.85 }}
        onPointerMissed={() => {
          // tapping empty space dismisses a shard label opened by touch
          if (shardStore.get().source === 'touch') shardStore.set({ active: null, source: null })
        }}
        aria-hidden="true"
      >
        <Lights />
        <Suspense fallback={null}>
          <Story />
        </Suspense>
        <CameraRig />
        <Effects mobile={isMobile} />
      </Canvas>
    </div>
  )
}
