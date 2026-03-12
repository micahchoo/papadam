/**
 * Unit tests for $lib/api
 *
 * Section 1 (per module): Route contract — verifies correct HTTP verb + URL.
 * Section 2 (per module): Response handling — asserts response shapes and error propagation.
 * Each describe block includes at least one adversarial case.
 *
 * Axios is fully mocked — no real network traffic.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';

// Prevent real fetch call in resolveBaseUrl (runs at module init)
global.fetch = vi.fn().mockResolvedValue({
	json: () => Promise.resolve({})
});

// Hoist mock HTTP instance so it is accessible inside vi.mock factory
const { mockHttp } = vi.hoisted(() => ({
	mockHttp: {
		get: vi.fn(),
		post: vi.fn(),
		patch: vi.fn(),
		delete: vi.fn(),
		put: vi.fn(),
		defaults: { baseURL: '' },
		interceptors: {
			request: { use: vi.fn() },
			response: { use: vi.fn() }
		}
	}
}));

vi.mock('axios', () => ({
	default: {
		create: vi.fn(() => mockHttp),
		post: vi.fn()
	}
}));

import {
	auth,
	archive,
	annotations,
	groups,
	tags,
	exhibits,
	events,
	importexport,
	mediaRelation,
	uiconfig
} from '$lib/api';

describe('auth', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('login posts to /auth/jwt/create/', () => {
		auth.login('alice', 'secret');
		expect(mockHttp.post).toHaveBeenCalledWith('/auth/jwt/create/', {
			username: 'alice',
			password: 'secret'
		});
	});

	it('me gets /auth/users/me/', () => {
		auth.me();
		expect(mockHttp.get).toHaveBeenCalledWith('/auth/users/me/');
	});

	// auth.refresh removed — handled by 401 interceptor

	it('register posts to /auth/users/', () => {
		auth.register({
			username: 'bob',
			password: 'pw123',
			email: 'bob@example.com',
			first_name: 'Bob',
			last_name: 'Smith'
		});
		expect(mockHttp.post).toHaveBeenCalledWith('/auth/users/', {
			username: 'bob',
			password: 'pw123',
			email: 'bob@example.com',
			first_name: 'Bob',
			last_name: 'Smith'
		});
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('login returns TokenPair shape', async () => {
		mockHttp.post.mockResolvedValueOnce({
			data: { access: 'access-tok', refresh: 'refresh-tok' }
		});
		const resp = await auth.login('alice', 'secret');
		expect(resp.data).toHaveProperty('access');
		expect(resp.data).toHaveProperty('refresh');
		expect(typeof resp.data.access).toBe('string');
		expect(typeof resp.data.refresh).toBe('string');
	});

	it('login rejects on 401', async () => {
		const error = new Error('Request failed with status code 401');
		mockHttp.post.mockRejectedValueOnce(error);
		await expect(auth.login('alice', 'wrong')).rejects.toThrow('401');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('login sends empty strings when given empty credentials', () => {
		auth.login('', '');
		expect(mockHttp.post).toHaveBeenCalledWith('/auth/jwt/create/', {
			username: '',
			password: ''
		});
	});
});

describe('groups', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('list gets /api/v1/group/', () => {
		groups.list();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/group/', { params: undefined });
	});

	it('get hits /api/v1/group/{id}/', () => {
		groups.get(42);
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/group/42/');
	});

	it('create posts to /api/v1/group/', () => {
		groups.create({ name: 'New Group' });
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/group/', { name: 'New Group' });
	});

	it('update patches /api/v1/group/{id}/', () => {
		groups.update(7, { name: 'Renamed' });
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/group/7/', { name: 'Renamed' });
	});

	it('delete deletes /api/v1/group/{id}/', () => {
		groups.delete(7);
		expect(mockHttp.delete).toHaveBeenCalledWith('/api/v1/group/7/');
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('list returns paginated shape with results array', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { count: 0, next: null, previous: null, results: [] }
		});
		const resp = await groups.list();
		expect(Array.isArray(resp.data.results)).toBe(true);
		expect(typeof resp.data.count).toBe('number');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('list with no params sends params: undefined', () => {
		groups.list();
		const call = mockHttp.get.mock.calls[0];
		expect(call?.[1]).toEqual({ params: undefined });
	});
});

describe('archive', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('list accepts searchFrom + searchCollections params', () => {
		archive.list({ searchFrom: 'selected_collections', searchCollections: '5' });
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/archive/', {
			params: { searchFrom: 'selected_collections', searchCollections: '5' }
		});
	});

	it('list accepts mediaType param', () => {
		archive.list({ mediaType: 'audio' });
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/archive/', {
			params: { mediaType: 'audio' }
		});
	});

	it('get hits /api/v1/archive/{uuid}/', () => {
		archive.get('abc-123');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/archive/abc-123/');
	});

	it('create posts to /api/v1/archive/ with multipart/form-data header', () => {
		const fd = new FormData();
		archive.create(fd);
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/archive/', fd, {
			headers: { 'Content-Type': 'multipart/form-data' }
		});
	});

	it('update patches /api/v1/archive/{uuid}/ with multipart/form-data header', () => {
		const fd = new FormData();
		archive.update('abc-123', fd);
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/archive/abc-123/', fd, {
			headers: { 'Content-Type': 'multipart/form-data' }
		});
	});

	it('delete hits /api/v1/archive/{uuid}/', () => {
		archive.delete('abc-123');
		expect(mockHttp.delete).toHaveBeenCalledWith('/api/v1/archive/abc-123/');
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('list returns paginated shape', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { count: 1, next: null, previous: null, results: [{ uuid: 'x' }] }
		});
		const resp = await archive.list();
		expect(Array.isArray(resp.data.results)).toBe(true);
		expect(resp.data.count).toBe(resp.data.results.length);
	});

	it('create resolves with job_id field', async () => {
		mockHttp.post.mockResolvedValueOnce({
			data: { uuid: 'new-uuid', job_id: 'job-1' }
		});
		const resp = await archive.create(new FormData());
		expect(resp.data).toHaveProperty('job_id');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('list with empty params sends params: undefined', () => {
		archive.list();
		const call = mockHttp.get.mock.calls[0];
		expect(call?.[1]).toEqual({ params: undefined });
	});

	it('get with empty string uuid still calls endpoint', () => {
		archive.get('');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/archive//');
	});
});

describe('annotations', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('list gets /api/v1/annotate/', () => {
		annotations.list({ group: 3 });
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/annotate/', { params: { group: 3 } });
	});

	it('byMedia hits /api/v1/annotate/search/{uuid}/ (not /media/)', () => {
		annotations.byMedia('media-uuid-99');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/annotate/search/media-uuid-99/');
	});

	it('get hits /api/v1/annotate/{uuid}/', () => {
		annotations.get('anno-uuid');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/annotate/anno-uuid/');
	});

	it('create posts to /api/v1/annotate/ with multipart/form-data header', () => {
		const fd = new FormData();
		annotations.create(fd);
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/annotate/', fd, {
			headers: { 'Content-Type': 'multipart/form-data' }
		});
	});

	it('update patches /api/v1/annotate/{uuid}/ with multipart/form-data header', () => {
		const fd = new FormData();
		annotations.update('anno-uuid', fd);
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/annotate/anno-uuid/', fd, {
			headers: { 'Content-Type': 'multipart/form-data' }
		});
	});

	it('delete hits /api/v1/annotate/{uuid}/', () => {
		annotations.delete('anno-uuid');
		expect(mockHttp.delete).toHaveBeenCalledWith('/api/v1/annotate/anno-uuid/');
	});

	it('addTag posts to /api/v1/annotate/{uuid}/add_tag/', () => {
		annotations.addTag('anno-uuid', 'fieldwork');
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/annotate/anno-uuid/add_tag/', {
			tag: 'fieldwork'
		});
	});

	it('removeTag posts to /api/v1/annotate/{uuid}/remove_tag/', () => {
		annotations.removeTag('anno-uuid', 'fieldwork');
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/annotate/anno-uuid/remove_tag/', {
			tag: 'fieldwork'
		});
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('byMedia returns array (not paginated)', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: [{ uuid: 'ann-1' }, { uuid: 'ann-2' }]
		});
		const resp = await annotations.byMedia('media-uuid');
		expect(Array.isArray(resp.data)).toBe(true);
		expect(resp.data).not.toHaveProperty('results');
	});

	it('list returns paginated shape', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { count: 1, next: null, previous: null, results: [{ uuid: 'ann-1' }] }
		});
		const resp = await annotations.list();
		expect(Array.isArray(resp.data.results)).toBe(true);
		expect(typeof resp.data.count).toBe('number');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('byMedia with empty string uuid still calls endpoint', () => {
		annotations.byMedia('');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/annotate/search//');
	});

	it('create rejects when mock rejects', async () => {
		mockHttp.post.mockRejectedValueOnce(new Error('Network Error'));
		await expect(annotations.create(new FormData())).rejects.toThrow('Network Error');
	});
});

describe('tags', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('list gets /api/v1/tags/', () => {
		tags.list();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/tags/');
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('list returns array of tags', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: [{ id: 1, name: 'fieldwork', count: 5 }]
		});
		const resp = await tags.list();
		expect(Array.isArray(resp.data)).toBe(true);
		expect(resp.data[0]).toHaveProperty('name');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('list resolves with empty array when no tags exist', async () => {
		mockHttp.get.mockResolvedValueOnce({ data: [] });
		const resp = await tags.list();
		expect(resp.data).toHaveLength(0);
	});
});

describe('exhibits', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('list gets /api/v1/exhibit/', () => {
		exhibits.list();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/exhibit/', { params: undefined });
	});

	it('get hits /api/v1/exhibit/{uuid}/', () => {
		exhibits.get('ex-uuid-1');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/');
	});

	it('create posts to /api/v1/exhibit/', () => {
		exhibits.create({ title: 'My Exhibit' });
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/exhibit/', { title: 'My Exhibit' });
	});

	it('update patches /api/v1/exhibit/{uuid}/', () => {
		exhibits.update('ex-uuid-1', { title: 'Updated' });
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/', { title: 'Updated' });
	});

	it('delete deletes /api/v1/exhibit/{uuid}/', () => {
		exhibits.delete('ex-uuid-1');
		expect(mockHttp.delete).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/');
	});

	it('blocks.create posts to /api/v1/exhibit/{uuid}/blocks/', () => {
		exhibits.blocks.create('ex-uuid-1', {
			block_type: 'media',
			media_uuid: 'med-uuid',
			annotation_uuid: null,
			caption: 'A caption',
			order: 0
		});
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/blocks/', {
			block_type: 'media',
			media_uuid: 'med-uuid',
			annotation_uuid: null,
			caption: 'A caption',
			order: 0
		});
	});

	it('blocks.delete deletes /api/v1/exhibit/{uuid}/blocks/{id}/', () => {
		exhibits.blocks.delete('ex-uuid-1', 42);
		expect(mockHttp.delete).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/blocks/42/');
	});

	it('blocks.reorder posts block_ids to /api/v1/exhibit/{uuid}/blocks/reorder/', () => {
		exhibits.blocks.reorder('ex-uuid-1', [3, 1, 2]);
		expect(mockHttp.post).toHaveBeenCalledWith(
			'/api/v1/exhibit/ex-uuid-1/blocks/reorder/',
			{ block_ids: [3, 1, 2] }
		);
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('get resolves with blocks array', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { uuid: 'ex-1', title: 'Test', blocks: [] }
		});
		const resp = await exhibits.get('ex-1');
		expect(Array.isArray(resp.data.blocks)).toBe(true);
	});

	it('blocks.reorder resolves with ordered blocks', async () => {
		mockHttp.post.mockResolvedValueOnce({
			data: [{ id: 3, order: 0 }, { id: 1, order: 1 }, { id: 2, order: 2 }]
		});
		const resp = await exhibits.blocks.reorder('ex-1', [3, 1, 2]);
		expect(Array.isArray(resp.data)).toBe(true);
		expect(resp.data.length).toBe(3);
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('blocks.reorder sends empty array when given []', () => {
		exhibits.blocks.reorder('ex-uuid-1', []);
		expect(mockHttp.post).toHaveBeenCalledWith(
			'/api/v1/exhibit/ex-uuid-1/blocks/reorder/',
			{ block_ids: [] }
		);
	});

	it('get with empty string uuid still calls endpoint', () => {
		exhibits.get('');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/exhibit//');
	});
});

// crdt.loadState/saveState tests removed — CRDT sync moved to WebSocket server

describe('events', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('jobStatus hits /api/v1/events/jobs/{id}/', () => {
		events.jobStatus('job-xyz-123');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/events/jobs/job-xyz-123/');
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('jobStatus resolves with job_id and status fields', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { job_id: 'job-1', status: 'complete' }
		});
		const resp = await events.jobStatus('job-1');
		expect(resp.data).toHaveProperty('job_id');
		expect(resp.data).toHaveProperty('status');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('jobStatus with empty string id still calls endpoint', () => {
		events.jobStatus('');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/events/jobs//');
	});
});

describe('importexport', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('listRequests hits /api/v1/myierequests/', () => {
		importexport.listRequests();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/myierequests/');
	});

	it('requestExport posts group id to /api/v1/export/', () => {
		importexport.requestExport(5);
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/export/', { group: 5 });
	});

	it('requestImport posts FormData to /api/v1/import/ with multipart/form-data header', () => {
		const fd = new FormData();
		importexport.requestImport(fd);
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/import/', fd, {
			headers: { 'Content-Type': 'multipart/form-data' }
		});
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('listRequests returns paginated shape', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: { count: 0, next: null, previous: null, results: [] }
		});
		const resp = await importexport.listRequests();
		expect(Array.isArray(resp.data.results)).toBe(true);
		expect(typeof resp.data.count).toBe('number');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('requestExport rejects when mock rejects', async () => {
		mockHttp.post.mockRejectedValueOnce(new Error('Server Error'));
		await expect(importexport.requestExport(999)).rejects.toThrow('Server Error');
	});
});

describe('mediaRelation', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('replies hits /api/v1/media-relation/replies/<uuid>/', () => {
		mediaRelation.replies('anno-uuid-42');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/media-relation/replies/anno-uuid-42/');
	});

	it('createReply posts to /api/v1/media-relation/replies/<uuid>/', () => {
		mediaRelation.createReply('anno-uuid-42', { annotation_text: 'hi' });
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/media-relation/replies/anno-uuid-42/', {
			annotation_text: 'hi'
		});
	});

	it('mediaRefs hits /api/v1/media-relation/media-refs/<uuid>/', () => {
		mediaRelation.mediaRefs('media-uuid-77');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/media-relation/media-refs/media-uuid-77/');
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('replies returns array (not paginated)', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: [{ uuid: 'reply-1' }, { uuid: 'reply-2' }]
		});
		const resp = await mediaRelation.replies('anno-uuid');
		expect(Array.isArray(resp.data)).toBe(true);
		expect(resp.data).not.toHaveProperty('results');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('createReply with empty text still posts', () => {
		mediaRelation.createReply('anno-uuid', { annotation_text: '' });
		expect(mockHttp.post).toHaveBeenCalledWith('/api/v1/media-relation/replies/anno-uuid/', {
			annotation_text: ''
		});
	});
});

describe('uiconfig', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	// ── Route contract ──────────────────────────────────────────────────────

	it('get hits /api/v1/uiconfig/', () => {
		uiconfig.get();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/uiconfig/');
	});

	it('patch sends partial UIConfig to /api/v1/uiconfig/', () => {
		uiconfig.patch({ brand_name: 'Test' });
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/uiconfig/', { brand_name: 'Test' });
	});

	// ── Response handling ────────────────────────────────────────────────────

	it('get resolves with UIConfig shape', async () => {
		mockHttp.get.mockResolvedValueOnce({
			data: {
				profile: 'standard',
				brand_name: 'Papad.alt',
				primary_color: '#333',
				updated_at: null
			}
		});
		const resp = await uiconfig.get();
		expect(resp.data).toHaveProperty('profile');
		expect(resp.data).toHaveProperty('brand_name');
	});

	// ── Adversarial ─────────────────────────────────────────────────────────

	it('patch with empty object still calls endpoint', () => {
		uiconfig.patch({});
		expect(mockHttp.patch).toHaveBeenCalledWith('/api/v1/uiconfig/', {});
	});
});

// ── Auth IDB sync ─────────────────────────────────────────────────────────────

describe('syncTokensToIdb / clearTokensFromIdb', () => {
	// These functions dual-write JWT tokens to IndexedDB so the service worker
	// can refresh auth when replaying queued uploads.

	function createMockAuthIDB() {
		const kvStore = new Map<string, string>();

		const mockStore = {
			put: (value: string, key: string) => {
				kvStore.set(key, value);
			},
			get: (key: string) => {
				const req = {
					result: null as unknown,
					onerror: null as unknown,
					onsuccess: null as unknown
				};
				queueMicrotask(() => {
					req.result = kvStore.get(key) ?? null;
					(req.onsuccess as (() => void) | null)?.();
				});
				return req;
			},
			delete: (key: string) => {
				kvStore.delete(key);
			}
		};

		const openRequest = {
			result: {
				createObjectStore: vi.fn(),
				transaction: () => ({
					objectStore: () => mockStore,
					oncomplete: null as unknown,
					onerror: null as unknown
				})
			},
			error: null,
			onerror: null as unknown,
			onsuccess: null as unknown,
			onupgradeneeded: null as unknown
		};

		vi.stubGlobal('indexedDB', {
			open: () => {
				queueMicrotask(() => {
					(openRequest.onsuccess as (() => void) | null)?.();
				});
				return openRequest;
			}
		});

		// Patch transaction to auto-fire oncomplete
		const origTransaction = openRequest.result.transaction;
		openRequest.result.transaction = (...args: Parameters<typeof origTransaction>) => {
			const tx = origTransaction(...args);
			queueMicrotask(() => {
				(tx.oncomplete as (() => void) | null)?.();
			});
			return tx;
		};

		return kvStore;
	}

	it('writes access and refresh tokens to IDB', async () => {
		const kvStore = createMockAuthIDB();
		const { syncTokensToIdb } = await import('./api');

		await syncTokensToIdb('access123', 'refresh456');
		expect(kvStore.get('access_token')).toBe('access123');
		expect(kvStore.get('refresh_token')).toBe('refresh456');
	});

	it('writes only access token when refresh is omitted', async () => {
		const kvStore = createMockAuthIDB();
		const { syncTokensToIdb } = await import('./api');

		await syncTokensToIdb('access789');
		expect(kvStore.get('access_token')).toBe('access789');
		expect(kvStore.has('refresh_token')).toBe(false);
	});

	it('clears tokens from IDB', async () => {
		const kvStore = createMockAuthIDB();
		kvStore.set('access_token', 'old');
		kvStore.set('refresh_token', 'old');
		const { clearTokensFromIdb } = await import('./api');

		await clearTokensFromIdb();
		expect(kvStore.has('access_token')).toBe(false);
		expect(kvStore.has('refresh_token')).toBe(false);
	});

	it('does not throw when IDB is unavailable', async () => {
		vi.stubGlobal('indexedDB', {
			open: () => {
				const req = {
					error: new Error('SecurityError'),
					onerror: null as unknown,
					onsuccess: null as unknown,
					onupgradeneeded: null as unknown
				};
				queueMicrotask(() => {
					(req.onerror as (() => void) | null)?.();
				});
				return req;
			}
		});
		const { syncTokensToIdb, clearTokensFromIdb } = await import('./api');

		// Should not throw — graceful degradation
		await expect(syncTokensToIdb('tok')).resolves.toBeUndefined();
		await expect(clearTokensFromIdb()).resolves.toBeUndefined();
	});
});
