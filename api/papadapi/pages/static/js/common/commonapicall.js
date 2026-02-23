 /**
         * Make an API call using Axios.
         * 
         * @param {string} route - The URL route for the API call.
         * @param {string} method - The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
         * @param {Object} [data] - The data to be sent with the request (for POST, PUT).
         * @param {Object} [headers] - Additional headers for the request.
         * @returns {Promise} - A promise that resolves with the response of the API call.
         */
function updateErrorMessage(title,message){
    const errorTitle = document.getElementById("errorTitle")
    const errorDetail = document.getElementById("errorDetail")
    const errorModal = document.getElementById("errorModal")
    errorTitle.innerText = title;
    errorDetail.innerHTML = message;
    errorModal.classList.remove("hidden");
    errorModal.classList.add("block");
}

 async function apiCall(route, method, data = {}, headers = {},onProgress = null) {
    
    try {
        if (tokenValue != null) {
            headers["Authorization"] = tokenValue
        }
        const startTime = Date.now();
        const response = await axios({
            method: method,
            url: route,
            data: data,
            headers: headers,
            onUploadProgress: progressEvent => {
                if (onProgress && progressEvent.progress) {
                    let percentUploaded = Math.round((progressEvent.loaded * 100) / progressEvent.total);

                    // Calculate the time elapsed since the start of the upload
                    let timeElapsed = (Date.now() - startTime) / 1000; // Time in seconds

                    // Calculate the speed in bytes per second
                    let speedBps = progressEvent.loaded / timeElapsed;

                    // Convert the speed to Kbps
                    let speedKbps = speedBps / 1024;
                    let speedMbps = speedKbps / 1024;
                    let remainingData = progressEvent.total - progressEvent.loaded;
                    let timeRemaining = remainingData / speedBps;
                     // Convert time remaining to a more readable format (e.g., minutes and seconds)
                    let minutesRemaining = Math.floor(timeRemaining / 60);
                    let secondsRemaining = Math.floor(timeRemaining % 60);
                    
                    let totalSizeMB = progressEvent.total / 1024 / 1024; // Get total size in MB
                    // Bytes uploaded so far
                    let uploadedSize = progressEvent.loaded / 1024 / 1024 ; // Get uploaded size in MB
                    onProgress(percentUploaded,speedKbps.toFixed(2),speedMbps.toFixed(2), `${minutesRemaining}m ${secondsRemaining}s`, uploadedSize.toFixed(2), totalSizeMB.toFixed(2) ); 
                }
            }
        });
        if (response.status === 200 || response.status === 201) {
            return response.data;
        } else if (response.status === 204) {
            return true;
        } else if (response.status === 403 || response.status === 401){
            updateErrorMessage(
                "UnAuthorized",
                "Possible Reasons include <br/> 1. You are not logged in to the system <br/> 2. You are not authorized to access or modify a private resource. <br /> 3. If you are accessing a private resource, you need to be added to the collection to make changes"
            )
            return response.data
        } else if (response.status === 400) {
            updateErrorMessage(
                "Something went wrong",
                "There seems to be a data error. Please check the data you are trying to update and retry. If the issue persists, please contact the admin"
            )
            return response

        } else if (response.status === 500 || response.status === 502){
            updateErrorMessage(
                "Something went wrong at our end",
                "There seems to be something wrong with the application. There is nothing you could do here, but you could report this error to the admin."
            )
            return response.data
        } else {
            throw new Error(`Unexpected response status: ${response.status}`);
        }
    } catch (error) {
        console.error('API call error:', error);
        // Rethrow or handle error as necessary
        console.error('API call error:', error);
        console.log('Response:', error.response); // Log the response for more details
        throw error;
    }
}
