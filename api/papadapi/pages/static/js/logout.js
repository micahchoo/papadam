function headerData() {
    return {
        isLoggedIn: false,

        init() {
            // Check if the user is logged in (e.g., by checking for a token in localStorage)
            this.isLoggedIn = !!localStorage.getItem('authToken');
        },

        logout() {
            // Clear the token or perform other logout actions
            localStorage.removeItem('authToken');

            // Update the isLoggedIn state
            this.isLoggedIn = false;

            // Redirect to the login page or homepage
            window.location.href = '/ui/login/';
        }
    };
}