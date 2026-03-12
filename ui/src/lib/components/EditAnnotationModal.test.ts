/**
 * Unit tests for EditAnnotationModal.svelte
 *
 * Verifies:
 * - Opens with pre-filled data from annotations.get
 * - Submits update on form submit
 * - Shows error on API failure
 * - Closes on successful submit
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import type { Annotation, User } from '$lib/api';

// ── Hoisted mocks ──────────────────────────────────────────────────────────────
const { mockTimeRangeInputMode, mockSelectedMediaDuration, mockPlaybackPosition, mockAnnoGet, mockAnnoUpdate } = vi.hoisted(() => {
	function writable<T>(initial: T) {
		let value = initial;
		const subs = new Set<(v: T) => void>();
		return {
			set(v: T) { value = v; subs.forEach((fn) => fn(v)); },
			update(fn: (v: T) => T) { value = fn(value); subs.forEach((s) => s(value)); },
			subscribe(fn: (v: T) => void) {
				fn(value);
				subs.add(fn);
				return () => { subs.delete(fn); };
			}
		};
	}
	return {
		mockTimeRangeInputMode: writable('slider'),
		mockSelectedMediaDuration: writable<number | null>(100),
		mockPlaybackPosition: writable(0),
		mockAnnoGet: vi.fn(),
		mockAnnoUpdate: vi.fn()
	};
});

vi.mock('$lib/stores', () => ({
	timeRangeInputMode: mockTimeRangeInputMode,
	selectedMediaDuration: mockSelectedMediaDuration,
	playbackPosition: mockPlaybackPosition
}));

vi.mock('$lib/api', () => ({
	annotations: {
		get: (...args: unknown[]) => mockAnnoGet(...args),
		update: (...args: unknown[]) => mockAnnoUpdate(...args)
	}
}));

import EditAnnotationModal from './EditAnnotationModal.svelte';

const MOCK_USER: User = { id: 1, username: 'alice', first_name: 'Alice', last_name: 'A' };

function makeAnnotation(overrides: Partial<Annotation> = {}): Annotation {
	return {
		id: 1,
		uuid: 'anno-uuid-1',
		media_reference_id: 'media-uuid-1',
		media_target: 't=10,30',
		annotation_text: 'Original text',
		annotation_image: null,
		annotation_audio: null,
		annotation_video: null,
		annotation_type: 'text',
		reply_to: null,
		media_ref_uuid: null,
		tags: [{ id: 1, name: 'fieldwork', count: 5 }],
		created_at: '2024-06-15T10:00:00Z',
		updated_at: '2024-06-15T10:00:00Z',
		created_by: MOCK_USER,
		...overrides
	};
}

describe('EditAnnotationModal', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockTimeRangeInputMode.set('slider');
		mockSelectedMediaDuration.set(100);
		mockPlaybackPosition.set(0);
	});

	it('opens with pre-filled data from annotations.get', async () => {
		const anno = makeAnnotation();
		mockAnnoGet.mockResolvedValueOnce({ data: anno });

		render(EditAnnotationModal, {
			props: { annotation: anno, showModal: true }
		});

		await waitFor(() => {
			expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
		});

		expect(mockAnnoGet).toHaveBeenCalledWith('anno-uuid-1');
		// Type shown as "Type: text (read-only)"
		expect(screen.getByText(/Type:.*text.*read-only/)).toBeInTheDocument();
		expect(screen.getByText('fieldwork')).toBeInTheDocument();
	});

	it('submits update on form submit', async () => {
		const anno = makeAnnotation();
		const updatedAnno = { ...anno, annotation_text: 'Updated text' };
		mockAnnoGet.mockResolvedValueOnce({ data: anno });
		mockAnnoUpdate.mockResolvedValueOnce({ data: updatedAnno });

		const onSaved = vi.fn();
		render(EditAnnotationModal, {
			props: { annotation: anno, showModal: true, onSaved }
		});

		await waitFor(() => {
			expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
		});

		const saveBtn = screen.getByText('Save');
		await fireEvent.click(saveBtn);

		await waitFor(() => {
			expect(mockAnnoUpdate).toHaveBeenCalledWith('anno-uuid-1', expect.any(FormData));
		});

		expect(onSaved).toHaveBeenCalledWith(updatedAnno);
	});

	it('shows error on API failure and does not close', async () => {
		const anno = makeAnnotation();
		mockAnnoGet.mockResolvedValueOnce({ data: anno });
		mockAnnoUpdate.mockRejectedValueOnce(new Error('Server error'));

		render(EditAnnotationModal, {
			props: { annotation: anno, showModal: true }
		});

		await waitFor(() => {
			expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
		});

		const saveBtn = screen.getByText('Save');
		await fireEvent.click(saveBtn);

		await waitFor(() => {
			expect(screen.getByText('Failed to update annotation.')).toBeInTheDocument();
		});

		expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
	});

	it('closes on successful submit', async () => {
		const anno = makeAnnotation();
		mockAnnoGet.mockResolvedValueOnce({ data: anno });
		mockAnnoUpdate.mockResolvedValueOnce({ data: anno });

		render(EditAnnotationModal, {
			props: { annotation: anno, showModal: true }
		});

		await waitFor(() => {
			expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
		});

		const saveBtn = screen.getByText('Save');
		await fireEvent.click(saveBtn);

		await waitFor(() => {
			expect(screen.queryByText('Edit Annotation')).not.toBeInTheDocument();
		});
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('falls back to prop data when annotations.get fails', async () => {
		const anno = makeAnnotation({ annotation_text: 'Fallback text' });
		mockAnnoGet.mockRejectedValueOnce(new Error('Network error'));

		render(EditAnnotationModal, {
			props: { annotation: anno, showModal: true }
		});

		await waitFor(() => {
			expect(screen.getByText('Edit Annotation')).toBeInTheDocument();
		});

		const textarea = screen.getByLabelText('Annotation text') as HTMLTextAreaElement;
		expect(textarea.value).toBe('Fallback text');
	});
});
