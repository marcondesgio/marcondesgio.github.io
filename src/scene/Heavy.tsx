import { Experience } from './Experience'
import { ScrollDriver } from '../scroll/ScrollDriver'

/**
 * Everything heavy (three.js, R3F, drei, GSAP, Lenis, the GLBs) lives behind this lazy chunk, so scene 0
 * (the loader) paints from the small initial bundle while this downloads.
 */
export default function Heavy({ locked }: { locked: boolean }) {
  return (
    <>
      <Experience />
      <ScrollDriver locked={locked} />
    </>
  )
}
