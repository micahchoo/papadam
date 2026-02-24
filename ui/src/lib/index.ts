// Re-export commonly used types through the $lib alias.
// Components should import directly from $lib/api, $lib/stores, etc.
// This file exists so `import { ... } from '$lib'` resolves cleanly.

export type { User, Tag, Group, MediaStore, Annotation, Exhibit } from '$lib/api';
