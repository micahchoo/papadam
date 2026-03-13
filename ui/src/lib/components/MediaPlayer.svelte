<script lang="ts">
	import { onDestroy } from 'svelte';
	import { attachHls } from '$lib/hls';
	import type { HlsHandle } from '$lib/hls';
	import {
		selectedMediaDuration,
		playbackPosition,
		playerSkipSeconds,
		defaultQuality
	} from '$lib/stores';

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
		/** WebVTT caption URL from the transcript worker. Empty string = no captions. */
		transcriptUrl?: string;
	}

	const {
		src = '',
		autoplay = false,
		controls = true,
		imageAnnotations = [],
		transcriptUrl = ''
	}: Props = $props();

	let videoEl = $state<HTMLVideoElement | null>(null);
	let audioEl = $state<HTMLAudioElement | null>(null);
	let hlsHandle: HlsHandle | null = null;
	let hlsError = $state('');

	const isAudio = $derived(
		src.startsWith('data:audio') || /\.(mp3|ogg|wav|flac|aac|m4a)(\?|$)/i.test(src)
	);

	const isImage = $derived(
		/\.(jpe?g|png|gif|webp|bmp|svg)(\?|$)/i.test(src)
	);

	/** Parse "t=start,end" → [start, end] in seconds, or null if malformed.
	 *  Accepts both decimal seconds (t=1.5,10) and MM:SS format (t=01:30,10:00). */
	function parseMediaTarget(target: string): [number, number] | null {
		const clean = target.replace(/\s+/g, '').replace(/^t=/, '');
		// Try MM:SS,MM:SS first
		const mmss = /^(\d{1,2}):(\d{2}),(\d{1,2}):(\d{2})$/.exec(clean);
		if (mmss?.[1] && mmss[2] && mmss[3] && mmss[4]) {
			return [
				parseInt(mmss[1]) * 60 + parseInt(mmss[2]),
				parseInt(mmss[3]) * 60 + parseInt(mmss[4])
			];
		}
		// Decimal seconds
		const parts = clean.split(',').map(Number);
		const start = parts[0];
		const end = parts[1];
		if (parts.length === 2 && start !== undefined && end !== undefined && !isNaN(start) && !isNaN(end)) {
			return [start, end];
		}
		return null;
	}

	/** Image URL of the annotation whose time range covers the current position, or null. */
	const activeOverlayImage = $derived(
		imageAnnotations.find((a) => {
			const range = parseMediaTarget(a.media_target);
			return range !== null && $playbackPosition >= range[0] && $playbackPosition <= range[1];
		})?.annotation_image ?? null
	);

	/** Map UIConfig quality to HLS.js startLevel. -1 = auto, 0 = lowest, Infinity = highest. */
	function qualityToStartLevel(q: string): number {
		if (q === 'low') return 0;
		if (q === 'high') return Infinity;
		// 'medium' and 'auto' both use HLS auto-selection (-1)
		return -1;
	}

	$effect(() => {
		const el = isAudio ? audioEl : videoEl;
		if (el && src) {
			hlsHandle?.destroy();
			hlsError = '';
			hlsHandle = attachHls(el, src, qualityToStartLevel($defaultQuality), (msg) => {
				hlsError = msg;
			});
		}
		return () => {
			hlsHandle?.destroy();
			hlsHandle = null;
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
		hlsHandle?.destroy();
	});
</script>

<div class="media-player-container pb-5">
	{#if src}
		{#if isImage}
			<img src={src} alt="Media" class="w-full rounded" />
		{:else}
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
						<track kind="captions" src={transcriptUrl} label="Captions" default={!!transcriptUrl} />
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
			<!-- Phase 5: waveform renderer — gated by showWaveform store -->
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
			{#if hlsError}
				<p class="mt-2 rounded bg-red-100 px-3 py-2 text-sm text-red-700" role="alert">{hlsError}</p>
			{/if}
		{/if}
	{:else}
		<video {controls} class="w-full bg-black"><track kind="captions" /></video>
	{/if}
</div>
