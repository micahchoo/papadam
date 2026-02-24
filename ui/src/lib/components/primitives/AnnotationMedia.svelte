<script lang="ts">
	import { onDestroy } from 'svelte';
	import Hls from 'hls.js';

	interface Props {
		src: string;
		mediaType: 'audio' | 'video';
	}

	const { src, mediaType }: Props = $props();

	let mediaEl = $state<HTMLMediaElement | null>(null);
	let hls: Hls | null = null;

	function initHls(el: HTMLMediaElement, url: string): void {
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
		if (mediaEl && src) initHls(mediaEl, src);
		return () => {
			hls?.destroy();
			hls = null;
		};
	});

	onDestroy(() => {
		hls?.destroy();
	});
</script>

{#if mediaType === 'audio'}
	<audio bind:this={mediaEl} controls class="mt-2 w-full">
		Your browser does not support audio playback.
	</audio>
{:else}
	<video bind:this={mediaEl} controls class="mt-2 w-full bg-black">
		<track kind="captions" src="" label="Captions" />
		Your browser does not support video playback.
	</video>
{/if}
