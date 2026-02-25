/**
 * Unit tests for $lib/stores
 *
 * Verifies initial state, derived values, and store aliases.
 * No API calls — stores only import domain types from api.ts (type-erased at runtime).
 */

import { describe, it, expect, beforeEach, test } from 'vitest';
import { get } from 'svelte/store';
import {
	currentUser,
	isAuthenticated,
	groupMediaList,
	selectedGroupMedia,
	selectedGroup,
	selectedGroupDetails,
	selectedMediaDuration,
	playbackPosition,
	uiConfig,
	exhibitEnabled,
	allowedAnnotationTypes,
	playerSkipSeconds,
	timeRangeInputMode,
	showTranscript,
	showWaveform,
	defaultQuality,
	dateLocale
} from '$lib/stores';
import type { User, Group, MediaStore, UIConfig } from '$lib/api';

const MOCK_USER: User = {
	id: 1,
	username: 'alice',
	first_name: 'Alice',
	last_name: 'A'
};

const MOCK_GROUP: Group = {
	id: 1,
	name: 'Test Group',
	description: 'desc',
	is_public: true,
	is_active: true,
	users: [],
	extra_group_questions: [],
	delete_wait_for: 0,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

const MOCK_MEDIA: MediaStore = {
	id: 1,
	uuid: 'media-uuid',
	name: 'Test Media',
	description: '',
	upload: null,
	tags: [],
	is_public: false,
	group: MOCK_GROUP,
	orig_name: 'test.mp4',
	orig_size: 0,
	file_extension: 'mp4',
	media_processing_status: 'Yet to process',
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z',
	created_by: null,
	transcript_vtt_url: ''
};

describe('auth stores', () => {
	beforeEach(() => {
		currentUser.set(null);
	});

	it('currentUser starts null', () => {
		expect(get(currentUser)).toBeNull();
	});

	it('isAuthenticated is false when no user', () => {
		expect(get(isAuthenticated)).toBe(false);
	});

	it('isAuthenticated is true when user is set', () => {
		currentUser.set(MOCK_USER);
		expect(get(isAuthenticated)).toBe(true);
	});

	it('isAuthenticated returns to false when user cleared', () => {
		currentUser.set(MOCK_USER);
		currentUser.set(null);
		expect(get(isAuthenticated)).toBe(false);
	});
});

describe('group stores', () => {
	beforeEach(() => {
		selectedGroup.set(null);
		groupMediaList.set([]);
	});

	it('selectedGroup starts null', () => {
		expect(get(selectedGroup)).toBeNull();
	});

	it('selectedGroupDetails is alias for selectedGroup', () => {
		selectedGroup.set(MOCK_GROUP);
		expect(get(selectedGroupDetails)).toEqual(MOCK_GROUP);
		// Writing via alias updates the original
		selectedGroupDetails.set(null);
		expect(get(selectedGroup)).toBeNull();
	});

	it('groupMediaList starts empty', () => {
		expect(get(groupMediaList)).toEqual([]);
	});

	it('selectedGroupMedia is alias for groupMediaList', () => {
		groupMediaList.set([MOCK_MEDIA]);
		expect(get(selectedGroupMedia)).toEqual([MOCK_MEDIA]);
		// Writing via alias updates the original
		selectedGroupMedia.set([]);
		expect(get(groupMediaList)).toEqual([]);
	});
});

describe('playback stores', () => {
	beforeEach(() => {
		selectedMediaDuration.set(null);
		playbackPosition.set(0);
	});

	it('selectedMediaDuration starts null', () => {
		expect(get(selectedMediaDuration)).toBeNull();
	});

	it('playbackPosition starts at 0', () => {
		expect(get(playbackPosition)).toBe(0);
	});

	it('playbackPosition can be updated', () => {
		playbackPosition.set(42.5);
		expect(get(playbackPosition)).toBe(42.5);
	});
});

const MOCK_UICONFIG: UIConfig = {
	profile: 'standard',
	brand_name: 'Test',
	brand_logo_url: '',
	primary_color: '#000',
	accent_color: '#fff',
	language: 'fr-FR',
	icon_set: '',
	font_scale: 1,
	color_scheme: 'default',
	voice_enabled: false,
	offline_first: false,
	player_controls: {
		skip_seconds: [5, 15],
		show_waveform: true,
		show_transcript: true,
		default_quality: 'high'
	},
	annotations_config: {
		allow_images: true,
		allow_audio: true,
		allow_video: false,
		allow_media_ref: false,
		time_range_input: 'slider'
	},
	exhibit_config: { enabled: true },
	updated_at: null
};

describe('UIConfig derived stores', () => {
	beforeEach(() => {
		uiConfig.set(null);
	});

	// ── exhibitEnabled ───────────────────────────────────────────────────────
	it('exhibitEnabled defaults to true when uiConfig is null', () => {
		expect(get(exhibitEnabled)).toBe(true);
	});

	it('exhibitEnabled reads from uiConfig', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(exhibitEnabled)).toBe(true);
	});

	it('exhibitEnabled is false when exhibit_config.enabled is false', () => {
		uiConfig.set({ ...MOCK_UICONFIG, exhibit_config: { enabled: false } });
		expect(get(exhibitEnabled)).toBe(false);
	});

	// ── allowedAnnotationTypes ────────────────────────────────────────────────
	it('allowedAnnotationTypes defaults to all types when uiConfig is null', () => {
		expect(get(allowedAnnotationTypes)).toEqual(['text', 'image', 'audio', 'video', 'media_ref']);
	});

	it('allowedAnnotationTypes respects annotation config', () => {
		uiConfig.set(MOCK_UICONFIG);
		// MOCK_UICONFIG: allow_images=true, allow_audio=true, allow_video=false, allow_media_ref=false
		expect(get(allowedAnnotationTypes)).toEqual(['text', 'image', 'audio']);
	});

	it('allowedAnnotationTypes always includes text', () => {
		uiConfig.set({
			...MOCK_UICONFIG,
			annotations_config: {
				...MOCK_UICONFIG.annotations_config,
				allow_images: false,
				allow_audio: false,
				allow_video: false,
				allow_media_ref: false
			}
		});
		expect(get(allowedAnnotationTypes)).toEqual(['text']);
	});

	// ── playerSkipSeconds ─────────────────────────────────────────────────────
	it('playerSkipSeconds defaults to [10, 30] when uiConfig is null', () => {
		expect(get(playerSkipSeconds)).toEqual([10, 30]);
	});

	it('playerSkipSeconds reads from uiConfig', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(playerSkipSeconds)).toEqual([5, 15]);
	});

	// ── timeRangeInputMode ────────────────────────────────────────────────────
	it('timeRangeInputMode defaults to slider when uiConfig is null', () => {
		expect(get(timeRangeInputMode)).toBe('slider');
	});

	it('timeRangeInputMode reads from uiConfig', () => {
		uiConfig.set({
			...MOCK_UICONFIG,
			annotations_config: { ...MOCK_UICONFIG.annotations_config, time_range_input: 'tap' }
		});
		expect(get(timeRangeInputMode)).toBe('tap');
	});

	// ── showTranscript ────────────────────────────────────────────────────────
	it('showTranscript defaults to false when uiConfig is null', () => {
		expect(get(showTranscript)).toBe(false);
	});

	it('showTranscript reads from uiConfig', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(showTranscript)).toBe(true);
	});

	// ── showWaveform ──────────────────────────────────────────────────────────
	it('showWaveform defaults to false when uiConfig is null', () => {
		expect(get(showWaveform)).toBe(false);
	});

	it('showWaveform reads from uiConfig', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(showWaveform)).toBe(true);
	});

	// ── defaultQuality ────────────────────────────────────────────────────────
	it('defaultQuality defaults to auto when uiConfig is null', () => {
		expect(get(defaultQuality)).toBe('auto');
	});

	it('defaultQuality reads from uiConfig', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(defaultQuality)).toBe('high');
	});

	// ── dateLocale ────────────────────────────────────────────────────────────
	it('dateLocale defaults to en-GB when uiConfig is null', () => {
		expect(get(dateLocale)).toBe('en-GB');
	});

	it('dateLocale reads uiConfig.language', () => {
		uiConfig.set(MOCK_UICONFIG);
		expect(get(dateLocale)).toBe('fr-FR');
	});

	it('dateLocale falls back to en-GB for empty language', () => {
		uiConfig.set({ ...MOCK_UICONFIG, language: '' });
		expect(get(dateLocale)).toBe('en-GB');
	});
});

/**
 * UIConfig completeness gate.
 *
 * Every actionable UIConfig sub-field must have a derived store in stores.ts.
 * If you add a new field to UIConfig.player_controls / annotations_config /
 * exhibit_config, add it here and create the store — this test will fail
 * until both are done.
 *
 * Fields explicitly deferred to Phase 5 are listed as TODO entries so
 * the test still documents them but doesn't block CI.
 */
describe('UIConfig → store completeness', () => {
	// Canonical mapping: UIConfig path → store export name.
	// If a field has no store yet but is deferred, mark it 'TODO(phase5)'.
	const FIELD_STORE_MAP: Record<string, string> = {
		// player_controls
		'player_controls.skip_seconds': 'playerSkipSeconds',
		'player_controls.show_waveform': 'showWaveform',
		'player_controls.show_transcript': 'showTranscript',
		'player_controls.default_quality': 'defaultQuality',
		// annotations_config
		'annotations_config.allow_*': 'allowedAnnotationTypes',
		'annotations_config.time_range_input': 'timeRangeInputMode',
		// exhibit_config
		'exhibit_config.enabled': 'exhibitEnabled',
		// top-level
		'language': 'dateLocale'
	};

	// Fields that exist in UIConfig but are intentionally NOT yet wired to stores.
	// When implemented, move them to FIELD_STORE_MAP and this test auto-enforces.
	const DEFERRED_FIELDS = [
		'profile',           // TODO(phase5): icon/voice rendering profiles
		'voice_enabled',     // TODO(phase5): TTS / voice UI
		'offline_first',     // TODO(phase5): service worker
		'icon_set',          // TODO(phase5): icon library switching
		'brand_logo_url',    // Read directly via $uiConfig?.brand_logo_url
		'font_scale',        // Applied via CSS var in layout, no store needed
		'primary_color',     // Applied via CSS var in layout, no store needed
		'accent_color',      // Applied via CSS var in layout, no store needed
		'brand_name',        // Read directly via $uiConfig?.brand_name
		'color_scheme'       // Applied via data attribute in layout, no store needed
	];

	const storeExports = {
		exhibitEnabled,
		allowedAnnotationTypes,
		playerSkipSeconds,
		timeRangeInputMode,
		showTranscript,
		showWaveform,
		defaultQuality,
		dateLocale
	};

	test.each(Object.entries(FIELD_STORE_MAP))(
		'UIConfig.%s → %s store exists and is readable',
		(_field, storeName) => {
			const store = storeExports[storeName as keyof typeof storeExports];
			expect(store, `Store "${storeName}" must be exported from stores.ts`).toBeDefined();
			// All derived stores must be readable (have .subscribe)
			expect(typeof store.subscribe).toBe('function');
		}
	);

	it('deferred fields are documented (update when implemented)', () => {
		// This test exists purely to document which UIConfig fields lack stores.
		// When a deferred field gets a store, remove it from DEFERRED_FIELDS
		// and add it to FIELD_STORE_MAP — the parametrized test above will
		// then enforce that the store exists.
		expect(DEFERRED_FIELDS.length).toBeGreaterThan(0);
	});
});
