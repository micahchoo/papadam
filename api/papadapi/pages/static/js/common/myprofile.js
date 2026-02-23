let isProfileFetched = false;

function getMyProfile() {
    return {
        myName: '',
        usernameWidth: 0, // Add a new variable to store the width of the username

        init() {
            if (tokenValue != null && !isProfileFetched) {
                isProfileFetched = true;
                apiCall("/auth/users/me/", 'GET')
                    .then(data => {
                        window.currentUserData = data;
                        window.myCollections = data.groups;
                        this.myName = data.username;
                        this.getUsernameWidth(); // Call the method to calculate the width of the username
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            }
        },

        getUsernameWidth() {
            // Get the width of the username element
            this.$nextTick(() => {
                this.usernameWidth = this.$refs.username.offsetWidth;
            });
        }
    };
}