import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Public URL for canonical / Open Graph / JSON-LD in index.html. Override with VITE_SITE_URL (e.g. in the
// Vercel project settings). TODO: confirm once the Vercel project exists.
const DEFAULT_SITE_URL = 'https://marcondesgio.github.io'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', 'VITE_')
  const siteUrl = (env.VITE_SITE_URL || DEFAULT_SITE_URL).replace(/\/$/, '')
  return {
    plugins: [
      react(),
      {
        name: 'site-url',
        transformIndexHtml: (html) => html.replaceAll('%VITE_SITE_URL%', siteUrl),
      },
    ],
    server: { port: 5173 },
  }
})
