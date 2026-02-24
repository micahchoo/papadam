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
import type { User, Group, MediaStore } from '$lib/api';

// ── Auth ──────────────────────────────────────────────────────────────────────

/** Authenticated user, null when logged out. */
export const currentUser = writable<User | null>(null);

/** Raw access token — kept in sync with localStorage by +layout.svelte. */
export const accessToken = writable<string | null>(
	typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null
);

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

// ── Single media item context ─────────────────────────────────────────────────

/** The media item currently open in the player. */
export const selectedMedia = writable<MediaStore | null>(null);

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

// ── Modal visibility ──────────────────────────────────────────────────────────

export const isUploadModalOpen = writable<boolean>(false);
export const isAnnotateModalOpen = writable<boolean>(false);
export const isEditMediaModalOpen = writable<boolean>(false);
