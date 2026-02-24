/**
 * Unit tests for $lib/events
 *
 * Verifies poll loop behaviour: status callbacks, terminal-state exit,
 * stop() cancellation, and resilience to transient network errors.
 * $lib/api is mocked — no real HTTP traffic.
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

const { mockJobStatus } = vi.hoisted(() => ({
	mockJobStatus: vi.fn()
}));

vi.mock('$lib/api', () => ({
	events: { jobStatus: mockJobStatus }
}));

import { pollJob } from '$lib/events';
import type { JobStatus } from '$lib/events';

describe('pollJob', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.useFakeTimers();
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it('invokes onStatus for each polled status until terminal', async () => {
		mockJobStatus
			.mockResolvedValueOnce({ data: { job_id: 'j1', status: 'queued' as JobStatus } })
			.mockResolvedValueOnce({ data: { job_id: 'j1', status: 'in_progress' as JobStatus } })
			.mockResolvedValueOnce({ data: { job_id: 'j1', status: 'complete' as JobStatus } });

		const onStatus = vi.fn();
		pollJob('j1', onStatus, 1_000);

		// First poll fires immediately — drain microtasks
		await vi.runAllTimersAsync();

		expect(onStatus).toHaveBeenNthCalledWith(1, 'queued');
		expect(onStatus).toHaveBeenNthCalledWith(2, 'in_progress');
		expect(onStatus).toHaveBeenNthCalledWith(3, 'complete');
		expect(mockJobStatus).toHaveBeenCalledTimes(3);
	});

	it('does not poll again after complete', async () => {
		mockJobStatus.mockResolvedValue({ data: { job_id: 'j1', status: 'complete' as JobStatus } });

		const onStatus = vi.fn();
		pollJob('j1', onStatus, 1_000);

		await vi.runAllTimersAsync();

		expect(onStatus).toHaveBeenCalledTimes(1);
		expect(mockJobStatus).toHaveBeenCalledTimes(1);
	});

	it('does not poll again after failed', async () => {
		mockJobStatus.mockResolvedValue({ data: { job_id: 'j1', status: 'failed' as JobStatus } });

		const onStatus = vi.fn();
		pollJob('j1', onStatus, 1_000);

		await vi.runAllTimersAsync();

		expect(onStatus).toHaveBeenCalledTimes(1);
		expect(onStatus).toHaveBeenCalledWith('failed');
	});

	it('does not poll again after not_found', async () => {
		mockJobStatus.mockResolvedValue({ data: { job_id: 'j1', status: 'not_found' as JobStatus } });

		const onStatus = vi.fn();
		pollJob('j1', onStatus, 1_000);

		await vi.runAllTimersAsync();

		expect(onStatus).toHaveBeenCalledTimes(1);
	});

	it('stop() cancels before the next poll fires', async () => {
		mockJobStatus.mockResolvedValue({ data: { job_id: 'j1', status: 'queued' as JobStatus } });

		const onStatus = vi.fn();
		const poller = pollJob('j1', onStatus, 1_000);

		// First poll completes
		await vi.advanceTimersByTimeAsync(0);
		expect(onStatus).toHaveBeenCalledTimes(1);

		// Cancel before the delay elapses
		poller.stop();
		await vi.advanceTimersByTimeAsync(5_000);

		// No further polls after stop()
		expect(onStatus).toHaveBeenCalledTimes(1);
	});

	it('continues polling after a transient network error', async () => {
		mockJobStatus
			.mockRejectedValueOnce(new Error('network timeout'))
			.mockResolvedValueOnce({ data: { job_id: 'j1', status: 'complete' as JobStatus } });

		const onStatus = vi.fn();
		pollJob('j1', onStatus, 1_000);

		await vi.runAllTimersAsync();

		// Error swallowed; second poll fires and delivers complete
		expect(onStatus).toHaveBeenCalledTimes(1);
		expect(onStatus).toHaveBeenCalledWith('complete');
		expect(mockJobStatus).toHaveBeenCalledTimes(2);
	});
});
