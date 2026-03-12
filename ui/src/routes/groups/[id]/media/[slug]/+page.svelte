<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import DOMPurify from 'dompurify';
	import { archive, annotations as annoApi, mediaRelation } from '$lib/api';
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

	// Cross-media references (marginalia)
	let mediaRefs = $state<Annotation[]>([]);
	let annotationError = $state<string | null>(null);
	let annotationRetrying = $state(false);

	async function loadAnnotations(): Promise<void> {
		annotationError = null;
		annotationRetrying = false;
		try {
			const annoResp = await annoApi.byMedia(mediaUuid);
			annotations = annoResp.data;
		} catch {
			annotationError = 'Annotations unavailable';
		}
	}

	function retryAnnotations(): void {
		annotationRetrying = true;
		void loadAnnotations().finally(() => { annotationRetrying = false; });
	}

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
		await loadAnnotations();
		// Load cross-media references
		try {
			const { data } = await mediaRelation.mediaRefs(mediaUuid);
			mediaRefs = data;
		} catch {
			// Silently fail — marginalia is supplementary
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

	function handleAnnotationUpdated(updated: Annotation) {
		annotations = annotations.map((a) => (a.uuid === updated.uuid ? updated : a));
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
	<div class="flex h-screen items-center justify-center">
		<p class="font-body text-gray-500">Loading...</p>
	</div>
{:else if error}
	<div class="mx-4 mt-4 border border-red-300 bg-red-50 px-4 py-3 font-body text-sm text-red-700" role="alert">
		<span>{error}</span>
	</div>
{:else if recording}
	<div class="mx-auto max-w-6xl px-4 py-6">
		<!-- Back + options -->
		<div class="mb-4 flex items-center justify-between">
			<button
				class="font-body text-sm text-gray-500 hover:underline"
				onclick={() => window.history.back()}
			>&larr; Back</button>
			<div class="relative">
				<button
					class="px-3 py-1 font-body text-sm text-gray-500 hover:bg-gray-100"
					onclick={() => (showMenu = !showMenu)}
					aria-label="Options"
				>&hellip;</button>
				{#if showMenu}
					<div class="absolute right-0 top-8 z-10 border border-gray-200 bg-white shadow-sm">
						<button
							class="block w-full px-4 py-2 text-left font-body text-sm hover:bg-gray-50"
							onclick={editMedia}>Edit</button>
						<button
							class="block w-full px-4 py-2 text-left font-body text-sm text-red-600 hover:bg-gray-50"
							onclick={() => {
								showDeleteConfirmation = true;
								showMenu = false;
							}}>Delete</button>
					</div>
				{/if}
			</div>
		</div>

		<!-- Main layout: media + annotations side-by-side (newspaper editorial) -->
		<div class="grid grid-cols-1 gap-8 lg:grid-cols-12">
			<!-- Left column: player + metadata -->
			<div class="lg:col-span-7">
				{#if recording.upload}
					<MediaPlayer
						bind:this={mediaPlayerRef}
						src={recording.upload}
						controls={true}
						{imageAnnotations}
						transcriptUrl={recording.transcript_vtt_url}
					/>
				{:else}
					<div class="flex h-48 items-center justify-center bg-gray-100 font-body text-sm text-gray-500">
						Media is being processed. Refresh the page to check progress.
					</div>
				{/if}

				{#if $showTranscript && recording.transcript_vtt_url}
					<div class="mt-3">
						{#if transcriptText === null}
							<button
								class="font-body text-sm text-gray-500 underline"
								onclick={() => {
									if (recording?.transcript_vtt_url) void loadTranscript(recording.transcript_vtt_url);
								}}
							>
								Show transcript
							</button>
						{:else if loadingTranscript}
							<p class="font-body text-sm text-gray-400">Loading transcript…</p>
						{:else if transcriptText}
							<details open>
								<summary class="cursor-pointer font-body text-sm font-medium text-gray-700">Transcript</summary>
								<p class="mt-2 font-body text-sm leading-relaxed text-gray-600">{transcriptText}</p>
							</details>
						{:else}
							<p class="font-body text-sm text-gray-400">Transcript unavailable.</p>
						{/if}
					</div>
				{/if}

				<header class="mt-6 border-b border-gray-200 pb-4">
					<h1 class="font-heading text-3xl font-black tracking-tight">{recording.name}</h1>
					<p class="mt-1 font-body text-sm text-gray-500">
						{new Date(recording.created_at).toLocaleDateString($dateLocale, {
							day: 'numeric',
							month: 'short',
							year: 'numeric'
						})}
					</p>
					{#if recording.tags.length > 0}
						<div class="mt-2 flex flex-wrap gap-2">
							{#each recording.tags as tag}
								{#if tag.name && tag.count > 0 && tag.name.length <= 30}
									<span class="font-body text-xs uppercase tracking-wider text-gray-500">
										{tag.name}
									</span>
								{/if}
							{/each}
						</div>
					{/if}
				</header>
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				<div class="mt-4 font-body leading-relaxed text-gray-700">
					{@html DOMPurify.sanitize(recording.description)}
				</div>
			</div>

			<!-- Right column: annotations as editorial marginalia -->
			<aside class="border-l border-gray-200 pl-6 lg:col-span-5">
				<div class="sticky top-20">
					<div class="mb-4 flex items-baseline justify-between border-b border-gray-900 pb-2">
						<h3 class="font-heading text-lg font-bold">Annotations</h3>
						<button
							class="border border-gray-900 px-3 py-1 font-body text-xs tracking-wide hover:bg-gray-900 hover:text-white"
							onclick={() => (showAnnotationModal = true)}
						>
							+ New
						</button>
					</div>
					{#if annotationError}
						<div class="py-4 text-center">
							<p class="mb-2 font-body text-sm text-red-700">{annotationError}</p>
							<button
								class="font-body text-sm text-gray-600 underline-offset-2 hover:underline"
								disabled={annotationRetrying}
								onclick={retryAnnotations}
							>{annotationRetrying ? 'Retrying...' : 'Retry'}</button>
						</div>
					{:else}
						<AnnotationViewer
							{annotations}
							onPlaySnippet={handlePlaySnippet}
							{formatTime}
							onAnnotationDeleted={handleAnnotationDeleted}
							onAnnotationUpdated={handleAnnotationUpdated}
						/>
					{/if}
				</div>
			</aside>
		</div>

		<!-- Cross-media references ("See also" marginalia) — below on mobile, sidebar on desktop -->
		{#if mediaRefs.length > 0}
			<section class="mt-10 border-t border-gray-200 pt-6 lg:mt-8">
				<h3 class="mb-3 font-heading text-lg font-bold">Referenced in</h3>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
					{#each mediaRefs as ref}
						<a
							href="/groups/{recording.group.id}/media/{ref.media_reference_id}"
							class="block border-l-2 border-gray-300 py-2 pl-4 hover:border-gray-900"
						>
							<p class="font-body text-sm font-medium text-gray-900">
								{ref.media_reference_id}
							</p>
							<p class="mt-1 line-clamp-2 font-body text-xs text-gray-500">
								{ref.annotation_text || 'No description'}
							</p>
						</a>
					{/each}
				</div>
			</section>
		{/if}
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
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
			<div class="border border-gray-200 bg-white p-6 shadow-lg">
				<h2 class="font-heading text-lg font-bold">Confirm Delete</h2>
				<p class="mt-2 font-body text-sm text-gray-700">Are you sure you want to delete this media?</p>
				<div class="mt-4 flex justify-end gap-3">
					<button
						class="border border-gray-300 px-4 py-2 font-body text-sm hover:bg-gray-100"
						onclick={() => (showDeleteConfirmation = false)}>Cancel</button>
					<button
						class="border border-red-500 px-4 py-2 font-body text-sm text-red-600 hover:bg-red-50"
						onclick={() => void deleteMedia()}>Delete</button>
				</div>
			</div>
		</div>
	{/if}
{/if}
