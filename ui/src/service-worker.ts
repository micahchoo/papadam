/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';
import { precacheAndRoute } from 'workbox-precaching';

// Precache all build output (JS, CSS) and static files
const precacheEntries = [...build, ...files].map((url) => ({
	url,
	revision: version
}));

precacheAndRoute(precacheEntries);
