function postSignup() {
    return {
        signupDetails: {
            first_name: '',
            last_name: '',
            username: '',
            password: '',
            email: '',
        },
        usernameError: '',
        passwordError: '',

        async doSignUp() {
            const headers = {
                "Content-Type": "application/json",
            };

            try {
                const response = await apiCall('/auth/users/', 'POST', this.signupDetails, headers);
                window.location.replace("/ui/login");
            } catch (error) {
                console.error('Error while calling API:', error);
                // Set error messages based on specific errors
                if (error.response && error.response.data) {
                    if (error.response.data.username) {
                        this.usernameError = error.response.data.username[0];
                    }
                    if (error.response.data.password) {
                        this.passwordError = error.response.data.password[0];
                    }
                }
            }
        }
    };
}