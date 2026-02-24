<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { exhibits } from '$lib/api';
	import type { ExhibitBlock, ExhibitBlockType } from '$lib/api';
	import { isAuthenticated, exhibitEnabled } from '$lib/stores';

	const exhibitUuid = $derived($page.params['uuid'] ?? '');

	// Exhibit metadata
	let editTitle = $state('');
	let editDescription = $state('');
	let editIsPublic = $state(true);
	let saving = $state(false);
	let saveError = $state('');
	let saveSuccess = $state(false);

	// Block list
	let blocks = $state<ExhibitBlock[]>([]);

	// Add block form
	let newBlockType = $state<ExhibitBlockType>('media');
	let newBlockUuid = $state('');
	let newBlockCaption = $state('');
	let addingBlock = $state(false);
	let addBlockError = $state('');

	// Delete exhibit
	let deleting = $state(false);

	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		if (!$exhibitEnabled) {
			await goto('/');
			return;
		}
		if (!$isAuthenticated) {
			await goto('/auth/login');
			return;
		}
		try {
			const { data } = await exhibits.get(exhibitUuid);
			editTitle = data.title;
			editDescription = data.description;
			editIsPublic = data.is_public;
			blocks = data.blocks;
		} catch {
			error = 'Exhibit not found.';
		} finally {
			loading = false;
		}
	});

	async function handleSave() {
		saving = true;
		saveError = '';
		saveSuccess = false;
		try {
			await exhibits.update(exhibitUuid, {
				title: editTitle.trim(),
				description: editDescription.trim(),
				is_public: editIsPublic
			});
			saveSuccess = true;
			setTimeout(() => {
				saveSuccess = false;
			}, 2_000);
		} catch {
			saveError = 'Failed to save changes.';
		} finally {
			saving = false;
		}
	}

	async function handleAddBlock() {
		if (!newBlockUuid.trim()) {
			addBlockError = 'UUID is required.';
			return;
		}
		const nextOrder = blocks.length > 0 ? Math.max(...blocks.map((b) => b.order)) + 1 : 0;
		addingBlock = true;
		addBlockError = '';
		try {
			const payload = {
				block_type: newBlockType,
				media_uuid: newBlockType === 'media' ? newBlockUuid.trim() : null,
				annotation_uuid: newBlockType === 'annotation' ? newBlockUuid.trim() : null,
				caption: newBlockCaption.trim(),
				order: nextOrder
			};
			const { data: newBlock } = await exhibits.blocks.create(exhibitUuid, payload);
			blocks = [...blocks, newBlock];
			newBlockUuid = '';
			newBlockCaption = '';
		} catch {
			addBlockError = 'Failed to add block. Check that the UUID is valid.';
		} finally {
			addingBlock = false;
		}
	}

	async function handleDelete() {
		if (!confirm('Delete this exhibit? This cannot be undone.')) return;
		deleting = true;
		try {
			await exhibits.delete(exhibitUuid);
			await goto('/exhibits');
		} catch {
			deleting = false;
			alert('Failed to delete exhibit.');
		}
	}
</script>

{#if loading}
	<div class="flex min-h-[60vh] items-center justify-center">
		<p class="text-gray-500">Loading…</p>
	</div>
{:else if error}
	<div class="flex min-h-[60vh] items-center justify-center">
		<p class="text-red-600">{error}</p>
	</div>
{:else}
	<div class="mx-auto max-w-3xl px-4 py-8">
		<div class="mb-6 flex items-center justify-between">
			<h1 class="text-2xl font-bold text-gray-800">Edit Exhibit</h1>
			<a href="/exhibits/{exhibitUuid}" class="text-sm text-gray-500 hover:underline">← View</a>
		</div>

		<!-- Metadata editor -->
		<section class="mb-8 rounded-lg bg-white p-6 shadow-sm">
			<h2 class="mb-4 text-lg font-semibold text-gray-700">Details</h2>

			{#if saveError}
				<p class="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{saveError}</p>
			{/if}
			{#if saveSuccess}
				<p class="mb-3 rounded bg-green-100 px-3 py-2 text-sm text-green-700">Saved.</p>
			{/if}

			<label class="mb-1 block text-sm font-medium text-gray-600" for="ed-title">Title</label>
			<input
				id="ed-title"
				type="text"
				bind:value={editTitle}
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="ed-desc">Description</label>
			<textarea
				id="ed-desc"
				bind:value={editDescription}
				rows="3"
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			></textarea>

			<label class="mb-4 flex items-center gap-2 text-sm text-gray-600">
				<input type="checkbox" bind:checked={editIsPublic} class="rounded" />
				Public exhibit
			</label>

			<button
				onclick={() => void handleSave()}
				disabled={saving}
				class="rounded bg-blue-950 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
			>
				{saving ? 'Saving…' : 'Save'}
			</button>
		</section>

		<!-- Block list -->
		<section class="mb-8 rounded-lg bg-white p-6 shadow-sm">
			<h2 class="mb-4 text-lg font-semibold text-gray-700">Blocks ({blocks.length})</h2>

			{#if blocks.length === 0}
				<p class="text-sm text-gray-400">No blocks yet. Add one below.</p>
			{:else}
				<ol class="space-y-2">
					{#each blocks as block}
						<li class="flex items-start gap-3 rounded border border-gray-200 p-3">
							<span
								class="shrink-0 rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
							>
								{block.order}
							</span>
							<div class="min-w-0 flex-1">
								<p class="text-sm font-medium capitalize text-gray-700">{block.block_type}</p>
								<p class="truncate text-xs text-gray-400">
									{block.block_type === 'media' ? block.media_uuid : block.annotation_uuid}
								</p>
								{#if block.caption}
									<p class="text-xs italic text-gray-500">{block.caption}</p>
								{/if}
							</div>
						</li>
					{/each}
				</ol>
			{/if}
		</section>

		<!-- Add block -->
		<section class="mb-8 rounded-lg bg-white p-6 shadow-sm">
			<h2 class="mb-4 text-lg font-semibold text-gray-700">Add Block</h2>

			{#if addBlockError}
				<p class="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{addBlockError}</p>
			{/if}

			<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-type">Block type</label>
			<select
				id="blk-type"
				bind:value={newBlockType}
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			>
				<option value="media">Media</option>
				<option value="annotation">Annotation</option>
			</select>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-uuid">
				{newBlockType === 'media' ? 'Media UUID' : 'Annotation UUID'}
			</label>
			<input
				id="blk-uuid"
				type="text"
				bind:value={newBlockUuid}
				placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-caption"
				>Caption (optional)</label
			>
			<input
				id="blk-caption"
				type="text"
				bind:value={newBlockCaption}
				class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
			/>

			<button
				onclick={() => void handleAddBlock()}
				disabled={addingBlock}
				class="rounded bg-blue-950 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
			>
				{addingBlock ? 'Adding…' : 'Add Block'}
			</button>
		</section>

		<!-- Danger zone -->
		<section class="rounded-lg border border-red-200 bg-red-50 p-6">
			<h2 class="mb-3 text-lg font-semibold text-red-700">Danger Zone</h2>
			<button
				onclick={() => void handleDelete()}
				disabled={deleting}
				class="rounded bg-red-500 px-4 py-2 text-sm text-white hover:bg-red-600 disabled:opacity-50"
			>
				{deleting ? 'Deleting…' : 'Delete Exhibit'}
			</button>
		</section>
	</div>
{/if}
