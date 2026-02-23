function postCollectionMediaAnnotateDetails() {
    return {
        createCollectionMediaAnnotateDetails: {},

        init() {

            apiCall("/api/v1/annotate/", 'POST')
                .then(data => {
                    this.createCollectionMediaAnnotateDetails = data
                })
                .catch(error => {
                    console.error('Error while calling API:', error);
                });


        }
    };
}