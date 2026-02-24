// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}

	// Declare Vite env vars as named properties so noPropertyAccessFromIndexSignature
	// allows dot notation and types are specific rather than `any`.
	interface ImportMetaEnv {
		readonly VITE_API_URL?: string;
		readonly VITE_CRDT_URL?: string;
	}
}

export {};
