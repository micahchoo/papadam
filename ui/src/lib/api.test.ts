/**
 * Unit tests for $lib/api
 *
 * Verifies that each API method calls the correct HTTP verb and URL path.
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
	crdt,
	events,
	importexport,
	mediaRelation
} from '$lib/api';

describe('auth', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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

	it('refresh posts to /auth/jwt/refresh/', () => {
		auth.refresh('refresh-tok');
		expect(mockHttp.post).toHaveBeenCalledWith('/auth/jwt/refresh/', { refresh: 'refresh-tok' });
	});

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
});

describe('groups', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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
});

describe('archive', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('list accepts searchFrom + searchCollections params', () => {
		archive.list({ searchFrom: 'selected_collections', searchCollections: '5' });
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/archive/', {
			params: { searchFrom: 'selected_collections', searchCollections: '5' }
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
});

describe('annotations', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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
});

describe('tags', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('list gets /api/v1/tags/', () => {
		tags.list();
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/tags/');
	});
});

describe('exhibits', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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

	it('blocks.list gets /api/v1/exhibit/{uuid}/blocks/', () => {
		exhibits.blocks.list('ex-uuid-1');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/exhibit/ex-uuid-1/blocks/');
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
});

describe('crdt', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('loadState gets /api/v1/crdt/{uuid}/ as arraybuffer', () => {
		crdt.loadState('media-uuid-1');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/crdt/media-uuid-1/', {
			responseType: 'arraybuffer'
		});
	});

	it('saveState puts binary to /api/v1/crdt/{uuid}/', () => {
		const bytes = new Uint8Array([1, 2, 3]);
		crdt.saveState('media-uuid-1', bytes);
		expect(mockHttp.put).toHaveBeenCalledWith('/api/v1/crdt/media-uuid-1/', bytes, {
			headers: { 'Content-Type': 'application/octet-stream' }
		});
	});
});

describe('events', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('jobStatus hits /api/v1/events/jobs/{id}/', () => {
		events.jobStatus('job-xyz-123');
		expect(mockHttp.get).toHaveBeenCalledWith('/api/v1/events/jobs/job-xyz-123/');
	});
});

describe('importexport', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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
});

describe('mediaRelation', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

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
});
