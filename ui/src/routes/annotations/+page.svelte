<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { annotations as annoApi, groups } from '$lib/api';
	import type { Annotation, AnnotationType, Group } from '$lib/api';
	import { dateLocale } from '$lib/stores';

	let annotationList = $state<Annotation[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let loadingMore = $state(false);
	let hasMore = $state(false);
	let currentPage = $state(1);

	// Filters
	let groupList = $state<Group[]>([]);
	let filterGroup = $state(0);
	let filterSearch = $state('');
	let filterType = $state<AnnotationType | ''>('');

	// Debounce search
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;

	onMount(async () => {
		// Read initial page from query param
		const qPage = $page.url.searchParams.get('page');
		if (qPage) currentPage = parseInt(qPage, 10) || 1;

		try {
			const [annoResp, groupResp] = await Promise.all([
				annoApi.list({ page: currentPage }),
				groups.list()
			]);
			annotationList = annoResp.data.results;
			hasMore = annoResp.data.next !== null;
			groupList = groupResp.data.results;
		} catch {
			error = 'Failed to load annotations.';
		} finally {
			loading = false;
		}
	});

	async function fetchAnnotations(reset = false): Promise<void> {
		if (reset) {
			currentPage = 1;
			annotationList = [];
		}
		loading = reset;
		loadingMore = !reset;
		error = null;
		try {
			const params: Record<string, unknown> = { page: currentPage };
			if (filterGroup) params['group'] = filterGroup;
			if (filterSearch.trim()) params['search'] = filterSearch.trim();
			// annotation_type filter passed as searchWhere if set
			const resp = await annoApi.list(params as Parameters<typeof annoApi.list>[0]);
			if (reset) {
				annotationList = resp.data.results;
			} else {
				annotationList = [...annotationList, ...resp.data.results];
			}
			hasMore = resp.data.next !== null;
		} catch {
			error = 'Failed to load annotations.';
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	function handleFilterChange(): void {
		void fetchAnnotations(true);
	}

	function handleSearchInput(): void {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			void fetchAnnotations(true);
		}, 400);
	}

	async function loadMore(): Promise<void> {
		currentPage += 1;
		await fetchAnnotations(false);
	}

	function retryLoad(): void {
		error = null;
		void fetchAnnotations(true);
	}

	function typeBadgeClass(t: AnnotationType): string {
		switch (t) {
			case 'text': return 'bg-gray-100 text-gray-700';
			case 'image': return 'bg-amber-50 text-amber-700';
			case 'audio': return 'bg-emerald-50 text-emerald-700';
			case 'video': return 'bg-indigo-50 text-indigo-700';
			case 'media_ref': return 'bg-purple-50 text-purple-700';
			default: return 'bg-gray-100 text-gray-600';
		}
	}
</script>

<svelte:head>
	<title>Annotations</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-6">
	<header class="mb-6 border-b-2 border-gray-900 pb-4">
		<h1 class="font-heading text-4xl font-black tracking-tight">Annotations</h1>
	</header>

	<!-- Filters -->
	<div class="mb-6 flex flex-col gap-3 md:flex-row md:items-end">
		<label class="flex-1">
			<span class="font-body text-xs text-gray-600">Search</span>
			<input
				type="text"
				bind:value={filterSearch}
				oninput={handleSearchInput}
				placeholder="Search annotations..."
				class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent"
			/>
		</label>
		<label>
			<span class="font-body text-xs text-gray-600">Collection</span>
			<select
				bind:value={filterGroup}
				onchange={handleFilterChange}
				class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
			>
				<option value={0}>All collections</option>
				{#each groupList as g}
					<option value={g.id}>{g.name}</option>
				{/each}
			</select>
		</label>
		<label>
			<span class="font-body text-xs text-gray-600">Type</span>
			<select
				bind:value={filterType}
				onchange={handleFilterChange}
				class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
			>
				<option value="">All types</option>
				<option value="text">Text</option>
				<option value="image">Image</option>
				<option value="audio">Audio</option>
				<option value="video">Video</option>
				<option value="media_ref">Media Ref</option>
			</select>
		</label>
	</div>

	<!-- Content -->
	{#if error}
		<div class="py-12 text-center">
			<p class="mb-3 font-body text-sm text-red-700">{error}</p>
			<button
				class="border border-gray-900 px-4 py-2 font-body text-sm hover:bg-gray-900 hover:text-white"
				onclick={retryLoad}
			>Retry</button>
		</div>
	{:else if loading}
		<p class="py-12 text-center font-body text-sm text-gray-500">Loading annotations...</p>
	{:else if annotationList.length === 0}
		<p class="py-12 text-center font-body text-sm text-gray-400">No annotations found.</p>
	{:else}
		<div class="divide-y divide-gray-200">
			{#each annotationList as anno}
				<article class="py-4">
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0 flex-1">
							<p class="line-clamp-2 font-body text-sm leading-relaxed text-gray-800">
								{anno.annotation_text || '(no text)'}
							</p>
							<div class="mt-2 flex flex-wrap items-center gap-2">
								<span class="px-2 py-0.5 font-body text-xs uppercase tracking-wider {typeBadgeClass(anno.annotation_type)}">
									{anno.annotation_type}
								</span>
								{#each anno.tags.slice(0, 4) as tag}
									<span class="border border-gray-200 px-1.5 py-0.5 font-body text-xs text-gray-500">
										{tag.name}
									</span>
								{/each}
							</div>
						</div>
						<div class="shrink-0 text-right">
							<p class="font-body text-xs text-gray-500">
								{anno.created_by?.username ?? 'Unknown'}
							</p>
							<p class="font-body text-xs text-gray-400">
								{new Date(anno.created_at).toLocaleDateString($dateLocale, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</p>
							<a
								href="/groups/0/media/{anno.media_reference_id}"
								class="mt-1 inline-block font-body text-xs text-gray-600 underline-offset-2 hover:underline"
							>View media</a>
						</div>
					</div>
				</article>
			{/each}
		</div>

		{#if hasMore}
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
