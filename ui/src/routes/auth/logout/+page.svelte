<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { currentUser } from '$lib/stores';

	onMount(async () => {
		localStorage.removeItem('access_token');
		localStorage.removeItem('refresh_token');
		currentUser.set(null);
		await goto('/');
	});
</script>

<div class="flex min-h-[70vh] items-center justify-center">
	<p class="text-gray-500">Signing out…</p>
</div>
