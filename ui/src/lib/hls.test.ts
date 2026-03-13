import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockDestroy = vi.fn();
const mockLoadSource = vi.fn();
const mockAttachMedia = vi.fn();
let mockIsSupported = true;
let lastConstructorConfig: Record<string, unknown> | undefined;

const mockOn = vi.fn();

vi.mock('hls.js', () => {
	const HlsMock = vi.fn().mockImplementation((config: Record<string, unknown>) => {
		lastConstructorConfig = config;
		return {
			destroy: mockDestroy,
			loadSource: mockLoadSource,
			attachMedia: mockAttachMedia,
			on: mockOn
		};
	});
	(HlsMock as any).isSupported = () => mockIsSupported;
	(HlsMock as any).Events = { ERROR: 'hlsError' };
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

	it('calls onError with message when fatal HLS error occurs', () => {
		const el = makeMockElement();
		const onError = vi.fn();
		attachHls(el, 'https://cdn.example.com/stream/master.m3u8', undefined, onError);

		// Simulate a fatal error via the captured on() handler
		const errorHandler = mockOn.mock.calls.find(
			(call: unknown[]) => call[0] === 'hlsError'
		)?.[1];
		expect(errorHandler).toBeDefined();
		errorHandler!('hlsError', { fatal: true, type: 'networkError' });
		expect(onError).toHaveBeenCalledWith('Playback error: networkError');
	});

	it('does not call onError for non-fatal HLS errors', () => {
		const el = makeMockElement();
		const onError = vi.fn();
		attachHls(el, 'https://cdn.example.com/stream/master.m3u8', undefined, onError);

		const errorHandler = mockOn.mock.calls.find(
			(call: unknown[]) => call[0] === 'hlsError'
		)?.[1];
		errorHandler!('hlsError', { fatal: false, type: 'networkError' });
		expect(onError).not.toHaveBeenCalled();
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
