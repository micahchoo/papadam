// papadam/ui — ESLint config
//
// Architecture enforcement via eslint-plugin-boundaries:
//   lib/api.ts          → may import from nothing internal (pure HTTP client)
//   lib/crdt.ts         → may import from lib/stores only
//   lib/config.ts       → may import from lib/api only
//   lib/stores.ts       → may import from lib/config, lib/crdt
//   lib/components/**   → may import from lib/stores, lib/api, lib/config, lib/i18n
//   routes/**           → may import from lib/** (anything)
//   No circular imports.

import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import sveltePlugin from 'eslint-plugin-svelte'
import boundariesPlugin from 'eslint-plugin-boundaries'
import svelteParser from 'svelte-eslint-parser'

export default [
  // ── TypeScript + Svelte base ──────────────────────────────────────────────
  {
    files: ['**/*.ts', '**/*.svelte'],
    plugins: {
      '@typescript-eslint': tsPlugin,
      svelte: sveltePlugin,
      boundaries: boundariesPlugin,
    },
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: './tsconfig.json',
        extraFileExtensions: ['.svelte'],
      },
    },
    rules: {
      // TypeScript strict rules
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',

      // No console.log in source (use structured logger)
      'no-console': ['error', { allow: ['warn', 'error'] }],
    },
  },

  // ── Svelte files ──────────────────────────────────────────────────────────
  {
    files: ['**/*.svelte'],
    languageOptions: {
      parser: svelteParser,
      parserOptions: { parser: tsParser },
    },
    rules: {
      ...sveltePlugin.configs.recommended.rules,
      // Accessibility rules — enforced, not warned
      'svelte/valid-compile': 'error',
    },
  },

  // ── Architecture boundaries ───────────────────────────────────────────────
  {
    files: ['src/**/*.ts', 'src/**/*.svelte'],
    settings: {
      'boundaries/elements': [
        { type: 'api',        pattern: 'src/lib/api.ts' },
        { type: 'crdt',       pattern: 'src/lib/crdt.ts' },
        { type: 'config',     pattern: 'src/lib/config.ts' },
        { type: 'stores',     pattern: 'src/lib/stores.ts' },
        { type: 'i18n',       pattern: 'src/lib/i18n/**' },
        { type: 'primitives', pattern: 'src/lib/components/primitives/**' },
        { type: 'components', pattern: 'src/lib/components/**' },
        { type: 'routes',     pattern: 'src/routes/**' },
      ],
    },
    rules: {
      'boundaries/element-types': ['error', {
        default: 'disallow',
        rules: [
          // api.ts is a leaf — pure HTTP, no internal imports
          { from: 'api',        allow: [] },

          // crdt.ts only needs stores
          { from: 'crdt',       allow: ['stores'] },

          // config.ts fetches UIConfig via api
          { from: 'config',     allow: ['api'] },

          // stores hold reactive state — may read config and crdt doc
          { from: 'stores',     allow: ['config', 'crdt'] },

          // i18n is a leaf — no internal imports
          { from: 'i18n',       allow: [] },

          // primitives: unstyled components, no business logic
          { from: 'primitives', allow: [] },

          // components: full access to lib layer, not to routes
          { from: 'components', allow: ['api', 'stores', 'config', 'i18n', 'primitives'] },

          // routes: full access to everything
          { from: 'routes',     allow: ['api', 'crdt', 'config', 'stores', 'i18n', 'primitives', 'components'] },
        ],
      }],

      'boundaries/no-unknown': 'error',
    },
  },

  // ── Test files ────────────────────────────────────────────────────────────
  {
    files: ['**/*.test.ts', '**/*.spec.ts', 'tests/**'],
    rules: {
      'no-console': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      'boundaries/element-types': 'off',
    },
  },
]
