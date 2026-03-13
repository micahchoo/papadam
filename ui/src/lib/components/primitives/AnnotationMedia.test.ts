/**
 * Unit tests for AnnotationMedia.svelte (primitive)
 *
 * Verifies correct media element rendering based on mediaType prop
 * (audio vs video) and fallback text content.
 */

import { vi, describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';

// ── Mock HLS ───────────────────────────────────────────────────────────────────
vi.mock('$lib/hls', () => ({
	attachHls: vi.fn(() => ({
		hls: null,
		destroy: vi.fn()
	}))
}));

import AnnotationMedia from './AnnotationMedia.svelte';

describe('AnnotationMedia', () => {
	// ── Audio rendering ──────────────────────────────────────────────────────

	it('renders audio element with fallback text for audio type', () => {
		render(AnnotationMedia, {
			props: { src: 'https://example.com/clip.mp3', mediaType: 'audio' }
		});
		expect(screen.getByText(/does not support audio playback/i)).toBeInTheDocument();
	});

	// ── Video rendering ──────────────────────────────────────────────────────

	it('renders video element with fallback text for video type', () => {
		render(AnnotationMedia, {
			props: { src: 'https://example.com/clip.mp4', mediaType: 'video' }
		});
		expect(screen.getByText(/does not support video playback/i)).toBeInTheDocument();
	});

	// ── HLS start level ──────────────────────────────────────────────────────

	it('accepts hlsStartLevel prop without error', () => {
		render(AnnotationMedia, {
			props: {
				src: 'https://example.com/stream.m3u8',
				mediaType: 'video',
				hlsStartLevel: 0
			}
		});
		expect(screen.getByText(/does not support video playback/i)).toBeInTheDocument();
	});

	// ── Adversarial ──────────────────────────────────────────────────────────

	it('renders without error when src is empty string', () => {
		render(AnnotationMedia, {
			props: { src: '', mediaType: 'audio' }
		});
		// Empty src still renders the element with fallback text
		expect(screen.getByText(/does not support audio playback/i)).toBeInTheDocument();
	});
});
