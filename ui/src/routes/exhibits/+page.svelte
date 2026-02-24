<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { exhibits } from '$lib/api';
	import type { Exhibit } from '$lib/api';
	import { isAuthenticated, selectedGroup, exhibitEnabled } from '$lib/stores';

	let exhibitList = $state<Exhibit[]>([]);
	let loading = $state(true);
	let error = $state('');

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
		} catch {
			error = 'Failed to load exhibits.';
		} finally {
			loading = false;
		}
	});

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
		} catch {
			createError = 'Failed to create exhibit.';
		} finally {
			creating = false;
		}
	}
</script>

<div class="mx-auto max-w-4xl px-4 py-8">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="text-2xl font-bold text-gray-800">Exhibits</h1>
		{#if $isAuthenticated}
			<button
				onclick={() => {
					showCreate = !showCreate;
				}}
				class="rounded bg-blue-950 px-4 py-2 text-sm text-white hover:bg-blue-700"
			>
				{showCreate ? 'Cancel' : 'New Exhibit'}
			</button>
		{/if}
	</div>

	{#if showCreate}
		<div class="mb-6 rounded-lg bg-white p-6 shadow-md">
			<h2 class="mb-4 text-lg font-semibold text-gray-700">Create Exhibit</h2>
			{#if createError}
				<p class="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{createError}</p>
			{/if}

			<label class="mb-1 block text-sm font-medium text-gray-600" for="ex-title">Title</label>
			<input
				id="ex-title"
				type="text"
				bind:value={newTitle}
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="ex-desc">Description</label>
			<textarea
				id="ex-desc"
				bind:value={newDescription}
				rows="3"
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			></textarea>

			<label class="mb-4 flex items-center gap-2 text-sm text-gray-600">
				<input type="checkbox" bind:checked={newIsPublic} class="rounded" />
				Public exhibit
			</label>

			<button
				onclick={() => void handleCreate()}
				disabled={creating}
				class="rounded bg-blue-950 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
			>
				{creating ? 'Creating…' : 'Create'}
			</button>
		</div>
	{/if}

	{#if error}
		<p class="text-red-600">{error}</p>
	{:else if loading}
		<p class="text-gray-500">Loading exhibits…</p>
	{:else if exhibitList.length === 0}
		<p class="text-gray-500">No exhibits yet.</p>
	{:else}
		<ul class="space-y-4">
			{#each exhibitList as exhibit}
				<li class="rounded-lg bg-white p-5 shadow-sm">
					<div class="flex items-start justify-between">
						<div>
							<h2 class="text-lg font-semibold text-gray-800">{exhibit.title}</h2>
							{#if exhibit.description}
								<p class="mt-1 text-sm text-gray-600">{exhibit.description}</p>
							{/if}
							<p class="mt-2 text-xs text-gray-400">
								{exhibit.blocks.length} block{exhibit.blocks.length !== 1 ? 's' : ''}
								&nbsp;·&nbsp;
								{exhibit.is_public ? 'Public' : 'Private'}
							</p>
						</div>
						<div class="ml-4 flex shrink-0 gap-3">
							<a href="/exhibits/{exhibit.uuid}" class="text-sm text-blue-600 hover:underline"
								>View</a
							>
							{#if $isAuthenticated}
								<a
									href="/exhibits/{exhibit.uuid}/edit"
									class="text-sm text-gray-500 hover:underline">Edit</a
								>
							{/if}
						</div>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>
