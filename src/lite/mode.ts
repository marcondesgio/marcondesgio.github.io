/**
 * Full 3D story or the simplified page (spec §10)? The simplified page is used for "reduce motion",
 * when WebGL is missing, or on a GPU/device that would not hold a decent frame rate. `?lite` / `?full`
 * force either one (handy for testing). Kept dependency-free: this runs before any 3D code loads.
 */
export type Mode = 'full' | 'lite'

const SOFTWARE_GPU = /swiftshader|llvmpipe|softpipe|software|basic render|mali-4|adreno \(tm\) [23]\d\d|powervr sgx/i

function gpuIsWeak(): boolean {
  try {
    const canvas = document.createElement('canvas')
    const gl = (canvas.getContext('webgl2') ?? canvas.getContext('webgl')) as WebGLRenderingContext | null
    if (!gl) return true // no WebGL at all
    const info = gl.getExtension('WEBGL_debug_renderer_info')
    const renderer = info ? String(gl.getParameter(info.UNMASKED_RENDERER_WEBGL)) : ''
    gl.getExtension('WEBGL_lose_context')?.loseContext()
    return SOFTWARE_GPU.test(renderer)
  } catch {
    return true
  }
}

export function chooseMode(): Mode {
  const params = new URLSearchParams(window.location.search)
  if (params.has('lite')) return 'lite'
  if (params.has('full')) return 'full'
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return 'lite'
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory
  if (memory !== undefined && memory < 2) return 'lite'
  return gpuIsWeak() ? 'lite' : 'full'
}
