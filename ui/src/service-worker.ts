/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';
import { ExpirationPlugin } from 'workbox-expiration';
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';

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

// API responses — network-first with cached fallback for offline
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
