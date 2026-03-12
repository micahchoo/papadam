<script lang="ts">
	import DOMPurify from 'dompurify';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { groups, archive, importexport } from '$lib/api';
	import type { MediaStore } from '$lib/api';
	import { selectedGroup, groupMediaList, dateLocale, isAuthenticated } from '$lib/stores';

	let exportMsg = $state<string | null>(null);
	let exportError = $state<string | null>(null);
	let exporting = $state(false);

	async function requestExport(): Promise<void> {
		exporting = true;
		exportMsg = null;
		exportError = null;
		try {
			await importexport.requestExport(groupId);
			exportMsg = 'Export requested — check Settings for status.';
		} catch {
			exportError = 'Failed to request export.';
		} finally {
			exporting = false;
		}
	}
	import UploadMediaModal from '$lib/components/UploadMediaModal.svelte';
	import SearchSort from '$lib/components/SearchSort.svelte';

	let error = $state('');
	let loading = $state(true);
	let showUploadModal = $state(false);
	let sortedRecordings = $state<MediaStore[]>([]);
	let filteredRecordings = $state<MediaStore[]>([]);
	let hasMore = $state(false);
	let currentPage = $state(1);
	let loadingMore = $state(false);
	let loadMoreError = $state<string | null>(null);

	const groupId = $derived(parseInt($page.params['id'] ?? '0', 10));

	onMount(async () => {
		try {
			const [groupResp, archiveResp] = await Promise.all([
				groups.get(groupId),
				archive.list({ searchFrom: 'selected_collections', searchCollections: String(groupId) })
			]);
			selectedGroup.set(groupResp.data);
			groupMediaList.set(archiveResp.data.results);
			hasMore = archiveResp.data.next !== null;
		} catch {
			error = 'Failed to load collection.';
		} finally {
			loading = false;
		}
	});

	async function loadMore(): Promise<void> {
		loadingMore = true;
		loadMoreError = null;
		try {
			currentPage += 1;
			const { data } = await archive.list({
				searchFrom: 'selected_collections',
				searchCollections: String(groupId),
				page: currentPage
			});
			groupMediaList.update((list) => [...list, ...data.results]);
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
</script>

<div class="mx-auto max-w-6xl px-4 py-6">
	{#if error}
		<p class="text-red-700">{error}</p>
	{:else if loading}
		<p class="text-gray-500">Loading...</p>
	{:else if $selectedGroup}
		<!-- Masthead-style collection header -->
		<header class="mb-6 border-b-2 border-gray-900 pb-4">
			<h1 class="font-heading text-4xl font-black tracking-tight">{$selectedGroup.name}</h1>
			<p class="mt-2 max-w-2xl font-body text-gray-600">
				{@html DOMPurify.sanitize($selectedGroup.description)}
			</p>
			{#if $isAuthenticated}
				<div class="mt-4 flex items-center gap-3">
					<button
						class="border border-gray-900 px-5 py-2 font-body text-sm font-medium tracking-wide hover:bg-gray-900 hover:text-white"
						onclick={() => (showUploadModal = true)}
					>
						Upload Media
					</button>
					<button
						class="border border-gray-300 px-4 py-2 font-body text-xs tracking-wide hover:bg-gray-100"
						disabled={exporting}
						onclick={() => void requestExport()}
					>
						{exporting ? 'Exporting...' : 'Export'}
					</button>
				</div>
				{#if exportMsg}
					<p class="mt-2 font-body text-sm text-green-700">{exportMsg}</p>
				{/if}
				{#if exportError}
					<p class="mt-2 font-body text-sm text-red-700">{exportError}</p>
				{/if}
			{/if}
		</header>

		<SearchSort bind:sortedRecordings bind:filteredRecordings {groupId} />

		{#if $groupMediaList.length === 0}
			<p class="py-12 text-center font-body text-sm text-gray-400">No media uploaded yet.</p>
		{:else if filteredRecordings.length === 0}
			<p class="py-12 text-center font-body text-sm text-gray-400">No results match your search.</p>
		{:else}
			<!-- Newspaper column grid -->
			<div class="mt-6 grid grid-cols-1 gap-x-8 gap-y-10 md:grid-cols-2 lg:grid-cols-3">
				{#each filteredRecordings as recording, i}
					<article
						class="group border-t border-gray-300 pt-4"
						class:md:col-span-2={i === 0}
						class:lg:col-span-2={i === 0}
					>
						<a href="{groupId}/media/{recording.uuid}" class="block">
							<h2
								class="font-heading font-bold leading-tight text-gray-900 group-hover:underline"
								class:text-2xl={i === 0}
								class:text-lg={i !== 0}
							>
								{recording.name}
							</h2>
						</a>
						<p class="mt-1 font-body text-xs text-gray-500">
							{recording.created_by?.username ?? 'Unknown'}
							<span class="mx-1">&middot;</span>
							{new Date(recording.created_at).toLocaleDateString($dateLocale, {
								day: 'numeric',
								month: 'short',
								year: 'numeric'
							})}
						</p>
						{#if recording.description}
							<p
								class="mt-2 line-clamp-3 font-body text-sm leading-relaxed text-gray-700"
								class:line-clamp-4={i === 0}
							>
								{recording.description}
							</p>
						{/if}
						{#if recording.tags.length > 0}
							<div class="mt-2 flex flex-wrap gap-1">
								{#each recording.tags.slice(0, 4) as tag}
									{#if tag.name && tag.count > 0 && tag.name.length <= 30}
										<span class="font-body text-xs uppercase tracking-wider text-gray-500">
											{tag.name}
										</span>
									{/if}
								{/each}
							</div>
						{/if}
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
	{/if}
</div>

{#if showUploadModal}
	<UploadMediaModal bind:showUploadModal />
{/if}
