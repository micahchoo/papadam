const urlParams = (location.pathname + location.search)
const groupId = urlParams.split("/")[3]
const mediaId = urlParams.split("/")[5]
const annotationId = urlParams.split("/")[7]
// TODO: Do basic checks before making these global
tokenValue = localStorage.getItem("authToken")


function truncateToWord(text, wordLimit) {
    const words = text.split(' ');
    if (words.length > wordLimit) {
        return words.slice(0, wordLimit).join(' ') + '...';
    } else {
        return text;
    }
}