import { expect, test } from '@playwright/test'

test.describe('Standard web e pagine pubbliche', () => {
  test('rotta inesistente mostra la pagina 404 personalizzata', async ({ page }) => {
    await page.goto('/rotta-inesistente-xyz-123')
    await expect(page.getByText('404')).toBeVisible()
    await expect(page.getByText('Pagina non trovata')).toBeVisible()
    await expect(page.getByRole('link', { name: /torna alla dashboard/i })).toBeVisible()
  })

  test('link alla Privacy Policy dal login', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /privacy policy/i }).click()
    await expect(page).toHaveURL('/privacy')
    await expect(
      page.getByRole('heading', { name: /informativa sulla privacy/i }),
    ).toBeVisible()
  })

  test('link ai Termini di Servizio dal login', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /termini/i }).click()
    await expect(page).toHaveURL('/termini')
    await expect(
      page.getByRole('heading', { name: /termini e condizioni di servizio/i }),
    ).toBeVisible()
  })

  test('link a Password dimenticata dal login', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /password dimenticata\?/i }).click()
    await expect(page).toHaveURL('/password-dimenticata')
    await expect(
      page.getByRole('heading', { name: /hai dimenticato la password\?/i }),
    ).toBeVisible()
    await expect(page.getByLabel(/la tua email/i)).toBeVisible()
  })

  test('link a Registrati dal login e pagina di registrazione', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /registrati/i }).click()
    await expect(page).toHaveURL('/register')
    await expect(page.getByRole('heading', { name: /crea il tuo account/i })).toBeVisible()
    await expect(page.getByLabel(/nome \*/i)).toBeVisible()
    await expect(page.getByLabel(/email \*/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /registrati/i })).toBeVisible()
  })

  test('gestione prenotazioni permette switch tra vista calendario e tabella', async ({ page }) => {
    // Login as admin
    await page.goto('/login')
    await page.getByLabel(/email/i).fill('admin@test.local')
    await page.getByLabel(/password/i).fill('test-password-sicura-123')
    await page.getByRole('button', { name: /accedi/i }).click()
    await expect(page).toHaveURL('/')

    await page.goto('/gestione-prenotazioni')
    await expect(page.getByRole('heading', { name: /gestione prenotazioni/i })).toBeVisible()

    // Di default e' in vista Calendario
    await expect(page.getByRole('button', { name: /calendario/i })).toBeVisible()
    await expect(page.getByText(/legenda/i)).toBeVisible()

    // Clicca Tabella
    await page.getByRole('button', { name: /tabella/i }).click()
    // Mostra la tabella con intestazione Cliente
    await expect(page.getByRole('columnheader', { name: /cliente/i })).toBeVisible()

    // Ritorna a Calendario
    await page.getByRole('button', { name: /calendario/i }).click()
    await expect(page.getByText(/legenda/i)).toBeVisible()
  })
})
