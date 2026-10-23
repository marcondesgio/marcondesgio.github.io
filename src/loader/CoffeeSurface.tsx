import { useEffect, useRef } from 'react'
import { onDrop } from './drops'

/**
 * The coffee seen from above: a tiny raw-WebGL fragment shader (no three.js, so it ships in the initial
 * bundle) with a dark radial body, the lamp's warm reflection and slow ripples. Falls back to a CSS
 * gradient (the canvas background) if WebGL is unavailable. Clicking the coffee drops a drop into it
 * (drops.ts): rings spread from that point and the whole surface sloshes away from it.
 */
const FRAG = `
precision mediump float;
uniform vec2 uRes;
uniform float uTime;
uniform float uMotion;
uniform vec3 uDrops[4]; // x, y, age in seconds (age < 0 = unused)
uniform vec3 uSlosh; // direction xy, age

void main() {
  vec2 uv = (gl_FragCoord.xy / uRes) * 2.0 - 1.0;
  float r = length(uv);
  if (r > 1.0) { gl_FragColor = vec4(0.0); return; }

  // gentle concentric ripples + a slow drift, used as a fake normal
  float t = uTime * uMotion;
  float w = sin(r * 26.0 - t * 1.4) * 0.5 + sin((uv.x + uv.y) * 9.0 + t * 0.7) * 0.25;
  vec2 n = normalize(uv + 1e-4) * w * 0.035 * (1.0 - r);

  // the cup was nudged: the liquid swings away from the drop and back, a few damped sways
  float sa = uSlosh.z;
  float sway = sa >= 0.0 ? sin(sa * 9.0) * exp(-sa * 2.4) : 0.0;
  vec2 sloshOff = uSlosh.xy * sway * 0.09;
  n += sloshOff * (0.6 + r);

  // drop rings: a travelling, fading wave per drop, plus a short crown right where it landed
  float ring = 0.0;
  for (int i = 0; i < 4; i++) {
    float age = uDrops[i].z;
    if (age < 0.0 || age > 3.0) continue;
    vec2 dv = uv - uDrops[i].xy;
    float d = length(dv);
    float front = age * 0.85;
    float env = exp(-age * 1.5) * exp(-pow((d - front) * 5.0, 2.0));
    float wave = sin((d - front) * 46.0) * env;
    wave += exp(-d * d * 260.0) * exp(-age * 7.0) * 1.4; // crown
    n += normalize(dv + 1e-4) * wave * 0.07;
    ring += wave;
  }

  // lighter, warmer coffee so it reads against the night (feedback round 2)
  vec3 deep = vec3(0.22, 0.13, 0.085);
  vec3 mid = vec3(0.45, 0.28, 0.18);
  vec3 col = mix(mid, deep, smoothstep(0.0, 1.0, r));

  // warm lamp reflection, top-left, wobbling with the ripples
  vec2 lp = uv - vec2(-0.42, 0.5) + n * 3.0;
  float lamp = exp(-dot(lp * vec2(1.6, 2.6), lp * vec2(1.6, 2.6)) * 3.0);
  col += vec3(0.62, 0.42, 0.40) * lamp * 0.6;

  // faint cool glint from the monitor, bottom-right
  vec2 mp = uv - vec2(0.45, -0.38) + n * 2.0;
  col += vec3(0.25, 0.35, 0.45) * exp(-dot(mp, mp) * 14.0) * 0.18;

  // meniscus: darker rim where the coffee meets the ceramic
  // ripples catch the light: crests lighter, troughs darker
  col += vec3(0.30, 0.22, 0.20) * clamp(ring, -0.6, 1.0) * 0.55;
  // the swaying liquid climbs the wall on one side, catching a lighter rim there
  col += vec3(0.20, 0.13, 0.10) * smoothstep(0.75, 1.0, r) * max(0.0, dot(normalize(uv + 1e-4), -uSlosh.xy) * sway) * 1.5;

  col *= mix(1.0, 0.65, smoothstep(0.86, 1.0, r));
  float a = 1.0 - smoothstep(0.985, 1.0, r);
  gl_FragColor = vec4(col * a, a);
}
`

const VERT = `attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }`

export function CoffeeSurface({ reducedMotion }: { reducedMotion: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    const gl = canvas?.getContext('webgl', { premultipliedAlpha: true, antialias: true })
    if (!canvas || !gl) return

    const compile = (type: number, src: string) => {
      const s = gl.createShader(type)!
      gl.shaderSource(s, src)
      gl.compileShader(s)
      return s
    }
    const prog = gl.createProgram()!
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT))
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG))
    gl.linkProgram(prog)
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return
    gl.useProgram(prog)

    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(prog, 'p')
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)
    const uRes = gl.getUniformLocation(prog, 'uRes')
    const uTime = gl.getUniformLocation(prog, 'uTime')
    gl.uniform1f(gl.getUniformLocation(prog, 'uMotion'), reducedMotion ? 0 : 1)
    const uDrops = gl.getUniformLocation(prog, 'uDrops')
    const uSlosh = gl.getUniformLocation(prog, 'uSlosh')
    const drops: { x: number; y: number; at: number }[] = []
    let slosh = { x: 0, y: 0, at: -1 }
    const offDrop = onDrop((d) => {
      drops.push(d)
      if (drops.length > 4) drops.shift()
      const len = Math.hypot(d.x, d.y) || 1
      // away from where the drop hit (a centred drop still nudges the cup a little forward)
      slosh = len < 0.15 ? { x: 0, y: -1, at: d.at } : { x: -d.x / len, y: -d.y / len, at: d.at }
    })
    const dropData = new Float32Array(12)

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const size = Math.round(canvas.clientWidth * dpr)
      canvas.width = canvas.height = size
      gl.viewport(0, 0, size, size)
      gl.uniform2f(uRes, size, size)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    let raf = 0
    const start = performance.now()
    const frame = (now: number) => {
      gl.uniform1f(uTime, (now - start) / 1000)
      for (let i = 0; i < 4; i++) {
        const d = drops[i]
        dropData.set(d ? [d.x, d.y, (now - d.at) / 1000] : [0, 0, -1], i * 3)
      }
      gl.uniform3fv(uDrops, dropData)
      gl.uniform3f(uSlosh, slosh.x, slosh.y, slosh.at < 0 ? -1 : (now - slosh.at) / 1000)
      gl.drawArrays(gl.TRIANGLES, 0, 3)
      if (!reducedMotion) raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    // no loseContext() here: the effect re-runs on the same canvas (StrictMode, motion toggles) and
    // getContext() would hand back the lost context
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      offDrop()
    }
  }, [reducedMotion])

  return <canvas ref={ref} className="coffee-surface" aria-hidden="true" />
}
