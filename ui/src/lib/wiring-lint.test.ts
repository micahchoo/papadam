/**
 * Wiring lint tests — catch UI wiring failures at CI time.
 *
 * These tests grep .svelte source files for patterns that indicate
 * broken wiring: hardcoded values that should come from UIConfig stores
 * or brand CSS variables.
 *
 * Each test documents WHY the pattern is banned and WHAT to use instead.
 */

import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

/** Recursively collect all .svelte files under a directory. */
function svelteFiles(dir: string): string[] {
	const results: string[] = [];
	for (const entry of readdirSync(dir)) {
		const full = join(dir, entry);
		if (statSync(full).isDirectory()) {
			results.push(...svelteFiles(full));
		} else if (full.endsWith('.svelte')) {
			results.push(full);
		}
	}
	return results;
}

const SRC_DIR = join(__dirname, '..');
const ALL_SVELTE = svelteFiles(join(SRC_DIR, 'routes')).concat(
	svelteFiles(join(SRC_DIR, 'lib', 'components'))
);

describe('no hardcoded locale in date formatting', () => {
	// Banned: toLocaleDateString('en-GB') or ('en-US') etc.
	// Use: $dateLocale store from $lib/stores
	const LOCALE_PATTERN = /toLocale\w+String\(\s*['"][a-z]{2}(-[A-Z]{2})?['"]/;

	it('no .svelte file uses hardcoded locale in toLocale*String()', () => {
		const violations: string[] = [];
		for (const file of ALL_SVELTE) {
			const content = readFileSync(file, 'utf-8');
			const lines = content.split('\n');
			for (let i = 0; i < lines.length; i++) {
				if (LOCALE_PATTERN.test(lines[i]!)) {
					const relative = file.replace(SRC_DIR + '/', '');
					violations.push(`${relative}:${i + 1}: ${lines[i]!.trim()}`);
				}
			}
		}
		expect(
			violations,
			'Use $dateLocale store instead of hardcoded locale.\n' + violations.join('\n')
		).toHaveLength(0);
	});
});

describe('no hardcoded brand colors in component/route source', () => {
	// Banned patterns: Tailwind classes and hex values that bypass brand tokens.
	// Use: bg-brand-primary, bg-brand-accent, text-brand-primary, var(--brand-primary), etc.
	//
	// The spinner #3498db in <style> blocks is also banned — use var(--brand-accent).
	const BANNED_COLORS = [
		{ pattern: /bg-blue-950/, replacement: 'bg-brand-primary' },
		{ pattern: /bg-blue-500/, replacement: 'bg-brand-accent' },
		{ pattern: /bg-green-500/, replacement: 'bg-brand-accent' },
		{ pattern: /#3498db/, replacement: 'var(--brand-accent)' },
		{ pattern: /bg-blue-100/, replacement: 'bg-white or neutral' },
		{ pattern: /bg-blue-200/, replacement: 'bg-gray-200 or neutral' },
		{ pattern: /text-blue-500/, replacement: 'text-gray-600 or neutral' },
		{ pattern: /text-blue-100/, replacement: 'text-white' }
	];

	const EXEMPT_FILES = new Set<string>([]);

	it('no .svelte file uses banned hardcoded brand colors', () => {
		const violations: string[] = [];
		for (const file of ALL_SVELTE) {
			const relative = file.replace(SRC_DIR + '/', '');
			if (EXEMPT_FILES.has(relative)) continue;

			const content = readFileSync(file, 'utf-8');
			const lines = content.split('\n');
			for (let i = 0; i < lines.length; i++) {
				for (const { pattern, replacement } of BANNED_COLORS) {
					if (pattern.test(lines[i]!)) {
						violations.push(`${relative}:${i + 1}: found ${pattern} → use ${replacement}`);
					}
				}
			}
		}
		expect(
			violations,
			'Hardcoded brand colors found. Use CSS var classes instead:\n' + violations.join('\n')
		).toHaveLength(0);
	});
});
