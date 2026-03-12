import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getQueuedUploads, discardUpload, getPendingCount } from './upload-queue';

/**
 * Minimal in-memory IndexedDB mock for the Workbox background-sync store.
 * Only implements the subset used by upload-queue.ts.
 */
function createMockIDB(entries: Record<string, unknown>[]) {
	const store: Record<string, unknown>[] = [...entries];

	const mockStore = {
		getAll: () => {
			const req = { result: null as unknown, onerror: null as unknown, onsuccess: null as unknown };
			queueMicrotask(() => {
				req.result = [...store];
				(req.onsuccess as (() => void) | null)?.();
			});
			return req;
		},
		delete: (id: number) => {
			const req = { onerror: null as unknown, onsuccess: null as unknown };
			queueMicrotask(() => {
				const idx = store.findIndex((e) => e['id'] === id);
				if (idx !== -1) store.splice(idx, 1);
				(req.onsuccess as (() => void) | null)?.();
			});
			return req;
		}
	};

	const mockDb = {
		transaction: () => ({
			objectStore: () => mockStore
		})
	};

	const openRequest = {
		result: mockDb,
		error: null,
		onerror: null as unknown,
		onsuccess: null as unknown
	};

	vi.stubGlobal('indexedDB', {
		open: () => {
			queueMicrotask(() => {
				(openRequest.onsuccess as (() => void) | null)?.();
			});
			return openRequest;
		}
	});

	return store;
}

describe('upload-queue', () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it('lists queued uploads filtered by queue name', async () => {
		createMockIDB([
			{
				id: 1,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/annotate/' },
				timestamp: 1000
			},
			{
				id: 2,
				queueName: 'other-queue',
				requestData: { url: '/api/v1/other/' },
				timestamp: 2000
			},
			{
				id: 3,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/archive/' },
				timestamp: 3000
			}
		]);

		const uploads = await getQueuedUploads();
		expect(uploads).toHaveLength(2);
		expect(uploads[0]).toEqual({
			id: 1,
			url: '/api/v1/annotate/',
			timestamp: 1000,
			metadata: undefined
		});
		expect(uploads[1]).toEqual({
			id: 3,
			url: '/api/v1/archive/',
			timestamp: 3000,
			metadata: undefined
		});
	});

	it('returns empty array when IndexedDB does not exist', async () => {
		vi.stubGlobal('indexedDB', {
			open: () => {
				const req = { error: new Error('NotFoundError'), onerror: null as unknown, onsuccess: null as unknown };
				queueMicrotask(() => {
					(req.onerror as (() => void) | null)?.();
				});
				return req;
			}
		});

		const uploads = await getQueuedUploads();
		expect(uploads).toEqual([]);
	});

	it('discards a queued upload by id', async () => {
		const store = createMockIDB([
			{
				id: 1,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/annotate/' },
				timestamp: 1000
			},
			{
				id: 2,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/archive/' },
				timestamp: 2000
			}
		]);

		await discardUpload(1);
		expect(store).toHaveLength(1);
		expect(store[0]!['id']).toBe(2);
	});

	it('returns correct pending count', async () => {
		createMockIDB([
			{
				id: 1,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/annotate/' },
				timestamp: 1000
			},
			{
				id: 2,
				queueName: 'upload-queue',
				requestData: { url: '/api/v1/archive/' },
				timestamp: 2000
			}
		]);

		const count = await getPendingCount();
		expect(count).toBe(2);
	});

	it('discardUpload does not throw when DB does not exist', async () => {
		vi.stubGlobal('indexedDB', {
			open: () => {
				const req = { error: new Error('NotFoundError'), onerror: null as unknown, onsuccess: null as unknown };
				queueMicrotask(() => {
					(req.onerror as (() => void) | null)?.();
				});
				return req;
			}
		});

		await expect(discardUpload(999)).resolves.toBeUndefined();
	});

	it('handles empty queue', async () => {
		createMockIDB([]);
		const uploads = await getQueuedUploads();
		expect(uploads).toEqual([]);
	});
});
