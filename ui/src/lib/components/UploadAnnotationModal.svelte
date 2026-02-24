<script lang="ts">
	import { annotations as annoApi } from '$lib/api';
	import type { Annotation, AnnotationType, MediaStore } from '$lib/api';
	import {
		selectedMediaDuration,
		allowedAnnotationTypes,
		timeRangeInputMode,
		playbackPosition
	} from '$lib/stores';

	const TYPE_LABELS: Record<AnnotationType, string> = {
		text: 'Text',
		image: 'Image',
		audio: 'Audio',
		video: 'Video',
		media_ref: 'Media Reference'
	};

	interface Props {
		showAnnotationModal: boolean;
		recording: MediaStore;
		annotations: Annotation[];
	}
	let { showAnnotationModal = $bindable(), recording, annotations = $bindable() }: Props = $props();

	let newAnnotation = $state({ start: 0, end: 0, description: '', tags: '' });
	let annotationType = $state<AnnotationType>('text');
	let imageFile = $state<File | null>(null);
	let audioFile = $state<File | null>(null);
	let videoFile = $state<File | null>(null);
	let mediaRefUuid = $state('');

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
			if (annotationType === 'image' && imageFile) {
				formData.append('annotation_image', imageFile);
			}
			if (annotationType === 'media_ref' && mediaRefUuid.trim()) {
				formData.append('media_ref_uuid', mediaRefUuid.trim());
			}
			if (annotationType === 'audio' && audioFile) {
				formData.append('annotation_audio', audioFile);
			}
			if (annotationType === 'video' && videoFile) {
				formData.append('annotation_video', videoFile);
			}
			const { data: created } = await annoApi.create(formData);
			annotations = [...annotations, created];
			newAnnotation = { start: 0, end: 0, description: '', tags: '' };
			annotationType = 'text';
			imageFile = null;
			audioFile = null;
			videoFile = null;
			mediaRefUuid = '';
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
	function handleImageChange(e: Event) {
		imageFile = (e.target as HTMLInputElement).files?.[0] ?? null;
	}
	function handleAudioChange(e: Event) {
		audioFile = (e.target as HTMLInputElement).files?.[0] ?? null;
	}
	function handleVideoChange(e: Event) {
		videoFile = (e.target as HTMLInputElement).files?.[0] ?? null;
	}
	/** Parse MM:SS timestamp string → seconds, or null if invalid. */
	function parseTimestamp(s: string): number | null {
		const m = /^(\d{1,2}):(\d{2})$/.exec(s.trim());
		if (!m?.[1] || !m[2]) return null;
		const mins = parseInt(m[1], 10);
		const secs = parseInt(m[2], 10);
		if (secs >= 60) return null;
		return mins * 60 + secs;
	}
	function handleTimestampStart(e: Event) {
		const val = parseTimestamp((e.target as HTMLInputElement).value);
		if (val !== null) {
			newAnnotation.start = val;
			if (val > newAnnotation.end) newAnnotation.end = val;
		}
	}
	function handleTimestampEnd(e: Event) {
		const val = parseTimestamp((e.target as HTMLInputElement).value);
		if (val !== null) {
			const clamped = Math.min(val, duration);
			newAnnotation.end = clamped;
			if (clamped < newAnnotation.start) newAnnotation.start = clamped;
		}
	}
	/** Capture current playback position as start time (tap mode). */
	function tapSetStart() {
		newAnnotation.start = $playbackPosition;
		if (newAnnotation.start > newAnnotation.end) newAnnotation.end = newAnnotation.start;
	}
	/** Capture current playback position as end time (tap mode). */
	function tapSetEnd() {
		newAnnotation.end = Math.min($playbackPosition, duration);
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

		<!-- Time range — slider or tap mode -->
		{#if $timeRangeInputMode === 'tap'}
			<div class="mb-4">
				<p class="mb-2 text-sm font-medium">Time Range</p>
				<div class="flex items-center gap-3">
					<button
						onclick={tapSetStart}
						class="rounded bg-green-100 px-3 py-1 text-sm text-green-800 hover:bg-green-200"
					>
						Set start ({formatTime(newAnnotation.start)})
					</button>
					<button
						onclick={tapSetEnd}
						class="rounded bg-red-100 px-3 py-1 text-sm text-red-800 hover:bg-red-200"
					>
						Set end ({formatTime(newAnnotation.end)})
					</button>
					<span class="text-xs text-gray-500">Now: {formatTime($playbackPosition)}</span>
				</div>
			</div>
		{:else if $timeRangeInputMode === 'timestamp'}
			<div class="mb-4">
				<p class="mb-2 text-sm font-medium">Time Range (MM:SS)</p>
				<div class="flex items-center gap-3">
					<label class="text-sm" for="ts-start">Start</label>
					<input
						id="ts-start"
						type="text"
						placeholder="00:00"
						value={formatTime(newAnnotation.start)}
						oninput={handleTimestampStart}
						class="w-24 rounded border p-1 font-mono text-sm"
					/>
					<label class="text-sm" for="ts-end">End</label>
					<input
						id="ts-end"
						type="text"
						placeholder="00:00"
						value={formatTime(newAnnotation.end)}
						oninput={handleTimestampEnd}
						class="w-24 rounded border p-1 font-mono text-sm"
					/>
				</div>
			</div>
		{:else}
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
		{/if}

		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium" for="anno-type">Annotation Type</label>
			<select id="anno-type" bind:value={annotationType} class="w-full rounded border p-2">
				{#each $allowedAnnotationTypes as type}
					<option value={type}>{TYPE_LABELS[type]}</option>
				{/each}
			</select>
		</div>

		<!-- Type-specific body fields -->
		{#if annotationType === 'image'}
			<div class="mb-4">
				<label class="mb-2 block text-sm font-medium" for="anno-image">Image file</label>
				<input
					id="anno-image"
					type="file"
					accept="image/*"
					onchange={handleImageChange}
					class="w-full text-sm"
				/>
			</div>
		{:else if annotationType === 'audio'}
			<div class="mb-4">
				<label class="mb-2 block text-sm font-medium" for="anno-audio">Audio file</label>
				<input
					id="anno-audio"
					type="file"
					accept="audio/*"
					onchange={handleAudioChange}
					class="w-full text-sm"
				/>
			</div>
		{:else if annotationType === 'video'}
			<div class="mb-4">
				<label class="mb-2 block text-sm font-medium" for="anno-video">Video file</label>
				<input
					id="anno-video"
					type="file"
					accept="video/*"
					onchange={handleVideoChange}
					class="w-full text-sm"
				/>
			</div>
		{:else if annotationType === 'media_ref'}
			<div class="mb-4">
				<label class="mb-2 block text-sm font-medium" for="anno-media-ref">Referenced media UUID</label>
				<input
					id="anno-media-ref"
					type="text"
					bind:value={mediaRefUuid}
					placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
					class="w-full rounded border p-2 font-mono text-sm"
				/>
			</div>
		{/if}

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
