/**
 * Unit tests for $lib/crdt
 *
 * y-indexeddb and y-websocket are mocked via tests/setup.ts.
 * Tests verify the Y.js document lifecycle and annotation CRDT operations.
 */

import { describe, it, expect, afterEach, vi } from 'vitest';
import { get } from 'svelte/store';
import {
	openMediaDoc,
	addAnnotation,
	getLiveAnnotations,
	deleteAnnotation,
	onAnnotationsChange,
	setAwarenessCursor,
	getAwarenessStates,
	type Awareness
} from '$lib/crdt';
import { selectedMediaDuration } from '$lib/stores';

const OPTS = { wsUrl: 'ws://localhost:1234', token: 'tok', userId: 'u1', username: 'alice' };

// Each test group uses a unique UUID to avoid registry collisions
describe('openMediaDoc', () => {
	it('returns a MediaDoc with doc, annotations, metadata, persistence', () => {
		const doc = openMediaDoc('crdt-test-open-1', OPTS);
		expect(doc.doc).toBeDefined();
		expect(doc.annotations).toBeDefined();
		expect(doc.metadata).toBeDefined();
		expect(doc.persistence).toBeDefined();
		doc.destroy();
	});

	it('returns the same instance for the same UUID (registry cache)', () => {
		const doc1 = openMediaDoc('crdt-test-cache-1', OPTS);
		const doc2 = openMediaDoc('crdt-test-cache-1', OPTS);
		expect(doc1).toBe(doc2);
		doc1.destroy();
	});

	it('destroy() removes from registry so next open creates a fresh doc', () => {
		const doc1 = openMediaDoc('crdt-test-destroy-1', OPTS);
		doc1.destroy();
		const doc2 = openMediaDoc('crdt-test-destroy-1', OPTS);
		expect(doc1).not.toBe(doc2);
		doc2.destroy();
	});
});

describe('addAnnotation + getLiveAnnotations', () => {
	const UUID = 'crdt-test-anno-1';

	afterEach(() => {
		openMediaDoc(UUID, OPTS).destroy();
	});

	it('adds an annotation and retrieves it as a live annotation', () => {
		openMediaDoc(UUID, OPTS);

		addAnnotation(UUID, {
			uuid: 'anno-a',
			annotation_text: 'Hello world',
			media_target: '00:00:10-00:00:20',
			tags: ['tag1', 'tag2'],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'alice',
			created_at: '2024-01-01T00:00:00Z',
			is_delete: false
		});

		const live = getLiveAnnotations(UUID);
		expect(live).toHaveLength(1);
		expect(live[0]!.uuid).toBe('anno-a');
		expect(live[0]!.annotation_text).toBe('Hello world');
		expect(live[0]!.tags).toEqual(['tag1', 'tag2']);
		expect(live[0]!.annotation_type).toBe('text');
	});

	it('getLiveAnnotations returns empty array for unknown media UUID', () => {
		expect(getLiveAnnotations('non-existent-uuid')).toEqual([]);
	});

	it('multiple annotations are returned sorted by created_at', () => {
		openMediaDoc(UUID, OPTS);

		addAnnotation(UUID, {
			uuid: 'anno-b2',
			annotation_text: 'Second',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'alice',
			created_at: '2024-01-02T00:00:00Z',
			is_delete: false
		});
		addAnnotation(UUID, {
			uuid: 'anno-b1',
			annotation_text: 'First',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'alice',
			created_at: '2024-01-01T00:00:00Z',
			is_delete: false
		});

		const live = getLiveAnnotations(UUID);
		expect(live[0]!.uuid).toBe('anno-b1');
		expect(live[1]!.uuid).toBe('anno-b2');
	});
});

describe('addAnnotation (error path)', () => {
	it('throws if no doc is open for the media UUID', () => {
		expect(() =>
			addAnnotation('no-such-uuid', {
				uuid: 'x',
				annotation_text: 'fail',
				media_target: '',
				tags: [],
				annotation_type: 'text',
				reply_to: null,
				media_ref_uuid: null,
				created_by: 'u1',
				created_at: '2024-01-01T00:00:00Z',
				is_delete: false
			})
		).toThrow('No open doc for media no-such-uuid');
	});
});

describe('deleteAnnotation', () => {
	const UUID = 'crdt-test-delete-1';

	afterEach(() => {
		openMediaDoc(UUID, OPTS).destroy();
	});

	it('soft-deletes: annotation disappears from getLiveAnnotations', () => {
		openMediaDoc(UUID, OPTS);

		addAnnotation(UUID, {
			uuid: 'anno-del',
			annotation_text: 'Will be deleted',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'u1',
			created_at: '2024-01-01T00:00:00Z',
			is_delete: false
		});

		expect(getLiveAnnotations(UUID)).toHaveLength(1);
		deleteAnnotation(UUID, 'anno-del');
		expect(getLiveAnnotations(UUID)).toHaveLength(0);
	});

	it('deleteAnnotation on unknown media UUID is a no-op', () => {
		expect(() => deleteAnnotation('no-such-media', 'no-such-anno')).not.toThrow();
	});

	it('deleteAnnotation on unknown annotation UUID (media open) is a no-op', () => {
		openMediaDoc(UUID, OPTS);
		// annotation 'ghost-anno' was never added — Y.Map.get returns undefined
		expect(() => deleteAnnotation(UUID, 'ghost-anno')).not.toThrow();
		expect(getLiveAnnotations(UUID)).toHaveLength(0);
	});
});

describe('onAnnotationsChange', () => {
	const UUID = 'crdt-test-observe-1';

	afterEach(() => {
		openMediaDoc(UUID, OPTS).destroy();
	});

	it('callback fires when an annotation is added', () => {
		openMediaDoc(UUID, OPTS);
		let callCount = 0;
		const unsub = onAnnotationsChange(UUID, () => {
			callCount++;
		});

		addAnnotation(UUID, {
			uuid: 'anno-obs',
			annotation_text: 'Observed',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'u1',
			created_at: '2024-01-01T00:00:00Z',
			is_delete: false
		});

		expect(callCount).toBeGreaterThan(0);
		unsub();
	});

	it('onAnnotationsChange on unknown UUID is a no-op (returns noop unsub)', () => {
		const unsub = onAnnotationsChange('no-such-uuid', () => {});
		expect(() => unsub()).not.toThrow();
	});

	it('unsubscribe stops future callbacks', () => {
		openMediaDoc(UUID, OPTS);
		let callCount = 0;
		const unsub = onAnnotationsChange(UUID, () => {
			callCount++;
		});

		addAnnotation(UUID, {
			uuid: 'anno-obs-2',
			annotation_text: 'Before unsub',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'u1',
			created_at: '2024-01-01T00:00:00Z',
			is_delete: false
		});

		const countAfterFirst = callCount;
		unsub();

		addAnnotation(UUID, {
			uuid: 'anno-obs-3',
			annotation_text: 'After unsub',
			media_target: '',
			tags: [],
			annotation_type: 'text',
			reply_to: null,
			media_ref_uuid: null,
			created_by: 'u1',
			created_at: '2024-01-02T00:00:00Z',
			is_delete: false
		});

		expect(callCount).toBe(countAfterFirst);
	});
});

describe('setAwarenessCursor', () => {
	const UUID = 'crdt-test-cursor-1';

	afterEach(() => {
		openMediaDoc(UUID, OPTS).destroy();
	});

	it('updates setLocalState with new cursor and pushes to selectedMediaDuration store', () => {
		const doc = openMediaDoc(UUID, OPTS);

		setAwarenessCursor(UUID, 42.5);

		// awareness is non-null when a doc is open; test files have no-non-null-assertion off
		expect(doc.awareness!.setLocalState).toHaveBeenCalledWith(
			expect.objectContaining({ cursor: 42.5 })
		);
		// selectedMediaDuration Svelte store should reflect the new position
		expect(get(selectedMediaDuration)).toBe(42.5);
	});

	it('is a no-op for an unknown media UUID', () => {
		expect(() => setAwarenessCursor('no-such-uuid', 10)).not.toThrow();
	});

	it('is a no-op when getLocalState returns null (awareness not initialised)', () => {
		const doc = openMediaDoc(UUID, OPTS);
		vi.mocked(doc.awareness!.getLocalState).mockReturnValueOnce(null);
		vi.mocked(doc.awareness!.setLocalState).mockClear(); // discard openMediaDoc's init call
		expect(() => setAwarenessCursor(UUID, 99)).not.toThrow();
		expect(doc.awareness!.setLocalState).not.toHaveBeenCalled();
	});
});

describe('getAwarenessStates', () => {
	const UUID = 'crdt-test-states-1';

	afterEach(() => {
		openMediaDoc(UUID, OPTS).destroy();
	});

	it('returns the result of awareness.getStates() as a Map', () => {
		const mockStates = new Map<number, Awareness>([
			[1, { user_id: 'u1', username: 'alice', color: '#aed581', cursor: 5 }]
		]);
		const doc = openMediaDoc(UUID, OPTS);
		// awareness is non-null when a doc is open; test files have no-non-null-assertion off
		vi.mocked(doc.awareness!.getStates).mockReturnValueOnce(mockStates);

		const result = getAwarenessStates(UUID);
		expect(result).toBe(mockStates);
	});

	it('returns an empty Map for an unknown media UUID', () => {
		const result = getAwarenessStates('no-such-uuid');
		expect(result).toEqual(new Map());
	});
});
