/**
 * Unit tests for SearchSort.svelte
 *
 * Verifies search input rendering, sort dropdown options,
 * media type filter, and search-by toggle.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import type { MediaStore, Group, User } from '$lib/api';

// ── Mock stores ────────────────────────────────────────────────────────────────
const mockSelectedGroupMedia = writable<MediaStore[]>([]);

vi.mock('$lib/stores', () => ({
	selectedGroupMedia: mockSelectedGroupMedia
}));

import SearchSort from './SearchSort.svelte';

const MOCK_GROUP: Group = {
	id: 1,
	name: 'Test',
	description: '',
	is_public: true,
	is_active: true,
	users: [],
	extra_group_questions: [],
	delete_wait_for: 0,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

function makeMedia(overrides: Partial<MediaStore> = {}): MediaStore {
	return {
		id: 1,
		uuid: 'uuid-1',
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
		transcript_vtt_url: '',
		...overrides
	};
}

describe('SearchSort', () => {
	beforeEach(() => {
		mockSelectedGroupMedia.set([]);
	});

	// ── Renders form controls ────────────────────────────────────────────────

	it('renders a search input with placeholder', () => {
		render(SearchSort);
		expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
	});

	it('renders search-by dropdown with Name and Tags options', () => {
		render(SearchSort);
		expect(screen.getByRole('option', { name: 'Name' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Tags' })).toBeInTheDocument();
	});

	it('renders sort order dropdown with all options', () => {
		render(SearchSort);
		expect(screen.getByRole('option', { name: 'Newest to Oldest' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Oldest to Newest' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Name Ascending' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Name Descending' })).toBeInTheDocument();
	});

	it('renders media type filter dropdown with All/Audio/Video/Image', () => {
		render(SearchSort);
		const options = screen.getAllByRole('option');
		const labels = options.map((o) => o.textContent);
		expect(labels).toContain('All');
		expect(labels).toContain('Audio');
		expect(labels).toContain('Video');
		expect(labels).toContain('Image');
	});

	it('renders sort label text', () => {
		render(SearchSort);
		expect(screen.getByText('Sort:')).toBeInTheDocument();
		expect(screen.getByText('Type:')).toBeInTheDocument();
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('renders without error when store contains zero media items', () => {
		mockSelectedGroupMedia.set([]);
		render(SearchSort);
		expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
	});
});
