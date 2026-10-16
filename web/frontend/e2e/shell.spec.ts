import { expect, test } from '@playwright/test';

test('desktop shell preserves navigation and company context', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Dashboard', exact: true })).toBeVisible();
  await expect(page.getByRole('navigation').getByRole('button')).toHaveCount(11);
  await expect(page.getByLabel('Empresa ativa')).toBeVisible();
  await page.screenshot({ path: '../docs/screenshots/task7-desktop.png', fullPage: true });
});

test('mobile drawer contains focus and tables scroll without overflowing the page', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  const trigger = page.getByRole('button', { name: 'Abrir menu' });
  await expect(page.getByRole('navigation')).not.toBeVisible();
  await trigger.click();
  await expect(page.getByRole('button', { name: 'Fechar menu', exact: true })).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('button', { name: 'Backup', exact: true })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('button', { name: 'Fechar menu', exact: true })).toBeFocused();
  await page.screenshot({ path: '../docs/screenshots/task7-mobile-drawer.png', fullPage: true });
  await page.keyboard.press('Escape');
  await expect(trigger).toBeFocused();
  await expect(page.getByRole('navigation')).not.toBeVisible();
  await page.screenshot({ path: '../docs/screenshots/task7-mobile.png', fullPage: true });
  await trigger.click();
  await page.getByRole('button', { name: 'Colaboradores', exact: true }).click();
  const table = page.getByRole('region', { name: 'Colaboradores cadastrados' });
  expect(await table.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await table.evaluate(element => { element.scrollLeft = element.scrollWidth; });
  await expect(page.getByRole('columnheader', { name: 'Status', exact: true })).toBeInViewport();
  await page.screenshot({ path: '../docs/screenshots/task7-mobile-table.png', fullPage: true });
});

test('resizing an open mobile drawer to desktop restores content interaction', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Abrir menu' }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(page.locator('.workspace')).not.toHaveAttribute('inert');
  await expect(page.locator('body')).not.toHaveCSS('overflow', 'hidden');
  await expect(page.getByLabel('Empresa ativa')).toBeVisible();
});
