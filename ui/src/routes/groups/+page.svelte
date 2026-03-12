<script lang="ts">
	import DOMPurify from 'dompurify';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { groups } from '$lib/api';
	import type { Group } from '$lib/api';

	const COLORS = [
		'bg-brand-primary',
		'bg-brand-accent',
		'bg-brand-primary opacity-80',
		'bg-brand-accent opacity-80',
		'bg-brand-primary opacity-60',
		'bg-brand-accent opacity-60',
		'bg-brand-primary opacity-40'
	] as const;

	let collections = $state<Group[]>([]);
	let loading = $state(true);
	let error = $state('');
	let hasMore = $state(false);
	let currentPage = $state(1);
	let loadingMore = $state(false);
	let loadMoreError = $state<string | null>(null);

	onMount(async () => {
		try {
			const { data } = await groups.list();
			collections = data.results;
			hasMore = data.next !== null;
		} catch {
			error = 'Failed to load collections.';
		} finally {
			loading = false;
		}
	});

	async function loadMore(): Promise<void> {
		loadingMore = true;
		loadMoreError = null;
		try {
			currentPage += 1;
			const { data } = await groups.list({ page: currentPage });
			collections = [...collections, ...data.results];
			hasMore = data.next !== null;
		} catch {
			currentPage -= 1;
			loadMoreError = 'Failed to load more — tap to retry';
		} finally {
			loadingMore = false;
		}
	}

	function retryLoadMore(): void {
		loadMoreError = null;
		void loadMore();
	}

	async function handleClick(id: number) {
		loading = true;
		await goto(`/groups/${id}`);
		loading = false;
	}
</script>

<div class="container relative mx-auto p-6">
	<h1 class="mx-auto mb-6 max-w-5xl font-heading text-3xl font-black tracking-tight">My Collections</h1>
	{#if error}
		<p class="font-body text-red-700">{error}</p>
	{:else if loading}
		<div class="flex min-h-[40vh] items-center justify-center">
			<div
				class="loader h-12 w-12 rounded-full border-4 border-t-4 border-gray-200 ease-linear"
			></div>
		</div>
	{:else if collections.length === 0}
		<p class="font-body text-gray-500">No collections found.</p>
	{:else}
		<div class="mx-auto grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-2">
			{#each collections as collection, index}
				<div
					class="flex cursor-pointer flex-col bg-white shadow-md transition-shadow hover:shadow-lg"
					role="button"
					tabindex="0"
					onclick={() => void handleClick(collection.id)}
					onkeydown={(e) => {
						if (e.key === 'Enter') void handleClick(collection.id);
					}}
				>
					<div class={`h-60 w-full ${COLORS[index % COLORS.length] ?? 'bg-gray-500'}`}></div>
					<div class="flex flex-col items-center justify-center p-5 text-center">
						<h2 class="font-heading text-xl font-bold">{collection.name}</h2>
						<!-- eslint-disable-next-line svelte/no-at-html-tags -->
						<p class="mt-2 font-body text-gray-600">{@html DOMPurify.sanitize(collection.description)}</p>
					</div>
				</div>
			{/each}
		</div>

		{#if loadMoreError}
			<div class="mt-6 text-center">
				<button
					class="font-body text-sm text-red-600 underline-offset-2 hover:underline"
					onclick={retryLoadMore}
				>{loadMoreError}</button>
			</div>
		{:else if hasMore}
			<div class="mt-6 text-center">
				<button
					onclick={() => void loadMore()}
					disabled={loadingMore}
					class="border border-gray-900 px-6 py-2 font-body text-sm tracking-wide hover:bg-gray-900 hover:text-white disabled:opacity-50"
				>
					{loadingMore ? 'Loading...' : 'Load More'}
				</button>
			</div>
		{/if}
	{/if}
</div>

<style>
	.loader {
		border-top-color: var(--brand-accent);
		animation: spinner 0.6s linear infinite;
	}
	@keyframes spinner {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
