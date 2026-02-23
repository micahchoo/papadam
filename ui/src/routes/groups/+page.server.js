import { getCollections } from '$lib/services/api.js';

export async function load() {
    const collections = await getCollections();
    return {
        collections
    };
}