function assetsDropzoneData() {
    return {
        progress: 0,
        isUploadTrigger: false,
        name: "",
        description: "",
        tags: '',
        uploadDetails: '',
        uploadError: '',
        tagError: '', // Error message for tags
        fileError: '', // Error message for file
        files: null, // Store files

        uploadMediaToCollection() {
            this.tagError = '';
            this.fileError = '';
            this.uploadError = '';
            this.uploadDetails = '';

            // Validate tags
            if (this.tags.trim() === '') {
                this.tagError = 'Tags cannot be empty.';
                return;
            }

            // Validate file selection
            if (!this.files || this.files.length === 0) {
                this.fileError = 'Please select a file to upload.';
                return;
            }

            this.isUploadTrigger = true;
            this.progress = 0;
            var data = new FormData();
            data.append("upload", this.files[0]);
            data.append("group", groupId); // Ensure groupId is defined
            data.append("name", this.name);
            data.append("description", CKEDITOR.instances.ckeditorDescription.getData()); // Use CKEditor data
            data.append("tags", this.tags);

            apiCall('/api/v1/archive/', 'POST', data, {}, (percentUploaded, speedKbps, speedMbps, estimateFinishTime, uploadedSizeMB, totalSizeMB) => {
                this.progress = percentUploaded;
                // Update for proper HTML rendering
                this.uploadDetails = `Uploaded ${uploadedSizeMB}/${totalSizeMB} MB @ ${speedKbps > 1 ? `${speedMbps}Mbps` : `${speedKbps}Kbps`}. Estimated finish time: ${estimateFinishTime} (Note: This is the speed at which the file is uploaded, not your internet speed)`;
            }).then(response => {
                this.uploadDetails = 'Upload completed successfully!';
                window.location.replace("/ui/collection/" + groupId + "/");
            }).catch(error => {
                this.uploadDetails = '';
                this.uploadError = 'Upload failed. Please try again.';
                console.log(this.uploadError)
                this.isUploadTrigger = false;
            });
        },

        init() {
            // Initialize CKEditor and sync with Alpine.js
            CKEDITOR.replace('ckeditorDescription', {
                on: {
                    change: function(evt) {
                        self.description = evt.editor.getData();
                    }
                }
            });
        },

        fileChosen(event) {
            this.files = event.target.files;
            this.fileError = ''; // Clear error when a file is chosen
        }
    };
}