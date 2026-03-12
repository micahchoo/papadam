<script lang="ts">
	import { annotations as annoApi } from '$lib/api';
	import type { Annotation } from '$lib/api';
	import { timeRangeInputMode, selectedMediaDuration, playbackPosition } from '$lib/stores';

	interface Props {
		annotation: Annotation;
		showModal: boolean;
		onSaved?: (updated: Annotation) => void;
	}

	let { annotation, showModal = $bindable(), onSaved }: Props = $props();

	let editText = $state('');
	let editStart = $state(0);
	let editEnd = $state(0);
	let submitting = $state(false);
	let errorMsg = $state('');
	let loading = $state(true);
	let freshAnnotation = $state<Annotation | null>(null);

	const duration = $derived($selectedMediaDuration ?? 100);

	// Load fresh data on open
	$effect(() => {
		if (showModal) {
			loading = true;
			errorMsg = '';
			annoApi.get(annotation.uuid)
				.then(({ data }) => {
					freshAnnotation = data;
					editText = data.annotation_text;
					parseTimeRange(data.media_target);
				})
				.catch(() => {
					// Fall back to prop data
					freshAnnotation = annotation;
					editText = annotation.annotation_text;
					parseTimeRange(annotation.media_target);
				})
				.finally(() => {
					loading = false;
				});
		}
	});

	function parseTimeRange(target: string) {
		const clean = target.replace(/\s+/g, '').replace(/^t=/, '');
		const parts = clean.split(',').map(Number);
		const [p0, p1] = parts;
		if (parts.length === 2 && p0 !== undefined && p1 !== undefined && !isNaN(p0) && !isNaN(p1)) {
			editStart = p0;
			editEnd = p1;
		}
	}

	function formatTime(s: number): string {
		const m = Math.floor(s / 60);
		const sc = Math.floor(s % 60);
		return `${String(m).padStart(2, '0')}:${String(sc).padStart(2, '0')}`;
	}

	function parseTimestamp(s: string): number | null {
		const m = /^(\d{1,2}):(\d{2})$/.exec(s.trim());
		if (!m?.[1] || !m[2]) return null;
		const mins = parseInt(m[1], 10);
		const secs = parseInt(m[2], 10);
		if (secs >= 60) return null;
		return mins * 60 + secs;
	}

	async function handleSubmit() {
		if (!freshAnnotation) return;
		submitting = true;
		errorMsg = '';
		try {
			const formData = new FormData();
			formData.append('annotation_text', editText);
			formData.append('media_target', `t=${editStart},${editEnd}`);
			const { data: updated } = await annoApi.update(freshAnnotation.uuid, formData);
			onSaved?.(updated);
			showModal = false;
		} catch {
			errorMsg = 'Failed to update annotation.';
		} finally {
			submitting = false;
		}
	}
</script>

{#if showModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		role="dialog"
		aria-label="Edit annotation"
	>
		<div class="w-full max-w-md border border-gray-200 bg-white p-6 shadow-lg">
			{#if loading}
				<p class="font-body text-sm text-gray-500">Loading…</p>
			{:else if freshAnnotation}
				<h2 class="font-heading text-xl font-bold">Edit Annotation</h2>
				<p class="mt-1 font-body text-xs text-gray-500">
					Type: {freshAnnotation.annotation_type} (read-only)
				</p>

				<!-- Time range respects timeRangeInputMode -->
				{#if $timeRangeInputMode === 'tap'}
					<div class="mt-4">
						<p class="mb-2 font-body text-sm font-medium">Time Range</p>
						<div class="flex items-center gap-3">
							<button
								onclick={() => { editStart = $playbackPosition; if (editStart > editEnd) editEnd = editStart; }}
								class="rounded bg-green-100 px-3 py-1 font-body text-sm text-green-800 hover:bg-green-200"
							>
								Set start ({formatTime(editStart)})
							</button>
							<button
								onclick={() => { editEnd = Math.min($playbackPosition, duration); if (editEnd < editStart) editStart = editEnd; }}
								class="rounded bg-red-100 px-3 py-1 font-body text-sm text-red-800 hover:bg-red-200"
							>
								Set end ({formatTime(editEnd)})
							</button>
						</div>
					</div>
				{:else if $timeRangeInputMode === 'timestamp'}
					<div class="mt-4">
						<p class="mb-2 font-body text-sm font-medium">Time Range (MM:SS)</p>
						<div class="flex items-center gap-3">
							<label class="font-body text-sm" for="edit-ts-start">Start</label>
							<input
								id="edit-ts-start"
								type="text"
								placeholder="00:00"
								value={formatTime(editStart)}
								oninput={(e) => {
									const v = parseTimestamp(e.currentTarget.value);
									if (v !== null) { editStart = v; if (v > editEnd) editEnd = v; }
								}}
								class="w-24 border p-1 font-mono text-sm"
							/>
							<label class="font-body text-sm" for="edit-ts-end">End</label>
							<input
								id="edit-ts-end"
								type="text"
								placeholder="00:00"
								value={formatTime(editEnd)}
								oninput={(e) => {
									const v = parseTimestamp(e.currentTarget.value);
									if (v !== null) { const c = Math.min(v, duration); editEnd = c; if (c < editStart) editStart = c; }
								}}
								class="w-24 border p-1 font-mono text-sm"
							/>
						</div>
					</div>
				{:else}
					<div class="mt-4">
						<label class="mb-1 block font-body text-sm font-medium" for="edit-start">Start ({formatTime(editStart)})</label>
						<input id="edit-start" type="range" min="0" max={duration} step="0.1" bind:value={editStart} class="w-full" />
						<label class="mb-1 mt-2 block font-body text-sm font-medium" for="edit-end">End ({formatTime(editEnd)})</label>
						<input id="edit-end" type="range" min="0" max={duration} step="0.1" bind:value={editEnd} class="w-full" />
					</div>
				{/if}

				<!-- Tags (read-only display — editing via AnnotationViewer chips) -->
				{#if freshAnnotation.tags.length > 0}
					<div class="mt-3 flex flex-wrap gap-1">
						{#each freshAnnotation.tags as tag}
							<span class="bg-gray-100 px-2 py-0.5 font-body text-xs text-gray-600">{tag.name}</span>
						{/each}
					</div>
				{/if}

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

				{#if errorMsg}
					<p class="mt-2 font-body text-sm text-red-600">{errorMsg}</p>
				{/if}

				<div class="mt-4 flex justify-end gap-3">
					<button
						class="border border-gray-300 px-4 py-2 font-body text-sm hover:bg-gray-100 disabled:opacity-50"
						disabled={submitting}
						onclick={() => (showModal = false)}
					>Cancel</button>
					<button
						class="border border-gray-900 px-4 py-2 font-body text-sm hover:bg-gray-900 hover:text-white disabled:opacity-50"
						disabled={submitting}
						onclick={() => void handleSubmit()}
					>{submitting ? 'Saving…' : 'Save'}</button>
				</div>
			{/if}
		</div>
	</div>
{/if}
