import '@testing-library/svelte/vitest';
import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

// Mock Y.js IndexedDB provider — don't touch real browser storage in unit tests
vi.mock('y-indexeddb', () => ({
	IndexeddbPersistence: vi.fn().mockImplementation(() => ({
		whenSynced: Promise.resolve(),
		destroy: vi.fn()
	}))
}));

// Mock y-websocket provider
vi.mock('y-websocket', () => ({
	WebsocketProvider: vi.fn().mockImplementation(() => ({
		awareness: {
			setLocalState: vi.fn(),
			getLocalState: vi.fn(() => ({
				user_id: 'u1',
				username: 'alice',
				color: '#aed581',
				cursor: 0
			})),
			getStates: vi.fn(() => new Map())
		},
		destroy: vi.fn(),
		disconnect: vi.fn(),
		connect: vi.fn(),
		on: vi.fn()
	}))
}));
