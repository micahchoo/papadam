import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockDestroy = vi.fn();
const mockLoadSource = vi.fn();
const mockAttachMedia = vi.fn();
let mockIsSupported = true;
let lastConstructorConfig: Record<string, unknown> | undefined;

vi.mock('hls.js', () => {
	const HlsMock = vi.fn().mockImplementation((config: Record<string, unknown>) => {
		lastConstructorConfig = config;
		return {
			destroy: mockDestroy,
			loadSource: mockLoadSource,
			attachMedia: mockAttachMedia
		};
	});
	(HlsMock as any).isSupported = () => mockIsSupported;
	return { default: HlsMock };
});

import { attachHls } from '$lib/hls';

function makeMockElement(): HTMLMediaElement {
	return { src: '' } as unknown as HTMLMediaElement;
}

beforeEach(() => {
	vi.clearAllMocks();
	mockIsSupported = true;
	lastConstructorConfig = undefined;
});

describe('attachHls', () => {
	it('creates Hls instance for m3u8 URL when supported', () => {
		const el = makeMockElement();
		const handle = attachHls(el, 'https://cdn.example.com/stream/master.m3u8');

		expect(handle.hls).not.toBeNull();
		expect(mockLoadSource).toHaveBeenCalledWith(
			'https://cdn.example.com/stream/master.m3u8'
		);
		expect(mockAttachMedia).toHaveBeenCalledWith(el);
		expect(el.src).toBe('');
	});

	it('falls back to direct src when Hls is not supported', () => {
		mockIsSupported = false;
		const el = makeMockElement();
		const handle = attachHls(el, 'https://cdn.example.com/stream/master.m3u8');

		expect(handle.hls).toBeNull();
		expect(el.src).toBe('https://cdn.example.com/stream/master.m3u8');
		expect(mockLoadSource).not.toHaveBeenCalled();
	});

	it('sets el.src directly for non-m3u8 URL', () => {
		const el = makeMockElement();
		const handle = attachHls(el, 'https://cdn.example.com/video.mp4');

		expect(handle.hls).toBeNull();
		expect(el.src).toBe('https://cdn.example.com/video.mp4');
		expect(mockLoadSource).not.toHaveBeenCalled();
	});

	it('forwards startLevel parameter to Hls constructor', () => {
		const el = makeMockElement();
		attachHls(el, 'https://cdn.example.com/stream/master.m3u8', 0);

		expect(lastConstructorConfig).toEqual(
			expect.objectContaining({ startLevel: 0 })
		);
	});

	it('defaults startLevel to -1 when not provided', () => {
		const el = makeMockElement();
		attachHls(el, 'https://cdn.example.com/stream/master.m3u8');

		expect(lastConstructorConfig).toEqual(
			expect.objectContaining({ startLevel: -1 })
		);
	});

	it('destroy function destroys the Hls instance', () => {
		const el = makeMockElement();
		const handle = attachHls(el, 'https://cdn.example.com/stream/master.m3u8');

		handle.destroy();
		expect(mockDestroy).toHaveBeenCalledOnce();
	});

	it('destroy is a no-op for non-HLS handles', () => {
		const el = makeMockElement();
		const handle = attachHls(el, 'https://cdn.example.com/video.mp4');

		// Should not throw
		handle.destroy();
		expect(mockDestroy).not.toHaveBeenCalled();
	});

	// Adversarial: empty string URL
	it('sets el.src to empty string for empty URL', () => {
		const el = makeMockElement();
		const handle = attachHls(el, '');

		expect(handle.hls).toBeNull();
		expect(el.src).toBe('');
		expect(mockLoadSource).not.toHaveBeenCalled();
	});
});
