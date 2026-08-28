import { defineConfig, devices } from '@playwright/test'

/**
 * Test E2E (Fase 7) — Playwright contro il frontend Vite in dev mode e il
 * backend Django. Il backend deve girare su http://localhost:8000 (vedi
 * docker-compose.yml o avvio locale in README.md). Vitest copre test
 * unitari/componente; Playwright copre i flussi critici end-to-end reali.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  // Ritenta automaticamente i test falliti in CI (rete piu' lenta, timing
  // diversi): 2 retry in CI, 0 in locale per feedback immediato.
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'html',
  use: {
    // URL del frontend Vite, avviato da webServer qui sotto.
    baseURL: 'http://localhost:5173',
    // Cattura screenshot + trace solo sui test falliti: evita di scaricare
    // centinaia di MB ad ogni run di CI verde.
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // Avvia Vite prima di eseguire i test: i test E2E girano contro il
  // frontend reale compilato sul momento, non un mock. Il backend Django
  // deve essere gia' attivo (via docker compose o avvio locale).
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
