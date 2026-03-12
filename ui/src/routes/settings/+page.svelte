<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { uiconfig, groups, importexport } from '$lib/api';
	import axios from 'axios';
	import type {
		UIConfig,
		UIConfigProfile,
		UIConfigColorScheme,
		MediaQuality,
		TimeRangeInput,
		Group,
		IERequest
	} from '$lib/api';
	import { isAuthenticated, uiConfig } from '$lib/stores';

	let saving = $state(false);
	let saved = $state(false);
	let error = $state<string | null>(null);
	let loaded = $state(false);

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

	// ── Group management ─────────────────────────────────────────────────────
	let collectionList = $state<Group[]>([]);
	let collectionsLoading = $state(true);
	let collectionsError = $state<string | null>(null);
	// Create form
	let showCreateForm = $state(false);
	let newGroupName = $state('');
	let newGroupDescription = $state('');
	let newGroupPublic = $state(true);
	let creatingGroup = $state(false);
	let createGroupError = $state<string | null>(null);
	// Inline edit
	let editingGroupId = $state<number | null>(null);
	let editName = $state('');
	let editDescription = $state('');
	let editPublic = $state(true);
	let updatingGroup = $state(false);
	let updateGroupError = $state<string | null>(null);
	// Delete confirmation
	let deletingGroupId = $state<number | null>(null);
	let deleteGroupLoading = $state(false);
	let deleteGroupError = $state<string | null>(null);

	// ── Import / Export ──────────────────────────────────────────────────────
	let ieRequests = $state<IERequest[]>([]);
	let ieLoading = $state(true);
	let ieError = $state<string | null>(null);
	let importFile = $state<File | null>(null);
	let importingFile = $state(false);
	let importError = $state<string | null>(null);
	let importSuccess = $state<string | null>(null);
	let pollTimer: ReturnType<typeof setInterval> | null = null;

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

	async function loadCollections(): Promise<void> {
		collectionsLoading = true;
		collectionsError = null;
		try {
			const { data } = await groups.list();
			collectionList = data.results;
		} catch {
			collectionsError = 'Failed to load collections.';
		} finally {
			collectionsLoading = false;
		}
	}

	async function loadIERequests(): Promise<void> {
		ieError = null;
		try {
			const { data } = await importexport.listRequests();
			ieRequests = data.results;
		} catch {
			ieError = 'Failed to load import/export requests.';
		} finally {
			ieLoading = false;
		}
	}

	function startPolling(): void {
		stopPolling();
		pollTimer = setInterval(() => {
			const hasPending = ieRequests.some(
				(r) => !r.is_complete && r.detail !== 'failed'
			);
			if (hasPending) {
				void loadIERequests();
			} else {
				stopPolling();
			}
		}, 30_000);
	}

	function stopPolling(): void {
		if (pollTimer !== null) {
			clearInterval(pollTimer);
			pollTimer = null;
		}
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
			loaded = true;
		} else {
			try {
				const { data } = await uiconfig.get();
				uiConfig.set(data);
				loadFromStore(data);
				loaded = true;
			} catch {
				error = 'Failed to load settings.';
			}
		}

		// Load collections and IE requests in parallel
		await Promise.all([loadCollections(), loadIERequests()]);
		startPolling();
	});

	onDestroy(() => {
		stopPolling();
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
			// Apply CSS vars and data attributes immediately so changes are visible without reload
			const root = document.documentElement;
			root.style.setProperty('--brand-primary', data.primary_color);
			root.style.setProperty('--brand-accent', data.accent_color);
			root.style.setProperty('--font-scale', String(data.font_scale));
			root.dataset['profile'] = data.profile;
			root.dataset['colorScheme'] = data.color_scheme;
			if (data.voice_enabled) {
				root.dataset['voice'] = 'true';
			} else {
				delete root.dataset['voice'];
			}
			saved = true;
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const data = err.response.data as Record<string, string[] | string>;
				error = typeof data['detail'] === 'string' ? data['detail'] : 'Failed to save settings.';
			} else {
				error = 'Failed to save settings.';
			}
		} finally {
			saving = false;
		}
	}

	// ── Group CRUD ───────────────────────────────────────────────────────────

	async function createGroup(): Promise<void> {
		if (!newGroupName.trim()) {
			createGroupError = 'Name is required.';
			return;
		}
		creatingGroup = true;
		createGroupError = null;
		try {
			const { data } = await groups.create({
				name: newGroupName.trim(),
				description: newGroupDescription.trim(),
				is_public: newGroupPublic
			});
			collectionList = [data, ...collectionList];
			newGroupName = '';
			newGroupDescription = '';
			newGroupPublic = true;
			showCreateForm = false;
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const d = err.response.data as Record<string, string[] | string>;
				createGroupError = typeof d['detail'] === 'string' ? d['detail'] : 'Failed to create collection.';
			} else {
				createGroupError = 'Failed to create collection.';
			}
		} finally {
			creatingGroup = false;
		}
	}

	function startEdit(g: Group): void {
		editingGroupId = g.id;
		editName = g.name;
		editDescription = g.description;
		editPublic = g.is_public;
		updateGroupError = null;
	}

	function cancelEdit(): void {
		editingGroupId = null;
		updateGroupError = null;
	}

	async function saveEdit(): Promise<void> {
		if (editingGroupId === null) return;
		updatingGroup = true;
		updateGroupError = null;
		try {
			const { data } = await groups.update(editingGroupId, {
				name: editName.trim(),
				description: editDescription.trim(),
				is_public: editPublic
			});
			collectionList = collectionList.map((g) => (g.id === data.id ? data : g));
			editingGroupId = null;
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const d = err.response.data as Record<string, string[] | string>;
				updateGroupError = typeof d['detail'] === 'string' ? d['detail'] : 'Failed to update collection.';
			} else {
				updateGroupError = 'Failed to update collection.';
			}
		} finally {
			updatingGroup = false;
		}
	}

	function confirmDelete(id: number): void {
		deletingGroupId = id;
		deleteGroupError = null;
	}

	async function executeDelete(): Promise<void> {
		if (deletingGroupId === null) return;
		deleteGroupLoading = true;
		deleteGroupError = null;
		try {
			await groups.delete(deletingGroupId);
			collectionList = collectionList.filter((g) => g.id !== deletingGroupId);
			deletingGroupId = null;
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const d = err.response.data as Record<string, string[] | string>;
				deleteGroupError = typeof d['detail'] === 'string' ? d['detail'] : 'Failed to delete collection.';
			} else {
				deleteGroupError = 'Failed to delete collection.';
			}
		} finally {
			deleteGroupLoading = false;
		}
	}

	// ── Import ───────────────────────────────────────────────────────────────

	function handleFileSelect(e: Event): void {
		const target = e.target as HTMLInputElement;
		importFile = target.files?.[0] ?? null;
	}

	async function submitImport(): Promise<void> {
		if (!importFile) {
			importError = 'Select a file first.';
			return;
		}
		importingFile = true;
		importError = null;
		importSuccess = null;
		try {
			const fd = new FormData();
			fd.append('requested_file', importFile);
			await importexport.requestImport(fd);
			importSuccess = 'Import requested. Status will appear below.';
			importFile = null;
			// Reset file input
			const input = document.getElementById('ie-file-input') as HTMLInputElement | null;
			if (input) input.value = '';
			await loadIERequests();
			startPolling();
		} catch (err: unknown) {
			if (axios.isAxiosError(err) && err.response?.data) {
				const d = err.response.data as Record<string, string[] | string>;
				importError = typeof d['detail'] === 'string' ? d['detail'] : 'Failed to submit import.';
			} else {
				importError = 'Failed to submit import.';
			}
		} finally {
			importingFile = false;
		}
	}
</script>

<svelte:head>
	<title>Settings — {$uiConfig?.brand_name ?? 'Papad.alt'}</title>
</svelte:head>

<div class="mx-auto max-w-2xl p-6">
	<h1 class="mb-6 font-heading text-3xl font-black tracking-tight">Instance Settings</h1>

	{#if error}
		<p class="mb-4 border border-red-300 bg-red-50 px-4 py-2 font-body text-sm text-red-700">
			{error}
		</p>
	{/if}
	{#if saved}
		<p class="mb-4 border border-green-300 bg-green-50 px-4 py-2 font-body text-sm text-green-700">
			Settings saved.
		</p>
	{/if}

	{#if !loaded && !error}
		<p class="mb-4 font-body text-sm text-gray-500">Loading settings...</p>
	{/if}

	<form
		onsubmit={(e) => {
			e.preventDefault();
			void save();
		}}
		class="space-y-5"
	>
		<!-- Branding -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Branding</legend>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Instance name</span>
				<input
					type="text"
					bind:value={brandName}
					maxlength="100"
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent"
				/>
			</label>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Logo URL</span>
				<input
					type="url"
					bind:value={brandLogoUrl}
					maxlength="500"
					placeholder="https://example.com/logo.png"
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent"
				/>
			</label>

			<div class="flex gap-4">
				<label class="block flex-1">
					<span class="font-body text-sm text-gray-700">Primary colour</span>
					<input
						type="color"
						bind:value={primaryColor}
						class="mt-1 block h-10 w-full cursor-pointer border border-gray-300"
					/>
				</label>
				<label class="block flex-1">
					<span class="font-body text-sm text-gray-700">Accent colour</span>
					<input
						type="color"
						bind:value={accentColor}
						class="mt-1 block h-10 w-full cursor-pointer border border-gray-300"
					/>
				</label>
			</div>
		</fieldset>

		<!-- Interaction profile -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Interface</legend>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Interaction profile</span>
				<select
					bind:value={profile}
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				>
					<option value="standard">Standard</option>
					<option value="icon">Icon (low-literacy)</option>
					<option value="voice">Voice</option>
					<option value="high-contrast">High contrast</option>
				</select>
			</label>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Colour scheme</span>
				<select
					bind:value={colorScheme}
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				>
					<option value="default">Default</option>
					<option value="warm">Warm</option>
					<option value="cool">Cool</option>
					<option value="high-contrast">High contrast</option>
				</select>
			</label>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Language (BCP 47)</span>
				<input
					type="text"
					bind:value={language}
					maxlength="10"
					placeholder="en"
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				/>
			</label>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Font scale ({fontScale}x)</span>
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
				<span class="font-body text-sm text-gray-700">Icon set <span class="text-xs text-gray-400">(experimental)</span></span>
				<input
					type="text"
					bind:value={iconSet}
					maxlength="200"
					placeholder="default"
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				/>
			</label>
		</fieldset>

		<!-- Accessibility -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Accessibility</legend>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={voiceEnabled} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Enable voice interaction</span>
			</label>

			<label class="mt-3 flex items-center gap-3">
				<input type="checkbox" bind:checked={offlineFirst} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Offline-first mode</span>
			</label>
		</fieldset>

		<!-- Player controls -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Player</legend>

			<div class="mb-3 flex gap-4">
				<label class="block flex-1">
					<span class="font-body text-sm text-gray-700">Skip backward ({skipBackward}s)</span>
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
					<span class="font-body text-sm text-gray-700">Skip forward ({skipForward}s)</span>
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
				<span class="font-body text-sm text-gray-700">Default quality</span>
				<select
					bind:value={defaultQuality}
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				>
					<option value="auto">Auto</option>
					<option value="low">Low</option>
					<option value="medium">Medium</option>
					<option value="high">High</option>
				</select>
			</label>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={showWaveform} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Show waveform</span>
			</label>

			<label class="mt-3 flex items-center gap-3">
				<input type="checkbox" bind:checked={showTranscript} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Show transcript</span>
			</label>
		</fieldset>

		<!-- Annotation capabilities -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Annotations</legend>

			<label class="mb-3 block">
				<span class="font-body text-sm text-gray-700">Time range input</span>
				<select
					bind:value={timeRangeInput}
					class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm"
				>
					<option value="slider">Slider</option>
					<option value="timestamp">Timestamp (MM:SS)</option>
					<option value="tap">Tap to mark</option>
				</select>
			</label>

			<p class="mb-2 font-body text-xs text-gray-500">Allowed annotation types</p>
			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={allowImages} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Images</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowAudio} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Audio clips</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowVideo} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Video clips</span>
			</label>
			<label class="mt-2 flex items-center gap-3">
				<input type="checkbox" bind:checked={allowMediaRef} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Media references</span>
			</label>
		</fieldset>

		<!-- Features -->
		<fieldset class="border border-gray-200 p-4">
			<legend class="px-1 font-body text-sm font-semibold text-gray-600">Features</legend>

			<label class="flex items-center gap-3">
				<input type="checkbox" bind:checked={exhibitEnabled} class="h-4 w-4" />
				<span class="font-body text-sm text-gray-700">Enable exhibit builder</span>
			</label>
		</fieldset>

		<button
			type="submit"
			disabled={saving || !loaded}
			class="w-full bg-brand-primary px-4 py-2 font-body text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
		>
			{saving ? 'Saving...' : 'Save settings'}
		</button>
	</form>

	<!-- ── Collections (Group Management) ────────────────────────────────── -->
	<section class="mt-12 border-t-2 border-gray-900 pt-6">
		<div class="mb-4 flex items-baseline justify-between">
			<h2 class="font-heading text-2xl font-black tracking-tight">Collections</h2>
			<button
				class="border border-gray-900 px-4 py-1.5 font-body text-sm tracking-wide hover:bg-gray-900 hover:text-white"
				onclick={() => { showCreateForm = !showCreateForm; createGroupError = null; }}
			>
				{showCreateForm ? 'Cancel' : 'Create collection'}
			</button>
		</div>

		{#if showCreateForm}
			<div class="mb-6 border border-gray-200 p-4">
				<h3 class="mb-3 font-heading text-lg font-bold">New Collection</h3>
				{#if createGroupError}
					<p class="mb-3 border border-red-300 bg-red-50 px-3 py-2 font-body text-sm text-red-700">{createGroupError}</p>
				{/if}
				<label class="mb-3 block">
					<span class="font-body text-sm text-gray-700">Name</span>
					<input type="text" bind:value={newGroupName} maxlength="100"
						class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent" />
				</label>
				<label class="mb-3 block">
					<span class="font-body text-sm text-gray-700">Description</span>
					<textarea bind:value={newGroupDescription} rows="2"
						class="mt-1 block w-full border border-gray-300 px-3 py-2 font-body text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent"></textarea>
				</label>
				<label class="mb-4 flex items-center gap-3">
					<input type="checkbox" bind:checked={newGroupPublic} class="h-4 w-4" />
					<span class="font-body text-sm text-gray-700">Public</span>
				</label>
				<button
					onclick={() => void createGroup()}
					disabled={creatingGroup}
					class="bg-brand-primary px-4 py-2 font-body text-sm text-white hover:opacity-90 disabled:opacity-50"
				>
					{creatingGroup ? 'Creating...' : 'Create'}
				</button>
			</div>
		{/if}

		{#if collectionsError}
			<p class="font-body text-sm text-red-700">{collectionsError}</p>
		{:else if collectionsLoading}
			<p class="font-body text-sm text-gray-500">Loading collections...</p>
		{:else if collectionList.length === 0}
			<p class="py-6 font-body text-sm text-gray-400">No collections yet.</p>
		{:else}
			<div class="divide-y divide-gray-200">
				{#each collectionList as g (g.id)}
					{#if editingGroupId === g.id}
						<!-- Inline edit form -->
						<div class="py-4">
							{#if updateGroupError}
								<p class="mb-2 border border-red-300 bg-red-50 px-3 py-1 font-body text-sm text-red-700">{updateGroupError}</p>
							{/if}
							<label class="mb-2 block">
								<span class="font-body text-xs text-gray-600">Name</span>
								<input type="text" bind:value={editName} maxlength="100"
									class="mt-1 block w-full border border-gray-300 px-3 py-1.5 font-body text-sm" />
							</label>
							<label class="mb-2 block">
								<span class="font-body text-xs text-gray-600">Description</span>
								<textarea bind:value={editDescription} rows="2"
									class="mt-1 block w-full border border-gray-300 px-3 py-1.5 font-body text-sm"></textarea>
							</label>
							<label class="mb-3 flex items-center gap-2">
								<input type="checkbox" bind:checked={editPublic} class="h-4 w-4" />
								<span class="font-body text-sm text-gray-700">Public</span>
							</label>
							<div class="flex gap-2">
								<button
									onclick={() => void saveEdit()}
									disabled={updatingGroup}
									class="bg-brand-primary px-3 py-1 font-body text-sm text-white hover:opacity-90 disabled:opacity-50"
								>{updatingGroup ? 'Saving...' : 'Save'}</button>
								<button
									onclick={cancelEdit}
									class="border border-gray-300 px-3 py-1 font-body text-sm hover:bg-gray-100"
								>Cancel</button>
							</div>
						</div>
					{:else if deletingGroupId === g.id}
						<!-- Delete confirmation -->
						<div class="py-4">
							{#if deleteGroupError}
								<p class="mb-2 border border-red-300 bg-red-50 px-3 py-1 font-body text-sm text-red-700">{deleteGroupError}</p>
							{/if}
							<p class="mb-3 font-body text-sm text-gray-700">Delete <strong>{g.name}</strong>? This cannot be undone.</p>
							<div class="flex gap-2">
								<button
									onclick={() => void executeDelete()}
									disabled={deleteGroupLoading}
									class="border border-red-500 px-3 py-1 font-body text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
								>{deleteGroupLoading ? 'Deleting...' : 'Confirm delete'}</button>
								<button
									onclick={() => { deletingGroupId = null; deleteGroupError = null; }}
									class="border border-gray-300 px-3 py-1 font-body text-sm hover:bg-gray-100"
								>Cancel</button>
							</div>
						</div>
					{:else}
						<!-- Normal row -->
						<div class="flex items-center justify-between py-3">
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-2">
									<span class="font-heading text-sm font-bold">{g.name}</span>
									<span class="font-body text-xs uppercase tracking-wider {g.is_public ? 'text-green-700' : 'text-gray-500'}">
										{g.is_public ? 'Public' : 'Private'}
									</span>
								</div>
								{#if g.description}
									<p class="mt-0.5 line-clamp-1 font-body text-xs text-gray-500">{g.description}</p>
								{/if}
							</div>
							<div class="ml-3 flex shrink-0 gap-2">
								<button
									class="font-body text-xs text-gray-600 underline-offset-2 hover:underline"
									onclick={() => startEdit(g)}
								>Edit</button>
								<button
									class="font-body text-xs text-red-600 underline-offset-2 hover:underline"
									onclick={() => confirmDelete(g.id)}
								>Delete</button>
							</div>
						</div>
					{/if}
				{/each}
			</div>
		{/if}
	</section>

	<!-- ── Import / Export ────────────────────────────────────────────────── -->
	<section class="mt-12 border-t-2 border-gray-900 pt-6">
		<h2 class="mb-4 font-heading text-2xl font-black tracking-tight">Import / Export</h2>

		<!-- Import form -->
		<div class="mb-6 border border-gray-200 p-4">
			<h3 class="mb-3 font-heading text-lg font-bold">Import data</h3>
			{#if importError}
				<p class="mb-3 border border-red-300 bg-red-50 px-3 py-2 font-body text-sm text-red-700">{importError}</p>
			{/if}
			{#if importSuccess}
				<p class="mb-3 border border-green-300 bg-green-50 px-3 py-2 font-body text-sm text-green-700">{importSuccess}</p>
			{/if}
			<div class="flex items-end gap-3">
				<label class="flex-1">
					<span class="font-body text-sm text-gray-700">File</span>
					<input id="ie-file-input" type="file" onchange={handleFileSelect}
						class="mt-1 block w-full font-body text-sm text-gray-600" />
				</label>
				<button
					onclick={() => void submitImport()}
					disabled={importingFile || !importFile}
					class="bg-brand-primary px-4 py-2 font-body text-sm text-white hover:opacity-90 disabled:opacity-50"
				>
					{importingFile ? 'Uploading...' : 'Import'}
				</button>
			</div>
		</div>

		<!-- Request history -->
		{#if ieError}
			<p class="font-body text-sm text-red-700">{ieError}</p>
		{:else if ieLoading}
			<p class="font-body text-sm text-gray-500">Loading requests...</p>
		{:else if ieRequests.length === 0}
			<p class="py-6 font-body text-sm text-gray-400">No import or export requests yet.</p>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full font-body text-sm">
					<thead>
						<tr class="border-b-2 border-gray-900 text-left">
							<th class="pb-2 pr-4 font-semibold">Type</th>
							<th class="pb-2 pr-4 font-semibold">Status</th>
							<th class="pb-2 font-semibold">Requested</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200">
						{#each ieRequests as req}
							<tr>
								<td class="py-2 pr-4">
									<span class="font-body text-xs uppercase tracking-wider">
										{req.request_type}
									</span>
								</td>
								<td class="py-2 pr-4">
									{#if req.is_complete}
										<span class="text-green-700">Complete</span>
									{:else if req.detail === 'failed'}
										<span class="text-red-600">Failed</span>
									{:else}
										<span class="text-amber-600">Pending</span>
									{/if}
								</td>
								<td class="py-2 text-gray-500">
									{new Date(req.requested_at).toLocaleString()}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</section>
</div>
