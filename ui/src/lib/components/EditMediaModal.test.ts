/**
 * Unit tests for EditMediaModal.svelte
 *
 * Verifies form field rendering, labels, button text,
 * and validation error display.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';

// ── Mock api ───────────────────────────────────────────────────────────────────
const mockArchiveUpdate = vi.fn().mockResolvedValue({});

vi.mock('$lib/api', () => ({
	archive: {
		update: mockArchiveUpdate
	}
}));

import EditMediaModal from './EditMediaModal.svelte';

describe('EditMediaModal', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	const defaultProps = {
		showEditModal: true,
		mediaName: 'Test Media',
		mediaDescription: 'A description',
		recordingUuid: 'uuid-123'
	};

	// ── Form fields ──────────────────────────────────────────────────────────

	it('renders the Edit Media heading', () => {
		render(EditMediaModal, { props: defaultProps });
		expect(screen.getByText('Edit Media')).toBeInTheDocument();
	});

	it('renders Name and Description labels', () => {
		render(EditMediaModal, { props: defaultProps });
		expect(screen.getByLabelText('Name')).toBeInTheDocument();
		expect(screen.getByLabelText('Description')).toBeInTheDocument();
	});

	it('renders Save Changes and Cancel buttons', () => {
		render(EditMediaModal, { props: defaultProps });
		expect(screen.getByText('Save Changes')).toBeInTheDocument();
		expect(screen.getByText('Cancel')).toBeInTheDocument();
	});

	it('pre-fills form fields with provided props', () => {
		render(EditMediaModal, { props: defaultProps });
		const nameInput = screen.getByLabelText('Name') as HTMLInputElement;
		const descTextarea = screen.getByLabelText('Description') as HTMLTextAreaElement;
		expect(nameInput.value).toBe('Test Media');
		expect(descTextarea.value).toBe('A description');
	});

	// ── Validation ───────────────────────────────────────────────────────────

	it('shows validation error when name is empty on submit', async () => {
		render(EditMediaModal, {
			props: { ...defaultProps, mediaName: '', mediaDescription: 'desc' }
		});
		await fireEvent.click(screen.getByText('Save Changes'));
		expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
	});

	it('shows validation error when description is empty on submit', async () => {
		render(EditMediaModal, {
			props: { ...defaultProps, mediaName: 'Name', mediaDescription: '' }
		});
		await fireEvent.click(screen.getByText('Save Changes'));
		expect(screen.getByText('Please fill in all fields.')).toBeInTheDocument();
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('shows API error message when update fails', async () => {
		mockArchiveUpdate.mockRejectedValueOnce(new Error('Server Error'));
		render(EditMediaModal, { props: defaultProps });
		await fireEvent.click(screen.getByText('Save Changes'));
		await waitFor(() => {
			expect(screen.getByText('Failed to update media.')).toBeInTheDocument();
		});
	});
});
