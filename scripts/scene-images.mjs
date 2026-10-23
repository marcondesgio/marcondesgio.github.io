// Static images of the desk scene (from the Blender preview render) for the no-3D version and Open Graph.
// Run: node scripts/scene-images.mjs   (after blender/scripts/build_desk.py has rendered the previews)
import { mkdir, stat } from 'node:fs/promises'
import sharp from 'sharp'

const SRC = 'blender/previews/scene1_desk.png'
const OUT = 'public/images'
await mkdir(OUT, { recursive: true })

const jobs = [
  // lite version hero: 16:9, responsive widths
  ...[800, 1600].map((w) => [`${OUT}/scene-${w}.webp`, (s) => s.resize({ width: w }).webp({ quality: 78 })]),
  [`${OUT}/scene-1600.jpg`, (s) => s.resize({ width: 1600 }).jpeg({ quality: 80, mozjpeg: true })],
  // Open Graph / Twitter card: 1200×630, cropped around the desk
  ['public/og.jpg', (s) => s.resize({ width: 1200, height: 630, fit: 'cover', position: 'centre' }).jpeg({ quality: 82, mozjpeg: true })],
]
for (const [file, encode] of jobs) {
  await encode(sharp(SRC)).toFile(file)
  console.log(`${file}  ${((await stat(file)).size / 1024).toFixed(0)} KB`)
}
