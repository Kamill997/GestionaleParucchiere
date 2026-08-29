/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      // 'injectManifest': usa il service worker custom in src/sw.ts invece
      // di generarne uno da zero. Workbox inietta il precache manifest nel
      // file, poi il handler 'push' scritto in sw.ts gestisce le notifiche
      // native (docs/04-pwa-checklist.md, "Notifiche push").
      // Con 'generateSW' (precedente configurazione) le notifiche arrivavano
      // al browser ma non venivano mostrate: mancava questo handler.
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      registerType: 'prompt',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Gestionale Salone di Parrucchiere',
        short_name: 'Gestionale',
        description: 'Prenotazioni, catalogo servizi e gestione clienti per il salone.',
        lang: 'it',
        start_url: '/',
        display: 'standalone',
        background_color: '#faf7f5',
        theme_color: '#5c2a4d',
        orientation: 'any',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/icons/icon-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    // Esclude i file Playwright E2E: girano con `npm run test:e2e`,
    // non con vitest. Senza questa esclusione vitest prova a raccogliere
    // anche i file in e2e/ e crasha perche' la API di Playwright
    // (test.describe) non e' compatibile con quella di Vitest.
    exclude: ['**/node_modules/**', '**/dist/**', 'e2e/**'],
    // Esecuzione sequenziale dei file di test: con l'esecuzione concorrente
    // di default si e' osservata flakiness intermittente (stessa suite,
    // a volte verde a volte rossa) su una macchina sotto carico. La suite
    // e' ancora piccola: la determinismo vale piu' della velocita' qui.
    fileParallelism: false,
    testTimeout: 8000,
    env: {
      // Stesso fuso del backend (config/settings.py, TIME_ZONE) e del
      // pubblico reale dell'app: senza, i test sugli orari dipendono dal
      // fuso della macchina che li esegue invece che da un valore fisso
      // (bug reale osservato: un orario mostrato 2h prima del previsto).
      TZ: 'Europe/Rome',
    },
  },
})
