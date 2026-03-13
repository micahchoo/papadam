/**
 * Unit tests for SearchSort.svelte
 */

import { vi, describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';

vi.mock('$lib/stores', async () => {
	const { writable } = await import('svelte/store');
	return { selectedGroupMedia: writable([]) };
});

import SearchSort from './SearchSort.svelte';

describe('SearchSort', () => {
	it('renders a search input with placeholder', () => {
		render(SearchSort);
		expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
	});

	it('renders search-by dropdown with Name and Tags options', () => {
		render(SearchSort);
		expect(screen.getByRole('option', { name: 'Name' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Tags' })).toBeInTheDocument();
	});

	it('renders sort order dropdown with all options', () => {
		render(SearchSort);
		expect(screen.getByRole('option', { name: 'Newest to Oldest' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Oldest to Newest' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Name Ascending' })).toBeInTheDocument();
		expect(screen.getByRole('option', { name: 'Name Descending' })).toBeInTheDocument();
	});

	it('renders media type filter dropdown with All/Audio/Video/Image', () => {
		render(SearchSort);
		const options = screen.getAllByRole('option');
		const labels = options.map((o) => o.textContent);
		expect(labels).toContain('All');
		expect(labels).toContain('Audio');
		expect(labels).toContain('Video');
		expect(labels).toContain('Image');
	});

	it('renders sort label text', () => {
		render(SearchSort);
		expect(screen.getByText('Sort:')).toBeInTheDocument();
		expect(screen.getByText('Type:')).toBeInTheDocument();
	});

	it('renders without error when store contains zero media items', () => {
		render(SearchSort);
		expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
	});
});
