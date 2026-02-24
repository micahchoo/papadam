/**
 * papadam runtime config
 *
 * Loads the Django API base URL and CRDT WebSocket URL from /config.json
 * (injected by deploy/startup.sh at container start). Falls back to
 * VITE_* env vars for local dev.
 *
 * Architecture boundary: may only import from $lib/api.
 */

import { uiconfig } from '$lib/api';
import type { UIConfig } from '$lib/api';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RuntimeConfig {
	/** Django REST API base URL, e.g. "https://api.example.com" */
	apiUrl: string;
	/** CRDT WebSocket server URL, e.g. "wss://crdt.example.com" */
	crdtUrl: string;
}

// ── Defaults ──────────────────────────────────────────────────────────────────

const DEFAULT_RUNTIME: RuntimeConfig = {
	apiUrl: import.meta.env['VITE_API_URL'] ?? '',
	crdtUrl: import.meta.env['VITE_CRDT_URL'] ?? ''
};

// ── State ─────────────────────────────────────────────────────────────────────

let _runtime: RuntimeConfig = { ...DEFAULT_RUNTIME };
let _loaded = false;

// ── Runtime config loading ────────────────────────────────────────────────────

/**
 * Load runtime config from /config.json.
 * Safe to call multiple times — cached after first load.
 * Called once from +layout.svelte on mount.
 */
export async function loadConfig(): Promise<RuntimeConfig> {
	if (_loaded) return _runtime;

	// Env vars take precedence (local dev / Docker build-time injection)
	if (import.meta.env['VITE_API_URL']) {
		_loaded = true;
		return _runtime;
	}

	try {
		const resp = await fetch('/config.json');
		const json = (await resp.json()) as { API_URL?: string; CRDT_URL?: string };
		_runtime = {
			apiUrl: json['API_URL'] ?? '',
			crdtUrl: json['CRDT_URL'] ?? ''
		};
	} catch {
		// /config.json not found — keep defaults (local dev without config injection)
	}

	_loaded = true;
	return _runtime;
}

/** Synchronous getter — valid after loadConfig() resolves. */
export function getConfig(): RuntimeConfig {
	return _runtime;
}

// ── UIConfig loading ──────────────────────────────────────────────────────────

let _uiConfig: UIConfig | null = null;

/**
 * Fetch UIConfig from the API and cache it in module state.
 * Called from +layout.svelte on mount; subsequent callers get the cached value.
 */
export async function loadUIConfig(): Promise<UIConfig | null> {
	try {
		const { data } = await uiconfig.get();
		_uiConfig = data;
		return data;
	} catch {
		return null;
	}
}

/** Synchronous getter — valid after loadUIConfig() resolves. */
export function getUIConfig(): UIConfig | null {
	return _uiConfig;
}

export type { UIConfig };
