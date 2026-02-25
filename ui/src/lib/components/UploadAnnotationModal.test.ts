/**
 * Unit tests for UploadAnnotationModal.svelte
 *
 * Verifies annotation type selector, file input visibility per type,
 * form validation, and error display.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import type { Annotation, MediaStore, Group, AnnotationType, TimeRangeInput } from '$lib/api';

// ── Mock api ───────────────────────────────────────────────────────────────────
vi.mock('$lib/api', () => ({
	annotations: {
		create: vi.fn().mockResolvedValue({ data: {} })
	}
}));

// ── Mock stores ────────────────────────────────────────────────────────────────
const mockSelectedMediaDuration = writable<number | null>(120);
const mockAllowedAnnotationTypes = writable<AnnotationType[]>([
	'text',
	'image',
	'audio',
	'video',
	'media_ref'
]);
const mockTimeRangeInputMode = writable<TimeRangeInput>('slider');
const mockPlaybackPosition = writable(0);

vi.mock('$lib/stores', () => ({
	selectedMediaDuration: mockSelectedMediaDuration,
	allowedAnnotationTypes: mockAllowedAnnotationTypes,
	timeRangeInputMode: mockTimeRangeInputMode,
	playbackPosition: mockPlaybackPosition
}));

import UploadAnnotationModal from './UploadAnnotationModal.svelte';

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

const MOCK_RECORDING: MediaStore = {
	id: 1,
	uuid: 'media-uuid-1',
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

describe('UploadAnnotationModal', () => {
	beforeEach(() => {
		mockSelectedMediaDuration.set(120);
		mockAllowedAnnotationTypes.set(['text', 'image', 'audio', 'video', 'media_ref']);
		mockTimeRangeInputMode.set('slider');
		mockPlaybackPosition.set(0);
	});

	const defaultProps = {
		showAnnotationModal: true,
		recording: MOCK_RECORDING,
		annotations: [] as Annotation[]
	};

	// ── Form controls ────────────────────────────────────────────────────────

	it('renders the Create New Annotation heading', () => {
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Create New Annotation')).toBeInTheDocument();
	});

	it('renders Annotation Type selector with all allowed types', () => {
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByLabelText('Annotation Type')).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Text' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Image' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Audio' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Video' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Media Reference' })).toBeInTheDocument();
	});

	it('renders only allowed annotation types from store', () => {
		mockAllowedAnnotationTypes.set(['text', 'image']);
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByRole('option', { name: 'Text' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Image' })).toBeInTheDocument();
		expect(screen.queryByRole('option', { name: 'Audio' })).not.toBeInTheDocument();
		expect(screen.queryByRole('option', { name: 'Video' })).not.toBeInTheDocument();
	});

	it('renders description textarea', () => {
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByLabelText('Description')).toBeInTheDocument();
	});

	it('renders tags input', () => {
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByLabelText('Tags (comma-separated)')).toBeInTheDocument();
	});

	it('renders Create Annotation and Cancel buttons', () => {
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Create Annotation')).toBeInTheDocument();
		expect(screen.getByText('Cancel')).toBeInTheDocument();
	});

	// ── Time range input modes ───────────────────────────────────────────────

	it('renders slider inputs in slider mode', () => {
		mockTimeRangeInputMode.set('slider');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByLabelText('Start Time')).toBeInTheDocument();
		expect(screen.getByLabelText('End Time')).toBeInTheDocument();
	});

	it('renders timestamp text inputs in timestamp mode', () => {
		mockTimeRangeInputMode.set('timestamp');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Time Range (MM:SS)')).toBeInTheDocument();
	});

	it('renders tap buttons in tap mode', () => {
		mockTimeRangeInputMode.set('tap');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Time Range')).toBeInTheDocument();
		expect(screen.getByText(/Set start/)).toBeInTheDocument();
		expect(screen.getByText(/Set end/)).toBeInTheDocument();
	});

	// ── Validation ───────────────────────────────────────────────────────────

	it('shows error when submitting with zero time range', async () => {
		render(UploadAnnotationModal, { props: defaultProps });
		await fireEvent.click(screen.getByText('Create Annotation'));
		await waitFor(() => {
			expect(screen.getByText('Set a time range for the annotation.')).toBeInTheDocument();
		});
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('renders without error when duration is null', () => {
		mockSelectedMediaDuration.set(null);
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Create New Annotation')).toBeInTheDocument();
	});
});
