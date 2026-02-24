import { sveltekit } from '@sveltejs/kit/vite';
import { paraglide } from '@inlang/paraglide-sveltekit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit(),
		paraglide({
			// Project config — message sources read from messages/{languageTag}.json
			project: './project.inlang',
			// Generated runtime emitted here; matches the eslint `i18n` boundary element
			outdir: './src/lib/i18n'
		})
	]
});
