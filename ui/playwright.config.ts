import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: './tests/e2e',
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	workers: process.env.CI ? 1 : undefined,
	reporter: process.env.CI ? 'github' : 'html',

	use: {
		baseURL: process.env.BASE_URL ?? 'http://localhost:5173',
		trace: 'on-first-retry',
		// Accessibility — every test gets axe assertions available
		extraHTTPHeaders: { 'Accept-Language': 'en' }
	},

	projects: [
		{ name: 'chromium', use: { ...devices['Desktop Chrome'] } },
		{ name: 'firefox', use: { ...devices['Desktop Firefox'] } },
		// Low-end mobile — critical for target users
		{ name: 'mobile-android', use: { ...devices['Pixel 5'] } }
	],

	webServer: {
		command: 'npm run dev',
		port: 5173,
		reuseExistingServer: !process.env.CI
	}
});
