import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [svelte({ hot: !process.env.VITEST })],
	test: {
		environment: 'jsdom',
		globals: true,
		setupFiles: ['./tests/setup.ts'],
		include: ['src/**/*.{test,spec}.ts'],
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html'],
			include: ['src/lib/**'],
			exclude: [
				// Generated Paraglide runtime — not source code
				'src/lib/i18n/**',
				// Svelte UI components — covered by Playwright E2E, not Vitest
				'src/lib/components/**',
				// Type-only re-exports — no runtime code to cover
				'src/lib/index.ts'
			],
			thresholds: {
				lines: 80,
				functions: 80,
				branches: 70
			}
		}
	},
	resolve: {
		alias: {
			$lib: '/src/lib',
			$app: '/.svelte-kit/runtime/app'
		}
	}
});
