function postCollectionDetails() {
    return {
        createCollectionDetails: {
            name: '',
            description: '',
            users: '',
            is_public: true // Assuming default to be public
        },
        loading: false,
        error: null,

        init() {
            // Ensure CKEditor is loaded
            if (typeof CKEDITOR === 'undefined') {
                console.error('CKEditor not found');
                return;
            }

            // Check if CKEditor instance already exists
            if (CKEDITOR.instances['description']) {
                // Destroy the existing instance
                CKEDITOR.instances['description'].destroy(true);
            }

            // Initialize CKEditor and set up change event
            CKEDITOR.replace('description', {
                on: {
                    change: () => {
                        this.createCollectionDetails.description = CKEDITOR.instances['description'].getData();
                    }
                }
            });
        },

        submitForm() {
            // Manually update the description from CKEditor before submitting
            this.createCollectionDetails.description = CKEDITOR.instances['description'].getData();

            this.loading = true;
            this.error = null;

            // Perform the API call with the form data
            apiCall("/api/v1/group/", 'POST', this.createCollectionDetails)
                .then(data => {
                    window.location.replace(`/ui/collection/${data.id}/`);
                })
                .catch(error => {
                    this.error = error;
                    console.error('Error while calling API:', error);
                })
                .finally(() => {
                    this.loading = false;
                });
        }
    };
}