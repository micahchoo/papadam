function putCollectionDetails() {
    return {
        editCollectionDetails: {
            name: '',
            description: '',
            is_public: 'true'
        },
        loading: false,
        error: null,

        init() {
            this.loading = true;
            apiCall(`/api/v1/group/${groupId}/`, 'GET')
                .then(data => {
                    this.editCollectionDetails = data
                    // Initialize CKEditor here
                    if (CKEDITOR.instances['description']) {
                        CKEDITOR.instances['description'].destroy(true);
                    }
                    CKEDITOR.replace('description');
                    CKEDITOR.instances['description'].setData(this.editCollectionDetails.description);
                })
                .catch(error => {
                    console.error('Error fetching collection details:', error);
                    this.error = error;
                })
                .finally(() => {
                    this.loading = false;
                });
        },

        submitForm() {
            this.editCollectionDetails.description = CKEDITOR.instances['description'].getData();
            this.editCollectionDetails.users = null;
            this.loading = true;
            apiCall(`/api/v1/group/${groupId}/`, 'PUT', this.editCollectionDetails)
                .then(data => {
                    window.location.replace(`/ui/collection/${data.id}/`);
                })
                .catch(error => {
                    console.error('Error updating collection:', error);
                    this.error = error;
                })
                .finally(() => {
                    this.loading = false;
                });
        }
    };
}