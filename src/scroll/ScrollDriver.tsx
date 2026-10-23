import { useEffect, useRef } from 'react'
import Lenis from 'lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { progress, scrollToStory } from './progress'

gsap.registerPlugin(ScrollTrigger)

/**
 * Lenis smooth scroll + one ScrollTrigger over a tall track; the trigger's progress is p.
 * `scrub` adds a little lag so the story eases into place; scrolling back simply runs p backwards.
 * While `locked` (loading scene), scrolling is stopped.
 */
export function ScrollDriver({ locked }: { locked: boolean }) {
  const trackRef = useRef<HTMLDivElement>(null)
  const lenisRef = useRef<Lenis | null>(null)

  useEffect(() => {
    const lenis = new Lenis({ lerp: 0.09, smoothWheel: true, syncTouch: false })
    lenisRef.current = lenis
    lenis.on('scroll', ScrollTrigger.update)
    const tick = (time: number) => lenis.raf(time * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)

    const proxy = { p: 0 }
    const tween = gsap.to(proxy, {
      p: 1,
      ease: 'none',
      onUpdate: () => progress.set(scrollToStory(proxy.p)),
      scrollTrigger: { trigger: trackRef.current, start: 'top top', end: 'bottom bottom', scrub: 0.6 },
    })

    return () => {
      tween.scrollTrigger?.kill()
      tween.kill()
      gsap.ticker.remove(tick)
      lenis.destroy()
    }
  }, [])

  useEffect(() => {
    const lenis = lenisRef.current
    if (!lenis) return
    if (locked) lenis.stop()
    else lenis.start()
  }, [locked])

  // aria-hidden: purely a scroll length; content lives in the overlays and the accessible lists
  return <div ref={trackRef} className="scroll-track" aria-hidden="true" />
}
