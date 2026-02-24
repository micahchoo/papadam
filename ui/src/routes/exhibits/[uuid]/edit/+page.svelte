<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { archive, exhibits } from '$lib/api';
	import type { ExhibitBlock, ExhibitBlockType, MediaStore } from '$lib/api';
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
	// For media type: pick from loaded list; for annotation type: type UUID
	let selectedMediaUuid = $state('');
	let newAnnotationUuid = $state('');
	let newBlockCaption = $state('');
	let addingBlock = $state(false);
	let addBlockError = $state('');

	// Group media picker
	let groupMedia = $state<MediaStore[]>([]);
	let mediaSearch = $state('');
	const filteredMedia = $derived(
		mediaSearch.trim()
			? groupMedia.filter((m) => m.name.toLowerCase().includes(mediaSearch.toLowerCase()))
			: groupMedia
	);

	// Block deletion
	let deletingBlockId = $state<number | null>(null);
	let blockActionError = $state('');

	// Block reorder
	let reordering = $state(false);

	// Delete exhibit
	let deleting = $state(false);
	let deleteError = $state('');
	let showDeleteConfirm = $state(false);

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

			// Load group media for the picker (up to 100 items)
			if (data.group) {
				const mediaResp = await archive.list({
					searchFrom: 'selected_collections',
					searchCollections: String(data.group),
					page_size: 100
				});
				groupMedia = mediaResp.data.results;
				const first = groupMedia[0];
				if (first) selectedMediaUuid = first.uuid;
			}
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
		const blockUuid = newBlockType === 'media' ? selectedMediaUuid : newAnnotationUuid.trim();
		if (!blockUuid) {
			addBlockError =
				newBlockType === 'media' ? 'Select a media item.' : 'Annotation UUID is required.';
			return;
		}
		const nextOrder = blocks.length > 0 ? Math.max(...blocks.map((b) => b.order)) + 1 : 0;
		addingBlock = true;
		addBlockError = '';
		try {
			const payload = {
				block_type: newBlockType,
				media_uuid: newBlockType === 'media' ? blockUuid : null,
				annotation_uuid: newBlockType === 'annotation' ? blockUuid : null,
				caption: newBlockCaption.trim(),
				order: nextOrder
			};
			const { data: newBlock } = await exhibits.blocks.create(exhibitUuid, payload);
			blocks = [...blocks, newBlock];
			newBlockCaption = '';
			if (newBlockType === 'media') {
				const first = groupMedia[0];
				if (first) selectedMediaUuid = first.uuid;
			} else {
				newAnnotationUuid = '';
			}
		} catch {
			addBlockError = 'Failed to add block. Check that the UUID exists.';
		} finally {
			addingBlock = false;
		}
	}

	async function handleDeleteBlock(blockId: number) {
		deletingBlockId = blockId;
		blockActionError = '';
		try {
			await exhibits.blocks.delete(exhibitUuid, blockId);
			blocks = blocks.filter((b) => b.id !== blockId);
		} catch {
			blockActionError = 'Failed to remove block.';
		} finally {
			deletingBlockId = null;
		}
	}

	async function handleMoveBlock(blockId: number, dir: 'up' | 'down') {
		const idx = blocks.findIndex((b) => b.id === blockId);
		if (idx < 0) return;
		const swapIdx = dir === 'up' ? idx - 1 : idx + 1;
		if (swapIdx < 0 || swapIdx >= blocks.length) return;

		// Extract references before mapping — avoids non-null assertion on array access
		const blockAtIdx = blocks[idx];
		const blockAtSwap = blocks[swapIdx];
		if (!blockAtIdx || !blockAtSwap) return;

		// Optimistic local reorder
		const reordered = blocks.map((b, i) => {
			if (i === idx) return blockAtSwap;
			if (i === swapIdx) return blockAtIdx;
			return b;
		});
		blocks = reordered;

		reordering = true;
		try {
			await exhibits.blocks.reorder(
				exhibitUuid,
				reordered.map((b) => b.id)
			);
		} catch {
			// Revert — swap back
			const revertA = reordered[idx];
			const revertB = reordered[swapIdx];
			if (revertA && revertB) {
				blocks = reordered.map((b, i) => {
					if (i === idx) return revertB;
					if (i === swapIdx) return revertA;
					return b;
				});
			}
			blockActionError = 'Failed to reorder blocks.';
		} finally {
			reordering = false;
		}
	}

	async function handleDelete() {
		deleting = true;
		deleteError = '';
		try {
			await exhibits.delete(exhibitUuid);
			await goto('/exhibits');
		} catch {
			deleteError = 'Failed to delete exhibit.';
		} finally {
			deleting = false;
			showDeleteConfirm = false;
		}
	}

	function mediaLabel(m: MediaStore): string {
		return `${m.name} (${m.file_extension})`;
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

			{#if blockActionError}
				<p class="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{blockActionError}</p>
			{/if}

			{#if blocks.length === 0}
				<p class="text-sm text-gray-400">No blocks yet. Add one below.</p>
			{:else}
				<ol class="space-y-2">
					{#each blocks as block, idx}
						<li class="flex items-start gap-2 rounded border border-gray-200 p-3">
							<!-- Reorder buttons -->
							<div class="flex shrink-0 flex-col gap-0.5">
								<button
									onclick={() => void handleMoveBlock(block.id, 'up')}
									disabled={idx === 0 || reordering}
									aria-label="Move block up"
									class="rounded px-1 text-xs text-gray-400 hover:text-gray-700 disabled:opacity-20"
								>
									&#9650;
								</button>
								<button
									onclick={() => void handleMoveBlock(block.id, 'down')}
									disabled={idx === blocks.length - 1 || reordering}
									aria-label="Move block down"
									class="rounded px-1 text-xs text-gray-400 hover:text-gray-700 disabled:opacity-20"
								>
									&#9660;
								</button>
							</div>

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
							<button
								onclick={() => void handleDeleteBlock(block.id)}
								disabled={deletingBlockId === block.id}
								class="shrink-0 text-xs text-red-500 hover:underline disabled:opacity-50"
							>
								{deletingBlockId === block.id ? '…' : 'Remove'}
							</button>
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

			{#if newBlockType === 'media'}
				{#if groupMedia.length > 0}
					<label class="mb-1 block text-sm font-medium text-gray-600" for="media-search"
						>Search media</label
					>
					<input
						id="media-search"
						type="search"
						bind:value={mediaSearch}
						placeholder="Filter by name…"
						class="mb-2 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
					/>
					<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-media-select"
						>Select media item</label
					>
					<select
						id="blk-media-select"
						bind:value={selectedMediaUuid}
						class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
					>
						{#each filteredMedia as m}
							<option value={m.uuid}>{mediaLabel(m)}</option>
						{/each}
					</select>
				{:else}
					<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-uuid"
						>Media UUID</label
					>
					<input
						id="blk-uuid"
						type="text"
						bind:value={selectedMediaUuid}
						placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
						class="mb-4 w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm focus:outline-none focus:ring focus:ring-blue-200"
					/>
				{/if}
			{:else}
				<label class="mb-1 block text-sm font-medium text-gray-600" for="blk-ann-uuid"
					>Annotation UUID</label
				>
				<input
					id="blk-ann-uuid"
					type="text"
					bind:value={newAnnotationUuid}
					placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
					class="mb-4 w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm focus:outline-none focus:ring focus:ring-blue-200"
				/>
			{/if}

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
			{#if deleteError}
				<p class="mb-3 rounded bg-red-200 px-3 py-2 text-sm text-red-800">{deleteError}</p>
			{/if}
			{#if showDeleteConfirm}
				<div class="mb-3 rounded border border-red-300 bg-white p-4">
					<p class="mb-3 text-sm text-gray-700">Delete this exhibit? This cannot be undone.</p>
					<div class="flex gap-3">
						<button
							onclick={() => (showDeleteConfirm = false)}
							class="rounded bg-gray-200 px-3 py-1 text-sm text-gray-700 hover:bg-gray-300"
						>
							Cancel
						</button>
						<button
							onclick={() => void handleDelete()}
							disabled={deleting}
							class="rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600 disabled:opacity-50"
						>
							{deleting ? 'Deleting…' : 'Yes, delete'}
						</button>
					</div>
				</div>
			{:else}
				<button
					onclick={() => (showDeleteConfirm = true)}
					class="rounded bg-red-500 px-4 py-2 text-sm text-white hover:bg-red-600"
				>
					Delete Exhibit
				</button>
			{/if}
		</section>
	</div>
{/if}
