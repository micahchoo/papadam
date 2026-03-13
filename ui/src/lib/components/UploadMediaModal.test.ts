/**
 * Unit tests for UploadMediaModal.svelte
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import type { Group } from '$lib/api';

vi.mock('$lib/api', () => ({
	archive: {
		create: vi.fn().mockResolvedValue({ data: { uuid: 'new-uuid', job_id: null } })
	}
}));

vi.mock('$lib/events', () => ({
	pollJob: vi.fn(() => ({ stop: vi.fn() }))
}));

vi.mock('$lib/stores', async () => {
	const { writable } = await import('svelte/store');
	return {
		selectedGroupDetails: writable(null),
		groupMediaList: writable([])
	};
});

import UploadMediaModal from './UploadMediaModal.svelte';
import { selectedGroupDetails } from '$lib/stores';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const set = (store: unknown, value: unknown) => (store as any).set(value);

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
		set(selectedGroupDetails, MOCK_GROUP);
	});

	const defaultProps = { showUploadModal: true };

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

	it('shows No preview available when no file is selected', () => {
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText('No preview available')).toBeInTheDocument();
	});

	it('shows ellipsis when group details are null', () => {
		set(selectedGroupDetails, null);
		render(UploadMediaModal, { props: defaultProps });
		expect(screen.getByText(/Upload Media to \.\.\./)).toBeInTheDocument();
	});

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
