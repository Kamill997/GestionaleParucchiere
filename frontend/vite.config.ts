/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
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
