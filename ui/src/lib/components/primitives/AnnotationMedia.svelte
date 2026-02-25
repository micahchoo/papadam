<script lang="ts">
	import { onDestroy } from 'svelte';
	import { attachHls } from '$lib/hls';
	import type { HlsHandle } from '$lib/hls';

	interface Props {
		src: string;
		mediaType: 'audio' | 'video';
		/** HLS startLevel: -1 = auto, 0 = lowest, Infinity = highest. */
		hlsStartLevel?: number;
	}

	const { src, mediaType, hlsStartLevel = -1 }: Props = $props();

	let mediaEl = $state<HTMLMediaElement | null>(null);
	let hlsHandle: HlsHandle | null = null;

	$effect(() => {
		if (mediaEl && src) {
			hlsHandle?.destroy();
			hlsHandle = attachHls(mediaEl, src, hlsStartLevel);
		}
		return () => {
			hlsHandle?.destroy();
			hlsHandle = null;
		};
	});

	onDestroy(() => {
		hlsHandle?.destroy();
	});
</script>

{#if mediaType === 'audio'}
	<audio bind:this={mediaEl} controls class="mt-2 w-full">
		Your browser does not support audio playback.
	</audio>
{:else}
	<video bind:this={mediaEl} controls class="mt-2 w-full bg-black">
		<track kind="captions" />
		Your browser does not support video playback.
	</video>
{/if}
