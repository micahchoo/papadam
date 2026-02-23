function postLogin() {
    return {
        loginDetails: {
            username: '',
            password: '',
            error_message: '',
        },
        usernameError: '',
        passwordError: '',

        doLogin() {

            const headers = {
                "Content-Type": "application/json",
            };

            // Add your API call here using Alpine.js
            apiCall('/auth/token/login', 'POST', this.loginDetails, headers)
                .then(data => {
                    localStorage.setItem("authToken", "Token " + data.auth_token)
                    window.location.replace("/ui/")
                })
                .catch(error => {
                    console.error('Error while calling API:', error);
                    if (error.response && error.response.data) {
                        if (error.response.data.username) {
                            this.usernameError = error.response.data.username[0];
                        }
                        if (error.response.data.password) {
                            this.passwordError = error.response.data.password[0];
                        }
                        if (error.response.data.non_field_errors) {
                            this.loginDetails.error_message = "Your username/password is incorrect.";

                        }
                    }
                });
        }
    };
}