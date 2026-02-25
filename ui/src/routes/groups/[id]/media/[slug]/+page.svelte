<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import DOMPurify from 'dompurify';
	import { archive, annotations as annoApi } from '$lib/api';
	import type { MediaStore, Annotation } from '$lib/api';
	import { showTranscript, dateLocale } from '$lib/stores';
	import AnnotationViewer from '$lib/components/AnnotationViewer.svelte';
	import MediaPlayer from '$lib/components/MediaPlayer.svelte';
	import type { ImageAnnotation } from '$lib/components/MediaPlayer.svelte';
	import UploadAnnotationModal from '$lib/components/UploadAnnotationModal.svelte';
	import EditMediaModal from '$lib/components/EditMediaModal.svelte';

	const mediaUuid = $derived($page.params['slug'] ?? '');

	let recording = $state<MediaStore | null>(null);
	let annotations = $state<Annotation[]>([]);
	let loading = $state(true);
	let error = $state('');
	let showAnnotationModal = $state(false);
	let showEditModal = $state(false);
	let showDeleteConfirmation = $state(false);
	let showMenu = $state(false);

	// Edit modal fields (bound)
	let mediaName = $state('');
	let mediaDescription = $state('');

	let mediaPlayerRef = $state<{ playSnippet: (start: number, end: number) => void } | null>(null);
	let transcriptText = $state<string | null>(null);
	let loadingTranscript = $state(false);

	/** Image annotations whose annotation_image is set — passed to MediaPlayer for overlay. */
	const imageAnnotations = $derived(
		annotations
			.filter(
				(a): a is Annotation & { annotation_image: string } =>
					a.annotation_type === 'image' && a.annotation_image !== null
			)
			.map(
				(a): ImageAnnotation => ({
					media_target: a.media_target,
					annotation_image: a.annotation_image
				})
			)
	);

	onMount(async () => {
		try {
			const mediaResp = await archive.get(mediaUuid);
			recording = mediaResp.data;
		} catch {
			error = 'Failed to load media.';
		} finally {
			loading = false;
		}
		// Load annotations independently — don't block player render
		try {
			const annoResp = await annoApi.byMedia(mediaUuid);
			annotations = annoResp.data;
		} catch {
			// Annotations fail silently — player still works
		}
	});

	function formatTime(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = Math.floor(seconds % 60);
		return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
	}

	function handlePlaySnippet(start: number, end: number) {
		mediaPlayerRef?.playSnippet(start, end);
	}

	/** Strip VTT metadata lines; return joined cue text. */
	function parseVtt(raw: string): string {
		return raw
			.split('\n')
			.filter(
				(l) => l && !l.startsWith('WEBVTT') && !/^\d+$/.test(l) && !l.includes(' --> ')
			)
			.join(' ')
			.replace(/\s+/g, ' ')
			.trim();
	}

	async function loadTranscript(url: string) {
		loadingTranscript = true;
		try {
			const resp = await fetch(url);
			if (!resp.ok) throw new Error(`${resp.status}`);
			transcriptText = parseVtt(await resp.text());
		} catch {
			transcriptText = '';
		} finally {
			loadingTranscript = false;
		}
	}

	function handleAnnotationDeleted(id: number) {
		annotations = annotations.filter((a) => a.id !== id);
	}

	function editMedia() {
		if (!recording) return;
		mediaName = recording.name;
		mediaDescription = recording.description;
		showMenu = false;
		showEditModal = true;
	}

	async function deleteMedia() {
		if (!recording) return;
		loading = true;
		try {
			await archive.delete(recording.uuid);
			await goto('..');
		} catch (err) {
			console.error('Error deleting media:', err);
			error = 'An error occurred during deletion.';
		} finally {
			loading = false;
			showDeleteConfirmation = false;
		}
	}
</script>

{#if loading}
	<div class="flex h-screen items-center justify-center"><p>Loading...</p></div>
{:else if error}
	<div class="rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700" role="alert">
		<span>{error}</span>
	</div>
{:else if recording}
	{#if error}
		<div class="mx-4 mt-4 rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700" role="alert">
			<span>{error}</span>
		</div>
	{/if}
	<div class="mx-auto flex h-full max-w-5xl flex-col md:h-screen md:flex-row">
		<!-- Left: player + metadata -->
		<div class="w-full flex-shrink-0 overflow-y-auto p-6 md:w-1/2">
			<div class="relative">
				<button class="mb-2 text-sm text-blue-600 underline" onclick={() => window.history.back()}
					>← Back</button
				>
				<button
					class="absolute right-0 top-0 rounded bg-gray-200 px-3 py-1 text-sm"
					onclick={() => (showMenu = !showMenu)}
					aria-label="Options">⋮</button
				>
				{#if showMenu}
					<div class="absolute right-0 top-8 z-10 rounded bg-white shadow-md">
						<button
							class="block w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
							onclick={editMedia}>Edit</button
						>
						<button
							class="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100"
							onclick={() => {
								showDeleteConfirmation = true;
								showMenu = false;
							}}>Delete</button
						>
					</div>
				{/if}
			</div>

			{#if recording.upload}
				<MediaPlayer
					bind:this={mediaPlayerRef}
					src={recording.upload}
					controls={true}
					{imageAnnotations}
					transcriptUrl={recording.transcript_vtt_url}
				/>
			{:else}
				<div class="flex h-48 items-center justify-center rounded bg-gray-200 text-sm text-gray-600">
					Media is being processed. Refresh the page to check progress.
				</div>
			{/if}
			{#if $showTranscript && recording.transcript_vtt_url}
				<div class="mt-3">
					{#if transcriptText === null}
						<button
							class="text-sm text-blue-600 underline"
							onclick={() => {
							if (recording?.transcript_vtt_url) void loadTranscript(recording.transcript_vtt_url);
						}}
						>
							Show transcript
						</button>
					{:else if loadingTranscript}
						<p class="text-sm text-gray-500">Loading transcript…</p>
					{:else if transcriptText}
						<details open>
							<summary class="cursor-pointer text-sm font-medium text-gray-700">Transcript</summary>
							<p class="mt-2 text-sm leading-relaxed text-gray-600">{transcriptText}</p>
						</details>
					{:else}
						<p class="text-sm text-gray-400">Transcript unavailable.</p>
					{/if}
				</div>
			{/if}

			<h1 class="mt-4 text-2xl font-bold">{recording.name}</h1>
			<p class="text-sm text-gray-500">
				{new Date(recording.created_at).toLocaleDateString($dateLocale)}
			</p>
			<div class="py-2">
				{#each recording.tags as tag}
					{#if tag.name && tag.count > 0 && tag.name.length <= 30}
						<span
							class="mr-1 inline-flex bg-gray-200 px-2 py-1 text-xs font-semibold uppercase text-gray-600"
						>
							{tag.name}
						</span>
					{/if}
				{/each}
			</div>
			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			<p class="my-3">{@html DOMPurify.sanitize(recording.description)}</p>
		</div>

		<!-- Right: annotations -->
		<div class="overflow-y-auto p-6 md:w-1/2">
			<div class="bg-gray-100">
				<div class="sticky top-0 z-10 flex flex-col bg-gray-100">
					<h3 class="py-4 text-lg font-semibold">Annotations</h3>
					<button
						class="mb-4 rounded bg-brand-accent px-4 py-2 text-white hover:opacity-90 md:w-1/2"
						onclick={() => (showAnnotationModal = true)}
					>
						+ Create Annotation
					</button>
				</div>
							<div class="mt-2">
						<AnnotationViewer
							{annotations}
							onPlaySnippet={handlePlaySnippet}
							{formatTime}
							onAnnotationDeleted={handleAnnotationDeleted}
						/>
					</div>
			</div>
		</div>
	</div>

	{#if showAnnotationModal}
		<UploadAnnotationModal bind:showAnnotationModal {recording} bind:annotations />
	{/if}

	{#if showEditModal}
		<EditMediaModal
			bind:showEditModal
			bind:mediaName
			bind:mediaDescription
			recordingUuid={recording.uuid}
		/>
	{/if}

	{#if showDeleteConfirmation}
		<div class="fixed inset-0 z-10 flex items-center justify-center bg-black bg-opacity-50">
			<div class="rounded-lg bg-white p-6 shadow-lg">
				<h2 class="text-lg font-semibold">Confirm Delete</h2>
				<p class="mt-2 text-gray-700">Are you sure you want to delete this media?</p>
				<div class="mt-4 flex justify-end space-x-4">
					<button
						class="rounded bg-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-400"
						onclick={() => (showDeleteConfirmation = false)}>Cancel</button
					>
					<button
						class="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
						onclick={() => void deleteMedia()}>Delete</button
					>
				</div>
			</div>
		</div>
	{/if}
{/if}
