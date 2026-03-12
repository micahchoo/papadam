/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],

	theme: {
		extend: {
			colors: {
				// Maps to CSS custom properties set by +layout.svelte from UIConfig.
				// Opacity variants (bg-brand-primary/50) are not supported because
				// Tailwind can't inspect a CSS variable's channel values at build time.
				'brand-primary': 'var(--brand-primary)',
				'brand-accent': 'var(--brand-accent)'
			},
			fontFamily: {
				heading: ['Playfair Display', 'Georgia', 'serif'],
				body: ['Inter', 'system-ui', 'sans-serif']
			}
		}
	},

	plugins: []
};
