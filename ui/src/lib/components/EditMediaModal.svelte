<script lang="ts">
	import { archive } from '$lib/api';

	interface Props {
		showEditModal: boolean;
		mediaName: string;
		mediaDescription: string;
		recordingUuid: string;
	}
	let {
		showEditModal = $bindable(),
		mediaName = $bindable(),
		mediaDescription = $bindable(),
		recordingUuid
	}: Props = $props();

	let error = $state('');
	let saving = $state(false);

	async function submitEdit() {
		if (!mediaName || !mediaDescription) {
			error = 'Please fill in all fields.';
			return;
		}
		saving = true;
		error = '';
		const formData = new FormData();
		formData.append('name', mediaName);
		formData.append('description', mediaDescription);
		try {
			await archive.update(recordingUuid, formData);
			showEditModal = false;
		} catch {
			error = 'Failed to update media.';
		} finally {
			saving = false;
		}
	}
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center">
	<div class="rounded bg-white p-6 shadow-md">
		<h2 class="text-lg font-bold">Edit Media</h2>
		{#if error}
			<p class="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p>
		{/if}
		<label class="mt-4 block text-sm font-medium" for="edit-name">Name</label>
		<input
			id="edit-name"
			type="text"
			bind:value={mediaName}
			class="mb-4 w-full rounded border p-2"
		/>
		<label class="block text-sm font-medium" for="edit-description">Description</label>
		<textarea
			id="edit-description"
			bind:value={mediaDescription}
			class="mb-4 w-full rounded border p-2"
		></textarea>
		<button
			onclick={() => void submitEdit()}
			disabled={saving}
			class="rounded bg-brand-primary px-4 py-2 text-white hover:opacity-90 disabled:opacity-50"
			>{saving ? 'Saving...' : 'Save Changes'}</button
		>
		<button onclick={() => (showEditModal = false)} class="ml-2 rounded bg-gray-300 px-4 py-2"
			>Cancel</button
		>
	</div>
</div>
