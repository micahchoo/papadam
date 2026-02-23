<script>
	import { page } from '$app/stores';
	import { selectedGroupMedia, selectedGroupDetails } from '$lib/stores';
	import UploadMediaModal from '$lib/components/UploadMediaModal.svelte';
	import SearchSort from '$lib/components/SearchSort.svelte';

	export let data;
	let error;

	let showUploadModal = false;

	let sortedRecordings = [];
	let filteredRecordings = [];

	$: $selectedGroupDetails = data.groupDetails;
	$: $selectedGroupMedia = data.recordings;
</script>

<div class="mx-auto flex h-full max-w-5xl flex-col md:h-screen md:flex-row">
	<!-- Left Section: Group Details -->
	<div class="w-full flex-shrink-0 p-6 md:w-1/4">
		{#if error}
			<p class="text-red-500">{error}</p>
		{:else if $selectedGroupDetails}
			<div>
				<h1 class="text-xl font-bold">{$selectedGroupDetails.name}</h1>
				<p class="mt-2 text-gray-600">{@html $selectedGroupDetails.description}</p>
				<div class="mt-6">
					<button
						class="w-full rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
						on:click={() => (showUploadModal = true)}
					>
						Upload Media
					</button>
				</div>
			</div>
		{:else}
			<p class="text-gray-500">Loading collection details...</p>
		{/if}
	</div>

	<!-- Right Section: Scrollable Media Cards -->
	<div class="mb-6 w-full flex-1 overflow-y-auto px-3 md:my-6 md:w-3/4">
	<SearchSort bind:sortedRecordings bind:filteredRecordings></SearchSort>
		{#if $selectedGroupMedia && $selectedGroupMedia.length > 0}
		<div class="grid grid-cols-1 gap-y-4">
			{#each filteredRecordings as recording}
				<div class="relative min-h-40 bg-white">
					<div class="flex flex-col px-4 pt-4 md:flex-row md:justify-between">
						<h2 class="mb-2 text-xl font-semibold">{recording.name}</h2>
						<p class="text-sm text-gray-500">
							{new Date(recording.created_at).toLocaleDateString('en-GB')}
						</p>
					</div>
					<p class="my-5 mt-2 h-12 overflow-hidden px-4 text-gray-600">{recording.description}</p>
					<div class="px-4 md:p-6">
						{#each recording.tags.slice(0, 3) as tag}
							{#if tag.name && tag.count > 0 && tag.name.length <= 30}
								<span
									class="mr-1 inline-flex bg-blue-200 px-2 py-1 text-xs font-semibold uppercase text-blue-500"
								>
									{tag.name}
								</span>
							{/if}
						{/each}
					</div>
					<a href="{$page.params.id}/media/{recording.uuid}">
						<button
							class="mt-5 w-full bg-blue-950 px-4 py-4 text-white hover:bg-blue-600 md:absolute md:bottom-0 md:right-0 md:w-fit"
						>
							View Media
						</button>
					</a>
				</div>
			{/each}
		</div>
	{:else}
		<p class="text-gray-500">No media found for the search term.</p>
	{/if}
</div>
</div>


<!-- Upload Modal -->
{#if showUploadModal}
	<UploadMediaModal bind:showUploadModal />
{/if}
