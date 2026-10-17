import { expect, test } from '@playwright/test'

test('home explains the workshop and starts it', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Enterprise auth, hands on.')
  await expect(page.getByRole('figure')).toContainText('LEAK')

  await page.getByRole('link', { name: 'Start the workshop' }).click()
  await expect(page).toHaveURL(/\/workshop\/01-the-map$/)
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('The map')
})

test('the chapters list and page through', async ({ page }) => {
  await page.goto('/workshop')
  await expect(page.locator('main ol > li')).toHaveCount(7)

  await page.locator('main ol > li').nth(3).click()
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('SAML in one page')
  await page.getByRole('link', { name: /Next/ }).click()
  await expect(page).toHaveURL(/05-roles$/)
})

test('nothing scrolls sideways', async ({ page }) => {
  for (const path of ['/', '/workshop', '/workshop/03-oidc-id-tokens']) {
    await page.goto(path)
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    )
    expect(overflow, path).toBeLessThanOrEqual(0)
  }
})

test('back to top returns to the top', async ({ page }) => {
  await page.goto('/workshop/07-row-level-security')
  await page.evaluate(() => window.scrollTo(0, 3000))
  const button = page.getByRole('button', { name: 'Back to top' })

  await expect(button).toBeVisible()
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0)
})
