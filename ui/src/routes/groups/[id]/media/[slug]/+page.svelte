<script>
	import AnnotationViewer from '$lib/components/AnnotationViewer.svelte';
	import MediaPlayer from '$lib/components/MediaPlayer.svelte';
	import UploadAnnotationModal from '$lib/components/UploadAnnotationModal.svelte';
	import { deleteRecording } from '$lib/services/api.js';
	import EditMediaModal from '$lib/components/EditMediaModal.svelte';

	let mediaFile = null;
	let tags = ''; // Stores comma-separated tags for the new media
	let mediaName = ''; // Stores the name for the new media
	let mediaDescription = ''; // Stores the description for the new media
	let previewUrl = ''; // URL for the media preview
	let loading = false;
	let error = null;
	let showDeleteConfirmation = false; // State for showing delete confirmation modal

	export let data;
	let recording = data.mediaDetails;

	let annotations = recording.annotations;
	let playerUrl = recording.upload;

	// Formatting utility
	function formatTime(seconds) {
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = Math.floor(seconds % 60);
		return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
	}

	// Play snippet handler
	let mediaPlayerRef;
	function handlePlaySnippet(start, end) {
		if (mediaPlayerRef) {
			mediaPlayerRef.playSnippet(start, end);
		}
	}

	// Annotation creation state
	let showAnnotationModal = false;

	function openAnnotationModal() {
		showAnnotationModal = true;
	}

	let showEditModal = false; // State for showing the edit modal

	const editMedia = () => {
		if (recording) {
			toggleMenu()
			mediaName = recording.name; // Set current name
			mediaDescription = recording.description; // Set current description
			tags = recording.tags.map((tag) => tag.name).join(', '); // Set current tags
			mediaFile = recording.file; // Keep the existing file reference
			previewUrl = recording.upload; // Set preview URL for display
			showEditModal = true; // Open the edit modal for editing metadata
		}
	};

	const confirmDelete = () => {
		showDeleteConfirmation = true;
	};

	const cancelDelete = () => {
		showDeleteConfirmation = false;
		toggleMenu()
	};

	const deleteMedia = async () => {
		if (recording) {
			loading = true;
			try {
				await deleteRecording(recording.uuid);
				window.history.back();
			} catch (err) {
				console.error('Error deleting media:', err);
				error = err.response?.data?.detail || 'An error occurred during deletion.';
			} finally {
				loading = false;
				showDeleteConfirmation = false;
			}
		}
	};

	let showMenu = false;
	function toggleMenu() {
		showMenu = !showMenu;
	}
</script>

{#if loading}
	<div class="flex h-screen items-center justify-center">
		<p>Loading recording details...</p>
	</div>
{:else if error}
	<div
		class="relative rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700"
		role="alert"
	>
		<span class="block sm:inline">{error}</span>
	</div>
{:else if recording}
	<div class="mx-auto flex h-full min-h-screen p-5 md:h-screen md:max-w-6xl">
		<!-- Main Content -->
		<div class="flex h-full w-full flex-col gap-x-5 md:grid md:grid-cols-2">
			<!-- Media Player -->
			<div class="">
				<MediaPlayer bind:this={mediaPlayerRef} src={playerUrl} autoplay={false} />
				<div class="flex md: justify-between">
				<h1 class="text-2xl font-bold">{recording.name}</h1>
				<div class="relative">
					<button
						class="rounded px-4 py-2 text-black hover:bg-gray-300 text-xl font-black"
						on:click={toggleMenu}
					>
						⋮
					</button>
					{#if showMenu}
						<div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg">
							<button
								class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
								on:click={editMedia}
							>
								Edit
							</button>
							<button
								class="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
								on:click={confirmDelete}
							>
								Delete
							</button>
						</div>
					{/if}
				</div>
			</div>
				<div class="py-2">
					{#each recording.tags as tag}
						{#if tag.name && tag.count > 0 && tag.name.length <= 30}
							<span
								class="mr-1 inline-flex bg-blue-200 px-2 py-1 text-xs font-semibold uppercase text-blue-500"
							>
								{tag.name}
							</span>
						{/if}
					{/each}
				</div>
				<p class="my-3">{@html recording.description}</p>
			</div>
			<div class="overflow-y-auto">
				<!-- Annotations Panel -->
				<div class="bg-gray-100">
					<!-- Fixed Header Section -->
					<div class="sticky top-0 z-10 flex flex-col bg-gray-100 md:justify-between">
						<h3 class="py-4 text-lg font-semibold">Annotations</h3>
						<button
							class="mb-4 rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600 md:w-1/2"
							on:click={openAnnotationModal}
						>
							+ Create Annotation
						</button>
					</div>
					<!-- Scrollable Annotations List -->
					{#key annotations}
						<div class="mt-2">
							<AnnotationViewer {annotations} onPlaySnippet={handlePlaySnippet} {formatTime} />
						</div>
					{/key}
				</div>
			</div>
		</div>
	</div>

	<!-- Annotation Creation Modal -->
	{#if showAnnotationModal}
		<UploadAnnotationModal bind:showAnnotationModal bind:recording bind:annotations />
	{/if}

	<!-- Edit Media Modal -->
	{#if showEditModal}
		<EditMediaModal
			bind:showEditModal
			bind:mediaName
			bind:mediaDescription
			bind:tags
			bind:recordingUuid={recording.uuid}
		/>
	{/if}

	<!-- Delete Confirmation Modal -->
	{#if showDeleteConfirmation}
		<div class="fixed top-0 z-10 inset-0 flex items-center justify-center bg-black bg-opacity-50">
			<div class="bg-white rounded-lg p-6 shadow-lg">
				<h2 class="text-lg font-semibold">Confirm Delete</h2>
				<p class="mt-2 text-gray-700">Are you sure you want to delete this media?</p>
				<div class="mt-4 flex justify-end space-x-4">
					<button
						class="rounded bg-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-400"
						on:click={cancelDelete}
					>
						Cancel
					</button>
					<button
						class="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600"
						on:click={deleteMedia}
					>
						Delete
					</button>
				</div>
			</div>
		</div>
	{/if}
{/if}