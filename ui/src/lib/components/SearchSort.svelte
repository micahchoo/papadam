<script lang="ts">
	import type { MediaStore } from '$lib/api';
	import { selectedGroupMedia } from '$lib/stores';

	interface Props {
		sortedRecordings?: MediaStore[];
		filteredRecordings?: MediaStore[];
	}
	let { sortedRecordings = $bindable([]), filteredRecordings = $bindable([]) }: Props = $props();

	let sortOrder = $state<'newest' | 'oldest' | 'ascending' | 'descending'>('newest');
	let searchQuery = $state('');
	let searchBy = $state<'name' | 'tags'>('name');

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
</script>

<div class="sticky mb-6 w-full flex-1 overflow-y-auto px-3 md:my-6 md:w-3/4">
	<div class="my-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
		<div class="flex w-full items-center gap-2">
			<select
				bind:value={searchBy}
				class="w-1/5 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			>
				<option value="name">Name</option>
				<option value="tags">Tags</option>
			</select>
			<input
				type="text"
				placeholder="Search..."
				bind:value={searchQuery}
				class="w-4/5 rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>
		</div>
		<div class="flex items-center">
			<label for="sortOrder" class="mr-2 text-xs font-medium text-gray-600">Sort:</label>
			<select
				id="sortOrder"
				bind:value={sortOrder}
				class="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			>
				<option value="newest">Newest to Oldest</option>
				<option value="oldest">Oldest to Newest</option>
				<option value="ascending">Name Ascending</option>
				<option value="descending">Name Descending</option>
			</select>
		</div>
	</div>
</div>
