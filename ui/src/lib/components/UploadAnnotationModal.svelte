<script>
	import { uploadAnnotation } from '$lib/services/api.js';
    import { selectedMediaDuration } from '$lib/stores'; // Assuming selectedMediaDuration is a writable store
	export let showAnnotationModal;
	export let recording; // Contains the metadata of the media
	export let annotations;

	let newAnnotation = {
		start: 0,
		end: 0,
		description: '',
		tags: ''
	};

	async function submitAnnotation() {
		try {
			// Call the API to create a new annotation
			const tempNewAnnotation = await uploadAnnotation(
				recording.uuid,
				newAnnotation.description,
				newAnnotation.tags,
				newAnnotation.start,
				newAnnotation.end
			);

			// Update annotations list
			annotations.push(tempNewAnnotation);
			annotations = [...annotations]; // Ensure reactivity

			// Reset new annotation form
			newAnnotation = {
				start: 0,
				end: 0,
				description: '',
				tags: ''
			};
		} catch (err) {
			console.error('Failed to create annotation:', err);
		} finally {
			showAnnotationModal = false;
		}
	}

	function handleStartChange(event) {
		newAnnotation.start = parseFloat(event.target.value);

		// Ensure start time is less than or equal to end time
		if (newAnnotation.start > newAnnotation.end) {
			newAnnotation.end = newAnnotation.start;
		}
	}

	function handleEndChange(event) {
		newAnnotation.end = parseFloat(event.target.value);

		// Ensure end time is greater than or equal to start time
		if (newAnnotation.end < newAnnotation.start) {
			newAnnotation.start = newAnnotation.end;
		}

		// Ensure end time doesn't exceed the media duration
		if (newAnnotation.end > $selectedMediaDuration) {
			newAnnotation.end = $selectedMediaDuration;
		}
	}

	// Utility function to format seconds into mm:ss
	function formatTime(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = Math.floor(seconds % 60);
		return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
	}
</script>

<div
	class="fixed inset-0 top-0 z-10 flex h-full items-center justify-center bg-black bg-opacity-50"
>
	<div class="w-[500px] rounded-lg bg-white p-6">
		<h2 class="mb-4 text-xl font-bold">Create New Annotation</h2>

		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium">Start Time</label>
			<div class="flex items-center space-x-2">
				<input
					type="range"
					min="0"
					max={$selectedMediaDuration}
					step="0.1"
					bind:value={newAnnotation.start}
					on:input={handleStartChange}
					class="w-full appearance-none bg-green-400 h-2 rounded-full"
					style="background: linear-gradient(to right, #22c55e 0%, #22c55e {newAnnotation.start / $selectedMediaDuration * 100}%, #d1d5db {newAnnotation.start / $selectedMediaDuration * 100}% 100%)"
				/>
				<span>{formatTime(newAnnotation.start)}</span>
			</div>
		</div>
		
		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium">End Time</label>
			<div class="flex items-center space-x-2">
				<input
					type="range"
					min="0"
					max={$selectedMediaDuration}
					step="0.1"
					bind:value={newAnnotation.end}
					on:input={handleEndChange}
					class="w-full appearance-none bg-red-400 h-2 rounded-full"
					style="background: linear-gradient(to right, #ef4444 0%, #ef4444 {newAnnotation.end / $selectedMediaDuration * 100}%, #d1d5db {newAnnotation.end / $selectedMediaDuration * 100}% 100%)"
				/>
				<span>{formatTime(newAnnotation.end)}</span>
			</div>
		</div>		

		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium">Description</label>
			<textarea
				bind:value={newAnnotation.description}
				placeholder="Enter annotation description"
				class="w-full rounded border p-2"
			></textarea>
		</div>

		<div class="mb-4">
			<label class="mb-2 block text-sm font-medium">Tags (comma-separated)</label>
			<input
				type="text"
				bind:value={newAnnotation.tags}
				placeholder="e.g., important, review, key moment"
				class="w-full rounded border p-2"
			/>
		</div>

		<div class="flex justify-end space-x-2">
			<button
				class="rounded bg-gray-300 px-4 py-2 text-black hover:bg-gray-400"
				on:click={() => (showAnnotationModal = false)}
			>
				Cancel
			</button>
			<button
				class="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
				on:click={submitAnnotation}
			>
				Create Annotation
			</button>
		</div>
	</div>
</div>
