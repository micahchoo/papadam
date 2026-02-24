<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { ParaglideJS } from '@inlang/paraglide-sveltekit';
	import { createI18n } from '@inlang/paraglide-sveltekit';
	import * as runtime from '$lib/i18n/runtime';
	import * as m from '$lib/i18n/messages';
	import { loadConfig } from '$lib/config';
	import { currentUser, isAuthenticated } from '$lib/stores';
	import { auth } from '$lib/api';

	const i18n = createI18n(runtime);
	const { children } = $props();

	onMount(async () => {
		await loadConfig();
		const token = localStorage.getItem('access_token');
		if (token) {
			try {
				const { data } = await auth.me();
				currentUser.set(data);
			} catch {
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
			}
		}
	});
</script>

<ParaglideJS {i18n}>
	<!-- Navigation -->
	<nav class="sticky top-0 z-50 flex w-full justify-between bg-blue-950 p-5">
		<div class="flex items-center justify-center">
			<a href="/" class="flex items-center text-2xl font-semibold text-white">
				<h1>Papad.alt</h1>
			</a>
		</div>

		<div class="flex justify-center">
			<div class="flex flex-wrap space-x-4 text-center">
				<a href="/" class="font-medium text-white hover:text-gray-400">{m.nav_home()}</a>
				<a href="/groups" class="font-medium text-white hover:text-gray-400"
					>{m.nav_collections()}</a
				>
				<a href="/exhibits" class="font-medium text-white hover:text-gray-400">{m.nav_exhibits()}</a
				>
				{#if $isAuthenticated}
					<a href="/auth/logout" class="font-medium text-white hover:text-gray-400"
						>{m.nav_logout()}</a
					>
				{:else}
					<a href="/auth/login" class="font-medium text-white hover:text-gray-400"
						>{m.nav_login()}</a
					>
				{/if}
			</div>
		</div>
	</nav>

	<!-- Main Content -->
	<main class="bg-gray-100">
		{@render children()}
	</main>

	<footer class="w-screen bg-gray-900 p-10 text-gray-400">
		<div
			class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 text-sm lg:flex-row lg:items-start"
		>
			<div class="text-center text-sm lg:text-left">
				<p class="mb-1 max-w-md">
					Developed at <strong>Aruvu Collaboratory LLP</strong>, leveraging the
					<strong>PAPAD API</strong> by <strong>Janastu Servelots</strong>.
				</p>
				<ul class="list-none">
					<li>
						Email: <a href="mailto:wellbeing@aruvu.org" class="text-gray-300 hover:underline"
							>wellbeing@aruvu.org</a
						>
					</li>
					<li>
						Website: <a href="https://aruvu.org" class="text-gray-300 hover:underline">aruvu.org</a>
					</li>
				</ul>
			</div>
			<div class="text-center text-sm lg:text-right">
				<p class="mb-4">Links:</p>
				<ul class="flex list-none justify-center gap-x-3 md:flex-col lg:justify-end">
					<li>
						<a
							href="https://github.com/Aruvu-collab"
							target="_blank"
							class="text-gray-300 hover:underline">GitHub</a
						>
					</li>
					<li>
						<a
							href="https://instagram.com/aruvu"
							target="_blank"
							class="text-gray-300 hover:underline">Instagram</a
						>
					</li>
					<li>
						<a href="https://aruvu.org" target="_blank" class="text-gray-300 hover:underline"
							>Website</a
						>
					</li>
				</ul>
			</div>
		</div>
		<div class="mt-6 text-center text-sm text-gray-400">
			&copy; {new Date().getFullYear()} Aruvu Collaboratory LLP
		</div>
	</footer>
</ParaglideJS>
