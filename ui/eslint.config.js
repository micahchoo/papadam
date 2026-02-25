// papadam/ui — ESLint config
//
// Architecture enforcement via eslint-plugin-boundaries:
//   lib/api.ts          → may import from nothing internal (pure HTTP client)
//   lib/events.ts       → may import from lib/api only
//   lib/crdt.ts         → may import from lib/stores only
//   lib/config.ts       → may import from lib/api only
//   lib/stores.ts       → may import from lib/config, lib/crdt, lib/api (types)
//   lib/components/**   → may import from lib/stores, lib/api, lib/config, lib/events, lib/i18n
//   routes/**           → may import from lib/** (anything)
//   No circular imports.

import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import sveltePlugin from 'eslint-plugin-svelte';
import boundariesPlugin from 'eslint-plugin-boundaries';
import svelteParser from 'svelte-eslint-parser';

export default [
	// ── Ignored paths ─────────────────────────────────────────────────────────
	{
		ignores: [
			'.svelte-kit/**',
			'build/**',
			'coverage/**',
			'src/lib/i18n/**',
			'vitest.config.ts',
			'playwright.config.ts',
			'node_modules/**'
		]
	},

	// ── TypeScript + Svelte base ──────────────────────────────────────────────
	{
		files: ['**/*.ts', '**/*.svelte'],
		plugins: {
			'@typescript-eslint': tsPlugin,
			svelte: sveltePlugin,
			boundaries: boundariesPlugin
		},
		languageOptions: {
			parser: tsParser,
			parserOptions: {
				project: './tsconfig.json',
				extraFileExtensions: ['.svelte']
			}
		},
		rules: {
			// TypeScript: explicit types
			'@typescript-eslint/no-explicit-any': 'error',
			'@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
			'@typescript-eslint/consistent-type-imports': 'error',

			// TypeScript: unsafe `any` propagation (requires project: tsconfig.json)
			'@typescript-eslint/no-unsafe-assignment': 'error',
			'@typescript-eslint/no-unsafe-call': 'error',
			'@typescript-eslint/no-unsafe-member-access': 'error',
			'@typescript-eslint/no-unsafe-return': 'error',
			'@typescript-eslint/no-unsafe-argument': 'error',

			// Async / Promise safety
			'@typescript-eslint/no-floating-promises': 'error',
			'@typescript-eslint/no-misused-promises': 'error',
			'@typescript-eslint/prefer-promise-reject-errors': 'error',
			// return await in try-catch preserves the error stack inside the catch block
			'@typescript-eslint/return-await': ['error', 'in-try-catch'],

			// Exhaustiveness — switch on a discriminated union must handle every member
			'@typescript-eslint/switch-exhaustiveness-check': 'error',

			// Throw only Error instances — catch variables are always Error, not unknown
			'@typescript-eslint/only-throw-error': 'error',

			// Type quality
			'@typescript-eslint/no-redundant-type-constituents': 'error',
			'@typescript-eslint/prefer-optional-chain': 'error',
			'@typescript-eslint/no-non-null-assertion': 'error',
			'@typescript-eslint/no-unnecessary-type-assertion': 'error',
			'@typescript-eslint/prefer-nullish-coalescing': [
				'error',
				{ ignorePrimitives: { string: true, boolean: true, number: true } }
			],

			// Warn: useful signal but can fire on imperfect third-party types
			'@typescript-eslint/no-unnecessary-condition': 'warn',

			// No console.log in source (use structured logger)
			'no-console': ['error', { allow: ['warn', 'error'] }]
		}
	},

	// ── Svelte files ──────────────────────────────────────────────────────────
	{
		files: ['**/*.svelte'],
		languageOptions: {
			parser: svelteParser,
			parserOptions: { parser: tsParser }
		},
		rules: {
			...sveltePlugin.configs.recommended.rules,
			// Accessibility rules — enforced, not warned
			'svelte/valid-compile': 'error',
			// {@html} is always passed through DOMPurify.sanitize() before rendering
			'svelte/no-at-html-tags': 'warn'
		}
	},

	// ── Architecture boundaries ───────────────────────────────────────────────
	{
		files: ['src/**/*.ts', 'src/**/*.svelte'],
		settings: {
			'boundaries/ignore': ['**/*.css'],
			'boundaries/elements': [
				{ type: 'api', pattern: 'src/lib/api.ts' },
				{ type: 'events', pattern: 'src/lib/events.ts' },
				{ type: 'crdt', pattern: 'src/lib/crdt.ts' },
				{ type: 'config', pattern: 'src/lib/config.ts' },
				{ type: 'stores', pattern: 'src/lib/stores.ts' },
				{ type: 'hls', pattern: 'src/lib/hls.ts' },
				{ type: 'i18n', pattern: 'src/lib/i18n/**' },
				{ type: 'primitives', pattern: 'src/lib/components/primitives/**' },
				{ type: 'components', pattern: 'src/lib/components/**' },
				{ type: 'routes', pattern: 'src/routes/**' }
			]
		},
		rules: {
			'boundaries/element-types': [
				'error',
				{
					default: 'disallow',
					rules: [
						// api.ts is a leaf — pure HTTP, no internal imports
						{ from: 'api', allow: [] },

						// events.ts polls job status — imports api only
						{ from: 'events', allow: ['api'] },

						// crdt.ts only needs stores
						{ from: 'crdt', allow: ['stores'] },

						// config.ts fetches UIConfig via api
						{ from: 'config', allow: ['api'] },

						// stores hold reactive state — may read config and crdt doc; imports
						// domain types (User, Group, MediaStore) from api (type-only at runtime)
						{ from: 'stores', allow: ['config', 'crdt', 'api'] },

						// hls.ts is a leaf — pure HLS utility, no internal imports
						{ from: 'hls', allow: [] },

						// i18n is a leaf — no internal imports
						{ from: 'i18n', allow: [] },

						// primitives: unstyled components, may use hls utility
						{ from: 'primitives', allow: ['hls'] },

						// components: full access to lib layer (including events for upload progress)
						{
							from: 'components',
							allow: ['api', 'stores', 'config', 'events', 'i18n', 'primitives', 'hls']
						},

						// routes: full access to everything
						{
							from: 'routes',
							allow: [
								'api',
								'events',
								'crdt',
								'config',
								'stores',
								'i18n',
								'hls',
								'primitives',
								'components'
							]
						}
					]
				}
			],

			'boundaries/no-unknown': 'error'
		}
	},

	// ── Files that use DOMPurify.sanitize() before every {@html} ─────────────
	// The content IS sanitized; the rule cannot detect the sanitize() call so
	// we disable it per-file. Inline HTML comment directives are ignored by
	// eslint-plugin-svelte ≥ 2.46 for this rule.
	{
		files: [
			'src/lib/components/AnnotationViewer.svelte',
			// All group and exhibit routes use DOMPurify.sanitize() before every {@html}.
			// The SvelteKit [param] folder names contain brackets that glob treats as
			// character classes, so we match the whole subtree instead of specific files.
			'src/routes/exhibits/**/*.svelte',
			'src/routes/groups/**/*.svelte'
		],
		rules: {
			'svelte/no-at-html-tags': 'off'
		}
	},

	// ── Test files ────────────────────────────────────────────────────────────
	{
		files: ['**/*.test.ts', '**/*.spec.ts', 'tests/**'],
		rules: {
			'no-console': 'off',
			// Tests mock library boundaries with `any` — relax propagation rules consistently
			'@typescript-eslint/no-explicit-any': 'off',
			'@typescript-eslint/no-unsafe-assignment': 'off',
			'@typescript-eslint/no-unsafe-call': 'off',
			'@typescript-eslint/no-unsafe-member-access': 'off',
			'@typescript-eslint/no-unsafe-return': 'off',
			'@typescript-eslint/no-unsafe-argument': 'off',
			'@typescript-eslint/no-floating-promises': 'off',
			'@typescript-eslint/no-misused-promises': 'off',
			'@typescript-eslint/no-non-null-assertion': 'off',
			'@typescript-eslint/no-unnecessary-type-assertion': 'off',
			'@typescript-eslint/no-unnecessary-condition': 'off',
			'@typescript-eslint/prefer-nullish-coalescing': 'off',
			'@typescript-eslint/return-await': 'off',
			'boundaries/element-types': 'off'
		}
	}
];
