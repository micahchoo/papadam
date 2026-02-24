/**
 * Unit tests for $lib/config
 *
 * config.ts holds module-level state (_loaded, _runtime). Each test resets
 * the module via vi.resetModules() + dynamic import to get a clean slate.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

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
