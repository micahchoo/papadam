<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { archive } from '$lib/api';
	import { pollJob } from '$lib/events';
	import type { JobPoller } from '$lib/events';
	import { selectedGroupDetails, groupMediaList } from '$lib/stores';
	import { getQueuedUploads, discardUpload, type QueuedUpload } from '$lib/upload-queue';

	interface Props {
		showUploadModal: boolean;
	}
	let { showUploadModal = $bindable() }: Props = $props();

	let mediaName = $state('');
	let mediaDescription = $state('');
	let tags = $state('');
	let previewUrl = $state('');
	let mediaFile = $state<File | null>(null);
	let uploadState = $state<'idle' | 'uploading' | 'processing' | 'done' | 'error'>('idle');
	let processingStatus = $state('');
	let activePoller: JobPoller | null = null;

	const selectedGroupId = $derived($selectedGroupDetails?.id ?? null);

	let queuedUploads = $state<QueuedUpload[]>([]);

	async function refreshQueue() {
		queuedUploads = await getQueuedUploads();
	}

	async function handleDiscard(id: number) {
		await discardUpload(id);
		await refreshQueue();
	}

	onMount(() => {
		void refreshQueue();
	});

	// Auto-close a beat after processing completes
	$effect(() => {
		if (uploadState === 'done') {
			setTimeout(() => closeUploadModal(), 1_200);
		}
	});

	onDestroy(() => {
		activePoller?.stop();
	});

	function closeUploadModal() {
		activePoller?.stop();
		activePoller = null;
		showUploadModal = false;
		mediaFile = null;
		mediaName = '';
		mediaDescription = '';
		tags = '';
		previewUrl = '';
		uploadState = 'idle';
		processingStatus = '';
	}

	function handleFileChange(event: Event) {
		const file = (event.target as HTMLInputElement).files?.[0];
		if (file) {
			previewUrl = URL.createObjectURL(file);
			mediaFile = file;
		}
	}

	async function submitMedia() {
		if (!mediaFile || !selectedGroupId || !mediaName || !mediaDescription) return;
		const formData = new FormData();
		formData.append('name', mediaName);
		formData.append('description', mediaDescription);
		formData.append('tags', tags);
		formData.append('group', String(selectedGroupId));
		formData.append('upload', mediaFile);

		uploadState = 'uploading';
		try {
			const { data: newMedia } = await archive.create(formData);
			groupMediaList.update((list) => [...list, newMedia]);

			if (newMedia.job_id) {
				uploadState = 'processing';
				processingStatus = 'Queued…';
				activePoller = pollJob(newMedia.job_id, (status) => {
					if (status === 'complete') {
						processingStatus = 'Complete!';
						uploadState = 'done';
					} else if (status === 'failed' || status === 'not_found') {
						processingStatus = 'Processing failed';
						uploadState = 'error';
					} else {
						processingStatus = status === 'in_progress' ? 'Converting…' : 'Queued…';
					}
				});
			} else {
				// No conversion needed (e.g. unknown media type) — close immediately
				closeUploadModal();
			}
		} catch (err) {
			console.error('Error uploading media:', err);
			uploadState = 'error';
			processingStatus = 'Upload failed';
		}
	}
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-gray-800 bg-opacity-50">
	<div class="max-h-screen w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
		<h2 class="mb-6 text-center text-2xl font-bold text-gray-700">
			Upload Media to {$selectedGroupDetails?.name ?? '...'}
		</h2>

		{#if uploadState === 'uploading' || uploadState === 'processing' || uploadState === 'done'}
			<div class="flex flex-col items-center gap-4 py-10">
				{#if uploadState === 'uploading'}
					<p class="text-gray-600">Uploading…</p>
				{:else if uploadState === 'done'}
					<p class="font-semibold text-green-600">{processingStatus}</p>
				{:else}
					<p class="text-blue-600">{processingStatus}</p>
					<div
						class="loader h-10 w-10 rounded-full border-4 border-t-4 border-gray-200 ease-linear"
					></div>
				{/if}
			</div>
		{:else}
			<div class="grid grid-cols-1 gap-8 md:grid-cols-2">
				<div>
					<label class="mb-2 block text-sm font-medium text-gray-600" for="upload-name"
						>Media Name</label
					>
					<input
						id="upload-name"
						type="text"
						bind:value={mediaName}
						placeholder="Enter media name"
						class="mb-4 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
					/>
					<label class="mb-2 block text-sm font-medium text-gray-600" for="upload-desc"
						>Description</label
					>
					<textarea
						id="upload-desc"
						bind:value={mediaDescription}
						placeholder="Enter media description"
						class="mb-4 h-28 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
					></textarea>
					<label class="mb-2 block text-sm font-medium text-gray-600" for="upload-tags"
						>Tags (comma-separated)</label
					>
					<input
						id="upload-tags"
						type="text"
						bind:value={tags}
						placeholder="e.g., nature, city, people"
						class="mb-4 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
					/>
					{#if uploadState === 'error'}
						<p class="text-sm text-red-600">{processingStatus}</p>
					{/if}
				</div>
				<div class="flex flex-col items-center">
					<label class="mb-2 block text-sm font-medium text-gray-600" for="upload-file"
						>Upload Media</label
					>
					<input
						id="upload-file"
						type="file"
						onchange={handleFileChange}
						class="mb-4 w-full rounded border border-gray-300 px-3 py-2 focus:outline-none"
					/>
					{#if previewUrl}
						<div class="mt-4">
							<video controls src={previewUrl} class="w-full rounded-md shadow-md"
								><track kind="captions" src="" label="Captions" /></video
							>
						</div>
					{:else}
						<div
							class="mt-4 flex h-48 w-full items-center justify-center rounded-md bg-gray-100 text-gray-400"
						>
							No preview available
						</div>
					{/if}
				</div>
			</div>
			<div class="mt-6 flex justify-between">
				<button
					class="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600"
					onclick={closeUploadModal}>Cancel</button
				>
				<button
					class="rounded bg-brand-primary px-4 py-2 text-white hover:opacity-90"
					onclick={() => void submitMedia()}>Submit</button
				>
			</div>

			{#if queuedUploads.length > 0}
				<div class="mt-6 border-t border-gray-200 pt-4">
					<h3 class="mb-2 text-sm font-semibold text-gray-500">
						Pending uploads ({queuedUploads.length})
					</h3>
					<ul class="space-y-2">
						{#each queuedUploads as upload (upload.id)}
							<li class="flex items-center justify-between rounded bg-amber-50 px-3 py-2 text-sm">
								<span class="truncate text-gray-700">{upload.url}</span>
								<button
									class="ml-2 text-xs text-red-600 hover:underline"
									onclick={() => void handleDiscard(upload.id)}
								>
									Discard
								</button>
							</li>
						{/each}
					</ul>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.loader {
		border-top-color: var(--brand-accent);
		animation: spin 0.6s linear infinite;
	}
	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
