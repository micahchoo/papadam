<script lang="ts">
	import { annotations as annoApi } from '$lib/api';
	import type { Annotation, AnnotationType, MediaStore } from '$lib/api';
	import { selectedMediaDuration } from '$lib/stores';

	interface Props {
		showAnnotationModal: boolean;
		recording: MediaStore;
		annotations: Annotation[];
	}
	let { showAnnotationModal = $bindable(), recording, annotations = $bindable() }: Props = $props();

	let newAnnotation = $state({ start: 0, end: 0, description: '', tags: '' });
	let annotationType = $state<AnnotationType>('text');
	const duration = $derived($selectedMediaDuration ?? 100);
	const startPct = $derived((newAnnotation.start / duration) * 100);
	const endPct = $derived((newAnnotation.end / duration) * 100);

	async function submitAnnotation() {
		try {
			const formData = new FormData();
			formData.append('media_reference_id', recording.uuid);
			formData.append('annotation_type', annotationType);
			formData.append('annotation_text', newAnnotation.description);
			formData.append('media_target', `t=${newAnnotation.start},${newAnnotation.end}`);
			formData.append('tags', newAnnotation.tags);
			const { data: created } = await annoApi.create(formData);
			annotations = [...annotations, created];
			newAnnotation = { start: 0, end: 0, description: '', tags: '' };
			annotationType = 'text';
		} catch (err) {
			console.error('Failed to create annotation:', err);
		} finally {
			showAnnotationModal = false;
		}
	}

	function handleStartChange(e: Event) {
		const val = parseFloat((e.target as HTMLInputElement).value);
		newAnnotation.start = val;
		if (val > newAnnotation.end) newAnnotation.end = val;
	}
	function handleEndChange(e: Event) {
		const val = parseFloat((e.target as HTMLInputElement).value);
		newAnnotation.end = Math.min(val, duration);
		if (newAnnotation.end < newAnnotation.start) newAnnotation.start = newAnnotation.end;
	}
	function formatTime(s: number): string {
		const m = Math.floor(s / 60);
		const sc = Math.floor(s % 60);
		return `${String(m).padStart(2, '0')}:${String(sc).padStart(2, '0')}`;
	}
</script>

<div
	class="fixed inset-0 top-0 z-10 flex h-full items-center justify-center bg-black bg-opacity-50"
>
	<div class="w-[500px] rounded-lg bg-white p-6">
		<h2 class="mb-4 text-xl font-bold">Create New Annotation</h2>
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-start">Start Time</label>
			<div class="flex items-center space-x-2">
				<input
					id="anno-start"
					type="range"
					min="0"
					max={duration}
					step="0.1"
					bind:value={newAnnotation.start}
					oninput={handleStartChange}
					class="h-2 w-full appearance-none rounded-full"
					style="background: linear-gradient(to right, #22c55e 0%, #22c55e {startPct}%, #d1d5db {startPct}% 100%)"
				/>
				<span>{formatTime(newAnnotation.start)}</span>
			</div>
		</div>
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-end">End Time</label>
			<div class="flex items-center space-x-2">
				<input
					id="anno-end"
					type="range"
					min="0"
					max={duration}
					step="0.1"
					bind:value={newAnnotation.end}
					oninput={handleEndChange}
					class="h-2 w-full appearance-none rounded-full"
					style="background: linear-gradient(to right, #ef4444 0%, #ef4444 {endPct}%, #d1d5db {endPct}% 100%)"
				/>
				<span>{formatTime(newAnnotation.end)}</span>
			</div>
		</div>
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-desc">Description</label>
			<textarea
				id="anno-desc"
				bind:value={newAnnotation.description}
				placeholder="Enter annotation description"
				class="w-full rounded border p-2"
			></textarea>
		</div>
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-type">Annotation Type</label>
			<select id="anno-type" bind:value={annotationType} class="w-full rounded border p-2">
				<option value="text">Text</option>
				<option value="image">Image</option>
				<option value="audio">Audio</option>
				<option value="video">Video</option>
				<option value="media_ref">Media Reference</option>
			</select>
		</div>
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-tags">Tags (comma-separated)</label>
			<input
				id="anno-tags"
				type="text"
				bind:value={newAnnotation.tags}
				placeholder="e.g., important, review"
				class="w-full rounded border p-2"
			/>
		</div>
		<div class="flex justify-end space-x-2">
			<button
				class="rounded bg-gray-300 px-4 py-2 text-black hover:bg-gray-400"
				onclick={() => (showAnnotationModal = false)}>Cancel</button
			>
			<button
				class="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
				onclick={() => void submitAnnotation()}>Create Annotation</button
			>
		</div>
	</div>
</div>
