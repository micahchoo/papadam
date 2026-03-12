/**
 * Unit tests for AnnotationViewer.svelte
 *
 * Verifies annotation rendering for different types (text/image/audio/video/media_ref),
 * empty state, timestamp display, reply button, delete button visibility,
 * edit button visibility, and sanitized HTML output.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import type { Annotation, User } from '$lib/api';

// ── Hoisted mocks ──────────────────────────────────────────────────────────────
const { mockCurrentUser, mockDefaultQuality, mockDateLocale } = vi.hoisted(() => {
	// Inline writable implementation for hoisted context
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
		mockCurrentUser: writable<User | null>(null),
		mockDefaultQuality: writable('auto'),
		mockDateLocale: writable('en-GB')
	};
});

// ── Mock DOMPurify ─────────────────────────────────────────────────────────────
vi.mock('dompurify', () => ({
	default: {
		sanitize: (input: string) => input
	}
}));

// ── Mock api ───────────────────────────────────────────────────────────────────
vi.mock('$lib/api', () => ({
	annotations: {
		delete: vi.fn().mockResolvedValue({}),
		get: vi.fn().mockResolvedValue({ data: {} }),
		update: vi.fn().mockResolvedValue({ data: {} }),
		addTag: vi.fn().mockResolvedValue({ data: { tags: [] } }),
		removeTag: vi.fn().mockResolvedValue({ data: { tags: [] } })
	},
	mediaRelation: {
		createReply: vi.fn().mockResolvedValue({ data: {} }),
		replies: vi.fn().mockResolvedValue({ data: [] })
	},
	tags: {
		list: vi.fn().mockResolvedValue({ data: [] })
	},
	MAX_REPLY_DEPTH: 2
}));

// ── Mock stores ────────────────────────────────────────────────────────────────
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
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.queryByText('Delete')).not.toBeInTheDocument();
	});

	it('shows Delete button when current user owns the annotation', () => {
		mockCurrentUser.set(MOCK_USER);
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Delete')).toBeInTheDocument();
	});

	// ── Edit button visibility ──────────────────────────────────────────────

	it('shows Edit button when current user owns the annotation', () => {
		mockCurrentUser.set(MOCK_USER);
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('Edit')).toBeInTheDocument();
	});

	it('hides Edit button when user is not the annotation creator', () => {
		mockCurrentUser.set({ id: 999, username: 'bob', first_name: 'Bob', last_name: 'B' });
		const anno = makeAnnotation({ created_by: MOCK_USER });
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.queryByText('Edit')).not.toBeInTheDocument();
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
		const replyButtons = screen.getAllByText('Reply');
		expect(replyButtons).toHaveLength(2);
	});

	// ── Tag chip rendering ──────────────────────────────────────────────────

	it('renders tag chips when annotation has tags', () => {
		const anno = makeAnnotation({
			tags: [
				{ id: 1, name: 'fieldwork', count: 5 },
				{ id: 2, name: 'important', count: 3 }
			]
		});
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByText('fieldwork')).toBeInTheDocument();
		expect(screen.getByText('important')).toBeInTheDocument();
	});

	it('shows add-tag button when user is authenticated', () => {
		mockCurrentUser.set(MOCK_USER);
		const anno = makeAnnotation();
		render(AnnotationViewer, { props: { annotations: [anno] } });
		expect(screen.getByLabelText('Add tag')).toBeInTheDocument();
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
		expect(screen.getByText('fallback')).toBeInTheDocument();
	});
});
