<script>
    import {updateMedia} from '$lib/services/api.js';
    export let showEditModal = false;
    export let mediaName = '';
    export let mediaDescription = '';
    export let tags = '';
    export let recordingUuid;


    const submitEdit = async () => {
		// Validate the required fields
		if (mediaName && mediaDescription ) {
			const tagArray = tags.split(',').map((tag) => tag.trim()); // Convert tags to an array

			try {
				// Use the updateMedia function to make the API call
				await updateMedia(recordingUuid, mediaName, mediaDescription, tagArray);
				showEditModal = false; // Close the edit modal
			} catch (error) {
				console.error('Error updating media:', error);
			}
		} else {
			console.warn('Please fill in all fields before submitting.');
		}
	};

</script>
<div class="fixed inset-0 z-50 flex items-center justify-center">
    <div class="rounded bg-white p-6 shadow-md">
        <h2 class="text-lg font-bold">Edit Media</h2>
        <label>Name</label>
        <input type="text" bind:value={mediaName} class="mb-4 w-full rounded border p-2" />

        <label>Description</label>
        <textarea bind:value={mediaDescription} class="mb-4 w-full rounded border p-2"></textarea>

        <label>Tags</label>
        <input type="text" bind:value={tags} class="mb-4 w-full rounded border p-2" />

        <button on:click={submitEdit} class="rounded bg-blue-500 px-4 py-2 text-white">
            Save Changes
        </button>
        <button on:click={() => (showEditModal = false)} class="ml-2 rounded bg-gray-300 px-4 py-2">
            Cancel
        </button>
    </div>
</div>