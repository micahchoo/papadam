<script lang="ts">
	import { onDestroy } from 'svelte';
	import Hls from 'hls.js';
	import { selectedMediaDuration, playbackPosition, playerSkipSeconds } from '$lib/stores';

	/** Minimal annotation shape MediaPlayer needs for image overlays. */
	export interface ImageAnnotation {
		media_target: string;
		/** Absolute URL from MinIO — guaranteed non-null by caller. */
		annotation_image: string;
	}

	interface Props {
		src?: string;
		autoplay?: boolean;
		controls?: boolean;
		/** Image annotations to overlay during playback (type='image', annotation_image set). */
		imageAnnotations?: ImageAnnotation[];
	}

	const { src = '', autoplay = false, controls = true, imageAnnotations = [] }: Props = $props();

	let videoEl = $state<HTMLVideoElement | null>(null);
	let audioEl = $state<HTMLAudioElement | null>(null);
	let hls: Hls | null = null;

	const isAudio = $derived(
		src.startsWith('data:audio') || /\.(mp3|ogg|wav|flac|aac|m4a)(\?|$)/i.test(src)
	);

	/** Parse "t=start,end" → [start, end] in seconds, or null if malformed. */
	function parseMediaTarget(target: string): [number, number] | null {
		const m = /^t=(\d+\.?\d*),(\d+\.?\d*)$/.exec(target);
		if (!m?.[1] || !m[2]) return null;
		return [parseFloat(m[1]), parseFloat(m[2])];
	}

	/** Image URL of the annotation whose time range covers the current position, or null. */
	const activeOverlayImage = $derived(
		imageAnnotations.find((a) => {
			const range = parseMediaTarget(a.media_target);
			return range !== null && $playbackPosition >= range[0] && $playbackPosition <= range[1];
		})?.annotation_image ?? null
	);

	function initHls(el: HTMLMediaElement, url: string) {
		if (hls) {
			hls.destroy();
			hls = null;
		}
		if (url.includes('.m3u8') && Hls.isSupported()) {
			hls = new Hls({ enableWorker: false });
			hls.loadSource(url);
			hls.attachMedia(el);
		} else {
			el.src = url;
		}
	}

	$effect(() => {
		const el = isAudio ? audioEl : videoEl;
		if (el && src) initHls(el, src);
		return () => {
			hls?.destroy();
			hls = null;
		};
	});

	function onLoadedMetadata(e: Event) {
		const el = e.target as HTMLMediaElement;
		selectedMediaDuration.set(el.duration);
	}

	function onTimeUpdate(e: Event) {
		const el = e.target as HTMLMediaElement;
		playbackPosition.set(el.currentTime);
	}

	/** Play a specific time range. Called by parent route component. */
	export function playSnippet(start: number, end: number): void {
		const el = isAudio ? audioEl : videoEl;
		if (!el) return;
		el.currentTime = start;
		void el.play();
		const stop = () => {
			if (el.currentTime >= end) {
				el.pause();
				el.removeEventListener('timeupdate', stop);
			}
		};
		el.addEventListener('timeupdate', stop);
	}

	/** Skip playback by delta seconds (negative = rewind). */
	function skip(delta: number): void {
		const el = isAudio ? audioEl : videoEl;
		if (!el) return;
		el.currentTime = Math.max(0, Math.min(el.duration, el.currentTime + delta));
	}

	onDestroy(() => {
		hls?.destroy();
	});
</script>

<div class="media-player-container pb-5">
	{#if src}
		<div class="relative">
			{#if isAudio}
				<audio
					bind:this={audioEl}
					{controls}
					{autoplay}
					class="w-full"
					onloadedmetadata={onLoadedMetadata}
					ontimeupdate={onTimeUpdate}
				>
					Your browser does not support the audio element.
				</audio>
			{:else}
				<video
					bind:this={videoEl}
					{controls}
					{autoplay}
					class="h-full w-full bg-black"
					onloadedmetadata={onLoadedMetadata}
					ontimeupdate={onTimeUpdate}
				>
					<track kind="captions" src="" label="Captions" />
					Your browser does not support the video element.
				</video>
			{/if}
			{#if activeOverlayImage}
				<div
					class="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/60"
				>
					<img
						src={activeOverlayImage}
						alt="Pinned annotation"
						class="max-h-full max-w-full object-contain"
					/>
				</div>
			{/if}
		</div>
		<div class="mt-2 flex items-center justify-center gap-4">
			<button
				onclick={() => skip(-$playerSkipSeconds[0])}
				class="rounded bg-gray-200 px-3 py-1 text-sm text-gray-700 hover:bg-gray-300"
				aria-label="Skip back {$playerSkipSeconds[0]} seconds"
			>
				← {$playerSkipSeconds[0]}s
			</button>
			<button
				onclick={() => skip($playerSkipSeconds[1])}
				class="rounded bg-gray-200 px-3 py-1 text-sm text-gray-700 hover:bg-gray-300"
				aria-label="Skip forward {$playerSkipSeconds[1]} seconds"
			>
				{$playerSkipSeconds[1]}s →
			</button>
		</div>
	{:else}
		<video {controls} class="w-full bg-black"
			><track kind="captions" src="" label="Captions" /></video
		>
	{/if}
</div>
