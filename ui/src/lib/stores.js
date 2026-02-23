import { writable } from "svelte/store";

export let selectedGroupMedia = writable(null);
export let selectedGroupDetails = writable(null);
export let selectedMediaDuration = writable(null);