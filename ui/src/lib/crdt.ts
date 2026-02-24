/**
 * papadam CRDT client
 *
 * Initialises a Y.js document for a given media item.
 * Provides typed accessors for the annotation map, metadata, and awareness.
 *
 * Architecture boundary: this module may only import from $lib/stores.
 * Components access CRDT state via Svelte stores, not directly from here.
 */

import * as Y from 'yjs';
import { IndexeddbPersistence } from 'y-indexeddb';
import { WebsocketProvider } from 'y-websocket';
import { selectedMediaDuration } from '$lib/stores';

// ── Types matching ARCHITECTURE.md CRDT schema ────────────────────────────────

export type AnnotationType = 'text' | 'image' | 'audio' | 'video' | 'media_ref';

export interface CRDTAnnotation {
	uuid: string;
	annotation_text: Y.Text;
	media_target: string;
	tags: Y.Array<string>;
	annotation_type: AnnotationType;
	reply_to: string | null;
	media_ref_uuid: string | null;
	created_by: string;
	created_at: string;
	is_delete: boolean;
}

export interface Awareness {
	user_id: string;
	username: string;
	color: string;
	cursor: number; // playback position in seconds
}

export interface MediaDoc {
	doc: Y.Doc;
	annotations: Y.Map<Y.Map<unknown>>;
	metadata: Y.Map<unknown>;
	provider: WebsocketProvider | null;
	persistence: IndexeddbPersistence;
	awareness: WebsocketProvider['awareness'] | null;
	destroy: () => void;
}

// ── Stable colours for user presence ─────────────────────────────────────────

const PRESENCE_COLOURS = [
	'#e57373',
	'#64b5f6',
	'#81c784',
	'#ffb74d',
	'#ba68c8',
	'#4dd0e1',
	'#f06292',
	'#aed581'
];

function colourForUser(userId: string): string {
	let hash = 0;
	for (let i = 0; i < userId.length; i++) hash = userId.charCodeAt(i) + ((hash << 5) - hash);
	return PRESENCE_COLOURS[Math.abs(hash) % PRESENCE_COLOURS.length] ?? '#aed581';
}

// ── Active doc registry (one doc per media UUID per tab) ─────────────────────

const registry = new Map<string, MediaDoc>();

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Open (or reuse) a Y.js document for a media item.
 * Automatically persists to IndexedDB for offline use.
 * Connects to the CRDT WebSocket server when online.
 */
export function openMediaDoc(
	mediaUuid: string,
	opts: {
		wsUrl: string;
		token: string;
		userId: string;
		username: string;
	}
): MediaDoc {
	const existing = registry.get(mediaUuid);
	if (existing) return existing;

	const doc = new Y.Doc();
	const annotations = doc.getMap<Y.Map<unknown>>('annotations');
	const metadata = doc.getMap<unknown>('metadata');

	// Offline persistence — survives page reload without a server round-trip
	const persistence = new IndexeddbPersistence(`papadam:media:${mediaUuid}`, doc);

	// Online sync — connects when available, reconnects automatically
	let provider: WebsocketProvider | null = null;
	let awareness: WebsocketProvider['awareness'] | null = null;

	if (typeof window !== 'undefined') {
		provider = new WebsocketProvider(opts.wsUrl, `media:${mediaUuid}`, doc, {
			params: { token: opts.token }
		});

		awareness = provider.awareness;
		awareness.setLocalState({
			user_id: opts.userId,
			username: opts.username,
			color: colourForUser(opts.userId),
			cursor: 0
		} satisfies Awareness);
	}

	const mediaDoc: MediaDoc = {
		doc,
		annotations,
		metadata,
		provider,
		persistence,
		awareness,
		destroy() {
			provider?.destroy();
			void persistence.destroy();
			doc.destroy();
			registry.delete(mediaUuid);
		}
	};

	registry.set(mediaUuid, mediaDoc);
	return mediaDoc;
}

/**
 * Update the local awareness cursor position (playback position).
 * Called by the player on timeupdate.
 */
export function setAwarenessCursor(mediaUuid: string, positionSeconds: number): void {
	const entry = registry.get(mediaUuid);
	if (!entry?.awareness) return;
	const current = entry.awareness.getLocalState() as Awareness | null;
	if (!current) return;
	entry.awareness.setLocalState({ ...current, cursor: positionSeconds });
	// Also push to the Svelte store so the player waveform can react
	selectedMediaDuration.set(positionSeconds);
}

/**
 * Add a new annotation to the CRDT document.
 * Returns the annotation UUID.
 */
export function addAnnotation(
	mediaUuid: string,
	payload: Omit<CRDTAnnotation, 'annotation_text' | 'tags'> & {
		annotation_text: string;
		tags: string[];
	}
): string {
	const entry = registry.get(mediaUuid);
	if (!entry) throw new Error(`No open doc for media ${mediaUuid}`);

	const { annotations, doc } = entry;
	const annoMap = new Y.Map<unknown>();
	const text = new Y.Text(payload.annotation_text);
	const tagsArr = new Y.Array<string>();
	tagsArr.push(payload.tags);

	doc.transact(() => {
		annoMap.set('uuid', payload.uuid);
		annoMap.set('annotation_text', text);
		annoMap.set('media_target', payload.media_target);
		annoMap.set('tags', tagsArr);
		annoMap.set('annotation_type', payload.annotation_type);
		annoMap.set('reply_to', payload.reply_to);
		annoMap.set('media_ref_uuid', payload.media_ref_uuid);
		annoMap.set('created_by', payload.created_by);
		annoMap.set('created_at', payload.created_at);
		annoMap.set('is_delete', false);
		annotations.set(payload.uuid, annoMap);
	});

	return payload.uuid;
}

/**
 * Soft-delete an annotation in the CRDT document.
 * The server will also set is_delete=true on the normalized record.
 */
export function deleteAnnotation(mediaUuid: string, annotationUuid: string): void {
	const entry = registry.get(mediaUuid);
	if (!entry) return;
	const annoMap = entry.annotations.get(annotationUuid);
	if (!annoMap) return;
	entry.doc.transact(() => {
		annoMap.set('is_delete', true);
	});
}

/**
 * Get all live (non-deleted) annotations from the CRDT document as plain objects.
 * Reactive: call inside a Svelte $effect or subscribe to the Y.Map observer.
 */
export function getLiveAnnotations(mediaUuid: string): Array<{
	uuid: string;
	annotation_text: string;
	media_target: string;
	tags: string[];
	annotation_type: AnnotationType;
	reply_to: string | null;
	media_ref_uuid: string | null;
	created_by: string;
	created_at: string;
}> {
	const entry = registry.get(mediaUuid);
	if (!entry) return [];

	const result = [];
	for (const [, annoMap] of entry.annotations) {
		if (annoMap.get('is_delete') === true) continue;
		result.push({
			uuid: annoMap.get('uuid') as string,
			annotation_text: (annoMap.get('annotation_text') as Y.Text).toString(),
			media_target: annoMap.get('media_target') as string,
			tags: (annoMap.get('tags') as Y.Array<string>).toArray(),
			annotation_type: annoMap.get('annotation_type') as AnnotationType,
			reply_to: (annoMap.get('reply_to') as string | null) ?? null,
			media_ref_uuid: (annoMap.get('media_ref_uuid') as string | null) ?? null,
			created_by: annoMap.get('created_by') as string,
			created_at: annoMap.get('created_at') as string
		});
	}
	return result.sort((a, b) => a.created_at.localeCompare(b.created_at));
}

/**
 * Subscribe to annotation changes for a media item.
 * Returns an unsubscribe function.
 */
export function onAnnotationsChange(mediaUuid: string, callback: () => void): () => void {
	const entry = registry.get(mediaUuid);
	if (!entry) return () => undefined;
	entry.annotations.observe(callback);
	return () => entry.annotations.unobserve(callback);
}

/**
 * Get all current awareness states (connected users + their cursor positions).
 */
export function getAwarenessStates(mediaUuid: string): Map<number, Awareness> {
	const entry = registry.get(mediaUuid);
	if (!entry?.awareness) return new Map();
	return entry.awareness.getStates() as Map<number, Awareness>;
}
