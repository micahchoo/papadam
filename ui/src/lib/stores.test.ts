/**
 * Unit tests for $lib/stores
 *
 * Verifies initial state, derived values, and store aliases.
 * No API calls — stores only import domain types from api.ts (type-erased at runtime).
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
	currentUser,
	isAuthenticated,
	groupMediaList,
	selectedGroupMedia,
	selectedGroup,
	selectedGroupDetails,
	selectedMedia,
	selectedMediaDuration,
	playbackPosition,
	isUploadModalOpen,
	isAnnotateModalOpen
} from '$lib/stores';
import type { User, Group, MediaStore } from '$lib/api';

const MOCK_USER: User = {
	id: '1',
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
		selectedMedia.set(null);
		selectedMediaDuration.set(null);
		playbackPosition.set(0);
	});

	it('selectedMedia starts null', () => {
		expect(get(selectedMedia)).toBeNull();
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

describe('modal stores', () => {
	beforeEach(() => {
		isUploadModalOpen.set(false);
		isAnnotateModalOpen.set(false);
	});

	it('isUploadModalOpen starts false', () => {
		expect(get(isUploadModalOpen)).toBe(false);
	});

	it('isAnnotateModalOpen starts false', () => {
		expect(get(isAnnotateModalOpen)).toBe(false);
	});
});
