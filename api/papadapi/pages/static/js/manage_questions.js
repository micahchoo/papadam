function manageQuestions() {
    return {
        questionText: '',
        questionType: 'text',
        mandatory: false,
        default_value: '',
        isEditMode: false,
        editingQuestionId: null,
        questions: [],

        init() {
            this.listCurrentQuestions();
        },

        submitForm() {
            let payload = {
                question: this.questionText,
                type: this.questionType,
                mandatory: this.mandatory,
            };

            let endpoint = '';
            let method = 'PUT';

            if (this.isEditMode) {
                // Editing existing question
                endpoint = `/api/v1/group/update_question/${groupId}/`;
                payload.question_id = this.editingQuestionId;
            } else {
                // Adding a new question
                endpoint = `/api/v1/group/add_question/${groupId}/`;
                payload.default_value = this.default_value;
                payload.add_default_value = !!this.default_value; // Convert to boolean
            }

            apiCall(endpoint, method, payload)
                .then(response => {
                    console.log('Question added/updated successfully');
                    this.listCurrentQuestions();
                    this.resetForm();
                })
                .catch(error => {
                    console.error('Error while adding/updating question:', error);
                });
        },

        editQuestion(questionId) {
            const question = this.questions.find(q => q.id === questionId);
            this.questionText = question.question;
            this.questionType = question.type;
            this.mandatory = question.mandatory;
            this.default_value = question.default_value;
            this.isEditMode = true;
            this.editingQuestionId = questionId;

            // // Scroll to the form
            // this.$nextTick(() => { // Alpine.js way to wait for the DOM to update
            //     this.$refs.editQuestionSection.scrollIntoView({
            //         behavior: 'smooth'
            //     });
            // });
        },

        removeQuestion(questionId) {
            const payload = {
                question_id: questionId,
                remove_existing_data: true
            };

            apiCall(`/api/v1/group/remove_question/${groupId}/`, 'PUT', payload)
                .then(response => {
                    console.log('Question removed successfully');
                    this.listCurrentQuestions();
                })
                .catch(error => {
                    console.error('Error while removing question:', error);
                });
        },

        listCurrentQuestions() {
            apiCall(`/api/v1/group/${groupId}/`, 'GET')
                .then(response => {
                    this.questions = response.extra_group_questions || [];
                })
                .catch(error => {
                    console.error('Error while listing questions:', error);
                });
        },

        resetForm() {
            this.questionText = '';
            this.questionType = 'text';
            this.mandatory = false;
            this.default_value = '';
            this.isEditMode = false;
            this.editingQuestionId = null;
        },
        goBack() {
            window.location.href = '/ui/collection/' + groupId + '/';
        },
    };
}