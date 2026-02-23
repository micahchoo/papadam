let isDataFetched = false;

function getCollectionDetails() {
    return {
        collectionDetails: {},
        mediaDetails: {},
        userDetails: {},
        isMobile: false,
        isLoading: true,
        isAuthorised: true,
        inCollection: false,
        loadingStories: "Amazing stories coming up! Hold tight...",

        init() {
            if (!isDataFetched) {
                isDataFetched = true;
                // These variables comes from utilitiesjs
                apiCall("/api/v1/group/" + groupId + "/", 'GET')
                    .then(data => {
                        this.collectionDetails = data
                        if (tokenValue) {
                            this.currentUserId = window.currentUserData.id || [];
                            if (this.currentUserId && this.collectionDetails.users.some(user => user.id === this.currentUserId)) {
                                this.inCollection = true;
                            }
                        }
                    })
                    .catch(error => {
                        if (error.response && error.response.status === 401) {
                            window.location.href = `/ui/unauthorised/`;
                        } else {
                            console.error('Error while calling API:', error);
                        }
                    });

                apiCall("/api/v1/archive/?searchFrom=selected_collections&searchCollections=" + groupId, 'GET')
                    .then(data => {
                        this.mediaDetails = data.results
                        this.isLoading = false
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            }
        },
        editCollection() {
            // Redirect to the edit collection page
            window.location.href = `/ui/collection/${groupId}/edit/`;
        },
        editUser() {
            // Redirect to the edit user page
            window.location.href = `/ui/collection/${groupId}/edit_user/`;
        },
        editQuestion() {
            // Redirect to the edit user page
            window.location.href = `/ui/collection/${groupId}/add_question/`;
        },
        viewMedia(mediaId) {
            window.location.href = `/ui/collection/${groupId}/media/${mediaId}/`;
        },


    };
}