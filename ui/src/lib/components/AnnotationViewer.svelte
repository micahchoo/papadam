<script lang="ts">
	import { annotations as annoApi, mediaRelation } from '$lib/api';
	import type { Annotation } from '$lib/api';

	interface Props {
		annotations?: Annotation[];
		onPlaySnippet?: (start: number, end: number) => void;
		formatTime?: (s: number) => string;
	}

	const {
		annotations = [],
		onPlaySnippet = () => undefined,
		formatTime = defaultFormatTime
	}: Props = $props();

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

	async function deleteAnno(annotation: Annotation) {
		try {
			await annoApi.delete(annotation.uuid);
			window.history.back();
		} catch (err) {
			console.error('Error deleting annotation:', err);
		}
	}
</script>

<div class="annotation-viewer">
	{#if rootAnnotations.length > 0}
		<ul>
			{#each rootAnnotations as annotation}
				<li class="my-2 mb-5 rounded bg-white p-4 shadow-sm">
					{#if annotation.media_target && annotation.timeParts}
						<p>
							<strong>Timestamp:</strong>
							<span
								class="cursor-pointer text-blue-500 underline"
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

					<div class="mt-4 text-gray-600">
						{@html annotation.annotation_text || 'No note available'}
					</div>

					<div class="mt-2 flex gap-3">
						<button
							class="text-xs text-blue-600 hover:underline"
							onclick={() => toggleReplyForm(annotation.id)}
						>
							{expandedReplyFor === annotation.id ? 'Cancel' : 'Reply'}
						</button>
						<button
							class="text-xs text-red-500 hover:underline"
							onclick={() => void deleteAnno(annotation)}
						>
							Delete
						</button>
					</div>

					<!-- Existing replies (prop-supplied + locally posted) -->
					{#if allRepliesFor(annotation.id).length > 0}
						<ul class="mt-3 space-y-2 border-l-2 border-gray-200 pl-4">
							{#each allRepliesFor(annotation.id) as reply}
								<li class="rounded bg-gray-50 p-3 text-sm">
									<div class="text-gray-700">
										{@html reply.annotation_text || ''}
									</div>
									<span class="text-xs text-gray-400">{reply.created_at}</span>
								</li>
							{/each}
						</ul>
					{/if}

					<!-- Inline reply form -->
					{#if expandedReplyFor === annotation.id}
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
								class="mt-1 rounded bg-blue-950 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
							>
								{submittingReply ? 'Posting…' : 'Post Reply'}
							</button>
						</div>
					{/if}
				</li>
			{/each}
		</ul>
	{:else}
		<p class="text-gray-500">No annotations available.</p>
	{/if}
</div>
