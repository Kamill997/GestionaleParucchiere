import { test, expect } from '@playwright/test'

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@test.local'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'test-password-sicura-123'

async function loginAdmin(page: Parameters<typeof test>[1]) {
  await page.goto('/login')
  await page.getByLabel(/email/i).fill(ADMIN_EMAIL)
  await page.getByLabel(/password/i).fill(ADMIN_PASSWORD)
  await page.getByRole('button', { name: /accedi/i }).click()
  await expect(page).toHaveURL('/')
}

test.describe('Notification bell', () => {
  test('il campanello e visibile nella barra header dopo il login', async ({ page }) => {
    await loginAdmin(page)
    await expect(page.getByRole('button', { name: /notifiche/i })).toBeVisible()
  })

  test('aprire il campanello mostra la lista notifiche o il messaggio vuoto', async ({ page }) => {
    await loginAdmin(page)
    await page.getByRole('button', { name: /notifiche/i }).click()
    // Il pannello si apre mostrando l'intestazione e la lista (o il messaggio di stato)
    await expect(
      page.getByText(/nessuna notifica/i).or(page.locator('.max-h-96 button'))
    ).toBeVisible()
  })
})

test.describe('Impostazioni', () => {
  test('la pagina impostazioni e visibile per un amministratore', async ({ page }) => {
    await loginAdmin(page)
    await page.goto('/impostazioni')
    await expect(page.getByRole('heading', { name: /impostazioni/i })).toBeVisible()
    // Tutte le chiavi note devono essere visibili
    await expect(page.getByText('soglia_no_show')).toBeVisible()
    await expect(page.getByText('buffer_minuti_prenotazioni')).toBeVisible()
  })

  test('cliccare modifica su un valore mostra un input inline', async ({ page }) => {
    await loginAdmin(page)
    await page.goto('/impostazioni')
    // Hover sulla riga per far apparire il bottone matita
    const rigaSoglia = page.locator('tr').filter({ hasText: 'soglia_no_show' })
    await rigaSoglia.hover()
    await page
      .getByRole('button', { name: /modifica soglia_no_show/i })
      .click()
    await expect(page.locator('input[type="text"]').first()).toBeVisible()
    // Esc annulla
    await page.keyboard.press('Escape')
    await expect(page.locator('input[type="text"]')).not.toBeVisible()
  })
})
