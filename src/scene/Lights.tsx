import { useEffect, useMemo } from 'react'
import { AdditiveBlending, CanvasTexture, Object3D } from 'three'
import { b2t } from './coords'

/**
 * Real-time lights (spec §6): the environment's light and AO are baked into its textures and drawn unlit,
 * so only the two practical lights stay live — the desk lamp and the monitor — to light the moving
 * characters and the mug. The hemisphere is just the dim night ambient for those same characters
 * (it does not touch the baked, unlit meshes).
 */
export function Lights() {
  const lampTarget = useMemo(() => {
    const o = new Object3D()
    o.position.copy(b2t(0.3, 0.3, 0.75))
    return o
  }, [])
  useEffect(() => () => void lampTarget.removeFromParent(), [lampTarget])
  const spillTarget = useMemo(() => {
    const o = new Object3D()
    o.position.copy(b2t(0.5, -0.34, 0))
    return o
  }, [])
  useEffect(() => () => void spillTarget.removeFromParent(), [spillTarget])
  const poolMap = useMemo(() => {
    const c = document.createElement('canvas')
    c.width = c.height = 128
    const g = c.getContext('2d')!
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64)
    grad.addColorStop(0, 'rgba(255,255,255,1)')
    grad.addColorStop(0.5, 'rgba(255,255,255,0.4)')
    grad.addColorStop(1, 'rgba(255,255,255,0)')
    g.fillStyle = grad
    g.fillRect(0, 0, 128, 128)
    return new CanvasTexture(c)
  }, [])

  return (
    <>
      <color attach="background" args={['#241D3B']} />
      <hemisphereLight args={['#C7B8F2', '#5A4038', 1.35]} />
      {/* desk lamp: warm key */}
      <primitive object={lampTarget} />
      <spotLight
        position={b2t(0.62, 0.34, 1.13)}
        target={lampTarget}
        color="#FFD2A1"
        intensity={0.3}
        distance={4}
        angle={1.05}
        penumbra={0.7}
        decay={2}
      />
      <pointLight position={b2t(0.6, 0.29, 1.1)} color="#FFC9A0" intensity={0.11} distance={1.5} decay={2} />
      {/* floor where the mug lands: a soft overhead key on the spill and shards (scenes 3–5) */}
      <primitive object={spillTarget} />
      <spotLight
        position={b2t(0.75, -0.9, 1.7)}
        target={spillTarget}
        color="#FFE1EC"
        intensity={4.5}
        distance={4}
        angle={0.55}
        penumbra={1}
        decay={2}
      />
      {/* …and the matching pool of light on the floor, whose lightmap ignores real-time lights */}
      <mesh position={b2t(0.5, -0.34, 0.004)} rotation-x={-Math.PI / 2} renderOrder={1}>
        <planeGeometry args={[1.3, 1.3]} />
        <meshBasicMaterial map={poolMap} color="#FFD7C2" transparent opacity={0.32} depthWrite={false} blending={AdditiveBlending} toneMapped={false} />
      </mesh>
      {/* monitor: cool back light */}
      <pointLight position={b2t(-0.22, 0.4, 1.05)} color="#A9D8F5" intensity={1.1} distance={3} decay={2} />
    </>
  )
}
