import type { Lang } from '../i18n/I18nProvider'

export type Project =
  | { id: string; name: string; url: string; description: Record<Lang, string>; comingSoon?: false }
  | { id: string; comingSoon: true }

// Shard order = array order (shard_01 … shard_05 in public/models/cup_fracture.glb).
export const projects: Project[] = [
  {
    id: 'ceramic-relax',
    name: 'Ceramic Relax',
    url: 'https://github.com/marcondesgio/ceramic-relax',
    description: {
      pt: 'Jogo 3D relaxante de cerâmica no navegador: modele no torno, pinte e leve ao forno.',
      en: 'A relaxing 3D pottery game in the browser: shape it on the wheel, paint it and fire it in the kiln.',
    },
  },
  {
    id: 'pode-comer',
    name: 'Pode Comer?',
    url: 'https://github.com/marcondesgio/podecomer-app',
    description: {
      pt: 'App em Flutter que lê o código de barras dos alimentos e alerta sobre alergênicos para cada pessoa da família.',
      en: 'A Flutter app that scans food barcodes and flags allergens for each member of the family.',
    },
  },
  {
    id: 'duni-app',
    name: 'Duni App',
    url: 'https://github.com/marcondesgio/duni_app',
    description: {
      pt: 'Rede social corporativa baseada em interesses, hobbies e atividades em comum: grupos, desafios e interações que aproximam colegas para além do trabalho.',
      en: 'A corporate social platform built around shared interests, hobbies and activities: groups, challenges and interactions that bring coworkers closer beyond work.',
    },
  },
  { id: 'soon-1', comingSoon: true },
  { id: 'soon-2', comingSoon: true },
]
