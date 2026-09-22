import { test, expect } from '@playwright/test'

/**
 * Flusso di autenticazione (Fase 7, E2E):
 * questi test girano contro il backend Django REALE (non mock), cosi'
 * verificano il flusso JWT-cookie + CSRF dall'estremita' all'altra.
 *
 * Pre-requisito: un utente con email/password corrispondenti deve esistere
 * nel database dell'ambiente di test (creato via fixture o createsuperuser).
 */

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@test.local'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'test-password-sicura-123'
const CLIENTE_EMAIL = process.env.E2E_CLIENTE_EMAIL ?? 'cliente@test.local'
const CLIENTE_PASSWORD = process.env.E2E_CLIENTE_PASSWORD ?? 'test-password-sicura-123'

test.describe('Login e redirect', () => {
  test('visitatore non autenticato viene reindirizzato al login', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByRole('heading', { name: /gestionale salone/i })).toBeVisible()
  })

  test('credenziali sbagliate mostrano errore', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill('sbagliata@example.com')
    await page.getByLabel(/password/i).fill('password-sbagliata')
    await page.getByRole('button', { name: /accedi/i }).click()
    await expect(page.getByText(/email o password non corrette/i)).toBeVisible()
  })

  test('login admin porta alla dashboard con sezione Guadagni', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
    await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
    await page.getByRole('button', { name: /accedi/i }).click()

    await expect(page).toHaveURL('/')
    await expect(page.getByText(/prenotazioni oggi/i)).toBeVisible()
    await expect(page.getByText(/guadagni/i)).toBeVisible()
  })

  test('login cliente mostra dashboard cliente (prossimo appuntamento)', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(CLIENTE_EMAIL)
    await page.getByLabel(/password/i).fill(CLIENTE_PASSWORD)
    await page.getByRole('button', { name: /accedi/i }).click()

    await expect(page).toHaveURL('/')
    // Il cliente vede il suo prossimo appuntamento (o il link Prenota),
    // NON la griglia KPI staff.
    await expect(page.getByText(/prenotazioni oggi/i)).not.toBeVisible()
  })

  test('logout cancella i cookie e reindirizza al login', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
    await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
    await page.getByRole('button', { name: /accedi/i }).click()
    await expect(page).toHaveURL('/')
    const esciBtn = page.getByRole('button', { name: /esci/i })
    await expect(esciBtn).toBeVisible()
    await esciBtn.click()
    await expect(page).toHaveURL(/\/login/)

    // Tentativo di tornare alla dashboard: deve reindirizzare di nuovo al login
    await page.goto('/')
    await expect(page).toHaveURL(/\/login/)
  })

  test('profilo mostra la gestione sessioni e il dispositivo attuale', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
    await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
    await page.getByRole('button', { name: /accedi/i }).click()
    await expect(page).toHaveURL('/')

    await page.goto('/profilo')
    await expect(page.getByRole('heading', { name: /il mio profilo/i })).toBeVisible()
    await expect(page.getByRole('heading', { name: /dispositivi e sessioni attive/i })).toBeVisible()
    await expect(page.getByText(/dispositivo attuale/i)).toBeVisible()
  })
})
