<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { uiconfig } from '$lib/api';
	import type {
		UIConfig,
		UIConfigProfile,
		UIConfigColorScheme,
		MediaQuality,
		TimeRangeInput
	} from '$lib/api';
	import { isAuthenticated, uiConfig } from '$lib/stores';

	let saving = $state(false);
	let saved = $state(false);
	let error = $state<string | null>(null);

	// Local form state mirroring UIConfig fields
	let brandName = $state('Papad.alt');
	let brandLogoUrl = $state('');
	let primaryColor = $state('#1e3a5f');
	let accentColor = $state('#3b82f6');
	let iconSet = $state('default');
	let profile = $state<UIConfigProfile>('standard');
	let colorScheme = $state<UIConfigColorScheme>('default');
	let language = $state('en');
	let fontScale = $state(1.0);
	let voiceEnabled = $state(false);
	let offlineFirst = $state(false);
	// Player controls
	let skipBackward = $state(10);
	let skipForward = $state(30);
	let showWaveform = $state(false);
	let showTranscript = $state(false);
	let defaultQuality = $state<MediaQuality>('auto');
	// Annotation capabilities
	let allowImages = $state(true);
	let allowAudio = $state(true);
	let allowVideo = $state(true);
	let allowMediaRef = $state(true);
	let timeRangeInput = $state<TimeRangeInput>('slider');
	// Features
	let exhibitEnabled = $state(true);

	function loadFromStore(cfg: UIConfig): void {
		brandName = cfg.brand_name;
		brandLogoUrl = cfg.brand_logo_url;
		primaryColor = cfg.primary_color;
		accentColor = cfg.accent_color;
		iconSet = cfg.icon_set;
		profile = cfg.profile;
		colorScheme = cfg.color_scheme;
		language = cfg.language;
		fontScale = cfg.font_scale;
		voiceEnabled = cfg.voice_enabled;
		offlineFirst = cfg.offline_first;
		skipBackward = cfg.player_controls.skip_seconds[0];
		skipForward = cfg.player_controls.skip_seconds[1];
		showWaveform = cfg.player_controls.show_waveform;
		showTranscript = cfg.player_controls.show_transcript;
		defaultQuality = cfg.player_controls.default_quality;
		allowImages = cfg.annotations_config.allow_images;
		allowAudio = cfg.annotations_config.allow_audio;
		allowVideo = cfg.annotations_config.allow_video;
		allowMediaRef = cfg.annotations_config.allow_media_ref;
		timeRangeInput = cfg.annotations_config.time_range_input;
		exhibitEnabled = cfg.exhibit_config.enabled;
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
				brand_logo_url: brandLogoUrl,
				primary_color: primaryColor,
				accent_color: accentColor,
				icon_set: iconSet,
				profile,
				color_scheme: colorScheme,
				language,
				font_scale: fontScale,
				voice_enabled: voiceEnabled,
				offline_first: offlineFirst,
				player_controls: {
					skip_seconds: [skipBackward, skipForward],
					show_waveform: showWaveform,
					show_transcript: showTranscript,
					default_quality: defaultQuality
				},
				annotations_config: {
					allow_images: allowImages,
					allow_audio: allowAudio,
					allow_video: allowVideo,
					allow_media_ref: allowMediaRef,
					time_range_input: timeRangeInput
				},
				exhibit_config: { enabled: exhibitEnabled }
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

	<form
		onsubmit={(e) => {
			e.preventDefault();
			void save();
		}}
		class="space-y-5"
	>
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

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Logo URL</span>
				<input
					type="url"
					bind:value={brandLogoUrl}
					maxlength="500"
					placeholder="https://example.com/logo.png"
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

			<label class="block">
				<span class="text-sm text-gray-700">Icon set</span>
				<input
					type="text"
					bind:value={iconSet}
					maxlength="200"
					placeholder="default"
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
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

		<!-- Player controls -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Player</legend>

			<div class="mb-3 flex gap-4">
				<label class="block flex-1">
					<span class="text-sm text-gray-700">Skip backward ({skipBackward}s)</span>
					<input
						type="range"
						bind:value={skipBackward}
						min="5"
						max="60"
						step="5"
						class="mt-1 block w-full"
					/>
				</label>
				<label class="block flex-1">
					<span class="text-sm text-gray-700">Skip forward ({skipForward}s)</span>
					<input
						type="range"
						bind:value={skipForward}
						min="5"
						max="60"
						step="5"
						class="mt-1 block w-full"
					/>
				</label>
			</div>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Default quality</span>
				<select
					bind:value={defaultQuality}
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
				>
					<option value="auto">Auto</option>
					<option value="low">Low</option>
					<option value="medium">Medium</option>
					<option value="high">High</option>
				</select>
			</label>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={showWaveform} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Show waveform</span>
			</label>

			<label class="mt-3 flex items-center gap-3">
				<input type="checkbox" bind:checked={showTranscript} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Show transcript</span>
			</label>
		</fieldset>

		<!-- Annotation capabilities -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Annotations</legend>

			<label class="mb-3 block">
				<span class="text-sm text-gray-700">Time range input</span>
				<select
					bind:value={timeRangeInput}
					class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 text-sm"
				>
					<option value="slider">Slider</option>
					<option value="timestamp">Timestamp (MM:SS)</option>
					<option value="tap">Tap to mark</option>
				</select>
			</label>

			<p class="mb-2 text-xs text-gray-500">Allowed annotation types</p>
			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={allowImages} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Images</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowAudio} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Audio clips</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowVideo} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Video clips</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowMediaRef} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Media references</span>
			</label>
		</fieldset>

		<!-- Features -->
		<fieldset class="rounded border border-gray-200 p-4">
			<legend class="px-1 text-sm font-semibold text-gray-600">Features</legend>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={exhibitEnabled} class="h-4 w-4 rounded" />
				<span class="text-sm text-gray-700">Enable exhibit builder</span>
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
