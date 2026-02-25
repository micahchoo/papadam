/**
 * Unit tests for MediaPlayer.svelte
 *
 * Verifies media element rendering (video/audio/image),
 * empty src fallback, skip button labels, and HLS integration mock.
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { writable } from 'svelte/store';

// ── Mock HLS ───────────────────────────────────────────────────────────────────
vi.mock('$lib/hls', () => ({
	attachHls: vi.fn(() => ({
		hls: null,
		destroy: vi.fn()
	}))
}));

// ── Mock stores ────────────────────────────────────────────────────────────────
const mockSelectedMediaDuration = writable<number | null>(null);
const mockPlaybackPosition = writable(0);
const mockPlayerSkipSeconds = writable<[number, number]>([10, 30]);
const mockDefaultQuality = writable('auto');

vi.mock('$lib/stores', () => ({
	selectedMediaDuration: mockSelectedMediaDuration,
	playbackPosition: mockPlaybackPosition,
	playerSkipSeconds: mockPlayerSkipSeconds,
	defaultQuality: mockDefaultQuality
}));

import MediaPlayer from './MediaPlayer.svelte';

describe('MediaPlayer', () => {
	beforeEach(() => {
		mockSelectedMediaDuration.set(null);
		mockPlaybackPosition.set(0);
		mockPlayerSkipSeconds.set([10, 30]);
		mockDefaultQuality.set('auto');
	});

	// ── Video rendering ──────────────────────────────────────────────────────

	it('renders a video element when src is a video URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		// Video element with fallback text
		expect(screen.getByText(/browser does not support the video element/i)).toBeInTheDocument();
	});

	// ── Audio rendering ──────────────────────────────────────────────────────

	it('renders an audio element when src is an audio URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/track.mp3' } });
		expect(screen.getByText(/browser does not support the audio element/i)).toBeInTheDocument();
	});

	// ── Image rendering ──────────────────────────────────────────────────────

	it('renders an img element when src is an image URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/photo.jpg' } });
		expect(screen.getByAltText('Media')).toBeInTheDocument();
	});

	// ── Empty src fallback ───────────────────────────────────────────────────

	it('renders fallback video element when src is empty', () => {
		render(MediaPlayer, { props: { src: '' } });
		// When src is empty, renders a plain <video> without skip buttons
		expect(screen.queryByText(/Skip/i)).not.toBeInTheDocument();
	});

	// ── Skip buttons ─────────────────────────────────────────────────────────

	it('renders skip buttons with correct seconds from store', () => {
		mockPlayerSkipSeconds.set([5, 15]);
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		expect(screen.getByLabelText('Skip back 5 seconds')).toBeInTheDocument();
		expect(screen.getByLabelText('Skip forward 15 seconds')).toBeInTheDocument();
	});

	it('skip buttons reflect default skip seconds when store unchanged', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		expect(screen.getByLabelText('Skip back 10 seconds')).toBeInTheDocument();
		expect(screen.getByLabelText('Skip forward 30 seconds')).toBeInTheDocument();
	});

	// ── No skip buttons for image ────────────────────────────────────────────

	it('does not render skip buttons for image media', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/photo.png' } });
		expect(screen.queryByLabelText(/Skip/)).not.toBeInTheDocument();
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('handles src with query parameters for type detection', () => {
		// .mp3 with query string should still be detected as audio
		render(MediaPlayer, { props: { src: 'https://cdn.example.com/track.mp3?token=abc' } });
		expect(screen.getByText(/browser does not support the audio element/i)).toBeInTheDocument();
	});

	it('treats unknown extension as video (default branch)', () => {
		// .m3u8 HLS manifest is not audio or image, falls to video
		render(MediaPlayer, { props: { src: 'https://cdn.example.com/stream.m3u8' } });
		expect(screen.getByText(/browser does not support the video element/i)).toBeInTheDocument();
	});
});
