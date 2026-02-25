/**
 * Unit tests for $lib/config
 *
 * config.ts holds module-level state (_loaded, _runtime). Each test resets
 * the module via vi.resetModules() + dynamic import to get a clean slate.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Prevent api.ts from firing its module-level resolveBaseUrl() call (which calls fetch)
// when config.ts is re-imported after vi.resetModules().  config.ts only uses uiconfig.get()
// in loadUIConfig(), which is not under test here.
vi.mock('$lib/api', () => ({
	uiconfig: { get: vi.fn().mockResolvedValue({ data: null }) }
}));

beforeEach(() => {
	vi.resetModules();
	// Clear VITE_API_URL/VITE_CRDT_URL so .env.local values don't short-circuit config.ts.
	// Tests that need a specific value stub it explicitly; afterEach calls vi.unstubAllEnvs().
	vi.stubEnv('VITE_API_URL', '');
	vi.stubEnv('VITE_CRDT_URL', '');
});

afterEach(() => {
	vi.unstubAllGlobals();
	vi.unstubAllEnvs();
});

describe('getUIConfig', () => {
	it('returns null before loadUIConfig is called', async () => {
		const { getUIConfig } = await import('$lib/config');
		expect(getUIConfig()).toBeNull();
	});
});

describe('loadConfig', () => {
	it('fetches /config.json and populates apiUrl + crdtUrl', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				json: () => Promise.resolve({ API_URL: 'http://api.test', CRDT_URL: 'ws://crdt.test' })
			})
		);
		const { loadConfig, getConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(cfg.apiUrl).toBe('http://api.test');
		expect(cfg.crdtUrl).toBe('ws://crdt.test');
		// getConfig() should reflect the loaded values
		expect(getConfig().apiUrl).toBe('http://api.test');
	});

	it('falls back to empty strings when /config.json fetch throws', async () => {
		vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('ECONNREFUSED')));
		const { loadConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(cfg.apiUrl).toBe('');
		expect(cfg.crdtUrl).toBe('');
	});

	it('is cached — fetch called only once on repeated calls', async () => {
		const mockFetch = vi.fn().mockResolvedValue({
			json: () => Promise.resolve({ API_URL: 'http://once.test', CRDT_URL: '' })
		});
		vi.stubGlobal('fetch', mockFetch);
		const { loadConfig } = await import('$lib/config');
		await loadConfig();
		await loadConfig();
		expect(mockFetch).toHaveBeenCalledTimes(1);
	});

	it('skips fetch when VITE_API_URL env var is set', async () => {
		vi.stubEnv('VITE_API_URL', 'http://env.test');
		const mockFetch = vi.fn();
		vi.stubGlobal('fetch', mockFetch);
		const { loadConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(mockFetch).not.toHaveBeenCalled();
		expect(cfg.apiUrl).toBe('http://env.test');
	});
});

describe('loadConfig — adversarial', () => {
	it('handles malformed JSON gracefully (falls back to defaults)', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				json: () => Promise.reject(new SyntaxError('Unexpected token'))
			})
		);
		const { loadConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(cfg.apiUrl).toBe('');
		expect(cfg.crdtUrl).toBe('');
	});

	it('handles partial config (API_URL only, no CRDT_URL)', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				json: () => Promise.resolve({ API_URL: 'http://partial.test' })
			})
		);
		const { loadConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(cfg.apiUrl).toBe('http://partial.test');
		expect(cfg.crdtUrl).toBe('');
	});

	it('handles empty object {} — both fields fall back to empty string', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				json: () => Promise.resolve({})
			})
		);
		const { loadConfig } = await import('$lib/config');
		const cfg = await loadConfig();
		expect(cfg.apiUrl).toBe('');
		expect(cfg.crdtUrl).toBe('');
	});

	it('concurrent loadConfig calls both resolve to same values', async () => {
		const mockFetch = vi.fn().mockResolvedValue({
			json: () => Promise.resolve({ API_URL: 'http://concurrent.test', CRDT_URL: '' })
		});
		vi.stubGlobal('fetch', mockFetch);
		const { loadConfig } = await import('$lib/config');
		// loadConfig caches via _loaded flag set after await, so concurrent
		// calls before the first resolves will both fetch — but both converge
		// to the same config values.
		const [cfg1, cfg2] = await Promise.all([loadConfig(), loadConfig()]);
		expect(cfg1.apiUrl).toBe(cfg2.apiUrl);
		expect(cfg1.apiUrl).toBe('http://concurrent.test');
	});
});

describe('getConfig', () => {
	it('returns current runtime config after loadConfig resolves', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				json: () => Promise.resolve({ API_URL: 'http://getconfig.test', CRDT_URL: 'ws://gc.test' })
			})
		);
		const { loadConfig, getConfig } = await import('$lib/config');
		await loadConfig();
		const cfg = getConfig();
		expect(cfg.apiUrl).toBe('http://getconfig.test');
		expect(cfg.crdtUrl).toBe('ws://gc.test');
	});
});
