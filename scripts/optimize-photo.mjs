// Final photo (spec §8): resize + compress docs/eu_e_tutu.png into public/images/ as WebP (with JPG
// fallback) in responsive widths. Content is never edited — only scaled and re-encoded.
// Run: node scripts/optimize-photo.mjs
import { mkdir, stat } from 'node:fs/promises'
import sharp from 'sharp'

const SRC = 'docs/eu_e_tutu.png'
const OUT = 'public/images'
const WIDTHS = [480, 768, 1024]
const BUDGET = 250 * 1024 // spec: largest version < 250 KB

await mkdir(OUT, { recursive: true })
for (const w of WIDTHS) {
  const base = sharp(SRC).resize({ width: w })
  for (const [ext, encode] of [
    ['webp', (s) => s.webp({ quality: 80, effort: 6 })],
    ['jpg', (s) => s.jpeg({ quality: 80, mozjpeg: true })],
  ]) {
    const file = `${OUT}/eu_e_tutu-${w}.${ext}`
    await encode(base.clone()).toFile(file)
    const { size } = await stat(file)
    console.log(`${file}  ${(size / 1024).toFixed(0)} KB${size > BUDGET ? '  (over budget!)' : ''}`)
  }
}
