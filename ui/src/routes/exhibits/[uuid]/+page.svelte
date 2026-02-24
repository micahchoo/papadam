<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { exhibits, archive, annotations as annoApi } from '$lib/api';
	import type { ExhibitBlock, MediaStore, Annotation } from '$lib/api';
	import { isAuthenticated } from '$lib/stores';

	type BlockResult =
		| { kind: 'media'; blockId: number; data: MediaStore }
		| { kind: 'annotation'; blockId: number; data: Annotation }
		| null;

	const exhibitUuid = $derived($page.params.uuid ?? '');

	let title = $state('');
	let description = $state('');
	let isPublic = $state(true);
	let blocks = $state<ExhibitBlock[]>([]);
	let mediaData = $state<Record<number, MediaStore>>({});
	let annoData = $state<Record<number, Annotation>>({});
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const { data: ex } = await exhibits.get(exhibitUuid);
			title = ex.title;
			description = ex.description;
			isPublic = ex.is_public;
			blocks = ex.blocks;

			const results = await Promise.all(
				ex.blocks.map(async (block): Promise<BlockResult> => {
					if (block.block_type === 'media' && block.media_uuid) {
						const { data } = await archive.get(block.media_uuid);
						return { kind: 'media', blockId: block.id, data };
					}
					if (block.block_type === 'annotation' && block.annotation_uuid) {
						const { data } = await annoApi.get(block.annotation_uuid);
						return { kind: 'annotation', blockId: block.id, data };
					}
					return null;
				})
			);

			const media: Record<number, MediaStore> = {};
			const anno: Record<number, Annotation> = {};
			for (const r of results) {
				if (r?.kind === 'media') media[r.blockId] = r.data;
				if (r?.kind === 'annotation') anno[r.blockId] = r.data;
			}
			mediaData = media;
			annoData = anno;
		} catch {
			error = 'Exhibit not found or unavailable.';
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex min-h-[60vh] items-center justify-center">
		<p class="text-gray-500">Loading exhibit…</p>
	</div>
{:else if error}
	<div class="flex min-h-[60vh] items-center justify-center">
		<p class="text-red-600">{error}</p>
	</div>
{:else}
	<div class="mx-auto max-w-3xl px-4 py-8">
		<div class="mb-6 flex items-start justify-between">
			<div>
				<h1 class="text-3xl font-bold text-gray-900">{title}</h1>
				{#if description}
					<p class="mt-2 text-gray-600">{description}</p>
				{/if}
				{#if !isPublic}
					<span class="mt-2 inline-block rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600"
						>Private</span
					>
				{/if}
			</div>
			{#if $isAuthenticated}
				<a
					href="/exhibits/{exhibitUuid}/edit"
					class="ml-4 shrink-0 rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
				>
					Edit
				</a>
			{/if}
		</div>

		{#if blocks.length === 0}
			<p class="text-gray-500">This exhibit has no blocks yet.</p>
		{:else}
			<ol class="space-y-6">
				{#each blocks as block}
					<li class="rounded-lg bg-white p-6 shadow-sm">
						{#if block.block_type === 'media'}
							{@const media = mediaData[block.id]}
							{#if media}
								<h2 class="text-lg font-semibold text-gray-800">{media.name}</h2>
								{#if media.description}
									<p class="mt-1 text-sm text-gray-500">{media.description}</p>
								{/if}
								<a
									href="/groups/{media.group.id}/media/{media.uuid}"
									class="mt-3 inline-block text-sm text-blue-600 hover:underline"
								>
									Open in player →
								</a>
							{:else}
								<p class="text-sm text-gray-400">Media not available (uuid: {block.media_uuid})</p>
							{/if}
						{:else if block.block_type === 'annotation'}
							{@const anno = annoData[block.id]}
							{#if anno}
								<div class="prose prose-sm max-w-none text-gray-700">
									{@html anno.annotation_text || '(no text)'}
								</div>
							{:else}
								<p class="text-sm text-gray-400">
									Annotation not available (uuid: {block.annotation_uuid})
								</p>
							{/if}
						{/if}

						{#if block.caption}
							<p class="mt-3 text-sm italic text-gray-500">{block.caption}</p>
						{/if}
					</li>
				{/each}
			</ol>
		{/if}

		<div class="mt-8">
			<a href="/exhibits" class="text-sm text-gray-500 hover:underline">← All Exhibits</a>
		</div>
	</div>
{/if}
