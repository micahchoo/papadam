/**
 * papadam API client
 *
 * Single import point for all HTTP calls in the UI.
 * No component should import axios directly.
 *
 * Base URL is read from /config.json at runtime (injected by deploy/startup.sh),
 * falling back to the VITE_API_URL env variable for local dev.
 */

import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
	id: string;
	username: string;
	first_name: string;
	last_name: string;
}

export interface Tag {
	id: number;
	name: string;
	count: number;
}

/** QuestionsSerializer — common.models.Question */
export interface Question {
	id: number;
	question: string;
	question_type: string;
	question_mandatory: boolean;
}

export interface Group {
	id: number;
	name: string;
	description: string;
	is_public: boolean;
	is_active: boolean;
	/** Nested UserSerializer objects — GroupSerializer(users, many=True, read_only=True) */
	users: User[];
	/** QuestionsSerializer(many=True) — field name matches model: extra_group_questions */
	extra_group_questions: Question[];
	delete_wait_for: number;
	tags?: Tag[];
	users_count?: number;
	media_count?: number;
	created_at: string;
	updated_at: string;
}

export type MediaProcessingStatus =
	| 'Yet to process'
	| 'Video identified'
	| 'Audio identified'
	| 'Processing started'
	| 'Processing completed'
	| 'Processing error'
	| 'Media unknown'
	| 'Stream uploading'
	| 'Stream completed'
	| 'Stream upload error';

export interface MediaStore {
	id: number;
	uuid: string;
	name: string;
	description: string;
	upload: string | null;
	tags: Tag[];
	is_public: boolean;
	/** Nested Group object — MediaStoreSerializer uses GroupSerializer (not a flat FK id) */
	group: Group;
	orig_name: string;
	orig_size: number;
	file_extension: string;
	media_processing_status: MediaProcessingStatus;
	created_at: string;
	updated_at: string;
	/** Nested User object — MediaStoreSerializer uses UserSerializer */
	created_by: User | null;
}

export type AnnotationType = 'text' | 'image' | 'audio' | 'video' | 'media_ref';

export interface Annotation {
	id: number;
	uuid: string;
	media_reference_id: string;
	media_target: string;
	annotation_text: string;
	annotation_image: string | null;
	annotation_audio: string | null;
	annotation_video: string | null;
	annotation_type: AnnotationType;
	reply_to: number | null;
	media_ref_uuid: string | null;
	tags: Tag[];
	created_at: string;
	updated_at: string;
	/** Nested User object — AnnotationSerializer uses UserSerializer */
	created_by: User | null;
}

export type ExhibitBlockType = 'media' | 'annotation';

export interface ExhibitBlock {
	id: number;
	block_type: ExhibitBlockType;
	media_uuid: string | null;
	annotation_uuid: string | null;
	caption: string;
	order: number;
	created_at: string;
}

export interface Exhibit {
	id: number;
	uuid: string;
	title: string;
	description: string;
	group: number;
	is_public: boolean;
	created_by: number | null;
	blocks: ExhibitBlock[];
	created_at: string;
	updated_at: string;
}

// ── UIConfig types ─────────────────────────────────────────────────────────────

export type UIConfigProfile = 'standard' | 'icon' | 'voice' | 'high-contrast';
export type UIConfigColorScheme = 'default' | 'warm' | 'cool' | 'high-contrast';
export type MediaQuality = 'low' | 'medium' | 'high' | 'auto';
export type TimeRangeInput = 'slider' | 'timestamp' | 'tap';

export interface UIConfigPlayerControls {
	skip_seconds: [number, number];
	show_waveform: boolean;
	show_transcript: boolean;
	default_quality: MediaQuality;
}

export interface UIConfigAnnotations {
	allow_images: boolean;
	allow_audio: boolean;
	allow_video: boolean;
	allow_media_ref: boolean;
	time_range_input: TimeRangeInput;
}

export interface UIConfigExhibit {
	enabled: boolean;
}

export interface UIConfig {
	profile: UIConfigProfile;
	brand_name: string;
	brand_logo_url: string;
	primary_color: string;
	accent_color: string;
	language: string;
	icon_set: string;
	font_scale: number;
	color_scheme: UIConfigColorScheme;
	voice_enabled: boolean;
	offline_first: boolean;
	player_controls: UIConfigPlayerControls;
	annotations_config: UIConfigAnnotations;
	exhibit_config: UIConfigExhibit;
	updated_at: string | null;
}

/**
 * Response from archive.create() — MediaStore fields plus the ARQ job ID
 * for the HLS conversion task (null when no conversion is needed, e.g. unknown type).
 */
export type MediaCreateResponse = MediaStore & { job_id: string | null };

export interface PaginatedResponse<T> {
	count: number;
	next: string | null;
	previous: string | null;
	results: T[];
}

export interface TokenPair {
	access: string;
	refresh: string;
}

// ── Client setup ──────────────────────────────────────────────────────────────

async function resolveBaseUrl(): Promise<string> {
	if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
	try {
		const resp = await fetch('/config.json');
		const cfg = (await resp.json()) as { API_URL?: string };
		return cfg.API_URL ?? '';
	} catch {
		return '';
	}
}

let baseURL = '';
const http = axios.create({ baseURL });

// Propagate the resolved URL into the already-created axios instance.
// Must come after `http` is declared so the closure captures the binding.
void resolveBaseUrl().then((url) => {
	baseURL = url;
	http.defaults.baseURL = url;
});

// Attach access token from localStorage on every request
http.interceptors.request.use((config) => {
	const token = localStorage.getItem('access_token');
	if (token) config.headers.Authorization = `Bearer ${token}`;
	return config;
});

interface RetryableConfig extends InternalAxiosRequestConfig {
	_retry?: boolean;
}

// Attempt JWT refresh on 401; redirect to login on second failure
http.interceptors.response.use(
	(r) => r,
	async (rawErr: unknown) => {
		if (!axios.isAxiosError(rawErr)) {
			return Promise.reject(rawErr instanceof Error ? rawErr : new Error(String(rawErr)));
		}
		const original = rawErr.config as RetryableConfig | undefined;
		if (rawErr.response?.status === 401 && original && !original._retry) {
			original._retry = true;
			const refresh = localStorage.getItem('refresh_token');
			if (refresh) {
				try {
					const { data } = await axios.post<{ access: string }>(`${baseURL}/auth/jwt/refresh/`, {
						refresh
					});
					localStorage.setItem('access_token', data.access);
					original.headers['Authorization'] = `Bearer ${data.access}`;
					return await http(original);
				} catch {
					// refresh also failed — fall through to logout
				}
			}
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			window.location.href = '/auth/login';
		}
		return Promise.reject(rawErr);
	}
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export const auth = {
	login: (username: string, password: string) =>
		http.post<TokenPair>('/auth/jwt/create/', { username, password }),

	refresh: (refresh: string) => http.post<{ access: string }>('/auth/jwt/refresh/', { refresh }),

	me: () => http.get<User>('/auth/users/me/'),

	register: (payload: {
		username: string;
		password: string;
		email: string;
		first_name: string;
		last_name: string;
	}) => http.post<User>('/auth/users/', payload)
};

// ── Groups ────────────────────────────────────────────────────────────────────

export const groups = {
	list: (params?: { page?: number }) =>
		http.get<PaginatedResponse<Group>>('/api/v1/group/', { params }),

	get: (id: number) => http.get<Group>(`/api/v1/group/${id}/`),

	create: (payload: Partial<Group>) => http.post<Group>('/api/v1/group/', payload),

	update: (id: number, payload: Partial<Group>) =>
		http.patch<Group>(`/api/v1/group/${id}/`, payload),

	delete: (id: number) => http.delete(`/api/v1/group/${id}/`)
};

// ── Archive (media) ───────────────────────────────────────────────────────────

export const archive = {
	/**
	 * List media — backend filters by searchFrom/searchCollections, not by group id directly.
	 * For a specific group: { searchFrom: 'selected_collections', searchCollections: String(groupId) }
	 */
	list: (params?: {
		search?: string;
		searchWhere?: 'name' | 'description' | 'tags';
		searchFrom?: 'all_collections' | 'my_collections' | 'public' | 'selected_collections';
		searchCollections?: string; // comma-separated group IDs
		page?: number;
		page_size?: number;
	}) => http.get<PaginatedResponse<MediaStore>>('/api/v1/archive/', { params }),

	get: (uuid: string) => http.get<MediaStore>(`/api/v1/archive/${uuid}/`),

	create: (formData: FormData) =>
		http.post<MediaCreateResponse>('/api/v1/archive/', formData, {
			headers: { 'Content-Type': 'multipart/form-data' }
		}),

	update: (uuid: string, formData: FormData) =>
		http.patch<MediaStore>(`/api/v1/archive/${uuid}/`, formData, {
			headers: { 'Content-Type': 'multipart/form-data' }
		}),

	delete: (uuid: string) => http.delete(`/api/v1/archive/${uuid}/`)
};

// ── Annotations ───────────────────────────────────────────────────────────────

export const annotations = {
	list: (params?: {
		group?: number;
		search?: string;
		searchWhere?: string;
		searchFrom?: string;
		page?: number;
	}) => http.get<PaginatedResponse<Annotation>>('/api/v1/annotate/', { params }),

	/**
	 * Fetch all annotations for a media item.
	 * Backend: AnnotationByMediaRetreiveSet registered at annotate/search, lookup_field=uuid.
	 * Returns a list (not paginated — the view uses many=True directly).
	 */
	byMedia: (mediaUuid: string) => http.get<Annotation[]>(`/api/v1/annotate/search/${mediaUuid}/`),

	get: (uuid: string) => http.get<Annotation>(`/api/v1/annotate/${uuid}/`),

	create: (formData: FormData) =>
		http.post<Annotation>('/api/v1/annotate/', formData, {
			headers: { 'Content-Type': 'multipart/form-data' }
		}),

	update: (uuid: string, formData: FormData) =>
		http.patch<Annotation>(`/api/v1/annotate/${uuid}/`, formData, {
			headers: { 'Content-Type': 'multipart/form-data' }
		}),

	delete: (uuid: string) => http.delete(`/api/v1/annotate/${uuid}/`),

	addTag: (uuid: string, tagName: string) =>
		http.post(`/api/v1/annotate/${uuid}/add_tag/`, { tag: tagName }),

	removeTag: (uuid: string, tagName: string) =>
		http.post(`/api/v1/annotate/${uuid}/remove_tag/`, { tag: tagName })
};

// ── Tags ──────────────────────────────────────────────────────────────────────

export const tags = {
	list: () => http.get<Tag[]>('/api/v1/tags/')
};

// ── Exhibits ──────────────────────────────────────────────────────────────────

export const exhibits = {
	list: (params?: { group?: number; page?: number }) =>
		http.get<PaginatedResponse<Exhibit>>('/api/v1/exhibit/', { params }),

	get: (uuid: string) => http.get<Exhibit>(`/api/v1/exhibit/${uuid}/`),

	create: (payload: Partial<Exhibit>) => http.post<Exhibit>('/api/v1/exhibit/', payload),

	update: (uuid: string, payload: Partial<Exhibit>) =>
		http.patch<Exhibit>(`/api/v1/exhibit/${uuid}/`, payload),

	delete: (uuid: string) => http.delete(`/api/v1/exhibit/${uuid}/`),

	blocks: {
		/** GET /api/v1/exhibit/<uuid>/blocks/ — ordered block list */
		list: (exhibitUuid: string) =>
			http.get<ExhibitBlock[]>(`/api/v1/exhibit/${exhibitUuid}/blocks/`),

		/** POST /api/v1/exhibit/<uuid>/blocks/ — append a block */
		create: (
			exhibitUuid: string,
			payload: Pick<
				ExhibitBlock,
				'block_type' | 'media_uuid' | 'annotation_uuid' | 'caption' | 'order'
			>
		) => http.post<ExhibitBlock>(`/api/v1/exhibit/${exhibitUuid}/blocks/`, payload),

		/** DELETE /api/v1/exhibit/<uuid>/blocks/<id>/ — remove a block */
		delete: (exhibitUuid: string, blockId: number) =>
			http.delete(`/api/v1/exhibit/${exhibitUuid}/blocks/${blockId}/`),

		/**
		 * POST /api/v1/exhibit/<uuid>/blocks/reorder/
		 * Body: { block_ids: number[] } — ordered list of block PKs for this exhibit.
		 * Sets each block's order to its index in the supplied list.
		 */
		reorder: (exhibitUuid: string, blockIds: number[]) =>
			http.post<ExhibitBlock[]>(`/api/v1/exhibit/${exhibitUuid}/blocks/reorder/`, {
				block_ids: blockIds
			})
	}
};

// ── CRDT ──────────────────────────────────────────────────────────────────────

export const crdt = {
	/** Load binary Y.js state for a media item */
	loadState: (mediaUuid: string) =>
		http.get<ArrayBuffer>(`/api/v1/crdt/${mediaUuid}/`, {
			responseType: 'arraybuffer'
		}),

	/** Persist binary Y.js state delta */
	saveState: (mediaUuid: string, binary: Uint8Array) =>
		http.put(`/api/v1/crdt/${mediaUuid}/`, binary, {
			headers: { 'Content-Type': 'application/octet-stream' }
		})
};

// ── Events / Job status ───────────────────────────────────────────────────────

export type JobStatus = 'queued' | 'in_progress' | 'complete' | 'not_found' | 'failed';

export interface JobStatusResponse {
	job_id: string;
	status: JobStatus;
}

export const events = {
	/** GET /api/v1/events/jobs/<job_id>/ — current ARQ job status */
	jobStatus: (jobId: string) => http.get<JobStatusResponse>(`/api/v1/events/jobs/${jobId}/`)
};

// ── Media relations (replies + media-ref annotations) ─────────────────────────

export interface CreateReplyPayload {
	annotation_text: string;
	media_target?: string;
	annotation_type?: AnnotationType;
	tags?: string;
}

export const mediaRelation = {
	/** GET /api/v1/media-relation/replies/<annotation_uuid>/ — direct replies to an annotation */
	replies: (annotationUuid: string) =>
		http.get<Annotation[]>(`/api/v1/media-relation/replies/${annotationUuid}/`),

	/** POST /api/v1/media-relation/replies/<annotation_uuid>/ — post a reply */
	createReply: (annotationUuid: string, payload: CreateReplyPayload) =>
		http.post<Annotation>(`/api/v1/media-relation/replies/${annotationUuid}/`, payload),

	/** GET /api/v1/media-relation/media-refs/<media_uuid>/ — media_ref annotations pointing at this media */
	mediaRefs: (mediaUuid: string) =>
		http.get<Annotation[]>(`/api/v1/media-relation/media-refs/${mediaUuid}/`)
};

// ── UIConfig ──────────────────────────────────────────────────────────────────

export const uiconfig = {
	get: () => http.get<UIConfig>('/api/v1/uiconfig/'),
	patch: (payload: Partial<Omit<UIConfig, 'updated_at'>>) =>
		http.patch<UIConfig>('/api/v1/uiconfig/', payload)
};

// ── Import / Export ───────────────────────────────────────────────────────────

export const importexport = {
	requestExport: (groupId: number) => http.post('/api/v1/export/', { group: groupId }),

	requestImport: (formData: FormData) =>
		http.post('/api/v1/import/', formData, {
			headers: { 'Content-Type': 'multipart/form-data' }
		}),

	listRequests: () => http.get('/api/v1/myierequests/')
};
