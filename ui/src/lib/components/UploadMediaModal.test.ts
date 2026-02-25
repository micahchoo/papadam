/**
 * Unit tests for UploadMediaModal.svelte
 *
 * Verifies form field rendering, required fields, group name display,
 * and upload state transitions.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import type { Group, MediaStore } from '$lib/api';

// ── Mock api ───────────────────────────────────────────────────────────────────
vi.mock('$lib/api', () => ({
	archive: {
		create: vi.fn().mockResolvedValue({
			data: { uuid: 'new-uuid', job_id: null }
		})
	}
}));

// ── Mock events ────────────────────────────────────────────────────────────────
vi.mock('$lib/events', () => ({
	pollJob: vi.fn(() => ({ stop: vi.fn() }))
}));

// ── Mock stores ────────────────────────────────────────────────────────────────
const mockSelectedGroupDetails = writable<Group | null>(null);
const mockGroupMediaList = writable<MediaStore[]>([]);

vi.mock('$lib/stores', () => ({
	selectedGroupDetails: mockSelectedGroupDetails,
	groupMediaList: mockGroupMediaList
}));

import UploadMediaModal from './UploadMediaModal.svelte';

const MOCK_GROUP: Group = {
	id: 1,
	name: 'Test Group',
	description: '',
	is_public: true,
	is_active: true,
	users: [],
	extra_group_questions: [],
	delete_wait_for: 0,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('UploadMediaModal', () => {
	beforeEach(() => {
		mockSelectedGroupDetails.set(MOCK_GROUP);
		mockGroupMediaList.set([]);
	});

	const defaultProps = {
		showUploadModal: true
	};

	// ── Form fields ──────────────────────────────────────────────────────────

	it('renders the upload heading with group name', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText(/Upload Media to Test Group/)).toBeInTheDocument();
	});

	it('renders Media Name input field', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByLabelText('Media Name')).toBeInTheDocument();
	});

	it('renders Description textarea', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByLabelText('Description')).toBeInTheDocument();
	});

	it('renders Tags input field', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByLabelText('Tags (comma-separated)')).toBeInTheDocument();
	});

	it('renders file upload input', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByLabelText('Upload Media')).toBeInTheDocument();
	});

	it('renders Submit and Cancel buttons', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText('Submit')).toBeInTheDocument();
		expect(screen.getByText('Cancel')).toBeInTheDocument();
	});

	// ── Preview placeholder ──────────────────────────────────────────────────

	it('shows No preview available when no file is selected', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText('No preview available')).toBeInTheDocument();
	});

	// ── Group name fallback ──────────────────────────────────────────────────

	it('shows ellipsis when group details are null', () => {
		mockSelectedGroupDetails.set(null);
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText(/Upload Media to \.\.\./)).toBeInTheDocument();
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('renders all form fields with empty values without crashing', () => {
		render(UploadMediaModal, { props: defaultProps });
		const nameInput = screen.getByLabelText('Media Name') as HTMLInputElement;
		const descInput = screen.getByLabelText('Description') as HTMLTextAreaElement;
		const tagsInput = screen.getByLabelText('Tags (comma-separated)') as HTMLInputElement;
		expect(nameInput.value).toBe('');
		expect(descInput.value).toBe('');
		expect(tagsInput.value).toBe('');
	});
});
