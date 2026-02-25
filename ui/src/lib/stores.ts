/**
 * papadam Svelte stores
 *
 * Single source of truth for reactive UI state.
 * Used by components via the $store shorthand and by lib/crdt.ts.
 *
 * Architecture boundary: may import from $lib/config and $lib/crdt.
 * Components should never import axios or api.ts directly for state.
 */

import { writable, derived } from 'svelte/store';
import type {
	UIConfig,
	User,
	Group,
	MediaStore,
	AnnotationType,
	MediaQuality,
	TimeRangeInput
} from '$lib/api';

// ── Auth ──────────────────────────────────────────────────────────────────────

/** Authenticated user, null when logged out. */
export const currentUser = writable<User | null>(null);

/** True when a user object is loaded. */
export const isAuthenticated = derived(currentUser, ($u) => $u !== null);

// ── Group / Collection context ────────────────────────────────────────────────

/** The collection the user is currently browsing. */
export const selectedGroup = writable<Group | null>(null);

/** Alias used by existing components for the current group details. */
export const selectedGroupDetails = selectedGroup;

// ── Media list for the current group ─────────────────────────────────────────

/**
 * List of media items in the currently-selected group.
 * Populated by the group detail page on load; read by SearchSort + UploadMediaModal.
 */
export const groupMediaList = writable<MediaStore[]>([]);

/**
 * Alias used by existing components.
 * Naming kept from the original stores.js for backward compatibility.
 */
export const selectedGroupMedia = groupMediaList;

// ── Playback state ───────────────────────────────────────────────────────────

/**
 * Duration of the currently loaded media in seconds.
 * Set by MediaPlayer on loadedmetadata; read by UploadAnnotationModal.
 */
export const selectedMediaDuration = writable<number | null>(null);

/**
 * Current playback position in seconds.
 * Updated on timeupdate by the player; pushed to CRDT awareness by the route.
 */
export const playbackPosition = writable<number>(0);

// ── UIConfig ──────────────────────────────────────────────────────────────────

/** Instance UIConfig loaded from /api/v1/uiconfig/ on mount. */
export const uiConfig = writable<UIConfig | null>(null);

/** True when the Exhibits feature is enabled (UIConfig.exhibit_config.enabled; default true). */
export const exhibitEnabled = derived(uiConfig, ($c) => $c?.exhibit_config.enabled ?? true);

/**
 * Annotation types allowed by UIConfig.annotations_config.
 * 'text' is always present. When UIConfig is not yet loaded, all types are shown.
 */
export const allowedAnnotationTypes = derived(uiConfig, ($c): AnnotationType[] => {
	if (!$c) return ['text', 'image', 'audio', 'video', 'media_ref'];
	const types: AnnotationType[] = ['text'];
	if ($c.annotations_config.allow_images) types.push('image');
	if ($c.annotations_config.allow_audio) types.push('audio');
	if ($c.annotations_config.allow_video) types.push('video');
	if ($c.annotations_config.allow_media_ref) types.push('media_ref');
	return types;
});

/** Skip-seconds pair [backward, forward] from UIConfig.player_controls; default [10, 30]. */
export const playerSkipSeconds = derived(
	uiConfig,
	($c): [number, number] => $c?.player_controls.skip_seconds ?? [10, 30]
);

/** Time range input mode from UIConfig.annotations_config; default 'slider'. */
export const timeRangeInputMode = derived(
	uiConfig,
	($c): TimeRangeInput => $c?.annotations_config.time_range_input ?? 'slider'
);

/** Whether to show the transcript text panel; default false (Phase 5 if needed). */
export const showTranscript = derived(
	uiConfig,
	($c): boolean => $c?.player_controls.show_transcript ?? false
);

/** Whether to show an audio waveform; default false. Renderer is Phase 5 — store exists for gating. */
export const showWaveform = derived(
	uiConfig,
	($c): boolean => $c?.player_controls.show_waveform ?? false
);

/** Default HLS quality from UIConfig.player_controls; default 'auto'. */
export const defaultQuality = derived(
	uiConfig,
	($c): MediaQuality => $c?.player_controls.default_quality ?? 'auto'
);

/** BCP-47 locale for date formatting from UIConfig.language; default 'en-GB'. */
export const dateLocale = derived(
	uiConfig,
	($c): string => $c?.language || 'en-GB'
);
