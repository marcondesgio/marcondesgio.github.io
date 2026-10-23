import { Bloom, EffectComposer, Noise, ToneMapping, Vignette } from '@react-three/postprocessing'

// postprocessing's ToneMappingMode.NEUTRAL (same curve the renderer used before the composer took over)
const NEUTRAL = 8

/**
 * Post-processing (spec §2): soft bloom on the lamp, monitor, fairy lights and shard halos, a gentle
 * vignette and very light film grain. Depth of field was removed after feedback (it hid the details of
 * the room). Phones skip MSAA — spec §10.
 */
export function Effects({ mobile }: { mobile: boolean }) {
  return (
    <EffectComposer multisampling={mobile ? 0 : 4}>
      <Bloom mipmapBlur luminanceThreshold={0.9} luminanceSmoothing={0.15} intensity={0.5} radius={0.65} />
      <Vignette offset={0.38} darkness={0.22} />
      <Noise premultiply opacity={0.18} />
      <ToneMapping mode={NEUTRAL} />
    </EffectComposer>
  )
}
