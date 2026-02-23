/**
 * papadam API client
 *
 * Single import point for all HTTP calls in the UI.
 * No component should import axios directly.
 *
 * Base URL is read from /config.json at runtime (injected by deploy/startup.sh),
 * falling back to the VITE_API_URL env variable for local dev.
 */

import axios from 'axios'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface Tag {
  id: number
  name: string
  count: number
}

export interface Group {
  id: number
  name: string
  description: string
  is_public: boolean
  is_active: boolean
  users: string[]
  group_extra_questions: Record<string, unknown>
  delete_wait_for: number
  created_at: string
  updated_at: string
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
  | 'Steam upload error'

export interface MediaStore {
  id: number
  uuid: string
  name: string
  description: string
  upload: string | null
  tags: Tag[]
  is_public: boolean
  group: number
  orig_name: string
  orig_size: number
  file_extension: string
  media_processing_status: MediaProcessingStatus
  created_at: string
  updated_at: string
  created_by: string | null
}

export type AnnotationType = 'text' | 'image' | 'audio' | 'video' | 'media_ref'

export interface Annotation {
  id: number
  uuid: string
  media_reference_id: string
  media_target: string
  annotation_text: string
  annotation_image: string | null
  annotation_type: AnnotationType
  reply_to: string | null
  media_ref_uuid: string | null
  tags: Tag[]
  is_public: boolean
  group: number | null
  created_at: string
  updated_at: string
  created_by: string | null
}

export interface AnnotationThread {
  annotation: Annotation
  replies: AnnotationThread[]
}

export interface Exhibit {
  id: number
  uuid: string
  title: string
  description: string
  group: number
  is_public: boolean
  created_at: string
  updated_at: string
}

export type ExhibitBlockType = 'media' | 'annotation' | 'text' | 'heading' | 'divider'

export interface ExhibitBlock {
  id: number
  exhibit: number
  order: number
  block_type: ExhibitBlockType
  media: number | null
  annotation: number | null
  text_content: string | null
  start_time: number | null
  end_time: number | null
  display_options: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TokenPair {
  access: string
  refresh: string
}

// ── Client setup ──────────────────────────────────────────────────────────────

async function resolveBaseUrl(): Promise<string> {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL as string
  try {
    const resp = await fetch('/config.json')
    const cfg = await resp.json() as { API_URL?: string }
    return cfg.API_URL ?? ''
  } catch {
    return ''
  }
}

let baseURL = ''
resolveBaseUrl().then((url) => { baseURL = url })

const http = axios.create({ baseURL })

// Attach access token from localStorage on every request
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Attempt JWT refresh on 401; redirect to login on second failure
http.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config as typeof err.config & { _retry?: boolean }
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post<{ access: string }>(`${baseURL}/auth/jwt/refresh/`, { refresh })
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return http(original)
        } catch {
          // refresh also failed — fall through to logout
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/auth/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────

export const auth = {
  login: (username: string, password: string) =>
    http.post<TokenPair>('/auth/jwt/create/', { username, password }),

  refresh: (refresh: string) =>
    http.post<{ access: string }>('/auth/jwt/refresh/', { refresh }),

  me: () => http.get<User>('/auth/users/me/'),

  register: (payload: { username: string; password: string; email: string; first_name: string; last_name: string }) =>
    http.post<User>('/auth/users/', payload),
}

// ── Groups ────────────────────────────────────────────────────────────────────

export const groups = {
  list: (params?: { page?: number }) =>
    http.get<PaginatedResponse<Group>>('/api/v1/group/', { params }),

  get: (id: number) =>
    http.get<Group>(`/api/v1/group/${id}/`),

  create: (payload: Partial<Group>) =>
    http.post<Group>('/api/v1/group/', payload),

  update: (id: number, payload: Partial<Group>) =>
    http.patch<Group>(`/api/v1/group/${id}/`, payload),

  delete: (id: number) =>
    http.delete(`/api/v1/group/${id}/`),
}

// ── Archive (media) ───────────────────────────────────────────────────────────

export const archive = {
  list: (params?: { group?: number; page?: number }) =>
    http.get<PaginatedResponse<MediaStore>>('/api/v1/archive/', { params }),

  get: (uuid: string) =>
    http.get<MediaStore>(`/api/v1/archive/${uuid}/`),

  create: (formData: FormData) =>
    http.post<MediaStore>('/api/v1/archive/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  update: (uuid: string, formData: FormData) =>
    http.patch<MediaStore>(`/api/v1/archive/${uuid}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  delete: (uuid: string) =>
    http.delete(`/api/v1/archive/${uuid}/`),

  relations: (uuid: string) =>
    http.get<MediaStore[]>(`/api/v1/archive/${uuid}/relations/`),
}

// ── Annotations ───────────────────────────────────────────────────────────────

export const annotations = {
  list: (params?: {
    group?: number
    search?: string
    searchWhere?: string
    searchFrom?: string
    page?: number
  }) => http.get<PaginatedResponse<Annotation>>('/api/v1/annotate/', { params }),

  byMedia: (mediaUuid: string) =>
    http.get<Annotation[]>(`/api/v1/annotate/media/${mediaUuid}/`),

  thread: (annotationUuid: string) =>
    http.get<AnnotationThread>(`/api/v1/annotate/thread/${annotationUuid}/`),

  get: (uuid: string) =>
    http.get<Annotation>(`/api/v1/annotate/${uuid}/`),

  create: (formData: FormData) =>
    http.post<Annotation>('/api/v1/annotate/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  update: (uuid: string, formData: FormData) =>
    http.patch<Annotation>(`/api/v1/annotate/${uuid}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  delete: (uuid: string) =>
    http.delete(`/api/v1/annotate/${uuid}/`),

  addTag: (uuid: string, tagName: string) =>
    http.post(`/api/v1/annotate/${uuid}/add_tag/`, { tag: tagName }),

  removeTag: (uuid: string, tagName: string) =>
    http.post(`/api/v1/annotate/${uuid}/remove_tag/`, { tag: tagName }),
}

// ── Tags ──────────────────────────────────────────────────────────────────────

export const tags = {
  list: () => http.get<Tag[]>('/api/v1/tags/'),
}

// ── Exhibits ──────────────────────────────────────────────────────────────────

export const exhibits = {
  list: (params?: { group?: number; page?: number }) =>
    http.get<PaginatedResponse<Exhibit>>('/api/v1/exhibit/', { params }),

  get: (uuid: string) =>
    http.get<Exhibit>(`/api/v1/exhibit/${uuid}/`),

  create: (payload: Partial<Exhibit>) =>
    http.post<Exhibit>('/api/v1/exhibit/', payload),

  update: (uuid: string, payload: Partial<Exhibit>) =>
    http.patch<Exhibit>(`/api/v1/exhibit/${uuid}/`, payload),

  delete: (uuid: string) =>
    http.delete(`/api/v1/exhibit/${uuid}/`),

  publish: (uuid: string) =>
    http.get<{ blocks: ExhibitBlock[] }>(`/api/v1/exhibit/${uuid}/publish/`),

  blocks: {
    list: (exhibitUuid: string) =>
      http.get<ExhibitBlock[]>(`/api/v1/exhibit/${exhibitUuid}/blocks/`),

    create: (exhibitUuid: string, payload: Partial<ExhibitBlock>) =>
      http.post<ExhibitBlock>(`/api/v1/exhibit/${exhibitUuid}/blocks/`, payload),

    update: (exhibitUuid: string, blockId: number, payload: Partial<ExhibitBlock>) =>
      http.patch<ExhibitBlock>(`/api/v1/exhibit/${exhibitUuid}/blocks/${blockId}/`, payload),

    delete: (exhibitUuid: string, blockId: number) =>
      http.delete(`/api/v1/exhibit/${exhibitUuid}/blocks/${blockId}/`),
  },
}

// ── CRDT ──────────────────────────────────────────────────────────────────────

export const crdt = {
  /** Load binary Y.js state for a media item */
  loadState: (mediaUuid: string) =>
    http.get<ArrayBuffer>(`/api/v1/crdt/media/${mediaUuid}/`, {
      responseType: 'arraybuffer',
    }),

  /** Persist binary Y.js state delta */
  saveState: (mediaUuid: string, binary: Uint8Array) =>
    http.put(`/api/v1/crdt/media/${mediaUuid}/`, binary, {
      headers: { 'Content-Type': 'application/octet-stream' },
    }),
}

// ── Import / Export ───────────────────────────────────────────────────────────

export const importexport = {
  requestExport: (groupId: number) =>
    http.post('/api/v1/export/', { group: groupId }),

  requestImport: (formData: FormData) =>
    http.post('/api/v1/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  listRequests: () =>
    http.get('/api/v1/ie/'),
}
