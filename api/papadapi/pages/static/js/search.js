function searchArchiveDetails() {
    return {
        allArchiveDetails: [],
        allAnnotateDetails: [],
        isMobile: false,
        isLoading: true,
        search: null,
        searchIn: null,
        searchWhere: null,
        searchFrom: 'all_collections',
        searchCollections: [],
        currentUrl: new URL(window.location.href),
        params: null,
        noResults: true,
        loadingStories: 'We are pulling the story with its stories',
        isLoggedIn: false,


        URLConstructor() {
            this.params = new URLSearchParams(this.currentUrl.search)
            if (this.search != null) {
                this.params.set("search", this.search)
            }
            if (this.searchIn != null) {
                this.params.set("searchIn", this.searchIn)
            }
            if (this.searchWhere != null) {
                this.params.set("searchWhere", this.searchWhere)
            }
            if (this.searchFrom != null) {
                this.params.set("searchFrom", this.searchFrom)
            }
            if (this.searchCollections != [] && this.searchFrom === "selected_collections") {
                this.params.set("searchCollections", this.searchCollections.join(","))
            }
            history.pushState({}, '', `${this.currentUrl.pathname}?${this.params.toString()}`);
            if (this.searchIn === "media") {
                this.doArchiveSearch()
            } else {
                this.doAnnotateSearch()
            }
        },
        // Method to update the selected array
        updateSelection($event, value) {
            if ($event.target.checked) {
                // Add to the selected array
                this.searchCollections.push(value);
            } else {
                // Remove from the selected array
                this.searchCollections = this.searchCollections.filter(item => item !== value);
            }
        },
        init() {
            this.isLoggedIn = !!localStorage.getItem('authToken');
            this.params = new URLSearchParams(this.currentUrl.search)
            this.search = this.params.get("search")
            this.searchIn = this.params.get("searchIn")
            this.searchWhere = this.params.get("searchWhere")
            this.searchFrom = this.params.get("searchFrom")
            if (this.params.get("searchCollections") != null) {
                this.searchCollections = this.params.get("searchCollections")
            } else {
                this.searchCollections = []
            }
            if (this.searchIn === "media") {
                this.searchIn = "media"
                this.doArchiveSearch()
            } else {
                this.all
                this.searchIn = "annotation"
                this.doAnnotateSearch()
            }

        },
        doArchiveSearch() {
            if (this.search != "") {
                this.isLoading = true
                apiCall("/api/v1/archive/?" + this.params.toString(), 'GET')
                    .then(data => {
                        this.allAnnotateDetails = []
                        this.allArchiveDetails = data.results;
                        this.isLoading = false
                    })
                    .catch(error => {
                        this.isLoading = false
                        console.error('Error while calling API:', error);
                    });
            }
        },
        doAnnotateSearch() {
            this.isLoading = true
            apiCall("/api/v1/annotate/?" + this.params.toString(), 'GET')
                .then(data => {
                    this.allArchiveDetails = []
                    this.allAnnotateDetails = data.results
                    this.isLoading = false
                })
                .catch(error => {
                    this.isLoading = false
                    console.error('Error while calling API:', error);
                });
        }
    }
}