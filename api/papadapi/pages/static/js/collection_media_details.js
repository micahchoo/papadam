// Debounce function
function debounce(func, delay) {
    let inDebounce;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(inDebounce);
        inDebounce = setTimeout(() => func.apply(context, args), delay);
    };
}

function formatTime(seconds) {
    var hours = Math.floor(seconds / 3600);
    var minutes = Math.floor((seconds - (hours * 3600)) / 60);
    var seconds = Math.floor(seconds % 60);

    // Add leading zeros if necessary
    hours = (hours < 10) ? "0" + hours : hours;
    minutes = (minutes < 10) ? "0" + minutes : minutes;
    seconds = (seconds < 10) ? "0" + seconds : seconds;

    return hours + ":" + minutes + ":" + seconds;
}
let isDataFetched = false;

function getCollectionMediaDetails() {
    return {
        collectionMediaDetails: null,
        currentTime: 0,
        playing: false,
        player: null,
        playText: "Play",
        targetStart: "0",
        targetEnd: "0",
        annotationText: "",
        tags: [],
        newTag: '', // Reactive property for the input value
        tagsCsv: '',
        collectionMediaAnnotations: [],
        selectedOption: '', // Tracks the selected option
        isAnnotationEditing: false,
        annotationEditUUID: null,
        isLoading: true,
        errorMessage: '',
        currentUser: '',
        loadingStories: 'We are pulling the story with its stories',
        annotationDataStructure: {
            "media_reference_id": '',
            "annotation_text": '',
            "media_target": '',
            "tags": ''
        },

        init() {
            if (!isDataFetched) {
                isDataFetched = true;
                apiCall("/api/v1/archive/" + mediaId + "/", 'GET')
                    .then(data => {
                        this.currentUser = window.currentUserData || [];
                        this.collectionMediaDetails = data
                        // Initialize Video.js
                        this.player = videojs(document.getElementById('my-video'), {});
                        this.player.src({
                            src: data.upload,
                            type: data.file_extension, //'application/x-mpegURL' // or the appropriate type for your video
                        });

                        // Update Alpine.js state on time update with debouncing
                        this.player.on('timeupdate', debounce(() => {
                            this.currentTime = Math.floor(this.player.currentTime());
                        }, 100));

                        // Sync play/pause state
                        this.player.on('play', () => this.playing = true);
                        this.player.on('pause', () => this.playing = false);
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            }
        },

        togglePlay() {
            if (this.player.paused()) {
                this.player.play();
                this.playText = "Pause"
            } else {
                this.playText = "Play"
                this.player.pause();
            }
        },
        updateStartTime() {
            this.targetStart = this.currentTime;
        },
        updateEndTime() {
            this.targetEnd = this.currentTime;
            if (this.playing == true) {
                this.togglePlay();
            }
        },
        setStartTime(startTime) {
            this.player.currentTime(startTime);
        },

        sort() {
            var type = this.selectedOption;
            if (type === 'oldestCreated') {
                this.collectionMediaAnnotations = this.collectionMediaAnnotations.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            } else if (type === 'latestCreated') {
                this.collectionMediaAnnotations = this.collectionMediaAnnotations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            } else if (type === 'oldestUpdated') {
                this.collectionMediaAnnotations = this.collectionMediaAnnotations.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            } else if (type === 'latestUpdated') {
                this.collectionMediaAnnotations = this.collectionMediaAnnotations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            }
        },

        addTagsFromInput() {
            const tagArray = this.newTag.split(',').map(tag => tag.trim()).filter(tag => tag);
            tagArray.forEach(tag => {
                if (!this.tags.includes(tag)) {
                    this.tags.push(tag);
                }
            });
            this.newTag = ''; // Clear the input field
            this.updateCsv();
        },

        removeTag(index) {
            this.tags.splice(index, 1);
            this.updateCsv();
        },

        updateCsv() {
            this.tagsCsv = this.tags.join(',');
        },

        getAnnotations() {
            apiCall("/api/v1/annotate/search/" + mediaId + "/", 'GET')
                .then(data => {
                    this.collectionMediaAnnotations = data;
                    this.isLoading = false;
                })
                .catch(error => {
                    if (error.response && error.response.status === 401) {
                        window.location.href = `/ui/unauthorised/`;
                    } else {
                        console.error('Error while calling API:', error);
                    }
                });
        },
        resetAnnotationForm() {
            // Reset the form
            this.annotationText = null;
            this.targetEnd = 0;
            this.targetStart = 0;
            this.tags = [];
            this.tagsCsv = '';
            this.newTag = '';
            this.isAnnotationEditing = false;
            this.annotationEditUUID = null;
            this.errorMessage = '';
        },

        createOrEditAnnotation() {
            // Before saving, parse the input field and add any remaining tags
            this.addTagsFromInput();
            // Validation for tags
            if (this.tags.length === 0) {
                this.errorMessage = 'Please add at least one tag before annotating.';
                return; // Prevent the API call if validation fails
            }
            data = {
                "media_reference_id": mediaId,
                "annotation_text": this.annotationText,
                "media_target": "t=" + this.targetStart + "," + this.targetEnd,
                "tags": this.tagsCsv
            };
            if (this.isAnnotationEditing) {
                apiCall("/api/v1/annotate/" + this.annotationEditUUID + "/", 'PUT', data = data)
                    .then(data => {
                        this.collectionMediaAnnotations = this.collectionMediaAnnotations.filter(item => item.uuid !== this.annotationEditUUID);
                        this.collectionMediaAnnotations.push(data);
                        this.resetAnnotationForm();
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            } else {
                apiCall("/api/v1/annotate/", 'POST', data = data)
                    .then(data => {
                        this.collectionMediaAnnotations.push(data);
                        this.resetAnnotationForm();
                    })
                    .catch(error => {
                        console.error('Error while calling API:', error);
                    });
            }
        },

        loadAnnotationEdit(annotationUUID) {
            const annotationData = this.collectionMediaAnnotations.filter(item => item.uuid === annotationUUID)[0];
            const time = annotationData.media_target.split("=")[1].split(",");
            this.annotationText = annotationData.annotation_text;
            this.targetStart = time[0];
            this.targetEnd = time[1];
            for (var i = 0; i < annotationData.tags.length; i++) {
                var tag = annotationData.tags[i];
                this.newTag = tag.name;
                this.addTagsFromInput();
            }
            this.isAnnotationEditing = true;
            this.annotationEditUUID = annotationData.uuid;
            this.setStartTime(this.targetStart);
        },

        deleteAnnotation(annotationUUID) {
            apiCall("/api/v1/annotate/" + annotationUUID + "/", 'DELETE')
                .then(() => {
                    this.collectionMediaAnnotations = this.collectionMediaAnnotations.filter(item => item.uuid !== annotationUUID);
                })
                .catch(error => {
                    console.error('Error while calling API:', error);
                });
        },

        isAuthCollection() {
            if (this.currentUser !== '' && this.collectionMediaDetails.group.users.some(user => user.id === this.currentUser.id)) {
                return true;
            } else {
                return null;
            }
        },

        isAuthAnnotation(annotatedUserId) {
            if (this.currentUser !== '' && annotatedUserId === this.currentUser.id) {
                return true;
            } else {
                return null;
            }
        },

        convertUrlsToLinks(text) {
            const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
            if (urlRegex.test(text)) { // Check if there is any URL in the text
                return text.replace(urlRegex, function(url) {
                    return '<a href="' + url + '" target="_blank" class="text-blue-500 underline">' + url + '</a>';
                });
            }
            return text; // Return the original text if no URL is found
        },

        inGroup() {
            if (this.currentUser && this.collectionMediaDetails.group.users.some(user => user.id === this.currentUser.id)) {
                return true;
            } else {
                return false;
            }
        }

    };
}