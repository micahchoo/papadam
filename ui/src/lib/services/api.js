import axios from 'axios';

const API_URL = 'http://192.168.1.5:8000/';
const AUTH_TOKEN = 'a95f2d84e9fff4d5c70f35c497be60dad24b3984'; // Hardcoded auth token
// const AUTH_TOKEN = '494bd30bee4da8563096a095c85920af2fc9d56c';

export const getCollections = async () => {
    try {
        const response = await axios.get(`${API_URL}api/v1/group/`, {
            // headers: { "Authorization": `Token ${AUTH_TOKEN}` }
        });

        // Assuming the API returns both public and private collections in 'response.data.results'
        return response.data.results;
    } catch (error) {
        console.error('Error fetching collections:', error);
        throw error;
    }
};

export const getRecordings = async (groupId) => {
    try {
        const response = await axios.get(`${API_URL}api/v1/archive/?group=${groupId}`, {
            headers: {
                "Content-Type": "application/json",
                // "Authorization": `Token ${AUTH_TOKEN}`
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching recordings:', error);
        throw error;
    }
};

export const getGroupDetails = async (groupId) => {
    try {
        const response = await axios.get(`${API_URL}api/v1/group/${groupId}/`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${AUTH_TOKEN}`
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching group details:', error);
        throw error;
    }
};


export const uploadMedia = async (
    groupId,
    mediaFile,
    mediaName,
    mediaDescription,
    tags,
    extraField = [],
    mediaId = null,
    onProgressCallback
) => {
    try {
        const extraData = Object.values(extraField);
        const formData = new FormData();

        formData.append("name", mediaName);
        formData.append("description", mediaDescription);
        // formData.append("file_extension", mediaFile.type);

        formData.append("tags", tags);
        formData.append("group", groupId);
        formData.append("upload", mediaFile);

        if (extraField.length !== 0) {
            formData.append(
                "extra_group_response",
                `{"answers":${JSON.stringify(extraData)}}`
            );
        }

        let response = await axios.post(`${API_URL}api/v1/archive/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
                Authorization: `Token ${AUTH_TOKEN}`,
            },
            // onUploadProgress: (progressEvent) => {
            //     if (onProgressCallback) {
            //         const percentCompleted = Math.round(
            //             (progressEvent.loaded * 100) / progressEvent.total
            //         );
            //         onProgressCallback(percentCompleted);
            //     }
            // },
        })

        return response.data;
    } catch (error) {
        console.error("Error uploading media:", error);
        throw error;
    }
};



// export const uploadMedia = async (groupId, mediaFile, mediaName, mediaDescription, tags) => {
//     const formData = new FormData();
//     formData.append('group', groupId);
//     formData.append('upload', mediaFile);
//     formData.append('name', mediaName);
//     formData.append('description', mediaDescription);
//     formData.append('tags', tags);
//     try {
//         const response = await axios.post(`${API_URL}api/v1/archive/`, formData, {
//             headers: {
//                 "Content-Type": "multipart/form-data",
//                 "Authorization": `Token ${AUTH_TOKEN}`,
//             }
//         });
//         return response.data;
//     } catch (error) {
//         console.error('Error uploading media:', error);
//         throw error;
//     }
// };

export const uploadAnnotation = async (selectedMediaId, mediaName, tags, startTime, endTime) => {
    const formData = new FormData();
    formData.append('media_reference_id', selectedMediaId);
    formData.append('annotation_image', '');
    formData.append('annotation_text', mediaName);
    formData.append('media_target', `t=${startTime},${endTime}`);
    formData.append('tags', tags);

    try {
        const response = await axios.post(`${API_URL}api/v1/annotate/`, formData, {
            headers: {
                "Content-Type": "multipart/form-data",
                "Authorization": `Token ${AUTH_TOKEN}`,
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error uploading annotation:', error);
        throw error;
    }

};

export const updateMedia = async (id, mediaName, mediaDescription, tags) => {
    const formData = new FormData();
    formData.append('name', mediaName);
    formData.append('description', mediaDescription);
    // Ensure tags are handled correctly
    // if (tags) {
    //     formData.append('tags', tags);
    // }
    formData.append('tags', tags);
    try {
        const response = await axios.request({
            method: "PUT",
            url: `${API_URL}api/v1/archive/${id}/`,
            data: formData,
            withCredentials: true,
            headers: {
                "Content-Type": "multipart/form-data",
                "Authorization": `Token ${AUTH_TOKEN}`,
            },
        });
    } catch (error) {
        console.error("Error updating media:", error);
        if (error.response) {
            console.error("Response Status:", error.response.status);
            console.error("Response Data:", error.response.data);
            console.error("Response Headers:", error.response.headers);
        }
        throw error; // Throw error to be handled in the caller function
    }
};

export const getMedia = async (mediaId) => {
    try {
        const response = await axios.get(`${API_URL}api/v1/archive/${mediaId}/`, {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Token ${AUTH_TOKEN}`
            }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching media:', error);
        throw error;
    }
};

export const deleteRecording = async (mediaId) => {
    const options = {
        method: "DELETE",
        url: `${API_URL}api/v1/archive/${mediaId}/`,
        headers: {
            Authorization: `Token ${AUTH_TOKEN}`,
        },
    };

    try {
        const response = await axios.request(options);
        return response;
    } catch (error) {
        console.error("Error deleting media:", error);
        throw error;
    }
};

export const handleDelete = async (annoId) => {
    const options = {
        method: "DELETE",
        url: `${API_URL}api/v1/annotate/${annoId}/`,
        headers: {
            Authorization: `Token ${AUTH_TOKEN}`,
        },
    };

    try {
        const response = await axios.request(options);
        return response;
    } catch (error) {
        console.error("Error deleting media:", error);
        throw error;
    }
};


