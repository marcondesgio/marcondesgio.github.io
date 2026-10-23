import { forwardRef } from 'react'
import { useI18n } from '../i18n/I18nProvider'
import { PHOTO } from '../data/contact'

/** The eu_e_tutu photo: responsive WebP with a JPG fallback (spec §8). */
export const Photo = forwardRef<HTMLImageElement, { eager?: boolean }>(function Photo({ eager }, ref) {
  const { t } = useI18n()
  const sizes = '(max-width: 640px) 92vw, 40vw'
  return (
    <picture>
      <source type="image/webp" srcSet={PHOTO.widths.map((w) => `${PHOTO.src(w, 'webp')} ${w}w`).join(', ')} sizes={sizes} />
      <img
        ref={ref}
        src={PHOTO.src(768, 'jpg')}
        srcSet={PHOTO.widths.map((w) => `${PHOTO.src(w, 'jpg')} ${w}w`).join(', ')}
        sizes={sizes}
        width={1024}
        height={1536}
        alt={t.about.photoAlt}
        loading={eager ? 'eager' : 'lazy'}
        decoding="async"
      />
    </picture>
  )
})
