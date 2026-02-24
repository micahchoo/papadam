import { sveltekit } from '@sveltejs/kit/vite';
import { paraglide } from '@inlang/paraglide-sveltekit/vite';
import { defineConfig } from 'vite';

// Dev proxy target: reads VITE_API_URL from the environment (set in .env.local
// from .env.example). Falls back to the standard Django dev port.
// In production this file is not used — nginx/Caddy handles routing.
const API_TARGET = process.env['VITE_API_URL'] ?? 'http://localhost:8000';
const PROXY_OPTS = { target: API_TARGET, changeOrigin: true };

export default defineConfig({
	plugins: [
		sveltekit(),
		paraglide({
			// Project config — message sources read from messages/{languageTag}.json
			project: './project.inlang',
			// Generated runtime emitted here; matches the eslint `i18n` boundary element
			outdir: './src/lib/i18n'
		})
	],
	server: {
		proxy: {
			'/api': PROXY_OPTS,
			'/auth': PROXY_OPTS,
			'/healthcheck': PROXY_OPTS,
			'/config.json': PROXY_OPTS
		}
	}
});
