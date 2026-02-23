function putCollectionMediaDetails() {
    return {
        name: '',
        description: '',
        tags: [],
        tagMap: {},
        newTag: '',

        init() {
            // Fetch existing media details to populate the form
            apiCall(`/api/v1/archive/${mediaId}/`, 'GET')
                .then(data => {
                    this.name = data.name;
                    this.description = data.description;
                    this.tags = data.tags.map(tag => tag.name); // Ensure tags is an array of strings
                    this.tagMap = {}; // Initialize tagMap as an empty object
                    // Populate tagMap with tag names as keys and their ids as values
                    data.tags.forEach(tag => {
                            this.tagMap[tag.name] = tag.id;
                        }),
                        // Initialize CKEditor with the existing description
                        CKEDITOR.replace('ckeditorDescription');
                    CKEDITOR.instances.ckeditorDescription.setData(this.description);
                })
                .catch(error => {
                    console.error('Error fetching media details:', error);
                });
        },

        addTag() {
            if (this.newTag.trim() !== '' && !this.tags.includes(this.newTag)) {
                const tagToAdd = this.newTag.trim(); // Store the tag to add
                this.newTag = ''; // Clear the input field
                this.tags.push(tagToAdd); // Add the tag to the local array
                apiCall(`/api/v1/archive/add_tag/${mediaId}/`, 'PUT', {
                    tags: [tagToAdd] // Send the tag as an array to the API
                });
            }
        },

        removeTag(tagName) {
            const index = this.tags.indexOf(tagName);
            if (index !== -1) {
                this.tags.splice(index, 1); // Remove the tag from the local array
                const tagId = this.tagMap[tagName]; // Get the tag id from the map using the tag name
                if (tagId) {
                    apiCall(`/api/v1/archive/remove_tag/${mediaId}/`, 'PUT', {
                        tags: [tagId] // Send the tag ID to the API
                    }).then(() => {
                        delete this.tagMap[tagName]; // Remove the tag from the tagMap as well
                    });
                }
            }
        },

        saveMediaDetails() {
            // Prepare the data for the PUT request
            var data = new FormData();
            data.append("name", this.name);
            data.append("description", CKEDITOR.instances.ckeditorDescription.getData());
            data.append("tags", this.tags.join(',')); // Send tags as a comma-separated string

            // Send the PUT request to update the media details
            apiCall(`/api/v1/archive/${mediaId}/`, 'PUT', data)
                .then(response => {
                    window.location.replace(`/ui/collection/${groupId}/media/${mediaId}/`);
                })
                .catch(error => {
                    console.error('Error updating media details:', error);
                });
        },
        editMedia() {
            // Redirect to the edit media page
            window.location.href = `/ui/collection/${groupId}/media/${mediaId}/edit/`;
        },

        deleteMedia() {
            // Call the API to delete the media
            apiCall(`/api/v1/archive/${mediaId}/`, 'DELETE')
                .then(() => {
                    alert("Media deleted successfully.");
                    // Redirect to the collection page or update UI accordingly
                    window.location.href = `/ui/collection/${groupId}/`;
                })
                .catch(error => {
                    console.error('Error deleting media:', error);
                    alert("An error occurred while deleting the media.");
                });
        }
    };
}