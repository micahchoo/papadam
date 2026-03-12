/**
 * Upload queue status layer.
 *
 * Reads from Workbox's Background Sync internal IndexedDB store
 * (`workbox-background-sync`) to surface pending upload status to the UI.
 * Workbox owns the actual queuing and retry — this module is read-only
 * except for the discard operation.
 */

const DB_NAME = 'workbox-background-sync';
const STORE_NAME = 'requests';
const QUEUE_NAME = 'upload-queue';

export interface QueuedUpload {
	id: number;
	url: string;
	timestamp: number;
	metadata: Record<string, unknown> | undefined;
}

function openDb(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const request = indexedDB.open(DB_NAME);
		request.onerror = () => reject(request.error);
		request.onsuccess = () => resolve(request.result);
	});
}

/** List all pending uploads in the Background Sync queue. */
export async function getQueuedUploads(): Promise<QueuedUpload[]> {
	try {
		const db = await openDb();
		return await new Promise((resolve, reject) => {
			const tx = db.transaction(STORE_NAME, 'readonly');
			const store = tx.objectStore(STORE_NAME);
			const request = store.getAll();
			request.onerror = () => reject(request.error);
			request.onsuccess = () => {
				const entries = (request.result as Array<Record<string, unknown>>).filter(
					(entry) => entry['queueName'] === QUEUE_NAME
				);
				resolve(
					entries.map((entry) => ({
						id: entry['id'] as number,
						url: (entry['requestData'] as Record<string, unknown>)?.['url'] as string,
						timestamp: entry['timestamp'] as number,
						metadata: entry['metadata'] as Record<string, unknown> | undefined
					}))
				);
			};
		});
	} catch {
		// DB may not exist yet (no failed uploads) — that's fine
		return [];
	}
}

/** Remove a single entry from the Background Sync queue. */
export async function discardUpload(id: number): Promise<void> {
	const db = await openDb();
	return new Promise((resolve, reject) => {
		const tx = db.transaction(STORE_NAME, 'readwrite');
		const store = tx.objectStore(STORE_NAME);
		const request = store.delete(id);
		request.onerror = () => reject(request.error);
		request.onsuccess = () => resolve();
	});
}

/** Get count of pending uploads. */
export async function getPendingCount(): Promise<number> {
	const uploads = await getQueuedUploads();
	return uploads.length;
}
