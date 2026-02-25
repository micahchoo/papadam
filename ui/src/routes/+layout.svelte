<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import type { Snippet } from 'svelte';
	import { ParaglideJS } from '@inlang/paraglide-sveltekit';
	import { createI18n } from '@inlang/paraglide-sveltekit';
	import * as runtime from '$lib/i18n/runtime';
	import NavBar from '$lib/components/NavBar.svelte';
	import { loadConfig, loadUIConfig } from '$lib/config';
	import { currentUser, uiConfig } from '$lib/stores';
	import { auth } from '$lib/api';

	const i18n = createI18n(runtime);
	const { children }: { children: Snippet } = $props();
	let layoutReady = $state(false);

	onMount(async () => {
		await loadConfig();
		const token = localStorage.getItem('access_token');
		// auth.me() and loadUIConfig() are independent — run concurrently
		const [, cfg] = await Promise.all([
			token
				? auth.me().then(({ data }) => {
						currentUser.set(data);
					}).catch(() => {
						localStorage.removeItem('access_token');
						localStorage.removeItem('refresh_token');
					})
				: Promise.resolve(),
			loadUIConfig()
		]);
		if (cfg) {
			uiConfig.set(cfg);
			const root = document.documentElement;
			root.style.setProperty('--brand-primary', cfg.primary_color);
			root.style.setProperty('--brand-accent', cfg.accent_color);
			root.style.setProperty('--font-scale', String(cfg.font_scale));
			root.dataset['profile'] = cfg.profile;
			root.dataset['colorScheme'] = cfg.color_scheme;
			if (cfg.voice_enabled) {
				root.dataset['voice'] = 'true';
			} else {
				delete root.dataset['voice'];
			}
		}
		layoutReady = true;
	});
</script>

<ParaglideJS {i18n}>
	<NavBar />

	<!-- Main Content -->
	<main class="min-h-screen bg-[var(--scheme-bg,#f3f4f6)]">
		{#if layoutReady}
			{@render children()}
		{:else}
			<div class="flex min-h-[60vh] items-center justify-center">
				<p class="text-sm text-gray-400">Loading…</p>
			</div>
		{/if}
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
