/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { ExpirationPlugin } from 'workbox-expiration';
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, NetworkOnly, StaleWhileRevalidate } from 'workbox-strategies';

// Precache all build output (JS, CSS) and static files
const precacheEntries = [...build, ...files].map((url) => ({
	url,
	revision: version
}));

precacheAndRoute(precacheEntries);

// HLS segments, thumbnails, images, audio/video — stale-while-revalidate with LRU cap
registerRoute(
	({ url }) =>
		url.pathname.match(/\.(ts|m3u8|jpg|jpeg|png|gif|webp|svg|mp3|mp4|webm)$/i) !== null,
	new StaleWhileRevalidate({
		cacheName: 'media-cache',
		plugins: [
			new ExpirationPlugin({
				maxEntries: 200,
				maxAgeSeconds: 7 * 24 * 60 * 60 // 7 days
			})
		]
	})
);

// ── Auth token helpers for Background Sync replay ─────────────────────────────
// The SW can't read localStorage, so the client writes refresh_token to IDB.
// Before replaying queued uploads, we refresh the JWT if needed.

const AUTH_DB = 'papadam-auth';
const AUTH_STORE = 'tokens';

declare const self: ServiceWorkerGlobalScope;

async function openAuthDb(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const req = indexedDB.open(AUTH_DB, 1);
		req.onupgradeneeded = () => {
			req.result.createObjectStore(AUTH_STORE);
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
}

async function getRefreshToken(): Promise<string | null> {
	try {
		const db = await openAuthDb();
		return await new Promise((resolve) => {
			const tx = db.transaction(AUTH_STORE, 'readonly');
			const store = tx.objectStore(AUTH_STORE);
			const req = store.get('refresh_token');
			req.onsuccess = () => resolve((req.result as string) ?? null);
			req.onerror = () => resolve(null);
		});
	} catch {
		return null;
	}
}

async function storeAccessToken(token: string): Promise<void> {
	const db = await openAuthDb();
	return new Promise((resolve) => {
		const tx = db.transaction(AUTH_STORE, 'readwrite');
		tx.objectStore(AUTH_STORE).put(token, 'access_token');
		tx.oncomplete = () => resolve();
	});
}

async function refreshAccessToken(): Promise<string | null> {
	const refresh = await getRefreshToken();
	if (!refresh) return null;

	try {
		const res = await fetch('/auth/jwt/refresh/', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ refresh })
		});
		if (!res.ok) return null;
		const data = (await res.json()) as { access: string };
		await storeAccessToken(data.access);
		return data.access;
	} catch {
		return null;
	}
}

function notifyClientsAuthExpired() {
	self.clients.matchAll().then((clients) => {
		for (const client of clients) {
			client.postMessage({ type: 'AUTH_EXPIRED' });
		}
	});
}

// POST requests to upload endpoints: network-only with background sync retry
const uploadSyncPlugin = new BackgroundSyncPlugin('upload-queue', {
	maxRetentionTime: 7 * 24 * 60, // 7 days in minutes
	async onSync({ queue }) {
		// Refresh token before replaying queued requests
		const freshToken = await refreshAccessToken();
		if (!freshToken) {
			notifyClientsAuthExpired();
			// Throw so Workbox knows sync failed and will retry later
			throw new Error('Auth token refresh failed — will retry on next sync event');
		}

		let entry: Awaited<ReturnType<typeof queue.shiftRequest>>;
		while ((entry = await queue.shiftRequest())) {
			try {
				// Clone request with fresh auth header
				const headers = new Headers(entry.request.headers);
				headers.set('Authorization', `Bearer ${freshToken}`);
				const freshRequest = new Request(entry.request, { headers });
				await fetch(freshRequest);
			} catch (error) {
				// Re-add failed entry and stop processing
				await queue.unshiftRequest(entry);
				throw error;
			}
		}
	}
});

registerRoute(
	({ url }) =>
		url.pathname.startsWith('/api/v1/annotate/') || url.pathname.startsWith('/api/v1/archive/'),
	new NetworkOnly({ plugins: [uploadSyncPlugin] }),
	'POST'
);

// API GET responses — network-first with cached fallback for offline
registerRoute(
	({ url }) => url.pathname.startsWith('/api/'),
	new NetworkFirst({
		cacheName: 'api-cache',
		plugins: [
			new ExpirationPlugin({
				maxEntries: 100,
				maxAgeSeconds: 24 * 60 * 60 // 1 day
			})
		]
	})
);
