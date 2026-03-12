<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { exhibits } from '$lib/api';
	import type { Exhibit } from '$lib/api';
	import axios from 'axios';
	import { isAuthenticated, selectedGroup, exhibitEnabled, dateLocale } from '$lib/stores';

	let exhibitList = $state<Exhibit[]>([]);
	let loading = $state(true);
	let error = $state('');
	let loadMoreError = $state<string | null>(null);
	let hasMore = $state(false);
	let currentPage = $state(1);
	let loadingMore = $state(false);

	let showCreate = $state(false);
	let newTitle = $state('');
	let newDescription = $state('');
	let newIsPublic = $state(true);
	let creating = $state(false);
	let createError = $state('');

	onMount(async () => {
		if (!$exhibitEnabled) {
			await goto('/');
			return;
		}
		try {
			const { data } = await exhibits.list();
			exhibitList = data.results;
			hasMore = data.next !== null;
		} catch {
			error = 'Failed to load exhibits.';
		} finally {
			loading = false;
		}
	});

	async function loadMore(): Promise<void> {
		loadingMore = true;
		loadMoreError = null;
		try {
			currentPage += 1;
			const { data } = await exhibits.list({ page: currentPage });
			exhibitList = [...exhibitList, ...data.results];
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

	async function handleCreate() {
		if (!newTitle.trim()) {
			createError = 'Title is required.';
			return;
		}
		if (!$selectedGroup) {
			createError = 'Select a collection first (visit Collections).';
			return;
		}
		creating = true;
		createError = '';
		try {
			const { data } = await exhibits.create({
				title: newTitle.trim(),
				description: newDescription.trim(),
				is_public: newIsPublic,
				group: $selectedGroup.id
			});
			exhibitList = [data, ...exhibitList];
			showCreate = false;
			newTitle = '';
			newDescription = '';
			newIsPublic = true;
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const data = err.response.data as Record<string, string[] | string>;
				const detail = typeof data['detail'] === 'string' ? data['detail'] : null;
				createError = detail ?? 'Failed to create exhibit.';
			} else {
				createError = 'Failed to create exhibit.';
			}
		} finally {
			creating = false;
		}
	}
</script>

<div class="mx-auto max-w-5xl px-4 py-8">
	<!-- Masthead -->
	<header class="mb-8 border-b-2 border-gray-900 pb-4">
		<div class="flex items-baseline justify-between">
			<h1 class="font-heading text-4xl font-black tracking-tight">Exhibits</h1>
			{#if $isAuthenticated}
				<button
					onclick={() => { showCreate = !showCreate; }}
					class="border border-gray-900 px-5 py-2 font-body text-sm font-medium tracking-wide hover:bg-gray-900 hover:text-white"
				>
					{showCreate ? 'Cancel' : 'New Exhibit'}
				</button>
			{/if}
		</div>
	</header>

	{#if showCreate}
		<div class="mb-8 border border-gray-200 p-6">
			<h2 class="mb-4 font-heading text-xl font-bold">Create Exhibit</h2>
			{#if createError}
				<p class="mb-3 border border-red-300 bg-red-50 px-3 py-2 font-body text-sm text-red-700">{createError}</p>
			{/if}

			<label class="mb-1 block font-body text-sm font-medium text-gray-600" for="ex-title">Title</label>
			<input
				id="ex-title"
				type="text"
				bind:value={newTitle}
				class="mb-4 w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
			/>

			<label class="mb-1 block font-body text-sm font-medium text-gray-600" for="ex-desc">Description</label>
			<textarea
				id="ex-desc"
				bind:value={newDescription}
				rows="3"
				class="mb-4 w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
			></textarea>

			<label class="mb-4 flex items-center gap-2 font-body text-sm text-gray-600">
				<input type="checkbox" bind:checked={newIsPublic} />
				Public exhibit
			</label>

			<button
				onclick={() => void handleCreate()}
				disabled={creating}
				class="bg-brand-primary px-5 py-2 font-body text-sm text-white hover:opacity-90 disabled:opacity-50"
			>
				{creating ? 'Creating...' : 'Create'}
			</button>
		</div>
	{/if}

	{#if error}
		<p class="font-body text-red-700">{error}</p>
	{:else if loading}
		<p class="py-12 text-center font-body text-sm text-gray-500">Loading exhibits...</p>
	{:else if exhibitList.length === 0}
		<p class="py-12 text-center font-body text-sm text-gray-400">No exhibits yet.</p>
	{:else}
		<!-- Magazine-style feature spread -->
		<div class="grid grid-cols-1 gap-x-8 gap-y-10 md:grid-cols-2">
			{#each exhibitList as exhibit, i}
				<article
					class="border-t border-gray-300 pt-4"
					class:md:col-span-2={i === 0}
				>
					<div class="flex items-start justify-between">
						<div>
							<h2
								class="font-heading font-bold leading-tight text-gray-900"
								class:text-3xl={i === 0}
								class:text-xl={i !== 0}
							>
								<a href="/exhibits/{exhibit.uuid}" class="hover:underline">
									{exhibit.title}
								</a>
							</h2>
							{#if exhibit.description}
								<p
									class="mt-2 font-body leading-relaxed text-gray-600"
									class:text-base={i === 0}
									class:text-sm={i !== 0}
									class:line-clamp-3={i !== 0}
								>
									{exhibit.description}
								</p>
							{/if}
							<p class="mt-2 font-body text-xs text-gray-400">
								{exhibit.blocks.length} block{exhibit.blocks.length !== 1 ? 's' : ''}
								<span class="mx-1">&middot;</span>
								{exhibit.is_public ? 'Public' : 'Private'}
								<span class="mx-1">&middot;</span>
								{new Date(exhibit.created_at).toLocaleDateString($dateLocale, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</p>
						</div>
						<div class="ml-4 flex shrink-0 gap-3">
							<a href="/exhibits/{exhibit.uuid}" class="font-body text-sm text-gray-600 underline-offset-2 hover:underline">View</a>
							{#if $isAuthenticated}
								<a href="/exhibits/{exhibit.uuid}/edit" class="font-body text-sm text-gray-500 underline-offset-2 hover:underline">Edit</a>
							{/if}
						</div>
					</div>
				</article>
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
