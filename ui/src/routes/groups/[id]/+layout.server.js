// load funcrtion 
import { getGroupDetails, getRecordings } from '$lib/services/api.js';

export async function load({ params }) {
    const groupId = params.id;
    console.log(groupId)
    let groupDetails, recordingsDetails;
    try {
        const [groupData, recordingsData] = await Promise.all([
            getGroupDetails(groupId),
            getRecordings(groupId)
        ]);
    
    groupDetails = await groupData;
    recordingsDetails = await recordingsData.results;

    } catch (err) {
        let error = 'Failed to fetch group media. Please try again later.';
        console.error(err);
    }
    return {
        groupDetails:  groupDetails,
        recordings:  recordingsDetails
    };
}