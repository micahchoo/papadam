import Hls from 'hls.js';

export interface HlsHandle {
	hls: Hls | null;
	destroy: () => void;
}

/**
 * Attach an HLS stream (or direct src) to a media element.
 * Pure utility — no store imports. Caller provides startLevel.
 * Returns a handle with the Hls instance (if created) and a destroy function.
 */
export function attachHls(
	el: HTMLMediaElement,
	url: string,
	startLevel?: number
): HlsHandle {
	if (url.includes('.m3u8') && Hls.isSupported()) {
		const hls = new Hls({
			enableWorker: false,
			startLevel: startLevel ?? -1
		});
		hls.loadSource(url);
		hls.attachMedia(el);
		return {
			hls,
			destroy: () => hls.destroy()
		};
	}
	el.src = url;
	return { hls: null, destroy: () => {} };
}
