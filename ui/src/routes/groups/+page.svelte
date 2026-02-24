<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { groups } from '$lib/api';
	import type { Group } from '$lib/api';

	const COLORS = [
		'bg-red-500',
		'bg-blue-500',
		'bg-green-500',
		'bg-yellow-500',
		'bg-purple-500',
		'bg-pink-500',
		'bg-cyan-500'
	] as const;

	let collections = $state<Group[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const { data } = await groups.list();
			collections = data.results;
		} catch {
			error = 'Failed to load collections.';
		} finally {
			loading = false;
		}
	});

	async function handleClick(id: number) {
		loading = true;
		await goto(`/groups/${id}`);
		loading = false;
	}
</script>

<div class="container relative mx-auto p-6">
	<h1 class="mx-auto mb-6 max-w-5xl text-2xl font-bold">My Collections</h1>
	{#if error}
		<p class="text-red-500">{error}</p>
	{:else if loading}
		<div class="fixed inset-0 z-50 flex items-center justify-center bg-gray-500 bg-opacity-50">
			<div
				class="loader h-12 w-12 rounded-full border-4 border-t-4 border-gray-200 ease-linear"
			></div>
		</div>
	{:else if collections.length === 0}
		<p class="text-gray-500">No collections found.</p>
	{:else}
		<div class="mx-auto grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-2">
			{#each collections as collection, index}
				<div
					class="flex cursor-pointer flex-col bg-white shadow-md transition-shadow hover:shadow-lg"
					role="button"
					tabindex="0"
					onclick={() => void handleClick(collection.id)}
					onkeydown={(e) => {
						if (e.key === 'Enter') void handleClick(collection.id);
					}}
				>
					<div class={`h-60 w-full ${COLORS[index % COLORS.length] ?? 'bg-gray-500'}`}></div>
					<div class="flex flex-col items-center justify-center p-5 text-center">
						<h2 class="text-xl font-semibold">{collection.name}</h2>
						<p class="mt-2 text-gray-600">{@html collection.description}</p>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.loader {
		border-top-color: #3498db;
		animation: spinner 0.6s linear infinite;
	}
	@keyframes spinner {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}
</style>
