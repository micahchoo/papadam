function passwordReset() {
    return {
        userEmail: '',
        linkSent: false,

        requestReset() {
            const headers = {
                'Content-Type': 'application/json'
            };

            apiCall('/auth/users/reset_password/', 'POST', {
                    email: this.userEmail
                }, headers)
                .then(data => {
                    this.linkSent = true;
                })
                .catch(error => {
                    console.error('Reset request error:', error);

                });
        }
    };
}