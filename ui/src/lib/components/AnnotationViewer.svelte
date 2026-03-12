<script lang="ts">
	import DOMPurify from 'dompurify';
	import { annotations as annoApi, mediaRelation, MAX_REPLY_DEPTH } from '$lib/api';
	import type { Annotation } from '$lib/api';
	import { currentUser, defaultQuality, dateLocale } from '$lib/stores';
	import AnnotationMedia from '$lib/components/primitives/AnnotationMedia.svelte';

	interface Props {
		annotations?: Annotation[];
		onPlaySnippet?: (start: number, end: number) => void;
		formatTime?: (s: number) => string;
		onAnnotationDeleted?: (id: number) => void;
	}

	const {
		annotations = [],
		onPlaySnippet = () => undefined,
		formatTime = defaultFormatTime,
		onAnnotationDeleted
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

	function allRepliesFor(parentId: number): Annotation[] {
		return [...(repliesByParent[parentId] ?? []), ...(localReplies[parentId] ?? [])];
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

	const TYPE_BADGE: Record<string, string> = {
		text: 'bg-gray-100 text-gray-600',
		image: 'bg-cyan-100 text-cyan-700',
		audio: 'bg-green-100 text-green-700',
		video: 'bg-purple-100 text-purple-700',
		media_ref: 'bg-orange-100 text-orange-700'
	};

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
		<ul>
			{#each rootAnnotations as annotation}
				{@render annotationThread(annotation, 0)}
			{/each}
		</ul>
	{:else}
		<p class="text-gray-500">No annotations available.</p>
	{/if}
</div>

{#snippet annotationThread(annotation: Annotation & { timeParts?: [number, number] | null }, depth: number)}
	<li class="my-2 mb-5 rounded bg-white p-4 shadow-sm" style:margin-left="{depth * 1.5}rem">
		<span
			class="mb-2 inline-block rounded px-2 py-0.5 text-xs font-medium {TYPE_BADGE[annotation.annotation_type] ?? 'bg-gray-100 text-gray-600'}"
		>
			{annotation.annotation_type}
		</span>

		{#if depth > 0 && annotation.created_by}
			<span class="ml-2 text-xs text-gray-400">
				Replying to thread
			</span>
		{/if}

		{#if annotation.media_target && annotation.timeParts}
			<p>
				<strong>Timestamp:</strong>
				<span
					class="cursor-pointer text-blue-600 underline"
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
					{formatTime(annotation.timeParts[0])} - {formatTime(annotation.timeParts[1])}
				</span>
			</p>
		{:else}
			<p><strong>Timestamp:</strong> Invalid timestamp</p>
		{/if}

		<!-- Media-type body -->
		{#if annotation.annotation_type === 'image' && annotation.annotation_image}
			<img
				src={annotation.annotation_image}
				alt="Annotation"
				class="mt-2 max-w-full rounded border border-gray-200"
			/>
		{:else if annotation.annotation_type === 'audio' && annotation.annotation_audio}
			<AnnotationMedia src={annotation.annotation_audio} mediaType="audio" hlsStartLevel={hlsStartLevel} />
		{:else if annotation.annotation_type === 'video' && annotation.annotation_video}
			<AnnotationMedia src={annotation.annotation_video} mediaType="video" hlsStartLevel={hlsStartLevel} />
		{:else if annotation.annotation_type === 'media_ref' && annotation.media_ref_uuid}
			<p class="mt-2 text-sm text-gray-500">
				Linked media: <code class="font-mono text-xs">{annotation.media_ref_uuid}</code>
			</p>
		{/if}

		<div class="mt-4 text-gray-600">
			{@html DOMPurify.sanitize(annotation.annotation_text || 'No note available')}
		</div>

		<p class="mt-1 text-xs text-gray-400">
			{annotation.created_by?.username ?? 'Unknown'}
			{#if depth > 0}
				· {formatDate(annotation.created_at)}
			{/if}
		</p>

		<div class="mt-2 flex gap-3">
			{#if depth < MAX_REPLY_DEPTH}
				<button
					class="text-xs text-blue-600 hover:underline"
					onclick={() => toggleReplyForm(annotation.id)}
				>
					{expandedReplyFor === annotation.id ? 'Cancel' : 'Reply'}
				</button>
			{/if}
			{#if $currentUser && annotation.created_by?.id === $currentUser.id}
				<button
					class="text-xs text-red-500 hover:underline"
					onclick={() => void deleteAnno(annotation)}
				>
					Delete
				</button>
			{/if}
		</div>
		{#if deleteError[annotation.id]}
			<p class="mt-1 text-xs text-red-600">{deleteError[annotation.id]}</p>
		{/if}

		<!-- Inline reply form -->
		{#if depth < MAX_REPLY_DEPTH && expandedReplyFor === annotation.id}
			<div class="mt-3">
				{#if replyError}
					<p class="mb-2 text-xs text-red-600">{replyError}</p>
				{/if}
				<textarea
					bind:value={replyText}
					rows="2"
					placeholder="Write a reply…"
					class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
				></textarea>
				<button
					onclick={() => void handleReply(annotation)}
					disabled={submittingReply}
					class="mt-1 rounded bg-brand-primary px-3 py-1.5 text-sm text-white hover:opacity-90 disabled:opacity-50"
				>
					{submittingReply ? 'Posting…' : 'Post Reply'}
				</button>
			</div>
		{/if}

		<!-- Recursive children -->
		{#if allRepliesFor(annotation.id).length > 0}
			<ul class="mt-3 space-y-2 border-l-2 border-gray-200 pl-4">
				{#each allRepliesFor(annotation.id) as reply}
					{@render annotationThread({ ...reply, timeParts: getTimeParts(reply.media_target) }, depth + 1)}
				{/each}
			</ul>
		{/if}
	</li>
{/snippet}
