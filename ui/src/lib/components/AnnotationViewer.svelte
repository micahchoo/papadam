<script lang="ts">
	import DOMPurify from 'dompurify';
	import { annotations as annoApi, mediaRelation, tags as tagsApi, MAX_REPLY_DEPTH } from '$lib/api';
	import type { Annotation, Tag } from '$lib/api';
	import { currentUser, defaultQuality, dateLocale } from '$lib/stores';
	import AnnotationMedia from '$lib/components/primitives/AnnotationMedia.svelte';

	interface Props {
		annotations?: Annotation[];
		onPlaySnippet?: (start: number, end: number) => void;
		formatTime?: (s: number) => string;
		onAnnotationDeleted?: (id: number) => void;
		onAnnotationUpdated?: (updated: Annotation) => void;
	}

	const {
		annotations = [],
		onPlaySnippet = () => undefined,
		formatTime = defaultFormatTime,
		onAnnotationDeleted,
		onAnnotationUpdated
	}: Props = $props();

	/** Map UIConfig quality to HLS.js startLevel for annotation media. */
	const hlsStartLevel = $derived(
		$defaultQuality === 'low' ? 0 : $defaultQuality === 'high' ? Infinity : -1
	);

	function defaultFormatTime(seconds: number): string {
		if (isNaN(seconds)) return '00:00';
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
	}

	function getTimeParts(mediaTarget: string): [number, number] | null {
		try {
			const clean = mediaTarget.replace(/\s+/g, '').replace(/^t=/, '');
			const match = clean.match(/^(\d{2}):(\d{2}),(\d{2}):(\d{2})$/);
			if (match) {
				const [, g1, g2, g3, g4] = match;
				if (g1 && g2 && g3 && g4)
					return [parseInt(g1) * 60 + parseInt(g2), parseInt(g3) * 60 + parseInt(g4)];
			}
			const parts = clean.split(',').map(Number);
			const [p0, p1] = parts;
			if (parts.length === 2 && p0 !== undefined && p1 !== undefined && !isNaN(p0) && !isNaN(p1))
				return [p0, p1];
		} catch {
			/* fall through */
		}
		return null;
	}

	// Separate root annotations from replies
	const rootAnnotations = $derived(
		annotations
			.filter((a) => a.reply_to === null)
			.map((a) => ({ ...a, timeParts: getTimeParts(a.media_target) }))
	);

	// Index prop-supplied replies by parent id (O(1) lookup)
	const repliesByParent = $derived(
		annotations.reduce<Record<number, Annotation[]>>((acc, a) => {
			if (a.reply_to !== null) {
				(acc[a.reply_to] ??= []).push(a);
			}
			return acc;
		}, {})
	);

	// Locally posted replies (appended after successful POST — not yet in the prop)
	let localReplies = $state<Record<number, Annotation[]>>({});

	// Lazy-loaded replies from API
	let fetchedReplies = $state<Record<number, Annotation[]>>({});
	let fetchingReplies = $state<Record<number, boolean>>({});
	let fetchReplyError = $state<Record<number, string>>({});
	let expandedThreads = $state<Set<number>>(new Set());

	function allRepliesFor(parentId: number): Annotation[] {
		return [
			...(repliesByParent[parentId] ?? []),
			...(fetchedReplies[parentId] ?? []),
			...(localReplies[parentId] ?? [])
		];
	}

	async function loadReplies(annotationId: number, uuid: string) {
		if (expandedThreads.has(annotationId)) {
			// Toggle off
			expandedThreads = new Set([...expandedThreads].filter((id) => id !== annotationId));
			return;
		}
		expandedThreads = new Set([...expandedThreads, annotationId]);

		// If already have prop-supplied or fetched replies, don't re-fetch
		if ((repliesByParent[annotationId]?.length ?? 0) > 0 || (fetchedReplies[annotationId]?.length ?? 0) > 0) return;

		fetchingReplies = { ...fetchingReplies, [annotationId]: true };
		fetchReplyError = { ...fetchReplyError, [annotationId]: '' };
		try {
			const { data } = await mediaRelation.replies(uuid);
			fetchedReplies = { ...fetchedReplies, [annotationId]: data };
		} catch {
			fetchReplyError = { ...fetchReplyError, [annotationId]: "Couldn't load replies" };
		} finally {
			fetchingReplies = { ...fetchingReplies, [annotationId]: false };
		}
	}

	// Reply form state — one open form at a time
	let expandedReplyFor = $state<number | null>(null);
	let replyText = $state('');
	let submittingReply = $state(false);
	let replyError = $state('');

	function toggleReplyForm(annotationId: number) {
		if (expandedReplyFor === annotationId) {
			expandedReplyFor = null;
		} else {
			expandedReplyFor = annotationId;
			replyText = '';
			replyError = '';
		}
	}

	async function handleReply(annotation: Annotation) {
		if (!replyText.trim()) return;
		submittingReply = true;
		replyError = '';
		try {
			const { data: newReply } = await mediaRelation.createReply(annotation.uuid, {
				annotation_text: replyText.trim()
			});
			localReplies = {
				...localReplies,
				[annotation.id]: [...(localReplies[annotation.id] ?? []), newReply]
			};
			replyText = '';
			expandedReplyFor = null;
		} catch {
			replyError = 'Failed to post reply.';
		} finally {
			submittingReply = false;
		}
	}

	let deleteError = $state<Record<number, string>>({});

	async function deleteAnno(annotation: Annotation) {
		deleteError = { ...deleteError, [annotation.id]: '' };
		try {
			await annoApi.delete(annotation.uuid);
			onAnnotationDeleted?.(annotation.id);
		} catch {
			deleteError = { ...deleteError, [annotation.id]: 'Delete failed.' };
		}
	}

	// ── Tag management ──────────────────────────────────────────────────────
	let tagDropdownFor = $state<number | null>(null);
	let availableTags = $state<Tag[]>([]);
	let tagSearchQuery = $state('');
	let loadingTags = $state(false);

	const filteredTags = $derived(
		availableTags.filter((t) =>
			t.name.toLowerCase().includes(tagSearchQuery.toLowerCase())
		)
	);

	async function openTagDropdown(annotationId: number) {
		tagDropdownFor = annotationId;
		tagSearchQuery = '';
		if (availableTags.length === 0) {
			loadingTags = true;
			try {
				const { data } = await tagsApi.list();
				availableTags = data;
			} catch {
				// Silently fail — dropdown will be empty
			} finally {
				loadingTags = false;
			}
		}
	}

	async function addTag(annotation: Annotation, tagName: string) {
		// Optimistic update
		const prevTags = [...annotation.tags];
		annotation.tags = [...annotation.tags, { id: 0, name: tagName, count: 1 }];
		tagDropdownFor = null;
		try {
			const { data } = await annoApi.addTag(annotation.uuid, tagName);
			annotation.tags = data.tags;
			onAnnotationUpdated?.(data);
		} catch {
			annotation.tags = prevTags; // Rollback
		}
	}

	async function removeTag(annotation: Annotation, tagName: string) {
		// Optimistic update
		const prevTags = [...annotation.tags];
		annotation.tags = annotation.tags.filter((t) => t.name !== tagName);
		try {
			const { data } = await annoApi.removeTag(annotation.uuid, tagName);
			annotation.tags = data.tags;
			onAnnotationUpdated?.(data);
		} catch {
			annotation.tags = prevTags; // Rollback
		}
	}

	// ── Edit annotation ─────────────────────────────────────────────────────
	let editModalFor = $state<Annotation | null>(null);
	let editText = $state('');
	let editSubmitting = $state(false);
	let editError = $state('');

	async function openEditModal(annotation: Annotation) {
		editError = '';
		editSubmitting = false;
		try {
			const { data: fresh } = await annoApi.get(annotation.uuid);
			editModalFor = fresh;
			editText = fresh.annotation_text;
		} catch {
			editModalFor = annotation;
			editText = annotation.annotation_text;
		}
	}

	async function submitEdit() {
		if (!editModalFor) return;
		editSubmitting = true;
		editError = '';
		try {
			const formData = new FormData();
			formData.append('annotation_text', editText);
			const { data: updated } = await annoApi.update(editModalFor.uuid, formData);
			onAnnotationUpdated?.(updated);
			editModalFor = null;
		} catch {
			editError = 'Failed to update annotation.';
		} finally {
			editSubmitting = false;
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString($dateLocale, {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}
</script>

<div class="annotation-viewer">
	{#if rootAnnotations.length > 0}
		<ul class="space-y-0">
			{#each rootAnnotations as annotation}
				{@render annotationThread(annotation, 0)}
			{/each}
		</ul>
	{:else}
		<p class="py-6 font-body text-sm text-gray-400">No annotations available.</p>
	{/if}
</div>

{#snippet annotationThread(annotation: Annotation & { timeParts?: [number, number] | null }, depth: number)}
	<li
		class="border-l-2 py-3 pl-4"
		class:border-gray-300={depth === 0}
		class:border-gray-200={depth > 0}
		class:ml-0={depth === 0}
		style:margin-left="{depth * 1.5}rem"
	>
		<!-- Type badge + meta -->
		<div class="flex items-baseline gap-2">
			<span class="font-body text-xs font-medium uppercase tracking-wider text-gray-500">
				{annotation.annotation_type}
			</span>
			{#if depth > 0 && annotation.created_by}
				<span class="font-body text-xs text-gray-400">replying</span>
			{/if}
		</div>

		{#if annotation.media_target && annotation.timeParts}
			<p class="mt-1 font-body text-xs text-gray-500">
				<span
					class="cursor-pointer underline decoration-dotted"
					role="button"
					tabindex="0"
					onclick={() => {
						const p = annotation.timeParts;
						if (p) onPlaySnippet(p[0], p[1]);
					}}
					onkeydown={(e) => {
						const p = annotation.timeParts;
						if (e.key === 'Enter' && p) onPlaySnippet(p[0], p[1]);
					}}
				>
					{formatTime(annotation.timeParts[0])}&ndash;{formatTime(annotation.timeParts[1])}
				</span>
			</p>
		{:else}
			<p class="mt-1 font-body text-xs text-gray-400">Invalid timestamp</p>
		{/if}

		<!-- Media-type body -->
		{#if annotation.annotation_type === 'image' && annotation.annotation_image}
			<img
				src={annotation.annotation_image}
				alt="Annotation"
				class="mt-2 max-w-full border border-gray-200"
			/>
		{:else if annotation.annotation_type === 'audio' && annotation.annotation_audio}
			<AnnotationMedia src={annotation.annotation_audio} mediaType="audio" hlsStartLevel={hlsStartLevel} />
		{:else if annotation.annotation_type === 'video' && annotation.annotation_video}
			<AnnotationMedia src={annotation.annotation_video} mediaType="video" hlsStartLevel={hlsStartLevel} />
		{:else if annotation.annotation_type === 'media_ref' && annotation.media_ref_uuid}
			<p class="mt-2 font-body text-sm text-gray-500">
				Linked media: <code class="font-mono text-xs">{annotation.media_ref_uuid}</code>
			</p>
		{/if}

		<div class="mt-2 font-body text-sm leading-relaxed text-gray-800">
			{@html DOMPurify.sanitize(annotation.annotation_text || 'No note available')}
		</div>

		<!-- Tags -->
		{#if annotation.tags.length > 0 || $currentUser}
			<div class="mt-2 flex flex-wrap items-center gap-1">
				{#each annotation.tags as tag}
					<span class="inline-flex items-center gap-1 bg-gray-100 px-2 py-0.5 font-body text-xs text-gray-600">
						{tag.name}
						{#if $currentUser}
							<button
								class="ml-0.5 text-gray-400 hover:text-red-500"
								aria-label="Remove tag {tag.name}"
								onclick={() => void removeTag(annotation, tag.name)}
							>&times;</button>
						{/if}
					</span>
				{/each}
				{#if $currentUser}
					<div class="relative">
						<button
							class="inline-flex h-5 w-5 items-center justify-center border border-gray-300 text-xs text-gray-500 hover:bg-gray-100"
							aria-label="Add tag"
							onclick={() => void openTagDropdown(annotation.id)}
						>+</button>
						{#if tagDropdownFor === annotation.id}
							<div class="absolute left-0 top-6 z-20 w-48 border border-gray-200 bg-white shadow-sm">
								<input
									type="text"
									class="w-full border-b border-gray-200 px-2 py-1 font-body text-xs focus:outline-none"
									placeholder="Search tags…"
									bind:value={tagSearchQuery}
								/>
								{#if loadingTags}
									<p class="px-2 py-1 font-body text-xs text-gray-400">Loading…</p>
								{:else}
									<ul class="max-h-32 overflow-y-auto">
										{#each filteredTags as tag}
											<li>
												<button
													class="w-full px-2 py-1 text-left font-body text-xs hover:bg-gray-50"
													onclick={() => void addTag(annotation, tag.name)}
												>{tag.name}</button>
											</li>
										{/each}
										{#if filteredTags.length === 0}
											<li class="px-2 py-1 font-body text-xs text-gray-400">No tags found</li>
										{/if}
									</ul>
								{/if}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}

		<p class="mt-1 font-body text-xs text-gray-400">
			{annotation.created_by?.username ?? 'Unknown'}
			{#if depth > 0}
				&middot; {formatDate(annotation.created_at)}
			{/if}
		</p>

		<div class="mt-2 flex gap-3">
			{#if depth < MAX_REPLY_DEPTH}
				<button
					class="font-body text-xs text-gray-500 hover:underline"
					onclick={() => toggleReplyForm(annotation.id)}
				>
					{expandedReplyFor === annotation.id ? 'Cancel' : 'Reply'}
				</button>
				{#if allRepliesFor(annotation.id).length === 0 && !expandedThreads.has(annotation.id)}
					<button
						class="font-body text-xs text-gray-500 hover:underline"
						onclick={() => void loadReplies(annotation.id, annotation.uuid)}
					>
						Load replies
					</button>
				{/if}
			{/if}
			{#if $currentUser && annotation.created_by?.id === $currentUser.id}
				<button
					class="font-body text-xs text-gray-500 hover:underline"
					onclick={() => void openEditModal(annotation)}
					aria-label="Edit annotation"
				>
					Edit
				</button>
				<button
					class="font-body text-xs text-red-500 hover:underline"
					onclick={() => void deleteAnno(annotation)}
				>
					Delete
				</button>
			{/if}
		</div>
		{#if deleteError[annotation.id]}
			<p class="mt-1 font-body text-xs text-red-600">{deleteError[annotation.id]}</p>
		{/if}

		<!-- Loading / error for lazy replies -->
		{#if fetchingReplies[annotation.id]}
			<p class="mt-2 font-body text-xs text-gray-400">Loading replies…</p>
		{/if}
		{#if fetchReplyError[annotation.id]}
			<p class="mt-2 font-body text-xs text-red-500">
				{fetchReplyError[annotation.id]}
				<button
					class="ml-2 underline"
					onclick={() => void loadReplies(annotation.id, annotation.uuid)}
				>Retry</button>
			</p>
		{/if}

		<!-- Inline reply form -->
		{#if depth < MAX_REPLY_DEPTH && expandedReplyFor === annotation.id}
			<div class="mt-3">
				{#if replyError}
					<p class="mb-2 font-body text-xs text-red-600">{replyError}</p>
				{/if}
				<textarea
					bind:value={replyText}
					rows="2"
					placeholder="Write a reply…"
					class="w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
				></textarea>
				<button
					onclick={() => void handleReply(annotation)}
					disabled={submittingReply}
					class="mt-1 border border-gray-900 px-3 py-1 font-body text-sm hover:bg-gray-900 hover:text-white disabled:opacity-50"
				>
					{submittingReply ? 'Posting…' : 'Post Reply'}
				</button>
			</div>
		{/if}

		<!-- Recursive children (capped to prevent runaway recursion on malformed data) -->
		{#if depth < MAX_REPLY_DEPTH && allRepliesFor(annotation.id).length > 0}
			<ul class="mt-3 space-y-0">
				{#each allRepliesFor(annotation.id) as reply}
					{@render annotationThread({ ...reply, timeParts: getTimeParts(reply.media_target) }, depth + 1)}
				{/each}
			</ul>
		{/if}
	</li>
{/snippet}

<!-- Edit annotation modal -->
{#if editModalFor}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		role="dialog"
		aria-label="Edit annotation"
	>
		<div class="w-full max-w-md border border-gray-200 bg-white p-6 shadow-lg">
			<h2 class="font-heading text-xl font-bold">Edit Annotation</h2>
			<p class="mt-1 font-body text-xs text-gray-500">
				Type: {editModalFor.annotation_type} (read-only)
			</p>

			<div class="mt-4">
				<label class="mb-1 block font-body text-sm font-medium" for="edit-anno-text">
					Annotation text
				</label>
				<textarea
					id="edit-anno-text"
					bind:value={editText}
					rows="4"
					class="w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
				></textarea>
			</div>

			{#if editError}
				<p class="mt-2 font-body text-sm text-red-600">{editError}</p>
			{/if}

			<div class="mt-4 flex justify-end gap-3">
				<button
					class="border border-gray-300 px-4 py-2 font-body text-sm hover:bg-gray-100 disabled:opacity-50"
					disabled={editSubmitting}
					onclick={() => (editModalFor = null)}
				>Cancel</button>
				<button
					class="border border-gray-900 px-4 py-2 font-body text-sm hover:bg-gray-900 hover:text-white disabled:opacity-50"
					disabled={editSubmitting}
					onclick={() => void submitEdit()}
				>{editSubmitting ? 'Saving…' : 'Save'}</button>
			</div>
		</div>
	</div>
{/if}
