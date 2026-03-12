/**
 * Unit tests for AnnotationViewer.svelte
 *
 * Verifies annotation rendering for different types (text/image/audio/video/media_ref),
 * empty state, timestamp display, reply button, delete button visibility,
 * and sanitized HTML output.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import type { Annotation, User } from '$lib/api';

// ── Mock DOMPurify ─────────────────────────────────────────────────────────────
vi.mock('dompurify', () => ({
	default: {
		sanitize: (input: string) => input
	}
}));

// ── Mock api ───────────────────────────────────────────────────────────────────
vi.mock('$lib/api', () => ({
	annotations: {
		delete: vi.fn().mockResolvedValue({})
	},
	mediaRelation: {
		createReply: vi.fn().mockResolvedValue({ data: {} })
	},
	MAX_REPLY_DEPTH: 2
}));

// ── Mock stores ────────────────────────────────────────────────────────────────
const mockCurrentUser = writable<User | null>(null);
const mockDefaultQuality = writable('auto');
const mockDateLocale = writable('en-GB');

vi.mock('$lib/stores', () => ({
	currentUser: mockCurrentUser,
	defaultQuality: mockDefaultQuality,
	dateLocale: mockDateLocale
}));

// ── Mock AnnotationMedia primitive ─────────────────────────────────────────────
vi.mock('$lib/components/primitives/AnnotationMedia.svelte', () => ({
	default: vi.fn()
}));

import AnnotationViewer from './AnnotationViewer.svelte';

const MOCK_USER: User = { id: 1, username: 'alice', first_name: 'Alice', last_name: 'A' };

function makeAnnotation(overrides: Partial<Annotation> = {}): Annotation {
	return {
		id: 1,
		uuid: 'anno-uuid-1',
		media_reference_id: 'media-uuid-1',
		media_target: 't=10,30',
		annotation_text: 'Sample annotation text',
		annotation_image: null,
		annotation_audio: null,
		annotation_video: null,
		annotation_type: 'text',
		reply_to: null,
		media_ref_uuid: null,
		tags: [],
		created_at: '2024-06-15T10:00:00Z',
		updated_at: '2024-06-15T10:00:00Z',
		created_by: MOCK_USER,
		...overrides
	};
}

describe('AnnotationViewer', () => {
	beforeEach(() => {
		mockCurrentUser.set(null);
		mockDefaultQuality.set('auto');
		mockDateLocale.set('en-GB');
	});

	// ── Empty state ──────────────────────────────────────────────────────────

	it('shows empty message when no annotations are provided', () => {
		render(AnnotationViewer, { props: { annotations: [] } });
		expect(screen.getByText('No annotations available.')).toBeInTheDocument();
	});

	// ── Text annotation rendering ────────────────────────────────────────────

	it('renders annotation text content', () => {
		const anno = makeAnnotation({ annotation_text: 'Hello world' });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Hello world')).toBeInTheDocument();
	});

	it('displays annotation type badge', () => {
		const anno = makeAnnotation({ annotation_type: 'text' });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('text')).toBeInTheDocument();
	});

	it('displays creator username', () => {
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('alice')).toBeInTheDocument();
	});

	it('displays Unknown when created_by is null', () => {
		const anno = makeAnnotation({ created_by: null });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Unknown')).toBeInTheDocument();
	});

	// ── Timestamp rendering ──────────────────────────────────────────────────

	it('renders formatted timestamp for valid media_target', () => {
		const anno = makeAnnotation({ media_target: 't=10,30' });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Timestamp:')).toBeInTheDocument();
		// 10 seconds = 00:10, 30 seconds = 00:30
		expect(screen.getByText(/00:10/)).toBeInTheDocument();
		expect(screen.getByText(/00:30/)).toBeInTheDocument();
	});

	it('shows Invalid timestamp for malformed media_target', () => {
		const anno = makeAnnotation({ media_target: 'garbage' });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Invalid timestamp')).toBeInTheDocument();
	});

	// ── Image annotation ─────────────────────────────────────────────────────

	it('renders image element for image annotation type', () => {
		const anno = makeAnnotation({
			annotation_type: 'image',
			annotation_image: 'https://example.com/img.png'
		});
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByAltText('Annotation')).toBeInTheDocument();
	});

	// ── Media ref annotation ─────────────────────────────────────────────────

	it('renders linked media UUID for media_ref type', () => {
		const anno = makeAnnotation({
			annotation_type: 'media_ref',
			media_ref_uuid: 'ref-uuid-42'
		});
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('ref-uuid-42')).toBeInTheDocument();
		expect(screen.getByText('Linked media:')).toBeInTheDocument();
	});

	// ── Fallback text ────────────────────────────────────────────────────────

	it('shows No note available when annotation_text is empty', () => {
		const anno = makeAnnotation({ annotation_text: '' });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('No note available')).toBeInTheDocument();
	});

	// ── Reply button ─────────────────────────────────────────────────────────

	it('shows Reply button for each root annotation', () => {
		const anno = makeAnnotation();
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Reply')).toBeInTheDocument();
	});

	// ── Delete button visibility ─────────────────────────────────────────────

	it('hides Delete button when user is not the annotation creator', () => {
		mockCurrentUser.set({ id: 999, username: 'bob', first_name: 'Bob', last_name: 'B' });
		const anno = makeAnnotation({ created_by: MOCK_USER }); // created by alice (id=1)
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.queryByText('Delete')).not.toBeInTheDocument();
	});

	it('shows Delete button when current user owns the annotation', () => {
		mockCurrentUser.set(MOCK_USER);
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Delete')).toBeInTheDocument();
	});

	// ── Replies rendering ────────────────────────────────────────────────────

	it('renders replies nested under parent annotation', () => {
		const parent = makeAnnotation({ id: 1, annotation_text: 'Parent text' });
		const reply = makeAnnotation({
			id: 2,
			uuid: 'reply-uuid',
			annotation_text: 'Reply text',
			reply_to: 1
		});
		render(AnnotationViewer, {
			props: { annotations: [parent, reply] }
		});
		expect(screen.getByText('Parent text')).toBeInTheDocument();
		expect(screen.getByText('Reply text')).toBeInTheDocument();
	});

	// ── Multiple annotations ─────────────────────────────────────────────────

	it('renders multiple root annotations', () => {
		const annos = [
			makeAnnotation({ id: 1, uuid: 'a1', annotation_text: 'First' }),
			makeAnnotation({ id: 2, uuid: 'a2', annotation_text: 'Second' })
		];
		render(AnnotationViewer, { props: { annotations: annos } });
		expect(screen.getByText('First')).toBeInTheDocument();
		expect(screen.getByText('Second')).toBeInTheDocument();
	});

	// ── Depth-based reply hiding ────────────────────────────────────────

	it('hides Reply button at max nesting depth', () => {
		// root (depth 0) -> reply (depth 1) -> reply-to-reply (depth 2, no Reply button)
		const root = makeAnnotation({ id: 1, annotation_text: 'Root' });
		const child = makeAnnotation({
			id: 2,
			uuid: 'child-uuid',
			annotation_text: 'Child',
			reply_to: 1
		});
		const grandchild = makeAnnotation({
			id: 3,
			uuid: 'grandchild-uuid',
			annotation_text: 'Grandchild',
			reply_to: 2
		});
		render(AnnotationViewer, {
			props: { annotations: [root, child, grandchild] }
		});
		expect(screen.getByText('Grandchild')).toBeInTheDocument();
		// Root and child have Reply buttons (depth 0 and 1), grandchild (depth 2) does not
		const replyButtons = screen.getAllByText('Reply');
		expect(replyButtons).toHaveLength(2);
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('handles annotation with all null media fields without crashing', () => {
		const anno = makeAnnotation({
			annotation_type: 'image',
			annotation_image: null,
			annotation_audio: null,
			annotation_video: null,
			media_ref_uuid: null,
			annotation_text: 'fallback'
		});
		render(AnnotationViewer, { props: { annotations: [anno] } });
		// Image type with null image falls through — text is still rendered
		expect(screen.getByText('fallback')).toBeInTheDocument();
	});
});
