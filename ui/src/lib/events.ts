/**
 * papadam job-status poller
 *
 * Wraps GET /api/v1/events/jobs/<job_id>/ with a simple poll loop.
 * Stops automatically when the job reaches a terminal state.
 *
 * Architecture boundary: may import from $lib/api only.
 */

import { events as eventsApi } from '$lib/api';
import type { JobStatus } from '$lib/api';

export type { JobStatus };

export interface JobPoller {
	/** Cancel polling before the job reaches a terminal state. */
	stop: () => void;
}

const TERMINAL: ReadonlySet<JobStatus> = new Set(['complete', 'failed', 'not_found']);

/**
 * Poll an ARQ background job until it reaches a terminal state.
 *
 * @param jobId      ARQ job ID returned when the task was enqueued.
 * @param onStatus   Called on every successful poll with the current status.
 * @param intervalMs Polling interval in milliseconds (default 2 000).
 */
export function pollJob(
	jobId: string,
	onStatus: (status: JobStatus) => void,
	intervalMs = 2_000
): JobPoller {
	let active = true;

	async function run(): Promise<void> {
		while (active) {
			try {
				const { data } = await eventsApi.jobStatus(jobId);
				onStatus(data.status);
				if (TERMINAL.has(data.status)) break;
			} catch {
				// Transient network error — keep polling
			}
			// eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- TypeScript narrows `active` to true inside while(active), but stop() can mutate it across an await boundary
			if (!active) break;
			await new Promise<void>((resolve) => setTimeout(resolve, intervalMs));
		}
	}

	void run();
	return {
		stop() {
			active = false;
		}
	};
}
