<script lang="ts">
	import { annotations as annoApi } from '$lib/api';
	import type { MediaStore, Annotation } from '$lib/api';
	import { selectedGroupMedia, dateLocale } from '$lib/stores';

	type MediaTypeFilter = 'all' | 'audio' | 'video' | 'image';
	type SearchTarget = 'media' | 'annotations';

	const AUDIO_EXTS = new Set(['mp3', 'ogg', 'wav', 'flac', 'aac', 'm4a', 'wma', 'opus']);
	const VIDEO_EXTS = new Set(['mp4', 'webm', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'm4v']);
	const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff']);

	function mediaTypeOf(ext: string): 'audio' | 'video' | 'image' | 'other' {
		const e = ext.toLowerCase();
		if (AUDIO_EXTS.has(e)) return 'audio';
		if (VIDEO_EXTS.has(e)) return 'video';
		if (IMAGE_EXTS.has(e)) return 'image';
		return 'other';
	}

	interface Props {
		sortedRecordings?: MediaStore[];
		filteredRecordings?: MediaStore[];
		groupId?: number;
	}
	let { sortedRecordings = $bindable([]), filteredRecordings = $bindable([]), groupId }: Props = $props();

	let sortOrder = $state<'newest' | 'oldest' | 'ascending' | 'descending'>('newest');
	let searchQuery = $state('');
	let searchBy = $state<'name' | 'tags'>('name');
	let mediaTypeFilter = $state<MediaTypeFilter>('all');
	let searchTarget = $state<SearchTarget>('media');

	// Annotation search results
	let annoResults = $state<Annotation[]>([]);
	let annoLoading = $state(false);
	let annoError = $state<string | null>(null);
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;

	const sorted = $derived(
		[...$selectedGroupMedia].sort((a, b) => {
			if (sortOrder === 'newest')
				return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
			if (sortOrder === 'oldest')
				return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
			if (sortOrder === 'ascending') return a.name.localeCompare(b.name);
			return b.name.localeCompare(a.name);
		})
	);

	const filtered = $derived(
		sorted.filter((r) => {
			if (mediaTypeFilter !== 'all' && mediaTypeOf(r.file_extension) !== mediaTypeFilter) {
				return false;
			}
			if (searchBy === 'name') return r.name.toLowerCase().includes(searchQuery.toLowerCase());
			const searchTags = searchQuery
				.split(',')
				.map((t) => t.trim().toLowerCase())
				.filter(Boolean);
			return searchTags.every((st) => r.tags.some((t) => t.name.toLowerCase().includes(st)));
		})
	);

	$effect(() => {
		sortedRecordings = sorted;
	});
	$effect(() => {
		filteredRecordings = filtered;
	});

	function handleTargetSwitch(target: SearchTarget): void {
		searchTarget = target;
		if (target === 'annotations' && searchQuery.trim()) {
			void searchAnnotations();
		} else {
			annoResults = [];
		}
	}

	function handleAnnoSearchInput(): void {
		if (searchTarget !== 'annotations') return;
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			void searchAnnotations();
		}, 400);
	}

	async function searchAnnotations(): Promise<void> {
		if (!searchQuery.trim()) {
			annoResults = [];
			return;
		}
		annoLoading = true;
		annoError = null;
		try {
			const params: Parameters<typeof annoApi.list>[0] = {
				search: searchQuery.trim()
			};
			if (groupId !== undefined) params.group = groupId;
			const { data } = await annoApi.list(params);
			annoResults = data.results;
		} catch {
			annoError = 'Failed to search annotations.';
		} finally {
			annoLoading = false;
		}
	}

	function typeBadgeClass(t: string): string {
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

<div class="sticky mb-6 w-full flex-1 overflow-y-auto px-3 md:my-6 md:w-3/4">
	<!-- Search target tabs -->
	<div class="mb-3 flex border-b border-gray-300">
		<button
			class="px-4 py-2 font-body text-sm tracking-wide {searchTarget === 'media' ? 'border-b-2 border-gray-900 font-semibold' : 'text-gray-500 hover:text-gray-700'}"
			onclick={() => handleTargetSwitch('media')}
		>Media</button>
		<button
			class="px-4 py-2 font-body text-sm tracking-wide {searchTarget === 'annotations' ? 'border-b-2 border-gray-900 font-semibold' : 'text-gray-500 hover:text-gray-700'}"
			onclick={() => handleTargetSwitch('annotations')}
		>Annotations</button>
	</div>

	<div class="my-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
		<div class="flex w-full items-center gap-2">
			{#if searchTarget === 'media'}
				<select
					bind:value={searchBy}
					class="w-1/5 border border-gray-300 px-2 py-1 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
				>
					<option value="name">Name</option>
					<option value="tags">Tags</option>
				</select>
			{/if}
			<input
				type="text"
				placeholder={searchTarget === 'media' ? 'Search...' : 'Search annotations...'}
				bind:value={searchQuery}
				oninput={handleAnnoSearchInput}
				class="{searchTarget === 'media' ? 'w-4/5' : 'w-full'} border border-gray-300 px-4 py-2 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
			/>
		</div>
		{#if searchTarget === 'media'}
			<div class="flex items-center gap-3">
				<div class="flex items-center">
					<label for="mediaType" class="mr-2 font-body text-xs font-medium text-gray-600">Type:</label>
					<select
						id="mediaType"
						bind:value={mediaTypeFilter}
						class="border border-gray-300 px-2 py-1 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
					>
						<option value="all">All</option>
						<option value="audio">Audio</option>
						<option value="video">Video</option>
						<option value="image">Image</option>
					</select>
				</div>
				<div class="flex items-center">
					<label for="sortOrder" class="mr-2 font-body text-xs font-medium text-gray-600">Sort:</label>
					<select
						id="sortOrder"
						bind:value={sortOrder}
						class="border border-gray-300 px-2 py-1 font-body text-sm focus:outline-none focus:ring focus:ring-gray-200"
					>
						<option value="newest">Newest to Oldest</option>
						<option value="oldest">Oldest to Newest</option>
						<option value="ascending">Name Ascending</option>
						<option value="descending">Name Descending</option>
					</select>
				</div>
			</div>
		{/if}
	</div>

	<!-- Annotation search results (shown when Annotations tab active) -->
	{#if searchTarget === 'annotations'}
		{#if annoLoading}
			<p class="py-4 text-center font-body text-sm text-gray-500">Searching...</p>
		{:else if annoError}
			<p class="py-4 text-center font-body text-sm text-red-700">{annoError}</p>
		{:else if annoResults.length > 0}
			<div class="divide-y divide-gray-200">
				{#each annoResults as anno}
					<div class="py-3">
						<div class="flex items-start gap-2">
							<span class="shrink-0 px-1.5 py-0.5 font-body text-xs uppercase tracking-wider {typeBadgeClass(anno.annotation_type)}">
								{anno.annotation_type}
							</span>
							<p class="line-clamp-2 font-body text-sm text-gray-800">
								{anno.annotation_text || '(no text)'}
							</p>
						</div>
						<div class="mt-1 flex items-center gap-2">
							<a
								href="/groups/0/media/{anno.media_reference_id}"
								class="font-body text-xs text-gray-600 underline-offset-2 hover:underline"
							>View media</a>
							<span class="font-body text-xs text-gray-400">
								{new Date(anno.created_at).toLocaleDateString($dateLocale, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</span>
						</div>
					</div>
				{/each}
			</div>
		{:else if searchQuery.trim()}
			<p class="py-4 text-center font-body text-sm text-gray-400">No annotations match your search.</p>
		{/if}
	{/if}
</div>
