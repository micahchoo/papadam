<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { uiconfig } from '$lib/api';
	import type { UIConfig, UIConfigProfile, UIConfigColorScheme } from '$lib/api';
	import { isAuthenticated, uiConfig } from '$lib/stores';

	let saving = $state(false);
	let saved = $state(false);
	let error = $state<string | null>(null);

	// Local form state mirroring UIConfig fields
	let brandName = $state('Papad.alt');
	let primaryColor = $state('#1e3a5f');
	let accentColor = $state('#3b82f6');
	let profile = $state<UIConfigProfile>('standard');
	let colorScheme = $state<UIConfigColorScheme>('default');
	let language = $state('en');
	let fontScale = $state(1.0);
	let voiceEnabled = $state(false);
	let offlineFirst = $state(false);

	function loadFromStore(cfg: UIConfig): void {
		brandName = cfg.brand_name;
		primaryColor = cfg.primary_color;
		accentColor = cfg.accent_color;
		profile = cfg.profile;
		colorScheme = cfg.color_scheme;
		language = cfg.language;
		fontScale = cfg.font_scale;
		voiceEnabled = cfg.voice_enabled;
		offlineFirst = cfg.offline_first;
	}

	onMount(async () => {
		if (!$isAuthenticated) {
			void goto('/auth/login');
			return;
		}
		// Seed form from already-loaded store value, or fetch fresh
		const current = $uiConfig;
		if (current) {
			loadFromStore(current);
		} else {
			try {
				const { data } = await uiconfig.get();
				uiConfig.set(data);
				loadFromStore(data);
			} catch {
				error = 'Failed to load settings.';
			}
		}
	});

	async function save(): Promise<void> {
		saving = true;
		saved = false;
		error = null;
		try {
			const { data } = await uiconfig.patch({
				brand_name: brandName,
				primary_color: primaryColor,
				accent_color: accentColor,
				profile,
				color_scheme: colorScheme,
				language,
				font_scale: fontScale,
				voice_enabled: voiceEnabled,
				offline_first: offlineFirst
			});
			uiConfig.set(data);
			// Apply CSS vars immediately so the change is visible without reload
			const root = document.documentElement;
			root.style.setProperty('--brand-primary', data.primary_color);
			root.style.setProperty('--brand-accent', data.accent_color);
			root.style.setProperty('--font-scale', String(data.font_scale));
			saved = true;
		} catch {
			error = 'Failed to save settings.';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Settings — {$uiConfig?.brand_name ?? 'Papad.alt'}</title>
</svelte:head>

<div class="mx-auto max-w-2xl p-6">
	<h1 class="mb-6 text-2xl font-bold text-gray-800">Instance Settings</h1>

	{#if error}
		<p class="mb-4 rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
			{error}
		</p>
	{/if}
	{#if saved}
		<p class="mb-4 rounded border border-green-300 bg-green-50 px-4 py-2 text-sm text-green-700">
			Settings saved.
		</p>
	{/if}

	<form onsubmit={(e) => { e.preventDefault(); void save(); }} class="space-y-5">
		<!-- Branding -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Branding</legend>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Instance name</span>
				<input
					type="text"
					bind:value={brandName}
					maxlength="100"
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent"
				/>
			</label>

			<div class="flex gap-4">
				<label class="block flex-1">
					<span class="text-sm text-gray-700">Primary colour</span>
					<input
						type="color"
						bind:value={primaryColor}
						class="mt-1 block h-10 w-full cursor-pointer rounded border border-gray-300"
					/>
				</label>
				<label class="block flex-1">
					<span class="text-sm text-gray-700">Accent colour</span>
					<input
						type="color"
						bind:value={accentColor}
						class="mt-1 block h-10 w-full cursor-pointer rounded border border-gray-300"
					/>
				</label>
			</div>
		</fieldset>

		<!-- Interaction profile -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Interface</legend>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Interaction profile</span>
				<select
					bind:value={profile}
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
				>
					<option value="standard">Standard</option>
					<option value="icon">Icon (low-literacy)</option>
					<option value="voice">Voice</option>
					<option value="high-contrast">High contrast</option>
				</select>
			</label>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Colour scheme</span>
				<select
					bind:value={colorScheme}
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
				>
					<option value="default">Default</option>
					<option value="warm">Warm</option>
					<option value="cool">Cool</option>
					<option value="high-contrast">High contrast</option>
				</select>
			</label>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Language (BCP 47)</span>
				<input
					type="text"
					bind:value={language}
					maxlength="10"
					placeholder="en"
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
				/>
			</label>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Font scale ({fontScale}×)</span>
				<input
					type="range"
					bind:value={fontScale}
					min="0.8"
					max="2.0"
					step="0.1"
					class="mt-1 block w-full"
				/>
			</label>
		</fieldset>

		<!-- Accessibility -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Accessibility</legend>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={voiceEnabled} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Enable voice interaction</span>
			</label>

			<label class="mt-3 flex items-center gap-3">
				<input type="checkbox" bind:checked={offlineFirst} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Offline-first mode</span>
			</label>
		</fieldset>

		<button
			type="submit"
			disabled={saving}
			class="w-full rounded bg-brand-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
		>
			{saving ? 'Saving…' : 'Save settings'}
		</button>
	</form>
</div>
