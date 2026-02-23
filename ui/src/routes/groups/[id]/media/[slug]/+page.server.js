// load funcrtion 
import { getMedia } from '$lib/services/api.js';

export async function load({ params }) {
    const mediaId = params.slug;

    let mediaDetails;
    try {
        const mediaData = await getMedia(mediaId);
        mediaDetails = await mediaData;
    } catch (err) {
        let error = 'Failed to fetch group media. Please try again later.';
        console.error(err);
    }
    return {
        mediaDetails
    };

    //regex, get the group id from the url


}