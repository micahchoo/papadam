function addRemoveUsers() {
    return {
        collectionDetails: {},
        user: null,
        userSearch: "",
        users: [], // To store the list of users retrieved from the API

        init() {
            // Fetch existing group details to populate the form
            apiCall(`/api/v1/group/${groupId}/`, 'GET')
                .then(data => {
                    this.collectionDetails = data;
                    // Set the user property to the ID of the first user, if available
                    if (this.users.length > 0) {
                        this.user = this.users[0].id;
                    }
                })
                .catch(error => {
                    console.error('Error while calling API:', error);
                });
        },

        searchUserId() {
            if (this.userSearch === "") {
                this.users = [];
            } else {
                apiCall(`/api/v1/users/search/?search=${this.userSearch}`, 'GET')
                    .then(data => {
                        this.users = data.results; // Store the list of users retrieved from the API
                    })
                    .catch(error => {
                        console.error('Error while searching for user:', error);
                    });
            }
        },

        addUser() {
            // If user is still null, get the ID of the first displayed user from the search results
            if (this.user === null && this.users.length > 0) {
                this.user = this.users[0].id;
                this.username = this.users[0].username;
            } else {
                this.selectedUser = this.users.find(user => user.id === this.user);
                this.username = this.selectedUser.username
            }

            apiCall(`/api/v1/group/add_user/${groupId}/`, 'PUT', {
                    user: this.user
                })
                .then(response => {
                    // Update the collectionDetails with the new user
                    this.collectionDetails.users.push({
                        id: this.user,
                        username: this.username
                    });

                })
                .catch(error => {
                    console.error('Error while adding user:', error);
                });
        },


        removeUser(userid) {
            // Perform an API call to remove the user from the group using the ID
            apiCall(`/api/v1/group/remove_user/${groupId}/`, 'PUT', {
                    user: userid
                })
                .then(response => {
                    // Update the collectionDetails by filtering out the removed user
                    this.collectionDetails.users = this.collectionDetails.users.filter(user => user.id !== userid);
                })
                .catch(error => {
                    console.error('Error while removing user:', error);
                });
        },

        goBack() {
            window.location.href = `/ui/collection/${groupId}/`;
        },
    };
}