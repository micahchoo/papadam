/**
 * Unit tests for MediaPlayer.svelte
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';

vi.mock('$lib/hls', () => ({
	attachHls: vi.fn(() => ({ hls: null, destroy: vi.fn() }))
}));

vi.mock('$lib/stores', async () => {
	const { writable } = await import('svelte/store');
	return {
		selectedMediaDuration: writable(null),
		playbackPosition: writable(0),
		playerSkipSeconds: writable([10, 30]),
		defaultQuality: writable('auto')
	};
});

import MediaPlayer from './MediaPlayer.svelte';
import { playerSkipSeconds } from '$lib/stores';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const set = (store: unknown, value: unknown) => (store as any).set(value);

describe('MediaPlayer', () => {
	beforeEach(() => {
		set(playerSkipSeconds, [10, 30]);
	});

	it('renders a video element when src is a video URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		expect(
			screen.getByText(/browser does not support the video element/i)
		).toBeInTheDocument();
	});

	it('renders an audio element when src is an audio URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/track.mp3' } });
		expect(
			screen.getByText(/browser does not support the audio element/i)
		).toBeInTheDocument();
	});

	it('renders an img element when src is an image URL', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/photo.jpg' } });
		expect(screen.getByAltText('Media')).toBeInTheDocument();
	});

	it('renders fallback video element when src is empty', () => {
		render(MediaPlayer, { props: { src: '' } });
		expect(screen.queryByText(/Skip/i)).not.toBeInTheDocument();
	});

	it('renders skip buttons with correct seconds from store', () => {
		set(playerSkipSeconds, [5, 15]);
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		expect(screen.getByLabelText('Skip back 5 seconds')).toBeInTheDocument();
		expect(screen.getByLabelText('Skip forward 15 seconds')).toBeInTheDocument();
	});

	it('skip buttons reflect default skip seconds when store unchanged', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/video.mp4' } });
		expect(screen.getByLabelText('Skip back 10 seconds')).toBeInTheDocument();
		expect(screen.getByLabelText('Skip forward 30 seconds')).toBeInTheDocument();
	});

	it('does not render skip buttons for image media', () => {
		render(MediaPlayer, { props: { src: 'https://example.com/photo.png' } });
		expect(screen.queryByLabelText(/Skip/)).not.toBeInTheDocument();
	});

	it('handles src with query parameters for type detection', () => {
		render(MediaPlayer, {
			props: { src: 'https://cdn.example.com/track.mp3?token=abc' }
		});
		expect(
			screen.getByText(/browser does not support the audio element/i)
		).toBeInTheDocument();
	});

	it('treats unknown extension as video (default branch)', () => {
		render(MediaPlayer, {
			props: { src: 'https://cdn.example.com/stream.m3u8' }
		});
		expect(
			screen.getByText(/browser does not support the video element/i)
		).toBeInTheDocument();
	});
});
