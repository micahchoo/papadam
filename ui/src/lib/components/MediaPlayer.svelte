<script lang="ts">
	import { onDestroy } from 'svelte';
	import Hls from 'hls.js';
	import { selectedMediaDuration, playbackPosition } from '$lib/stores';

	interface Props {
		src?: string;
		autoplay?: boolean;
		controls?: boolean;
	}

	const { src = '', autoplay = false, controls = true }: Props = $props();

	let videoEl = $state<HTMLVideoElement | null>(null);
	let audioEl = $state<HTMLAudioElement | null>(null);
	let hls: Hls | null = null;

	const isAudio = $derived(
		src.startsWith('data:audio') || /\.(mp3|ogg|wav|flac|aac|m4a)(\?|$)/i.test(src)
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

	onDestroy(() => {
		hls?.destroy();
	});
</script>

<div class="media-player-container pb-5">
	{#if src}
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
	{:else}
		<video {controls} class="w-full bg-black"
			><track kind="captions" src="" label="Captions" /></video
		>
	{/if}
</div>
