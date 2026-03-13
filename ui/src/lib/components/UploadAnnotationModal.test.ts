/**
 * Unit tests for UploadAnnotationModal.svelte
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import type { Annotation, MediaStore, Group } from '$lib/api';

vi.mock('$lib/api', () => ({
	annotations: { create: vi.fn().mockResolvedValue({ data: {} }) }
}));

vi.mock('$lib/stores', async () => {
	const { writable } = await import('svelte/store');
	return {
		selectedMediaDuration: writable(120),
		allowedAnnotationTypes: writable(['text', 'image', 'audio', 'video', 'media_ref']),
		timeRangeInputMode: writable('slider'),
		playbackPosition: writable(0)
	};
});

import UploadAnnotationModal from './UploadAnnotationModal.svelte';
import {
	selectedMediaDuration,
	allowedAnnotationTypes,
	timeRangeInputMode
} from '$lib/stores';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const set = (store: unknown, value: unknown) => (store as any).set(value);

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
		set(selectedMediaDuration, 120);
		set(allowedAnnotationTypes, ['text', 'image', 'audio', 'video', 'media_ref']);
		set(timeRangeInputMode, 'slider');
	});

	const defaultProps = {
		showAnnotationModal: true,
		recording: MOCK_RECORDING,
		annotations: [] as Annotation[]
	};

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
		set(allowedAnnotationTypes, ['text', 'image']);
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

	it('renders slider inputs in slider mode', () => {
		set(timeRangeInputMode, 'slider');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByLabelText('Start Time')).toBeInTheDocument();
		expect(screen.getByLabelText('End Time')).toBeInTheDocument();
	});

	it('renders timestamp text inputs in timestamp mode', () => {
		set(timeRangeInputMode, 'timestamp');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Time Range (MM:SS)')).toBeInTheDocument();
	});

	it('renders tap buttons in tap mode', () => {
		set(timeRangeInputMode, 'tap');
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Time Range')).toBeInTheDocument();
		expect(screen.getByText(/Set start/)).toBeInTheDocument();
		expect(screen.getByText(/Set end/)).toBeInTheDocument();
	});

	it('shows error when submitting with zero time range', async () => {
		render(UploadAnnotationModal, { props: defaultProps });
		await fireEvent.click(screen.getByText('Create Annotation'));
		await waitFor(() => {
			expect(
				screen.getByText('Set a time range for the annotation.')
			).toBeInTheDocument();
		});
	});

	it('renders without error when duration is null', () => {
		set(selectedMediaDuration, null);
		render(UploadAnnotationModal, { props: defaultProps });
		expect(screen.getByText('Create New Annotation')).toBeInTheDocument();
	});
});
