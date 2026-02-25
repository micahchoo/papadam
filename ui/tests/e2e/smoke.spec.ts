/**
 * E2E smoke tests — papadam UI
 *
 * Verifies that key pages render without JS errors and display expected content.
 * Does not require a live backend; tests cover static/unauthenticated views only.
 */

import { test, expect } from '@playwright/test';

// Default brand values from `$uiConfig?.brand_name ?? 'Papad.alt'` in layout/components.
// Single change-point if the fallback changes.
const BRAND_NAME = 'Papad.alt';
const CONTACT_DOMAIN = 'aruvu.org';

test.describe('home page', () => {
	test('renders with title and navigation', async ({ page }) => {
		await page.goto('/');

		// Nav present
		await expect(page.locator('nav')).toBeVisible();
		await expect(page.getByRole('link', { name: BRAND_NAME }).first()).toBeVisible();

		// Hero content
		const brandPattern = new RegExp(BRAND_NAME.replace('.', '\\.'), 'i');
		await expect(page.getByRole('heading', { name: brandPattern }).first()).toBeVisible();

		// CTA button
		await expect(page.getByRole('button', { name: /View Collections/i })).toBeVisible();
	});

	test('navigation links are present', async ({ page }) => {
		await page.goto('/');

		await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Collections' })).toBeVisible();
		// Unauthenticated: Login link shown
		await expect(page.getByRole('link', { name: 'Login' })).toBeVisible();
	});

	test('footer is present with contact info', async ({ page }) => {
		await page.goto('/');

		const contactPattern = new RegExp(CONTACT_DOMAIN.replace('.', '\\.'), 'i');
		await expect(page.locator('footer')).toBeVisible();
		await expect(
			page
				.locator('footer')
				.getByRole('link', { name: contactPattern })
				.first()
		).toBeVisible();
	});

	test('View Collections button navigates to /groups', async ({ page }) => {
		await page.goto('/');

		await page.getByRole('button', { name: /View Collections/i }).click();
		await expect(page).toHaveURL(/\/groups/);
	});
});

test.describe('groups page', () => {
	test('renders without crashing (no backend)', async ({ page }) => {
		// Page may show loading spinner or error — it should not crash the app
		const errors: string[] = [];
		page.on('pageerror', (err) => errors.push(err.message));

		await page.goto('/groups');

		// Nav should still be there (layout renders)
		await expect(page.locator('nav')).toBeVisible();

		// No uncaught JS errors (API failure is handled gracefully)
		expect(errors.filter((e) => !e.includes('Failed to load collection'))).toHaveLength(0);
	});
});

test.describe('exhibits page', () => {
	test('nav includes Exhibits link', async ({ page }) => {
		await page.goto('/');
		await expect(page.getByRole('link', { name: 'Exhibits' })).toBeVisible();
	});

	test('renders without crashing (no backend)', async ({ page }) => {
		const errors: string[] = [];
		page.on('pageerror', (err) => errors.push(err.message));

		await page.goto('/exhibits');

		// Layout renders
		await expect(page.locator('nav')).toBeVisible();

		// No uncaught JS errors
		expect(errors).toHaveLength(0);
	});
});

test.describe('adversarial routes', () => {
	test('nonexistent route shows error page without crash', async ({ page }) => {
		const errors: string[] = [];
		page.on('pageerror', (err) => errors.push(err.message));

		await page.goto('/nonexistent-route-12345');

		// App should still render layout (nav present)
		await expect(page.locator('nav')).toBeVisible();

		// No uncaught JS errors
		expect(errors).toHaveLength(0);
	});
});
