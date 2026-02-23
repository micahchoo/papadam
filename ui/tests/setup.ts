import '@testing-library/svelte/vitest'

// Mock Y.js IndexedDB provider — don't touch real browser storage in unit tests
vi.mock('y-indexeddb', () => ({
  IndexeddbPersistence: vi.fn().mockImplementation(() => ({
    whenSynced: Promise.resolve(),
    destroy: vi.fn(),
  })),
}))

// Mock y-websocket provider
vi.mock('y-websocket', () => ({
  WebsocketProvider: vi.fn().mockImplementation(() => ({
    awareness: { setLocalState: vi.fn(), getStates: vi.fn(() => new Map()) },
    disconnect: vi.fn(),
    connect: vi.fn(),
    on: vi.fn(),
  })),
}))
