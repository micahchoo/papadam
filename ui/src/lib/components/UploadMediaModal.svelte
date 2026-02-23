<script>
	import { selectedGroupMedia, selectedGroupDetails } from '$lib/stores';
	import { uploadMedia } from '$lib/services/api.js';

	export let showUploadModal;

	let mediaName = '';
	let mediaDescription = '';
	let tags = '';
	let previewUrl = '';

	let mediaFile;
	let selectedGroupId;

	$: if ($selectedGroupDetails) {
		selectedGroupId = $selectedGroupDetails.id;
	}

	// Close modal
	const closeUploadModal = () => {
		showUploadModal = false;
		mediaFile = null;
		mediaName = '';
		mediaDescription = '';
		tags = '';
		previewUrl = '';
	};

	// Handle file input and preview
	const handleFileChange = (event) => {
		const file = event.target.files[0];
		if (file) {
			previewUrl = URL.createObjectURL(file);
			mediaFile = file;
		}
	};

	// Submit media
	const submitMedia = async () => {
		if (mediaFile && selectedGroupId && mediaName && mediaDescription) {
			const tagArray = tags.split(',').map((tag) => tag.trim()); // Convert tags to an array

			try {
				let response = await uploadMedia(
					selectedGroupId,
					mediaFile,
					mediaName,
					mediaDescription,
					tagArray
				); // Correct order of parameterse)
				$selectedGroupMedia.push(response);
				$selectedGroupMedia = $selectedGroupMedia;
				// await loadGroupData(selectedGroupId); // Refresh the recordings
				closeUploadModal();
			} catch (error) {
				console.error('Error uploading media:', error);
			}
		} else {
			console.warn('Please fill in all fields before submitting.');
		}
	};
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-gray-800 bg-opacity-50">
	<div class="w-full max-w-4xl max-h-screen overflow-y-auto rounded-lg bg-white p-6 shadow-lg">
		<h2 class="mb-6 text-center text-2xl font-bold text-gray-700">
			Upload Media to {$selectedGroupDetails.name}
		</h2>
		<div class="grid grid-cols-1 gap-8 md:grid-cols-2">
			<div>
				<label class="mb-2 block text-sm font-medium text-gray-600">Media Name</label>
				<input
					type="text"
					bind:value={mediaName}
					placeholder="Enter media name"
					class="mb-4 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
				/>

				<label class="mb-2 block text-sm font-medium text-gray-600">Description</label>
				<textarea
					bind:value={mediaDescription}
					placeholder="Enter media description"
					class="mb-4 h-28 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
				></textarea>

				<label class="mb-2 block text-sm font-medium text-gray-600">Tags (comma-separated)</label>
				<input
					type="text"
					bind:value={tags}
					placeholder="e.g., nature, city, people"
					class="mb-4 w-full rounded border border-gray-300 px-4 py-2 focus:outline-none focus:ring focus:ring-blue-200"
				/>
			</div>

			<div class="flex flex-col items-center">
				<label class="mb-2 block text-sm font-medium text-gray-600">Upload Media</label>
				<input
					type="file"
					on:change={handleFileChange}
					class="mb-4 w-full rounded border border-gray-300 px-3 py-2 focus:outline-none"
				/>
				{#if previewUrl}
					<div class="mt-4">
						<video controls src={previewUrl} class="w-full rounded-md shadow-md" />
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
				on:click={closeUploadModal}
			>
				Cancel
			</button>
			<button
				class="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
				on:click={submitMedia}
			>
				Submit
			</button>
		</div>
	</div>
</div>
