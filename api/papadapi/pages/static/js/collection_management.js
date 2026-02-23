let isDataFetched = false;

function getCollectionList() {
    return {
        myCollections: {},
        publicCollections: {},
        collectionClass: 'publicCollection',
        isLoading: true,
        isLoggedIn: false,
        loadingStories: "Hold up ! We are crafting your stories...",

        init() {
            if (!isDataFetched) {
                isDataFetched = true;
                this.isLoggedIn = !!localStorage.getItem('authToken');
                apiCall("/api/v1/group", 'GET')
                    .then(data => {
                        this.publicCollections = data.results;
                        if (tokenValue != null) {
                            this.myCollections = window.myCollections || [];
                        }
                        this.isLoading = false;
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            }
        }
    };
}

function navigateToCollection(collectionId) {
    window.location.href = '/ui/collection/' + collectionId + '/';
}